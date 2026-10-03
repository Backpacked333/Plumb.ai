"""Tests for the committed JSON Schemas and their generator.

The schemas under ``schemas/`` are the machine-readable form of the 17
top-level contracts (design section 3) and the five supporting records. These
tests prove that the committed files are exactly what
``python -m plumb.schemas_tool.generate`` produces from the Pydantic models,
that each is a well-formed draft 2020-12 schema with ``$schema``/``$id``/title,
and that real artifacts (the three scenario envelopes and plans, the malformed
plan fixtures, the packaged capability registry) validate against the schema
of their kind after a round trip through the contract classes.

Requirements exercised: PL-004 (tenant and kind typed on every artifact),
PL-005 (envelope contract), PL-008 (capability records), PL-014 (build plans),
PL-037 (action intents), PL-040 (approval records).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from pydantic import BaseModel

from plumb.contracts import SUPPORTING_CONTRACTS, TOP_LEVEL_CONTRACTS, pinned_kind
from plumb.contracts.approval import ApprovalRecord
from plumb.contracts.build_plan import BuildPlan
from plumb.contracts.capability import CapabilityRecord
from plumb.contracts.common import ArtifactKind, EffectClass, compute_artifact_digest
from plumb.contracts.effect import ActionIntent, EffectSlot, derive_idempotency_key
from plumb.contracts.envelope import AutonomyEnvelope
from plumb.registry.registry import DEFAULT_REGISTRY_PATH
from plumb.schemas_tool import generate
from tests.conftest import FIXTURES_DIR, REPO_ROOT, load_fixture

SCHEMAS_DIR = REPO_ROOT / "schemas"
SUPPORTING_DIR = SCHEMAS_DIR / "supporting"
SCENARIOS = ["accounting_evidence_preparation", "industrial_rfq_preparation", "laundry_route_preparation"]
INVALID_FIXTURES = sorted(path.name for path in (FIXTURES_DIR / "invalid").glob("*.json"))


def read_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_for(name: str) -> dict[str, Any]:
    path = SCHEMAS_DIR / f"{name}.json" if name in TOP_LEVEL_CONTRACTS else SUPPORTING_DIR / f"{name}.json"
    return read_schema(path)


def validator_for(name: str) -> Draft202012Validator:
    schema = schema_for(name)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def round_trip(model: BaseModel) -> dict[str, Any]:
    """Serialise a validated model exactly as the artifact store would."""
    return model.model_dump(mode="json")


def run_generator(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "plumb.schemas_tool.generate", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


# ---------------------------------------------------------------------------
# File inventory
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-004")
def test_exactly_17_top_level_schema_files() -> None:
    files = sorted(path.name for path in SCHEMAS_DIR.glob("*.json") if path.name != "index.json")
    assert len(files) == 17
    assert files == sorted(f"{name}.json" for name in TOP_LEVEL_CONTRACTS)
    assert not [path for path in SCHEMAS_DIR.iterdir() if path.is_dir() and path.name != "supporting"]


@pytest.mark.requirements("PL-055", "PL-057")
def test_exactly_5_supporting_schema_files() -> None:
    files = sorted(path.name for path in SUPPORTING_DIR.glob("*.json"))
    assert len(files) == 5
    assert files == sorted(f"{name}.json" for name in SUPPORTING_CONTRACTS)


@pytest.mark.requirements("PL-004")
@pytest.mark.parametrize("name", [*TOP_LEVEL_CONTRACTS, *SUPPORTING_CONTRACTS])
def test_each_schema_parses_and_declares_dialect_id_title_and_description(name: str) -> None:
    schema = schema_for(name)
    relative = f"{name}.json" if name in TOP_LEVEL_CONTRACTS else f"supporting/{name}.json"
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == f"https://plumb.example/schemas/0.2/{relative}"
    assert schema["title"] == name
    assert schema["description"].strip()
    assert "\n" not in schema["description"], "description is the first docstring line only"
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False, "StrictModel forbids unknown fields"
    Draft202012Validator.check_schema(schema)


@pytest.mark.requirements("PL-004")
@pytest.mark.parametrize("name", list(TOP_LEVEL_CONTRACTS))
def test_each_top_level_schema_pins_kind_and_the_header_fields(name: str) -> None:
    schema = schema_for(name)
    kind = schema["properties"]["kind"]
    assert kind["const"] == name
    assert kind["default"] == name
    for header_field in ("artifact_id", "tenant_id", "version", "producer", "created_at"):
        assert header_field in schema["required"], f"{name} must require {header_field}"
    assert schema["properties"]["tenant_id"]["pattern"] == "^tnt_[a-z0-9]{4,32}$"


@pytest.mark.requirements("PL-004")
def test_files_are_rendered_deterministically() -> None:
    for path in [*SCHEMAS_DIR.glob("*.json"), *SUPPORTING_DIR.glob("*.json")]:
        text = path.read_text(encoding="utf-8")
        assert text.endswith("\n") and not text.endswith("\n\n")
        document = json.loads(text)
        assert text == json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n", path.name


@pytest.mark.requirements("PL-004")
def test_index_lists_every_schema_with_path_and_digest() -> None:
    index = read_schema(SCHEMAS_DIR / "index.json")
    assert index["schema_version"] == "0.2"
    assert [entry["name"] for entry in index["top_level"]] == list(TOP_LEVEL_CONTRACTS)
    assert [entry["name"] for entry in index["supporting"]] == list(SUPPORTING_CONTRACTS)
    for entry in index["top_level"]:
        assert entry["kind"] == pinned_kind(TOP_LEVEL_CONTRACTS[entry["name"]]).value
    for entry in [*index["top_level"], *index["supporting"]]:
        path = SCHEMAS_DIR / entry["path"]
        assert path.is_file(), entry["path"]
        assert entry["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        assert read_schema(path)["$id"].endswith("/" + entry["path"])


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-004")
def test_generation_check_passes_for_the_committed_schemas() -> None:
    result = run_generator("--check")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "match" in result.stdout


@pytest.mark.requirements("PL-004")
def test_generation_check_detects_stale_missing_and_unexpected_files(tmp_path: Path) -> None:
    out = tmp_path / "schemas"
    shutil.copytree(SCHEMAS_DIR, out)
    assert run_generator("--check", "--out", str(out)).returncode == 0

    stale = out / "BuildPlan.json"
    document = read_schema(stale)
    document["description"] = "edited by hand"
    stale.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "supporting" / "AgentTask.json").unlink()
    (out / "Rogue.json").write_text("{}\n", encoding="utf-8")

    result = run_generator("--check", "--out", str(out))
    assert result.returncode == 1
    assert "stale: BuildPlan.json" in result.stdout
    assert "missing: supporting/AgentTask.json" in result.stdout
    assert "unexpected: Rogue.json" in result.stdout
    assert "index.json" not in result.stdout, "the untouched index still matches fresh generation"


@pytest.mark.requirements("PL-004")
def test_generator_writes_a_fresh_tree_identical_to_the_committed_one(tmp_path: Path) -> None:
    out = tmp_path / "fresh"
    result = run_generator("--out", str(out))
    assert result.returncode == 0, result.stdout + result.stderr
    produced = sorted(p.relative_to(out).as_posix() for p in out.rglob("*.json"))
    committed = sorted(p.relative_to(SCHEMAS_DIR).as_posix() for p in SCHEMAS_DIR.rglob("*.json"))
    assert produced == committed
    for relative in produced:
        assert (out / relative).read_bytes() == (SCHEMAS_DIR / relative).read_bytes(), relative
    assert generate.check_schemas(out) == []


# ---------------------------------------------------------------------------
# Real artifacts validate against the schema of their kind
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-005", "PL-014")
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_scenario_envelope_and_plan_fixtures_validate_against_their_schemas(scenario: str) -> None:
    envelope_raw = load_fixture(f"envelopes/{scenario}.json")
    plan_raw = load_fixture(f"plans/{scenario}.json")
    envelope_validator = validator_for("AutonomyEnvelope")
    plan_validator = validator_for("BuildPlan")

    envelope_validator.validate(envelope_raw)
    plan_validator.validate(plan_raw)

    envelope = AutonomyEnvelope.model_validate(envelope_raw)
    plan = BuildPlan.model_validate(plan_raw)
    envelope_validator.validate(round_trip(envelope))
    plan_validator.validate(round_trip(plan))
    assert envelope.kind is ArtifactKind.AUTONOMY_ENVELOPE and plan.kind is ArtifactKind.BUILD_PLAN


@pytest.mark.requirements("PL-005", "PL-014")
@pytest.mark.parametrize("fixture", INVALID_FIXTURES)
def test_malformed_plan_fixtures_are_schema_valid_so_the_checker_can_judge_them(fixture: str) -> None:
    # Fixtures in fixtures/invalid carry defects the *checker* must find; they still parse.
    document = load_fixture(f"invalid/{fixture}")
    validator_for("AutonomyEnvelope").validate(document["envelope"])
    validator_for("BuildPlan").validate(document["plan"])
    validator_for("BuildPlan").validate(round_trip(BuildPlan.model_validate(document["plan"])))


@pytest.mark.requirements("PL-008")
def test_packaged_capability_registry_entries_validate_against_capability_record_schema() -> None:
    entries = json.loads(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))["capabilities"]
    assert len(entries) >= 23
    validator = validator_for("CapabilityRecord")
    for entry in entries:
        validator.validate(entry)
        validator.validate(round_trip(CapabilityRecord.model_validate(entry)))


@pytest.mark.requirements("PL-037", "PL-040")
def test_hand_built_approval_and_action_intent_examples_validate() -> None:
    approver = {"principal_id": "approver-01", "principal_type": "HUMAN_APPROVER", "authenticated_via": "oidc:test-issuer"}
    approval = ApprovalRecord(
        artifact_id="apr-example-01",
        tenant_id="tnt_schema01",
        version=1,
        producer=approver,
        created_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        approval_id="apr-example-01",
        decision_kind="IMPLEMENT_OPERATE",
        subject_digest="sha256:" + "a" * 64,
        policy_version="1.0.0",
        approver=approver,
        authenticated_decision_ref="decision:idp/session/01",
        approved_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        expires_at=datetime(2026, 12, 1, tzinfo=timezone.utc),
        scope_tenant="tnt_schema01",
    )
    validator_for("ApprovalRecord").validate(round_trip(approval))

    slot = EffectSlot(
        tenant_id="tnt_schema01",
        case_id="case-01",
        obligation_id="obl-01",
        obligation_epoch=0,
        operation="send_reminder",
        target="recipient-01",
    )
    intent = ActionIntent(
        artifact_id="act-example-01",
        tenant_id="tnt_schema01",
        version=1,
        producer={"principal_id": "runtime-01", "principal_type": "RUNTIME_AGENT", "authenticated_via": "spiffe:runtime"},
        created_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        action_id="act-example-01",
        slot=slot,
        payload_digest="sha256:" + "b" * 64,
        expected_state_version=3,
        authority_ref="apr-example-01",
        deployment_version="rel-01",
        provider_target={"source_id": "src-mail", "provider": "mail-provider", "external_account_id": "acct-01"},
        effect_class=EffectClass.EXTERNAL_COMMUNICATION,
        idempotency_key=derive_idempotency_key("act-example-01", slot),
    )
    validator_for("ActionIntent").validate(round_trip(intent))


@pytest.mark.requirements("PL-004", "PL-005")
def test_schemas_reject_unknown_fields_and_malformed_identifiers() -> None:
    validator = validator_for("AutonomyEnvelope")
    envelope = load_fixture(f"envelopes/{SCENARIOS[0]}.json")

    with_extra = {**envelope, "unexpected_field": True}
    assert not validator.is_valid(with_extra)

    foreign_tenant = {**envelope, "tenant_id": "customer-123"}
    assert not validator.is_valid(foreign_tenant)

    wrong_kind = {**envelope, "kind": "BuildPlan"}
    assert not validator.is_valid(wrong_kind)

    missing_owner = {key: value for key, value in envelope.items() if key != "owner"}
    assert not validator.is_valid(missing_owner)

    bad_digest = {**envelope, "content_digest": "md5:abc"}
    assert not validator.is_valid(bad_digest)
    assert validator.is_valid({**envelope, "content_digest": compute_artifact_digest(AutonomyEnvelope.model_validate(envelope))})


# ---------------------------------------------------------------------------
# Kinds and registry agree
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-004")
def test_every_top_level_artifact_kind_is_a_registry_key() -> None:
    top_level_kinds = [member for member in ArtifactKind if member.value in TOP_LEVEL_CONTRACTS]
    assert len(top_level_kinds) == 17
    for kind in top_level_kinds:
        contract = TOP_LEVEL_CONTRACTS[kind.value]
        assert pinned_kind(contract) is kind
        assert schema_for(kind.value)["properties"]["kind"]["const"] == kind.value
    assert {kind.value for kind in top_level_kinds} == set(TOP_LEVEL_CONTRACTS)
