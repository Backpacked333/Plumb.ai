"""Capability record: what a primitive can do, and how well that has been established.

Implements (specification v0.2):

* PL-007: an inventory lists supported operations; a logo or a vendor page is
  not an operation capability. Capability records name the exact ``provider``
  and ``operation`` behind a ``step_type``.
* PL-008: discovered, documented, sandbox-tested and production-verified
  capabilities are distinct (:class:`~plumb.contracts.common.CapabilityMaturity`).
  A record may only claim ``SANDBOX_TESTED`` or ``PRODUCTION_VERIFIED`` when it
  carries a ``probe_receipt_ref`` and a ``tested_environment``: a documented
  endpoint is not a verified capability, and a successful probe records the
  account and exact operation without exposing credentials.
* Appendix A section 5: the registry records tested environment, failure modes,
  required authority and observed maintenance burden so that implementation
  experience improves future build plans.

Capability records are platform-level engineering knowledge, kept apart from
customer records: every record is stored under :data:`PLATFORM_TENANT_ID`.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Literal

from pydantic import Field, field_validator, model_validator

from plumb.contracts.common import (
    ArtifactHeader,
    ArtifactKind,
    CapabilityMaturity,
    DataPurpose,
    EffectClass,
    Identifier,
    SemVer,
    ShortStr,
)

PLATFORM_TENANT_ID = "tnt_platform"
"""Tenant under which platform-level (non-customer) artifacts are stored."""

MATURITY_RANK: dict[CapabilityMaturity, int] = {
    CapabilityMaturity.DISCOVERED: 0,
    CapabilityMaturity.DOCUMENTED: 1,
    CapabilityMaturity.SANDBOX_TESTED: 2,
    CapabilityMaturity.PRODUCTION_VERIFIED: 3,
}
"""Total order over maturities: higher means more evidence (PL-008)."""

EVIDENCE_BACKED_MATURITIES: frozenset[CapabilityMaturity] = frozenset(
    {CapabilityMaturity.SANDBOX_TESTED, CapabilityMaturity.PRODUCTION_VERIFIED}
)
"""Maturities that may only be claimed with a probe receipt and a tested environment."""

_SECRET_LIKE = re.compile(r"secret|password|token=", re.IGNORECASE)
_BASE64_RUN = re.compile(r"[A-Za-z0-9+/=]{40,}")


def reject_secret_like(value: str, field_name: str) -> str:
    """Reject reference values that look like credentials (design section 2).

    References point at receipts or records; they never carry secret material.
    """
    if _SECRET_LIKE.search(value) or _BASE64_RUN.fullmatch(value):
        raise ValueError(f"{field_name} looks like a secret; references must not carry credentials")
    return value


class MaintenanceBurden(str, Enum):
    """Observed maintenance burden of a capability (Appendix A section 5)."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CapabilityRecord(ArtifactHeader):
    """One verified-or-not primitive the planner may schedule for a step type (PL-007, PL-008)."""

    kind: Literal[ArtifactKind.CAPABILITY_RECORD] = ArtifactKind.CAPABILITY_RECORD
    capability_id: Identifier
    step_type: Identifier = Field(description="Build-plan step type this capability implements.")
    provider: ShortStr = Field(description="Adapter or substrate providing the operation.")
    operation: ShortStr = Field(description="Exact operation on the provider, never a product name.")
    maturity: CapabilityMaturity
    effect_classes: list[EffectClass] = Field(
        min_length=1, description="Every effect class the operation can produce."
    )
    required_purposes: list[DataPurpose] = Field(
        default_factory=list, description="Data purposes the source grant must include."
    )
    required_authority: list[ShortStr] = Field(
        default_factory=list, description="Grants, approvals or roles needed to dispatch it."
    )
    tested_environment: ShortStr | None = Field(
        default=None, description="Where the probe ran, e.g. sandbox account or production region."
    )
    failure_modes: list[ShortStr] = Field(default_factory=list)
    maintenance_burden: MaintenanceBurden
    produces: list[ArtifactKind] = Field(default_factory=list)
    consumes: list[ArtifactKind] = Field(default_factory=list)
    probe_receipt_ref: Identifier | None = Field(
        default=None, description="Receipt of the successful probe that established the maturity."
    )
    capability_version: SemVer

    @field_validator("probe_receipt_ref")
    @classmethod
    def _probe_receipt_not_secret(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return reject_secret_like(value, "probe_receipt_ref")

    @model_validator(mode="after")
    def _check_record(self) -> "CapabilityRecord":
        if self.tenant_id != PLATFORM_TENANT_ID:
            raise ValueError(f"capability records are platform-level; tenant_id must be {PLATFORM_TENANT_ID}")
        for name in ("effect_classes", "required_purposes", "required_authority", "produces", "consumes"):
            values = getattr(self, name)
            if len(set(values)) != len(values):
                raise ValueError(f"{name} must not contain duplicates")
        if self.maturity in EVIDENCE_BACKED_MATURITIES:
            if self.probe_receipt_ref is None:
                raise ValueError(
                    f"maturity {self.maturity.value} requires probe_receipt_ref; "
                    "a documented endpoint is not a verified capability"
                )
            if self.tested_environment is None:
                raise ValueError(f"maturity {self.maturity.value} requires tested_environment")
        return self

    def at_least(self, minimum: CapabilityMaturity) -> bool:
        """True when this record's maturity meets ``minimum`` in the PL-008 order."""
        return MATURITY_RANK[self.maturity] >= MATURITY_RANK[minimum]


__all__ = [
    "PLATFORM_TENANT_ID",
    "MATURITY_RANK",
    "EVIDENCE_BACKED_MATURITIES",
    "reject_secret_like",
    "MaintenanceBurden",
    "CapabilityRecord",
]
