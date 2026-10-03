"""Structural tests for the proposed control-plane OpenAPI document.

Exercises PL-004 (tenant from authentication, 404 not 403), PL-055 (idempotency
keys, 202 job envelopes, payload conflicts) and PL-056 (If-Match/412, opaque
cursors with bounded page sizes) as they are expressed in ``api/openapi.yaml``,
plus the section 22 protocol shapes (error classes, event fields) and the
reference validator in ``api/validate_openapi.py``.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
OPENAPI_PATH = REPO_ROOT / "api" / "openapi.yaml"
VALIDATOR_PATH = REPO_ROOT / "api" / "validate_openapi.py"

EXPECTED_OPERATION_IDS = {
    "createEnvelope",
    "getEnvelope",
    "startInventoryJob",
    "getInventoryJob",
    "startOpportunityDiscovery",
    "listOpportunities",
    "createBuild",
    "getBuild",
    "listBuildEvents",
    "resolveBuildDependency",
    "createConnectionIntent",
    "getConnectionIntent",
    "startCollectionJob",
    "getCollectionJob",
    "startDatasetJob",
    "startTrainingJob",
    "getTrainingJob",
    "createEvaluation",
    "createRelease",
    "activateRelease",
    "pauseRelease",
    "dispatchAction",
    "reconcileAction",
    "listOutcomes",
}

LONG_RUNNING_OPERATIONS = {
    "startInventoryJob",
    "startOpportunityDiscovery",
    "createBuild",
    "resolveBuildDependency",
    "startCollectionJob",
    "startDatasetJob",
    "startTrainingJob",
    "createEvaluation",
    "activateRelease",
    "dispatchAction",
    "reconcileAction",
}
SYNCHRONOUS_CREATES = {"createEnvelope", "createConnectionIntent", "createRelease"}
IF_MATCH_OPERATIONS = {"activateRelease", "pauseRelease", "resolveBuildDependency"}
LIST_OPERATIONS = {"listOpportunities", "listBuildEvents", "listOutcomes"}

ERROR_CLASSES = [
    "AUTH_REQUIRED",
    "SCOPE_DENIED",
    "PURPOSE_DENIED",
    "POLICY_STALE",
    "STATE_CONFLICT",
    "PAYLOAD_CONFLICT",
    "BUDGET_EXCEEDED",
    "CAPABILITY_UNSUPPORTED",
    "SOURCE_STALE",
    "DATA_QUALITY_FAILED",
    "VERIFICATION_FAILED",
    "EFFECT_UNKNOWN",
    "RETRY_EXHAUSTED",
]
EVENT_FIELDS = [
    "event_id",
    "tenant_id",
    "aggregate_id",
    "aggregate_version",
    "event_type",
    "occurred_at",
    "recorded_at",
    "correlation_id",
    "causation_id",
    "schema_version",
    "payload_ref",
]
CONTRACT_SCHEMAS_EXPECTED = {
    "AutonomyEnvelope",
    "EnvironmentInventory",
    "OpportunitySpec",
    "BuildPlan",
    "CollectionSpec",
    "DatasetManifest",
    "TrainingSpec",
    "EvaluationReport",
    "ReleaseManifest",
    "ActionIntent",
    "ApprovalRecord",
    "JobEnvelope",
    "ErrorEnvelope",
    "EventEnvelope",
}
MUTATING_METHODS = {"post", "put", "patch", "delete"}


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("validate_openapi", VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def validator() -> ModuleType:
    return _load_validator()


@pytest.fixture(scope="module")
def spec() -> dict[str, Any]:
    return yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def operations(validator: ModuleType, spec: dict[str, Any]) -> dict[str, tuple[str, str, dict[str, Any]]]:
    """operationId -> (path, method, operation object)."""
    return {op["operationId"]: (path, method, op) for path, method, op in validator.iter_operations(spec)}


@pytest.fixture(scope="module")
def result(validator: ModuleType) -> dict[str, Any]:
    return validator.validate_document(OPENAPI_PATH)


def _resolve(spec: dict[str, Any], ref: str) -> dict[str, Any]:
    node: Any = spec
    for token in ref[2:].split("/"):
        node = node[token]
    return node


def _parameters(spec: dict[str, Any], path: str, operation: dict[str, Any]) -> list[dict[str, Any]]:
    """Operation parameters merged with path-level parameters, $refs resolved."""
    merged: list[dict[str, Any]] = []
    for param in list(spec["paths"][path].get("parameters", [])) + list(operation.get("parameters", [])):
        merged.append(_resolve(spec, param["$ref"]) if "$ref" in param else param)
    return merged


def _response(spec: dict[str, Any], operation: dict[str, Any], code: str) -> dict[str, Any]:
    response = operation["responses"][code]
    return _resolve(spec, response["$ref"]) if "$ref" in response else response


def _schema_ref_of(spec: dict[str, Any], response: dict[str, Any]) -> str:
    return response["content"]["application/json"]["schema"]["$ref"]


# --------------------------------------------------------------------------
# Document identity and operation inventory
# --------------------------------------------------------------------------


@pytest.mark.requirements("PL-055", "PL-056")
def test_document_identity(spec: dict[str, Any]) -> None:
    assert spec["openapi"].startswith("3.1.")
    assert spec["info"]["title"] == "Plumb Control-Plane API (proposed)"
    assert spec["info"]["version"] == "0.2.0"
    assert "bearerAuth" in spec["components"]["securitySchemes"]
    assert spec["components"]["securitySchemes"]["bearerAuth"]["scheme"] == "bearer"
    assert spec["security"] == [{"bearerAuth": []}]


@pytest.mark.requirements("PL-055", "PL-056")
def test_exactly_24_operations_with_expected_ids(
    validator: ModuleType, spec: dict[str, Any], operations: dict[str, Any]
) -> None:
    assert validator.count_operations(spec) == 24
    assert set(operations) == EXPECTED_OPERATION_IDS
    assert "revokeEnvelope" not in operations, "envelope revocation is a new version + If-Match (design §8)"


@pytest.mark.requirements("PL-004")
def test_every_path_is_tenant_scoped(spec: dict[str, Any]) -> None:
    for path in spec["paths"]:
        assert path.startswith("/v1/tenants/{tenant_id}/"), path


@pytest.mark.requirements("PL-004", "PL-056")
def test_tenant_path_parameter_is_informational_and_cross_tenant_is_404(spec: dict[str, Any], operations: dict[str, Any]) -> None:
    tenant_param = spec["components"]["parameters"]["TenantId"]
    assert tenant_param["in"] == "path" and tenant_param["required"] is True
    assert "PL-004" in tenant_param["description"]
    not_found = spec["components"]["responses"]["NotFound"]["description"]
    assert "403" in not_found and "another tenant" in not_found
    for operation_id, (_, _, op) in operations.items():
        assert "404" in op["responses"], f"{operation_id} lacks a 404 response"
        assert "PL-004" in op["description"], f"{operation_id} does not cite PL-004"


@pytest.mark.requirements("PL-055", "PL-056")
def test_every_operation_has_summary_description_tags_and_error_response(spec: dict[str, Any], operations: dict[str, Any]) -> None:
    declared_tags = {tag["name"] for tag in spec["tags"]}
    for operation_id, (_, _, op) in operations.items():
        assert op.get("summary"), f"{operation_id} lacks a summary"
        assert op.get("description"), f"{operation_id} lacks a description"
        assert op.get("tags") and set(op["tags"]) <= declared_tags, f"{operation_id} has undeclared tags"
        error_codes = [code for code in op["responses"] if code.startswith("4")]
        assert error_codes, f"{operation_id} has no 4xx response"
        for code in error_codes:
            assert _schema_ref_of(spec, _response(spec, op, code)) == "#/components/schemas/ErrorEnvelope"
        assert "401" in op["responses"] and "403" in op["responses"]


# --------------------------------------------------------------------------
# PL-055: idempotency and 202 job envelopes
# --------------------------------------------------------------------------


@pytest.mark.requirements("PL-055")
def test_every_mutating_operation_requires_idempotency_key(spec: dict[str, Any], operations: dict[str, Any]) -> None:
    mutating = {oid for oid, (_, method, _) in operations.items() if method in MUTATING_METHODS}
    assert mutating == LONG_RUNNING_OPERATIONS | SYNCHRONOUS_CREATES | {"pauseRelease"}
    for operation_id in mutating:
        path, _, op = operations[operation_id]
        headers = [p for p in _parameters(spec, path, op) if p["in"] == "header" and p["name"] == "Idempotency-Key"]
        assert len(headers) == 1, f"{operation_id} lacks an Idempotency-Key header"
        assert headers[0]["required"] is True
        assert "PL-055" in op["description"], f"{operation_id} does not cite PL-055"
        assert "409" in op["responses"], f"{operation_id} lacks the 409 payload-conflict response"
        conflict = _response(spec, op, "409")
        assert "PAYLOAD_CONFLICT" in conflict["description"]
        assert _schema_ref_of(spec, conflict) == "#/components/schemas/ErrorEnvelope"


@pytest.mark.requirements("PL-055")
def test_read_operations_do_not_take_idempotency_key(spec: dict[str, Any], operations: dict[str, Any]) -> None:
    for operation_id, (path, method, op) in operations.items():
        if method == "get":
            names = {p["name"] for p in _parameters(spec, path, op)}
            assert "Idempotency-Key" not in names, operation_id
            assert "409" not in op["responses"], operation_id


@pytest.mark.requirements("PL-055")
def test_long_running_operations_return_202_job_envelope(spec: dict[str, Any], operations: dict[str, Any]) -> None:
    for operation_id in LONG_RUNNING_OPERATIONS:
        _, _, op = operations[operation_id]
        assert "202" in op["responses"], f"{operation_id} must return 202"
        assert "201" not in op["responses"] and "200" not in op["responses"], operation_id
        assert _schema_ref_of(spec, _response(spec, op, "202")) == "#/components/schemas/JobEnvelope"


@pytest.mark.requirements("PL-055")
def test_synchronous_creates_return_201_not_202(spec: dict[str, Any], operations: dict[str, Any]) -> None:
    for operation_id in SYNCHRONOUS_CREATES:
        _, _, op = operations[operation_id]
        assert "201" in op["responses"], operation_id
        assert "202" not in op["responses"], operation_id
        assert _schema_ref_of(spec, _response(spec, op, "201")) != "#/components/schemas/JobEnvelope"


@pytest.mark.requirements("PL-055")
def test_job_envelope_shape(spec: dict[str, Any]) -> None:
    from plumb.contracts.api import JobEnvelope, JobStatus

    job = spec["components"]["schemas"]["JobEnvelope"]
    assert job["x-plumb-contract"] == "JobEnvelope"
    # The component mirrors the package contract field for field (x-plumb-contract).
    assert set(job["properties"]) == set(JobEnvelope.model_fields)
    assert set(job["required"]) == {name for name, field in JobEnvelope.model_fields.items() if field.is_required()}
    assert {"job_id", "tenant_id", "status", "idempotency_key", "result_ref", "error"} <= set(job["properties"])
    assert job["additionalProperties"] is False
    status_enum = spec["components"]["schemas"]["JobStatus"]["enum"]
    assert status_enum == [status.value for status in JobStatus]
    assert {"RUNNING", "SUCCEEDED", "FAILED", "WAITING"} <= set(status_enum)


# --------------------------------------------------------------------------
# PL-056: If-Match / 412 and cursor pagination
# --------------------------------------------------------------------------


@pytest.mark.requirements("PL-056")
def test_if_match_operations_define_412(spec: dict[str, Any], operations: dict[str, Any]) -> None:
    for operation_id in IF_MATCH_OPERATIONS:
        path, _, op = operations[operation_id]
        if_match = [p for p in _parameters(spec, path, op) if p["in"] == "header" and p["name"] == "If-Match"]
        assert len(if_match) == 1 and if_match[0]["required"] is True, operation_id
        assert "412" in op["responses"], f"{operation_id} lacks 412"
        precondition = _response(spec, op, "412")
        assert _schema_ref_of(spec, precondition) == "#/components/schemas/ErrorEnvelope"
        assert "PL-056" in op["description"]


@pytest.mark.requirements("PL-056")
def test_every_operation_with_if_match_has_412_and_vice_versa(spec: dict[str, Any], operations: dict[str, Any]) -> None:
    for operation_id, (path, _, op) in operations.items():
        takes_if_match = any(p["name"] == "If-Match" for p in _parameters(spec, path, op))
        assert takes_if_match == ("412" in op["responses"]), operation_id


@pytest.mark.requirements("PL-056")
def test_list_operations_use_opaque_cursor_and_bounded_limit(spec: dict[str, Any], operations: dict[str, Any]) -> None:
    for operation_id in LIST_OPERATIONS:
        path, method, op = operations[operation_id]
        assert method == "get"
        params = {p["name"]: p for p in _parameters(spec, path, op) if p["in"] == "query"}
        assert params["cursor"]["schema"]["type"] == "string", operation_id
        assert params["cursor"]["required"] is False
        limit = params["limit"]["schema"]
        assert limit["type"] == "integer" and limit["maximum"] == 200 and limit["minimum"] >= 1, operation_id
        page_schema = _resolve(spec, _schema_ref_of(spec, _response(spec, op, "200")))
        assert set(page_schema["required"]) == {"items", "next_cursor"}
        assert page_schema["properties"]["items"]["type"] == "array"
        assert "null" in page_schema["properties"]["next_cursor"]["type"], "last page must carry next_cursor: null"
        assert "PL-056" in op["description"]


@pytest.mark.requirements("PL-056")
def test_non_list_operations_do_not_paginate(spec: dict[str, Any], operations: dict[str, Any]) -> None:
    for operation_id, (path, _, op) in operations.items():
        if operation_id in LIST_OPERATIONS:
            continue
        names = {p["name"] for p in _parameters(spec, path, op) if p["in"] == "query"}
        assert not names & {"cursor", "limit"}, operation_id


# --------------------------------------------------------------------------
# Section 22 shapes
# --------------------------------------------------------------------------


@pytest.mark.requirements("PL-055", "PL-056")
def test_error_envelope_has_the_13_error_classes_and_operator_fields(spec: dict[str, Any]) -> None:
    error_class = spec["components"]["schemas"]["ErrorClass"]["enum"]
    assert error_class == ERROR_CLASSES
    assert len(set(error_class)) == 13
    envelope = spec["components"]["schemas"]["ErrorEnvelope"]
    assert envelope["x-plumb-contract"] == "ErrorEnvelope"
    assert envelope["properties"]["error_class"]["$ref"] == "#/components/schemas/ErrorClass"
    assert {"retryable", "dependency_id", "operator_action", "correlation_id", "message"} <= set(envelope["properties"])
    assert {"error_class", "message", "retryable", "correlation_id"} <= set(envelope["required"])


@pytest.mark.requirements("PL-057", "PL-060")
def test_event_envelope_has_the_11_spec_fields(spec: dict[str, Any]) -> None:
    event = spec["components"]["schemas"]["EventEnvelope"]
    assert event["x-plumb-contract"] == "EventEnvelope"
    # causation_id is the one optional field of the eleven (a root event has no cause), as in the contract.
    assert list(event["required"]) == [name for name in EVENT_FIELDS if name != "causation_id"]
    assert list(event["properties"]) == EVENT_FIELDS
    assert event["additionalProperties"] is False


# --------------------------------------------------------------------------
# Component parity with the Pydantic contracts (x-plumb-contract)
# --------------------------------------------------------------------------


def _flatten_component(spec: dict[str, Any], component: dict[str, Any]) -> tuple[dict[str, Any], set[str]]:
    """Properties and required set of a component, with ``allOf`` members (ArtifactHeader) merged in."""
    properties: dict[str, Any] = {}
    required: set[str] = set()
    for member in component.get("allOf", []):
        resolved = _resolve(spec, member["$ref"]) if "$ref" in member else member
        nested_properties, nested_required = _flatten_component(spec, resolved)
        properties.update(nested_properties)
        required |= nested_required
    properties.update(component.get("properties", {}))
    required |= set(component.get("required", []))
    return properties, required


def _leaf(spec: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """Resolve a property schema to its constraint-bearing leaf (through $ref and oneOf-with-null)."""
    if "$ref" in schema:
        resolved = dict(_resolve(spec, schema["$ref"]))
        resolved.pop("description", None)
        return resolved
    if "oneOf" in schema:
        branches = [branch for branch in schema["oneOf"] if branch.get("type") != "null"]
        if len(branches) == 1:
            return _leaf(spec, branches[0])
    return schema


def _pydantic_leaf(definitions: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    if "$ref" in schema:
        return definitions[schema["$ref"].rsplit("/", 1)[-1]]
    if "anyOf" in schema:
        branches = [branch for branch in schema["anyOf"] if branch.get("type") != "null"]
        if len(branches) == 1:
            return _pydantic_leaf(definitions, branches[0])
    return schema


CONSTRAINT_KEYS = ("minLength", "maxLength", "pattern", "minimum", "maximum", "minItems", "maxItems", "enum")


@pytest.mark.requirements("PL-055", "PL-046", "PL-037")
@pytest.mark.parametrize("name", sorted(CONTRACT_SCHEMAS_EXPECTED))
def test_annotated_component_mirrors_its_contract(spec: dict[str, Any], name: str) -> None:
    """Every ``x-plumb-contract`` component has the contract's properties, required set and leaf constraints."""
    from plumb.contracts import SUPPORTING_CONTRACTS, TOP_LEVEL_CONTRACTS

    model = {**TOP_LEVEL_CONTRACTS, **SUPPORTING_CONTRACTS}[name]
    component = spec["components"]["schemas"][name]
    assert component["x-plumb-contract"] == name
    properties, required = _flatten_component(spec, component)
    assert set(properties) == set(model.model_fields), name
    assert required == {field_name for field_name, field in model.model_fields.items() if field.is_required()}, name

    generated = model.model_json_schema(mode="validation")
    definitions = generated.get("$defs", {})
    drift: list[str] = []
    for field_name, pydantic_schema in generated["properties"].items():
        expected = _pydantic_leaf(definitions, pydantic_schema)
        actual = _leaf(spec, properties[field_name])
        for key in CONSTRAINT_KEYS:
            if key in expected and actual.get(key) != expected[key]:
                drift.append(f"{name}.{field_name}: {key} openapi={actual.get(key)!r} contract={expected[key]!r}")
            if key in actual and key not in expected and key in ("minItems", "pattern", "minimum"):
                drift.append(f"{name}.{field_name}: {key}={actual[key]!r} is stricter than the contract")
    assert drift == [], "\n".join(drift)


