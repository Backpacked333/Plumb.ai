"""ActionIntent and the effect-slot vocabulary (specification section 16).

Implements:

* PL-037: before dispatch the gateway persists an action intent carrying a
  stable effect slot (tenant + case + obligation epoch + operation + target),
  a *separate* payload digest, the expected case state version, the authority
  reference, the deployment (release) version and the provider/account target.
  The slot is the deduplication identity; the payload digest is stored apart
  from it so that a changed payload on the same slot is a conflict, never a
  silent re-send. Supersession is an explicit field (``supersedes_action_id``),
  never an inference from a changed body.
* PL-038: :class:`ActionReceipt` stores provider request ids, external ids and
  read-after-write probe results. :class:`ReconciliationResult` makes the three
  possible outcomes of a reconciliation explicit and refuses a ``CONFIRMED``
  without a receipt and a ``FAILED_FINAL`` without provider-confirmed
  non-occurrence, so a timeout can never be recorded as "nothing happened".
  :class:`RejectionEvidence` is the same asymmetry for a *synchronous*
  rejection: a dispatched action may be settled as ``FAILED_FINAL`` only with
  the provider's own answer (its response digest and confirmed non-occurrence);
  a timeout is never rejection evidence and goes through ``UNKNOWN``.
* PL-039: ``idempotency_key`` is derived from the logical action identity by
  :func:`derive_idempotency_key`, never from the payload and never from the
  release, so deduplication survives worker restarts and workflow releases.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field, StringConstraints, model_validator

from plumb.contracts.common import (
    ArtifactHeader,
    ArtifactKind,
    EffectClass,
    Identifier,
    NonEmptyStr,
    NonSecretIdentifier,
    Sha256Digest,
    ShortStr,
    SourceRef,
    StrictModel,
    TenantId,
    digest_json,
    reject_secret_like,
)

SLOT_KEY_SEPARATOR = "|"
"""Joins the six slot components. No identifier pattern admits this character."""

IdempotencyKey = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
"""Provider idempotency key: the hex SHA-256 of the logical action identity."""

reject_secret_marker = reject_secret_like
"""Former name of :func:`plumb.contracts.common.reject_secret_like`; kept for existing imports."""


class EffectSlot(StrictModel):
    """The semantic identity of one business action (PL-037, PL-039).

    Two intents with the same slot are the *same* business action regardless of
    their payload, their release or the worker that produced them. A deliberate
    new action for the same obligation belongs to a new ``obligation_epoch``.
    """

    tenant_id: TenantId
    case_id: Identifier
    obligation_id: Identifier
    obligation_epoch: int = Field(
        ge=0, description="Approved epoch of the obligation; a new approved action increments it."
    )
    operation: Identifier = Field(description="Operation performed, e.g. send_reminder or post_journal.")
    target: Identifier = Field(description="Provider account / recipient identity the effect lands on.")

    def key(self) -> str:
        """Return ``tenant|case|obligation|epoch|operation|target``."""
        return SLOT_KEY_SEPARATOR.join(
            (
                self.tenant_id,
                self.case_id,
                self.obligation_id,
                str(self.obligation_epoch),
                self.operation,
                self.target,
            )
        )


def derive_idempotency_key(action_id: str, slot: EffectSlot) -> str:
    """Derive the provider idempotency key from the logical action identity (PL-039).

    The key is a function of ``action_id`` and the slot only. It deliberately
    excludes the payload digest and the deployment version: a changed body or
    a new release must never mint a fresh key for the same business action.
    """
    return digest_json({"action_id": action_id, "slot": slot.key()}).removeprefix("sha256:")


class ActionIntent(ArtifactHeader):
    """Persisted intent to perform one external effect (PL-037)."""

    kind: Literal[ArtifactKind.ACTION_INTENT] = ArtifactKind.ACTION_INTENT
    action_id: Identifier = Field(description="Logical action id; stable across retries of the same action.")
    slot: EffectSlot
    payload_digest: Sha256Digest = Field(description="Digest of the exact payload to be sent; stored apart from the slot.")
    expected_state_version: int = Field(
        ge=1, description="Case state version the action was prepared/approved against (section 15); cases start at 1."
    )
    authority_ref: NonSecretIdentifier = Field(description="Approval or envelope that authorizes this effect.")
    deployment_version: Identifier = Field(description="Release id that prepared the action; not part of the identity.")
    provider_target: SourceRef
    effect_class: EffectClass
    idempotency_key: IdempotencyKey = Field(
        description="Must equal derive_idempotency_key(action_id, slot); never derived from the payload."
    )
    supersedes_action_id: Identifier | None = Field(
        default=None,
        description="Explicit supersession decision: the settled action on the same slot this one replaces.",
    )

    @model_validator(mode="after")
    def _consistent_identity(self) -> "ActionIntent":
        if self.slot.tenant_id != self.tenant_id:
            raise ValueError("slot.tenant_id must equal the intent's tenant_id")
        if self.idempotency_key != derive_idempotency_key(self.action_id, self.slot):
            raise ValueError(
                "idempotency_key must be derived from the logical action identity; "
                "use derive_idempotency_key(action_id, slot)"
            )
        if self.supersedes_action_id == self.action_id:
            raise ValueError("an action cannot supersede itself")
        if self.effect_class is EffectClass.READ:
            raise ValueError("an action intent records an external effect; READ operations are not dispatched")
        return self


class ActionReceipt(StrictModel):
    """What the provider gave back for a dispatched action (PL-038).

    A request id alone proves only that a request was made. Evidence that the
    effect *occurred* is an external id assigned by the provider or the result
    of a read-after-write probe; at least one of them is required.
    """

    provider_request_id: ShortStr = Field(description="Provider's identity for the request (opaque, non-secret).")
    external_id: ShortStr | None = Field(
        default=None, description="Provider-assigned identity of the created/changed object, if any."
    )
    postcondition_probe: NonEmptyStr | None = Field(
        default=None, description="Result of the read-after-write probe that observed the effect."
    )
    observed_at: AwareDatetime
    raw_receipt_digest: Sha256Digest = Field(description="Digest of the raw provider response kept in the artifact store.")

    @model_validator(mode="after")
    def _carries_evidence(self) -> "ActionReceipt":
        if self.external_id is None and self.postcondition_probe is None:
            raise ValueError(
                "a receipt must carry an external id or a read-after-write probe result; "
                "a request id alone does not prove the effect occurred"
            )
        return self


class RejectionEvidence(StrictModel):
    """The provider's synchronous, definitive rejection of a dispatched request (PL-038).

    Settling a ``DISPATCHED`` effect as ``FAILED_FINAL`` needs this record, the
    way ``CONFIRMED`` needs an :class:`ActionReceipt`. The provider must have
    positively confirmed that nothing happened (``provider_confirmed_absent``
    is always true here; a record saying otherwise is not rejection evidence),
    and its raw response is kept by digest. A timeout, a dropped connection or
    a missing answer is not a rejection: it is ``UNKNOWN``.
    """

    provider_request_id: ShortStr | None = Field(
        default=None, description="Provider's identity for the rejected request, when the provider assigned one."
    )
    raw_response_digest: Sha256Digest = Field(description="Digest of the raw provider response kept in the artifact store.")
    provider_confirmed_absent: bool = Field(
        default=True, description="Must be true: the provider itself stated the action did not occur."
    )
    detail: NonEmptyStr = Field(description="What the provider answered, e.g. '400 invalid recipient'.")
    observed_at: AwareDatetime

    @model_validator(mode="after")
    def _is_a_rejection(self) -> "RejectionEvidence":
        if not self.provider_confirmed_absent:
            raise ValueError(
                "rejection evidence requires the provider to have confirmed non-occurrence; "
                "a timeout or missing answer is UNKNOWN, not a rejection"
            )
        return self


class ReconciliationOutcome(str, Enum):
    """Result of looking up an UNKNOWN effect at the provider (PL-038)."""

    CONFIRMED = "CONFIRMED"
    FAILED_FINAL = "FAILED_FINAL"
    STILL_UNKNOWN = "STILL_UNKNOWN"


class ReconciliationResult(StrictModel):
    """Outcome of reconciling an UNKNOWN effect (PL-038).

    ``CONFIRMED`` requires a receipt. ``FAILED_FINAL`` requires the provider to
    have confirmed that the action did not occur (``provider_confirmed_absent``)
    together with the evidence consulted. Anything else is ``STILL_UNKNOWN``.
    """

    outcome: ReconciliationOutcome
    receipt: ActionReceipt | None = None
    evidence: NonEmptyStr = Field(description="What was looked up at the provider and what it returned.")
    provider_confirmed_absent: bool = Field(
        default=False, description="True only when the provider positively confirmed non-occurrence."
    )
    reconciled_at: AwareDatetime

    @model_validator(mode="after")
    def _outcome_backed_by_evidence(self) -> "ReconciliationResult":
        if self.outcome is ReconciliationOutcome.CONFIRMED:
            if self.receipt is None:
                raise ValueError("CONFIRMED requires an external receipt")
            if self.provider_confirmed_absent:
                raise ValueError("CONFIRMED contradicts provider_confirmed_absent")
        elif self.outcome is ReconciliationOutcome.FAILED_FINAL:
            if not self.provider_confirmed_absent:
                raise ValueError(
                    "FAILED_FINAL requires provider-confirmed non-occurrence; "
                    "a timeout or missing answer is STILL_UNKNOWN"
                )
            if self.receipt is not None:
                raise ValueError("FAILED_FINAL contradicts a receipt proving the effect occurred")
        else:
            if self.receipt is not None:
                raise ValueError("a receipt proves occurrence; the outcome is CONFIRMED, not STILL_UNKNOWN")
            if self.provider_confirmed_absent:
                raise ValueError("provider-confirmed absence is FAILED_FINAL, not STILL_UNKNOWN")
        return self


__all__ = [
    "SLOT_KEY_SEPARATOR",
    "IdempotencyKey",
    "NonSecretIdentifier",
    "reject_secret_marker",
    "EffectSlot",
    "derive_idempotency_key",
    "ActionIntent",
    "ActionReceipt",
    "RejectionEvidence",
    "ReconciliationOutcome",
    "ReconciliationResult",
]
