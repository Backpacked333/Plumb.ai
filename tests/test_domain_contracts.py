"""Contract tests for the evidence and domain contracts.

Covers EnvironmentInventory, EvidencePacket, OpportunitySpec, IntegrationSpec,
CollectionSpec, WorkflowSpec, the API envelopes and the Appendix A protocol
records. Every model gets a valid construction with a JSON round trip, and
every MUST / MUST NOT rule gets a negative test. All fixtures are synthetic.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from plumb.contracts.api import ErrorEnvelope, EventEnvelope, JobEnvelope, JobStatus
from plumb.contracts.collection import (
    BackfillBoundary,
    CollectionSpec,
    CorrectionPolicy,
    DeletionHandling,
    Destination,
    HealthContract,
    IncrementalMechanism,
    JoinKind,
    JoinStrategy,
    QualityCheck,
    Reconciliation,
    ReorderingPolicy,
    Retention,
    SourceCursor,
    Watermark,
)
from plumb.contracts.common import (
    ArtifactKind,
    ArtifactRef,
    Budget,
    CapabilityMaturity,
    DependencyRecord,
    EffectClass,
    ErrorClass,
    FactStatus,
    FailureClass,
    Money,
    Presence,
    Principal,
    PrincipalType,
    ResourceScope,
    SourceRef,
    TimeAxes,
)
from plumb.contracts.evidence import (
    DerivedFact,
    EvidenceEvent,
    EvidencePacket,
    ExternalId,
    MergeRecord,
    ObjectLink,
    ObjectResolution,
    ResolutionCandidate,
    ScopedCorrection,
    SplitRecord,
)
from plumb.contracts.integration import (
    REQUIRED_CONTRACT_TESTS,
    WRITE_CONTRACT_TESTS,
    BackoffStrategy,
    CurrencySemantics,
    CursorKind,
    CursorStrategy,
    DeletionBehavior,
    FieldMapping,
    IntegrationOperation,
    IntegrationPath,
    IntegrationSpec,
    MaintenanceExposure,
    NullSemantics,
    RateLimit,
    RetrySemantics,
    SchemaDriftHandling,
    StateCapture,
    TimezoneSemantics,
    UnitSemantics,
)
from plumb.contracts.inventory import (
    ApplicationRecord,
    AuthorizationStatus,
    CoverageReport,
    EnvironmentInventory,
    OperationCapability,
    OperationDirection,
    Quota,
    UpdateMechanism,
)
from plumb.contracts.opportunity import (
    BenefitRange,
    BlockingCondition,
    CandidateKind,
    CandidateSystem,
    EvidenceCoverage,
    InterventionKind,
    MeasurementMethod,
    MeasurementPlan,
    OpportunitySpec,
    OpportunityStatus,
    ProposedChange,
)
from plumb.contracts.protocol import (
    FORBIDDEN_RESULT_FIELD_MARKERS,
    AgentTask,
    StepResult,
    check_result_against_task,
)
from plumb.contracts.workflow import (
    CERTIFIED_PRIMITIVES,
    CaseIdentity,
    CompletionCondition,
    CustomPrimitive,
    DeterministicRule,
    DurableWait,
    HumanDecisionPoint,
    Transition,
    Trigger,
    TriggerKind,
    TypedInput,
    WorkflowOperation,
    WorkflowSpec,
    WorkflowState,
)

T0 = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
DAY = timedelta(days=1)
TENANT = "tnt_synthetic01"
OTHER_TENANT = "tnt_othertenant1"
DIGEST = "sha256:" + "ab" * 32
DIGEST_2 = "sha256:" + "cd" * 32
LEDGER = "src-ledger"
MAILBOX = "src-mailbox"


# ---------------------------------------------------------------------------
# Shared synthetic builders
# ---------------------------------------------------------------------------


def _roundtrip(model: Any) -> Any:
    via_dict = type(model).model_validate(model.model_dump(mode="json"))
    via_json = type(model).model_validate_json(model.model_dump_json())
    assert via_dict == model
    assert via_json == model
    return via_json


def _principal(principal_type: PrincipalType = PrincipalType.BUILD_AGENT) -> Principal:
    return Principal(principal_id="agent-01", principal_type=principal_type, authenticated_via="oidc:test-issuer")


def _header(artifact_id: str) -> dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "tenant_id": TENANT,
        "version": 1,
        "producer": _principal(),
        "created_at": T0,
    }


def _source(source_id: str = LEDGER, provider: str = "ledger-provider", account: str = "acct-100") -> SourceRef:
    return SourceRef(source_id=source_id, provider=provider, external_account_id=account)


def _money(minor_units: int, currency: str = "USD") -> Money:
    return Money(minor_units=minor_units, currency=currency)


# ---------------------------------------------------------------------------
# EnvironmentInventory
# ---------------------------------------------------------------------------


def _operation(**overrides: Any) -> OperationCapability:
    data: dict[str, Any] = {
        "operation": "GET /v1/invoices",
        "direction": OperationDirection.READ,
        "maturity": CapabilityMaturity.SANDBOX_TESTED,
        "probe_receipt_ref": "probe-ledger-001",
        "last_probed_at": T0 - DAY,
        "account_id": LEDGER,
    }
    data.update(overrides)
    return OperationCapability(**data)


def _application(**overrides: Any) -> ApplicationRecord:
    data: dict[str, Any] = {
        "application_id": "app-ledger",
        "name": "Ledger",
        "accounts": [_source()],
        "entities": ["invoice", "journal_entry"],
        "schema_versions": {"invoice": "2026-07"},
        "operations": [_operation()],
        "authorization_status": AuthorizationStatus.AUTHORIZED,
        "available_history_from": T0 - 365 * DAY,
        "quotas": [Quota(name="requests", limit=1000, window_seconds=60)],
        "update_mechanism": UpdateMechanism.WEBHOOK,
        "freshness_seconds": 120,
        "owners": ["owner-01"],
    }
    data.update(overrides)
    return ApplicationRecord(**data)


def _coverage(**overrides: Any) -> CoverageReport:
    data: dict[str, Any] = {
        "observed_applications": ["app-ledger"],
        "unobserved_applications": ["Shared spreadsheet"],
        "observed_employee_count": 7,
        "unobserved_employee_count": 2,
        "capture_scope": "Ledger API and bookkeeping mailbox only",
        "exclusions": ["personal mailboxes"],
        "retention_days": 90,
        "disclosure": "Two employees and one spreadsheet-based handoff are not observed.",
    }
    data.update(overrides)
    return CoverageReport(**data)


def _inventory(**overrides: Any) -> EnvironmentInventory:
    data: dict[str, Any] = {
        **_header("inv-001"),
        "inventory_id": "inv-001",
        "applications": [_application()],
        "coverage_report": _coverage(),
        "low_confidence_assumptions": ["the ledger is the authoritative record of invoices"],
    }
    data.update(overrides)
    return EnvironmentInventory(**data)


@pytest.mark.requirements("PL-007", "PL-008")
def test_inventory_constructs_and_round_trips() -> None:
    inventory = _inventory()
    assert inventory.kind is ArtifactKind.ENVIRONMENT_INVENTORY
    restored = _roundtrip(inventory)
    assert restored.application("app-ledger").verified_operations()[0].operation == "GET /v1/invoices"


@pytest.mark.requirements("PL-008")
@pytest.mark.parametrize("maturity", [CapabilityMaturity.SANDBOX_TESTED, CapabilityMaturity.PRODUCTION_VERIFIED])
def test_tested_maturity_without_probe_rejected(maturity: CapabilityMaturity) -> None:
    with pytest.raises(ValidationError, match="requires probe_receipt_ref"):
        _operation(maturity=maturity, probe_receipt_ref=None)
    with pytest.raises(ValidationError, match="requires probe_receipt_ref"):
        _operation(maturity=maturity, last_probed_at=None)
    documented = _operation(maturity=CapabilityMaturity.DOCUMENTED, probe_receipt_ref=None, last_probed_at=None)
    assert documented.maturity is CapabilityMaturity.DOCUMENTED


@pytest.mark.requirements("PL-008")
def test_probe_receipt_ref_rejects_secret_looking_values() -> None:
    with pytest.raises(ValidationError, match="looks like a secret"):
        _operation(probe_receipt_ref="probe-with-password")


@pytest.mark.requirements("PL-007", "PL-008")
def test_operation_account_must_be_an_application_account() -> None:
    with pytest.raises(ValidationError, match="not one of the application's accounts"):
        _application(operations=[_operation(account_id="acct-unknown")])
    assert _application(operations=[_operation(account_id="acct-100")]).operations[0].account_id == "acct-100"


@pytest.mark.requirements("PL-007")
def test_application_consistency_rules() -> None:
    with pytest.raises(ValidationError, match="at least one authorized account"):
        _application(accounts=[], operations=[])
    with pytest.raises(ValidationError, match="duplicate operation"):
        _application(operations=[_operation(), _operation()])
    pending = _application(accounts=[], operations=[], authorization_status=AuthorizationStatus.CONSENT_REQUIRED)
    assert pending.verified_operations() == []


@pytest.mark.requirements("PL-007")
def test_coverage_report_must_disclose_limits() -> None:
    with pytest.raises(ValidationError):
        _coverage(disclosure="   ")
    with pytest.raises(ValidationError):
        _coverage(observed_employee_count=-1)
    with pytest.raises(ValidationError, match="not in inventory"):
        _inventory(coverage_report=_coverage(observed_applications=["app-missing"]))


@pytest.mark.requirements("PL-007")
def test_inventory_requires_applications_and_coverage() -> None:
    with pytest.raises(ValidationError):
        _inventory(applications=[])
    data = {**_header("inv-002"), "inventory_id": "inv-002", "applications": [_application()]}
    with pytest.raises(ValidationError, match="coverage_report"):
        EnvironmentInventory(**data)
    with pytest.raises(ValidationError, match="unique"):
        _inventory(applications=[_application(), _application()])
    with pytest.raises(ValidationError):
        _inventory(unexpected_field="x")


# ---------------------------------------------------------------------------
# EvidencePacket
# ---------------------------------------------------------------------------


def _axes(event: datetime, observed: datetime, available: datetime) -> TimeAxes:
    return TimeAxes(event_time=event, observation_time=observed, availability_time=available)


def _event(event_id: str = "evt-ledger-001", source: SourceRef | None = None, **overrides: Any) -> EvidenceEvent:
    data: dict[str, Any] = {
        "event_id": event_id,
        "source": source or _source(),
        "external_record_id": "inv-20260815-0042",
        "external_version": "3",
        "time": _axes(T0 - 20 * DAY, T0 - DAY, T0),
        "content_digest": DIGEST,
        "raw_content_ref": "blob://evidence/" + event_id,
        "access_policy_ref": "policy://bookkeeping/read",
        "retention_class": "financial-7y",
        "extraction_version": "1.2.0",
        "object_ids": ["obj-client-a", "obj-period-2026-08"],
    }
    data.update(overrides)
    return EvidenceEvent(**data)


def _late_event() -> EvidenceEvent:
    return _event(
        "evt-mail-001",
        source=_source(MAILBOX, "mail-provider", "mbx-7"),
        external_record_id="msg-991",
        time=_axes(T0 - 20 * DAY, T0 + 10 * DAY, T0 + 10 * DAY),
        object_ids=["obj-client-a"],
    )


def _fact(fact_id: str = "fact-001", **overrides: Any) -> DerivedFact:
    data: dict[str, Any] = {
        "fact_id": fact_id,
        "subject_object_id": "obj-client-a",
        "predicate": "august_invoice_total_minor",
        "value": 125000,
        "supporting_evidence_ids": ["evt-ledger-001"],
        "derivation_version": "1.0.0",
        "valid_from": T0 - 20 * DAY,
        "valid_to": None,
        "status": FactStatus.CONFIRMED,
        "presence": Presence.PRESENT,
        "confidence": 0.98,
    }
    data.update(overrides)
    return DerivedFact(**data)


def _resolution(object_id: str = "obj-client-a", **overrides: Any) -> ObjectResolution:
    data: dict[str, Any] = {
        "object_id": object_id,
        "object_type": "client",
        "external_ids": [
            ExternalId(system="ledger-provider", value="CUST-100", confirmed_financial_identity=True),
            ExternalId(system="plumb", value="prov-77", provisional=True),
        ],
        "candidates": [ResolutionCandidate(candidate_object_id="obj-client-a-dup", score=0.41, rationale="same email")],
        "merge_history": [MergeRecord(merged_at=T0 - 5 * DAY, absorbed_object_ids=["obj-client-old"], reason="same tax id")],
        "split_history": [],
        "corrections": [
            ScopedCorrection(
                correction_id="corr-001",
                scope_object_ids=[object_id, "obj-period-2026-08"],
                old_meaning="Square: payment processor",
                new_meaning="Square: client's retail location",
                impact_set=["fact-002"],
                applied_at=T0 - DAY,
            )
        ],
    }
    data.update(overrides)
    return ObjectResolution(**data)


def _packet(**overrides: Any) -> EvidencePacket:
    data: dict[str, Any] = {
        **_header("pkt-001"),
        "packet_id": "pkt-001",
        "authoritative_source_ids": [LEDGER],
        "events": [_event(), _late_event()],
        "facts": [
            _fact(),
            _fact(
                "fact-002",
                predicate="statement_mentions_square",
                value="retail location",
                supporting_evidence_ids=["evt-mail-001"],
                status=FactStatus.OBSERVED,
                confidence=0.6,
            ),
        ],
        "object_resolutions": [
            _resolution(),
            ObjectResolution(object_id="obj-period-2026-08", object_type="period"),
        ],
        "links": [
            ObjectLink(from_object_id="evt-mail-001", to_object_id="obj-client-a", relation="mentions_client"),
            ObjectLink(from_object_id="obj-client-a", to_object_id="obj-engagement-ext", relation="under_engagement"),
        ],
        "external_object_ids": ["obj-engagement-ext"],
    }
    data.update(overrides)
    return EvidencePacket(**data)


@pytest.mark.requirements("PL-009", "PL-010", "PL-011")
def test_evidence_packet_constructs_and_round_trips() -> None:
    packet = _packet()
    assert packet.kind is ArtifactKind.EVIDENCE_PACKET
    restored = _roundtrip(packet)
    assert restored.facts[0].value == 125000 and isinstance(restored.facts[0].value, int)
    assert restored.resolution("obj-client-a").confirmed_financial_ids[0].value == "CUST-100"


@pytest.mark.requirements("PL-009")
def test_event_preserves_time_axes_and_references_raw_content() -> None:
    with pytest.raises(ValidationError, match="availability_time cannot precede observation_time"):
        _event(time=_axes(T0 - 20 * DAY, T0, T0 - DAY))
    with pytest.raises(ValidationError):
        _event(raw_content_ref="Invoice total is 1,250.00 payable in 30 days")
    with pytest.raises(ValidationError, match="looks like a secret"):
        _event(access_policy_ref="policy?token=abc")
    for field in ("external_version", "content_digest", "retention_class", "extraction_version"):
        with pytest.raises(ValidationError, match=field):
            EvidenceEvent(**{k: v for k, v in _event().model_dump().items() if k != field})


@pytest.mark.requirements("PL-010")
def test_fact_requires_supporting_evidence_present_in_packet() -> None:
    with pytest.raises(ValidationError):
        _fact(supporting_evidence_ids=[])
    with pytest.raises(ValidationError, match="cites evidence not in the packet"):
        _packet(facts=[_fact(supporting_evidence_ids=["evt-missing"])])
    with pytest.raises(ValidationError, match="unknown object"):
        _packet(facts=[_fact(subject_object_id="obj-nowhere")])


@pytest.mark.requirements("PL-010")
def test_confirmed_fact_requires_authoritative_evidence() -> None:
    with pytest.raises(ValidationError, match="CONFIRMED without evidence from an authoritative source"):
        _packet(facts=[_fact(supporting_evidence_ids=["evt-mail-001"], confidence=1.0)])
    with pytest.raises(ValidationError, match="CONFIRMED without evidence"):
        _packet(authoritative_source_ids=[])
    inferred = _packet(facts=[_fact(supporting_evidence_ids=["evt-mail-001"], status=FactStatus.INFERRED)])
    assert inferred.facts[0].status is FactStatus.INFERRED


@pytest.mark.requirements("PL-010")
def test_confidence_is_bounded_and_absence_is_explicit() -> None:
    with pytest.raises(ValidationError):
        _fact(confidence=1.5)
    with pytest.raises(ValidationError, match="CONFIRMED fact cannot have UNKNOWN presence"):
        _fact(value=None, presence=Presence.UNKNOWN, status=FactStatus.CONFIRMED)
    with pytest.raises(ValidationError, match="cannot carry a value"):
        _fact(presence=Presence.CONFIRMED_ABSENT)
    with pytest.raises(ValidationError, match="PRESENT fact must carry a value"):
        _fact(value=None)
    with pytest.raises(ValidationError, match="valid_to cannot precede valid_from"):
        _fact(valid_to=T0 - 30 * DAY)
    unknown = _fact(value=None, presence=Presence.UNKNOWN, status=FactStatus.OBSERVED)
    absent = _fact(value=None, presence=Presence.CONFIRMED_ABSENT, status=FactStatus.CONFIRMED)
    assert unknown.presence is not absent.presence


@pytest.mark.requirements("PL-011")
def test_provisional_id_cannot_be_confirmed_financial_identity() -> None:
    with pytest.raises(ValidationError, match="provisional id cannot be marked confirmed_financial_identity"):
        ExternalId(system="plumb", value="prov-1", provisional=True, confirmed_financial_identity=True)


@pytest.mark.requirements("PL-011")
def test_correction_is_scoped_never_global() -> None:
    base = _resolution().corrections[0].model_dump()
    with pytest.raises(ValidationError):
        ScopedCorrection(**{**base, "scope_object_ids": []})
    with pytest.raises(ValidationError, match="must be reversible"):
        ScopedCorrection(**{**base, "reversible": False})
    with pytest.raises(ValidationError, match="must differ"):
        ScopedCorrection(**{**base, "new_meaning": base["old_meaning"]})
    with pytest.raises(ValidationError, match="must include it in scope"):
        _resolution(corrections=[ScopedCorrection(**{**base, "scope_object_ids": ["obj-period-2026-08"]})])
    assert "scope_object_ids" in ScopedCorrection.model_fields
    assert ScopedCorrection.model_fields["scope_object_ids"].is_required()


@pytest.mark.requirements("PL-011")
def test_resolution_history_and_candidates_are_coherent() -> None:
    with pytest.raises(ValidationError, match="own resolution candidate"):
        _resolution(candidates=[ResolutionCandidate(candidate_object_id="obj-client-a", score=0.9)])
    with pytest.raises(ValidationError):
        SplitRecord(split_at=T0, resulting_object_ids=["obj-only-one"], reason="split")
    with pytest.raises(ValidationError, match="unique"):
        _packet(object_resolutions=[_resolution(), _resolution()])


@pytest.mark.requirements("PL-011")
def test_link_endpoints_must_be_resolved_event_or_declared_external() -> None:
    with pytest.raises(ValidationError, match="neither resolved, an event, nor declared external"):
        _packet(links=[ObjectLink(from_object_id="obj-client-a", to_object_id="obj-ghost", relation="r")])
    with pytest.raises(ValidationError, match="cannot relate an object to itself"):
        ObjectLink(from_object_id="obj-client-a", to_object_id="obj-client-a", relation="self")
    with pytest.raises(ValidationError, match="must not overlap"):
        _packet(external_object_ids=["obj-client-a", "obj-engagement-ext"])
    with pytest.raises(ValidationError, match="references unknown objects"):
        _packet(events=[_event(object_ids=["obj-unknown"]), _late_event()])


@pytest.mark.requirements("PL-009", "PL-010")
def test_facts_as_of_excludes_later_available_evidence() -> None:
    packet = _packet()
    september_decision = T0 + DAY
    assert [fact.fact_id for fact in packet.facts_as_of(september_decision)] == ["fact-001"]
    assert [fact.fact_id for fact in packet.facts_as_of(T0 + 20 * DAY)] == ["fact-001", "fact-002"]
    with pytest.raises(ValueError, match="timezone-aware"):
        packet.facts_as_of(datetime(2026, 9, 2, 12, 0))


# ---------------------------------------------------------------------------
# OpportunitySpec
# ---------------------------------------------------------------------------


def _benefit(low: int = 100_000, high: int = 500_000, horizon_days: int = 90) -> BenefitRange:
    return BenefitRange(low=_money(low), high=_money(high), horizon_days=horizon_days)


def _candidate(kind: CandidateKind, cost: int = 30_000) -> CandidateSystem:
    return CandidateSystem(
        kind=kind, description=f"{kind.value.lower()} alternative", expected_cost=_money(cost), expected_benefit_range=_benefit()
    )


def _opportunity(**overrides: Any) -> OpportunitySpec:
    data: dict[str, Any] = {
        **_header("opp-001"),
        "opportunity_id": "opp-001",
        "goal_id": "goal-month-end",
        "business_objective": "Collect missing client documents before month-end close",
        "eligible_case_population": "Monthly bookkeeping engagements with at least one open obligation",
        "baseline": "Accountant emails each client manually; median 6 days to receive documents",
        "evidence_coverage": EvidenceCoverage(observed_case_count=180, eligible_case_count=210, source_ids=[LEDGER, MAILBOX]),
        "proposed_change": ProposedChange(
            intervention_kind=InterventionKind.DETERMINISTIC_AUTOMATION,
            description="Send authorized reminders from the obligation checklist",
        ),
        "dependencies": ["opp-identity-normalization"],
        "expected_benefit_range": _benefit(),
        "failure_cost": _money(20_000),
        "review_cost": _money(10_000),
        "implementation_cost": _money(40_000),
        "measurement_plan": MeasurementPlan(
            prospective=True,
            method=MeasurementMethod.STAGED_ROLLOUT,
            metrics=["days_to_documents_received"],
            confounders_accounted=["case mix", "calendar effects"],
            horizon_days=90,
        ),
        "candidate_comparison": [
            _candidate(CandidateKind.CURRENT_PROCESS, cost=0),
            _candidate(CandidateKind.NATIVE_FEATURE, cost=5_000),
            _candidate(CandidateKind.PROPOSED_SYSTEM, cost=40_000),
        ],
        "blocking_conditions": [],
        "overlap_refs": ["opp-002"],
        "status": OpportunityStatus.FEASIBLE,
    }
    data.update(overrides)
    return OpportunitySpec(**data)


@pytest.mark.requirements("PL-012", "PL-013")
def test_opportunity_constructs_and_round_trips() -> None:
    opportunity = _opportunity()
    assert opportunity.kind is ArtifactKind.OPPORTUNITY_SPEC
    _roundtrip(opportunity)
    assert opportunity.expected_net_value_range() == (100_000 - 70_000, 500_000 - 70_000)
    assert opportunity.evidence_coverage.ratio == pytest.approx(180 / 210)


@pytest.mark.requirements("PL-012")
@pytest.mark.parametrize(
    "field",
    [
        "business_objective",
        "eligible_case_population",
        "baseline",
        "evidence_coverage",
        "proposed_change",
        "expected_benefit_range",
        "failure_cost",
        "review_cost",
        "measurement_plan",
    ],
)
def test_opportunity_requires_every_pl012_field(field: str) -> None:
    data = _opportunity().model_dump()
    del data[field]
    with pytest.raises(ValidationError, match=field):
        OpportunitySpec(**data)


@pytest.mark.requirements("PL-013")
def test_candidate_comparison_requires_current_process_and_native_feature() -> None:
    with pytest.raises(ValidationError, match="NATIVE_FEATURE"):
        _opportunity(candidate_comparison=[_candidate(CandidateKind.CURRENT_PROCESS), _candidate(CandidateKind.PROPOSED_SYSTEM)])
    with pytest.raises(ValidationError, match="CURRENT_PROCESS"):
        _opportunity(candidate_comparison=[_candidate(CandidateKind.NATIVE_FEATURE), _candidate(CandidateKind.PROPOSED_SYSTEM)])
    assert {InterventionKind.REMOVE_STEP, InterventionKind.NATIVE_SETTING} <= set(InterventionKind)


@pytest.mark.requirements("PL-012")
def test_benefit_range_is_ordered_over_a_horizon() -> None:
    with pytest.raises(ValidationError, match="low bound cannot exceed"):
        _benefit(low=600_000, high=500_000)
    with pytest.raises(ValidationError):
        _benefit(horizon_days=0)
    with pytest.raises(ValidationError, match="share a currency"):
        BenefitRange(low=_money(1, "EUR"), high=_money(2, "USD"), horizon_days=30)
    with pytest.raises(ValidationError, match="currency"):
        _opportunity(failure_cost=_money(100, "EUR"))


@pytest.mark.requirements("PL-012")
def test_measurement_plan_must_be_prospective() -> None:
    with pytest.raises(ValidationError, match="must be prospective"):
        MeasurementPlan(prospective=False, method=MeasurementMethod.STAGED_ROLLOUT, metrics=["m"], horizon_days=30)


@pytest.mark.requirements("PL-013")
def test_non_positive_net_value_requires_rejected_status() -> None:
    with pytest.raises(ValidationError, match="must be REJECTED_NEGATIVE_VALUE"):
        _opportunity(expected_benefit_range=_benefit(low=0, high=60_000))
    rejected = _opportunity(expected_benefit_range=_benefit(low=0, high=60_000), status=OpportunityStatus.REJECTED_NEGATIVE_VALUE)
    assert rejected.expected_net_value_range()[1] <= 0


@pytest.mark.requirements("PL-013")
def test_failed_feasibility_remains_a_blocked_backlog_entry() -> None:
    blocker = BlockingCondition(
        condition_id="blk-001",
        failure_class=FailureClass.MISSING_AUTHORIZATION,
        description="Mailbox send scope not granted",
        missing_authority=["mailbox:send"],
    )
    with pytest.raises(ValidationError, match="must record its blocking conditions"):
        _opportunity(status=OpportunityStatus.BLOCKED)
    with pytest.raises(ValidationError, match="cannot be FEASIBLE"):
        _opportunity(blocking_conditions=[blocker])
    blocked = _opportunity(blocking_conditions=[blocker], status=OpportunityStatus.BLOCKED)
    assert blocked.blocking_conditions[0].missing_authority == ["mailbox:send"]
    with pytest.raises(ValidationError, match="overlap with itself"):
        _opportunity(overlap_refs=["opp-001"])


# ---------------------------------------------------------------------------
# IntegrationSpec
# ---------------------------------------------------------------------------


def _read_operation(**overrides: Any) -> IntegrationOperation:
    data: dict[str, Any] = {
        "name": "list_invoices",
        "direction": OperationDirection.READ,
        "effect_class": EffectClass.READ,
        "path_used": IntegrationPath.VERIFIED_ADAPTER,
        "maintenance_exposure": MaintenanceExposure.LOW,
        "verification_probe_refs": ["probe-001"],
    }
    data.update(overrides)
    return IntegrationOperation(**data)


def _write_operation(**overrides: Any) -> IntegrationOperation:
    data: dict[str, Any] = {
        "name": "post_journal_entry",
        "direction": OperationDirection.WRITE,
        "effect_class": EffectClass.EXTERNAL_WRITE_REVERSIBLE,
        "path_used": IntegrationPath.GENERATED_CODE,
        "maintenance_exposure": MaintenanceExposure.MEDIUM,
        "verification_probe_refs": ["probe-002"],
    }
    data.update(overrides)
    return IntegrationOperation(**data)


def _mapping(**overrides: Any) -> FieldMapping:
    data: dict[str, Any] = {
        "source_field": "TotalAmt",
        "target_field": "total_minor_units",
        "unit": UnitSemantics(source_unit="dollars", target_unit="cents", conversion_factor=Decimal("100")),
        "currency": CurrencySemantics(source_currency="USD", target_currency="USD"),
        "timezone": TimezoneSemantics(source_timezone="America/New_York", target_timezone="UTC"),
        "enum_map": {"Paid": "PAID", "Open": "OPEN"},
        "null_semantics": NullSemantics.NULL_MEANS_UNKNOWN,
        "note": "provider stores decimal dollars",
    }
    data.update(overrides)
    return FieldMapping(**data)


def _integration(**overrides: Any) -> IntegrationSpec:
    data: dict[str, Any] = {
        **_header("int-001"),
        "integration_id": "int-001",
        "source": _source(),
        "operations": [_read_operation(), _write_operation()],
        "authentication_ref": "vault://connections/ledger-acct-100",
        "required_scopes": ["invoices.read", "journal.write"],
        "schema_mappings": [_mapping()],
        "cursor_strategy": CursorStrategy(kind=CursorKind.UPDATED_SINCE_OVERLAP, overlap_seconds=300, stable_version_field="SyncToken"),
        "rate_limits": [RateLimit(requests=500, window_seconds=60, scope="per account")],
        "retry_semantics": RetrySemantics(max_attempts=5, backoff=BackoffStrategy.EXPONENTIAL, retry_on=["429", "503"]),
        "deletion_behavior": DeletionBehavior.TOMBSTONE,
        "verification_probes": ["probe-001", "probe-002"],
        "schema_drift_handling": SchemaDriftHandling.QUARANTINE_AND_REMAP,
        "contract_tests_passed": sorted(REQUIRED_CONTRACT_TESTS | WRITE_CONTRACT_TESTS),
        "activated": True,
    }
    data.update(overrides)
    return IntegrationSpec(**data)


@pytest.mark.requirements("PL-020", "PL-021", "PL-022")
def test_integration_spec_constructs_and_round_trips() -> None:
    spec = _integration()
    assert spec.kind is ArtifactKind.INTEGRATION_SPEC
    restored = _roundtrip(spec)
    assert restored.schema_mappings[0].unit is not None
    assert restored.schema_mappings[0].unit.conversion_factor == Decimal("100")
    assert restored.has_write_operations and restored.missing_contract_tests() == set()


@pytest.mark.requirements("PL-021")
def test_cents_to_dollars_without_conversion_factor_rejected() -> None:
    with pytest.raises(ValidationError, match="requires an explicit conversion_factor"):
        UnitSemantics(source_unit="cents", target_unit="dollars")
    with pytest.raises(ValidationError, match="must be positive"):
        UnitSemantics(source_unit="cents", target_unit="dollars", conversion_factor=Decimal("0"))
    with pytest.raises(ValidationError, match="identical units"):
        UnitSemantics(source_unit="cents", target_unit="cents", conversion_factor=Decimal("100"))
    explicit = _mapping(unit=UnitSemantics(source_unit="cents", target_unit="dollars", conversion_factor=Decimal("0.01")))
    assert explicit.unit is not None and explicit.unit.conversion_factor == Decimal("0.01")


@pytest.mark.requirements("PL-021")
def test_mapping_semantics_are_explicit() -> None:
    with pytest.raises(ValidationError, match="cannot convert currencies"):
        CurrencySemantics(source_currency="USD", target_currency="EUR")
    with pytest.raises(ValidationError, match="unknown IANA time zone"):
        TimezoneSemantics(source_timezone="Mars/Olympus", target_timezone="UTC")
    with pytest.raises(ValidationError, match="null_semantics"):
        FieldMapping(source_field="a", target_field="b")
    with pytest.raises(ValidationError, match="same target field"):
        _integration(schema_mappings=[_mapping(), _mapping(source_field="Amount")])


@pytest.mark.requirements("PL-021")
def test_authentication_ref_is_a_reference_not_a_secret() -> None:
    with pytest.raises(ValidationError, match="looks like a secret"):
        _integration(authentication_ref="client_secret=abc123")
    with pytest.raises(ValidationError, match="looks like a secret"):
        _integration(authentication_ref="A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8S9t0U1v2")


@pytest.mark.requirements("PL-022")
def test_activation_without_contract_tests_rejected() -> None:
    with pytest.raises(ValidationError, match="contract tests not passed: account_boundaries"):
        _integration(contract_tests_passed=sorted((REQUIRED_CONTRACT_TESTS | WRITE_CONTRACT_TESTS) - {"account_boundaries"}))
    with pytest.raises(ValidationError, match="business_state_verification, uncertain_write_behavior"):
        _integration(contract_tests_passed=sorted(REQUIRED_CONTRACT_TESTS))
    read_only = _integration(operations=[_read_operation()], contract_tests_passed=sorted(REQUIRED_CONTRACT_TESTS))
    assert read_only.activated and not read_only.has_write_operations
    inactive = _integration(contract_tests_passed=[], activated=False)
    assert inactive.missing_contract_tests() == REQUIRED_CONTRACT_TESTS | WRITE_CONTRACT_TESTS


@pytest.mark.requirements("PL-020", "PL-022")
def test_activation_requires_verification_probe_per_operation() -> None:
    with pytest.raises(ValidationError, match="operations without a verification probe: post_journal_entry"):
        _integration(operations=[_read_operation(), _write_operation(verification_probe_refs=[])])
    with pytest.raises(ValidationError, match="cites probes not in verification_probes"):
        _integration(verification_probes=["probe-001"])
    with pytest.raises(ValidationError, match="without reconciling uncertain writes"):
        _integration(retry_semantics=RetrySemantics(max_attempts=3, backoff=BackoffStrategy.LINEAR, reconcile_writes_before_retry=False))


@pytest.mark.requirements("PL-021")
def test_operation_direction_matches_effect_class() -> None:
    with pytest.raises(ValidationError, match="READ operation list_invoices cannot have effect class"):
        _read_operation(effect_class=EffectClass.EXTERNAL_WRITE_REVERSIBLE)
    with pytest.raises(ValidationError, match="must declare a non-READ effect class"):
        _write_operation(effect_class=EffectClass.READ)
    with pytest.raises(ValidationError, match="unique"):
        _integration(operations=[_read_operation(), _read_operation()])


@pytest.mark.requirements("PL-021")
def test_configuration_change_captures_before_and_after_state() -> None:
    change = _write_operation(name="enable_reminders", configuration_change=True, path_used=IntegrationPath.DECLARATIVE_CONFIG)
    with pytest.raises(ValidationError, match="requires a before/after StateCapture"):
        _integration(operations=[_read_operation(), change])
    capture = StateCapture(
        operation_name="enable_reminders",
        before_state_ref="snapshot://settings/v1",
        after_state_ref="snapshot://settings/v2",
        affected_resources=["reminder_settings"],
        expected_effect="Weekly reminders sent for overdue invoices",
        reversal_limits="Reminders already sent cannot be recalled",
    )
    configured = _integration(operations=[_read_operation(), change], before_after_state_refs=[capture])
    assert configured.before_after_state_refs[0].operation_name == "enable_reminders"
    with pytest.raises(ValidationError, match="is a WRITE operation"):
        _read_operation(configuration_change=True)


@pytest.mark.requirements("PL-021", "PL-024")
def test_cursor_overlap_requires_stable_record_versions() -> None:
    with pytest.raises(ValidationError, match="requires overlap_seconds and stable_version_field"):
        CursorStrategy(kind=CursorKind.UPDATED_SINCE_OVERLAP, overlap_seconds=60)
    assert CursorStrategy(kind=CursorKind.OPAQUE_CURSOR).overlap_seconds is None


# ---------------------------------------------------------------------------
# CollectionSpec
# ---------------------------------------------------------------------------


def _collection(**overrides: Any) -> CollectionSpec:
    data: dict[str, Any] = {
        **_header("col-001"),
        "collection_id": "col-001",
        "objective_ref": "opp-001",
        "allowed_sources": [_source()],
        "selected_fields": ["invoice_id", "client_id", "total_minor_units", "due_date"],
        "join_strategy": JoinStrategy(kind=JoinKind.EXACT_KEY, keys=["client_id"]),
        "incremental_mechanism": IncrementalMechanism.POLLING_OVERLAP,
        "overlap_seconds": 600,
        "reordering_policy": ReorderingPolicy.SOURCE_VERSION_WINS,
        "correction_policy": CorrectionPolicy.NEW_VERSION_SUPERSEDES,
        "watermark": Watermark(field="updated_at", value="2026-01-01T00:00:00Z", as_of=T0),
        "backfill_boundary": BackfillBoundary(start=T0 - 365 * DAY, end=T0, agreed_by="owner-01"),
        "idempotent_event_identity": ["source_id", "invoice_id", "sync_token"],
        "cursors": [SourceCursor(source_id=LEDGER, cursor="c3Vuc2V0", processing_offset=42, updated_at=T0)],
        "reconciliation": Reconciliation(source_count_reconciliation=True, sample_size=50),
        "retention": Retention(retention_days=2555, deletion_handling=DeletionHandling.TOMBSTONE),
        "destination": Destination(destination_id="dest-evidence-store", region="us-east-1", schema_ref="schema://invoices/v3"),
        "access_policy_ref": "policy://bookkeeping/collect",
        "quality_checks": [QualityCheck(name="total_non_negative", expression="total_minor_units >= 0")],
        "permitted_purpose_evidence_ref": "grant://src-ledger/collect",
        "health": HealthContract(
            freshness_deadline_seconds=900,
            lag_metric="collector.lag_seconds",
            completeness_metric="collector.completeness_ratio",
            failure_state_metric="collector.failure_state",
        ),
        "downstream_block_on_missing_coverage": True,
    }
    data.update(overrides)
    return CollectionSpec(**data)


@pytest.mark.requirements("PL-023", "PL-024", "PL-025")
def test_collection_spec_constructs_and_round_trips() -> None:
    spec = _collection()
    assert spec.kind is ArtifactKind.COLLECTION_SPEC
    _roundtrip(spec)


@pytest.mark.requirements("PL-024")
def test_polling_requires_positive_overlap() -> None:
    with pytest.raises(ValidationError, match="POLLING_OVERLAP requires overlap_seconds"):
        _collection(overlap_seconds=None)
    with pytest.raises(ValidationError):
        _collection(overlap_seconds=0)


@pytest.mark.requirements("PL-024")
def test_webhook_without_authoritative_fetch_rejected() -> None:
    with pytest.raises(ValidationError, match="WEBHOOK collection must fetch authoritative state"):
        _collection(incremental_mechanism=IncrementalMechanism.WEBHOOK, overlap_seconds=None)
    webhook = _collection(incremental_mechanism=IncrementalMechanism.WEBHOOK, overlap_seconds=None, webhook_fetches_authoritative_state=True)
    assert webhook.webhook_fetches_authoritative_state


@pytest.mark.requirements("PL-024")
def test_idempotent_identity_cursors_and_reconciliation_are_explicit() -> None:
    with pytest.raises(ValidationError):
        _collection(idempotent_event_identity=[])
    with pytest.raises(ValidationError, match="source_count_reconciliation must be true"):
        Reconciliation(source_count_reconciliation=False, sample_size=10)
    with pytest.raises(ValidationError, match="not in allowed_sources"):
        _collection(cursors=[SourceCursor(source_id=MAILBOX, cursor="x", processing_offset=0, updated_at=T0)])
    with pytest.raises(ValidationError, match="reordering_policy"):
        CollectionSpec(**{k: v for k, v in _collection().model_dump().items() if k != "reordering_policy"})
    with pytest.raises(ValidationError, match="backfill end cannot precede start"):
        BackfillBoundary(start=T0, end=T0 - DAY, agreed_by="owner-01")


@pytest.mark.requirements("PL-025")
def test_health_contract_requires_all_four_signals() -> None:
    for field in ("freshness_deadline_seconds", "lag_metric", "completeness_metric", "failure_state_metric"):
        data = _collection().health.model_dump()
        del data[field]
        with pytest.raises(ValidationError, match=field):
            HealthContract(**data)


@pytest.mark.requirements("PL-023", "PL-025")
def test_collection_is_justified_and_blocks_downstream_on_missing_coverage() -> None:
    data = _collection().model_dump()
    del data["permitted_purpose_evidence_ref"]
    with pytest.raises(ValidationError, match="permitted_purpose_evidence_ref"):
        CollectionSpec(**data)
    with pytest.raises(ValidationError, match="downstream_block_on_missing_coverage must be true"):
        _collection(downstream_block_on_missing_coverage=False)
    with pytest.raises(ValidationError):
        _collection(quality_checks=[])


# ---------------------------------------------------------------------------
# WorkflowSpec
# ---------------------------------------------------------------------------


def _wf_operation(**overrides: Any) -> WorkflowOperation:
    data: dict[str, Any] = {
        "name": "request_documents",
        "primitive": "request_missing_information",
        "external_effect": True,
        "effect_class": EffectClass.EXTERNAL_COMMUNICATION,
        "requires_case_state_version_check": True,
        "deterministic_rule_ref": "rule-approved-recipient",
    }
    data.update(overrides)
    return WorkflowOperation(**data)


def _fetch_operation(**overrides: Any) -> WorkflowOperation:
    data: dict[str, Any] = {
        "name": "fetch_ledger_state",
        "primitive": "fetch",
        "external_effect": False,
        "effect_class": EffectClass.READ,
        "requires_case_state_version_check": False,
    }
    data.update(overrides)
    return WorkflowOperation(**data)


def _workflow(**overrides: Any) -> WorkflowSpec:
    data: dict[str, Any] = {
        **_header("wf-001"),
        "workflow_id": "wf-001",
        "case_identity": CaseIdentity(fields=["client_id", "period"], description="One client-period engagement"),
        "triggers": [Trigger(kind=TriggerKind.EVENT, source="period_opened")],
        "typed_inputs": [TypedInput(name="engagement_checklist", type_ref="schema://checklist/v1")],
        "states": [
            WorkflowState(name="resolving"),
            WorkflowState(name="waiting_documents", durable_wait=True),
            WorkflowState(name="review"),
            WorkflowState(name="done", terminal=True),
            WorkflowState(name="expired", terminal=True),
        ],
        "initial_state": "resolving",
        "transitions": [
            Transition(from_state="resolving", to_state="waiting_documents", trigger="request_documents"),
            Transition(from_state="waiting_documents", to_state="review", trigger="documents_received"),
            Transition(from_state="waiting_documents", to_state="expired", trigger="timeout"),
            Transition(from_state="review", to_state="done", trigger="accountant_signoff", guard_rule_ref="rule-approved-recipient"),
        ],
        "allowed_operations": [
            _fetch_operation(),
            _wf_operation(),
            WorkflowOperation(
                name="prepare_review_package",
                primitive="review",
                external_effect=False,
                effect_class=EffectClass.INTERNAL_WRITE,
                requires_case_state_version_check=True,
            ),
        ],
        "deterministic_rules": [
            DeterministicRule(rule_id="rule-approved-recipient", expression="recipient in engagement.approved_contacts")
        ],
        "max_iterations": 20,
        "max_duration_seconds": 30 * 86400,
        "max_cost": _money(5_000),
        "durable_waits": [DurableWait(state="waiting_documents", timeout_seconds=14 * 86400, on_timeout_state="expired")],
        "human_decision_points": [
            HumanDecisionPoint(state="review", decision="Accountant signs off the review package", decider_role=PrincipalType.HUMAN_REVIEWER)
        ],
        "completion_conditions": [CompletionCondition(terminal_state="done", description="Review package signed off")],
        "model_output_validation_required": True,
    }
    data.update(overrides)
    return WorkflowSpec(**data)


@pytest.mark.requirements("PL-035", "PL-036")
def test_workflow_constructs_and_round_trips() -> None:
    workflow = _workflow()
    assert workflow.kind is ArtifactKind.WORKFLOW_SPEC
    _roundtrip(workflow)
    assert [operation.name for operation in workflow.external_operations] == ["request_documents"]


@pytest.mark.requirements("PL-035")
def test_write_primitive_without_external_effect_rejected() -> None:
    with pytest.raises(ValidationError, match="always has an external effect"):
        _wf_operation(name="post_entry", primitive="write", external_effect=False, effect_class=EffectClass.READ)
    with pytest.raises(ValidationError, match="always has an external effect"):
        _wf_operation(external_effect=False, effect_class=EffectClass.READ)
    with pytest.raises(ValidationError, match="has external_effect but effect class READ"):
        _wf_operation(effect_class=EffectClass.READ)
    with pytest.raises(ValidationError, match="without external_effect"):
        _fetch_operation(effect_class=EffectClass.EXTERNAL_WRITE_REVERSIBLE)


@pytest.mark.requirements("PL-035", "PL-036")
def test_external_effects_check_case_state_and_are_rule_gated() -> None:
    with pytest.raises(ValidationError, match="must check the case state version"):
        _wf_operation(requires_case_state_version_check=False)
    with pytest.raises(ValidationError, match="a prompt is not an approval mechanism"):
        _wf_operation(deterministic_rule_ref=None)
    with pytest.raises(ValidationError, match="references unknown rule"):
        _workflow(allowed_operations=[_fetch_operation(), _wf_operation(deterministic_rule_ref="rule-missing")])


@pytest.mark.requirements("PL-035")
def test_non_certified_primitive_rejected_unless_declared_with_verification() -> None:
    rogue = _fetch_operation(name="route_vehicles", primitive="solve_routes")
    with pytest.raises(ValidationError, match="neither certified nor a declared custom primitive"):
        _workflow(allowed_operations=[rogue, _wf_operation()])
    certified = _workflow(
        allowed_operations=[rogue, _wf_operation()],
        custom_primitives=[CustomPrimitive(name="solve_routes", adapter_verification_ref="verify-solver-001", description="Routing solver adapter")],
    )
    assert certified.allowed_operations[0].primitive == "solve_routes"
    with pytest.raises(ValidationError, match="shadows a certified primitive"):
        CustomPrimitive(name="write", adapter_verification_ref="verify-x", description="x")
    assert "request_missing_information" in CERTIFIED_PRIMITIVES and len(CERTIFIED_PRIMITIVES) == 11


@pytest.mark.requirements("PL-036")
def test_rules_live_outside_the_model_and_outputs_are_validated() -> None:
    with pytest.raises(ValidationError, match="enforced outside model text"):
        DeterministicRule(rule_id="rule-x", expression="x > 0", enforced_outside_model=False)
    with pytest.raises(ValidationError, match="model_output_validation_required must be true"):
        _workflow(model_output_validation_required=False)


@pytest.mark.requirements("PL-035")
def test_states_and_transitions_are_consistent() -> None:
    with pytest.raises(ValidationError, match="unknown state nowhere"):
        _workflow(transitions=[Transition(from_state="resolving", to_state="nowhere", trigger="t")])
    with pytest.raises(ValidationError, match="terminal state done cannot have outgoing"):
        _workflow(transitions=[Transition(from_state="done", to_state="resolving", trigger="t")])
    with pytest.raises(ValidationError, match="initial_state cannot be terminal"):
        _workflow(initial_state="done")
    with pytest.raises(ValidationError, match="not flagged durable_wait"):
        _workflow(durable_waits=[DurableWait(state="review", timeout_seconds=10, on_timeout_state="expired")])
    with pytest.raises(ValidationError, match="is not terminal"):
        _workflow(completion_conditions=[CompletionCondition(terminal_state="review", description="x")])
    with pytest.raises(ValidationError, match="not a declared rule"):
        _workflow(transitions=[Transition(from_state="resolving", to_state="done", trigger="t", guard_rule_ref="rule-ghost")])


@pytest.mark.requirements("PL-035")
def test_workflow_bounds_waits_and_decision_points_are_required() -> None:
    with pytest.raises(ValidationError):
        _workflow(max_iterations=0)
    with pytest.raises(ValidationError):
        _workflow(durable_waits=[])
    with pytest.raises(ValidationError):
        _workflow(human_decision_points=[])
    with pytest.raises(ValidationError):
        _workflow(completion_conditions=[])
    with pytest.raises(ValidationError, match="human principal type"):
        HumanDecisionPoint(state="review", decision="x", decider_role=PrincipalType.RUNTIME_AGENT)


# ---------------------------------------------------------------------------
# API envelopes
# ---------------------------------------------------------------------------


def _error(**overrides: Any) -> ErrorEnvelope:
    data: dict[str, Any] = {
        "error_class": ErrorClass.SCOPE_DENIED,
        "message": "destination not within envelope scope",
        "retryable": False,
        "dependency_id": "dep-scope-001",
        "operator_action": "Owner must extend the envelope's approved destinations",
        "correlation_id": "corr-001",
        "tenant_id": TENANT,
    }
    data.update(overrides)
    return ErrorEnvelope(**data)


def _job(**overrides: Any) -> JobEnvelope:
    data: dict[str, Any] = {
        "job_id": "job-001",
        "tenant_id": TENANT,
        "status": JobStatus.SUCCEEDED,
        "idempotency_key": "idem-7f3a",
        "operation": "startinventoryjob",
        "created_at": T0,
        "updated_at": T0 + timedelta(minutes=5),
        "result_ref": ArtifactRef(artifact_id="inv-001", kind=ArtifactKind.ENVIRONMENT_INVENTORY, digest=DIGEST),
        "server_assigned_version": 3,
        "request_payload_digest": DIGEST_2,
    }
    data.update(overrides)
    return JobEnvelope(**data)


def _event_envelope(**overrides: Any) -> EventEnvelope:
    data: dict[str, Any] = {
        "event_id": "ev-001",
        "tenant_id": TENANT,
        "aggregate_id": "build-001",
        "aggregate_version": 4,
        "event_type": "build.step_verified",
        "occurred_at": T0,
        "recorded_at": T0 + timedelta(seconds=2),
        "correlation_id": "corr-001",
        "causation_id": "cmd-001",
        "schema_version": "0.2.0",
        "payload_ref": "outbox://events/ev-001",
    }
    data.update(overrides)
    return EventEnvelope(**data)


@pytest.mark.requirements("PL-055")
def test_job_envelope_constructs_and_round_trips() -> None:
    _roundtrip(_job())
    _roundtrip(_job(status=JobStatus.FAILED, result_ref=None, error=_error()))
    waiting = _job(status=JobStatus.WAITING, result_ref=None, error=_error(error_class=ErrorClass.AUTH_REQUIRED))
    assert waiting.error is not None and waiting.error.error_class is ErrorClass.AUTH_REQUIRED


@pytest.mark.requirements("PL-055")
def test_job_status_and_result_are_consistent() -> None:
    with pytest.raises(ValidationError, match="SUCCEEDED job must carry result_ref"):
        _job(result_ref=None)
    with pytest.raises(ValidationError, match="FAILED job must carry an error"):
        _job(status=JobStatus.FAILED, result_ref=None)
    with pytest.raises(ValidationError, match="RUNNING job cannot carry result_ref"):
        _job(status=JobStatus.RUNNING)
    with pytest.raises(ValidationError, match="updated_at cannot precede created_at"):
        _job(updated_at=T0 - DAY)
    with pytest.raises(ValidationError):
        _job(server_assigned_version=0)
    with pytest.raises(ValidationError, match="must match the job's tenant"):
        _job(status=JobStatus.FAILED, result_ref=None, error=_error(tenant_id=OTHER_TENANT, message="denied"))


@pytest.mark.requirements("PL-056")
def test_error_message_never_reveals_other_tenants_or_secrets() -> None:
    with pytest.raises(ValidationError, match="other tenants' identifiers"):
        _error(message=f"resource belongs to {OTHER_TENANT}")
    own = _error(message=f"envelope for {TENANT} has expired")
    assert TENANT in own.message
    for fragment in ("password=hunter2", "client secret=abc", "access token=xyz"):
        with pytest.raises(ValidationError, match="carries a secret"):
            _error(message=f"upstream rejected {fragment}")


@pytest.mark.requirements("PL-056", "PL-004")
def test_authority_errors_are_not_retryable_and_name_their_resolution() -> None:
    with pytest.raises(ValidationError, match="cannot be retryable"):
        _error(retryable=True)
    with pytest.raises(ValidationError, match="cannot be retryable"):
        _error(error_class=ErrorClass.EFFECT_UNKNOWN, retryable=True)
    with pytest.raises(ValidationError, match="must name a dependency_id or operator_action"):
        _error(dependency_id=None, operator_action=None)
    transient = _error(error_class=ErrorClass.SOURCE_STALE, retryable=True, dependency_id=None, operator_action=None)
    assert transient.retryable


@pytest.mark.requirements("PL-055", "PL-057")
def test_event_envelope_round_trips_and_orders_time() -> None:
    _roundtrip(_event_envelope())
    with pytest.raises(ValidationError, match="recorded_at cannot precede occurred_at"):
        _event_envelope(recorded_at=T0 - timedelta(seconds=1))
    with pytest.raises(ValidationError):
        _event_envelope(aggregate_version=0)
    with pytest.raises(ValidationError, match="cannot cause itself"):
        _event_envelope(causation_id="ev-001")
    assert set(EventEnvelope.model_fields) == {
        "event_id",
        "tenant_id",
        "aggregate_id",
        "aggregate_version",
        "event_type",
        "occurred_at",
        "recorded_at",
        "correlation_id",
        "causation_id",
        "schema_version",
        "payload_ref",
    }


# ---------------------------------------------------------------------------
# Appendix A protocol records
# ---------------------------------------------------------------------------


def _task(**overrides: Any) -> AgentTask:
    data: dict[str, Any] = {
        "task_id": "task-001",
        "tenant_id": TENANT,
        "parent_build_id": "build-001",
        "parent_step_id": "step-integration-contract-test",
        "goal_ref": "goal-month-end",
        "acceptance_refs": ["acceptance-contract-tests-v1"],
        "input_artifact_refs": [ArtifactRef(artifact_id="int-001", kind=ArtifactKind.INTEGRATION_SPEC, digest=DIGEST)],
        "permitted_capabilities": ["cap-ledger-contract-test"],
        "scope": ResourceScope(source_ids=[LEDGER], regions=["us-east-1"]),
        "remaining_budget": Budget(spend=_money(50_000), max_attempts=3, max_elapsed_seconds=3600, max_model_calls=40),
        "workspace_base_digest": DIGEST_2,
        "fencing_token": 7,
    }
    data.update(overrides)
    return AgentTask(**data)


def _result(**overrides: Any) -> StepResult:
    data: dict[str, Any] = {
        "task_id": "task-001",
        "step_id": "step-integration-contract-test",
        "attempt": 1,
        "fencing_token": 7,
        "input_digests": [DIGEST],
        "output_digests": [DIGEST_2],
        "execution_environment_digest": "sha256:" + "ef" * 32,
        "tool_call_refs": ["toolcall-001"],
        "effect_refs": ["action-001"],
        "test_log_refs": ["log-contract-tests-001"],
        "claimed_postconditions": ["contract tests passed against sandbox account"],
        "cost_usage": _money(1_200),
        "unresolved_dependencies": [],
    }
    data.update(overrides)
    return StepResult(**data)


@pytest.mark.requirements("PL-004", "PL-058")
def test_agent_task_constructs_and_round_trips() -> None:
    task = _task()
    _roundtrip(task)
    with pytest.raises(ValidationError):
        _task(acceptance_refs=[])
    with pytest.raises(ValidationError):
        _task(permitted_capabilities=[])
    with pytest.raises(ValidationError, match="looks like a secret"):
        _task(goal_ref="goal-with-secret")
    with pytest.raises(ValidationError, match="duplicate digests"):
        _task(input_artifact_refs=[task.input_artifact_refs[0], task.input_artifact_refs[0]])


@pytest.mark.requirements("PL-016", "PL-042")
def test_step_result_round_trips_and_carries_only_claims() -> None:
    dependency = DependencyRecord(
        dependency_id="dep-001",
        failure_class=FailureClass.MISSING_AUTHORIZATION,
        error_class=ErrorClass.SCOPE_DENIED,
        description="Sandbox account lacks journal.write scope",
        missing_authority=["journal.write"],
        resolver_role=PrincipalType.HUMAN_OWNER,
        blocked_step_ids=["step-integration-contract-test"],
        raised_at=T0,
    )
    result = _result(unresolved_dependencies=[dependency], diagnostics="pagination test flaked once, then passed")
    _roundtrip(result)
    assert not any(marker in name for name in StepResult.model_fields for marker in FORBIDDEN_RESULT_FIELD_MARKERS)


@pytest.mark.requirements("PL-016", "PL-042")
@pytest.mark.parametrize("claim", ["verifier_attestation", "verified", "attestation_ref", "trusted", "production_ready"])
def test_step_result_rejects_verification_claims(claim: str) -> None:
    with pytest.raises(ValidationError, match="verifier attestations are separate records"):
        _result(**{claim: True})
    with pytest.raises(ValidationError):
        _result(unexpected_field=True)


@pytest.mark.requirements("PL-057", "PL-058")
def test_check_result_against_task_reports_stale_fencing_and_budget() -> None:
    task = _task()
    assert check_result_against_task(task, _result()) == []
    stale = check_result_against_task(task, _result(fencing_token=6))
    assert len(stale) == 1 and "stale fencing token" in stale[0]
    over = check_result_against_task(task, _result(attempt=4, cost_usage=_money(60_000)))
    assert any("exceeds max_attempts" in reason for reason in over)
    assert any("exceeds remaining spend" in reason for reason in over)
    wrong = check_result_against_task(task, _result(task_id="task-999", step_id="step-other", cost_usage=_money(1, "EUR")))
    assert len(wrong) == 3