@pytest.mark.requirements("PL-057")
def test_lifecycle_enums_match_section_23(spec: dict[str, Any]) -> None:
    schemas = spec["components"]["schemas"]
    assert schemas["BuildState"]["enum"] == ["DRAFT", "VALIDATED", "RUNNING", "WAITING_AUTH", "WAITING_INPUT", "VERIFYING", "VERIFIED", "FAILED", "CANCELLED"]
    assert schemas["BuildStepState"]["enum"] == ["PENDING", "READY", "RUNNING", "VERIFYING", "VERIFIED", "FAILED", "BLOCKED", "CANCELLED"]
    assert schemas["CollectorState"]["enum"] == ["PLANNED", "SHADOW", "BACKFILLING", "RECONCILING", "ACTIVE", "DEGRADED", "PAUSED", "RETIRED"]
    assert schemas["DatasetState"]["enum"] == ["PROPOSED", "MATERIALIZING", "QUARANTINED", "VERIFIED", "SUPERSEDED", "UNAVAILABLE"]
    assert schemas["TrainingState"]["enum"] == ["PLANNED", "SUBMITTED", "RUNNING", "CANDIDATE", "FAILED", "CANCELLED"]
    assert schemas["ReleaseState"]["enum"] == ["CANDIDATE", "VERIFIED", "SHADOW", "CANARY", "ACTIVE", "PAUSED", "ROLLED_BACK", "RETIRED"]
    assert schemas["EffectState"]["enum"] == ["RESERVED", "DISPATCHED", "UNKNOWN", "CONFIRMED", "FAILED_FINAL", "COMPENSATED"]
    assert schemas["BuildStatus"]["properties"]["state"]["$ref"] == "#/components/schemas/BuildState"
    assert schemas["BuildStepStatus"]["properties"]["state"]["$ref"] == "#/components/schemas/BuildStepState"
    assert schemas["BuildStatus"]["properties"]["dependencies"]["items"]["$ref"] == "#/components/schemas/DependencyRecord"


