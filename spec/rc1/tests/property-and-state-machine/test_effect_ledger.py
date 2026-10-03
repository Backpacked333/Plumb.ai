"""External effect protocol scenarios (AT-030..AT-044). Mock provider, SQLite ledger, YAML-driven transitions."""
from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ledger import AuthorityRevoked, EffectLedger, MockProvider, SlotConflict, StaleWorker, make_slot, payload_digest
from machine import GuardFailed, InvalidTransition

T0 = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)


def intent(n: int = 1, payload=None, slot=None, retry_class="provider_keyed", approval="apr_case_1", comp="irreversible", max_attempts=3):
    payload = payload or {"to": "maria@pinestreetbakery.example", "template_class": "document_request_v1", "items": ["bank_statement_2026_08"]}
    slot = slot or make_slot("tnt_barlowkim", "case_0142_2026_08", 1, "gmail.messages.send", "contact_maria")
    return {
        "tenant_id": "tnt_barlowkim",
        "effect_slot": slot,
        "logical_action_id": f"act_{slot}_{n}",
        "payload": payload,
        "payload_digest": payload_digest(payload),
        "operation_id": "google_workspace:gmail.messages.send",
        "retry_class": retry_class,
        "compensation_class": comp,
        "authority": {"approval_id": approval, "release_id": "rel_doc_intake_v1", "envelope_id": "env_barlowkim_v3"},
        "expected_state_versions": {"case": 7},
        "max_attempts": max_attempts,
    }


@pytest.fixture
def db(tmp_path):
    return str(tmp_path / "ledger.db")


def test_happy_path_confirms_with_receipt_and_postcondition(db):
    L, P = EffectLedger(db), MockProvider()
    e = L.reserve(intent(), 50, now=T0)
    eid, tok = L.claim_next("w1", now=T0)
    assert eid == e and L.state(e) == "DISPATCHING"
    assert L.dispatch(e, tok, P, now=T0) == "DISPATCHED"
    assert L.verify_postcondition(e, P) == "CONFIRMED"
    assert [t[1] for t in L.audit_trail(e)] == ["RESERVED", "DISPATCHING", "DISPATCHED", "CONFIRMED"]
    assert P.send_calls == 1 and L.receipts_for(e) == 1


def test_duplicate_trigger_is_idempotent_and_payload_change_conflicts(db):
    L = EffectLedger(db)
    a = L.reserve(intent(1), 50)
    b = L.reserve(intent(2), 50)  # different logical id, same slot and payload -> same effect
    assert a == b
    with pytest.raises(SlotConflict):
        L.reserve(intent(3, payload={"to": "maria@pinestreetbakery.example", "template_class": "document_request_v1", "items": ["bank_statement_2026_08", "payroll_2026_08"]}), 50)


def test_dedup_survives_restart_and_new_workflow_run(db):
    L1 = EffectLedger(db)
    e = L1.reserve(intent(1), 50)
    L2 = EffectLedger(db)  # "restart"
    assert L2.reserve(intent(99), 50) == e


def test_crash_after_provider_accept_never_sends_twice(db):
    L, P = EffectLedger(db), MockProvider()
    P.script = ["crash_after_accept"]
    e = L.reserve(intent(), 50, now=T0)
    eid, tok = L.claim_next("w1", now=T0, lease_ttl_s=30)
    assert L.dispatch(e, tok, P, now=T0) == "CRASHED"
    L2 = EffectLedger(db)  # process restarts; nothing was persisted after the provider call
    assert L2.state(e) == "DISPATCHING"
    assert L2.claim_next("w2", now=T0 + timedelta(seconds=5)) is None  # outbox row already claimed; no blind redispatch
    assert L2.expire_leases(now=T0 + timedelta(seconds=60)) == [e]
    assert L2.state(e) == "UNKNOWN"
    assert L2.reconcile(e, P) == "CONFIRMED"
    assert P.send_calls == 1


def test_lost_response_after_accept_reconciles_to_confirmed(db):
    L, P = EffectLedger(db), MockProvider()
    P.script = ["timeout_after_accept"]
    e = L.reserve(intent(), 50, now=T0)
    eid, tok = L.claim_next("w1", now=T0)
    assert L.dispatch(e, tok, P, now=T0) == "UNKNOWN"
    assert L.reconcile(e, P) == "CONFIRMED"
    assert P.send_calls == 1


