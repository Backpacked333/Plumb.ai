"""Reference plan checker: is this BuildPlan executable within this envelope? (design section 4)

Implements (specification v0.2):

* PL-005: a derived task cannot widen the autonomy envelope. Every step's scope,
  effect class, purposes, budget, attempts and deployment environment are
  compared against the envelope the plan claims to be compiled against, and the
  envelope must be the one named (id, version and content digest), in force at
  the evaluation instant, belonging to the same tenant, and the plan's goal must
  be one of the envelope's goals.
* PL-008: discovered, documented, sandbox-tested and production-verified
  capabilities are distinct. Every step except ``dependency.raise`` is bound to
  at least one registry record; production steps need ``SANDBOX_TESTED`` or
  better, ``release.*`` and ``infrastructure.apply`` need
  ``PRODUCTION_VERIFIED``, read-only probes and shadow deployments that write
  only to Plumb's own storage accept ``DOCUMENTED`` (see :func:`required_maturity`).
  A step with no bound capability has no established effect class, purposes or
  maturity, so it is rejected rather than trusted.
* PL-014: a plan is a finite dependency graph of typed steps. Unsupported step
  types and unknown capabilities are rejected rather than interpreted, and the
  graph must be acyclic (the cycle members are reported).
* PL-015: unique ids, valid dependencies, cycles, input/output compatibility
  (producer kind equals consumer kind, and the bound capabilities actually
  produce and consume those kinds), missing artifacts, authority,
  region/purpose restrictions, effect class, budget and verification coverage
  are all checked; a syntactically valid plan is not necessarily executable.
* PL-016 / PL-043: every step except ``dependency.raise`` carries at least one
  verification obligation; a step with external effects needs a check at
  ``INTEGRATION_BEHAVIOR`` or higher (passing unit tests cannot substitute for
  verifying a real external effect); a ``release.*`` step needs a
  ``BUSINESS_OUTCOME`` check. A required step may only consume verifiable,
  required prerequisites: never an optional (``required=False``) step and never
  a ``dependency.raise`` step, which has no verification obligation.
* PL-018 / PL-058: the declared worst-case budgets must nest in every
  dimension: step spend sums to at most the plan total and the plan total is
  within the envelope spending limit, in one currency; a step's attempts,
  elapsed time and model calls stay within the plan total (steps may run in
  parallel, so elapsed time is compared per step, model calls are summed) and
  attempts within the envelope's per-step limit. The checker verifies declared
  reservations; it meters nothing.
* PL-045: an ``infrastructure.apply`` step must consume the
  ``InfrastructurePreview`` of a preceding ``infrastructure.preview`` step and
  an ``ApprovalRecord``; infrastructure code never runs unpreviewed or
  unapproved.
* PL-053: for every source a step touches, its purposes (declared, plus those
  the bound capabilities require) must be granted for that source. *Derived
  data inherits restrictions*: a step also touches every source that flows into
  it through data-bearing inputs (evidence packets, datasets, model versions,
  ...), transitively along ``from_step`` edges, unless the input declares a
  narrower ``source_ids`` set that is a subset of what its producer touched.
  Permission to ``TRAIN`` or ``EXPORT`` is never inferred from ``INSPECT`` or
  ``COLLECT``, and a step that trains or exports without touching any source
  (declared or inherited) has established no authority at all.

Finding table (``code`` -> error class; severity ERROR unless stated):

=================================== ====================== =======================================
DUPLICATE_STEP_ID                   STATE_CONFLICT         step ids unique
UNKNOWN_DEPENDENCY                  STATE_CONFLICT         every depends_on names a step
DEPENDENCY_CYCLE                    STATE_CONFLICT         graph is a DAG; ``details.members``
UNSUPPORTED_STEP_TYPE               CAPABILITY_UNSUPPORTED step_type known to the registry
UNKNOWN_CAPABILITY                  CAPABILITY_UNSUPPORTED capability in registry and for this step
                                                           type; every step but dependency.raise
                                                           binds at least one
CAPABILITY_MATURITY_INSUFFICIENT    CAPABILITY_UNSUPPORTED bound capability meets :func:`required_maturity`
ARTIFACT_KIND_UNSUPPORTED           CAPABILITY_UNSUPPORTED bound capabilities produce every output
                                                           kind and consume every input kind
INPUT_UNRESOLVED                    STATE_CONFLICT         from_step in depends_on and produces the output
INPUT_KIND_MISMATCH                 STATE_CONFLICT         input kind equals the producing kind
MISSING_ARTIFACT                    STATE_CONFLICT         plan_input names a BuildPlan.inputs entry
PRECONDITION_MISSING                STATE_CONFLICT         infrastructure.apply consumes a preview from an
                                                           infrastructure.preview dependency and an
                                                           ApprovalRecord (PL-045)
UNVERIFIABLE_PREREQUISITE           VERIFICATION_FAILED    a required step never depends on or consumes
                                                           an optional or dependency.raise step
TENANT_MISMATCH                     SCOPE_DENIED           plan and envelope share a tenant
ENVELOPE_MISMATCH                   POLICY_STALE           plan names this envelope id and version, and its
                                                           envelope input ref has this kind and digest
ENVELOPE_INACTIVE                   POLICY_STALE           envelope not revoked, in force at the instant
GOAL_NOT_AUTHORIZED                 SCOPE_DENIED           plan.goal_id is one of the envelope's goals
SCOPE_EXCEEDED                      SCOPE_DENIED           step scope within the envelope scope; an input's
                                                           source narrowing within its producer's sources
EFFECT_CLASS_DENIED                 SCOPE_DENIED           effect class allowed by envelope and capability
                                                           (WARNING when a bound capability can also
                                                           produce a class the envelope does not allow)
PURPOSE_DENIED                      PURPOSE_DENIED         purposes granted per declared and inherited
                                                           source (PL-053)
BUDGET_EXCEEDED                     BUDGET_EXCEEDED        nested budgets, one currency (PL-058)
ATTEMPTS_EXCEEDED                   BUDGET_EXCEEDED        max_attempts within the envelope and plan limits
MISSING_VERIFICATION                VERIFICATION_FAILED    obligations present and at the required level
DEPLOYMENT_ENV_DENIED               SCOPE_DENIED           environment declared and allowed
                                                           (WARNING for a read-only infrastructure step
                                                           that declares none)
=================================== ====================== =======================================

Conventions:

* The evaluation instant is the later of ``plan.planned_at`` and the caller's
  ``now`` (both timezone-aware); grants and the envelope's validity are
  evaluated at that instant. A revoked envelope is inactive whatever the instant.
* The deployment environment of a step is read from ``BuildStep.environment``;
  nothing is inferred from ``scope.destination_ids``.
* Lineage flows only through :data:`DATA_BEARING_KINDS`; a ``ReleaseManifest``
  or ``VerificationReceipt`` carries no customer data and ends the chain.
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
    ArtifactKind,
    CapabilityMaturity,
    DataPurpose,
    EffectClass,
    ErrorClass,
    VerificationLevel,
    compute_artifact_digest,
    require_aware,
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
    "ARTIFACT_KIND_UNSUPPORTED": ErrorClass.CAPABILITY_UNSUPPORTED,
    "INPUT_UNRESOLVED": ErrorClass.STATE_CONFLICT,
    "INPUT_KIND_MISMATCH": ErrorClass.STATE_CONFLICT,
    "MISSING_ARTIFACT": ErrorClass.STATE_CONFLICT,
    "PRECONDITION_MISSING": ErrorClass.STATE_CONFLICT,
    "UNVERIFIABLE_PREREQUISITE": ErrorClass.VERIFICATION_FAILED,
    "TENANT_MISMATCH": ErrorClass.SCOPE_DENIED,
    "ENVELOPE_MISMATCH": ErrorClass.POLICY_STALE,
    "ENVELOPE_INACTIVE": ErrorClass.POLICY_STALE,
    "GOAL_NOT_AUTHORIZED": ErrorClass.SCOPE_DENIED,
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
INFRASTRUCTURE_PREVIEW_STEP_TYPE = "infrastructure.preview"
INFRASTRUCTURE_APPLY_STEP_TYPE = "infrastructure.apply"

SHADOW_STEP_TYPES: frozenset[str] = frozenset({"collection.deploy_shadow"})
"""Steps that write only to Plumb's own shadow path; with READ or INTERNAL_WRITE they are not production steps."""