@pytest.mark.requirements("PL-053", "PL-005")
def test_shared_enums_match_common_vocabulary(spec: dict[str, Any]) -> None:
    from plumb.contracts.common import DataPurpose, EffectClass, HumanEffortCategory, PrincipalType

    schemas = spec["components"]["schemas"]
    assert schemas["EffectClass"]["enum"] == [e.value for e in EffectClass]
    assert schemas["DataPurpose"]["enum"] == [e.value for e in DataPurpose]
    assert schemas["PrincipalType"]["enum"] == [e.value for e in PrincipalType]
    assert schemas["HumanEffortCategory"]["enum"] == [e.value for e in HumanEffortCategory]
    money = schemas["Money"]
    assert money["properties"]["minor_units"]["type"] == "integer"
    assert money["properties"]["currency"]["type"] == "string"
    assert set(money["required"]) == {"minor_units", "currency"}


@pytest.mark.requirements("PL-059", "PL-003")
def test_outcome_observation_shape(spec: dict[str, Any]) -> None:
    outcome = spec["components"]["schemas"]["OutcomeObservation"]["properties"]
    assert {"case_id", "release_id", "model_calls", "completed", "correct", "realized_value", "review_minutes", "human_effort_category"} <= set(outcome)
    assert outcome["realized_value"]["oneOf"][0]["$ref"] == "#/components/schemas/Money"
    assert outcome["human_effort_category"]["oneOf"][0]["$ref"] == "#/components/schemas/HumanEffortCategory"


