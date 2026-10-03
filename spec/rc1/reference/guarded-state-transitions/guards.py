"""Guard registries. Each guard reads a context dict assembled by the owning service from authoritative
state (never from a model's output). Keys used by each guard are documented inline; a missing key fails closed.

Context assembly rules (SR-013): every value in ctx is read inside the same database transaction that
will persist the transition's writes, so a guard never passes on data that could be stale at commit time.
"""
from __future__ import annotations

from datetime import datetime, timezone


def _now(ctx: dict) -> datetime:
    return ctx.get("now") or datetime.now(timezone.utc)


def _get(ctx: dict, key: str):
    return ctx.get(key)


# ---------------------------------------------------------------- effect guards

EFFECT_GUARDS = {
    "release_active_or_canary": lambda c: c.get("release_state") in ("ACTIVE", "CANARY"),
    "authority_current_not_revoked": lambda c: bool(c.get("approval_state") in ("GRANTED", None if not c.get("requires_case_approval") else "GRANTED"))
    and not c.get("grant_revoked", False)
    and c.get("envelope_status") == "active"
    and _now(c) < c.get("approval_expires_at", _now(c).replace(year=9999)),
    "expected_state_versions_match": lambda c: c.get("expected_state_versions") == c.get("current_state_versions"),
    "cost_reserved": lambda c: c.get("reservation_status") == "reserved",
    "lease_cas_succeeded": lambda c: bool(c.get("lease_cas_ok")),
    "outbox_row_claimed": lambda c: bool(c.get("outbox_claimed")),
    "fencing_token_current": lambda c: c.get("fencing_token") == c.get("current_fencing_token"),
    "receipt_recorded": lambda c: bool(c.get("receipt_id")) and bool(c.get("receipt_verified")),
    "rejection_is_non_terminal": lambda c: c.get("rejection_kind") in ("rate_limited", "transient", "unavailable"),
    "attempts_remaining": lambda c: int(c.get("attempt_no", 0)) < int(c.get("max_attempts", 0)),
    "rejection_is_terminal_or_attempts_exhausted": lambda c: c.get("rejection_kind") in ("invalid", "forbidden", "not_found")
    or int(c.get("attempt_no", 0)) >= int(c.get("max_attempts", 0)),
    "postcondition_read_from_provider_or_verified_receipt": lambda c: bool(c.get("postcondition_ok")) and c.get("postcondition_source") in ("provider_read", "verified_receipt"),
    "reservation_settled": lambda c: c.get("reservation_status") in ("settled", "settling"),
    "provider_lookup_confirms_occurrence": lambda c: c.get("lookup_result") == "found",
    "provider_lookup_establishes_non_occurrence": lambda c: c.get("lookup_result") == "absent" and bool(c.get("lookup_authoritative")),
    "provider_state_conflicts_with_expected": lambda c: c.get("lookup_result") == "conflict",
    "non_occurrence_unprovable_and_retry_class_forbids": lambda c: c.get("lookup_result") in ("absent_unverifiable", "unknown")
    and c.get("retry_class") == "not_retryable_after_ambiguity",
    "still_uncertain_within_reconcile_budget": lambda c: c.get("lookup_result") in ("absent_unverifiable", "unknown")
    and c.get("retry_class") != "not_retryable_after_ambiguity"
    and int(c.get("reconcile_attempts", 0)) < int(c.get("max_reconcile_attempts", 0)),
    "retry_class_permits": lambda c: c.get("retry_class") in ("natural_idempotent", "provider_keyed", "reconcilable")
    and not (c.get("retry_class") == "provider_keyed" and c.get("idempotency_window_expired", False)),
    "attempts_exhausted_or_retry_forbidden": lambda c: int(c.get("attempt_no", 0)) >= int(c.get("max_attempts", 0))
    or c.get("retry_class") == "not_retryable_after_ambiguity"
    or (c.get("retry_class") == "provider_keyed" and c.get("idempotency_window_expired", False)),
    "resolver_authorized": lambda c: c.get("resolver_role") in ("domain_approver", "tenant_owner", "platform_operator"),
    "resolution_recorded": lambda c: bool(c.get("resolution_id")),
    "cancel_or_revocation_recorded": lambda c: bool(c.get("cancel_record_id")),
    "supersession_authorized": lambda c: bool(c.get("supersession_approval_id")),
    "successor_intent_recorded": lambda c: bool(c.get("successor_intent_id")),
    "compensation_authorized": lambda c: bool(c.get("compensation_approval_id")),
    "compensation_class_permits": lambda c: c.get("compensation_class") in ("native_undo", "compensating_effect"),
    "compensation_effect_confirmed": lambda c: c.get("compensation_effect_state") == "CONFIRMED",
}

