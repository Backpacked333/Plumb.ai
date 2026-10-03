"""Reference dataset checker (PL-026, PL-027, PL-028, PL-029, PL-030, PL-053).

``check_dataset`` inspects a persisted :class:`DatasetManifest`, optionally
against the :class:`~plumb.contracts.envelope.AutonomyEnvelope` whose grants the
manifest cites, and reports:

================================= ==================== ========= ======================================
code                              error_class          severity  rule
================================= ==================== ========= ======================================
``FUTURE_INFORMATION``            DATA_QUALITY_FAILED  ERROR     input available after the decision (PL-029)
``TARGET_LEAK``                   DATA_QUALITY_FAILED  ERROR     correction/expert decision available before
                                                                 the decision it corrects (PL-029)
``UNKNOWN_AVAILABILITY``          DATA_QUALITY_FAILED  WARNING   accepted row whose target, input or decision
                                                                 time is unknown (PL-029)
``FAITHFUL_REPLAY_NOT_CLAIMABLE`` DATA_QUALITY_FAILED  INFO      summary emitted once when any availability
                                                                 is unknown (PL-029)
``MISSING_TARGET_EVIDENCE``       DATA_QUALITY_FAILED  ERROR     accepted row without target evidence
                                                                 (defensive, PL-028)
``DUPLICATE_EXAMPLE_ID``          DATA_QUALITY_FAILED  ERROR     example ids are not stable/unique (defensive,
                                                                 PL-028)
``DUPLICATE_FAMILY_ACROSS_SPLITS`` DATA_QUALITY_FAILED ERROR     a group_id appears in more than one split
``TEMPORAL_HOLDOUT_NOT_LATER``    DATA_QUALITY_FAILED  ERROR     a test_temporal decision is not later than
                                                                 every train/validation decision (PL-030)
``QUARANTINED_ROW_IN_TRAINING``   DATA_QUALITY_FAILED  ERROR     train split row not ACCEPTED (PL-027)
``LABEL_KIND_MISMATCH``           DATA_QUALITY_FAILED  ERROR     a row's label kind differs from the manifest's
                                                                 label definition (PL-026, PL-030)
``WEAK_PROXY_IN_TRAINING``        DATA_QUALITY_FAILED  WARNING   accepted WEAK_PROXY rows in train/validation
                                                                 under a WEAK_PROXY label definition: lack of
                                                                 complaint is not correctness (PL-027)
``MISSING_EXCLUSION_REASON``      DATA_QUALITY_FAILED  ERROR     non-accepted row without a reason (PL-028)
``UNPINNED_SOURCE``               DATA_QUALITY_FAILED  ERROR     no pinned source versions (PL-030)
``COUNT_MISMATCH``                DATA_QUALITY_FAILED  ERROR     declared counts differ from rows (PL-030)
``SPLIT_WITHOUT_QUESTION``        DATA_QUALITY_FAILED  ERROR     a used split has no rule or no question
``DISALLOWED_SOURCE_USE``         PURPOSE_DENIED       ERROR     row claims an authorization the manifest does
                                                                 not carry; with an envelope: a cited grant is
                                                                 unknown or inactive, belongs to another tenant,
                                                                 does not cover the row's purpose (TRAIN for
                                                                 train/validation, EVALUATE for test splits) or
                                                                 does not name a declared source
                                                                 (PL-029, PL-053)
================================= ==================== ========= ======================================

Without an envelope the authorization rules are internal consistency only
(``details.cause == "not_in_manifest"``): every row's grant id must be among the
manifest's ``source_rights_refs``. With an envelope the grant ids are resolved
to :class:`~plumb.contracts.envelope.SourceGrant` records active at ``now``
(default: the manifest's ``created_at``) and permission to train is never
inferred from permission to inspect or collect. The checker never executes
anything and never mutates the manifest. Rules already enforced by the contract
validators (exclusion reason, split rules, unique ids, target evidence) are
re-checked so that a manifest built with ``model_construct`` or loaded from an
older schema is judged on content, not on how it was instantiated.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from plumb.checker.findings import CheckReport, Finding, Severity
from plumb.contracts.common import DataPurpose, ErrorClass, LabelKind, LabelStatus
from plumb.contracts.dataset import DatasetManifest, DatasetRow, SplitRule
from plumb.contracts.envelope import AutonomyEnvelope

CHECKER_NAME = "dataset_checker"

_LEAK_SENSITIVE_LABEL_KINDS = frozenset({LabelKind.CORRECTION, LabelKind.EXPERT_DECISION})
"""Label kinds whose target cannot legitimately exist before the decision it records."""

TRAINING_SPLITS: frozenset[str] = frozenset({"train", "validation"})
"""Splits whose rows are training inputs (fitting and model selection); they need TRAIN authority (PL-053)."""

EVALUATION_SPLITS: frozenset[str] = frozenset({"test_temporal", "test_client_disjoint"})
"""Held-out splits; their rows need EVALUATE authority (PL-053)."""


def check_dataset(
    manifest: DatasetManifest,
    envelope: AutonomyEnvelope | None = None,
    *,
    now: datetime | None = None,
) -> CheckReport:
    """Inspect ``manifest`` (and its grants against ``envelope`` when given); ``report.ok`` means no ERROR finding."""
    report = CheckReport(checker=CHECKER_NAME, subject=manifest.artifact_id)
    authorized = set(manifest.source_rights_refs)
    unknown_availability = 0
    seen_ids: set[str] = set()
    for row in manifest.rows:
        if row.example_id in seen_ids:
            _error(report, "DUPLICATE_EXAMPLE_ID", row, "example_id is repeated; example ids must be stable and unique")
        seen_ids.add(row.example_id)
        unknown_availability += _check_row(row, manifest, authorized, report)
    if envelope is not None:
        _check_grants(manifest, envelope, now, report)
    if unknown_availability:
        report.add(
            Finding(
                code="FAITHFUL_REPLAY_NOT_CLAIMABLE",
                error_class=ErrorClass.DATA_QUALITY_FAILED,
                severity=Severity.INFO,
                message=(
                    f"{unknown_availability} accepted row(s) have unknown target availability; "
                    "this revision cannot claim faithful historical replay"
                ),
                details={"rows_with_unknown_availability": unknown_availability},
            )
        )
    _check_families(manifest, report)
    _check_temporal_holdout(manifest, report)
    _check_sources(manifest, report)
    _check_counts(manifest, report)
    _check_split_rules(manifest, report)
    report.summary = _summary(manifest, report, unknown_availability, envelope)
    return report


def _check_row(row: DatasetRow, manifest: DatasetManifest, authorized: set[str], report: CheckReport) -> int:
    """Row-level rules. Returns 1 when any of the row's availability times is unknown, else 0."""
    unknown = 0
    accepted = row.label_status == LabelStatus.ACCEPTED
    if row.input_availability_time is None or row.decision_time is None:
        unknown = 1
        report.add(
            Finding(
                code="UNKNOWN_AVAILABILITY",
                error_class=ErrorClass.DATA_QUALITY_FAILED,
                severity=Severity.WARNING,
                subject_id=row.example_id,
                message="input availability or decision time is unknown; point-in-time replay is unverified",
                details={
                    "input_availability_time": _iso(row.input_availability_time),
                    "decision_time": _iso(row.decision_time),
                },
            )
        )
    elif row.input_availability_time > row.decision_time:
        _error(
            report,
            "FUTURE_INFORMATION",
            row,
            "input became available after the decision it is meant to inform",
            input_availability_time=row.input_availability_time.isoformat(),
            decision_time=row.decision_time.isoformat(),
        )
    if (
        row.label_kind in _LEAK_SENSITIVE_LABEL_KINDS
        and row.target_availability_time is not None
        and row.target_availability_time < row.decision_time
    ):
        _error(
            report,
            "TARGET_LEAK",
            row,
            f"{row.label_kind.value} target available before the decision it records",
            target_availability_time=row.target_availability_time.isoformat(),
            decision_time=row.decision_time.isoformat(),
        )
    if accepted and row.target_evidence_ref is None:
        unknown = 1
        _error(
            report,
            "MISSING_TARGET_EVIDENCE",
            row,
            "an ACCEPTED row must reference its target evidence; without it the label has no provenance",
        )
    elif accepted and row.target_availability_time is None:
        unknown = 1
        report.add(
            Finding(
                code="UNKNOWN_AVAILABILITY",
                error_class=ErrorClass.DATA_QUALITY_FAILED,
                severity=Severity.WARNING,
                subject_id=row.example_id,
                message="target evidence has no availability time; point-in-time replay is unverified",
                details={"target_evidence_ref": row.target_evidence_ref},
            )
        )
    if row.split == "train" and not accepted:
        _error(
            report,
            "QUARANTINED_ROW_IN_TRAINING",
            row,
            f"row with label_status {row.label_status.value} is in the train split",
            label_status=row.label_status.value,
        )
    definition_kind = manifest.label_definition.label_kind
    if row.label_kind is not definition_kind:
        _error(
            report,
            "LABEL_KIND_MISMATCH",
            row,
            f"row label is {row.label_kind.value} but the manifest's label definition is {definition_kind.value}; "
            "the recorded label definition must be true for every row",
            row_label_kind=row.label_kind.value,
            definition_label_kind=definition_kind.value,
        )
    elif row.label_kind is LabelKind.WEAK_PROXY and accepted and row.split in TRAINING_SPLITS:
        report.add(
            Finding(
                code="WEAK_PROXY_IN_TRAINING",
                error_class=ErrorClass.DATA_QUALITY_FAILED,
                severity=Severity.WARNING,
                subject_id=row.example_id,
                message=(
                    f"accepted WEAK_PROXY row in the {row.split} split; employee acceptance or lack of complaint "
                    "is not correctness and the label definition says so"
                ),
                details={"split": row.split},
            )
        )
    if not accepted and not (row.exclusion_reason or "").strip():
        _error(
            report,
            "MISSING_EXCLUSION_REASON",
            row,
            f"row with label_status {row.label_status.value} has no exclusion_reason",
            label_status=row.label_status.value,
        )
    if row.purpose_authorization_ref not in authorized:
        report.add(
            Finding(
                code="DISALLOWED_SOURCE_USE",
                error_class=ErrorClass.PURPOSE_DENIED,
                subject_id=row.example_id,
                message=(
                    f"row claims authorization {row.purpose_authorization_ref!r} which is not among the "
                    "manifest's source_rights_refs"
                ),
                details={"purpose_authorization_ref": row.purpose_authorization_ref, "cause": "not_in_manifest"},
            )
        )
    return unknown


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _check_grants(manifest: DatasetManifest, envelope: AutonomyEnvelope, now: datetime | None, report: CheckReport) -> None:
    """Resolve the manifest's grant ids against the envelope's active grants (PL-053)."""
    at = now if now is not None else manifest.created_at
    if manifest.tenant_id != envelope.tenant_id:
        report.add(
            Finding(
                code="DISALLOWED_SOURCE_USE",
                error_class=ErrorClass.PURPOSE_DENIED,
                subject_id=manifest.artifact_id,
                message="manifest and envelope belong to different tenants; the envelope's grants authorize nothing here",
                details={"cause": "tenant_mismatch", "manifest_tenant": manifest.tenant_id, "envelope_tenant": envelope.tenant_id},
            )
        )
        return
    declared_sources = set(manifest.source_ids)
    covered_sources: set[str] = set()
    for grant_id in manifest.source_rights_refs:
        grants = envelope.grants_by_id(grant_id, now=at)
        if not grants:
            report.add(
                Finding(
                    code="DISALLOWED_SOURCE_USE",
                    error_class=ErrorClass.PURPOSE_DENIED,
                    subject_id=manifest.artifact_id,
                    message=f"source_rights_refs names {grant_id!r}, which is not an active grant of the envelope at {at.isoformat()}",
                    details={"cause": "unknown_grant", "grant_id": grant_id, "evaluated_at": at.isoformat()},
                )
            )
            continue
        covered_sources.update(grant.source_id for grant in grants)
    for source_id in sorted(declared_sources - covered_sources):
        report.add(
            Finding(
                code="DISALLOWED_SOURCE_USE",
                error_class=ErrorClass.PURPOSE_DENIED,
                subject_id=manifest.artifact_id,
                message=f"manifest derives from source {source_id!r} but cites no active grant for it",
                details={"cause": "source_without_grant", "source_id": source_id},
            )
        )
    for row in manifest.rows:
        grants = envelope.grants_by_id(row.purpose_authorization_ref, now=at)
        if not grants:
            continue  # reported as not_in_manifest / unknown_grant already
        needed = DataPurpose.TRAIN if row.split in TRAINING_SPLITS else DataPurpose.EVALUATE
        granted: set[DataPurpose] = set()
        for grant in grants:
            granted.update(grant.purposes)
        grant_sources = sorted({grant.source_id for grant in grants})
        if needed not in granted:
            message = (
                f"row cites grant {row.purpose_authorization_ref!r}, which grants {', '.join(sorted(p.value for p in granted))} "
                f"on {', '.join(grant_sources)} but not {needed.value}, the purpose of the {row.split} split"
            )
            if needed is DataPurpose.TRAIN:
                message += "; permission to train is never inferred from permission to inspect or collect"
            report.add(
                Finding(
                    code="DISALLOWED_SOURCE_USE",
                    error_class=ErrorClass.PURPOSE_DENIED,
                    subject_id=row.example_id,
                    message=message,
                    details={
                        "cause": "purpose_not_granted",
                        "purpose_authorization_ref": row.purpose_authorization_ref,
                        "required_purpose": needed.value,
                        "granted_purposes": sorted(p.value for p in granted),
                        "grant_sources": grant_sources,
                    },
                )
            )
        if declared_sources and not set(grant_sources) <= declared_sources:
            report.add(
                Finding(
                    code="DISALLOWED_SOURCE_USE",
                    error_class=ErrorClass.PURPOSE_DENIED,
                    subject_id=row.example_id,
                    message=(
                        f"row cites grant {row.purpose_authorization_ref!r} for source(s) {', '.join(grant_sources)}, "
                        f"which the manifest does not declare among its sources ({', '.join(sorted(declared_sources))})"
                    ),
                    details={
                        "cause": "source_not_declared",
                        "purpose_authorization_ref": row.purpose_authorization_ref,
                        "grant_sources": grant_sources,
                        "declared_sources": sorted(declared_sources),
                    },
                )
            )