INTERNAL_EFFECT_CLASSES: frozenset[EffectClass] = frozenset({EffectClass.READ, EffectClass.INTERNAL_WRITE})
"""Effect classes that stay inside Plumb's own storage; the only ones a shadow deployment may declare and stay exempt."""

DEPLOYMENT_STEP_TYPE_PREFIXES: tuple[str, ...] = (INFRASTRUCTURE_STEP_TYPE_PREFIX, RELEASE_STEP_TYPE_PREFIX)
"""Step types that must declare the deployment environment they act on."""

DATA_BEARING_KINDS: frozenset[ArtifactKind] = frozenset(
    {
        ArtifactKind.EVIDENCE_PACKET,
        ArtifactKind.QUALITY_REPORT,
        ArtifactKind.SOURCE_CANDIDATE_TABLE,
        ArtifactKind.DATASET_MANIFEST,
        ArtifactKind.LABEL_AUDIT_REPORT,
        ArtifactKind.MODEL_VERSION,
        ArtifactKind.EVALUATION_REPORT,
    }
)
"""Artifact kinds that carry customer data derived from sources; lineage (PL-053) flows through them."""

REQUIRED_INPUT_KINDS: dict[str, dict[ArtifactKind, str | None]] = {
    INFRASTRUCTURE_APPLY_STEP_TYPE: {
        ArtifactKind.INFRASTRUCTURE_PREVIEW: INFRASTRUCTURE_PREVIEW_STEP_TYPE,
        ArtifactKind.APPROVAL_RECORD: None,
    },
}
"""Per step type, the input kinds that must precede it and (optionally) the step type that must produce them (PL-045)."""

