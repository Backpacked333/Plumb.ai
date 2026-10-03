"""Canonical models. Source of truth for contracts/generated-json-schema (see tools/gen_schemas.py).

Conventions
- Every model forbids unknown fields. An unknown field is a contract defect, not an extension point.
- Identifiers are opaque strings with a type prefix (tnt_, env_, grant_, plan_, step_, eff_ ...).
- Money is MoneyAmount (integer minor units + ISO 4217 currency). A bare float named "amount" is forbidden.
- Timestamps are timezone-aware ISO 8601 strings validated by pydantic AwareDatetime.
- `authority` annotations in field descriptions say who may set a value:
    derived   = computed by platform services from evidence
    asserted  = stated by an authenticated human principal
    external  = copied from an external source of record
    platform  = assigned by a trusted platform service (digests, ids, verifier outcomes)
  No model-controlled field may elevate a proposal into approval, verification or completion (SI-001).
"""
from __future__ import annotations

import re
from typing import Any, Literal, Optional

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

from .enums import (
    ApprovalKind,
    ApprovalState,
    BuildState,
    CapabilityKind,
    CaseState,
    CheckOutcome,
    CollectorState,
    CompensationClass,
    CoverageTier,
    DataRole,
    DatasetState,
    EffectClass,
    EffectState,
    FactStatus,
    GrantStatus,
    ImpactClass,
    LabelAuthority,
    LaborCategory,
    ObligationStatus,
    OpportunityRoute,
    OpportunityStatus,
    ProtectionClass,
    Purpose,
    ReleaseState,
    RemovalState,
    RetryClass,
    SolutionClass,
    StepState,
    StepType,
    TrainingState,
    VerificationLevel,
)

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
ID_RE = re.compile(r"^[a-z]{2,8}_[A-Za-z0-9_.-]{3,80}$")


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def _check_id(v: str, prefix: str) -> str:
    if not ID_RE.match(v) or not v.startswith(prefix + "_"):
        raise ValueError(f"identifier {v!r} must look like {prefix}_<token>")
    return v


class MoneyAmount(Strict):
    minor_units: int = Field(description="Integer amount in the currency's minor unit (cents for USD)")
    currency: str = Field(pattern=r"^[A-Z]{3}$", description="ISO 4217 code")