@pytest.mark.requirements("PL-037", "PL-038")
def test_action_schemas_carry_slot_payload_digest_and_reconciliation_evidence(spec: dict[str, Any]) -> None:
    schemas = spec["components"]["schemas"]
    intent = schemas["ActionIntent"]["allOf"][1]
    assert {"action_id", "slot", "payload_digest", "expected_state_version", "authority_ref", "deployment_version", "provider_target", "effect_class", "idempotency_key"} <= set(intent["required"])
    assert set(schemas["EffectSlot"]["required"]) == {"tenant_id", "case_id", "obligation_id", "obligation_epoch", "operation", "target"}
    reconciliation = schemas["ReconciliationRequest"]
    assert reconciliation["properties"]["outcome"]["enum"] == ["CONFIRMED", "FAILED_FINAL", "STILL_UNKNOWN"]
    assert reconciliation["properties"]["receipt"]["oneOf"][0]["$ref"] == "#/components/schemas/ActionReceipt"
    assert "provider_request_id" in schemas["ActionReceipt"]["required"]


@pytest.mark.requirements("PL-006", "PL-054")
def test_connection_intent_exposes_a_consent_reference_not_a_credential(spec: dict[str, Any]) -> None:
    intent = spec["components"]["schemas"]["ConnectionIntent"]
    assert {"provider", "requested_scopes", "consent_url_ref", "state"} <= set(intent["required"])
    assert intent["properties"]["consent_url_ref"]["$ref"] == "#/components/schemas/NonSecretRef"
    assert not {"access_token", "refresh_token", "client_secret", "password"} & set(intent["properties"])


