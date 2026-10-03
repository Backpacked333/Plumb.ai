# Reference package design contract

This document fixes the layout, naming and inter-module interfaces of the Plumb
reference package so that modules written independently fit together. It is
derived from the normative specification (`spec/` — v0.2, October 2, 2026).
Where this document and the specification disagree, the specification wins.

The package is a **reference implementation of selected controls**. It never
connects to a customer system, calls a model, trains weights or provisions
infrastructure (spec section 28, Appendix C).

## 1. Layout and file ownership

```
plumb/
  __init__.py
  contracts/
    __init__.py            exports TOP_LEVEL_CONTRACTS (17) and SUPPORTING_CONTRACTS
    common.py              shared primitives (DONE — do not change signatures; add only)
    envelope.py            AutonomyEnvelope
    capability.py          CapabilityRecord
    inventory.py           EnvironmentInventory
    evidence.py            EvidencePacket (+ EvidenceEvent, DerivedFact, ObjectResolution)
    opportunity.py         OpportunitySpec
    build_plan.py          BuildPlan (+ BuildStep, StepInput, StepOutput, VerificationObligation)
    integration.py         IntegrationSpec
    collection.py          CollectionSpec
    dataset.py             DatasetManifest (+ DatasetRow, SplitRule)
    training.py            TrainingSpec
    workflow.py            WorkflowSpec
    evaluation.py          EvaluationReport
    infrastructure.py      InfrastructurePlan
    release.py             ReleaseManifest
    effect.py              ActionIntent (+ EffectSlot, ActionReceipt)
    approval.py            ApprovalRecord
    verification.py        VerificationAttestation
    api.py                 JobEnvelope, ErrorEnvelope, EventEnvelope (supporting)
    protocol.py            AgentTask, StepResult (supporting; Appendix A)
  registry/
    __init__.py
    registry.py            load_registry(), CapabilityRegistry (lookups)
    capability_registry.json
  checker/
    __init__.py
    findings.py            Finding, CheckReport
    plan_checker.py        check_plan(plan, envelope, registry) -> CheckReport
    dataset_checker.py     check_dataset(manifest) -> CheckReport
    approval_checker.py    check_approval(approval, *, subject_digest, tenant_id, policy_version, case_version=None, now) -> CheckReport
    release_checker.py     check_release(manifest, attestations, approvals, *, now, current_policy_version) -> CheckReport
    cli.py                 python -m plumb.checker.cli plan <plan.json> <envelope.json>
  ledger/
    __init__.py
    effect_ledger.py       EffectLedger (SQLite)
  statemachines/
    __init__.py
    machines.py            StateMachine per aggregate, transition() with guards + reason
  schemas_tool/
    __init__.py
    generate.py            python -m plumb.schemas_tool.generate  -> schemas/*.json (17) + schemas/supporting/*.json
schemas/                   generated JSON Schemas (committed; test asserts they match models)
api/
  openapi.yaml             24 operations
  validate_openapi.py      JSON validity + local $ref resolution + operation count
sql/
  001_initial_design.sql   PostgreSQL design migration (not executed)
fixtures/
  envelopes/accounting_evidence_preparation.json
  envelopes/industrial_rfq_preparation.json
  envelopes/laundry_route_preparation.json
  plans/accounting_evidence_preparation.json
  plans/industrial_rfq_preparation.json
  plans/laundry_route_preparation.json
  invalid/*.json           malformed plans used by tests (named by the defect)
acceptance/
  production_acceptance_catalog.yaml   30 scenarios
spec/
  Plumb_Autonomous_Implementation_Specification_v0.2.md   normative Markdown
  requirements_index.json              63 PL requirements + 10 ADRs
tests/
  conftest.py              requirement markers
  test_*.py
scripts/
  validate.py              runs everything, writes VALIDATION_REPORT.md and MANIFEST.json
README.md
VALIDATION_REPORT.md
MANIFEST.json
```

## 2. Conventions

* Python ≥ 3.11, Pydantic v2 only. Every model subclasses `StrictModel` from
  `plumb.contracts.common` (extra fields forbidden).