class Ref(Strict):
    """Reference to an artifact or record. Artifacts consumed by a run MUST carry a digest (SR-031)."""

    object_type: str = Field(pattern=r"^[A-Za-z]{3,40}$")
    id: str
    digest: Optional[str] = Field(default=None, description="platform: sha256 of canonical bytes")
    alias: Optional[str] = Field(default=None, description="Mutable alias the ref was resolved from, if any")

    @field_validator("digest")
    @classmethod
    def _digest_shape(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not DIGEST_RE.match(v):
            raise ValueError("digest must be sha256:<64 hex>")
        return v


class Port(Strict):
    """A typed input or output of a build step. A name alone is not a semantic type (SR-042)."""

    name: str = Field(pattern=r"^[a-z][a-z0-9_]{1,40}$")
    semantic_type: str = Field(description="e.g. money, timestamp, identifier, record_set, document, model_artifact")
    unit: Optional[str] = None
    currency: Optional[str] = Field(default=None, pattern=r"^[A-Z]{3}$")
    tz: Optional[str] = None
    scope: Optional[str] = Field(default=None, description="entity/account scope the value is valid for")
    nullable: bool = False
    freshness_max_s: Optional[int] = Field(default=None, ge=1)
    purpose_restrictions: list[Purpose] = Field(default_factory=list)

    @model_validator(mode="after")
    def _semantic_completeness(self) -> "Port":
        if self.semantic_type == "money" and self.currency is None:
            raise ValueError("money port requires currency")
        if self.semantic_type == "timestamp" and self.tz is None:
            raise ValueError("timestamp port requires tz")
        if self.semantic_type == "identifier" and self.scope is None:
            raise ValueError("identifier port requires scope (namespace)")
        return self


# ---------------------------------------------------------------- tenancy and authority


class Principal(Strict):
    principal_id: str
    tenant_id: str
    kind: Literal[
        "platform_operator",
        "tenant_owner",
        "employee",
        "domain_approver",
        "client_grantor",
        "sponsor",
        "service_identity",
        "build_worker",
        "runtime_worker",
        "verifier",
        "integration_manager",
    ]
    display_name: Optional[str] = None
    roles: list[str] = Field(default_factory=list)
    active: bool = True


class SourceGrant(Strict):
    """Observation/data-use authority (layer 1). Permission to read is not permission to train (SI-004)."""

    grant_id: str
    tenant_id: str
    grantor_principal_id: str = Field(description="asserted: authenticated grantor")
    provider: str
    account_ref: str = Field(description="external: verified provider account identity, never a display name")
    entity_scope: list[str] = Field(default_factory=list, description="business entities / clients covered")
    field_scope: list[str] = Field(default_factory=list, description="empty = all fields the provider exposes")
    purposes: list[Purpose]
    processors_allowed: list[str] = Field(default_factory=list)
    regions_allowed: list[str] = Field(default_factory=list)
    retention_days: int = Field(ge=1)
    history_from: Optional[AwareDatetime] = None
    granted_at: AwareDatetime
    expires_at: Optional[AwareDatetime] = None
    status: GrantStatus = GrantStatus.ACTIVE
    terms_version: Optional[str] = Field(default=None, description="provider terms version in force at grant time")

    @field_validator("grant_id")
    @classmethod
    def _id(cls, v: str) -> str:
        return _check_id(v, "grant")


class SpendCaps(Strict):
    build_max: MoneyAmount
    monthly_operation_max: MoneyAmount
    single_action_max: MoneyAmount


class EscalationRule(Strict):
    condition: str = Field(description="named condition from spec/authority-and-verification.md")
    route_to: str = Field(description="principal id or role")
    deadline_hours: int = Field(ge=1)


class AutonomyEnvelope(Strict):
    """Standing implementation and operation authority (layer 2). Versioned; a derived task cannot widen it."""

    envelope_id: str
    tenant_id: str
    version: int = Field(ge=1)
    owner_principal_id: str
    goals: list[str] = Field(min_length=1)
    source_grant_ids: list[str] = Field(min_length=1)
    processors_allowed: list[str]
    regions_allowed: list[str]
    destinations_allowed: list[str] = Field(description="destination patterns, e.g. mailbox:client_contacts, provider:quickbooks:realm_123")
    effect_classes_allowed: list[EffectClass]
    max_auto_impact: ImpactClass = Field(description="highest impact class deployable without a release approval")
    intervention_classes_allowed: list[SolutionClass]
    environments: list[Literal["sandbox", "shadow", "canary", "production"]]
    spend: SpendCaps
    expires_at: AwareDatetime
    escalation: list[EscalationRule]
    approval_id: Optional[str] = Field(default=None, description="detached approval binding this version")
    status: Literal["draft", "active", "expired", "revoked"] = "draft"

    @field_validator("envelope_id")
    @classmethod
    def _id(cls, v: str) -> str:
        return _check_id(v, "env")


# ---------------------------------------------------------------- inventory and capability


class OperationCapability(Strict):
    operation_id: str = Field(description="provider:operation, e.g. quickbooks:query.Purchase")
    kind: CapabilityKind
    verification_level: VerificationLevel
    verified_at: Optional[AwareDatetime] = None
    verified_by: Optional[str] = Field(default=None, description="platform: verifier identity")
    account_ref: Optional[str] = None
    limits: dict[str, Any] = Field(default_factory=dict)
    history_available_from: Optional[AwareDatetime] = None
    update_mechanism: Optional[Literal["webhook", "change_capture", "poll_overlap", "cdc", "none"]] = None
    expires_at: Optional[AwareDatetime] = Field(default=None, description="verification expiry")
    limitations: list[str] = Field(default_factory=list)
    documentation_ref: Optional[str] = None


class SystemInventory(Strict):
    provider: str
    account_ref: str
    entitlement: Optional[str] = None
    schema_version: Optional[str] = None
    owner_principal_id: Optional[str] = None
    operations: list[OperationCapability]


class EnvironmentInventory(Strict):
    inventory_id: str
    tenant_id: str
    produced_at: AwareDatetime
    systems: list[SystemInventory]
    coverage_notes: list[str] = Field(default_factory=list)
    content_digest: Optional[str] = None


# ---------------------------------------------------------------- evidence and knowledge


class ProtectionReport(Strict):
    omitted: list[str] = Field(default_factory=list)
    tokenized: list[str] = Field(default_factory=list)
    protected_refs: list[str] = Field(default_factory=list)
    clear: list[str] = Field(default_factory=list)


class EvidenceEvent(Strict):
    event_id: str
    tenant_id: str
    source_provider: str
    source_account_ref: str
    external_record_id: Optional[str] = None
    external_version: Optional[str] = None
    modality: Literal["screen", "accessibility", "dom", "message", "document", "recording", "api_record", "runtime_proof", "interview"]
    event_time: Optional[AwareDatetime] = Field(default=None, description="when the thing happened in the world; None = unknown")
    valid_from: Optional[AwareDatetime] = None
    valid_to: Optional[AwareDatetime] = None
    source_recorded_time: Optional[AwareDatetime] = None
    available_time: Optional[AwareDatetime] = Field(default=None, description="when the source could first have served it")
    ingested_time: AwareDatetime
    content_digest: str
    content_ref: Optional[str] = Field(default=None, description="object store reference; raw media is never copied here")
    access_policy_ref: str
    retention_class: str
    extraction_version: str
    protection: ProtectionReport = Field(default_factory=ProtectionReport)
    labels: dict[str, Any] = Field(default_factory=dict, description="derived labels with confidence")

    @field_validator("content_digest")
    @classmethod
    def _digest(cls, v: str) -> str:
        if not DIGEST_RE.match(v):
            raise ValueError("content_digest must be sha256:<64 hex>")
        return v


class EvidencePacket(Strict):
    packet_id: str
    tenant_id: str
    purpose: Purpose
    knowledge_boundary: AwareDatetime = Field(description="only events with available_time <= boundary are inside")
    event_refs: list[Ref]
    fact_refs: list[Ref] = Field(default_factory=list)
    grants_used: list[str]
    assembled_at: AwareDatetime
    coverage: dict[str, float] = Field(default_factory=dict, description="coverage fractions by dimension")
    truncated: bool = False


class Fact(Strict):
    fact_id: str
    tenant_id: str
    subject: Ref
    predicate: str
    value: Any
    status: FactStatus
    evidence: list[Ref] = Field(min_length=1)
    derivation_version: str
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    valid_from: Optional[AwareDatetime] = None
    valid_to: Optional[AwareDatetime] = None
    source_of_record: Optional[str] = Field(default=None, description="provider that is authoritative for this predicate")

    @model_validator(mode="after")
    def _authority(self) -> "Fact":
        if self.status == FactStatus.CONFIRMED and self.confidence is not None and self.confidence < 1.0:
            raise ValueError("a confirmed fact carries no residual confidence; confirmation is an authority, not a score")
        return self


class Obligation(Strict):
    obligation_id: str
    tenant_id: str
    obligor: Ref
    obligee: Ref
    engagement_ref: Optional[Ref] = None
    case_key: dict[str, str] = Field(description="e.g. {client: obj_client_0142, period: 2026-08}")
    rule_version: str
    fulfillment_predicate: str = Field(description="named predicate from the domain pack")
    due_at: Optional[AwareDatetime] = None
    status: ObligationStatus = ObligationStatus.OPEN
    epoch: int = Field(default=1, ge=1, description="increments on reopen or supersession; part of the effect slot")
    recurrence: Optional[str] = Field(default=None, description="RRULE or pack schedule id")
    evidence: list[Ref] = Field(default_factory=list)


# ---------------------------------------------------------------- opportunity and solution


class MetricEstimate(Strict):
    name: str
    unit: str
    point: float
    low: float
    high: float
    denominator: int = Field(ge=0, description="cases behind the estimate")
    method: str


class OpportunitySpec(Strict):
    opportunity_id: str
    tenant_id: str
    route: OpportunityRoute
    objective: str
    population: str = Field(description="query over business objects defining eligible cases")
    baseline: list[MetricEstimate]
    hypothesis: str
    suspected_bottleneck: Optional[str] = None
    evidence_packet_ref: Ref
    evidence_coverage: float = Field(ge=0.0, le=1.0)
    policy_dependencies: list[str] = Field(default_factory=list)
    known_exceptions: list[str] = Field(default_factory=list)
    expected_intervention: str
    credible_alternatives: list[str] = Field(default_factory=list)
    expected_benefit: list[MetricEstimate]
    expected_downside: str
    review_burden: Optional[MetricEstimate] = None
    falsifiers: list[str] = Field(min_length=1)
    hard_constraints: list[str] = Field(default_factory=list)
    measurement_plan: str
    status: OpportunityStatus = OpportunityStatus.HYPOTHESIS
    objective_accepted_by: Optional[str] = Field(default=None, description="asserted: principal who accepted the objective")


class CandidateDesign(Strict):
    candidate_id: str
    solution_class: SolutionClass
    components: list[str]
    joint_error_profile: str
    estimated_cost: MoneyAmount
    estimated_review_minutes_per_case: float = Field(ge=0)
    rejected_reason: Optional[str] = None


class SolutionSpec(Strict):
    solution_id: str
    tenant_id: str
    opportunity_ref: Ref
    baseline_candidate_id: str
    candidates: list[CandidateDesign] = Field(min_length=2, description="baseline plus at least one alternative")
    selected_candidate_id: str
    outcome_semantics: str = Field(description="completion predicate name the intervention delivers, e.g. review_package_prepared")
    policy_decisions: list[str] = Field(default_factory=list)
    decision_record: str
    impact_class: ImpactClass
    experiment_evidence: list[Ref] = Field(default_factory=list)
    content_digest: Optional[str] = None

    @model_validator(mode="after")
    def _selected_exists(self) -> "SolutionSpec":
        ids = {c.candidate_id for c in self.candidates}
        if self.selected_candidate_id not in ids or self.baseline_candidate_id not in ids:
            raise ValueError("selected and baseline candidates must be among candidates")
        return self


# ---------------------------------------------------------------- build plan


class VerificationObligation(Strict):
    check_id: str
    criteria_version: str
    data_role: DataRole = DataRole.REGRESSION


class BuildStep(Strict):
    step_id: str = Field(pattern=r"^step_[A-Za-z0-9_-]{2,60}$")
    type: StepType
    inputs: list[Ref] = Field(default_factory=list)
    input_ports: list[Port] = Field(default_factory=list)
    output_ports: list[Port] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    min_capability_level: VerificationLevel = VerificationLevel.SANDBOX_TESTED
    depends_on: list[str] = Field(default_factory=list)
    purposes_used: list[Purpose] = Field(default_factory=list)
    processors_used: list[str] = Field(default_factory=list)
    destinations: list[str] = Field(default_factory=list)
    effect_class: EffectClass = EffectClass.NONE
    compensation_class: CompensationClass = CompensationClass.NOT_NEEDED
    budget_max: MoneyAmount
    max_attempts: int = Field(ge=1, le=10)
    timeout_s: int = Field(ge=1, le=86400)
    max_iterations: Optional[int] = Field(default=None, ge=1, le=200, description="required for agent_loop")
    verification: list[VerificationObligation] = Field(default_factory=list)
    produces_release_artifact: bool = False
    notes: Optional[str] = None

    @model_validator(mode="after")
    def _loop_bound(self) -> "BuildStep":
        if self.type == StepType.AGENT_LOOP and self.max_iterations is None:
            raise ValueError("agent_loop requires max_iterations")
        return self


class BuildPlan(Strict):
    plan_id: str
    tenant_id: str
    solution_ref: Ref
    envelope_ref: Ref
    schema_version: str = "1.0"
    steps: list[BuildStep] = Field(min_length=1)
    total_budget_max: MoneyAmount
    release_schema_version: str = "1.0"
    case_migration_declared: bool = False
    content_digest: Optional[str] = None

    @field_validator("plan_id")
    @classmethod
    def _id(cls, v: str) -> str:
        return _check_id(v, "plan")


# ---------------------------------------------------------------- engineering harness (Appendix A of Source B, made concrete)


class BudgetReservation(Strict):
    reservation_id: str
    tenant_id: str
    build_id: str
    step_id: str
    attempt_no: int = Field(ge=1)
    reserved: MoneyAmount
    settled: Optional[MoneyAmount] = None
    status: Literal["reserved", "settled", "released"] = "reserved"


class TaskLease(Strict):
    lease_id: str
    task_id: str
    worker_id: str
    fencing_token: int = Field(ge=1, description="platform: monotonically increasing per task")
    acquired_at: AwareDatetime
    expires_at: AwareDatetime


class WorkspaceSnapshot(Strict):
    snapshot_id: str
    task_id: str
    base_digest: str
    commit_digest: str
    accepted_artifacts: list[Ref] = Field(default_factory=list)
    taken_at: AwareDatetime


class ExternalDependency(Strict):
    dependency_id: str
    tenant_id: str
    build_id: str
    step_id: Optional[str] = None
    kind: Literal["authorization", "business_decision", "access", "commitment", "unsupported_capability"]
    question: str
    options: list[dict[str, str]] = Field(default_factory=list)
    respondent_role: str
    default_after_hours: Optional[int] = None
    default_option: Optional[str] = Field(default=None, description="never a production action")
    status: Literal["open", "resolved", "withdrawn"] = "open"
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None


class FailureDiagnostic(Strict):
    diagnostic_id: str
    task_id: str
    attempt_no: int
    failure_class: Literal[
        "transient_infrastructure",
        "implementation_defect",
        "semantic_uncertainty",
        "missing_authorization",
        "missing_business_judgment",
        "unsupported_capability",
        "exhausted_resources",
        "source_schema_change",
        "poor_model_quality",
    ]
    hypothesis: str
    evidence_refs: list[Ref] = Field(default_factory=list)
    change_made: Optional[str] = None
    tests_to_rerun: list[str] = Field(default_factory=list)


class AgentTask(Strict):
    task_id: str
    tenant_id: str
    build_id: str
    step_id: str
    goal_ref: Ref
    acceptance_ref: Ref = Field(description="reference to the verification obligations; builder cannot edit the protected bundle")
    input_artifacts: list[Ref]
    permitted_capabilities: list[str]
    source_scope: list[str]
    destination_scope: list[str]
    remaining_spend: MoneyAmount
    remaining_time_s: int = Field(ge=0)
    remaining_attempts: int = Field(ge=0)
    workspace_base_digest: str
    prior_diagnostics: list[Ref] = Field(default_factory=list)
    lease: Optional[TaskLease] = None


class StepResult(Strict):
    """Proposed by the worker. Never changes a step to VERIFIED on its own (SR-055)."""

    task_id: str
    step_id: str
    attempt_no: int
    fencing_token: int
    input_digests: list[str]
    output_artifacts: list[Ref]
    environment_digest: str
    effect_refs: list[Ref] = Field(default_factory=list)
    test_log_refs: list[Ref] = Field(default_factory=list)
    claimed_postconditions: list[str] = Field(default_factory=list)
    cost_used: MoneyAmount
    unresolved_dependencies: list[str] = Field(default_factory=list)
    progress_summary: Optional[str] = Field(default=None, description="convenience only; not authoritative")


# ---------------------------------------------------------------- integrations and collection


class IntegrationSpec(Strict):
    integration_id: str
    tenant_id: str
    provider: str
    account_ref: str
    connection_grantor_id: str
    rung: Literal[1, 2, 3, 4, 5]
    operations: list[str]
    auth_ref: str = Field(description="vault reference, never a token value")
    scopes: list[str]
    schema_mappings: dict[str, str] = Field(default_factory=dict)
    cursor_strategy: Literal["webhook_then_fetch", "change_capture", "poll_overlap", "cdc", "manual"]
    rate_limits: dict[str, Any] = Field(default_factory=dict)
    retry_class: RetryClass
    deletion_behaviour: str
    effect_class: EffectClass
    verification_probes: list[str]
    schema_drift_policy: str
    capability_manifest_digest: Optional[str] = None
    maintenance_exposure: Literal["library", "generated", "ui_bridge"]


class QualityCheck(Strict):
    name: str
    rule: str
    on_fail: Literal["block", "degrade", "quarantine", "warn"]


class CollectionSpec(Strict):
    collection_id: str
    tenant_id: str
    purpose: Purpose
    objective_ref: Ref
    source_grant_ids: list[str] = Field(min_length=1)
    integration_ref: Ref
    account_scope: list[str]
    selected_fields: list[str]
    semantic_schema: list[Port]
    join_keys: list[str]
    update_mechanism: Literal["webhook_then_fetch", "change_capture", "poll_overlap", "cdc", "device_event", "valve_event"]
    overlap_window_s: Optional[int] = Field(default=None, ge=0)
    backfill_from: Optional[AwareDatetime] = None
    watermark_field: str
    storage_destination: str
    transformation_version: str
    quality_checks: list[QualityCheck]
    retention_days: int
    deletion_behaviour: Literal["tombstone_and_cascade", "tombstone_only"]
    downstream: list[str]
    budget_monthly: MoneyAmount
    completeness_claim: Literal["provable", "bounded", "sampled"]


# ---------------------------------------------------------------- learning


class DatasetRow(Strict):
    example_id: str
    family_id: str
    tenant_id: str
    permission_compartment: str
    input_snapshot_refs: list[Ref]
    decision_time: AwareDatetime
    source_availability_evidence: Ref
    target_evidence: Ref
    label_authority: LabelAuthority
    label_status: Literal["provisional", "mature", "amended", "disputed"]
    policy_version: str
    transformation_version: str
    allowed_purposes: list[Purpose]
    inclusion_reason: Optional[str] = None
    exclusion_reason: Optional[str] = None


class SplitRule(Strict):
    kind: Literal["temporal", "family_disjoint", "client_disjoint", "stratified"]
    detail: str
    answers_question: str


class DatasetManifest(Strict):
    dataset_id: str
    tenant_id: str
    version: int
    task_definition_ref: Ref
    roles: dict[DataRole, int] = Field(description="row counts by role")
    split_rules: list[SplitRule]
    knowledge_boundary_rule: str
    source_pins: list[Ref]
    transformation_version: str
    row_count: int = Field(ge=0)
    rejected_count: int = Field(ge=0)
    label_maturity: dict[str, int] = Field(default_factory=dict)
    distributions: dict[str, Any] = Field(default_factory=dict)
    content_digest: Optional[str] = None
    status: DatasetState = DatasetState.PROPOSED
    unavailable_reason: Optional[str] = None


class TrainingSpec(Strict):
    training_id: str
    tenant_id: str
    dataset_ref: Ref
    base_model: str
    method: str
    provider: str
    region: str
    objective: str
    resource_limits: dict[str, Any]
    spend_max: MoneyAmount
    stopping_condition: str
    data_handling_constraints: list[str]
    evaluation_plan_ref: Ref
    submission_identity: Optional[str] = Field(default=None, description="platform: persisted before provider call (SR-072)")
    provider_job_id: Optional[str] = None
    status: TrainingState = TrainingState.PLANNED


# ---------------------------------------------------------------- workflow (business runtime)


class WorkflowTransition(Strict):
    from_state: str
    event: str
    to_state: str
    guards: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)