# --------------------------------------------------------------------------
# Reference validation (section 22 "JSON validity and local schema references")
# --------------------------------------------------------------------------


@pytest.mark.requirements("PL-055", "PL-056")
def test_validator_reports_valid_document(result: dict[str, Any]) -> None:
    assert result["errors"] == []
    assert result["spec_valid"] is True
    assert result["operations"] == 24
    assert result["unresolved_refs"] == []
    assert result["resolved_refs"] > 100
    assert sorted(EXPECTED_OPERATION_IDS) == result["operation_ids"]


@pytest.mark.requirements("PL-055")
def test_all_refs_are_local_and_resolve(validator: ModuleType, spec: dict[str, Any]) -> None:
    refs = validator.collect_refs(spec)
    assert refs
    for location, ref in refs:
        assert ref.startswith("#/components/"), f"{ref} at {location} is not a local component reference"
        assert validator.resolve_local_ref(spec, ref), f"{ref} at {location} does not resolve"


@pytest.mark.requirements("PL-055")
def test_every_contract_annotation_is_an_allowed_contract(validator: ModuleType, spec: dict[str, Any], result: dict[str, Any]) -> None:
    annotated = {
        name: schema["x-plumb-contract"]
        for name, schema in spec["components"]["schemas"].items()
        if "x-plumb-contract" in schema
    }
    assert set(annotated) == CONTRACT_SCHEMAS_EXPECTED
    for name, contract in annotated.items():
        assert contract == name
        assert contract in validator.ALLOWED_CONTRACTS
    assert len(validator.TOP_LEVEL_CONTRACTS) == 17 and len(validator.SUPPORTING_CONTRACTS) == 5
    assert set(result["contracts_referenced"]) >= CONTRACT_SCHEMAS_EXPECTED
    for name in ("BuildStatus", "ConnectionIntent", "ActionReceipt", "ReconciliationRequest", "OutcomeObservation"):
        assert "x-plumb-contract" not in spec["components"]["schemas"][name], f"{name} is API-level, not a package contract"


