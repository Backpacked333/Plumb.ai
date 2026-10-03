"""Behavioural tests for the trust vertical: approval, verification, infrastructure and release.

Builders construct a small valid world (one tenant, one human owner, one build
agent, one verifier) and each MUST / MUST NOT rule is then provoked by one
minimal mutation. Fixtures are synthetic; no secret values appear anywhere.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from pydantic import ValidationError

from plumb.checker.approval_checker import (
    CHECKER_NAME as APPROVAL_CHECKER,
    check_approval,
    group_missing_authorizations,
)
from plumb.checker.findings import Severity
from plumb.checker.release_checker import CHECKER_NAME as RELEASE_CHECKER, check_release
from plumb.contracts.approval import ApprovalRecord, DecisionKind
from plumb.contracts.common import (
    ArtifactKind,
    ArtifactRef,
    DependencyRecord,
    EffectClass,
    ErrorClass,
    FailureClass,
    Money,
    Principal,
    PrincipalType,
    ReleaseState,
    ResourceScope,
    VerificationLevel,
    compute_artifact_digest,
    digest_bytes,
)
from plumb.contracts.infrastructure import (
    ChangeAction,
    ExpandContractPhase,
    InfrastructurePlan,
    ResourceChange,
    RollbackClassification,
)
from plumb.contracts.release import (
    REQUIRED_COMPONENTS,
    ReleaseComponent,
    ReleaseManifest,
    RolloutStage,
    is_immutable_model_version,
)
from plumb.contracts.verification import (
    AttestationResult,
    CheckOutcome,
    CheckResult,
    VerificationAttestation,
)

T0 = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
NOW = T0 + timedelta(hours=2)
TENANT = "tnt_demo0001"
OTHER_TENANT = "tnt_demo0002"
POLICY = "1.4.0"
ENVIRONMENT = "sandbox-eu"

OWNER = Principal(principal_id="own_demo_owner", principal_type=PrincipalType.HUMAN_OWNER, authenticated_via="oidc:demo-idp")
APPROVER = Principal(
    principal_id="apv_demo_controller", principal_type=PrincipalType.HUMAN_APPROVER, authenticated_via="oidc:demo-idp"
)
APPROVAL_SERVICE = Principal(principal_id="svc_approvals", principal_type=PrincipalType.SERVICE, authenticated_via="mtls:approvals")
BUILD_AGENT = Principal(principal_id="agent_build_17", principal_type=PrincipalType.BUILD_AGENT, authenticated_via="workload:build")
RUNTIME_AGENT = Principal(
    principal_id="agent_runtime_3", principal_type=PrincipalType.RUNTIME_AGENT, authenticated_via="workload:runtime"
)
VERIFIER = Principal(principal_id="verifier_core", principal_type=PrincipalType.VERIFIER, authenticated_via="mtls:verifier")
RELEASE_EXECUTOR = Principal(
    principal_id="svc_release_executor", principal_type=PrincipalType.RELEASE_EXECUTOR, authenticated_via="mtls:release"
)


def digest(label: str) -> str:
    return digest_bytes(label.encode("utf-8"))


def header(artifact_id: str, producer: Principal, **overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "artifact_id": artifact_id,
        "tenant_id": TENANT,
        "version": 1,
        "producer": producer,
        "created_at": T0,
    }
    fields.update(overrides)
    return fields


def rejects(builder: Any, match: str, **overrides: Any) -> None:
    with pytest.raises(ValidationError, match=match):
        builder(**overrides)


def only(findings: list[Any], code: str) -> list[Any]:
    return [finding for finding in findings if finding.code == code]


def bypass_validation(model: Any, **overrides: Any) -> Any:
    """Rebuild ``model`` through ``model_construct`` so contract validators do not run."""
    fields = {name: getattr(model, name) for name in type(model).model_fields}
    fields.update(overrides)
    return type(model).model_construct(**fields)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

SUBJECT_DIGEST = digest("release-manifest-bytes")


def make_approval(**overrides: Any) -> ApprovalRecord:
    fields = header("apr_release_001", APPROVAL_SERVICE)
    fields.update(
        approval_id="apr_release_001",
        decision_kind=DecisionKind.IMPLEMENT_OPERATE,
        subject_digest=SUBJECT_DIGEST,
        policy_version=POLICY,
        approver=OWNER,
        authenticated_decision_ref="idp-event:demo/decision/4711",
        approved_at=T0,
        expires_at=T0 + timedelta(days=30),
        scope_tenant=TENANT,
    )
    fields.update(overrides)
    return ApprovalRecord(**fields)


def make_check(
    name: str = "contract_tests",
    level: VerificationLevel = VerificationLevel.INTEGRATION_BEHAVIOR,
    result: CheckOutcome = CheckOutcome.PASS,
    evidence_refs: tuple[str, ...] = ("log:verifier/run/1",),
    detail: str | None = None,
) -> CheckResult:
    return CheckResult(name=name, level=level, result=result, evidence_refs=list(evidence_refs), detail=detail)


def make_attestation(
    input_digest: str,
    level: VerificationLevel = VerificationLevel.INTEGRATION_BEHAVIOR,
    checks: list[CheckResult] | None = None,
    **overrides: Any,
) -> VerificationAttestation:
    fields = header("att_connector_001", VERIFIER)
    fields.update(
        verifier=VERIFIER,
        verifier_version="2.1.0",
        input_artifact_digest=input_digest,
        level=level,
        checks=checks if checks is not None else [make_check(level=level)],
        result=AttestationResult.PASS,
        timestamp=T0 + timedelta(minutes=30),
        environment=ENVIRONMENT,
        protected_bundle_digest=digest("protected-bundle-v3"),
        assessed_producer=BUILD_AGENT,
        scope=ResourceScope(source_ids=["src_demo_ledger"], destination_ids=["dst_demo_drafts"]),
    )
    fields.update(overrides)
    return VerificationAttestation(**fields)


def make_change(**overrides: Any) -> ResourceChange:
    fields: dict[str, Any] = {
        "resource_id": "res_queue_collector",
        "action": ChangeAction.CREATE,
        "rollback_classification": RollbackClassification.ROLLBACK,
        "ownership_tags": {"owner": "plumb", "tenant": TENANT},
        "estimated_cost": Money(minor_units=1200, currency="USD"),
    }
    fields.update(overrides)
    return ResourceChange(**fields)


def preview_ref(kind: ArtifactKind = ArtifactKind.INFRASTRUCTURE_PREVIEW) -> ArtifactRef:
    return ArtifactRef(artifact_id="prev_collector_001", kind=kind, digest=digest("preview"))


def make_plan(**overrides: Any) -> InfrastructurePlan:
    fields = header("inf_collector_001", BUILD_AGENT)
    fields.update(
        template_refs=[ArtifactRef(artifact_id="tpl_queue_v2", kind=ArtifactKind.ADAPTER_CONFIGURATION, digest=digest("tpl"))],
        preview_diff_ref=preview_ref(),
        cost_estimate=Money(minor_units=5000, currency="USD"),
        state_lock_ref="lock:stacks/demo/collector",
        environment=ENVIRONMENT,
        changes=[make_change()],
        expand_contract_phase=ExpandContractPhase.NONE,
    )
    fields.update(overrides)
    return InfrastructurePlan(**fields)


COMPONENT_KINDS_FOR_FIXTURE: dict[str, ArtifactKind] = {
    "workflow": ArtifactKind.WORKFLOW_SPEC,
    "connector": ArtifactKind.INTEGRATION_SPEC,
    "collector": ArtifactKind.COLLECTION_SPEC,
    "model": ArtifactKind.MODEL_VERSION,
    "infrastructure": ArtifactKind.INFRASTRUCTURE_PLAN,
    "evaluation": ArtifactKind.EVALUATION_REPORT,
}
OMITTED: dict[str, str] = {
    "prompt": "deterministic extraction; no model prompt in this release",
    "policy": "policy carried by the envelope, unchanged",
    "schema": "no schema change",
}
COMPONENT_LEVELS: dict[str, VerificationLevel] = {
    "workflow": VerificationLevel.BUSINESS_OUTCOME,
    "connector": VerificationLevel.INTEGRATION_BEHAVIOR,
    "collector": VerificationLevel.INTEGRATION_BEHAVIOR,
    "model": VerificationLevel.ARTIFACT_INTEGRITY,
    "infrastructure": VerificationLevel.INTEGRATION_BEHAVIOR,
    "evaluation": VerificationLevel.ARTIFACT_INTEGRITY,
}


def component_ref(key: str) -> ArtifactRef:
    return ArtifactRef(artifact_id=f"{key}_demo_001", kind=COMPONENT_KINDS_FOR_FIXTURE[key], digest=digest(f"{key}-bytes"))


def make_components() -> dict[str, ReleaseComponent]:
    components = {key: ReleaseComponent(ref=component_ref(key)) for key in COMPONENT_KINDS_FOR_FIXTURE}
    components.update({key: ReleaseComponent(omitted_reason=reason) for key, reason in OMITTED.items()})
    return components


def attestation_ref(attestation: VerificationAttestation) -> ArtifactRef:
    return ArtifactRef(
        artifact_id=attestation.artifact_id,
        kind=ArtifactKind.VERIFICATION_ATTESTATION,
        digest=compute_artifact_digest(attestation),
    )


def approval_ref(approval: ApprovalRecord) -> ArtifactRef:
    return ArtifactRef(artifact_id=approval.artifact_id, kind=ArtifactKind.APPROVAL_RECORD, digest=compute_artifact_digest(approval))


def workflow_checks() -> list[CheckResult]:
    return [
        make_check("business_scenarios", VerificationLevel.BUSINESS_OUTCOME, evidence_refs=("receipt:cases/42",)),
        make_check("adversarial_instructions", VerificationLevel.BUSINESS_OUTCOME, evidence_refs=("log:adversarial/1",)),
    ]


def component_attestation(key: str, **overrides: Any) -> VerificationAttestation:
    level = COMPONENT_LEVELS[key]
    checks = workflow_checks() if key == "workflow" else [make_check(f"{key}_checks", level)]
    fields: dict[str, Any] = {"artifact_id": f"att_{key}_001", "level": level, "checks": checks}
    fields.update(overrides)
    return make_attestation(component_ref(key).digest, **fields)


def default_attestations() -> dict[str, VerificationAttestation]:
    return {key: component_attestation(key) for key in COMPONENT_KINDS_FOR_FIXTURE}


def rollout() -> list[RolloutStage]:
    return [
        RolloutStage(state=ReleaseState.SHADOW, gate="shadow parity >= 0.98 over 200 cases", environment=ENVIRONMENT, max_case_fraction=1.0),
        RolloutStage(state=ReleaseState.CANARY, gate="no high-severity failure in canary", environment=ENVIRONMENT, max_case_fraction=0.1),
        RolloutStage(state=ReleaseState.ACTIVE, gate="owner sign-off on canary report", environment=ENVIRONMENT, max_case_fraction=1.0),
    ]


def make_manifest(
    attestations: dict[str, VerificationAttestation] | None = None,
    approvals: list[ApprovalRecord] | None = None,
    **overrides: Any,
) -> ReleaseManifest:
    attestations = attestations if attestations is not None else default_attestations()
    fields = header("rel_demo_001", RELEASE_EXECUTOR)
    fields.update(
        components=make_components(),
        attestation_refs=[attestation_ref(attestation) for attestation in attestations.values()],
        approval_refs=[approval_ref(approval) for approval in (approvals or [])],
        rollout_policy=rollout(),
        resolved_model_version="invoice-classifier:12",
        denominators={"cases_shadowed": 200},
        allowed_effect_classes=[EffectClass.READ, EffectClass.INTERNAL_WRITE],
        review_thresholds={"confidence_floor": 0.8},
        scope=ResourceScope(source_ids=["src_demo_ledger"]),
    )
    fields.update(overrides)
    return ReleaseManifest(**fields)


def release_world(
    attestations: dict[str, VerificationAttestation] | None = None, **approval_overrides: Any
) -> tuple[ReleaseManifest, list[VerificationAttestation], list[ApprovalRecord]]:
    """Manifest, its attestations and one approval bound to the manifest's approval subject digest."""
    attestations = attestations if attestations is not None else default_attestations()
    unapproved = make_manifest(attestations)
    approval_fields: dict[str, Any] = {"subject_digest": unapproved.approval_subject_digest()}
    approval_fields.update(approval_overrides)
    approval = make_approval(**approval_fields)
    manifest = make_manifest(attestations, approvals=[approval])
    assert manifest.approval_subject_digest() == unapproved.approval_subject_digest()
    return manifest, list(attestations.values()), [approval]


