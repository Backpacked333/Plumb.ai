"""Autonomy envelope: the authority boundary every derived task is compiled against.

Implements (specification v0.2):

* PL-005: the envelope defines goals, authorized source scope, approved
  destinations/processors, allowed effect classes, spending limits, deployment
  environments, allowed regions, expiry and escalation conditions. It is
  versioned (``envelope_version``) and tied to an authorized business owner
  (``owner`` must be a ``HUMAN_OWNER``). A derived task cannot widen it: the
  reference checker compares a plan's scope against :meth:`AutonomyEnvelope.scope`.
* PL-040 / section 17: approvals bind to a policy version and expire; the
  envelope carries ``policy_version``, ``expires_at`` and ``revoked_at`` so that
  :meth:`AutonomyEnvelope.is_active` can be evaluated at any instant. Expiry is
  exclusive (inactive at and after ``expires_at``). Revocation is an *event
  that has happened*: a non-null ``revoked_at`` makes the envelope inactive at
  every instant ("revocation invalidates cached grants and queued dispatches"),
  which is also how the plan checker reads it (``ENVELOPE_INACTIVE``). A
  scheduled future revocation is expressed by issuing a new version with an
  earlier ``expires_at``, never by a ``revoked_at`` in the future.
* Section 4 / Appendix A section 1: the envelope is authority, so it cannot be
  produced by the agent it constrains; ``producer`` is never a build or runtime
  agent, in parity with :class:`~plumb.contracts.approval.ApprovalRecord`.
  Every :class:`SourceGrant` has a stable identity (``grant_id``, defaulting to
  ``grant:<source_id>:<policy_version>``) that dataset rows and manifests cite
  as their ``purpose_authorization_ref`` / ``source_rights_refs``.
* PL-053: data-purpose authorization is per source grant, not a tenant-wide
  checkbox. :meth:`AutonomyEnvelope.purposes_for` returns exactly the purposes
  granted for one source by grants that are unexpired at the evaluation time;
  permission to ``TRAIN`` is never inferred from ``INSPECT`` or ``COLLECT``.

This module is a data contract. It validates purely local facts; cross-artifact
rules (plan scope within envelope scope, budget within spending limit) belong to
``plumb.checker.plan_checker`` so that they can be reported as findings.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from plumb.contracts.common import (
    AGENT_PRINCIPAL_TYPES,
    HUMAN_PRINCIPAL_TYPES,
    ArtifactHeader,
    ArtifactKind,
    DataPurpose,
    EffectClass,
    Identifier,
    Money,
    NonEmptyStr,
    NonSecretIdentifier,
    Principal,
    PrincipalType,
    Region,
    ResourceScope,
    SemVer,
    ShortStr,
    StrictModel,
    require_aware,
)

_require_aware = require_aware


def _unique(values: list[object], field_name: str) -> None:
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")


class Goal(StrictModel):
    """A business goal the owner has authorized Plumb to pursue (PL-005)."""

    goal_id: Identifier
    objective: NonEmptyStr = Field(description="What the owner wants changed, in business terms.")
    success_metric: NonEmptyStr | None = Field(
        default=None, description="How the outcome will be measured prospectively, if already known."
    )
    horizon_days: int | None = Field(default=None, ge=1, description="Measurement horizon in days.")


class SourceGrant(StrictModel):
    """An actual customer grant to use one source for specific purposes (PL-005, PL-053).

    A grant is the unit of data-purpose authority. It names who granted it,
    when, under which policy version, and optionally when it expires. Derived
    data inherits these restrictions; nothing in this package infers a purpose
    that is not listed here.
    """

    grant_id: NonSecretIdentifier | None = Field(
        default=None,
        description="Stable identity datasets cite as their authorization; defaults to grant:<source_id>:<policy_version>.",
    )
    source_id: Identifier
    purposes: list[DataPurpose] = Field(min_length=1)
    granted_by: Principal
    granted_at: AwareDatetime
    expires_at: AwareDatetime | None = None
    policy_version: SemVer

    @property
    def effective_grant_id(self) -> str:
        """``grant_id`` when set, else the derived ``grant:<source_id>:<policy_version>``."""
        return self.grant_id if self.grant_id is not None else f"grant:{self.source_id}:{self.policy_version}"

    @model_validator(mode="after")
    def _check_grant(self) -> "SourceGrant":
        _unique(list(self.purposes), "purposes")
        if self.granted_by.principal_type not in HUMAN_PRINCIPAL_TYPES:
            raise ValueError(
                "granted_by must be a human principal; an agent or service cannot grant source access"
            )
        if self.expires_at is not None and self.expires_at <= self.granted_at:
            raise ValueError("expires_at must be after granted_at")
        return self

    def is_active(self, now: datetime) -> bool:
        """True when the grant has started and has not expired at ``now``."""
        _require_aware(now, "now")
        if now < self.granted_at:
            return False
        return self.expires_at is None or now < self.expires_at


class AutonomyEnvelope(ArtifactHeader):
    """The versioned authority an accountable human owner delegates to Plumb (PL-005).

    ``envelope_id`` always equals ``artifact_id``: the envelope is itself the
    stored artifact, and ``envelope_version`` tracks its immutable versions.
    """

    kind: Literal[ArtifactKind.AUTONOMY_ENVELOPE] = ArtifactKind.AUTONOMY_ENVELOPE
    envelope_id: Identifier
    envelope_version: int = Field(ge=1)
    owner: Principal = Field(description="The accountable business owner; must be a HUMAN_OWNER.")
    goals: list[Goal] = Field(min_length=1)
    source_grants: list[SourceGrant] = Field(default_factory=list)
    approved_destinations: list[Identifier] = Field(default_factory=list)
    approved_processors: list[Identifier] = Field(default_factory=list)
    allowed_effect_classes: list[EffectClass] = Field(min_length=1)
    spending_limit: Money
    per_step_attempt_limit: int = Field(ge=1, le=1000)
    deployment_environments: list[ShortStr] = Field(default_factory=list)
    allowed_regions: list[Region] = Field(default_factory=list)
    expires_at: AwareDatetime
    escalation_conditions: list[NonEmptyStr] = Field(default_factory=list)
    policy_version: SemVer
    revoked_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def _check_envelope(self) -> "AutonomyEnvelope":
        if self.envelope_id != self.artifact_id:
            raise ValueError("envelope_id must equal artifact_id")
        if self.owner.principal_type != PrincipalType.HUMAN_OWNER:
            raise ValueError("owner must be a HUMAN_OWNER principal")
        if self.producer.principal_type in AGENT_PRINCIPAL_TYPES:
            raise ValueError(
                "an autonomy envelope cannot be produced by a build or runtime agent; a derived task cannot "
                "mint or widen the authority it is compiled against (PL-005, Appendix A section 1)"
            )
        if self.spending_limit.minor_units <= 0:
            raise ValueError("spending_limit must be a positive amount")
        if self.expires_at <= self.created_at:
            raise ValueError("expires_at must be after created_at")
        if self.revoked_at is not None and self.revoked_at < self.created_at:
            raise ValueError("revoked_at cannot precede created_at")
        _unique(list(self.allowed_effect_classes), "allowed_effect_classes")
        _unique([goal.goal_id for goal in self.goals], "goals[].goal_id")
        _unique(list(self.approved_destinations), "approved_destinations")
        _unique(list(self.approved_processors), "approved_processors")
        _unique(list(self.allowed_regions), "allowed_regions")
        _unique(list(self.deployment_environments), "deployment_environments")
        _unique([grant.grant_id for grant in self.source_grants if grant.grant_id is not None], "source_grants[].grant_id")
        for grant in self.source_grants:
            if grant.expires_at is not None and grant.expires_at <= self.created_at:
                raise ValueError(
                    f"source grant for {grant.source_id} is already expired at the envelope's created_at"
                )
        return self

    def grants_by_id(self, grant_id: str, now: datetime | None = None) -> list[SourceGrant]:
        """Active grants whose :attr:`SourceGrant.effective_grant_id` is ``grant_id``.

        Several grants for one source under one policy version share the derived
        id; they necessarily name the same source, so a consumer unions their
        purposes. Empty when no active grant carries the id.
        """
        return [grant for grant in self.active_grants(now) if grant.effective_grant_id == grant_id]

    # -- time-dependent queries -------------------------------------------------

    def _evaluation_time(self, now: datetime | None) -> datetime:
        """The instant grants are evaluated at: ``now`` or, by default, the envelope's issuance."""
        if now is None:
            return self.created_at
        return _require_aware(now, "now")

    def is_active(self, now: datetime) -> bool:
        """True when the envelope is in force at ``now`` and has not been revoked (PL-005, PL-040).

        Revocation is an event that has happened: any ``revoked_at`` makes the
        envelope inactive at every instant, matching the plan checker's
        ``ENVELOPE_INACTIVE`` rule.
        """
        _require_aware(now, "now")
        if self.revoked_at is not None:
            return False
        return self.created_at <= now < self.expires_at

    def active_grants(self, now: datetime | None = None) -> list[SourceGrant]:
        """Grants that are in force at ``now`` (default: the envelope's ``created_at``)."""
        at = self._evaluation_time(now)
        return [grant for grant in self.source_grants if grant.is_active(at)]

    def scope(self, now: datetime | None = None) -> ResourceScope:
        """The outer resource scope a derived task may not exceed (PL-005).

        Sources come from the grants in force at ``now``; destinations,
        processors and regions are the approved lists.
        """
        source_ids: list[str] = []
        for grant in self.active_grants(now):
            if grant.source_id not in source_ids:
                source_ids.append(grant.source_id)
        return ResourceScope(
            source_ids=source_ids,
            destination_ids=list(self.approved_destinations),
            processor_ids=list(self.approved_processors),
            regions=list(self.allowed_regions),
        )

    def purposes_for(self, source_id: str, now: datetime | None = None) -> set[DataPurpose]:
        """Purposes granted for ``source_id`` by grants unexpired at ``now`` (PL-053).

        Returns the union over matching grants and nothing else: ``TRAIN`` is
        never inferred from ``INSPECT`` or ``COLLECT``. An unknown source yields
        the empty set.
        """
        purposes: set[DataPurpose] = set()
        for grant in self.active_grants(now):
            if grant.source_id == source_id:
                purposes.update(grant.purposes)
        return purposes


__all__ = ["HUMAN_PRINCIPAL_TYPES", "Goal", "SourceGrant", "AutonomyEnvelope"]
