"""ReleaseManifest: the immutable binding of everything a release deploys (specification sections 14, 19).

Implements:

* PL-046: the manifest binds workflow, connector, collector, model, prompt,
  policy, schema, infrastructure and evaluation versions through immutable
  digests. Every required component key is present; a component is either a
  pinned :class:`~plumb.contracts.common.ArtifactRef` or an explicit
  ``omitted_reason``, never silently absent. Attestations and approvals are
  bound by digest too (``attestation_refs``, ``approval_refs``). Whether those
  attestations were produced for the same bytes and scope is decided by
  :func:`plumb.checker.release_checker.check_release`.
* PL-034 / ADR-008: when a model component is present, ``resolved_model_version``
  must name an immutable version (a numeric registry version or a digest).
  Mutable aliases such as ``latest``, ``champion`` or ``prod`` are rejected so
  that one customer case can never silently switch model behaviour.
* PL-047: the rollout policy is an ordered list of stages SHADOW < CANARY <
  ACTIVE, each with a gate, an environment and a bounded case fraction (a
  canary is bounded, so its fraction is strictly below 1). ``in_flight_pinning``
  must be true: in-flight cases stay pinned to the release they started on
  unless an explicit migration is validated outside this contract.

``approval_subject_digest`` is the digest an approval of this release binds to:
the manifest content without ``content_digest`` and without ``approval_refs``,
because the approval references themselves cannot be part of the bytes the
approver signed off on.
"""

from __future__ import annotations

import re
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from plumb.contracts.approval import require_aware
from plumb.contracts.common import (
    ArtifactHeader,
    ArtifactKind,
    ArtifactRef,
    EffectClass,
    Identifier,
    NonEmptyStr,
    ReleaseState,
    ResourceScope,
    ShortStr,
    StrictModel,
    digest_json,
)

REQUIRED_COMPONENTS: tuple[str, ...] = (
    "workflow",
    "connector",
    "collector",
    "model",
    "prompt",
    "policy",
    "schema",
    "infrastructure",
    "evaluation",
)
"""Component keys every manifest must carry, present or explicitly omitted (PL-046)."""

COMPONENT_KINDS: dict[str, frozenset[ArtifactKind]] = {
    "workflow": frozenset({ArtifactKind.WORKFLOW_SPEC}),
    "connector": frozenset({ArtifactKind.INTEGRATION_SPEC, ArtifactKind.ADAPTER_CODE, ArtifactKind.ADAPTER_CONFIGURATION}),
    "collector": frozenset({ArtifactKind.COLLECTION_SPEC}),
    "model": frozenset({ArtifactKind.MODEL_VERSION}),
    "infrastructure": frozenset({ArtifactKind.INFRASTRUCTURE_PLAN}),
    "evaluation": frozenset({ArtifactKind.EVALUATION_REPORT}),
}
"""Artifact kinds a component key may reference; keys absent here (prompt, policy, schema) are unconstrained."""

ROLLOUT_STAGE_ORDER: dict[ReleaseState, int] = {
    ReleaseState.SHADOW: 0,
    ReleaseState.CANARY: 1,
    ReleaseState.ACTIVE: 2,
}
"""Stages a rollout policy may contain, in the only order they may appear (PL-047)."""

MODEL_ALIAS_WORDS: frozenset[str] = frozenset(
    {"latest", "champion", "challenger", "prod", "production", "staging", "stable", "current", "default", "canary", "live"}
)
"""Mutable registry aliases that never identify a model version (PL-034, ADR-008)."""

_IMMUTABLE_MODEL_VERSION = re.compile(
    r"^(?:"
    r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}"  # registry model name ...
    r"(?:"
    r":v?\d+(?:\.\d+){0,3}"  # ... :12  :v3  :1.2.3
    r"|/versions?/\d+"  # ... /versions/12
    r"|@sha256:[0-9a-f]{64}"  # ... @sha256:<digest>
    r")"
    r"|sha256:[0-9a-f]{64}"  # or a bare content digest
    r")$"
)

