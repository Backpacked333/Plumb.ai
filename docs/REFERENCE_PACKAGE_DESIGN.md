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
    plan_checker.py        check_plan(plan, envelope, registry=None, now=None) -> CheckReport
    dataset_checker.py     check_dataset(manifest, envelope=None, *, now=None) -> CheckReport
    approval_checker.py    check_approval(approval, *, subject_digest, tenant_id, policy_version, case_version=None, now, decision_kind=None) -> CheckReport
    release_checker.py     check_release(manifest, attestations, approvals, *, now, current_policy_version) -> CheckReport
    cli.py                 python -m plumb.checker.cli plan <plan.json> [<envelope.json>] [--registry <registry.json>] [--now ISO] [--json]
                           (one file with top-level "plan" and "envelope" keys is accepted; fixtures/invalid/ uses it)
                           python -m plumb.checker.cli dataset <manifest.json> [--envelope <envelope.json>] [--json]
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
  One helper, `plumb.contracts.common.reject_secret_like`, is the only secret
  heuristic in the package (the names re-exported by capability, approval,
  training, effect and inventory are aliases of it). Every field named `*_ref`
  or `*_refs`, the authentication and authority fields (`Principal.authenticated_via`,
  `CapabilityRecord.required_authority`, `DependencyRecord.missing_authority`)
  and both operator-facing texts of `ErrorEnvelope` carry it through the
  `NonSecretRef` / `NonSecretIdentifier` / `NonSecretText` / `StorageRef`
  annotated types. It rejects the strictest union of the former copies: the
  markers `secret`, `password`, `token=`, `token:`, `bearer `, `private key`;
  AWS access-key and JWT shapes; ≥ 32 hex characters; ≥ 40 characters of base64
  (standard or URL-safe, any case); and whole-value base64. Only `sha256:<64 hex>`
  digest segments are exempt. `StorageRef` additionally requires a
  `scheme:` / `scheme://` grammar so document content cannot pass as a reference.