class WorkflowAction(Strict):
    action_id: str
    operation_id: str
    effect_class: EffectClass
    compensation_class: CompensationClass
    retry_class: RetryClass
    requires_case_approval: bool
    recipient_scope: Optional[str] = None
    template_class: Optional[str] = None
    per_recipient_budget: Optional[int] = Field(default=None, ge=0, description="max messages per recipient per period")


class WorkflowSpec(Strict):
    workflow_id: str
    tenant_id: str
    case_key_fields: list[str] = Field(min_length=1)
    triggers: list[str] = Field(min_length=1)
    input_ports: list[Port]
    source_freshness: dict[str, int] = Field(default_factory=dict, description="source -> max age seconds")
    states: list[str] = Field(min_length=2)
    initial_state: str
    terminal_states: list[str] = Field(min_length=1)
    transitions: list[WorkflowTransition] = Field(min_length=1)
    actions: list[WorkflowAction] = Field(default_factory=list)
    durable_waits: list[str] = Field(default_factory=list)
    timers: dict[str, int] = Field(default_factory=dict)
    bounded_loops: dict[str, int] = Field(default_factory=dict, description="loop name -> max iterations")
    completion_predicate: str
    review_surfaces: list[str] = Field(default_factory=list)
    max_cost_per_case: MoneyAmount
    content_digest: Optional[str] = None

    @model_validator(mode="after")
    def _graph(self) -> "WorkflowSpec":
        st = set(self.states)
        if self.initial_state not in st:
            raise ValueError("initial_state not in states")
        for t in self.terminal_states:
            if t not in st:
                raise ValueError(f"terminal state {t} not in states")
        for tr in self.transitions:
            if tr.from_state not in st or tr.to_state not in st:
                raise ValueError(f"transition {tr.from_state}->{tr.to_state} references unknown state")
            if tr.from_state in self.terminal_states:
                raise ValueError(f"terminal state {tr.from_state} has an outgoing transition")
        return self


