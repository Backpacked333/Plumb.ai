"""Reference plan checker: is this BuildPlan executable within this envelope? (design section 4)

Implements (specification v0.2):

* PL-005: a derived task cannot widen the autonomy envelope. Every step's scope,
  effect class, purposes, budget, attempts and deployment environment are
  compared against the envelope the plan claims to be compiled against, and the
  envelope must be the one named (id and version), in force at the evaluation
  instant and belonging to the same tenant.
* PL-008: discovered, documented, sandbox-tested and production-verified
  capabilities are distinct. A step is bound to registry records; production
  steps need ``SANDBOX_TESTED`` or better, ``release.*`` and
  ``infrastructure.apply`` need ``PRODUCTION_VERIFIED``, read-only probes and
  shadow deployments accept ``DOCUMENTED`` (see :func:`required_maturity`).
* PL-014: a plan is a finite dependency graph of typed steps. Unsupported step
  types and unknown capabilities are rejected rather than interpreted, and the
  graph must be acyclic (the cycle members are reported).
* PL-015: unique ids, valid dependencies, cycles, input/output compatibility,
  missing artifacts, authority, region/purpose restrictions, effect class,
  budget and verification coverage are all checked; a syntactically valid plan
  is not necessarily executable.
* PL-016 / PL-043: every step except ``dependency.raise`` carries at least one
  verification obligation; a step with external effects needs a check at
  ``INTEGRATION_BEHAVIOR`` or higher (passing unit tests cannot substitute for
  verifying a real external effect); a ``release.*`` step needs a
  ``BUSINESS_OUTCOME`` check.
* PL-018: a step's attempt bound may not exceed the envelope's per-step limit.
* PL-053: for every source a step touches, its purposes (declared, plus those
  the bound capabilities require) must be granted for that source. Permission
  to ``TRAIN`` or ``EXPORT`` is never inferred from ``INSPECT`` or ``COLLECT``.
* PL-058: the declared worst-case budgets must nest: sum of step spend <= plan
  total <= envelope spending limit, in one currency. The checker verifies
  declared reservations; it meters nothing.

Finding table (``code`` -> error class; severity ERROR unless stated):

=================================== ====================== =======================================
DUPLICATE_STEP_ID                   STATE_CONFLICT         step ids unique
UNKNOWN_DEPENDENCY                  STATE_CONFLICT         every depends_on names a step
DEPENDENCY_CYCLE                    STATE_CONFLICT         graph is a DAG; ``details.members``
UNSUPPORTED_STEP_TYPE               CAPABILITY_UNSUPPORTED step_type known to the registry
UNKNOWN_CAPABILITY                  CAPABILITY_UNSUPPORTED capability in registry and for this step type
CAPABILITY_MATURITY_INSUFFICIENT    CAPABILITY_UNSUPPORTED bound capability meets :func:`required_maturity`
INPUT_UNRESOLVED                    STATE_CONFLICT         from_step in depends_on and produces the output
INPUT_KIND_MISMATCH                 STATE_CONFLICT         input kind equals the producing kind
MISSING_ARTIFACT                    STATE_CONFLICT         plan_input names a BuildPlan.inputs entry
TENANT_MISMATCH                     SCOPE_DENIED           plan and envelope share a tenant
ENVELOPE_MISMATCH                   POLICY_STALE           plan names this envelope id and version
ENVELOPE_INACTIVE                   POLICY_STALE           envelope not revoked, in force at the instant
SCOPE_EXCEEDED                      SCOPE_DENIED           step scope within the envelope scope
EFFECT_CLASS_DENIED                 SCOPE_DENIED           effect class allowed by envelope and capability
                                                           (WARNING when a bound capability can also
                                                           produce a class the envelope does not allow)
PURPOSE_DENIED                      PURPOSE_DENIED         purposes granted per source (PL-053)
BUDGET_EXCEEDED                     BUDGET_EXCEEDED        nested budgets, one currency (PL-058)
ATTEMPTS_EXCEEDED                   BUDGET_EXCEEDED        max_attempts within the envelope limit
MISSING_VERIFICATION                VERIFICATION_FAILED    obligations present and at the required level
DEPLOYMENT_ENV_DENIED               SCOPE_DENIED           environment declared and allowed
                                                           (WARNING for a read-only infrastructure step
                                                           that declares none)
=================================== ====================== =======================================

Conventions:

* The evaluation instant is the later of ``plan.planned_at`` and the caller's
  ``now`` (both timezone-aware); grants and the envelope's validity are
  evaluated at that instant. A revoked envelope is inactive whatever the instant.
* The deployment environment of a step is read from ``BuildStep.environment``
  (a field stage 1 added for this purpose); nothing is inferred from
  ``scope.destination_ids``.
* Rules the contract models already enforce at parse time (self-dependency,
  empty verification, one input origin, step currency) are re-checked here, so
  a plan built with ``model_construct`` or loaded from an older schema is judged
  on content rather than on how it was instantiated.
* The checker never executes anything and never mutates its inputs.
"""

