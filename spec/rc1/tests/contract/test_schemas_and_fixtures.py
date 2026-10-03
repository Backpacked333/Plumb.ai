"""Contract tests: fixtures agree with the canonical models and generated schemas; state tables agree with enums.
Covers AT-001, AT-002, AT-003, AT-010."""
import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "contracts" / "generated-json-schema"
FX = ROOT / "fixtures"

from plumb_contracts import enums  # noqa: E402
from plumb_contracts.models import TOP_LEVEL_MODELS  # noqa: E402
from machine import GuardedMachine  # noqa: E402

FIXTURE_MODEL = {
    "build_plan.json": "BuildPlan",
    "workflow_spec.json": "WorkflowSpec",
    "solution_spec.json": "SolutionSpec",
    "opportunity_spec.json": "OpportunitySpec",
    "approval_release_activation.json": "Approval",
    "action_intent_send_request.json": "ActionIntent",
    "release_manifest.json": "ReleaseManifest",
    "collection_spec_qbo.json": "CollectionSpec",
    "autonomy_envelope.json": "AutonomyEnvelope",
}

MACHINE_ENUM = {
    "build.yaml": enums.BuildState,
    "step.yaml": enums.StepState,
    "collector.yaml": enums.CollectorState,
    "dataset.yaml": enums.DatasetState,
    "training.yaml": enums.TrainingState,
    "release.yaml": enums.ReleaseState,
    "effect.yaml": enums.EffectState,
    "approval.yaml": enums.ApprovalState,
    "case.yaml": enums.CaseState,
    "removal.yaml": enums.RemovalState,
}


def _fixture_files():
    for scenario in ("accounting", "industrial-rfq", "laundry-routing"):
        for f in sorted((FX / scenario).glob("*.json")):
            model = FIXTURE_MODEL.get(f.name) or ("SourceGrant" if f.name.startswith("source_grant_") else None)
            if model:
                yield pytest.param(f, model, id=f"{scenario}/{f.name}")


@pytest.mark.parametrize("path,model", list(_fixture_files()))
def test_fixture_validates_against_model_and_schema(path, model):
    obj = json.loads(path.read_text())
    TOP_LEVEL_MODELS[model].model_validate(obj)
    schema = json.loads((SCHEMAS / f"{model}.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema).validate(obj)


def test_generated_schemas_are_current(tmp_path):
    """Regenerating must reproduce the committed schemas byte for byte (schema drift is a defect)."""
    env = {"PYTHONPATH": str(ROOT / "contracts" / "canonical-models")}
    code = (ROOT / "tools" / "gen_schemas.py").read_text().replace('OUT = ROOT / "contracts" / "generated-json-schema"', f'OUT = Path(r"{tmp_path}")')
    (tmp_path / "gen.py").write_text(code)
    subprocess.run([sys.executable, str(tmp_path / "gen.py")], check=True, cwd=ROOT, env=env, capture_output=True)
    for f in SCHEMAS.glob("*.schema.json"):
        assert (tmp_path / f.name).read_text() == f.read_text(), f"{f.name} drifted from models"


@pytest.mark.parametrize("name", [n for n in json.loads((FX / "failure-cases" / "expected.json").read_text()) if not n.startswith("plan_")])
def test_schema_level_failure_fixtures_are_rejected(name):
    expected = json.loads((FX / "failure-cases" / "expected.json").read_text())[name]
    model = expected[0].split(":", 1)[1]
    obj = json.loads((FX / "failure-cases" / f"{name}.json").read_text())
    with pytest.raises(Exception):
        TOP_LEVEL_MODELS[model].model_validate(obj)


@pytest.mark.parametrize("fname,enum", list(MACHINE_ENUM.items()))
def test_state_tables_match_enums_and_are_well_formed(fname, enum):
    table = yaml.safe_load((ROOT / "contracts" / "state-machines" / fname).read_text())
    assert set(table["states"]) == {e.value for e in enum}, f"{fname} states differ from enum {enum.__name__}"
    m = GuardedMachine.load(fname)  # constructor checks reachability and terminal outgoing transitions
    assert m.initial == enum(table["initial"]).value
    for t in m.transitions:
        assert t.writes, f"{fname}: transition {t.from_state}->{t.to_state} declares no writes"
        assert t.emits, f"{fname}: transition {t.from_state}->{t.to_state} emits nothing"


def test_every_guard_named_in_tables_for_tested_machines_is_registered():
    from guards import REGISTRY
    for fname, guards in REGISTRY.items():
        table = yaml.safe_load((ROOT / "contracts" / "state-machines" / fname).read_text())
        named = {g for t in table["transitions"] for g in t.get("guards", [])}
        missing = named - set(guards)
        assert not missing, f"{fname}: guards without implementation {sorted(missing)}"
