"""EvidencePacket: events, derived facts, object resolution and links (specification section 6).

Implements:

* PL-009: every :class:`EvidenceEvent` preserves source identity, external
  record id and version, the three time axes (event, observation,
  availability), a content digest, a *reference* to the raw content, the access
  policy reference, retention class and extraction version. The tenant is the
  packet's tenant. Raw content is referenced, never copied.
* PL-010: every :class:`DerivedFact` carries at least one supporting evidence
  id, a derivation version, a validity interval and a status from the closed
  :class:`~plumb.contracts.common.FactStatus` vocabulary. Confidence is a
  number in [0, 1] and never substitutes for authority: a fact may only be
  ``CONFIRMED`` when at least one supporting event comes from a source the
  packet lists as authoritative. Unknown absence stays distinguishable from
  confirmed absence through :class:`~plumb.contracts.common.Presence`, and
  ``CONFIRMED_ABSENT`` is itself a confirmation: it requires status
  ``CONFIRMED`` (hence authoritative evidence); an inferred absence is
  ``UNKNOWN`` presence, however high its confidence.
* PL-011: :class:`ObjectResolution` keeps ambiguous candidates with scores,
  merge/split history and reversible :class:`ScopedCorrection` records. A
  correction names the objects it applies to and the impact set to revalidate;
  there is no construction that changes a meaning globally.
* Section 6 (identity and time): externally assigned ids are kept; a
  provisional id can never be marked a confirmed financial identity.
  :meth:`EvidencePacket.facts_as_of` applies the knowledge boundary: for a
  decision at time *t*, only facts whose supporting evidence was available at
  *t* count, so a later correction cannot be treated as then-available.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from plumb.contracts.common import (
    ArtifactHeader,
    ArtifactKind,
    FactStatus,
    Identifier,
    NonEmptyStr,
    Presence,
    SemVer,
    Sha256Digest,
    ShortStr,
    NonSecretRef,
    SourceRef,
    StorageRef,
    StrictModel,
    TimeAxes,
)

FactValue = str | int | float | bool | None
"""JSON scalar carried by a fact; structured values are separate facts."""


class EvidenceEvent(StrictModel):
    """One observed record from one source at one point in time (PL-009)."""

    event_id: Identifier
    source: SourceRef
    external_record_id: ShortStr = Field(description="Identifier the source assigned to the record.")
    external_version: ShortStr = Field(description="Source-assigned version, etag or revision of the record.")
    time: TimeAxes = Field(description="Event, observation and availability time.")
    content_digest: Sha256Digest
    raw_content_ref: StorageRef = Field(
        description="Locator of the stored raw content (scheme://path); never the content itself (PL-009)."
    )
    access_policy_ref: NonSecretRef
    retention_class: ShortStr
    extraction_version: SemVer
    object_ids: list[Identifier] = Field(
        default_factory=list, description="Business objects this event relates to (many-to-many)."
    )

    @model_validator(mode="after")
    def _distinct_objects(self) -> "EvidenceEvent":
        if len(set(self.object_ids)) != len(self.object_ids):
            raise ValueError("object_ids must not contain duplicates")
        return self


class DerivedFact(StrictModel):
    """A statement derived from evidence; status and presence are explicit (PL-010)."""

    fact_id: Identifier
    subject_object_id: Identifier
    predicate: Identifier = Field(description="What is asserted about the subject, e.g. total_amount_minor.")
    value: FactValue = Field(default=None)
    supporting_evidence_ids: list[Identifier] = Field(min_length=1)
    derivation_version: SemVer
    valid_from: AwareDatetime
    valid_to: AwareDatetime | None = None
    status: FactStatus
    presence: Presence
    confidence: float = Field(ge=0.0, le=1.0, description="Derivation confidence; never a substitute for authority.")

    @model_validator(mode="after")
    def _coherent_fact(self) -> "DerivedFact":
        if len(set(self.supporting_evidence_ids)) != len(self.supporting_evidence_ids):
            raise ValueError("supporting_evidence_ids must not contain duplicates")
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError("valid_to cannot precede valid_from")
        if self.presence is Presence.PRESENT and self.value is None:
            raise ValueError("a PRESENT fact must carry a value")
        if self.presence is not Presence.PRESENT and self.value is not None:
            raise ValueError(f"a {self.presence.value} fact cannot carry a value; absence has no value")
        if self.status is FactStatus.CONFIRMED and self.presence is Presence.UNKNOWN:
            raise ValueError("a CONFIRMED fact cannot have UNKNOWN presence; unknown absence is not confirmed absence")
        if self.presence is Presence.CONFIRMED_ABSENT and self.status is not FactStatus.CONFIRMED:
            raise ValueError(
                f"CONFIRMED_ABSENT requires status CONFIRMED, not {self.status.value}; an inferred absence is "
                "UNKNOWN presence, because confidence does not substitute for source authority (PL-010)"
            )
        return self


class ExternalId(StrictModel):
    """An identifier assigned by an external system, kept as assigned (section 6)."""

    system: ShortStr = Field(description="Namespace that assigned the id, e.g. the provider or ledger.")
    value: ShortStr
    provisional: bool = Field(default=False, description="True when Plumb assigned or inferred the id.")
    confirmed_financial_identity: bool = Field(
        default=False, description="True only for the source-confirmed financial or customer identity."
    )

    @model_validator(mode="after")
    def _provisional_is_not_confirmed(self) -> "ExternalId":
        if self.provisional and self.confirmed_financial_identity:
            raise ValueError(
                "a provisional id cannot be marked confirmed_financial_identity; "
                "provisional ids must not be substituted for confirmed identities"
            )
        return self


class ResolutionCandidate(StrictModel):
    """One possible identity for an object, with the score that supports it (PL-011)."""

    candidate_object_id: Identifier
    score: float = Field(ge=0.0, le=1.0)
    rationale: ShortStr | None = None


class MergeRecord(StrictModel):
    """Objects absorbed into this one; the absorbed ids stay recorded so the merge is reversible."""

    merged_at: AwareDatetime
    absorbed_object_ids: list[Identifier] = Field(min_length=1)
    reason: NonEmptyStr
    correction_id: Identifier | None = Field(default=None, description="Scoped correction that caused the merge.")


class SplitRecord(StrictModel):
    """This object was split into the listed objects."""

    split_at: AwareDatetime
    resulting_object_ids: list[Identifier] = Field(min_length=2)
    reason: NonEmptyStr
    correction_id: Identifier | None = None


class ScopedCorrection(StrictModel):
    """A reversible correction to the meaning of an object within an explicit scope (PL-011).

    ``scope_object_ids`` is non-empty by construction: a correction always names
    the contexts it applies to, so "Square" corrected in one engagement cannot
    rewrite every occurrence of the word.
    """

    correction_id: Identifier
    scope_object_ids: list[Identifier] = Field(min_length=1)
    old_meaning: NonEmptyStr
    new_meaning: NonEmptyStr
    impact_set: list[Identifier] = Field(
        default_factory=list, description="Facts, datasets and plans to revalidate after the correction."
    )
    applied_at: AwareDatetime
    reversible: bool = True

    @model_validator(mode="after")
    def _reversible_and_meaningful(self) -> "ScopedCorrection":
        if not self.reversible:
            raise ValueError("corrections must be reversible (PL-011)")
        if self.old_meaning == self.new_meaning:
            raise ValueError("new_meaning must differ from old_meaning")
        if len(set(self.scope_object_ids)) != len(self.scope_object_ids):
            raise ValueError("scope_object_ids must not contain duplicates")
        return self


class ObjectResolution(StrictModel):
    """The resolved identity of one business object and its history (PL-011)."""

    object_id: Identifier
    object_type: ShortStr = Field(description="client, period, document, obligation, action, ...")
    external_ids: list[ExternalId] = Field(default_factory=list)
    candidates: list[ResolutionCandidate] = Field(
        default_factory=list, description="Ambiguous alternatives still under consideration."
    )
    merge_history: list[MergeRecord] = Field(default_factory=list)
    split_history: list[SplitRecord] = Field(default_factory=list)
    corrections: list[ScopedCorrection] = Field(default_factory=list)

    @model_validator(mode="after")
    def _coherent_resolution(self) -> "ObjectResolution":
        candidate_ids = [candidate.candidate_object_id for candidate in self.candidates]
        if len(set(candidate_ids)) != len(candidate_ids):
            raise ValueError("candidates must have distinct candidate_object_ids")
        if self.object_id in candidate_ids:
            raise ValueError("an object cannot be its own resolution candidate")
        external_keys = [(external.system, external.value) for external in self.external_ids]
        if len(set(external_keys)) != len(external_keys):
            raise ValueError("external_ids must be distinct per (system, value)")
        for correction in self.corrections:
            if self.object_id not in correction.scope_object_ids:
                raise ValueError(
                    f"correction {correction.correction_id} attached to {self.object_id} must include it in scope"
                )
        return self

    @property
    def confirmed_financial_ids(self) -> list[ExternalId]:
        return [external for external in self.external_ids if external.confirmed_financial_identity]


class ObjectLink(StrictModel):
    """Directed many-to-many relation between events and business objects (section 6)."""

    from_object_id: Identifier
    to_object_id: Identifier
    relation: Identifier = Field(description="e.g. belongs_to_client, covers_period, evidences_obligation.")

    @model_validator(mode="after")
    def _distinct_endpoints(self) -> "ObjectLink":
        if self.from_object_id == self.to_object_id:
            raise ValueError("a link cannot relate an object to itself")
        return self


class EvidencePacket(ArtifactHeader):
    """Evidence, derived facts, resolved objects and links for one tenant (PL-009, PL-010, PL-011)."""

    kind: Literal[ArtifactKind.EVIDENCE_PACKET] = ArtifactKind.EVIDENCE_PACKET
    packet_id: Identifier
    authoritative_source_ids: list[Identifier] = Field(
        default_factory=list,
        description="Sources the owner designated as authoritative; nothing is authoritative by default.",
    )
    events: list[EvidenceEvent] = Field(default_factory=list)
    facts: list[DerivedFact] = Field(default_factory=list)
    object_resolutions: list[ObjectResolution] = Field(default_factory=list)
    links: list[ObjectLink] = Field(default_factory=list)
    external_object_ids: list[Identifier] = Field(
        default_factory=list, description="Objects resolved in another packet that links or facts may reference."
    )

    @model_validator(mode="after")
    def _referential_integrity(self) -> "EvidencePacket":
        event_ids = [event.event_id for event in self.events]
        if len(set(event_ids)) != len(event_ids):
            raise ValueError("event_id values must be unique within a packet")
        fact_ids = [fact.fact_id for fact in self.facts]
        if len(set(fact_ids)) != len(fact_ids):
            raise ValueError("fact_id values must be unique within a packet")
        object_ids = [resolution.object_id for resolution in self.object_resolutions]
        if len(set(object_ids)) != len(object_ids):
            raise ValueError("object_id values must be unique within a packet")
        known_objects = set(object_ids)
        external = set(self.external_object_ids)
        if known_objects & external:
            raise ValueError("external_object_ids must not overlap with resolved object ids")
        known_endpoints = known_objects | external
        events_by_id = {event.event_id: event for event in self.events}

        for event in self.events:
            missing = sorted(set(event.object_ids) - known_endpoints)
            if missing:
                raise ValueError(f"event {event.event_id} references unknown objects: {', '.join(missing)}")

        authoritative = set(self.authoritative_source_ids)
        for fact in self.facts:
            missing = sorted(set(fact.supporting_evidence_ids) - events_by_id.keys())
            if missing:
                raise ValueError(f"fact {fact.fact_id} cites evidence not in the packet: {', '.join(missing)}")
            if fact.subject_object_id not in known_endpoints:
                raise ValueError(f"fact {fact.fact_id} is about unknown object {fact.subject_object_id}")
            if fact.status is FactStatus.CONFIRMED and not any(
                events_by_id[event_id].source.source_id in authoritative for event_id in fact.supporting_evidence_ids
            ):
                raise ValueError(
                    f"fact {fact.fact_id} is CONFIRMED without evidence from an authoritative source; "
                    "confidence does not substitute for source authority"
                )

        link_endpoints = known_endpoints | events_by_id.keys()
        for link in self.links:
            for endpoint in (link.from_object_id, link.to_object_id):
                if endpoint not in link_endpoints:
                    raise ValueError(
                        f"link {link.relation} endpoint {endpoint} is neither resolved, an event, nor declared external"
                    )
        return self

    def facts_as_of(self, knowledge_time: datetime) -> list[DerivedFact]:
        """Facts whose every supporting event was available at ``knowledge_time``.

        This is the knowledge boundary for replay (section 6): a fact derived
        from evidence that arrived later is not then-available knowledge, even
        if its valid time lies before ``knowledge_time``.
        """
        if knowledge_time.tzinfo is None:
            raise ValueError("knowledge_time must be timezone-aware")
        availability = {event.event_id: event.time.availability_time for event in self.events}
        return [
            fact
            for fact in self.facts
            if all(availability[event_id] <= knowledge_time for event_id in fact.supporting_evidence_ids)
        ]

    def resolution(self, object_id: str) -> ObjectResolution:
        for candidate in self.object_resolutions:
            if candidate.object_id == object_id:
                return candidate
        raise KeyError(object_id)


__all__ = [
    "FactValue",
    "EvidenceEvent",
    "DerivedFact",
    "ExternalId",
    "ResolutionCandidate",
    "MergeRecord",
    "SplitRecord",
    "ScopedCorrection",
    "ObjectResolution",
    "ObjectLink",
    "EvidencePacket",
]