from __future__ import annotations

import heapq
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from plumb.checker.findings import CheckReport, Finding, Severity
from plumb.contracts.build_plan import DEPENDENCY_RAISE_STEP_TYPE, BuildPlan, BuildStep
from plumb.contracts.capability import MATURITY_RANK, CapabilityRecord
from plumb.contracts.common import (
    CapabilityMaturity,
    DataPurpose,
    EffectClass,
    ErrorClass,
    VerificationLevel,
)
from plumb.contracts.envelope import AutonomyEnvelope
from plumb.registry.registry import CapabilityRegistry

CHECKER_NAME = "plan_checker"

FINDING_ERROR_CLASSES: dict[str, ErrorClass] = {
    "DUPLICATE_STEP_ID": ErrorClass.STATE_CONFLICT,
    "UNKNOWN_DEPENDENCY": ErrorClass.STATE_CONFLICT,
    "DEPENDENCY_CYCLE": ErrorClass.STATE_CONFLICT,
    "UNSUPPORTED_STEP_TYPE": ErrorClass.CAPABILITY_UNSUPPORTED,
    "UNKNOWN_CAPABILITY": ErrorClass.CAPABILITY_UNSUPPORTED,
    "CAPABILITY_MATURITY_INSUFFICIENT": ErrorClass.CAPABILITY_UNSUPPORTED,
    "INPUT_UNRESOLVED": ErrorClass.STATE_CONFLICT,
    "INPUT_KIND_MISMATCH": ErrorClass.STATE_CONFLICT,
    "MISSING_ARTIFACT": ErrorClass.STATE_CONFLICT,
    "TENANT_MISMATCH": ErrorClass.SCOPE_DENIED,
    "ENVELOPE_MISMATCH": ErrorClass.POLICY_STALE,
    "ENVELOPE_INACTIVE": ErrorClass.POLICY_STALE,
    "SCOPE_EXCEEDED": ErrorClass.SCOPE_DENIED,
    "EFFECT_CLASS_DENIED": ErrorClass.SCOPE_DENIED,
    "PURPOSE_DENIED": ErrorClass.PURPOSE_DENIED,
    "BUDGET_EXCEEDED": ErrorClass.BUDGET_EXCEEDED,
    "ATTEMPTS_EXCEEDED": ErrorClass.BUDGET_EXCEEDED,
    "MISSING_VERIFICATION": ErrorClass.VERIFICATION_FAILED,
    "DEPLOYMENT_ENV_DENIED": ErrorClass.SCOPE_DENIED,
}
"""Every finding code this checker emits, with the error class fixed by design section 4."""

VERIFICATION_LEVEL_RANK: dict[VerificationLevel, int] = {
    VerificationLevel.SCHEMA_VALIDITY: 0,
    VerificationLevel.ARTIFACT_INTEGRITY: 1,
    VerificationLevel.INTEGRATION_BEHAVIOR: 2,
    VerificationLevel.BUSINESS_OUTCOME: 3,
    VerificationLevel.ECONOMIC_RESULT: 4,
}
"""The five verification levels in increasing order (specification section 18)."""

RELEASE_STEP_TYPE_PREFIX = "release."
INFRASTRUCTURE_STEP_TYPE_PREFIX = "infrastructure."
INFRASTRUCTURE_APPLY_STEP_TYPE = "infrastructure.apply"

