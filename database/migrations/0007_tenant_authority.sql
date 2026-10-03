-- Apply after the six immutable RC1 design migrations, before granting service access.
SET search_path TO plumb;

ALTER TABLE collector_health ADD COLUMN tenant_id text;
UPDATE collector_health h SET tenant_id = c.tenant_id FROM collectors c WHERE c.collection_id = h.collection_id;
ALTER TABLE collector_health ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE effect_attempts ADD COLUMN tenant_id text;
UPDATE effect_attempts a SET tenant_id = e.tenant_id FROM effects e WHERE e.effect_id = a.effect_id;
ALTER TABLE effect_attempts ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE outbox_dead_letter ADD COLUMN tenant_id text;
UPDATE outbox_dead_letter d SET tenant_id = o.tenant_id FROM outbox o WHERE o.event_id = d.event_id;
ALTER TABLE outbox_dead_letter ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE consumer_offsets ADD COLUMN tenant_id text;
UPDATE consumer_offsets c SET tenant_id = o.tenant_id FROM outbox o WHERE o.event_id = c.event_id;
ALTER TABLE consumer_offsets ALTER COLUMN tenant_id SET NOT NULL;

ALTER TABLE outbox_dead_letter ADD CONSTRAINT dead_letter_event_fk FOREIGN KEY (event_id) REFERENCES outbox(event_id);
ALTER TABLE consumer_offsets ADD CONSTRAINT consumer_event_fk FOREIGN KEY (event_id) REFERENCES outbox(event_id);

-- RLS cannot enforce tenant equality across a foreign key: FK checks bypass RLS.
DO $$
DECLARE
    fk record;
    child_columns text;
    parent_columns text;
BEGIN
    FOR fk IN
        SELECT c.*, c.conrelid::regclass AS child_table, c.confrelid::regclass AS parent_table
        FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE n.nspname = 'plumb' AND c.contype = 'f'
          AND NOT EXISTS (
              SELECT 1 FROM unnest(c.conkey) AS key(attnum)
              JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = key.attnum
              WHERE a.attname = 'tenant_id'
          )
    LOOP
        SELECT string_agg(format('%I', a.attname), ', ' ORDER BY key.position)
        INTO child_columns FROM unnest(fk.conkey) WITH ORDINALITY AS key(attnum, position)
        JOIN pg_attribute a ON a.attrelid = fk.conrelid AND a.attnum = key.attnum;
        SELECT string_agg(format('%I', a.attname), ', ' ORDER BY key.position)
        INTO parent_columns FROM unnest(fk.confkey) WITH ORDINALITY AS key(attnum, position)
        JOIN pg_attribute a ON a.attrelid = fk.confrelid AND a.attnum = key.attnum;
        EXECUTE format('CREATE UNIQUE INDEX IF NOT EXISTS %I ON %s (tenant_id, %s)',
                       'tenant_ref_' || fk.confrelid || '_' || array_to_string(fk.confkey, '_'),
                       fk.parent_table, parent_columns);
        EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I', fk.child_table, fk.conname);
        EXECUTE format('ALTER TABLE %s ADD CONSTRAINT %I FOREIGN KEY (tenant_id, %s) REFERENCES %s (tenant_id, %s)',
                       fk.child_table, fk.conname, child_columns, fk.parent_table, parent_columns);
    END LOOP;
END $$;

DO $$
DECLARE
    relation record;
BEGIN
    FOR relation IN
        SELECT c.oid, c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'plumb' AND c.relkind = 'r'
    LOOP
        IF relation.relname <> 'tenants' THEN
            EXECUTE format('ALTER TABLE plumb.%I ADD CONSTRAINT tenant_exists FOREIGN KEY (tenant_id) REFERENCES plumb.tenants(tenant_id)', relation.relname);
        END IF;
        EXECUTE format('ALTER TABLE plumb.%I ENABLE ROW LEVEL SECURITY', relation.relname);
        EXECUTE format('ALTER TABLE plumb.%I FORCE ROW LEVEL SECURITY', relation.relname);
        EXECUTE format('CREATE POLICY tenant_isolation ON plumb.%I USING (tenant_id = nullif(current_setting(''plumb.tenant_id'', true), '''')) WITH CHECK (tenant_id = nullif(current_setting(''plumb.tenant_id'', true), ''''))', relation.relname);
        EXECUTE format('ALTER TABLE plumb.%I OWNER TO plumb_migrator', relation.relname);
    END LOOP;
END $$;

-- RESTRICTIVE is essential: permissive policies are combined with OR, not AND.
CREATE POLICY verifier_identity ON verification_attestations AS RESTRICTIVE
    FOR INSERT TO plumb_verifier WITH CHECK (verifier_identity = current_user);

ALTER SCHEMA plumb OWNER TO plumb_migrator;
REVOKE ALL ON SCHEMA plumb FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA plumb FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA plumb FROM PUBLIC;
GRANT USAGE ON SCHEMA plumb TO plumb_control, plumb_runtime, plumb_verifier, plumb_builder, plumb_reporting;

GRANT SELECT, INSERT, UPDATE ON
    tenants, principals, source_grants, autonomy_envelopes, approvals, revocations,
    artifact_aliases, environment_inventories, capabilities, opportunities, coverage_decisions,
    solutions, builds, build_steps, task_leases, budget_reservations, external_dependencies,
    failure_diagnostics, integrations, collectors, collector_health, datasets, training_jobs, model_versions,
    releases, cases, review_items, action_intents, effects, effect_attempts, receipts,
    outbox, outbox_dead_letter, consumer_offsets, removal_requests
TO plumb_control;
GRANT SELECT, INSERT ON artifacts, evidence_events, business_objects, object_attribute_history,
    event_object_links, object_object_links, identity_candidates, facts, obligations,
    dataset_rows, usage_records, cost_records, labor_records, billable_units,
    outcome_observations TO plumb_control;
GRANT SELECT ON verification_attestations TO plumb_control;
GRANT UPDATE (invalidated_at) ON verification_attestations TO plumb_control;

GRANT SELECT ON cases, releases, review_items, action_intents, effects, effect_attempts,
    receipts, approvals, source_grants, autonomy_envelopes TO plumb_runtime;
GRANT SELECT ON builds, build_steps, releases, datasets, dataset_rows TO plumb_verifier;
GRANT SELECT, INSERT ON verification_attestations TO plumb_verifier;
GRANT SELECT ON builds, build_steps, task_leases, budget_reservations, failure_diagnostics,
    external_dependencies, artifacts, artifact_aliases, source_grants, autonomy_envelopes,
    capabilities TO plumb_builder;
GRANT INSERT ON artifacts TO plumb_builder;
-- Reporting stays denied until scoped, small-cohort-safe aggregate views exist.
GRANT SELECT, INSERT ON audit_log TO plumb_control, plumb_runtime, plumb_builder, plumb_verifier;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA plumb TO plumb_control;
GRANT USAGE ON SEQUENCE audit_log_seq_seq TO plumb_runtime, plumb_builder, plumb_verifier;
