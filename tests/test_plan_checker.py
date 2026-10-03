"""Behavioural tests for ``plumb.checker.plan_checker`` and ``plumb.checker.cli``.

A synthetic four-step baseline plan (probe, profile, configure an integration,
build a dataset) passes against a baseline envelope. Every finding code is then
provoked twice: by a targeted mutation here and by one of the data-driven
fixtures under ``fixtures/invalid/`` (which were derived from these builders).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from plumb.checker.cli import EXIT_FINDINGS, EXIT_OK, EXIT_USAGE, main
from plumb.checker.findings import CheckReport, Finding, Severity
from plumb.checker.plan_checker import (
    CHECKER_NAME,
    FINDING_ERROR_CLASSES,
    check_plan,
    evaluation_instant,
    required_maturity,
)
from plumb.contracts.build_plan import BuildPlan, BuildStep, StepInput, StepOutput, VerificationObligation
from plumb.contracts.capability import EVIDENCE_BACKED_MATURITIES, PLATFORM_TENANT_ID, CapabilityRecord, MaintenanceBurden
from plumb.contracts.common import (
    ArtifactKind,
    ArtifactRef,
    Budget,
    CapabilityMaturity,
    DataPurpose,
    EffectClass,
    ErrorClass,
    Money,
    Principal,
    PrincipalType,
    ResourceScope,
    VerificationLevel,
    compute_artifact_digest,
)
from plumb.contracts.envelope import AutonomyEnvelope, Goal, SourceGrant
from plumb.registry.registry import CapabilityRegistry
from tests.conftest import FIXTURES_DIR, REPO_ROOT, load_fixture

UTC = timezone.utc
T0 = datetime(2026, 10, 1, tzinfo=UTC)
PLANNED_AT = datetime(2026, 10, 2, tzinfo=UTC)
EXPIRES_AT = datetime(2027, 1, 1, tzinfo=UTC)
DAY = timedelta(days=1)

TENANT = "tnt_fixture01"
ENVELOPE_ID = "env-fixture-baseline"
PLAN_ID = "plan-fixture-baseline"
LEDGER = "src-ledger"
MAILBOX = "src-mailbox"
DESTINATION = "dst-tenant-storage"
PROCESSOR = "proc-plumb-eu"
REGION = "eu-west-1"
ENVIRONMENT = "staging"
DIGEST = "sha256:" + "ab" * 32
APPROVAL_ID = "apr-fixture-implement-operate"

INVALID_FIXTURE_PATHS = sorted((FIXTURES_DIR / "invalid").glob("*.json"))


# ---------------------------------------------------------------------------
# Synthetic builders (the fixture generator derives fixtures/invalid/*.json from these)
# ---------------------------------------------------------------------------


def principal(principal_id: str = "owner-01", principal_type: PrincipalType = PrincipalType.HUMAN_OWNER) -> Principal:
    return Principal(principal_id=principal_id, principal_type=principal_type, authenticated_via="oidc:test-issuer")


def grant(source_id: str, purposes: list[DataPurpose], **overrides: Any) -> SourceGrant:
    data: dict[str, Any] = {
        "source_id": source_id,
        "purposes": purposes,
        "granted_by": principal(),
        "granted_at": T0 - DAY,
        "expires_at": None,
        "policy_version": "1.0.0",
    }
    data.update(overrides)
    return SourceGrant(**data)


def baseline_grants() -> list[SourceGrant]:
    return [
        grant(LEDGER, [DataPurpose.INSPECT, DataPurpose.COLLECT, DataPurpose.TRANSFORM]),
        grant(MAILBOX, [DataPurpose.INSPECT]),
    ]


def envelope(**overrides: Any) -> AutonomyEnvelope:
    data: dict[str, Any] = {
        "artifact_id": ENVELOPE_ID,
        "tenant_id": TENANT,
        "version": 1,
        "producer": principal(),
        "created_at": T0,
        "envelope_id": ENVELOPE_ID,
        "envelope_version": 1,
        "owner": principal(),
        "goals": [Goal(goal_id="goal-fewer-evidence-requests", objective="Reduce duplicated evidence requests.")],
        "source_grants": baseline_grants(),
        "approved_destinations": [DESTINATION],
        "approved_processors": [PROCESSOR],
        "allowed_effect_classes": [EffectClass.READ, EffectClass.INTERNAL_WRITE, EffectClass.EXTERNAL_WRITE_REVERSIBLE],
        "spending_limit": Money(minor_units=500_000, currency="USD"),
        "per_step_attempt_limit": 3,
        "deployment_environments": [ENVIRONMENT],
        "allowed_regions": [REGION],
        "expires_at": EXPIRES_AT,
        "escalation_conditions": ["a new processor is requested"],
        "policy_version": "1.0.0",
        "revoked_at": None,
    }
    data.update(overrides)
    return AutonomyEnvelope(**data)


def budget(minor_units: int = 10_000, currency: str = "USD", **overrides: Any) -> Budget:
    data: dict[str, Any] = {
        "spend": Money(minor_units=minor_units, currency=currency),
        "max_attempts": 3,
        "max_elapsed_seconds": 3600,
    }
    data.update(overrides)
    return Budget(**data)


def obligation(level: VerificationLevel = VerificationLevel.ARTIFACT_INTEGRITY, check: str = "artifact_digest") -> VerificationObligation:
    return VerificationObligation(check=check, level=level, description=f"{check} confirmed by the verifier.")


def scope(sources: list[str] | None = None, processors: list[str] | None = None, **overrides: Any) -> ResourceScope:
    data: dict[str, Any] = {
        "source_ids": [LEDGER] if sources is None else sources,
        "destination_ids": [DESTINATION],
        "processor_ids": [] if processors is None else processors,
        "regions": [REGION],
    }
    data.update(overrides)
    return ResourceScope(**data)


def step(**overrides: Any) -> BuildStep:
    """The baseline probe step unless overridden."""
    data: dict[str, Any] = {
        "step_id": "probe-sources",
        "step_type": "inventory.probe",
        "description": "Probe the authorized ledger and mailbox accounts.",
        "depends_on": [],
        "inputs": [StepInput(name="envelope", kind=ArtifactKind.AUTONOMY_ENVELOPE, plan_input=ENVELOPE_ID)],
        "outputs": [StepOutput(name="inventory", kind=ArtifactKind.ENVIRONMENT_INVENTORY)],
        "required_capabilities": ["cap.inventory.probe.management-api"],
        "effect_class": EffectClass.READ,
        "purposes": [DataPurpose.INSPECT],
        "scope": scope(sources=[LEDGER, MAILBOX]),
        "budget": budget(),
        "verification": [obligation(check="probe_receipt")],
    }
    data.update(overrides)
    return BuildStep(**data)


def baseline_steps() -> list[BuildStep]:
    return [
        step(),
        step(
            step_id="profile-sources",
            step_type="source.profile",
            description="Profile the ledger schema and sample permitted records.",
            depends_on=["probe-sources"],
            inputs=[StepInput(name="inventory", kind=ArtifactKind.ENVIRONMENT_INVENTORY, from_step="probe-sources")],
            outputs=[StepOutput(name="profile", kind=ArtifactKind.QUALITY_REPORT)],
            required_capabilities=["cap.source.profile.sampler"],
            scope=scope(),
        ),
        step(
            step_id="configure-integration",
            step_type="integration.configure",
            description="Configure the managed ledger connection.",
            depends_on=["probe-sources"],
            inputs=[StepInput(name="inventory", kind=ArtifactKind.ENVIRONMENT_INVENTORY, from_step="probe-sources")],
            outputs=[StepOutput(name="integration", kind=ArtifactKind.INTEGRATION_SPEC)],
            required_capabilities=["cap.integration.configure.management-api"],
            effect_class=EffectClass.EXTERNAL_WRITE_REVERSIBLE,
            purposes=[DataPurpose.INSPECT, DataPurpose.COLLECT],
            scope=scope(processors=[PROCESSOR]),
            verification=[obligation(VerificationLevel.INTEGRATION_BEHAVIOR, "contract_tests")],
        ),
        step(
            step_id="build-dataset",
            step_type="dataset.build",
            description="Assemble the evidence dataset from collected ledger records.",
            depends_on=["profile-sources", "configure-integration"],
            inputs=[
                StepInput(name="profile", kind=ArtifactKind.QUALITY_REPORT, from_step="profile-sources"),
                StepInput(name="integration", kind=ArtifactKind.INTEGRATION_SPEC, from_step="configure-integration"),
            ],
            outputs=[StepOutput(name="dataset", kind=ArtifactKind.DATASET_MANIFEST)],
            required_capabilities=["cap.dataset.build.builder"],
            effect_class=EffectClass.INTERNAL_WRITE,
            purposes=[DataPurpose.COLLECT, DataPurpose.TRANSFORM],
            scope=scope(processors=[PROCESSOR]),
            verification=[obligation(check="dataset_counts")],
        ),
    ]


def train_step(**overrides: Any) -> BuildStep:
    data: dict[str, Any] = {
        "step_id": "train-model",
        "step_type": "training.submit",
        "description": "Submit a bounded fine-tuning job on the verified dataset.",
        "depends_on": ["build-dataset"],
        "inputs": [StepInput(name="dataset", kind=ArtifactKind.DATASET_MANIFEST, from_step="build-dataset")],
        "outputs": [StepOutput(name="model", kind=ArtifactKind.MODEL_VERSION)],
        "required_capabilities": ["cap.training.submit.managed-open-model"],
        "effect_class": EffectClass.INTERNAL_WRITE,
        "purposes": [DataPurpose.TRAIN],
        "scope": scope(processors=[PROCESSOR]),
        "verification": [obligation(check="model_version_recorded")],
    }
    data.update(overrides)
    return step(**data)


def release_step(**overrides: Any) -> BuildStep:
    data: dict[str, Any] = {
        "step_id": "create-release",
        "step_type": "release.create",
        "description": "Assemble the release manifest for the staging environment.",
        "depends_on": ["configure-integration"],
        "inputs": [StepInput(name="integration", kind=ArtifactKind.INTEGRATION_SPEC, from_step="configure-integration")],
        "outputs": [StepOutput(name="release", kind=ArtifactKind.RELEASE_MANIFEST)],
        "required_capabilities": ["cap.release.create.executor"],
        "effect_class": EffectClass.INTERNAL_WRITE,
        "purposes": [],
        "scope": scope(sources=[]),
        "verification": [obligation(check="manifest_digest"), obligation(VerificationLevel.BUSINESS_OUTCOME, "scenario_suite")],
        "environment": ENVIRONMENT,
    }
    data.update(overrides)
    return step(**data)


def preview_step(**overrides: Any) -> BuildStep:
    data: dict[str, Any] = {
        "step_id": "preview-infrastructure",
        "step_type": "infrastructure.preview",
        "description": "Preview the infrastructure change (plan/diff and cost estimate).",
        "depends_on": [],
        "inputs": [],
        "outputs": [StepOutput(name="preview", kind=ArtifactKind.INFRASTRUCTURE_PREVIEW)],
        "required_capabilities": ["cap.infrastructure.preview.automation-api"],
        "effect_class": EffectClass.READ,
        "purposes": [],
        "scope": scope(sources=[]),
        "verification": [obligation(check="preview_digest")],
        "environment": ENVIRONMENT,
    }
    data.update(overrides)
    return step(**data)


def apply_step(**overrides: Any) -> BuildStep:
    """An infrastructure.apply step that consumes the preview of ``preview_step()`` and the plan's approval (PL-045)."""
    data: dict[str, Any] = {
        "step_id": "apply-infrastructure",
        "step_type": "infrastructure.apply",
        "description": "Apply the previewed infrastructure change.",
        "depends_on": ["preview-infrastructure"],
        "inputs": [
            StepInput(name="preview", kind=ArtifactKind.INFRASTRUCTURE_PREVIEW, from_step="preview-infrastructure"),
            StepInput(name="approval", kind=ArtifactKind.APPROVAL_RECORD, plan_input=APPROVAL_ID),
        ],
        "outputs": [StepOutput(name="receipt", kind=ArtifactKind.VERIFICATION_RECEIPT)],
        "required_capabilities": ["cap.infrastructure.apply.automation-api"],
        "effect_class": EffectClass.INFRASTRUCTURE_CHANGE,
        "purposes": [],
        "scope": scope(sources=[]),
        "verification": [obligation(VerificationLevel.INTEGRATION_BEHAVIOR, "resource_state")],
        "environment": ENVIRONMENT,
    }
    data.update(overrides)
    return step(**data)