SHADOW_STEP_TYPES: frozenset[str] = frozenset({"collection.deploy_shadow"})
"""Steps that write only to Plumb's own shadow path; they are not production steps for PL-008."""

DEPLOYMENT_STEP_TYPE_PREFIXES: tuple[str, ...] = (INFRASTRUCTURE_STEP_TYPE_PREFIX, RELEASE_STEP_TYPE_PREFIX)
"""Step types that must declare the deployment environment they act on."""

_READ_LIKE_PURPOSES: frozenset[DataPurpose] = frozenset({DataPurpose.INSPECT, DataPurpose.COLLECT})
_NEVER_INFERRED_PURPOSES: frozenset[DataPurpose] = frozenset({DataPurpose.TRAIN, DataPurpose.EXPORT})


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def required_maturity(step: BuildStep) -> CapabilityMaturity:
    """The maturity floor a capability bound to ``step`` must meet (PL-008).

    ``release.*`` and ``infrastructure.apply`` act on the production estate and
    need ``PRODUCTION_VERIFIED``. Any other step whose effect class is not
    ``READ`` and that is not a shadow deployment is a production step and needs
    ``SANDBOX_TESTED``. Read-only steps and shadow deployments need
    ``DOCUMENTED``: a merely discovered capability has no operation to bind to.
    """
    if step.step_type.startswith(RELEASE_STEP_TYPE_PREFIX) or step.step_type == INFRASTRUCTURE_APPLY_STEP_TYPE:
        return CapabilityMaturity.PRODUCTION_VERIFIED
    if step.effect_class != EffectClass.READ and step.step_type not in SHADOW_STEP_TYPES:
        return CapabilityMaturity.SANDBOX_TESTED
    return CapabilityMaturity.DOCUMENTED


def evaluation_instant(plan: BuildPlan, now: datetime | None) -> datetime:
    """The instant authority is evaluated at: the later of ``plan.planned_at`` and ``now``."""
    planned_at = _require_aware(plan.planned_at, "plan.planned_at")
    if now is None:
        return planned_at
    return max(planned_at, _require_aware(now, "now"))


def check_plan(
    plan: BuildPlan,
    envelope: AutonomyEnvelope,
    registry: CapabilityRegistry | None = None,
    now: datetime | None = None,
) -> CheckReport:
    """Inspect ``plan`` against ``envelope`` and ``registry``; ``report.ok`` means no ERROR finding.

    ``registry`` defaults to the packaged registry. ``now`` (timezone-aware)
    moves the evaluation instant forward from ``plan.planned_at``; it never
    moves it back. ``report.topological_order`` is set when the graph is acyclic.
    """
    if registry is None:
        registry = CapabilityRegistry.default()
    at = evaluation_instant(plan, now)
    report = CheckReport(checker=CHECKER_NAME, subject=plan.artifact_id)

    graph = _StepGraph(plan)
    _check_graph(graph, report)
    report.topological_order = graph.topological_order()

    for step in plan.steps:
        bound = _check_capabilities(step, registry, report)
        _check_inputs(step, plan, graph, report)
        _check_scope(step, envelope, at, report)
        _check_effect_class(step, envelope, bound, report)
        _check_purposes(step, envelope, bound, at, report)
        _check_verification(step, report)
        _check_environment(step, envelope, report)

    _check_envelope_binding(plan, envelope, at, report)
    _check_budgets(plan, envelope, report)

    report.summary = {
        "plan_id": plan.plan_id,
        "steps": len(plan.steps),
        "findings": len(report.findings),
        "errors": len(report.errors),
        "warnings": len(report.warnings),
        "codes": sorted(report.codes()),
        "acyclic": report.topological_order is not None,
        "evaluated_at": at.isoformat(),
    }
    return report


# ---------------------------------------------------------------------------
# Graph structure (PL-014, PL-015)
# ---------------------------------------------------------------------------


