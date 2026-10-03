"""The one secret heuristic of the package and the fields it protects (PL-054, design section 2).

``plumb.contracts.common.reject_secret_like`` is the only secret heuristic; the
module-level names that used to carry their own copies (inventory, approval,
training, capability, effect) are aliases of it. Every ``*_ref`` / ``*_refs``
string field of every contract carries the validator, as do the authentication
and authority fields that the review found unprotected, and the error envelope
screens both of its operator-facing texts.
"""

from __future__ import annotations

import typing
from datetime import datetime, timezone
from typing import Any, get_args, get_origin

import pytest
from pydantic import AfterValidator, BaseModel, TypeAdapter, ValidationError

from plumb.contracts import SUPPORTING_CONTRACTS, TOP_LEVEL_CONTRACTS
from plumb.contracts import approval, capability, common, effect, inventory, training
from plumb.contracts.api import ErrorEnvelope, JobEnvelope, JobStatus
from plumb.contracts.common import (
    ErrorClass,
    NonSecretIdentifier,
    NonSecretRef,
    NonSecretText,
    Principal,
    PrincipalType,
    StorageRef,
    reject_secret_like,
)
from plumb.contracts.training import DataHandling

SECRET_PROBES: dict[str, str] = {
    "password=": "password=hunter2",
    "token=": "token=abc",
    "token:": "token:abc",
    "bare word secret": "client-secret-abc",
    "aws access key id": "AKIAABCDEFGHIJKLMNOP",
    "mixed base64 run": "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8S9t0U1v2",
    "uniform-case base64 run": "A" * 48,
    "url-safe base64 run": "Ab1_Cd2-Ef3_Gh4-Ij5_Kl6-Mn7_Op8-Qr9_St0-",
    "vault prefix + mixed run": "vault:QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVowMTIzNDU2Nzg5",
    "lower-case hex key": "0123456789abcdef" * 4,
    "pem header": "BEGIN PRIVATE KEY",
    "bearer jwt": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ4In0.sig",
    "jwt alone": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ4In0.sig",
}

REFERENCE_SHAPED: tuple[str, ...] = (
    "probe:platform/nango-management/integration.create_and_authorize/2026-09-15",
    "registry://tenant-synthetic/models/invoice-class",
    "cred://training/provider-01",
    "idp-event:demo/decision/4711",
    "oidc:synthetic-tenant-idp",
    "sha256:" + "ab" * 32,
    "artifact:" + "sha256:" + "cd" * 32,
    "lock:stacks/demo/collector",
)

HELPERS = {
    "common": common.reject_secret_like,
    "inventory": inventory.reject_secret_like,
    "approval": approval.reject_secret_like,
    "training": training.reject_secret_like,
    "capability": capability.reject_secret_like,
    "effect": effect.reject_secret_marker,
}


def _carries_secret_validator(annotation: Any, metadata: list[Any] = ()) -> bool:
    """True when the field (annotation plus the metadata pydantic lifted off a top-level Annotated) is guarded."""
    if any(isinstance(extra, AfterValidator) and extra.func is reject_secret_like for extra in metadata):
        return True
    origin = get_origin(annotation)
    if origin is typing.Annotated:
        base, *extras = get_args(annotation)
        if any(isinstance(extra, AfterValidator) and extra.func is reject_secret_like for extra in extras):
            return True
        return _carries_secret_validator(base)
    if origin is not None:
        return any(_carries_secret_validator(arg) for arg in get_args(annotation) if arg is not type(None))
    return False


def _is_string_like(annotation: Any) -> bool:
    origin = get_origin(annotation)
    if origin is typing.Annotated:
        return _is_string_like(get_args(annotation)[0])
    if origin is not None:
        return any(_is_string_like(arg) for arg in get_args(annotation) if arg is not type(None))
    return annotation is str


