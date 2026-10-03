"""Collector convergence scenarios (AT-080..AT-087). Group: Evidence and collectors."""
from datetime import datetime, timedelta, timezone

from convergence import Collector, MockSource, SourceRecord

T0 = datetime(2026, 10, 1, tzinfo=timezone.utc)


def mk(n, t, v=1, deleted=False):
    return SourceRecord(external_id=f"txn_{n}", external_version=v, updated_at=t, deleted=deleted, payload={"n": n, "v": v})


def test_duplicates_reordered_and_tied_timestamps_converge():
    src, col = MockSource(), Collector(MockSource(), overlap=timedelta(minutes=10), poll_interval=timedelta(minutes=5))
    col.source = src
    for n in (3, 1, 2):
        src.upsert(mk(n, T0 + timedelta(minutes=1)))  # tied timestamps, out of order
    col.poll(T0 + timedelta(minutes=2))
    col.poll(T0 + timedelta(minutes=7))  # overlap re-reads the same window
    assert len(col.state.stored) == 3 and col.state.duplicates_suppressed == 3


def test_late_correction_replaces_by_version_not_time():
    src = MockSource()
    col = Collector(src, overlap=timedelta(minutes=10), poll_interval=timedelta(minutes=5))
    src.upsert(mk(1, T0, v=1))
    col.poll(T0 + timedelta(minutes=1))
    src.upsert(mk(1, T0 + timedelta(minutes=30), v=2))  # corrected later
    col.poll(T0 + timedelta(minutes=31))
    assert col.state.stored["txn_1"].external_version == 2
    src.upsert(mk(1, T0 + timedelta(minutes=40), v=1))  # stale replay of an old version
    col.poll(T0 + timedelta(minutes=41))
    assert col.state.stored["txn_1"].external_version == 2


def test_deletion_becomes_tombstone():
    src = MockSource()
    col = Collector(src, overlap=timedelta(minutes=10), poll_interval=timedelta(minutes=5))
    src.upsert(mk(1, T0))
    col.poll(T0 + timedelta(minutes=1))
    src.upsert(mk(1, T0 + timedelta(minutes=5), v=2, deleted=True))
    col.poll(T0 + timedelta(minutes=6))
    assert "txn_1" in col.state.tombstones and "txn_1" not in col.state.stored
    assert col.object_absent("txn_1") == "deleted"


def test_outage_is_unknown_not_absent():
    src = MockSource()
    col = Collector(src, overlap=timedelta(minutes=10), poll_interval=timedelta(minutes=5))
    src.upsert(mk(1, T0))
    col.poll(T0 + timedelta(minutes=1))
    assert col.object_absent("txn_2") == "absent"
    src.outage = True
    r = col.poll(T0 + timedelta(minutes=10))
    assert r["coverage_state"] == "unknown" and col.object_absent("txn_2") == "unknown"
    assert not col.freshness(T0 + timedelta(minutes=10), timedelta(minutes=5))["healthy"]


def test_expired_cursor_triggers_resync_and_detects_silent_deletes():
    src = MockSource(cursor_ttl=timedelta(days=30))
    col = Collector(src, overlap=timedelta(hours=2), poll_interval=timedelta(hours=1))
    src.upsert(mk(1, T0)); src.upsert(mk(2, T0))
    col.poll(T0 + timedelta(hours=1))
    del src.records["txn_2"]  # hard-deleted at source, no tombstone served
    src.upsert(mk(3, T0 + timedelta(days=40)))
    r = col.poll(T0 + timedelta(days=45))  # beyond provider look-back
    assert r["coverage_state"] == "complete_after_resync"
    assert set(col.state.stored) == {"txn_1", "txn_3"} and "txn_2" in col.state.tombstones


def test_pagination_captures_every_record_across_pages():
    src = MockSource()
    col = Collector(src, overlap=timedelta(minutes=10), poll_interval=timedelta(minutes=5))
    for n in range(257):
        src.upsert(mk(n, T0 + timedelta(seconds=n)))
    col.poll(T0 + timedelta(minutes=10))
    assert len(col.state.stored) == 257


def test_watermark_never_advances_past_observed_records():
    src = MockSource()
    col = Collector(src, overlap=timedelta(minutes=10), poll_interval=timedelta(minutes=5))
    src.upsert(mk(1, T0))
    col.poll(T0 + timedelta(hours=5))
    assert col.state.watermark == T0  # not "now": a late record with updated_at between would otherwise be missed
