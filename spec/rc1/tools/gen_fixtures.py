"""Generate fixtures for the three reference scenarios and the failure catalog.

Run: python tools/gen_fixtures.py
All identifiers are synthetic. Valid fixtures are checked against the canonical models before writing; the
failure cases record the validator error codes they must produce (fixtures/failure-cases/expected.json).
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "contracts" / "canonical-models"))
from plumb_contracts.canonical import digest  # noqa: E402
from plumb_contracts.models import TOP_LEVEL_MODELS  # noqa: E402

FX = ROOT / "fixtures"
T = "2026-10-03T12:00:00+00:00"
TEXP = "2027-04-01T00:00:00+00:00"


def write(path: Path, obj: dict, model: str | None = None) -> None:
    if model:
        TOP_LEVEL_MODELS[model].model_validate(obj)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def money(cents: int) -> dict:
    return {"minor_units": cents, "currency": "USD"}


def ref(obj_type: str, id_: str, art: dict) -> dict:
    return {"object_type": obj_type, "id": id_, "digest": art[id_]["digest"]}


# ---------------------------------------------------------------- shared context builders


def envelope(tenant: str, env_id: str, grants: list[str], extra_dest: list[str] | None = None) -> dict:
    return {
        "envelope_id": env_id,
        "tenant_id": tenant,
        "version": 3,
        "owner_principal_id": "prn_owner_01",
        "goals": ["Reduce duplicate document chasing and accountant review time for monthly close"],
        "source_grant_ids": grants,
        "processors_allowed": ["plumb:control", "openai:api:zdr", "anthropic:api:zdr"],
        "regions_allowed": ["us-east-1"],
        "destinations_allowed": ["mailbox:client_contacts:*", "provider:quickbooks:realm_4011*", "storage:tenant:*"] + (extra_dest or []),
        "effect_classes_allowed": ["none", "internal", "external_message", "config_change", "infra_change"],
        "max_auto_impact": "low",
        "intervention_classes_allowed": ["remove_step", "native_configuration", "deterministic_rules", "classical_model", "general_model_workflow", "retrieval", "specialist_api", "trained_component", "optimizer"],
        "environments": ["sandbox", "shadow", "canary", "production"],
        "spend": {"build_max": money(250000), "monthly_operation_max": money(150000), "single_action_max": money(500)},
        "expires_at": TEXP,
        "escalation": [{"condition": "new_processor_required", "route_to": "prn_owner_01", "deadline_hours": 72}],
        "approval_id": "apr_env_v3",
        "status": "active",
    }


def grant(tenant: str, gid: str, provider: str, account: str, purposes: list[str]) -> dict:
    return {
        "grant_id": gid,
        "tenant_id": tenant,
        "grantor_principal_id": "prn_owner_01",
        "provider": provider,
        "account_ref": account,
        "entity_scope": ["client:*"],
        "field_scope": [],
        "purposes": purposes,
        "processors_allowed": ["plumb:control", "openai:api:zdr", "anthropic:api:zdr"],
        "regions_allowed": ["us-east-1"],
        "retention_days": 730,
        "history_from": "2024-01-01T00:00:00+00:00",
        "granted_at": T,
        "expires_at": TEXP,
        "status": "active",
        "terms_version": f"{provider}-terms-2026-01",
    }


def registry(tenant: str, caps: dict[str, tuple[str, str]]) -> dict:
    """caps: operation_id -> (account_ref, verification_level)"""
    return {op: {"tenant_id": tenant, "account_ref": acct, "verification_level": lvl} for op, (acct, lvl) in caps.items()}


def artifacts(tenant: str, ids: dict[str, dict]) -> dict:
    out = {}
    for id_, payload in ids.items():
        d = digest({"id": id_, **payload})
        out[id_] = {"tenant_id": tenant, "digest": d, **payload}
    return out


def step(sid: str, typ: str, **kw) -> dict:
    base = {
        "step_id": sid,
        "type": typ,
        "inputs": [],
        "input_ports": [],
        "output_ports": [],
        "required_capabilities": [],
        "min_capability_level": "sandbox_tested",
        "depends_on": [],
        "purposes_used": ["implementation"],
        "processors_used": ["plumb:control"],
        "destinations": [],
        "effect_class": "none",
        "compensation_class": "not_needed",
        "budget_max": money(2000),
        "max_attempts": 3,
        "timeout_s": 1800,
        "verification": [],
        "produces_release_artifact": False,
    }
    base.update(kw)
    return base


# ---------------------------------------------------------------- accounting scenario


def accounting() -> tuple[dict, dict]:
    tenant = "tnt_barlowkim"
    grants = {
        "grant_gmail_ops": grant(tenant, "grant_gmail_ops", "google_workspace", "gws-acct-7F2A", ["discovery", "implementation", "operation"]),
        "grant_qbo_main": grant(tenant, "grant_qbo_main", "quickbooks_online", "qbo-realm-4011", ["discovery", "implementation", "operation", "evaluation", "training"]),
        "grant_drive_docs": grant(tenant, "grant_drive_docs", "google_drive", "gws-acct-7F2A", ["discovery", "implementation", "operation"]),
    }
    env = envelope(tenant, "env_barlowkim_v3", list(grants))
    arts = artifacts(
        tenant,
        {
            "sol_doc_intake_v1": {"kind": "SolutionSpec", "impact_class": "low"},
            "env_barlowkim_v3": {"kind": "AutonomyEnvelope", "version": 3},
            "inv_barlowkim_2026_09": {"kind": "EnvironmentInventory"},
            "pkt_doc_chase_evidence": {"kind": "EvidencePacket"},
            "tsk_categorization_v1": {"kind": "TaskDefinition"},
            "chk_bundle_doc_intake_v1": {"kind": "ProtectedCheckBundle"},
        },
    )
    arts["pkt_other_tenant"] = {"tenant_id": "tnt_other_firm", "digest": digest({"id": "pkt_other_tenant"}), "kind": "EvidencePacket"}
    caps = registry(
        tenant,
        {
            "google_workspace:gmail.threads.list": ("gws-acct-7F2A", "account_verified"),
            "google_workspace:gmail.drafts.create": ("gws-acct-7F2A", "account_verified"),
            "google_workspace:gmail.messages.send": ("gws-acct-7F2A", "sandbox_tested"),
            "google_drive:files.list": ("gws-acct-7F2A", "account_verified"),
            "google_drive:changes.watch": ("gws-acct-7F2A", "sandbox_tested"),
            "quickbooks_online:query.Purchase": ("qbo-realm-4011", "account_verified"),
            "quickbooks_online:cdc": ("qbo-realm-4011", "account_verified"),
            "quickbooks_online:webhooks.subscribe": ("qbo-realm-4011", "sandbox_tested"),
            "quickbooks_online:attachable.create": ("qbo-realm-4011", "documented"),
            "plumb:collector.deploy": ("plumb", "production_observed"),
            "plumb:dataset.build": ("plumb", "production_observed"),
            "plumb:workflow.compile": ("plumb", "production_observed"),
            "plumb:verifier.request": ("plumb", "production_observed"),
            "plumb:infra.pulumi": ("plumb", "sandbox_tested"),
            "plumb:release.create": ("plumb", "production_observed"),
            "plumb:agent.harness": ("plumb", "sandbox_tested"),
        },
    )
    rec_port = {"name": "qbo_records", "semantic_type": "record_set", "scope": "qbo-realm-4011"}
    money_port = {"name": "txn_amounts", "semantic_type": "money", "currency": "USD", "scope": "qbo-realm-4011"}
    plan = {
        "plan_id": "plan_barlowkim_doc_intake_v1",
        "tenant_id": tenant,
        "solution_ref": ref("SolutionSpec", "sol_doc_intake_v1", arts),
        "envelope_ref": ref("AutonomyEnvelope", "env_barlowkim_v3", arts),
        "schema_version": "1.0",
        "release_schema_version": "1.0",
        "case_migration_declared": False,
        "total_budget_max": money(60000),
        "steps": [
            step("step_probe_gmail", "probe_source", inputs=[ref("EnvironmentInventory", "inv_barlowkim_2026_09", arts)], required_capabilities=["google_workspace:gmail.threads.list"], min_capability_level="account_verified", purposes_used=["discovery", "implementation"]),
            step("step_probe_qbo", "probe_source", inputs=[ref("EnvironmentInventory", "inv_barlowkim_2026_09", arts)], required_capabilities=["quickbooks_online:query.Purchase", "quickbooks_online:cdc"], min_capability_level="account_verified", purposes_used=["discovery", "implementation"]),
            step("step_profile_qbo", "profile_source", depends_on=["step_probe_qbo"], output_ports=[rec_port, money_port], required_capabilities=["quickbooks_online:query.Purchase"], min_capability_level="account_verified"),
            step("step_adapter_drive_folder_map", "generate_adapter", depends_on=["step_probe_gmail"], required_capabilities=["plumb:agent.harness", "google_drive:files.list"], budget_max=money(8000), timeout_s=7200, notes="Nontrivial adaptation: map the firm's non-standard client folder layout to client/period identities"),
            step("step_test_adapter", "test_adapter", depends_on=["step_adapter_drive_folder_map"], required_capabilities=["plumb:agent.harness"], verification=[{"check_id": "chk_adapter_contract_v1", "criteria_version": "1", "data_role": "regression"}]),
            step("step_collector_docs", "deploy_collector", depends_on=["step_test_adapter"], required_capabilities=["plumb:collector.deploy", "google_drive:changes.watch"], effect_class="config_change", compensation_class="native_undo", destinations=["storage:tenant:barlowkim"], budget_max=money(3000), verification=[{"check_id": "chk_collector_live_event_v1", "criteria_version": "1", "data_role": "regression"}], produces_release_artifact=True),
            step("step_collector_qbo", "deploy_collector", depends_on=["step_profile_qbo"], input_ports=[rec_port], required_capabilities=["plumb:collector.deploy", "quickbooks_online:cdc"], min_capability_level="account_verified", effect_class="config_change", compensation_class="native_undo", destinations=["storage:tenant:barlowkim"], budget_max=money(3000), verification=[{"check_id": "chk_collector_live_event_v1", "criteria_version": "1", "data_role": "regression"}], produces_release_artifact=True),
            step("step_backfill_qbo", "backfill", depends_on=["step_collector_qbo"], required_capabilities=["quickbooks_online:query.Purchase"], min_capability_level="account_verified", budget_max=money(4000), timeout_s=14400),
            step("step_reconcile_qbo", "reconcile_collector", depends_on=["step_backfill_qbo"], required_capabilities=["plumb:collector.deploy"], verification=[{"check_id": "chk_backfill_reconciliation_v1", "criteria_version": "1", "data_role": "regression"}]),
            step("step_discover_labels", "discover_labels", depends_on=["step_reconcile_qbo"], inputs=[ref("TaskDefinition", "tsk_categorization_v1", arts)], input_ports=[rec_port], purposes_used=["evaluation"], required_capabilities=["plumb:dataset.build"]),
            step("step_build_dataset", "build_dataset", depends_on=["step_discover_labels"], purposes_used=["evaluation", "training"], required_capabilities=["plumb:dataset.build"], verification=[{"check_id": "chk_dataset_leakage_v1", "criteria_version": "1", "data_role": "protected_acceptance"}]),
            step("step_experiment", "run_experiment", depends_on=["step_build_dataset"], purposes_used=["evaluation"], processors_used=["plumb:control", "openai:api:zdr"], required_capabilities=["plumb:dataset.build"], budget_max=money(6000)),
            step("step_compile_workflow", "compile_workflow", depends_on=["step_collector_docs", "step_experiment"], required_capabilities=["plumb:workflow.compile"], produces_release_artifact=True, verification=[{"check_id": "chk_workflow_scenarios_v1", "criteria_version": "1", "data_role": "protected_acceptance"}]),
            step("step_generate_tests", "generate_tests", depends_on=["step_compile_workflow"], required_capabilities=["plumb:agent.harness"]),
            step("step_request_verification", "request_verification", depends_on=["step_generate_tests"], inputs=[ref("ProtectedCheckBundle", "chk_bundle_doc_intake_v1", arts)], required_capabilities=["plumb:verifier.request"], min_capability_level="production_observed"),
            step("step_preview_infra", "preview_infra", depends_on=["step_request_verification"], required_capabilities=["plumb:infra.pulumi"]),
            step("step_apply_infra", "apply_infra", depends_on=["step_preview_infra"], required_capabilities=["plumb:infra.pulumi"], effect_class="infra_change", compensation_class="native_undo", destinations=["storage:tenant:barlowkim"], budget_max=money(5000)),
            step("step_create_release", "create_release", depends_on=["step_apply_infra"], required_capabilities=["plumb:release.create"], produces_release_artifact=True, verification=[{"check_id": "chk_release_manifest_v1", "criteria_version": "1", "data_role": "regression"}]),
        ],
    }
    ctx = {"tenant_id": tenant, "envelope": env, "grants": grants, "artifacts": arts, "capabilities": caps, "approval_obligations": []}
    workflow = {
        "workflow_id": "wf_barlowkim_doc_intake_v1",
        "tenant_id": tenant,
        "case_key_fields": ["client_id", "period"],
        "triggers": ["schedule:period_start", "event:document.arrived", "event:obligation.reopened"],
        "input_ports": [{"name": "obligations", "semantic_type": "record_set", "scope": "tnt_barlowkim"}, {"name": "documents", "semantic_type": "record_set", "scope": "tnt_barlowkim"}],
        "source_freshness": {"google_drive": 900, "quickbooks_online": 3600, "google_workspace": 900},
        "states": ["RESOLVE_CASE", "RECONCILE_EVIDENCE", "CONSOLIDATE_MISSING", "REQUEST_DRAFTED", "AWAIT_SEND_REVIEW", "SENT", "WAIT_DOCUMENTS", "VALIDATE_DOCUMENTS", "PREPARE_PACKAGE", "AWAIT_SIGNOFF", "PACKAGE_ACCEPTED", "ESCALATED", "CANCELLED"],
        "initial_state": "RESOLVE_CASE",
        "terminal_states": ["PACKAGE_ACCEPTED", "ESCALATED", "CANCELLED"],
        "transitions": [
            {"from_state": "RESOLVE_CASE", "event": "case_resolved", "to_state": "RECONCILE_EVIDENCE", "guards": ["client_and_period_resolved_to_approved_identities"]},
            {"from_state": "RECONCILE_EVIDENCE", "event": "evidence_reconciled", "to_state": "CONSOLIDATE_MISSING", "guards": ["sources_fresh"]},
            {"from_state": "CONSOLIDATE_MISSING", "event": "nothing_missing", "to_state": "PREPARE_PACKAGE", "guards": ["checklist_satisfied"]},
            {"from_state": "CONSOLIDATE_MISSING", "event": "items_missing", "to_state": "REQUEST_DRAFTED", "guards": ["reminder_policy_permits", "no_open_request_for_obligation_epoch"], "actions": ["draft_consolidated_request"]},
            {"from_state": "REQUEST_DRAFTED", "event": "policy_auto_send", "to_state": "SENT", "guards": ["standing_send_authority", "recipient_authorized", "per_recipient_budget_ok"], "actions": ["act_send_request"]},
            {"from_state": "REQUEST_DRAFTED", "event": "review_required", "to_state": "AWAIT_SEND_REVIEW", "guards": ["review_surface_available"]},
            {"from_state": "AWAIT_SEND_REVIEW", "event": "approved", "to_state": "SENT", "guards": ["approval_bound_to_draft_digest_and_case_version"], "actions": ["act_send_request"]},
            {"from_state": "AWAIT_SEND_REVIEW", "event": "rejected", "to_state": "CONSOLIDATE_MISSING", "guards": []},
            {"from_state": "SENT", "event": "effect_confirmed", "to_state": "WAIT_DOCUMENTS", "guards": ["send_effect_confirmed"]},
            {"from_state": "WAIT_DOCUMENTS", "event": "document_arrived", "to_state": "VALIDATE_DOCUMENTS", "guards": ["event_matches_case_key"]},
            {"from_state": "WAIT_DOCUMENTS", "event": "reminder_timer", "to_state": "CONSOLIDATE_MISSING", "guards": ["reminder_loop_under_max"]},
            {"from_state": "WAIT_DOCUMENTS", "event": "escalation_timer", "to_state": "ESCALATED", "guards": ["reminder_loop_exhausted"]},
            {"from_state": "VALIDATE_DOCUMENTS", "event": "valid", "to_state": "CONSOLIDATE_MISSING", "guards": ["document_matches_client_period", "not_duplicate"]},
            {"from_state": "VALIDATE_DOCUMENTS", "event": "invalid", "to_state": "CONSOLIDATE_MISSING", "guards": ["invalid_reason_recorded"]},
            {"from_state": "PREPARE_PACKAGE", "event": "package_ready", "to_state": "AWAIT_SIGNOFF", "guards": ["package_digest_recorded", "review_surface_available"]},
            {"from_state": "AWAIT_SIGNOFF", "event": "accepted", "to_state": "PACKAGE_ACCEPTED", "guards": ["signoff_bound_to_package_digest"]},
            {"from_state": "AWAIT_SIGNOFF", "event": "returned", "to_state": "CONSOLIDATE_MISSING", "guards": ["return_reason_recorded"]},
            {"from_state": "AWAIT_SIGNOFF", "event": "evidence_changed", "to_state": "PREPARE_PACKAGE", "guards": ["material_change_detected"]},
            {"from_state": "RESOLVE_CASE", "event": "cancel", "to_state": "CANCELLED", "guards": ["cancel_authorized"]},
            {"from_state": "WAIT_DOCUMENTS", "event": "cancel", "to_state": "CANCELLED", "guards": ["cancel_authorized"]},
        ],
        "actions": [
            {"action_id": "act_send_request", "operation_id": "google_workspace:gmail.messages.send", "effect_class": "external_message", "compensation_class": "irreversible", "retry_class": "provider_keyed", "requires_case_approval": False, "recipient_scope": "client_contacts", "template_class": "document_request_v1", "per_recipient_budget": 3}
        ],
        "durable_waits": ["WAIT_DOCUMENTS", "AWAIT_SEND_REVIEW", "AWAIT_SIGNOFF"],
        "timers": {"reminder_timer": 604800, "escalation_timer": 2592000},
        "bounded_loops": {"reminder_loop": 3},
        "completion_predicate": "review_package_accepted",
        "review_surfaces": ["gmail_draft", "plumb_companion_review"],
        "max_cost_per_case": money(300),
    }
    others = {
        "solution_spec": {
            "solution_id": "sol_doc_intake_v1",
            "tenant_id": tenant,
            "opportunity_ref": {"object_type": "OpportunitySpec", "id": "opp_doc_chase_01", "digest": digest({"id": "opp_doc_chase_01"})},
            "baseline_candidate_id": "cand_native_reminders",
            "candidates": [
                {"candidate_id": "cand_native_reminders", "solution_class": "native_configuration", "components": ["practice_mgmt:auto_reminders"], "joint_error_profile": "no consolidation across sources; duplicate chasing persists", "estimated_cost": money(0), "estimated_review_minutes_per_case": 12.0, "rejected_reason": "does not detect documents already present in Drive or QBO"},
                {"candidate_id": "cand_rules_plus_drafts", "solution_class": "general_model_workflow", "components": ["deterministic_checklist", "drive_folder_adapter", "qbo_cdc_collector", "drafted_consolidated_request"], "joint_error_profile": "wrong-client folder mapping is the dominant risk; mitigated by approved identities and review", "estimated_cost": money(120), "estimated_review_minutes_per_case": 4.0},
                {"candidate_id": "cand_trained_categorizer", "solution_class": "trained_component", "components": ["cand_rules_plus_drafts", "classical_categorizer"], "joint_error_profile": "adds categorization suggestions; not needed for the review-package deliverable", "estimated_cost": money(160), "estimated_review_minutes_per_case": 3.5, "rejected_reason": "deferred to learning-enabled variant; no posting authority in release 1"},
            ],
            "selected_candidate_id": "cand_rules_plus_drafts",
            "outcome_semantics": "review_package_accepted",
            "policy_decisions": ["reminder cadence 7 days, max 3 reminders per obligation epoch", "documents already present are never requested"],
            "decision_record": "Selected the rules-plus-drafts composition: it removes duplicate chasing (the evidenced friction) with low impact and no posting authority. Trained categorization is a separate gated branch.",
            "impact_class": "low",
            "experiment_evidence": [],
        },
        "opportunity_spec": {
            "opportunity_id": "opp_doc_chase_01",
            "tenant_id": tenant,
            "route": "friction",
            "objective": "Stop chasing clients twice for the same document and shorten review-package preparation",
            "population": "obligations where fulfillment_predicate = 'bank_statement_received' AND period >= 2026-01",
            "baseline": [{"name": "duplicate_requests_per_obligation", "unit": "count", "point": 0.31, "low": 0.24, "high": 0.38, "denominator": 412, "method": "email thread and call log backfill, 12 months"}],
            "hypothesis": "Requests are duplicated because document presence in Drive and the ledger is not visible to the person sending reminders",
            "suspected_bottleneck": "no shared view of document presence across Drive, email and the ledger",
            "evidence_packet_ref": {"object_type": "EvidencePacket", "id": "pkt_doc_chase_evidence", "digest": arts["pkt_doc_chase_evidence"]["digest"]},
            "evidence_coverage": 0.83,
            "policy_dependencies": ["authoritative engagement checklist owner", "reminder cadence policy"],
            "known_exceptions": ["a second reminder by a partner is sometimes an intentional escalation"],
            "expected_intervention": "consolidated missing-item request drafted from reconciled evidence, one owner per obligation",
            "credible_alternatives": ["practice management auto-reminders only", "do nothing"],
            "expected_benefit": [{"name": "duplicate_requests_per_obligation", "unit": "count", "point": 0.05, "low": 0.0, "high": 0.12, "denominator": 412, "method": "counterfactual on backfill; prospective cohort confirms"}],
            "expected_downside": "a wrong client/period mapping sends a request about the wrong period; mitigated by approved identities and send review",
            "review_burden": {"name": "review_minutes_per_case", "unit": "minutes", "point": 4.0, "low": 2.0, "high": 8.0, "denominator": 0, "method": "estimate, to be measured prospectively"},
            "falsifiers": ["duplicate requests persist after shared presence view", "partners confirm second reminders are intentional controls"],
            "hard_constraints": ["no ledger posting", "no commitments in client messages"],
            "measurement_plan": "prospective: duplicate requests per obligation and review minutes per case over 2 periods, cohort by client",
            "status": "objective_accepted",
            "objective_accepted_by": "prn_owner_01",
        },
        "approval_release": {
            "approval_id": "apr_release_doc_intake_v1",
            "tenant_id": tenant,
            "kind": "release_activation",
            "bound_digests": [digest({"release_id": "rel_doc_intake_v1"})],
            "prerequisite_state": {"release_state": "VERIFIED"},
            "scope": {"environments": ["canary", "production"]},
            "approver_principal_id": "prn_owner_01",
            "policy_version": "pol-2026-10",
            "nonce": "nonce_8f1c2d",
            "requested_at": T,
            "decided_at": T,
            "expires_at": TEXP,
            "decision": "granted",
            "status": "GRANTED",
        },
        "action_intent": {
            "intent_id": "int_send_req_0142_2026_08",
            "tenant_id": tenant,
            "case_ref": {"object_type": "Case", "id": "case_0142_2026_08"},
            "obligation_ref": {"object_type": "Obligation", "id": "obl_0142_2026_08_bank_stmt"},
            "obligation_epoch": 1,
            "operation_id": "google_workspace:gmail.messages.send",
            "provider": "google_workspace",
            "account_ref": "gws-acct-7F2A",
            "effect_slot": "tnt_barlowkim|case_0142_2026_08|1|gmail.messages.send|contact_maria",
            "logical_action_id": "act_" + digest({"slot": "tnt_barlowkim|case_0142_2026_08|1|gmail.messages.send|contact_maria", "n": 1})[7:27],
            "payload_digest": digest({"to": "maria@pinestreetbakery.example", "template_class": "document_request_v1", "items": ["bank_statement_2026_08"]}),
            "payload_ref": "obj://tnt_barlowkim/payloads/int_send_req_0142_2026_08.json",
            "expected_state_versions": {"case": 7, "obligation": 2},
            "authority": {"envelope_id": "env_barlowkim_v3", "envelope_version": "3", "release_id": "rel_doc_intake_v1", "grant_ids": "grant_gmail_ops"},
            "cost_reservation_id": "res_01HZ",
            "retry_class": "provider_keyed",
            "compensation_class": "irreversible",
            "effect_class": "external_message",
        },
        "release_manifest": {
            "release_id": "rel_doc_intake_v1",
            "tenant_id": tenant,
            "components": {
                "workflow": {"object_type": "WorkflowSpec", "id": "wf_barlowkim_doc_intake_v1", "digest": digest({"id": "wf_barlowkim_doc_intake_v1"})},
                "connector_drive": {"object_type": "IntegrationSpec", "id": "int_drive_folder_map_v1", "digest": digest({"id": "int_drive_folder_map_v1"})},
                "collector_docs": {"object_type": "CollectionSpec", "id": "col_docs_v1", "digest": digest({"id": "col_docs_v1"})},
                "collector_qbo": {"object_type": "CollectionSpec", "id": "col_qbo_v1", "digest": digest({"id": "col_qbo_v1"})},
                "rules": {"object_type": "RuleSet", "id": "rules_checklist_v1", "digest": digest({"id": "rules_checklist_v1"})},
                "prompts": {"object_type": "PromptSet", "id": "prompts_request_v1", "digest": digest({"id": "prompts_request_v1"})},
                "policies": {"object_type": "PolicySnapshot", "id": "pol-2026-10", "digest": digest({"id": "pol-2026-10"})},
                "infra": {"object_type": "InfrastructurePlan", "id": "infra_doc_intake_v1", "digest": digest({"id": "infra_doc_intake_v1"})},
            },
            "required_checks": ["chk_adapter_contract_v1", "chk_collector_live_event_v1", "chk_backfill_reconciliation_v1", "chk_workflow_scenarios_v1", "chk_release_manifest_v1", "chk_gateway_adversarial_v1"],
            "schema_versions": {"case": "1.0", "event": "1.0"},
            "policy_version": "pol-2026-10",
            "rollout": {"shadow_min_opportunities": 40, "shadow_divergence_max": 0.03, "canary_clients": 5, "canary_min_opportunities": 25},
            "status": "CANDIDATE",
        },
        "collection_spec": {
            "collection_id": "col_qbo_v1",
            "tenant_id": tenant,
            "purpose": "operation",
            "objective_ref": {"object_type": "OpportunitySpec", "id": "opp_doc_chase_01"},
            "source_grant_ids": ["grant_qbo_main"],
            "integration_ref": {"object_type": "IntegrationSpec", "id": "int_qbo_v1"},
            "account_scope": ["qbo-realm-4011"],
            "selected_fields": ["Id", "SyncToken", "TxnDate", "TotalAmt", "AccountRef", "EntityRef", "MetaData.LastUpdatedTime", "AttachableRef"],
            "semantic_schema": [{"name": "txn_amount", "semantic_type": "money", "currency": "USD", "scope": "qbo-realm-4011"}, {"name": "txn_date", "semantic_type": "timestamp", "tz": "America/New_York", "scope": "qbo-realm-4011"}],
            "join_keys": ["Id", "EntityRef.value", "TxnDate.period"],
            "update_mechanism": "change_capture",
            "overlap_window_s": 7200,
            "backfill_from": "2024-01-01T00:00:00+00:00",
            "watermark_field": "MetaData.LastUpdatedTime",
            "storage_destination": "storage:tenant:barlowkim/collections/qbo_purchases",
            "transformation_version": "xf-qbo-purchase-1.2",
            "quality_checks": [{"name": "count_reconciliation", "rule": "abs(local_count - source_count)/source_count <= 0.005 per month", "on_fail": "block"}, {"name": "cdc_window", "rule": "poll interval <= 20 days (provider look-back is 30)", "on_fail": "degrade"}],
            "retention_days": 730,
            "deletion_behaviour": "tombstone_and_cascade",
            "downstream": ["evidence.facts", "dataset.categorization"],
            "budget_monthly": money(2500),
            "completeness_claim": "bounded",
        },
    }
    scenario = {"plan": plan, "context": ctx, "workflow": workflow, **others}
    return scenario, arts


def rfq() -> dict:
    tenant = "tnt_norbridge_mfg"
    grants = {
        "grant_erp_rfq": grant(tenant, "grant_erp_rfq", "netsuite", "ns-acct-55120", ["discovery", "implementation", "operation", "evaluation"]),
        "grant_mail_sales": grant(tenant, "grant_mail_sales", "microsoft_365", "m365-tenant-9ab", ["discovery", "implementation", "operation"]),
    }
    env = envelope(tenant, "env_norbridge_v1", list(grants), extra_dest=["provider:netsuite:ns-acct-55120*"])
    arts = artifacts(tenant, {"sol_rfq_prep_v1": {"kind": "SolutionSpec", "impact_class": "medium"}, "env_norbridge_v1": {"kind": "AutonomyEnvelope"}, "inv_norbridge_2026_10": {"kind": "EnvironmentInventory"}})
    caps = registry(tenant, {
        "netsuite:items.search": ("ns-acct-55120", "account_verified"),
        "netsuite:pricing.get": ("ns-acct-55120", "account_verified"),
        "microsoft_365:mail.list": ("m365-tenant-9ab", "account_verified"),
        "plumb:collector.deploy": ("plumb", "production_observed"),
        "plumb:workflow.compile": ("plumb", "production_observed"),
        "plumb:verifier.request": ("plumb", "production_observed"),
        "plumb:release.create": ("plumb", "production_observed"),
        "plumb:agent.harness": ("plumb", "sandbox_tested"),
    })
    qty_port = {"name": "quantities", "semantic_type": "quantity", "unit": "each", "scope": "ns-acct-55120"}
    price_port = {"name": "unit_prices", "semantic_type": "money", "currency": "USD", "scope": "ns-acct-55120", "freshness_max_s": 86400}
    plan = {
        "plan_id": "plan_norbridge_rfq_prep_v1",
        "tenant_id": tenant,
        "solution_ref": ref("SolutionSpec", "sol_rfq_prep_v1", arts),
        "envelope_ref": ref("AutonomyEnvelope", "env_norbridge_v1", arts),
        "total_budget_max": money(40000),
        "steps": [
            step("step_probe_erp", "probe_source", inputs=[ref("EnvironmentInventory", "inv_norbridge_2026_10", arts)], required_capabilities=["netsuite:items.search", "netsuite:pricing.get"], min_capability_level="account_verified", purposes_used=["discovery", "implementation"]),
            step("step_profile_pricing", "profile_source", depends_on=["step_probe_erp"], output_ports=[qty_port, price_port], required_capabilities=["netsuite:pricing.get"], min_capability_level="account_verified"),
            step("step_adapter_sku_units", "generate_adapter", depends_on=["step_profile_pricing"], input_ports=[qty_port, price_port], required_capabilities=["plumb:agent.harness"], budget_max=money(8000), notes="unit/SKU normalization: cases vs eaches, price list freshness"),
            step("step_collector_rfq_mail", "deploy_collector", depends_on=["step_probe_erp"], required_capabilities=["plumb:collector.deploy", "microsoft_365:mail.list"], min_capability_level="account_verified", effect_class="config_change", compensation_class="native_undo", destinations=["storage:tenant:norbridge"], produces_release_artifact=True, verification=[{"check_id": "chk_collector_live_event_v1", "criteria_version": "1"}]),
            step("step_compile_workflow", "compile_workflow", depends_on=["step_adapter_sku_units", "step_collector_rfq_mail"], required_capabilities=["plumb:workflow.compile"], produces_release_artifact=True, verification=[{"check_id": "chk_workflow_scenarios_v1", "criteria_version": "1", "data_role": "protected_acceptance"}]),
            step("step_request_verification", "request_verification", depends_on=["step_compile_workflow"], required_capabilities=["plumb:verifier.request"], min_capability_level="production_observed"),
            step("step_create_release", "create_release", depends_on=["step_request_verification"], required_capabilities=["plumb:release.create"], produces_release_artifact=True, verification=[{"check_id": "chk_release_manifest_v1", "criteria_version": "1"}]),
        ],
    }
    workflow = {
        "workflow_id": "wf_norbridge_rfq_prep_v1",
        "tenant_id": tenant,
        "case_key_fields": ["rfq_id"],
        "triggers": ["event:rfq.received"],
        "input_ports": [{"name": "rfq_lines", "semantic_type": "record_set", "scope": "tnt_norbridge_mfg"}],
        "source_freshness": {"netsuite": 86400},
        "states": ["PARSE_RFQ", "NORMALIZE_LINES", "PRICE_LINES", "DRAFT_QUOTE", "AWAIT_COMMERCIAL_APPROVAL", "QUOTE_READY", "REJECTED", "CANCELLED"],
        "initial_state": "PARSE_RFQ",
        "terminal_states": ["QUOTE_READY", "REJECTED", "CANCELLED"],
        "transitions": [
            {"from_state": "PARSE_RFQ", "event": "parsed", "to_state": "NORMALIZE_LINES", "guards": ["customer_resolved"]},
            {"from_state": "NORMALIZE_LINES", "event": "normalized", "to_state": "PRICE_LINES", "guards": ["units_resolved_or_flagged"]},
            {"from_state": "PRICE_LINES", "event": "priced", "to_state": "DRAFT_QUOTE", "guards": ["price_list_fresh_within_24h"]},
            {"from_state": "DRAFT_QUOTE", "event": "drafted", "to_state": "AWAIT_COMMERCIAL_APPROVAL", "guards": ["review_surface_available"]},
            {"from_state": "AWAIT_COMMERCIAL_APPROVAL", "event": "approved", "to_state": "QUOTE_READY", "guards": ["approval_bound_to_quote_digest"]},
            {"from_state": "AWAIT_COMMERCIAL_APPROVAL", "event": "rejected", "to_state": "REJECTED", "guards": []},
            {"from_state": "PARSE_RFQ", "event": "cancel", "to_state": "CANCELLED", "guards": ["cancel_authorized"]},
        ],
        "actions": [],
        "durable_waits": ["AWAIT_COMMERCIAL_APPROVAL"],
        "timers": {},
        "bounded_loops": {},
        "completion_predicate": "quote_draft_approved",
        "review_surfaces": ["plumb_companion_review"],
        "max_cost_per_case": money(150),
    }
    return {"plan": plan, "context": {"tenant_id": tenant, "envelope": env, "grants": grants, "artifacts": arts, "capabilities": caps, "approval_obligations": []}, "workflow": workflow}


def laundry() -> dict:
    tenant = "tnt_freshpress"
    grants = {"grant_orders": grant(tenant, "grant_orders", "cleancloud", "cc-store-group-77", ["discovery", "implementation", "operation", "evaluation"]), "grant_fleet": grant(tenant, "grant_fleet", "samsara", "sam-org-310", ["discovery", "implementation", "operation", "evaluation"])}
    env = envelope(tenant, "env_freshpress_v1", list(grants), extra_dest=["provider:cleancloud:cc-store-group-77*"])
    arts = artifacts(tenant, {"sol_route_prep_v1": {"kind": "SolutionSpec", "impact_class": "low"}, "env_freshpress_v1": {"kind": "AutonomyEnvelope"}, "inv_freshpress_2026_10": {"kind": "EnvironmentInventory"}})
    caps = registry(tenant, {
        "cleancloud:orders.list": ("cc-store-group-77", "account_verified"),
        "samsara:vehicles.list": ("sam-org-310", "account_verified"),
        "samsara:trips.list": ("sam-org-310", "sandbox_tested"),
        "plumb:solver.vrp": ("plumb", "production_observed"),
        "plumb:collector.deploy": ("plumb", "production_observed"),
        "plumb:workflow.compile": ("plumb", "production_observed"),
        "plumb:verifier.request": ("plumb", "production_observed"),
        "plumb:release.create": ("plumb", "production_observed"),
    })
    dur_port = {"name": "stop_durations", "semantic_type": "duration", "unit": "s", "scope": "sam-org-310"}
    plan = {
        "plan_id": "plan_freshpress_route_prep_v1",
        "tenant_id": tenant,
        "solution_ref": ref("SolutionSpec", "sol_route_prep_v1", arts),
        "envelope_ref": ref("AutonomyEnvelope", "env_freshpress_v1", arts),
        "total_budget_max": money(30000),
        "steps": [
            step("step_probe_orders", "probe_source", inputs=[ref("EnvironmentInventory", "inv_freshpress_2026_10", arts)], required_capabilities=["cleancloud:orders.list"], min_capability_level="account_verified", purposes_used=["discovery", "implementation"]),
            step("step_collector_trips", "deploy_collector", depends_on=["step_probe_orders"], output_ports=[dur_port], required_capabilities=["plumb:collector.deploy", "samsara:trips.list"], effect_class="config_change", compensation_class="native_undo", destinations=["storage:tenant:freshpress"], produces_release_artifact=True, verification=[{"check_id": "chk_collector_live_event_v1", "criteria_version": "1"}]),
            step("step_solver_config", "run_experiment", depends_on=["step_collector_trips"], input_ports=[dur_port], purposes_used=["evaluation"], required_capabilities=["plumb:solver.vrp"], budget_max=money(4000), notes="constraint satisfaction on last 8 weeks of actual stops; hard constraints: vehicle capacity, store windows, driver shifts"),
            step("step_compile_workflow", "compile_workflow", depends_on=["step_solver_config"], required_capabilities=["plumb:workflow.compile"], produces_release_artifact=True, verification=[{"check_id": "chk_workflow_scenarios_v1", "criteria_version": "1", "data_role": "protected_acceptance"}]),
            step("step_request_verification", "request_verification", depends_on=["step_compile_workflow"], required_capabilities=["plumb:verifier.request"], min_capability_level="production_observed"),
            step("step_create_release", "create_release", depends_on=["step_request_verification"], required_capabilities=["plumb:release.create"], produces_release_artifact=True, verification=[{"check_id": "chk_release_manifest_v1", "criteria_version": "1"}]),
        ],
    }
    workflow = {
        "workflow_id": "wf_freshpress_route_prep_v1",
        "tenant_id": tenant,
        "case_key_fields": ["service_date", "depot_id"],
        "triggers": ["schedule:daily_cutoff", "event:order.changed"],
        "input_ports": [{"name": "orders", "semantic_type": "record_set", "scope": "tnt_freshpress"}],
        "source_freshness": {"cleancloud": 600},
        "states": ["COLLECT_ORDERS", "SOLVE", "PLAN_DRAFTED", "AWAIT_PUBLISH_APPROVAL", "PUBLISHED", "RESOLVE_INFEASIBLE", "CANCELLED"],
        "initial_state": "COLLECT_ORDERS",
        "terminal_states": ["PUBLISHED", "CANCELLED"],
        "transitions": [
            {"from_state": "COLLECT_ORDERS", "event": "cutoff", "to_state": "SOLVE", "guards": ["orders_fresh"]},
            {"from_state": "SOLVE", "event": "solved", "to_state": "PLAN_DRAFTED", "guards": ["hard_constraints_satisfied"]},
            {"from_state": "SOLVE", "event": "infeasible", "to_state": "RESOLVE_INFEASIBLE", "guards": []},
            {"from_state": "RESOLVE_INFEASIBLE", "event": "constraints_relaxed_by_human", "to_state": "SOLVE", "guards": ["relaxation_authorized", "solve_loop_under_max"]},
            {"from_state": "PLAN_DRAFTED", "event": "review", "to_state": "AWAIT_PUBLISH_APPROVAL", "guards": ["review_surface_available"]},
            {"from_state": "AWAIT_PUBLISH_APPROVAL", "event": "approved", "to_state": "PUBLISHED", "guards": ["approval_bound_to_plan_digest"], "actions": ["act_publish_routes"]},
            {"from_state": "AWAIT_PUBLISH_APPROVAL", "event": "order_changed", "to_state": "SOLVE", "guards": ["solve_loop_under_max"]},
            {"from_state": "COLLECT_ORDERS", "event": "cancel", "to_state": "CANCELLED", "guards": ["cancel_authorized"]},
        ],
        "actions": [{"action_id": "act_publish_routes", "operation_id": "cleancloud:routes.publish", "effect_class": "external_record_write", "compensation_class": "native_undo", "retry_class": "provider_keyed", "requires_case_approval": True}],
        "durable_waits": ["AWAIT_PUBLISH_APPROVAL", "RESOLVE_INFEASIBLE"],
        "timers": {},
        "bounded_loops": {"solve_loop": 5},
        "completion_predicate": "routes_published",
        "review_surfaces": ["plumb_companion_review"],
        "max_cost_per_case": money(200),
    }
    return {"plan": plan, "context": {"tenant_id": tenant, "envelope": env, "grants": grants, "artifacts": arts, "capabilities": caps, "approval_obligations": ["step_collector_trips"]}, "workflow": workflow}


def failure_cases(acc: dict) -> dict[str, tuple[dict, list[str]]]:
    base = acc["plan"]
    cases: dict[str, tuple[dict, list[str]]] = {}

    def mut(name: str, fn, expected: list[str]):
        p = copy.deepcopy(base)
        fn(p)
        cases[name] = (p, expected)

    def by_id(p, sid):
        return next(s for s in p["steps"] if s["step_id"] == sid)

    mut("plan_cycle", lambda p: by_id(p, "step_probe_qbo")["depends_on"].append("step_reconcile_qbo"), ["E_GRAPH_CYCLE"])
    mut("plan_missing_ref", lambda p: by_id(p, "step_probe_gmail")["inputs"].append({"object_type": "EvidencePacket", "id": "pkt_does_not_exist", "digest": "sha256:" + "0" * 64}), ["E_REF_UNRESOLVED"])
    mut("plan_stale_artifact", lambda p: by_id(p, "step_discover_labels")["inputs"][0].update({"digest": "sha256:" + "a" * 64}), ["E_ARTIFACT_IDENTITY"])
    mut("plan_alias_unresolved", lambda p: by_id(p, "step_discover_labels")["inputs"][0].update({"digest": None, "alias": "latest"}), ["E_ARTIFACT_IDENTITY"])
    mut("plan_unit_mismatch", lambda p: by_id(p, "step_collector_qbo")["input_ports"].__setitem__(0, {"name": "qbo_records", "semantic_type": "record_set", "scope": "qbo-realm-9999"}), ["E_TYPE_MISMATCH"])
    mut("plan_currency_mismatch", lambda p: by_id(p, "step_discover_labels")["input_ports"].append({"name": "txn_amounts", "semantic_type": "money", "currency": "EUR", "scope": "qbo-realm-4011"}), ["E_TYPE_MISMATCH"])
    mut("plan_unsupported_step_type", lambda p: by_id(p, "step_generate_tests").__setitem__("type", "do_whatever_is_needed"), ["E_SYNTAX"])
    mut("plan_hidden_unbounded_loop", lambda p: p["steps"].append(step("step_free_agent", "agent_loop", depends_on=["step_create_release"], required_capabilities=["plumb:agent.harness"])), ["E_SYNTAX"])
    mut("plan_purpose_denied", lambda p: by_id(p, "step_profile_qbo").__setitem__("purposes_used", ["export"]), ["E_AUTHZ_PURPOSE"])
    mut("plan_processor_outside_envelope", lambda p: by_id(p, "step_experiment").__setitem__("processors_used", ["plumb:control", "unknown-vendor:api"]), ["E_AUTHZ_PROCESSOR"])
    mut("plan_destination_outside_envelope", lambda p: by_id(p, "step_collector_docs").__setitem__("destinations", ["storage:external:dropbox"]), ["E_AUTHZ_DESTINATION"])
    mut("plan_effect_class_outside_envelope", lambda p: by_id(p, "step_apply_infra").__setitem__("effect_class", "external_record_write"), ["E_AUTHZ_EFFECT_CLASS"])
    mut("plan_over_budget", lambda p: by_id(p, "step_experiment").__setitem__("budget_max", money(9000000)), ["E_BUDGET_EXCEEDED"])
    mut("plan_budget_over_envelope", lambda p: p.__setitem__("total_budget_max", money(99999999)), ["E_BUDGET_EXCEEDED"])
    mut("plan_effect_without_compensation", lambda p: by_id(p, "step_collector_docs").__setitem__("compensation_class", "not_needed"), ["E_EFFECT_NO_COMPENSATION"])
    mut("plan_irreversible_without_approval", lambda p: by_id(p, "step_apply_infra").__setitem__("compensation_class", "irreversible"), ["E_EFFECT_IRREVERSIBLE_UNAPPROVED"])
    mut("plan_payment_in_build", lambda p: by_id(p, "step_apply_infra").__setitem__("effect_class", "external_payment"), ["E_EFFECT_PAYMENT_IN_BUILD"])
    mut("plan_missing_verifier", lambda p: by_id(p, "step_compile_workflow").__setitem__("verification", []), ["E_VERIFIER_COVERAGE"])
    mut("plan_verifier_only_training_role", lambda p: by_id(p, "step_compile_workflow").__setitem__("verification", [{"check_id": "chk_x", "criteria_version": "1", "data_role": "training"}]), ["E_VERIFIER_COVERAGE"])
    mut("plan_capability_level_too_low", lambda p: by_id(p, "step_probe_qbo")["required_capabilities"].append("quickbooks_online:attachable.create"), ["E_CAPABILITY_UNAVAILABLE"])
    mut("plan_capability_unknown", lambda p: by_id(p, "step_probe_qbo")["required_capabilities"].append("quickbooks_online:bankfeed.review.read"), ["E_CAPABILITY_UNAVAILABLE"])
    mut("plan_release_schema_change_without_migration", lambda p: p.__setitem__("release_schema_version", "1.1"), ["E_RELEASE_COMPAT"])
    mut("plan_cross_tenant_reference", lambda p: by_id(p, "step_probe_gmail")["inputs"].append({"object_type": "EvidencePacket", "id": "pkt_other_tenant", "digest": "sha256:" + "b" * 64}), ["E_AUTHZ_CROSS_TENANT"])
    mut("plan_dangling_dependency", lambda p: by_id(p, "step_probe_gmail")["depends_on"].append("step_ghost"), ["E_GRAPH_DANGLING"])
    return cases


def main() -> None:
    acc, acc_arts = accounting()
    out = FX / "accounting"
    write(out / "build_plan.json", acc["plan"], "BuildPlan")
    write(out / "validation_context.json", acc["context"])
    write(out / "workflow_spec.json", acc["workflow"], "WorkflowSpec")
    write(out / "solution_spec.json", acc["solution_spec"], "SolutionSpec")
    write(out / "opportunity_spec.json", acc["opportunity_spec"], "OpportunitySpec")
    write(out / "approval_release_activation.json", acc["approval_release"], "Approval")
    write(out / "action_intent_send_request.json", acc["action_intent"], "ActionIntent")
    write(out / "release_manifest.json", acc["release_manifest"], "ReleaseManifest")
    write(out / "collection_spec_qbo.json", acc["collection_spec"], "CollectionSpec")
    write(out / "autonomy_envelope.json", acc["context"]["envelope"], "AutonomyEnvelope")
    for gid, g in acc["context"]["grants"].items():
        write(out / f"source_grant_{gid}.json", g, "SourceGrant")

    r = rfq()
    write(FX / "industrial-rfq" / "build_plan.json", r["plan"], "BuildPlan")
    write(FX / "industrial-rfq" / "validation_context.json", r["context"])
    write(FX / "industrial-rfq" / "workflow_spec.json", r["workflow"], "WorkflowSpec")

    l = laundry()
    write(FX / "laundry-routing" / "build_plan.json", l["plan"], "BuildPlan")
    write(FX / "laundry-routing" / "validation_context.json", l["context"])
    write(FX / "laundry-routing" / "workflow_spec.json", l["workflow"], "WorkflowSpec")

    cases = failure_cases(acc)
    expected = {}
    for name, (p, codes) in cases.items():
        write(FX / "failure-cases" / f"{name}.json", p)
        expected[name] = codes
    # non-plan failure fixtures (schema level)
    other = {
        "approval_self_reference": {"model": "Approval", "obj": {**acc["approval_release"], "bound_digests": ["apr_release_doc_intake_v1"]}},
        "workflow_terminal_with_outgoing": {"model": "WorkflowSpec", "obj": {**acc["workflow"], "transitions": acc["workflow"]["transitions"] + [{"from_state": "PACKAGE_ACCEPTED", "event": "x", "to_state": "CANCELLED"}]}},
        "port_money_without_currency": {"model": "CollectionSpec", "obj": {**acc["collection_spec"], "semantic_schema": [{"name": "amt", "semantic_type": "money"}]}},
        "fact_confirmed_with_residual_confidence": {"model": "Fact", "obj": {"fact_id": "fct_x", "tenant_id": "tnt_barlowkim", "subject": {"object_type": "Close", "id": "obj_close_1207"}, "predicate": "chased_times", "value": 4, "status": "confirmed", "evidence": [{"object_type": "EvidenceEvent", "id": "evt_1"}], "derivation_version": "d1", "confidence": 0.7}},
        "release_component_without_digest": {"model": "ReleaseManifest", "obj": {**acc["release_manifest"], "components": {**acc["release_manifest"]["components"], "rules": {"object_type": "RuleSet", "id": "rules_checklist_v1"}}}},
    }
    for name, spec in other.items():
        write(FX / "failure-cases" / f"{name}.json", spec["obj"])
        expected[name] = ["E_SYNTAX:" + spec["model"]]
    write(FX / "failure-cases" / "expected.json", expected)
    print(f"wrote fixtures; failure cases: {len(expected)}")


if __name__ == "__main__":
    main()