class _StepGraph:
    """Dependency graph over the plan's step ids; edges point from a prerequisite to its dependent."""

    def __init__(self, plan: BuildPlan) -> None:
        self.first_declared: dict[str, BuildStep] = {}
        self.declaration_index: dict[str, int] = {}
        self.occurrences: dict[str, int] = {}
        for index, step in enumerate(plan.steps):
            self.occurrences[step.step_id] = self.occurrences.get(step.step_id, 0) + 1
            if step.step_id not in self.first_declared:
                self.first_declared[step.step_id] = step
                self.declaration_index[step.step_id] = index
        self.dependents: dict[str, set[str]] = {step_id: set() for step_id in self.first_declared}
        self.unknown_dependencies: list[tuple[str, str]] = []
        for step in plan.steps:
            for dependency in step.depends_on:
                if dependency in self.first_declared:
                    self.dependents[dependency].add(step.step_id)
                else:
                    self.unknown_dependencies.append((step.step_id, dependency))

    @property
    def duplicates(self) -> dict[str, int]:
        return {step_id: count for step_id, count in self.occurrences.items() if count > 1}

    def topological_order(self) -> list[str] | None:
        """Kahn's algorithm; ties broken by declaration order. None when a cycle exists."""
        indegree = {step_id: 0 for step_id in self.first_declared}
        for dependents in self.dependents.values():
            for dependent in dependents:
                indegree[dependent] += 1
        ready = [(self.declaration_index[step_id], step_id) for step_id, degree in indegree.items() if degree == 0]
        heapq.heapify(ready)
        order: list[str] = []
        while ready:
            _, step_id = heapq.heappop(ready)
            order.append(step_id)
            for dependent in self.dependents[step_id]:
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    heapq.heappush(ready, (self.declaration_index[dependent], dependent))
        if len(order) != len(self.first_declared):
            return None
        return order

    def cycles(self) -> list[list[str]]:
        """Strongly connected components that contain a cycle (Tarjan), members in declaration order."""
        index: dict[str, int] = {}
        lowlink: dict[str, int] = {}
        on_stack: set[str] = set()
        stack: list[str] = []
        components: list[list[str]] = []
        counter = 0

        def visit(node: str) -> None:
            nonlocal counter
            index[node] = lowlink[node] = counter
            counter += 1
            stack.append(node)
            on_stack.add(node)
            for successor in self.dependents[node]:
                if successor not in index:
                    visit(successor)
                    lowlink[node] = min(lowlink[node], lowlink[successor])
                elif successor in on_stack:
                    lowlink[node] = min(lowlink[node], index[successor])
            if lowlink[node] == index[node]:
                component: list[str] = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                if len(component) > 1 or node in self.dependents[node]:
                    components.append(sorted(component, key=self.declaration_index.__getitem__))

        for step_id in self.first_declared:
            if step_id not in index:
                visit(step_id)
        components.sort(key=lambda members: self.declaration_index[members[0]])
        return components


def _check_graph(graph: _StepGraph, report: CheckReport) -> None:
    for step_id, count in graph.duplicates.items():
        _add(
            report,
            "DUPLICATE_STEP_ID",
            f"step id {step_id!r} is declared {count} times; step ids must be unique",
            step_id=step_id,
            occurrences=count,
        )
    for step_id, dependency in graph.unknown_dependencies:
        _add(
            report,
            "UNKNOWN_DEPENDENCY",
            f"step {step_id!r} depends on {dependency!r}, which is not a step of this plan",
            step_id=step_id,
            dependency=dependency,
        )
    for members in graph.cycles():
        _add(
            report,
            "DEPENDENCY_CYCLE",
            f"steps {', '.join(members)} are mutually dependent; the build graph must be acyclic",
            step_id=members[0],
            members=members,
        )


# ---------------------------------------------------------------------------
# Registry binding (PL-008, PL-014)
# ---------------------------------------------------------------------------