def run_release(
    manifest: ReleaseManifest, attestations: list[VerificationAttestation], approvals: list[ApprovalRecord], **kwargs: Any
) -> Any:
    options: dict[str, Any] = {"now": NOW, "current_policy_version": POLICY}
    options.update(kwargs)
    return check_release(manifest, attestations, approvals, **options)


# ---------------------------------------------------------------------------
# ApprovalRecord
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-040", "PL-041")
def test_approval_binds_and_is_valid_only_inside_its_window() -> None:
    approval = make_approval()
    assert approval.kind is ArtifactKind.APPROVAL_RECORD
    assert approval.is_valid_at(T0)
    assert approval.is_valid_at(T0 + timedelta(days=29))
    assert not approval.is_valid_at(T0 - timedelta(seconds=1))
    assert not approval.is_valid_at(T0 + timedelta(days=30))
    revoked = make_approval(revoked_at=T0 + timedelta(days=2))
    assert revoked.is_valid_at(T0 + timedelta(days=1))
    assert not revoked.is_valid_at(T0 + timedelta(days=2))
    assert ApprovalRecord.model_validate(approval.model_dump(mode="json")) == approval


@pytest.mark.requirements("PL-040")
def test_approval_rejects_naive_instant() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        make_approval().is_valid_at(datetime(2026, 10, 1, 13, 0))


