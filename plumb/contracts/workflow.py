"""WorkflowSpec: a compiled business workflow (specification section 15).

Implements:

* PL-035: a workflow declares case identity, triggers, typed inputs, states,
  transitions, allowed operations, maximum iteration/time/cost bounds, durable
  waits, human decision points and completion conditions. Every operation is
  flagged ``external_effect`` with an effect class, so read-only preparation is
  distinguished from external business effects by construction.
* PL-036: deterministic business rules are enforced outside model text.
  :class:`DeterministicRule` records are ``enforced_outside_model``; every
  operation with an external effect references such a rule as its guard and
  requires a case-state version check; ``model_output_validation_required``
  must be true. A prompt is not an approval mechanism.
* Section 15 (primitives): operations use the certified primitives in
  :data:`CERTIFIED_PRIMITIVES`, or a declared custom primitive that carries an
  adapter verification reference, since a generated primitive must pass the
  same adapter and verification requirements as a new connector.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field, model_validator

from plumb.contracts.common import (
    ArtifactHeader,
    ArtifactKind,
    EffectClass,
    Identifier,
    Money,
    NonEmptyStr,
    PrincipalType,
    ShortStr,
    StrictModel,
)
from plumb.contracts.inventory import NonSecretIdentifier, NonSecretRef

CERTIFIED_PRIMITIVES: frozenset[str] = frozenset(
    {
        "fetch",
        "classify",
        "extract",
        "validate",
        "match",
        "calculate",
        "optimize",
        "request_missing_information",
        "wait",
        "review",
        "write",
    }
)
"""Primitives the runtime certifies (section 15)."""

EXTERNAL_EFFECT_PRIMITIVES: frozenset[str] = frozenset({"write", "request_missing_information"})
"""Certified primitives that always act on the world outside Plumb."""

PREPARATION_EFFECT_CLASSES: frozenset[EffectClass] = frozenset({EffectClass.READ, EffectClass.INTERNAL_WRITE})
"""Effect classes compatible with read-only preparation (no external effect)."""

HUMAN_PRINCIPAL_TYPES: frozenset[PrincipalType] = frozenset(
    {PrincipalType.HUMAN_OWNER, PrincipalType.HUMAN_REVIEWER, PrincipalType.HUMAN_APPROVER}
)


class TriggerKind(str, Enum):
    EVENT = "EVENT"
    SCHEDULE = "SCHEDULE"
    MANUAL = "MANUAL"


class CaseIdentity(StrictModel):
    """Fields that identify one case, e.g. client + period (PL-035)."""

    fields: list[ShortStr] = Field(min_length=1)
    description: NonEmptyStr


class Trigger(StrictModel):
    kind: TriggerKind
    source: ShortStr = Field(description="Event type, schedule expression or manual entry point.")


class TypedInput(StrictModel):
    name: Identifier
    type_ref: NonSecretRef = Field(description="Schema or contract the input must satisfy.")
    required: bool = True


class WorkflowState(StrictModel):
    name: Identifier
    terminal: bool = False
    durable_wait: bool = Field(default=False, description="True when the case may rest here across restarts.")


class Transition(StrictModel):
    from_state: Identifier
    to_state: Identifier
    trigger: Identifier = Field(description="Operation name, timeout or decision that fires the transition.")
    guard_rule_ref: Identifier | None = Field(default=None, description="Deterministic rule that must hold.")


class WorkflowOperation(StrictModel):
    """One permitted operation and whether it touches the world (PL-035, PL-036)."""

    name: Identifier
    primitive: Identifier
    external_effect: bool
    effect_class: EffectClass
    requires_case_state_version_check: bool
    deterministic_rule_ref: Identifier | None = Field(
        default=None, description="Rule enforced outside the model that gates this operation."
    )

    @model_validator(mode="after")
    def _effects_are_explicit(self) -> "WorkflowOperation":
        if self.primitive in EXTERNAL_EFFECT_PRIMITIVES and not self.external_effect:
            raise ValueError(f"primitive {self.primitive} always has an external effect")
        if self.external_effect:
            if self.effect_class in PREPARATION_EFFECT_CLASSES:
                raise ValueError(
                    f"operation {self.name} has external_effect but effect class {self.effect_class.value}"
                )
            if not self.requires_case_state_version_check:
                raise ValueError(
                    f"operation {self.name} has an external effect and must check the case state version first"
                )
            if self.deterministic_rule_ref is None:
                raise ValueError(
                    f"operation {self.name} has an external effect and must be gated by a deterministic rule; "
                    "a prompt is not an approval mechanism"
                )
        elif self.effect_class not in PREPARATION_EFFECT_CLASSES:
            raise ValueError(
                f"operation {self.name} declares effect class {self.effect_class.value} without external_effect"
            )
        return self


class CustomPrimitive(StrictModel):
    """A generated primitive; it meets the same adapter and verification requirements as a connector."""

    name: Identifier
    adapter_verification_ref: NonSecretIdentifier
    description: NonEmptyStr

    @model_validator(mode="after")
    def _not_shadowing_certified(self) -> "CustomPrimitive":
        if self.name in CERTIFIED_PRIMITIVES:
            raise ValueError(f"custom primitive {self.name} shadows a certified primitive")
        return self


class DeterministicRule(StrictModel):
    """A business rule enforced by the runtime, not by model text (PL-036)."""

    rule_id: Identifier
    expression: NonEmptyStr
    enforced_outside_model: bool = True

    @model_validator(mode="after")
    def _outside_model(self) -> "DeterministicRule":
        if not self.enforced_outside_model:
            raise ValueError(f"rule {self.rule_id} must be enforced outside model text")
        return self


class DurableWait(StrictModel):
    state: Identifier
    timeout_seconds: int = Field(ge=1)
    on_timeout_state: Identifier


class HumanDecisionPoint(StrictModel):
    state: Identifier
    decision: NonEmptyStr
    decider_role: PrincipalType

    @model_validator(mode="after")
    def _human_decides(self) -> "HumanDecisionPoint":
        if self.decider_role not in HUMAN_PRINCIPAL_TYPES:
            raise ValueError("a human decision point must be decided by a human principal type")
        return self


class CompletionCondition(StrictModel):
    terminal_state: Identifier
    description: NonEmptyStr
    rule_ref: Identifier | None = None


class WorkflowSpec(ArtifactHeader):
    """A bounded, auditable workflow built from certified primitives (PL-035, PL-036)."""

    kind: Literal[ArtifactKind.WORKFLOW_SPEC] = ArtifactKind.WORKFLOW_SPEC
    workflow_id: Identifier
    case_identity: CaseIdentity
    triggers: list[Trigger] = Field(min_length=1)
    typed_inputs: list[TypedInput] = Field(min_length=1)
    states: list[WorkflowState] = Field(min_length=2)
    initial_state: Identifier
    transitions: list[Transition] = Field(min_length=1)
    allowed_operations: list[WorkflowOperation] = Field(min_length=1)
    custom_primitives: list[CustomPrimitive] = Field(default_factory=list)
    deterministic_rules: list[DeterministicRule] = Field(default_factory=list)
    max_iterations: int = Field(ge=1)
    max_duration_seconds: int = Field(ge=1)
    max_cost: Money
    durable_waits: list[DurableWait] = Field(min_length=1)
    human_decision_points: list[HumanDecisionPoint] = Field(min_length=1)
    completion_conditions: list[CompletionCondition] = Field(min_length=1)
    model_output_validation_required: bool = Field(
        description="Must be true: the runtime validates model outputs before tool execution."
    )

    @property
    def external_operations(self) -> list[WorkflowOperation]:
        return [operation for operation in self.allowed_operations if operation.external_effect]

    @model_validator(mode="after")
    def _coherent_workflow(self) -> "WorkflowSpec":
        if not self.model_output_validation_required:
            raise ValueError("model_output_validation_required must be true (PL-036)")
        state_names = [state.name for state in self.states]
        if len(set(state_names)) != len(state_names):
            raise ValueError("state names must be unique")
        states = {state.name: state for state in self.states}
        if self.initial_state not in states:
            raise ValueError(f"initial_state {self.initial_state} is not a declared state")
        if states[self.initial_state].terminal:
            raise ValueError("initial_state cannot be terminal")
        if not any(state.terminal for state in self.states):
            raise ValueError("at least one state must be terminal")

        rule_ids = [rule.rule_id for rule in self.deterministic_rules]
        if len(set(rule_ids)) != len(rule_ids):
            raise ValueError("rule_id values must be unique")
        rules = set(rule_ids)

        for transition in self.transitions:
            for endpoint in (transition.from_state, transition.to_state):
                if endpoint not in states:
                    raise ValueError(f"transition {transition.trigger} references unknown state {endpoint}")
            if states[transition.from_state].terminal:
                raise ValueError(f"terminal state {transition.from_state} cannot have outgoing transitions")
            if transition.guard_rule_ref is not None and transition.guard_rule_ref not in rules:
                raise ValueError(f"transition guard {transition.guard_rule_ref} is not a declared rule")

        custom_names = [primitive.name for primitive in self.custom_primitives]
        if len(set(custom_names)) != len(custom_names):
            raise ValueError("custom primitive names must be unique")
        permitted_primitives = CERTIFIED_PRIMITIVES | set(custom_names)
        operation_names = [operation.name for operation in self.allowed_operations]
        if len(set(operation_names)) != len(operation_names):
            raise ValueError("operation names must be unique")
        for operation in self.allowed_operations:
            if operation.primitive not in permitted_primitives:
                raise ValueError(
                    f"operation {operation.name} uses primitive {operation.primitive!r}, which is neither certified "
                    "nor a declared custom primitive with adapter verification"
                )
            if operation.deterministic_rule_ref is not None and operation.deterministic_rule_ref not in rules:
                raise ValueError(f"operation {operation.name} references unknown rule {operation.deterministic_rule_ref}")

        for wait in self.durable_waits:
            for endpoint in (wait.state, wait.on_timeout_state):
                if endpoint not in states:
                    raise ValueError(f"durable wait references unknown state {endpoint}")
            if not states[wait.state].durable_wait:
                raise ValueError(f"durable wait state {wait.state} is not flagged durable_wait")
        for point in self.human_decision_points:
            if point.state not in states:
                raise ValueError(f"human decision point references unknown state {point.state}")
        for condition in self.completion_conditions:
            if condition.terminal_state not in states:
                raise ValueError(f"completion condition references unknown state {condition.terminal_state}")
            if not states[condition.terminal_state].terminal:
                raise ValueError(f"completion condition state {condition.terminal_state} is not terminal")
            if condition.rule_ref is not None and condition.rule_ref not in rules:
                raise ValueError(f"completion condition references unknown rule {condition.rule_ref}")
        return self


__all__ = [
    "CERTIFIED_PRIMITIVES",
    "EXTERNAL_EFFECT_PRIMITIVES",
    "PREPARATION_EFFECT_CLASSES",
    "HUMAN_PRINCIPAL_TYPES",
    "TriggerKind",
    "CaseIdentity",
    "Trigger",
    "TypedInput",
    "WorkflowState",
    "Transition",
    "WorkflowOperation",
    "CustomPrimitive",
    "DeterministicRule",
    "DurableWait",
    "HumanDecisionPoint",
    "CompletionCondition",
    "WorkflowSpec",
]