* Every **top-level contract** subclasses `ArtifactHeader` and fixes its
  `kind` with `Literal[...]` defaulting to the matching `ArtifactKind` value,
  e.g. `kind: Literal[ArtifactKind.BUILD_PLAN] = ArtifactKind.BUILD_PLAN`.
* Identifiers use `Identifier` (lower-case). Tenants use `TenantId`
  (`tnt_…`). Digests use `Sha256Digest` (`sha256:<64 hex>`).
* Money is `Money(minor_units, currency)`; never floats.
* Timestamps are timezone-aware `datetime`. Fixtures use ISO-8601 with `Z`.
* No secrets anywhere: fields hold *references* (`credential_ref`), never values.
  A validator on any field named `*_ref` must reject values that look like
  secrets (contain `secret`, `password`, `token=` or are ≥ 40 chars of base64).
* Module-level docstrings cite the PL requirements they implement.
* Tests mark the requirements they exercise:
  `@pytest.mark.requirements("PL-014", "PL-015")`. `scripts/validate.py`
  builds the coverage matrix from these markers; a requirement with no marker
  is reported as *not locally enforced*.
* Each test file is self-contained; fixtures are loaded via helpers in
  `tests/conftest.py` (`load_fixture(relative_path)`).

## 3. Top-level contracts (17)

