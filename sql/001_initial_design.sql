-- =============================================================================
-- Plumb Autonomous Implementation System -- PostgreSQL DESIGN migration 001
-- =============================================================================
--
-- STATUS: DESIGN MIGRATION. This file has NOT been executed against PostgreSQL
-- in the environment that produced the reference package (specification
-- section 23, Appendix C). Production review must check grants, transaction
-- isolation, migration tooling, indexes and workload behaviour before use.
-- The local simulation uses SQLite only for the smaller effect-ledger contract
-- (plumb/ledger) and must not be mistaken for this persistence design.
--
-- Requirements implemented:
--   PL-052  tenant isolation on database queries: every tenant table carries
--           tenant_id, ENABLE + FORCE ROW LEVEL SECURITY and a policy keyed on
--           current_setting('plumb.tenant_id', true). Platform, migration and
--           ordinary service roles are separated (plumb_platform_admin,
--           plumb_migrator, plumb_app).
--           ISOLATION CAVEAT: PostgreSQL row security has owner/superuser
--           exceptions. Superusers and roles with BYPASSRLS bypass every policy;
--           FORCE ROW LEVEL SECURITY makes policies apply to the table owner but
--           not to superusers. Merely enabling RLS is therefore NOT a complete
--           isolation design; object storage, caches, search, workspaces, logs
--           and exports need their own controls.
--   PL-057  authoritative state transitions are transactional, versioned
--           (row_version compare-and-set) and auditable (effect_transitions,
--           build_step_attempts). A worker lease is never the only record that
--           an external action was attempted: the effects row is written
--           before dispatch.
--   PL-055  jobs(tenant_id, idempotency_key) is unique and stores the payload
--           digest so a repeated key with a different payload is a conflict.
--   PL-037..PL-039  effects(tenant_id, slot_key) is unique; payload digest and
--           logical action id are stored separately; dedup is independent of
--           the release (deployment_version is not part of the slot).
--   Section 22  outbox + processed_events implement at-least-once delivery with
--           consumer deduplication (processed_events PK (consumer, event_id)).
--   Section 23  state columns are CHECK-constrained to the exact lifecycles.
--   PL-003/PL-059  human_effort and outcome_observations record effort by
--           category and distinguish model calls, completed cases, correct
--           outcomes and realized value.
--
-- Conventions:
--   * Composite (tenant_id, id) primary keys where practical; every foreign key
--     between tenant tables includes tenant_id so a row can never point into
--     another tenant.
--   * No secret values are stored: *_ref columns hold references resolved by
--     the gateway (PL-054).
--   * Partitioning: large append-only tables (evidence_events, outbox,
--     effect_transitions, dataset_rows) are candidates for range partitioning
--     by recorded_at AFTER measured need, not by default (section 23). No
--     partitioning is declared here.
--   * Timestamps are TIMESTAMPTZ. Money is BIGINT minor units + CHAR(3)
--     currency; never floating point (section 10).
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- Roles (PL-052): separated platform, migration and service roles.
-- Role creation is cluster-wide; guarded so the migration is re-runnable.
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'plumb_migrator') THEN
        -- Owns the schema and runs migrations. FORCE RLS applies to it as owner.
        CREATE ROLE plumb_migrator NOLOGIN NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'plumb_app') THEN
        -- Ordinary service role. Subject to RLS; must SET plumb.tenant_id per transaction.
        CREATE ROLE plumb_app NOLOGIN NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'plumb_platform_admin') THEN
        -- Audited cross-tenant operations (retention, support). The only role
        -- intended to bypass RLS; never used by build or runtime agents (PL-006).
        CREATE ROLE plumb_platform_admin NOLOGIN NOINHERIT BYPASSRLS;
    END IF;
END
$$;

CREATE SCHEMA IF NOT EXISTS plumb AUTHORIZATION plumb_migrator;
SET LOCAL search_path TO plumb, public;

-- -----------------------------------------------------------------------------
-- Domains mirroring plumb.contracts.common constrained scalars
-- -----------------------------------------------------------------------------
CREATE DOMAIN plumb.tenant_id AS TEXT
    CHECK (VALUE ~ '^tnt_[a-z0-9]{4,32}$');
CREATE DOMAIN plumb.identifier AS TEXT
    CHECK (VALUE ~ '^[a-z][a-z0-9_.:/-]{0,159}$');
CREATE DOMAIN plumb.sha256_digest AS TEXT
    CHECK (VALUE ~ '^sha256:[0-9a-f]{64}$');
CREATE DOMAIN plumb.semver AS TEXT
    CHECK (VALUE ~ '^[0-9]+\.[0-9]+\.[0-9]+$');
CREATE DOMAIN plumb.currency_code AS CHAR(3)
    CHECK (VALUE ~ '^[A-Z]{3}$');

-- -----------------------------------------------------------------------------
-- Helper: optimistic concurrency. Bumps row_version and updated_at on UPDATE
-- (PL-056 If-Match, PL-057 versioned transitions). Services issue
--   UPDATE ... WHERE tenant_id = $1 AND id = $2 AND row_version = $expected
-- and treat zero affected rows as a stale version (HTTP 412).
-- -----------------------------------------------------------------------------
CREATE FUNCTION plumb.bump_row_version() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    NEW.row_version := OLD.row_version + 1;
    NEW.updated_at := now();
    RETURN NEW;
END
$$;

-- =============================================================================
-- Platform-level tables (no tenant_id; not subject to tenant RLS)
-- =============================================================================

CREATE TABLE plumb.tenants (
    id              plumb.tenant_id PRIMARY KEY,
    display_name    TEXT        NOT NULL,
    home_region     TEXT        NOT NULL CHECK (home_region ~ '^[a-z]{2,3}(-[a-z0-9]+)*$'),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    suspended_at    TIMESTAMPTZ
);
COMMENT ON TABLE plumb.tenants IS 'Platform registry of tenants. Tenant identity is derived from verified authentication, never from a request body (PL-004).';

