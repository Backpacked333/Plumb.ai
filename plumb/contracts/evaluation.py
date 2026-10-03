"""EvaluationReport (specification sections 13, 14 and 18).

Implements:

* PL-031: candidates (native/rules baseline, prompted general model,
  retrieval, specialist API, trained component) are compared on complete task
  performance *and* total operating cost including review and serving
  utilisation, never on a model score alone.
* PL-034: promotion needs a held-out evaluation; the report names the pinned
  held-out dataset and the split it used, which can never be ``train``.
* PL-044: evaluation data is segregated from tuning and repair examples; the
  report carries an explicit segregation statement that must assert
  disjointness. Nondeterministic components are evaluated over several trials.
* Section 13: sampling and exclusions are auditable and included in the
  denominators, so every metric carries numerator and denominator and the
  report states how many eligible cases were excluded and why.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field, field_validator, model_validator

from plumb.contracts.common import (
    ArtifactHeader,
    ArtifactKind,
    ArtifactRef,
    Identifier,
    Money,
    NonEmptyStr,
    StrictModel,
    VerificationLevel,
)

HeldOutSplit = Literal["validation", "test_temporal", "test_client_disjoint"]
"""Splits an evaluation may run on; ``train`` is excluded by construction (PL-034, PL-044)."""

MIN_TRIALS_NONDETERMINISTIC = 2
"""Fewest trials accepted for a nondeterministic component."""

RECOMMENDED_TRIALS_NONDETERMINISTIC = 3
"""Trials recommended for a nondeterministic component (section 18)."""


class ErrorSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CandidateKind(str, Enum):
    """The implementation options the model planner compares (PL-031)."""

    BASELINE_NATIVE_RULES = "BASELINE_NATIVE_RULES"
    PROMPTED_GENERAL_MODEL = "PROMPTED_GENERAL_MODEL"
    RETRIEVAL = "RETRIEVAL"
    SPECIALIST_API = "SPECIALIST_API"
    TRAINED = "TRAINED"


class Metric(StrictModel):
    """A rate with an explicit denominator; a bare percentage is not a metric (section 13)."""

    name: Identifier
    numerator: int = Field(ge=0)
    denominator: int = Field(ge=1, description="Cases, fields or trials the numerator is measured over.")
    description: NonEmptyStr | None = None

    @property
    def value(self) -> float:
        return self.numerator / self.denominator


class ErrorSeverityBreakdown(StrictModel):
    """Observed errors by severity; releases set thresholds per severity (section 24)."""

    low: int = Field(ge=0)
    medium: int = Field(ge=0)
    high: int = Field(ge=0)

    @property
    def total(self) -> int:
        return self.low + self.medium + self.high

    def count(self, severity: ErrorSeverity) -> int:
        return getattr(self, severity.value.lower())


class CandidateComparison(StrictModel):
    """One candidate's complete task performance and total operating cost (PL-031)."""

    candidate: CandidateKind
    candidate_ref: ArtifactRef | None = Field(
        default=None, description="Pinned artifact of the candidate (model version, workflow, ...)."
    )
    total_operating_cost: Money = Field(
        description="Total cost for the evaluated cases including review and serving utilisation."
    )
    task_performance: Metric
    review_time_minutes: int = Field(ge=0)
    notes: NonEmptyStr | None = None


class SegregationStatement(StrictModel):
    """Attestation that evaluation data was not used for tuning or repair (PL-044)."""

    evaluation_data_disjoint_from_tuning: bool
    basis: NonEmptyStr = Field(description="How disjointness was established, e.g. by split content hashes.")