| # | Contract | Module | Key fields beyond `ArtifactHeader` (spec refs) |
|---|----------|--------|-----------------------------------------------|
| 1 | `AutonomyEnvelope` | envelope.py | `envelope_id`, `envelope_version:int`, `owner: Principal` (HUMAN_OWNER), `goals: list[Goal]`, `source_grants: list[SourceGrant]` (source_id, purposes, granted_by, granted_at, expires_at, policy_version), `approved_destinations`, `approved_processors`, `allowed_effect_classes`, `spending_limit: Money`, `per_step_attempt_limit`, `deployment_environments: list[str]`, `allowed_regions: list[Region]`, `expires_at`, `escalation_conditions: list[str]`, `policy_version: SemVer`, `revoked_at: datetime|None`. Methods: `is_active(now)`, `scope() -> ResourceScope`, `purposes_for(source_id) -> set[DataPurpose]`. (PL-005, PL-040, PL-053) |
| 2 | `CapabilityRecord` | capability.py | `capability_id`, `step_type`, `provider`, `operation`, `maturity: CapabilityMaturity`, `effect_classes: list[EffectClass]`, `required_purposes: list[DataPurpose]`, `required_authority: list[str]`, `tested_environment`, `failure_modes`, `maintenance_burden: {LOW,MEDIUM,HIGH}`, `produces: list[ArtifactKind]`, `consumes: list[ArtifactKind]`, `probe_receipt_ref`, `capability_version: SemVer` (PL-007, PL-008, Appendix A.5) |
| 3 | `EnvironmentInventory` | inventory.py | `applications: list[ApplicationRecord]` each with `accounts`, `entities`, `schema_versions`, `operations: list[OperationCapability]` (operation, read/write, maturity, probe receipt id, last probed), `authorization_status`, `quotas`, `update_mechanism` (WEBHOOK/POLLING/CDC/EXPORT), `freshness`, `owners`; `coverage_report` (observed vs unobserved applications/employees — PL-007, PL-008, section 5) |
| 4 | `EvidencePacket` | evidence.py | `events: list[EvidenceEvent]` (source identity, external_record_id, external_version, time: TimeAxes, content_digest, raw_content_ref, access_policy_ref, retention_class, extraction_version), `facts: list[DerivedFact]` (supporting_evidence_ids ≥1, derivation_version, valid_from/valid_to, status: FactStatus, presence: Presence, confidence ∈[0,1] *not* authority), `object_resolutions: list[ObjectResolution]` (candidates, merge/split history, scoped corrections with impact set), `links` many-to-many (PL-009, PL-010, PL-011) |
| 5 | `OpportunitySpec` | opportunity.py | `business_objective`, `eligible_case_population`, `baseline`, `evidence_coverage`, `proposed_change` (`intervention_kind` incl. NATIVE_SETTING, DETERMINISTIC_AUTOMATION, GENERAL_MODEL_WORKFLOW, SPECIALIST_SERVICE, RETRIEVAL_SYSTEM, TRAINED_COMPONENT, REMOVE_STEP), `dependencies`, `expected_benefit_range: {low, high, horizon_days}`, `failure_cost`, `review_cost`, `measurement_plan` (prospective), `blocking_conditions`, `overlap_refs` (PL-012, PL-013) |
| 6 | `BuildPlan` | build_plan.py | see §4 (PL-014..PL-019) |
| 7 | `IntegrationSpec` | integration.py | `source: SourceRef`, `operations: list[IntegrationOperation]` (name, direction READ/WRITE, effect_class, path_used: VERIFIED_ADAPTER/DECLARATIVE_CONFIG/GENERATED_CODE/UI_ADAPTER, maintenance_exposure), `authentication_ref`, `required_scopes`, `schema_mappings` (source field → target field with unit/currency/timezone/enum/null semantics), `cursor_strategy`, `rate_limits`, `retry_semantics`, `deletion_behavior`, `verification_probes`, `schema_drift_handling`, `contract_tests_passed: list[str]` must include pagination, empty_pages, duplicates, rate_limiting, authorization_failure, malformed_responses, schema_changes, account_boundaries before `activated=True`; write adapters also `business_state_verification`, `uncertain_write_behavior` (PL-020..PL-022) |
| 8 | `CollectionSpec` | collection.py | `objective_ref`, `allowed_sources`, `selected_fields`, `join_strategy`, `incremental_mechanism` (WEBHOOK/POLLING_OVERLAP/CDC), `watermark`, `backfill_boundary`, `retention`, `destination`, `access_policy_ref`, `quality_checks`, `permitted_purpose_evidence`, `health: {freshness, lag, completeness, failure_state}` publishing contract, `idempotent_event_identity` (PL-023..PL-025) |
| 9 | `DatasetManifest` | dataset.py | see §5 (PL-028..PL-030) |
| 10 | `TrainingSpec` | training.py | `dataset_ref: ArtifactRef` (pinned), `base_model: {provider, capability, version}`, `method` (API_FINETUNE/MANAGED_OPEN_MODEL/NONE), `objective`, `budget`, `stopping_condition`, `output_location`, `data_handling: {processor, region, retention, credential_ref}`, `evaluation_plan_ref`, `submission_identity` (persisted before submit), `supported_combination_check` (PL-032, PL-033) |
| 11 | `WorkflowSpec` | workflow.py | `case_identity`, `triggers`, `typed_inputs`, `states`, `transitions`, `allowed_operations` (certified primitives: fetch, classify, extract, validate, match, calculate, optimize, request_missing_information, wait, review, write), `max_iterations`, `max_duration_seconds`, `max_cost`, `durable_waits`, `human_decision_points`, `completion_conditions`, each operation flagged `external_effect: bool` and `effect_class` (PL-035, PL-036) |
| 12 | `EvaluationReport` | evaluation.py | `subject_ref`, `dataset_ref` (held-out), `level: VerificationLevel`, `metrics` with denominators, `error_severity_breakdown`, `review_time`, `cost_comparison`, `candidate_comparison` (baseline vs general model vs trained), `trials`, `segregation_statement` (eval data not used for tuning) (PL-031, PL-034, PL-044) |
| 13 | `InfrastructurePlan` | infrastructure.py | `template_refs` (approved), `preview_diff_ref`, `cost_estimate: Money`, `state_lock_ref`, `ownership_tags`, `rollback_classification` (ROLLBACK/COMPENSATE/IRREVERSIBLE per resource), `expand_contract_phase`, `destructive_changes_require_authorization: bool` (PL-045) |
| 14 | `ReleaseManifest` | release.py | `components: dict[str, ArtifactRef]` keys ⊇ {workflow, connector, collector, model, prompt, policy, schema, infrastructure, evaluation} (any may be `null` with `omitted_reason`), `attestation_refs`, `approval_refs`, `rollout_policy` (stages SHADOW→CANARY→ACTIVE with gates), `resolved_model_version`, `denominators`, `allowed_effect_classes`, `review_thresholds` (PL-034, PL-046, PL-047) |
| 15 | `ActionIntent` | effect.py | see §6 (PL-037..PL-039) |
| 16 | `ApprovalRecord` | approval.py | `approval_id`, `decision_kind` (DATA_USE / IMPLEMENT_OPERATE / CASE_LEVEL_BUSINESS), `subject_digest: Sha256Digest`, `case_version: int|None`, `policy_version: SemVer`, `approver: Principal` (HUMAN_*), `authenticated_decision_ref`, `approved_at`, `expires_at`, `revoked_at`, `scope_tenant: TenantId` (PL-040, PL-041) |
| 17 | `VerificationAttestation` | verification.py | `verifier: Principal` (VERIFIER), `verifier_version: SemVer`, `input_artifact_digest`, `level: VerificationLevel`, `checks: list[CheckResult]` (name, result PASS/FAIL/SKIPPED, evidence_refs), `result`, `timestamp`, `environment`, `protected_bundle_digest` (PL-042, PL-043) |