CREATE TABLE plumb.capabilities (
    id                  plumb.identifier PRIMARY KEY,
    step_type           plumb.identifier NOT NULL,
    provider            TEXT        NOT NULL,
    operation           TEXT        NOT NULL,
    maturity            TEXT        NOT NULL CHECK (maturity IN ('DISCOVERED', 'DOCUMENTED', 'SANDBOX_TESTED', 'PRODUCTION_VERIFIED')),
    effect_classes      TEXT[]      NOT NULL CHECK (effect_classes <@ ARRAY['READ', 'INTERNAL_WRITE', 'EXTERNAL_WRITE_REVERSIBLE', 'EXTERNAL_WRITE_IRREVERSIBLE', 'EXTERNAL_COMMUNICATION', 'FINANCIAL_COMMITMENT', 'INFRASTRUCTURE_CHANGE', 'DESTRUCTIVE']::TEXT[]),
    required_purposes   TEXT[]      NOT NULL CHECK (required_purposes <@ ARRAY['INSPECT', 'COLLECT', 'TRANSFORM', 'EVALUATE', 'TRAIN', 'SERVE', 'EXPORT']::TEXT[]),
    required_authority  TEXT[]      NOT NULL DEFAULT '{}',
    tested_environment  TEXT,
    maintenance_burden  TEXT        NOT NULL CHECK (maintenance_burden IN ('LOW', 'MEDIUM', 'HIGH')),
    produces            TEXT[]      NOT NULL DEFAULT '{}',
    consumes            TEXT[]      NOT NULL DEFAULT '{}',
    probe_receipt_ref   TEXT,
    capability_version  plumb.semver NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE plumb.capabilities IS 'Platform capability registry (PL-007, PL-008). Discovered, documented, sandbox-tested and production-verified are distinct maturities.';

-- =============================================================================
-- Tenant tables. Every table below carries tenant_id and is RLS-protected.
-- =============================================================================

-- Artifacts: immutable, digest-addressed records (section 8). Content lives in
-- object storage; this table stores the header and the storage reference only.
CREATE TABLE plumb.artifacts (
    tenant_id               plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                      plumb.identifier NOT NULL,
    version                 INTEGER     NOT NULL CHECK (version >= 1),
    kind                    TEXT        NOT NULL CHECK (kind IN (
                                'AutonomyEnvelope', 'CapabilityRecord', 'EnvironmentInventory', 'EvidencePacket',
                                'OpportunitySpec', 'BuildPlan', 'IntegrationSpec', 'CollectionSpec', 'DatasetManifest',
                                'TrainingSpec', 'WorkflowSpec', 'EvaluationReport', 'InfrastructurePlan',
                                'ReleaseManifest', 'ActionIntent', 'ApprovalRecord', 'VerificationAttestation',
                                'AdapterCode', 'AdapterConfiguration', 'TransformationCode', 'TestBundle',
                                'ProbeReceipt', 'VerificationReceipt', 'QualityReport', 'LabelAuditReport',
                                'SourceCandidateTable', 'TaskDefinition', 'ModelVersion', 'ServingConfiguration',
                                'CandidateComparison', 'InfrastructurePreview', 'CanaryReport', 'DependencyRecord',
                                'ReviewPackage')),
    schema_version          plumb.semver NOT NULL,
    content_digest          plumb.sha256_digest NOT NULL,
    producer_principal_id   plumb.identifier NOT NULL,
    producer_principal_type TEXT        NOT NULL CHECK (producer_principal_type IN ('HUMAN_OWNER', 'HUMAN_REVIEWER', 'HUMAN_APPROVER', 'SERVICE', 'BUILD_AGENT', 'RUNTIME_AGENT', 'VERIFIER', 'RELEASE_EXECUTOR')),
    storage_ref             TEXT        NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id, version),
    UNIQUE (tenant_id, content_digest)
);
COMMENT ON TABLE plumb.artifacts IS 'Immutable artifact headers. plumb_app may INSERT and SELECT only; a verified artifact can never be replaced under the same identifier (section 19).';
CREATE INDEX artifacts_kind_idx ON plumb.artifacts (tenant_id, kind, created_at);

-- Envelopes (PL-005). One row per envelope id; the current version is pinned by
-- artifact id/version and superseded through compare-and-set on row_version.
CREATE TABLE plumb.envelopes (
    tenant_id                   plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                          plumb.identifier NOT NULL,
    envelope_version            INTEGER     NOT NULL CHECK (envelope_version >= 1),
    artifact_id                 plumb.identifier NOT NULL,
    artifact_version            INTEGER     NOT NULL,
    owner_principal_id          plumb.identifier NOT NULL,
    policy_version              plumb.semver NOT NULL,
    spending_limit_minor_units  BIGINT      NOT NULL CHECK (spending_limit_minor_units >= 0),
    spending_limit_currency     plumb.currency_code NOT NULL,
    per_step_attempt_limit      INTEGER     NOT NULL CHECK (per_step_attempt_limit BETWEEN 1 AND 1000),
    expires_at                  TIMESTAMPTZ NOT NULL,
    revoked_at                  TIMESTAMPTZ,
    row_version                 BIGINT      NOT NULL DEFAULT 1,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, artifact_id, artifact_version) REFERENCES plumb.artifacts (tenant_id, id, version)
);
CREATE TRIGGER envelopes_row_version BEFORE UPDATE ON plumb.envelopes
    FOR EACH ROW EXECUTE FUNCTION plumb.bump_row_version();

-- Source grants (PL-053): actual customer grants per source and purpose, never a
-- tenant-wide checkbox. TRAIN is never inferred from INSPECT/COLLECT.
CREATE TABLE plumb.source_grants (
    tenant_id               plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                      plumb.identifier NOT NULL,
    envelope_id             plumb.identifier NOT NULL,
    source_id               plumb.identifier NOT NULL,
    purposes                TEXT[]      NOT NULL CHECK (cardinality(purposes) >= 1 AND purposes <@ ARRAY['INSPECT', 'COLLECT', 'TRANSFORM', 'EVALUATE', 'TRAIN', 'SERVE', 'EXPORT']::TEXT[]),
    granted_by_principal_id plumb.identifier NOT NULL,
    granted_at              TIMESTAMPTZ NOT NULL,
    expires_at              TIMESTAMPTZ,
    revoked_at              TIMESTAMPTZ,
    policy_version          plumb.semver NOT NULL,
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, envelope_id) REFERENCES plumb.envelopes (tenant_id, id)
);
CREATE INDEX source_grants_source_idx ON plumb.source_grants (tenant_id, source_id, envelope_id);

-- Evidence events (PL-009..PL-011): raw observations with separate time axes.
CREATE TABLE plumb.evidence_events (
    tenant_id           plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                  plumb.identifier NOT NULL,
    source_id           plumb.identifier NOT NULL,
    external_record_id  TEXT        NOT NULL,
    external_version    TEXT        NOT NULL,
    event_time          TIMESTAMPTZ NOT NULL,
    observation_time    TIMESTAMPTZ NOT NULL,
    availability_time   TIMESTAMPTZ NOT NULL,
    content_digest      plumb.sha256_digest NOT NULL,
    raw_content_ref     TEXT        NOT NULL,
    access_policy_ref   TEXT        NOT NULL,
    retention_class     TEXT        NOT NULL,
    extraction_version  plumb.semver NOT NULL,
    recorded_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    CONSTRAINT evidence_events_availability_after_observation CHECK (availability_time >= observation_time)
);
COMMENT ON TABLE plumb.evidence_events IS 'Append-only. Candidate for range partitioning on recorded_at after measured need (section 23).';
-- External source identity: the same source record/version is stored once.
CREATE UNIQUE INDEX evidence_events_external_identity_idx
    ON plumb.evidence_events (tenant_id, source_id, external_record_id, external_version);
CREATE INDEX evidence_events_availability_idx
    ON plumb.evidence_events (tenant_id, source_id, availability_time);

-- Business objects and resolution history (PL-011).
CREATE TABLE plumb.objects (
    tenant_id               plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                      plumb.identifier NOT NULL,
    object_type             plumb.identifier NOT NULL,
    canonical_key           TEXT        NOT NULL,
    resolution_version      INTEGER     NOT NULL DEFAULT 1 CHECK (resolution_version >= 1),
    merged_into_object_id   plumb.identifier,
    split_from_object_id    plumb.identifier,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    superseded_at           TIMESTAMPTZ,
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, merged_into_object_id) REFERENCES plumb.objects (tenant_id, id),
    FOREIGN KEY (tenant_id, split_from_object_id) REFERENCES plumb.objects (tenant_id, id)
);
CREATE INDEX objects_canonical_key_idx ON plumb.objects (tenant_id, object_type, canonical_key);

