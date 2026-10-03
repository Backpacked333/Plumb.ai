"""Reference dataset checker (PL-027, PL-028, PL-029, PL-030, PL-053).

``check_dataset`` inspects a persisted :class:`DatasetManifest` and reports:

=============================== ==================== ========= ======================================
code                            error_class          severity  rule
=============================== ==================== ========= ======================================
``FUTURE_INFORMATION``          DATA_QUALITY_FAILED  ERROR     input available after the decision (PL-029)
``TARGET_LEAK``                 DATA_QUALITY_FAILED  ERROR     correction/expert decision available before
                                                               the decision it corrects (PL-029)
``UNKNOWN_AVAILABILITY``        DATA_QUALITY_FAILED  WARNING   accepted row with a target but no target
                                                               availability time (PL-029)
``FAITHFUL_REPLAY_NOT_CLAIMABLE`` DATA_QUALITY_FAILED INFO     summary emitted once when any availability
                                                               is unknown (PL-029)
``DUPLICATE_FAMILY_ACROSS_SPLITS`` DATA_QUALITY_FAILED ERROR   a group_id appears in more than one split
``QUARANTINED_ROW_IN_TRAINING`` DATA_QUALITY_FAILED  ERROR     train split row not ACCEPTED (PL-027)
``MISSING_EXCLUSION_REASON``    DATA_QUALITY_FAILED  ERROR     non-accepted row without a reason (PL-028)
``UNPINNED_SOURCE``             DATA_QUALITY_FAILED  ERROR     no pinned source versions (PL-030)
``COUNT_MISMATCH``              DATA_QUALITY_FAILED  ERROR     declared counts differ from rows (PL-030)
``SPLIT_WITHOUT_QUESTION``      DATA_QUALITY_FAILED  ERROR     a used split has no rule or no question
``DISALLOWED_SOURCE_USE``       PURPOSE_DENIED       ERROR     row claims an authorization the manifest
                                                               does not carry (PL-029, PL-053)
=============================== ==================== ========= ======================================

The checker never executes anything and never mutates the manifest. Rules
already enforced by the contract validators (exclusion reason, split rules) are
re-checked so that a manifest built with ``model_construct`` or loaded from an
older schema is judged on content, not on how it was instantiated.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from plumb.checker.findings import CheckReport, Finding, Severity
from plumb.contracts.common import ErrorClass, LabelKind, LabelStatus
from plumb.contracts.dataset import DatasetManifest, DatasetRow, SplitRule

CHECKER_NAME = "dataset_checker"

_LEAK_SENSITIVE_LABEL_KINDS = frozenset({LabelKind.CORRECTION, LabelKind.EXPERT_DECISION})
"""Label kinds whose target cannot legitimately exist before the decision it records."""


def check_dataset(manifest: DatasetManifest) -> CheckReport:
    """Inspect ``manifest`` and return a report; ``report.ok`` means no ERROR finding."""
    report = CheckReport(checker=CHECKER_NAME, subject=manifest.artifact_id)
    authorized = set(manifest.source_rights_refs)
    unknown_availability = 0
    for row in manifest.rows:
        unknown_availability += _check_row(row, authorized, report)
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
    _check_sources(manifest, report)
    _check_counts(manifest, report)
    _check_split_rules(manifest, report)
    report.summary = _summary(manifest, report, unknown_availability)
    return report


def _check_row(row: DatasetRow, authorized: set[str], report: CheckReport) -> int:
    """Row-level rules. Returns 1 when the row's target availability is unknown, else 0."""
    unknown = 0
    if row.input_availability_time > row.decision_time:
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
    accepted = row.label_status == LabelStatus.ACCEPTED
    if accepted and row.target_evidence_ref is not None and row.target_availability_time is None:
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
                details={"purpose_authorization_ref": row.purpose_authorization_ref},
            )
        )
    return unknown


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


def _summary(manifest: DatasetManifest, report: CheckReport, unknown_availability: int) -> dict[str, Any]:
    return {
        "dataset_id": manifest.dataset_id,
        "revision": manifest.revision,
        "available": manifest.is_available,
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


__all__ = ["CHECKER_NAME", "check_dataset"]