_READ_LIKE_PURPOSES: frozenset[DataPurpose] = frozenset({DataPurpose.INSPECT, DataPurpose.COLLECT})
_NEVER_INFERRED_PURPOSES: frozenset[DataPurpose] = frozenset({DataPurpose.TRAIN, DataPurpose.EXPORT})


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def required_maturity(step: BuildStep) -> CapabilityMaturity:
    """The maturity floor a capability bound to ``step`` must meet (PL-008).

    ``release.*`` and ``infrastructure.apply`` act on the production estate and
    need ``PRODUCTION_VERIFIED``. ``dependency.raise`` records a dependency in
    Plumb's own control plane and needs ``DOCUMENTED``. Any other step whose
    effect class reaches outside Plumb's storage is a production step and needs
    ``SANDBOX_TESTED``; so does any ``INTERNAL_WRITE`` step other than a shadow
    deployment. Read-only steps and shadow deployments that declare ``READ`` or
    ``INTERNAL_WRITE`` need ``DOCUMENTED``: a merely discovered capability has
    no operation to bind to. A shadow deployment that declares an external
    write is not writing to the shadow path and gets no exemption.
    """
    if step.step_type.startswith(RELEASE_STEP_TYPE_PREFIX) or step.step_type == INFRASTRUCTURE_APPLY_STEP_TYPE:
        return CapabilityMaturity.PRODUCTION_VERIFIED
    if step.step_type == DEPENDENCY_RAISE_STEP_TYPE:
        return CapabilityMaturity.DOCUMENTED
    if step.effect_class == EffectClass.READ:
        return CapabilityMaturity.DOCUMENTED
    if step.step_type in SHADOW_STEP_TYPES and step.effect_class in INTERNAL_EFFECT_CLASSES:
        return CapabilityMaturity.DOCUMENTED
    return CapabilityMaturity.SANDBOX_TESTED


def evaluation_instant(plan: BuildPlan, now: datetime | None) -> datetime:
    """The instant authority is evaluated at: the later of ``plan.planned_at`` and ``now``."""
    planned_at = require_aware(plan.planned_at, "plan.planned_at")
    if now is None:
        return planned_at
    return max(planned_at, require_aware(now, "now"))


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
    lineage = _Lineage(graph, report)

    for step in plan.steps:
        bound = _check_capabilities(step, registry, report)
        _check_inputs(step, plan, graph, report)
        _check_artifact_kinds(step, bound, report)
        _check_preconditions(step, graph, report)
        _check_prerequisites(step, graph, report)
        _check_scope(step, envelope, at, report)
        _check_effect_class(step, envelope, bound, report)
        _check_purposes(step, envelope, bound, lineage.sources_of(step), at, report)
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
        "inherited_sources": {step_id: sorted(sources) for step_id, sources in lineage.inherited.items() if sources},
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
# Source lineage (PL-053: derived data inherits restrictions)
# ---------------------------------------------------------------------------


