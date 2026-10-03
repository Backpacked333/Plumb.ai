"""CollectionSpec: continuing evidence capture for one objective (specification section 11).

Implements:

* PL-023: the spec identifies the objective it supports, allowed sources,
  selected fields, join strategy, incremental mechanism, retention,
  destination, access policy, quality checks and the evidence that the purpose
  is permitted (``permitted_purpose_evidence_ref`` is required: collection is
  justified by the active customer use case, never by default).
* PL-024: backfill and live capture converge without silent gaps or
  duplicates. The spec carries cursors, a watermark, a backfill boundary and a
  non-empty idempotent event identity; reordered events and later corrections
  have explicit policies; polling declares a positive overlap window; a
  webhook is a signal to fetch authoritative state
  (``webhook_fetches_authoritative_state`` must be true for ``WEBHOOK``);
  source-count reconciliation is mandatory.
* PL-025: the collector publishes freshness, lag, completeness and failure
  state through :class:`HealthContract`, and downstream work blocks or degrades
  explicitly when coverage is missing (``downstream_block_on_missing_coverage``
  must be true), so a stopped collector never makes an obligation appear
  satisfied by default.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from plumb.contracts.common import (
    ArtifactHeader,
    ArtifactKind,
    Identifier,
    NonEmptyStr,
    OpaqueCursor,
    Region,
    ShortStr,
    SourceRef,
    StrictModel,
)
from plumb.contracts.inventory import NonSecretRef


class IncrementalMechanism(str, Enum):
    """How continuing changes are captured (PL-023, section 11)."""

    WEBHOOK = "WEBHOOK"
    POLLING_OVERLAP = "POLLING_OVERLAP"
    CDC = "CDC"
    EXPORT = "EXPORT"


class JoinKind(str, Enum):
    EXACT_KEY = "EXACT_KEY"
    NORMALIZED_IDENTITY = "NORMALIZED_IDENTITY"
    RESOLVED_OBJECT = "RESOLVED_OBJECT"


class ReorderingPolicy(str, Enum):
    """How out-of-order events are handled; it must be chosen explicitly (PL-024)."""

    SOURCE_VERSION_WINS = "SOURCE_VERSION_WINS"
    LATEST_OBSERVATION_WINS = "LATEST_OBSERVATION_WINS"
    QUARANTINE_OUT_OF_ORDER = "QUARANTINE_OUT_OF_ORDER"


class CorrectionPolicy(str, Enum):
    """How later corrections to already-captured records are handled (PL-024)."""

    NEW_VERSION_SUPERSEDES = "NEW_VERSION_SUPERSEDES"
    QUARANTINE_FOR_REVIEW = "QUARANTINE_FOR_REVIEW"


class DeletionHandling(str, Enum):
    PROPAGATE_DELETE = "PROPAGATE_DELETE"
    TOMBSTONE = "TOMBSTONE"
    RETAIN_WITH_FLAG = "RETAIN_WITH_FLAG"


class CheckSeverity(str, Enum):
    BLOCK = "BLOCK"
    WARN = "WARN"


class JoinStrategy(StrictModel):
    kind: JoinKind
    keys: list[ShortStr] = Field(min_length=1)


class Watermark(StrictModel):
    """Agreed point from which backfill proceeds (section 11)."""

    field: ShortStr
    value: ShortStr
    as_of: AwareDatetime


class BackfillBoundary(StrictModel):
    start: AwareDatetime
    end: AwareDatetime | None = Field(default=None, description="None while backfill is open-ended.")
    agreed_by: Identifier = Field(description="Principal who agreed the boundary.")

    @model_validator(mode="after")
    def _ordered(self) -> "BackfillBoundary":
        if self.end is not None and self.end < self.start:
            raise ValueError("backfill end cannot precede start")
        return self


class SourceCursor(StrictModel):
    """Current position in one source (PL-024)."""

    source_id: Identifier
    cursor: OpaqueCursor
    processing_offset: int = Field(ge=0)
    updated_at: AwareDatetime


class Reconciliation(StrictModel):
    """How backfill and live capture are shown to converge (PL-024)."""

    source_count_reconciliation: bool = Field(description="Must be true: counts are compared against the source.")
    sampled_identity_reconciliation: bool = True
    sample_size: int = Field(ge=1)

    @model_validator(mode="after")
    def _counts_reconciled(self) -> "Reconciliation":
        if not self.source_count_reconciliation:
            raise ValueError("source_count_reconciliation must be true; a cron job alone is not evidence of convergence")
        return self


class Retention(StrictModel):
    retention_days: int = Field(ge=0)
    deletion_handling: DeletionHandling


class Destination(StrictModel):
    destination_id: Identifier
    region: Region
    schema_ref: NonSecretRef


class QualityCheck(StrictModel):
    name: Identifier
    expression: NonEmptyStr
    severity: CheckSeverity = CheckSeverity.BLOCK


class HealthContract(StrictModel):
    """What the collector publishes; all four signals are mandatory (PL-025)."""

    freshness_deadline_seconds: int = Field(ge=1)
    lag_metric: Identifier
    completeness_metric: Identifier
    failure_state_metric: Identifier


class CollectionSpec(ArtifactHeader):
    """Specification of one collector (PL-023..PL-025)."""

    kind: Literal[ArtifactKind.COLLECTION_SPEC] = ArtifactKind.COLLECTION_SPEC
    collection_id: Identifier
    objective_ref: Identifier = Field(description="Goal or opportunity the collection serves.")
    allowed_sources: list[SourceRef] = Field(min_length=1)
    selected_fields: list[ShortStr] = Field(min_length=1)
    join_strategy: JoinStrategy
    incremental_mechanism: IncrementalMechanism
    overlap_seconds: int | None = Field(default=None, ge=1, description="Polling window overlap.")
    webhook_fetches_authoritative_state: bool = Field(
        default=False, description="A webhook is a signal to fetch authoritative state; must be true for WEBHOOK."
    )
    reordering_policy: ReorderingPolicy
    correction_policy: CorrectionPolicy
    watermark: Watermark
    backfill_boundary: BackfillBoundary
    idempotent_event_identity: list[ShortStr] = Field(min_length=1, description="Fields forming the stable event key.")
    cursors: list[SourceCursor] = Field(default_factory=list)
    reconciliation: Reconciliation
    retention: Retention
    destination: Destination
    access_policy_ref: NonSecretRef
    quality_checks: list[QualityCheck] = Field(min_length=1)
    permitted_purpose_evidence_ref: NonSecretRef = Field(
        description="Grant or approval that justifies collecting these fields for this objective."
    )
    health: HealthContract
    downstream_block_on_missing_coverage: bool = Field(
        description="Must be true: downstream work blocks or degrades explicitly when coverage is missing."
    )

    @model_validator(mode="after")
    def _coherent_collection(self) -> "CollectionSpec":
        source_ids = [source.source_id for source in self.allowed_sources]
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("allowed_sources must have distinct source_ids")
        if len(set(self.selected_fields)) != len(self.selected_fields):
            raise ValueError("selected_fields must not contain duplicates")
        if len(set(self.idempotent_event_identity)) != len(self.idempotent_event_identity):
            raise ValueError("idempotent_event_identity must not contain duplicates")
        if self.incremental_mechanism is IncrementalMechanism.POLLING_OVERLAP and self.overlap_seconds is None:
            raise ValueError("POLLING_OVERLAP requires overlap_seconds > 0; a single maximum timestamp misses ties")
        if self.incremental_mechanism is IncrementalMechanism.WEBHOOK and not self.webhook_fetches_authoritative_state:
            raise ValueError(
                "WEBHOOK collection must fetch authoritative state; a webhook payload is a signal, not the record"
            )
        unknown_cursors = sorted({cursor.source_id for cursor in self.cursors} - set(source_ids))
        if unknown_cursors:
            raise ValueError(f"cursors reference sources not in allowed_sources: {', '.join(unknown_cursors)}")
        check_names = [check.name for check in self.quality_checks]
        if len(set(check_names)) != len(check_names):
            raise ValueError("quality_checks must have distinct names")
        if not self.downstream_block_on_missing_coverage:
            raise ValueError(
                "downstream_block_on_missing_coverage must be true; a stopped collector must never make an "
                "obligation appear satisfied or unsatisfied by default"
            )
        return self


__all__ = [
    "IncrementalMechanism",
    "JoinKind",
    "ReorderingPolicy",
    "CorrectionPolicy",
    "DeletionHandling",
    "CheckSeverity",
    "JoinStrategy",
    "Watermark",
    "BackfillBoundary",
    "SourceCursor",
    "Reconciliation",
    "Retention",
    "Destination",
    "QualityCheck",
    "HealthContract",
    "CollectionSpec",
]
