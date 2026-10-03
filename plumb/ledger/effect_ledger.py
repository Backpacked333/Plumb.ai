"""SQLite effect ledger (specification sections 16 and 23).

A small, local simulation of the production effect gateway's persistence. It
exercises persisted deduplication, payload conflicts, UNKNOWN reconciliation
and auditable transitions; it does not implement a production outbox,
distributed leases or provider guarantees.

Implements:

* PL-037: :meth:`EffectLedger.reserve` persists the action intent *before*
  dispatch. The slot key is ``UNIQUE``: the same slot with the same payload
  returns the existing action; the same slot with a different payload raises
  :class:`PayloadConflict` unless the intent names the settled action it
  supersedes (an explicit supersession decision).
* PL-038: a timeout or ambiguous outcome moves the effect to ``UNKNOWN``
  (:meth:`EffectLedger.mark_unknown`); while UNKNOWN, a retry on the slot is
  refused with :class:`EffectUnknown`. Leaving UNKNOWN requires a
  :class:`~plumb.contracts.effect.ReconciliationResult`: a receipt for
  ``CONFIRMED`` or provider-confirmed non-occurrence for ``FAILED_FINAL``.
  Provider request ids, external ids and receipts are stored on the row.
* PL-039: deduplication is keyed on the effect slot alone, so it survives
  process restarts (same file, new connection) and is independent of
  ``deployment_version``.
* PL-057 / PL-017: every write runs in an explicit ``BEGIN IMMEDIATE``
  transaction; every state change goes through the ``EFFECT`` state machine
  and is persisted with its reason, time and guard in ``effect_transitions``;
  the row carries a ``state_version``. The lease owner is recorded alongside
  the intent, so a lease is never the only record that an action was attempted.
  :meth:`EffectLedger.outstanding` is the restart reconciliation list.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import AwareDatetime, ConfigDict

from plumb.contracts.common import (
    EffectClass,
    EffectState,
    ErrorClass,
    NonEmptyStr,
    SourceRef,
    StrictModel,
    utcnow,
)
from plumb.contracts.effect import (
    ActionIntent,
    ActionReceipt,
    EffectSlot,
    ReconciliationOutcome,
    ReconciliationResult,
)
from plumb.statemachines.machines import EFFECT, IllegalTransition

SETTLED_STATES: frozenset[EffectState] = frozenset(
    {EffectState.CONFIRMED, EffectState.FAILED_FINAL, EffectState.COMPENSATED}
)
"""States in which an action may be superseded on its slot."""

OUTSTANDING_STATES: frozenset[EffectState] = frozenset({EffectState.DISPATCHED, EffectState.UNKNOWN})
"""States a restarted dispatcher must reconcile before doing anything else (PL-039)."""

SUPERSEDED_MARKER = "#superseded-by:"
"""Appended to a superseded row's slot key so the new action can hold the logical key."""

_RECONCILE_TARGET: Mapping[ReconciliationOutcome, EffectState] = {
    ReconciliationOutcome.CONFIRMED: EffectState.CONFIRMED,
    ReconciliationOutcome.FAILED_FINAL: EffectState.FAILED_FINAL,
    ReconciliationOutcome.STILL_UNKNOWN: EffectState.UNKNOWN,
}