@pytest.mark.requirements("PL-055")
def test_result_contract_annotations_name_existing_contract_schemas(validator: ModuleType, spec: dict[str, Any], operations: dict[str, Any]) -> None:
    for operation_id in LONG_RUNNING_OPERATIONS:
        _, _, op = operations[operation_id]
        contract = op["x-plumb-result-contract"]
        assert contract in validator.ALLOWED_CONTRACTS, operation_id
        assert contract in spec["components"]["schemas"], operation_id


@pytest.mark.requirements("PL-055")
def test_validator_rejects_unresolved_and_non_local_refs(validator: ModuleType, tmp_path: Path, spec: dict[str, Any]) -> None:
    broken = json.loads(json.dumps(spec))
    broken["paths"]["/v1/tenants/{tenant_id}/outcomes"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"] = "#/components/schemas/DoesNotExist"
    broken["components"]["schemas"]["Money"]["properties"]["currency"] = {"$ref": "common.json#/CurrencyCode"}
    path = tmp_path / "broken.yaml"
    path.write_text(yaml.safe_dump(broken), encoding="utf-8")
    result = validator.validate_document(path)
    assert result["spec_valid"] is False
    assert {entry["ref"] for entry in result["unresolved_refs"]} == {"#/components/schemas/DoesNotExist", "common.json#/CurrencyCode"}
    assert any("does not resolve" in error for error in result["errors"])
    assert any("non-local" in error for error in result["errors"])
    assert any("skipped" in error for error in result["errors"]), "the library validator must not run (it would fetch non-local refs)"


@pytest.mark.requirements("PL-055")
def test_validator_rejects_unknown_contract_annotation_and_wrong_operation_count(validator: ModuleType, tmp_path: Path, spec: dict[str, Any]) -> None:
    broken = json.loads(json.dumps(spec))
    broken["components"]["schemas"]["Money"]["x-plumb-contract"] = "MoneyContract"
    del broken["paths"]["/v1/tenants/{tenant_id}/outcomes"]
    path = tmp_path / "broken.yaml"
    path.write_text(yaml.safe_dump(broken), encoding="utf-8")
    result = validator.validate_document(path)
    assert any("MoneyContract" in error for error in result["errors"])
    assert result["operations"] == 23
    assert any("expected 24 operations, found 23" in error for error in result["errors"])
    assert "MoneyContract" not in result["contracts_referenced"]


@pytest.mark.requirements("PL-055")
def test_validator_rejects_wrong_openapi_version_and_integer_response_codes(validator: ModuleType, tmp_path: Path) -> None:
    document = {
        "openapi": "3.0.3",
        "info": {"title": "x", "version": "0"},
        "paths": {"/v1/tenants/{tenant_id}/ping": {"get": {"operationId": "ping", "responses": {200: {"description": "ok"}}}}},
    }
    path = tmp_path / "old.yaml"
    path.write_text(yaml.safe_dump(document), encoding="utf-8")
    result = validator.validate_document(path)
    assert any("3.1.x" in error for error in result["errors"])
    assert any("response code key must be a string" in error for error in result["errors"])


@pytest.mark.requirements("PL-055")
def test_validator_reports_unreadable_document(validator: ModuleType, tmp_path: Path) -> None:
    missing = validator.validate_document(tmp_path / "missing.yaml")
    assert missing["spec_valid"] is False and missing["operations"] == 0
    assert any("cannot read" in error for error in missing["errors"])
    scalar = tmp_path / "scalar.yaml"
    scalar.write_text("just a string\n", encoding="utf-8")
    assert any("mapping" in error for error in validator.validate_document(scalar)["errors"])


@pytest.mark.requirements("PL-055", "PL-056")
def test_cli_exit_code_zero_and_json_summary() -> None:
    completed = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(OPENAPI_PATH), "--json"],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["operations"] == 24 and payload["spec_valid"] is True and payload["errors"] == []


@pytest.mark.requirements("PL-055")
def test_cli_exit_code_one_on_broken_document(tmp_path: Path, spec: dict[str, Any]) -> None:
    broken = json.loads(json.dumps(spec))
    del broken["components"]["schemas"]["JobEnvelope"]
    path = tmp_path / "broken.yaml"
    path.write_text(yaml.safe_dump(broken), encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(path)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )
    assert completed.returncode == 1
    assert "JobEnvelope" in completed.stdout
