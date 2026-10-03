"""IntegrationSpec: how Plumb talks to one provider account (specification section 10).

Implements:

* PL-020: each operation records which construction path was used
  (:class:`IntegrationPath`, in the order of preference the spec fixes) and the
  resulting :class:`MaintenanceExposure`.
* PL-021: the spec declares provider/account identity, exact operations,
  authentication *reference*, required scopes, schema mappings with unit,
  currency, time zone, enum and null semantics, cursor strategy, rate limits,
  retry semantics, deletion behavior, effect class per operation, verification
  probes and schema-drift handling.
* PL-022: ``activated`` may only be true once ``contract_tests_passed`` covers
  :data:`REQUIRED_CONTRACT_TESTS`, plus :data:`WRITE_CONTRACT_TESTS` when any
  operation writes, and every operation carries a verification probe.
* Section 10 (semantics): a :class:`FieldMapping` whose units differ, such as
  cents to dollars, is rejected unless it states an explicit conversion
  factor; currencies are never converted by a field mapping. Configuration
  changes in the customer's application capture before/after state, affected
  resources, expected effect and reversal limits (:class:`StateCapture`).
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator, model_validator

from plumb.contracts.common import (
    ArtifactHeader,
    ArtifactKind,
    CurrencyCode,
    EffectClass,
    Identifier,
    NonEmptyStr,
    ShortStr,
    SourceRef,
    StrictModel,
)
from plumb.contracts.inventory import NonSecretIdentifier, NonSecretRef, OperationDirection

REQUIRED_CONTRACT_TESTS: frozenset[str] = frozenset(
    {
        "pagination",
        "empty_pages",
        "duplicates",
        "rate_limiting",
        "authorization_failure",
        "malformed_responses",
        "schema_changes",
        "account_boundaries",
    }
)
"""Contract tests every adapter passes before activation (PL-022)."""

WRITE_CONTRACT_TESTS: frozenset[str] = frozenset({"business_state_verification", "uncertain_write_behavior"})
"""Additional contract tests for adapters with any WRITE operation (PL-022)."""


class IntegrationPath(str, Enum):
    """Construction paths in the spec's order of preference (PL-020)."""

    VERIFIED_ADAPTER = "VERIFIED_ADAPTER"
    DECLARATIVE_CONFIG = "DECLARATIVE_CONFIG"
    GENERATED_CODE = "GENERATED_CODE"
    UI_ADAPTER = "UI_ADAPTER"


class MaintenanceExposure(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class NullSemantics(str, Enum):
    """What a null in the source field means (section 10)."""

    NULL_MEANS_UNKNOWN = "NULL_MEANS_UNKNOWN"
    NULL_MEANS_ABSENT = "NULL_MEANS_ABSENT"
    NULL_MEANS_ZERO = "NULL_MEANS_ZERO"
    NULL_NOT_ALLOWED = "NULL_NOT_ALLOWED"


class CursorKind(str, Enum):
    OPAQUE_CURSOR = "OPAQUE_CURSOR"
    UPDATED_SINCE_OVERLAP = "UPDATED_SINCE_OVERLAP"
    CHANGE_FEED = "CHANGE_FEED"
    FULL_SNAPSHOT = "FULL_SNAPSHOT"


class BackoffStrategy(str, Enum):
    EXPONENTIAL = "EXPONENTIAL"
    LINEAR = "LINEAR"
    PROVIDER_RETRY_AFTER = "PROVIDER_RETRY_AFTER"
    NONE = "NONE"


class DeletionBehavior(str, Enum):
    """How the provider exposes deletions (PL-021)."""

    TOMBSTONE = "TOMBSTONE"
    SOFT_DELETE_FLAG = "SOFT_DELETE_FLAG"
    HARD_DELETE_VISIBLE_BY_DIFF = "HARD_DELETE_VISIBLE_BY_DIFF"
    NOT_OBSERVABLE = "NOT_OBSERVABLE"


class SchemaDriftHandling(str, Enum):
    """What happens when the source schema changes (PL-021, Appendix A section 3)."""

    QUARANTINE_AND_REMAP = "QUARANTINE_AND_REMAP"
    TOLERATE_ADDITIVE_FIELDS = "TOLERATE_ADDITIVE_FIELDS"
    FAIL_CLOSED = "FAIL_CLOSED"


class UnitSemantics(StrictModel):
    """Units on both sides of a mapping; differing units need an explicit factor (section 10)."""

    source_unit: ShortStr
    target_unit: ShortStr
    conversion_factor: Decimal | None = Field(
        default=None, description="target = source * conversion_factor; required when the units differ."
    )

    @model_validator(mode="after")
    def _explicit_conversion(self) -> "UnitSemantics":
        if self.source_unit.lower() != self.target_unit.lower():
            if self.conversion_factor is None:
                raise ValueError(
                    f"mapping {self.source_unit!r} to {self.target_unit!r} requires an explicit conversion_factor; "
                    "an amount in cents must not land in a dollars field because the names resemble each other"
                )
            if self.conversion_factor <= 0:
                raise ValueError("conversion_factor must be positive")
        elif self.conversion_factor not in (None, Decimal(1)):
            raise ValueError("identical units cannot carry a conversion factor other than 1")
        return self


class CurrencySemantics(StrictModel):
    """Currency on both sides; a field mapping never performs currency conversion."""

    source_currency: CurrencyCode
    target_currency: CurrencyCode

    @model_validator(mode="after")
    def _no_silent_conversion(self) -> "CurrencySemantics":
        if self.source_currency != self.target_currency:
            raise ValueError("a field mapping cannot convert currencies; conversion is a dated business operation")
        return self


class TimezoneSemantics(StrictModel):
    """IANA time zones the source and target interpret naive timestamps in."""

    source_timezone: ShortStr
    target_timezone: ShortStr

    @field_validator("source_timezone", "target_timezone")
    @classmethod
    def _known_zone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"unknown IANA time zone {value!r}") from exc
        return value