@pytest.mark.requirements("PL-040")
@pytest.mark.parametrize("approver", [BUILD_AGENT, RUNTIME_AGENT, APPROVAL_SERVICE, VERIFIER])
def test_agent_supplied_approval_is_rejected(approver: Principal) -> None:
    rejects(make_approval, "approver must be a human principal", approver=approver)


@pytest.mark.requirements("PL-040")
@pytest.mark.parametrize("producer", [BUILD_AGENT, RUNTIME_AGENT])
def test_approval_produced_by_agent_is_rejected(producer: Principal) -> None:
    rejects(make_approval, "cannot be produced by a build or runtime agent", producer=producer)


@pytest.mark.requirements("PL-040")
def test_approval_temporal_bindings() -> None:
    rejects(make_approval, "expires_at must be after approved_at", expires_at=T0)
    rejects(make_approval, "revoked_at cannot precede approved_at", revoked_at=T0 - timedelta(days=1))


@pytest.mark.requirements("PL-040", "PL-041")
def test_case_level_approval_requires_case_version() -> None:
    rejects(make_approval, "case_version is required", decision_kind=DecisionKind.CASE_LEVEL_BUSINESS)
    approval = make_approval(decision_kind=DecisionKind.CASE_LEVEL_BUSINESS, case_version=3)
    assert approval.case_version == 3


@pytest.mark.requirements("PL-040")
def test_approval_scope_tenant_must_match_tenant() -> None:
    rejects(make_approval, "scope_tenant .* must equal tenant_id", scope_tenant=OTHER_TENANT)


@pytest.mark.requirements("PL-040")
def test_approval_decision_ref_must_not_be_a_secret_and_extra_fields_are_rejected() -> None:
    rejects(make_approval, "looks like a secret", authenticated_decision_ref="session token=abc123")
    rejects(make_approval, "looks like a secret", authenticated_decision_ref="Zm9vYmFyMTIzNDU2Nzg5MGFiY2RlZmdoaWprbG1ub3BxcnN0dXZ3eHl6QUJD")
    rejects(make_approval, "extra_forbidden|Extra inputs", approved_by_agent=True)


# ---------------------------------------------------------------------------
# check_approval
# ---------------------------------------------------------------------------


def judge(approval: ApprovalRecord, **overrides: Any) -> Any:
    options: dict[str, Any] = {
        "subject_digest": SUBJECT_DIGEST,
        "tenant_id": TENANT,
        "policy_version": POLICY,
        "now": NOW,
    }
    options.update(overrides)
    return check_approval(approval, **options)


@pytest.mark.requirements("PL-040")
def test_valid_approval_passes_check() -> None:
    report = judge(make_approval())
    assert report.ok, report.render()
    assert report.findings == []
    assert report.checker == APPROVAL_CHECKER
    assert report.subject == "apr_release_001"
    assert report.summary["valid"] is True
    assert report.summary["approver"] == OWNER.principal_id