# ---------------------------------------------------------------- release, verification, approval


class ReleaseManifest(Strict):
    release_id: str
    tenant_id: str
    components: dict[str, Ref] = Field(description="kind -> ref with digest: workflow, connectors, collectors, models, prompts, rules, schemas, policies, infra")
    required_checks: list[str]
    schema_versions: dict[str, str]
    policy_version: str
    rollout: dict[str, Any]
    manifest_digest: Optional[str] = Field(default=None, description="platform: computed over canonical bytes excluding approvals")
    status: ReleaseState = ReleaseState.CANDIDATE

    @model_validator(mode="after")
    def _digests(self) -> "ReleaseManifest":
        for k, r in self.components.items():
            if r.digest is None:
                raise ValueError(f"component {k} lacks a digest")
        return self


class VerificationAttestation(Strict):
    attestation_id: str
    tenant_id: str
    check_id: str
    check_version: str
    criteria_version: str
    artifact_digests: list[str] = Field(min_length=1)
    input_digests: list[str] = Field(default_factory=list)
    environment: str
    account_scope: list[str] = Field(default_factory=list)
    data_role: DataRole
    outcome: CheckOutcome
    evidence_refs: list[Ref] = Field(default_factory=list)
    verifier_identity: str = Field(description="platform: verifier service identity, never the builder")
    issued_at: AwareDatetime
    expires_at: Optional[AwareDatetime] = None
    invalidation_conditions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    signature: Optional[str] = Field(default=None, description="detached signature over canonical bytes")