CREATE TABLE plumb.object_links (
    tenant_id           plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                  plumb.identifier NOT NULL,
    object_id           plumb.identifier NOT NULL,
    evidence_event_id   plumb.identifier NOT NULL,
    link_kind           plumb.identifier NOT NULL,
    confidence          NUMERIC(5, 4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    UNIQUE (tenant_id, object_id, evidence_event_id, link_kind),
    FOREIGN KEY (tenant_id, object_id) REFERENCES plumb.objects (tenant_id, id),
    FOREIGN KEY (tenant_id, evidence_event_id) REFERENCES plumb.evidence_events (tenant_id, id)
);
CREATE INDEX object_links_evidence_idx ON plumb.object_links (tenant_id, evidence_event_id);

-- Derived facts (PL-010): closed status vocabulary; unknown absence stays
-- distinguishable from confirmed absence; confidence is not authority.
CREATE TABLE plumb.facts (
    tenant_id               plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                      plumb.identifier NOT NULL,
    object_id               plumb.identifier NOT NULL,
    fact_type               plumb.identifier NOT NULL,
    value                   JSONB       NOT NULL,
    status                  TEXT        NOT NULL CHECK (status IN ('OBSERVED', 'INFERRED', 'CONFIRMED', 'DISPUTED', 'STALE', 'SUPERSEDED')),
    presence                TEXT        NOT NULL CHECK (presence IN ('PRESENT', 'CONFIRMED_ABSENT', 'UNKNOWN')),
    confidence              NUMERIC(5, 4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    derivation_version      plumb.semver NOT NULL,
    supporting_evidence_ids TEXT[]      NOT NULL CHECK (cardinality(supporting_evidence_ids) >= 1),
    valid_from              TIMESTAMPTZ NOT NULL,
    valid_to                TIMESTAMPTZ,
    superseded_by_fact_id   plumb.identifier,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, object_id) REFERENCES plumb.objects (tenant_id, id),
    FOREIGN KEY (tenant_id, superseded_by_fact_id) REFERENCES plumb.facts (tenant_id, id)
);
CREATE INDEX facts_object_type_idx ON plumb.facts (tenant_id, object_id, fact_type, valid_from);

-- Goals and opportunities (PL-005, PL-012, PL-013).
CREATE TABLE plumb.goals (
    tenant_id       plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id              plumb.identifier NOT NULL,
    envelope_id     plumb.identifier NOT NULL,
    objective       TEXT        NOT NULL CHECK (length(objective) > 0),
    success_metric  TEXT,
    horizon_days    INTEGER     CHECK (horizon_days IS NULL OR horizon_days >= 1),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, envelope_id) REFERENCES plumb.envelopes (tenant_id, id)
);

CREATE TABLE plumb.opportunities (
    tenant_id                       plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                              plumb.identifier NOT NULL,
    goal_id                         plumb.identifier NOT NULL,
    artifact_id                     plumb.identifier NOT NULL,
    artifact_version                INTEGER     NOT NULL,
    intervention_kind               TEXT        NOT NULL CHECK (intervention_kind IN ('NATIVE_SETTING', 'DETERMINISTIC_AUTOMATION', 'GENERAL_MODEL_WORKFLOW', 'SPECIALIST_SERVICE', 'RETRIEVAL_SYSTEM', 'TRAINED_COMPONENT', 'REMOVE_STEP')),
    expected_benefit_low_minor_units  BIGINT    NOT NULL CHECK (expected_benefit_low_minor_units >= 0),
    expected_benefit_high_minor_units BIGINT    NOT NULL CHECK (expected_benefit_high_minor_units >= expected_benefit_low_minor_units),
    benefit_currency                plumb.currency_code NOT NULL,
    benefit_horizon_days            INTEGER     NOT NULL CHECK (benefit_horizon_days >= 1),
    failure_cost_minor_units        BIGINT      NOT NULL CHECK (failure_cost_minor_units >= 0),
    review_cost_minor_units         BIGINT      NOT NULL CHECK (review_cost_minor_units >= 0),
    selected_at                     TIMESTAMPTZ,
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, goal_id) REFERENCES plumb.goals (tenant_id, id),
    FOREIGN KEY (tenant_id, artifact_id, artifact_version) REFERENCES plumb.artifacts (tenant_id, id, version)
);
CREATE INDEX opportunities_goal_idx ON plumb.opportunities (tenant_id, goal_id, created_at);

-- Builds (section 23 lifecycle; PL-014..PL-019; PL-058 reservations).
CREATE TABLE plumb.builds (
    tenant_id                   plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                          plumb.identifier NOT NULL,
    goal_id                     plumb.identifier NOT NULL,
    envelope_id                 plumb.identifier NOT NULL,
    envelope_version            INTEGER     NOT NULL CHECK (envelope_version >= 1),
    opportunity_id              plumb.identifier,
    plan_artifact_id            plumb.identifier NOT NULL,
    plan_artifact_version       INTEGER     NOT NULL,
    state                       TEXT        NOT NULL CHECK (state IN ('DRAFT', 'VALIDATED', 'RUNNING', 'WAITING_AUTH', 'WAITING_INPUT', 'VERIFYING', 'VERIFIED', 'FAILED', 'CANCELLED')),
    state_reason                TEXT        NOT NULL CHECK (length(state_reason) > 0),
    failure_class               TEXT        CHECK (failure_class IS NULL OR failure_class IN ('TRANSIENT_INFRASTRUCTURE', 'IMPLEMENTATION_DEFECT', 'SOURCE_SCHEMA_CHANGE', 'MISSING_AUTHORIZATION', 'MISSING_BUSINESS_DECISION', 'UNSUPPORTED_CAPABILITY', 'POOR_MODEL_QUALITY', 'EXHAUSTED_RESOURCES')),
    budget_spend_minor_units    BIGINT      NOT NULL CHECK (budget_spend_minor_units >= 0),
    budget_currency             plumb.currency_code NOT NULL,
    reserved_minor_units        BIGINT      NOT NULL DEFAULT 0 CHECK (reserved_minor_units >= 0),
    spent_minor_units           BIGINT      NOT NULL DEFAULT 0 CHECK (spent_minor_units >= 0),
    row_version                 BIGINT      NOT NULL DEFAULT 1,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, goal_id) REFERENCES plumb.goals (tenant_id, id),
    FOREIGN KEY (tenant_id, envelope_id) REFERENCES plumb.envelopes (tenant_id, id),
    FOREIGN KEY (tenant_id, opportunity_id) REFERENCES plumb.opportunities (tenant_id, id),
    FOREIGN KEY (tenant_id, plan_artifact_id, plan_artifact_version) REFERENCES plumb.artifacts (tenant_id, id, version),
    CONSTRAINT builds_reservation_within_budget CHECK (reserved_minor_units + spent_minor_units <= budget_spend_minor_units)
);
CREATE TRIGGER builds_row_version BEFORE UPDATE ON plumb.builds
    FOR EACH ROW EXECUTE FUNCTION plumb.bump_row_version();
CREATE INDEX builds_goal_state_idx ON plumb.builds (tenant_id, goal_id, state);

