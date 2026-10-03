"""InfrastructurePlan: a previewed, costed, lock-protected change set (specification section 19).

Implements:

* PL-045: infrastructure is generated from approved resource templates or
  reviewed modules (``template_refs`` non-empty, each pinned by digest). A
  preview/diff (``preview_diff_ref``), cost estimate, state lock and, per
  resource, ownership tags and a rollback/compensation classification precede
  application. The plan carries ``environment`` so the deployment boundary can
  be checked against the envelope's deployment environments.
* PL-047 (rollout discipline for schema changes): database changes follow
  expand/contract (:class:`ExpandContractPhase`). Destructive migrations need
  explicit authorization and a verified backup/restore strategy: any ``DELETE``
  or ``REPLACE`` action, or any resource classified ``IRREVERSIBLE``, requires
  both ``destructive_authorization_ref`` and ``backup_restore_strategy_ref``.
  Application rollback does not restore destroyed data, which is why the
  classification is recorded per resource rather than per plan.

The plan is a description. Nothing in this package applies it.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field, field_validator, model_validator

from plumb.contracts.common import NonSecretIdentifier, NonSecretRef
from plumb.contracts.common import (
    ArtifactHeader,
    ArtifactKind,
    ArtifactRef,
    Identifier,
    Money,
    ShortStr,
    StrictModel,
)


class ChangeAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    REPLACE = "REPLACE"
    DELETE = "DELETE"


class RollbackClassification(str, Enum):
    """How a change can be undone (PL-045)."""

    ROLLBACK = "ROLLBACK"
    COMPENSATE = "COMPENSATE"
    IRREVERSIBLE = "IRREVERSIBLE"


class ExpandContractPhase(str, Enum):
    """Phase of an expand/contract migration; NONE when no schema change is involved."""

    EXPAND = "EXPAND"
    MIGRATE = "MIGRATE"
    CONTRACT = "CONTRACT"
    NONE = "NONE"


DESTRUCTIVE_ACTIONS: frozenset[ChangeAction] = frozenset({ChangeAction.DELETE, ChangeAction.REPLACE})
"""Actions that destroy or recreate a resource and therefore need explicit authorization."""


class ResourceChange(StrictModel):
    """One resource-level change with its ownership and rollback classification (PL-045)."""

    resource_id: Identifier
    action: ChangeAction
    rollback_classification: RollbackClassification
    ownership_tags: dict[ShortStr, ShortStr] = Field(
        min_length=1, description="Resource ownership tags applied on creation/update (owner, tenant, build ...)."
    )
    estimated_cost: Money

    @property
    def is_destructive(self) -> bool:
        """True for DELETE/REPLACE actions and for anything classified IRREVERSIBLE."""
        return self.action in DESTRUCTIVE_ACTIONS or self.rollback_classification is RollbackClassification.IRREVERSIBLE


class InfrastructurePlan(ArtifactHeader):
    """A change set that may be applied only after preview, costing, locking and authorization (PL-045)."""

    kind: Literal[ArtifactKind.INFRASTRUCTURE_PLAN] = ArtifactKind.INFRASTRUCTURE_PLAN
    template_refs: list[ArtifactRef] = Field(
        min_length=1, description="Approved resource templates or reviewed modules the plan was generated from."
    )
    preview_diff_ref: ArtifactRef = Field(description="The InfrastructurePreview (plan/diff) produced before application.")
    cost_estimate: Money = Field(description="Worst-case estimate for the whole plan; never below the per-resource sum.")
    state_lock_ref: NonSecretRef = Field(description="Reference to the acquired state lock, never a lock token value.")
    environment: ShortStr
    changes: list[ResourceChange] = Field(default_factory=list)
    expand_contract_phase: ExpandContractPhase
    destructive_authorization_ref: NonSecretIdentifier | None = Field(
        default=None, description="ApprovalRecord or envelope clause authorizing destructive changes."
    )
    backup_restore_strategy_ref: NonSecretIdentifier | None = Field(
        default=None, description="Verified backup/restore strategy covering the destructive changes."
    )

    @field_validator("preview_diff_ref")
    @classmethod
    def _preview_kind(cls, ref: ArtifactRef) -> ArtifactRef:
        if ref.kind is not ArtifactKind.INFRASTRUCTURE_PREVIEW:
            raise ValueError(f"preview_diff_ref must reference an InfrastructurePreview, not {ref.kind.value}")
        return ref

    @model_validator(mode="after")
    def _check_plan(self) -> "InfrastructurePlan":
        ids = [change.resource_id for change in self.changes]
        repeated = sorted({rid for rid in ids if ids.count(rid) > 1})
        if repeated:
            raise ValueError(f"resource_id must be unique within a plan; repeated: {', '.join(repeated)}")
        total = Money(minor_units=0, currency=self.cost_estimate.currency)
        for change in self.changes:
            if change.estimated_cost.currency != self.cost_estimate.currency:
                raise ValueError(
                    f"resource {change.resource_id} is estimated in {change.estimated_cost.currency} but the plan "
                    f"estimate is in {self.cost_estimate.currency}"
                )
            total = total + change.estimated_cost
        if total.exceeds(self.cost_estimate):
            raise ValueError(
                f"cost_estimate {self.cost_estimate.minor_units} is below the per-resource sum {total.minor_units}; "
                "the plan estimate is the worst case (PL-045)"
            )
        destructive = [change.resource_id for change in self.changes if change.is_destructive]
        if destructive:
            missing = [
                name
                for name, value in (
                    ("destructive_authorization_ref", self.destructive_authorization_ref),
                    ("backup_restore_strategy_ref", self.backup_restore_strategy_ref),
                )
                if value is None
            ]
            if missing:
                raise ValueError(
                    f"destructive changes ({', '.join(destructive)}) require explicit authorization and a verified "
                    f"backup/restore strategy; missing {', '.join(missing)} (PL-045)"
                )
        return self

    def destructive_changes(self) -> list[ResourceChange]:
        """Changes that need explicit authorization before application."""
        return [change for change in self.changes if change.is_destructive]


__all__ = [
    "DESTRUCTIVE_ACTIONS",
    "ChangeAction",
    "RollbackClassification",
    "ExpandContractPhase",
    "ResourceChange",
    "InfrastructurePlan",
]