* Timestamps that the checkers compare are `AwareDatetime`; a naive datetime is
  a validation error (`require_aware` in `common` is the runtime check for
  caller-supplied instants).
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
| 1 | `AutonomyEnvelope` | envelope.py | `envelope_id`, `envelope_version:int`, `owner: Principal` (HUMAN_OWNER), `goals: list[Goal]`, `source_grants: list[SourceGrant]` (source_id, purposes, granted_by, granted_at, expires_at, policy_version), `approved_destinations`, `approved_processors`, `allowed_effect_classes`, `spending_limit: Money`, `per_step_attempt_limit`, `deployment_environments: list[str]`, `allowed_regions: list[Region]`, `expires_at`, `escalation_conditions: list[str]`, `policy_version: SemVer`, `revoked_at: datetime|None`; `envelope_id == artifact_id`; `SourceGrant.grant_id` is optional and, when given, unique (`effective_grant_id` derives `grant:<source_id>:<policy_version>` otherwise); `granted_by` is a HUMAN_* principal. Methods: `is_active(now)` (expiry exclusive; **false whenever `revoked_at` is set**, regardless of `now`, so a revoked envelope never authorises anything), `scope(now=None) -> ResourceScope`, `purposes_for(source_id, now=None) -> set[DataPurpose]`, `active_grants(now=None)`, `grants_by_id(grant_id, now=None)`; `now` defaults to `created_at`, the checker passes `planned_at` or its own `now`. (PL-005, PL-040, PL-053) |
| 2 | `CapabilityRecord` | capability.py | `capability_id`, `step_type`, `provider`, `operation`, `maturity: CapabilityMaturity`, `effect_classes: list[EffectClass]`, `required_purposes: list[DataPurpose]`, `required_authority: list[str]`, `tested_environment`, `failure_modes`, `maintenance_burden: {LOW,MEDIUM,HIGH}`, `produces: list[ArtifactKind]`, `consumes: list[ArtifactKind]`, `probe_receipt_ref`, `capability_version: SemVer`; `tenant_id` is `tnt_platform` and `tested_environment` is required at SANDBOX_TESTED / PRODUCTION_VERIFIED (PL-007, PL-008, Appendix A.5) |
| 3 | `EnvironmentInventory` | inventory.py | `applications: list[ApplicationRecord]` each with `accounts`, `entities`, `schema_versions`, `operations: list[OperationCapability]` (operation, read/write, maturity, probe receipt id, last probed), `authorization_status`, `quotas`, `update_mechanism` (WEBHOOK/POLLING/CDC/EXPORT/NONE), `freshness_seconds`, `available_history_from`, `owners`; an `OperationCapability.account_id` must name one of the application's accounts; `coverage_report` (observed vs unobserved applications/employees — PL-007, PL-008, section 5) |
| 4 | `EvidencePacket` | evidence.py | `events: list[EvidenceEvent]` (source identity, external_record_id, external_version, time: TimeAxes, content_digest, raw_content_ref: StorageRef, access_policy_ref, retention_class, extraction_version), `facts: list[DerivedFact]` (supporting_evidence_ids ≥1, derivation_version, valid_from/valid_to, status: FactStatus, presence: Presence, confidence ∈[0,1] *not* authority), `object_resolutions: list[ObjectResolution]` (candidates, merge/split history, scoped corrections with impact set), `links` many-to-many (PL-009, PL-010, PL-011) |
| 5 | `OpportunitySpec` | opportunity.py | `business_objective`, `eligible_case_population`, `baseline`, `evidence_coverage`, `proposed_change` (`intervention_kind` incl. NATIVE_SETTING, DETERMINISTIC_AUTOMATION, GENERAL_MODEL_WORKFLOW, SPECIALIST_SERVICE, RETRIEVAL_SYSTEM, TRAINED_COMPONENT, REMOVE_STEP), `dependencies`, `expected_benefit_range: {low, high, horizon_days}`, `failure_cost`, `review_cost`, `measurement_plan` (prospective), `blocking_conditions`, `overlap_refs` (PL-012, PL-013) |
| 6 | `BuildPlan` | build_plan.py | see §4 (PL-014..PL-019) |
| 7 | `IntegrationSpec` | integration.py | `source: SourceRef`, `operations: list[IntegrationOperation]` (name, direction READ/WRITE, effect_class, path_used: VERIFIED_ADAPTER/DECLARATIVE_CONFIG/GENERATED_CODE/UI_ADAPTER, maintenance_exposure), `authentication_ref`, `required_scopes`, `schema_mappings` (source field → target field with unit/currency/timezone/enum/null semantics), `cursor_strategy`, `rate_limits`, `retry_semantics`, `deletion_behavior`, `verification_probes`, `schema_drift_handling`, `contract_tests_passed: list[str]` must include pagination, empty_pages, duplicates, rate_limiting, authorization_failure, malformed_responses, schema_changes, account_boundaries before `activated=True`; write adapters also `business_state_verification`, `uncertain_write_behavior` (PL-020..PL-022) |
| 8 | `CollectionSpec` | collection.py | `objective_ref`, `allowed_sources`, `selected_fields`, `join_strategy`, `incremental_mechanism` (WEBHOOK/POLLING_OVERLAP/CDC/EXPORT), `watermark`, `backfill_boundary`, `retention`, `destination`, `access_policy_ref`, `quality_checks`, `permitted_purpose_evidence`, `health: CollectorHealth {freshness_seconds, lag_seconds, completeness, failure_state, health_deadline_seconds}` publishing contract, `idempotent_event_identity`, `reordering_policy`, `correction_policy` (PL-023..PL-025) |
| 9 | `DatasetManifest` | dataset.py | see §5 (PL-028..PL-030) |
| 10 | `TrainingSpec` | training.py | `dataset_ref: ArtifactRef` (pinned), `base_model: {provider, capability, version}`, `method` (API_FINETUNE/MANAGED_OPEN_MODEL/NONE), `objective`, `budget`, `stopping_condition`, `output_location`, `data_handling: {processor, region, retention, credential_ref}`, `evaluation_plan_ref: ArtifactRef`, `submission_identity` (persisted before submit), `supported_combination_check`; `base_model.version` rejects mutable aliases (`latest`, `stable`, …); method NONE forbids a budget and allows only PLANNED/CANCELLED (PL-032, PL-033) |
| 11 | `WorkflowSpec` | workflow.py | `case_identity`, `triggers`, `typed_inputs`, `states`, `transitions`, `allowed_operations` (certified primitives: fetch, classify, extract, validate, match, calculate, optimize, request_missing_information, wait, review, write), `max_iterations`, `max_duration_seconds`, `max_cost`, `durable_waits`, `human_decision_points` (both lists are required fields and may be empty; a human decision point is mandatory when an `external_effect` operation is FINANCIAL_COMMITMENT / EXTERNAL_WRITE_IRREVERSIBLE / DESTRUCTIVE, `COMMITMENT_EFFECT_CLASSES`), `completion_conditions`, each operation flagged `external_effect: bool` and `effect_class` (PL-035, PL-036) |
| 12 | `EvaluationReport` | evaluation.py | `subject_ref`, `dataset_ref` (held-out), `level: VerificationLevel`, `metrics` with denominators, `error_severity_breakdown`, `review_time`, `cost_comparison`, `candidate_comparison` (baseline vs general model vs trained), `trials`, `segregation_statement` (eval data not used for tuning; carries `basis`), `held_out_split` (never `train`), `case_count`, `nondeterministic`, `excluded_case_count` (> 0 requires `exclusion_summary`) (PL-031, PL-034, PL-044) |
| 13 | `InfrastructurePlan` | infrastructure.py | `template_refs` (approved), `preview_diff_ref: ArtifactRef` (the InfrastructurePreview), `cost_estimate: Money` (≥ per-resource sum), `state_lock_ref: NonSecretRef`, `environment`, `changes: list[ResourceChange]` (each with `resource_id`, `action`, `rollback_classification` ROLLBACK/COMPENSATE/IRREVERSIBLE, `ownership_tags`, `estimated_cost`), `expand_contract_phase`, `destructive_authorization_ref` and `backup_restore_strategy_ref` (`NonSecretIdentifier|None`, required when a change is destructive) (PL-045) |
| 14 | `ReleaseManifest` | release.py | `components: dict[str, ReleaseComponent]` keys ⊇ {workflow, connector, collector, model, prompt, policy, schema, infrastructure, evaluation} (each `ref: ArtifactRef|None` with `omitted_reason`; kinds constrained per component; a model or workflow component requires the evaluation component), `attestation_refs` (≥ 1), `approval_refs`, `rollout_policy: list[RolloutStage]` (`state`, `gate`, `environment`, `max_case_fraction`; starts at SHADOW, reaches ACTIVE only through CANARY), `resolved_model_version`, `denominators`, `allowed_effect_classes`, `review_thresholds` (values in [0,1]), `in_flight_pinning`, `scope: ResourceScope`, `operating_plan: OperatingPlan` (monitors covering the seven PL-048 signals, human `rollback_owner`, `escalation_contact`, `outcome_measurement_ref`, `review_capacity_per_day`). `approval_subject_digest()` (manifest minus `content_digest` and `approval_refs`) is what approvals bind to (PL-034, PL-043, PL-046, PL-047, PL-048) |
| 15 | `ActionIntent` | effect.py | see §6 (PL-037..PL-039) |
| 16 | `ApprovalRecord` | approval.py | `approval_id`, `decision_kind` (DATA_USE / IMPLEMENT_OPERATE / CASE_LEVEL_BUSINESS), `subject_digest: Sha256Digest`, `case_version: int|None`, `policy_version: SemVer`, `approver: Principal` (HUMAN_*), `authenticated_decision_ref`, `approved_at`, `expires_at`, `revoked_at`, `scope_tenant: TenantId` (PL-040, PL-041) |
| 17 | `VerificationAttestation` | verification.py | `verifier: Principal` (VERIFIER), `verifier_version: SemVer`, `input_artifact_digest`, `level: VerificationLevel`, `checks: list[CheckResult]` (name, result PASS/FAIL/SKIPPED, evidence_refs), `result`, `timestamp`, `environment`, `scope: ResourceScope`, `assessed_producer: Principal`, `protected_bundle_digest`; the producer of the attestation is never an agent (PL-042, PL-043) |