-- Build steps. Step ids repeat across builds, so the key is (tenant, build, step).
CREATE TABLE plumb.build_steps (
    tenant_id                       plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    build_id                        plumb.identifier NOT NULL,
    step_id                         plumb.identifier NOT NULL,
    step_type                       plumb.identifier NOT NULL,
    state                           TEXT        NOT NULL CHECK (state IN ('PENDING', 'READY', 'RUNNING', 'VERIFYING', 'VERIFIED', 'FAILED', 'BLOCKED', 'CANCELLED')),
    state_reason                    TEXT        NOT NULL CHECK (length(state_reason) > 0),
    required                        BOOLEAN     NOT NULL DEFAULT TRUE,
    effect_class                    TEXT        NOT NULL CHECK (effect_class IN ('READ', 'INTERNAL_WRITE', 'EXTERNAL_WRITE_REVERSIBLE', 'EXTERNAL_WRITE_IRREVERSIBLE', 'EXTERNAL_COMMUNICATION', 'FINANCIAL_COMMITMENT', 'INFRASTRUCTURE_CHANGE', 'DESTRUCTIVE')),
    max_attempts                    INTEGER     NOT NULL CHECK (max_attempts BETWEEN 1 AND 1000),
    attempt_count                   INTEGER     NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    verifier_attestation_artifact_id      plumb.identifier,
    verifier_attestation_artifact_version INTEGER,
    row_version                     BIGINT      NOT NULL DEFAULT 1,
    updated_at                      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, build_id, step_id),
    FOREIGN KEY (tenant_id, build_id) REFERENCES plumb.builds (tenant_id, id),
    FOREIGN KEY (tenant_id, verifier_attestation_artifact_id, verifier_attestation_artifact_version) REFERENCES plumb.artifacts (tenant_id, id, version),
    -- A worker's claim never makes a step VERIFIED; a verifier attestation does (Appendix A §2, PL-043).
    CONSTRAINT build_steps_verified_needs_attestation CHECK (state <> 'VERIFIED' OR verifier_attestation_artifact_id IS NOT NULL),
    CONSTRAINT build_steps_attempts_within_limit CHECK (attempt_count <= max_attempts)
);
CREATE TRIGGER build_steps_row_version BEFORE UPDATE ON plumb.build_steps
    FOR EACH ROW EXECUTE FUNCTION plumb.bump_row_version();
-- Job readiness: the scheduler selects READY steps per build (Appendix A §2).
CREATE INDEX build_steps_ready_idx ON plumb.build_steps (tenant_id, build_id, state) WHERE state = 'READY';

-- Build step attempts: lease / fencing record per attempt (PL-057, Appendix A §2).
-- The lease is never the only record of an external action; see effects.
CREATE TABLE plumb.build_step_attempts (
    tenant_id               plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                      plumb.identifier NOT NULL,
    build_id                plumb.identifier NOT NULL,
    step_id                 plumb.identifier NOT NULL,
    attempt_no              INTEGER     NOT NULL CHECK (attempt_no >= 1),
    lease_owner             TEXT        NOT NULL,
    lease_expires_at        TIMESTAMPTZ NOT NULL,
    fencing_token           BIGINT      NOT NULL,
    workspace_base_digest   plumb.sha256_digest,
    result_digest           plumb.sha256_digest,
    reserved_minor_units    BIGINT      NOT NULL CHECK (reserved_minor_units >= 0),
    actual_minor_units      BIGINT      CHECK (actual_minor_units IS NULL OR actual_minor_units >= 0),
    budget_currency         plumb.currency_code NOT NULL,
    outcome                 TEXT        NOT NULL DEFAULT 'RUNNING' CHECK (outcome IN ('RUNNING', 'PROPOSED', 'VERIFIED', 'FAILED', 'LEASE_EXPIRED', 'CANCELLED')),
    failure_class           TEXT        CHECK (failure_class IS NULL OR failure_class IN ('TRANSIENT_INFRASTRUCTURE', 'IMPLEMENTATION_DEFECT', 'SOURCE_SCHEMA_CHANGE', 'MISSING_AUTHORIZATION', 'MISSING_BUSINESS_DECISION', 'UNSUPPORTED_CAPABILITY', 'POOR_MODEL_QUALITY', 'EXHAUSTED_RESOURCES')),
    started_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at             TIMESTAMPTZ,
    PRIMARY KEY (tenant_id, id),
    UNIQUE (tenant_id, build_id, step_id, attempt_no),
    UNIQUE (tenant_id, build_id, step_id, fencing_token),
    FOREIGN KEY (tenant_id, build_id, step_id) REFERENCES plumb.build_steps (tenant_id, build_id, step_id)
);
CREATE INDEX build_step_attempts_open_lease_idx
    ON plumb.build_step_attempts (tenant_id, lease_expires_at) WHERE outcome = 'RUNNING';

-- Collectors (section 23 lifecycle; PL-023..PL-025 health publication).
CREATE TABLE plumb.collectors (
    tenant_id               plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                      plumb.identifier NOT NULL,
    spec_artifact_id        plumb.identifier NOT NULL,
    spec_artifact_version   INTEGER     NOT NULL,
    source_id               plumb.identifier NOT NULL,
    state                   TEXT        NOT NULL CHECK (state IN ('PLANNED', 'SHADOW', 'BACKFILLING', 'RECONCILING', 'ACTIVE', 'DEGRADED', 'PAUSED', 'RETIRED')),
    state_reason            TEXT        NOT NULL CHECK (length(state_reason) > 0),
    watermark               TEXT,
    freshness_seconds       INTEGER     CHECK (freshness_seconds IS NULL OR freshness_seconds >= 0),
    lag_seconds             INTEGER     CHECK (lag_seconds IS NULL OR lag_seconds >= 0),
    completeness            NUMERIC(5, 4) CHECK (completeness IS NULL OR completeness BETWEEN 0 AND 1),
    failure_state           TEXT        NOT NULL DEFAULT 'STOPPED' CHECK (failure_state IN ('HEALTHY', 'DEGRADED', 'STOPPED')),
    health_deadline_seconds INTEGER     NOT NULL CHECK (health_deadline_seconds >= 1),
    last_event_at           TIMESTAMPTZ,
    row_version             BIGINT      NOT NULL DEFAULT 1,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, spec_artifact_id, spec_artifact_version) REFERENCES plumb.artifacts (tenant_id, id, version)
);
CREATE TRIGGER collectors_row_version BEFORE UPDATE ON plumb.collectors
    FOR EACH ROW EXECUTE FUNCTION plumb.bump_row_version();
CREATE INDEX collectors_source_state_idx ON plumb.collectors (tenant_id, source_id, state);

-- Datasets (section 23 lifecycle; PL-028..PL-030). A revision is immutable; a
-- deleted source makes it UNAVAILABLE with a reason rather than falsified.
CREATE TABLE plumb.datasets (
    tenant_id                   plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                          plumb.identifier NOT NULL,
    revision                    INTEGER     NOT NULL CHECK (revision >= 1),
    manifest_artifact_id        plumb.identifier NOT NULL,
    manifest_artifact_version   INTEGER     NOT NULL,
    task_definition_ref         TEXT        NOT NULL,
    state                       TEXT        NOT NULL CHECK (state IN ('PROPOSED', 'MATERIALIZING', 'QUARANTINED', 'VERIFIED', 'SUPERSEDED', 'UNAVAILABLE')),
    state_reason                TEXT        NOT NULL CHECK (length(state_reason) > 0),
    unavailable_reason          TEXT,
    row_count                   INTEGER     NOT NULL DEFAULT 0 CHECK (row_count >= 0),
    content_digest              plumb.sha256_digest,
    row_version                 BIGINT      NOT NULL DEFAULT 1,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id, revision),
    FOREIGN KEY (tenant_id, manifest_artifact_id, manifest_artifact_version) REFERENCES plumb.artifacts (tenant_id, id, version),
    CONSTRAINT datasets_unavailable_has_reason CHECK ((state = 'UNAVAILABLE') = (unavailable_reason IS NOT NULL))
);
CREATE TRIGGER datasets_row_version BEFORE UPDATE ON plumb.datasets
    FOR EACH ROW EXECUTE FUNCTION plumb.bump_row_version();

