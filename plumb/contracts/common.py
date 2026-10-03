"""Shared primitives for every Plumb contract.

Everything in this module is referenced by several top-level contracts, by the
reference checker, by the effect ledger and by the state machines. Keep it
dependency-free (standard library + Pydantic only).

Design notes (specification v0.2):

* PL-004: every operation carries tenant, acting principal, purpose, resource
  scope, capability version, policy version and budget allocation
  (:class:`OperationContext`).
* PL-009 / ADR-005: evidence carries several time axes; event/valid time is
  stored separately from observation and availability time (:class:`TimeAxes`).
* PL-010: derived facts carry a status from a closed vocabulary
  (:class:`FactStatus`); unknown absence stays distinguishable from confirmed
  absence (:class:`Presence`).
* Section 22: the initial error classes (:class:`ErrorClass`).
* Section 23: aggregate lifecycles (the ``*State`` enums).
* Money is carried in integer minor units with an explicit currency so that an
  amount in cents can never be mapped into a dollars field by accident
  (section 10).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

SCHEMA_VERSION = "0.2.0"
"""Schema version stamped on every artifact header produced by this package."""


# ---------------------------------------------------------------------------
# Base model
# ---------------------------------------------------------------------------


class StrictModel(BaseModel):
    """Base for all contracts: unknown fields are rejected, strings are stripped."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=False,
    )


# ---------------------------------------------------------------------------
# Constrained scalar types
# ---------------------------------------------------------------------------

Identifier = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z][a-z0-9_.:/-]{0,159}$"),
]
"""Lower-case machine identifier for steps, artifacts, sources, capabilities."""

TenantId = Annotated[str, StringConstraints(pattern=r"^tnt_[a-z0-9]{4,32}$")]
"""Tenant identity. Derived from verified authentication, never from a body (PL-004)."""

Sha256Digest = Annotated[str, StringConstraints(pattern=r"^sha256:[0-9a-f]{64}$")]
"""Content digest of an immutable artifact or payload."""

SemVer = Annotated[str, StringConstraints(pattern=r"^\d+\.\d+\.\d+$")]

Region = Annotated[str, StringConstraints(pattern=r"^[a-z]{2,3}(-[a-z0-9]+)*$")]
"""Deployment / processing region label, e.g. ``us-east-1`` or ``eu``."""

CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]

OpaqueCursor = Annotated[str, StringConstraints(min_length=1, max_length=512)]

NonEmptyStr = Annotated[str, StringConstraints(min_length=1, max_length=4000)]

ShortStr = Annotated[str, StringConstraints(min_length=1, max_length=256)]


# ---------------------------------------------------------------------------
# Closed vocabularies
# ---------------------------------------------------------------------------


class EffectClass(str, Enum):
    """What an operation may do to the world. Envelopes allow a subset (PL-005)."""

    READ = "READ"
    INTERNAL_WRITE = "INTERNAL_WRITE"
    EXTERNAL_WRITE_REVERSIBLE = "EXTERNAL_WRITE_REVERSIBLE"
    EXTERNAL_WRITE_IRREVERSIBLE = "EXTERNAL_WRITE_IRREVERSIBLE"
    EXTERNAL_COMMUNICATION = "EXTERNAL_COMMUNICATION"
    FINANCIAL_COMMITMENT = "FINANCIAL_COMMITMENT"
    INFRASTRUCTURE_CHANGE = "INFRASTRUCTURE_CHANGE"
    DESTRUCTIVE = "DESTRUCTIVE"


class DataPurpose(str, Enum):
    """Data-purpose authorization is enforced per stage (PL-053)."""

    INSPECT = "INSPECT"
    COLLECT = "COLLECT"
    TRANSFORM = "TRANSFORM"
    EVALUATE = "EVALUATE"
    TRAIN = "TRAIN"
    SERVE = "SERVE"
    EXPORT = "EXPORT"