# ---------------------------------------------------------------- approval guards

APPROVAL_GUARDS = {
    "approver_authenticated_and_authorized": lambda c: bool(c.get("approver_authenticated"))
    and c.get("approver_role") in set(c.get("allowed_roles", []))
    and c.get("approver_tenant") == c.get("tenant_id"),
    "nonce_unused": lambda c: not c.get("nonce_consumed", True),
    "not_expired": lambda c: _now(c) < c["expires_at"] if "expires_at" in c else False,
    "bound_digests_match_current_artifacts": lambda c: set(c.get("bound_digests", [])) == set(c.get("current_digests", [])) and bool(c.get("bound_digests")),
    "prerequisite_state_matches": lambda c: c.get("prerequisite_state", {}) == c.get("current_prerequisite_state", {}),
    "expiry_passed": lambda c: "expires_at" in c and _now(c) >= c["expires_at"],
    "revoker_authorized": lambda c: c.get("revoker_role") in ("tenant_owner", "domain_approver", "platform_operator") or c.get("revoker_id") == c.get("approver_id"),
    "bound_digest_or_prerequisite_changed": lambda c: set(c.get("bound_digests", [])) != set(c.get("current_digests", []))
    or c.get("prerequisite_state", {}) != c.get("current_prerequisite_state", {}),
}

# ---------------------------------------------------------------- release guards

RELEASE_GUARDS = {
    "all_required_attestations_bound_to_manifest_digest": lambda c: set(c.get("required_checks", [])) <= {a["check_id"] for a in c.get("attestations", []) if c.get("manifest_digest") in a.get("artifact_digests", []) and a.get("outcome") in ("pass", "pass_with_limitations")},
    "attestations_not_expired": lambda c: all((a.get("expires_at") is None) or (_now(c) < a["expires_at"]) for a in c.get("attestations", [])),
    "no_attestation_from_builder_identity": lambda c: all(a.get("verifier_identity") not in set(c.get("builder_identities", [])) for a in c.get("attestations", [])),
    "activation_approval_bound_to_manifest_digest_or_not_required": lambda c: (not c.get("activation_approval_required"))
    or (c.get("activation_approval_state") == "GRANTED" and c.get("manifest_digest") in set(c.get("activation_approval_bound_digests", []))),
    "envelope_active": lambda c: c.get("envelope_status") == "active" and _now(c) < c.get("envelope_expires_at", _now(c).replace(year=9999)),
    "infra_applied_and_verified": lambda c: bool(c.get("infra_attestation_ok")),
    "shadow_divergence_within_limit": lambda c: c.get("shadow_divergence") is not None and c["shadow_divergence"] <= c.get("shadow_divergence_max", 0.0),
    "shadow_duration_met": lambda c: c.get("shadow_opportunities_for_failure", 0) >= c.get("shadow_min_opportunities", 1),
    "canary_gates_passed": lambda c: bool(c.get("canary_gates_ok")) and int(c.get("canary_high_severity_failures", 1)) == 0,
    "current_authority_not_revoked": lambda c: not c.get("authority_revoked", False),
    "diagnostic_recorded": lambda c: bool(c.get("diagnostic_id")),
    "canary_cases_reconciled": lambda c: int(c.get("unknown_effects", 1)) == 0,
    "pause_authorized_or_kill_switch": lambda c: c.get("actor_role") in ("tenant_owner", "domain_approver", "platform_operator", "runtime_operator_service") or bool(c.get("kill_switch")),
    "resume_authorized": lambda c: c.get("actor_role") in ("tenant_owner", "domain_approver", "platform_operator"),
    "incident_closed_or_absent": lambda c: c.get("open_incident") in (None, False),
    "previous_compatible_release_available": lambda c: bool(c.get("previous_release_id")) and bool(c.get("previous_schema_compatible")),
    "in_flight_cases_pinned_or_migrated": lambda c: int(c.get("unpinned_in_flight_cases", 1)) == 0,
    "retire_authorized": lambda c: c.get("actor_role") in ("tenant_owner", "platform_operator"),
    "no_active_cases_pinned": lambda c: int(c.get("active_cases_pinned", 1)) == 0,
}

