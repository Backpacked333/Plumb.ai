"""ApprovalRecord: an independently authenticated human decision (specification section 17).

Implements:

* PL-040: an approval binds to the artifact/action digest (``subject_digest``),
  the relevant case version (``case_version``, mandatory for a case-level
  business decision), the policy version, the approver identity and an expiry.
  An approval for one version or tenant never authorizes another: the record
  carries ``scope_tenant`` (which must equal the artifact's ``tenant_id``) and
  :func:`plumb.checker.approval_checker.check_approval` compares every binding
  against the thing being authorized. The approval must come from an
  independently authenticated decision, not a value supplied by the build
  agent: ``approver`` must be a human principal, ``authenticated_decision_ref``
  points at the authenticated decision, and the artifact ``producer`` cannot be
  a build or runtime agent.
* PL-041: three distinct decisions exist (:class:`DecisionKind`): authority to
  observe/use particular data, authority to implement and operate a described
  intervention, and any case-level business approval the intervention
  requires. Expiry and revocation stop future actions promptly:
  :meth:`ApprovalRecord.is_valid_at` is false at and after ``expires_at`` or
  ``revoked_at``.

This module also hosts the small helpers shared by the trust vertical
(approval, verification, infrastructure, release): :func:`reject_secret_like`
for ``*_ref`` fields that must never carry a credential value, and
:func:`require_aware` for instants used in comparisons.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import AfterValidator, AwareDatetime, Field, model_validator

from plumb.contracts.common import (
    ArtifactHeader,
    ArtifactKind,
    Identifier,
    Principal,
    PrincipalType,
    SemVer,
    Sha256Digest,
    ShortStr,
    TenantId,
)

HUMAN_APPROVER_TYPES: frozenset[PrincipalType] = frozenset(
    {PrincipalType.HUMAN_OWNER, PrincipalType.HUMAN_REVIEWER, PrincipalType.HUMAN_APPROVER}
)
"""Principal types that can approve. Agents, services and verifiers cannot (PL-040)."""

AGENT_PRINCIPAL_TYPES: frozenset[PrincipalType] = frozenset(
    {PrincipalType.BUILD_AGENT, PrincipalType.RUNTIME_AGENT}
)
"""Principal types whose supplied values never constitute an approval (PL-040)."""

_SECRET_MARKERS: tuple[str, ...] = ("secret", "password", "token=")
_BASE64_RUN = re.compile(r"[A-Za-z0-9+/=_-]{40,}")


def reject_secret_like(value: str) -> str:
    """Reject a string that looks like a secret value rather than a reference to one.

    A reference contains none of ``secret``, ``password`` or ``token=`` and no
    run of 40+ base64-like characters mixing upper case, lower case and digits.
    """
    lowered = value.lower()
    for marker in _SECRET_MARKERS:
        if marker in lowered:
            raise ValueError(f"value looks like a secret (contains {marker!r}); store a reference, not a value")
    for run in _BASE64_RUN.findall(value):
        if any(c.isupper() for c in run) and any(c.islower() for c in run) and any(c.isdigit() for c in run):
            raise ValueError("value looks like a secret (40+ characters of base64-like text)")
    return value


NonSecretRef = Annotated[ShortStr, AfterValidator(reject_secret_like)]
"""A short reference string that is rejected when it looks like a credential value."""


def require_aware(value: datetime, field_name: str) -> datetime:
    """Reject naive datetimes so that comparisons between instants are always defined."""
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")
    return value


class DecisionKind(str, Enum):
    """The three distinct decisions an owner or reviewer can make (PL-041)."""

    DATA_USE = "DATA_USE"
    IMPLEMENT_OPERATE = "IMPLEMENT_OPERATE"
    CASE_LEVEL_BUSINESS = "CASE_LEVEL_BUSINESS"


class ApprovalRecord(ArtifactHeader):
    """A human decision bound to exactly one digest, case version, policy version and tenant (PL-040)."""

    kind: Literal[ArtifactKind.APPROVAL_RECORD] = ArtifactKind.APPROVAL_RECORD
    approval_id: Identifier
    decision_kind: DecisionKind
    subject_digest: Sha256Digest = Field(
        description="Digest of the artifact or action payload this approval authorizes; nothing else."
    )
    case_version: int | None = Field(
        default=None, ge=1, description="Case version approved; required for CASE_LEVEL_BUSINESS decisions."
    )
    policy_version: SemVer = Field(description="Policy version in force when the decision was made.")
    approver: Principal = Field(description="The human who decided; never a build or runtime agent.")
    authenticated_decision_ref: NonSecretRef = Field(
        description="Reference to the independently authenticated decision (e.g. an identity-provider event)."
    )
    approved_at: AwareDatetime
    expires_at: AwareDatetime = Field(description="Instant from which the approval no longer authorizes anything.")
    revoked_at: AwareDatetime | None = Field(
        default=None, description="Instant of revocation; cached grants and queued dispatches are invalid from here."
    )
    scope_tenant: TenantId = Field(description="Tenant the approval is valid for; must equal tenant_id.")

    @model_validator(mode="after")
    def _check_bindings(self) -> "ApprovalRecord":
        require_aware(self.created_at, "created_at")
        if self.approver.principal_type not in HUMAN_APPROVER_TYPES:
            raise ValueError(
                "approver must be a human principal (HUMAN_OWNER, HUMAN_REVIEWER or HUMAN_APPROVER); "
                f"a {self.approver.principal_type.value} cannot approve (PL-040)"
            )
        if self.producer.principal_type in AGENT_PRINCIPAL_TYPES:
            raise ValueError(
                "an approval record cannot be produced by a build or runtime agent; "
                "approval must come from an independently authenticated decision (PL-040)"
            )
        if self.decision_kind is DecisionKind.CASE_LEVEL_BUSINESS and self.case_version is None:
            raise ValueError("case_version is required for a CASE_LEVEL_BUSINESS approval (PL-040)")
        if self.expires_at <= self.approved_at:
            raise ValueError("expires_at must be after approved_at")
        if self.revoked_at is not None and self.revoked_at < self.approved_at:
            raise ValueError("revoked_at cannot precede approved_at")
        if self.scope_tenant != self.tenant_id:
            raise ValueError(
                f"scope_tenant {self.scope_tenant} must equal tenant_id {self.tenant_id}; "
                "an approval for one tenant never authorizes another (PL-040)"
            )
        return self

    def is_valid_at(self, now: datetime) -> bool:
        """True when ``now`` is within [approved_at, expires_at) and before any revocation."""
        require_aware(now, "now")
        if now < self.approved_at or now >= self.expires_at:
            return False
        return self.revoked_at is None or now < self.revoked_at


__all__ = [
    "AGENT_PRINCIPAL_TYPES",
    "HUMAN_APPROVER_TYPES",
    "NonSecretRef",
    "DecisionKind",
    "ApprovalRecord",
    "reject_secret_like",
    "require_aware",
]