def _check_capabilities(step: BuildStep, registry: CapabilityRegistry, report: CheckReport) -> list[CapabilityRecord]:
    """Report unsupported step types, unknown capabilities and insufficient maturity.

    Returns the registry records that exist and implement the step's type (the
    capabilities the step is actually bound to); later rules reason about these.
    """
    if not registry.step_type_known(step.step_type):
        _add(
            report,
            "UNSUPPORTED_STEP_TYPE",
            f"step type {step.step_type!r} is not in the capability registry and is rejected, not interpreted",
            step_id=step.step_id,
            step_type=step.step_type,
        )
    bound: list[CapabilityRecord] = []
    for capability_id in step.required_capabilities:
        record = registry.get(capability_id)
        if record is None:
            _add(
                report,
                "UNKNOWN_CAPABILITY",
                f"capability {capability_id!r} is not in the registry",
                step_id=step.step_id,
                capability_id=capability_id,
            )
        elif record.step_type != step.step_type:
            _add(
                report,
                "UNKNOWN_CAPABILITY",
                f"capability {capability_id!r} implements {record.step_type!r}, not {step.step_type!r}",
                step_id=step.step_id,
                capability_id=capability_id,
                capability_step_type=record.step_type,
            )
        else:
            bound.append(record)
    _check_maturity(step, bound, report)
    return bound


def _check_maturity(step: BuildStep, bound: list[CapabilityRecord], report: CheckReport) -> None:
    if step.step_type == DEPENDENCY_RAISE_STEP_TYPE:
        return
    floor = required_maturity(step)
    if not bound:
        if MATURITY_RANK[floor] >= MATURITY_RANK[CapabilityMaturity.SANDBOX_TESTED]:
            _add(
                report,
                "CAPABILITY_MATURITY_INSUFFICIENT",
                f"no registered capability is bound to this step, so {floor.value} maturity cannot be established",
                step_id=step.step_id,
                required=floor.value,
            )
        return
    for record in bound:
        if not record.at_least(floor):
            _add(
                report,
                "CAPABILITY_MATURITY_INSUFFICIENT",
                f"capability {record.capability_id!r} is {record.maturity.value}; "
                f"this step requires {floor.value} (a documented endpoint is not a verified capability)",
                step_id=step.step_id,
                capability_id=record.capability_id,
                maturity=record.maturity.value,
                required=floor.value,
            )


# ---------------------------------------------------------------------------
# Inputs and outputs (PL-015, PL-016)
# ---------------------------------------------------------------------------


def _check_inputs(step: BuildStep, plan: BuildPlan, graph: _StepGraph, report: CheckReport) -> None:
    for item in step.inputs:
        if (item.from_step is None) == (item.plan_input is None):
            _add(
                report,
                "INPUT_UNRESOLVED",
                f"input {item.name!r} must name exactly one origin (from_step or plan_input)",
                step_id=step.step_id,
                input=item.name,
            )
            continue
        if item.plan_input is not None:
            ref = plan.plan_input_named(item.plan_input)
            if ref is None:
                _add(
                    report,
                    "MISSING_ARTIFACT",
                    f"input {item.name!r} refers to plan input {item.plan_input!r}, which the plan does not carry",
                    step_id=step.step_id,
                    input=item.name,
                    plan_input=item.plan_input,
                )
            elif ref.kind != item.kind:
                _add(
                    report,
                    "INPUT_KIND_MISMATCH",
                    f"input {item.name!r} expects {item.kind.value} but plan input {item.plan_input!r} is {ref.kind.value}",
                    step_id=step.step_id,
                    input=item.name,
                    expected=item.kind.value,
                    actual=ref.kind.value,
                )
            continue
        producer_id = item.from_step
        assert producer_id is not None  # established by the origin check above
        if producer_id not in graph.first_declared:
            _add(
                report,
                "INPUT_UNRESOLVED",
                f"input {item.name!r} comes from step {producer_id!r}, which is not a step of this plan",
                step_id=step.step_id,
                input=item.name,
                from_step=producer_id,
            )
            continue
        if producer_id not in step.depends_on:
            _add(
                report,
                "INPUT_UNRESOLVED",
                f"input {item.name!r} comes from step {producer_id!r}, which is not in depends_on; "
                "a step may only consume verified prerequisites",
                step_id=step.step_id,
                input=item.name,
                from_step=producer_id,
            )
            continue
        output = graph.first_declared[producer_id].output_named(item.name)
        if output is None:
            _add(
                report,
                "INPUT_UNRESOLVED",
                f"step {producer_id!r} does not produce an output named {item.name!r}",
                step_id=step.step_id,
                input=item.name,
                from_step=producer_id,
            )
        elif output.kind != item.kind:
            _add(
                report,
                "INPUT_KIND_MISMATCH",
                f"input {item.name!r} expects {item.kind.value} but step {producer_id!r} produces {output.kind.value}",
                step_id=step.step_id,
                input=item.name,
                from_step=producer_id,
                expected=item.kind.value,
                actual=output.kind.value,
            )


