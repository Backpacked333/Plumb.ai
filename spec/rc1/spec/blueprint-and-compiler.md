# Blueprint language, typed intermediate representation and compiler

The normative schema is the Pydantic model set (DC-001); JSON Schema is generated; the human-readable Blueprint is a rendered view. Execution is a trusted interpreter over validated primitives with isolated activities for generated adapter code (ADR-022).

## 1. Source of truth and precedence

contracts/canonical-models (models) > contracts/generated-json-schema > contracts/openapi.yaml > fixtures > prose. A contradiction between any two is a defect; tests/contract enforces the first three.

## 2. Execution architecture and what is statically verified

The build runtime interprets BuildStep records; each step type maps to a certified primitive with fixed semantics. Generated code exists only inside generate_adapter steps and runs as an isolated activity with its own contract tests and verifier attestation. Static validation establishes: closed vocabulary, graph finiteness, type compatibility, authorization and budget bounds, effect declarations, verifier coverage, release compatibility. It does not establish that generated code is safe or semantically correct; that claim belongs to the Verifier (SR-049).

## 3. Step types

| Type | Required capabilities | Effect class | Verification obligation |
| --- | --- | --- | --- |
| probe_source, profile_source | source_read on the account | none | none (results are inventory evidence) |
| generate_adapter, test_adapter | agent harness, source_read | none | adapter contract kit |
| configure_integration | integration_admin | config_change | probe on the account |
| deploy_collector, backfill, reconcile_collector | integration_admin, source_subscribe | config_change | live-event attestation, reconciliation attestation |
| discover_labels, build_dataset, audit_labels | dataset build | none | leakage and label audit (protected role) |
| run_experiment, submit_training, evaluate_candidate | model inference or training | none | held-out evaluation |
| compile_workflow, generate_tests | workflow compile | none | protected workflow scenarios |
| request_verification | verifier request | none | n/a |
| preview_infra, apply_infra | infra_admin | infra_change (apply) | post-apply verification |
| create_release | release create | none | manifest attestation |
| agent_loop | agent harness | none | bounded by max_iterations and timeout; outputs are proposals |

Ports: name, semantic_type, unit, currency, tz, scope, nullable, freshness_max_s, purpose restrictions (SR-042). Semantic types in release 1: money, quantity, duration, timestamp, identifier, record_set, document, model_artifact, text.

## 4. Validation passes and errors

| Pass | Error codes | Rejected fixture |
| --- | --- | --- |
| P1 syntax | E_SYNTAX | plan_unsupported_step_type, plan_hidden_unbounded_loop |
| P2 references | E_REF_UNRESOLVED | plan_missing_ref |
| P3 artifact identity | E_ARTIFACT_IDENTITY | plan_stale_artifact, plan_alias_unresolved |
| P4 graph | E_GRAPH_CYCLE, E_GRAPH_DANGLING, E_GRAPH_DUPLICATE_ID | plan_cycle, plan_dangling_dependency |
| P5 types | E_TYPE_MISMATCH, E_TYPE_UNSOURCED | plan_unit_mismatch, plan_currency_mismatch |
| P6 capabilities | E_CAPABILITY_UNAVAILABLE | plan_capability_unknown, plan_capability_level_too_low |
| P7 authorization | E_AUTHZ_PURPOSE, E_AUTHZ_PROCESSOR, E_AUTHZ_DESTINATION, E_AUTHZ_EFFECT_CLASS, E_AUTHZ_CROSS_TENANT, E_AUTHZ_ENVELOPE, E_TENANT_MISMATCH | plan_purpose_denied, plan_processor_outside_envelope, plan_destination_outside_envelope, plan_effect_class_outside_envelope, plan_cross_tenant_reference |
| P8 budgets | E_BUDGET_EXCEEDED, E_BUDGET_CURRENCY | plan_over_budget, plan_budget_over_envelope |
| P9 effects | E_EFFECT_NO_COMPENSATION, E_EFFECT_IRREVERSIBLE_UNAPPROVED, E_EFFECT_PAYMENT_IN_BUILD | plan_effect_without_compensation, plan_irreversible_without_approval, plan_payment_in_build |
| P10 verifier coverage | E_VERIFIER_COVERAGE | plan_missing_verifier, plan_verifier_only_training_role |
| P11 release compatibility | E_RELEASE_COMPAT | plan_release_schema_change_without_migration |
| P12 loops | E_UNBOUNDED_LOOP | (also caught by P1) |

Accepted fixtures: fixtures/accounting, fixtures/industrial-rfq, fixtures/laundry-routing. The validator is reference/bounded-plan-validator/validator.py.

## 5. Business workflow versus build graph

The BuildPlan is finite. The WorkflowSpec carries branching, durable waits, joins, bounded loops (bounded_loops with a maximum), timers, cancellation and re-entry. An agent_loop inside a build is bounded by max_iterations and timeout and can only propose artifacts; hidden recursion is impossible because a step cannot create steps.

## 6. Worked compilation trace (fixtures/accounting)

1. OpportunitySpec opp_doc_chase_01 (route friction, objective accepted by prn_owner_01).
2. SolutionSpec sol_doc_intake_v1 selects cand_rules_plus_drafts, impact low, outcome review_package_accepted.
3. BuildPlan plan_barlowkim_doc_intake_v1: 18 steps from probes through release, budget $600, envelope env_barlowkim_v3 (version 3, build cap $2,500). Validation: no errors.
4. Generated artifacts: int_drive_folder_map_v1 (rung 3 adapter, the nontrivial adaptation), col_docs_v1 and col_qbo_v1 (CollectionSpecs), ds_categorization (built but not used by release 1's workflow), wf_barlowkim_doc_intake_v1 (WorkflowSpec, 13 states, one external action act_send_request with per-recipient budget 3).
5. Evaluation: protected scenarios chk_workflow_scenarios_v1; collector live-event attestation chk_collector_live_event_v1; adapter kit chk_adapter_contract_v1; backfill reconciliation chk_backfill_reconciliation_v1; gateway adversarial chk_gateway_adversarial_v1.
6. ReleaseManifest rel_doc_intake_v1 composes the eight component digests and six required checks; activation does not need a release approval (impact low ≤ envelope ceiling low) but the fixture includes one to show the binding.

## 7. Invalidation rules

A change to any input artifact, generated code, policy snapshot, configuration, model version or acceptance criteria produces a new digest; attestations bound to the old digest are invalidated; approvals bound to the old digest move to INVALIDATED; the ReleaseManifest must be recomposed. Canonicalization and detached approvals are DC-003.

## 8. Extension path

New primitives are added by a platform engineer with: a StepType enum value, an interpreter implementation, a capability kind, a verification obligation, accepted and rejected fixtures and a kit test. Unknown step types never degrade to free-form instructions (SR-040).