Supporting (not counted): `JobEnvelope` (job_id, tenant_id, status: JobStatus {PENDING, RUNNING, SUCCEEDED, FAILED, WAITING}, idempotency_key ≤ 255 chars, operation: OperationId, result_ref, error, created_at, updated_at, server_assigned_version),
`ErrorEnvelope` (error_class, message, retryable, dependency_id, operator_action, correlation_id, tenant_id, request_payload_digest; message and operator_action are screened for secrets and foreign tenant ids),
`EventEnvelope` (event_id, tenant_id, aggregate_id, aggregate_version, event_type,
occurred_at, recorded_at, correlation_id, causation_id, schema_version, payload_ref),
`AgentTask`, `StepResult` (Appendix A §1, §3; `fencing_token` is an `int` lease epoch; an AgentTask rejects fields whose names look like credentials, PL-019).

## 4. BuildPlan and the reference checker

```python
class StepInput(StrictModel):
    name: Identifier
    kind: ArtifactKind
    from_step: Identifier | None      # None => plan-level input artifact
    plan_input: Identifier | None     # name of a BuildPlan.inputs entry
    source_ids: list[Identifier] | None   # lineage narrowing: the subset of the producer's sources this input carries (from_step inputs only)

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

`check_plan(plan, envelope, registry=None, now=None) -> CheckReport` (registry defaults to the packaged one; `now` only moves the evaluation instant forward from `planned_at`) emits `Finding(code, error_class, step_id, message, severity)` for:

| code | error_class | rule |
|------|-------------|------|
| `DUPLICATE_STEP_ID` | STATE_CONFLICT | step ids unique (PL-015) |
| `UNKNOWN_DEPENDENCY` | STATE_CONFLICT | every depends_on exists (PL-015) |
| `DEPENDENCY_CYCLE` | STATE_CONFLICT | graph is a DAG; report the cycle (PL-014) |
| `UNSUPPORTED_STEP_TYPE` | CAPABILITY_UNSUPPORTED | step_type in registry (PL-014) |
| `UNKNOWN_CAPABILITY` | CAPABILITY_UNSUPPORTED | each required capability in registry and matches step_type; a step with no bound capability at all (except `dependency.raise`) is unknown, whatever its effect class |
| `CAPABILITY_MATURITY_INSUFFICIENT` | CAPABILITY_UNSUPPORTED | `dependency.raise` needs DOCUMENTED; other steps need SANDBOX_TESTED+ (the shadow exemption applies to `collection.deploy_shadow` only for READ/INTERNAL_WRITE); `release.*`/`infrastructure.apply` need PRODUCTION_VERIFIED (PL-008). Emitted alongside UNSUPPORTED_STEP_TYPE/UNKNOWN_CAPABILITY when no capability binds |
| `ARTIFACT_KIND_UNSUPPORTED` | CAPABILITY_UNSUPPORTED | every step output kind is in a bound capability's `produces`, every input kind in its `consumes` (PL-007) |
| `INPUT_UNRESOLVED` | STATE_CONFLICT | input from_step must be in depends_on and produce that output name (PL-015) |
| `INPUT_KIND_MISMATCH` | STATE_CONFLICT | input kind == producing output kind / plan input kind |
| `MISSING_ARTIFACT` | STATE_CONFLICT | plan_input name not in plan.inputs |
| `PRECONDITION_MISSING` | STATE_CONFLICT | `infrastructure.apply` consumes an InfrastructurePreview from a depended-on `infrastructure.preview` step and an ApprovalRecord (PL-045) |
| `UNVERIFIABLE_PREREQUISITE` | VERIFICATION_FAILED | a required step depends on an optional step or on `dependency.raise` without being optional itself (PL-015, PL-016) |
| `TENANT_MISMATCH` | SCOPE_DENIED | plan.tenant_id == envelope.tenant_id |
| `ENVELOPE_MISMATCH` | POLICY_STALE | plan.envelope_id/version == envelope (PL-005) |
| `ENVELOPE_INACTIVE` | POLICY_STALE | envelope expired at `now`/planned_at, or revoked at all (PL-005) |
| `GOAL_NOT_AUTHORIZED` | SCOPE_DENIED | plan.goal_id is one of envelope.goals; the plan input referencing the envelope carries its kind and current digest (PL-005) |
| `SCOPE_EXCEEDED` | SCOPE_DENIED | step.scope within envelope scope (sources, destinations, processors, regions); `StepInput.source_ids` must be a subset of the producer's effective sources (PL-005) |
| `EFFECT_CLASS_DENIED` | SCOPE_DENIED | step.effect_class ∈ envelope.allowed_effect_classes and ⊆ registry capability effect classes |
| `PURPOSE_DENIED` | PURPOSE_DENIED | for each source the step touches, declared **or inherited through lineage** (data-bearing artifact kinds flowing in from upstream steps, narrowed by `StepInput.source_ids`), step.purposes ⊆ envelope.purposes_for(source, at); TRAIN/EXPORT never inferred from INSPECT/COLLECT and never allowed without a source; a step with only inherited sources and no declared purposes is skipped (PL-053) |
| `BUDGET_EXCEEDED` | BUDGET_EXCEEDED | nested in every dimension: Σ step worst-case spend ≤ plan.total_budget.spend ≤ envelope.spending_limit (currency consistent); Σ step `max_model_calls` ≤ plan; each step `max_elapsed_seconds` ≤ plan; `details.dimension` names the dimension (PL-058) |
| `ATTEMPTS_EXCEEDED` | BUDGET_EXCEEDED | step.budget.max_attempts ≤ envelope.per_step_attempt_limit and ≤ plan.total_budget.max_attempts (`details.plan_max_attempts`) (PL-018) |
| `MISSING_VERIFICATION` | VERIFICATION_FAILED | each step (except `dependency.raise`) has ≥1 verification obligation; steps with external effects need ≥ INTEGRATION_BEHAVIOR; `release.*` needs an obligation at exactly BUSINESS_OUTCOME (ECONOMIC_RESULT does not substitute) (PL-016, PL-043) |
| `DEPLOYMENT_ENV_DENIED` | SCOPE_DENIED | infrastructure/release steps declare `environment` within envelope.deployment_environments |

`CheckReport.ok` is true iff no finding of severity `ERROR`. `CheckReport.topological_order` is populated when the graph is acyclic; `summary.inherited_sources` lists the lineage-derived sources per step. The checker never executes anything. `BuildStep.environment` is an ERROR when missing on `release.*`/`infrastructure.apply` and a WARNING on `infrastructure.preview`. `BuildStep.step_type` is not validated against the registry at the model level by design; `plan_id` is not forced to equal `artifact_id`.

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
    input_snapshot_refs: list[NonSecretIdentifier] # evidence event ids
    input_availability_time: AwareDatetime | None  # max availability time among inputs
    decision_time: AwareDatetime
    target_evidence_ref: NonSecretIdentifier | None
    target_availability_time: AwareDatetime | None
    label_kind: LabelKind
    label_status: LabelStatus
    purpose_authorization_ref: NonSecretIdentifier   # a SourceGrant id (explicit grant_id or grant:<source>:<policy>)
    split: Literal["train","validation","test_temporal","test_client_disjoint"]
    exclusion_reason: str | None          # required when label_status != ACCEPTED

class DatasetManifest(ArtifactHeader):
    dataset_id, revision:int, task_definition_ref, label_definition, split_rules: list[SplitRule]
    (name, question_answered, rule), schema_ref, rows: list[DatasetRow], counts (by split, by label status),
    distributions, content_hashes, source_versions: list[ArtifactRef] (pinned), source_ids: list[Identifier] (the
    sources the rows were drawn from), transformation_refs, lineage_refs, availability: `unavailable_reason: str|None`,
    source_rights_refs (the grant ids the rows may cite); counts are typed dict[SplitName,int] / dict[LabelStatus,int];
    task_definition_ref is an ArtifactRef of kind TASK_DEFINITION
```