class Approval(Strict):
    approval_id: str
    tenant_id: str
    kind: ApprovalKind
    bound_digests: list[str] = Field(min_length=1, description="exact artifact or action digests this decision covers")
    prerequisite_state: dict[str, Any] = Field(default_factory=dict, description="e.g. case_version, release_state")
    scope: dict[str, Any] = Field(default_factory=dict)
    approver_principal_id: str
    policy_version: str
    nonce: str = Field(description="platform: single-use anti-replay token for link-based approvals")
    requested_at: AwareDatetime
    decided_at: Optional[AwareDatetime] = None
    expires_at: AwareDatetime
    decision: Optional[Literal["granted", "denied"]] = None
    status: ApprovalState = ApprovalState.REQUESTED

    @model_validator(mode="after")
    def _no_self_reference(self) -> "Approval":
        if self.approval_id in self.bound_digests:
            raise ValueError("approval cannot bind its own id")
        return self


# ---------------------------------------------------------------- external effects


class Receipt(Strict):
    receipt_id: str
    provider: str
    provider_request_id: Optional[str] = None
    provider_object_id: Optional[str] = None
    received_at: AwareDatetime
    verified: bool = Field(description="platform: signature/lookup verification result")
    raw_ref: Optional[str] = None


class DispatchAttempt(Strict):
    attempt_no: int
    lease_id: str
    fencing_token: int
    idempotency_key: str
    started_at: AwareDatetime
    finished_at: Optional[AwareDatetime] = None
    result: Literal["accepted", "rejected", "timeout", "crashed", "cancelled"]
    provider_request_id: Optional[str] = None