# ---------------------------------------------------------------------------
# Envelope binding (PL-005)
# ---------------------------------------------------------------------------


def _check_envelope_binding(plan: BuildPlan, envelope: AutonomyEnvelope, at: datetime, report: CheckReport) -> None:
    if plan.tenant_id != envelope.tenant_id:
        _add(
            report,
            "TENANT_MISMATCH",
            f"plan belongs to tenant {plan.tenant_id!r} but the envelope belongs to {envelope.tenant_id!r}",
            plan_tenant_id=plan.tenant_id,
            envelope_tenant_id=envelope.tenant_id,
        )
    mismatches: dict[str, dict[str, Any]] = {}
    if plan.envelope_id != envelope.envelope_id:
        mismatches["envelope_id"] = {"plan": plan.envelope_id, "envelope": envelope.envelope_id}
    if plan.envelope_version != envelope.envelope_version:
        mismatches["envelope_version"] = {"plan": plan.envelope_version, "envelope": envelope.envelope_version}
    if mismatches:
        _add(
            report,
            "ENVELOPE_MISMATCH",
            f"plan was compiled against envelope {plan.envelope_id!r} v{plan.envelope_version} "
            f"but is checked against {envelope.envelope_id!r} v{envelope.envelope_version}",
            **mismatches,
        )
    if envelope.revoked_at is not None:
        _add(
            report,
            "ENVELOPE_INACTIVE",
            f"envelope was revoked at {envelope.revoked_at.isoformat()}; cached authority is invalid",
            revoked_at=envelope.revoked_at.isoformat(),
        )
    if at >= envelope.expires_at:
        _add(
            report,
            "ENVELOPE_INACTIVE",
            f"envelope expired at {envelope.expires_at.isoformat()}, before the evaluation instant {at.isoformat()}",
            expires_at=envelope.expires_at.isoformat(),
            evaluated_at=at.isoformat(),
        )
    if at < envelope.created_at:
        _add(
            report,
            "ENVELOPE_INACTIVE",
            f"envelope version comes into force at {envelope.created_at.isoformat()}, "
            f"after the evaluation instant {at.isoformat()}",
            created_at=envelope.created_at.isoformat(),
            evaluated_at=at.isoformat(),
        )


# ---------------------------------------------------------------------------
# Authority per step (PL-005, PL-053)
# ---------------------------------------------------------------------------


def _check_scope(step: BuildStep, envelope: AutonomyEnvelope, at: datetime, report: CheckReport) -> None:
    violations = step.scope.is_within(envelope.scope(now=at))
    if violations:
        _add(
            report,
            "SCOPE_EXCEEDED",
            f"step scope exceeds the envelope: {'; '.join(violations)}",
            step_id=step.step_id,
            violations=violations,
        )


def _check_effect_class(
    step: BuildStep, envelope: AutonomyEnvelope, bound: list[CapabilityRecord], report: CheckReport
) -> None:
    allowed = set(envelope.allowed_effect_classes)
    if step.effect_class not in allowed:
        _add(
            report,
            "EFFECT_CLASS_DENIED",
            f"effect class {step.effect_class.value} is not allowed by the envelope "
            f"(allowed: {_values(sorted(allowed, key=_enum_value))})",
            step_id=step.step_id,
            effect_class=step.effect_class.value,
        )
    for record in bound:
        if step.effect_class not in record.effect_classes:
            _add(
                report,
                "EFFECT_CLASS_DENIED",
                f"capability {record.capability_id!r} produces {_values(record.effect_classes)}, "
                f"not the declared {step.effect_class.value}",
                step_id=step.step_id,
                capability_id=record.capability_id,
                effect_class=step.effect_class.value,
            )
        wider = [effect for effect in record.effect_classes if effect not in allowed and effect != step.effect_class]
        if wider:
            _add(
                report,
                "EFFECT_CLASS_DENIED",
                f"capability {record.capability_id!r} can also produce {_values(wider)}, "
                "which the envelope does not allow",
                step_id=step.step_id,
                severity=Severity.WARNING,
                capability_id=record.capability_id,
                undeclared_effect_classes=[effect.value for effect in wider],
            )