def _walk_models(models: list[type[BaseModel]]) -> list[type[BaseModel]]:
    """Every model reachable from ``models`` through field annotations, once each."""
    seen: dict[type[BaseModel], None] = {}
    queue = list(models)
    while queue:
        model = queue.pop()
        if model in seen:
            continue
        seen[model] = None
        for field in model.model_fields.values():
            queue.extend(_nested_models(field.annotation))
    return list(seen)


def _nested_models(annotation: Any) -> list[type[BaseModel]]:
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return [annotation]
    found: list[type[BaseModel]] = []
    for arg in get_args(annotation):
        found.extend(_nested_models(arg))
    return found


ALL_MODELS = _walk_models([*TOP_LEVEL_CONTRACTS.values(), *SUPPORTING_CONTRACTS.values()])
REFERENCE_FIELDS = sorted(
    f"{model.__name__}.{name}"
    for model in ALL_MODELS
    for name, field in model.model_fields.items()
    if (name.endswith("_ref") or name.endswith("_refs")) and _is_string_like(field.annotation)
)


@pytest.mark.requirements("PL-054")
@pytest.mark.parametrize("probe", list(SECRET_PROBES), ids=lambda label: label.replace(" ", "_"))
def test_every_helper_is_the_same_function_and_rejects_the_probe(probe: str) -> None:
    value = SECRET_PROBES[probe]
    for name, helper in HELPERS.items():
        with pytest.raises(ValueError, match="looks like a secret"):
            helper(value)
        assert helper is reject_secret_like or getattr(helper, "__wrapped__", helper) is reject_secret_like, name


@pytest.mark.requirements("PL-054")
def test_helpers_are_one_function_and_accept_structured_references() -> None:
    assert len({id(helper) for helper in HELPERS.values()}) == 1, "five copies used to disagree on 4 of 9 probes"
    for value in REFERENCE_SHAPED:
        assert reject_secret_like(value) == value
    assert reject_secret_like("probe:x", "probe_receipt_ref") == "probe:x"
    with pytest.raises(ValueError, match="probe_receipt_ref looks like a secret"):
        reject_secret_like("password=1", "probe_receipt_ref")


@pytest.mark.requirements("PL-054")
def test_every_reference_field_of_every_contract_carries_the_secret_validator() -> None:
    assert REFERENCE_FIELDS, "the walk found no reference fields; the introspection is broken"
    unprotected = []
    for label in REFERENCE_FIELDS:
        model_name, field_name = label.split(".")
        field = next(m for m in ALL_MODELS if m.__name__ == model_name).model_fields[field_name]
        if not _carries_secret_validator(field.annotation, list(field.metadata)):
            unprotected.append(label)
    assert unprotected == [], f"reference fields without the PL-054 validator: {unprotected}"
    assert {"DatasetRow.purpose_authorization_ref", "EvidenceEvent.raw_content_ref", "DatasetManifest.source_rights_refs"} <= set(REFERENCE_FIELDS)
    assert len(REFERENCE_FIELDS) >= 30
    principal = Principal.model_fields["authenticated_via"]
    assert _carries_secret_validator(principal.annotation, list(principal.metadata))


@pytest.mark.requirements("PL-054", "PL-006")
def test_authentication_and_authority_fields_reject_credential_material() -> None:
    for value in ("bearer token=eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ4In0.abc", "password=hunter2", "AKIAABCDEFGHIJKLMNOP"):
        with pytest.raises(ValidationError, match="looks like a secret|should match pattern"):
            Principal(principal_id="svc-1", principal_type=PrincipalType.SERVICE, authenticated_via=value)
    assert Principal(principal_id="svc-1", principal_type=PrincipalType.SERVICE, authenticated_via="oidc:issuer").authenticated_via == "oidc:issuer"
    for value in ("BEGIN PRIVATE KEY", "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ4In0.sig", "0123456789abcdef" * 4):
        with pytest.raises(ValidationError, match="looks like a secret|should match pattern"):
            DataHandling(processor="proc-a", region="eu", retention="r", credential_ref=value)
    with pytest.raises(ValidationError, match="looks like a secret"):
        TypeAdapter(NonSecretText).validate_python("needs grant password=hunter2")
    assert TypeAdapter(NonSecretText).validate_python("source grant: INSPECT on the ledger") == "source grant: INSPECT on the ledger"
    with pytest.raises(ValidationError, match="looks like a secret"):
        TypeAdapter(NonSecretIdentifier).validate_python("grant_secret_abc")
    for value in ("AKIAABCDEFGHIJKLMNOP", "a b"):
        with pytest.raises(ValidationError):
            TypeAdapter(NonSecretRef).validate_python(value)