class PrincipalType(str, Enum):
    HUMAN_OWNER = "HUMAN_OWNER"
    HUMAN_REVIEWER = "HUMAN_REVIEWER"
    HUMAN_APPROVER = "HUMAN_APPROVER"
    SERVICE = "SERVICE"
    BUILD_AGENT = "BUILD_AGENT"
    RUNTIME_AGENT = "RUNTIME_AGENT"
    VERIFIER = "VERIFIER"
    RELEASE_EXECUTOR = "RELEASE_EXECUTOR"


class HumanEffortCategory(str, Enum):
    """All human effort is recorded by category (PL-003)."""

    CUSTOMER_AUTHORIZATION = "CUSTOMER_AUTHORIZATION"
    DOMAIN_CLARIFICATION = "DOMAIN_CLARIFICATION"
    NORMAL_BUSINESS_REVIEW = "NORMAL_BUSINESS_REVIEW"
    ENGINEERING_INTERVENTION = "ENGINEERING_INTERVENTION"
    OPERATIONAL_REPAIR = "OPERATIONAL_REPAIR"


class ErrorClass(str, Enum):
    """Initial error classes of the control-plane protocol (section 22)."""

    AUTH_REQUIRED = "AUTH_REQUIRED"
    SCOPE_DENIED = "SCOPE_DENIED"
    PURPOSE_DENIED = "PURPOSE_DENIED"
    POLICY_STALE = "POLICY_STALE"
    STATE_CONFLICT = "STATE_CONFLICT"
    PAYLOAD_CONFLICT = "PAYLOAD_CONFLICT"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    CAPABILITY_UNSUPPORTED = "CAPABILITY_UNSUPPORTED"
    SOURCE_STALE = "SOURCE_STALE"
    DATA_QUALITY_FAILED = "DATA_QUALITY_FAILED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    EFFECT_UNKNOWN = "EFFECT_UNKNOWN"
    RETRY_EXHAUSTED = "RETRY_EXHAUSTED"


class FailureClass(str, Enum):
    """Failure classification that determines the next action (section 9, Appendix A.3)."""

    TRANSIENT_INFRASTRUCTURE = "TRANSIENT_INFRASTRUCTURE"
    IMPLEMENTATION_DEFECT = "IMPLEMENTATION_DEFECT"
    SOURCE_SCHEMA_CHANGE = "SOURCE_SCHEMA_CHANGE"
    MISSING_AUTHORIZATION = "MISSING_AUTHORIZATION"
    MISSING_BUSINESS_DECISION = "MISSING_BUSINESS_DECISION"
    UNSUPPORTED_CAPABILITY = "UNSUPPORTED_CAPABILITY"
    POOR_MODEL_QUALITY = "POOR_MODEL_QUALITY"
    EXHAUSTED_RESOURCES = "EXHAUSTED_RESOURCES"


class CapabilityMaturity(str, Enum):
    """Discovered, documented, sandbox-tested and production-verified are distinct (PL-008)."""

    DISCOVERED = "DISCOVERED"
    DOCUMENTED = "DOCUMENTED"
    SANDBOX_TESTED = "SANDBOX_TESTED"
    PRODUCTION_VERIFIED = "PRODUCTION_VERIFIED"


class FactStatus(str, Enum):
    """Status vocabulary for derived facts (PL-010)."""

    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    CONFIRMED = "CONFIRMED"
    DISPUTED = "DISPUTED"
    STALE = "STALE"
    SUPERSEDED = "SUPERSEDED"


class Presence(str, Enum):
    """Unknown absence must remain distinguishable from confirmed absence (PL-010)."""

    PRESENT = "PRESENT"
    CONFIRMED_ABSENT = "CONFIRMED_ABSENT"
    UNKNOWN = "UNKNOWN"


class VerificationLevel(str, Enum):
    """The five verification levels (section 18)."""

    SCHEMA_VALIDITY = "SCHEMA_VALIDITY"
    ARTIFACT_INTEGRITY = "ARTIFACT_INTEGRITY"
    INTEGRATION_BEHAVIOR = "INTEGRATION_BEHAVIOR"
    BUSINESS_OUTCOME = "BUSINESS_OUTCOME"
    ECONOMIC_RESULT = "ECONOMIC_RESULT"


