"""Tests for the ActionIntent contract and the SQLite effect ledger (specification section 16).

Covers persisted deduplication, payload conflicts and explicit supersession
(PL-037), UNKNOWN handling and reconciliation (PL-038), deduplication across
restarts and releases with idempotency keys derived from the logical action
identity (PL-039) and transactional, auditable transitions (PL-057). Fixtures
are synthetic; the ledger runs on ``tmp_path`` files with a deterministic clock.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from plumb.contracts.common import (
    ArtifactKind,
    EffectClass,
    EffectState,
    ErrorClass,
    Principal,
    PrincipalType,
    SourceRef,
    compute_artifact_digest,
    digest_json,
)
from plumb.contracts.effect import (
    ActionIntent,
    ActionReceipt,
    EffectSlot,
    ReconciliationOutcome,
    ReconciliationResult,
    RejectionEvidence,
    derive_idempotency_key,
)
from plumb.ledger.effect_ledger import (
    EVENT_PROVIDER_REQUEST_RECORDED,
    EVENT_RECONCILIATION_ATTEMPT,
    EVENT_SUPERSEDED,
    EVENT_TRANSITION,
    OUTSTANDING_STATES,
    SETTLED_STATES,
    ActionIdConflict,
    EffectLedger,
    EffectUnknown,
    IllegalTransition,
    LedgerError,
    PayloadConflict,
    ReceiptMismatch,
    ReservationResult,
    SupersessionRefused,
    TargetConflict,
    UnknownAction,
)
from plumb.statemachines.machines import GuardFailed, MissingReason

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=timezone.utc)
TENANT = "tnt_synthetic01"
PRODUCER = Principal(
    principal_id="runtime_agent_01",
    principal_type=PrincipalType.RUNTIME_AGENT,
    authenticated_via="oidc:synthetic-issuer",
)
MAIL_TARGET = SourceRef(source_id="mail_01", provider="synthetic-mail", external_account_id="acct-synthetic-1")


class TickingClock:
    """Deterministic clock: every call advances by one second."""

    def __init__(self, start: datetime = T0) -> None:
        self.now = start

    def __call__(self) -> datetime:
        current = self.now
        self.now = current + timedelta(seconds=1)
        return current


def make_slot(*, epoch: int = 1, target: str = "recipient_01", case_id: str = "case_01") -> EffectSlot:
    return EffectSlot(
        tenant_id=TENANT,
        case_id=case_id,
        obligation_id="obl_missing_bank_statement",
        obligation_epoch=epoch,
        operation="send_reminder",
        target=target,
    )


def make_intent(
    action_id: str,
    body: str = "please send the march statement",
    *,
    slot: EffectSlot | None = None,
    deployment_version: str = "rel_01",
    supersedes: str | None = None,
    effect_class: EffectClass = EffectClass.EXTERNAL_COMMUNICATION,
    idempotency_key: str | None = None,
    tenant_id: str = TENANT,
) -> ActionIntent:
    slot = slot or make_slot()
    return ActionIntent(
        artifact_id=f"intent_{action_id}",
        tenant_id=tenant_id,
        version=1,
        producer=PRODUCER,
        created_at=T0,
        action_id=action_id,
        slot=slot,
        payload_digest=digest_json({"body": body}),
        expected_state_version=7,
        authority_ref="approval_case_01_v3",
        deployment_version=deployment_version,
        provider_target=MAIL_TARGET,
        effect_class=effect_class,
        idempotency_key=idempotency_key or derive_idempotency_key(action_id, slot),
        supersedes_action_id=supersedes,
    )


def make_receipt(request_id: str = "req-synthetic-1", external_id: str | None = "msg-synthetic-1", probe: str | None = None) -> ActionReceipt:
    return ActionReceipt(
        provider_request_id=request_id,
        external_id=external_id,
        postcondition_probe=probe,
        observed_at=T0 + timedelta(minutes=5),
        raw_receipt_digest=digest_json({"request_id": request_id, "external_id": external_id}),
    )


def make_rejection(request_id: str | None = "req-synthetic-1", detail: str = "400 invalid recipient") -> RejectionEvidence:
    return RejectionEvidence(
        provider_request_id=request_id,
        raw_response_digest=digest_json({"status": 400, "detail": detail}),
        detail=detail,
        observed_at=T0 + timedelta(minutes=1),
    )


def reconciliation(outcome: ReconciliationOutcome, *, receipt: ActionReceipt | None = None, evidence: str = "provider lookup by request id", absent: bool = False) -> ReconciliationResult:
    return ReconciliationResult(
        outcome=outcome,
        receipt=receipt,
        evidence=evidence,
        provider_confirmed_absent=absent,
        reconciled_at=T0 + timedelta(minutes=10),
    )


@pytest.fixture
def ledger_path(tmp_path: Path) -> Path:
    return tmp_path / "effects.sqlite"


@pytest.fixture
def ledger(ledger_path: Path):
    with EffectLedger(ledger_path, clock=TickingClock()) as instance:
        yield instance


def dispatched(ledger: EffectLedger, action_id: str = "act_01", **intent_kwargs) -> ActionIntent:
    intent = make_intent(action_id, **intent_kwargs)
    ledger.reserve(intent)
    ledger.mark_dispatched(action_id, "worker-synthetic-1", "req-synthetic-1")
    return intent


# ---------------------------------------------------------------------------
# Contract: EffectSlot / ActionIntent / ActionReceipt / ReconciliationResult
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-037", "PL-039")
def test_effect_slot_key_is_the_six_part_semantic_identity() -> None:
    slot = make_slot(epoch=2)
    assert slot.key() == f"{TENANT}|case_01|obl_missing_bank_statement|2|send_reminder|recipient_01"
    assert make_slot(epoch=3).key() != slot.key(), "a new approved epoch is a new business action"
    assert make_slot(epoch=2, target="recipient_02").key() != slot.key()
    with pytest.raises(ValidationError):
        EffectSlot(tenant_id=TENANT, case_id="case_01", obligation_id="obl_x", obligation_epoch=-1, operation="op", target="t")
    with pytest.raises(ValidationError):
        EffectSlot.model_validate(make_slot().model_dump() | {"case_id": "Case With Spaces"})


@pytest.mark.requirements("PL-037")
def test_action_intent_is_a_top_level_contract_with_pinned_kind() -> None:
    intent = make_intent("act_01")
    assert intent.kind is ArtifactKind.ACTION_INTENT
    assert ActionIntent.model_fields["kind"].default is ArtifactKind.ACTION_INTENT
    assert compute_artifact_digest(intent).startswith("sha256:")
    with pytest.raises(ValidationError):
        ActionIntent.model_validate(intent.model_dump(mode="json") | {"kind": ArtifactKind.BUILD_PLAN.value})
    with pytest.raises(ValidationError):
        ActionIntent.model_validate(intent.model_dump(mode="json") | {"payload": "inline body"})


@pytest.mark.requirements("PL-039")
def test_idempotency_key_derives_from_action_identity_not_payload_or_release() -> None:
    slot = make_slot()
    key = derive_idempotency_key("act_01", slot)
    assert len(key) == 64 and int(key, 16) >= 0
    assert derive_idempotency_key("act_01", slot) == key
    assert derive_idempotency_key("act_02", slot) != key
    assert derive_idempotency_key("act_01", make_slot(epoch=2)) != key
    same_action_other_body = make_intent("act_01", "a different message body")
    same_action_other_release = make_intent("act_01", deployment_version="rel_02")
    assert same_action_other_body.idempotency_key == key
    assert same_action_other_release.idempotency_key == key
    with pytest.raises(ValidationError, match="derive_idempotency_key"):
        make_intent("act_01", idempotency_key=digest_json({"body": "payload-derived"}).removeprefix("sha256:"))
    with pytest.raises(ValidationError):
        make_intent("act_01", idempotency_key="not-a-hex-digest")


@pytest.mark.requirements("PL-037", "PL-004")
def test_action_intent_rejects_inconsistent_identity() -> None:
    with pytest.raises(ValidationError, match="tenant_id"):
        make_intent("act_01", tenant_id="tnt_othertenant")
    with pytest.raises(ValidationError, match="supersede itself"):
        make_intent("act_01", supersedes="act_01")
    with pytest.raises(ValidationError, match="READ"):
        make_intent("act_01", effect_class=EffectClass.READ)
    with pytest.raises(ValidationError, match="secret"):
        ActionIntent.model_validate(make_intent("act_01").model_dump(mode="json") | {"authority_ref": "approval_secret_value"})
    with pytest.raises(ValidationError):
        ActionIntent.model_validate(make_intent("act_01").model_dump(mode="json") | {"expected_state_version": -1})


@pytest.mark.requirements("PL-038")
def test_receipt_must_carry_provider_evidence_of_occurrence() -> None:
    assert make_receipt(external_id="msg-1").external_id == "msg-1"
    assert make_receipt(external_id=None, probe="read-after-write: message found in sent folder").postcondition_probe
    with pytest.raises(ValidationError, match="external id or a read-after-write probe"):
        make_receipt(external_id=None, probe=None)
    with pytest.raises(ValidationError):
        ActionReceipt.model_validate(make_receipt().model_dump(mode="json") | {"raw_receipt_digest": "sha256:short"})


@pytest.mark.requirements("PL-038")
def test_reconciliation_result_outcomes_are_backed_by_evidence() -> None:
    with pytest.raises(ValidationError, match="CONFIRMED requires an external receipt"):
        reconciliation(ReconciliationOutcome.CONFIRMED)
    with pytest.raises(ValidationError, match="provider-confirmed non-occurrence"):
        reconciliation(ReconciliationOutcome.FAILED_FINAL, evidence="request timed out again")
    with pytest.raises(ValidationError):
        reconciliation(ReconciliationOutcome.FAILED_FINAL, absent=True, evidence="")
    with pytest.raises(ValidationError, match="contradicts a receipt"):
        reconciliation(ReconciliationOutcome.FAILED_FINAL, absent=True, receipt=make_receipt())
    with pytest.raises(ValidationError, match="contradicts provider_confirmed_absent"):
        reconciliation(ReconciliationOutcome.CONFIRMED, receipt=make_receipt(), absent=True)
    with pytest.raises(ValidationError, match="not STILL_UNKNOWN"):
        reconciliation(ReconciliationOutcome.STILL_UNKNOWN, receipt=make_receipt())
    with pytest.raises(ValidationError, match="not STILL_UNKNOWN"):
        reconciliation(ReconciliationOutcome.STILL_UNKNOWN, absent=True)
    assert reconciliation(ReconciliationOutcome.CONFIRMED, receipt=make_receipt()).outcome is ReconciliationOutcome.CONFIRMED
    assert reconciliation(ReconciliationOutcome.FAILED_FINAL, absent=True, evidence="provider: no request with that id").provider_confirmed_absent
    assert reconciliation(ReconciliationOutcome.STILL_UNKNOWN, evidence="provider status endpoint unavailable").receipt is None


# ---------------------------------------------------------------------------
# Ledger: reservation and deduplication
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-057")
def test_ledger_runs_in_wal_mode_with_foreign_keys(ledger: EffectLedger, ledger_path: Path) -> None:
    assert ledger.pragmas() == {"journal_mode": "wal", "foreign_keys": True}
    assert ledger.path == str(ledger_path)


@pytest.mark.requirements("PL-037", "PL-039", "PL-055")
def test_reserve_same_slot_and_payload_is_idempotent(ledger: EffectLedger) -> None:
    intent = make_intent("act_01")
    first = ledger.reserve(intent)
    assert first == ReservationResult(action_id="act_01", state=EffectState.RESERVED, created=True, existing_action_id=None)
    second = ledger.reserve(intent)
    assert second == ReservationResult(action_id="act_01", state=EffectState.RESERVED, created=False, existing_action_id="act_01")
    other_worker = ledger.reserve(make_intent("act_from_other_worker"))
    assert other_worker.created is False and other_worker.action_id == "act_01"
    with pytest.raises(UnknownAction):
        ledger.get("act_from_other_worker")
    row = ledger.get("act_01")
    assert row.state is EffectState.RESERVED and row.state_version == 1
    assert row.slot_key == intent.slot.key() and row.idempotency_key == intent.idempotency_key
    assert row.provider_target == MAIL_TARGET and row.effect_class is EffectClass.EXTERNAL_COMMUNICATION
    assert ledger.find_by_slot(intent.slot) == row and ledger.find_by_slot(intent.slot.key()) == row
    assert len(ledger.transitions("act_01")) == 1, "idempotent re-reservation writes nothing"


@pytest.mark.requirements("PL-037")
def test_same_slot_different_payload_raises_payload_conflict(ledger: EffectLedger) -> None:
    ledger.reserve(make_intent("act_01", "body A"))
    with pytest.raises(PayloadConflict) as excinfo:
        ledger.reserve(make_intent("act_02", "body B"))
    error = excinfo.value
    assert error.error_class is ErrorClass.PAYLOAD_CONFLICT
    assert isinstance(error, LedgerError)
    assert error.action_id == "act_01" and error.slot_key == make_slot().key()
    assert error.existing_payload_digest == digest_json({"body": "body A"})
    assert error.offered_payload_digest == digest_json({"body": "body B"})
    assert "supersession" in str(error)
    with pytest.raises(UnknownAction):
        ledger.get("act_02")
    assert ledger.get("act_01").state is EffectState.RESERVED


@pytest.mark.requirements("PL-039", "PL-037")
def test_same_action_id_with_changed_payload_shares_the_key_and_conflicts(ledger: EffectLedger) -> None:
    original = make_intent("act_01", "first body")
    changed = make_intent("act_01", "edited body")
    assert original.idempotency_key == changed.idempotency_key
    assert original.payload_digest != changed.payload_digest
    ledger.reserve(original)
    with pytest.raises(PayloadConflict) as excinfo:
        ledger.reserve(changed)
    assert excinfo.value.error_class is ErrorClass.PAYLOAD_CONFLICT
    assert ledger.get("act_01").payload_digest == original.payload_digest


@pytest.mark.requirements("PL-039")
def test_dedup_is_independent_of_deployment_version(ledger: EffectLedger) -> None:
    first = ledger.reserve(make_intent("act_rel1", deployment_version="rel_01"))
    second = ledger.reserve(make_intent("act_rel2", deployment_version="rel_02"))
    assert first.created is True
    assert second.created is False and second.action_id == "act_rel1"
    assert ledger.get("act_rel1").deployment_version == "rel_01"
    assert make_intent("act_rel1", deployment_version="rel_02").idempotency_key == make_intent("act_rel1").idempotency_key


@pytest.mark.requirements("PL-039", "PL-017")
def test_dedup_survives_process_restart(ledger_path: Path) -> None:
    intent = make_intent("act_01")
    with EffectLedger(ledger_path, clock=TickingClock()) as first_process:
        assert first_process.reserve(intent).created is True
    with EffectLedger(ledger_path, clock=TickingClock(T0 + timedelta(hours=1))) as second_process:
        again = second_process.reserve(make_intent("act_minted_after_restart"))
        assert again.created is False and again.action_id == "act_01"
        assert second_process.get("act_01").created_at == T0
        with pytest.raises(PayloadConflict):
            second_process.reserve(make_intent("act_02", "changed after restart"))


@pytest.mark.requirements("PL-037", "PL-057")
def test_action_id_cannot_be_rebound_to_another_slot(ledger: EffectLedger) -> None:
    ledger.reserve(make_intent("act_01"))
    with pytest.raises(ActionIdConflict) as excinfo:
        ledger.reserve(make_intent("act_01", slot=make_slot(case_id="case_02")))
    assert excinfo.value.error_class is ErrorClass.STATE_CONFLICT
    assert ledger.find_by_slot(make_slot(case_id="case_02")) is None


# ---------------------------------------------------------------------------
# Ledger: supersession
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-037")
def test_supersession_succeeds_only_once_the_old_action_is_settled(ledger: EffectLedger) -> None:
    ledger.reserve(make_intent("act_01", "body A"))
    superseding = make_intent("act_02", "body B", supersedes="act_01")
    with pytest.raises(SupersessionRefused) as refused:
        ledger.reserve(superseding)
    assert isinstance(refused.value, PayloadConflict)
    assert refused.value.error_class is ErrorClass.PAYLOAD_CONFLICT
    assert "RESERVED" in str(refused.value)

    ledger.mark_dispatched("act_01", "worker-synthetic-1", "req-synthetic-1")
    with pytest.raises(SupersessionRefused):
        ledger.reserve(superseding)

    ledger.confirm("act_01", make_receipt())
    assert ledger.get("act_01").state in SETTLED_STATES
    result = ledger.reserve(superseding)
    assert result == ReservationResult(action_id="act_02", state=EffectState.RESERVED, created=True, existing_action_id="act_01")

    old, new = ledger.get("act_01"), ledger.get("act_02")
    assert new.slot_key == make_slot().key() and new.supersedes_action_id == "act_01" and new.is_slot_holder
    assert old.slot_key == make_slot().key() and old.superseded_by_action_id == "act_02" and not old.is_slot_holder
    assert old.state is EffectState.CONFIRMED and old.receipt is not None, "the superseded receipt is retained"
    assert old.state_version == 4, "the supersession is a versioned change to the superseded row (PL-057)"
    assert ledger.find_by_slot(make_slot()) == new
    assert [row.action_id for row in ledger.slot_history(make_slot())] == ["act_01", "act_02"]
    supersession = ledger.transitions("act_01")[-1]
    assert supersession.reason.startswith("superseded by action act_02")
    assert supersession.event == EVENT_SUPERSEDED and not supersession.is_state_change
    assert (supersession.from_state, supersession.to_state) == (EffectState.CONFIRMED, EffectState.CONFIRMED)
    assert "supersedes action act_01" in ledger.transitions("act_02")[0].reason

    retry = ledger.reserve(superseding)
    assert retry.created is False and retry.action_id == "act_02"


@pytest.mark.requirements("PL-037")
def test_supersession_must_name_the_action_holding_the_slot(ledger: EffectLedger) -> None:
    ledger.reserve(make_intent("act_01", "body A"))
    ledger.fail_final("act_01", "released without dispatch")
    with pytest.raises(SupersessionRefused, match="held by 'act_01'"):
        ledger.reserve(make_intent("act_02", "body B", supersedes="act_unrelated"))
    with pytest.raises(SupersessionRefused, match="nothing to supersede"):
        ledger.reserve(make_intent("act_03", slot=make_slot(epoch=9), supersedes="act_01"))
    assert ledger.reserve(make_intent("act_02", "body B", supersedes="act_01")).created is True


@pytest.mark.requirements("PL-037", "PL-038")
def test_supersession_of_an_unknown_action_is_refused_until_reconciled(ledger: EffectLedger) -> None:
    dispatched(ledger, "act_01")
    ledger.mark_unknown("act_01", "provider timeout after send")
    with pytest.raises(EffectUnknown):
        ledger.reserve(make_intent("act_02", "body B", supersedes="act_01"))


# ---------------------------------------------------------------------------
# Ledger: dispatch, UNKNOWN and reconciliation
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-038", "PL-057")
def test_dispatch_then_timeout_marks_unknown(ledger: EffectLedger) -> None:
    intent = dispatched(ledger, "act_01")
    row = ledger.get("act_01")
    assert row.state is EffectState.DISPATCHED
    assert row.lease_owner == "worker-synthetic-1" and row.provider_request_id == "req-synthetic-1"
    assert row.state_version == 2
    row = ledger.mark_unknown("act_01", "provider timeout after send; outcome ambiguous")
    assert row.state is EffectState.UNKNOWN and row.state_version == 3
    assert row.provider_request_id == "req-synthetic-1", "the request id survives for reconciliation"
    assert ledger.find_by_slot(intent.slot).state is EffectState.UNKNOWN


@pytest.mark.requirements("PL-057")
def test_mark_dispatched_requires_lease_and_request_id(ledger: EffectLedger) -> None:
    ledger.reserve(make_intent("act_01"))
    with pytest.raises(ValueError, match="lease_owner"):
        ledger.mark_dispatched("act_01", "", "req-1")
    with pytest.raises(ValueError, match="provider_request_id"):
        ledger.mark_dispatched("act_01", "worker-1", "  ")
    assert ledger.get("act_01").state is EffectState.RESERVED
    with pytest.raises(UnknownAction):
        ledger.mark_dispatched("act_missing", "worker-1", "req-1")


@pytest.mark.requirements("PL-038")
def test_reserve_on_unknown_slot_raises_effect_unknown(ledger: EffectLedger) -> None:
    intent = dispatched(ledger, "act_01")
    ledger.mark_unknown("act_01", "timeout")
    with pytest.raises(EffectUnknown) as same_payload:
        ledger.reserve(intent)
    assert same_payload.value.error_class is ErrorClass.EFFECT_UNKNOWN
    assert same_payload.value.action_id == "act_01" and same_payload.value.slot_key == intent.slot.key()
    with pytest.raises(EffectUnknown):
        ledger.reserve(make_intent("act_02", "different body"))
    with pytest.raises(IllegalTransition):
        ledger.mark_dispatched("act_01", "worker-2", "req-2")


@pytest.mark.requirements("PL-038")
def test_reconcile_unknown_to_confirmed_requires_a_receipt(ledger: EffectLedger) -> None:
    dispatched(ledger, "act_01")
    ledger.mark_unknown("act_01", "timeout")
    with pytest.raises(ValidationError):
        reconciliation(ReconciliationOutcome.CONFIRMED, receipt=None)
    with pytest.raises(GuardFailed):
        ledger.confirm("act_01", make_receipt())  # direct confirm is not a reconciliation
    receipt = make_receipt(external_id="msg-found-by-lookup")
    row = ledger.reconcile("act_01", reconciliation(ReconciliationOutcome.CONFIRMED, receipt=receipt, evidence="provider lookup by request id found msg-found-by-lookup"))
    assert row.state is EffectState.CONFIRMED
    assert row.receipt == receipt and row.external_id == "msg-found-by-lookup"
    last = ledger.transitions("act_01")[-1]
    assert (last.from_state, last.to_state) == (EffectState.UNKNOWN, EffectState.CONFIRMED)
    assert last.guard == "reconciliation_result == 'CONFIRMED' and external_receipt"
    assert "msg-found-by-lookup" in last.reason
    assert ledger.reserve(make_intent("act_retry")).created is False


@pytest.mark.requirements("PL-038")
def test_reconcile_still_unknown_leaves_state_unknown_but_records_the_attempt(ledger: EffectLedger) -> None:
    intent = dispatched(ledger, "act_01")
    ledger.mark_unknown("act_01", "timeout")
    before = len(ledger.transitions("act_01"))
    row = ledger.reconcile("act_01", reconciliation(ReconciliationOutcome.STILL_UNKNOWN, evidence="provider status endpoint returned 503"))
    assert row.state is EffectState.UNKNOWN and row.state_version == 4, "the attempt is a versioned change to the row"
    attempts = ledger.transitions("act_01")
    assert len(attempts) == before + 1
    assert (attempts[-1].from_state, attempts[-1].to_state) == (EffectState.UNKNOWN, EffectState.UNKNOWN)
    assert attempts[-1].event == EVENT_RECONCILIATION_ATTEMPT and not attempts[-1].is_state_change
    assert "503" in attempts[-1].reason
    with pytest.raises(EffectUnknown):
        ledger.reserve(intent)
    assert [r.action_id for r in ledger.outstanding()] == ["act_01"]


@pytest.mark.requirements("PL-038")
def test_reconcile_failed_final_requires_provider_confirmed_absence(ledger: EffectLedger) -> None:
    intent = dispatched(ledger, "act_01")
    ledger.mark_unknown("act_01", "timeout")
    with pytest.raises(ValidationError):
        reconciliation(ReconciliationOutcome.FAILED_FINAL, evidence="still timing out", absent=False)
    with pytest.raises(GuardFailed) as excinfo:
        ledger.fail_final("act_01", "operator assumes it never happened")
    assert excinfo.value.guard_name == "reconciliation_result == 'FAILED_FINAL' and provider_confirmed_absent"
    with pytest.raises(GuardFailed):
        ledger.fail_final("act_01", "operator has a rejection", evidence=make_rejection())  # UNKNOWN leaves only via reconcile
    assert ledger.get("act_01").state is EffectState.UNKNOWN
    row = ledger.reconcile("act_01", reconciliation(ReconciliationOutcome.FAILED_FINAL, absent=True, evidence="provider: no message for request id req-synthetic-1"))
    assert row.state is EffectState.FAILED_FINAL and row.receipt is None
    assert ledger.transitions("act_01")[-1].guard == "reconciliation_result == 'FAILED_FINAL' and provider_confirmed_absent"
    assert ledger.outstanding() == []
    assert ledger.reserve(intent).created is False, "the slot still belongs to the settled action"
    assert ledger.reserve(make_intent("act_02", supersedes="act_01")).created is True, "an explicit re-attempt supersedes it"


@pytest.mark.requirements("PL-038")
def test_reconcile_applies_only_to_unknown_effects(ledger: EffectLedger) -> None:
    dispatched(ledger, "act_01")
    with pytest.raises(IllegalTransition, match="UNKNOWN effects only"):
        ledger.reconcile("act_01", reconciliation(ReconciliationOutcome.CONFIRMED, receipt=make_receipt()))
    with pytest.raises(IllegalTransition):
        ledger.reconcile("act_01", reconciliation(ReconciliationOutcome.STILL_UNKNOWN))
    assert ledger.get("act_01").state is EffectState.DISPATCHED
    with pytest.raises(TypeError):
        ledger.reconcile("act_01", {"outcome": "CONFIRMED"})  # type: ignore[arg-type]


@pytest.mark.requirements("PL-038")
def test_confirm_requires_a_receipt_by_type_and_stores_it(ledger: EffectLedger) -> None:
    dispatched(ledger, "act_01")
    with pytest.raises(TypeError):
        ledger.confirm("act_01", None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ledger.confirm("act_01", {"provider_request_id": "req-1"})  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        make_receipt(external_id=None, probe=None)
    assert ledger.get("act_01").state is EffectState.DISPATCHED
    receipt = make_receipt(external_id=None, probe="read-after-write: message present in sent folder")
    row = ledger.confirm("act_01", receipt)
    assert row.state is EffectState.CONFIRMED and row.receipt == receipt and row.external_id is None
    assert ledger.transitions("act_01")[-1].guard == "external_receipt"
    with pytest.raises(IllegalTransition):
        ledger.confirm("act_01", receipt)


@pytest.mark.requirements("PL-037", "PL-057")
def test_fail_final_releases_a_reservation_or_records_a_definitive_rejection(ledger: EffectLedger) -> None:
    ledger.reserve(make_intent("act_01"))
    released = ledger.fail_final("act_01", "case state version changed before dispatch; released")
    assert released.state is EffectState.FAILED_FINAL
    dispatched(ledger, "act_02", slot=make_slot(epoch=2))
    with pytest.raises(GuardFailed) as excinfo:
        ledger.fail_final("act_02", "provider timeout after 30s; assuming the request never arrived")
    assert excinfo.value.guard_name == "rejection_evidence"
    assert ledger.get("act_02").state is EffectState.DISPATCHED, "a timeout is UNKNOWN, never a definitive failure (PL-038)"
    rejected = ledger.fail_final("act_02", "provider rejected the request synchronously: invalid recipient", evidence=make_rejection())
    assert rejected.state is EffectState.FAILED_FINAL and rejected.rejection == make_rejection()
    assert ledger.transitions("act_02")[-1].guard == "rejection_evidence"
    with pytest.raises(IllegalTransition):
        ledger.fail_final("act_02", "twice", evidence=make_rejection())
    with pytest.raises(IllegalTransition):
        ledger.mark_unknown("act_01", "cannot become unknown without a dispatch")


@pytest.mark.requirements("PL-038", "PL-057")
def test_compensate_requires_confirmed_and_retains_the_original_receipt(ledger: EffectLedger) -> None:
    dispatched(ledger, "act_01")
    compensation = make_receipt(request_id="req-compensate-1", external_id="recall-1")
    with pytest.raises(IllegalTransition):
        ledger.compensate("act_01", compensation)
    original = make_receipt()
    ledger.confirm("act_01", original)
    with pytest.raises(TypeError):
        ledger.compensate("act_01", None)  # type: ignore[arg-type]
    row = ledger.compensate("act_01", compensation)
    assert row.state is EffectState.COMPENSATED
    assert row.receipt == original and row.compensation_receipt == compensation
    assert ledger.transitions("act_01")[-1].guard == "compensation_receipt"
    with pytest.raises(IllegalTransition):
        ledger.compensate("act_01", compensation)


# ---------------------------------------------------------------------------
# Ledger: outstanding list, audit trail, restart
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-039", "PL-038")
def test_outstanding_lists_dispatched_and_unknown_only(ledger: EffectLedger) -> None:
    assert OUTSTANDING_STATES == {EffectState.DISPATCHED, EffectState.UNKNOWN}
    ledger.reserve(make_intent("act_reserved", slot=make_slot(epoch=1)))
    dispatched(ledger, "act_dispatched", slot=make_slot(epoch=2))
    dispatched(ledger, "act_unknown", slot=make_slot(epoch=3))
    ledger.mark_unknown("act_unknown", "timeout")
    dispatched(ledger, "act_confirmed", slot=make_slot(epoch=4))
    ledger.confirm("act_confirmed", make_receipt())
    dispatched(ledger, "act_failed", slot=make_slot(epoch=5))
    ledger.fail_final("act_failed", "rejected", evidence=make_rejection())
    dispatched(ledger, "act_compensated", slot=make_slot(epoch=6))
    ledger.confirm("act_compensated", make_receipt())
    ledger.compensate("act_compensated", make_receipt(request_id="req-c", external_id="recall"))
    assert [row.action_id for row in ledger.outstanding()] == ["act_dispatched", "act_unknown"]
    assert [row.action_id for row in ledger.outstanding(TENANT)] == ["act_dispatched", "act_unknown"]
    assert ledger.outstanding("tnt_othertenant") == []


@pytest.mark.requirements("PL-057", "PL-038")
def test_transitions_are_persisted_with_reasons_times_and_guards(ledger: EffectLedger) -> None:
    dispatched(ledger, "act_01")
    ledger.mark_unknown("act_01", "provider timeout after send")
    receipt = make_receipt()
    ledger.reconcile("act_01", reconciliation(ReconciliationOutcome.CONFIRMED, receipt=receipt, evidence="lookup found msg-synthetic-1"))
    ledger.compensate("act_01", make_receipt(request_id="req-c", external_id="recall-1"), reason="recipient asked for recall")
    trail = ledger.transitions("act_01")
    assert [(t.from_state, t.to_state) for t in trail] == [
        (None, EffectState.RESERVED),
        (EffectState.RESERVED, EffectState.DISPATCHED),
        (EffectState.DISPATCHED, EffectState.UNKNOWN),
        (EffectState.UNKNOWN, EffectState.CONFIRMED),
        (EffectState.CONFIRMED, EffectState.COMPENSATED),
    ]
    assert all(t.reason.strip() for t in trail)
    assert trail[2].reason == "provider timeout after send"
    assert trail[4].reason == "recipient asked for recall"
    assert [t.guard for t in trail] == [None, None, None, "reconciliation_result == 'CONFIRMED' and external_receipt", "compensation_receipt"]
    assert [t.seq for t in trail] == sorted(t.seq for t in trail)
    assert all(earlier.at < later.at for earlier, later in zip(trail, trail[1:]))
    assert trail[0].at == T0 and ledger.get("act_01").created_at == T0
    assert ledger.get("act_01").state_version == len(trail)
    assert ledger.transitions("act_never_seen") == []


@pytest.mark.requirements("PL-057")
def test_empty_reason_is_rejected_and_nothing_is_persisted(ledger: EffectLedger) -> None:
    ledger.reserve(make_intent("act_01"))
    with pytest.raises(MissingReason):
        ledger.mark_dispatched("act_01", "worker-1", "req-1", reason="   ")
    dispatched_row = ledger.mark_dispatched("act_01", "worker-1", "req-1")
    with pytest.raises(MissingReason):
        ledger.mark_unknown("act_01", "")
    assert ledger.get("act_01") == dispatched_row
    assert len(ledger.transitions("act_01")) == 2


@pytest.mark.requirements("PL-038", "PL-039", "PL-017")
def test_crash_after_dispatch_is_reconciled_not_redispatched(ledger_path: Path) -> None:
    intent = make_intent("act_01")
    crashing_worker = EffectLedger(ledger_path, clock=TickingClock())
    crashing_worker.reserve(intent)
    crashing_worker.mark_dispatched("act_01", "worker-crashed", "req-before-crash")
    crashing_worker.close()  # the process dies before any receipt is stored

    with EffectLedger(ledger_path, clock=TickingClock(T0 + timedelta(minutes=30))) as replacement:
        pending = replacement.outstanding()
        assert [row.action_id for row in pending] == ["act_01"]
        assert pending[0].state is EffectState.DISPATCHED
        assert pending[0].lease_owner == "worker-crashed" and pending[0].provider_request_id == "req-before-crash"

        same_business_action = replacement.reserve(intent)
        assert same_business_action.created is False and same_business_action.state is EffectState.DISPATCHED
        with pytest.raises(IllegalTransition):
            replacement.mark_dispatched("act_01", "worker-replacement", "req-after-restart")
        assert replacement.reserve(make_intent("act_new_id_after_restart")).action_id == "act_01"

        replacement.mark_unknown("act_01", "lease expired; the old request may have reached the provider")
        with pytest.raises(EffectUnknown):
            replacement.reserve(intent)
        replacement.reconcile(
            "act_01",
            reconciliation(ReconciliationOutcome.CONFIRMED, receipt=make_receipt(request_id="req-before-crash"), evidence="provider lookup by req-before-crash"),
        )
        assert replacement.outstanding() == []
        assert replacement.get("act_01").state is EffectState.CONFIRMED
        assert replacement.get("act_01").lease_owner == "worker-crashed", "the attempt record outlives the lease"


@pytest.mark.requirements("PL-057")
def test_failed_transition_rolls_back_the_transaction(ledger: EffectLedger) -> None:
    dispatched(ledger, "act_01")
    ledger.mark_unknown("act_01", "timeout")
    before_row, before_trail = ledger.get("act_01"), ledger.transitions("act_01")
    with pytest.raises(GuardFailed):
        ledger.confirm("act_01", make_receipt())  # UNKNOWN needs a reconciliation result, not a bare confirm
    with pytest.raises(IllegalTransition):
        ledger.compensate("act_01", make_receipt())
    assert ledger.get("act_01") == before_row
    assert ledger.transitions("act_01") == before_trail


@pytest.mark.requirements("PL-057")
def test_ledger_clock_must_be_timezone_aware(ledger_path: Path) -> None:
    naive = EffectLedger(ledger_path, clock=lambda: datetime(2026, 3, 1, 9, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        naive.reserve(make_intent("act_01"))
    naive.close()
    with EffectLedger(ledger_path, clock=TickingClock()) as aware:
        assert aware.find_by_slot(make_slot()) is None, "the failed reservation was rolled back"


# ---------------------------------------------------------------------------
# Review regressions (effects lens)
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-057")
def test_blank_reasons_are_refused_on_every_audit_path_and_the_trail_stays_readable(ledger: EffectLedger) -> None:
    """reserve() and reconcile(STILL_UNKNOWN) used to persist whitespace reasons that broke transitions() (EFF-01)."""
    with pytest.raises(MissingReason):
        ledger.reserve(make_intent("act_a"), reason="   ")
    with pytest.raises(UnknownAction):
        ledger.get("act_a")
    dispatched(ledger, "act_b", slot=make_slot(epoch=2))
    ledger.mark_unknown("act_b", "timeout")
    before = len(ledger.transitions("act_b"))
    still = reconciliation(ReconciliationOutcome.STILL_UNKNOWN, evidence="503")
    row = ledger.reconcile("act_b", still, reason="\t ")  # blank falls back to the derived reason
    assert row.state is EffectState.UNKNOWN
    trail = ledger.transitions("act_b")
    assert len(trail) == before + 1 and trail[-1].reason == "reconciled as STILL_UNKNOWN: 503"
    with pytest.raises(MissingReason):
        ledger.record_provider_request("act_b", "req-synthetic-1", reason=" ")
    assert all(entry.reason.strip() for entry in ledger.transitions("act_b"))


@pytest.mark.requirements("PL-038", "PL-037")
def test_timeout_cannot_be_settled_as_failed_final_and_the_slot_stays_reserved(ledger: EffectLedger) -> None:
    """fail_final() on a DISPATCHED action needs the provider's rejection, so a timeout cannot free the slot (EFF-02)."""
    intent = dispatched(ledger, "act_01")
    with pytest.raises(GuardFailed):
        ledger.fail_final("act_01", "provider timeout after 30s; assuming the request never arrived")
    assert [row.action_id for row in ledger.outstanding()] == ["act_01"]
    with pytest.raises(SupersessionRefused):
        ledger.reserve(make_intent("act_02", supersedes="act_01"))
    with pytest.raises(ValidationError):
        RejectionEvidence(provider_request_id="req-synthetic-1", raw_response_digest=digest_json({"x": 1}), provider_confirmed_absent=False, detail="timed out", observed_at=T0)
    with pytest.raises(TypeError):
        ledger.fail_final("act_01", "rejected", evidence={"detail": "400"})  # type: ignore[arg-type]
    with pytest.raises(ReceiptMismatch):
        ledger.fail_final("act_01", "rejected", evidence=make_rejection(request_id="req-someone-else"))
    row = ledger.fail_final("act_01", "provider answered 400 invalid recipient", evidence=make_rejection())
    assert row.state is EffectState.FAILED_FINAL and row.rejection is not None and row.rejection.detail == "400 invalid recipient"
    assert ledger.reserve(make_intent("act_02", supersedes="act_01")).created is True, "now the slot can be superseded"
    assert ledger.reserve(intent).created is False and ledger.find_by_slot(intent.slot).action_id == "act_02"