class _Lineage:
    """Effective source set per step: declared sources plus those inherited through data-bearing inputs.

    Computed over the graph in topological order; in a cyclic graph only the
    declared sources are used (the cycle is reported separately). An input may
    narrow the lineage it carries with ``StepInput.source_ids``; the narrowing
    must be a subset of what the producer touched, otherwise it is reported as
    ``SCOPE_EXCEEDED`` and the excess is ignored.
    """

    def __init__(self, graph: _StepGraph, report: CheckReport) -> None:
        self.effective: dict[str, set[str]] = {}
        self.inherited: dict[str, set[str]] = {}
        order = graph.topological_order() or list(graph.first_declared)
        for step_id in order:
            step = graph.first_declared[step_id]
            declared = set(step.scope.source_ids)
            inherited: set[str] = set()
            for item in step.inputs:
                if item.from_step is None or item.kind not in DATA_BEARING_KINDS:
                    continue
                producer_sources = self.effective.get(item.from_step)
                if producer_sources is None:
                    continue  # unresolved producer or cyclic graph; reported elsewhere
                if item.source_ids is None:
                    inherited |= producer_sources
                    continue
                narrowed = set(item.source_ids)
                extra = sorted(narrowed - producer_sources)
                if extra:
                    _add(
                        report,
                        "SCOPE_EXCEEDED",
                        f"input {item.name!r} narrows its lineage to source(s) {', '.join(extra)} that its producer "
                        f"{item.from_step!r} does not touch (producer sources: {_names(producer_sources)})",
                        step_id=step.step_id,
                        input=item.name,
                        from_step=item.from_step,
                        narrowed_to=sorted(narrowed),
                        producer_sources=sorted(producer_sources),
                    )
                inherited |= narrowed & producer_sources
            self.inherited[step_id] = inherited - declared
            self.effective[step_id] = declared | inherited

    def sources_of(self, step: BuildStep) -> set[str]:
        return self.effective.get(step.step_id, set(step.scope.source_ids))


# ---------------------------------------------------------------------------
# Registry binding (PL-008, PL-014, PL-015)
# ---------------------------------------------------------------------------


