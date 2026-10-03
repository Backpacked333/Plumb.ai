"""Argument-aware action gateway (spec/authority-and-verification.md, SI-005..SI-014).

A tool-name allowlist is not authorization. The gateway checks the *arguments* of every ActionIntent against
authenticated identity, the active envelope, source grants, the pinned release's declared actions, the bound
approval (digest, case version, expiry, revocation) and destination rules (authorized recipients, template class,
attachment scope, per-recipient budget). Any failure denies with a reason code from ErrorEnvelope.code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class AuthContext:
    principal_id: str
    tenant_id: str           # derived from the authenticated credential, never from the request body
    role: str


@dataclass
class Decision:
    allowed: bool
    reasons: list[str] = field(default_factory=list)


@dataclass
class GatewayStore:
    """Authoritative state the gateway reads inside the dispatch transaction."""

    envelopes: dict[str, dict[str, Any]]
    grants: dict[str, dict[str, Any]]
    releases: dict[str, dict[str, Any]]      # release_id -> {"state":..., "actions": {action_id: {...}}, "tenant_id":...}
    approvals: dict[str, dict[str, Any]]
    cases: dict[str, dict[str, Any]]         # case_id -> {"tenant_id":..., "version": int, "client_id":..., "documents": [...]}
    client_contacts: dict[str, set[str]]     # client_id -> authorized recipient addresses
    recipient_sends: dict[tuple[str, str], int]  # (recipient, period) -> count
    revoked_approvals: set[str]
    now: Optional[datetime] = None

    def clock(self) -> datetime:
        return self.now or datetime.now(timezone.utc)


def authorize(intent: dict[str, Any], auth: AuthContext, store: GatewayStore) -> Decision:
    reasons: list[str] = []
    tenant = auth.tenant_id
    if intent.get("tenant_id") != tenant:
        return Decision(False, ["SCOPE_DENIED:tenant_mismatch"])
    if auth.role not in ("runtime_worker", "domain_approver", "tenant_owner"):
        reasons.append("SCOPE_DENIED:principal_role")

    case = store.cases.get(intent["case_ref"]["id"])
    if case is None or case.get("tenant_id") != tenant:
        return Decision(False, ["SCOPE_DENIED:case_not_in_tenant"])

    release = store.releases.get(intent["authority"].get("release_id", ""))
    if release is None or release.get("tenant_id") != tenant:
        reasons.append("SCOPE_DENIED:release_not_in_tenant")
    elif release.get("state") not in ("ACTIVE", "CANARY"):
        reasons.append("POLICY_STALE:release_not_active")
    action = (release or {}).get("actions", {}).get(intent["operation_id"])
    if action is None:
        reasons.append("CAPABILITY_UNSUPPORTED:operation_not_declared_in_release")

    env = store.envelopes.get(intent["authority"].get("envelope_id", ""))
    if env is None or env.get("tenant_id") != tenant or env.get("status") != "active":
        reasons.append("POLICY_STALE:envelope")
    else:
        if intent.get("effect_class") not in set(env.get("effect_classes_allowed", [])):
            reasons.append("SCOPE_DENIED:effect_class")
        proc = intent.get("processor")
        if proc and proc not in set(env.get("processors_allowed", [])):
            reasons.append("SCOPE_DENIED:processor")
        if intent.get("spend_minor", 0) > env.get("single_action_max_minor", 0):
            reasons.append("BUDGET_EXCEEDED:single_action")
        if env.get("version") != intent["authority"].get("envelope_version"):
            reasons.append("POLICY_STALE:envelope_version")

    # source grants: purpose 'operation' for every source the payload draws on
    for gid in intent["authority"].get("grant_ids", []):
        g = store.grants.get(gid)
        if g is None or g.get("tenant_id") != tenant or g.get("status") != "active":
            reasons.append(f"PURPOSE_DENIED:grant_inactive:{gid}")
        elif "operation" not in set(g.get("purposes", [])):
            reasons.append(f"PURPOSE_DENIED:grant_lacks_operation:{gid}")

    # approval binding for case-level decisions
    if action and action.get("requires_case_approval"):
        ap = store.approvals.get(intent["authority"].get("approval_id", ""))
        if ap is None or ap.get("tenant_id") != tenant:
            reasons.append("AUTH_REQUIRED:case_approval_missing")
        else:
            if ap["approval_id"] in store.revoked_approvals or ap.get("status") != "GRANTED":
                reasons.append("AUTH_REQUIRED:approval_not_granted")
            if intent["payload_digest"] not in set(ap.get("bound_digests", [])):
                reasons.append("STATE_CONFLICT:approval_bound_to_different_payload")
            if ap.get("prerequisite_state", {}).get("case_version") != case.get("version"):
                reasons.append("STATE_CONFLICT:case_changed_since_approval")
            if store.clock() >= ap.get("expires_at", store.clock()):
                reasons.append("AUTH_REQUIRED:approval_expired")
            if ap.get("approver_role") not in set(action.get("allowed_approver_roles", [])):
                reasons.append("SCOPE_DENIED:approver_role")
            if ap.get("source") == "message_body":
                reasons.append("AUTH_REQUIRED:approval_text_in_untrusted_content_is_not_an_approval")

    # destination rules for external messages
    if intent.get("effect_class") == "external_message" and action is not None:
        payload = intent.get("payload", {})
        recipient = payload.get("to")
        allowed = store.client_contacts.get(case.get("client_id"), set())
        if recipient not in allowed:
            reasons.append("SCOPE_DENIED:recipient_not_authorized_for_client")
        if payload.get("template_class") != action.get("template_class"):
            reasons.append("SCOPE_DENIED:template_class")
        attachments = set(payload.get("attachments", []))
        if not attachments <= set(case.get("documents", [])):
            reasons.append("SCOPE_DENIED:attachment_outside_case")
        budget = action.get("per_recipient_budget")
        if budget is not None and store.recipient_sends.get((recipient, payload.get("period", "")), 0) >= budget:
            reasons.append("SCOPE_DENIED:per_recipient_budget_exhausted")
        if payload.get("commitment_class") not in (None, "none"):
            reasons.append("SCOPE_DENIED:commitment_not_permitted")

    if intent.get("effect_class") == "external_record_write" and action is not None:
        if intent.get("account_ref") != action.get("account_ref"):
            reasons.append("SCOPE_DENIED:wrong_provider_account")
        if intent.get("sql") is not None:
            reasons.append("SCOPE_DENIED:raw_sql_not_an_operation")

    return Decision(not reasons, reasons)
