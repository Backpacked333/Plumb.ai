"""Compiler validation passes on accepted and rejected fixtures (AT-020..AT-024)."""
import json
from pathlib import Path

import pytest

from plumb_contracts.models import AutonomyEnvelope
from validator import ValidationContext, validate_plan

ROOT = Path(__file__).resolve().parents[2]
FX = ROOT / "fixtures"


def load_ctx(scenario: str) -> ValidationContext:
    raw = json.loads((FX / scenario / "validation_context.json").read_text())
    return ValidationContext(
        tenant_id=raw["tenant_id"],
        envelope=AutonomyEnvelope.model_validate(raw["envelope"]),
        grants=raw["grants"],
        artifacts={k: {**v, "impact_class": __import__("plumb_contracts.enums", fromlist=["ImpactClass"]).ImpactClass(v["impact_class"]) if "impact_class" in v else None} for k, v in raw["artifacts"].items()},
        capabilities=raw["capabilities"],
        approval_obligations=set(raw.get("approval_obligations", [])),
    )


@pytest.mark.parametrize("scenario", ["accounting", "industrial-rfq", "laundry-routing"])
def test_reference_plans_validate(scenario):
    plan = json.loads((FX / scenario / "build_plan.json").read_text())
    report = validate_plan(plan, load_ctx(scenario))
    assert report.ok, [f"{i.code} {i.path}: {i.message}" for i in report.errors]


def test_medium_impact_plan_warns_that_activation_needs_approval():
    plan = json.loads((FX / "industrial-rfq" / "build_plan.json").read_text())
    report = validate_plan(plan, load_ctx("industrial-rfq"))
    assert any(i.code == "W_RELEASE_APPROVAL_REQUIRED" for i in report.issues)


@pytest.mark.parametrize("name", [n for n in json.loads((FX / "failure-cases" / "expected.json").read_text()) if n.startswith("plan_")])
def test_failure_fixtures_produce_expected_codes(name):
    expected = set(json.loads((FX / "failure-cases" / "expected.json").read_text())[name])
    plan = json.loads((FX / "failure-cases" / f"{name}.json").read_text())
    report = validate_plan(plan, load_ctx("accounting"))
    assert not report.ok, f"{name} unexpectedly validated"
    assert expected <= report.codes(), f"{name}: expected {expected}, got {report.codes()}"


def test_cross_tenant_plan_is_refused_even_when_well_formed():
    plan = json.loads((FX / "accounting" / "build_plan.json").read_text())
    ctx = load_ctx("accounting")
    ctx.tenant_id = "tnt_someone_else"
    report = validate_plan(plan, ctx)
    assert "E_TENANT_MISMATCH" in report.codes()


def test_inactive_envelope_blocks_validation():
    plan = json.loads((FX / "accounting" / "build_plan.json").read_text())
    ctx = load_ctx("accounting")
    ctx.envelope = ctx.envelope.model_copy(update={"status": "revoked"})
    assert "E_AUTHZ_ENVELOPE" in validate_plan(plan, ctx).codes()