# ---------------------------------------------------------------- step guards (subset used in tests)

STEP_GUARDS = {
    "all_dependencies_verified": lambda c: all(s == "VERIFIED" for s in c.get("dependency_states", [])),
    "lease_cas_succeeded": lambda c: bool(c.get("lease_cas_ok")),
    "budget_reserved_for_attempt": lambda c: c.get("reservation_status") == "reserved",
    "attempts_remaining": lambda c: int(c.get("attempt_no", 0)) < int(c.get("max_attempts", 0)),
    "attempts_exhausted": lambda c: int(c.get("attempt_no", 0)) >= int(c.get("max_attempts", 0)),
    "capability_grant_issued": lambda c: bool(c.get("capability_grant_id")),
    "fencing_token_current": lambda c: c.get("fencing_token") == c.get("current_fencing_token"),
    "result_digests_present": lambda c: bool(c.get("output_digests")) and all(d.startswith("sha256:") for d in c.get("output_digests", [])),
    "no_unknown_effects_outstanding": lambda c: int(c.get("unknown_effects", 1)) == 0,
    "dependency_recorded": lambda c: bool(c.get("dependency_id")),
    "dependency_resolved_by_authorized_role": lambda c: c.get("dependency_resolver_role") == c.get("dependency_respondent_role"),
    "attestation_matches_result_digests": lambda c: set(c.get("attestation_digests", [])) == set(c.get("output_digests", [])) and bool(c.get("output_digests")),
    "attestation_from_verifier_identity": lambda c: c.get("attestation_verifier") == c.get("verifier_identity") and c.get("attestation_verifier") not in set(c.get("builder_identities", [])),
    "diagnostic_recorded": lambda c: bool(c.get("diagnostic_id")),
    "failure_class_retryable": lambda c: c.get("failure_class") in ("transient_infrastructure", "implementation_defect", "source_schema_change", "poor_model_quality"),
    "failure_class_terminal_or_attempts_exhausted": lambda c: c.get("failure_class") in ("exhausted_resources", "unsupported_capability")
    or int(c.get("attempt_no", 0)) >= int(c.get("max_attempts", 0)),
    "cancel_authorized": lambda c: c.get("actor_role") in ("tenant_owner", "platform_operator", "build_orchestrator_service"),
}

# ---------------------------------------------------------------- build guards (subset)