class ActionIntent(Strict):
    intent_id: str
    tenant_id: str
    case_ref: Ref
    obligation_ref: Optional[Ref] = None
    obligation_epoch: int = Field(ge=1)
    operation_id: str
    provider: str
    account_ref: str
    effect_slot: str = Field(description="platform: tenant|case|obligation_epoch|operation|target")
    logical_action_id: str
    payload_digest: str
    payload_ref: str
    expected_state_versions: dict[str, int]
    authority: dict[str, str] = Field(description="approval_id, envelope_version, release_id, grant_ids")
    cost_reservation_id: Optional[str] = None
    retry_class: RetryClass
    compensation_class: CompensationClass
    effect_class: EffectClass
    supersedes_intent_id: Optional[str] = None

    @field_validator("payload_digest")
    @classmethod
    def _digest(cls, v: str) -> str:
        if not DIGEST_RE.match(v):
            raise ValueError("payload_digest must be sha256:<64 hex>")
        return v


class EffectRecord(Strict):
    effect_id: str
    tenant_id: str
    intent_ref: Ref
    state: EffectState
    attempts: list[DispatchAttempt] = Field(default_factory=list)
    receipts: list[Receipt] = Field(default_factory=list)
    postconditions_verified: Optional[bool] = None
    reconciliation: Optional[Literal["confirmed", "not_occurred", "still_uncertain", "conflict", "needs_human"]] = None
    compensation_effect_id: Optional[str] = None
    last_transition_reason: Optional[str] = None