-- Dataset rows (PL-028, PL-029). Point-in-time and split hygiene are enforced as
-- CHECK constraints in addition to the dataset checker.
CREATE TABLE plumb.dataset_rows (
    tenant_id                   plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    dataset_id                  plumb.identifier NOT NULL,
    dataset_revision            INTEGER     NOT NULL,
    example_id                  plumb.identifier NOT NULL,
    group_id                    plumb.identifier NOT NULL,
    input_snapshot_refs         TEXT[]      NOT NULL CHECK (cardinality(input_snapshot_refs) >= 1),
    input_availability_time     TIMESTAMPTZ NOT NULL,
    decision_time               TIMESTAMPTZ NOT NULL,
    target_evidence_ref         TEXT,
    target_availability_time    TIMESTAMPTZ,
    label_kind                  TEXT        NOT NULL CHECK (label_kind IN ('OBSERVED_OUTCOME', 'EXPERT_DECISION', 'CORRECTION', 'PREFERENCE', 'WEAK_PROXY')),
    label_status                TEXT        NOT NULL CHECK (label_status IN ('ACCEPTED', 'QUARANTINED_AMBIGUOUS', 'QUARANTINED_INCONSISTENT', 'QUARANTINED_DISPUTED', 'REJECTED')),
    purpose_authorization_ref   TEXT        NOT NULL,
    split                       TEXT        NOT NULL CHECK (split IN ('train', 'validation', 'test_temporal', 'test_client_disjoint')),
    exclusion_reason            TEXT,
    PRIMARY KEY (tenant_id, dataset_id, dataset_revision, example_id),
    FOREIGN KEY (tenant_id, dataset_id, dataset_revision) REFERENCES plumb.datasets (tenant_id, id, revision),
    CONSTRAINT dataset_rows_no_future_information CHECK (input_availability_time <= decision_time),
    CONSTRAINT dataset_rows_exclusion_reason_when_not_accepted CHECK (label_status = 'ACCEPTED' OR exclusion_reason IS NOT NULL),
    CONSTRAINT dataset_rows_no_quarantine_in_training CHECK (split <> 'train' OR label_status = 'ACCEPTED')
);
COMMENT ON TABLE plumb.dataset_rows IS 'Append-only per revision. Candidate for partitioning per dataset after measured need (section 23).';
CREATE INDEX dataset_rows_group_idx ON plumb.dataset_rows (tenant_id, dataset_id, dataset_revision, group_id);

-- Training jobs (section 23 lifecycle; PL-032, PL-033). Submission identity is
-- persisted before the provider call so a lost response cannot duplicate a job.
CREATE TABLE plumb.training_jobs (
    tenant_id                   plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                          plumb.identifier NOT NULL,
    spec_artifact_id            plumb.identifier NOT NULL,
    spec_artifact_version       INTEGER     NOT NULL,
    dataset_id                  plumb.identifier NOT NULL,
    dataset_revision            INTEGER     NOT NULL,
    state                       TEXT        NOT NULL CHECK (state IN ('PLANNED', 'SUBMITTED', 'RUNNING', 'CANDIDATE', 'FAILED', 'CANCELLED')),
    state_reason                TEXT        NOT NULL CHECK (length(state_reason) > 0),
    submission_identity         TEXT,
    provider_job_ref            TEXT,
    candidate_model_artifact_id       plumb.identifier,
    candidate_model_artifact_version  INTEGER,
    reserved_minor_units        BIGINT      NOT NULL CHECK (reserved_minor_units >= 0),
    actual_minor_units          BIGINT      CHECK (actual_minor_units IS NULL OR actual_minor_units >= 0),
    budget_currency             plumb.currency_code NOT NULL,
    row_version                 BIGINT      NOT NULL DEFAULT 1,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    UNIQUE (tenant_id, submission_identity),
    FOREIGN KEY (tenant_id, spec_artifact_id, spec_artifact_version) REFERENCES plumb.artifacts (tenant_id, id, version),
    FOREIGN KEY (tenant_id, dataset_id, dataset_revision) REFERENCES plumb.datasets (tenant_id, id, revision),
    FOREIGN KEY (tenant_id, candidate_model_artifact_id, candidate_model_artifact_version) REFERENCES plumb.artifacts (tenant_id, id, version),
    CONSTRAINT training_jobs_submitted_has_identity CHECK (state = 'PLANNED' OR submission_identity IS NOT NULL)
);
CREATE TRIGGER training_jobs_row_version BEFORE UPDATE ON plumb.training_jobs
    FOR EACH ROW EXECUTE FUNCTION plumb.bump_row_version();

-- Evaluations (PL-031, PL-034): held-out reports pinned to a dataset revision.
CREATE TABLE plumb.evaluations (
    tenant_id                   plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                          plumb.identifier NOT NULL,
    report_artifact_id          plumb.identifier NOT NULL,
    report_artifact_version     INTEGER     NOT NULL,
    subject_artifact_id         plumb.identifier NOT NULL,
    subject_artifact_version    INTEGER     NOT NULL,
    dataset_id                  plumb.identifier NOT NULL,
    dataset_revision            INTEGER     NOT NULL,
    level                       TEXT        NOT NULL CHECK (level IN ('SCHEMA_VALIDITY', 'ARTIFACT_INTEGRITY', 'INTEGRATION_BEHAVIOR', 'BUSINESS_OUTCOME', 'ECONOMIC_RESULT')),
    trials                      INTEGER     NOT NULL CHECK (trials >= 1),
    case_count                  INTEGER     NOT NULL CHECK (case_count >= 1),
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, report_artifact_id, report_artifact_version) REFERENCES plumb.artifacts (tenant_id, id, version),
    FOREIGN KEY (tenant_id, subject_artifact_id, subject_artifact_version) REFERENCES plumb.artifacts (tenant_id, id, version),
    FOREIGN KEY (tenant_id, dataset_id, dataset_revision) REFERENCES plumb.datasets (tenant_id, id, revision)
);
CREATE INDEX evaluations_subject_idx ON plumb.evaluations (tenant_id, subject_artifact_id, created_at);

-- Approvals (PL-040, PL-041): bound to subject digest, case version, policy
-- version, approver identity and expiry. An approval for one version or tenant
-- never authorizes another (tenant_id is part of the key; subject_digest is exact).
CREATE TABLE plumb.approvals (
    tenant_id                   plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                          plumb.identifier NOT NULL,
    decision_kind               TEXT        NOT NULL CHECK (decision_kind IN ('DATA_USE', 'IMPLEMENT_OPERATE', 'CASE_LEVEL_BUSINESS')),
    subject_digest              plumb.sha256_digest NOT NULL,
    case_version                INTEGER     CHECK (case_version IS NULL OR case_version >= 1),
    policy_version              plumb.semver NOT NULL,
    approver_principal_id       plumb.identifier NOT NULL,
    approver_principal_type     TEXT        NOT NULL CHECK (approver_principal_type IN ('HUMAN_OWNER', 'HUMAN_REVIEWER', 'HUMAN_APPROVER')),
    authenticated_decision_ref  TEXT        NOT NULL,
    approved_at                 TIMESTAMPTZ NOT NULL,
    expires_at                  TIMESTAMPTZ NOT NULL,
    revoked_at                  TIMESTAMPTZ,
    PRIMARY KEY (tenant_id, id),
    CONSTRAINT approvals_expiry_after_approval CHECK (expires_at > approved_at),
    CONSTRAINT approvals_case_decision_has_case_version CHECK (decision_kind <> 'CASE_LEVEL_BUSINESS' OR case_version IS NOT NULL)
);
CREATE INDEX approvals_subject_idx ON plumb.approvals (tenant_id, subject_digest, policy_version);
CREATE INDEX approvals_active_idx ON plumb.approvals (tenant_id, expires_at) WHERE revoked_at IS NULL;