`check_dataset(manifest, envelope=None, *, now=None)` emits: `FUTURE_INFORMATION` (input_availability_time > decision_time), `TARGET_LEAK` (the name the implementation uses for the leak finding; an OBSERVED_OUTCOME known before the decision is fine; a CORRECTION or EXPERT_DECISION target available before decision_time is a leak), `UNKNOWN_AVAILABILITY` (WARNING: missing availability) plus one `FAITHFUL_REPLAY_NOT_CLAIMABLE` (INFO summary) when any availability is unknown, `MISSING_TARGET_EVIDENCE`, `DUPLICATE_EXAMPLE_ID`, `DUPLICATE_FAMILY_ACROSS_SPLITS` (same group_id in >1 split), `TEMPORAL_HOLDOUT_NOT_LATER` (a test_temporal decision not later than every training decision), `QUARANTINED_ROW_IN_TRAINING` (non-ACCEPTED label in train split), `LABEL_KIND_MISMATCH` (row label kind ≠ manifest label definition), `WEAK_PROXY_IN_TRAINING` (WARNING), `MISSING_EXCLUSION_REASON`, `UNPINNED_SOURCE` (source_versions empty or without digest), `COUNT_MISMATCH` (declared counts ≠ rows), `SPLIT_WITHOUT_QUESTION`. Error class DATA_QUALITY_FAILED for all of these (PL-026..PL-030). `DISALLOWED_SOURCE_USE` (PURPOSE_DENIED, PL-053) fires when a row cites an authorization the manifest does not carry (`details.cause = not_in_manifest`) and, when an envelope is supplied, when a cited grant is unknown or inactive at `now`, belongs to another tenant, does not grant the row's purpose (TRAIN for train/validation, EVALUATE for the test splits) or names a source outside `source_ids` (`cause` ∈ {tenant_mismatch, unknown_grant, source_without_grant, purpose_not_granted, source_not_declared}). `CheckReport.subject` is `manifest.artifact_id`; `summary` carries `available`, `envelope_checked`, `weak_proxy_rows`, dataset id and revision; `unavailable_reason` is reported, not judged.