@pytest.mark.requirements("PL-057", "PL-038", "PL-039")
def test_lease_is_recorded_before_the_provider_call_and_the_request_id_afterwards(ledger_path: Path) -> None:
    """The dispatcher records its lease, invokes the provider, then stores the id the provider assigned (EFF-03)."""
    worker = EffectLedger(ledger_path, clock=TickingClock())
    worker.reserve(make_intent("act_01"))
    row = worker.mark_dispatched("act_01", "worker-1")
    assert row.state is EffectState.DISPATCHED and row.lease_owner == "worker-1" and row.provider_request_id is None
    worker.close()  # provider invoked; the worker dies before it can store the answer

    with EffectLedger(ledger_path, clock=TickingClock(T0 + timedelta(minutes=30))) as replacement:
        pending = replacement.outstanding()
        assert [row.action_id for row in pending] == ["act_01"], "the attempt is on record although no request id ever was"
        assert pending[0].lease_owner == "worker-1"
        assert replacement.reserve(make_intent("act_01")).created is False
        with pytest.raises(IllegalTransition):
            replacement.mark_dispatched("act_01", "worker-2")
        recorded = replacement.record_provider_request("act_01", "req-found-in-provider-log", reason="request id recovered from the provider log")
        assert recorded.provider_request_id == "req-found-in-provider-log"
        assert replacement.transitions("act_01")[-1].event == EVENT_PROVIDER_REQUEST_RECORDED
        assert replacement.record_provider_request("act_01", "req-found-in-provider-log") == recorded, "idempotent for the same id"
        with pytest.raises(ReceiptMismatch):
            replacement.record_provider_request("act_01", "req-another")
        receipt = make_receipt(request_id="req-found-in-provider-log")
        assert replacement.confirm("act_01", receipt).state is EffectState.CONFIRMED
        with pytest.raises(IllegalTransition):
            replacement.record_provider_request("act_01", "req-late")


