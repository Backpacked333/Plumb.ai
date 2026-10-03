"""Contract tests for the learning vertical: DatasetManifest, TrainingSpec, EvaluationReport.

Fixtures are synthetic. Requirement markers name the PL ids each test exercises.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from pydantic import ValidationError

from plumb.contracts.common import (
    ArtifactKind,
    ArtifactRef,
    Budget,
    LabelKind,
    LabelStatus,
    Money,
    Principal,
    PrincipalType,
    TrainingState,
    VerificationLevel,
    compute_artifact_digest,
    digest_json,
)
from plumb.contracts.dataset import (
    DatasetCounts,
    DatasetManifest,
    DatasetRow,
    LabelDefinition,
    SplitRule,
)
from plumb.contracts.evaluation import (
    CandidateComparison,
    CandidateKind,
    ErrorSeverity,
    ErrorSeverityBreakdown,
    EvaluationReport,
    Metric,
    SegregationStatement,
)
from plumb.contracts.training import (
    BaseModelRef,
    DataHandling,
    StoppingCondition,
    SupportedCombinationCheck,
    TrainingMethod,
    TrainingSpec,
)

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=timezone.utc)
TENANT = "tnt_synthetic01"
GRANT = "grant_ledger_train_01"
PRODUCER = Principal(
    principal_id="build_agent_01",
    principal_type=PrincipalType.BUILD_AGENT,
    authenticated_via="oidc:synthetic-issuer",
)

# (split, index) layout of the reference manifest: distinct families, temporal rows later.
ROW_LAYOUT: tuple[tuple[str, int], ...] = (
    ("train", 0),
    ("train", 1),
    ("train", 2),
    ("validation", 3),
    ("validation", 4),
    ("test_temporal", 5),
    ("test_temporal", 6),
    ("test_client_disjoint", 7),
)


def ref(artifact_id: str, kind: ArtifactKind) -> ArtifactRef:
    return ArtifactRef(artifact_id=artifact_id, kind=kind, digest=digest_json(artifact_id))


def header(artifact_id: str) -> dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "tenant_id": TENANT,
        "version": 1,
        "producer": PRODUCER,
        "created_at": T0 + timedelta(days=30),
    }


def make_row(index: int, split: str = "train", **overrides: Any) -> DatasetRow:
    decision = T0 + timedelta(days=index)
    data: dict[str, Any] = {
        "example_id": f"ex_{index:03d}",
        "group_id": f"fam_{index:03d}",
        "input_snapshot_refs": [f"evt_in_{index:03d}_a", f"evt_in_{index:03d}_b"],
        "input_availability_time": decision - timedelta(hours=1),
        "decision_time": decision,
        "target_evidence_ref": f"evt_target_{index:03d}",
        "target_availability_time": decision + timedelta(days=2),
        "label_kind": LabelKind.EXPERT_DECISION,
        "label_status": LabelStatus.ACCEPTED,
        "purpose_authorization_ref": GRANT,
        "split": split,
    }
    data.update(overrides)
    return DatasetRow(**data)


def default_rows() -> list[DatasetRow]:
    return [make_row(index, split) for split, index in ROW_LAYOUT]


def split_rules() -> list[SplitRule]:
    return [
        SplitRule(name="train", question_answered="fit", rule="decision_time < 2026-03-04"),
        SplitRule(name="validation", question_answered="model selection", rule="2026-03-04 <= decision_time < 2026-03-06"),
        SplitRule(name="test_temporal", question_answered="performance on future work", rule="decision_time >= 2026-03-06"),
        SplitRule(name="test_client_disjoint", question_answered="generalisation to unseen clients", rule="client not in train"),
    ]


def counts_for(rows: list[DatasetRow]) -> DatasetCounts:
    by_split: dict[str, int] = {}
    by_status: dict[LabelStatus, int] = {}
    for row in rows:
        by_split[row.split] = by_split.get(row.split, 0) + 1
        by_status[row.label_status] = by_status.get(row.label_status, 0) + 1
    return DatasetCounts(by_split=by_split, by_label_status=by_status)


def make_manifest(rows: list[DatasetRow] | None = None, **overrides: Any) -> DatasetManifest:
    rows = default_rows() if rows is None else rows
    data: dict[str, Any] = {
        **header("ds_invoice_class_r1"),
        "dataset_id": "ds_invoice_class",
        "revision": 1,
        "task_definition_ref": ref("task_invoice_class", ArtifactKind.TASK_DEFINITION),
        "label_definition": LabelDefinition(
            text="Accountant-confirmed ledger category after the 30-day amendment window.",
            label_kind=LabelKind.EXPERT_DECISION,
            maturation_window_days=30,
        ),
        "split_rules": split_rules(),
        "schema_ref": "schema_invoice_rows_v1",
        "rows": rows,
        "counts": counts_for(rows),
        "distributions": {"label_frequency": {"travel": 0.5, "software": 0.5}},
        "content_hashes": {"train": digest_json("train"), "validation": digest_json("validation")},
        "source_versions": [ref("src_ledger_export_2026_03", ArtifactKind.EVIDENCE_PACKET)],
        "transformation_refs": [ref("xf_join_v3", ArtifactKind.TRANSFORMATION_CODE)],
        "lineage_refs": ["lineage_run_0042"],
        "source_rights_refs": [GRANT],
    }
    data.update(overrides)
    return DatasetManifest(**data)


def dataset_ref() -> ArtifactRef:
    return ref("ds_invoice_class_r1", ArtifactKind.DATASET_MANIFEST)


def supported_check(**overrides: Any) -> SupportedCombinationCheck:
    data: dict[str, Any] = {
        "provider": "synthetic-model-cloud",
        "method": TrainingMethod.API_FINETUNE,
        "modality": "text",
        "supported": True,
        "checked_at": T0 + timedelta(days=31),
    }
    data.update(overrides)
    return SupportedCombinationCheck(**data)


def make_training_spec(**overrides: Any) -> TrainingSpec:
    data: dict[str, Any] = {
        **header("train_invoice_class_01"),
        "dataset_ref": dataset_ref(),
        "method": TrainingMethod.API_FINETUNE,
        "objective": "Minimise accountant corrections on ledger category.",
        "evaluation_plan_ref": ref("evalplan_invoice_class", ArtifactKind.TASK_DEFINITION),
        "base_model": BaseModelRef(provider="synthetic-model-cloud", capability="text-classification-tuning", version="2026-02-15"),
        "budget": Budget(spend=Money(minor_units=25_000, currency="USD"), max_attempts=1, max_elapsed_seconds=7200),
        "stopping_condition": StoppingCondition(max_epochs=3, max_elapsed_seconds=5400),
        "output_location": "registry://tenant-synthetic/models/invoice-class",
        "data_handling": DataHandling(
            processor="proc_model_cloud_eu",
            region="eu-west-1",
            retention="delete_after_job",
            credential_ref="cred://training/provider-01",
            selected_fields=["vendor_text", "amount_minor", "label"],
        ),
        "submission_identity": "train-ds_invoice_class-r1-attempt-1",
        "supported_combination_check": supported_check(),
    }
    data.update(overrides)
    return TrainingSpec(**data)


def make_none_spec(**overrides: Any) -> TrainingSpec:
    data: dict[str, Any] = {
        **header("train_invoice_class_none"),
        "dataset_ref": dataset_ref(),
        "method": TrainingMethod.NONE,
        "objective": "Rules baseline suffices; training earns no deployment advantage.",
        "evaluation_plan_ref": ref("evalplan_invoice_class", ArtifactKind.TASK_DEFINITION),
    }
    data.update(overrides)
    return TrainingSpec(**data)


def comparison(kind: CandidateKind, cost: int, correct: int) -> CandidateComparison:
    return CandidateComparison(
        candidate=kind,
        total_operating_cost=Money(minor_units=cost, currency="USD"),
        task_performance=Metric(name="category_correct", numerator=correct, denominator=200),
        review_time_minutes=max(0, 400 - correct),
    )


def make_evaluation(**overrides: Any) -> EvaluationReport:
    data: dict[str, Any] = {
        **header("eval_invoice_class_01"),
        "subject_ref": ref("model_invoice_class_v3", ArtifactKind.MODEL_VERSION),
        "dataset_ref": dataset_ref(),
        "held_out_split": "test_temporal",
        "level": VerificationLevel.BUSINESS_OUTCOME,
        "case_count": 200,
        "metrics": [
            Metric(name="category_correct", numerator=184, denominator=200),
            Metric(name="amount_exact", numerator=199, denominator=200),
        ],
        "error_severity_breakdown": ErrorSeverityBreakdown(low=12, medium=3, high=1),
        "review_time_minutes": 95,
        "cost_comparison": [
            comparison(CandidateKind.BASELINE_NATIVE_RULES, 40_000, 150),
            comparison(CandidateKind.PROMPTED_GENERAL_MODEL, 61_000, 178),
            comparison(CandidateKind.TRAINED, 52_000, 184),
        ],
        "nondeterministic": True,
        "trials": 3,
        "segregation_statement": SegregationStatement(
            evaluation_data_disjoint_from_tuning=True,
            basis="test_temporal content hash absent from every tuning and repair set",
        ),
    }
    data.update(overrides)
    return EvaluationReport(**data)


# ---------------------------------------------------------------------------
# DatasetRow / DatasetManifest
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-028", "PL-030")
def test_valid_manifest_constructs_and_pins_kind() -> None:
    manifest = make_manifest()
    assert manifest.kind == ArtifactKind.DATASET_MANIFEST
    assert len(manifest.rows) == 8
    assert manifest.is_available
    assert [row.example_id for row in manifest.rows_in_split("train")] == ["ex_000", "ex_001", "ex_002"]
    assert manifest.splits_used() == {"train", "validation", "test_temporal", "test_client_disjoint"}
    assert manifest.families()["fam_005"] == {"test_temporal"}
    assert all(len(splits) == 1 for splits in manifest.families().values())


@pytest.mark.requirements("PL-028", "PL-030")
def test_manifest_round_trips_through_json_with_stable_digest() -> None:
    manifest = make_manifest()
    restored = DatasetManifest.model_validate_json(manifest.model_dump_json())
    assert restored == manifest
    assert compute_artifact_digest(restored) == compute_artifact_digest(manifest)
    assert compute_artifact_digest(make_manifest(revision=2)) != compute_artifact_digest(manifest)


@pytest.mark.requirements("PL-028")
def test_row_without_exclusion_reason_rejected_when_not_accepted() -> None:
    with pytest.raises(ValidationError, match="exclusion_reason is required"):
        make_row(0, label_status=LabelStatus.QUARANTINED_AMBIGUOUS)
    row = make_row(0, label_status=LabelStatus.QUARANTINED_AMBIGUOUS, exclusion_reason="two candidate targets")
    assert not row.is_accepted


@pytest.mark.requirements("PL-028")
def test_row_exclusion_reason_cannot_be_blank() -> None:
    with pytest.raises(ValidationError):
        make_row(0, label_status=LabelStatus.REJECTED, exclusion_reason="   ")


@pytest.mark.requirements("PL-028")
def test_row_requires_input_snapshots_and_authorization() -> None:
    with pytest.raises(ValidationError, match="input_snapshot_refs"):
        make_row(0, input_snapshot_refs=[])
    data = make_row(0).model_dump()
    del data["purpose_authorization_ref"]
    with pytest.raises(ValidationError, match="purpose_authorization_ref"):
        DatasetRow(**data)


@pytest.mark.requirements("PL-028")
def test_accepted_row_requires_target_evidence() -> None:
    with pytest.raises(ValidationError, match="target evidence"):
        make_row(0, target_evidence_ref=None)
    rejected = make_row(0, label_status=LabelStatus.REJECTED, target_evidence_ref=None, exclusion_reason="target missing")
    assert rejected.target_evidence_ref is None


@pytest.mark.requirements("PL-028", "PL-029")
def test_row_timestamps_must_be_timezone_aware_and_unknown_availability_is_nullable() -> None:
    with pytest.raises(ValidationError):
        make_row(0, decision_time=datetime(2026, 3, 1, 9, 0))
    row = make_row(0, target_availability_time=None)
    assert row.target_availability_time is None


@pytest.mark.requirements("PL-028")
def test_row_rejects_unknown_split_and_extra_fields() -> None:
    with pytest.raises(ValidationError):
        make_row(0, split="holdout")
    with pytest.raises(ValidationError):
        make_row(0, label_confidence=0.9)


@pytest.mark.requirements("PL-030")
def test_manifest_revision_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        make_manifest(revision=0)


@pytest.mark.requirements("PL-030")
def test_manifest_requires_a_rule_for_every_used_split() -> None:
    rules = [rule for rule in split_rules() if rule.name != "test_client_disjoint"]
    with pytest.raises(ValidationError, match="test_client_disjoint"):
        make_manifest(split_rules=rules)


@pytest.mark.requirements("PL-030")
def test_split_rule_must_state_its_question() -> None:
    with pytest.raises(ValidationError):
        SplitRule(name="train", question_answered="", rule="decision_time < cutoff")
    with pytest.raises(ValidationError):
        make_manifest(split_rules=split_rules() + [SplitRule(name="train", question_answered="again", rule="x")])


@pytest.mark.requirements("PL-028")
def test_manifest_rejects_duplicate_example_ids() -> None:
    rows = default_rows()
    rows[1] = make_row(1, "train", example_id="ex_000", group_id="fam_001")
    with pytest.raises(ValidationError, match="ex_000"):
        make_manifest(rows=rows)


@pytest.mark.requirements("PL-030")
def test_manifest_task_definition_and_hashes_are_typed() -> None:
    with pytest.raises(ValidationError, match="TaskDefinition"):
        make_manifest(task_definition_ref=ref("task_x", ArtifactKind.EVIDENCE_PACKET))
    with pytest.raises(ValidationError):
        make_manifest(content_hashes={"train": "md5:abc"})
    with pytest.raises(ValidationError):
        make_manifest(counts=DatasetCounts(by_split={"holdout": 1}))


@pytest.mark.requirements("PL-030")
def test_deleted_source_marks_manifest_unavailable_instead_of_falsifying() -> None:
    manifest = make_manifest(unavailable_reason="source export src_ledger_export_2026_03 deleted on customer request")
    assert not manifest.is_available
    assert manifest.source_versions, "pinned versions stay recorded; only availability changes"
    with pytest.raises(ValidationError):
        make_manifest(unavailable_reason="")


@pytest.mark.requirements("PL-027", "PL-028")
def test_quarantined_rows_remain_in_manifest_with_reason() -> None:
    rows = default_rows()
    rows[4] = make_row(
        4,
        "validation",
        label_status=LabelStatus.QUARANTINED_DISPUTED,
        exclusion_reason="accountant and client disagree on category",
    )
    manifest = make_manifest(rows=rows)
    assert manifest.counts.by_label_status[LabelStatus.QUARANTINED_DISPUTED] == 1
    assert manifest.counts.by_label_status[LabelStatus.ACCEPTED] == 7


# ---------------------------------------------------------------------------
# TrainingSpec
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-032", "PL-033")
def test_valid_training_spec_constructs() -> None:
    spec = make_training_spec()
    assert spec.kind == ArtifactKind.TRAINING_SPEC
    assert spec.requires_provider_job
    assert spec.state == TrainingState.PLANNED
    restored = TrainingSpec.model_validate_json(spec.model_dump_json())
    assert restored == spec


@pytest.mark.requirements("PL-032")
def test_unsupported_combination_rejected_before_submission() -> None:
    with pytest.raises(ValidationError, match="not a supported combination"):
        make_training_spec(supported_combination_check=supported_check(supported=False))


@pytest.mark.requirements("PL-032")
def test_supported_check_must_match_provider_and_method() -> None:
    with pytest.raises(ValidationError, match="provider"):
        make_training_spec(supported_combination_check=supported_check(provider="other-cloud"))
    with pytest.raises(ValidationError, match="method"):
        make_training_spec(supported_combination_check=supported_check(method=TrainingMethod.MANAGED_OPEN_MODEL))


@pytest.mark.requirements("PL-032")
@pytest.mark.parametrize(
    "credential",
    [
        "cred/my_secret_value",
        "PASSWORD-for-training",
        "https://provider.example/api?token=abc123",
        "QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVowMTIzNDU2Nzg5",
    ],
)
def test_secret_looking_credential_ref_rejected(credential: str) -> None:
    with pytest.raises(ValidationError, match="looks like a secret"):
        DataHandling(processor="proc_a", region="eu", retention="delete_after_job", credential_ref=credential)


@pytest.mark.requirements("PL-032")
def test_reference_like_credential_ref_accepted() -> None:
    handling = DataHandling(
        processor="proc_a",
        region="eu",
        retention="30d",
        credential_ref="vault://tenant/training/provider-credential-01",
    )
    assert handling.credential_ref.startswith("vault://")


@pytest.mark.requirements("PL-032")
def test_method_none_forbids_provider_job_fields() -> None:
    assert not make_none_spec().requires_provider_job
    with pytest.raises(ValidationError, match="base_model"):
        make_none_spec(base_model=BaseModelRef(provider="p", capability="c", version="1"))
    with pytest.raises(ValidationError, match="submission_identity"):
        make_none_spec(submission_identity="train-attempt-1")
    with pytest.raises(ValidationError, match="there is no job"):
        make_none_spec(state=TrainingState.SUBMITTED)


@pytest.mark.requirements("PL-033")
def test_missing_submission_identity_rejected() -> None:
    with pytest.raises(ValidationError, match="submission_identity"):
        make_training_spec(submission_identity=None)


@pytest.mark.requirements("PL-032")
@pytest.mark.parametrize("field", ["base_model", "budget", "stopping_condition", "output_location", "data_handling"])
def test_training_methods_require_pinned_job_fields(field: str) -> None:
    with pytest.raises(ValidationError, match=field):
        make_training_spec(**{field: None})
    with pytest.raises(ValidationError, match=field):
        make_training_spec(method=TrainingMethod.MANAGED_OPEN_MODEL, **{
            field: None,
            "supported_combination_check": supported_check(method=TrainingMethod.MANAGED_OPEN_MODEL),
        })


@pytest.mark.requirements("PL-032")
def test_training_spec_pins_a_dataset_manifest() -> None:
    with pytest.raises(ValidationError, match="DatasetManifest"):
        make_training_spec(dataset_ref=ref("ds_x", ArtifactKind.EVIDENCE_PACKET))


@pytest.mark.requirements("PL-032")
def test_stopping_condition_needs_a_hard_bound() -> None:
    with pytest.raises(ValidationError, match="at least one"):
        StoppingCondition(early_stopping_metric="val_loss")
    with pytest.raises(ValidationError, match="early_stopping_metric"):
        StoppingCondition(max_steps=100, early_stopping_patience=2)


@pytest.mark.requirements("PL-033", "PL-034")
def test_completed_job_is_candidate_not_approved_model() -> None:
    spec = make_training_spec(state=TrainingState.CANDIDATE)
    assert spec.state == TrainingState.CANDIDATE
    assert not any("APPROVED" in state.name or "ACTIVE" in state.name for state in TrainingState)


# ---------------------------------------------------------------------------
# EvaluationReport
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-031", "PL-034", "PL-044")
def test_valid_evaluation_report_constructs() -> None:
    report = make_evaluation()
    assert report.kind == ArtifactKind.EVALUATION_REPORT
    assert report.metric("category_correct").value == pytest.approx(0.92)
    assert report.error_severity_breakdown.total == 16
    assert report.error_severity_breakdown.count(ErrorSeverity.HIGH) == 1
    assert report.meets_recommended_trials
    assert EvaluationReport.model_validate_json(report.model_dump_json()) == report


@pytest.mark.requirements("PL-031")
def test_metric_denominator_zero_rejected() -> None:
    with pytest.raises(ValidationError):
        Metric(name="category_correct", numerator=0, denominator=0)
    with pytest.raises(ValidationError):
        Metric(name="category_correct", numerator=-1, denominator=10)


@pytest.mark.requirements("PL-044")
def test_segregation_false_rejected() -> None:
    with pytest.raises(ValidationError, match="used for tuning"):
        make_evaluation(
            segregation_statement=SegregationStatement(
                evaluation_data_disjoint_from_tuning=False, basis="shared with repair set"
            )
        )


@pytest.mark.requirements("PL-044")
def test_nondeterministic_component_needs_multiple_trials() -> None:
    with pytest.raises(ValidationError, match="at least 2 trials"):
        make_evaluation(nondeterministic=True, trials=1)
    two = make_evaluation(nondeterministic=True, trials=2)
    assert not two.meets_recommended_trials
    one = make_evaluation(nondeterministic=False, trials=1)
    assert one.meets_recommended_trials
    with pytest.raises(ValidationError):
        make_evaluation(trials=0)


@pytest.mark.requirements("PL-034", "PL-044")
def test_held_out_dataset_is_required_and_never_the_train_split() -> None:
    data = make_evaluation().model_dump()
    del data["dataset_ref"]
    with pytest.raises(ValidationError, match="dataset_ref"):
        EvaluationReport(**data)
    with pytest.raises(ValidationError, match="DatasetManifest"):
        make_evaluation(dataset_ref=ref("ds_x", ArtifactKind.MODEL_VERSION))
    with pytest.raises(ValidationError):
        make_evaluation(held_out_split="train")


@pytest.mark.requirements("PL-031")
def test_cost_comparison_is_complete_and_consistent() -> None:
    with pytest.raises(ValidationError, match="min_length|at least 1"):
        make_evaluation(cost_comparison=[])
    with pytest.raises(ValidationError, match="appears once"):
        make_evaluation(
            cost_comparison=[
                comparison(CandidateKind.TRAINED, 1, 1),
                comparison(CandidateKind.TRAINED, 2, 2),
            ]
        )
    euro = CandidateComparison(
        candidate=CandidateKind.RETRIEVAL,
        total_operating_cost=Money(minor_units=10, currency="EUR"),
        task_performance=Metric(name="category_correct", numerator=1, denominator=2),
        review_time_minutes=0,
    )
    with pytest.raises(ValidationError, match="one currency"):
        make_evaluation(cost_comparison=[comparison(CandidateKind.TRAINED, 1, 1), euro])


@pytest.mark.requirements("PL-031", "PL-044")
def test_exclusions_must_be_explained_and_metric_names_unique() -> None:
    with pytest.raises(ValidationError, match="exclusion_summary"):
        make_evaluation(excluded_case_count=4)
    report = make_evaluation(excluded_case_count=4, exclusion_summary="4 cases lacked a matured label")
    assert report.excluded_case_count == 4
    with pytest.raises(ValidationError, match="unique"):
        make_evaluation(
            metrics=[
                Metric(name="category_correct", numerator=1, denominator=2),
                Metric(name="category_correct", numerator=2, denominator=2),
            ]
        )