def _check_purposes(
    step: BuildStep,
    envelope: AutonomyEnvelope,
    bound: list[CapabilityRecord],
    at: datetime,
    report: CheckReport,
) -> None:
    if not step.scope.source_ids:
        return
    required_by_capability: dict[DataPurpose, list[str]] = {}
    for record in bound:
        for purpose in record.required_purposes:
            required_by_capability.setdefault(purpose, []).append(record.capability_id)
    effective = set(step.purposes) | set(required_by_capability)
    if not effective:
        _add(
            report,
            "PURPOSE_DENIED",
            f"step touches source(s) {', '.join(step.scope.source_ids)} but declares no data purpose",
            step_id=step.step_id,
            source_ids=list(step.scope.source_ids),
        )
        return
    for source_id in step.scope.source_ids:
        granted = envelope.purposes_for(source_id, now=at)
        missing = sorted(effective - granted, key=_enum_value)
        if not missing:
            continue
        message = (
            f"purpose(s) {_values(missing)} are not granted for source {source_id!r} "
            f"(granted: {_values(sorted(granted, key=_enum_value)) or 'none'})"
        )
        if _NEVER_INFERRED_PURPOSES.intersection(missing) and _READ_LIKE_PURPOSES.intersection(granted):
            message += "; permission to train or export is never inferred from permission to inspect or collect"
        _add(
            report,
            "PURPOSE_DENIED",
            message,
            step_id=step.step_id,
            source_id=source_id,
            missing=[purpose.value for purpose in missing],
            granted=sorted(purpose.value for purpose in granted),
            required_by_capabilities={
                purpose.value: capability_ids
                for purpose, capability_ids in required_by_capability.items()
                if purpose in missing
            },
        )


# ---------------------------------------------------------------------------
# Budgets (PL-018, PL-058)
# ---------------------------------------------------------------------------


def _check_budgets(plan: BuildPlan, envelope: AutonomyEnvelope, report: CheckReport) -> None:
    currency = plan.total_budget.spend.currency
    step_total = 0
    for step in plan.steps:
        if step.budget.spend.currency != currency:
            _add(
                report,
                "BUDGET_EXCEEDED",
                f"step budget is in {step.budget.spend.currency} but the plan total is in {currency}; "
                "budgets cannot be summed across currencies",
                step_id=step.step_id,
                step_currency=step.budget.spend.currency,
                plan_currency=currency,
            )
        else:
            step_total += step.budget.spend.minor_units
        if step.budget.max_attempts > envelope.per_step_attempt_limit:
            _add(
                report,
                "ATTEMPTS_EXCEEDED",
                f"step allows {step.budget.max_attempts} attempts but the envelope permits "
                f"at most {envelope.per_step_attempt_limit} per step",
                step_id=step.step_id,
                max_attempts=step.budget.max_attempts,
                per_step_attempt_limit=envelope.per_step_attempt_limit,
            )
    declared_total = plan.total_budget.spend.minor_units
    if step_total > declared_total:
        _add(
            report,
            "BUDGET_EXCEEDED",
            f"worst-case step spend {step_total} {currency} exceeds the declared plan total {declared_total} {currency}",
            step_spend_total=step_total,
            plan_total=declared_total,
            currency=currency,
        )
    limit = envelope.spending_limit
    if limit.currency != currency:
        _add(
            report,
            "BUDGET_EXCEEDED",
            f"plan budget is in {currency} but the envelope spending limit is in {limit.currency}",
            plan_currency=currency,
            envelope_currency=limit.currency,
        )
    elif declared_total > limit.minor_units:
        _add(
            report,
            "BUDGET_EXCEEDED",
            f"declared plan total {declared_total} {currency} exceeds the envelope spending limit "
            f"{limit.minor_units} {currency}",
            plan_total=declared_total,
            spending_limit=limit.minor_units,
            currency=currency,
        )


