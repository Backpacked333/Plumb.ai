"""Reference release checker (PL-034, PL-040, PL-042, PL-043, PL-046, PL-047, PL-061).

``check_release`` judges a persisted :class:`ReleaseManifest` together with the
attestations and approvals it references. Records are matched to the manifest's
references by their *recomputed* digest (:func:`compute_artifact_digest`), never
by the ``content_digest`` they declare about themselves: a record whose declared
digest does not match its bytes is rejected outright. An attestation is
*accepted* for a component only when the manifest references it by digest, it
was issued by a verifier (not an agent), it passed, its input digest is exactly
the component's digest and it was produced in the release's scope. It reports:

================================ =================== ========= ===============================================
code                             error_class         severity  rule
================================ =================== ========= ===============================================
``ARTIFACT_DIGEST_INCONSISTENT`` VERIFICATION_FAILED ERROR     a supplied attestation or approval declares a
                                                               content_digest that is not the digest of its
                                                               own bytes; it is not evidence for anything
                                                               (PL-040, PL-046)
``ATTESTATION_DIGEST_MISMATCH``  VERIFICATION_FAILED ERROR     an attestation_ref names a digest no supplied
                                                               attestation carries, or an attestation's input
                                                               digest matches no component: verification was
                                                               produced for different bytes (PL-046)
``ATTESTATION_SCOPE_MISMATCH``   VERIFICATION_FAILED ERROR     attestation environment is not a rollout
                                                               environment, its tenant differs, or it did not
                                                               cover the release scope (PL-046)
``ATTESTATION_NOT_INDEPENDENT``  VERIFICATION_FAILED ERROR     attestation produced by a build or runtime
                                                               agent, or its verifier is not a VERIFIER
                                                               (defensive, PL-042)
``ATTESTATION_FAILED``           VERIFICATION_FAILED ERROR     attestation result is FAIL (PL-042)
``ATTESTATION_MISSING``          VERIFICATION_FAILED ERROR     a present component has no accepted attestation
                                                               for its digest (PL-046)
``ENVIRONMENT_NOT_VERIFIED``     VERIFICATION_FAILED ERROR     a rollout stage runs in an environment where no
                                                               accepted attestation established
                                                               INTEGRATION_BEHAVIOR or higher (PL-043, PL-046)
``MISSING_VERIFICATION_LEVEL``   VERIFICATION_FAILED ERROR     no accepted passing check at INTEGRATION_BEHAVIOR,
                                                               or none at BUSINESS_OUTCOME; levels are read from
                                                               the checks that passed, not from a declared field
                                                               (PL-043)
``HELD_OUT_EVALUATION_MISSING``  VERIFICATION_FAILED ERROR     a model or workflow component is present but the
                                                               evaluation component is omitted (PL-034, PL-043)
``OPERATING_PLAN_MISSING``       VERIFICATION_FAILED ERROR     no operating plan, or monitors missing for a
                                                               PL-048 signal (defensive, PL-043, PL-048)
``APPROVAL_INVALID``             per check_approval  ERROR     an approval_ref is not supplied, or
                                                               :func:`check_approval` rejects the approval for
                                                               the manifest's approval subject digest, tenant,
                                                               the current policy version and the
                                                               IMPLEMENT_OPERATE decision (PL-040, PL-041)
``MODEL_ALIAS_UNRESOLVED``       STATE_CONFLICT      ERROR     model component present without an immutable
                                                               resolved_model_version (PL-034, ADR-008)
``ADVERSARIAL_TESTS_MISSING``    VERIFICATION_FAILED WARNING   no accepted attestation has a passing check named
                                                               ``adversarial*`` (PL-043, PL-061)
================================ =================== ========= ===============================================

``ADVERSARIAL_TESTS_MISSING`` is a warning rather than an error in this
reference checker because the rule is enforced by *name*: adversarial coverage
may live inside a protected bundle under a check name the checker cannot
recognise, and a local naming convention must not be able to block a release
on its own. The production gate for PL-061 (all high-severity failures block
activation) runs the adversarial suite itself; this finding tells the operator
that the manifest shows no evidence of it.

The checker never executes anything and never mutates its inputs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from plumb.checker.approval_checker import check_approval
from plumb.checker.findings import CheckReport, Finding, Severity
from plumb.contracts.approval import AGENT_PRINCIPAL_TYPES, ApprovalRecord, DecisionKind, require_aware
from plumb.contracts.common import ErrorClass, PrincipalType, VerificationLevel, compute_artifact_digest
from plumb.contracts.release import EVALUATION_DEPENDENT_COMPONENTS, MonitorKind, ReleaseManifest, is_immutable_model_version
from plumb.contracts.verification import AttestationResult, VerificationAttestation

CHECKER_NAME = "release_checker"

REQUIRED_VERIFICATION_LEVELS: tuple[VerificationLevel, ...] = (
    VerificationLevel.INTEGRATION_BEHAVIOR,
    VerificationLevel.BUSINESS_OUTCOME,
)
"""Levels a release must carry accepted attestations at (PL-043)."""

_LEVEL_RANK: dict[VerificationLevel, int] = {level: index for index, level in enumerate(VerificationLevel)}

ADVERSARIAL_CHECK_PREFIX = "adversarial"
RELEASE_DECISION_KIND = DecisionKind.IMPLEMENT_OPERATE
"""The decision an approval of a release must record (PL-041)."""


def check_release(
    manifest: ReleaseManifest,
    attestations: list[VerificationAttestation],
    approvals: list[ApprovalRecord],
    *,
    now: datetime,
    current_policy_version: str,
) -> CheckReport:
    """Judge ``manifest`` with the supplied evidence; ``report.ok`` means no ERROR finding.

    ``attestations`` and ``approvals`` are the records the caller resolved for
    the manifest's ``attestation_refs`` and ``approval_refs``. Records that the
    manifest does not reference are ignored as evidence and listed in the
    summary, because a release binds its evidence by digest or not at all.
    """
    require_aware(now, "now")
    report = CheckReport(checker=CHECKER_NAME, subject=manifest.artifact_id)
    components = manifest.present_components()
    keys_by_digest: dict[str, list[str]] = {}
    for key, ref in components.items():
        keys_by_digest.setdefault(ref.digest, []).append(key)

    accepted, unreferenced = _accept_attestations(manifest, attestations, keys_by_digest, report)

    verified: set[str] = set()
    for attestation in accepted:
        verified.update(keys_by_digest[attestation.input_artifact_digest])
    for key in sorted(components):
        if key not in verified:
            _error(
                report,
                "ATTESTATION_MISSING",
                f"component {key!r} ({components[key].artifact_id}) has no accepted attestation for its digest",
                subject_id=key,
                component_digest=components[key].digest,
            )

    # Levels are established by the checks that actually passed, not by the level an attestation declares.
    levels = {check.level for attestation in accepted for check in attestation.passed_checks()}
    for level in REQUIRED_VERIFICATION_LEVELS:
        if level not in levels:
            _error(
                report,
                "MISSING_VERIFICATION_LEVEL",
                f"no accepted attestation has a passing check at level {level.value}; passing unit tests cannot "
                "substitute for verifying a real effect in the intended environment",
                level=level.value,
            )

    # Every environment a rollout stage runs in must have been verified behaviourally in that environment.
    integration_rank = _LEVEL_RANK[VerificationLevel.INTEGRATION_BEHAVIOR]
    behaviourally_verified = {
        attestation.environment
        for attestation in accepted
        if any(_LEVEL_RANK[check.level] >= integration_rank for check in attestation.passed_checks())
    }
    for stage in manifest.rollout_policy:
        if stage.environment not in behaviourally_verified:
            _error(
                report,
                "ENVIRONMENT_NOT_VERIFIED",
                f"rollout stage {stage.state.value} runs in {stage.environment!r}, where no accepted attestation "
                f"established {VerificationLevel.INTEGRATION_BEHAVIOR.value} or higher; a sandbox result does not "
                "verify a real effect in the production environment",
                subject_id=stage.environment,
                stage=stage.state.value,
                environment=stage.environment,
                verified_environments=sorted(behaviourally_verified),
            )

    needing_evaluation = [
        key for key in EVALUATION_DEPENDENT_COMPONENTS if (component := manifest.components.get(key)) is not None and component.present
    ]
    evaluation = manifest.components.get("evaluation")
    if needing_evaluation and not (evaluation is not None and evaluation.present):
        _error(
            report,
            "HELD_OUT_EVALUATION_MISSING",
            f"components {', '.join(needing_evaluation)} are present but the evaluation component is omitted; model "
            "promotion requires a held-out evaluation and a release requires business scenario evaluation",
            subject_id="evaluation",
            present_components=needing_evaluation,
        )

    operating_plan = getattr(manifest, "operating_plan", None)
    if operating_plan is None:
        _error(
            report,
            "OPERATING_PLAN_MISSING",
            "release carries no prospective operating plan (monitors, rollback owner, outcome measurement)",
            subject_id="operating_plan",
        )
    else:
        uncovered = sorted(kind.value for kind in MonitorKind if kind not in operating_plan.covered_kinds())
        if uncovered:
            _error(
                report,
                "OPERATING_PLAN_MISSING",
                f"operating plan has no monitor for: {', '.join(uncovered)}; every active intervention is monitored on "
                "freshness, schema change, execution failure, quality drift, review burden, cost and outcome",
                subject_id="operating_plan",
                missing_monitors=uncovered,
            )

    if not any(
        check.name.startswith(ADVERSARIAL_CHECK_PREFIX)
        for attestation in accepted
        for check in attestation.passed_checks()
    ):
        report.add(
            Finding(
                code="ADVERSARIAL_TESTS_MISSING",
                error_class=ErrorClass.VERIFICATION_FAILED,
                severity=Severity.WARNING,
                message=(
                    f"no accepted attestation has a passing check named {ADVERSARIAL_CHECK_PREFIX}*; the manifest "
                    "shows no evidence of adversarial tests (advisory: the production release suite enforces this)"
                ),
            )
        )

    approvals_valid = _check_approvals(manifest, approvals, report, now=now, current_policy_version=current_policy_version)

    model = manifest.components.get("model")
    if model is not None and model.present:
        resolved = manifest.resolved_model_version
        if resolved is None or not is_immutable_model_version(resolved):
            _error(
                report,
                "MODEL_ALIAS_UNRESOLVED",
                f"model component is present but resolved_model_version {resolved!r} is not an immutable version; "
                "a mutable alias could switch behaviour mid-case",
                error_class=ErrorClass.STATE_CONFLICT,
                subject_id="model",
                resolved_model_version=resolved,
            )

    report.summary = {
        "verified_components": sorted(verified),
        "unverified_components": sorted(set(components) - verified),
        "omitted_components": sorted(key for key, component in manifest.components.items() if not component.present),
        "accepted_attestations": sorted(attestation.artifact_id for attestation in accepted),
        "verification_levels": sorted(level.value for level in levels),
        "behaviourally_verified_environments": sorted(behaviourally_verified),
        "unreferenced_attestations": sorted(unreferenced),
        "approvals_checked": len(manifest.approval_refs),
        "approvals_valid": approvals_valid,
        "rollout_environments": sorted(manifest.rollout_environments()),
        "evaluated_at": now.isoformat(),
    }
    return report


def _accept_attestations(
    manifest: ReleaseManifest,
    attestations: list[VerificationAttestation],
    keys_by_digest: dict[str, list[str]],
    report: CheckReport,
) -> tuple[list[VerificationAttestation], list[str]]:
    """Return the accepted attestations and the ids of supplied attestations the manifest does not reference."""
    by_digest = _index_by_digest(attestations, "attestation", report)
    referenced = {ref.digest for ref in manifest.attestation_refs}
    for ref in manifest.attestation_refs:
        if ref.digest not in by_digest:
            _error(
                report,
                "ATTESTATION_DIGEST_MISMATCH",
                f"attestation_ref {ref.artifact_id} names digest {ref.digest} but no supplied attestation carries it",
                subject_id=ref.artifact_id,
                reason="attestation_not_supplied",
                referenced_digest=ref.digest,
            )
    environments = manifest.rollout_environments()
    accepted: list[VerificationAttestation] = []
    unreferenced: list[str] = []
    for digest, attestation in by_digest.items():
        if digest not in referenced:
            unreferenced.append(attestation.artifact_id)
            continue
        acceptable = True
        if attestation.input_artifact_digest not in keys_by_digest:
            acceptable = False
            _error(
                report,
                "ATTESTATION_DIGEST_MISMATCH",
                f"attestation {attestation.artifact_id} verified digest {attestation.input_artifact_digest}, which is "
                "no component of this release: verification was produced for different bytes",
                subject_id=attestation.artifact_id,
                reason="different_bytes",
                input_artifact_digest=attestation.input_artifact_digest,
            )
        problems = _scope_problems(manifest, attestation, environments)
        if problems:
            acceptable = False
            _error(
                report,
                "ATTESTATION_SCOPE_MISMATCH",
                f"attestation {attestation.artifact_id} was produced for a different scope: " + "; ".join(problems),
                subject_id=attestation.artifact_id,
                environment=attestation.environment,
                rollout_environments=sorted(environments),
                problems=problems,
            )
        independence = _independence_problems(attestation)
        if independence:
            acceptable = False
            _error(
                report,
                "ATTESTATION_NOT_INDEPENDENT",
                f"attestation {attestation.artifact_id} is not independent evidence: " + "; ".join(independence),
                subject_id=attestation.artifact_id,
                problems=independence,
            )
        if attestation.result is AttestationResult.FAIL:
            acceptable = False
            _error(
                report,
                "ATTESTATION_FAILED",
                f"attestation {attestation.artifact_id} failed: "
                + ", ".join(check.name for check in attestation.checks if check.result.value == "FAIL"),
                subject_id=attestation.artifact_id,
            )
        if acceptable:
            accepted.append(attestation)
    return accepted, unreferenced


def _independence_problems(attestation: VerificationAttestation) -> list[str]:
    """Defensive re-check of PL-042 for records that bypassed the contract validators."""
    problems: list[str] = []
    if attestation.producer.principal_type in AGENT_PRINCIPAL_TYPES:
        problems.append(f"produced by {attestation.producer.principal_id}, a {attestation.producer.principal_type.value}")
    if attestation.verifier.principal_type is not PrincipalType.VERIFIER:
        problems.append(f"verifier {attestation.verifier.principal_id} is a {attestation.verifier.principal_type.value}")
    if attestation.verifier.principal_id == attestation.assessed_producer.principal_id:
        problems.append("verifier is the principal it assesses")
    return problems


def _scope_problems(
    manifest: ReleaseManifest, attestation: VerificationAttestation, environments: set[str]
) -> list[str]:
    problems: list[str] = []
    if attestation.environment not in environments:
        problems.append(
            f"environment {attestation.environment!r} is not a rollout environment ({', '.join(sorted(environments))})"
        )
    if attestation.tenant_id != manifest.tenant_id:
        problems.append(f"tenant {attestation.tenant_id} differs from release tenant {manifest.tenant_id}")
    problems.extend(
        f"verification did not cover release {violation}" for violation in manifest.scope.is_within(attestation.scope)
    )
    return problems


def _check_approvals(
    manifest: ReleaseManifest,
    approvals: list[ApprovalRecord],
    report: CheckReport,
    *,
    now: datetime,
    current_policy_version: str,
) -> int:
    """Run ``check_approval`` for every approval_ref; return how many approvals are valid."""
    by_digest = _index_by_digest(approvals, "approval", report)
    subject_digest = manifest.approval_subject_digest()
    valid = 0
    for ref in manifest.approval_refs:
        approval = by_digest.get(ref.digest)
        if approval is None:
            _error(
                report,
                "APPROVAL_INVALID",
                f"approval_ref {ref.artifact_id} names digest {ref.digest} but no supplied approval carries it",
                error_class=ErrorClass.AUTH_REQUIRED,
                subject_id=ref.artifact_id,
                cause="approval_record_not_supplied",
            )
            continue
        sub_report = check_approval(
            approval,
            subject_digest=subject_digest,
            tenant_id=manifest.tenant_id,
            policy_version=current_policy_version,
            now=now,
            decision_kind=RELEASE_DECISION_KIND,
        )
        if sub_report.ok:
            valid += 1
        for finding in sub_report.errors:
            _error(
                report,
                "APPROVAL_INVALID",
                f"approval {approval.approval_id} does not authorize this release: {finding.message}",
                error_class=finding.error_class,
                subject_id=approval.approval_id,
                cause=finding.code,
                **finding.details,
            )
    return valid


def _index_by_digest(records: list[Any], label: str, report: CheckReport) -> dict[str, Any]:
    """Index records by the digest of their own bytes; a record whose declared digest disagrees is dropped.

    The declared ``content_digest`` is a claim; the recomputed digest is the
    fact. A record that claims another digest is reported and never used as
    evidence, so a forged attestation or approval cannot be bound to the
    manifest by naming the digest the manifest expects.
    """
    by_digest: dict[str, Any] = {}
    for record in records:
        actual = compute_artifact_digest(record)
        declared = getattr(record, "content_digest", None)
        if declared is not None and declared != actual:
            _error(
                report,
                "ARTIFACT_DIGEST_INCONSISTENT",
                f"{label} {record.artifact_id} declares content_digest {declared} but its bytes digest to {actual}; "
                "a record that misstates its own digest is not evidence",
                subject_id=record.artifact_id,
                declared_digest=declared,
                actual_digest=actual,
            )
            continue
        by_digest[actual] = record
    return by_digest


def _artifact_digest(artifact: BaseModel) -> str:
    """The digest of an artifact's own bytes; the declared ``content_digest`` is never trusted."""
    return compute_artifact_digest(artifact)


def _error(
    report: CheckReport,
    code: str,
    message: str,
    *,
    error_class: ErrorClass = ErrorClass.VERIFICATION_FAILED,
    subject_id: str | None = None,
    **details: Any,
) -> None:
    report.add(
        Finding(code=code, error_class=error_class, message=message, subject_id=subject_id, details=details)
    )


__all__ = ["CHECKER_NAME", "REQUIRED_VERIFICATION_LEVELS", "ADVERSARIAL_CHECK_PREFIX", "RELEASE_DECISION_KIND", "check_release"]