def _check_capabilities(step: BuildStep, registry: CapabilityRegistry, report: CheckReport) -> list[CapabilityRecord]:
    """Report unsupported step types, unknown or missing capabilities and insufficient maturity.

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
    if not step.required_capabilities and step.step_type != DEPENDENCY_RAISE_STEP_TYPE:
        _add(
            report,
            "UNKNOWN_CAPABILITY",
            "step binds no registered capability; its effect class, required purposes and maturity cannot be "
            "established from the planner's declaration alone (PL-008, PL-014)",
            step_id=step.step_id,
            step_type=step.step_type,
            registered_capabilities=[record.capability_id for record in registry.capabilities_for_step_type(step.step_type)],
        )
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
    floor = required_maturity(step)
    if not bound:
        if step.step_type == DEPENDENCY_RAISE_STEP_TYPE:
            return  # the control plane itself records the dependency; nothing external is bound
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


def _check_artifact_kinds(step: BuildStep, bound: list[CapabilityRecord], report: CheckReport) -> None:
    """Outputs must be producible and inputs consumable by the bound capabilities (PL-015)."""
    if not bound:
        return
    produces = {kind for record in bound for kind in record.produces}
    consumes = {kind for record in bound for kind in record.consumes}
    capability_ids = [record.capability_id for record in bound]
    for output in step.outputs:
        if output.kind not in produces:
            _add(
                report,
                "ARTIFACT_KIND_UNSUPPORTED",
                f"output {output.name!r} is declared as {output.kind.value}, which none of the bound capabilities "
                f"({', '.join(capability_ids)}) produces; a step cannot fabricate an artifact kind",
                step_id=step.step_id,
                direction="produces",
                artifact=output.name,
                kind=output.kind.value,
                capability_ids=capability_ids,
                supported=sorted(kind.value for kind in produces),
            )
    for item in step.inputs:
        if item.kind not in consumes:
            _add(
                report,
                "ARTIFACT_KIND_UNSUPPORTED",
                f"input {item.name!r} is a {item.kind.value}, which none of the bound capabilities "
                f"({', '.join(capability_ids)}) consumes",
                step_id=step.step_id,
                direction="consumes",
                artifact=item.name,
                kind=item.kind.value,
                capability_ids=capability_ids,
                supported=sorted(kind.value for kind in consumes),
            )


# ---------------------------------------------------------------------------
# Inputs, outputs and prerequisites (PL-015, PL-016, PL-045)
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


def _check_preconditions(step: BuildStep, graph: _StepGraph, report: CheckReport) -> None:
    """Steps with mandatory preceding artifacts (PL-045: preview and approval before infrastructure.apply)."""
    required = REQUIRED_INPUT_KINDS.get(step.step_type)
    if not required:
        return
    for kind, producer_type in required.items():
        candidates = [item for item in step.inputs if item.kind is kind]
        if producer_type is not None:
            candidates = [
                item
                for item in candidates
                if item.from_step is not None
                and item.from_step in step.depends_on
                and item.from_step in graph.first_declared
                and graph.first_declared[item.from_step].step_type == producer_type
            ]
        if candidates:
            continue
        origin = (
            f"produced by a preceding {producer_type} step it depends on"
            if producer_type
            else "as a plan input or a preceding step's output"
        )
        _add(
            report,
            "PRECONDITION_MISSING",
            f"{step.step_type} consumes no {kind.value} {origin}; a preview/diff, cost estimate and approval "
            "must precede application (PL-045)",
            step_id=step.step_id,
            required_kind=kind.value,
            required_producer_step_type=producer_type,
        )


def _check_prerequisites(step: BuildStep, graph: _StepGraph, report: CheckReport) -> None:
    """A required step never rests on an optional or unverifiable (dependency.raise) prerequisite (PL-016)."""
    if step.step_type == DEPENDENCY_RAISE_STEP_TYPE:
        return
    referenced = list(dict.fromkeys([*step.depends_on, *(item.from_step for item in step.inputs if item.from_step)]))
    for prerequisite_id in referenced:
        prerequisite = graph.first_declared.get(prerequisite_id)
        if prerequisite is None:
            continue  # unknown dependency / unresolved input; reported elsewhere
        if prerequisite.step_type == DEPENDENCY_RAISE_STEP_TYPE:
            _add(
                report,
                "UNVERIFIABLE_PREREQUISITE",
                f"step depends on {prerequisite_id!r}, a dependency.raise step that carries no verification obligation "
                "and can never become a verified prerequisite; downstream steps must not consume it",
                step_id=step.step_id,
                prerequisite=prerequisite_id,
                reason="dependency_raise",
            )
        elif step.required and not prerequisite.required:
            _add(
                report,
                "UNVERIFIABLE_PREREQUISITE",
                f"required step depends on optional step {prerequisite_id!r} (required=False); an optional step may be "
                "skipped or fail without failing the build, so a required step cannot rest on it",
                step_id=step.step_id,
                prerequisite=prerequisite_id,
                reason="optional_prerequisite",
            )


# ---------------------------------------------------------------------------
# Envelope binding (PL-005)
# ---------------------------------------------------------------------------


def _check_envelope_binding(plan: BuildPlan, envelope: AutonomyEnvelope, at: datetime, report: CheckReport) -> None:
    if plan.tenant_id != envelope.tenant_id:
        _add(
            report,
            "TENANT_MISMATCH",
            "plan and envelope belong to different tenants; a plan is checked only against the authenticated tenant's envelope",
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
    envelope_ref = plan.plan_input_named(envelope.envelope_id)
    if envelope_ref is not None:
        actual_digest = compute_artifact_digest(envelope)
        problems: dict[str, Any] = {}
        if envelope_ref.kind is not ArtifactKind.AUTONOMY_ENVELOPE:
            problems["kind"] = {"plan_input": envelope_ref.kind.value, "expected": ArtifactKind.AUTONOMY_ENVELOPE.value}
        if envelope_ref.digest != actual_digest:
            problems["digest"] = {"plan_input": envelope_ref.digest, "envelope": actual_digest}
        if problems:
            _add(
                report,
                "ENVELOPE_MISMATCH",
                f"plan input {envelope_ref.artifact_id!r} does not pin the envelope it is checked against "
                f"({', '.join(problems)} differ); the plan was compiled against different envelope bytes",
                **problems,
            )
    if plan.goal_id not in {goal.goal_id for goal in envelope.goals}:
        _add(
            report,
            "GOAL_NOT_AUTHORIZED",
            f"plan pursues goal {plan.goal_id!r}, which the envelope does not define "
            f"(authorized goals: {', '.join(goal.goal_id for goal in envelope.goals)})",
            plan_goal_id=plan.goal_id,
            envelope_goal_ids=[goal.goal_id for goal in envelope.goals],
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
    sources: set[str],
    at: datetime,
    report: CheckReport,
) -> None:
    """Every declared or inherited source must grant the step's effective purposes (PL-053)."""
    required_by_capability: dict[DataPurpose, list[str]] = {}
    for record in bound:
        for purpose in record.required_purposes:
            required_by_capability.setdefault(purpose, []).append(record.capability_id)
    effective = set(step.purposes) | set(required_by_capability)
    declared_sources = list(step.scope.source_ids)
    inherited_sources = sorted(sources - set(declared_sources))
    if not sources:
        never_inferred = sorted(effective & _NEVER_INFERRED_PURPOSES, key=_enum_value)
        if never_inferred:
            _add(
                report,
                "PURPOSE_DENIED",
                f"step declares purpose(s) {_values(never_inferred)} but touches no source, declared or inherited; "
                "permission to train or export is established per source grant and cannot be claimed without one",
                step_id=step.step_id,
                purposes=[purpose.value for purpose in never_inferred],
            )
        return
    if not effective:
        if declared_sources:
            _add(
                report,
                "PURPOSE_DENIED",
                f"step touches source(s) {', '.join(declared_sources)} but declares no data purpose",
                step_id=step.step_id,
                source_ids=declared_sources,
            )
        return  # inherited-only lineage with no data use (e.g. a release binding an evaluation report) is not a use
    for source_id in [*declared_sources, *inherited_sources]:
        granted = envelope.purposes_for(source_id, now=at)
        missing = sorted(effective - granted, key=_enum_value)
        if not missing:
            continue
        inherited = source_id not in declared_sources
        message = (
            f"purpose(s) {_values(missing)} are not granted for source {source_id!r} "
            f"(granted: {_values(sorted(granted, key=_enum_value)) or 'none'})"
        )
        if inherited:
            message += "; the source is inherited through this step's inputs and derived data inherits its restrictions"
        if _NEVER_INFERRED_PURPOSES.intersection(missing) and _READ_LIKE_PURPOSES.intersection(granted):
            message += "; permission to train or export is never inferred from permission to inspect or collect"
        _add(
            report,
            "PURPOSE_DENIED",
            message,
            step_id=step.step_id,
            source_id=source_id,
            inherited=inherited,
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
    total = plan.total_budget
    currency = total.spend.currency
    step_total = 0
    model_calls_total = 0
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
        model_calls_total += step.budget.max_model_calls or 0
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
        elif step.budget.max_attempts > total.max_attempts:
            _add(
                report,
                "ATTEMPTS_EXCEEDED",
                f"step allows {step.budget.max_attempts} attempts but the plan's total budget bounds attempts "
                f"at {total.max_attempts}",
                step_id=step.step_id,
                max_attempts=step.budget.max_attempts,
                plan_max_attempts=total.max_attempts,
            )
        if step.budget.max_elapsed_seconds > total.max_elapsed_seconds:
            _add(
                report,
                "BUDGET_EXCEEDED",
                f"step may run for {step.budget.max_elapsed_seconds}s but the plan's total budget bounds elapsed time "
                f"at {total.max_elapsed_seconds}s",
                step_id=step.step_id,
                dimension="max_elapsed_seconds",
                step_max_elapsed_seconds=step.budget.max_elapsed_seconds,
                plan_max_elapsed_seconds=total.max_elapsed_seconds,
            )
    declared_total = total.spend.minor_units
    if step_total > declared_total:
        _add(
            report,
            "BUDGET_EXCEEDED",
            f"worst-case step spend {step_total} {currency} exceeds the declared plan total {declared_total} {currency}",
            step_spend_total=step_total,
            plan_total=declared_total,
            currency=currency,
        )
    if total.max_model_calls is not None and model_calls_total > total.max_model_calls:
        _add(
            report,
            "BUDGET_EXCEEDED",
            f"worst-case step model calls {model_calls_total} exceed the declared plan total {total.max_model_calls}",
            dimension="max_model_calls",
            step_model_calls_total=model_calls_total,
            plan_max_model_calls=total.max_model_calls,
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


_require_aware = require_aware


def _enum_value(member: EffectClass | DataPurpose) -> str:
    return member.value


def _values(members: Iterable[EffectClass | DataPurpose]) -> str:
    return ", ".join(member.value for member in members)


def _names(values: Iterable[str]) -> str:
    return ", ".join(sorted(values)) or "none"


__all__ = [
    "CHECKER_NAME",
    "FINDING_ERROR_CLASSES",
    "VERIFICATION_LEVEL_RANK",
    "SHADOW_STEP_TYPES",
    "INTERNAL_EFFECT_CLASSES",
    "DEPLOYMENT_STEP_TYPE_PREFIXES",
    "DATA_BEARING_KINDS",
    "REQUIRED_INPUT_KINDS",
    "required_maturity",
    "evaluation_instant",
    "check_plan",
]
