"""Job, error and event envelopes of the control-plane protocol (specification section 22).

Implements:

* PL-055: long-running mutations return a :class:`JobEnvelope` with a job
  identity, durable status and a tenant-scoped idempotency key; the server
  assigns the version (``server_assigned_version``) so client claims never
  overwrite server state. ``request_payload_digest`` lets a server detect the
  same key arriving with a different payload (a conflict).
* Section 22 (errors): :class:`ErrorEnvelope` uses the closed
  :class:`~plumb.contracts.common.ErrorClass` vocabulary and records
  retryability, dependency identity and operator action. Neither ``message``
  nor ``operator_action`` may carry a secret-looking value (the package's one
  heuristic, :func:`plumb.contracts.common.reject_secret_like`) or another
  tenant's identifier. Authority errors are not retryable and must name what
  resolves them; an unknown effect is not retried.
* PL-055: ``JobEnvelope.idempotency_key`` is at most 255 characters, the same
  limit as the ``Idempotency-Key`` header and the ``jobs`` table, so a valid
  envelope can always be sent and stored; ``operation`` is the OpenAPI
  ``operationId`` that started the job (camelCase, :data:`OperationId`).
* Section 22 (events): :class:`EventEnvelope` carries exactly the fields the
  spec lists; ``recorded_at`` cannot precede ``occurred_at`` and the aggregate
  version is per aggregate (ordering is never global).
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Annotated

from pydantic import AwareDatetime, Field, StringConstraints, model_validator

from plumb.contracts.common import (
    ArtifactRef,
    ErrorClass,
    Identifier,
    NonEmptyStr,
    OperationId,
    SemVer,
    Sha256Digest,
    StorageRef,
    StrictModel,
    TenantId,
    reject_secret_like,
)

_TENANT_ID_PATTERN = re.compile(r"tnt_[a-z0-9]{4,32}")

IDEMPOTENCY_KEY_MAX_LENGTH = 255
"""One limit for the Idempotency-Key header, JobEnvelope.idempotency_key and the jobs table (PL-055)."""

IdempotencyKeyStr = Annotated[str, StringConstraints(min_length=1, max_length=IDEMPOTENCY_KEY_MAX_LENGTH)]

NON_RETRYABLE_ERROR_CLASSES: frozenset[ErrorClass] = frozenset(
    {
        ErrorClass.AUTH_REQUIRED,
        ErrorClass.SCOPE_DENIED,
        ErrorClass.PURPOSE_DENIED,
        ErrorClass.CAPABILITY_UNSUPPORTED,
        ErrorClass.PAYLOAD_CONFLICT,
        ErrorClass.EFFECT_UNKNOWN,
        ErrorClass.RETRY_EXHAUSTED,
    }
)
"""Error classes a retry can never resolve (section 22, Appendix A section 3)."""

AUTHORITY_ERROR_CLASSES: frozenset[ErrorClass] = frozenset(
    {ErrorClass.AUTH_REQUIRED, ErrorClass.SCOPE_DENIED, ErrorClass.PURPOSE_DENIED}
)
"""Errors that only a grant, consent or decision resolves; they must name it."""


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    WAITING = "WAITING"


class ErrorEnvelope(StrictModel):
    """Shared error shape of every control-plane response (section 22)."""

    error_class: ErrorClass
    message: NonEmptyStr
    retryable: bool
    dependency_id: Identifier | None = Field(default=None, description="Dependency record that resolves the error.")
    operator_action: NonEmptyStr | None = None
    correlation_id: Identifier
    tenant_id: TenantId | None = Field(default=None, description="Tenant the error belongs to, when known.")

    @model_validator(mode="after")
    def _safe_and_actionable(self) -> "ErrorEnvelope":
        for field_name in ("message", "operator_action"):
            text = getattr(self, field_name)
            if text is None:
                continue
            try:
                reject_secret_like(text)
            except ValueError as exc:
                raise ValueError(f"error {field_name} looks like it carries a secret: {exc}") from None
            foreign = sorted(set(_TENANT_ID_PATTERN.findall(text)) - {self.tenant_id})
            if foreign:
                raise ValueError(
                    f"error {field_name} must not mention other tenants' identifiers: {', '.join(foreign)}"
                )
        if self.retryable and self.error_class in NON_RETRYABLE_ERROR_CLASSES:
            raise ValueError(f"{self.error_class.value} cannot be retryable; missing authority is not a generic retry")
        if self.error_class in AUTHORITY_ERROR_CLASSES and self.dependency_id is None and self.operator_action is None:
            raise ValueError(f"{self.error_class.value} must name a dependency_id or operator_action that resolves it")
        return self


class JobEnvelope(StrictModel):
    """Durable status of a long-running mutation (PL-055)."""

    job_id: Identifier
    tenant_id: TenantId
    status: JobStatus
    idempotency_key: IdempotencyKeyStr = Field(description="Client key, scoped to the tenant by the server; at most 255 characters.")
    operation: OperationId = Field(description="OpenAPI operationId that started the job, e.g. createBuild.")
    created_at: AwareDatetime
    updated_at: AwareDatetime
    result_ref: ArtifactRef | None = None
    error: ErrorEnvelope | None = None
    server_assigned_version: int = Field(ge=1, description="Set only by the server; client values are ignored.")
    request_payload_digest: Sha256Digest | None = Field(
        default=None, description="Digest of the original request so a repeated key with another payload conflicts."
    )

    @model_validator(mode="after")
    def _status_consistent(self) -> "JobEnvelope":
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot precede created_at")
        if self.status is JobStatus.SUCCEEDED:
            if self.result_ref is None:
                raise ValueError("a SUCCEEDED job must carry result_ref")
            if self.error is not None:
                raise ValueError("a SUCCEEDED job cannot carry an error")
        else:
            if self.result_ref is not None:
                raise ValueError(f"a {self.status.value} job cannot carry result_ref")
            if self.status is JobStatus.FAILED and self.error is None:
                raise ValueError("a FAILED job must carry an error")
            if self.status in (JobStatus.PENDING, JobStatus.RUNNING) and self.error is not None:
                raise ValueError(f"a {self.status.value} job cannot carry an error")
        if self.error is not None and self.error.tenant_id not in (None, self.tenant_id):
            raise ValueError("error.tenant_id must match the job's tenant")
        return self


class EventEnvelope(StrictModel):
    """Domain event as published through the outbox (section 22)."""

    event_id: Identifier
    tenant_id: TenantId
    aggregate_id: Identifier
    aggregate_version: int = Field(ge=1, description="Per-aggregate ordering; never compare across aggregates.")
    event_type: Identifier
    occurred_at: AwareDatetime
    recorded_at: AwareDatetime
    correlation_id: Identifier
    causation_id: Identifier | None = Field(default=None, description="Event or command that caused this one.")
    schema_version: SemVer
    payload_ref: StorageRef = Field(description="Locator of the stored payload (scheme://path); never the payload itself.")

    @model_validator(mode="after")
    def _times_and_causes(self) -> "EventEnvelope":
        if self.recorded_at < self.occurred_at:
            raise ValueError("recorded_at cannot precede occurred_at")
        if self.causation_id == self.event_id:
            raise ValueError("an event cannot cause itself")
        return self


__all__ = [
    "IDEMPOTENCY_KEY_MAX_LENGTH",
    "IdempotencyKeyStr",
    "NON_RETRYABLE_ERROR_CLASSES",
    "AUTHORITY_ERROR_CLASSES",
    "JobStatus",
    "ErrorEnvelope",
    "JobEnvelope",
    "EventEnvelope",
]