### Approval and release checkers

`check_approval(approval, *, subject_digest, tenant_id, policy_version, case_version=None, now, decision_kind=None)` judges one persisted `ApprovalRecord` against what it is used to authorize (every code is severity ERROR):

| code | error_class | rule |
|------|-------------|------|
| `APPROVAL_NOT_HUMAN` | AUTH_REQUIRED | approver is not a human principal (defensive: judged on content even for `model_construct` records) (PL-040) |
| `APPROVAL_AGENT_SUPPLIED` | AUTH_REQUIRED | the record was produced by a build or runtime agent (PL-040) |
| `APPROVAL_CASE_VERSION_MISSING` | STATE_CONFLICT | a CASE_LEVEL_BUSINESS approval carries no `case_version` (PL-040) |
| `APPROVAL_WRONG_DECISION_KIND` | SCOPE_DENIED | `decision_kind` differs from the decision the approval is used for (data use, implement/operate and case-level business approvals are distinct, PL-041) |
| `APPROVAL_DIGEST_MISMATCH` | SCOPE_DENIED | `subject_digest` is not the digest being authorized (PL-040) |
| `APPROVAL_TENANT_MISMATCH` | SCOPE_DENIED | `scope_tenant` differs (PL-040) |
| `APPROVAL_POLICY_STALE` | POLICY_STALE | decided under another policy version (PL-040) |
| `APPROVAL_CASE_VERSION_MISMATCH` | STATE_CONFLICT | bound to a different case version (PL-040) |
| `APPROVAL_NOT_YET_EFFECTIVE` | STATE_CONFLICT | evaluated before `approved_at` |
| `APPROVAL_EXPIRED` | POLICY_STALE | evaluated at or after `expires_at` (PL-041) |
| `APPROVAL_REVOKED` | POLICY_STALE | evaluated at or after `revoked_at` (PL-041) |

