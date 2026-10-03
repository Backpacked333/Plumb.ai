"""Adapter contract kit applied to the mock provider (IC-010 subset). Real adapters run the same kit against
provider sandboxes (integration-gated)."""
from datetime import datetime, timezone

from ledger import MockProvider

T0 = datetime(2026, 10, 3, tzinfo=timezone.utc)


def test_provider_side_idempotency_inside_window():
    p = MockProvider(idempotency_window_s=3600)
    a = p.send("k1", {"x": 1}, T0)
    b = p.send("k1", {"x": 1}, T0)
    assert a.request_id == b.request_id and len(p.sent) == 1


def test_provider_window_expiry_creates_second_object():
    from datetime import timedelta
    p = MockProvider(idempotency_window_s=10)
    a = p.send("k1", {"x": 1}, T0)
    b = p.send("k1", {"x": 1}, T0 + timedelta(seconds=11))
    assert a.request_id != b.request_id  # why PROVIDER_KEYED retries are forbidden after the window


def test_signature_verification_rejects_tampering():
    p = MockProvider()
    sig = p.sign("req_1")
    assert sig != p.sign("req_2")