class EvaluationReport(ArtifactHeader):
    """Held-out evaluation of one subject with denominators, severities, cost and trials."""

    kind: Literal[ArtifactKind.EVALUATION_REPORT] = ArtifactKind.EVALUATION_REPORT
    subject_ref: ArtifactRef = Field(description="The model version, workflow or release being evaluated.")
    dataset_ref: ArtifactRef = Field(description="Pinned held-out DatasetManifest (PL-034).")
    held_out_split: HeldOutSplit
    level: VerificationLevel
    case_count: int = Field(ge=1, description="Held-out cases the evaluation ran on.")
    excluded_case_count: int = Field(
        default=0, ge=0, description="Eligible cases excluded from the run; part of the audit trail."
    )
    exclusion_summary: NonEmptyStr | None = Field(
        default=None, description="Why cases were excluded; required when excluded_case_count > 0."
    )
    metrics: list[Metric] = Field(min_length=1)
    error_severity_breakdown: ErrorSeverityBreakdown
    review_time_minutes: int = Field(ge=0, description="Human review time spent over the evaluated cases.")
    cost_comparison: list[CandidateComparison] = Field(min_length=1)
    nondeterministic: bool = Field(description="Whether the subject's output varies between identical runs.")
    trials: int = Field(ge=1, description="Independent runs over the held-out cases.")
    segregation_statement: SegregationStatement

    @field_validator("dataset_ref")
    @classmethod
    def _dataset_kind(cls, ref: ArtifactRef) -> ArtifactRef:
        if ref.kind != ArtifactKind.DATASET_MANIFEST:
            raise ValueError(f"dataset_ref must reference a DatasetManifest, not {ref.kind.value}")
        return ref

    @field_validator("metrics")
    @classmethod
    def _metric_names_unique(cls, metrics: list[Metric]) -> list[Metric]:
        names = [metric.name for metric in metrics]
        repeated = sorted({name for name in names if names.count(name) > 1})
        if repeated:
            raise ValueError(f"metric names must be unique; repeated: {', '.join(repeated)}")
        return metrics

    @field_validator("cost_comparison")
    @classmethod
    def _candidates_comparable(cls, candidates: list[CandidateComparison]) -> list[CandidateComparison]:
        kinds = [entry.candidate for entry in candidates]
        repeated = sorted({kind.value for kind in kinds if kinds.count(kind) > 1})
        if repeated:
            raise ValueError(f"each candidate kind appears once in cost_comparison; repeated: {', '.join(repeated)}")
        currencies = {entry.total_operating_cost.currency for entry in candidates}
        if len(currencies) > 1:
            raise ValueError(f"cost_comparison must use one currency; found {', '.join(sorted(currencies))}")
        return candidates

    @model_validator(mode="after")
    def _report_is_admissible(self) -> "EvaluationReport":
        if not self.segregation_statement.evaluation_data_disjoint_from_tuning:
            raise ValueError(
                "evaluation data was used for tuning or repair; the report is not a held-out evaluation (PL-044)"
            )
        if self.nondeterministic and self.trials < MIN_TRIALS_NONDETERMINISTIC:
            raise ValueError(
                f"a nondeterministic component needs at least {MIN_TRIALS_NONDETERMINISTIC} trials "
                f"({RECOMMENDED_TRIALS_NONDETERMINISTIC} recommended); got {self.trials}"
            )
        if self.excluded_case_count > 0 and self.exclusion_summary is None:
            raise ValueError("exclusion_summary is required when cases were excluded (exclusions must be auditable)")
        return self

    @property
    def meets_recommended_trials(self) -> bool:
        return not self.nondeterministic or self.trials >= RECOMMENDED_TRIALS_NONDETERMINISTIC

    def metric(self, name: str) -> Metric:
        for entry in self.metrics:
            if entry.name == name:
                return entry
        raise KeyError(name)


__all__ = [
    "HeldOutSplit",
    "MIN_TRIALS_NONDETERMINISTIC",
    "RECOMMENDED_TRIALS_NONDETERMINISTIC",
    "ErrorSeverity",
    "CandidateKind",
    "Metric",
    "ErrorSeverityBreakdown",
    "CandidateComparison",
    "SegregationStatement",
    "EvaluationReport",
]
