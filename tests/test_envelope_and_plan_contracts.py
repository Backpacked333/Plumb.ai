"""Contract tests: AutonomyEnvelope, CapabilityRecord, BuildPlan and the capability registry.

Exercises PL-005, PL-007, PL-008, PL-014, PL-015, PL-016, PL-018, PL-040,
PL-053 and PL-058 with synthetic fixtures only. Each MUST / MUST NOT rule has a
negative test proving the contract rejects the violation.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from plumb.contracts.build_plan import (
    DEPENDENCY_RAISE_STEP_TYPE,
    EXTERNAL_EFFECT_CLASSES,
    STEP_TYPE_VOCABULARY,
    BuildPlan,
    BuildStep,
    StepInput,
    StepOutput,
    VerificationObligation,
)
from plumb.contracts.capability import (
    EVIDENCE_BACKED_MATURITIES,
    PLATFORM_TENANT_ID,
    CapabilityRecord,
    MaintenanceBurden,
)
from plumb.contracts.common import (
    ArtifactKind,
    ArtifactRef,
    Budget,
    CapabilityMaturity,
    DataPurpose,
    EffectClass,
    Money,
    Principal,
    PrincipalType,
    ResourceScope,
    VerificationLevel,
    compute_artifact_digest,
)
from plumb.contracts.envelope import AutonomyEnvelope, Goal, SourceGrant
from plumb.registry.registry import (
    DEFAULT_REGISTRY_PATH,
    CapabilityRegistry,
    RegistryError,
    load_registry,
)

T0 = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
DAY = timedelta(days=1)
TENANT = "tnt_synthetic01"
DIGEST = "sha256:" + "ab" * 32
SOURCE = "src-bookkeeping"
OTHER_SOURCE = "src-mailbox"


# ---------------------------------------------------------------------------
# Synthetic builders
# ---------------------------------------------------------------------------


def _principal(
    principal_id: str = "owner-01", principal_type: PrincipalType = PrincipalType.HUMAN_OWNER
) -> Principal:
    return Principal(principal_id=principal_id, principal_type=principal_type, authenticated_via="oidc:test-issuer")


def _grant(**overrides: Any) -> SourceGrant:
    data: dict[str, Any] = {
        "source_id": SOURCE,
        "purposes": [DataPurpose.INSPECT, DataPurpose.COLLECT],
        "granted_by": _principal(),
        "granted_at": T0 - DAY,
        "expires_at": None,
        "policy_version": "1.0.0",
    }
    data.update(overrides)
    return SourceGrant(**data)


def _envelope(**overrides: Any) -> AutonomyEnvelope:
    data: dict[str, Any] = {
        "artifact_id": "env-synthetic",
        "tenant_id": TENANT,
        "version": 1,
        "producer": _principal(),
        "created_at": T0,
        "envelope_id": "env-synthetic",
        "envelope_version": 1,
        "owner": _principal(),
        "goals": [Goal(goal_id="goal-close-evidence", objective="Reduce duplicated evidence requests.")],
        "source_grants": [_grant()],
        "approved_destinations": ["dst-tenant-storage"],
        "approved_processors": ["proc-plumb-eu"],
        "allowed_effect_classes": [EffectClass.READ, EffectClass.INTERNAL_WRITE],
        "spending_limit": Money(minor_units=500_000, currency="USD"),
        "per_step_attempt_limit": 3,
        "deployment_environments": ["staging", "production"],
        "allowed_regions": ["eu-west-1"],
        "expires_at": T0 + 90 * DAY,
        "escalation_conditions": ["new processor requested"],
        "policy_version": "1.0.0",
        "revoked_at": None,
    }
    data.update(overrides)
    return AutonomyEnvelope(**data)


def _capability(**overrides: Any) -> CapabilityRecord:
    data: dict[str, Any] = {
        "artifact_id": "cap.test.probe",
        "tenant_id": PLATFORM_TENANT_ID,
        "version": 1,
        "producer": _principal("platform-registry", PrincipalType.SERVICE),
        "created_at": T0,
        "capability_id": "cap.test.probe",
        "step_type": "inventory.probe",
        "provider": "nango-management",
        "operation": "connection.describe_operations",
        "maturity": CapabilityMaturity.PRODUCTION_VERIFIED,
        "effect_classes": [EffectClass.READ],
        "required_purposes": [DataPurpose.INSPECT],
        "required_authority": ["source_grant:INSPECT"],
        "tested_environment": "sandbox:plumb-staging/2026-09",
        "failure_modes": ["rate_limited"],
        "maintenance_burden": MaintenanceBurden.LOW,
        "produces": [ArtifactKind.ENVIRONMENT_INVENTORY],
        "consumes": [ArtifactKind.AUTONOMY_ENVELOPE],
        "probe_receipt_ref": "probe:platform/nango-management/describe/2026-09-15",
        "capability_version": "1.0.0",
    }
    data.update(overrides)
    return CapabilityRecord(**data)


def _budget(minor_units: int = 10_000, currency: str = "USD", **overrides: Any) -> Budget:
    data: dict[str, Any] = {
        "spend": Money(minor_units=minor_units, currency=currency),
        "max_attempts": 3,
        "max_elapsed_seconds": 3600,
    }
    data.update(overrides)
    return Budget(**data)


def _verification() -> VerificationObligation:
    return VerificationObligation(
        check="probe_receipt", level=VerificationLevel.ARTIFACT_INTEGRITY, description="Receipt present."
    )


def _step(**overrides: Any) -> BuildStep:
    data: dict[str, Any] = {
        "step_id": "probe-sources",
        "step_type": "inventory.probe",
        "description": "Probe the authorized bookkeeping account.",
        "depends_on": [],
        "inputs": [StepInput(name="envelope", kind=ArtifactKind.AUTONOMY_ENVELOPE, plan_input="env-synthetic")],
        "outputs": [StepOutput(name="inventory", kind=ArtifactKind.ENVIRONMENT_INVENTORY)],
        "required_capabilities": ["cap.inventory.probe.management-api"],
        "effect_class": EffectClass.READ,
        "purposes": [DataPurpose.INSPECT],
        "scope": ResourceScope(source_ids=[SOURCE], destination_ids=["dst-tenant-storage"], regions=["eu-west-1"]),
        "budget": _budget(),
        "verification": [_verification()],
    }
    data.update(overrides)
    return BuildStep(**data)


def _plan(**overrides: Any) -> BuildPlan:
    data: dict[str, Any] = {
        "artifact_id": "plan-synthetic",
        "tenant_id": TENANT,
        "version": 1,
        "producer": _principal("planner", PrincipalType.BUILD_AGENT),
        "created_at": T0,
        "plan_id": "plan-synthetic",
        "goal_id": "goal-close-evidence",
        "opportunity_ref": None,
        "envelope_id": "env-synthetic",
        "envelope_version": 1,
        "inputs": [ArtifactRef(artifact_id="env-synthetic", kind=ArtifactKind.AUTONOMY_ENVELOPE, digest=DIGEST)],
        "steps": [_step()],
        "total_budget": _budget(minor_units=100_000),
        "planned_at": T0,
    }
    data.update(overrides)
    return BuildPlan(**data)


def _roundtrip(model: Any) -> Any:
    return type(model).model_validate(model.model_dump(mode="json"))


# ---------------------------------------------------------------------------
# AutonomyEnvelope
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-005", "PL-040")
def test_envelope_constructs_and_round_trips() -> None:
    envelope = _envelope()
    assert envelope.kind is ArtifactKind.AUTONOMY_ENVELOPE
    dumped = envelope.model_dump(mode="json")
    assert dumped["kind"] == "AutonomyEnvelope"
    assert dumped["expires_at"].endswith("Z")
    assert AutonomyEnvelope.model_validate(dumped) == envelope


@pytest.mark.requirements("PL-005")
def test_envelope_kind_is_pinned_and_extra_fields_forbidden() -> None:
    dumped = _envelope().model_dump(mode="json")
    with pytest.raises(ValidationError):
        AutonomyEnvelope.model_validate({**dumped, "kind": "BuildPlan"})
    with pytest.raises(ValidationError):
        AutonomyEnvelope.model_validate({**dumped, "admin_override": True})


@pytest.mark.requirements("PL-005")
@pytest.mark.parametrize(
    "principal_type",
    [t for t in PrincipalType if t is not PrincipalType.HUMAN_OWNER],
)
def test_envelope_owner_must_be_human_owner(principal_type: PrincipalType) -> None:
    with pytest.raises(ValidationError, match="HUMAN_OWNER"):
        _envelope(owner=_principal("not-owner", principal_type))


@pytest.mark.requirements("PL-005")
def test_envelope_spending_limit_must_be_positive() -> None:
    with pytest.raises(ValidationError, match="spending_limit"):
        _envelope(spending_limit=Money(minor_units=0, currency="USD"))


@pytest.mark.requirements("PL-005", "PL-040")
def test_envelope_expiry_must_follow_creation() -> None:
    with pytest.raises(ValidationError, match="expires_at"):
        _envelope(expires_at=T0)
    with pytest.raises(ValidationError, match="expires_at"):
        _envelope(expires_at=T0 - DAY)
    with pytest.raises(ValidationError, match="revoked_at"):
        _envelope(revoked_at=T0 - DAY)


@pytest.mark.requirements("PL-005")
def test_envelope_requires_effect_classes_without_duplicates() -> None:
    with pytest.raises(ValidationError):
        _envelope(allowed_effect_classes=[])
    with pytest.raises(ValidationError, match="duplicates"):
        _envelope(allowed_effect_classes=[EffectClass.READ, EffectClass.READ])


@pytest.mark.requirements("PL-005")
def test_envelope_id_must_equal_artifact_id() -> None:
    with pytest.raises(ValidationError, match="envelope_id"):
        _envelope(envelope_id="env-other")


@pytest.mark.requirements("PL-005")
def test_envelope_requires_goals_and_unique_lists() -> None:
    with pytest.raises(ValidationError):
        _envelope(goals=[])
    goal = Goal(goal_id="g", objective="x")
    with pytest.raises(ValidationError, match="goal_id"):
        _envelope(goals=[goal, goal])
    with pytest.raises(ValidationError, match="approved_destinations"):
        _envelope(approved_destinations=["dst-a", "dst-a"])
    with pytest.raises(ValidationError):
        _envelope(envelope_version=0)


@pytest.mark.requirements("PL-005")
def test_envelope_rejects_naive_timestamps() -> None:
    with pytest.raises(ValidationError):
        _envelope(expires_at=datetime(2027, 1, 1))
    with pytest.raises(ValidationError, match="timezone"):
        _envelope(created_at=datetime(2026, 10, 1, 12, 0))


@pytest.mark.requirements("PL-005", "PL-040")
def test_is_active_respects_expiry_and_revocation() -> None:
    envelope = _envelope()
    assert envelope.is_active(T0)
    assert envelope.is_active(T0 + 89 * DAY)
    assert not envelope.is_active(T0 + 90 * DAY), "expiry instant is exclusive"
    assert not envelope.is_active(T0 + 91 * DAY)
    assert not envelope.is_active(T0 - DAY), "not yet issued"

    # Revocation is an event that has happened (section 17: it invalidates cached grants and
    # queued dispatches): any revoked_at makes the envelope inactive at every instant, which is
    # exactly how the plan checker's ENVELOPE_INACTIVE rule reads it.
    revoked = _envelope(revoked_at=T0 + 10 * DAY)
    assert not revoked.is_active(T0 + 9 * DAY)
    assert not revoked.is_active(T0 + 10 * DAY)
    assert not revoked.is_active(T0 + 30 * DAY)

    with pytest.raises(ValueError, match="timezone-aware"):
        envelope.is_active(datetime(2026, 10, 2))


@pytest.mark.requirements("PL-005")
def test_scope_reflects_grants_and_approved_lists() -> None:
    envelope = _envelope(
        source_grants=[
            _grant(),
            _grant(purposes=[DataPurpose.TRAIN]),
            _grant(source_id=OTHER_SOURCE, purposes=[DataPurpose.INSPECT]),
        ]
    )
    scope = envelope.scope()
    assert scope.source_ids == [SOURCE, OTHER_SOURCE], "sources deduplicated, order preserved"
    assert scope.destination_ids == ["dst-tenant-storage"]
    assert scope.processor_ids == ["proc-plumb-eu"]
    assert scope.regions == ["eu-west-1"]
    wider = ResourceScope(source_ids=[SOURCE, "src-payroll"], processor_ids=["proc-other"])
    assert wider.is_within(scope) == [
        "source_ids not in scope: src-payroll",
        "processor_ids not in scope: proc-other",
    ]


@pytest.mark.requirements("PL-005", "PL-053")
def test_scope_and_purposes_exclude_grants_expired_at_evaluation_time() -> None:
    envelope = _envelope(source_grants=[_grant(expires_at=T0 + 10 * DAY)])
    assert envelope.scope().source_ids == [SOURCE], "default evaluation time is the envelope's issuance"
    assert envelope.purposes_for(SOURCE) == {DataPurpose.INSPECT, DataPurpose.COLLECT}
    assert envelope.scope(now=T0 + 9 * DAY).source_ids == [SOURCE]
    assert envelope.scope(now=T0 + 10 * DAY).source_ids == []
    assert envelope.purposes_for(SOURCE, now=T0 + 20 * DAY) == set()
    assert envelope.active_grants(now=T0 + 20 * DAY) == []


@pytest.mark.requirements("PL-053")
def test_purposes_for_never_infers_train_from_read() -> None:
    envelope = _envelope(
        source_grants=[
            _grant(),
            _grant(source_id=OTHER_SOURCE, purposes=[DataPurpose.INSPECT, DataPurpose.TRAIN]),
        ]
    )
    assert envelope.purposes_for(SOURCE) == {DataPurpose.INSPECT, DataPurpose.COLLECT}
    assert DataPurpose.TRAIN not in envelope.purposes_for(SOURCE)
    assert envelope.purposes_for(OTHER_SOURCE) == {DataPurpose.INSPECT, DataPurpose.TRAIN}
    assert envelope.purposes_for("src-unknown") == set()


@pytest.mark.requirements("PL-005", "PL-053")
def test_source_grant_rejects_empty_duplicate_or_agent_grants() -> None:
    with pytest.raises(ValidationError):
        _grant(purposes=[])
    with pytest.raises(ValidationError, match="duplicates"):
        _grant(purposes=[DataPurpose.INSPECT, DataPurpose.INSPECT])
    with pytest.raises(ValidationError, match="expires_at"):
        _grant(expires_at=T0 - DAY)
    with pytest.raises(ValidationError, match="human principal"):
        _grant(granted_by=_principal("builder", PrincipalType.BUILD_AGENT))
    approver_grant = _grant(granted_by=_principal("approver", PrincipalType.HUMAN_APPROVER))
    assert approver_grant.is_active(T0)
    assert not approver_grant.is_active(T0 - 2 * DAY), "a grant is inactive before granted_at"


@pytest.mark.requirements("PL-005")
def test_envelope_rejects_grant_already_expired_at_issuance() -> None:
    with pytest.raises(ValidationError, match="already expired"):
        _envelope(source_grants=[_grant(granted_at=T0 - 2 * DAY, expires_at=T0 - DAY)])


# ---------------------------------------------------------------------------
# CapabilityRecord
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-007", "PL-008")
def test_capability_record_constructs_and_round_trips() -> None:
    record = _capability()
    assert record.kind is ArtifactKind.CAPABILITY_RECORD
    dumped = record.model_dump(mode="json")
    assert dumped["kind"] == "CapabilityRecord"
    assert dumped["maintenance_burden"] == "LOW"
    assert CapabilityRecord.model_validate(dumped) == record
    with pytest.raises(ValidationError):
        CapabilityRecord.model_validate({**dumped, "kind": "EnvironmentInventory"})
    with pytest.raises(ValidationError):
        CapabilityRecord.model_validate({**dumped, "logo_url": "https://example.invalid/logo.png"})


@pytest.mark.requirements("PL-008")
@pytest.mark.parametrize("maturity", sorted(EVIDENCE_BACKED_MATURITIES, key=lambda m: m.value))
def test_tested_maturity_requires_probe_receipt_and_environment(maturity: CapabilityMaturity) -> None:
    with pytest.raises(ValidationError, match="probe_receipt_ref"):
        _capability(maturity=maturity, probe_receipt_ref=None)
    with pytest.raises(ValidationError, match="tested_environment"):
        _capability(maturity=maturity, tested_environment=None)
    assert _capability(maturity=maturity).at_least(CapabilityMaturity.SANDBOX_TESTED)


@pytest.mark.requirements("PL-008")
@pytest.mark.parametrize("maturity", [CapabilityMaturity.DISCOVERED, CapabilityMaturity.DOCUMENTED])
def test_documented_capability_is_not_verified(maturity: CapabilityMaturity) -> None:
    record = _capability(maturity=maturity, probe_receipt_ref=None, tested_environment=None)
    assert record.probe_receipt_ref is None
    assert not record.at_least(CapabilityMaturity.SANDBOX_TESTED)
    assert not record.at_least(CapabilityMaturity.PRODUCTION_VERIFIED)
    assert record.at_least(maturity)


@pytest.mark.requirements("PL-008")
def test_maturity_order_is_total() -> None:
    ranks = [CapabilityMaturity.DISCOVERED, CapabilityMaturity.DOCUMENTED,
             CapabilityMaturity.SANDBOX_TESTED, CapabilityMaturity.PRODUCTION_VERIFIED]
    for i, maturity in enumerate(ranks):
        receipt = "probe:x" if maturity in EVIDENCE_BACKED_MATURITIES else None
        env = "sandbox:x" if maturity in EVIDENCE_BACKED_MATURITIES else None
        record = _capability(maturity=maturity, probe_receipt_ref=receipt, tested_environment=env)
        for j, minimum in enumerate(ranks):
            assert record.at_least(minimum) is (i >= j)


@pytest.mark.requirements("PL-007")
def test_capability_records_are_platform_level() -> None:
    with pytest.raises(ValidationError, match=PLATFORM_TENANT_ID):
        _capability(tenant_id=TENANT)


@pytest.mark.requirements("PL-008")
@pytest.mark.parametrize("value", ["probe:secret-store/abc", "probe:password/abc", "probe:api-secret"])
def test_probe_receipt_ref_rejects_secret_like_values(value: str) -> None:
    with pytest.raises(ValidationError, match="secret"):
        _capability(probe_receipt_ref=value)


@pytest.mark.requirements("PL-007")
def test_capability_effect_classes_required_and_lists_unique() -> None:
    with pytest.raises(ValidationError):
        _capability(effect_classes=[])
    with pytest.raises(ValidationError, match="effect_classes"):
        _capability(effect_classes=[EffectClass.READ, EffectClass.READ])
    with pytest.raises(ValidationError, match="produces"):
        _capability(produces=[ArtifactKind.PROBE_RECEIPT, ArtifactKind.PROBE_RECEIPT])
    with pytest.raises(ValidationError, match="required_authority"):
        _capability(required_authority=["a", "a"])


@pytest.mark.requirements("PL-007")
def test_maintenance_burden_is_closed_vocabulary() -> None:
    assert {m.value for m in MaintenanceBurden} == {"LOW", "MEDIUM", "HIGH"}
    assert _capability(maintenance_burden="HIGH").maintenance_burden is MaintenanceBurden.HIGH
    with pytest.raises(ValidationError):
        _capability(maintenance_burden="UNKNOWN")


# ---------------------------------------------------------------------------
# BuildPlan
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-014")
def test_build_plan_constructs_and_round_trips() -> None:
    plan = _plan()
    assert plan.kind is ArtifactKind.BUILD_PLAN
    dumped = plan.model_dump(mode="json")
    assert dumped["kind"] == "BuildPlan"
    assert dumped["steps"][0]["effect_class"] == "READ"
    assert BuildPlan.model_validate(dumped) == plan
    with pytest.raises(ValidationError):
        BuildPlan.model_validate({**dumped, "kind": "AutonomyEnvelope"})
    with pytest.raises(ValidationError):
        BuildPlan.model_validate({**dumped, "free_text_instructions": "do anything"})


@pytest.mark.requirements("PL-015")
def test_step_input_requires_exactly_one_origin() -> None:
    with pytest.raises(ValidationError, match="exactly one"):
        StepInput(name="x", kind=ArtifactKind.EVIDENCE_PACKET)
    with pytest.raises(ValidationError, match="exactly one"):
        StepInput(name="x", kind=ArtifactKind.EVIDENCE_PACKET, from_step="a", plan_input="b")
    assert StepInput(name="x", kind=ArtifactKind.EVIDENCE_PACKET, from_step="a").plan_input is None
    assert StepInput(name="x", kind=ArtifactKind.EVIDENCE_PACKET, plan_input="b").from_step is None


@pytest.mark.requirements("PL-015")
def test_step_rejects_self_dependency_and_duplicate_dependencies() -> None:
    with pytest.raises(ValidationError, match="depend on itself"):
        _step(depends_on=["probe-sources"])
    with pytest.raises(ValidationError, match="depends_on"):
        _step(depends_on=["a", "a"])


@pytest.mark.requirements("PL-015")
def test_step_output_and_input_names_are_unique() -> None:
    out = StepOutput(name="inventory", kind=ArtifactKind.ENVIRONMENT_INVENTORY)
    with pytest.raises(ValidationError, match="outputs"):
        _step(outputs=[out, out])
    inp = StepInput(name="envelope", kind=ArtifactKind.AUTONOMY_ENVELOPE, plan_input="env-synthetic")
    with pytest.raises(ValidationError, match="inputs"):
        _step(inputs=[inp, inp])
    with pytest.raises(ValidationError, match="required_capabilities"):
        _step(required_capabilities=["cap.a", "cap.a"])
    with pytest.raises(ValidationError, match="purposes"):
        _step(purposes=[DataPurpose.INSPECT, DataPurpose.INSPECT])


@pytest.mark.requirements("PL-014", "PL-016")
def test_step_requires_verification_unless_dependency_raise() -> None:
    with pytest.raises(ValidationError, match="verification obligation"):
        _step(verification=[])
    raise_step = _step(
        step_id="raise-access",
        step_type=DEPENDENCY_RAISE_STEP_TYPE,
        effect_class=EffectClass.INTERNAL_WRITE,
        inputs=[],
        outputs=[StepOutput(name="dependency", kind=ArtifactKind.DEPENDENCY_RECORD)],
        verification=[],
    )
    assert raise_step.verification == []
    with pytest.raises(ValidationError, match="verification"):
        _step(verification=[_verification(), _verification()])


@pytest.mark.requirements("PL-058")
def test_plan_rejects_step_budget_in_different_currency() -> None:
    with pytest.raises(ValidationError, match="currency"):
        _plan(steps=[_step(budget=_budget(currency="EUR"))])


@pytest.mark.requirements("PL-014", "PL-005")
def test_plan_requires_steps_and_positive_envelope_version() -> None:
    with pytest.raises(ValidationError):
        _plan(steps=[])
    with pytest.raises(ValidationError):
        _plan(envelope_version=0)
    with pytest.raises(ValidationError):
        _plan(planned_at=datetime(2026, 10, 1))


@pytest.mark.requirements("PL-015")
def test_plan_input_artifact_ids_are_unique() -> None:
    ref = ArtifactRef(artifact_id="env-synthetic", kind=ArtifactKind.AUTONOMY_ENVELOPE, digest=DIGEST)
    with pytest.raises(ValidationError, match="inputs"):
        _plan(inputs=[ref, ref])


@pytest.mark.requirements("PL-018", "PL-058")
def test_budget_bounds_are_enforced_on_steps() -> None:
    with pytest.raises(ValidationError):
        _step(budget=_budget(max_attempts=0))
    with pytest.raises(ValidationError):
        _step(budget=_budget(max_elapsed_seconds=0))
    with pytest.raises(ValidationError):
        _step(budget=_budget(minor_units=-1))
    with pytest.raises(ValidationError):
        _step(budget=_budget(max_attempts=1001))


@pytest.mark.requirements("PL-015")
def test_graph_level_defects_remain_parseable_for_the_checker() -> None:
    """Cycles, unknown dependencies, duplicate ids and unknown step types are checker findings."""
    a = _step(step_id="a", depends_on=["b"],
              inputs=[StepInput(name="from-b", kind=ArtifactKind.QUALITY_REPORT, from_step="b")])
    b = _step(step_id="b", depends_on=["a"],
              inputs=[StepInput(name="from-a", kind=ArtifactKind.ENVIRONMENT_INVENTORY, from_step="a")])
    cyclic = _plan(steps=[a, b])
    assert cyclic.step_ids == ["a", "b"]

    duplicated = _plan(steps=[_step(), _step()])
    assert duplicated.step_ids == ["probe-sources", "probe-sources"]

    dangling = _plan(steps=[_step(depends_on=["never-declared"])])
    assert dangling.find_step("never-declared") is None

    unknown_type = _plan(steps=[_step(step_type="shell.execute_arbitrary")])
    assert unknown_type.steps[0].step_type not in STEP_TYPE_VOCABULARY

    over_budget = _plan(total_budget=_budget(minor_units=1), steps=[_step(budget=_budget(minor_units=10_000))])
    assert over_budget.worst_case_step_spend().exceeds(over_budget.total_budget.spend)


@pytest.mark.requirements("PL-014", "PL-058")
def test_plan_helpers() -> None:
    second = _step(
        step_id="profile-sources",
        step_type="source.profile",
        depends_on=["probe-sources"],
        inputs=[StepInput(name="inventory", kind=ArtifactKind.ENVIRONMENT_INVENTORY, from_step="probe-sources")],
        outputs=[StepOutput(name="profile", kind=ArtifactKind.QUALITY_REPORT)],
        budget=_budget(minor_units=2_500),
    )
    canary = _step(
        step_id="canary",
        step_type="release.canary",
        effect_class=EffectClass.EXTERNAL_COMMUNICATION,
        environment="production",
        budget=_budget(minor_units=500),
    )
    plan = _plan(steps=[_step(), second, canary])
    assert plan.find_step("profile-sources") is second
    assert plan.find_step("missing") is None
    assert plan.plan_input_named("env-synthetic") == plan.inputs[0]
    assert plan.plan_input_named("missing") is None
    assert plan.worst_case_step_spend() == Money(minor_units=13_000, currency="USD")
    assert second.output_named("profile") is not None and second.output_named("nope") is None
    assert not second.has_external_effect
    assert canary.has_external_effect and canary.environment == "production"
    assert EffectClass.READ not in EXTERNAL_EFFECT_CLASSES
    assert EffectClass.INTERNAL_WRITE not in EXTERNAL_EFFECT_CLASSES
    assert EffectClass.DESTRUCTIVE in EXTERNAL_EFFECT_CLASSES


# ---------------------------------------------------------------------------
# Capability registry
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def registry() -> CapabilityRegistry:
    return CapabilityRegistry.default()


@pytest.fixture(scope="module")
def raw_registry() -> dict[str, Any]:
    return json.loads(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))


@pytest.mark.requirements("PL-014")
def test_default_registry_covers_all_23_step_types(registry: CapabilityRegistry) -> None:
    assert len(STEP_TYPE_VOCABULARY) == 23
    assert registry.step_types() == STEP_TYPE_VOCABULARY
    for step_type in STEP_TYPE_VOCABULARY:
        assert registry.step_type_known(step_type)
        assert registry.capabilities_for_step_type(step_type), step_type
    assert not registry.step_type_known("shell.execute_arbitrary")
    assert registry.capabilities_for_step_type("shell.execute_arbitrary") == []


@pytest.mark.requirements("PL-007", "PL-008")
def test_every_registry_entry_is_a_valid_capability_record(
    registry: CapabilityRegistry, raw_registry: dict[str, Any]
) -> None:
    entries = raw_registry["capabilities"]
    assert len(entries) == len(registry) >= 23
    for entry in entries:
        record = CapabilityRecord.model_validate(entry)
        assert registry.get(record.capability_id) == record
        assert record.tenant_id == PLATFORM_TENANT_ID
        assert record.step_type in STEP_TYPE_VOCABULARY
        assert record.content_digest == compute_artifact_digest(record), record.capability_id
        assert record.tested_environment or record.maturity not in EVIDENCE_BACKED_MATURITIES
        assert _roundtrip(record) == record


@pytest.mark.requirements("PL-008")
def test_documented_entries_lack_receipts_and_verified_entries_have_them(registry: CapabilityRegistry) -> None:
    documented = [r for r in registry if r.maturity in {CapabilityMaturity.DOCUMENTED, CapabilityMaturity.DISCOVERED}]
    verified = [r for r in registry if r.maturity in EVIDENCE_BACKED_MATURITIES]
    assert documented, "the registry must carry a documented-only capability for negative tests"
    assert verified
    for record in documented:
        assert record.probe_receipt_ref is None
        assert not record.at_least(CapabilityMaturity.SANDBOX_TESTED)
    for record in verified:
        assert record.probe_receipt_ref is not None
        assert record.tested_environment is not None
        assert record.at_least(CapabilityMaturity.SANDBOX_TESTED)


@pytest.mark.requirements("PL-008")
def test_release_infrastructure_apply_and_verification_are_production_verified(
    registry: CapabilityRegistry,
) -> None:
    gated = {"infrastructure.apply", "verification.request"} | {
        step_type for step_type in STEP_TYPE_VOCABULARY if step_type.startswith("release.")
    }
    assert len(gated) == 5
    for step_type in gated:
        for record in registry.capabilities_for_step_type(step_type):
            assert record.maturity is CapabilityMaturity.PRODUCTION_VERIFIED, record.capability_id
            assert record.probe_receipt_ref is not None


@pytest.mark.requirements("PL-008")
def test_documented_only_capability_is_rejectable_for_production_steps(registry: CapabilityRegistry) -> None:
    documented = registry.get("cap.training.submit.api-finetune")
    assert documented is not None
    assert documented.maturity is CapabilityMaturity.DOCUMENTED
    assert not documented.at_least(CapabilityMaturity.SANDBOX_TESTED)
    alternatives = [
        r for r in registry.capabilities_for_step_type("training.submit") if r.at_least(CapabilityMaturity.SANDBOX_TESTED)
    ]
    assert alternatives, "a verified alternative exists for the same step type"


@pytest.mark.requirements("PL-014")
def test_registry_lookups(registry: CapabilityRegistry) -> None:
    record = registry.get("cap.inventory.probe.management-api")
    assert record is not None and record.step_type == "inventory.probe"
    assert registry.get("cap.does.not.exist") is None
    assert "cap.inventory.probe.management-api" in registry
    assert "cap.does.not.exist" not in registry
    assert registry.capability_ids() == {r.capability_id for r in registry}
    assert registry.records() == list(registry)
    assert len(registry.capability_ids()) == len(registry)
    by_type = registry.capabilities_for_step_type("inventory.probe")
    assert [r.capability_id for r in by_type] == [
        "cap.inventory.probe.management-api",
        "cap.inventory.probe.portal-scrape",
    ]


@pytest.mark.requirements("PL-005", "PL-007")
def test_registry_effect_classes_match_step_semantics(registry: CapabilityRegistry) -> None:
    for step_type in ("inventory.probe", "source.profile", "integration.contract_test", "evaluation.run"):
        for record in registry.capabilities_for_step_type(step_type):
            assert record.effect_classes == [EffectClass.READ], record.capability_id
    apply_records = registry.capabilities_for_step_type("infrastructure.apply")
    assert all(EffectClass.INFRASTRUCTURE_CHANGE in r.effect_classes for r in apply_records)
    configure = registry.capabilities_for_step_type("integration.configure")
    assert all(EffectClass.EXTERNAL_WRITE_REVERSIBLE in r.effect_classes for r in configure)
    for step_type in ("dataset.build", "collection.backfill", "dependency.raise", "release.create"):
        for record in registry.capabilities_for_step_type(step_type):
            assert set(record.effect_classes).isdisjoint(EXTERNAL_EFFECT_CLASSES), record.capability_id
    train = registry.capabilities_for_step_type("training.submit")
    assert all(DataPurpose.TRAIN in r.required_purposes for r in train)


@pytest.mark.requirements("PL-008")
def test_registry_rejects_entry_claiming_verification_without_receipt(
    raw_registry: dict[str, Any], tmp_path: Path
) -> None:
    broken = json.loads(json.dumps(raw_registry))
    entry = broken["capabilities"][0]
    assert entry["maturity"] == "PRODUCTION_VERIFIED"
    entry["probe_receipt_ref"] = None
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(broken), encoding="utf-8")
    with pytest.raises(RegistryError, match=entry["capability_id"]):
        CapabilityRegistry.from_file(path)


@pytest.mark.requirements("PL-014")
def test_registry_rejects_duplicate_capability_ids(raw_registry: dict[str, Any], tmp_path: Path) -> None:
    broken = json.loads(json.dumps(raw_registry))
    broken["capabilities"].append(json.loads(json.dumps(broken["capabilities"][0])))
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(broken), encoding="utf-8")
    with pytest.raises(RegistryError, match="duplicate capability_id"):
        load_registry(path)


@pytest.mark.requirements("PL-014")
def test_registry_rejects_malformed_documents(tmp_path: Path) -> None:
    as_list = tmp_path / "list.json"
    as_list.write_text("[]", encoding="utf-8")
    with pytest.raises(RegistryError, match="capabilities"):
        CapabilityRegistry.from_file(as_list)
    not_json = tmp_path / "broken.json"
    not_json.write_text("{not json", encoding="utf-8")
    with pytest.raises(RegistryError, match="not valid JSON"):
        CapabilityRegistry.from_file(not_json)
    with pytest.raises(RegistryError, match="not found"):
        CapabilityRegistry.from_file(tmp_path / "missing.json")
    not_a_record = tmp_path / "entry.json"
    not_a_record.write_text(json.dumps({"capabilities": [{"capability_id": "cap.x"}]}), encoding="utf-8")
    with pytest.raises(RegistryError, match="cap.x"):
        CapabilityRegistry.from_file(not_a_record)


@pytest.mark.requirements("PL-014")
def test_load_registry_default_matches_packaged_file(registry: CapabilityRegistry) -> None:
    loaded = load_registry()
    assert loaded.capability_ids() == registry.capability_ids()
    assert loaded.step_types() == registry.step_types()
    assert load_registry(DEFAULT_REGISTRY_PATH).records() == registry.records()


# ---------------------------------------------------------------------------
# Review regressions (contracts fidelity lens)
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-005", "PL-040")
@pytest.mark.parametrize("principal_type", [PrincipalType.BUILD_AGENT, PrincipalType.RUNTIME_AGENT])
def test_envelope_cannot_be_produced_by_an_agent(principal_type: PrincipalType) -> None:
    """An agent cannot mint the authority artifact it is compiled against (F6)."""
    with pytest.raises(ValidationError, match="cannot be produced by a build or runtime agent"):
        _envelope(producer=_principal("build-agent-1", principal_type))
    assert _envelope(producer=_principal("control-plane", PrincipalType.SERVICE)).producer.principal_type is PrincipalType.SERVICE


@pytest.mark.requirements("PL-040", "PL-057")
def test_every_artifact_header_rejects_a_naive_created_at() -> None:
    """ArtifactHeader.created_at is AwareDatetime on every contract, not only on five of them (F10)."""
    with pytest.raises(ValidationError, match="timezone"):
        _plan(created_at=datetime(2026, 10, 1, 12, 0))
    with pytest.raises(ValidationError, match="timezone"):
        _capability(created_at=datetime(2026, 10, 1, 12, 0))
    with pytest.raises(ValidationError, match="timezone"):
        _plan(planned_at=datetime(2026, 10, 2, 12, 0))


@pytest.mark.requirements("PL-053")
def test_source_grants_have_a_stable_identity_datasets_can_cite() -> None:
    envelope = _envelope(source_grants=[_grant(), _grant(source_id=OTHER_SOURCE, purposes=[DataPurpose.INSPECT], grant_id="grant-other-inspect")])
    assert envelope.source_grants[0].effective_grant_id == f"grant:{SOURCE}:1.0.0"
    assert envelope.source_grants[1].effective_grant_id == "grant-other-inspect"
    assert [g.source_id for g in envelope.grants_by_id("grant-other-inspect")] == [OTHER_SOURCE]
    assert envelope.grants_by_id("grant-unknown") == []
    with pytest.raises(ValidationError, match="grant_id must not contain duplicates"):
        _envelope(source_grants=[_grant(grant_id="g1"), _grant(grant_id="g1", purposes=[DataPurpose.TRAIN])])
    with pytest.raises(ValidationError, match="looks like a secret"):
        _grant(grant_id="grant-with-password")


@pytest.mark.requirements("PL-053", "PL-015")
def test_step_input_lineage_narrowing_is_declared_on_from_step_inputs_only() -> None:
    narrowed = StepInput(name="dataset", kind=ArtifactKind.DATASET_MANIFEST, from_step="build-dataset", source_ids=[SOURCE])
    assert narrowed.source_ids == [SOURCE]
    with pytest.raises(ValidationError, match="a plan input carries none"):
        StepInput(name="envelope", kind=ArtifactKind.AUTONOMY_ENVELOPE, plan_input="env-synthetic", source_ids=[SOURCE])
    with pytest.raises(ValidationError, match="must not contain duplicates"):
        StepInput(name="dataset", kind=ArtifactKind.DATASET_MANIFEST, from_step="build-dataset", source_ids=[SOURCE, SOURCE])
