"""Effect protocol harness (spec/workflow-and-effects.md, SR-080..SR-092).

What this harness proves locally: persisted deduplication by effect slot across restarts, payload conflict
detection and explicit supersession, lease fencing against stale dispatchers, UNKNOWN as a first-class state
that only reconciliation can leave, receipt verification (HMAC) with duplicate-webhook suppression, revocation
reaching queued dispatches, cancellation during an in-flight request, provider-keyed idempotency window expiry
and compensation as a new authorized effect.

What it does NOT prove: PostgreSQL isolation, distributed leases, provider behaviour under real network
partitions, or exactly-once delivery (no such property exists across arbitrary SaaS APIs).

The transition table is contracts/state-machines/effect.yaml; this module never bypasses it.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "guarded-state-transitions"))
from guards import EFFECT_GUARDS  # noqa: E402
from machine import GuardedMachine, GuardFailed, InvalidTransition  # noqa: E402

ACTIVE_STATES_EXCLUDED = ("CANCELLED", "SUPERSEDED", "FAILED_FINAL")

SCHEMA = """
CREATE TABLE IF NOT EXISTS effects (
  effect_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  effect_slot TEXT NOT NULL,
  logical_action_id TEXT NOT NULL UNIQUE,
  payload_digest TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  operation_id TEXT NOT NULL,
  retry_class TEXT NOT NULL,
  compensation_class TEXT NOT NULL,
  state TEXT NOT NULL,
  attempt_no INTEGER NOT NULL DEFAULT 0,
  max_attempts INTEGER NOT NULL,
  reconcile_attempts INTEGER NOT NULL DEFAULT 0,
  max_reconcile_attempts INTEGER NOT NULL DEFAULT 5,
  idempotency_key TEXT NOT NULL UNIQUE,
  authority_json TEXT NOT NULL,
  expected_versions_json TEXT NOT NULL,
  fencing_token INTEGER NOT NULL DEFAULT 0,
  first_dispatched_at TEXT,
  supersedes TEXT,
  successor TEXT,
  compensation_effect_id TEXT,
  reason TEXT,
  created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_effect_slot_active ON effects(effect_slot)
  WHERE state NOT IN ('CANCELLED','SUPERSEDED','FAILED_FINAL');
CREATE TABLE IF NOT EXISTS outbox (
  outbox_id INTEGER PRIMARY KEY AUTOINCREMENT,
  effect_id TEXT NOT NULL,
  claimed_by TEXT,
  claimed_at TEXT,
  fencing_token INTEGER,
  done INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS leases (
  lease_id TEXT PRIMARY KEY,
  effect_id TEXT NOT NULL,
  worker_id TEXT NOT NULL,
  fencing_token INTEGER NOT NULL,
  expires_at TEXT NOT NULL,
  released INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS attempts (
  attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
  effect_id TEXT NOT NULL,
  attempt_no INTEGER NOT NULL,
  fencing_token INTEGER NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  result TEXT,
  provider_request_id TEXT
);
CREATE TABLE IF NOT EXISTS receipts (
  receipt_id TEXT PRIMARY KEY,
  effect_id TEXT NOT NULL,
  provider_request_id TEXT NOT NULL UNIQUE,
  provider_object_id TEXT,
  signature_valid INTEGER NOT NULL,
  received_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rejected_receipts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  effect_id TEXT,
  provider_request_id TEXT,
  reason TEXT NOT NULL,
  received_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reservations (
  reservation_id TEXT PRIMARY KEY,
  effect_id TEXT NOT NULL,
  amount_minor INTEGER NOT NULL,
  status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS revocations (
  approval_id TEXT PRIMARY KEY,
  revoked_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit (
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  effect_id TEXT NOT NULL,
  from_state TEXT NOT NULL,
  to_state TEXT NOT NULL,
  event TEXT NOT NULL,
  reason TEXT NOT NULL,
  at TEXT NOT NULL
);
"""


class SlotConflict(Exception):
    """Same effect slot, different payload: requires explicit supersession (PAYLOAD_CONFLICT)."""


class StaleWorker(Exception):
    """Fencing token no longer current; the caller's lease was superseded."""


class AuthorityRevoked(Exception):
    pass


@dataclass
class ProviderResult:
    kind: str  # accepted | rejected | timeout | crash_after_accept
    request_id: Optional[str] = None
    rejection_kind: Optional[str] = None


def payload_digest(payload: dict) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def make_slot(tenant: str, case: str, obligation_epoch: int, operation: str, target: str) -> str:
    return f"{tenant}|{case}|{obligation_epoch}|{operation}|{target}"


class MockProvider:
    """Deterministic provider double. Behaviour is scripted per call through `script` (a list of kinds)."""

    def __init__(self, secret: bytes = b"provider-secret", idempotency_window_s: int = 3600):
        self.secret = secret
        self.idempotency_window_s = idempotency_window_s
        self.script: list[str] = []
        self.sent: dict[str, dict] = {}  # idempotency_key -> {request_id, payload, at}
        self.send_calls = 0
        self.lookups = 0
        self.cancel_requests: list[str] = []
        self.authoritative_lookup = True

    def send(self, idempotency_key: str, payload: dict, now: datetime) -> ProviderResult:
        self.send_calls += 1
        kind = self.script.pop(0) if self.script else "accepted"
        if kind == "rejected_invalid":
            return ProviderResult("rejected", rejection_kind="invalid")
        if kind == "rejected_rate_limited":
            return ProviderResult("rejected", rejection_kind="rate_limited")
        if idempotency_key in self.sent:
            # provider-side dedup inside its window
            prior = self.sent[idempotency_key]
            if (now - prior["at"]).total_seconds() <= self.idempotency_window_s:
                return ProviderResult("accepted", request_id=prior["request_id"])
        request_id = "req_" + uuid.uuid4().hex[:12]
        self.sent[idempotency_key] = {"request_id": request_id, "payload": payload, "at": now}
        if kind == "timeout_after_accept":
            return ProviderResult("timeout")  # provider did the work, caller never saw it
        if kind == "timeout_before_accept":
            del self.sent[idempotency_key]
            return ProviderResult("timeout")
        if kind == "crash_after_accept":
            return ProviderResult("crash_after_accept", request_id=request_id)
        return ProviderResult("accepted", request_id=request_id)

    def lookup(self, idempotency_key: str) -> str:
        self.lookups += 1
        if idempotency_key in self.sent:
            return "found"
        return "absent" if self.authoritative_lookup else "absent_unverifiable"

    def read_object(self, request_id: str) -> Optional[dict]:
        for v in self.sent.values():
            if v["request_id"] == request_id:
                return v["payload"]
        return None

    def sign(self, request_id: str) -> str:
        return hmac.new(self.secret, request_id.encode(), hashlib.sha256).hexdigest()

    def cancel(self, request_id: str) -> str:
        self.cancel_requests.append(request_id)
        return "too_late" if any(v["request_id"] == request_id for v in self.sent.values()) else "cancelled"


class EffectLedger:
    def __init__(self, db_path: str, provider_secret: bytes = b"provider-secret"):
        self.conn = sqlite3.connect(db_path, isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.machine = GuardedMachine.load("effect.yaml", EFFECT_GUARDS)
        self.provider_secret = provider_secret

    # ------------------------------------------------------------ helpers
    def _row(self, effect_id: str) -> sqlite3.Row:
        r = self.conn.execute("SELECT * FROM effects WHERE effect_id=?", (effect_id,)).fetchone()
        if r is None:
            raise KeyError(effect_id)
        return r

    def state(self, effect_id: str) -> str:
        return self._row(effect_id)["state"]

    def _transition(self, effect_id: str, event: str, ctx: dict, reason: str, extra_sql: Optional[list] = None) -> str:
        """Fire the YAML machine then persist state + audit + extra writes in ONE transaction."""
        row = self._row(effect_id)
        base = {
            "attempt_no": row["attempt_no"],
            "max_attempts": row["max_attempts"],
            "retry_class": row["retry_class"],
            "compensation_class": row["compensation_class"],
            "reconcile_attempts": row["reconcile_attempts"],
            "max_reconcile_attempts": row["max_reconcile_attempts"],
            "current_fencing_token": row["fencing_token"],
        }
        base.update(ctx)
        result = self.machine.fire(row["state"], event, base, reason)
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            cur = self.conn.execute(
                "UPDATE effects SET state=?, reason=? WHERE effect_id=? AND state=?",
                (result.to_state, reason, effect_id, row["state"]),
            )
            if cur.rowcount != 1:
                raise StaleWorker("state changed concurrently; compare-and-set failed")
            for sql, params in extra_sql or []:
                self.conn.execute(sql, params)
            self.conn.execute(
                "INSERT INTO audit(effect_id, from_state, to_state, event, reason, at) VALUES (?,?,?,?,?,?)",
                (effect_id, row["state"], result.to_state, event, reason, _iso(_utcnow())),
            )
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise
        return result.to_state

    # ------------------------------------------------------------ reservation (SR-080)
    def reserve(self, intent: dict, reservation_minor: int, now: Optional[datetime] = None) -> str:
        """Persist an intent. Same slot + same digest is idempotent; same slot + different digest conflicts."""
        now = now or _utcnow()
        for a in intent["authority"].values():
            if self.conn.execute("SELECT 1 FROM revocations WHERE approval_id=?", (a,)).fetchone():
                raise AuthorityRevoked(a)
        existing = self.conn.execute(
            "SELECT * FROM effects WHERE effect_slot=? AND state NOT IN ('CANCELLED','SUPERSEDED','FAILED_FINAL')",
            (intent["effect_slot"],),
        ).fetchone()
        if existing is not None:
            if existing["payload_digest"] == intent["payload_digest"]:
                return existing["effect_id"]
            raise SlotConflict(f"slot {intent['effect_slot']} already holds {existing['effect_id']} with a different payload")
        effect_id = "eff_" + uuid.uuid4().hex[:12]
        idem = "idem_" + hashlib.sha256(intent["logical_action_id"].encode()).hexdigest()[:24]
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            self.conn.execute(
                """INSERT INTO effects(effect_id, tenant_id, effect_slot, logical_action_id, payload_digest, payload_json,
                   operation_id, retry_class, compensation_class, state, attempt_no, max_attempts, idempotency_key,
                   authority_json, expected_versions_json, supersedes, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,'RESERVED',0,?,?,?,?,?,?)""",
                (
                    effect_id,
                    intent["tenant_id"],
                    intent["effect_slot"],
                    intent["logical_action_id"],
                    intent["payload_digest"],
                    json.dumps(intent["payload"], sort_keys=True),
                    intent["operation_id"],
                    intent["retry_class"],
                    intent["compensation_class"],
                    intent.get("max_attempts", 3),
                    idem,
                    json.dumps(intent["authority"], sort_keys=True),
                    json.dumps(intent.get("expected_state_versions", {}), sort_keys=True),
                    intent.get("supersedes_intent_id"),
                    _iso(now),
                ),
            )
            self.conn.execute(
                "INSERT INTO reservations(reservation_id, effect_id, amount_minor, status) VALUES (?,?,?,'reserved')",
                ("res_" + uuid.uuid4().hex[:10], effect_id, reservation_minor),
            )
            self.conn.execute("INSERT INTO outbox(effect_id) VALUES (?)", (effect_id,))
            self.conn.execute(
                "INSERT INTO audit(effect_id, from_state, to_state, event, reason, at) VALUES (?,?,?,?,?,?)",
                (effect_id, "-", "RESERVED", "reserve", "intent persisted", _iso(now)),
            )
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise
        return effect_id

    # ------------------------------------------------------------ claim and dispatch (SR-081..SR-084)
    def claim_next(self, worker_id: str, now: Optional[datetime] = None, lease_ttl_s: int = 30, runtime_ctx: Optional[dict] = None) -> Optional[tuple[str, int]]:
        """Claim one outbox row with compare-and-set; move RESERVED -> DISPATCHING. Returns (effect_id, fencing_token)."""
        now = now or _utcnow()
        runtime_ctx = runtime_ctx or {}
        row = self.conn.execute(
            "SELECT o.outbox_id, o.effect_id FROM outbox o JOIN effects e ON e.effect_id=o.effect_id "
            "WHERE o.claimed_by IS NULL AND o.done=0 AND e.state='RESERVED' ORDER BY o.outbox_id LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        eff = self._row(row["effect_id"])
        # authority re-check at claim time: cached grants do not survive revocation (SI-012)
        for a in json.loads(eff["authority_json"]).values():
            if self.conn.execute("SELECT 1 FROM revocations WHERE approval_id=?", (a,)).fetchone():
                self.cancel(eff["effect_id"], cancel_record_id="auto_revocation:" + a, reason="authority revoked before dispatch")
                return self.claim_next(worker_id, now, lease_ttl_s, runtime_ctx)
        token = eff["fencing_token"] + 1
        cur = self.conn.execute(
            "UPDATE outbox SET claimed_by=?, claimed_at=?, fencing_token=? WHERE outbox_id=? AND claimed_by IS NULL",
            (worker_id, _iso(now), token, row["outbox_id"]),
        )
        if cur.rowcount != 1:
            return None  # lost the race
        lease_id = "lease_" + uuid.uuid4().hex[:10]
        extra = [
            ("UPDATE effects SET fencing_token=?, attempt_no=attempt_no+1, first_dispatched_at=COALESCE(first_dispatched_at, ?) WHERE effect_id=?", (token, _iso(now), eff["effect_id"])),
            ("INSERT INTO leases(lease_id, effect_id, worker_id, fencing_token, expires_at) VALUES (?,?,?,?,?)", (lease_id, eff["effect_id"], worker_id, token, _iso(now + timedelta(seconds=lease_ttl_s)))),
            ("INSERT INTO attempts(effect_id, attempt_no, fencing_token, started_at) VALUES (?,?,?,?)", (eff["effect_id"], eff["attempt_no"] + 1, token, _iso(now))),
        ]
        ctx = {
            "release_state": runtime_ctx.get("release_state", "ACTIVE"),
            "approval_state": runtime_ctx.get("approval_state", "GRANTED"),
            "requires_case_approval": runtime_ctx.get("requires_case_approval", False),
            "envelope_status": runtime_ctx.get("envelope_status", "active"),
            "approval_expires_at": runtime_ctx.get("approval_expires_at", now + timedelta(days=1)),
            "now": now,
            "expected_state_versions": json.loads(eff["expected_versions_json"]),
            "current_state_versions": runtime_ctx.get("current_state_versions", json.loads(eff["expected_versions_json"])),
            "reservation_status": "reserved",
            "lease_cas_ok": True,
            "outbox_claimed": True,
        }
        try:
            self._transition(eff["effect_id"], "claim", ctx, "outbox row claimed by " + worker_id, extra)
        except GuardFailed:
            self.conn.execute("UPDATE outbox SET claimed_by=NULL, claimed_at=NULL, fencing_token=NULL WHERE outbox_id=?", (row["outbox_id"],))
            raise
        return eff["effect_id"], token

    def dispatch(self, effect_id: str, fencing_token: int, provider: MockProvider, now: Optional[datetime] = None, crash_before_persist: bool = False) -> str:
        """Call the provider outside any transaction, then persist the outcome under the fencing token."""
        now = now or _utcnow()
        eff = self._row(effect_id)
        if eff["fencing_token"] != fencing_token:
            raise StaleWorker("fencing token superseded before dispatch")
        if eff["state"] != "DISPATCHING":
            raise InvalidTransition("Effect", eff["state"], "dispatch")
        result = provider.send(eff["idempotency_key"], json.loads(eff["payload_json"]), now)
        if crash_before_persist or result.kind == "crash_after_accept":
            # Simulated process death between provider acceptance and local persistence. Nothing is written.
            return "CRASHED"
        if result.kind == "accepted":
            receipt_ok = self._store_receipt(effect_id, result.request_id, provider.sign(result.request_id), now)
            ctx = {"fencing_token": fencing_token, "receipt_id": "r", "receipt_verified": receipt_ok}
            extra = [("UPDATE attempts SET finished_at=?, result='accepted', provider_request_id=? WHERE effect_id=? AND fencing_token=?", (_iso(now), result.request_id, effect_id, fencing_token))]
            return self._transition(effect_id, "provider_accepted", ctx, "provider accepted request " + result.request_id, extra)
        if result.kind == "rejected":
            ctx = {"fencing_token": fencing_token, "rejection_kind": result.rejection_kind}
            extra = [("UPDATE attempts SET finished_at=?, result='rejected' WHERE effect_id=? AND fencing_token=?", (_iso(now), effect_id, fencing_token))]
            new_state = self._transition(effect_id, "provider_rejected", ctx, f"provider rejected: {result.rejection_kind}", extra)
            if new_state == "RESERVED":
                self.conn.execute("INSERT INTO outbox(effect_id) VALUES (?)", (effect_id,))
            else:
                self.conn.execute("UPDATE reservations SET status='released' WHERE effect_id=?", (effect_id,))
            return new_state
        # timeout: ambiguous. UNKNOWN, never FAILED (SR-086).
        extra = [("UPDATE attempts SET finished_at=?, result='timeout' WHERE effect_id=? AND fencing_token=?", (_iso(now), effect_id, fencing_token))]
        return self._transition(effect_id, "ambiguous", {"fencing_token": fencing_token}, "provider call timed out; outcome unknown", extra)

    # ------------------------------------------------------------ receipts (SR-087)
    def _store_receipt(self, effect_id: str, request_id: str, signature: str, now: datetime) -> bool:
        expected = hmac.new(self.provider_secret, request_id.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            self.conn.execute("INSERT INTO rejected_receipts(effect_id, provider_request_id, reason, received_at) VALUES (?,?,?,?)", (effect_id, request_id, "bad_signature", _iso(now)))
            return False
        try:
            self.conn.execute(
                "INSERT INTO receipts(receipt_id, effect_id, provider_request_id, signature_valid, received_at) VALUES (?,?,?,1,?)",
                ("rcpt_" + uuid.uuid4().hex[:10], effect_id, request_id, _iso(now)),
            )
        except sqlite3.IntegrityError:
            return True  # duplicate webhook: already recorded, idempotent
        return True

    def receive_webhook(self, effect_id: str, request_id: str, signature: str, now: Optional[datetime] = None) -> str:
        """Provider-originated receipt. Forged receipts are rejected and never move state."""
        now = now or _utcnow()
        ok = self._store_receipt(effect_id, request_id, signature, now)
        st = self.state(effect_id)
        if not ok:
            return st
        if st in ("UNKNOWN",):
            return self._transition(effect_id, "reconcile", {"lookup_result": "found", "reservation_status": "settling"}, "verified receipt arrived for unknown effect",
                                    [("UPDATE reservations SET status='settled' WHERE effect_id=?", (effect_id,))])
        if st == "DISPATCHING":
            return self._transition(effect_id, "provider_accepted", {"fencing_token": self._row(effect_id)["fencing_token"], "receipt_id": "r", "receipt_verified": True}, "verified receipt arrived while dispatching")
        if st == "CANCEL_REQUESTED":
            return self._transition(effect_id, "provider_accepted", {"receipt_id": "r", "receipt_verified": True}, "provider completed despite cancel request")
        return st

    # ------------------------------------------------------------ postcondition and reconciliation (SR-088)
    def verify_postcondition(self, effect_id: str, provider: MockProvider) -> str:
        eff = self._row(effect_id)
        rcpt = self.conn.execute("SELECT provider_request_id FROM receipts WHERE effect_id=? ORDER BY received_at LIMIT 1", (effect_id,)).fetchone()
        obj = provider.read_object(rcpt["provider_request_id"]) if rcpt else None
        if obj is not None and payload_digest(obj) == eff["payload_digest"]:
            return self._transition(effect_id, "postcondition_verified", {"postcondition_ok": True, "postcondition_source": "provider_read", "reservation_status": "settling"},
                                    "read-after-write matched payload digest", [("UPDATE reservations SET status='settled' WHERE effect_id=?", (effect_id,))])
        return self._transition(effect_id, "postcondition_failed", {}, "read-after-write did not match")

    def reconcile(self, effect_id: str, provider: MockProvider) -> str:
        eff = self._row(effect_id)
        if eff["state"] != "UNKNOWN":
            raise InvalidTransition("Effect", eff["state"], "reconcile")
        lookup = provider.lookup(eff["idempotency_key"])
        self.conn.execute("UPDATE effects SET reconcile_attempts=reconcile_attempts+1 WHERE effect_id=?", (effect_id,))
        extra = []
        if lookup == "found":
            # obtain the provider's request id for the receipt record
            rid = provider.sent[eff["idempotency_key"]]["request_id"]
            self._store_receipt(effect_id, rid, provider.sign(rid), _utcnow())
            extra.append(("UPDATE reservations SET status='settled' WHERE effect_id=?", (effect_id,)))
        ctx = {"lookup_result": lookup, "lookup_authoritative": provider.authoritative_lookup, "reservation_status": "settling"}
        return self._transition(effect_id, "reconcile", ctx, f"reconciliation lookup returned {lookup}", extra)

    def requeue(self, effect_id: str, now: Optional[datetime] = None, provider_window_s: int = 3600) -> str:
        now = now or _utcnow()
        eff = self._row(effect_id)
        expired = False
        if eff["first_dispatched_at"]:
            expired = (now - datetime.fromisoformat(eff["first_dispatched_at"])).total_seconds() > provider_window_s
        for a in json.loads(eff["authority_json"]).values():
            if self.conn.execute("SELECT 1 FROM revocations WHERE approval_id=?", (a,)).fetchone():
                raise AuthorityRevoked(a)
        ctx = {"idempotency_window_expired": expired, "grant_revoked": False, "envelope_status": "active", "approval_state": "GRANTED", "now": now}
        try:
            st = self._transition(effect_id, "requeue", ctx, "requeue after confirmed non-occurrence")
            self.conn.execute("INSERT INTO outbox(effect_id) VALUES (?)", (effect_id,))
            return st
        except GuardFailed:
            return self._transition(effect_id, "give_up", ctx, "retry forbidden by class, window or attempts",
                                    [("UPDATE reservations SET status='released' WHERE effect_id=?", (effect_id,))])

    # ------------------------------------------------------------ leases (SR-083)
    def expire_leases(self, now: Optional[datetime] = None) -> list[str]:
        """An expired lease on a DISPATCHING effect makes it UNKNOWN. It is never requeued blindly."""
        now = now or _utcnow()
        moved = []
        rows = self.conn.execute("SELECT l.effect_id FROM leases l JOIN effects e ON e.effect_id=l.effect_id WHERE l.released=0 AND l.expires_at<=? AND e.state='DISPATCHING'", (_iso(now),)).fetchall()
        for r in rows:
            self.conn.execute("UPDATE leases SET released=1 WHERE effect_id=? AND released=0", (r["effect_id"],))
            self._transition(r["effect_id"], "ambiguous", {}, "dispatcher lease expired with provider outcome unknown")
            moved.append(r["effect_id"])
        return moved

    # ------------------------------------------------------------ cancellation, revocation, supersession, compensation
    def cancel(self, effect_id: str, cancel_record_id: str, reason: str, provider: Optional[MockProvider] = None) -> str:
        st = self.state(effect_id)
        ctx = {"cancel_record_id": cancel_record_id}
        if st == "RESERVED":
            self.conn.execute("UPDATE outbox SET done=1 WHERE effect_id=? AND done=0", (effect_id,))
            return self._transition(effect_id, "cancel", ctx, reason, [("UPDATE reservations SET status='released' WHERE effect_id=?", (effect_id,))])
        if st == "DISPATCHING":
            new = self._transition(effect_id, "cancel", ctx, reason)
            if provider is not None:
                att = self.conn.execute("SELECT provider_request_id FROM attempts WHERE effect_id=? ORDER BY attempt_id DESC LIMIT 1", (effect_id,)).fetchone()
                if att and att["provider_request_id"]:
                    provider.cancel(att["provider_request_id"])
            return new
        raise InvalidTransition("Effect", st, "cancel")

    def revoke_authority(self, approval_id: str, now: Optional[datetime] = None) -> dict[str, list[str]]:
        now = now or _utcnow()
        self.conn.execute("INSERT OR IGNORE INTO revocations(approval_id, revoked_at) VALUES (?,?)", (approval_id, _iso(now)))
        out = {"cancelled": [], "cancel_requested": [], "retained_for_reconciliation": []}
        for r in self.conn.execute("SELECT effect_id, state, authority_json FROM effects").fetchall():
            if approval_id not in json.loads(r["authority_json"]).values():
                continue
            if r["state"] == "RESERVED":
                self.cancel(r["effect_id"], "revocation:" + approval_id, "authority revoked")
                out["cancelled"].append(r["effect_id"])
            elif r["state"] == "DISPATCHING":
                self.cancel(r["effect_id"], "revocation:" + approval_id, "authority revoked during dispatch")
                out["cancel_requested"].append(r["effect_id"])
            elif r["state"] in ("DISPATCHED", "UNKNOWN", "CONFIRMED"):
                out["retained_for_reconciliation"].append(r["effect_id"])
        return out

    def supersede(self, effect_id: str, new_intent: dict, supersession_approval_id: str, reservation_minor: int) -> str:
        eff = self._row(effect_id)
        if eff["effect_slot"] != new_intent["effect_slot"]:
            raise ValueError("supersession must target the same effect slot")
        self.conn.execute("UPDATE outbox SET done=1 WHERE effect_id=? AND done=0", (effect_id,))
        self._transition(effect_id, "supersede", {"supersession_approval_id": supersession_approval_id, "successor_intent_id": new_intent["logical_action_id"]},
                         "explicit supersession " + supersession_approval_id,
                         [("UPDATE effects SET successor=? WHERE effect_id=?", (new_intent["logical_action_id"], effect_id)), ("UPDATE reservations SET status='released' WHERE effect_id=?", (effect_id,))])
        new_intent = dict(new_intent, supersedes_intent_id=effect_id)
        return self.reserve(new_intent, reservation_minor)

    def compensate(self, effect_id: str, compensation_approval_id: str, compensation_intent: dict, reservation_minor: int) -> str:
        """Compensation is a new authorized effect in its own slot; the original record is never deleted."""
        self._transition(effect_id, "compensate", {"compensation_approval_id": compensation_approval_id}, "compensation authorized " + compensation_approval_id)
        comp_id = self.reserve(compensation_intent, reservation_minor)
        self.conn.execute("UPDATE effects SET compensation_effect_id=? WHERE effect_id=?", (comp_id, effect_id))
        return comp_id

    def finish_compensation(self, effect_id: str) -> str:
        eff = self._row(effect_id)
        comp = self._row(eff["compensation_effect_id"])
        if comp["state"] == "CONFIRMED":
            return self._transition(effect_id, "compensation_confirmed", {"compensation_effect_state": "CONFIRMED"}, "compensating effect confirmed")
        return self._transition(effect_id, "compensation_failed", {}, "compensating effect did not confirm")

    # ------------------------------------------------------------ introspection
    def audit_trail(self, effect_id: str) -> list[tuple[str, str, str]]:
        return [(r["from_state"], r["to_state"], r["event"]) for r in self.conn.execute("SELECT * FROM audit WHERE effect_id=? ORDER BY seq", (effect_id,))]

    def receipts_for(self, effect_id: str) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM receipts WHERE effect_id=?", (effect_id,)).fetchone()[0]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()