`check_release(manifest, attestations, approvals, *, now, current_policy_version)` matches records to the manifest by their *recomputed* digest (`compute_artifact_digest`), never by the `content_digest` they declare; an attestation is *accepted* for a component only when the manifest references it, a VERIFIER (not an agent) issued it, it passed, its input digest is the component's digest and it was produced in the release scope. Verification levels are read from the checks that passed, never from the declared `level` field. Codes (ERROR unless stated):

| code | error_class | rule |
|------|-------------|------|
| `ARTIFACT_DIGEST_INCONSISTENT` | VERIFICATION_FAILED | a supplied attestation or approval declares a `content_digest` that is not the digest of its own bytes (PL-040, PL-046) |
| `ATTESTATION_DIGEST_MISMATCH` | VERIFICATION_FAILED | an `attestation_ref` names no supplied attestation, or an attestation's input digest matches no component (PL-046) |
| `ATTESTATION_SCOPE_MISMATCH` | VERIFICATION_FAILED | environment not a rollout environment, tenant differs, or release scope not covered (PL-046) |
| `ATTESTATION_NOT_INDEPENDENT` | VERIFICATION_FAILED | produced by a build/runtime agent or its verifier is not a VERIFIER (PL-042) |
| `ATTESTATION_FAILED` | VERIFICATION_FAILED | attestation result is FAIL (PL-042) |
| `ATTESTATION_MISSING` | VERIFICATION_FAILED | a present component has no accepted attestation for its digest (PL-046) |
| `ENVIRONMENT_NOT_VERIFIED` | VERIFICATION_FAILED | a rollout stage's environment has no accepted attestation at INTEGRATION_BEHAVIOR or higher (PL-043, PL-046) |
| `MISSING_VERIFICATION_LEVEL` | VERIFICATION_FAILED | no accepted passing check at INTEGRATION_BEHAVIOR, or none at BUSINESS_OUTCOME (PL-043) |
| `HELD_OUT_EVALUATION_MISSING` | VERIFICATION_FAILED | a model or workflow component is present but the evaluation component is omitted (PL-034, PL-043) |
| `OPERATING_PLAN_MISSING` | VERIFICATION_FAILED | no operating plan, or a PL-048 signal without a monitor (PL-043, PL-048) |
| `APPROVAL_INVALID` | per `check_approval` | an `approval_ref` is not supplied, or `check_approval` rejects it for `approval_subject_digest()`, the tenant, `current_policy_version` and the IMPLEMENT_OPERATE decision (PL-040, PL-041) |
| `MODEL_ALIAS_UNRESOLVED` | STATE_CONFLICT | model component present without an immutable `resolved_model_version` (PL-034, ADR-008) |
| `ADVERSARIAL_TESTS_MISSING` | VERIFICATION_FAILED (WARNING) | no accepted attestation has a passing check named `adversarial*` (PL-043, PL-061); a warning because the rule is enforced by name |

`summary` carries `accepted_attestations`, `behaviourally_verified_environments` and `unreferenced_attestations` (unreferenced records are never evidence).

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
    idempotency_key: str                # sha256 hex derived from action_id, not from payload
    supersedes_action_id: Identifier | None
    # effect_class READ is rejected: a read is not an external effect