def _check_temporal_holdout(manifest: DatasetManifest, report: CheckReport) -> None:
    """A temporal holdout answers 'performance on future work' only when it lies after the training data (PL-030)."""
    training = [row.decision_time for row in manifest.rows if row.split in TRAINING_SPLITS and row.decision_time is not None]
    holdout = [row for row in manifest.rows if row.split == "test_temporal" and row.decision_time is not None]
    if not training or not holdout:
        return
    latest_training = max(training)
    for row in holdout:
        if row.decision_time <= latest_training:
            _error(
                report,
                "TEMPORAL_HOLDOUT_NOT_LATER",
                row,
                "test_temporal decision is not later than every train/validation decision; the split cannot claim "
                "performance on future work",
                decision_time=row.decision_time.isoformat(),
                latest_training_decision_time=latest_training.isoformat(),
            )


def _check_families(manifest: DatasetManifest, report: CheckReport) -> None:
    for group_id, splits in sorted(manifest.families().items()):
        if len(splits) > 1:
            report.add(
                Finding(
                    code="DUPLICATE_FAMILY_ACROSS_SPLITS",
                    error_class=ErrorClass.DATA_QUALITY_FAILED,
                    subject_id=group_id,
                    message=f"family {group_id} appears in splits {', '.join(sorted(splits))}",
                    details={"splits": sorted(splits)},
                )
            )