Supporting (not counted): `JobEnvelope` (job_id, tenant_id, status, idempotency_key, result_ref, error),
`ErrorEnvelope` (error_class, message, retryable, dependency_id, operator_action),
`EventEnvelope` (event_id, tenant_id, aggregate_id, aggregate_version, event_type,
occurred_at, recorded_at, correlation_id, causation_id, schema_version, payload_ref),
`AgentTask`, `StepResult` (Appendix A §1, §3).

## 4. BuildPlan and the reference checker

```python
class StepInput(StrictModel):
    name: Identifier
    kind: ArtifactKind
    from_step: Identifier | None      # None => plan-level input artifact
    plan_input: Identifier | None     # name of a BuildPlan.inputs entry

class StepOutput(StrictModel):
    name: Identifier
    kind: ArtifactKind

class VerificationObligation(StrictModel):
    check: Identifier                 # e.g. "contract_tests", "source_to_storage_receipt"
    level: VerificationLevel
    description: NonEmptyStr

class BuildStep(StrictModel):
    step_id: Identifier
    step_type: Identifier             # must exist in the capability registry
    description: NonEmptyStr
    depends_on: list[Identifier]
    inputs: list[StepInput]
    outputs: list[StepOutput]
    required_capabilities: list[Identifier]   # capability_ids in the registry
    effect_class: EffectClass
    purposes: list[DataPurpose]
    scope: ResourceScope
    budget: Budget
    verification: list[VerificationObligation]   # ≥1 unless step_type == "dependency.raise"
    required: bool = True
    environment: ShortStr | None = None   # deployment environment for infrastructure.*/release.* steps

class BuildPlan(ArtifactHeader):
    kind = BuildPlan
    plan_id: Identifier
    goal_id: Identifier
    opportunity_ref: ArtifactRef | None
    envelope_id: Identifier
    envelope_version: int
    inputs: list[ArtifactRef]           # plan-level immutable inputs
    steps: list[BuildStep]
    total_budget: Budget                # declared worst case for whole plan
    planned_at: datetime
```

`check_plan(plan, envelope, registry) -> CheckReport` emits `Finding(code, error_class, step_id, message, severity)` for:

| code | error_class | rule |
|------|-------------|------|
| `DUPLICATE_STEP_ID` | STATE_CONFLICT | step ids unique (PL-015) |
| `UNKNOWN_DEPENDENCY` | STATE_CONFLICT | every depends_on exists (PL-015) |
| `DEPENDENCY_CYCLE` | STATE_CONFLICT | graph is a DAG; report the cycle (PL-014) |
| `UNSUPPORTED_STEP_TYPE` | CAPABILITY_UNSUPPORTED | step_type in registry (PL-014) |
| `UNKNOWN_CAPABILITY` | CAPABILITY_UNSUPPORTED | each required capability in registry and matches step_type |
| `CAPABILITY_MATURITY_INSUFFICIENT` | CAPABILITY_UNSUPPORTED | production steps (effect ≠ READ, non-shadow) need SANDBOX_TESTED+; `release.*`/`infrastructure.apply` need PRODUCTION_VERIFIED (PL-008) |
| `INPUT_UNRESOLVED` | STATE_CONFLICT | input from_step must be in depends_on and produce that output name (PL-015) |
| `INPUT_KIND_MISMATCH` | STATE_CONFLICT | input kind == producing output kind / plan input kind |
| `MISSING_ARTIFACT` | STATE_CONFLICT | plan_input name not in plan.inputs |
| `TENANT_MISMATCH` | SCOPE_DENIED | plan.tenant_id == envelope.tenant_id |
| `ENVELOPE_MISMATCH` | POLICY_STALE | plan.envelope_id/version == envelope (PL-005) |
| `ENVELOPE_INACTIVE` | POLICY_STALE | envelope expired or revoked at `now`/planned_at (PL-005) |
| `SCOPE_EXCEEDED` | SCOPE_DENIED | step.scope within envelope scope (sources, destinations, processors, regions) (PL-005) |
| `EFFECT_CLASS_DENIED` | SCOPE_DENIED | step.effect_class ∈ envelope.allowed_effect_classes and ⊆ registry capability effect classes |
| `PURPOSE_DENIED` | PURPOSE_DENIED | for each source in step.scope.source_ids, step.purposes ⊆ envelope.purposes_for(source); TRAIN never inferred from INSPECT/COLLECT (PL-053) |
| `BUDGET_EXCEEDED` | BUDGET_EXCEEDED | Σ step worst-case spend ≤ plan.total_budget.spend ≤ envelope.spending_limit; currency consistent (PL-058) |
| `ATTEMPTS_EXCEEDED` | BUDGET_EXCEEDED | step.budget.max_attempts ≤ envelope.per_step_attempt_limit (PL-018) |
| `MISSING_VERIFICATION` | VERIFICATION_FAILED | each step (except `dependency.raise`) has ≥1 verification obligation; steps with external effects need ≥ INTEGRATION_BEHAVIOR; `release.*` needs BUSINESS_OUTCOME (PL-016, PL-043) |
| `DEPLOYMENT_ENV_DENIED` | SCOPE_DENIED | infrastructure/release steps declare `environment` within envelope.deployment_environments |

`CheckReport.ok` is true iff no finding of severity `ERROR`. `CheckReport.topological_order` is populated when the graph is acyclic. The checker never executes anything.

The step-type vocabulary (registry keys) is:
`inventory.probe`, `source.profile`, `integration.configure`, `integration.generate_adapter`,
`integration.contract_test`, `collection.deploy_shadow`, `collection.backfill`,
`collection.reconcile`, `collection.enable_incremental`, `dataset.discover_sources`,
`dataset.build`, `dataset.label_audit`, `training.submit`, `evaluation.run`,
`workflow.compile`, `workflow.test_bundle`, `infrastructure.preview`, `infrastructure.apply`,
`release.create`, `release.activate_shadow`, `release.canary`, `verification.request`,
`dependency.raise`.

## 5. DatasetManifest and dataset checker

```python
class DatasetRow(StrictModel):
    example_id: Identifier
    group_id: Identifier                  # transaction/document family
    input_snapshot_refs: list[Identifier] # evidence event ids
    input_availability_time: datetime     # max availability time among inputs
    decision_time: datetime
    target_evidence_ref: Identifier | None
    target_availability_time: datetime | None
    label_kind: LabelKind
    label_status: LabelStatus
    purpose_authorization_ref: Identifier
    split: Literal["train","validation","test_temporal","test_client_disjoint"]
    exclusion_reason: str | None          # required when label_status != ACCEPTED

class DatasetManifest(ArtifactHeader):
    dataset_id, revision:int, task_definition_ref, label_definition, split_rules: list[SplitRule]
    (name, question_answered, rule), schema_ref, rows: list[DatasetRow], counts (by split, by label status),
    distributions, content_hashes, source_versions: list[ArtifactRef] (pinned), transformation_refs,
    lineage_refs, availability: DatasetState-ish flag `unavailable_reason: str|None`, source_rights_refs
```

`check_dataset(manifest)` emits: `FUTURE_INFORMATION` (input_availability_time > decision_time), `TARGET_LEAK` (an OBSERVED_OUTCOME known before the decision is fine; a CORRECTION or EXPERT_DECISION target available before decision_time is a leak), `UNKNOWN_AVAILABILITY` (missing availability → cannot claim faithful replay), `DUPLICATE_FAMILY_ACROSS_SPLITS` (same group_id in >1 split), `QUARANTINED_ROW_IN_TRAINING` (non-ACCEPTED label in train split), `MISSING_EXCLUSION_REASON`, `UNPINNED_SOURCE` (source_versions empty or without digest), `COUNT_MISMATCH` (declared counts ≠ rows), `SPLIT_WITHOUT_QUESTION`. Error classes: DATA_QUALITY_FAILED (PL-027..PL-030).