-- Releases (section 23 lifecycle; PL-034, PL-046, PL-047). resolved_model_version
-- is the immutable registry version, never a mutable alias.
CREATE TABLE plumb.releases (
    tenant_id                   plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                          plumb.identifier NOT NULL,
    manifest_artifact_id        plumb.identifier NOT NULL,
    manifest_artifact_version   INTEGER     NOT NULL,
    state                       TEXT        NOT NULL CHECK (state IN ('CANDIDATE', 'VERIFIED', 'SHADOW', 'CANARY', 'ACTIVE', 'PAUSED', 'ROLLED_BACK', 'RETIRED')),
    state_reason                TEXT        NOT NULL CHECK (length(state_reason) > 0),
    resolved_model_version      TEXT,
    previous_release_id         plumb.identifier,
    activated_at                TIMESTAMPTZ,
    paused_at                   TIMESTAMPTZ,
    row_version                 BIGINT      NOT NULL DEFAULT 1,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, manifest_artifact_id, manifest_artifact_version) REFERENCES plumb.artifacts (tenant_id, id, version),
    FOREIGN KEY (tenant_id, previous_release_id) REFERENCES plumb.releases (tenant_id, id),
    -- A release without a model component (omitted_reason in the manifest) has no
    -- resolved_model_version; when present it must be a pinned version, never an
    -- alias such as "latest" or "prod" (PL-034, ADR-008).
    CONSTRAINT releases_model_version_not_alias CHECK (resolved_model_version IS NULL OR lower(resolved_model_version) NOT IN ('latest', 'champion', 'challenger', 'prod', 'production', 'staging', 'stable', 'current', 'default', 'canary', 'live'))
);
CREATE TRIGGER releases_row_version BEFORE UPDATE ON plumb.releases
    FOR EACH ROW EXECUTE FUNCTION plumb.bump_row_version();
CREATE INDEX releases_state_idx ON plumb.releases (tenant_id, state);

-- Cases (PL-035, PL-047): versioned business cases pinned to a release.
CREATE TABLE plumb.cases (
    tenant_id               plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                      plumb.identifier NOT NULL,
    release_id              plumb.identifier NOT NULL,
    workflow_state          plumb.identifier NOT NULL,
    case_version            BIGINT      NOT NULL DEFAULT 1 CHECK (case_version >= 1),
    external_subject_key    TEXT        NOT NULL,
    review_state            TEXT        NOT NULL CHECK (review_state IN ('NONE', 'READY_FOR_REVIEW', 'APPROVED', 'REJECTED')),
    opened_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at               TIMESTAMPTZ,
    row_version             BIGINT      NOT NULL DEFAULT 1,
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, release_id) REFERENCES plumb.releases (tenant_id, id)
);
CREATE TRIGGER cases_row_version BEFORE UPDATE ON plumb.cases
    FOR EACH ROW EXECUTE FUNCTION plumb.bump_row_version();
-- Case lookups: by release/state for the runtime and by external subject for dedup.
CREATE INDEX cases_release_state_idx ON plumb.cases (tenant_id, release_id, workflow_state);
CREATE INDEX cases_external_subject_idx ON plumb.cases (tenant_id, external_subject_key);
CREATE INDEX cases_open_idx ON plumb.cases (tenant_id, opened_at) WHERE closed_at IS NULL;

-- Effects (PL-037..PL-039; section 23 lifecycle). The row is written BEFORE
-- dispatch. slot_key = tenant|case|obligation|epoch|operation|target; the
-- payload digest and logical action id are separate; deployment_version is
-- recorded but is not part of the identity.
CREATE TABLE plumb.effects (
    tenant_id               plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                      plumb.identifier NOT NULL,
    slot_key                TEXT        NOT NULL,
    case_id                 plumb.identifier NOT NULL,
    obligation_id           plumb.identifier NOT NULL,
    obligation_epoch        INTEGER     NOT NULL CHECK (obligation_epoch >= 0),
    operation               plumb.identifier NOT NULL,
    target                  plumb.identifier NOT NULL,
    payload_digest          plumb.sha256_digest NOT NULL,
    expected_state_version  BIGINT      NOT NULL CHECK (expected_state_version >= 1),
    authority_ref           TEXT        NOT NULL,
    deployment_version      plumb.identifier NOT NULL,
    provider                TEXT        NOT NULL,
    external_account_id     TEXT        NOT NULL,
    effect_class            TEXT        NOT NULL CHECK (effect_class IN ('READ', 'INTERNAL_WRITE', 'EXTERNAL_WRITE_REVERSIBLE', 'EXTERNAL_WRITE_IRREVERSIBLE', 'EXTERNAL_COMMUNICATION', 'FINANCIAL_COMMITMENT', 'INFRASTRUCTURE_CHANGE', 'DESTRUCTIVE')),
    idempotency_key         TEXT        NOT NULL,
    state                   TEXT        NOT NULL CHECK (state IN ('RESERVED', 'DISPATCHED', 'UNKNOWN', 'CONFIRMED', 'FAILED_FINAL', 'COMPENSATED')),
    state_reason            TEXT        NOT NULL CHECK (length(state_reason) > 0),
    supersedes_action_id    plumb.identifier,
    lease_owner             TEXT,
    provider_request_id     TEXT,
    external_id             TEXT,
    receipt_digest          plumb.sha256_digest,
    reserved_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    dispatched_at           TIMESTAMPTZ,
    finalized_at            TIMESTAMPTZ,
    row_version             BIGINT      NOT NULL DEFAULT 1,
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, case_id) REFERENCES plumb.cases (tenant_id, id),
    FOREIGN KEY (tenant_id, deployment_version) REFERENCES plumb.releases (tenant_id, id),
    FOREIGN KEY (tenant_id, supersedes_action_id) REFERENCES plumb.effects (tenant_id, id),
    -- A CONFIRMED effect requires an external receipt/postcondition (section 23).
    CONSTRAINT effects_confirmed_has_receipt CHECK (state NOT IN ('CONFIRMED', 'COMPENSATED') OR receipt_digest IS NOT NULL),
    -- Anything that reached the provider records who dispatched it and when; a
    -- RESERVED action may still fail final (e.g. authority revoked) without dispatch.
    CONSTRAINT effects_dispatch_recorded CHECK (state IN ('RESERVED', 'FAILED_FINAL') OR (lease_owner IS NOT NULL AND dispatched_at IS NOT NULL))
);
CREATE TRIGGER effects_row_version BEFORE UPDATE ON plumb.effects
    FOR EACH ROW EXECUTE FUNCTION plumb.bump_row_version();
-- One business action per effect slot; dedup survives restarts and releases.
CREATE UNIQUE INDEX effects_slot_key_idx ON plumb.effects (tenant_id, slot_key);
CREATE UNIQUE INDEX effects_idempotency_key_idx ON plumb.effects (tenant_id, idempotency_key);
-- Outstanding effects: the restart reconciliation list (PL-038, PL-039).
CREATE INDEX effects_outstanding_idx ON plumb.effects (tenant_id, state) WHERE state IN ('DISPATCHED', 'UNKNOWN');
CREATE INDEX effects_case_idx ON plumb.effects (tenant_id, case_id, obligation_id);
CREATE INDEX effects_provider_request_idx ON plumb.effects (tenant_id, provider, provider_request_id) WHERE provider_request_id IS NOT NULL;