@pytest.mark.requirements("PL-040")
def test_approval_for_different_digest() -> None:
    report = judge(make_approval(), subject_digest=digest("other-bytes"))
    [finding] = only(report.findings, "APPROVAL_DIGEST_MISMATCH")
    assert finding.error_class is ErrorClass.SCOPE_DENIED
    assert finding.severity is Severity.ERROR
    assert report.codes() == {"APPROVAL_DIGEST_MISMATCH"}
    assert report.summary["valid"] is False


@pytest.mark.requirements("PL-040")
def test_approval_for_different_tenant() -> None:
    report = judge(make_approval(), tenant_id=OTHER_TENANT)
    [finding] = only(report.findings, "APPROVAL_TENANT_MISMATCH")
    assert finding.error_class is ErrorClass.SCOPE_DENIED
    assert finding.details["requested_tenant"] == OTHER_TENANT


@pytest.mark.requirements("PL-040")
def test_approval_under_stale_policy() -> None:
    report = judge(make_approval(), policy_version="1.5.0")
    [finding] = only(report.findings, "APPROVAL_POLICY_STALE")
    assert finding.error_class is ErrorClass.POLICY_STALE


@pytest.mark.requirements("PL-040")
def test_case_level_approval_binds_to_one_case_version() -> None:
    approval = make_approval(decision_kind=DecisionKind.CASE_LEVEL_BUSINESS, case_version=3)
    assert judge(approval, case_version=3).ok
    report = judge(approval, case_version=4)
    [finding] = only(report.findings, "APPROVAL_CASE_VERSION_MISMATCH")
    assert finding.error_class is ErrorClass.STATE_CONFLICT
    assert judge(approval).has("APPROVAL_CASE_VERSION_MISMATCH")
    assert judge(make_approval(), case_version=4).ok


@pytest.mark.requirements("PL-040", "PL-041")
def test_expired_revoked_and_not_yet_effective_approvals() -> None:
    expired = judge(make_approval(), now=T0 + timedelta(days=30))
    [finding] = only(expired.findings, "APPROVAL_EXPIRED")
    assert finding.error_class is ErrorClass.POLICY_STALE
    revoked = judge(make_approval(revoked_at=T0 + timedelta(hours=1)))
    [finding] = only(revoked.findings, "APPROVAL_REVOKED")
    assert finding.error_class is ErrorClass.POLICY_STALE
    assert revoked.codes() == {"APPROVAL_REVOKED"}
    early = judge(make_approval(), now=T0 - timedelta(minutes=1))
    [finding] = only(early.findings, "APPROVAL_NOT_YET_EFFECTIVE")
    assert finding.error_class is ErrorClass.STATE_CONFLICT
    with pytest.raises(ValueError, match="timezone-aware"):
        judge(make_approval(), now=datetime(2026, 10, 1, 14, 0))


@pytest.mark.requirements("PL-040")
def test_checker_rejects_non_human_approver_even_when_validation_was_bypassed() -> None:
    forged = bypass_validation(make_approval(), approver=BUILD_AGENT)
    report = judge(forged)
    [finding] = only(report.findings, "APPROVAL_NOT_HUMAN")
    assert finding.error_class is ErrorClass.AUTH_REQUIRED
    assert finding.details["approver_type"] == "BUILD_AGENT"


def dependency(dependency_id: str, resolver: PrincipalType, error_class: ErrorClass, steps: list[str], authority: list[str], minutes: int) -> DependencyRecord:
    return DependencyRecord(
        dependency_id=dependency_id,
        failure_class=FailureClass.MISSING_AUTHORIZATION,
        error_class=error_class,
        description=f"{dependency_id} needs {', '.join(authority)}",
        missing_authority=authority,
        resolver_role=resolver,
        blocked_step_ids=steps,
        resumes_after="collector deploy continues",
        raised_at=T0 + timedelta(minutes=minutes),
    )


@pytest.mark.requirements("PL-041")
def test_group_missing_authorizations_groups_by_resolver_and_error_class() -> None:
    dependencies = [
        dependency("dep_mailbox_read", PrincipalType.HUMAN_OWNER, ErrorClass.PURPOSE_DENIED, ["step_collect"], ["COLLECT on src_mailbox"], 5),
        dependency("dep_ledger_read", PrincipalType.HUMAN_OWNER, ErrorClass.PURPOSE_DENIED, ["step_collect", "step_reconcile"], ["COLLECT on src_ledger", "COLLECT on src_mailbox"], 2),
        dependency("dep_posting_signoff", PrincipalType.HUMAN_REVIEWER, ErrorClass.AUTH_REQUIRED, ["step_write"], ["case-level sign-off"], 9),
    ]
    requests = group_missing_authorizations(dependencies)
    assert len(requests) == 2
    owner_request, reviewer_request = requests
    assert owner_request["resolver_role"] == "HUMAN_OWNER"
    assert owner_request["error_class"] == "PURPOSE_DENIED"
    assert owner_request["dependency_ids"] == ["dep_ledger_read", "dep_mailbox_read"]
    assert owner_request["missing_authority"] == ["COLLECT on src_ledger", "COLLECT on src_mailbox"]
    assert owner_request["blocked_step_ids"] == ["step_collect", "step_reconcile"]
    assert owner_request["first_raised_at"].startswith("2026-10-01T12:02")
    assert reviewer_request["resolver_role"] == "HUMAN_REVIEWER"
    assert reviewer_request["blocked_step_ids"] == ["step_write"]
    assert group_missing_authorizations([]) == []


