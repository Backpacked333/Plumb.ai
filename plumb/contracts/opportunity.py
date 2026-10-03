"""OpportunitySpec: a hypothesis about where automation pays (specification section 7).

Implements:

* PL-012: every opportunity states the business objective, eligible case
  population, baseline, evidence coverage, proposed change, dependencies,
  expected benefit range, failure cost, review cost and a *prospective*
  measurement plan. Causal improvements are never inferred from historical
  replay alone, so ``measurement_plan.prospective`` must be true.
* PL-013: candidate generation includes non-ML interventions and native product
  configuration (:class:`InterventionKind` carries ``NATIVE_SETTING`` and
  ``REMOVE_STEP``), and the complete candidate system is compared against the
  current process and a reasonable native-feature baseline
  (``candidate_comparison`` must contain a ``CURRENT_PROCESS`` and a
  ``NATIVE_FEATURE`` entry).
* Section 7 (portfolio economics): failed feasibility checks remain backlog
  entries with explicit ``blocking_conditions``; ``overlap_refs`` record other
  opportunities claiming the same labor or revenue so benefits are not double
  counted. An opportunity whose expected net value cannot be positive cannot be
  ``CANDIDATE``, ``FEASIBLE`` or ``SELECTED``: it is ``REJECTED_NEGATIVE_VALUE``,
  or ``BLOCKED`` when a blocking condition (not the economics alone) is what
  keeps it in the backlog. The spec states the rejection as a SHOULD;
  :meth:`OpportunitySpec.should_reject` is the advisory the planner consults.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field, model_validator

from plumb.contracts.common import (
    ArtifactHeader,
    ArtifactKind,
    FailureClass,
    Identifier,
    Money,
    NonEmptyStr,
    NonSecretIdentifier,
    NonSecretText,
    ShortStr,
    StrictModel,
)


class InterventionKind(str, Enum):
    """What kind of change is proposed; most are not machine learning (PL-013)."""

    NATIVE_SETTING = "NATIVE_SETTING"
    DETERMINISTIC_AUTOMATION = "DETERMINISTIC_AUTOMATION"
    GENERAL_MODEL_WORKFLOW = "GENERAL_MODEL_WORKFLOW"
    SPECIALIST_SERVICE = "SPECIALIST_SERVICE"
    RETRIEVAL_SYSTEM = "RETRIEVAL_SYSTEM"
    TRAINED_COMPONENT = "TRAINED_COMPONENT"
    REMOVE_STEP = "REMOVE_STEP"


class CandidateKind(str, Enum):
    """Role of an entry in the candidate comparison (PL-013)."""

    CURRENT_PROCESS = "CURRENT_PROCESS"
    NATIVE_FEATURE = "NATIVE_FEATURE"
    PROPOSED_SYSTEM = "PROPOSED_SYSTEM"
    ALTERNATIVE = "ALTERNATIVE"


class MeasurementMethod(str, Enum):
    """Prospective designs that can support a causal claim (section 7)."""

    STAGED_ROLLOUT = "STAGED_ROLLOUT"
    COMPARABLE_CASE_COHORTS = "COMPARABLE_CASE_COHORTS"


class OpportunityStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    FEASIBLE = "FEASIBLE"
    BLOCKED = "BLOCKED"
    SELECTED = "SELECTED"
    REJECTED_NEGATIVE_VALUE = "REJECTED_NEGATIVE_VALUE"


REQUIRED_COMPARISON_KINDS: frozenset[CandidateKind] = frozenset(
    {CandidateKind.CURRENT_PROCESS, CandidateKind.NATIVE_FEATURE}
)
"""Baselines every candidate comparison must contain (PL-013)."""

BLOCKED_STATUSES: frozenset[OpportunityStatus] = frozenset(
    {OpportunityStatus.BLOCKED, OpportunityStatus.REJECTED_NEGATIVE_VALUE}
)
"""Statuses compatible with recorded blocking conditions."""


class BenefitRange(StrictModel):
    """Expected benefit as a range over a defined horizon (section 7)."""

    low: Money
    high: Money
    horizon_days: int = Field(ge=1)

    @model_validator(mode="after")
    def _ordered_same_currency(self) -> "BenefitRange":
        if self.low.currency != self.high.currency:
            raise ValueError("benefit range bounds must share a currency")
        if self.low.minor_units > self.high.minor_units:
            raise ValueError("benefit range low bound cannot exceed the high bound")
        return self


class EvidenceCoverage(StrictModel):
    """How much of the eligible population the available evidence actually covers (PL-012)."""

    observed_case_count: int = Field(ge=0)
    eligible_case_count: int = Field(ge=0)
    source_ids: list[Identifier] = Field(default_factory=list)
    gaps: list[ShortStr] = Field(default_factory=list, description="Known unobserved handoffs, systems or periods.")

    @model_validator(mode="after")
    def _observed_within_eligible(self) -> "EvidenceCoverage":
        if self.observed_case_count > self.eligible_case_count:
            raise ValueError("observed_case_count cannot exceed eligible_case_count")
        return self

    @property
    def ratio(self) -> float:
        if self.eligible_case_count == 0:
            return 0.0
        return self.observed_case_count / self.eligible_case_count


class ProposedChange(StrictModel):
    intervention_kind: InterventionKind
    description: NonEmptyStr
    affected_steps: list[ShortStr] = Field(default_factory=list)
    required_capability_ids: list[Identifier] = Field(default_factory=list)


class CandidateSystem(StrictModel):
    """One complete alternative in the comparison, costed end to end (PL-013)."""

    kind: CandidateKind
    description: NonEmptyStr
    expected_cost: Money
    expected_benefit_range: BenefitRange

    @model_validator(mode="after")
    def _single_currency(self) -> "CandidateSystem":
        if self.expected_cost.currency != self.expected_benefit_range.low.currency:
            raise ValueError("candidate cost and benefit must share a currency")
        return self


class MeasurementPlan(StrictModel):
    """How value will be measured once the change is live (PL-012)."""

    prospective: bool = Field(description="Must be true: historical replay alone cannot establish causal gains.")
    method: MeasurementMethod
    metrics: list[ShortStr] = Field(min_length=1)
    confounders_accounted: list[ShortStr] = Field(
        default_factory=list, description="Case mix, calendar effects, employee review and the like."
    )
    horizon_days: int = Field(ge=1)

    @model_validator(mode="after")
    def _must_be_prospective(self) -> "MeasurementPlan":
        if not self.prospective:
            raise ValueError("measurement_plan must be prospective; do not infer causal improvements from replay alone")
        return self


class BlockingCondition(StrictModel):
    """Why feasibility failed, precisely enough to resume once resolved (section 7)."""

    condition_id: Identifier
    failure_class: FailureClass
    description: NonEmptyStr
    missing_authority: list[NonSecretText] = Field(
        default_factory=list, description="Exact grants, consents or decisions required; names, never values."
    )


class OpportunitySpec(ArtifactHeader):
    """A costed, measurable hypothesis about one improvement (PL-012, PL-013)."""

    kind: Literal[ArtifactKind.OPPORTUNITY_SPEC] = ArtifactKind.OPPORTUNITY_SPEC
    opportunity_id: Identifier
    goal_id: Identifier
    business_objective: NonEmptyStr
    eligible_case_population: NonEmptyStr
    baseline: NonEmptyStr = Field(description="The current process and its measured cost or cycle time.")
    evidence_coverage: EvidenceCoverage
    proposed_change: ProposedChange
    dependencies: list[Identifier] = Field(
        default_factory=list, description="Prerequisite opportunities, capabilities or dependency records."
    )
    expected_benefit_range: BenefitRange
    failure_cost: Money
    review_cost: Money
    implementation_cost: Money | None = None
    operation_cost: Money | None = None
    change_management_cost: Money | None = None
    measurement_plan: MeasurementPlan
    candidate_comparison: list[CandidateSystem] = Field(min_length=2)
    blocking_conditions: list[BlockingCondition] = Field(default_factory=list)
    overlap_refs: list[NonSecretIdentifier] = Field(
        default_factory=list, description="Other opportunity ids claiming the same labor or revenue."
    )
    status: OpportunityStatus

    @model_validator(mode="after")
    def _coherent_opportunity(self) -> "OpportunitySpec":
        currency = self.expected_benefit_range.low.currency
        for name, amount in self._cost_fields():
            if amount.currency != currency:
                raise ValueError(f"{name} currency {amount.currency} differs from benefit currency {currency}")
        kinds = {candidate.kind for candidate in self.candidate_comparison}
        missing = sorted(kind.value for kind in REQUIRED_COMPARISON_KINDS - kinds)
        if missing:
            raise ValueError(f"candidate_comparison must include baselines: {', '.join(missing)}")
        if self.opportunity_id in self.overlap_refs:
            raise ValueError("an opportunity cannot overlap with itself")
        if len(set(self.overlap_refs)) != len(self.overlap_refs):
            raise ValueError("overlap_refs must not contain duplicates")
        if self.status is OpportunityStatus.BLOCKED and not self.blocking_conditions:
            raise ValueError("a BLOCKED opportunity must record its blocking conditions")
        if self.blocking_conditions and self.status not in BLOCKED_STATUSES:
            raise ValueError("an opportunity with blocking conditions cannot be FEASIBLE, SELECTED or CANDIDATE")
        if self.should_reject() and self.status not in BLOCKED_STATUSES:
            raise ValueError(
                "expected net value upper bound is not positive; status must be REJECTED_NEGATIVE_VALUE "
                "(or BLOCKED when a blocking condition keeps the entry in the backlog)"
            )
        return self

    def should_reject(self) -> bool:
        """Section 7 advisory: the upper bound of the expected net value is not positive."""
        _, upper = self.expected_net_value_range()
        return upper <= 0

    def _cost_fields(self) -> list[tuple[str, Money]]:
        costs = [("failure_cost", self.failure_cost), ("review_cost", self.review_cost)]
        for name in ("implementation_cost", "operation_cost", "change_management_cost"):
            amount: Money | None = getattr(self, name)
            if amount is not None:
                costs.append((name, amount))
        return costs

    def total_cost_minor_units(self) -> int:
        return sum(amount.minor_units for _, amount in self._cost_fields())

    def expected_net_value_range(self) -> tuple[int, int]:
        """(low, high) expected net value in minor units over the benefit horizon; may be negative."""
        costs = self.total_cost_minor_units()
        return (
            self.expected_benefit_range.low.minor_units - costs,
            self.expected_benefit_range.high.minor_units - costs,
        )


__all__ = [
    "InterventionKind",
    "CandidateKind",
    "MeasurementMethod",
    "OpportunityStatus",
    "REQUIRED_COMPARISON_KINDS",
    "BLOCKED_STATUSES",
    "BenefitRange",
    "EvidenceCoverage",
    "ProposedChange",
    "CandidateSystem",
    "MeasurementPlan",
    "BlockingCondition",
    "OpportunitySpec",
]