def plan(**overrides: Any) -> BuildPlan:
    data: dict[str, Any] = {
        "artifact_id": PLAN_ID,
        "tenant_id": TENANT,
        "version": 1,
        "producer": principal("planner-01", PrincipalType.BUILD_AGENT),
        "created_at": PLANNED_AT,
        "plan_id": PLAN_ID,
        "goal_id": "goal-fewer-evidence-requests",
        "opportunity_ref": None,
        "envelope_id": ENVELOPE_ID,
        "envelope_version": 1,
        "inputs": [
            ArtifactRef(artifact_id=ENVELOPE_ID, kind=ArtifactKind.AUTONOMY_ENVELOPE, digest=compute_artifact_digest(envelope())),
            ArtifactRef(artifact_id=APPROVAL_ID, kind=ArtifactKind.APPROVAL_RECORD, digest=DIGEST),
        ],
        "steps": baseline_steps(),
        "total_budget": budget(minor_units=100_000),
        "planned_at": PLANNED_AT,
    }
    data.update(overrides)
    return BuildPlan(**data)


def capability(
    capability_id: str,
    step_type: str,
    maturity: CapabilityMaturity,
    effect_classes: list[EffectClass],
    required_purposes: list[DataPurpose] | None = None,
) -> CapabilityRecord:
    data: dict[str, Any] = {
        "artifact_id": capability_id,
        "tenant_id": PLATFORM_TENANT_ID,
        "version": 1,
        "producer": principal("platform-registry", PrincipalType.SERVICE),
        "created_at": T0,
        "capability_id": capability_id,
        "step_type": step_type,
        "provider": "synthetic-provider",
        "operation": "synthetic.operation",
        "maturity": maturity,
        "effect_classes": effect_classes,
        "required_purposes": required_purposes or [],
        "maintenance_burden": MaintenanceBurden.LOW,
        "capability_version": "1.0.0",
    }
    if maturity in EVIDENCE_BACKED_MATURITIES:
        data["probe_receipt_ref"] = f"probe:platform/synthetic/{step_type}/2026-09-15"
        data["tested_environment"] = "sandbox:plumb-staging/2026-09"
    return CapabilityRecord(**data)


def registry_with(*records: CapabilityRecord) -> CapabilityRegistry:
    """The packaged registry extended with ``records``."""
    return CapabilityRegistry([*CapabilityRegistry.default().records(), *records])


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def modified(model: BuildStep, **overrides: Any) -> BuildStep:
    """``model`` with ``overrides`` applied and validators re-run."""
    return BuildStep.model_validate({**model.model_dump(), **overrides})


def replace(steps: list[BuildStep], step_id: str, **overrides: Any) -> list[BuildStep]:
    return [modified(item, **overrides) if item.step_id == step_id else item for item in steps]


def bypass(model: BaseModel, **overrides: Any) -> Any:
    """Rebuild ``model`` through ``model_construct`` so contract validators do not run."""
    fields = {name: getattr(model, name) for name in type(model).model_fields}
    fields.update(overrides)
    return type(model).model_construct(**fields)


def pinned_to(plan_: BuildPlan, envelope_: AutonomyEnvelope) -> BuildPlan:
    """``plan_`` with its envelope input re-pinned to ``envelope_``'s digest (as a planner compiling against it would)."""
    inputs = [
        ArtifactRef(artifact_id=ref.artifact_id, kind=ref.kind, digest=compute_artifact_digest(envelope_))
        if ref.artifact_id == envelope_.envelope_id and ref.kind is ArtifactKind.AUTONOMY_ENVELOPE
        else ref
        for ref in plan_.inputs
    ]
    return plan_.model_copy(update={"inputs": inputs})


def check(plan_: BuildPlan, envelope_: AutonomyEnvelope | None = None, *, repin: bool = True, **kwargs: Any) -> CheckReport:
    """Check ``plan_`` against ``envelope_`` (default: the baseline envelope).

    Most tests mutate the envelope to provoke one rule; the plan is then re-pinned
    to that envelope's digest so that only the rule under test fires. Pass
    ``repin=False`` to keep the plan's own envelope digest (the digest-binding tests).
    """
    target = envelope_ if envelope_ is not None else envelope()
    if repin:
        plan_ = pinned_to(plan_, target)
    return check_plan(plan_, target, **kwargs)


def only(report: CheckReport, code: str) -> list[Finding]:
    return [finding for finding in report.findings if finding.code == code]


def single(report: CheckReport, code: str) -> Finding:
    matches = only(report, code)
    assert len(matches) == 1, report.render()
    return matches[0]