_STATE_LIST = ", ".join(f"'{state.value}'" for state in EffectState)
_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS effects (
    action_id                 TEXT PRIMARY KEY,
    tenant_id                 TEXT NOT NULL,
    slot_key                  TEXT NOT NULL UNIQUE,
    payload_digest            TEXT NOT NULL,
    expected_state_version    INTEGER NOT NULL,
    authority_ref             TEXT NOT NULL,
    deployment_version        TEXT NOT NULL,
    provider_target_json      TEXT NOT NULL,
    effect_class              TEXT NOT NULL,
    idempotency_key           TEXT NOT NULL,
    state                     TEXT NOT NULL CHECK (state IN ({_STATE_LIST})),
    state_version             INTEGER NOT NULL DEFAULT 1,
    lease_owner               TEXT,
    provider_request_id       TEXT,
    external_id               TEXT,
    receipt_json              TEXT,
    compensation_receipt_json TEXT,
    supersedes_action_id      TEXT REFERENCES effects(action_id),
    created_at                TEXT NOT NULL,
    updated_at                TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS effects_outstanding
    ON effects(tenant_id, state) WHERE state IN ('DISPATCHED', 'UNKNOWN');
CREATE TABLE IF NOT EXISTS effect_transitions (
    seq        INTEGER PRIMARY KEY AUTOINCREMENT,
    action_id  TEXT NOT NULL REFERENCES effects(action_id),
    from_state TEXT,
    to_state   TEXT NOT NULL,
    reason     TEXT NOT NULL CHECK (length(reason) > 0),
    at         TEXT NOT NULL,
    guard      TEXT
);
CREATE INDEX IF NOT EXISTS effect_transitions_by_action ON effect_transitions(action_id, seq);
"""


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------


class EffectRow(StrictModel):
    """One persisted effect, as stored."""

    model_config = ConfigDict(frozen=True)

    action_id: str
    tenant_id: str
    slot_key: str
    payload_digest: str
    expected_state_version: int
    authority_ref: str
    deployment_version: str
    provider_target: SourceRef
    effect_class: EffectClass
    idempotency_key: str
    state: EffectState
    state_version: int
    lease_owner: str | None
    provider_request_id: str | None
    external_id: str | None
    receipt: ActionReceipt | None
    compensation_receipt: ActionReceipt | None
    supersedes_action_id: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime

    @property
    def logical_slot_key(self) -> str:
        """The slot key without any supersession marker."""
        return self.slot_key.split(SUPERSEDED_MARKER, 1)[0]

    @property
    def superseded_by_action_id(self) -> str | None:
        """The action that took over this row's slot, if any."""
        _, marker, successor = self.slot_key.partition(SUPERSEDED_MARKER)
        return successor if marker else None


class EffectTransition(StrictModel):
    """One persisted row of ``effect_transitions`` (PL-057)."""

    model_config = ConfigDict(frozen=True)

    seq: int
    action_id: str
    from_state: EffectState | None
    to_state: EffectState
    reason: NonEmptyStr
    at: AwareDatetime
    guard: str | None


class ReservationResult(StrictModel):
    """Outcome of :meth:`EffectLedger.reserve`."""

    model_config = ConfigDict(frozen=True)

    action_id: str
    state: EffectState
    created: bool
    existing_action_id: str | None


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class LedgerError(Exception):
    """Base class for ledger errors; ``error_class`` names the protocol error class (section 22)."""

    error_class: ErrorClass = ErrorClass.STATE_CONFLICT


class UnknownAction(LedgerError):
    """No row exists for the given ``action_id``."""

    def __init__(self, action_id: str) -> None:
        self.action_id = action_id
        super().__init__(f"unknown action {action_id!r}")


class ActionIdConflict(LedgerError):
    """The ``action_id`` is already bound to a different effect slot."""

    def __init__(self, action_id: str, bound_slot_key: str, offered_slot_key: str) -> None:
        self.action_id = action_id
        self.bound_slot_key = bound_slot_key
        self.offered_slot_key = offered_slot_key
        super().__init__(f"action {action_id!r} is already bound to slot {bound_slot_key!r}")


class PayloadConflict(LedgerError):
    """Same effect slot, different payload, no valid supersession decision (PL-037)."""

    error_class = ErrorClass.PAYLOAD_CONFLICT

    def __init__(
        self,
        action_id: str,
        slot_key: str,
        existing_payload_digest: str,
        offered_payload_digest: str,
        detail: str | None = None,
    ) -> None:
        self.action_id = action_id
        self.slot_key = slot_key
        self.existing_payload_digest = existing_payload_digest
        self.offered_payload_digest = offered_payload_digest
        message = (
            f"slot {slot_key!r} is held by action {action_id!r} with payload {existing_payload_digest}; "
            f"offered payload {offered_payload_digest}"
        )
        super().__init__(f"{message}: {detail}" if detail else f"{message}: explicit supersession required")


class SupersessionRefused(PayloadConflict):
    """The intent claims a supersession the ledger cannot honour."""


class EffectUnknown(LedgerError):
    """The slot's action is UNKNOWN; retry is refused until it is reconciled (PL-038)."""

    error_class = ErrorClass.EFFECT_UNKNOWN

    def __init__(self, action_id: str, slot_key: str) -> None:
        self.action_id = action_id
        self.slot_key = slot_key
        super().__init__(f"action {action_id!r} on slot {slot_key!r} is UNKNOWN; reconcile before retrying")


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------


class EffectLedger:
    """Persisted effect identity, deduplication and reconciliation over SQLite.

    ``clock`` supplies every timestamp written by the ledger (defaults to
    :func:`plumb.contracts.common.utcnow`) so tests can be deterministic.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        clock: Callable[[], datetime] = utcnow,
        busy_timeout_ms: int = 5000,
    ) -> None:
        self._path = str(path)
        self._clock = clock
        self._conn = sqlite3.connect(self._path, isolation_level=None, timeout=busy_timeout_ms / 1000)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute(f"PRAGMA busy_timeout={int(busy_timeout_ms)}")
        self._conn.executescript(_SCHEMA)

    # -- lifecycle -----------------------------------------------------------

    @property
    def path(self) -> str:
        return self._path

    def pragmas(self) -> dict[str, Any]:
        """Connection settings relevant to durability: journal mode and foreign-key enforcement."""
        return {
            "journal_mode": self._conn.execute("PRAGMA journal_mode").fetchone()[0],
            "foreign_keys": bool(self._conn.execute("PRAGMA foreign_keys").fetchone()[0]),
        }

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "EffectLedger":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # -- writes --------------------------------------------------------------

    def reserve(self, intent: ActionIntent, *, reason: str = "reserved before dispatch") -> ReservationResult:
        """Persist the intent in ``RESERVED`` or return the action already holding its slot (PL-037).

        * same slot, same payload: the existing action is returned (``created=False``);
        * same slot, different payload: :class:`PayloadConflict`, unless
          ``intent.supersedes_action_id`` names the settled action holding the slot;
        * slot held by an ``UNKNOWN`` action: :class:`EffectUnknown` (PL-038).
        """
        slot_key = intent.slot.key()
        with self._transaction() as cur:
            existing = self._fetch_by_slot(cur, slot_key)
            if existing is None:
                if intent.supersedes_action_id is not None:
                    raise SupersessionRefused(
                        intent.supersedes_action_id,
                        slot_key,
                        "<none>",
                        intent.payload_digest,
                        detail=f"no live action holds slot {slot_key!r}; nothing to supersede",
                    )
                self._insert(cur, intent, slot_key, reason)
                return ReservationResult(
                    action_id=intent.action_id, state=EffectState.RESERVED, created=True, existing_action_id=None
                )

            if existing.state is EffectState.UNKNOWN:
                raise EffectUnknown(existing.action_id, slot_key)

            same_payload = existing.payload_digest == intent.payload_digest
            if same_payload and intent.supersedes_action_id in (None, existing.supersedes_action_id):
                return ReservationResult(
                    action_id=existing.action_id,
                    state=existing.state,
                    created=False,
                    existing_action_id=existing.action_id,
                )

            if intent.supersedes_action_id is None:
                raise PayloadConflict(existing.action_id, slot_key, existing.payload_digest, intent.payload_digest)
            if intent.supersedes_action_id != existing.action_id:
                raise SupersessionRefused(
                    existing.action_id,
                    slot_key,
                    existing.payload_digest,
                    intent.payload_digest,
                    detail=f"intent supersedes {intent.supersedes_action_id!r} but the slot is held by "
                    f"{existing.action_id!r}",
                )
            if existing.state not in SETTLED_STATES:
                raise SupersessionRefused(
                    existing.action_id,
                    slot_key,
                    existing.payload_digest,
                    intent.payload_digest,
                    detail=f"action {existing.action_id!r} is {existing.state.value}; only "
                    f"{'/'.join(sorted(s.value for s in SETTLED_STATES))} actions can be superseded",
                )

            now = self._now()
            cur.execute(
                "UPDATE effects SET slot_key = ?, updated_at = ? WHERE action_id = ?",
                (f"{slot_key}{SUPERSEDED_MARKER}{intent.action_id}", now.isoformat(), existing.action_id),
            )
            self._record_transition(
                cur,
                existing.action_id,
                existing.state,
                existing.state,
                f"superseded by action {intent.action_id} (explicit supersession decision)",
                now,
                None,
            )
            self._insert(cur, intent, slot_key, f"{reason}; supersedes action {existing.action_id}")
            return ReservationResult(
                action_id=intent.action_id,
                state=EffectState.RESERVED,
                created=True,
                existing_action_id=existing.action_id,
            )

    def mark_dispatched(
        self,
        action_id: str,
        lease_owner: str,
        provider_request_id: str,
        *,
        reason: str = "dispatched to provider under lease",
    ) -> EffectRow:
        """``RESERVED -> DISPATCHED``; records the lease owner and the provider request id (PL-057)."""
        if not lease_owner.strip():
            raise ValueError("lease_owner must be recorded before dispatch")
        if not provider_request_id.strip():
            raise ValueError("provider_request_id must be recorded before dispatch")
        with self._transaction() as cur:
            row = self._load(cur, action_id)
            return self._move(
                cur,
                row,
                EffectState.DISPATCHED,
                {},
                reason,
                lease_owner=lease_owner,
                provider_request_id=provider_request_id,
            )

    def mark_unknown(self, action_id: str, reason: str) -> EffectRow:
        """``DISPATCHED -> UNKNOWN`` on timeout or ambiguous outcome (PL-038)."""
        with self._transaction() as cur:
            row = self._load(cur, action_id)
            return self._move(cur, row, EffectState.UNKNOWN, {}, reason)

    def confirm(
        self,
        action_id: str,
        receipt: ActionReceipt,
        *,
        reason: str = "provider receipt stored and postcondition observed",
    ) -> EffectRow:
        """``DISPATCHED -> CONFIRMED``; the receipt is mandatory and stored (PL-038)."""
        if not isinstance(receipt, ActionReceipt):
            raise TypeError("confirm() requires an ActionReceipt")
        with self._transaction() as cur:
            row = self._load(cur, action_id)
            return self._move(
                cur,
                row,
                EffectState.CONFIRMED,
                {"external_receipt": receipt},
                reason,
                receipt_json=receipt.model_dump_json(),
                external_id=receipt.external_id,
            )

    def fail_final(self, action_id: str, reason: str) -> EffectRow:
        """``RESERVED|DISPATCHED -> FAILED_FINAL``. From ``UNKNOWN`` use :meth:`reconcile`."""
        with self._transaction() as cur:
            row = self._load(cur, action_id)
            return self._move(cur, row, EffectState.FAILED_FINAL, {}, reason)

    def reconcile(self, action_id: str, result: ReconciliationResult, *, reason: str | None = None) -> EffectRow:
        """Leave ``UNKNOWN`` only through a valid reconciliation result (PL-038).

        ``CONFIRMED`` stores the receipt and moves to CONFIRMED; ``FAILED_FINAL``
        moves to FAILED_FINAL; ``STILL_UNKNOWN`` leaves the state untouched but
        records the attempt in ``effect_transitions``.
        """
        if not isinstance(result, ReconciliationResult):
            raise TypeError("reconcile() requires a ReconciliationResult")
        text = reason or f"reconciled as {result.outcome.value}: {result.evidence}"
        target = _RECONCILE_TARGET[result.outcome]
        with self._transaction() as cur:
            row = self._load(cur, action_id)
            if row.state is not EffectState.UNKNOWN:
                raise IllegalTransition(
                    EFFECT.name, row.state.value, target.value, detail="reconcile applies to UNKNOWN effects only"
                )
            if result.outcome is ReconciliationOutcome.STILL_UNKNOWN:
                now = self._now()
                self._record_transition(cur, action_id, row.state, row.state, text, now, None)
                cur.execute("UPDATE effects SET updated_at = ? WHERE action_id = ?", (now.isoformat(), action_id))
                return self._load(cur, action_id)
            context: dict[str, Any] = {"reconciliation_result": result.outcome.value}
            updates: dict[str, Any] = {}
            if result.outcome is ReconciliationOutcome.CONFIRMED:
                receipt = result.receipt
                assert receipt is not None  # guaranteed by ReconciliationResult's validator
                context["external_receipt"] = receipt
                updates = {"receipt_json": receipt.model_dump_json(), "external_id": receipt.external_id}
            return self._move(cur, row, target, context, text, **updates)

    def compensate(
        self,
        action_id: str,
        compensation_receipt: ActionReceipt,
        *,
        reason: str = "compensating action confirmed by provider receipt",
    ) -> EffectRow:
        """``CONFIRMED -> COMPENSATED``; the original receipt is retained alongside the compensation receipt."""
        if not isinstance(compensation_receipt, ActionReceipt):
            raise TypeError("compensate() requires an ActionReceipt")
        with self._transaction() as cur:
            row = self._load(cur, action_id)
            return self._move(
                cur,
                row,
                EffectState.COMPENSATED,
                {"compensation_receipt": compensation_receipt},
                reason,
                compensation_receipt_json=compensation_receipt.model_dump_json(),
            )

    # -- reads ---------------------------------------------------------------

    def get(self, action_id: str) -> EffectRow:
        row = self._fetch(self._conn, action_id)
        if row is None:
            raise UnknownAction(action_id)
        return row

    def find_by_slot(self, slot: EffectSlot | str) -> EffectRow | None:
        """The action currently holding a slot (superseded rows are not returned)."""
        slot_key = slot.key() if isinstance(slot, EffectSlot) else slot
        return self._fetch_by_slot(self._conn, slot_key)

    def outstanding(self, tenant_id: str | None = None) -> list[EffectRow]:
        """Effects in DISPATCHED or UNKNOWN: what a restarted dispatcher must reconcile first (PL-039)."""
        sql = f"SELECT * FROM effects WHERE state IN ({', '.join('?' for _ in OUTSTANDING_STATES)})"
        params: list[Any] = sorted(state.value for state in OUTSTANDING_STATES)
        if tenant_id is not None:
            sql += " AND tenant_id = ?"
            params.append(tenant_id)
        sql += " ORDER BY created_at, action_id"
        return [_row_to_effect(row) for row in self._conn.execute(sql, params)]

    def transitions(self, action_id: str) -> list[EffectTransition]:
        """The persisted audit trail of one action, oldest first (PL-057)."""
        rows = self._conn.execute(
            "SELECT * FROM effect_transitions WHERE action_id = ? ORDER BY seq", (action_id,)
        ).fetchall()
        return [_row_to_transition(row) for row in rows]

    # -- internals -----------------------------------------------------------

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Cursor]:
        cur = self._conn.cursor()
        cur.execute("BEGIN IMMEDIATE")
        try:
            yield cur
        except BaseException:
            cur.execute("ROLLBACK")
            raise
        else:
            cur.execute("COMMIT")
        finally:
            cur.close()

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("the ledger clock must return timezone-aware datetimes")
        return now

    @staticmethod
    def _fetch(executor: sqlite3.Connection | sqlite3.Cursor, action_id: str) -> EffectRow | None:
        row = executor.execute("SELECT * FROM effects WHERE action_id = ?", (action_id,)).fetchone()
        return _row_to_effect(row) if row is not None else None

    @staticmethod
    def _fetch_by_slot(executor: sqlite3.Connection | sqlite3.Cursor, slot_key: str) -> EffectRow | None:
        row = executor.execute("SELECT * FROM effects WHERE slot_key = ?", (slot_key,)).fetchone()
        return _row_to_effect(row) if row is not None else None

    def _load(self, cur: sqlite3.Cursor, action_id: str) -> EffectRow:
        row = self._fetch(cur, action_id)
        if row is None:
            raise UnknownAction(action_id)
        return row

    def _insert(self, cur: sqlite3.Cursor, intent: ActionIntent, slot_key: str, reason: str) -> None:
        bound = self._fetch(cur, intent.action_id)
        if bound is not None:
            raise ActionIdConflict(intent.action_id, bound.slot_key, slot_key)
        now = self._now().isoformat()
        cur.execute(
            """
            INSERT INTO effects (
                action_id, tenant_id, slot_key, payload_digest, expected_state_version, authority_ref,
                deployment_version, provider_target_json, effect_class, idempotency_key, state, state_version,
                supersedes_action_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            """,
            (
                intent.action_id,
                intent.tenant_id,
                slot_key,
                intent.payload_digest,
                intent.expected_state_version,
                intent.authority_ref,
                intent.deployment_version,
                intent.provider_target.model_dump_json(),
                intent.effect_class.value,
                intent.idempotency_key,
                EffectState.RESERVED.value,
                intent.supersedes_action_id,
                now,
                now,
            ),
        )
        self._record_transition(cur, intent.action_id, None, EffectState.RESERVED, reason, datetime.fromisoformat(now), None)

    def _move(
        self,
        cur: sqlite3.Cursor,
        row: EffectRow,
        target: EffectState,
        context: Mapping[str, Any],
        reason: str,
        **column_updates: Any,
    ) -> EffectRow:
        """Apply one state-machine transition and persist it atomically with the row update."""
        now = self._now()
        transition = EFFECT.transition(row.state, target, context, reason, at=now)
        columns: dict[str, Any] = {
            **column_updates,
            "state": target.value,
            "state_version": row.state_version + 1,
            "updated_at": now.isoformat(),
        }
        assignments = ", ".join(f"{name} = ?" for name in columns)
        cur.execute(f"UPDATE effects SET {assignments} WHERE action_id = ?", (*columns.values(), row.action_id))
        self._record_transition(cur, row.action_id, row.state, target, reason, now, transition.guard)
        return self._load(cur, row.action_id)

    @staticmethod
    def _record_transition(
        cur: sqlite3.Cursor,
        action_id: str,
        from_state: EffectState | None,
        to_state: EffectState,
        reason: str,
        at: datetime,
        guard: str | None,
    ) -> None:
        cur.execute(
            "INSERT INTO effect_transitions (action_id, from_state, to_state, reason, at, guard) VALUES (?, ?, ?, ?, ?, ?)",
            (
                action_id,
                from_state.value if from_state is not None else None,
                to_state.value,
                reason,
                at.isoformat(),
                guard,
            ),
        )


def _row_to_effect(row: sqlite3.Row) -> EffectRow:
    return EffectRow(
        action_id=row["action_id"],
        tenant_id=row["tenant_id"],
        slot_key=row["slot_key"],
        payload_digest=row["payload_digest"],
        expected_state_version=row["expected_state_version"],
        authority_ref=row["authority_ref"],
        deployment_version=row["deployment_version"],
        provider_target=SourceRef.model_validate_json(row["provider_target_json"]),
        effect_class=EffectClass(row["effect_class"]),
        idempotency_key=row["idempotency_key"],
        state=EffectState(row["state"]),
        state_version=row["state_version"],
        lease_owner=row["lease_owner"],
        provider_request_id=row["provider_request_id"],
        external_id=row["external_id"],
        receipt=_receipt_or_none(row["receipt_json"]),
        compensation_receipt=_receipt_or_none(row["compensation_receipt_json"]),
        supersedes_action_id=row["supersedes_action_id"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _receipt_or_none(text: str | None) -> ActionReceipt | None:
    return ActionReceipt.model_validate(json.loads(text)) if text else None


def _row_to_transition(row: sqlite3.Row) -> EffectTransition:
    return EffectTransition(
        seq=row["seq"],
        action_id=row["action_id"],
        from_state=EffectState(row["from_state"]) if row["from_state"] is not None else None,
        to_state=EffectState(row["to_state"]),
        reason=row["reason"],
        at=datetime.fromisoformat(row["at"]),
        guard=row["guard"],
    )


__all__ = [
    "SETTLED_STATES",
    "OUTSTANDING_STATES",
    "SUPERSEDED_MARKER",
    "EffectRow",
    "EffectTransition",
    "ReservationResult",
    "LedgerError",
    "UnknownAction",
    "ActionIdConflict",
    "PayloadConflict",
    "SupersessionRefused",
    "EffectUnknown",
    "IllegalTransition",
    "EffectLedger",
]
