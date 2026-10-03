"""Tests for the aggregate state machines (specification section 23, design section 7).

Every machine gets a legal happy path, an illegal edge, its spec-fixed guards
exercised both failing (no context) and passing, a terminal-state check and the
non-empty-reason rule. Fixtures are synthetic.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

import pytest
from pydantic import ValidationError

from plumb.contracts.common import (
    BuildState,
    BuildStepState,
    CollectorState,
    DatasetState,
    EffectState,
    ErrorClass,
    ReleaseState,
    TrainingState,
)
from plumb.statemachines.machines import (
    BUILD,
    BUILD_STEP,
    COLLECTOR,
    DATASET,
    EFFECT,
    MACHINES,
    RELEASE,
    TRAINING,
    Guard,
    GuardFailed,
    IllegalTransition,
    MissingReason,
    StateMachine,
    Transition,
    UnknownState,
    all_of,
    equals,
    flag,
    machine_for,
    present,
)

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=timezone.utc)

ALL_MACHINES = [BUILD, BUILD_STEP, COLLECTOR, DATASET, TRAINING, RELEASE, EFFECT]


def walk(machine: StateMachine, path: list, context: dict | None = None) -> list[Transition]:
    """Drive ``machine`` along consecutive states in ``path`` with a fixed context."""
    return [
        machine.transition(source, target, context or {}, f"step {index}: {source.value} -> {target.value}", at=T0)
        for index, (source, target) in enumerate(zip(path, path[1:]), start=1)
    ]


def assert_illegal(machine: StateMachine, source: Enum, target: Enum) -> IllegalTransition:
    with pytest.raises(IllegalTransition) as excinfo:
        machine.transition(source, target, {}, "attempted illegal edge", at=T0)
    assert excinfo.value.error_class is ErrorClass.STATE_CONFLICT
    assert not isinstance(excinfo.value, GuardFailed), "absent edge must not be reported as a guard failure"
    return excinfo.value


def assert_guard_fails(machine: StateMachine, source: Enum, target: Enum, context: dict, guard_name: str) -> None:
    with pytest.raises(GuardFailed) as excinfo:
        machine.transition(source, target, context, "attempt with insufficient context", at=T0)
    assert excinfo.value.guard_name == guard_name
    assert isinstance(excinfo.value, IllegalTransition)
    assert excinfo.value.error_class is ErrorClass.STATE_CONFLICT


# ---------------------------------------------------------------------------
# Generic behaviour
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-057")
@pytest.mark.parametrize("machine", ALL_MACHINES, ids=lambda m: m.name)
def test_terminal_states_have_no_outgoing_edges(machine: StateMachine) -> None:
    terminal = machine.terminal_states()
    assert terminal, f"{machine.name} must have at least one terminal state"
    for state in terminal:
        assert machine.targets_from(state) == frozenset()
        assert machine.is_terminal(state)
        for other in machine.states:
            if other is not state:
                error = assert_illegal(machine, state, other)
                assert "terminal" in str(error)
    for source, _ in machine.edges():
        assert source not in terminal


@pytest.mark.requirements("PL-057")
@pytest.mark.parametrize(
    ("machine", "expected"),
    [
        (BUILD, {BuildState.VERIFIED, BuildState.FAILED, BuildState.CANCELLED}),
        (BUILD_STEP, {BuildStepState.VERIFIED, BuildStepState.CANCELLED}),
        (COLLECTOR, {CollectorState.RETIRED}),
        (DATASET, {DatasetState.UNAVAILABLE}),
        (TRAINING, {TrainingState.CANDIDATE, TrainingState.FAILED, TrainingState.CANCELLED}),
        (RELEASE, {ReleaseState.RETIRED}),
        (EFFECT, {EffectState.FAILED_FINAL, EffectState.COMPENSATED}),
    ],
    ids=lambda value: value.name if isinstance(value, StateMachine) else "",
)
def test_terminal_sets_match_design(machine: StateMachine, expected: set) -> None:
    assert machine.terminal_states() == frozenset(expected)


@pytest.mark.requirements("PL-057")
@pytest.mark.parametrize("machine", ALL_MACHINES, ids=lambda m: m.name)
@pytest.mark.parametrize("reason", ["", "   ", "\n"])
def test_every_transition_requires_a_non_empty_reason(machine: StateMachine, reason: str) -> None:
    source, target = machine.edges()[0]
    with pytest.raises(MissingReason) as excinfo:
        machine.transition(source, target, {"required_steps_verified": True}, reason, at=T0)
    assert isinstance(excinfo.value, ValueError)


@pytest.mark.requirements("PL-057")
def test_transition_record_carries_reason_time_and_guard() -> None:
    unguarded = BUILD.transition(BuildState.DRAFT, BuildState.VALIDATED, {}, "plan checker passed", at=T0)
    assert unguarded == Transition(
        machine="build", from_state="DRAFT", to_state="VALIDATED", reason="plan checker passed", at=T0, guard=None
    )
    guarded = BUILD.transition(
        BuildState.VERIFYING, BuildState.VERIFIED, {"required_steps_verified": True}, "all required steps verified", at=T0
    )
    assert guarded.guard == "required_steps_verified"
    assert guarded.to_state == BuildState.VERIFIED
    with pytest.raises(ValidationError):
        guarded.reason = "rewritten"  # type: ignore[misc]  # the record is frozen
    later = BUILD.transition(BuildState.DRAFT, BuildState.VALIDATED, {}, "default clock")
    assert later.at.tzinfo is not None and later.at > T0


@pytest.mark.requirements("PL-057")
def test_states_may_be_passed_as_values_but_unknown_values_are_rejected() -> None:
    transition = EFFECT.transition("RESERVED", "DISPATCHED", {}, "string states accepted", at=T0)
    assert transition.from_state == "RESERVED" and transition.to_state == "DISPATCHED"
    with pytest.raises(UnknownState):
        EFFECT.transition("RESERVED", "VERIFIED", {}, "not an effect state", at=T0)
    with pytest.raises(UnknownState):
        EFFECT.transition(BuildState.DRAFT, EffectState.DISPATCHED, {}, "wrong aggregate", at=T0)
    assert EFFECT.has_edge("RESERVED", "DISPATCHED")
    assert not EFFECT.has_edge("RESERVED", "CONFIRMED")
    assert EFFECT.guard_for("DISPATCHED", "CONFIRMED").name == "external_receipt"
    with pytest.raises(IllegalTransition):
        EFFECT.guard_for("RESERVED", "CONFIRMED")


@pytest.mark.requirements("PL-057")
def test_machine_for_resolves_every_aggregate() -> None:
    assert len(MACHINES) == 7
    assert machine_for("build") is BUILD
    assert machine_for("Build step") is BUILD_STEP
    assert machine_for("build-step") is BUILD_STEP
    assert machine_for("COLLECTOR") is COLLECTOR
    assert machine_for("dataset") is DATASET
    assert machine_for("training") is TRAINING
    assert machine_for("release") is RELEASE
    assert machine_for("effect") is EFFECT
    with pytest.raises(KeyError, match="unknown aggregate"):
        machine_for("workflow")


@pytest.mark.requirements("PL-057")
def test_machine_definition_rejects_foreign_states_and_self_loops() -> None:
    with pytest.raises(ValueError, match="outside"):
        StateMachine("broken", EffectState, {(EffectState.RESERVED, BuildState.DRAFT): None})
    with pytest.raises(ValueError, match="self-loop"):
        StateMachine("broken", EffectState, {(EffectState.RESERVED, EffectState.RESERVED): None})


@pytest.mark.requirements("PL-057")
def test_guard_helpers_compose() -> None:
    both = flag("a", "b")
    assert both.name == "a and b"
    assert both.predicate({"a": True, "b": True})
    assert not both.predicate({"a": True, "b": 1}), "flags must be exactly True"
    assert present("receipt").predicate({"receipt": {"id": "x"}})
    assert not present("receipt").predicate({"receipt": None})
    composite = all_of(equals("k", "V"), present("r"))
    assert composite.name == "k == 'V' and r"
    assert composite.predicate({"k": "V", "r": "yes"})
    assert not composite.predicate({"k": "V"})
    assert isinstance(composite, Guard)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-016", "PL-057")
def test_build_happy_path_with_waits_and_repair() -> None:
    B = BuildState
    transitions = walk(
        BUILD,
        [B.DRAFT, B.VALIDATED, B.RUNNING, B.WAITING_AUTH, B.RUNNING, B.WAITING_INPUT, B.RUNNING, B.VERIFYING, B.RUNNING, B.VERIFYING],
    )
    assert [t.to_state for t in transitions][-1] == "VERIFYING"
    final = BUILD.transition(B.VERIFYING, B.VERIFIED, {"required_steps_verified": True}, "every required step verified", at=T0)
    assert final.guard == "required_steps_verified"
    assert all(t.reason for t in transitions + [final])


@pytest.mark.requirements("PL-016")
def test_build_verified_requires_all_required_steps_verified() -> None:
    B = BuildState
    assert_guard_fails(BUILD, B.VERIFYING, B.VERIFIED, {}, "required_steps_verified")
    assert_guard_fails(BUILD, B.VERIFYING, B.VERIFIED, {"required_steps_verified": False}, "required_steps_verified")
    assert_guard_fails(BUILD, B.VERIFYING, B.VERIFIED, {"required_steps_verified": "yes"}, "required_steps_verified")
    assert_guard_fails(BUILD, B.VERIFYING, B.VERIFIED, {"worker_says_done": True}, "required_steps_verified")
    ok = BUILD.transition(B.VERIFYING, B.VERIFIED, {"required_steps_verified": True}, "verified", at=T0)
    assert ok.to_state == "VERIFIED"


@pytest.mark.requirements("PL-016", "PL-057")
def test_build_illegal_edges_and_cancellation() -> None:
    B = BuildState
    assert_illegal(BUILD, B.DRAFT, B.RUNNING)
    assert_illegal(BUILD, B.VALIDATED, B.VERIFIED)
    assert_illegal(BUILD, B.RUNNING, B.VERIFIED)
    assert_illegal(BUILD, B.VERIFIED, B.RUNNING)
    assert_illegal(BUILD, B.FAILED, B.RUNNING)
    for state in (B.DRAFT, B.VALIDATED, B.RUNNING, B.WAITING_AUTH, B.WAITING_INPUT, B.VERIFYING):
        assert BUILD.transition(state, B.CANCELLED, {}, "owner cancelled the build", at=T0).to_state == "CANCELLED"


# ---------------------------------------------------------------------------
# Build step
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-016", "PL-042")
def test_build_step_happy_path_and_verifier_attestation_guard() -> None:
    S = BuildStepState
    walk(BUILD_STEP, [S.PENDING, S.READY, S.RUNNING, S.BLOCKED, S.READY, S.RUNNING, S.VERIFYING])
    assert_guard_fails(BUILD_STEP, S.VERIFYING, S.VERIFIED, {}, "verifier_attestation")
    assert_guard_fails(BUILD_STEP, S.VERIFYING, S.VERIFIED, {"worker_claim": "all checks passed"}, "verifier_attestation")
    assert_guard_fails(BUILD_STEP, S.VERIFYING, S.VERIFIED, {"verifier_attestation": None}, "verifier_attestation")
    ok = BUILD_STEP.transition(
        S.VERIFYING, S.VERIFIED, {"verifier_attestation": "att_synthetic_01"}, "independent verifier attested", at=T0
    )
    assert ok.guard == "verifier_attestation"


@pytest.mark.requirements("PL-018")
def test_build_step_repair_requires_remaining_repair_budget() -> None:
    S = BuildStepState
    assert_guard_fails(BUILD_STEP, S.FAILED, S.READY, {}, "repair_budget_remaining")
    assert_guard_fails(BUILD_STEP, S.FAILED, S.READY, {"repair_budget_remaining": False}, "repair_budget_remaining")
    assert_guard_fails(BUILD_STEP, S.VERIFYING, S.RUNNING, {}, "repair_budget_remaining")
    assert BUILD_STEP.transition(S.FAILED, S.READY, {"repair_budget_remaining": True}, "attempt 2 of 3", at=T0).to_state == "READY"
    assert BUILD_STEP.transition(S.VERIFYING, S.RUNNING, {"repair_budget_remaining": True}, "bounded repair", at=T0).to_state == "RUNNING"


@pytest.mark.requirements("PL-016", "PL-057")
def test_build_step_illegal_edges() -> None:
    S = BuildStepState
    assert_illegal(BUILD_STEP, S.PENDING, S.RUNNING)
    assert_illegal(BUILD_STEP, S.READY, S.VERIFIED)
    assert_illegal(BUILD_STEP, S.RUNNING, S.VERIFIED)
    assert_illegal(BUILD_STEP, S.VERIFIED, S.RUNNING)
    assert_illegal(BUILD_STEP, S.CANCELLED, S.READY)
    assert BUILD_STEP.transition(S.BLOCKED, S.FAILED, {}, "dependency expired", at=T0).to_state == "FAILED"


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-024", "PL-025")
def test_collector_happy_path_and_coverage_guard() -> None:
    C = CollectorState
    walk(COLLECTOR, [C.PLANNED, C.SHADOW, C.BACKFILLING, C.RECONCILING, C.BACKFILLING, C.RECONCILING, C.ACTIVE, C.DEGRADED, C.ACTIVE, C.PAUSED])
    assert_guard_fails(COLLECTOR, C.PAUSED, C.ACTIVE, {}, "coverage_restored")
    assert_guard_fails(COLLECTOR, C.PAUSED, C.ACTIVE, {"coverage_restored": False}, "coverage_restored")
    assert COLLECTOR.transition(C.PAUSED, C.ACTIVE, {"coverage_restored": True}, "coverage restored", at=T0).guard == "coverage_restored"
    assert COLLECTOR.transition(C.DEGRADED, C.PAUSED, {}, "operator paused", at=T0).to_state == "PAUSED"
    for state in (C.PLANNED, C.SHADOW, C.BACKFILLING, C.RECONCILING, C.ACTIVE, C.DEGRADED, C.PAUSED):
        assert COLLECTOR.transition(state, C.RETIRED, {}, "retired", at=T0).to_state == "RETIRED"


@pytest.mark.requirements("PL-024", "PL-057")
def test_collector_illegal_edges() -> None:
    C = CollectorState
    assert_illegal(COLLECTOR, C.PLANNED, C.ACTIVE)
    assert_illegal(COLLECTOR, C.SHADOW, C.ACTIVE)
    assert_illegal(COLLECTOR, C.BACKFILLING, C.ACTIVE)
    assert_illegal(COLLECTOR, C.PAUSED, C.DEGRADED)
    assert_illegal(COLLECTOR, C.RETIRED, C.ACTIVE)


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-029", "PL-030")
def test_dataset_happy_path_checker_guard_and_unavailability() -> None:
    D = DatasetState
    walk(DATASET, [D.PROPOSED, D.MATERIALIZING, D.QUARANTINED, D.MATERIALIZING])
    assert_guard_fails(DATASET, D.MATERIALIZING, D.VERIFIED, {}, "checker_ok")
    assert_guard_fails(DATASET, D.MATERIALIZING, D.VERIFIED, {"checker_ok": False}, "checker_ok")
    assert DATASET.transition(D.MATERIALIZING, D.VERIFIED, {"checker_ok": True}, "dataset checker passed", at=T0).guard == "checker_ok"
    assert DATASET.transition(D.VERIFIED, D.SUPERSEDED, {}, "new revision verified", at=T0).to_state == "SUPERSEDED"
    for state in (D.PROPOSED, D.MATERIALIZING, D.QUARANTINED, D.VERIFIED, D.SUPERSEDED):
        assert DATASET.transition(state, D.UNAVAILABLE, {}, "source material deleted", at=T0).to_state == "UNAVAILABLE"


@pytest.mark.requirements("PL-029", "PL-057")
def test_dataset_illegal_edges() -> None:
    D = DatasetState
    assert_illegal(DATASET, D.PROPOSED, D.VERIFIED)
    assert_illegal(DATASET, D.QUARANTINED, D.VERIFIED)
    assert_illegal(DATASET, D.SUPERSEDED, D.VERIFIED)
    assert_illegal(DATASET, D.UNAVAILABLE, D.MATERIALIZING)


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-033")
def test_training_submission_requires_persisted_identity() -> None:
    T = TrainingState
    assert_guard_fails(TRAINING, T.PLANNED, T.SUBMITTED, {}, "submission_identity_persisted")
    assert_guard_fails(TRAINING, T.PLANNED, T.SUBMITTED, {"submission_identity_persisted": False}, "submission_identity_persisted")
    submitted = TRAINING.transition(
        T.PLANNED, T.SUBMITTED, {"submission_identity_persisted": True}, "submission identity persisted", at=T0
    )
    assert submitted.guard == "submission_identity_persisted"
    walk(TRAINING, [T.SUBMITTED, T.RUNNING, T.CANDIDATE])
    assert TRAINING.transition(T.SUBMITTED, T.FAILED, {}, "provider rejected", at=T0).to_state == "FAILED"
    for state in (T.PLANNED, T.SUBMITTED, T.RUNNING):
        assert TRAINING.transition(state, T.CANCELLED, {}, "cancelled", at=T0).to_state == "CANCELLED"


@pytest.mark.requirements("PL-033", "PL-057")
def test_training_illegal_edges() -> None:
    T = TrainingState
    assert_illegal(TRAINING, T.PLANNED, T.RUNNING)
    assert_illegal(TRAINING, T.PLANNED, T.CANDIDATE)
    assert_illegal(TRAINING, T.CANDIDATE, T.RUNNING)
    assert_illegal(TRAINING, T.FAILED, T.SUBMITTED)


# ---------------------------------------------------------------------------
# Release
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-040", "PL-043", "PL-047")
def test_release_happy_path_and_activation_guards() -> None:
    R = ReleaseState
    assert_guard_fails(RELEASE, R.CANDIDATE, R.VERIFIED, {}, "attestations_accepted")
    verified = RELEASE.transition(R.CANDIDATE, R.VERIFIED, {"attestations_accepted": True}, "attestations accepted", at=T0)
    assert verified.guard == "attestations_accepted"
    walk(RELEASE, [R.VERIFIED, R.SHADOW, R.CANARY])
    guard_name = "authority_current and attestations_accepted"
    assert_guard_fails(RELEASE, R.CANARY, R.ACTIVE, {}, guard_name)
    assert_guard_fails(RELEASE, R.CANARY, R.ACTIVE, {"authority_current": True}, guard_name)
    assert_guard_fails(RELEASE, R.CANARY, R.ACTIVE, {"attestations_accepted": True}, guard_name)
    assert_guard_fails(RELEASE, R.CANARY, R.ACTIVE, {"authority_current": True, "attestations_accepted": False}, guard_name)
    full = {"authority_current": True, "attestations_accepted": True}
    assert RELEASE.transition(R.CANARY, R.ACTIVE, full, "canary gates passed", at=T0).guard == guard_name
    assert RELEASE.transition(R.ACTIVE, R.PAUSED, {}, "operator paused new effects", at=T0).to_state == "PAUSED"
    assert_guard_fails(RELEASE, R.PAUSED, R.ACTIVE, {"attestations_accepted": True}, guard_name)
    assert RELEASE.transition(R.PAUSED, R.ACTIVE, full, "authority re-checked, resumed", at=T0).to_state == "ACTIVE"
    for state in (R.CANARY, R.ACTIVE, R.PAUSED):
        assert RELEASE.transition(state, R.ROLLED_BACK, {}, "rolled back", at=T0).to_state == "ROLLED_BACK"
    for state in (R.CANDIDATE, R.VERIFIED, R.SHADOW, R.CANARY, R.ACTIVE, R.PAUSED, R.ROLLED_BACK):
        assert RELEASE.transition(state, R.RETIRED, {}, "retired", at=T0).to_state == "RETIRED"


@pytest.mark.requirements("PL-047", "PL-057")
def test_release_illegal_edges() -> None:
    R = ReleaseState
    assert_illegal(RELEASE, R.CANDIDATE, R.ACTIVE)
    assert_illegal(RELEASE, R.VERIFIED, R.ACTIVE)
    assert_illegal(RELEASE, R.SHADOW, R.ACTIVE)
    assert_illegal(RELEASE, R.ROLLED_BACK, R.ACTIVE)
    assert_illegal(RELEASE, R.RETIRED, R.ACTIVE)


# ---------------------------------------------------------------------------
# Effect
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-037", "PL-038", "PL-039")
def test_effect_happy_paths() -> None:
    E = EffectState
    walk(EFFECT, [E.RESERVED, E.DISPATCHED])
    receipt = {"provider_request_id": "req-synthetic-1", "external_id": "msg-1"}
    confirmed = EFFECT.transition(E.DISPATCHED, E.CONFIRMED, {"external_receipt": receipt}, "receipt stored", at=T0)
    assert confirmed.guard == "external_receipt"
    compensated = EFFECT.transition(E.CONFIRMED, E.COMPENSATED, {"compensation_receipt": receipt}, "compensated", at=T0)
    assert compensated.guard == "compensation_receipt"
    assert EFFECT.transition(E.RESERVED, E.FAILED_FINAL, {}, "released without dispatch", at=T0).to_state == "FAILED_FINAL"
    rejection = {"provider_request_id": "req-synthetic-1", "detail": "400 invalid recipient"}
    rejected = EFFECT.transition(E.DISPATCHED, E.FAILED_FINAL, {"rejection_evidence": rejection}, "provider rejected synchronously", at=T0)
    assert rejected.to_state == "FAILED_FINAL" and rejected.guard == "rejection_evidence"
    assert EFFECT.transition(E.DISPATCHED, E.UNKNOWN, {}, "timeout after send", at=T0).to_state == "UNKNOWN"


@pytest.mark.requirements("PL-038")
def test_effect_dispatched_failed_final_requires_rejection_evidence() -> None:
    """A timeout can never be settled as FAILED_FINAL: only the provider's own rejection can (PL-038)."""
    E = EffectState
    assert_guard_fails(EFFECT, E.DISPATCHED, E.FAILED_FINAL, {}, "rejection_evidence")
    assert_guard_fails(EFFECT, E.DISPATCHED, E.FAILED_FINAL, {"rejection_evidence": None}, "rejection_evidence")
    assert_guard_fails(EFFECT, E.DISPATCHED, E.FAILED_FINAL, {"worker_assumes_never_arrived": True}, "rejection_evidence")
    assert EFFECT.guard_for(E.RESERVED, E.FAILED_FINAL) is None, "releasing an undispatched reservation needs no evidence"