class LabelKind(str, Enum):
    """Observable outcomes, expert decisions, corrections, preferences and weak proxies differ (PL-026)."""

    OBSERVED_OUTCOME = "OBSERVED_OUTCOME"
    EXPERT_DECISION = "EXPERT_DECISION"
    CORRECTION = "CORRECTION"
    PREFERENCE = "PREFERENCE"
    WEAK_PROXY = "WEAK_PROXY"


class LabelStatus(str, Enum):
    """Row-level label status; quarantined rows never enter training inputs (PL-027)."""

    ACCEPTED = "ACCEPTED"
    QUARANTINED_AMBIGUOUS = "QUARANTINED_AMBIGUOUS"
    QUARANTINED_INCONSISTENT = "QUARANTINED_INCONSISTENT"
    QUARANTINED_DISPUTED = "QUARANTINED_DISPUTED"
    REJECTED = "REJECTED"


class ArtifactKind(str, Enum):
    """Kinds of stored artifacts. The first 17 are the top-level contracts of this package."""

    AUTONOMY_ENVELOPE = "AutonomyEnvelope"
    CAPABILITY_RECORD = "CapabilityRecord"
    ENVIRONMENT_INVENTORY = "EnvironmentInventory"
    EVIDENCE_PACKET = "EvidencePacket"
    OPPORTUNITY_SPEC = "OpportunitySpec"
    BUILD_PLAN = "BuildPlan"
    INTEGRATION_SPEC = "IntegrationSpec"
    COLLECTION_SPEC = "CollectionSpec"
    DATASET_MANIFEST = "DatasetManifest"
    TRAINING_SPEC = "TrainingSpec"
    WORKFLOW_SPEC = "WorkflowSpec"
    EVALUATION_REPORT = "EvaluationReport"
    INFRASTRUCTURE_PLAN = "InfrastructurePlan"
    RELEASE_MANIFEST = "ReleaseManifest"
    ACTION_INTENT = "ActionIntent"
    APPROVAL_RECORD = "ApprovalRecord"
    VERIFICATION_ATTESTATION = "VerificationAttestation"
    # Supporting / generated artifacts that steps may produce or consume.
    ADAPTER_CODE = "AdapterCode"
    ADAPTER_CONFIGURATION = "AdapterConfiguration"
    TRANSFORMATION_CODE = "TransformationCode"
    TEST_BUNDLE = "TestBundle"
    PROBE_RECEIPT = "ProbeReceipt"
    VERIFICATION_RECEIPT = "VerificationReceipt"
    QUALITY_REPORT = "QualityReport"
    LABEL_AUDIT_REPORT = "LabelAuditReport"
    SOURCE_CANDIDATE_TABLE = "SourceCandidateTable"
    TASK_DEFINITION = "TaskDefinition"
    MODEL_VERSION = "ModelVersion"
    SERVING_CONFIGURATION = "ServingConfiguration"
    CANDIDATE_COMPARISON = "CandidateComparison"
    INFRASTRUCTURE_PREVIEW = "InfrastructurePreview"
    CANARY_REPORT = "CanaryReport"
    DEPENDENCY_RECORD = "DependencyRecord"
    REVIEW_PACKAGE = "ReviewPackage"


# --- Aggregate lifecycles (section 23) --------------------------------------


