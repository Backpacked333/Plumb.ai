"""Collector convergence reference (spec/integrations-and-collectors.md, DC-010..DC-016).

Implements overlap-window polling with (external_id, external_version) deduplication, late corrections,
deletions as tombstones, tied timestamps, expired-cursor resync and explicit coverage state. An empty page and
an outage are different facts: the first says the source had nothing new in the window, the second says we do
not know. Neither is evidence that a business object does not exist.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


class SourceOutage(Exception):
    pass


class CursorExpired(Exception):
    pass


@dataclass
class SourceRecord:
    external_id: str
    external_version: int
    updated_at: datetime
    deleted: bool = False
    payload: dict = field(default_factory=dict)


class MockSource:
    def __init__(self, cursor_ttl: timedelta = timedelta(days=30)):
        self.records: dict[str, SourceRecord] = {}
        self.outage = False
        self.cursor_ttl = cursor_ttl
        self.now: Optional[datetime] = None

    def upsert(self, rec: SourceRecord) -> None:
        self.records[rec.external_id] = rec

    def changed_since(self, since: datetime, now: datetime, page_size: int = 100, page: int = 0) -> list[SourceRecord]:
        if self.outage:
            raise SourceOutage()
        if now - since > self.cursor_ttl:
            raise CursorExpired()
        rows = sorted([r for r in self.records.values() if r.updated_at >= since], key=lambda r: (r.updated_at, r.external_id))
        return rows[page * page_size : (page + 1) * page_size]

    def full_list(self, now: datetime) -> list[SourceRecord]:
        if self.outage:
            raise SourceOutage()
        return sorted(self.records.values(), key=lambda r: (r.updated_at, r.external_id))


@dataclass
class CollectorState:
    watermark: Optional[datetime] = None
    seen: dict[str, int] = field(default_factory=dict)       # external_id -> highest version stored
    stored: dict[str, SourceRecord] = field(default_factory=dict)
    tombstones: set[str] = field(default_factory=set)
    duplicates_suppressed: int = 0
    last_success: Optional[datetime] = None
    coverage_state: str = "unknown"   # unknown | complete | bounded
    failures: int = 0


class Collector:
    def __init__(self, source: MockSource, overlap: timedelta, poll_interval: timedelta):
        self.source = source
        self.overlap = overlap
        self.poll_interval = poll_interval
        self.state = CollectorState()

    def _apply(self, rec: SourceRecord) -> bool:
        """Returns True when the record changed local state."""
        prev = self.state.seen.get(rec.external_id)
        if prev is not None and rec.external_version <= prev:
            self.state.duplicates_suppressed += 1
            return False
        self.state.seen[rec.external_id] = rec.external_version
        if rec.deleted:
            self.state.tombstones.add(rec.external_id)
            self.state.stored.pop(rec.external_id, None)
        else:
            self.state.stored[rec.external_id] = rec
        return True

    def poll(self, now: datetime) -> dict:
        since = (self.state.watermark - self.overlap) if self.state.watermark else datetime.min.replace(tzinfo=now.tzinfo)
        try:
            page, changed, max_seen = 0, 0, self.state.watermark
            while True:
                rows = self.source.changed_since(since, now, page=page)
                for r in rows:
                    if self._apply(r):
                        changed += 1
                    if max_seen is None or r.updated_at > max_seen:
                        max_seen = r.updated_at
                if len(rows) < 100:
                    break
                page += 1
            # watermark advances only to the latest record time we actually saw, never to `now`
            if max_seen is not None:
                self.state.watermark = max_seen
            self.state.last_success = now
            self.state.coverage_state = "complete"
            self.state.failures = 0
            return {"changed": changed, "coverage_state": "complete", "lag_s": 0.0}
        except CursorExpired:
            return self.resync(now)
        except SourceOutage:
            self.state.failures += 1
            self.state.coverage_state = "unknown"
            lag = (now - self.state.last_success).total_seconds() if self.state.last_success else None
            return {"changed": 0, "coverage_state": "unknown", "lag_s": lag}

    def resync(self, now: datetime) -> dict:
        """Expired cursor: full listing, reconciled against local state. Deletions are detected by absence."""
        rows = self.source.full_list(now)
        present = {r.external_id for r in rows}
        changed = sum(1 for r in rows if self._apply(r))
        for ext_id in list(self.state.stored):
            if ext_id not in present:
                self.state.tombstones.add(ext_id)
                self.state.stored.pop(ext_id)
                changed += 1
        self.state.watermark = max((r.updated_at for r in rows), default=self.state.watermark)
        self.state.last_success = now
        self.state.coverage_state = "complete"
        return {"changed": changed, "coverage_state": "complete_after_resync", "lag_s": 0.0}

    def freshness(self, now: datetime, max_age: timedelta) -> dict:
        age = (now - self.state.last_success) if self.state.last_success else None
        healthy = age is not None and age <= max_age and self.state.coverage_state.startswith("complete")
        return {"age_s": None if age is None else age.total_seconds(), "healthy": healthy, "coverage_state": self.state.coverage_state}

    def object_absent(self, external_id: str) -> str:
        """Three-valued: 'absent' only when coverage is complete; otherwise 'unknown'."""
        if external_id in self.state.stored:
            return "present"
        if external_id in self.state.tombstones:
            return "deleted"
        return "absent" if self.state.coverage_state.startswith("complete") else "unknown"
