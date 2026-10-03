"""Structural validator for the proposed Plumb control-plane OpenAPI document.

Specification section 22 states that the OpenAPI document is a *proposed
interface, not a running endpoint* and that its reference validation checks
JSON validity and local schema references only. This module implements exactly
that reference validation:

* the document parses and declares OpenAPI ``3.1.x``;
* it exposes the fixed number of operations of the reference package (24);
* every ``$ref`` is local (``#/...``) and resolves inside the document;
* every ``x-plumb-contract`` annotation names one of the 17 top-level or 5
  supporting package contracts, and every ``x-plumb-result-contract`` names a
  schema that exists in the document and is such a contract;
* response-code keys are strings (a YAML ``202:`` would silently become an int);
* ``openapi_spec_validator`` accepts the document.

Requirements exercised by the document this validates: PL-004 (tenant from
authentication), PL-055 (idempotency, 202 jobs), PL-056 (If-Match/412, opaque
cursors). Authentication, serialization compatibility and complete OpenAPI
conformance need implementation-time tests and are out of scope here.

Usage::

    python3 api/validate_openapi.py [api/openapi.yaml] [--json]

The process exits ``1`` when the result carries any error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from openapi_spec_validator import validate as _validate_spec
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError

DEFAULT_DOCUMENT = Path(__file__).resolve().parent / "openapi.yaml"

EXPECTED_OPERATIONS = 24
"""Operation count fixed by the reference package design (design §8)."""

HTTP_METHODS: tuple[str, ...] = ("get", "put", "post", "delete", "options", "head", "patch", "trace")

TOP_LEVEL_CONTRACTS: tuple[str, ...] = (
    "AutonomyEnvelope",
    "CapabilityRecord",
    "EnvironmentInventory",
    "EvidencePacket",
    "OpportunitySpec",
    "BuildPlan",
    "IntegrationSpec",
    "CollectionSpec",
    "DatasetManifest",
    "TrainingSpec",
    "WorkflowSpec",
    "EvaluationReport",
    "InfrastructurePlan",
    "ReleaseManifest",
    "ActionIntent",
    "ApprovalRecord",
    "VerificationAttestation",
)
"""The 17 top-level contracts of design §3, in table order."""

SUPPORTING_CONTRACTS: tuple[str, ...] = ("JobEnvelope", "ErrorEnvelope", "EventEnvelope", "AgentTask", "StepResult")
"""Supporting contracts (design §3, Appendix A)."""

ALLOWED_CONTRACTS: frozenset[str] = frozenset(TOP_LEVEL_CONTRACTS) | frozenset(SUPPORTING_CONTRACTS)

CONTRACT_EXTENSION = "x-plumb-contract"
RESULT_CONTRACT_EXTENSION = "x-plumb-result-contract"


class DocumentLoadError(ValueError):
    """The document could not be read or is not a YAML/JSON mapping."""


def load_document(path: str | Path) -> dict[str, Any]:
    """Parse the OpenAPI document (YAML is a superset of JSON) into a mapping."""
    document_path = Path(path)
    try:
        text = document_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DocumentLoadError(f"cannot read {document_path}: {exc}") from exc
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise DocumentLoadError(f"{document_path} is not valid YAML/JSON: {exc}") from exc
    if not isinstance(loaded, dict):
        raise DocumentLoadError(f"{document_path} must contain a mapping at the top level")
    return loaded


def iter_operations(spec: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    """Return ``(path, method, operation)`` for every HTTP method under ``paths``."""
    operations: list[tuple[str, str, dict[str, Any]]] = []
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        return operations
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        for method in HTTP_METHODS:
            operation = item.get(method)
            if isinstance(operation, dict):
                operations.append((str(path), method, operation))
    return operations


def count_operations(spec: dict[str, Any]) -> int:
    return len(iter_operations(spec))


def collect_refs(node: Any, location: str = "#") -> list[tuple[str, str]]:
    """Collect every ``$ref`` string in the document as ``(location, ref)`` pairs."""
    found: list[tuple[str, str]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            child_location = f"{location}/{_escape_pointer(str(key))}"
            if key == "$ref" and isinstance(value, str):
                found.append((child_location, value))
            else:
                found.extend(collect_refs(value, child_location))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(collect_refs(value, f"{location}/{index}"))
    return found


def resolve_local_ref(spec: dict[str, Any], ref: str) -> bool:
    """True when ``ref`` is a local JSON pointer (``#/a/b``) that exists in ``spec``."""
    if not ref.startswith("#/"):
        return False
    node: Any = spec
    for raw_token in ref[2:].split("/"):
        token = _unescape_pointer(raw_token)
        if isinstance(node, dict):
            if token not in node:
                return False
            node = node[token]
        elif isinstance(node, list):
            if not token.isdigit() or int(token) >= len(node):
                return False
            node = node[int(token)]
        else:
            return False
    return True


def collect_extension_values(node: Any, extension: str, location: str = "#") -> list[tuple[str, Any]]:
    """Collect ``(location, value)`` for every occurrence of an ``x-`` extension key."""
    found: list[tuple[str, Any]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            child_location = f"{location}/{_escape_pointer(str(key))}"
            if key == extension:
                found.append((child_location, value))
            else:
                found.extend(collect_extension_values(value, extension, child_location))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(collect_extension_values(value, extension, f"{location}/{index}"))
    return found


def non_string_response_codes(spec: dict[str, Any]) -> list[str]:
    """Locations of response-code keys that are not strings (a YAML ``202:`` parses as int)."""
    offenders: list[str] = []
    for path, method, operation in iter_operations(spec):
        responses = operation.get("responses")
        if not isinstance(responses, dict):
            continue
        for code in responses:
            if not isinstance(code, str):
                offenders.append(f"{path} {method} responses/{code!r}")
    return offenders


def validate_document(path: str | Path = DEFAULT_DOCUMENT) -> dict[str, Any]:
    """Run the reference validation and return a JSON-serialisable summary.

    Keys: ``operations``, ``operation_ids``, ``resolved_refs``, ``unresolved_refs``,
    ``contracts_referenced``, ``spec_valid``, ``errors``, ``openapi_version``.
    ``errors`` is empty iff the document passes every check.
    """
    errors: list[str] = []
    try:
        spec = load_document(path)
    except DocumentLoadError as exc:
        return {
            "operations": 0,
            "operation_ids": [],
            "resolved_refs": 0,
            "unresolved_refs": [],
            "contracts_referenced": [],
            "spec_valid": False,
            "errors": [str(exc)],
            "openapi_version": None,
        }

    openapi_version = spec.get("openapi")
    if not isinstance(openapi_version, str) or not openapi_version.startswith("3.1."):
        errors.append(f"openapi version must be 3.1.x, found {openapi_version!r}")

    operations = iter_operations(spec)
    operation_ids: list[str] = []
    for path, method, operation in operations:
        operation_id = operation.get("operationId")
        if not isinstance(operation_id, str) or not operation_id:
            errors.append(f"{path} {method}: operation has no operationId")
            continue
        if operation_id in operation_ids:
            errors.append(f"duplicate operationId {operation_id!r}")
        operation_ids.append(operation_id)
    if len(operations) != EXPECTED_OPERATIONS:
        errors.append(f"expected {EXPECTED_OPERATIONS} operations, found {len(operations)}")

    for offender in non_string_response_codes(spec):
        errors.append(f"response code key must be a string: {offender}")

    refs = collect_refs(spec)
    unresolved: list[dict[str, str]] = []
    resolved_count = 0
    for location, ref in refs:
        if resolve_local_ref(spec, ref):
            resolved_count += 1
        else:
            unresolved.append({"at": location, "ref": ref})
            reason = "non-local" if not ref.startswith("#/") else "does not resolve"
            errors.append(f"$ref {ref!r} at {location} {reason}")

    schemas = spec.get("components", {}).get("schemas", {}) if isinstance(spec.get("components"), dict) else {}
    contracts: set[str] = set()
    for location, value in collect_extension_values(spec, CONTRACT_EXTENSION):
        if not isinstance(value, str) or value not in ALLOWED_CONTRACTS:
            errors.append(f"{CONTRACT_EXTENSION} {value!r} at {location} is not a package contract")
            continue
        contracts.add(value)
    for location, value in collect_extension_values(spec, RESULT_CONTRACT_EXTENSION):
        if not isinstance(value, str) or value not in ALLOWED_CONTRACTS:
            errors.append(f"{RESULT_CONTRACT_EXTENSION} {value!r} at {location} is not a package contract")
        elif value not in schemas:
            errors.append(f"{RESULT_CONTRACT_EXTENSION} {value!r} at {location} has no schema in components")
        else:
            contracts.add(value)

    spec_valid = False
    if errors:
        # The library validator resolves references itself and would try to fetch
        # a non-local one over the network; it also fails on int response keys.
        # Run it only on a document that already passes the local checks.
        errors.append("openapi_spec_validator: skipped because local checks failed")
    else:
        try:
            _validate_spec(spec)
            spec_valid = True
        except OpenAPIValidationError as exc:
            errors.append(f"openapi_spec_validator: {exc.message}")
        except Exception as exc:  # noqa: BLE001 - the library surfaces resolver errors of many types
            errors.append(f"openapi_spec_validator: {type(exc).__name__}: {exc}")

    return {
        "operations": len(operations),
        "operation_ids": sorted(operation_ids),
        "resolved_refs": resolved_count,
        "unresolved_refs": unresolved,
        "contracts_referenced": sorted(contracts),
        "spec_valid": spec_valid,
        "errors": errors,
        "openapi_version": openapi_version,
    }


def _escape_pointer(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def _unescape_pointer(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def _render_text(result: dict[str, Any]) -> str:
    lines = [
        f"openapi version : {result['openapi_version']}",
        f"operations      : {result['operations']} (expected {EXPECTED_OPERATIONS})",
        f"resolved $refs  : {result['resolved_refs']}",
        f"unresolved $refs: {len(result['unresolved_refs'])}",
        f"contracts       : {', '.join(result['contracts_referenced']) or '-'}",
        f"spec_valid      : {result['spec_valid']}",
    ]
    if result["errors"]:
        lines.append("errors:")
        lines.extend(f"  - {error}" for error in result["errors"])
    else:
        lines.append("errors: none")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the proposed Plumb OpenAPI document (section 22).")
    parser.add_argument("document", nargs="?", default=str(DEFAULT_DOCUMENT), help="Path to openapi.yaml")
    parser.add_argument("--json", action="store_true", help="Print the result as JSON instead of text")
    args = parser.parse_args(argv)

    result = validate_document(args.document)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(_render_text(result))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