@pytest.mark.requirements("PL-038")
def test_confirmation_binds_the_receipt_to_the_dispatched_request_id(ledger: EffectLedger) -> None:
    """A receipt for another request does not confirm this action (EFF-07)."""
    ledger.reserve(make_intent("act_01"))
    ledger.mark_dispatched("act_01", "worker-1", "req-1")
    with pytest.raises(ReceiptMismatch) as excinfo:
        ledger.confirm("act_01", make_receipt(request_id="req-unrelated"))
    assert excinfo.value.error_class is ErrorClass.STATE_CONFLICT
    assert ledger.get("act_01").state is EffectState.DISPATCHED
    ledger.mark_unknown("act_01", "timeout")
    with pytest.raises(ReceiptMismatch):
        ledger.reconcile("act_01", reconciliation(ReconciliationOutcome.CONFIRMED, receipt=make_receipt(request_id="req-unrelated")))
    row = ledger.reconcile("act_01", reconciliation(ReconciliationOutcome.CONFIRMED, receipt=make_receipt(request_id="req-1")))
    assert row.state is EffectState.CONFIRMED and row.provider_request_id == "req-1"
    # When no request id was recorded at dispatch, the receipt supplies it.
    ledger.reserve(make_intent("act_02", slot=make_slot(epoch=2)))
    ledger.mark_dispatched("act_02", "worker-1")
    assert ledger.confirm("act_02", make_receipt(request_id="req-2")).provider_request_id == "req-2"