class BuildState(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    RUNNING = "RUNNING"
    WAITING_AUTH = "WAITING_AUTH"
    WAITING_INPUT = "WAITING_INPUT"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class BuildStepState(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


class CollectorState(str, Enum):
    PLANNED = "PLANNED"
    SHADOW = "SHADOW"
    BACKFILLING = "BACKFILLING"
    RECONCILING = "RECONCILING"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    PAUSED = "PAUSED"
    RETIRED = "RETIRED"


class DatasetState(str, Enum):
    PROPOSED = "PROPOSED"
    MATERIALIZING = "MATERIALIZING"
    QUARANTINED = "QUARANTINED"
    VERIFIED = "VERIFIED"
    SUPERSEDED = "SUPERSEDED"
    UNAVAILABLE = "UNAVAILABLE"


class TrainingState(str, Enum):
    PLANNED = "PLANNED"
    SUBMITTED = "SUBMITTED"
    RUNNING = "RUNNING"
    CANDIDATE = "CANDIDATE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ReleaseState(str, Enum):
    CANDIDATE = "CANDIDATE"
    VERIFIED = "VERIFIED"
    SHADOW = "SHADOW"
    CANARY = "CANARY"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ROLLED_BACK = "ROLLED_BACK"
    RETIRED = "RETIRED"


class EffectState(str, Enum):
    RESERVED = "RESERVED"
    DISPATCHED = "DISPATCHED"
    UNKNOWN = "UNKNOWN"
    CONFIRMED = "CONFIRMED"
    FAILED_FINAL = "FAILED_FINAL"
    COMPENSATED = "COMPENSATED"


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


class Money(StrictModel):
    """An amount in integer minor units (cents) plus an ISO 4217 currency code."""

    minor_units: int = Field(ge=0, description="Amount in the currency's minor unit (e.g. cents).")
    currency: CurrencyCode = Field(description="ISO 4217 code, e.g. USD.")

    def __add__(self, other: "Money") -> "Money":
        if other.currency != self.currency:
            raise ValueError(f"currency mismatch: {self.currency} vs {other.currency}")
        return Money(minor_units=self.minor_units + other.minor_units, currency=self.currency)

    def exceeds(self, other: "Money") -> bool:
        if other.currency != self.currency:
            raise ValueError(f"currency mismatch: {self.currency} vs {other.currency}")
        return self.minor_units > other.minor_units


class Budget(StrictModel):
    """Worst-case reservation for a unit of work (PL-014, PL-018, PL-058)."""

    spend: Money
    max_attempts: int = Field(ge=1, le=1000)
    max_elapsed_seconds: int = Field(ge=1)
    max_model_calls: int | None = Field(default=None, ge=0)


class TimeAxes(StrictModel):
    """Separate time axes for evidence (PL-009, ADR-005).

    ``event_time`` is when the described thing happened (valid time).
    ``observation_time`` is when Plumb observed it at the source.
    ``availability_time`` is when it became available to Plumb's decision
    boundary (knowledge time). Availability can never precede observation.
    """

    event_time: datetime
    observation_time: datetime
    availability_time: datetime

    @model_validator(mode="after")
    def _availability_not_before_observation(self) -> "TimeAxes":
        if self.availability_time < self.observation_time:
            raise ValueError("availability_time cannot precede observation_time")
        return self


class Principal(StrictModel):
    """An authenticated acting principal."""

    principal_id: Identifier
    principal_type: PrincipalType
    authenticated_via: ShortStr = Field(
        description="Authentication mechanism reference (e.g. oidc:issuer), never a secret."
    )


class ResourceScope(StrictModel):
    """Sources, destinations, processors and regions an operation may touch."""

    source_ids: list[Identifier] = Field(default_factory=list)
    destination_ids: list[Identifier] = Field(default_factory=list)
    processor_ids: list[Identifier] = Field(default_factory=list)
    regions: list[Region] = Field(default_factory=list)

    def is_within(self, outer: "ResourceScope") -> list[str]:
        """Return a list of human-readable violations where ``self`` exceeds ``outer``."""
        violations: list[str] = []
        for name in ("source_ids", "destination_ids", "processor_ids", "regions"):
            extra = sorted(set(getattr(self, name)) - set(getattr(outer, name)))
            if extra:
                violations.append(f"{name} not in scope: {', '.join(extra)}")
        return violations


class OperationContext(StrictModel):
    """Mandatory context on every operation (PL-004)."""

    tenant_id: TenantId
    principal: Principal
    purpose: DataPurpose
    resource_scope: ResourceScope
    capability_version: SemVer
    policy_version: SemVer
    budget_allocation: Budget


class SourceRef(StrictModel):
    """A reference to an authorized external source/account. Never carries credentials."""

    source_id: Identifier
    provider: ShortStr
    external_account_id: ShortStr = Field(
        description="Provider-assigned account identity (opaque, non-secret)."
    )
    resource: ShortStr | None = Field(
        default=None, description="Resource within the account, e.g. mailbox or ledger name."
    )


class Provenance(StrictModel):
    """Who/what produced an artifact or fact, from which evidence, at which derivation version."""

    producer: Identifier
    produced_at: datetime
    derivation_version: SemVer
    evidence_refs: list[Identifier] = Field(default_factory=list)


class ArtifactRef(StrictModel):
    """Immutable reference to a stored artifact by digest (section 8)."""

    artifact_id: Identifier
    kind: ArtifactKind
    digest: Sha256Digest
    schema_version: SemVer = SCHEMA_VERSION


class ArtifactHeader(StrictModel):
    """Fields every stored artifact carries (section 8).

    ``content_digest`` is assigned by the artifact store over the canonical JSON
    of the artifact with this field blank; see :func:`compute_artifact_digest`.
    """

    artifact_id: Identifier
    tenant_id: TenantId
    kind: ArtifactKind
    schema_version: SemVer = SCHEMA_VERSION
    version: int = Field(ge=1, description="Immutable version number of this artifact id.")
    content_digest: Sha256Digest | None = None
    producer: Principal
    created_at: datetime
    evidence_links: list[Identifier] = Field(default_factory=list)


class DependencyRecord(StrictModel):
    """A precise, resumable external dependency (PL-001, Appendix A ``dependency.raise``)."""

    dependency_id: Identifier
    failure_class: FailureClass
    error_class: ErrorClass
    description: NonEmptyStr
    missing_authority: list[ShortStr] = Field(
        default_factory=list, description="Exact grants, consents or decisions required."
    )
    resolver_role: PrincipalType
    blocked_step_ids: list[Identifier] = Field(default_factory=list)
    resumes_after: NonEmptyStr | None = Field(
        default=None, description="What continues once the dependency is supplied."
    )
    raised_at: datetime


class HumanEffortRecord(StrictModel):
    """Recorded human effort by category (PL-003, PL-062)."""

    category: HumanEffortCategory
    principal: Principal
    minutes: int = Field(ge=0)
    description: NonEmptyStr
    recorded_at: datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def canonical_json(data: Any) -> bytes:
    """Deterministic JSON encoding used for all digests in this package."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode(
        "utf-8"
    )


def digest_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def digest_json(data: Any) -> str:
    """Digest of any JSON-serialisable value via :func:`canonical_json`."""
    return digest_bytes(canonical_json(data))


def compute_artifact_digest(model: BaseModel) -> str:
    """Digest of an artifact: canonical JSON with ``content_digest`` removed."""
    data = model.model_dump(mode="json")
    data.pop("content_digest", None)
    return digest_json(data)


__all__ = [
    "SCHEMA_VERSION",
    "StrictModel",
    "Identifier",
    "TenantId",
    "Sha256Digest",
    "SemVer",
    "Region",
    "CurrencyCode",
    "OpaqueCursor",
    "NonEmptyStr",
    "ShortStr",
    "EffectClass",
    "DataPurpose",
    "PrincipalType",
    "HumanEffortCategory",
    "ErrorClass",
    "FailureClass",
    "CapabilityMaturity",
    "FactStatus",
    "Presence",
    "VerificationLevel",
    "LabelKind",
    "LabelStatus",
    "ArtifactKind",
    "BuildState",
    "BuildStepState",
    "CollectorState",
    "DatasetState",
    "TrainingState",
    "ReleaseState",
    "EffectState",
    "Money",
    "Budget",
    "TimeAxes",
    "Principal",
    "ResourceScope",
    "OperationContext",
    "SourceRef",
    "Provenance",
    "ArtifactRef",
    "ArtifactHeader",
    "DependencyRecord",
    "HumanEffortRecord",
    "utcnow",
    "canonical_json",
    "digest_bytes",
    "digest_json",
    "compute_artifact_digest",
]