# ---------------------------------------------------------------------------
# VerificationAttestation
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-042", "PL-043")
def test_attestation_positive_path() -> None:
    attestation = make_attestation(digest("adapter"))
    assert attestation.kind is ArtifactKind.VERIFICATION_ATTESTATION
    assert attestation.result is AttestationResult.PASS
    assert [check.name for check in attestation.passed_checks()] == ["contract_tests"]
    failed = make_attestation(
        digest("adapter"),
        checks=[make_check(), make_check("rate_limiting", result=CheckOutcome.FAIL, evidence_refs=(), detail="429 not retried")],
        result=AttestationResult.FAIL,
    )
    assert failed.result is AttestationResult.FAIL
    assert VerificationAttestation.model_validate(attestation.model_dump(mode="json")) == attestation


@pytest.mark.requirements("PL-042")
@pytest.mark.parametrize("verifier", [BUILD_AGENT, APPROVAL_SERVICE, OWNER])
def test_verifier_must_be_a_verifier_principal(verifier: Principal) -> None:
    rejects(make_attestation, "verifier must be a VERIFIER principal", input_digest=digest("x"), verifier=verifier)


@pytest.mark.requirements("PL-042")
def test_verifier_equal_to_assessed_producer_is_rejected() -> None:
    self_assessing = Principal(principal_id=BUILD_AGENT.principal_id, principal_type=PrincipalType.VERIFIER, authenticated_via="mtls:verifier")
    rejects(make_attestation, "verifier must not be the principal it assesses", input_digest=digest("x"), verifier=self_assessing)
    rejects(make_attestation, "cannot be produced by the job it assesses", input_digest=digest("x"), producer=BUILD_AGENT)


@pytest.mark.requirements("PL-042")
def test_pass_check_requires_evidence_and_skipped_requires_detail() -> None:
    with pytest.raises(ValidationError, match="PASS without evidence"):
        make_check(evidence_refs=())
    with pytest.raises(ValidationError, match="SKIPPED without a detail"):
        make_check(result=CheckOutcome.SKIPPED, evidence_refs=())
    skipped = make_check(result=CheckOutcome.SKIPPED, evidence_refs=(), detail="no write path in this release")
    assert skipped.result is CheckOutcome.SKIPPED
    with pytest.raises(ValidationError, match="looks like a secret"):
        make_check(evidence_refs=("password=hunter2",))


@pytest.mark.requirements("PL-042", "PL-043")
def test_attestation_result_must_reflect_its_checks() -> None:
    failing = [make_check(), make_check("duplicates", result=CheckOutcome.FAIL, evidence_refs=(), detail="dup rows")]
    rejects(make_attestation, "result must be FAIL when any check failed", input_digest=digest("x"), checks=failing)
    rejects(make_attestation, "at least 1 item", input_digest=digest("x"), checks=[])
    rejects(make_attestation, "check names must be unique", input_digest=digest("x"), checks=[make_check(), make_check()])
    only_skipped = [make_check(result=CheckOutcome.SKIPPED, evidence_refs=(), detail="not run")]
    rejects(make_attestation, "needs at least one passing check at that level", input_digest=digest("x"), checks=only_skipped)


@pytest.mark.requirements("PL-042", "PL-044")
def test_attestation_identifies_the_protected_bundle_by_digest() -> None:
    attestation = make_attestation(digest("workflow"))
    assert attestation.protected_bundle_digest == digest("protected-bundle-v3")
    rejects(make_attestation, "String should match pattern", input_digest=digest("x"), protected_bundle_digest="bundle:v3")
    rejects(make_attestation, "String should match pattern", input_digest=digest("x"), protected_bundle_digest="holdout rows: 1,2,3")


@pytest.mark.requirements("PL-043")
def test_unit_tests_cannot_establish_a_business_outcome() -> None:
    schema_only = [make_check("schema_valid", VerificationLevel.SCHEMA_VALIDITY)]
    rejects(
        make_attestation,
        "needs at least one passing check at that level",
        input_digest=digest("x"),
        level=VerificationLevel.BUSINESS_OUTCOME,
        checks=schema_only,
    )


# ---------------------------------------------------------------------------
# InfrastructurePlan
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-045")
def test_infrastructure_plan_positive_path() -> None:
    plan = make_plan()
    assert plan.kind is ArtifactKind.INFRASTRUCTURE_PLAN
    assert plan.destructive_changes() == []
    assert not plan.changes[0].is_destructive
    assert InfrastructurePlan.model_validate(plan.model_dump(mode="json")) == plan


@pytest.mark.requirements("PL-045", "PL-047")
@pytest.mark.parametrize(
    "change",
    [
        make_change(action=ChangeAction.DELETE),
        make_change(action=ChangeAction.REPLACE),
        make_change(rollback_classification=RollbackClassification.IRREVERSIBLE),
    ],
)
def test_destructive_change_requires_authorization_and_backup_strategy(change: ResourceChange) -> None:
    assert change.is_destructive
    rejects(make_plan, "destructive changes .* require explicit authorization", changes=[change])
    rejects(make_plan, "missing backup_restore_strategy_ref", changes=[change], destructive_authorization_ref="apr_destructive_001")
    rejects(make_plan, "missing destructive_authorization_ref", changes=[change], backup_restore_strategy_ref="bkp_snapshot_001")
    plan = make_plan(changes=[change], destructive_authorization_ref="apr_destructive_001", backup_restore_strategy_ref="bkp_snapshot_001")
    assert plan.destructive_changes() == [change]


@pytest.mark.requirements("PL-045")
def test_plan_must_come_from_templates_with_a_preview() -> None:
    rejects(make_plan, "at least 1 item", template_refs=[])
    rejects(make_plan, "must reference an InfrastructurePreview", preview_diff_ref=preview_ref(ArtifactKind.TEST_BUNDLE))


