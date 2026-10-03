"""Behavioural tests for the three reference-scenario fixtures (specification section 25, Appendix B).

The fixtures under ``fixtures/envelopes/`` and ``fixtures/plans/`` are synthetic
build plans for accounting evidence preparation, industrial RFQ preparation and
laundry route preparation. They exercise the same core contracts across three
different outcomes (representational reuse, PL-061) and each encodes its
production boundary as authority that is simply absent from the envelope plus a
``dependency.raise`` step recording the human decision that remains (PL-001).

Requirements exercised: PL-001, PL-004, PL-005, PL-008, PL-014, PL-015, PL-016,
PL-018, PL-020, PL-040, PL-043, PL-045, PL-053, PL-058, PL-061.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pytest

from plumb.checker.cli import EXIT_OK, main
from plumb.checker.findings import CheckReport, Severity
from plumb.checker.plan_checker import check_plan, required_maturity
from plumb.contracts.build_plan import (
    DEPENDENCY_RAISE_STEP_TYPE,
    STEP_TYPE_VOCABULARY,
    BuildPlan,
    BuildStep,
)
from plumb.contracts.common import (
    ArtifactKind,
    DataPurpose,
    EffectClass,
    ErrorClass,
    PrincipalType,
    VerificationLevel,
    compute_artifact_digest,
)
from plumb.contracts.envelope import AutonomyEnvelope
from plumb.registry.registry import CapabilityRegistry
from tests.conftest import FIXTURES_DIR, load_fixture

ACCOUNTING = "accounting_evidence_preparation"
RFQ = "industrial_rfq_preparation"
LAUNDRY = "laundry_route_preparation"
SCENARIOS = (ACCOUNTING, RFQ, LAUNDRY)

ACCT_LEDGER = "src-acct-bookkeeping-ledger"
ACCT_DOCS = "src-acct-document-store"
ACCT_MAIL = "src-acct-mailbox"

REGISTRY = CapabilityRegistry.default()
AFTER_EXPIRY = datetime(2027, 4, 1, tzinfo=timezone.utc)
DEPLOYMENT_ENVIRONMENTS = ["shadow", "canary", "production"]
BINDING_COMMITMENT_CLASSES = {EffectClass.FINANCIAL_COMMITMENT, EffectClass.EXTERNAL_WRITE_IRREVERSIBLE}
PHYSICAL_EXECUTION_FREE_CLASSES = {
    EffectClass.READ,
    EffectClass.INTERNAL_WRITE,
    EffectClass.EXTERNAL_WRITE_REVERSIBLE,
    EffectClass.INFRASTRUCTURE_CHANGE,
}
INTEGRATION_RANK = {
    VerificationLevel.SCHEMA_VALIDITY: 0,
    VerificationLevel.ARTIFACT_INTEGRITY: 1,
    VerificationLevel.INTEGRATION_BEHAVIOR: 2,
    VerificationLevel.BUSINESS_OUTCOME: 3,
    VerificationLevel.ECONOMIC_RESULT: 4,
}
PIPELINE_ORDER = (
    "inventory.probe",
    "source.profile",
    "integration.configure",
    "integration.contract_test",
    "collection.deploy_shadow",
    "collection.backfill",
    "collection.reconcile",
    "collection.enable_incremental",
    "dataset.discover_sources",
    "dataset.build",
    "dataset.label_audit",
    "evaluation.run",
    "workflow.compile",
    "workflow.test_bundle",
    "release.create",
    "release.activate_shadow",
    "verification.request",
    DEPENDENCY_RAISE_STEP_TYPE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_envelope(name: str) -> AutonomyEnvelope:
    return AutonomyEnvelope.model_validate(load_fixture(f"envelopes/{name}.json"))


def load_plan(name: str) -> BuildPlan:
    return BuildPlan.model_validate(load_fixture(f"plans/{name}.json"))


def check(name: str, now: datetime | None = None) -> CheckReport:
    return check_plan(load_plan(name), load_envelope(name), REGISTRY, now=now)


def steps_of_type(plan: BuildPlan, step_type: str) -> list[BuildStep]:
    return [step for step in plan.steps if step.step_type == step_type]


def the_step(plan: BuildPlan, step_type: str) -> BuildStep:
    matches = steps_of_type(plan, step_type)
    assert len(matches) == 1, f"expected exactly one {step_type} step, found {[s.step_id for s in matches]}"
    return matches[0]


def with_steps(plan: BuildPlan, steps: list[dict[str, Any]]) -> BuildPlan:
    """``plan`` with its steps replaced, re-validated through the contract."""
    return BuildPlan.model_validate({**plan.model_dump(mode="json"), "steps": steps})


def step_dicts(plan: BuildPlan) -> list[dict[str, Any]]:
    return [step.model_dump(mode="json") for step in plan.steps]


def effective_purposes(step: BuildStep) -> set[DataPurpose]:
    """Declared purposes plus those the bound capabilities require (what the checker enforces)."""
    purposes = set(step.purposes)
    for capability_id in step.required_capabilities:
        record = REGISTRY.get(capability_id)
        assert record is not None, capability_id
        purposes.update(record.required_purposes)
    return purposes


def position(order: list[str], plan: BuildPlan, step_type: str) -> int:
    return order.index(the_step(plan, step_type).step_id)


# ---------------------------------------------------------------------------
# Every scenario
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-005", "PL-014")
@pytest.mark.parametrize("name", SCENARIOS)
def test_fixture_parses_into_the_contracts_and_binds_plan_to_envelope(name: str) -> None:
    envelope = load_envelope(name)
    plan = load_plan(name)
    assert envelope.kind is ArtifactKind.AUTONOMY_ENVELOPE
    assert plan.kind is ArtifactKind.BUILD_PLAN
    assert envelope.owner.principal_type is PrincipalType.HUMAN_OWNER
    assert plan.producer.principal_type is PrincipalType.BUILD_AGENT
    assert plan.tenant_id == envelope.tenant_id
    assert (plan.envelope_id, plan.envelope_version) == (envelope.envelope_id, envelope.envelope_version)
    assert plan.goal_id in {goal.goal_id for goal in envelope.goals}
    assert envelope.deployment_environments == DEPLOYMENT_ENVIRONMENTS
    assert envelope.escalation_conditions, "an envelope must say when to escalate"
    assert envelope.is_active(plan.planned_at)
    assert len(envelope.source_grants) == 3
    assert all(grant.granted_by.principal_type is PrincipalType.HUMAN_OWNER for grant in envelope.source_grants)


@pytest.mark.requirements("PL-014", "PL-015", "PL-016")
@pytest.mark.parametrize("name", SCENARIOS)
def test_plan_passes_the_checker_with_zero_findings(name: str) -> None:
    plan = load_plan(name)
    report = check(name)
    assert report.ok, report.render()
    assert report.findings == [], report.render()
    assert report.summary["warnings"] == 0
    assert report.summary["codes"] == []
    order = report.topological_order
    assert order is not None
    assert sorted(order) == sorted(plan.step_ids)
    index = {step_id: position_ for position_, step_id in enumerate(order)}
    for step in plan.steps:
        for dependency in step.depends_on:
            assert index[dependency] < index[step.step_id], f"{dependency} must precede {step.step_id}"


@pytest.mark.requirements("PL-015")
@pytest.mark.parametrize("name", SCENARIOS)
def test_cli_reports_ok_for_the_fixture(name: str, capsys: pytest.CaptureFixture[str]) -> None:
    plan_path = FIXTURES_DIR / "plans" / f"{name}.json"
    envelope_path = FIXTURES_DIR / "envelopes" / f"{name}.json"
    assert main(["plan", str(plan_path), str(envelope_path), "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["findings"] == []
    assert len(payload["topological_order"]) == len(load_plan(name).steps)


@pytest.mark.requirements("PL-008", "PL-014")
@pytest.mark.parametrize("name", SCENARIOS)
def test_steps_are_bound_to_registered_capabilities_of_sufficient_maturity(name: str) -> None:
    plan = load_plan(name)
    assert 14 <= len(plan.steps) <= 22
    assert len(set(plan.step_ids)) == len(plan.steps)
    for step in plan.steps:
        assert REGISTRY.step_type_known(step.step_type), step.step_type
        assert step.required_capabilities, f"{step.step_id} binds no capability"
        for capability_id in step.required_capabilities:
            record = REGISTRY.get(capability_id)
            assert record is not None, capability_id
            assert record.step_type == step.step_type
            assert record.at_least(required_maturity(step)), (step.step_id, record.maturity)
            assert step.effect_class in record.effect_classes
            for output in step.outputs:
                assert output.kind in record.produces, (step.step_id, output.name, capability_id)


@pytest.mark.requirements("PL-015", "PL-016")
@pytest.mark.parametrize("name", SCENARIOS)
def test_inputs_resolve_to_verified_prerequisites_and_pinned_plan_inputs(name: str) -> None:
    envelope = load_envelope(name)
    plan = load_plan(name)
    by_id = {step.step_id: step for step in plan.steps}
    for step in plan.steps:
        for item in step.inputs:
            if item.from_step is not None:
                assert item.from_step in step.depends_on, (step.step_id, item.name)
                output = by_id[item.from_step].output_named(item.name)
                assert output is not None and output.kind == item.kind, (step.step_id, item.name)
            else:
                ref = plan.plan_input_named(item.plan_input or "")
                assert ref is not None and ref.kind == item.kind, (step.step_id, item.name)
    envelope_ref = plan.plan_input_named(envelope.envelope_id)
    assert envelope_ref is not None and envelope_ref.kind is ArtifactKind.AUTONOMY_ENVELOPE
    assert envelope_ref.digest == envelope.content_digest == compute_artifact_digest(envelope)
    assert plan.content_digest == compute_artifact_digest(plan)
    assert plan.opportunity_ref is not None and plan.plan_input_named(plan.opportunity_ref.artifact_id) is not None


@pytest.mark.requirements("PL-018", "PL-058")
@pytest.mark.parametrize("name", SCENARIOS)
def test_budgets_nest_inside_the_envelope_spending_limit(name: str) -> None:
    envelope = load_envelope(name)
    plan = load_plan(name)
    currency = plan.total_budget.spend.currency
    assert envelope.spending_limit.currency == currency
    step_total = plan.worst_case_step_spend()
    assert 0 < step_total.minor_units <= plan.total_budget.spend.minor_units <= envelope.spending_limit.minor_units
    for step in plan.steps:
        assert step.budget.spend.currency == currency
        assert 1 <= step.budget.max_attempts <= envelope.per_step_attempt_limit
        assert step.budget.max_elapsed_seconds >= 1


@pytest.mark.requirements("PL-016", "PL-043", "PL-045")
@pytest.mark.parametrize("name", SCENARIOS)
def test_verification_obligations_match_each_step_effect(name: str) -> None:
    plan = load_plan(name)
    for step in plan.steps:
        levels = {obligation.level for obligation in step.verification}
        if step.step_type == DEPENDENCY_RAISE_STEP_TYPE:
            assert levels == set()
            continue
        assert levels, f"{step.step_id} declares no verification obligation"
        if step.has_external_effect:
            assert max(INTEGRATION_RANK[level] for level in levels) >= INTEGRATION_RANK[VerificationLevel.INTEGRATION_BEHAVIOR]
        if step.step_type.startswith("release."):
            assert VerificationLevel.BUSINESS_OUTCOME in levels
    apply = the_step(plan, "infrastructure.apply")
    preview = the_step(plan, "infrastructure.preview")
    assert preview.step_id in apply.depends_on, "a preview must precede application (PL-045)"
    assert {item.kind for item in apply.inputs} >= {ArtifactKind.INFRASTRUCTURE_PREVIEW, ArtifactKind.APPROVAL_RECORD}


@pytest.mark.requirements("PL-005")
@pytest.mark.parametrize("name", SCENARIOS)
def test_deployment_steps_declare_an_allowed_environment_and_stay_in_scope(name: str) -> None:
    envelope = load_envelope(name)
    plan = load_plan(name)
    outer = envelope.scope(now=plan.planned_at)
    for step in plan.steps:
        assert step.scope.is_within(outer) == [], step.step_id
        assert step.effect_class in envelope.allowed_effect_classes, step.step_id
        if step.step_type.startswith(("infrastructure.", "release.")):
            assert step.environment in envelope.deployment_environments, step.step_id
        elif step.environment is not None:
            assert step.environment in envelope.deployment_environments, step.step_id
    assert the_step(plan, "infrastructure.apply").environment == "production"
    assert the_step(plan, "release.activate_shadow").environment == "shadow"


@pytest.mark.requirements("PL-053")
@pytest.mark.parametrize("name", SCENARIOS)
def test_every_purpose_is_granted_per_source(name: str) -> None:
    envelope = load_envelope(name)
    plan = load_plan(name)
    for step in plan.steps:
        if not step.scope.source_ids:
            continue
        assert step.purposes, f"{step.step_id} touches sources but declares no purpose"
        for source_id in step.scope.source_ids:
            granted = envelope.purposes_for(source_id, now=plan.planned_at)
            assert effective_purposes(step) <= granted, (step.step_id, source_id)
    train_steps = steps_of_type(plan, "training.submit")
    for step in train_steps:
        for source_id in step.scope.source_ids:
            assert DataPurpose.TRAIN in envelope.purposes_for(source_id, now=plan.planned_at)


@pytest.mark.requirements("PL-001")
@pytest.mark.parametrize("name", SCENARIOS)
def test_production_boundary_is_recorded_as_a_resumable_dependency(name: str) -> None:
    plan = load_plan(name)
    boundary = the_step(plan, DEPENDENCY_RAISE_STEP_TYPE)
    assert boundary.verification == []
    assert boundary.effect_class is EffectClass.INTERNAL_WRITE
    assert [output.kind for output in boundary.outputs] == [ArtifactKind.DEPENDENCY_RECORD]
    assert boundary.depends_on, "the boundary is raised after the verified work it blocks"
    assert all(boundary.step_id not in step.depends_on for step in plan.steps)
    assert "ready for" in boundary.description.lower(), "the dependency must say how completion is reported"


@pytest.mark.requirements("PL-014", "PL-016", "PL-020", "PL-045")
@pytest.mark.parametrize("name", SCENARIOS)
def test_pipeline_follows_the_section_25_order(name: str) -> None:
    plan = load_plan(name)
    order = check(name).topological_order
    assert order is not None
    positions = [position(order, plan, step_type) for step_type in PIPELINE_ORDER]
    assert positions == sorted(positions), list(zip(PIPELINE_ORDER, positions))
    assert position(order, plan, "infrastructure.preview") < position(order, plan, "infrastructure.apply") < position(order, plan, "release.create")
    assert order[-1] == the_step(plan, DEPENDENCY_RAISE_STEP_TYPE).step_id


@pytest.mark.requirements("PL-005", "PL-040")
@pytest.mark.parametrize("name", SCENARIOS)
def test_envelope_authority_expires_in_2027(name: str) -> None:
    envelope = load_envelope(name)
    assert envelope.expires_at.year == 2027
    assert all(grant.expires_at is not None and grant.expires_at.year == 2027 for grant in envelope.source_grants)
    report = check(name, now=AFTER_EXPIRY)
    assert not report.ok
    assert {finding.code for finding in report.errors} >= {"ENVELOPE_INACTIVE"}


# ---------------------------------------------------------------------------
# Scenario-specific production boundaries
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-005", "PL-061")
def test_accounting_envelope_excludes_posting_but_allows_consolidated_reminders() -> None:
    envelope = load_envelope(ACCOUNTING)
    plan = load_plan(ACCOUNTING)
    allowed = set(envelope.allowed_effect_classes)
    assert EffectClass.FINANCIAL_COMMITMENT not in allowed
    assert EffectClass.EXTERNAL_WRITE_IRREVERSIBLE not in allowed
    assert EffectClass.DESTRUCTIVE not in allowed
    assert EffectClass.EXTERNAL_COMMUNICATION in allowed
    assert all(step.effect_class is not EffectClass.FINANCIAL_COMMITMENT for step in plan.steps)
    canary = the_step(plan, "release.canary")
    assert canary.effect_class is EffectClass.EXTERNAL_COMMUNICATION
    assert "reminder" in canary.description.lower()
    assert any("journal" in condition.lower() for condition in envelope.escalation_conditions)


@pytest.mark.requirements("PL-053")
def test_accounting_mailbox_grant_carries_no_training_right_and_no_step_trains_on_mail() -> None:
    envelope = load_envelope(ACCOUNTING)
    plan = load_plan(ACCOUNTING)
    mailbox_grants = [grant for grant in envelope.source_grants if grant.source_id == ACCT_MAIL]
    assert len(mailbox_grants) == 1
    assert set(mailbox_grants[0].purposes) == {DataPurpose.INSPECT, DataPurpose.COLLECT}
    assert DataPurpose.TRAIN not in envelope.purposes_for(ACCT_MAIL, now=plan.planned_at)
    assert DataPurpose.TRAIN not in envelope.purposes_for(ACCT_DOCS, now=plan.planned_at)
    assert DataPurpose.TRAIN in envelope.purposes_for(ACCT_LEDGER, now=plan.planned_at)
    for step in plan.steps:
        if ACCT_MAIL in step.scope.source_ids:
            assert effective_purposes(step) <= {DataPurpose.INSPECT, DataPurpose.COLLECT}, step.step_id
    training = the_step(plan, "training.submit")
    assert training.scope.source_ids == [ACCT_LEDGER]
    assert DataPurpose.TRAIN in training.purposes
    assert all(ACCT_MAIL not in step.scope.source_ids for step in plan.steps if DataPurpose.TRAIN in effective_purposes(step))


@pytest.mark.requirements("PL-001", "PL-061")
def test_accounting_dependency_names_the_accountant_approval() -> None:
    boundary = the_step(load_plan(ACCOUNTING), DEPENDENCY_RAISE_STEP_TYPE)
    text = boundary.description.lower()
    assert "accountant approval" in text
    assert "journal" in text and "financial_commitment" in text
    assert "training rights" in text


@pytest.mark.requirements("PL-005", "PL-053", "PL-001")
def test_rfq_envelope_and_plan_never_produce_a_binding_quote() -> None:
    envelope = load_envelope(RFQ)
    plan = load_plan(RFQ)
    assert BINDING_COMMITMENT_CLASSES.isdisjoint(envelope.allowed_effect_classes)
    assert all(step.effect_class not in BINDING_COMMITMENT_CLASSES for step in plan.steps)
    assert steps_of_type(plan, "training.submit") == []
    assert all(DataPurpose.TRAIN not in grant.purposes for grant in envelope.source_grants)
    canary = the_step(plan, "release.canary")
    assert canary.effect_class is EffectClass.EXTERNAL_WRITE_REVERSIBLE
    boundary = the_step(plan, DEPENDENCY_RAISE_STEP_TYPE)
    text = boundary.description.lower()
    assert "binding quote" in text and "commercial terms" in text and "freshness" in text


@pytest.mark.requirements("PL-005", "PL-001")
def test_laundry_envelope_excludes_physical_execution_and_the_plan_stops_at_shadow() -> None:
    envelope = load_envelope(LAUNDRY)
    plan = load_plan(LAUNDRY)
    assert set(envelope.allowed_effect_classes) <= PHYSICAL_EXECUTION_FREE_CLASSES
    assert EffectClass.EXTERNAL_WRITE_REVERSIBLE in envelope.allowed_effect_classes
    assert all(step.effect_class in PHYSICAL_EXECUTION_FREE_CLASSES for step in plan.steps)
    assert steps_of_type(plan, "release.canary") == []
    assert steps_of_type(plan, "training.submit") == []
    boundary = the_step(plan, DEPENDENCY_RAISE_STEP_TYPE)
    text = boundary.description.lower()
    assert "physical execution" in text and "route publication" in text
    assert "dispatcher" in text


# ---------------------------------------------------------------------------
# Negative: the boundaries are enforced, not merely described
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-005", "PL-015")
def test_injected_journal_posting_step_is_rejected_as_effect_class_denied() -> None:
    plan = load_plan(ACCOUNTING)
    envelope = load_envelope(ACCOUNTING)
    assert check_plan(plan, envelope, REGISTRY).ok
    shadow = the_step(plan, "release.activate_shadow")
    posting = {
        **the_step(plan, "release.canary").model_dump(mode="json"),
        "step_id": "post-journal-entries",
        "description": "Post the categorized journal entries to the ledger for the canary client-periods.",
        "depends_on": [shadow.step_id],
        "inputs": [{"name": "shadow-release-manifest", "kind": "ReleaseManifest", "from_step": shadow.step_id}],
        "outputs": [{"name": "posting-canary-report", "kind": "CanaryReport"}],
        "effect_class": EffectClass.FINANCIAL_COMMITMENT.value,
        "budget": {"spend": {"minor_units": 5000, "currency": "EUR"}, "max_attempts": 1, "max_elapsed_seconds": 3600},
    }
    mutated = with_steps(plan, [*step_dicts(plan), posting])

    report = check_plan(mutated, envelope, REGISTRY)

    assert not report.ok
    denied = [finding for finding in report.findings if finding.code == "EFFECT_CLASS_DENIED"]
    assert denied and all(finding.step_id == "post-journal-entries" for finding in denied)
    assert all(finding.error_class is ErrorClass.SCOPE_DENIED for finding in denied)
    assert any(finding.severity is Severity.ERROR and "not allowed by the envelope" in finding.message for finding in denied)
    assert {finding.code for finding in report.errors} == {"EFFECT_CLASS_DENIED"}
    assert all(finding.step_id == "post-journal-entries" for finding in report.findings)


@pytest.mark.requirements("PL-053")
@pytest.mark.parametrize(
    ("step_type", "source_id"),
    [
        ("dataset.build", ACCT_MAIL),
        ("dataset.build", ACCT_DOCS),
        ("training.submit", ACCT_MAIL),
    ],
)
def test_train_purpose_on_a_source_without_training_rights_is_purpose_denied(step_type: str, source_id: str) -> None:
    plan = load_plan(ACCOUNTING)
    envelope = load_envelope(ACCOUNTING)
    target = the_step(plan, step_type)
    steps = step_dicts(plan)
    for item in steps:
        if item["step_id"] == target.step_id:
            item["scope"]["source_ids"] = [ACCT_LEDGER, source_id]
            item["purposes"] = sorted({*item["purposes"], DataPurpose.TRAIN.value})
    mutated = with_steps(plan, steps)

    report = check_plan(mutated, envelope, REGISTRY)

    assert not report.ok
    denied = [finding for finding in report.findings if finding.code == "PURPOSE_DENIED"]
    assert [finding.step_id for finding in denied] == [target.step_id]
    finding = denied[0]
    assert finding.error_class is ErrorClass.PURPOSE_DENIED
    assert finding.details["source_id"] == source_id
    assert "TRAIN" in finding.details["missing"]
    assert "never inferred from permission to inspect or collect" in finding.message
    assert {finding.code for finding in report.errors} == {"PURPOSE_DENIED"}, report.render()


@pytest.mark.requirements("PL-053")
def test_train_purpose_on_the_ledger_alone_is_granted() -> None:
    plan = load_plan(ACCOUNTING)
    steps = step_dicts(plan)
    target = the_step(plan, "dataset.build")
    for item in steps:
        if item["step_id"] == target.step_id:
            assert item["scope"]["source_ids"] == [ACCT_LEDGER]
            item["purposes"] = sorted({*item["purposes"], DataPurpose.TRAIN.value})
    report = check_plan(with_steps(plan, steps), load_envelope(ACCOUNTING), REGISTRY)
    assert report.ok, report.render()
    assert report.findings == []


# ---------------------------------------------------------------------------
# Representational reuse and isolation across the three scenarios
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-061", "PL-014")
def test_the_three_scenarios_share_one_step_type_vocabulary() -> None:
    vocabularies = {name: {step.step_type for step in load_plan(name).steps} for name in SCENARIOS}
    common = set.intersection(*vocabularies.values())
    assert len(common) >= 12, sorted(common)
    assert set(PIPELINE_ORDER) <= common
    union = set.union(*vocabularies.values())
    assert union == STEP_TYPE_VOCABULARY == REGISTRY.step_types()
    assert "training.submit" in vocabularies[ACCOUNTING]
    assert "training.submit" not in vocabularies[RFQ] | vocabularies[LAUNDRY]
    assert "release.canary" in vocabularies[ACCOUNTING] & vocabularies[RFQ]
    assert "release.canary" not in vocabularies[LAUNDRY]


@pytest.mark.requirements("PL-004", "PL-005")
def test_scenarios_are_distinct_tenants_and_a_plan_is_refused_against_another_envelope() -> None:
    envelopes = {name: load_envelope(name) for name in SCENARIOS}
    plans = {name: load_plan(name) for name in SCENARIOS}
    assert len({envelope.tenant_id for envelope in envelopes.values()}) == 3
    assert len({envelope.envelope_id for envelope in envelopes.values()}) == 3
    assert len({plan.plan_id for plan in plans.values()}) == 3
    assert len({envelope.spending_limit.currency for envelope in envelopes.values()}) == 3
    report = check_plan(plans[ACCOUNTING], envelopes[RFQ], REGISTRY)
    assert not report.ok
    assert {"TENANT_MISMATCH", "ENVELOPE_MISMATCH"} <= {finding.code for finding in report.errors}
