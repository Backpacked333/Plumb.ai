"""BuildPlan: the implementation intermediate representation (design section 4).

Implements (specification v0.2):

* PL-014: a plan is a finite dependency graph of typed steps with declared
  inputs, outputs, required capabilities, budget reservations, bounded attempts
  and verification obligations. Step types are an open identifier here; the
  checker rejects any step type absent from the capability registry instead of
  interpreting it as an instruction.
* PL-015: this module validates the purely local facts a parser can establish
  (an input names exactly one origin, a step does not depend on itself, output
  names are unique, verification is declared, currencies agree). Graph-level
  facts (unique ids, unknown dependencies, cycles, scope, budgets against the
  envelope) are deliberately left to ``plumb.checker.plan_checker`` so that a
  parseable plan can be reported on finding by finding.
* PL-016: every step except ``dependency.raise`` must declare at least one
  verification obligation; a step cannot become verified by a worker's claim.
* PL-018: budgets carry bounded attempts, spend and elapsed time
  (:class:`~plumb.contracts.common.Budget`).
* PL-058: the plan declares a worst-case total budget; step budgets must be
  expressed in the same currency so that they can be summed and compared.
"""

from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from plumb.contracts.common import (
    ArtifactHeader,
    ArtifactKind,
    ArtifactRef,
    Budget,
    DataPurpose,
    EffectClass,
    Identifier,
    Money,
    NonEmptyStr,
    ResourceScope,
    ShortStr,
    StrictModel,
    VerificationLevel,
)

DEPENDENCY_RAISE_STEP_TYPE = "dependency.raise"
"""The one step type that records a missing dependency instead of producing a verifiable artifact."""

STEP_TYPE_VOCABULARY: frozenset[str] = frozenset(
    {
        "inventory.probe",
        "source.profile",
        "integration.configure",
        "integration.generate_adapter",
        "integration.contract_test",
        "collection.deploy_shadow",
        "collection.backfill",
        "collection.reconcile",
        "collection.enable_incremental",
        "dataset.discover_sources",
        "dataset.build",
        "dataset.label_audit",
        "training.submit",
        "evaluation.run",
        "workflow.compile",
        "workflow.test_bundle",
        "infrastructure.preview",
        "infrastructure.apply",
        "release.create",
        "release.activate_shadow",
        "release.canary",
        "verification.request",
        DEPENDENCY_RAISE_STEP_TYPE,
    }
)
"""The 23 step types of design section 4. The registry, not this set, is authoritative at check time."""

EXTERNAL_EFFECT_CLASSES: frozenset[EffectClass] = frozenset(
    {
        EffectClass.EXTERNAL_WRITE_REVERSIBLE,
        EffectClass.EXTERNAL_WRITE_IRREVERSIBLE,
        EffectClass.EXTERNAL_COMMUNICATION,
        EffectClass.FINANCIAL_COMMITMENT,
        EffectClass.INFRASTRUCTURE_CHANGE,
        EffectClass.DESTRUCTIVE,
    }
)
"""Effect classes that touch the world outside Plumb's own storage."""


def _unique(values: list[object], field_name: str) -> None:
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")


class StepInput(StrictModel):
    """An artifact a step consumes: produced by another step or supplied to the plan."""

    name: Identifier
    kind: ArtifactKind
    from_step: Identifier | None = Field(
        default=None, description="Producing step id; None means a plan-level input artifact."
    )
    plan_input: Identifier | None = Field(
        default=None, description="artifact_id of a BuildPlan.inputs entry."
    )

    @model_validator(mode="after")
    def _exactly_one_origin(self) -> "StepInput":
        if (self.from_step is None) == (self.plan_input is None):
            raise ValueError("StepInput must set exactly one of from_step or plan_input")
        return self


class StepOutput(StrictModel):
    """A typed artifact a step promises to produce."""

    name: Identifier
    kind: ArtifactKind


class VerificationObligation(StrictModel):
    """A check the verifier must pass before the step becomes VERIFIED (PL-016)."""

    check: Identifier = Field(description='e.g. "contract_tests", "source_to_storage_receipt".')
    level: VerificationLevel
    description: NonEmptyStr


