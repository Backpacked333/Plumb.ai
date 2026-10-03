"""Reference release checker (PL-034, PL-040, PL-042, PL-043, PL-046, PL-047, PL-061).

``check_release`` judges a persisted :class:`ReleaseManifest` together with the
attestations and approvals it references. An attestation is *accepted* for a
component only when the manifest references it by digest, it passed, its input
digest is exactly the component's digest and it was produced in the release's
scope. It reports:

============================== =================== ========= ===============================================
code                           error_class         severity  rule
============================== =================== ========= ===============================================
``ATTESTATION_DIGEST_MISMATCH`` VERIFICATION_FAILED ERROR    an attestation_ref names a digest no supplied
                                                             attestation carries, or an attestation's input
                                                             digest matches no component: verification was
                                                             produced for different bytes (PL-046)
``ATTESTATION_SCOPE_MISMATCH`` VERIFICATION_FAILED ERROR     attestation environment is not a rollout
                                                             environment, its tenant differs, or it did not
                                                             cover the release scope (PL-046)
``ATTESTATION_FAILED``         VERIFICATION_FAILED ERROR     attestation result is FAIL (PL-042)
``ATTESTATION_MISSING``        VERIFICATION_FAILED ERROR     a present component has no accepted attestation
                                                             for its digest (PL-046)
``MISSING_VERIFICATION_LEVEL`` VERIFICATION_FAILED ERROR     no accepted attestation at INTEGRATION_BEHAVIOR,
                                                             or none at BUSINESS_OUTCOME; passing unit tests
                                                             cannot substitute (PL-043)
``APPROVAL_INVALID``           per check_approval  ERROR     an approval_ref is not supplied, or
                                                             :func:`check_approval` rejects the approval for
                                                             the manifest's approval subject digest, tenant
                                                             and the current policy version (PL-040)
``MODEL_ALIAS_UNRESOLVED``     STATE_CONFLICT      ERROR     model component present without an immutable
                                                             resolved_model_version (PL-034, ADR-008)
``ADVERSARIAL_TESTS_MISSING``  VERIFICATION_FAILED WARNING   no accepted attestation has a passing check named
                                                             ``adversarial*`` (PL-043, PL-061)
============================== =================== ========= ===============================================

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
from plumb.contracts.approval import ApprovalRecord, require_aware
from plumb.contracts.common import ErrorClass, VerificationLevel, compute_artifact_digest
from plumb.contracts.release import ReleaseManifest, is_immutable_model_version
from plumb.contracts.verification import AttestationResult, VerificationAttestation

CHECKER_NAME = "release_checker"

REQUIRED_VERIFICATION_LEVELS: tuple[VerificationLevel, ...] = (
    VerificationLevel.INTEGRATION_BEHAVIOR,
    VerificationLevel.BUSINESS_OUTCOME,
)
"""Levels a release must carry accepted attestations at (PL-043)."""

ADVERSARIAL_CHECK_PREFIX = "adversarial"


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

    levels = {attestation.level for attestation in accepted}
    for level in REQUIRED_VERIFICATION_LEVELS:
        if level not in levels:
            _error(
                report,
                "MISSING_VERIFICATION_LEVEL",
                f"no accepted attestation at level {level.value}; passing unit tests cannot substitute for "
                "verifying a real effect in the intended environment",
                level=level.value,
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
    by_digest = {_artifact_digest(attestation): attestation for attestation in attestations}
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
    by_digest = {_artifact_digest(approval): approval for approval in approvals}
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


def _artifact_digest(artifact: BaseModel) -> str:
    """The store-assigned digest when present, else the digest the store would assign."""
    assigned = getattr(artifact, "content_digest", None)
    return assigned if assigned is not None else compute_artifact_digest(artifact)


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


__all__ = ["CHECKER_NAME", "REQUIRED_VERIFICATION_LEVELS", "ADVERSARIAL_CHECK_PREFIX", "check_release"]