def _check_sources(manifest: DatasetManifest, report: CheckReport) -> None:
    unpinned = [ref.artifact_id for ref in manifest.source_versions if not getattr(ref, "digest", None)]
    if not manifest.source_versions:
        message = "source_versions is empty; the dataset is not reproducible from pinned sources"
    elif unpinned:
        message = f"source versions without a digest: {', '.join(unpinned)}"
    else:
        return
    report.add(
        Finding(
            code="UNPINNED_SOURCE",
            error_class=ErrorClass.DATA_QUALITY_FAILED,
            message=message,
            details={"unpinned": unpinned},
        )
    )


def _check_counts(manifest: DatasetManifest, report: CheckReport) -> None:
    actual_by_split = Counter(row.split for row in manifest.rows)
    actual_by_status = Counter(row.label_status.value for row in manifest.rows)
    declared_by_split = {str(split): count for split, count in manifest.counts.by_split.items()}
    declared_by_status = {status.value: count for status, count in manifest.counts.by_label_status.items()}
    for dimension, declared, actual in (
        ("by_split", declared_by_split, actual_by_split),
        ("by_label_status", declared_by_status, actual_by_status),
    ):
        for key in sorted(set(declared) | set(actual)):
            if declared.get(key, 0) != actual.get(key, 0):
                report.add(
                    Finding(
                        code="COUNT_MISMATCH",
                        error_class=ErrorClass.DATA_QUALITY_FAILED,
                        subject_id=f"{dimension}.{key}",
                        message=(
                            f"counts.{dimension}[{key!r}] declares {declared.get(key, 0)} row(s) "
                            f"but the manifest holds {actual.get(key, 0)}"
                        ),
                        details={"dimension": dimension, "key": key, "declared": declared.get(key, 0), "actual": actual.get(key, 0)},
                    )
                )


