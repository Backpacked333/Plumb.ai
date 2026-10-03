"""Argument-aware gateway scenarios (AT-060..AT-072). Group: Authority and identity; Security and privacy."""
import copy
from datetime import datetime, timedelta, timezone

import pytest

from gateway import AuthContext, GatewayStore, authorize

NOW = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)
D = "sha256:" + "1" * 64


def store():
    return GatewayStore(
        envelopes={"env_1": {"tenant_id": "t1", "status": "active", "version": "3", "effect_classes_allowed": ["external_message", "external_record_write"], "processors_allowed": ["plumb:control", "openai:api:zdr"], "single_action_max_minor": 500}},
        grants={"g_mail": {"tenant_id": "t1", "status": "active", "purposes": ["discovery", "operation"]}, "g_read_only": {"tenant_id": "t1", "status": "active", "purposes": ["discovery"]}, "g_expired": {"tenant_id": "t1", "status": "expired", "purposes": ["operation"]}},
        releases={"rel_1": {"tenant_id": "t1", "state": "ACTIVE", "actions": {
            "gmail.send": {"requires_case_approval": True, "allowed_approver_roles": ["domain_approver"], "template_class": "document_request_v1", "per_recipient_budget": 3},
            "qbo.attachable.create": {"requires_case_approval": False, "account_ref": "qbo-realm-4011"},
        }}},
        approvals={"apr_1": {"approval_id": "apr_1", "tenant_id": "t1", "status": "GRANTED", "bound_digests": [D], "prerequisite_state": {"case_version": 7}, "expires_at": NOW + timedelta(hours=2), "approver_role": "domain_approver"}},
        cases={"case_1": {"tenant_id": "t1", "version": 7, "client_id": "client_0142", "documents": ["doc_req_list_2026_08"]}, "case_t2": {"tenant_id": "t2", "version": 1, "client_id": "c9"}},
        client_contacts={"client_0142": {"maria@pinestreetbakery.example"}},
        recipient_sends={},
        revoked_approvals=set(),
        now=NOW,
    )


def intent(**over):
    base = {
        "tenant_id": "t1",
        "case_ref": {"object_type": "Case", "id": "case_1"},
        "operation_id": "gmail.send",
        "effect_class": "external_message",
        "payload_digest": D,
        "payload": {"to": "maria@pinestreetbakery.example", "template_class": "document_request_v1", "attachments": ["doc_req_list_2026_08"], "period": "2026-08"},
        "authority": {"release_id": "rel_1", "envelope_id": "env_1", "envelope_version": "3", "grant_ids": ["g_mail"], "approval_id": "apr_1"},
        "processor": "openai:api:zdr",
        "spend_minor": 20,
    }
    base.update(over)
    return base


AUTH = AuthContext("svc_runtime", "t1", "runtime_worker")


def test_happy_path_allowed():
    assert authorize(intent(), AUTH, store()).allowed


def test_forged_body_tenant_denied():
    d = authorize(intent(tenant_id="t2"), AUTH, store())
    assert not d.allowed and d.reasons == ["SCOPE_DENIED:tenant_mismatch"]


def test_cross_tenant_case_reference_denied():
    d = authorize(intent(case_ref={"object_type": "Case", "id": "case_t2"}), AUTH, store())
    assert "SCOPE_DENIED:case_not_in_tenant" in d.reasons


def test_wrong_provider_account_and_raw_sql_denied():
    d = authorize(intent(operation_id="qbo.attachable.create", effect_class="external_record_write", account_ref="qbo-realm-9999", sql="DROP TABLE x", payload={}), AUTH, store())
    assert {"SCOPE_DENIED:wrong_provider_account", "SCOPE_DENIED:raw_sql_not_an_operation"} <= set(d.reasons)


def test_expired_grant_and_read_only_grant_denied():
    assert "PURPOSE_DENIED:grant_inactive:g_expired" in authorize(intent(authority={**intent()["authority"], "grant_ids": ["g_expired"]}), AUTH, store()).reasons
    assert "PURPOSE_DENIED:grant_lacks_operation:g_read_only" in authorize(intent(authority={**intent()["authority"], "grant_ids": ["g_read_only"]}), AUTH, store()).reasons


def test_processor_outside_scope_denied():
    assert "SCOPE_DENIED:processor" in authorize(intent(processor="mystery-vendor:api"), AUTH, store()).reasons


def test_revoked_approval_and_role_change_denied():
    s = store()
    s.revoked_approvals.add("apr_1")
    assert "AUTH_REQUIRED:approval_not_granted" in authorize(intent(), AUTH, s).reasons
    s2 = store()
    s2.approvals["apr_1"]["approver_role"] = "employee"  # role changed after approval
    assert "SCOPE_DENIED:approver_role" in authorize(intent(), AUTH, s2).reasons


def test_approval_bound_to_different_payload_or_case_version_denied():
    assert "STATE_CONFLICT:approval_bound_to_different_payload" in authorize(intent(payload_digest="sha256:" + "2" * 64), AUTH, store()).reasons
    s = store()
    s.cases["case_1"]["version"] = 8  # document arrived during approval
    assert "STATE_CONFLICT:case_changed_since_approval" in authorize(intent(), AUTH, s).reasons


def test_expired_approval_denied():
    s = store()
    s.now = NOW + timedelta(hours=3)
    assert "AUTH_REQUIRED:approval_expired" in authorize(intent(), AUTH, s).reasons


def test_approved_text_in_message_body_is_not_an_approval():
    s = store()
    s.approvals["apr_1"]["source"] = "message_body"
    assert any(r.startswith("AUTH_REQUIRED:approval_text") for r in authorize(intent(), AUTH, s).reasons)


def test_unauthorized_recipient_attachment_template_and_budget():
    p = intent()["payload"]
    assert "SCOPE_DENIED:recipient_not_authorized_for_client" in authorize(intent(payload={**p, "to": "attacker@example.net"}), AUTH, store()).reasons
    assert "SCOPE_DENIED:attachment_outside_case" in authorize(intent(payload={**p, "attachments": ["doc_of_other_client"]}), AUTH, store()).reasons
    assert "SCOPE_DENIED:template_class" in authorize(intent(payload={**p, "template_class": "free_text"}), AUTH, store()).reasons
    assert "SCOPE_DENIED:commitment_not_permitted" in authorize(intent(payload={**p, "commitment_class": "fee_quote"}), AUTH, store()).reasons
    s = store()
    s.recipient_sends[("maria@pinestreetbakery.example", "2026-08")] = 3
    assert "SCOPE_DENIED:per_recipient_budget_exhausted" in authorize(intent(), AUTH, s).reasons


def test_release_not_active_and_stale_envelope_version_denied():
    s = store()
    s.releases["rel_1"]["state"] = "PAUSED"
    assert "POLICY_STALE:release_not_active" in authorize(intent(), AUTH, s).reasons
    assert "POLICY_STALE:envelope_version" in authorize(intent(authority={**intent()["authority"], "envelope_version": "2"}), AUTH, store()).reasons


def test_builder_principal_cannot_dispatch():
    d = authorize(intent(), AuthContext("svc_build", "t1", "build_worker"), store())
    assert "SCOPE_DENIED:principal_role" in d.reasons


def test_spend_over_single_action_cap_denied():
    assert "BUDGET_EXCEEDED:single_action" in authorize(intent(spend_minor=900), AUTH, store()).reasons
