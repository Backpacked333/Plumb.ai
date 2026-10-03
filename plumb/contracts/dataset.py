"""Dataset manifests and rows (specification section 13).

Implements:

* PL-028: every training/evaluation row carries stable example and grouping
  ids, input snapshot references, decision time, source availability time,
  target evidence, label status, purpose authorization and an exclusion reason
  whenever the label was not accepted. The dataset revision lives on the
  manifest that owns the rows.
* PL-029: rows preserve both decision (event) time and knowledge availability
  time so that :mod:`plumb.checker.dataset_checker` can detect future
  information, near-duplicate families straddling splits and disallowed source
  uses. A row whose target availability is unknown cannot support a claim of
  faithful historical replay; the contract keeps the field nullable instead of
  inventing a timestamp.
* PL-030: a manifest is reproducible from pinned source versions and
  transformations and records split rules, schema, hashes, counts,
  distributions, rejected examples, label definition and lineage. When required
  source material has been deleted the manifest is marked unavailable through
  ``unavailable_reason`` rather than falsifying reproducibility.
* PL-027: quarantined and rejected rows remain in the manifest with their
  status and reason; they are never silently dropped.

The contract validates what must hold for *any* well-formed manifest. Rules
whose violation is a data-quality finding (future information, leaked targets,
families across splits, count mismatches, ...) are deliberately left to the
checker so that a manifest produced by a builder can be recorded and judged.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AwareDatetime, Field, field_validator, model_validator

from plumb.contracts.common import (
    ArtifactHeader,
    ArtifactKind,
    ArtifactRef,
    Identifier,
    LabelKind,
    LabelStatus,
    NonEmptyStr,
    Sha256Digest,
    StrictModel,
)

SplitName = Literal["train", "validation", "test_temporal", "test_client_disjoint"]
"""The four dataset splits. Temporal and client-disjoint holdouts answer different questions."""

NonNegativeCount = Annotated[int, Field(ge=0)]


class DatasetRow(StrictModel):
    """One training/evaluation example with its point-in-time bookkeeping (PL-028)."""

    example_id: Identifier
    group_id: Identifier = Field(
        description="Transaction/document family. Near-duplicate families must not straddle splits."
    )
    input_snapshot_refs: list[Identifier] = Field(
        min_length=1, description="Evidence event ids whose values were known at the decision boundary."
    )
    input_availability_time: AwareDatetime = Field(
        description="Latest availability time among the input snapshots (knowledge time)."
    )
    decision_time: AwareDatetime = Field(description="When the decision the row models was made.")
    target_evidence_ref: Identifier | None = Field(
        default=None, description="Evidence event id carrying the label; required for accepted rows."
    )
    target_availability_time: AwareDatetime | None = Field(
        default=None,
        description="When the target became available. None means unknown, not 'at decision time'.",
    )
    label_kind: LabelKind
    label_status: LabelStatus
    purpose_authorization_ref: Identifier = Field(
        description="Grant that permits this row's source to be used for the dataset's purpose."
    )
    split: SplitName
    exclusion_reason: NonEmptyStr | None = Field(
        default=None, description="Why the row is not an accepted example; required when not ACCEPTED."
    )

    @property
    def is_accepted(self) -> bool:
        return self.label_status == LabelStatus.ACCEPTED

    @model_validator(mode="after")
    def _status_and_target_are_consistent(self) -> "DatasetRow":
        if self.is_accepted:
            if self.target_evidence_ref is None:
                raise ValueError(
                    f"row {self.example_id}: an ACCEPTED row must reference its target evidence"
                )
        elif self.exclusion_reason is None:
            raise ValueError(
                f"row {self.example_id}: exclusion_reason is required when label_status is "
                f"{self.label_status.value}"
            )
        return self


class LabelDefinition(StrictModel):
    """What the label means and how long it takes to mature (section 13)."""

    text: NonEmptyStr = Field(description="Human-readable definition of the target.")
    label_kind: LabelKind
    maturation_window_days: int = Field(
        ge=0, description="Days after the decision before the label is considered settled."
    )


class SplitRule(StrictModel):
    """How a split is populated and which question it answers (PL-030)."""

    name: SplitName
    question_answered: NonEmptyStr = Field(
        description="E.g. 'performance on future work' or 'generalisation to unseen clients'."
    )
    rule: NonEmptyStr = Field(description="Deterministic assignment rule, e.g. a decision_time cut-off.")


class DatasetCounts(StrictModel):
    """Declared row counts; the checker compares them with the rows (PL-030)."""

    by_split: dict[SplitName, NonNegativeCount] = Field(default_factory=dict)
    by_label_status: dict[LabelStatus, NonNegativeCount] = Field(default_factory=dict)


class DatasetManifest(ArtifactHeader):
    """Immutable, reproducible description of one dataset revision (PL-028..PL-030)."""

    kind: Literal[ArtifactKind.DATASET_MANIFEST] = ArtifactKind.DATASET_MANIFEST
    dataset_id: Identifier
    revision: int = Field(ge=1, description="Dataset revision; a new revision never mutates an old one.")
    task_definition_ref: ArtifactRef = Field(description="Pinned TaskDefinition the rows were built for.")
    label_definition: LabelDefinition
    split_rules: list[SplitRule] = Field(min_length=1)
    schema_ref: Identifier = Field(description="Row schema the materialised rows conform to.")
    rows: list[DatasetRow] = Field(default_factory=list)
    counts: DatasetCounts = Field(default_factory=DatasetCounts)
    distributions: dict[str, dict[str, float]] = Field(
        default_factory=dict, description="Named distributions, e.g. label frequency per split."
    )
    content_hashes: dict[SplitName, Sha256Digest] = Field(
        default_factory=dict, description="Digest of the materialised rows of each split."
    )
    source_versions: list[ArtifactRef] = Field(
        default_factory=list, description="Pinned source artifacts the rows were derived from."
    )
    transformation_refs: list[ArtifactRef] = Field(
        default_factory=list, description="Pinned transformation code that produced the rows."
    )
    lineage_refs: list[Identifier] = Field(default_factory=list)
    source_rights_refs: list[Identifier] = Field(
        default_factory=list, description="Grants authorising the sources for the dataset's purpose."
    )
    unavailable_reason: NonEmptyStr | None = Field(
        default=None,
        description=(
            "Set when required source material was deleted and the dataset is intentionally "
            "unreconstructable; the manifest is kept and marked, never falsified."
        ),
    )

    @field_validator("task_definition_ref")
    @classmethod
    def _task_definition_kind(cls, ref: ArtifactRef) -> ArtifactRef:
        if ref.kind != ArtifactKind.TASK_DEFINITION:
            raise ValueError(f"task_definition_ref must reference a TaskDefinition, not {ref.kind.value}")
        return ref

    @model_validator(mode="after")
    def _structure_is_consistent(self) -> "DatasetManifest":
        rule_names = [rule.name for rule in self.split_rules]
        duplicates = sorted({name for name in rule_names if rule_names.count(name) > 1})
        if duplicates:
            raise ValueError(f"split_rules must name each split once; duplicated: {', '.join(duplicates)}")
        example_ids = [row.example_id for row in self.rows]
        repeated = sorted({eid for eid in example_ids if example_ids.count(eid) > 1})
        if repeated:
            raise ValueError(f"example_id must be unique within a manifest; repeated: {', '.join(repeated)}")
        unruled = sorted(self.splits_used() - set(rule_names))
        if unruled:
            raise ValueError(
                "every split used by rows needs a SplitRule stating the question it answers; "
                f"missing: {', '.join(unruled)}"
            )
        return self

    @property
    def is_available(self) -> bool:
        return self.unavailable_reason is None

    def splits_used(self) -> set[str]:
        """Names of the splits that have at least one row."""
        return {row.split for row in self.rows}

    def rows_in_split(self, split: SplitName) -> list[DatasetRow]:
        return [row for row in self.rows if row.split == split]

    def families(self) -> dict[str, set[str]]:
        """Map each ``group_id`` to the set of splits its rows appear in."""
        result: dict[str, set[str]] = {}
        for row in self.rows:
            result.setdefault(row.group_id, set()).add(row.split)
        return result


__all__ = [
    "SplitName",
    "DatasetRow",
    "LabelDefinition",
    "SplitRule",
    "DatasetCounts",
    "DatasetManifest",
]