@pytest.mark.requirements("PL-045")
def test_plan_ownership_tags_cost_and_lock() -> None:
    with pytest.raises(ValidationError, match="at least 1 item"):
        make_change(ownership_tags={})
    rejects(make_plan, "is below the per-resource sum", cost_estimate=Money(minor_units=100, currency="USD"))
    rejects(make_plan, "estimated in EUR but the plan estimate is in USD", changes=[make_change(estimated_cost=Money(minor_units=1, currency="EUR"))])
    rejects(make_plan, "resource_id must be unique", changes=[make_change(), make_change()])
    rejects(make_plan, "looks like a secret", state_lock_ref="lock secret value")


# ---------------------------------------------------------------------------
# ReleaseManifest
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-034", "PL-046", "PL-047")
def test_release_manifest_positive_path() -> None:
    manifest = make_manifest()
    assert manifest.kind is ArtifactKind.RELEASE_MANIFEST
    assert set(manifest.components) == set(REQUIRED_COMPONENTS)
    assert sorted(manifest.present_components()) == sorted(COMPONENT_KINDS_FOR_FIXTURE)
    assert manifest.rollout_environments() == {ENVIRONMENT}
    assert manifest.in_flight_pinning is True
    assert ReleaseManifest.model_validate(manifest.model_dump(mode="json")) == manifest


@pytest.mark.requirements("PL-046")
def test_release_manifest_requires_every_component_key() -> None:
    components = make_components()
    del components["schema"]
    rejects(make_manifest, "missing: schema", components=components)


@pytest.mark.requirements("PL-046")
def test_release_component_is_a_ref_or_an_omission_never_both_or_neither() -> None:
    with pytest.raises(ValidationError, match="exactly one"):
        ReleaseComponent()
    with pytest.raises(ValidationError, match="exactly one"):
        ReleaseComponent(ref=component_ref("model"), omitted_reason="also omitted")
    components = make_components()
    components["model"] = ReleaseComponent(ref=component_ref("workflow"))
    rejects(make_manifest, "component 'model' references a WorkflowSpec", components=components)


@pytest.mark.requirements("PL-046")
def test_release_manifest_binds_evidence_by_kind_and_digest() -> None:
    attestation = component_attestation("connector")
    wrong_kind = ArtifactRef(artifact_id="att_x", kind=ArtifactKind.EVALUATION_REPORT, digest=digest("x"))
    rejects(make_manifest, "attestation_refs must reference VerificationAttestation", attestation_refs=[wrong_kind])
    rejects(make_manifest, "at least 1 item", attestation_refs=[])
    rejects(make_manifest, "must not reference the same digest twice", attestation_refs=[attestation_ref(attestation)] * 2)
    wrong_approval = ArtifactRef(artifact_id="apr_x", kind=ArtifactKind.VERIFICATION_ATTESTATION, digest=digest("y"))
    rejects(make_manifest, "approval_refs must reference ApprovalRecord", approval_refs=[wrong_approval])


@pytest.mark.requirements("PL-047")
def test_rollout_policy_is_ordered_and_canary_is_bounded() -> None:
    shadow, canary, active = rollout()
    rejects(make_manifest, "order SHADOW, CANARY, ACTIVE", rollout_policy=[canary, shadow, active])
    rejects(make_manifest, "order SHADOW, CANARY, ACTIVE", rollout_policy=[shadow, shadow])
    rejects(make_manifest, "order SHADOW, CANARY, ACTIVE", rollout_policy=[active, canary])
    with pytest.raises(ValidationError, match="canary is bounded"):
        RolloutStage(state=ReleaseState.CANARY, gate="g", environment=ENVIRONMENT, max_case_fraction=1.0)
    with pytest.raises(ValidationError, match="less than or equal to 1"):
        RolloutStage(state=ReleaseState.ACTIVE, gate="g", environment=ENVIRONMENT, max_case_fraction=1.5)
    with pytest.raises(ValidationError, match="Input should be"):
        RolloutStage(state=ReleaseState.PAUSED, gate="g", environment=ENVIRONMENT, max_case_fraction=0.5)
    assert make_manifest(rollout_policy=[shadow, active]).rollout_policy[-1].state is ReleaseState.ACTIVE


@pytest.mark.requirements("PL-034")
@pytest.mark.parametrize("alias", ["latest", "invoice-classifier:latest", "invoice-classifier@champion", "models/inv:prod", "invoice-classifier", "inv/versions/stable"])
def test_model_alias_is_rejected(alias: str) -> None:
    assert not is_immutable_model_version(alias)
    rejects(make_manifest, "not an immutable version reference", resolved_model_version=alias)


@pytest.mark.requirements("PL-034")
@pytest.mark.parametrize("version", ["invoice-classifier:12", "invoice-classifier:v3", "models/inv/versions/7", "inv@sha256:" + "a" * 64, "sha256:" + "b" * 64])
def test_immutable_model_versions_are_accepted(version: str) -> None:
    assert is_immutable_model_version(version)
    assert make_manifest(resolved_model_version=version).resolved_model_version == version


@pytest.mark.requirements("PL-034")
def test_resolved_model_version_tracks_the_model_component() -> None:
    rejects(make_manifest, "resolved_model_version is required", resolved_model_version=None)
    components = make_components()
    components["model"] = ReleaseComponent(omitted_reason="rule-based release, no model")
    rejects(make_manifest, "must be null when the model component is omitted", components=components)
    attestations = {key: value for key, value in default_attestations().items() if key != "model"}
    manifest = make_manifest(attestations, components=components, resolved_model_version=None)
    assert manifest.resolved_model_version is None


@pytest.mark.requirements("PL-047")
def test_in_flight_cases_stay_pinned() -> None:
    rejects(make_manifest, "in_flight_pinning must be true", in_flight_pinning=False)