-- Effect transitions (PL-057): every transition persists from/to/reason/actor.
CREATE TABLE plumb.effect_transitions (
    tenant_id           plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                  BIGINT      GENERATED ALWAYS AS IDENTITY,
    action_id           plumb.identifier NOT NULL,
    from_state          TEXT        CHECK (from_state IS NULL OR from_state IN ('RESERVED', 'DISPATCHED', 'UNKNOWN', 'CONFIRMED', 'FAILED_FINAL', 'COMPENSATED')),
    to_state            TEXT        NOT NULL CHECK (to_state IN ('RESERVED', 'DISPATCHED', 'UNKNOWN', 'CONFIRMED', 'FAILED_FINAL', 'COMPENSATED')),
    reason              TEXT        NOT NULL CHECK (length(reason) > 0),
    actor_principal_id  plumb.identifier NOT NULL,
    transitioned_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, action_id) REFERENCES plumb.effects (tenant_id, id)
);
COMMENT ON TABLE plumb.effect_transitions IS 'Append-only audit of effect state changes. Candidate for range partitioning on transitioned_at after measured need.';
CREATE INDEX effect_transitions_action_idx ON plumb.effect_transitions (tenant_id, action_id, transitioned_at);

-- Outbox (section 22, Appendix A §2 step 7): events are written in the same
-- transaction as the state change and published at least once.
CREATE TABLE plumb.outbox (
    tenant_id           plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                  plumb.identifier NOT NULL,
    aggregate_type      plumb.identifier NOT NULL,
    aggregate_id        plumb.identifier NOT NULL,
    aggregate_version   BIGINT      NOT NULL CHECK (aggregate_version >= 1),
    event_type          plumb.identifier NOT NULL,
    occurred_at         TIMESTAMPTZ NOT NULL,
    recorded_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    correlation_id      plumb.identifier NOT NULL,
    causation_id        plumb.identifier,
    schema_version      plumb.semver NOT NULL,
    payload_ref         TEXT        NOT NULL,
    published_at        TIMESTAMPTZ,
    publish_attempts    INTEGER     NOT NULL DEFAULT 0 CHECK (publish_attempts >= 0),
    PRIMARY KEY (tenant_id, id),
    -- Ordering is per aggregate only: one event per aggregate version.
    UNIQUE (tenant_id, aggregate_type, aggregate_id, aggregate_version)
);
COMMENT ON TABLE plumb.outbox IS 'Transactional outbox. Candidate for range partitioning on recorded_at after measured need (section 23).';
CREATE INDEX outbox_unpublished_idx ON plumb.outbox (tenant_id, recorded_at) WHERE published_at IS NULL;
CREATE INDEX outbox_aggregate_idx ON plumb.outbox (tenant_id, aggregate_type, aggregate_id, aggregate_version);

-- Processed events (section 22): a consumer records the processed event id in
-- the same local transaction as its state update; the primary key makes the
-- second delivery a no-op.
CREATE TABLE plumb.processed_events (
    consumer        plumb.identifier NOT NULL,
    event_id        plumb.identifier NOT NULL,
    tenant_id       plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    processed_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (consumer, event_id)
);
CREATE INDEX processed_events_tenant_idx ON plumb.processed_events (tenant_id, consumer, processed_at);

-- Jobs (PL-055): durable identity for long-running mutations. The idempotency
-- key is unique per tenant; a repeat with a different payload digest is a
-- PAYLOAD_CONFLICT. Status is server-assigned.
CREATE TABLE plumb.jobs (
    tenant_id                   plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                          plumb.identifier NOT NULL,
    operation_id                TEXT        NOT NULL,
    idempotency_key             TEXT        NOT NULL CHECK (length(idempotency_key) BETWEEN 1 AND 255),
    payload_digest              plumb.sha256_digest NOT NULL,
    status                      TEXT        NOT NULL CHECK (status IN ('ACCEPTED', 'RUNNING', 'WAITING', 'SUCCEEDED', 'FAILED', 'CANCELLED')),
    result_artifact_id          plumb.identifier,
    result_artifact_version     INTEGER,
    error_class                 TEXT        CHECK (error_class IS NULL OR error_class IN ('AUTH_REQUIRED', 'SCOPE_DENIED', 'PURPOSE_DENIED', 'POLICY_STALE', 'STATE_CONFLICT', 'PAYLOAD_CONFLICT', 'BUDGET_EXCEEDED', 'CAPABILITY_UNSUPPORTED', 'SOURCE_STALE', 'DATA_QUALITY_FAILED', 'VERIFICATION_FAILED', 'EFFECT_UNKNOWN', 'RETRY_EXHAUSTED')),
    error_message               TEXT,
    retryable                   BOOLEAN,
    dependency_id               plumb.identifier,
    operator_action             TEXT,
    correlation_id              plumb.identifier NOT NULL,
    row_version                 BIGINT      NOT NULL DEFAULT 1,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    UNIQUE (tenant_id, idempotency_key),
    FOREIGN KEY (tenant_id, result_artifact_id, result_artifact_version) REFERENCES plumb.artifacts (tenant_id, id, version),
    CONSTRAINT jobs_failed_has_error CHECK (status <> 'FAILED' OR error_class IS NOT NULL)
);
CREATE TRIGGER jobs_row_version BEFORE UPDATE ON plumb.jobs
    FOR EACH ROW EXECUTE FUNCTION plumb.bump_row_version();
CREATE INDEX jobs_open_idx ON plumb.jobs (tenant_id, created_at) WHERE status IN ('ACCEPTED', 'RUNNING', 'WAITING');

-- Outcome observations (PL-059): model calls, completed cases, correct outcomes
-- and realized value are distinct columns; technical and commercial success are
-- recorded separately.
CREATE TABLE plumb.outcome_observations (
    tenant_id                   plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id                          plumb.identifier NOT NULL,
    case_id                     plumb.identifier NOT NULL,
    release_id                  plumb.identifier NOT NULL,
    model_calls                 INTEGER     NOT NULL CHECK (model_calls >= 0),
    completed                   BOOLEAN     NOT NULL,
    correct                     BOOLEAN,
    realized_value_minor_units  BIGINT      CHECK (realized_value_minor_units IS NULL OR realized_value_minor_units >= 0),
    realized_value_currency     plumb.currency_code,
    review_minutes              INTEGER     NOT NULL CHECK (review_minutes >= 0),
    human_effort_category       TEXT        CHECK (human_effort_category IS NULL OR human_effort_category IN ('CUSTOMER_AUTHORIZATION', 'DOMAIN_CLARIFICATION', 'NORMAL_BUSINESS_REVIEW', 'ENGINEERING_INTERVENTION', 'OPERATIONAL_REPAIR')),
    observed_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, case_id) REFERENCES plumb.cases (tenant_id, id),
    FOREIGN KEY (tenant_id, release_id) REFERENCES plumb.releases (tenant_id, id),
    CONSTRAINT outcome_observations_value_has_currency CHECK ((realized_value_minor_units IS NULL) = (realized_value_currency IS NULL)),
    CONSTRAINT outcome_observations_correct_only_when_completed CHECK (completed OR correct IS NULL)
);
CREATE INDEX outcome_observations_release_idx ON plumb.outcome_observations (tenant_id, release_id, observed_at);
CREATE INDEX outcome_observations_case_idx ON plumb.outcome_observations (tenant_id, case_id);

