"""Bounded plan validator (spec/blueprint-and-compiler.md, SR-040..SR-052).

Passes, in order, each producing typed errors. A plan with any error is not VALIDATED.

  P1 syntax                  pydantic parse of BuildPlan (closed step types, semantic ports)
  P2 reference resolution    every input Ref resolves in the artifact registry
  P3 artifact identity       every resolved Ref carries the registry's current digest (no bare aliases)
  P4 graph structure         unique step ids, dependencies exist, no cycles, no orphan outputs feeding nothing (warning)
  P5 type compatibility      output ports consumed by inputs agree on semantic type, unit, currency, tz, scope
  P6 capability availability required capabilities exist for the tenant account at >= min_capability_level
  P7 authorization/data flow purposes in active grants, processors/destinations/effect classes inside envelope
  P8 cost/resource bounds    sum of worst-case step budgets <= plan budget <= envelope build cap; attempts/timeouts present
  P9 effect/compensation     external effects declare compensation class; irreversible effects require case approval obligation
  P10 verifier coverage      every release-artifact step carries a verification obligation on a non-training data role
  P11 release compatibility  release schema version supported; case migration declared when version changes
  P12 bounded loops          agent_loop steps carry max_iterations and timeout (also enforced by schema)

What is NOT verified here: the semantic correctness or safety of generated code. That is the Verifier's job
with protected acceptance tests (spec/authority-and-verification.md).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1] / "contracts" / "canonical-models"))
from plumb_contracts.enums import IMPACT_ORDER, VERIFICATION_ORDER, CompensationClass, DataRole, EffectClass, StepType, VerificationLevel  # noqa: E402
from plumb_contracts.models import AutonomyEnvelope, BuildPlan, Port  # noqa: E402


@dataclass
class ValidationIssue:
    code: str
    path: str
    message: str
    severity: str = "error"  # error | warning


@dataclass
class ValidationContext:
    tenant_id: str
    envelope: AutonomyEnvelope
    grants: dict[str, dict[str, Any]]  # grant_id -> {"status": "active", "purposes": [...], "processors_allowed": [...]}
    artifacts: dict[str, dict[str, Any]]  # artifact_id -> {"tenant_id":..., "digest": "sha256:..."}
    capabilities: dict[str, dict[str, Any]]  # operation_id -> {"account_ref":..., "verification_level": ..., "tenant_id": ...}
    supported_release_schema_versions: set[str] = field(default_factory=lambda: {"1.0"})
    current_release_schema_version: str = "1.0"
    approval_obligations: set[str] = field(default_factory=set)  # step ids that will have case-approval obligations


@dataclass
class ValidationReport:
    issues: list[ValidationIssue]

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def codes(self) -> set[str]:
        return {i.code for i in self.errors}


def _level_at_least(have: VerificationLevel, need: VerificationLevel) -> bool:
    return VERIFICATION_ORDER.index(have) >= VERIFICATION_ORDER.index(need)


def _ports_compatible(out: Port, inp: Port) -> list[str]:
    problems = []
    if out.semantic_type != inp.semantic_type:
        problems.append(f"semantic type {out.semantic_type} -> {inp.semantic_type}")
    for attr in ("unit", "currency", "tz", "scope"):
        a, b = getattr(out, attr), getattr(inp, attr)
        if a != b and not (a is None and b is None):
            problems.append(f"{attr} {a!r} -> {b!r}")
    if out.nullable and not inp.nullable:
        problems.append("nullable output feeds non-nullable input")
    if inp.freshness_max_s is not None and out.freshness_max_s is not None and out.freshness_max_s > inp.freshness_max_s:
        problems.append("output freshness looser than input requires")
    return problems


def validate_plan(raw_plan: dict[str, Any], ctx: ValidationContext) -> ValidationReport:
    issues: list[ValidationIssue] = []

    # P1 syntax
    try:
        plan = BuildPlan.model_validate(raw_plan)
    except PydanticValidationError as e:
        for err in e.errors():
            issues.append(ValidationIssue("E_SYNTAX", ".".join(str(p) for p in err["loc"]), err["msg"]))
        return ValidationReport(issues)

    if plan.tenant_id != ctx.tenant_id:
        issues.append(ValidationIssue("E_TENANT_MISMATCH", "tenant_id", "plan tenant differs from authenticated tenant"))

    step_index = {s.step_id: s for s in plan.steps}
    if len(step_index) != len(plan.steps):
        issues.append(ValidationIssue("E_GRAPH_DUPLICATE_ID", "steps", "duplicate step ids"))

    # P2 + P3 reference resolution and artifact identity (also envelope/solution refs)
    for ref_name, ref in (("solution_ref", plan.solution_ref), ("envelope_ref", plan.envelope_ref)):
        art = ctx.artifacts.get(ref.id)
        if art is None:
            issues.append(ValidationIssue("E_REF_UNRESOLVED", ref_name, f"{ref.id} not found"))
        else:
            if art.get("tenant_id") != ctx.tenant_id:
                issues.append(ValidationIssue("E_AUTHZ_CROSS_TENANT", ref_name, f"{ref.id} belongs to another tenant"))
            if ref.digest is None or ref.digest != art.get("digest"):
                issues.append(ValidationIssue("E_ARTIFACT_IDENTITY", ref_name, f"{ref.id} digest missing or stale"))
    for s in plan.steps:
        for i, ref in enumerate(s.inputs):
            art = ctx.artifacts.get(ref.id)
            path = f"steps.{s.step_id}.inputs[{i}]"
            if art is None:
                issues.append(ValidationIssue("E_REF_UNRESOLVED", path, f"{ref.id} not found"))
                continue
            if art.get("tenant_id") != ctx.tenant_id:
                issues.append(ValidationIssue("E_AUTHZ_CROSS_TENANT", path, f"{ref.id} belongs to another tenant"))
            if ref.digest is None:
                issues.append(ValidationIssue("E_ARTIFACT_IDENTITY", path, f"{ref.id} referenced without digest (alias not resolved)"))
            elif ref.digest != art.get("digest"):
                issues.append(ValidationIssue("E_ARTIFACT_IDENTITY", path, f"{ref.id} digest {ref.digest[:16]} is stale"))

    # P4 graph structure
    for s in plan.steps:
        for d in s.depends_on:
            if d not in step_index:
                issues.append(ValidationIssue("E_GRAPH_DANGLING", f"steps.{s.step_id}.depends_on", f"unknown dependency {d}"))
            if d == s.step_id:
                issues.append(ValidationIssue("E_GRAPH_CYCLE", f"steps.{s.step_id}", "step depends on itself"))
    # cycle detection (Kahn)
    indeg = {sid: 0 for sid in step_index}
    for s in plan.steps:
        for d in s.depends_on:
            if d in step_index and d != s.step_id:
                indeg[s.step_id] += 1
    queue = [sid for sid, n in indeg.items() if n == 0]
    seen = 0
    while queue:
        cur = queue.pop()
        seen += 1
        for s in plan.steps:
            if cur in s.depends_on:
                indeg[s.step_id] -= 1
                if indeg[s.step_id] == 0:
                    queue.append(s.step_id)
    if seen != len(step_index):
        issues.append(ValidationIssue("E_GRAPH_CYCLE", "steps", "dependency graph contains a cycle"))

    # P5 type compatibility: an input port named X is matched to the output port named X of the nearest
    # transitive dependency that produces it (ports flow along build edges)
    def ancestors(sid: str) -> list[str]:
        out, frontier, seen = [], list(step_index[sid].depends_on), set()
        while frontier:
            cur = frontier.pop(0)
            if cur in seen or cur not in step_index:
                continue
            seen.add(cur)
            out.append(cur)
            frontier.extend(step_index[cur].depends_on)
        return out

    for s in plan.steps:
        for inp in s.input_ports:
            producers = []
            for d in ancestors(s.step_id):
                found = [p for p in step_index[d].output_ports if p.name == inp.name]
                if found:
                    producers = [(d, p) for p in found]
                    break
            if not producers and inp.name not in {r.id for r in s.inputs}:
                issues.append(ValidationIssue("E_TYPE_UNSOURCED", f"steps.{s.step_id}.input_ports.{inp.name}", "no dependency produces this port"))
            for d, out in producers:
                for problem in _ports_compatible(out, inp):
                    issues.append(ValidationIssue("E_TYPE_MISMATCH", f"steps.{s.step_id}.input_ports.{inp.name}", f"from {d}: {problem}"))

    # P6 capability availability
    for s in plan.steps:
        for cap in s.required_capabilities:
            rec = ctx.capabilities.get(cap)
            path = f"steps.{s.step_id}.required_capabilities"
            if rec is None or rec.get("tenant_id") != ctx.tenant_id:
                issues.append(ValidationIssue("E_CAPABILITY_UNAVAILABLE", path, f"{cap} not verified for this tenant"))
                continue
            have = VerificationLevel(rec["verification_level"])
            if not _level_at_least(have, s.min_capability_level):
                issues.append(ValidationIssue("E_CAPABILITY_UNAVAILABLE", path, f"{cap} verified at {have.value}, step needs {s.min_capability_level.value}"))

    # P7 authorization and data flow
    env = ctx.envelope
    if env.tenant_id != ctx.tenant_id or env.status != "active":
        issues.append(ValidationIssue("E_AUTHZ_ENVELOPE", "envelope_ref", "envelope inactive or foreign"))
    active_grants = {gid: g for gid, g in ctx.grants.items() if g.get("status") == "active" and gid in set(env.source_grant_ids)}
    granted_purposes = {p for g in active_grants.values() for p in g.get("purposes", [])}
    for s in plan.steps:
        base = f"steps.{s.step_id}"
        for p in s.purposes_used:
            if p.value not in granted_purposes:
                issues.append(ValidationIssue("E_AUTHZ_PURPOSE", base + ".purposes_used", f"purpose {p.value} not granted by any active source grant in the envelope"))
        for proc in s.processors_used:
            if proc not in set(env.processors_allowed):
                issues.append(ValidationIssue("E_AUTHZ_PROCESSOR", base + ".processors_used", f"processor {proc} outside envelope"))
            for gid, g in active_grants.items():
                allowed = g.get("processors_allowed")
                if allowed and proc not in allowed and any(p.value in g.get("purposes", []) for p in s.purposes_used):
                    issues.append(ValidationIssue("E_AUTHZ_PROCESSOR", base + ".processors_used", f"processor {proc} not permitted by grant {gid}"))
        for dest in s.destinations:
            if not any(dest == d or dest.startswith(d.rstrip("*")) for d in env.destinations_allowed):
                issues.append(ValidationIssue("E_AUTHZ_DESTINATION", base + ".destinations", f"destination {dest} outside envelope"))
        if s.effect_class != EffectClass.NONE and s.effect_class not in set(env.effect_classes_allowed):
            issues.append(ValidationIssue("E_AUTHZ_EFFECT_CLASS", base + ".effect_class", f"effect class {s.effect_class.value} outside envelope"))

    # P8 cost and resource bounds
    total = sum(s.budget_max.minor_units for s in plan.steps)
    currencies = {s.budget_max.currency for s in plan.steps} | {plan.total_budget_max.currency, env.spend.build_max.currency}
    if len(currencies) != 1:
        issues.append(ValidationIssue("E_BUDGET_CURRENCY", "total_budget_max", f"mixed currencies {sorted(currencies)}"))
    else:
        if total > plan.total_budget_max.minor_units:
            issues.append(ValidationIssue("E_BUDGET_EXCEEDED", "total_budget_max", f"sum of step worst-case budgets {total} exceeds plan budget {plan.total_budget_max.minor_units}"))
        if plan.total_budget_max.minor_units > env.spend.build_max.minor_units:
            issues.append(ValidationIssue("E_BUDGET_EXCEEDED", "total_budget_max", "plan budget exceeds envelope build cap"))

    # P9 effect and compensation rules
    for s in plan.steps:
        base = f"steps.{s.step_id}"
        if s.effect_class in (EffectClass.EXTERNAL_MESSAGE, EffectClass.EXTERNAL_RECORD_WRITE, EffectClass.EXTERNAL_PAYMENT, EffectClass.CONFIG_CHANGE, EffectClass.INFRA_CHANGE):
            if s.compensation_class == CompensationClass.NOT_NEEDED:
                issues.append(ValidationIssue("E_EFFECT_NO_COMPENSATION", base, "external effect declares no compensation class"))
            if s.compensation_class == CompensationClass.IRREVERSIBLE and s.step_id not in ctx.approval_obligations:
                issues.append(ValidationIssue("E_EFFECT_IRREVERSIBLE_UNAPPROVED", base, "irreversible effect without a case-approval obligation"))
        if s.effect_class == EffectClass.EXTERNAL_PAYMENT:
            issues.append(ValidationIssue("E_EFFECT_PAYMENT_IN_BUILD", base, "build steps may not perform payments; payments are runtime actions behind approval"))

    # P10 verifier coverage
    for s in plan.steps:
        if s.produces_release_artifact:
            if not s.verification:
                issues.append(ValidationIssue("E_VERIFIER_COVERAGE", f"steps.{s.step_id}", "release artifact without verification obligation"))
            elif all(v.data_role == DataRole.TRAINING for v in s.verification):
                issues.append(ValidationIssue("E_VERIFIER_COVERAGE", f"steps.{s.step_id}", "verification only on training data role"))

    # P11 release compatibility
    if plan.release_schema_version not in ctx.supported_release_schema_versions:
        issues.append(ValidationIssue("E_RELEASE_COMPAT", "release_schema_version", "unsupported release schema version"))
    if plan.release_schema_version != ctx.current_release_schema_version and not plan.case_migration_declared:
        issues.append(ValidationIssue("E_RELEASE_COMPAT", "case_migration_declared", "schema version changes without a declared case migration"))

    # P12 bounded loops (belt and braces; schema also enforces)
    for s in plan.steps:
        if s.type == StepType.AGENT_LOOP and (s.max_iterations is None or s.timeout_s <= 0):
            issues.append(ValidationIssue("E_UNBOUNDED_LOOP", f"steps.{s.step_id}", "agent loop without bounds"))

    # impact class of the plan vs envelope auto ceiling (warning: a release approval will be required)
    sol = ctx.artifacts.get(plan.solution_ref.id, {})
    impact = sol.get("impact_class")
    if impact and IMPACT_ORDER.index(impact) > IMPACT_ORDER.index(env.max_auto_impact):
        issues.append(ValidationIssue("W_RELEASE_APPROVAL_REQUIRED", "solution_ref", f"impact {impact.value} above envelope auto ceiling; activation needs an approval", severity="warning"))

    return ValidationReport(issues)