# ---------------------------------------------------------------- outcomes, ledgers, removal


class OutcomeObservation(Strict):
    observation_id: str
    tenant_id: str
    case_ref: Optional[Ref] = None
    release_ref: Optional[Ref] = None
    metric: str
    value: float
    unit: str
    method: Literal["prospective_cohort", "rollout_comparison", "direct_measurement", "survey", "timing_simulation"]
    cohort: Optional[str] = None
    observed_at: AwareDatetime
    limitations: list[str] = Field(default_factory=list)


class LaborRecord(Strict):
    record_id: str
    tenant_id: str
    build_id: Optional[str] = None
    case_ref: Optional[Ref] = None
    category: LaborCategory
    actor_role: str
    minutes: float = Field(ge=0)
    description: str
    recorded_at: AwareDatetime


class BillableUnitRecord(Strict):
    unit_id: str
    tenant_id: str
    case_ref: Ref
    predicate: str = Field(description="e.g. review_package_accepted; must equal the WorkflowSpec completion_predicate")
    release_ref: Ref
    satisfied_at: AwareDatetime
    status: Literal["billable", "credited", "superseded", "void"] = "billable"
    supersedes_unit_id: Optional[str] = None


class RemovalRequest(Strict):
    removal_id: str
    tenant_id: str
    requester_principal_id: str
    scope: dict[str, Any]
    legal_basis: Optional[str] = None
    status: RemovalState = RemovalState.RECEIVED
    impact: dict[str, Any] = Field(default_factory=dict)
    hold_reason: Optional[str] = None
    completion_evidence_ref: Optional[Ref] = None