@pytest.mark.requirements("PL-037", "PL-040")
def test_idempotent_reservation_reports_divergent_authority_and_refuses_another_account(ledger: EffectLedger) -> None:
    """Same slot and payload: another provider account is a conflict; another authority or case version is flagged (EFF-06)."""
    first = make_intent("act_01")
    ledger.reserve(first)
    other_account = make_intent("act_02").model_copy(
        update={"provider_target": SourceRef(source_id="mail_02", provider="synthetic-mail", external_account_id="acct-OTHER")}
    )
    with pytest.raises(TargetConflict) as excinfo:
        ledger.reserve(other_account)
    assert excinfo.value.error_class is ErrorClass.STATE_CONFLICT and "acct-OTHER" in str(excinfo.value)
    divergent = make_intent("act_03").model_copy(update={"authority_ref": "approval_case_01_v9", "expected_state_version": 99})
    result = ledger.reserve(divergent)
    assert result == ReservationResult(
        action_id="act_01", state=EffectState.RESERVED, created=False, existing_action_id="act_01",
        authority_matches=False, state_version_matches=False,
    )
    assert ledger.reserve(first).authority_matches is True and ledger.reserve(first).state_version_matches is True
    stored = ledger.get("act_01")
    assert (stored.authority_ref, stored.expected_state_version) == ("approval_case_01_v3", 7), "the stored intent is never rewritten"


