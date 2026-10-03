"""Behavioural tests for ``plumb.checker.dataset_checker.check_dataset``.

A small valid manifest (8 rows, four splits, distinct families) passes; each
finding code is then provoked by one minimal mutation.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest

from plumb.checker.dataset_checker import CHECKER_NAME, check_dataset
from plumb.checker.findings import Severity
from plumb.contracts.common import ArtifactKind, ArtifactRef, ErrorClass, LabelKind, LabelStatus
from plumb.contracts.dataset import DatasetCounts, DatasetManifest, DatasetRow, SplitRule
from tests.test_dataset_contracts import (
    GRANT,
    T0,
    default_rows,
    make_manifest,
    make_row,
    split_rules,
)


def replace_row(index: int, **overrides: Any) -> list[DatasetRow]:
    rows = default_rows()
    split = rows[index].split
    rows[index] = make_row(index, split, **overrides)
    return rows


def only(report_findings: list[Any], code: str) -> list[Any]:
    return [finding for finding in report_findings if finding.code == code]


def bypass_validation(manifest: DatasetManifest, **overrides: Any) -> DatasetManifest:
    """Rebuild ``manifest`` through ``model_construct`` so contract validators do not run."""
    fields = {name: getattr(manifest, name) for name in DatasetManifest.model_fields}
    fields.update(overrides)
    return DatasetManifest.model_construct(**fields)


@pytest.mark.requirements("PL-028", "PL-029", "PL-030")
def test_valid_manifest_passes_with_summary() -> None:
    report = check_dataset(make_manifest())
    assert report.ok, report.render()
    assert report.findings == []
    assert report.checker == CHECKER_NAME
    assert report.subject == "ds_invoice_class_r1"
    assert report.summary["row_count"] == 8
    assert report.summary["rows_by_split"] == {
        "test_client_disjoint": 1,
        "test_temporal": 2,
        "train": 3,
        "validation": 2,
    }
    assert report.summary["rows_by_label_status"] == {"ACCEPTED": 8}
    assert report.summary["family_count"] == 8
    assert report.summary["faithful_replay_claimable"] is True
    assert report.summary["available"] is True


@pytest.mark.requirements("PL-029")
def test_future_information() -> None:
    decision = T0 + timedelta(days=1)
    rows = replace_row(1, input_availability_time=decision + timedelta(minutes=5))
    report = check_dataset(make_manifest(rows=rows))
    assert not report.ok
    [finding] = only(report.findings, "FUTURE_INFORMATION")
    assert finding.subject_id == "ex_001"
    assert finding.error_class == ErrorClass.DATA_QUALITY_FAILED
    assert finding.severity == Severity.ERROR
    assert report.codes() == {"FUTURE_INFORMATION"}


@pytest.mark.requirements("PL-029")
def test_target_leak_for_correction_and_expert_decision() -> None:
    decision = T0 + timedelta(days=2)
    rows = replace_row(2, label_kind=LabelKind.CORRECTION, target_availability_time=decision - timedelta(days=1))
    report = check_dataset(make_manifest(rows=rows))
    [finding] = only(report.findings, "TARGET_LEAK")
    assert finding.subject_id == "ex_002"
    assert "CORRECTION" in finding.message
    rows = replace_row(3, label_kind=LabelKind.EXPERT_DECISION, target_availability_time=T0 + timedelta(days=2))
    assert check_dataset(make_manifest(rows=rows)).has("TARGET_LEAK")


@pytest.mark.requirements("PL-029")
def test_observed_outcome_known_before_decision_is_not_a_leak() -> None:
    decision = T0 + timedelta(days=2)
    rows = replace_row(2, label_kind=LabelKind.OBSERVED_OUTCOME, target_availability_time=decision - timedelta(hours=1))
    report = check_dataset(make_manifest(rows=rows))
    assert report.ok
    assert not report.has("TARGET_LEAK")


@pytest.mark.requirements("PL-029")
def test_unknown_availability_is_a_warning_and_forbids_faithful_replay_claim() -> None:
    rows = replace_row(0, target_availability_time=None)
    report = check_dataset(make_manifest(rows=rows))
    assert report.ok, "unknown availability does not fail the dataset but limits its claims"
    [warning] = only(report.findings, "UNKNOWN_AVAILABILITY")
    assert warning.severity == Severity.WARNING
    assert warning.subject_id == "ex_000"
    [info] = only(report.findings, "FAITHFUL_REPLAY_NOT_CLAIMABLE")
    assert info.severity == Severity.INFO
    assert info.details == {"rows_with_unknown_availability": 1}
    assert report.summary["faithful_replay_claimable"] is False
    assert report.summary["rows_with_unknown_availability"] == 1


@pytest.mark.requirements("PL-029")
def test_rejected_row_without_availability_is_not_an_unknown_availability_finding() -> None:
    rows = replace_row(
        4,
        label_status=LabelStatus.REJECTED,
        target_evidence_ref=None,
        target_availability_time=None,
        exclusion_reason="target document missing",
    )
    report = check_dataset(make_manifest(rows=rows))
    assert report.ok
    assert not report.has("UNKNOWN_AVAILABILITY")
    assert not report.has("FAITHFUL_REPLAY_NOT_CLAIMABLE")


@pytest.mark.requirements("PL-029")
def test_duplicate_family_across_splits() -> None:
    rows = replace_row(5, group_id="fam_000")
    report = check_dataset(make_manifest(rows=rows))
    assert not report.ok
    [finding] = only(report.findings, "DUPLICATE_FAMILY_ACROSS_SPLITS")
    assert finding.subject_id == "fam_000"
    assert finding.details == {"splits": ["test_temporal", "train"]}
    assert report.summary["family_count"] == 7


@pytest.mark.requirements("PL-029")
def test_same_family_twice_within_one_split_is_allowed() -> None:
    rows = replace_row(1, group_id="fam_000")
    report = check_dataset(make_manifest(rows=rows))
    assert report.ok
    assert not report.has("DUPLICATE_FAMILY_ACROSS_SPLITS")


@pytest.mark.requirements("PL-027")
def test_quarantined_row_in_training() -> None:
    rows = replace_row(
        0,
        label_status=LabelStatus.QUARANTINED_INCONSISTENT,
        exclusion_reason="two accountants disagreed",
    )
    report = check_dataset(make_manifest(rows=rows))
    assert not report.ok
    [finding] = only(report.findings, "QUARANTINED_ROW_IN_TRAINING")
    assert finding.subject_id == "ex_000"
    assert finding.details["label_status"] == "QUARANTINED_INCONSISTENT"
    assert not report.has("MISSING_EXCLUSION_REASON")


@pytest.mark.requirements("PL-027")
def test_quarantined_row_outside_training_is_recorded_not_flagged() -> None:
    rows = replace_row(
        6,
        label_status=LabelStatus.QUARANTINED_AMBIGUOUS,
        exclusion_reason="two candidate target documents",
    )
    report = check_dataset(make_manifest(rows=rows))
    assert report.ok
    assert report.summary["rows_by_label_status"] == {"ACCEPTED": 7, "QUARANTINED_AMBIGUOUS": 1}


@pytest.mark.requirements("PL-028")
def test_missing_exclusion_reason_is_caught_even_when_validation_was_bypassed() -> None:
    manifest = make_manifest()
    rows = list(manifest.rows)
    fields = {name: getattr(rows[7], name) for name in DatasetRow.model_fields}
    rows[7] = DatasetRow.model_construct(**{**fields, "label_status": LabelStatus.REJECTED})
    report = check_dataset(bypass_validation(manifest, rows=rows))
    assert not report.ok
    [finding] = only(report.findings, "MISSING_EXCLUSION_REASON")
    assert finding.subject_id == "ex_007"
    assert not report.has("QUARANTINED_ROW_IN_TRAINING")


@pytest.mark.requirements("PL-030")
def test_unpinned_source() -> None:
    report = check_dataset(make_manifest(source_versions=[]))
    assert not report.ok
    [finding] = only(report.findings, "UNPINNED_SOURCE")
    assert "empty" in finding.message
    assert report.summary["pinned_source_count"] == 0


@pytest.mark.requirements("PL-030")
def test_source_without_digest_is_unpinned() -> None:
    unpinned = ArtifactRef.model_construct(
        artifact_id="src_ledger_export", kind=ArtifactKind.EVIDENCE_PACKET, digest=None
    )
    report = check_dataset(make_manifest(source_versions=[unpinned]))
    [finding] = only(report.findings, "UNPINNED_SOURCE")
    assert finding.details == {"unpinned": ["src_ledger_export"]}


@pytest.mark.requirements("PL-030")
def test_count_mismatch_by_split_and_by_label_status() -> None:
    manifest = make_manifest(
        counts=DatasetCounts(
            by_split={"train": 3, "validation": 2, "test_temporal": 2},
            by_label_status={LabelStatus.ACCEPTED: 9},
        )
    )
    report = check_dataset(manifest)
    assert not report.ok
    findings = only(report.findings, "COUNT_MISMATCH")
    assert {finding.subject_id for finding in findings} == {
        "by_split.test_client_disjoint",
        "by_label_status.ACCEPTED",
    }
    by_subject = {finding.subject_id: finding.details for finding in findings}
    assert by_subject["by_split.test_client_disjoint"]["declared"] == 0
    assert by_subject["by_split.test_client_disjoint"]["actual"] == 1
    assert by_subject["by_label_status.ACCEPTED"] == {
        "dimension": "by_label_status",
        "key": "ACCEPTED",
        "declared": 9,
        "actual": 8,
    }


@pytest.mark.requirements("PL-030")
def test_explicit_zero_counts_are_not_mismatches() -> None:
    manifest = make_manifest()
    counts = manifest.counts.model_copy(
        update={"by_label_status": {**manifest.counts.by_label_status, LabelStatus.REJECTED: 0}}
    )
    assert check_dataset(make_manifest(counts=counts)).ok


@pytest.mark.requirements("PL-030")
def test_split_without_question_when_rule_missing_or_blank() -> None:
    manifest = make_manifest()
    rules = [rule for rule in split_rules() if rule.name != "validation"]
    report = check_dataset(bypass_validation(manifest, split_rules=rules))
    assert not report.ok
    [finding] = only(report.findings, "SPLIT_WITHOUT_QUESTION")
    assert finding.subject_id == "validation"
    assert "no SplitRule" in finding.message

    blank = SplitRule.model_construct(name="train", question_answered="  ", rule="cutoff")
    rules = [blank] + [rule for rule in split_rules() if rule.name != "train"]
    [finding] = only(check_dataset(bypass_validation(manifest, split_rules=rules)).findings, "SPLIT_WITHOUT_QUESTION")
    assert finding.subject_id == "train"
    assert "question" in finding.message


@pytest.mark.requirements("PL-029", "PL-053")
def test_disallowed_source_use_is_purpose_denied() -> None:
    rows = replace_row(3, purpose_authorization_ref="grant_payroll_inspect_only")
    report = check_dataset(make_manifest(rows=rows))
    assert not report.ok
    [finding] = only(report.findings, "DISALLOWED_SOURCE_USE")
    assert finding.error_class == ErrorClass.PURPOSE_DENIED
    assert finding.severity == Severity.ERROR
    assert finding.subject_id == "ex_003"
    assert finding.details == {"purpose_authorization_ref": "grant_payroll_inspect_only"}


@pytest.mark.requirements("PL-029", "PL-053")
def test_manifest_without_source_rights_denies_every_row() -> None:
    report = check_dataset(make_manifest(source_rights_refs=[]))
    assert len(only(report.findings, "DISALLOWED_SOURCE_USE")) == 8
    assert all(finding.details["purpose_authorization_ref"] == GRANT for finding in report.findings)


@pytest.mark.requirements("PL-029", "PL-030")
def test_multiple_defects_are_all_reported_and_counted() -> None:
    rows = replace_row(0, target_availability_time=None)
    rows[5] = make_row(5, "test_temporal", group_id="fam_001")
    manifest = make_manifest(rows=rows, source_versions=[], unavailable_reason="source export deleted")
    report = check_dataset(manifest)
    assert not report.ok
    assert report.codes() == {
        "UNKNOWN_AVAILABILITY",
        "FAITHFUL_REPLAY_NOT_CLAIMABLE",
        "DUPLICATE_FAMILY_ACROSS_SPLITS",
        "UNPINNED_SOURCE",
    }
    assert report.summary["findings_by_code"] == {
        "DUPLICATE_FAMILY_ACROSS_SPLITS": 1,
        "FAITHFUL_REPLAY_NOT_CLAIMABLE": 1,
        "UNKNOWN_AVAILABILITY": 1,
        "UNPINNED_SOURCE": 1,
    }
    assert report.summary["errors"] == 2
    assert report.summary["warnings"] == 1
    assert report.summary["available"] is False
    assert "FAILED" in report.render()


@pytest.mark.requirements("PL-030")
def test_checker_does_not_mutate_the_manifest() -> None:
    manifest = make_manifest()
    before = manifest.model_dump_json()
    check_dataset(manifest)
    assert manifest.model_dump_json() == before
