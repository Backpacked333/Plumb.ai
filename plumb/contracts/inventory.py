"""EnvironmentInventory: what a customer's environment can actually do (specification section 5).

Implements:

* PL-007: the inventory lists accessible applications with their accounts,
  entities, schema versions, supported read/write operations, authorization
  status, available history, quotas, update mechanism, source freshness and
  owners. Only :class:`OperationCapability` entries are capabilities; an
  application logo or a product name is not one.
* PL-008: discovered, documented, sandbox-tested and production-verified
  operations are distinct. An operation may claim ``SANDBOX_TESTED`` or
  ``PRODUCTION_VERIFIED`` only when it carries the probe receipt and probe time
  that established it, and the probe records the account and exact operation
  without exposing credentials.
* Section 5 (coverage): the product works when some employees or applications
  are not observed, and its :class:`CoverageReport` must disclose that
  limitation. Low-confidence assumptions stay visible on the inventory while
  unaffected work progresses.

The reference types this module used to define (:data:`NonSecretRef`,
:data:`NonSecretIdentifier`, :func:`reject_secret_like`) now live in
:mod:`plumb.contracts.common` and are re-exported here unchanged in name so
existing imports keep working; there is exactly one secret heuristic in the package.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from plumb.contracts.common import (
    ArtifactHeader,
    ArtifactKind,
    CapabilityMaturity,
    Identifier,
    NonEmptyStr,
    NonSecretIdentifier,
    NonSecretRef,
    ShortStr,
    SourceRef,
    StrictModel,
    reject_secret_like,
)

EVIDENCE_BACKED_MATURITIES: frozenset[CapabilityMaturity] = frozenset(
    {CapabilityMaturity.SANDBOX_TESTED, CapabilityMaturity.PRODUCTION_VERIFIED}
)
"""Maturities that require a recorded probe (PL-008)."""


# ---------------------------------------------------------------------------
# Vocabularies
# ---------------------------------------------------------------------------


class OperationDirection(str, Enum):
    """Whether an operation reads from or writes to the application."""

    READ = "READ"
    WRITE = "WRITE"


class AuthorizationStatus(str, Enum):
    """Whether Plumb currently holds authorization for an application (section 5)."""

    AUTHORIZED = "AUTHORIZED"
    CONSENT_REQUIRED = "CONSENT_REQUIRED"
    DENIED = "DENIED"
    UNKNOWN = "UNKNOWN"


class UpdateMechanism(str, Enum):
    """How changes in the application can be observed (PL-007, section 11)."""

    WEBHOOK = "WEBHOOK"
    POLLING = "POLLING"
    CDC = "CDC"
    EXPORT = "EXPORT"
    NONE = "NONE"


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------


class OperationCapability(StrictModel):
    """One exact operation on one account, with the evidence behind its maturity (PL-008)."""

    operation: ShortStr = Field(description="Exact provider operation, e.g. GET /v1/invoices; never a product name.")
    direction: OperationDirection
    maturity: CapabilityMaturity
    probe_receipt_ref: NonSecretIdentifier | None = Field(
        default=None, description="Receipt of the successful probe that established the maturity."
    )
    last_probed_at: AwareDatetime | None = None
    account_id: ShortStr = Field(
        description="Account the capability was established for: a source_id or external_account_id "
        "of the owning application's accounts."
    )

    @model_validator(mode="after")
    def _maturity_requires_probe(self) -> "OperationCapability":
        if self.maturity in EVIDENCE_BACKED_MATURITIES:
            if self.probe_receipt_ref is None or self.last_probed_at is None:
                raise ValueError(
                    f"maturity {self.maturity.value} requires probe_receipt_ref and last_probed_at; "
                    "a vendor page saying an API exists is not evidence that this account can use it"
                )
        return self


class Quota(StrictModel):
    """A provider-imposed limit on an application or account."""

    name: ShortStr
    limit: int = Field(ge=0)
    window_seconds: int | None = Field(default=None, ge=1, description="None for absolute (non-rolling) quotas.")


class ApplicationRecord(StrictModel):
    """One application observed during inventory (PL-007)."""

    application_id: Identifier
    name: ShortStr
    accounts: list[SourceRef] = Field(default_factory=list)
    entities: list[ShortStr] = Field(default_factory=list, description="Business entities exposed, e.g. invoice.")
    schema_versions: dict[str, ShortStr] = Field(
        default_factory=dict, description="Entity or API surface -> observed schema version."
    )
    operations: list[OperationCapability] = Field(default_factory=list)
    authorization_status: AuthorizationStatus
    available_history_from: AwareDatetime | None = Field(
        default=None, description="Earliest record time the account exposes; None when unknown."
    )
    quotas: list[Quota] = Field(default_factory=list)
    update_mechanism: UpdateMechanism
    freshness_seconds: int | None = Field(
        default=None, ge=0, description="Observed delay between a change at the source and its visibility."
    )
    owners: list[Identifier] = Field(default_factory=list, description="Principal ids accountable for the application.")

    @model_validator(mode="after")
    def _consistent_record(self) -> "ApplicationRecord":
        account_ids = {account.source_id for account in self.accounts} | {
            account.external_account_id for account in self.accounts
        }
        if len({account.source_id for account in self.accounts}) != len(self.accounts):
            raise ValueError("accounts must have distinct source_ids")
        if self.authorization_status is AuthorizationStatus.AUTHORIZED and not self.accounts:
            raise ValueError("an AUTHORIZED application must list at least one authorized account")
        seen: set[tuple[str, OperationDirection]] = set()
        for operation in self.operations:
            key = (operation.operation, operation.direction)
            if key in seen:
                raise ValueError(f"duplicate operation {operation.operation!r} ({operation.direction.value})")
            seen.add(key)
            if operation.account_id not in account_ids:
                raise ValueError(
                    f"operation {operation.operation!r} names account {operation.account_id!r} "
                    "which is not one of the application's accounts"
                )
        if len(set(self.owners)) != len(self.owners):
            raise ValueError("owners must not contain duplicates")
        return self

    def verified_operations(self, minimum: CapabilityMaturity = CapabilityMaturity.SANDBOX_TESTED) -> list[OperationCapability]:
        """Operations whose maturity is at least ``minimum`` in the PL-008 order."""
        order = list(CapabilityMaturity)
        return [op for op in self.operations if order.index(op.maturity) >= order.index(minimum)]


class CoverageReport(StrictModel):
    """What the inventory did and did not observe; the limitation must be disclosed (section 5)."""

    observed_applications: list[Identifier] = Field(default_factory=list)
    unobserved_applications: list[ShortStr] = Field(
        default_factory=list, description="Applications known to exist but not observed (names, not ids)."
    )
    observed_employee_count: int = Field(ge=0)
    unobserved_employee_count: int = Field(ge=0)
    capture_scope: NonEmptyStr = Field(description="What capture covers, as shown on the enrollment screen.")
    exclusions: list[ShortStr] = Field(default_factory=list)
    retention_days: int = Field(ge=0)
    disclosure: NonEmptyStr = Field(description="Customer-facing statement of the coverage limitation.")

    @model_validator(mode="after")
    def _no_overlap(self) -> "CoverageReport":
        if len(set(self.observed_applications)) != len(self.observed_applications):
            raise ValueError("observed_applications must not contain duplicates")
        return self


class EnvironmentInventory(ArtifactHeader):
    """Inventory produced before any production build is proposed (PL-007)."""

    kind: Literal[ArtifactKind.ENVIRONMENT_INVENTORY] = ArtifactKind.ENVIRONMENT_INVENTORY
    inventory_id: Identifier
    applications: list[ApplicationRecord] = Field(min_length=1)
    coverage_report: CoverageReport
    low_confidence_assumptions: list[str] = Field(
        default_factory=list, description="Assumptions that remain visible while unaffected work progresses."
    )

    @model_validator(mode="after")
    def _consistent_inventory(self) -> "EnvironmentInventory":
        application_ids = [application.application_id for application in self.applications]
        if len(set(application_ids)) != len(application_ids):
            raise ValueError("application_id values must be unique within an inventory")
        unknown = sorted(set(self.coverage_report.observed_applications) - set(application_ids))
        if unknown:
            raise ValueError(f"coverage_report.observed_applications not in inventory: {', '.join(unknown)}")
        return self

    def application(self, application_id: str) -> ApplicationRecord:
        for record in self.applications:
            if record.application_id == application_id:
                return record
        raise KeyError(application_id)


__all__ = [
    "reject_secret_like",
    "NonSecretRef",
    "NonSecretIdentifier",
    "EVIDENCE_BACKED_MATURITIES",
    "OperationDirection",
    "AuthorizationStatus",
    "UpdateMechanism",
    "OperationCapability",
    "Quota",
    "ApplicationRecord",
    "CoverageReport",
    "EnvironmentInventory",
]