def _check_split_rules(manifest: DatasetManifest, report: CheckReport) -> None:
    rules: dict[str, SplitRule] = {rule.name: rule for rule in manifest.split_rules}
    for split in sorted(manifest.splits_used()):
        rule = rules.get(split)
        if rule is None:
            message = f"split {split!r} is used by rows but has no SplitRule"
        elif not (rule.question_answered or "").strip():
            message = f"split {split!r} has a rule that does not state the question it answers"
        else:
            continue
        report.add(
            Finding(
                code="SPLIT_WITHOUT_QUESTION",
                error_class=ErrorClass.DATA_QUALITY_FAILED,
                subject_id=split,
                message=message,
            )
        )


def _error(report: CheckReport, code: str, row: DatasetRow, message: str, **details: Any) -> None:
    report.add(
        Finding(
            code=code,
            error_class=ErrorClass.DATA_QUALITY_FAILED,
            subject_id=row.example_id,
            message=message,
            details=details,
        )
    )


def _summary(
    manifest: DatasetManifest, report: CheckReport, unknown_availability: int, envelope: AutonomyEnvelope | None
) -> dict[str, Any]:
    return {
        "dataset_id": manifest.dataset_id,
        "revision": manifest.revision,
        "available": manifest.is_available,
        "envelope_checked": envelope.envelope_id if envelope is not None else None,
        "weak_proxy_rows": sum(1 for row in manifest.rows if row.label_kind is LabelKind.WEAK_PROXY),
        "row_count": len(manifest.rows),
        "rows_by_split": dict(sorted(Counter(row.split for row in manifest.rows).items())),
        "rows_by_label_status": dict(sorted(Counter(row.label_status.value for row in manifest.rows).items())),
        "family_count": len(manifest.families()),
        "pinned_source_count": len(manifest.source_versions),
        "rows_with_unknown_availability": unknown_availability,
        "faithful_replay_claimable": unknown_availability == 0,
        "findings_by_code": dict(sorted(Counter(finding.code for finding in report.findings).items())),
        "errors": len(report.errors),
        "warnings": len(report.warnings),
    }


__all__ = ["CHECKER_NAME", "TRAINING_SPLITS", "EVALUATION_SPLITS", "check_dataset"]