## 6. ActionIntent and the effect ledger

```python
class EffectSlot(StrictModel):
    tenant_id: TenantId
    case_id: Identifier
    obligation_id: Identifier
    obligation_epoch: int
    operation: Identifier
    target: Identifier          # provider account/recipient identity
    def key(self) -> str        # "tenant|case|obligation|epoch|operation|target"

class ActionIntent(ArtifactHeader):
    kind = ActionIntent
    action_id: Identifier               # logical action id (stable across retries)
    slot: EffectSlot
    payload_digest: Sha256Digest
    expected_state_version: int
    authority_ref: Identifier           # approval/envelope reference
    deployment_version: Identifier      # release id
    provider_target: SourceRef
    effect_class: EffectClass
    idempotency_key: str                # derived from action_id, not from payload
    supersedes_action_id: Identifier | None
```

`EffectLedger(path)` (SQLite, WAL) with methods:

* `reserve(intent) -> ReservationResult` — inserts row in RESERVED; **same slot key with same payload digest returns the existing action (idempotent)**; **same slot key with different payload digest raises `PayloadConflict` (PAYLOAD_CONFLICT) unless `intent.supersedes_action_id` names the existing action and that action is in a terminal state or explicitly superseded** (PL-037).
* `mark_dispatched(action_id, lease_owner, provider_request_id)` — RESERVED→DISPATCHED, records lease and request id (PL-057).
* `mark_unknown(action_id, reason)` — DISPATCHED→UNKNOWN on timeout/ambiguous outcome; **a timeout is never treated as "nothing happened"** (PL-038).
* `reconcile(action_id, outcome: ReconciliationResult)` — UNKNOWN→CONFIRMED (requires external receipt/postcondition), UNKNOWN→FAILED_FINAL (requires provider-confirmed non-occurrence), otherwise stays UNKNOWN; **retry is refused while UNKNOWN** (`EffectUnknown` error, EFFECT_UNKNOWN).
* `confirm(action_id, receipt)` — DISPATCHED→CONFIRMED, receipt required.
* `fail_final(action_id, reason)`; `compensate(action_id, compensation_receipt)` — CONFIRMED→COMPENSATED.
* `outstanding()` — list of DISPATCHED/UNKNOWN effects (restart reconciliation list, PL-039).
* All transitions persist `(from_state, to_state, reason, at)` in an `effect_transitions` table.
* Deduplication survives process restart: reopening the same file and reserving the same slot returns the same action (PL-039). Dedup is independent of `deployment_version` (same slot across releases is the same business action).

## 7. State machines

`plumb.statemachines.machines` exposes `BUILD`, `BUILD_STEP`, `COLLECTOR`, `DATASET`, `TRAINING`, `RELEASE`, `EFFECT` machines, each an instance of
`StateMachine(name, states_enum, transitions: dict[(from,to)] -> Guard | None)`. `machine.transition(current, target, context: dict, reason: str) -> Transition` raises `IllegalTransition` (STATE_CONFLICT) when the edge is absent or a guard fails (`GuardFailed` carries the guard name). Guards fixed by spec:

* Build → VERIFIED requires `context["required_steps_verified"] is True`.
* Release → ACTIVE requires `context["authority_current"]` and `context["attestations_accepted"]`.
* Effect → CONFIRMED requires `context["external_receipt"]` (truthy).
* Effect UNKNOWN → * requires `context["reconciliation_result"] in {"CONFIRMED","FAILED_FINAL"}` matching the target.
* Build step → VERIFIED requires `context["verifier_attestation"]` (a worker's claim is not enough).
* Dataset → VERIFIED requires `context["checker_ok"]`.
* Terminal states have no outgoing edges: Build {VERIFIED? no — VERIFIED is terminal for build}, FAILED, CANCELLED; Effect CONFIRMED→COMPENSATED allowed, FAILED_FINAL and COMPENSATED terminal; Release RETIRED terminal.

Every `Transition` carries `reason` (non-empty) and `at`.

## 8. OpenAPI (24 operations)

Paths under `/v1/tenants/{tenant_id}/…`. Tenant id in the path is informational; servers derive tenant from auth (PL-004) and MUST 404-not-403 on cross-tenant access (PL-056). Long-running mutations return 202 with `JobEnvelope`; mutating operations require `Idempotency-Key` header; versioned updates require `If-Match` and define 412. List operations take `cursor` + `limit` (max 200) and return `next_cursor`.

Operations (operationId): `createEnvelope`, `getEnvelope`, `revokeEnvelope`,
`startInventoryJob`, `getInventoryJob`, `startOpportunityDiscovery`, `listOpportunities`,
`createBuild`, `getBuild`, `listBuildEvents`, `resolveBuildDependency`,
`createConnectionIntent`, `getConnectionIntent`,
`startCollectionJob`, `getCollectionJob`,
`startDatasetJob`, `startTrainingJob`, `getTrainingJob`,
`createEvaluation`, `createRelease`, `activateRelease`, `pauseRelease`,
`dispatchAction`, `reconcileAction`, `listOutcomes`.
That is 25 — drop `revokeEnvelope` (envelope revocation is modelled through `createEnvelope` of a new version + `If-Match`) to land on exactly 24. Components reference the generated JSON Schemas conceptually but must be **self-contained** in the document (`#/components/schemas/...`), with `x-plumb-contract: <ContractName>` annotations linking to `schemas/<ContractName>.json`.

## 9. SQL design migration

Tables: `tenants`, `envelopes`, `source_grants`, `capabilities`, `artifacts`, `evidence_events`, `objects`, `object_links`, `facts`, `goals`, `opportunities`, `builds`, `build_steps`, `build_step_attempts`, `datasets`, `dataset_rows`, `training_jobs`, `evaluations`, `approvals`, `releases`, `cases`, `effects`, `effect_transitions`, `outbox`, `processed_events`, `outcome_observations`, `human_effort`. Composite `(tenant_id, <id>)` primary keys; FKs include tenant_id; indexes for case lookups, external source identity, job readiness (`build_steps(tenant_id, build_id, state) WHERE state='READY'`), outstanding effects (`effects(tenant_id, state) WHERE state IN ('DISPATCHED','UNKNOWN')`); unique `effects(tenant_id, slot_key)`; RLS enabled with the explicit comment that owner/superuser bypass remains (PL-052); separate roles `plumb_app`, `plumb_migrator`, `plumb_platform_admin`.

## 10. Requirements index

`spec/requirements_index.json`:

```json
{
  "spec_version": "0.2",
  "spec_date": "2026-10-02",
  "requirements": [
    {"id": "PL-001", "section": "1", "section_title": "Product contract: Plumb performs the implementation",
     "text": "...exact text...", "keywords": ["MUST", "MUST NOT"]}
  ],
  "adrs": [{"id": "ADR-001", "title": "...", "rationale": "..."}]
}
```

Exactly 63 requirements and 10 ADRs. Text must match the specification verbatim (whitespace-normalised).

## 11. Production acceptance catalog

`acceptance/production_acceptance_catalog.yaml`: exactly 30 scenarios, each with
`id` (`PA-001`…), `title`, `category` (one of: normal, boundary, corrupted_input,
stale_revoked_access, duplicate_reordered_events, crash_after_dispatch,
concurrent_actors, source_edit_after_approval, adversarial_instruction,
isolation, economics), `scenario` (one of accounting, industrial_rfq, laundry, platform),
`requirements` (PL ids), `preconditions`, `steps`, `expected_outcome`,
`severity` (HIGH blocks activation per PL-061), `requires` (list: real_adapter,
isolation, grants, deployment, prospective_outcome), `locally_executed: false`.
The nine mandatory PL-061 categories must each appear at least once, and the
Appendix B failure cases (wrong client, ambiguous period, already-received
document, corrected statement, duplicate request, expired permission, provider
timeout after send, changed approval, stale source) must all appear.