def test_timeout_before_accept_reconciles_to_not_occurred_then_requeues(db):
    L, P = EffectLedger(db), MockProvider()
    P.script = ["timeout_before_accept"]
    e = L.reserve(intent(), 50, now=T0)
    eid, tok = L.claim_next("w1", now=T0)
    assert L.dispatch(e, tok, P, now=T0) == "UNKNOWN"
    assert L.reconcile(e, P) == "NOT_OCCURRED"
    assert L.requeue(e, now=T0 + timedelta(seconds=10)) == "RESERVED"
    eid, tok = L.claim_next("w1", now=T0 + timedelta(seconds=11))
    assert L.dispatch(e, tok, P, now=T0 + timedelta(seconds=11)) == "DISPATCHED"
    assert L.verify_postcondition(e, P) == "CONFIRMED"
    assert P.send_calls == 2 and len(P.sent) == 1


def test_unknown_is_never_treated_as_failed(db):
    L, P = EffectLedger(db), MockProvider()
    P.script = ["timeout_after_accept"]
    e = L.reserve(intent(), 50, now=T0)
    eid, tok = L.claim_next("w1", now=T0)
    L.dispatch(e, tok, P, now=T0)
    with pytest.raises((InvalidTransition, GuardFailed)):
        L.requeue(e)  # no reconciliation yet: requeue from UNKNOWN is not a legal transition


def test_stale_dispatcher_cannot_write(db):
    L, P = EffectLedger(db), MockProvider()
    e = L.reserve(intent(), 50, now=T0)
    eid, old_tok = L.claim_next("w1", now=T0, lease_ttl_s=10)
    L.expire_leases(now=T0 + timedelta(seconds=30))  # w1 presumed dead; effect UNKNOWN
    assert L.state(e) == "UNKNOWN"
    with pytest.raises((StaleWorker, InvalidTransition)):
        L.dispatch(e, old_tok, P, now=T0 + timedelta(seconds=31))  # w1 wakes up late
    assert P.send_calls == 0


def test_revocation_before_dispatch_cancels_and_blocks_new_intents(db):
    L = EffectLedger(db)
    e = L.reserve(intent(), 50, now=T0)
    out = L.revoke_authority("apr_case_1", now=T0)
    assert out["cancelled"] == [e] and L.state(e) == "CANCELLED"
    assert L.claim_next("w1", now=T0) is None
    with pytest.raises(AuthorityRevoked):
        L.reserve(intent(2, slot=make_slot("tnt_barlowkim", "case_0142_2026_08", 2, "gmail.messages.send", "contact_maria")), 50)


def test_revocation_during_dispatch_retains_provider_completion(db):
    L, P = EffectLedger(db), MockProvider()
    e = L.reserve(intent(), 50, now=T0)
    eid, tok = L.claim_next("w1", now=T0)
    out = L.revoke_authority("apr_case_1", now=T0)
    assert out["cancel_requested"] == [e] and L.state(e) == "CANCEL_REQUESTED"
    # provider completed anyway and sends its receipt
    rid = "req_late_accept"
    assert L.receive_webhook(e, rid, P.sign(rid), now=T0) == "DISPATCHED"
    assert L.receipts_for(e) == 1  # retained for remediation, never deleted


def test_forged_receipt_is_rejected_and_duplicate_webhook_suppressed(db):
    L, P = EffectLedger(db), MockProvider()
    P.script = ["timeout_after_accept"]
    e = L.reserve(intent(), 50, now=T0)
    eid, tok = L.claim_next("w1", now=T0)
    L.dispatch(e, tok, P, now=T0)
    assert L.receive_webhook(e, "req_forged", "deadbeef" * 8, now=T0) == "UNKNOWN"
    assert L.conn.execute("SELECT COUNT(*) FROM rejected_receipts").fetchone()[0] == 1
    rid = P.sent[L._row(e)["idempotency_key"]]["request_id"]
    assert L.receive_webhook(e, rid, P.sign(rid), now=T0) == "CONFIRMED"
    assert L.receive_webhook(e, rid, P.sign(rid), now=T0) == "CONFIRMED"  # duplicate webhook
    assert L.receipts_for(e) == 1


def test_expired_idempotency_window_forbids_retry_for_provider_keyed(db):
    L, P = EffectLedger(db), MockProvider(idempotency_window_s=60)
    P.script = ["timeout_before_accept"]
    e = L.reserve(intent(), 50, now=T0)
    eid, tok = L.claim_next("w1", now=T0)
    L.dispatch(e, tok, P, now=T0)
    L.reconcile(e, P)
    assert L.requeue(e, now=T0 + timedelta(hours=2), provider_window_s=60) == "FAILED_FINAL"