@pytest.mark.requirements("PL-057", "PL-037")
def test_find_by_slot_never_returns_a_superseded_row(ledger: EffectLedger) -> None:
    """Supersession is a column, not a key suffix; lookups by slot always find the live holder (EFF-05)."""
    dispatched(ledger, "act_01", body="one")
    ledger.confirm("act_01", make_receipt())
    ledger.reserve(make_intent("act_02", "two", supersedes="act_01"))
    assert ledger.find_by_slot(make_slot()).action_id == "act_02"
    assert ledger.find_by_slot(make_slot().key()).action_id == "act_02"
    assert [row.is_slot_holder for row in ledger.slot_history(make_slot())] == [False, True]
    events = [entry.event for entry in ledger.transitions("act_01")]
    assert events == [EVENT_TRANSITION, EVENT_TRANSITION, EVENT_TRANSITION, EVENT_SUPERSEDED]
    assert all(entry.is_state_change for entry in ledger.transitions("act_01") if entry.event == EVENT_TRANSITION)


@pytest.mark.requirements("PL-039", "PL-057")
def test_outstanding_is_ordered_chronologically_whatever_the_clock_offset(ledger_path: Path) -> None:
    """Timestamps are stored in UTC, so dispatchers in different zones do not scramble the reconciliation list (EFF-08)."""
    plus_two = timezone(timedelta(hours=2))
    earlier = EffectLedger(ledger_path, clock=lambda: datetime(2026, 3, 1, 12, 0, tzinfo=plus_two))  # 10:00Z
    earlier.reserve(make_intent("earlier_instant", slot=make_slot(epoch=1)))
    earlier.mark_dispatched("earlier_instant", "worker-a", "req-1")
    earlier.close()
    later = EffectLedger(ledger_path, clock=lambda: datetime(2026, 3, 1, 11, 0, tzinfo=timezone.utc))  # 11:00Z
    later.reserve(make_intent("later_instant", slot=make_slot(epoch=2)))
    later.mark_dispatched("later_instant", "worker-b", "req-2")
    rows = later.outstanding()
    assert [row.action_id for row in rows] == ["earlier_instant", "later_instant"]
    assert all(row.created_at.utcoffset() == timedelta(0) for row in rows)
    assert rows[0].created_at == datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    later.close()