@pytest.mark.requirements("PL-038")
def test_effect_confirmed_requires_external_receipt() -> None:
    E = EffectState
    assert_guard_fails(EFFECT, E.DISPATCHED, E.CONFIRMED, {}, "external_receipt")
    assert_guard_fails(EFFECT, E.DISPATCHED, E.CONFIRMED, {"external_receipt": None}, "external_receipt")
    assert_guard_fails(EFFECT, E.DISPATCHED, E.CONFIRMED, {"worker_claims_sent": True}, "external_receipt")
    assert_guard_fails(EFFECT, E.CONFIRMED, E.COMPENSATED, {}, "compensation_receipt")


@pytest.mark.requirements("PL-038")
def test_effect_unknown_exits_only_through_matching_reconciliation_result() -> None:
    E = EffectState
    confirm_guard = "reconciliation_result == 'CONFIRMED' and external_receipt"
    fail_guard = "reconciliation_result == 'FAILED_FINAL' and provider_confirmed_absent"
    assert_guard_fails(EFFECT, E.UNKNOWN, E.CONFIRMED, {}, confirm_guard)
    assert_guard_fails(EFFECT, E.UNKNOWN, E.CONFIRMED, {"external_receipt": {"id": "x"}}, confirm_guard)
    assert_guard_fails(EFFECT, E.UNKNOWN, E.CONFIRMED, {"reconciliation_result": "CONFIRMED"}, confirm_guard)
    assert_guard_fails(
        EFFECT, E.UNKNOWN, E.CONFIRMED, {"reconciliation_result": "FAILED_FINAL", "external_receipt": {"id": "x"}}, confirm_guard
    )
    assert_guard_fails(EFFECT, E.UNKNOWN, E.FAILED_FINAL, {}, fail_guard)
    assert_guard_fails(EFFECT, E.UNKNOWN, E.FAILED_FINAL, {"reconciliation_result": "CONFIRMED"}, fail_guard)
    assert_guard_fails(EFFECT, E.UNKNOWN, E.FAILED_FINAL, {"reconciliation_result": "STILL_UNKNOWN"}, fail_guard)
    assert_guard_fails(EFFECT, E.UNKNOWN, E.FAILED_FINAL, {"reconciliation_result": "FAILED_FINAL"}, fail_guard)
    assert_guard_fails(
        EFFECT, E.UNKNOWN, E.FAILED_FINAL, {"reconciliation_result": "FAILED_FINAL", "provider_confirmed_absent": False}, fail_guard
    )
    ok = EFFECT.transition(
        E.UNKNOWN, E.CONFIRMED, {"reconciliation_result": "CONFIRMED", "external_receipt": {"id": "x"}}, "provider lookup found it", at=T0
    )
    assert ok.guard == confirm_guard
    failed = EFFECT.transition(
        E.UNKNOWN, E.FAILED_FINAL, {"reconciliation_result": "FAILED_FINAL", "provider_confirmed_absent": True}, "provider confirmed absence", at=T0
    )
    assert failed.guard == fail_guard


@pytest.mark.requirements("PL-037", "PL-038", "PL-057")
def test_effect_illegal_edges_forbid_retry_and_skipping_dispatch() -> None:
    E = EffectState
    assert_illegal(EFFECT, E.UNKNOWN, E.DISPATCHED)  # no retry while UNKNOWN (ADR-009)
    assert_illegal(EFFECT, E.UNKNOWN, E.RESERVED)
    assert_illegal(EFFECT, E.RESERVED, E.CONFIRMED)
    assert_illegal(EFFECT, E.RESERVED, E.UNKNOWN)
    assert_illegal(EFFECT, E.DISPATCHED, E.COMPENSATED)
    assert_illegal(EFFECT, E.CONFIRMED, E.DISPATCHED)
    assert_illegal(EFFECT, E.FAILED_FINAL, E.DISPATCHED)
    assert_illegal(EFFECT, E.COMPENSATED, E.CONFIRMED)
