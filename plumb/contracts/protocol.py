"""AgentTask and StepResult: the agent execution protocol (specification Appendix A §1 and §3).

These are supporting contracts describing *proposed production behaviour*; the
package does not implement the distributed protocol.

* Appendix A §1: an :class:`AgentTask` is a bounded engineering assignment. Its
  envelope carries the task id, authenticated tenant, parent build and step,
  goal and acceptance references, immutable input artifact references,
  permitted capabilities, source/destination scope, remaining budget, workspace
  base digest and a fencing token. All values come from trusted state; a
  generated artifact cannot grant access to itself.
* Appendix A §3: a :class:`StepResult` is a *proposal*: task/step/attempt ids,
  fencing token, input and output digests, execution environment digest, tool
  call and effect references, test-log references, claimed postconditions, cost
  usage and unresolved dependencies. Verifier attestations are separate records
  issued by the verifier, never fields the builder may fill; any field whose
  name suggests verification is rejected (:data:`FORBIDDEN_RESULT_FIELD_MARKERS`).
* Appendix A §2: :func:`check_result_against_task` lists why a result cannot be
  committed against its task (fencing token, attempt and spend budget), so the
  scheduler's compare-and-set has an explicit reason.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from plumb.contracts.common import (
    ArtifactRef,
    Budget,
    DependencyRecord,
    Identifier,
    Money,
    NonEmptyStr,
    ResourceScope,
    Sha256Digest,
    StrictModel,
    TenantId,
)
from plumb.contracts.inventory import NonSecretIdentifier

FORBIDDEN_RESULT_FIELD_MARKERS: tuple[str, ...] = ("verif", "attest", "trusted", "production_ready")
"""Name fragments a worker result may never carry: those records come from the verifier."""


class AgentTask(StrictModel):
    """A bounded engineering assignment compiled from trusted state (Appendix A §1)."""

    task_id: Identifier
    tenant_id: TenantId
    parent_build_id: Identifier
    parent_step_id: Identifier
    goal_ref: NonSecretIdentifier
    acceptance_refs: list[NonSecretIdentifier] = Field(
        min_length=1, description="Protected acceptance contracts the verifier will apply."
    )
    input_artifact_refs: list[ArtifactRef] = Field(
        default_factory=list, description="Immutable, digest-pinned inputs; never mutable ids."
    )
    permitted_capabilities: list[Identifier] = Field(min_length=1)
    scope: ResourceScope
    remaining_budget: Budget
    workspace_base_digest: Sha256Digest
    fencing_token: int = Field(ge=1, description="Monotonic lease epoch; a stale token cannot commit.")

    @model_validator(mode="after")
    def _distinct_references(self) -> "AgentTask":
        if len(set(self.acceptance_refs)) != len(self.acceptance_refs):
            raise ValueError("acceptance_refs must not contain duplicates")
        if len(set(self.permitted_capabilities)) != len(self.permitted_capabilities):
            raise ValueError("permitted_capabilities must not contain duplicates")
        digests = [ref.digest for ref in self.input_artifact_refs]
        if len(set(digests)) != len(digests):
            raise ValueError("input_artifact_refs must not contain duplicate digests")
        return self


class StepResult(StrictModel):
    """What a worker proposes; nothing here is verified state (Appendix A §3)."""

    task_id: Identifier
    step_id: Identifier
    attempt: int = Field(ge=1)
    fencing_token: int = Field(ge=1)
    input_digests: list[Sha256Digest] = Field(default_factory=list)
    output_digests: list[Sha256Digest] = Field(default_factory=list)
    execution_environment_digest: Sha256Digest
    tool_call_refs: list[NonSecretIdentifier] = Field(default_factory=list)
    effect_refs: list[Identifier] = Field(default_factory=list, description="Action ids recorded before external writes.")
    test_log_refs: list[NonSecretIdentifier] = Field(default_factory=list)
    claimed_postconditions: list[NonEmptyStr] = Field(
        default_factory=list, description="Claims to be checked by the verifier; never verified state."
    )
    cost_usage: Money
    unresolved_dependencies: list[DependencyRecord] = Field(default_factory=list)
    diagnostics: NonEmptyStr | None = Field(default=None, description="Kept so the next worker does not repeat it.")

    @model_validator(mode="before")
    @classmethod
    def _reject_verification_claims(cls, data: Any) -> Any:
        if isinstance(data, dict):
            offending = sorted(
                str(name)
                for name in data
                if any(marker in str(name).lower() for marker in FORBIDDEN_RESULT_FIELD_MARKERS)
            )
            if offending:
                raise ValueError(
                    f"a StepResult cannot carry {', '.join(offending)}: verifier attestations are separate "
                    "records issued by the verifier, not fields the builder may fill"
                )
        return data

    @model_validator(mode="after")
    def _distinct_references(self) -> "StepResult":
        for name in ("input_digests", "output_digests", "tool_call_refs", "effect_refs", "test_log_refs"):
            values = getattr(self, name)
            if len(set(values)) != len(values):
                raise ValueError(f"{name} must not contain duplicates")
        return self


def check_result_against_task(task: AgentTask, result: StepResult) -> list[str]:
    """Reasons a result cannot be committed against ``task`` (Appendix A §2 step 7); empty when it can."""
    reasons: list[str] = []
    if result.task_id != task.task_id:
        reasons.append(f"result is for task {result.task_id}, not {task.task_id}")
    if result.step_id != task.parent_step_id:
        reasons.append(f"result is for step {result.step_id}, not {task.parent_step_id}")
    if result.fencing_token != task.fencing_token:
        reasons.append(f"stale fencing token {result.fencing_token}; current is {task.fencing_token}")
    if result.attempt > task.remaining_budget.max_attempts:
        reasons.append(f"attempt {result.attempt} exceeds max_attempts {task.remaining_budget.max_attempts}")
    spend = task.remaining_budget.spend
    if result.cost_usage.currency != spend.currency:
        reasons.append(f"cost currency {result.cost_usage.currency} differs from budget currency {spend.currency}")
    elif result.cost_usage.exceeds(spend):
        reasons.append(f"cost {result.cost_usage.minor_units} exceeds remaining spend {spend.minor_units}")
    return reasons


__all__ = [
    "FORBIDDEN_RESULT_FIELD_MARKERS",
    "AgentTask",
    "StepResult",
    "check_result_against_task",
]