-- Human effort (PL-003, PL-062): every category of human work is recorded so a
-- deployment is never called autonomous when a person did the implementation.
CREATE TABLE plumb.human_effort (
    tenant_id       plumb.tenant_id NOT NULL REFERENCES plumb.tenants (id),
    id              plumb.identifier NOT NULL,
    category        TEXT        NOT NULL CHECK (category IN ('CUSTOMER_AUTHORIZATION', 'DOMAIN_CLARIFICATION', 'NORMAL_BUSINESS_REVIEW', 'ENGINEERING_INTERVENTION', 'OPERATIONAL_REPAIR')),
    principal_id    plumb.identifier NOT NULL,
    principal_type  TEXT        NOT NULL CHECK (principal_type IN ('HUMAN_OWNER', 'HUMAN_REVIEWER', 'HUMAN_APPROVER', 'SERVICE', 'BUILD_AGENT', 'RUNTIME_AGENT', 'VERIFIER', 'RELEASE_EXECUTOR')),
    minutes         INTEGER     NOT NULL CHECK (minutes >= 0),
    description     TEXT        NOT NULL CHECK (length(description) > 0),
    build_id        plumb.identifier,
    case_id         plumb.identifier,
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, build_id) REFERENCES plumb.builds (tenant_id, id),
    FOREIGN KEY (tenant_id, case_id) REFERENCES plumb.cases (tenant_id, id)
);
CREATE INDEX human_effort_category_idx ON plumb.human_effort (tenant_id, category, recorded_at);

-- =============================================================================
-- Row level security (PL-052). Applied to every tenant table.
--
-- plumb_app sets the tenant once per transaction:
--     SET LOCAL plumb.tenant_id = 'tnt_...';
-- current_setting('plumb.tenant_id', true) returns NULL when unset, so the
-- policy fails closed (no rows visible, no rows writable).
--
-- EXCEPTIONS THAT REMAIN (PL-052): superusers, roles with BYPASSRLS
-- (plumb_platform_admin, by design and audited) and any future owner that is
-- not covered by FORCE ROW LEVEL SECURITY. RLS is one layer of the isolation
-- design, not the whole of it.
-- =============================================================================

ALTER TABLE plumb.artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.artifacts FORCE ROW LEVEL SECURITY;
CREATE POLICY artifacts_tenant_isolation ON plumb.artifacts
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.envelopes ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.envelopes FORCE ROW LEVEL SECURITY;
CREATE POLICY envelopes_tenant_isolation ON plumb.envelopes
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.source_grants ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.source_grants FORCE ROW LEVEL SECURITY;
CREATE POLICY source_grants_tenant_isolation ON plumb.source_grants
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.evidence_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.evidence_events FORCE ROW LEVEL SECURITY;
CREATE POLICY evidence_events_tenant_isolation ON plumb.evidence_events
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.objects ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.objects FORCE ROW LEVEL SECURITY;
CREATE POLICY objects_tenant_isolation ON plumb.objects
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.object_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.object_links FORCE ROW LEVEL SECURITY;
CREATE POLICY object_links_tenant_isolation ON plumb.object_links
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.facts ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.facts FORCE ROW LEVEL SECURITY;
CREATE POLICY facts_tenant_isolation ON plumb.facts
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.goals FORCE ROW LEVEL SECURITY;
CREATE POLICY goals_tenant_isolation ON plumb.goals
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.opportunities FORCE ROW LEVEL SECURITY;
CREATE POLICY opportunities_tenant_isolation ON plumb.opportunities
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.builds ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.builds FORCE ROW LEVEL SECURITY;
CREATE POLICY builds_tenant_isolation ON plumb.builds
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.build_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.build_steps FORCE ROW LEVEL SECURITY;
CREATE POLICY build_steps_tenant_isolation ON plumb.build_steps
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.build_step_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.build_step_attempts FORCE ROW LEVEL SECURITY;
CREATE POLICY build_step_attempts_tenant_isolation ON plumb.build_step_attempts
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.collectors ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.collectors FORCE ROW LEVEL SECURITY;
CREATE POLICY collectors_tenant_isolation ON plumb.collectors
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.datasets ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.datasets FORCE ROW LEVEL SECURITY;
CREATE POLICY datasets_tenant_isolation ON plumb.datasets
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.dataset_rows ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.dataset_rows FORCE ROW LEVEL SECURITY;
CREATE POLICY dataset_rows_tenant_isolation ON plumb.dataset_rows
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.training_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.training_jobs FORCE ROW LEVEL SECURITY;
CREATE POLICY training_jobs_tenant_isolation ON plumb.training_jobs
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.evaluations FORCE ROW LEVEL SECURITY;
CREATE POLICY evaluations_tenant_isolation ON plumb.evaluations
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.approvals FORCE ROW LEVEL SECURITY;
CREATE POLICY approvals_tenant_isolation ON plumb.approvals
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.releases ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.releases FORCE ROW LEVEL SECURITY;
CREATE POLICY releases_tenant_isolation ON plumb.releases
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.cases FORCE ROW LEVEL SECURITY;
CREATE POLICY cases_tenant_isolation ON plumb.cases
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.effects ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.effects FORCE ROW LEVEL SECURITY;
CREATE POLICY effects_tenant_isolation ON plumb.effects
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.effect_transitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.effect_transitions FORCE ROW LEVEL SECURITY;
CREATE POLICY effect_transitions_tenant_isolation ON plumb.effect_transitions
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.outbox ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.outbox FORCE ROW LEVEL SECURITY;
CREATE POLICY outbox_tenant_isolation ON plumb.outbox
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.processed_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.processed_events FORCE ROW LEVEL SECURITY;
CREATE POLICY processed_events_tenant_isolation ON plumb.processed_events
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.jobs FORCE ROW LEVEL SECURITY;
CREATE POLICY jobs_tenant_isolation ON plumb.jobs
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.outcome_observations ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.outcome_observations FORCE ROW LEVEL SECURITY;
CREATE POLICY outcome_observations_tenant_isolation ON plumb.outcome_observations
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE plumb.human_effort ENABLE ROW LEVEL SECURITY;
ALTER TABLE plumb.human_effort FORCE ROW LEVEL SECURITY;
CREATE POLICY human_effort_tenant_isolation ON plumb.human_effort
    USING (tenant_id = current_setting('plumb.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

-- =============================================================================
-- Grants (PL-052, PL-006). The service role never holds DELETE or DDL; append-
-- only tables are INSERT/SELECT only; retention is a platform-admin duty.
-- =============================================================================

GRANT USAGE ON SCHEMA plumb TO plumb_app, plumb_platform_admin;

-- Platform tables: the service reads them; the platform admin maintains them.
GRANT SELECT ON plumb.tenants, plumb.capabilities TO plumb_app;
GRANT SELECT, INSERT, UPDATE ON plumb.tenants, plumb.capabilities TO plumb_platform_admin;

-- Append-only records.
GRANT SELECT, INSERT ON
    plumb.artifacts,
    plumb.evidence_events,
    plumb.effect_transitions,
    plumb.processed_events,
    plumb.outcome_observations,
    plumb.human_effort,
    plumb.dataset_rows
TO plumb_app;

-- Mutable aggregates (compare-and-set on row_version; no DELETE).
GRANT SELECT, INSERT, UPDATE ON
    plumb.envelopes,
    plumb.source_grants,
    plumb.objects,
    plumb.object_links,
    plumb.facts,
    plumb.goals,
    plumb.opportunities,
    plumb.builds,
    plumb.build_steps,
    plumb.build_step_attempts,
    plumb.collectors,
    plumb.datasets,
    plumb.training_jobs,
    plumb.evaluations,
    plumb.approvals,
    plumb.releases,
    plumb.cases,
    plumb.effects,
    plumb.outbox,
    plumb.jobs
TO plumb_app;

-- Platform admin: cross-tenant read for support and audited retention deletes.
-- Every use of this role must be logged (PL-052, PL-057 audit).
GRANT SELECT, DELETE ON ALL TABLES IN SCHEMA plumb TO plumb_platform_admin;

GRANT EXECUTE ON FUNCTION plumb.bump_row_version() TO plumb_app;

-- The migrator owns every object (CREATE SCHEMA ... AUTHORIZATION) and holds no
-- login; migrations run under it, services never do.

COMMIT;