RolloutStageState = Literal[ReleaseState.SHADOW, ReleaseState.CANARY, ReleaseState.ACTIVE]
CaseFraction = Annotated[float, Field(ge=0.0, le=1.0)]
Threshold = Annotated[float, Field(ge=0.0, le=1.0)]


def is_immutable_model_version(value: str) -> bool:
    """True when ``value`` pins a model to a numeric version or digest rather than an alias."""
    if not _IMMUTABLE_MODEL_VERSION.match(value):
        return False
    tail = re.split(r"[:@/]", value)[-1].lower()
    return tail not in MODEL_ALIAS_WORDS


class ReleaseComponent(StrictModel):
    """A component slot: either a pinned artifact or an explicit reason for its absence (PL-046)."""

    ref: ArtifactRef | None = None
    omitted_reason: NonEmptyStr | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> "ReleaseComponent":
        if (self.ref is None) == (self.omitted_reason is None):
            raise ValueError("a component is either a pinned ref or an omitted_reason, exactly one (PL-046)")
        return self

    @property
    def present(self) -> bool:
        return self.ref is not None


class RolloutStage(StrictModel):
    """One rollout stage with its gate, environment and bounded case fraction (PL-047)."""

    state: RolloutStageState
    gate: NonEmptyStr = Field(description="Condition that must hold before entering this stage.")
    environment: ShortStr = Field(description="Environment this stage runs in; attestations must cover it.")
    max_case_fraction: CaseFraction = Field(description="Upper bound on the fraction of eligible cases routed here.")

    @model_validator(mode="after")
    def _bounded(self) -> "RolloutStage":
        if self.state is ReleaseState.CANARY and not 0.0 < self.max_case_fraction < 1.0:
            raise ValueError(
                f"a canary is bounded: max_case_fraction must be strictly between 0 and 1, got {self.max_case_fraction} (PL-047)"
            )
        if self.state is ReleaseState.ACTIVE and self.max_case_fraction <= 0.0:
            raise ValueError("an ACTIVE stage must route a positive fraction of cases")
        return self