def test_unverifiable_non_occurrence_needs_human_when_retry_forbidden(db):
    L, P = EffectLedger(db), MockProvider()
    P.script = ["timeout_before_accept"]
    P.authoritative_lookup = False
    e = L.reserve(intent(retry_class="not_retryable_after_ambiguity"), 50, now=T0)
    eid, tok = L.claim_next("w1", now=T0)
    L.dispatch(e, tok, P, now=T0)
    assert L.reconcile(e, P) == "NEEDS_HUMAN"


def test_supersession_is_explicit_and_old_payload_stays_blocked(db):
    L = EffectLedger(db)
    a = L.reserve(intent(1), 50)
    new_payload = {"to": "maria@pinestreetbakery.example", "template_class": "document_request_v1", "items": ["bank_statement_2026_08", "payroll_2026_08"]}
    b = L.supersede(a, intent(2, payload=new_payload), "apr_supersede_7", 50)
    assert L.state(a) == "SUPERSEDED" and L.state(b) == "RESERVED" and a != b
    with pytest.raises(SlotConflict):
        L.reserve(intent(3), 50)  # the original payload no longer matches the slot's active effect


def test_compensation_is_a_new_authorized_effect_and_original_is_kept(db):
    L, P = EffectLedger(db), MockProvider()
    e = L.reserve(intent(comp="compensating_effect"), 50, now=T0)
    eid, tok = L.claim_next("w1", now=T0)
    L.dispatch(e, tok, P, now=T0)
    L.verify_postcondition(e, P)
    comp_intent = intent(5, payload={"retract": True}, slot=make_slot("tnt_barlowkim", "case_0142_2026_08", 1, "gmail.messages.send:compensate", "contact_maria"), comp="not_needed")
    c = L.compensate(e, "apr_comp_9", comp_intent, 50)
    assert L.state(e) == "COMPENSATION_PENDING"
    cid, ctok = L.claim_next("w1", now=T0)
    L.dispatch(c, ctok, P, now=T0)
    L.verify_postcondition(c, P)
    assert L.finish_compensation(e) == "COMPENSATED"
    assert L.receipts_for(e) == 1  # original receipt retained


def test_cancel_during_inflight_then_provider_rejects(db):
    L, P = EffectLedger(db), MockProvider()
    e = L.reserve(intent(), 50, now=T0)
    eid, tok = L.claim_next("w1", now=T0)
    assert L.cancel(e, "cancel_rec_1", "operator cancel", provider=P) == "CANCEL_REQUESTED"
    assert L._transition(e, "provider_rejected", {}, "provider confirmed cancellation") == "CANCELLED"


def test_rate_limit_requeues_and_invalid_fails_final(db):
    L, P = EffectLedger(db), MockProvider()
    P.script = ["rejected_rate_limited", "rejected_invalid"]
    e = L.reserve(intent(), 50, now=T0)
    eid, tok = L.claim_next("w1", now=T0)
    assert L.dispatch(e, tok, P, now=T0) == "RESERVED"
    eid, tok = L.claim_next("w1", now=T0)
    assert L.dispatch(e, tok, P, now=T0) == "FAILED_FINAL"


@settings(max_examples=60, deadline=None)
@given(ops=st.lists(st.sampled_from(["claim", "crash", "expire", "reconcile", "dispatch_ok", "restart"]), min_size=1, max_size=12))
def test_property_one_slot_never_yields_two_provider_objects(tmp_path_factory, ops):
    db = str(tmp_path_factory.mktemp("prop") / "l.db")
    L, P = EffectLedger(db), MockProvider()
    e = L.reserve(intent(), 50, now=T0)
    now, tok = T0, None
    for op in ops:
        now += timedelta(seconds=40)
        try:
            if op == "claim":
                r = L.claim_next("w", now=now, lease_ttl_s=30)
                tok = r[1] if r else tok
            elif op == "crash":
                if L.state(e) == "DISPATCHING" and tok is not None:
                    P.script = ["crash_after_accept"]
                    L.dispatch(e, tok, P, now=now)
            elif op == "dispatch_ok":
                if L.state(e) == "DISPATCHING" and tok is not None:
                    L.dispatch(e, tok, P, now=now)
            elif op == "expire":
                L.expire_leases(now=now)
            elif op == "reconcile":
                if L.state(e) == "UNKNOWN":
                    L.reconcile(e, P)
            elif op == "restart":
                L = EffectLedger(db)
        except (StaleWorker, InvalidTransition, GuardFailed):
            pass
    assert len(P.sent) <= 1
    assert L.state(e) in {"RESERVED", "DISPATCHING", "DISPATCHED", "UNKNOWN", "CONFIRMED", "NOT_OCCURRED", "FAILED_FINAL"}