class CoverageDecision(Strict):
    """Eligibility is decided before the outcome is known (PR-016)."""

    decision_id: str
    tenant_id: str
    opportunity_ref: Ref
    tier: CoverageTier
    criteria_version: str
    decided_at: AwareDatetime
    rationale: str


# ---------------------------------------------------------------- API envelopes and events


class JobEnvelope(Strict):
    job_id: str
    tenant_id: str
    kind: str
    status: Literal["queued", "running", "waiting", "succeeded", "failed", "cancelled"]
    created_at: AwareDatetime
    updated_at: AwareDatetime
    result_ref: Optional[Ref] = None
    dependency_id: Optional[str] = None
    error: Optional["ErrorEnvelope"] = None


class ErrorEnvelope(Strict):
    code: Literal[
        "AUTH_REQUIRED",
        "SCOPE_DENIED",
        "PURPOSE_DENIED",
        "POLICY_STALE",
        "STATE_CONFLICT",
        "PAYLOAD_CONFLICT",
        "BUDGET_EXCEEDED",
        "CAPABILITY_UNSUPPORTED",
        "SOURCE_STALE",
        "DATA_QUALITY_FAILED",
        "VERIFICATION_FAILED",
        "EFFECT_UNKNOWN",
        "RETRY_EXHAUSTED",
        "VALIDATION_FAILED",
        "NOT_FOUND",
        "RATE_LIMITED",
    ]
    message: str
    retryable: bool
    dependency_id: Optional[str] = None
    operator_action: Optional[str] = None
    details: list[dict[str, Any]] = Field(default_factory=list)


class EventEnvelope(Strict):
    event_id: str
    tenant_id: str
    aggregate_type: str
    aggregate_id: str
    aggregate_version: int = Field(ge=1)
    event_type: str
    schema_version: str
    occurred_at: AwareDatetime
    recorded_at: AwareDatetime
    correlation_id: str
    causation_id: Optional[str] = None
    payload_ref: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    tombstone: bool = False


JobEnvelope.model_rebuild()

TOP_LEVEL_MODELS: dict[str, type[Strict]] = {
    "Principal": Principal,
    "SourceGrant": SourceGrant,
    "AutonomyEnvelope": AutonomyEnvelope,
    "EnvironmentInventory": EnvironmentInventory,
    "EvidenceEvent": EvidenceEvent,
    "EvidencePacket": EvidencePacket,
    "Fact": Fact,
    "Obligation": Obligation,
    "OpportunitySpec": OpportunitySpec,
    "SolutionSpec": SolutionSpec,
    "BuildPlan": BuildPlan,
    "AgentTask": AgentTask,
    "TaskLease": TaskLease,
    "StepResult": StepResult,
    "WorkspaceSnapshot": WorkspaceSnapshot,
    "BudgetReservation": BudgetReservation,
    "ExternalDependency": ExternalDependency,
    "FailureDiagnostic": FailureDiagnostic,
    "IntegrationSpec": IntegrationSpec,
    "CollectionSpec": CollectionSpec,
    "DatasetRow": DatasetRow,
    "DatasetManifest": DatasetManifest,
    "TrainingSpec": TrainingSpec,
    "WorkflowSpec": WorkflowSpec,
    "ReleaseManifest": ReleaseManifest,
    "VerificationAttestation": VerificationAttestation,
    "Approval": Approval,
    "ActionIntent": ActionIntent,
    "EffectRecord": EffectRecord,
    "OutcomeObservation": OutcomeObservation,
    "LaborRecord": LaborRecord,
    "BillableUnitRecord": BillableUnitRecord,
    "RemovalRequest": RemovalRequest,
    "CoverageDecision": CoverageDecision,
    "JobEnvelope": JobEnvelope,
    "ErrorEnvelope": ErrorEnvelope,
    "EventEnvelope": EventEnvelope,
}