def write_json(path: Path, model: BaseModel) -> Path:
    path.write_text(json.dumps(model.model_dump(mode="json"), indent=2), encoding="utf-8")
    return path


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    return subprocess.run(
        [sys.executable, "-m", "plumb.checker.cli", *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-014", "PL-015")
def test_valid_baseline_plan_is_ok_with_topological_order() -> None:
    report = check(plan())
    assert report.ok, report.render()
    assert report.findings == []
    assert report.checker == CHECKER_NAME
    assert report.subject == PLAN_ID
    assert report.topological_order == ["probe-sources", "profile-sources", "configure-integration", "build-dataset"]
    assert report.summary["steps"] == 4
    assert report.summary["errors"] == 0
    assert report.summary["warnings"] == 0
    assert report.summary["findings"] == 0
    assert report.summary["acyclic"] is True
    assert report.summary["evaluated_at"] == PLANNED_AT.isoformat()


@pytest.mark.requirements("PL-014")
def test_default_registry_is_used_when_none_is_given() -> None:
    assert check_plan(plan(), envelope()).ok
    assert check_plan(plan(), envelope(), None).ok
    assert check_plan(plan(), envelope(), CapabilityRegistry.default()).ok


@pytest.mark.requirements("PL-015")
def test_every_finding_code_has_the_designed_error_class() -> None:
    assert FINDING_ERROR_CLASSES == {
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


# ---------------------------------------------------------------------------
# Data-driven malformed plans
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-005", "PL-008", "PL-014", "PL-015", "PL-016", "PL-018", "PL-043", "PL-053", "PL-058")
@pytest.mark.parametrize("fixture_path", INVALID_FIXTURE_PATHS, ids=lambda path: path.stem)
def test_invalid_fixture_reports_expected_codes(fixture_path: Path) -> None:
    fixture = load_fixture(f"invalid/{fixture_path.name}")
    assert fixture["description"]
    assert fixture["expected_codes"]
    envelope_ = AutonomyEnvelope.model_validate(fixture["envelope"])
    plan_ = BuildPlan.model_validate(fixture["plan"])
    report = check_plan(plan_, envelope_)
    assert not report.ok, f"{fixture_path.name} passed the checker"
    for code in fixture["expected_codes"]:
        matches = only(report, code)
        assert matches, f"{fixture_path.name}: expected {code}, got {sorted(report.codes())}"
        assert any(finding.severity is Severity.ERROR for finding in matches)
    for finding in report.findings:
        assert finding.error_class is FINDING_ERROR_CLASSES[finding.code]
    assert report.summary["errors"] == len(report.errors)


@pytest.mark.requirements("PL-014", "PL-015")
def test_invalid_fixtures_cover_every_finding_code() -> None:
    expected: set[str] = set()
    for path in INVALID_FIXTURE_PATHS:
        fixture = load_fixture(f"invalid/{path.name}")
        expected.update(fixture["expected_codes"])
    assert expected == set(FINDING_ERROR_CLASSES)


# ---------------------------------------------------------------------------
# Graph structure
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-014")
def test_three_cycle_is_reported_with_its_members_only() -> None:
    cycle = [
        step(step_id="a", inputs=[], depends_on=["c"]),
        step(step_id="b", inputs=[], depends_on=["a"]),
        step(step_id="c", inputs=[], depends_on=["b"]),
        step(step_id="d", inputs=[], depends_on=["a"]),
    ]
    report = check(plan(steps=cycle))
    finding = single(report, "DEPENDENCY_CYCLE")
    assert finding.details["members"] == ["a", "b", "c"]
    assert finding.step_id == "a"
    assert finding.error_class is ErrorClass.STATE_CONFLICT
    assert report.topological_order is None
    assert report.summary["acyclic"] is False
    assert not report.ok


@pytest.mark.requirements("PL-014")
def test_independent_cycles_are_reported_separately() -> None:
    steps = [
        step(step_id="a", inputs=[], depends_on=["b"]),
        step(step_id="b", inputs=[], depends_on=["a"]),
        step(step_id="c", inputs=[], depends_on=["d"]),
        step(step_id="d", inputs=[], depends_on=["c"]),
    ]
    report = check(plan(steps=steps))
    assert [finding.details["members"] for finding in only(report, "DEPENDENCY_CYCLE")] == [["a", "b"], ["c", "d"]]


@pytest.mark.requirements("PL-014", "PL-015")
def test_self_dependency_built_without_validation_is_a_cycle() -> None:
    looped = bypass(step(), depends_on=["probe-sources"])
    report = check(bypass(plan(), steps=[looped]))
    assert single(report, "DEPENDENCY_CYCLE").details["members"] == ["probe-sources"]


@pytest.mark.requirements("PL-015")
def test_duplicate_step_ids_are_reported_once_per_id() -> None:
    report = check(plan(steps=[step(), step(), step()]))
    finding = single(report, "DUPLICATE_STEP_ID")
    assert finding.step_id == "probe-sources"
    assert finding.details["occurrences"] == 3
    assert report.topological_order == ["probe-sources"]


@pytest.mark.requirements("PL-015")
def test_unknown_dependency_is_reported_and_ignored_for_ordering() -> None:
    report = check(plan(steps=replace(baseline_steps(), "build-dataset", depends_on=["profile-sources", "configure-integration", "label-audit"])))
    finding = single(report, "UNKNOWN_DEPENDENCY")
    assert finding.step_id == "build-dataset"
    assert finding.details["dependency"] == "label-audit"
    assert report.topological_order is not None


# ---------------------------------------------------------------------------
# Registry binding and maturity
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-014")
def test_unsupported_step_type_is_rejected_not_interpreted() -> None:
    report = check(plan(steps=replace(baseline_steps(), "build-dataset", step_type="shell.execute_arbitrary")))
    finding = single(report, "UNSUPPORTED_STEP_TYPE")
    assert finding.step_id == "build-dataset"
    assert finding.error_class is ErrorClass.CAPABILITY_UNSUPPORTED
    assert "rejected" in finding.message
    # The dataset capability no longer matches the step type either.
    assert single(report, "UNKNOWN_CAPABILITY").details["capability_step_type"] == "dataset.build"


@pytest.mark.requirements("PL-014", "PL-008")
def test_unknown_capability_and_capability_for_other_step_type() -> None:
    report = check(plan(steps=replace(baseline_steps(), "build-dataset", required_capabilities=["cap.dataset.build.nonexistent", "cap.source.profile.sampler"])))
    findings = only(report, "UNKNOWN_CAPABILITY")
    assert [finding.details["capability_id"] for finding in findings] == ["cap.dataset.build.nonexistent", "cap.source.profile.sampler"]
    assert "not in the registry" in findings[0].message
    assert "implements 'source.profile'" in findings[1].message
    # With no capability bound, an INTERNAL_WRITE step cannot establish SANDBOX_TESTED maturity.
    assert single(report, "CAPABILITY_MATURITY_INSUFFICIENT").details["required"] == "SANDBOX_TESTED"


@pytest.mark.requirements("PL-008")
def test_required_maturity_floors() -> None:
    assert required_maturity(step()) is CapabilityMaturity.DOCUMENTED
    assert required_maturity(baseline_steps()[3]) is CapabilityMaturity.SANDBOX_TESTED
    assert required_maturity(baseline_steps()[2]) is CapabilityMaturity.SANDBOX_TESTED
    assert required_maturity(release_step()) is CapabilityMaturity.PRODUCTION_VERIFIED
    assert required_maturity(release_step(step_type="release.activate_shadow")) is CapabilityMaturity.PRODUCTION_VERIFIED
    assert required_maturity(apply_step()) is CapabilityMaturity.PRODUCTION_VERIFIED
    assert required_maturity(step(step_type="infrastructure.preview")) is CapabilityMaturity.DOCUMENTED
    shadow = step(step_type="collection.deploy_shadow", effect_class=EffectClass.INTERNAL_WRITE)
    assert required_maturity(shadow) is CapabilityMaturity.DOCUMENTED


@pytest.mark.requirements("PL-008")
def test_documented_capability_rejected_for_production_step_but_accepted_for_read_probe() -> None:
    probe_only = plan(steps=replace(baseline_steps(), "probe-sources", required_capabilities=["cap.inventory.probe.portal-scrape"]))
    assert check(probe_only).ok

    training_envelope = envelope(source_grants=[grant(LEDGER, [DataPurpose.INSPECT, DataPurpose.COLLECT, DataPurpose.TRANSFORM, DataPurpose.TRAIN]), grant(MAILBOX, [DataPurpose.INSPECT])])
    documented_training = plan(steps=[*baseline_steps(), train_step(required_capabilities=["cap.training.submit.api-finetune"])])
    report = check(documented_training, training_envelope)
    finding = single(report, "CAPABILITY_MATURITY_INSUFFICIENT")
    assert finding.step_id == "train-model"
    assert finding.details == {"capability_id": "cap.training.submit.api-finetune", "maturity": "DOCUMENTED", "required": "SANDBOX_TESTED"}
    assert report.codes() == {"CAPABILITY_MATURITY_INSUFFICIENT"}

    verified_training = plan(steps=[*baseline_steps(), train_step()])
    assert check(verified_training, training_envelope).ok


@pytest.mark.requirements("PL-008")
def test_release_steps_require_production_verified_capabilities() -> None:
    sandbox_release = capability("cap.release.create.sandbox", "release.create", CapabilityMaturity.SANDBOX_TESTED, [EffectClass.INTERNAL_WRITE])
    report = check(
        plan(steps=[*baseline_steps(), release_step(required_capabilities=["cap.release.create.sandbox"])]),
        registry=registry_with(sandbox_release),
    )
    finding = single(report, "CAPABILITY_MATURITY_INSUFFICIENT")
    assert finding.details["required"] == "PRODUCTION_VERIFIED"
    assert check(plan(steps=[*baseline_steps(), release_step()])).ok


@pytest.mark.requirements("PL-008")
def test_shadow_deployment_accepts_documented_but_backfill_does_not() -> None:
    registry = registry_with(
        capability("cap.collection.deploy_shadow.documented", "collection.deploy_shadow", CapabilityMaturity.DOCUMENTED, [EffectClass.INTERNAL_WRITE], [DataPurpose.COLLECT]),
        capability("cap.collection.backfill.documented", "collection.backfill", CapabilityMaturity.DOCUMENTED, [EffectClass.INTERNAL_WRITE], [DataPurpose.COLLECT]),
    )
    shadow = step(step_id="deploy-shadow", step_type="collection.deploy_shadow", inputs=[], effect_class=EffectClass.INTERNAL_WRITE, purposes=[DataPurpose.COLLECT], scope=scope(), required_capabilities=["cap.collection.deploy_shadow.documented"])
    backfill = step(step_id="backfill", step_type="collection.backfill", inputs=[], effect_class=EffectClass.INTERNAL_WRITE, purposes=[DataPurpose.COLLECT], scope=scope(), required_capabilities=["cap.collection.backfill.documented"])
    report = check(plan(steps=[shadow, backfill]), registry=registry)
    assert [finding.step_id for finding in only(report, "CAPABILITY_MATURITY_INSUFFICIENT")] == ["backfill"]


@pytest.mark.requirements("PL-007", "PL-008")
def test_discovered_capability_is_rejected_even_for_read_only_probe() -> None:
    discovered = capability("cap.inventory.probe.discovered", "inventory.probe", CapabilityMaturity.DISCOVERED, [EffectClass.READ], [DataPurpose.INSPECT])
    report = check(plan(steps=[step(required_capabilities=["cap.inventory.probe.discovered"])]), registry=registry_with(discovered))
    assert single(report, "CAPABILITY_MATURITY_INSUFFICIENT").details["required"] == "DOCUMENTED"


@pytest.mark.requirements("PL-008", "PL-014")
def test_production_step_without_any_capability_cannot_establish_maturity() -> None:
    report = check(plan(steps=replace(baseline_steps(), "build-dataset", required_capabilities=[])))
    assert single(report, "CAPABILITY_MATURITY_INSUFFICIENT").details == {"required": "SANDBOX_TESTED"}
    assert single(report, "UNKNOWN_CAPABILITY").details["registered_capabilities"] == ["cap.dataset.build.builder"]
    # A read-only step without a capability is rejected too: nothing establishes what it does (PL-014).
    read_only = check(plan(steps=[step(required_capabilities=[])]))
    assert not read_only.ok
    assert single(read_only, "UNKNOWN_CAPABILITY").step_id == "probe-sources"
    assert not read_only.has("CAPABILITY_MATURITY_INSUFFICIENT"), "DOCUMENTED needs no maturity finding; the binding itself is missing"


@pytest.mark.requirements("PL-005", "PL-008", "PL-014", "PL-015")
def test_write_only_step_type_cannot_hide_behind_read_with_no_capability() -> None:
    """An integration.configure step declared READ with no capability must not pass a READ-only envelope (PC-02)."""
    narrow = envelope(allowed_effect_classes=[EffectClass.READ, EffectClass.INTERNAL_WRITE])
    disguised = replace(
        baseline_steps(),
        "configure-integration",
        effect_class=EffectClass.READ,
        required_capabilities=[],
        purposes=[DataPurpose.INSPECT],
        verification=[obligation(check="config_digest")],
    )
    report = check(plan(steps=disguised), narrow)
    assert not report.ok
    assert single(report, "UNKNOWN_CAPABILITY").step_id == "configure-integration"
    honest = check(plan(steps=baseline_steps()), narrow)
    assert single(honest, "EFFECT_CLASS_DENIED").step_id == "configure-integration"


# ---------------------------------------------------------------------------
# Inputs and outputs
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-015", "PL-016")
def test_input_from_step_must_be_a_declared_dependency_that_produces_it() -> None:
    not_dependency = plan(steps=replace(baseline_steps(), "build-dataset", depends_on=["configure-integration"]))
    finding = single(check(not_dependency), "INPUT_UNRESOLVED")
    assert finding.details == {"input": "profile", "from_step": "profile-sources"}
    assert "not in depends_on" in finding.message

    renamed = plan(steps=replace(baseline_steps(), "build-dataset", inputs=[StepInput(name="profile-report", kind=ArtifactKind.QUALITY_REPORT, from_step="profile-sources"), StepInput(name="integration", kind=ArtifactKind.INTEGRATION_SPEC, from_step="configure-integration")]))
    assert "does not produce an output named 'profile-report'" in single(check(renamed), "INPUT_UNRESOLVED").message

    ghost = plan(steps=replace(baseline_steps(), "build-dataset", depends_on=["profile-sources", "configure-integration", "ghost"], inputs=[StepInput(name="profile", kind=ArtifactKind.QUALITY_REPORT, from_step="ghost")]))
    report = check(ghost)
    assert "not a step of this plan" in single(report, "INPUT_UNRESOLVED").message
    assert report.has("UNKNOWN_DEPENDENCY")


@pytest.mark.requirements("PL-015")
def test_input_kind_must_match_producer_or_plan_input() -> None:
    wrong_step_kind = plan(steps=replace(baseline_steps(), "build-dataset", inputs=[StepInput(name="profile", kind=ArtifactKind.EVIDENCE_PACKET, from_step="profile-sources"), StepInput(name="integration", kind=ArtifactKind.INTEGRATION_SPEC, from_step="configure-integration")]))
    finding = single(check(wrong_step_kind), "INPUT_KIND_MISMATCH")
    assert finding.details["expected"] == "EvidencePacket"
    assert finding.details["actual"] == "QualityReport"

    wrong_plan_kind = plan(steps=replace(baseline_steps(), "probe-sources", inputs=[StepInput(name="envelope", kind=ArtifactKind.OPPORTUNITY_SPEC, plan_input=ENVELOPE_ID)]))
    finding = single(check(wrong_plan_kind), "INPUT_KIND_MISMATCH")
    assert finding.details == {"input": "envelope", "expected": "OpportunitySpec", "actual": "AutonomyEnvelope"}


@pytest.mark.requirements("PL-015")
def test_plan_input_must_exist_and_an_input_needs_exactly_one_origin() -> None:
    missing = plan(steps=replace(baseline_steps(), "probe-sources", inputs=[StepInput(name="envelope", kind=ArtifactKind.AUTONOMY_ENVELOPE, plan_input="env-not-supplied")]))
    finding = single(check(missing), "MISSING_ARTIFACT")
    assert finding.details == {"input": "envelope", "plan_input": "env-not-supplied"}

    two_origins = bypass(StepInput(name="envelope", kind=ArtifactKind.AUTONOMY_ENVELOPE, plan_input=ENVELOPE_ID), from_step="probe-sources")
    report = check(bypass(plan(), steps=[bypass(step(), inputs=[two_origins])]))
    assert "exactly one origin" in single(report, "INPUT_UNRESOLVED").message


# ---------------------------------------------------------------------------
# Envelope binding
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-005")
def test_tenant_and_envelope_identity_must_match() -> None:
    tenant = single(check(plan(tenant_id="tnt_other0002")), "TENANT_MISMATCH")
    assert tenant.error_class is ErrorClass.SCOPE_DENIED
    assert tenant.details == {"plan_tenant_id": "tnt_other0002", "envelope_tenant_id": TENANT}

    version = single(check(plan(envelope_version=2)), "ENVELOPE_MISMATCH")
    assert version.error_class is ErrorClass.POLICY_STALE
    assert version.details == {"envelope_version": {"plan": 2, "envelope": 1}}

    identity = single(check(plan(envelope_id="env-other", envelope_version=3)), "ENVELOPE_MISMATCH")
    assert set(identity.details) == {"envelope_id", "envelope_version"}


@pytest.mark.requirements("PL-005", "PL-040")
def test_envelope_expired_at_planned_at_is_inactive() -> None:
    expired = single(check(plan(planned_at=EXPIRES_AT)), "ENVELOPE_INACTIVE")
    assert "expired" in expired.message
    assert expired.details["evaluated_at"] == EXPIRES_AT.isoformat()
    assert check(plan(planned_at=EXPIRES_AT - timedelta(seconds=1))).ok


@pytest.mark.requirements("PL-005", "PL-040")
def test_evaluation_instant_is_the_later_of_planned_at_and_now() -> None:
    assert evaluation_instant(plan(), None) == PLANNED_AT
    assert evaluation_instant(plan(), T0) == PLANNED_AT
    assert evaluation_instant(plan(), EXPIRES_AT) == EXPIRES_AT
    assert check(plan(), now=T0).ok
    later = check(plan(), now=EXPIRES_AT + DAY)
    assert single(later, "ENVELOPE_INACTIVE").details["evaluated_at"] == (EXPIRES_AT + DAY).isoformat()
    assert later.summary["evaluated_at"] == (EXPIRES_AT + DAY).isoformat()


@pytest.mark.requirements("PL-005", "PL-040")
def test_revoked_envelope_is_inactive_whatever_the_instant() -> None:
    revoked_later = envelope(revoked_at=PLANNED_AT + DAY)
    finding = single(check(plan(), revoked_later), "ENVELOPE_INACTIVE")
    assert "revoked" in finding.message
    assert finding.details["revoked_at"] == (PLANNED_AT + DAY).isoformat()
    revoked_before = envelope(revoked_at=PLANNED_AT - timedelta(hours=1))
    assert single(check(plan(), revoked_before), "ENVELOPE_INACTIVE").details["revoked_at"]


@pytest.mark.requirements("PL-005")
def test_plan_made_before_the_envelope_version_exists_is_inactive() -> None:
    finding = single(check(plan(planned_at=T0 - DAY)), "ENVELOPE_INACTIVE")
    assert "comes into force" in finding.message


@pytest.mark.requirements("PL-005")
def test_now_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        check(plan(), now=datetime(2026, 10, 3))


# ---------------------------------------------------------------------------
# Scope, effect classes and purposes
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-005")
def test_scope_exceeded_lists_every_violation() -> None:
    wide = scope(sources=[LEDGER, "src-payroll"], processors=["proc-other"], destination_ids=[DESTINATION, "dst-external-bucket"], regions=["us-east-1"])
    report = check(plan(steps=replace(baseline_steps(), "configure-integration", scope=wide)))
    finding = single(report, "SCOPE_EXCEEDED")
    assert finding.step_id == "configure-integration"
    assert finding.details["violations"] == [
        "source_ids not in scope: src-payroll",
        "destination_ids not in scope: dst-external-bucket",
        "processor_ids not in scope: proc-other",
        "regions not in scope: us-east-1",
    ]
    # An ungranted source also has no purposes granted.
    assert single(report, "PURPOSE_DENIED").details["source_id"] == "src-payroll"


@pytest.mark.requirements("PL-005", "PL-053")
def test_expired_grant_removes_source_from_scope_and_purposes_at_the_instant() -> None:
    expiring = envelope(source_grants=[grant(LEDGER, [DataPurpose.INSPECT, DataPurpose.COLLECT, DataPurpose.TRANSFORM], expires_at=PLANNED_AT), grant(MAILBOX, [DataPurpose.INSPECT])])
    report = check(plan(), expiring)
    assert {finding.step_id for finding in only(report, "SCOPE_EXCEEDED")} == {"probe-sources", "profile-sources", "configure-integration", "build-dataset"}
    assert report.has("PURPOSE_DENIED")
    assert check(plan(planned_at=PLANNED_AT - timedelta(hours=1)), expiring).ok


@pytest.mark.requirements("PL-005")
def test_effect_class_denied_by_envelope_and_by_capability() -> None:
    narrow = envelope(allowed_effect_classes=[EffectClass.READ, EffectClass.INTERNAL_WRITE])
    finding = single(check(plan(), narrow), "EFFECT_CLASS_DENIED")
    assert finding.step_id == "configure-integration"
    assert finding.details == {"effect_class": "EXTERNAL_WRITE_REVERSIBLE"}

    understated = plan(steps=replace(baseline_steps(), "configure-integration", effect_class=EffectClass.READ))
    finding = single(check(understated), "EFFECT_CLASS_DENIED")
    assert finding.details["capability_id"] == "cap.integration.configure.management-api"
    assert "not the declared READ" in finding.message


@pytest.mark.requirements("PL-005")
def test_capability_wider_than_envelope_is_a_warning_not_an_error() -> None:
    canary = release_step(
        step_id="canary",
        step_type="release.canary",
        required_capabilities=["cap.release.canary.executor"],
        effect_class=EffectClass.EXTERNAL_WRITE_REVERSIBLE,
        depends_on=["create-release"],
        inputs=[
            StepInput(name="release", kind=ArtifactKind.RELEASE_MANIFEST, from_step="create-release"),
            StepInput(name="approval", kind=ArtifactKind.APPROVAL_RECORD, plan_input=APPROVAL_ID),
        ],
        outputs=[StepOutput(name="canary", kind=ArtifactKind.CANARY_REPORT)],
    )
    report = check(plan(steps=[*baseline_steps(), release_step(), canary]))
    finding = single(report, "EFFECT_CLASS_DENIED")
    assert finding.severity is Severity.WARNING
    assert finding.details["undeclared_effect_classes"] == ["EXTERNAL_COMMUNICATION"]
    assert report.ok
    assert report.summary["warnings"] == 1


@pytest.mark.requirements("PL-053")
def test_train_is_denied_when_grant_only_covers_inspect_and_collect() -> None:
    report = check(plan(steps=[*baseline_steps(), train_step()]))
    finding = single(report, "PURPOSE_DENIED")
    assert finding.step_id == "train-model"
    assert finding.error_class is ErrorClass.PURPOSE_DENIED
    assert finding.details["source_id"] == LEDGER
    assert finding.details["missing"] == ["TRAIN"]
    assert finding.details["granted"] == ["COLLECT", "INSPECT", "TRANSFORM"]
    assert "never inferred" in finding.message
    assert report.codes() == {"PURPOSE_DENIED"}


@pytest.mark.requirements("PL-053")
def test_export_is_denied_when_grant_only_covers_read_like_purposes() -> None:
    exporter = modified(baseline_steps()[3], purposes=[DataPurpose.COLLECT, DataPurpose.TRANSFORM, DataPurpose.EXPORT])
    report = check(plan(steps=[*baseline_steps()[:3], exporter]))
    finding = single(report, "PURPOSE_DENIED")
    assert finding.details["missing"] == ["EXPORT"]
    assert "never inferred" in finding.message


@pytest.mark.requirements("PL-053")
def test_train_is_allowed_only_with_an_explicit_train_grant() -> None:
    granted = envelope(source_grants=[grant(LEDGER, [DataPurpose.INSPECT, DataPurpose.COLLECT, DataPurpose.TRANSFORM, DataPurpose.TRAIN]), grant(MAILBOX, [DataPurpose.INSPECT])])
    assert check(plan(steps=[*baseline_steps(), train_step()]), granted).ok


@pytest.mark.requirements("PL-053")
def test_capability_required_purposes_are_enforced_even_when_the_step_understates_them() -> None:
    understated = train_step(purposes=[DataPurpose.COLLECT])
    report = check(plan(steps=[*baseline_steps(), understated]))
    finding = single(report, "PURPOSE_DENIED")
    assert finding.details["missing"] == ["TRAIN"]
    assert finding.details["required_by_capabilities"] == {"TRAIN": ["cap.training.submit.managed-open-model"]}


@pytest.mark.requirements("PL-004", "PL-053")
def test_purpose_denied_per_source_and_when_no_purpose_is_declared() -> None:
    mailbox_collect = modified(baseline_steps()[1], scope=scope(sources=[LEDGER, MAILBOX]), purposes=[DataPurpose.INSPECT, DataPurpose.COLLECT], required_capabilities=[])
    report = check(plan(steps=[baseline_steps()[0], mailbox_collect]))
    finding = single(report, "PURPOSE_DENIED")
    assert finding.details["source_id"] == MAILBOX
    assert finding.details["missing"] == ["COLLECT"]

    purposeless = step(purposes=[], required_capabilities=[])
    finding = single(check(plan(steps=[purposeless])), "PURPOSE_DENIED")
    assert "declares no data purpose" in finding.message
    assert finding.details["source_ids"] == [LEDGER, MAILBOX]


# ---------------------------------------------------------------------------
# Budgets and attempts
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-058")
def test_budget_nesting_steps_within_plan_within_envelope() -> None:
    over_total = single(check(plan(total_budget=budget(minor_units=30_000))), "BUDGET_EXCEEDED")
    assert over_total.step_id is None
    assert over_total.details == {"step_spend_total": 40_000, "plan_total": 30_000, "currency": "USD"}

    over_limit = single(check(plan(total_budget=budget(minor_units=600_000))), "BUDGET_EXCEEDED")
    assert over_limit.details == {"plan_total": 600_000, "spending_limit": 500_000, "currency": "USD"}

    exact = check(plan(total_budget=budget(minor_units=40_000)), envelope(spending_limit=Money(minor_units=40_000, currency="USD")))
    assert exact.ok


@pytest.mark.requirements("PL-058")
def test_budget_currency_must_be_consistent() -> None:
    envelope_currency = single(check(plan(), envelope(spending_limit=Money(minor_units=500_000, currency="EUR"))), "BUDGET_EXCEEDED")
    assert envelope_currency.details == {"plan_currency": "USD", "envelope_currency": "EUR"}

    foreign_step = bypass(step(), budget=budget(currency="EUR"))
    report = check(bypass(plan(), steps=[foreign_step]))
    finding = single(report, "BUDGET_EXCEEDED")
    assert finding.step_id == "probe-sources"
    assert finding.details == {"step_currency": "EUR", "plan_currency": "USD"}


@pytest.mark.requirements("PL-018")
def test_attempts_may_not_exceed_the_envelope_per_step_limit() -> None:
    report = check(plan(steps=replace(baseline_steps(), "build-dataset", budget=budget(max_attempts=4))))
    finding = single(report, "ATTEMPTS_EXCEEDED")
    assert finding.step_id == "build-dataset"
    assert finding.error_class is ErrorClass.BUDGET_EXCEEDED
    assert finding.details == {"max_attempts": 4, "per_step_attempt_limit": 3}
    assert check(plan(steps=replace(baseline_steps(), "build-dataset", budget=budget(max_attempts=3)))).ok


# ---------------------------------------------------------------------------
# Verification coverage
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-016", "PL-043")
def test_external_effect_requires_integration_behavior_verification() -> None:
    weak = plan(steps=replace(baseline_steps(), "configure-integration", verification=[obligation(VerificationLevel.SCHEMA_VALIDITY, "schema_valid")]))
    finding = single(check(weak), "MISSING_VERIFICATION")
    assert finding.step_id == "configure-integration"
    assert finding.error_class is ErrorClass.VERIFICATION_FAILED
    assert finding.details["required_level"] == "INTEGRATION_BEHAVIOR"
    assert finding.details["declared_levels"] == ["SCHEMA_VALIDITY"]
    stronger = plan(steps=replace(baseline_steps(), "configure-integration", verification=[obligation(VerificationLevel.BUSINESS_OUTCOME, "scenario_suite")]))
    assert check(stronger).ok


@pytest.mark.requirements("PL-016", "PL-043")
def test_release_steps_need_a_business_outcome_obligation() -> None:
    weak_release = release_step(verification=[obligation(check="manifest_digest"), obligation(VerificationLevel.ECONOMIC_RESULT, "cost_tracking")])
    finding = single(check(plan(steps=[*baseline_steps(), weak_release])), "MISSING_VERIFICATION")
    assert finding.step_id == "create-release"
    assert finding.details["required_level"] == "BUSINESS_OUTCOME"
    assert check(plan(steps=[*baseline_steps(), release_step()])).ok


@pytest.mark.requirements("PL-016")
def test_every_step_except_dependency_raise_needs_an_obligation() -> None:
    raise_dependency = step(step_id="raise-access", step_type="dependency.raise", inputs=[], outputs=[StepOutput(name="dependency", kind=ArtifactKind.DEPENDENCY_RECORD)], required_capabilities=["cap.dependency.raise.control-plane"], effect_class=EffectClass.INTERNAL_WRITE, purposes=[], scope=scope(sources=[]), verification=[])
    assert check(plan(steps=[raise_dependency])).ok

    unverified = bypass(step(), verification=[])
    finding = single(check(bypass(plan(), steps=[unverified])), "MISSING_VERIFICATION")
    assert "no verification obligation" in finding.message


# ---------------------------------------------------------------------------
# Deployment environments
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-005")
def test_deployment_environment_must_be_declared_and_allowed() -> None:
    production = release_step(environment="production")
    finding = single(check(plan(steps=[*baseline_steps(), production])), "DEPLOYMENT_ENV_DENIED")
    assert finding.step_id == "create-release"
    assert finding.error_class is ErrorClass.SCOPE_DENIED
    assert finding.details == {"environment": "production", "allowed_environments": [ENVIRONMENT]}

    undeclared = release_step(environment=None)
    finding = single(check(plan(steps=[*baseline_steps(), undeclared])), "DEPLOYMENT_ENV_DENIED")
    assert finding.severity is Severity.ERROR
    assert "declares no deployment environment" in finding.message

    nowhere = envelope(deployment_environments=[])
    assert single(check(plan(steps=[*baseline_steps(), release_step()]), nowhere), "DEPLOYMENT_ENV_DENIED").details["allowed_environments"] == []


def infra_envelope() -> AutonomyEnvelope:
    return envelope(allowed_effect_classes=[EffectClass.READ, EffectClass.INTERNAL_WRITE, EffectClass.EXTERNAL_WRITE_REVERSIBLE, EffectClass.INFRASTRUCTURE_CHANGE])


@pytest.mark.requirements("PL-005", "PL-045")
def test_infrastructure_apply_needs_an_environment_but_preview_only_warns() -> None:
    assert check(plan(steps=[preview_step(), apply_step()]), infra_envelope()).ok

    silent_apply = single(check(plan(steps=[preview_step(), apply_step(environment=None)]), infra_envelope()), "DEPLOYMENT_ENV_DENIED")
    assert silent_apply.severity is Severity.ERROR

    report = check(plan(steps=[preview_step(environment=None)]), infra_envelope())
    assert single(report, "DEPLOYMENT_ENV_DENIED").severity is Severity.WARNING
    assert report.ok


@pytest.mark.requirements("PL-045", "PL-015")
def test_infrastructure_apply_requires_a_preview_and_an_approval_before_application() -> None:
    """PL-045: a preview/diff and approval MUST precede application; an apply step with neither is rejected (PC-01)."""
    lone_apply = apply_step(depends_on=[], inputs=[])
    report = check(plan(steps=[lone_apply]), infra_envelope())
    assert not report.ok
    findings = only(report, "PRECONDITION_MISSING")
    assert sorted(finding.details["required_kind"] for finding in findings) == ["ApprovalRecord", "InfrastructurePreview"]
    assert all(finding.error_class is ErrorClass.STATE_CONFLICT and finding.step_id == "apply-infrastructure" for finding in findings)
    assert {finding.code for finding in report.errors} == {"PRECONDITION_MISSING"}

    # A preview that merely exists is not enough: apply must consume it from a preview step it depends on.
    no_preview_input = apply_step(inputs=[StepInput(name="approval", kind=ArtifactKind.APPROVAL_RECORD, plan_input=APPROVAL_ID)])
    report = check(plan(steps=[preview_step(), no_preview_input]), infra_envelope())
    assert [finding.details["required_kind"] for finding in only(report, "PRECONDITION_MISSING")] == ["InfrastructurePreview"]

    # The preview must come from an infrastructure.preview step, not from any step that emits the kind.
    forged_preview = step(
        step_id="fake-preview",
        step_type="inventory.probe",
        outputs=[StepOutput(name="preview", kind=ArtifactKind.INFRASTRUCTURE_PREVIEW)],
        scope=scope(sources=[LEDGER, MAILBOX]),
    )
    forged_apply = apply_step(
        depends_on=["fake-preview"],
        inputs=[
            StepInput(name="preview", kind=ArtifactKind.INFRASTRUCTURE_PREVIEW, from_step="fake-preview"),
            StepInput(name="approval", kind=ArtifactKind.APPROVAL_RECORD, plan_input=APPROVAL_ID),
        ],
    )
    report = check(plan(steps=[forged_preview, forged_apply]), infra_envelope())
    assert [finding.details["required_producer_step_type"] for finding in only(report, "PRECONDITION_MISSING")] == ["infrastructure.preview"]
    assert report.has("ARTIFACT_KIND_UNSUPPORTED"), "a probe cannot produce an InfrastructurePreview either"
    # Without an approval the apply is rejected even when the preview is genuine.
    unapproved = apply_step(inputs=[StepInput(name="preview", kind=ArtifactKind.INFRASTRUCTURE_PREVIEW, from_step="preview-infrastructure")])
    report = check(plan(steps=[preview_step(), unapproved]), infra_envelope())
    assert [finding.details["required_kind"] for finding in only(report, "PRECONDITION_MISSING")] == ["ApprovalRecord"]


@pytest.mark.requirements("PL-005")
def test_any_step_declaring_an_environment_must_use_an_allowed_one() -> None:
    misplaced = plan(steps=replace(baseline_steps(), "build-dataset", environment="production"))
    assert single(check(misplaced), "DEPLOYMENT_ENV_DENIED").details["environment"] == "production"
    assert check(plan(steps=replace(baseline_steps(), "build-dataset", environment=ENVIRONMENT))).ok


# ---------------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-014", "PL-015")
def test_cli_exits_0_for_a_valid_plan(tmp_path: Path) -> None:
    plan_path = write_json(tmp_path / "plan.json", plan())
    envelope_path = write_json(tmp_path / "envelope.json", envelope())
    completed = run_cli("plan", str(plan_path), str(envelope_path))
    assert completed.returncode == EXIT_OK, completed.stderr
    assert f"{CHECKER_NAME}: {PLAN_ID}: OK" in completed.stdout


@pytest.mark.requirements("PL-014", "PL-015")
def test_cli_exits_1_and_prints_json_findings(tmp_path: Path) -> None:
    cyclic = plan(steps=[step(step_id="a", inputs=[], depends_on=["b"]), step(step_id="b", inputs=[], depends_on=["a"])])
    plan_path = write_json(tmp_path / "plan.json", cyclic)
    envelope_path = write_json(tmp_path / "envelope.json", envelope())
    completed = run_cli("plan", str(plan_path), str(envelope_path), "--json")
    assert completed.returncode == EXIT_FINDINGS, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["ok"] is False
    assert payload["topological_order"] is None
    assert {finding["code"] for finding in payload["findings"]} == {"DEPENDENCY_CYCLE"}
    assert payload["findings"][0]["error_class"] == "STATE_CONFLICT"
    assert payload["summary"]["errors"] == 1


@pytest.mark.requirements("PL-014")
def test_cli_exits_2_on_usage_and_parse_errors(tmp_path: Path) -> None:
    envelope_path = write_json(tmp_path / "envelope.json", envelope())
    missing = run_cli("plan", str(tmp_path / "absent.json"), str(envelope_path))
    assert missing.returncode == EXIT_USAGE
    assert "cannot read" in missing.stderr

    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    malformed = run_cli("plan", str(broken), str(envelope_path))
    assert malformed.returncode == EXIT_USAGE
    assert "not valid JSON" in malformed.stderr

    not_a_plan = run_cli("plan", str(envelope_path), str(envelope_path))
    assert not_a_plan.returncode == EXIT_USAGE
    assert "not a valid BuildPlan" in not_a_plan.stderr

    no_subcommand = run_cli()
    assert no_subcommand.returncode == EXIT_USAGE


@pytest.mark.requirements("PL-005", "PL-014")
def test_cli_in_process_registry_and_now_options(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    plan_path = write_json(tmp_path / "plan.json", plan())
    envelope_path = write_json(tmp_path / "envelope.json", envelope())
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        json.dumps({"capabilities": [record.model_dump(mode="json") for record in CapabilityRegistry.default().records()]}),
        encoding="utf-8",
    )
    assert main(["plan", str(plan_path), str(envelope_path), "--registry", str(registry_path)]) == EXIT_OK
    capsys.readouterr()

    assert main(["plan", str(plan_path), str(envelope_path), "--now", "2027-06-01T00:00:00Z", "--json"]) == EXIT_FINDINGS
    payload = json.loads(capsys.readouterr().out)
    assert "ENVELOPE_INACTIVE" in payload["summary"]["codes"]

    assert main(["plan", str(plan_path), str(envelope_path), "--now", "2027-06-01T00:00:00"]) == EXIT_USAGE
    assert "timezone" in capsys.readouterr().err

    registry_path.write_text("[]", encoding="utf-8")
    assert main(["plan", str(plan_path), str(envelope_path), "--registry", str(registry_path)]) == EXIT_USAGE
    assert "capabilities" in capsys.readouterr().err

    assert main(["--help"]) == EXIT_OK
    assert "{plan,dataset}" in capsys.readouterr().out


@pytest.mark.requirements("PL-028")
def test_cli_dataset_subcommand_exits_2_on_unreadable_manifest(tmp_path: Path) -> None:
    completed = run_cli("dataset", str(tmp_path / "absent.json"))
    assert completed.returncode == EXIT_USAGE
    assert "absent.json" in completed.stderr


# ---------------------------------------------------------------------------
# Review regressions: authority rules a planner could previously route around
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-053", "PL-004")
def test_training_on_derived_data_inherits_the_source_restrictions() -> None:
    """A training step that omits scope.source_ids still trains on the dataset's sources (PC-03, SEC-04)."""
    no_train_anywhere = envelope()
    assert all(DataPurpose.TRAIN not in g.purposes for g in no_train_anywhere.source_grants)
    hidden = train_step(scope=scope(sources=[], processors=[PROCESSOR]))
    report = check(plan(steps=[*baseline_steps(), hidden]), no_train_anywhere)
    assert not report.ok
    finding = single(report, "PURPOSE_DENIED")
    assert finding.step_id == "train-model"
    assert finding.details == {
        "source_id": LEDGER,
        "inherited": True,
        "missing": ["TRAIN"],
        "granted": ["COLLECT", "INSPECT", "TRANSFORM"],
        "required_by_capabilities": {"TRAIN": ["cap.training.submit.managed-open-model"]},
    }
    assert "derived data inherits its restrictions" in finding.message
    assert report.summary["inherited_sources"]["train-model"] == [LEDGER]
    # The same plan is fine once the ledger grant carries TRAIN: inheritance is not a blanket denial.
    granted = envelope(source_grants=[grant(LEDGER, [DataPurpose.INSPECT, DataPurpose.COLLECT, DataPurpose.TRANSFORM, DataPurpose.TRAIN]), grant(MAILBOX, [DataPurpose.INSPECT])])
    assert check(plan(steps=[*baseline_steps(), hidden]), granted).ok


@pytest.mark.requirements("PL-053")
def test_export_or_train_without_any_source_is_denied_not_skipped() -> None:
    exporter = step(
        step_id="export-dataset",
        step_type="dataset.build",
        description="Export the dataset to the approved destination.",
        depends_on=[],
        inputs=[],
        outputs=[StepOutput(name="dataset", kind=ArtifactKind.DATASET_MANIFEST)],
        required_capabilities=["cap.dataset.build.builder"],
        effect_class=EffectClass.INTERNAL_WRITE,
        purposes=[DataPurpose.COLLECT, DataPurpose.TRANSFORM, DataPurpose.EXPORT],
        scope=scope(sources=[], processors=[PROCESSOR]),
    )
    finding = single(check(plan(steps=[exporter])), "PURPOSE_DENIED")
    assert finding.details == {"purposes": ["EXPORT"]}
    assert "touches no source" in finding.message


@pytest.mark.requirements("PL-053", "PL-015")
def test_input_lineage_may_be_narrowed_only_to_sources_the_producer_touched() -> None:
    """``StepInput.source_ids`` declares which of the producer's sources an input carries (SEC-04)."""
    wide_grants = envelope(source_grants=[grant(LEDGER, [DataPurpose.INSPECT, DataPurpose.COLLECT, DataPurpose.TRANSFORM, DataPurpose.TRAIN]), grant(MAILBOX, [DataPurpose.INSPECT, DataPurpose.COLLECT, DataPurpose.TRANSFORM])])
    steps = replace(baseline_steps(), "build-dataset", scope=scope(sources=[LEDGER, MAILBOX], processors=[PROCESSOR]))
    both = train_step(scope=scope(sources=[], processors=[PROCESSOR]))
    denied = check(plan(steps=[*steps, both]), wide_grants)
    assert single(denied, "PURPOSE_DENIED").details["source_id"] == MAILBOX

    ledger_only = train_step(
        scope=scope(sources=[], processors=[PROCESSOR]),
        inputs=[StepInput(name="dataset", kind=ArtifactKind.DATASET_MANIFEST, from_step="build-dataset", source_ids=[LEDGER])],
    )
    narrowed = check(plan(steps=[*steps, ledger_only]), wide_grants)
    assert narrowed.ok, narrowed.render()
    assert narrowed.summary["inherited_sources"]["train-model"] == [LEDGER]

    invented = train_step(
        scope=scope(sources=[], processors=[PROCESSOR]),
        inputs=[StepInput(name="dataset", kind=ArtifactKind.DATASET_MANIFEST, from_step="build-dataset", source_ids=["src-payroll"])],
    )
    finding = single(check(plan(steps=[*steps, invented]), wide_grants), "SCOPE_EXCEEDED")
    assert finding.details["narrowed_to"] == ["src-payroll"] and finding.details["producer_sources"] == [LEDGER, MAILBOX]


@pytest.mark.requirements("PL-008")
def test_shadow_deployment_exemption_does_not_cover_external_writes() -> None:
    """A collection.deploy_shadow step that writes to the customer's system needs SANDBOX_TESTED (PC-04)."""
    documented_external = capability(
        "cap.collection.deploy_shadow.documented-external", "collection.deploy_shadow", CapabilityMaturity.DOCUMENTED,
        [EffectClass.EXTERNAL_WRITE_REVERSIBLE], [DataPurpose.COLLECT],
    )
    shadow = step(
        step_id="deploy-shadow", step_type="collection.deploy_shadow", description="Register a webhook on the customer system.",
        inputs=[], outputs=[StepOutput(name="collection", kind=ArtifactKind.COLLECTION_SPEC)],
        required_capabilities=["cap.collection.deploy_shadow.documented-external"],
        effect_class=EffectClass.EXTERNAL_WRITE_REVERSIBLE, purposes=[DataPurpose.COLLECT], scope=scope(),
        verification=[obligation(VerificationLevel.INTEGRATION_BEHAVIOR, "webhook_receipt")],
    )
    assert required_maturity(shadow) is CapabilityMaturity.SANDBOX_TESTED
    assert required_maturity(modified(shadow, effect_class=EffectClass.INTERNAL_WRITE, verification=[obligation(check="shadow_path")])) is CapabilityMaturity.DOCUMENTED
    finding = single(check(plan(steps=[shadow]), registry=registry_with(documented_external)), "CAPABILITY_MATURITY_INSUFFICIENT")
    assert finding.details["required"] == "SANDBOX_TESTED"


@pytest.mark.requirements("PL-008")
def test_dependency_raise_bound_to_a_discovered_capability_is_rejected() -> None:
    """The raise step is exempt from binding, not from maturity once bound (PC-11)."""
    discovered = capability("cap.dependency.raise.discovered", "dependency.raise", CapabilityMaturity.DISCOVERED, [EffectClass.INTERNAL_WRITE])
    raise_step = step(
        step_id="raise", step_type="dependency.raise", inputs=[], outputs=[StepOutput(name="dep", kind=ArtifactKind.DEPENDENCY_RECORD)],
        required_capabilities=["cap.dependency.raise.discovered"], effect_class=EffectClass.INTERNAL_WRITE, purposes=[], scope=scope(sources=[]), verification=[],
    )
    assert required_maturity(raise_step) is CapabilityMaturity.DOCUMENTED
    finding = single(check(plan(steps=[raise_step]), registry=registry_with(discovered)), "CAPABILITY_MATURITY_INSUFFICIENT")
    assert finding.details["required"] == "DOCUMENTED"
    unbound = modified(raise_step, required_capabilities=[])
    assert check(plan(steps=[unbound])).ok, "the control plane records a dependency itself; no binding is required"


@pytest.mark.requirements("PL-005")
def test_plan_goal_must_be_one_of_the_envelope_goals() -> None:
    finding = single(check(plan(goal_id="goal-post-journal-entries-automatically")), "GOAL_NOT_AUTHORIZED")
    assert finding.error_class is ErrorClass.SCOPE_DENIED
    assert finding.details == {"plan_goal_id": "goal-post-journal-entries-automatically", "envelope_goal_ids": ["goal-fewer-evidence-requests"]}
    two_goals = envelope(goals=[Goal(goal_id="goal-fewer-evidence-requests", objective="Fewer requests."), Goal(goal_id="goal-faster-close", objective="Faster close.")])
    assert check(plan(goal_id="goal-faster-close"), two_goals).ok


@pytest.mark.requirements("PL-015", "PL-014")
def test_output_and_input_kinds_must_be_supported_by_the_bound_capability() -> None:
    """dataset.build cannot emit a ReleaseManifest for release.activate_shadow to consume (PC-06)."""
    fabricated = replace(baseline_steps(), "build-dataset", outputs=[StepOutput(name="release-manifest", kind=ArtifactKind.RELEASE_MANIFEST)])
    shadow = release_step(
        step_id="activate-shadow", step_type="release.activate_shadow", required_capabilities=["cap.release.activate_shadow.executor"],
        depends_on=["build-dataset"],
        inputs=[StepInput(name="release-manifest", kind=ArtifactKind.RELEASE_MANIFEST, from_step="build-dataset")],
        outputs=[StepOutput(name="shadow-manifest", kind=ArtifactKind.RELEASE_MANIFEST)],
    )
    report = check(plan(steps=[*fabricated, shadow]))
    [finding] = only(report, "ARTIFACT_KIND_UNSUPPORTED")
    assert finding.step_id == "build-dataset" and finding.details["direction"] == "produces" and finding.details["kind"] == "ReleaseManifest"
    assert finding.error_class is ErrorClass.CAPABILITY_UNSUPPORTED

    unconsumable = replace(baseline_steps(), "profile-sources", inputs=[StepInput(name="inventory", kind=ArtifactKind.ENVIRONMENT_INVENTORY, from_step="probe-sources")])
    probe_emits_dataset = replace(unconsumable, "probe-sources", outputs=[StepOutput(name="inventory", kind=ArtifactKind.ENVIRONMENT_INVENTORY), StepOutput(name="dataset", kind=ArtifactKind.DATASET_MANIFEST)])
    consumer = replace(probe_emits_dataset, "profile-sources", inputs=[StepInput(name="dataset", kind=ArtifactKind.DATASET_MANIFEST, from_step="probe-sources")])
    report = check(plan(steps=consumer))
    assert {(f.step_id, f.details["direction"]) for f in only(report, "ARTIFACT_KIND_UNSUPPORTED")} == {("probe-sources", "produces"), ("profile-sources", "consumes")}


@pytest.mark.requirements("PL-016", "PL-015")
def test_required_step_cannot_rest_on_an_optional_or_dependency_raise_prerequisite() -> None:
    """``BuildStep.required`` has semantics (PC-07): optional and raise steps are not verifiable prerequisites."""
    optional_producer = check(plan(steps=replace(baseline_steps(), "profile-sources", required=False)))
    finding = single(optional_producer, "UNVERIFIABLE_PREREQUISITE")
    assert (finding.step_id, finding.details) == ("build-dataset", {"prerequisite": "profile-sources", "reason": "optional_prerequisite"})
    assert finding.error_class is ErrorClass.VERIFICATION_FAILED
    # An optional consumer of an optional producer is fine.
    assert check(plan(steps=replace(replace(baseline_steps(), "profile-sources", required=False), "build-dataset", required=False))).ok

    raise_step = step(
        step_id="raise-access", step_type="dependency.raise", description="Ask for access.", inputs=[],
        outputs=[StepOutput(name="dependency", kind=ArtifactKind.DEPENDENCY_RECORD)],
        required_capabilities=["cap.dependency.raise.control-plane"], effect_class=EffectClass.INTERNAL_WRITE,
        purposes=[], scope=scope(sources=[]), verification=[],
    )
    consumer = replace(
        baseline_steps(), "configure-integration", depends_on=["probe-sources", "raise-access"],
        inputs=[
            StepInput(name="inventory", kind=ArtifactKind.ENVIRONMENT_INVENTORY, from_step="probe-sources"),
            StepInput(name="dependency", kind=ArtifactKind.DEPENDENCY_RECORD, from_step="raise-access"),
        ],
    )
    report = check(plan(steps=[*consumer, raise_step]))
    assert single(report, "UNVERIFIABLE_PREREQUISITE").details == {"prerequisite": "raise-access", "reason": "dependency_raise"}
    assert report.has("ARTIFACT_KIND_UNSUPPORTED"), "integration.configure does not consume a DependencyRecord either"


@pytest.mark.requirements("PL-058", "PL-018", "PL-014")
def test_elapsed_time_model_calls_and_attempts_nest_inside_the_plan_total() -> None:
    """Only spend used to nest; every dimension of the plan total bounds the steps now (PC-08)."""
    greedy = replace(baseline_steps(), "build-dataset", budget=budget(max_elapsed_seconds=10**9, max_model_calls=10**9))
    total = budget(minor_units=100_000, max_elapsed_seconds=3600, max_model_calls=100)
    report = check(plan(steps=greedy, total_budget=total))
    assert not report.ok
    dimensions = {finding.details.get("dimension") for finding in only(report, "BUDGET_EXCEEDED")}
    assert dimensions == {"max_elapsed_seconds", "max_model_calls"}
    # Attempts: the plan total bounds a step even when the envelope would allow more.
    roomy = envelope(per_step_attempt_limit=10)
    report = check(plan(steps=replace(baseline_steps(), "build-dataset", budget=budget(max_attempts=5)), total_budget=budget(minor_units=100_000, max_attempts=3)), roomy)
    assert single(report, "ATTEMPTS_EXCEEDED").details == {"max_attempts": 5, "plan_max_attempts": 3}
    # Model calls sum across steps; an unset plan total imposes no bound.
    unbounded = check(plan(steps=greedy, total_budget=budget(minor_units=100_000, max_elapsed_seconds=10**9)))
    assert unbounded.ok


@pytest.mark.requirements("PL-005", "PL-016")
def test_plan_envelope_input_must_pin_the_envelope_it_is_checked_against() -> None:
    """The plan's envelope ArtifactRef binds by digest, not only by id and version (PC-09)."""
    forged = ArtifactRef(artifact_id=ENVELOPE_ID, kind=ArtifactKind.AUTONOMY_ENVELOPE, digest="sha256:" + "00" * 32)
    approval = ArtifactRef(artifact_id=APPROVAL_ID, kind=ArtifactKind.APPROVAL_RECORD, digest=DIGEST)
    report = check(plan(inputs=[forged, approval]), repin=False)
    finding = single(report, "ENVELOPE_MISMATCH")
    assert finding.details["digest"]["plan_input"] == forged.digest
    assert finding.details["digest"]["envelope"] == compute_artifact_digest(envelope())
    assert finding.error_class is ErrorClass.POLICY_STALE

    wrong_kind = ArtifactRef(artifact_id=ENVELOPE_ID, kind=ArtifactKind.APPROVAL_RECORD, digest=compute_artifact_digest(envelope()))
    report = check(plan(inputs=[wrong_kind, approval], steps=[step(inputs=[StepInput(name="envelope", kind=ArtifactKind.APPROVAL_RECORD, plan_input=ENVELOPE_ID)])]), repin=False)
    assert "kind" in single(report, "ENVELOPE_MISMATCH").details

    # A plan compiled against a different version of the same envelope carries a different digest.
    revised = envelope(version=2, envelope_version=2)
    report = check(plan(envelope_version=2), revised, repin=False)
    assert "digest" in single(report, "ENVELOPE_MISMATCH").details
    assert check(plan(envelope_version=2), revised).ok, "re-pinned to the revised envelope the plan is fine"
    assert check(plan()).ok, "the baseline plan pins the baseline envelope"


@pytest.mark.requirements("PL-014", "PL-015")
def test_cli_accepts_a_single_file_embedding_plan_and_envelope() -> None:
    cycle = FIXTURES_DIR / "invalid" / "cycle.json"
    completed = run_cli("plan", str(cycle), "--json")
    assert completed.returncode == EXIT_FINDINGS, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["ok"] is False and "DEPENDENCY_CYCLE" in {f["code"] for f in payload["findings"]}
    bare_plan = FIXTURES_DIR / "plans" / "accounting_evidence_preparation.json"
    completed = run_cli("plan", str(bare_plan))
    assert completed.returncode == EXIT_USAGE
    assert "does not embed an envelope" in completed.stderr