```

`ActionReceipt` requires `external_id` or a `postcondition_probe`; its `provider_request_id`, when given, must equal the one the ledger recorded. `ReconciliationResult.evidence` is non-empty for every outcome. `RejectionEvidence` (provider_request_id, raw_response_digest, `provider_confirmed_absent` must be true, detail, observed_at) is what a DISPATCHED → FAILED_FINAL transition needs.

`EffectLedger(path)` (SQLite, WAL) with methods:

* `reserve(intent) -> ReservationResult` — inserts row in RESERVED; **same slot key with same payload digest returns the existing action (idempotent)**; **same slot key with different payload digest raises `PayloadConflict` (PAYLOAD_CONFLICT) unless `intent.supersedes_action_id` names the existing action and that action is in a terminal state or explicitly superseded** (PL-037).
* `reserve(intent, *, reason=...)` also raises `TargetConflict` when the same slot is reserved for a different provider target or deployment version and `ActionIdConflict` when the action id is already bound to another slot; the result carries `created`, `authority_matches`, `state_version_matches` and `superseded_action_id`.
* `mark_dispatched(action_id, lease_owner, provider_request_id=None, *, reason)` — RESERVED→DISPATCHED, records lease and (optionally) the request id (PL-057). `record_provider_request(action_id, provider_request_id, *, reason)` binds the id after dispatch; a second, different id raises `ReceiptMismatch`.
* `mark_unknown(action_id, reason)` — DISPATCHED→UNKNOWN on timeout/ambiguous outcome; **a timeout is never treated as "nothing happened"** (PL-038).
* `reconcile(action_id, result: ReconciliationResult, *, reason=None)` — UNKNOWN→CONFIRMED (requires external receipt/postcondition), UNKNOWN→FAILED_FINAL (requires provider-confirmed non-occurrence), STILL_UNKNOWN stays UNKNOWN but is recorded as a RECONCILIATION_ATTEMPT row and bumps `state_version`; **retry is refused while UNKNOWN** (`EffectUnknown` error, EFFECT_UNKNOWN).
* `confirm(action_id, receipt, *, reason)` — DISPATCHED→CONFIRMED, receipt required; a receipt whose `provider_request_id` differs from the recorded one raises `ReceiptMismatch`.
* `fail_final(action_id, reason, *, evidence: RejectionEvidence)` — DISPATCHED→FAILED_FINAL only with provider rejection evidence; `compensate(action_id, compensation_receipt, *, reason)` — CONFIRMED→COMPENSATED, the original receipt is retained.
* `outstanding(tenant_id=None)` — list of DISPATCHED/UNKNOWN effects (restart reconciliation list, PL-039). `find_by_slot(slot)` returns the live slot holder only; `slot_history(slot)` returns every row that ever held the slot.
* Every mutation requires a non-empty `reason` (`MissingReason`), bumps `state_version` and persists `(event, from_state, to_state, reason, at)` in `effect_transitions`; `event` ∈ {TRANSITION, SUPERSEDED, RECONCILIATION_ATTEMPT, PROVIDER_REQUEST_RECORDED}. All instants are normalised to UTC.
* Columns beyond the intent: `state`, `state_version`, `lease_owner`, `provider_request_id`, `receipt_json`, `rejection_json`, `compensation_receipt_json`, `superseded_by_action_id` (a deferred self-reference; **slot uniqueness is the partial unique index on `slot_key WHERE superseded_by_action_id IS NULL`**, there is no slot-key suffix convention). `EffectRow.is_slot_holder` reflects it.
* Deduplication survives process restart: reopening the same file and reserving the same slot returns the same action (PL-039). Dedup is independent of `deployment_version` (same slot across releases is the same business action).

## 7. State machines

`plumb.statemachines.machines` exposes `BUILD`, `BUILD_STEP`, `COLLECTOR`, `DATASET`, `TRAINING`, `RELEASE`, `EFFECT` machines, each an instance of
`StateMachine(name, states_enum, transitions: dict[(from,to)] -> Guard | None)`. `machine.transition(current, target, context: dict, reason: str) -> Transition` raises `IllegalTransition` (STATE_CONFLICT) when the edge is absent and `GuardFailed` (a subclass of `IllegalTransition`, carrying the guard name) when a guard rejects; an empty reason raises `MissingReason`. Guards are built from `flag(*keys)` (exactly `True`), `present(key)` (truthy), `equals(key, value)` and `all_of(...)`. Guards fixed by spec:

* Build → VERIFIED requires `context["required_steps_verified"] is True`.
* Release → ACTIVE requires `context["authority_current"]` and `context["attestations_accepted"]`.
* Effect DISPATCHED → CONFIRMED requires `context["external_receipt"]` (truthy); DISPATCHED → FAILED_FINAL requires `context["rejection_evidence"]`; CONFIRMED → COMPENSATED requires `context["compensation_receipt"]`.
* Effect UNKNOWN → CONFIRMED requires `reconciliation_result == "CONFIRMED"` and an `external_receipt`; UNKNOWN → FAILED_FINAL requires `reconciliation_result == "FAILED_FINAL"` and `provider_confirmed_absent is True`.
* Training PLANNED → SUBMITTED requires `submission_identity_persisted`; Collector PAUSED → ACTIVE requires `coverage_restored`; build-step repair edges are bounded by the repair-budget guard.
* Build step → VERIFIED requires `context["verifier_attestation"]` (a worker's claim is not enough).
* Dataset → VERIFIED requires `context["checker_ok"]`.
* Terminal states have no outgoing edges: Build VERIFIED, FAILED and CANCELLED are terminal; Effect CONFIRMED→COMPENSATED is allowed, FAILED_FINAL and COMPENSATED are terminal; Release RETIRED is terminal.

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
`revokeEnvelope` is deliberately not an operation: revocation is modelled as a new envelope version created with `If-Match`, so the document has exactly 24 operations. Components reference the generated JSON Schemas conceptually but must be **self-contained** in the document (`#/components/schemas/...`), with `x-plumb-contract: <ContractName>` annotations linking to `schemas/<ContractName>.json`; `x-plumb-result-contract` on a 202 operation names the contract its `JobEnvelope.result_ref` produces (both extensions are validated by `api/validate_openapi.py`). Annotated components mirror their Pydantic model field for field (properties, required lists, enums and leaf constraints; `tests/test_openapi.py` compares them). `JobStatus` is the vocabulary of `plumb.contracts.api.JobStatus`; `ConnectionIntentState` (PENDING_CONSENT, CONSENTED, DENIED, EXPIRED) exists only at the API level because no Pydantic contract models a connection intent. The document resolves far more than Appendix C's 103 local references because scalar types are shared components; `VALIDATION_REPORT.md` reports the measured count.