@pytest.mark.requirements("PL-046")
def test_release_manifest_scalar_constraints() -> None:
    rejects(make_manifest, "at least 1 item", allowed_effect_classes=[])
    rejects(make_manifest, "must not contain duplicates", allowed_effect_classes=[EffectClass.READ, EffectClass.READ])
    rejects(make_manifest, "greater than or equal to 1", denominators={"cases": 0})
    rejects(make_manifest, "less than or equal to 1", review_thresholds={"confidence_floor": 1.5})


# ---------------------------------------------------------------------------
# check_release
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-034", "PL-040", "PL-042", "PL-043", "PL-046", "PL-047")
def test_release_positive_path_lists_verified_components() -> None:
    manifest, attestations, approvals = release_world()
    report = run_release(manifest, attestations, approvals)
    assert report.ok, report.render()
    assert report.findings == []
    assert report.checker == RELEASE_CHECKER
    assert report.subject == "rel_demo_001"
    assert report.summary["verified_components"] == sorted(COMPONENT_KINDS_FOR_FIXTURE)
    assert report.summary["unverified_components"] == []
    assert report.summary["omitted_components"] == sorted(OMITTED)
    assert report.summary["verification_levels"] == ["ARTIFACT_INTEGRITY", "BUSINESS_OUTCOME", "INTEGRATION_BEHAVIOR"]
    assert report.summary["approvals_checked"] == 1
    assert report.summary["approvals_valid"] == 1
    assert report.summary["unreferenced_attestations"] == []


@pytest.mark.requirements("PL-046")
def test_attestation_for_different_bytes_is_rejected() -> None:
    attestations = default_attestations()
    attestations["connector"] = component_attestation("connector", input_artifact_digest=digest("connector-bytes-before-last-patch"))
    manifest, supplied, approvals = release_world(attestations)
    report = run_release(manifest, supplied, approvals)
    assert not report.ok
    [mismatch] = only(report.findings, "ATTESTATION_DIGEST_MISMATCH")
    assert mismatch.error_class is ErrorClass.VERIFICATION_FAILED
    assert mismatch.subject_id == "att_connector_001"
    assert mismatch.details["reason"] == "different_bytes"
    [missing] = only(report.findings, "ATTESTATION_MISSING")
    assert missing.subject_id == "connector"
    assert report.summary["unverified_components"] == ["connector"]


@pytest.mark.requirements("PL-046")
def test_attestation_ref_without_a_matching_record_is_rejected() -> None:
    manifest, attestations, approvals = release_world()
    dangling = ArtifactRef(artifact_id="att_ghost", kind=ArtifactKind.VERIFICATION_ATTESTATION, digest=digest("ghost"))
    manifest = make_manifest(approvals=approvals, attestation_refs=[*manifest.attestation_refs, dangling])
    report = run_release(manifest, attestations, approvals)
    [finding] = only(report.findings, "ATTESTATION_DIGEST_MISMATCH")
    assert finding.subject_id == "att_ghost"
    assert finding.details["reason"] == "attestation_not_supplied"


@pytest.mark.requirements("PL-046", "PL-043")
def test_attestation_from_different_environment_is_rejected() -> None:
    attestations = default_attestations()
    attestations["workflow"] = component_attestation("workflow", environment="developer-laptop")
    manifest, supplied, approvals = release_world(attestations)
    report = run_release(manifest, supplied, approvals)
    [scope] = only(report.findings, "ATTESTATION_SCOPE_MISMATCH")
    assert scope.error_class is ErrorClass.VERIFICATION_FAILED
    assert scope.details["environment"] == "developer-laptop"
    assert scope.details["rollout_environments"] == [ENVIRONMENT]
    assert only(report.findings, "ATTESTATION_MISSING")[0].subject_id == "workflow"
    [level] = only(report.findings, "MISSING_VERIFICATION_LEVEL")
    assert level.details["level"] == "BUSINESS_OUTCOME"
    assert report.has("ADVERSARIAL_TESTS_MISSING")


@pytest.mark.requirements("PL-046")
def test_attestation_for_different_tenant_or_narrower_scope_is_rejected() -> None:
    attestations = default_attestations()
    attestations["collector"] = component_attestation("collector", tenant_id=OTHER_TENANT)
    attestations["model"] = component_attestation("model", scope=ResourceScope(source_ids=["src_other_ledger"]))
    manifest, supplied, approvals = release_world(attestations)
    report = run_release(manifest, supplied, approvals)
    findings = {finding.subject_id: finding for finding in only(report.findings, "ATTESTATION_SCOPE_MISMATCH")}
    assert set(findings) == {"att_collector_001", "att_model_001"}
    assert any("tenant" in problem for problem in findings["att_collector_001"].details["problems"])
    assert any("src_demo_ledger" in problem for problem in findings["att_model_001"].details["problems"])


@pytest.mark.requirements("PL-042", "PL-046")
def test_failed_attestation_blocks_release() -> None:
    attestations = default_attestations()
    attestations["connector"] = component_attestation(
        "connector",
        checks=[make_check("connector_checks"), make_check("rate_limiting", result=CheckOutcome.FAIL, evidence_refs=(), detail="429 not retried")],
        result=AttestationResult.FAIL,
    )
    manifest, supplied, approvals = release_world(attestations)
    report = run_release(manifest, supplied, approvals)
    [finding] = only(report.findings, "ATTESTATION_FAILED")
    assert finding.subject_id == "att_connector_001"
    assert "rate_limiting" in finding.message
    assert only(report.findings, "ATTESTATION_MISSING")[0].subject_id == "connector"