class FieldMapping(StrictModel):
    """One source field mapped onto one target field with explicit semantics (PL-021)."""

    source_field: ShortStr
    target_field: ShortStr
    unit: UnitSemantics | None = None
    currency: CurrencySemantics | None = None
    timezone: TimezoneSemantics | None = None
    enum_map: dict[str, str] = Field(default_factory=dict, description="Source enum value -> target enum value.")
    null_semantics: NullSemantics
    note: ShortStr | None = None


class IntegrationOperation(StrictModel):
    """One exact operation, how it was built and how it is verified (PL-020, PL-021)."""

    name: Identifier
    direction: OperationDirection
    effect_class: EffectClass
    path_used: IntegrationPath
    maintenance_exposure: MaintenanceExposure
    verification_probe_refs: list[NonSecretIdentifier] = Field(default_factory=list)
    configuration_change: bool = Field(
        default=False, description="True when the operation changes settings in the customer's application."
    )

    @model_validator(mode="after")
    def _direction_matches_effect(self) -> "IntegrationOperation":
        if self.direction is OperationDirection.READ and self.effect_class is not EffectClass.READ:
            raise ValueError(f"READ operation {self.name} cannot have effect class {self.effect_class.value}")
        if self.direction is OperationDirection.WRITE and self.effect_class is EffectClass.READ:
            raise ValueError(f"WRITE operation {self.name} must declare a non-READ effect class")
        if self.configuration_change and self.direction is not OperationDirection.WRITE:
            raise ValueError(f"configuration change {self.name} is a WRITE operation")
        if len(set(self.verification_probe_refs)) != len(self.verification_probe_refs):
            raise ValueError("verification_probe_refs must not contain duplicates")
        return self


class CursorStrategy(StrictModel):
    """How incremental reads resume (PL-021, section 11)."""

    kind: CursorKind
    overlap_seconds: int | None = Field(default=None, ge=1)
    stable_version_field: ShortStr | None = Field(
        default=None, description="Record version used to deduplicate overlapping windows."
    )

    @model_validator(mode="after")
    def _overlap_needs_versions(self) -> "CursorStrategy":
        if self.kind is CursorKind.UPDATED_SINCE_OVERLAP and (
            self.overlap_seconds is None or self.stable_version_field is None
        ):
            raise ValueError(
                "UPDATED_SINCE_OVERLAP requires overlap_seconds and stable_version_field; "
                "a single maximum timestamp can miss ties or late changes"
            )
        return self


class RateLimit(StrictModel):
    requests: int = Field(ge=1)
    window_seconds: int = Field(ge=1)
    scope: ShortStr | None = Field(default=None, description="e.g. per account, per endpoint.")


class RetrySemantics(StrictModel):
    max_attempts: int = Field(ge=1)
    backoff: BackoffStrategy
    retry_on: list[ShortStr] = Field(default_factory=list, description="Provider statuses or codes that are retried.")
    reconcile_writes_before_retry: bool = Field(
        default=True, description="Uncertain writes are reconciled before any retry (Appendix A section 3)."
    )