## 9. SQL design migration

Tables (schema `plumb`): `tenants`, `envelopes`, `source_grants`, `capabilities`, `artifacts`, `evidence_events`, `objects`, `object_links`, `facts`, `goals`, `opportunities`, `builds`, `build_steps`, `build_step_attempts`, `collectors`, `datasets`, `dataset_rows`, `training_jobs`, `evaluations`, `approvals`, `releases`, `cases`, `effects`, `effect_transitions`, `outbox`, `processed_events`, `jobs`, `outcome_observations`, `human_effort`. The `effects` and `effect_transitions` tables mirror the SQLite ledger column for column (`state_version` = the ledger's `state_version`, `superseded_by_action_id` as a deferred self-reference with the partial unique slot index, `rejection_response_digest`, `compensation_receipt_digest`, the `event` and `guard` columns and the non-blank `reason` check); `jobs.status` is the `JobStatus` vocabulary. The migration targets PostgreSQL 15+ and has never been executed here. Composite `(tenant_id, <id>)` primary keys; FKs include tenant_id; indexes for case lookups, external source identity, job readiness (`build_steps(tenant_id, build_id, state) WHERE state='READY'`), outstanding effects (`effects(tenant_id, state) WHERE state IN ('DISPATCHED','UNKNOWN')`); unique `effects(tenant_id, slot_key) WHERE superseded_by_action_id IS NULL`; RLS enabled with the explicit comment that owner/superuser bypass remains (PL-052); separate roles `plumb_app`, `plumb_migrator`, `plumb_platform_admin`.

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
isolation, grants, deployment, prospective_outcome, model, training; each defined in the
header's `requires_definitions`), `locally_executed: false`, and `local_reference_check`
(a test name or checker finding code in this package, or `null` when the package has no
analogue, as for PA-021 and PA-026). The header carries `catalog_version`,
`generated_for_spec`, `spec_date`, `title`, `executed_against_production: false`,
`production_execution_note`, `severity_definitions`, `requires_definitions`,
`category_definitions` and `scenario_domains`. Severity is graded by the scenario's
blast radius: two scenarios are MEDIUM (PA-024, PA-027) and one LOW (PA-030). PL-050 is
covered through PA-027 (M5 replication) rather than a dedicated scenario because the count
is fixed at 30.
The nine mandatory PL-061 categories must each appear at least once, and the
Appendix B failure cases (wrong client, ambiguous period, already-received
document, corrected statement, duplicate request, expired permission, provider
timeout after send, changed approval, stale source) must all appear.