class BuildStep(StrictModel):
    """One typed node of the build graph (PL-014)."""

    step_id: Identifier
    step_type: Identifier = Field(description="Must exist in the capability registry (checked by the checker).")
    description: NonEmptyStr
    depends_on: list[Identifier] = Field(default_factory=list)
    inputs: list[StepInput] = Field(default_factory=list)
    outputs: list[StepOutput] = Field(default_factory=list)
    required_capabilities: list[Identifier] = Field(
        default_factory=list, description="capability_ids in the registry."
    )
    effect_class: EffectClass
    purposes: list[DataPurpose] = Field(default_factory=list)
    scope: ResourceScope
    budget: Budget
    verification: list[VerificationObligation] = Field(
        default_factory=list, description="At least one unless step_type == dependency.raise."
    )
    required: bool = True
    environment: ShortStr | None = Field(
        default=None,
        description="Deployment environment for infrastructure/release steps; checked against the envelope.",
    )

    @model_validator(mode="after")
    def _check_step(self) -> "BuildStep":
        _unique(list(self.depends_on), "depends_on")
        if self.step_id in self.depends_on:
            raise ValueError(f"step {self.step_id} cannot depend on itself")
        _unique([item.name for item in self.inputs], "inputs[].name")
        _unique([item.name for item in self.outputs], "outputs[].name")
        _unique(list(self.required_capabilities), "required_capabilities")
        _unique(list(self.purposes), "purposes")
        _unique([(item.check, item.level) for item in self.verification], "verification[].(check, level)")
        if not self.verification and self.step_type != DEPENDENCY_RAISE_STEP_TYPE:
            raise ValueError(
                f"step {self.step_id} must declare at least one verification obligation "
                f"(only {DEPENDENCY_RAISE_STEP_TYPE} steps are exempt)"
            )
        return self

    @property
    def has_external_effect(self) -> bool:
        """True when the declared effect class reaches outside Plumb's own storage."""
        return self.effect_class in EXTERNAL_EFFECT_CLASSES

    def output_named(self, name: str) -> StepOutput | None:
        for output in self.outputs:
            if output.name == name:
                return output
        return None


class BuildPlan(ArtifactHeader):
    """A finite, typed, budgeted implementation graph compiled against one envelope version."""

    kind: Literal[ArtifactKind.BUILD_PLAN] = ArtifactKind.BUILD_PLAN
    plan_id: Identifier
    goal_id: Identifier
    opportunity_ref: ArtifactRef | None = None
    envelope_id: Identifier
    envelope_version: int = Field(ge=1)
    inputs: list[ArtifactRef] = Field(default_factory=list, description="Plan-level immutable inputs.")
    steps: list[BuildStep] = Field(min_length=1)
    total_budget: Budget = Field(description="Declared worst case for the whole plan.")
    planned_at: AwareDatetime

    @model_validator(mode="after")
    def _check_plan(self) -> "BuildPlan":
        _unique([ref.artifact_id for ref in self.inputs], "inputs[].artifact_id")
        currency = self.total_budget.spend.currency
        for step in self.steps:
            if step.budget.spend.currency != currency:
                raise ValueError(
                    f"step {step.step_id} budget currency {step.budget.spend.currency} "
                    f"differs from total_budget currency {currency}"
                )
        return self

    @property
    def step_ids(self) -> list[str]:
        """Step ids in declaration order (duplicates preserved for the checker to report)."""
        return [step.step_id for step in self.steps]

    def find_step(self, step_id: str) -> BuildStep | None:
        """The first step with ``step_id``, or None."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def plan_input_named(self, artifact_id: str) -> ArtifactRef | None:
        for ref in self.inputs:
            if ref.artifact_id == artifact_id:
                return ref
        return None

    def worst_case_step_spend(self) -> Money:
        """Sum of the steps' declared worst-case spend, in the plan currency (PL-058)."""
        total = Money(minor_units=0, currency=self.total_budget.spend.currency)
        for step in self.steps:
            total = total + step.budget.spend
        return total


__all__ = [
    "DEPENDENCY_RAISE_STEP_TYPE",
    "STEP_TYPE_VOCABULARY",
    "EXTERNAL_EFFECT_CLASSES",
    "StepInput",
    "StepOutput",
    "VerificationObligation",
    "BuildStep",
    "BuildPlan",
]