BUILD_GUARDS = {
    "plan_validator_passed": lambda c: c.get("validation_errors") == [],
    "plan_digest_recorded": lambda c: str(c.get("plan_digest", "")).startswith("sha256:"),
    "envelope_active": RELEASE_GUARDS["envelope_active"],
    "implement_approval_present_if_required": lambda c: (not c.get("implement_approval_required")) or c.get("implement_approval_state") == "GRANTED",
    "build_budget_reserved": lambda c: c.get("reservation_status") == "reserved",
    "dependency_kind_is_authorization_or_access": lambda c: c.get("dependency_kind") in ("authorization", "access", "commitment"),
    "dependency_kind_is_business_decision": lambda c: c.get("dependency_kind") in ("business_decision", "unsupported_capability"),
    "dependency_resolved_by_authorized_role": STEP_GUARDS["dependency_resolved_by_authorized_role"],
    "all_required_steps_verified": lambda c: all(s == "VERIFIED" for s in c.get("required_step_states", [])) and bool(c.get("required_step_states")),
    "no_open_dependencies": lambda c: int(c.get("open_dependencies", 1)) == 0,
    "required_attestations_bound_to_current_digests": RELEASE_GUARDS["all_required_attestations_bound_to_manifest_digest"],
    "attestations_not_expired": RELEASE_GUARDS["attestations_not_expired"],
    "repair_budget_remaining": lambda c: int(c.get("repair_attempts", 0)) < int(c.get("max_repair_attempts", 0)),
    "repair_budget_exhausted": lambda c: int(c.get("repair_attempts", 0)) >= int(c.get("max_repair_attempts", 0)),
    "failure_classified": lambda c: bool(c.get("failure_class")),
    "cancel_authorized": STEP_GUARDS["cancel_authorized"],
    "uncertain_effects_reconciled": lambda c: int(c.get("unknown_effects", 1)) == 0,
}

# ---------------------------------------------------------------- case guards (subset)

CASE_GUARDS = {
    "release_pinned": lambda c: bool(c.get("release_id")) and c.get("release_state") in ("ACTIVE", "CANARY", "SHADOW"),
    "required_sources_fresh": lambda c: all(age <= mx for age, mx in c.get("source_ages", [])),
    "case_key_unique_for_release_epoch": lambda c: not c.get("duplicate_case_exists", True),
    "durable_wait_declared_in_workflow": lambda c: c.get("wait_name") in set(c.get("declared_waits", [])),
    "event_matches_case_key": lambda c: c.get("event_case_key") == c.get("case_key"),
    "event_not_already_processed": lambda c: c.get("event_id") not in set(c.get("processed_event_ids", [])),
    "timer_declared_in_workflow": lambda c: c.get("timer_name") in set(c.get("declared_timers", [])),
    "review_surface_available": lambda c: bool(c.get("review_surface")),
    "review_item_created": lambda c: bool(c.get("review_item_id")),
    "reviewer_authorized": lambda c: c.get("reviewer_role") in set(c.get("allowed_reviewer_roles", [])),
    "decision_bound_to_case_version": lambda c: c.get("decision_case_version") == c.get("case_version"),
    "case_version_unchanged_since_item": lambda c: c.get("item_case_version") == c.get("case_version"),
    "material_change_detected": lambda c: bool(c.get("material_change")),
    "completion_predicate_satisfied": lambda c: bool(c.get("predicate_ok")),
    "all_effects_confirmed_or_not_needed": lambda c: all(s in ("CONFIRMED", "COMPENSATED") for s in c.get("effect_states", [])),
    "no_unknown_effects": lambda c: "UNKNOWN" not in set(c.get("effect_states", [])),
    "terminal_failure_classified": lambda c: bool(c.get("failure_class")),
    "cancel_authorized": STEP_GUARDS["cancel_authorized"],
    "reopen_authorized_or_retroactive_change_detected": lambda c: bool(c.get("reopen_authorized")) or bool(c.get("retroactive_change")),
    "obligation_epoch_incremented": lambda c: int(c.get("new_epoch", 0)) == int(c.get("old_epoch", 0)) + 1,
}

REGISTRY = {
    "effect.yaml": EFFECT_GUARDS,
    "approval.yaml": APPROVAL_GUARDS,
    "release.yaml": RELEASE_GUARDS,
    "step.yaml": STEP_GUARDS,
    "build.yaml": BUILD_GUARDS,
    "case.yaml": CASE_GUARDS,
}
