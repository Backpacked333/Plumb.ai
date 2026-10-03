-- Roles, grants and row-level security. Design proposal, not executed here (see VERIFICATION_REPORT.md).
-- Principle (SI-002): tenant isolation = RLS on every tenant table + per-service roles without BYPASSRLS
-- + application-level tenant derivation from authentication + separate migration role. Enabling RLS alone is
-- not isolation: table owners and superusers bypass policies, so no service role may own a table.
SET search_path TO plumb;

CREATE ROLE plumb_migrator NOLOGIN;              -- owns tables; used only by migrations
CREATE ROLE plumb_control LOGIN NOBYPASSRLS;     -- control service: lifecycle transitions, approvals, builds
CREATE ROLE plumb_runtime LOGIN NOBYPASSRLS;     -- workflow runtime and gateway dispatcher
CREATE ROLE plumb_verifier LOGIN NOBYPASSRLS;    -- verifier service: may INSERT attestations, nothing else writes them
CREATE ROLE plumb_builder LOGIN NOBYPASSRLS;     -- build orchestration: builds, steps, leases, diagnostics; no attestations, no approvals
CREATE ROLE plumb_reporting LOGIN NOBYPASSRLS;   -- sponsor and Studio read models (aggregates only)

ALTER TABLE tenants OWNER TO plumb_migrator;
ALTER TABLE principals OWNER TO plumb_migrator;
ALTER TABLE source_grants OWNER TO plumb_migrator;
ALTER TABLE autonomy_envelopes OWNER TO plumb_migrator;
ALTER TABLE approvals OWNER TO plumb_migrator;
ALTER TABLE evidence_events OWNER TO plumb_migrator;
ALTER TABLE facts OWNER TO plumb_migrator;
ALTER TABLE obligations OWNER TO plumb_migrator;
ALTER TABLE builds OWNER TO plumb_migrator;
ALTER TABLE build_steps OWNER TO plumb_migrator;
ALTER TABLE verification_attestations OWNER TO plumb_migrator;
ALTER TABLE releases OWNER TO plumb_migrator;
ALTER TABLE cases OWNER TO plumb_migrator;
ALTER TABLE action_intents OWNER TO plumb_migrator;
ALTER TABLE effects OWNER TO plumb_migrator;
ALTER TABLE receipts OWNER TO plumb_migrator;
ALTER TABLE outbox OWNER TO plumb_migrator;
ALTER TABLE audit_log OWNER TO plumb_migrator;
ALTER TABLE labor_records OWNER TO plumb_migrator;
ALTER TABLE billable_units OWNER TO plumb_migrator;

-- Row-level security on every tenant-scoped table (pattern shown for the tables used by the first slice)
ALTER TABLE source_grants ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_grants FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON source_grants USING (tenant_id = current_setting('plumb.tenant_id', true)) WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE approvals FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON approvals USING (tenant_id = current_setting('plumb.tenant_id', true)) WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE evidence_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_events FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON evidence_events USING (tenant_id = current_setting('plumb.tenant_id', true)) WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE builds ENABLE ROW LEVEL SECURITY;
ALTER TABLE builds FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON builds USING (tenant_id = current_setting('plumb.tenant_id', true)) WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE verification_attestations ENABLE ROW LEVEL SECURITY;
ALTER TABLE verification_attestations FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON verification_attestations USING (tenant_id = current_setting('plumb.tenant_id', true)) WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));
-- only the verifier role may insert attestations; nobody updates them (invalidation is a dated column set by control)
CREATE POLICY verifier_insert ON verification_attestations FOR INSERT TO plumb_verifier WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true) AND verifier_identity = current_setting('plumb.service_identity', true));

ALTER TABLE releases ENABLE ROW LEVEL SECURITY;
ALTER TABLE releases FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON releases USING (tenant_id = current_setting('plumb.tenant_id', true)) WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE cases FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON cases USING (tenant_id = current_setting('plumb.tenant_id', true)) WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE effects ENABLE ROW LEVEL SECURITY;
ALTER TABLE effects FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON effects USING (tenant_id = current_setting('plumb.tenant_id', true)) WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON audit_log USING (tenant_id = current_setting('plumb.tenant_id', true)) WITH CHECK (tenant_id = current_setting('plumb.tenant_id', true));

-- Grants: least privilege per role. Attestations and approvals are the two tables the builder never writes.
GRANT USAGE ON SCHEMA plumb TO plumb_control, plumb_runtime, plumb_verifier, plumb_builder, plumb_reporting;
GRANT SELECT, INSERT, UPDATE ON source_grants, approvals, autonomy_envelopes, builds, build_steps, releases, cases, review_items, external_dependencies TO plumb_control;
GRANT SELECT, INSERT ON audit_log, outbox TO plumb_control, plumb_runtime, plumb_builder, plumb_verifier;
GRANT SELECT, INSERT, UPDATE ON action_intents, effects, effect_attempts, receipts, cases, consumer_offsets TO plumb_runtime;
GRANT SELECT ON approvals, releases, source_grants, autonomy_envelopes TO plumb_runtime;
GRANT SELECT, INSERT ON verification_attestations TO plumb_verifier;
GRANT SELECT ON builds, build_steps, releases, datasets, dataset_rows TO plumb_verifier;
GRANT SELECT, INSERT, UPDATE ON builds, build_steps, task_leases, budget_reservations, failure_diagnostics, external_dependencies, artifacts, artifact_aliases TO plumb_builder;
GRANT SELECT ON source_grants, autonomy_envelopes, capabilities TO plumb_builder;
REVOKE ALL ON verification_attestations FROM plumb_builder;
REVOKE ALL ON approvals FROM plumb_builder;
GRANT SELECT ON billable_units, outcome_observations, labor_records TO plumb_reporting;
-- Sponsor read models are views over aggregates; raw evidence_events are never granted to plumb_reporting.