# ---------------------------------------------------------------------------
# Verification coverage (PL-016, PL-043)
# ---------------------------------------------------------------------------


def _check_verification(step: BuildStep, report: CheckReport) -> None:
    levels = {obligation.level for obligation in step.verification}
    highest = max((VERIFICATION_LEVEL_RANK[level] for level in levels), default=-1)
    if not levels and step.step_type != DEPENDENCY_RAISE_STEP_TYPE:
        _add(
            report,
            "MISSING_VERIFICATION",
            "step declares no verification obligation; a worker's completion claim cannot verify it",
            step_id=step.step_id,
        )
    elif step.has_external_effect and highest < VERIFICATION_LEVEL_RANK[VerificationLevel.INTEGRATION_BEHAVIOR]:
        _add(
            report,
            "MISSING_VERIFICATION",
            f"step has effect class {step.effect_class.value} but no obligation at "
            f"{VerificationLevel.INTEGRATION_BEHAVIOR.value} or higher; passing unit tests cannot "
            "substitute for verifying a real external effect",
            step_id=step.step_id,
            effect_class=step.effect_class.value,
            required_level=VerificationLevel.INTEGRATION_BEHAVIOR.value,
            declared_levels=sorted(level.value for level in levels),
        )
    if step.step_type.startswith(RELEASE_STEP_TYPE_PREFIX) and VerificationLevel.BUSINESS_OUTCOME not in levels:
        _add(
            report,
            "MISSING_VERIFICATION",
            f"release step has no {VerificationLevel.BUSINESS_OUTCOME.value} obligation; "
            "a release must include business scenario evaluation",
            step_id=step.step_id,
            required_level=VerificationLevel.BUSINESS_OUTCOME.value,
            declared_levels=sorted(level.value for level in levels),
        )


# ---------------------------------------------------------------------------
# Deployment environments (PL-005)
# ---------------------------------------------------------------------------


def _check_environment(step: BuildStep, envelope: AutonomyEnvelope, report: CheckReport) -> None:
    deployment_step = step.step_type.startswith(DEPLOYMENT_STEP_TYPE_PREFIXES)
    if step.environment is None:
        if deployment_step:
            read_only = step.effect_class == EffectClass.READ
            _add(
                report,
                "DEPLOYMENT_ENV_DENIED",
                f"{step.step_type} step declares no deployment environment; "
                f"allowed environments are {', '.join(envelope.deployment_environments) or 'none'}",
                step_id=step.step_id,
                severity=Severity.WARNING if read_only else Severity.ERROR,
                allowed_environments=list(envelope.deployment_environments),
            )
        return
    if step.environment not in envelope.deployment_environments:
        _add(
            report,
            "DEPLOYMENT_ENV_DENIED",
            f"environment {step.environment!r} is not among the envelope's deployment environments "
            f"({', '.join(envelope.deployment_environments) or 'none'})",
            step_id=step.step_id,
            environment=step.environment,
            allowed_environments=list(envelope.deployment_environments),
        )


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _add(
    report: CheckReport,
    code: str,
    message: str,
    *,
    step_id: str | None = None,
    severity: Severity = Severity.ERROR,
    **details: Any,
) -> None:
    report.add(
        Finding(
            code=code,
            error_class=FINDING_ERROR_CLASSES[code],
            message=message,
            severity=severity,
            step_id=step_id,
            details=details,
        )
    )


def _require_aware(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    return value


def _enum_value(member: EffectClass | DataPurpose) -> str:
    return member.value


def _values(members: Iterable[EffectClass | DataPurpose]) -> str:
    return ", ".join(member.value for member in members)


__all__ = [
    "CHECKER_NAME",
    "FINDING_ERROR_CLASSES",
    "VERIFICATION_LEVEL_RANK",
    "SHADOW_STEP_TYPES",
    "DEPLOYMENT_STEP_TYPE_PREFIXES",
    "required_maturity",
    "evaluation_instant",
    "check_plan",
]
