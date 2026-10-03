"""Guard behaviour for approval, release, step and case machines (AT-050..AT-058)."""
from datetime import datetime, timedelta, timezone

import pytest

from guards import REGISTRY
from machine import GuardFailed, GuardedMachine, InvalidTransition

NOW = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)


def m(name):
    return GuardedMachine.load(name, REGISTRY[name])


def test_unregistered_guard_fails_closed():
    mm = GuardedMachine.load("approval.yaml", {})  # no guards registered
    with pytest.raises(GuardFailed):
        mm.fire("REQUESTED", "decide_grant", {}, "x")


def test_invalid_transition_and_terminal_states():
    with pytest.raises(InvalidTransition):
        m("approval.yaml").fire("DENIED", "decide_grant", {}, "x")
    with pytest.raises(InvalidTransition):
        m("effect.yaml").fire("UNKNOWN", "claim", {}, "x")


def _approval_ctx(**over):
    ctx = {
        "approver_authenticated": True, "approver_role": "domain_approver", "allowed_roles": ["domain_approver"],
        "approver_tenant": "t1", "tenant_id": "t1", "nonce_consumed": False, "now": NOW,
        "expires_at": NOW + timedelta(hours=1), "bound_digests": ["sha256:a"], "current_digests": ["sha256:a"],
        "prerequisite_state": {"case_version": 7}, "current_prerequisite_state": {"case_version": 7},
    }
    ctx.update(over)
    return ctx


def test_approval_requires_fresh_nonce_matching_digest_and_unchanged_case():
    a = m("approval.yaml")
    assert a.fire("REQUESTED", "decide_grant", _approval_ctx(), "ok").to_state == "GRANTED"
    for bad in ({"nonce_consumed": True}, {"current_digests": ["sha256:b"]}, {"current_prerequisite_state": {"case_version": 8}}, {"expires_at": NOW - timedelta(seconds=1)}, {"approver_role": "employee"}, {"approver_tenant": "t2"}):
        with pytest.raises(GuardFailed):
            a.fire("REQUESTED", "decide_grant", _approval_ctx(**bad), "bad")
    r = a.fire("GRANTED", "artifact_or_state_changed", _approval_ctx(current_digests=["sha256:b"]), "changed")
    assert r.to_state == "INVALIDATED"


def _attest(check, digest, who="verifier-svc", outcome="pass"):
    return {"check_id": check, "artifact_digests": [digest], "verifier_identity": who, "outcome": outcome, "expires_at": None}


def test_release_verification_requires_verifier_attestations_on_manifest_digest():
    r = m("release.yaml")
    base = {"required_checks": ["chk_a", "chk_b"], "manifest_digest": "sha256:m", "builder_identities": ["builder-svc"], "now": NOW}
    ok = dict(base, attestations=[_attest("chk_a", "sha256:m"), _attest("chk_b", "sha256:m")])
    assert r.fire("CANDIDATE", "verify", ok, "ok").to_state == "VERIFIED"
    for bad in (
        dict(base, attestations=[_attest("chk_a", "sha256:m")]),                                   # missing check
        dict(base, attestations=[_attest("chk_a", "sha256:m"), _attest("chk_b", "sha256:old")]),    # stale bytes
        dict(base, attestations=[_attest("chk_a", "sha256:m"), _attest("chk_b", "sha256:m", who="builder-svc")]),  # builder attesting
        dict(base, attestations=[_attest("chk_a", "sha256:m"), _attest("chk_b", "sha256:m", outcome="fail")]),
    ):
        with pytest.raises(GuardFailed):
            r.fire("CANDIDATE", "verify", bad, "bad")


def test_release_activation_approval_must_bind_manifest_digest():
    r = m("release.yaml")
    with pytest.raises(GuardFailed):
        r.fire("VERIFIED", "approve", {"activation_approval_required": True, "activation_approval_state": "GRANTED", "manifest_digest": "sha256:m", "activation_approval_bound_digests": ["sha256:other"]}, "x")
    assert r.fire("VERIFIED", "approve", {"activation_approval_required": False}, "low impact").to_state == "APPROVED"
    with pytest.raises(GuardFailed):
        r.fire("CANARY", "activate", {"canary_gates_ok": True, "canary_high_severity_failures": 0, "envelope_status": "active", "now": NOW, "authority_revoked": True}, "revoked")


def test_step_result_cannot_verify_itself():
    s = m("step.yaml")
    ctx = {"fencing_token": 3, "current_fencing_token": 3, "output_digests": ["sha256:x"]}
    assert s.fire("RUNNING", "result_committed", ctx, "committed").to_state == "VERIFYING"
    with pytest.raises(GuardFailed):
        s.fire("VERIFYING", "attestation_accepted", {"attestation_digests": ["sha256:x"], "output_digests": ["sha256:x"], "attestation_verifier": "builder-svc", "verifier_identity": "verifier-svc", "builder_identities": ["builder-svc"]}, "builder signed")
    assert s.fire("VERIFYING", "attestation_accepted", {"attestation_digests": ["sha256:x"], "output_digests": ["sha256:x"], "attestation_verifier": "verifier-svc", "verifier_identity": "verifier-svc", "builder_identities": ["builder-svc"]}, "ok").to_state == "VERIFIED"
    with pytest.raises(GuardFailed):
        s.fire("RUNNING", "result_committed", {"fencing_token": 2, "current_fencing_token": 3, "output_digests": ["sha256:x"]}, "stale")


def test_lease_expiry_reconciles_before_reassignment():
    s = m("step.yaml")
    assert s.fire("RUNNING", "lease_expired", {}, "expired").to_state == "RECONCILING"
    with pytest.raises(GuardFailed):
        s.fire("RECONCILING", "effects_reconciled", {"unknown_effects": 1, "attempt_no": 1, "max_attempts": 3}, "still unknown")
    assert s.fire("RECONCILING", "effects_reconciled", {"unknown_effects": 0, "attempt_no": 1, "max_attempts": 3}, "clean").to_state == "READY"


def test_case_completion_blocked_by_unknown_effect_and_reopen_bumps_epoch():
    c = m("case.yaml")
    with pytest.raises(GuardFailed):
        c.fire("ACTIVE", "complete", {"predicate_ok": True, "effect_states": ["CONFIRMED", "UNKNOWN"]}, "x")
    assert c.fire("ACTIVE", "complete", {"predicate_ok": True, "effect_states": ["CONFIRMED"]}, "done").to_state == "COMPLETED"
    with pytest.raises(GuardFailed):
        c.fire("COMPLETED", "reopen", {"retroactive_change": True, "old_epoch": 1, "new_epoch": 1}, "no epoch bump")
    assert c.fire("COMPLETED", "reopen", {"retroactive_change": True, "old_epoch": 1, "new_epoch": 2}, "late statement").to_state == "REOPENED"


def test_review_decision_bound_to_case_version():
    c = m("case.yaml")
    with pytest.raises(GuardFailed):
        c.fire("WAITING_REVIEW", "review_decided", {"reviewer_role": "domain_approver", "allowed_reviewer_roles": ["domain_approver"], "decision_case_version": 7, "case_version": 8, "item_case_version": 7}, "stale")
    assert c.fire("WAITING_REVIEW", "evidence_changed", {"material_change": True}, "doc arrived").to_state == "ACTIVE"