@pytest.mark.requirements("PL-009", "PL-054")
def test_storage_references_have_a_positive_grammar_so_content_cannot_pass() -> None:
    adapter = TypeAdapter(StorageRef)
    for value in ("blob://evidence/evt-001", "snapshot://settings/v2", "outbox://events/ev-001", "s3://bucket/key/2026/09/01.json", "artifact:sha256:" + "ab" * 32):
        assert adapter.validate_python(value) == value
    compact_json = '{"vendor":"acme-synthetic","invoice_no":4711,"total_minor":120000}'
    underscored = "Dear_accountant_please_find_attached_the_invoice_for_September"
    for value in (compact_json, underscored, "data:text/plain,Dear%20accountant", "deadbeef" * 25, "Invoice total is 1,250.00", "blob://evidence/" + "a" * 300):
        with pytest.raises(ValidationError):
            adapter.validate_python(value)


@pytest.mark.requirements("PL-054", "PL-052")
def test_error_envelope_screens_operator_action_as_well_as_message() -> None:
    base: dict[str, Any] = {"error_class": ErrorClass.AUTH_REQUIRED, "retryable": False, "correlation_id": "corr-1", "tenant_id": "tnt_acct0001"}
    with pytest.raises(ValidationError, match="operator_action must not mention other tenants"):
        ErrorEnvelope(message="credentials missing", operator_action="ask the owner of tnt_acct0002 to re-grant", **base)
    with pytest.raises(ValidationError, match="operator_action looks like it carries a secret"):
        ErrorEnvelope(message="credentials missing", operator_action="re-login with password=hunter2", **base)
    for message in ("the client secret abcdef1234 is invalid", "key AKIAABCDEFGHIJKLMNOP unknown", "bad Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ4In0.sig"):
        with pytest.raises(ValidationError, match="message looks like it carries a secret"):
            ErrorEnvelope(message=message, operator_action="rotate the credential in the vault", **base)
    ok = ErrorEnvelope(message="envelope for tnt_acct0001 expired at 2026-10-01", operator_action="ask the owner to issue a new envelope version", **base)
    assert ok.operator_action is not None


@pytest.mark.requirements("PL-055")
def test_job_envelope_operation_accepts_every_openapi_operation_id() -> None:
    import re
    from pathlib import Path

    text = (Path(__file__).resolve().parent.parent / "api" / "openapi.yaml").read_text(encoding="utf-8")
    operation_ids = re.findall(r"operationId: (\S+)", text)
    assert len(operation_ids) == 24
    now = datetime(2026, 10, 1, tzinfo=timezone.utc)
    for operation_id in operation_ids:
        job = JobEnvelope(job_id="job-1", tenant_id="tnt_acct0001", status=JobStatus.PENDING, idempotency_key="k" * 255, operation=operation_id, created_at=now, updated_at=now, server_assigned_version=1)
        assert job.operation == operation_id
    with pytest.raises(ValidationError):
        JobEnvelope(job_id="job-1", tenant_id="tnt_acct0001", status=JobStatus.PENDING, idempotency_key="k" * 256, operation="createBuild", created_at=now, updated_at=now, server_assigned_version=1)