class StateCapture(StrictModel):
    """Before/after record of a configuration change in the customer's application (section 10)."""

    operation_name: Identifier
    before_state_ref: NonSecretRef
    after_state_ref: NonSecretRef
    affected_resources: list[ShortStr] = Field(min_length=1)
    expected_effect: NonEmptyStr
    reversal_limits: NonEmptyStr


class IntegrationSpec(ArtifactHeader):
    """Everything needed to operate one adapter against one account (PL-020..PL-022)."""

    kind: Literal[ArtifactKind.INTEGRATION_SPEC] = ArtifactKind.INTEGRATION_SPEC
    integration_id: Identifier
    source: SourceRef
    operations: list[IntegrationOperation] = Field(min_length=1)
    authentication_ref: NonSecretRef = Field(description="Reference resolved by the gateway; never a credential.")
    required_scopes: list[ShortStr] = Field(default_factory=list)
    schema_mappings: list[FieldMapping] = Field(default_factory=list)
    cursor_strategy: CursorStrategy
    rate_limits: list[RateLimit] = Field(default_factory=list)
    retry_semantics: RetrySemantics
    deletion_behavior: DeletionBehavior
    verification_probes: list[NonSecretIdentifier] = Field(
        default_factory=list, description="Every probe receipt the operations' verification_probe_refs cite."
    )
    schema_drift_handling: SchemaDriftHandling
    contract_tests_passed: list[Identifier] = Field(default_factory=list)
    activated: bool = False
    before_after_state_refs: list[StateCapture] = Field(default_factory=list)

    @property
    def has_write_operations(self) -> bool:
        return any(operation.direction is OperationDirection.WRITE for operation in self.operations)

    def missing_contract_tests(self) -> set[str]:
        """Contract tests still required before this adapter may be activated (PL-022)."""
        required = set(REQUIRED_CONTRACT_TESTS)
        if self.has_write_operations:
            required |= WRITE_CONTRACT_TESTS
        return required - set(self.contract_tests_passed)

    @model_validator(mode="after")
    def _coherent_spec(self) -> "IntegrationSpec":
        names = [operation.name for operation in self.operations]
        if len(set(names)) != len(names):
            raise ValueError("operation names must be unique")
        if len(set(self.contract_tests_passed)) != len(self.contract_tests_passed):
            raise ValueError("contract_tests_passed must not contain duplicates")
        probes = set(self.verification_probes)
        for operation in self.operations:
            unknown = sorted(set(operation.verification_probe_refs) - probes)
            if unknown:
                raise ValueError(f"operation {operation.name} cites probes not in verification_probes: {unknown}")
        targets = [mapping.target_field for mapping in self.schema_mappings]
        if len(set(targets)) != len(targets):
            raise ValueError("schema_mappings must not map two source fields onto the same target field")
        captured = {capture.operation_name for capture in self.before_after_state_refs}
        for operation in self.operations:
            if operation.configuration_change and operation.name not in captured:
                raise ValueError(
                    f"configuration change {operation.name} requires a before/after StateCapture "
                    "(before_after_state_refs)"
                )
        unknown_captures = sorted(captured - set(names))
        if unknown_captures:
            raise ValueError(f"before_after_state_refs name unknown operations: {unknown_captures}")
        if self.activated:
            missing = sorted(self.missing_contract_tests())
            if missing:
                raise ValueError(f"cannot activate: contract tests not passed: {', '.join(missing)}")
            unprobed = [operation.name for operation in self.operations if not operation.verification_probe_refs]
            if unprobed:
                raise ValueError(
                    f"cannot activate: operations without a verification probe: {', '.join(unprobed)}; "
                    "a documented endpoint is not a verified capability"
                )
            if self.has_write_operations and not self.retry_semantics.reconcile_writes_before_retry:
                raise ValueError("cannot activate a write adapter that retries without reconciling uncertain writes")
        return self


__all__ = [
    "REQUIRED_CONTRACT_TESTS",
    "WRITE_CONTRACT_TESTS",
    "IntegrationPath",
    "MaintenanceExposure",
    "NullSemantics",
    "CursorKind",
    "BackoffStrategy",
    "DeletionBehavior",
    "SchemaDriftHandling",
    "UnitSemantics",
    "CurrencySemantics",
    "TimezoneSemantics",
    "FieldMapping",
    "IntegrationOperation",
    "CursorStrategy",
    "RateLimit",
    "RetrySemantics",
    "StateCapture",
    "IntegrationSpec",
]