class ReleaseManifest(ArtifactHeader):
    """Everything a release deploys, bound by digest, with its rollout policy (PL-034, PL-046, PL-047)."""

    kind: Literal[ArtifactKind.RELEASE_MANIFEST] = ArtifactKind.RELEASE_MANIFEST
    components: dict[Identifier, ReleaseComponent] = Field(
        description="Component slots keyed by name; must include every REQUIRED_COMPONENTS key."
    )
    attestation_refs: list[ArtifactRef] = Field(
        min_length=1, description="VerificationAttestation artifacts that verified the components."
    )
    approval_refs: list[ArtifactRef] = Field(
        default_factory=list, description="ApprovalRecord artifacts authorizing this release."
    )
    rollout_policy: list[RolloutStage] = Field(min_length=1)
    resolved_model_version: str | None = Field(
        default=None, description="Immutable model version in use; required iff the model component is present."
    )
    denominators: dict[Identifier, Annotated[int, Field(ge=1)]] = Field(
        default_factory=dict, description="Case counts behind every reported rate, so no rate is shown without one."
    )
    allowed_effect_classes: list[EffectClass] = Field(min_length=1)
    review_thresholds: dict[Identifier, Threshold] = Field(
        default_factory=dict, description="Fractions (0..1) above/below which a case goes to human review."
    )
    in_flight_pinning: bool = Field(
        default=True, description="In-flight cases stay on their release; must be true (PL-047)."
    )
    scope: ResourceScope = Field(
        default_factory=ResourceScope, description="Sources, destinations, processors and regions the release touches."
    )

    @field_validator("attestation_refs")
    @classmethod
    def _attestation_kinds(cls, refs: list[ArtifactRef]) -> list[ArtifactRef]:
        _require_kind(refs, ArtifactKind.VERIFICATION_ATTESTATION, "attestation_refs")
        return refs

    @field_validator("approval_refs")
    @classmethod
    def _approval_kinds(cls, refs: list[ArtifactRef]) -> list[ArtifactRef]:
        _require_kind(refs, ArtifactKind.APPROVAL_RECORD, "approval_refs")
        return refs

    @field_validator("rollout_policy")
    @classmethod
    def _stages_ordered(cls, stages: list[RolloutStage]) -> list[RolloutStage]:
        ranks = [ROLLOUT_STAGE_ORDER[stage.state] for stage in stages]
        if any(later <= earlier for earlier, later in zip(ranks, ranks[1:])):
            raise ValueError(
                "rollout_policy stages must appear once each in the order SHADOW, CANARY, ACTIVE; got "
                + ", ".join(stage.state.value for stage in stages)
                + " (PL-047)"
            )
        return stages

    @field_validator("allowed_effect_classes")
    @classmethod
    def _effect_classes_unique(cls, classes: list[EffectClass]) -> list[EffectClass]:
        if len(set(classes)) != len(classes):
            raise ValueError("allowed_effect_classes must not contain duplicates")
        return classes

    @model_validator(mode="after")
    def _check_manifest(self) -> "ReleaseManifest":
        require_aware(self.created_at, "created_at")
        missing = [key for key in REQUIRED_COMPONENTS if key not in self.components]
        if missing:
            raise ValueError(f"components must include every required key; missing: {', '.join(missing)} (PL-046)")
        for key, component in self.components.items():
            allowed = COMPONENT_KINDS.get(key)
            if component.ref is not None and allowed is not None and component.ref.kind not in allowed:
                raise ValueError(
                    f"component {key!r} references a {component.ref.kind.value}; expected one of "
                    + ", ".join(sorted(kind.value for kind in allowed))
                )
        model = self.components["model"]
        if model.present:
            if self.resolved_model_version is None:
                raise ValueError("resolved_model_version is required when the model component is present (PL-034)")
            if not is_immutable_model_version(self.resolved_model_version):
                raise ValueError(
                    f"resolved_model_version {self.resolved_model_version!r} is not an immutable version reference; "
                    "mutable aliases such as latest, champion or prod must be resolved per case (PL-034, ADR-008)"
                )
        elif self.resolved_model_version is not None:
            raise ValueError("resolved_model_version must be null when the model component is omitted")
        if not self.in_flight_pinning:
            raise ValueError(
                "in_flight_pinning must be true: in-flight cases stay pinned unless an explicit migration is validated (PL-047)"
            )
        return self

    def present_components(self) -> dict[str, ArtifactRef]:
        """Component key -> pinned ref for every component that is present."""
        return {key: component.ref for key, component in self.components.items() if component.ref is not None}

    def rollout_environments(self) -> set[str]:
        """Environments any rollout stage runs in."""
        return {stage.environment for stage in self.rollout_policy}

    def approval_subject_digest(self) -> str:
        """Digest an approval of this release binds to: the manifest without content_digest and approval_refs."""
        data = self.model_dump(mode="json")
        data.pop("content_digest", None)
        data.pop("approval_refs", None)
        return digest_json(data)


def _require_kind(refs: list[ArtifactRef], kind: ArtifactKind, field_name: str) -> None:
    wrong = sorted({ref.kind.value for ref in refs if ref.kind is not kind})
    if wrong:
        raise ValueError(f"{field_name} must reference {kind.value} artifacts only; found {', '.join(wrong)}")
    digests = [ref.digest for ref in refs]
    if len(set(digests)) != len(digests):
        raise ValueError(f"{field_name} must not reference the same digest twice")


__all__ = [
    "REQUIRED_COMPONENTS",
    "COMPONENT_KINDS",
    "ROLLOUT_STAGE_ORDER",
    "MODEL_ALIAS_WORDS",
    "RolloutStageState",
    "ReleaseComponent",
    "RolloutStage",
    "ReleaseManifest",
    "is_immutable_model_version",
]