@pytest.mark.requirements("PL-043")
def test_missing_business_outcome_attestation_is_flagged() -> None:
    attestations = default_attestations()
    attestations["workflow"] = component_attestation(
        "workflow",
        level=VerificationLevel.INTEGRATION_BEHAVIOR,
        checks=[make_check("workflow_integration"), make_check("adversarial_instructions", evidence_refs=("log:adv/1",))],
    )
    manifest, supplied, approvals = release_world(attestations)
    report = run_release(manifest, supplied, approvals)
    assert not report.ok
    [finding] = only(report.findings, "MISSING_VERIFICATION_LEVEL")
    assert finding.error_class is ErrorClass.VERIFICATION_FAILED
    assert finding.details["level"] == "BUSINESS_OUTCOME"
    assert report.summary["verified_components"] == sorted(COMPONENT_KINDS_FOR_FIXTURE)
    assert not report.has("ADVERSARIAL_TESTS_MISSING")


@pytest.mark.requirements("PL-043")
def test_only_unit_level_attestations_miss_both_required_levels() -> None:
    attestations = {
        key: component_attestation(key, level=VerificationLevel.SCHEMA_VALIDITY, checks=[make_check(f"{key}_schema", VerificationLevel.SCHEMA_VALIDITY)])
        for key in COMPONENT_KINDS_FOR_FIXTURE
    }
    manifest, supplied, approvals = release_world(attestations)
    report = run_release(manifest, supplied, approvals)
    levels = sorted(finding.details["level"] for finding in only(report.findings, "MISSING_VERIFICATION_LEVEL"))
    assert levels == ["BUSINESS_OUTCOME", "INTEGRATION_BEHAVIOR"]
    assert report.summary["verified_components"] == sorted(COMPONENT_KINDS_FOR_FIXTURE)


@pytest.mark.requirements("PL-043", "PL-061")
def test_missing_adversarial_tests_is_a_warning_not_a_block() -> None:
    attestations = default_attestations()
    attestations["workflow"] = component_attestation(
        "workflow", checks=[make_check("business_scenarios", VerificationLevel.BUSINESS_OUTCOME, evidence_refs=("receipt:cases/42",))]
    )
    manifest, supplied, approvals = release_world(attestations)
    report = run_release(manifest, supplied, approvals)
    assert report.ok
    [finding] = only(report.findings, "ADVERSARIAL_TESTS_MISSING")
    assert finding.severity is Severity.WARNING
    assert finding.error_class is ErrorClass.VERIFICATION_FAILED
    assert report.warnings == [finding]


@pytest.mark.requirements("PL-040", "PL-041")
def test_stale_or_expired_approval_invalidates_release() -> None:
    manifest, attestations, approvals = release_world(expires_at=NOW - timedelta(minutes=1))
    report = run_release(manifest, attestations, approvals)
    [finding] = only(report.findings, "APPROVAL_INVALID")
    assert finding.error_class is ErrorClass.POLICY_STALE
    assert finding.details["cause"] == "APPROVAL_EXPIRED"
    assert report.summary["approvals_valid"] == 0
    manifest, attestations, approvals = release_world()
    stale = run_release(manifest, attestations, approvals, current_policy_version="1.5.0")
    assert [finding.details["cause"] for finding in only(stale.findings, "APPROVAL_INVALID")] == ["APPROVAL_POLICY_STALE"]


@pytest.mark.requirements("PL-040")
def test_approval_for_different_digest_or_tenant_does_not_authorize_release() -> None:
    manifest, attestations, approvals = release_world(subject_digest=digest("some-other-release"))
    report = run_release(manifest, attestations, approvals)
    [finding] = only(report.findings, "APPROVAL_INVALID")
    assert finding.error_class is ErrorClass.SCOPE_DENIED
    assert finding.details["cause"] == "APPROVAL_DIGEST_MISMATCH"
    manifest, attestations, approvals = release_world(tenant_id=OTHER_TENANT, scope_tenant=OTHER_TENANT)
    report = run_release(manifest, attestations, approvals)
    assert {finding.details["cause"] for finding in only(report.findings, "APPROVAL_INVALID")} == {"APPROVAL_TENANT_MISMATCH"}


@pytest.mark.requirements("PL-040")
def test_approval_ref_without_record_is_invalid() -> None:
    manifest, attestations, approvals = release_world()
    report = run_release(manifest, attestations, [])
    [finding] = only(report.findings, "APPROVAL_INVALID")
    assert finding.error_class is ErrorClass.AUTH_REQUIRED
    assert finding.details["cause"] == "approval_record_not_supplied"
    assert finding.subject_id == approvals[0].artifact_id


@pytest.mark.requirements("PL-034")
def test_model_alias_is_flagged_even_when_validation_was_bypassed() -> None:
    manifest, attestations, approvals = release_world()
    forged = bypass_validation(manifest, resolved_model_version="latest")
    report = run_release(forged, attestations, approvals)
    [finding] = only(report.findings, "MODEL_ALIAS_UNRESOLVED")
    assert finding.error_class is ErrorClass.STATE_CONFLICT
    assert finding.subject_id == "model"
    assert finding.details["resolved_model_version"] == "latest"


@pytest.mark.requirements("PL-046")
def test_unreferenced_attestations_are_not_evidence() -> None:
    attestations = default_attestations()
    stray = component_attestation("connector", artifact_id="att_connector_stray", environment="other-env")
    manifest, supplied, approvals = release_world(attestations)
    report = run_release(manifest, [*supplied, stray], approvals)
    assert report.ok, report.render()
    assert report.summary["unreferenced_attestations"] == ["att_connector_stray"]
    with pytest.raises(ValueError, match="timezone-aware"):
        run_release(manifest, supplied, approvals, now=datetime(2026, 10, 1, 14, 0))
