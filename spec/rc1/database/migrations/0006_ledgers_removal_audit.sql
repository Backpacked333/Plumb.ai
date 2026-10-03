-- 0006: usage, cost, labor and billing ledgers; outcomes; removal requests; append-only audit.
SET search_path TO plumb;

CREATE TABLE usage_records (
  usage_id      text PRIMARY KEY,
  tenant_id     text NOT NULL REFERENCES tenants(tenant_id),
  producer      text NOT NULL CHECK (producer IN ('model_gateway','connector_runtime','training_adapter','infra_adapter')),
  case_id       text REFERENCES cases(case_id),
  build_id      text REFERENCES builds(build_id),
  release_id    text REFERENCES releases(release_id),
  part          text NOT NULL,
  quantity      numeric(18,6) NOT NULL,
  unit          text NOT NULL,
  cost_minor    bigint,
  currency      char(3),
  recorded_at   timestamptz NOT NULL DEFAULT now(),
  correction_of text REFERENCES usage_records(usage_id)
);
CREATE INDEX usage_records_tenant_time_idx ON usage_records(tenant_id, recorded_at);

CREATE TABLE cost_records (
  cost_id       text PRIMARY KEY,
  tenant_id     text NOT NULL REFERENCES tenants(tenant_id),
  category      text NOT NULL CHECK (category IN ('provider_usage','plumb_operating','storage','logs','backfill','verification','quarantine','idle_serving','support','repair')),
  amount_minor  bigint NOT NULL,
  currency      char(3) NOT NULL,
  period        char(7) NOT NULL,
  reference_id  text,
  recorded_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE labor_records (
  record_id    text PRIMARY KEY,
  tenant_id    text NOT NULL REFERENCES tenants(tenant_id),
  build_id     text REFERENCES builds(build_id),
  case_id      text REFERENCES cases(case_id),
  category     text NOT NULL CHECK (category IN ('customer_authorization','domain_clarification','business_review','engineering_intervention','operational_repair','platform_engineering')),
  actor_role   text NOT NULL,
  minutes      numeric(9,2) NOT NULL CHECK (minutes >= 0),
  description  text NOT NULL,
  recorded_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX labor_records_build_idx ON labor_records(build_id, category);

CREATE TABLE billable_units (
  unit_id            text PRIMARY KEY,
  tenant_id          text NOT NULL REFERENCES tenants(tenant_id),
  case_id            text NOT NULL REFERENCES cases(case_id),
  obligation_epoch   integer NOT NULL,
  predicate          text NOT NULL,
  release_id         text NOT NULL REFERENCES releases(release_id),
  satisfied_at       timestamptz NOT NULL,
  status             text NOT NULL CHECK (status IN ('billable','credited','superseded','void')),
  supersedes_unit_id text REFERENCES billable_units(unit_id),
  UNIQUE (case_id, obligation_epoch, predicate)
);

CREATE TABLE outcome_observations (
  observation_id text PRIMARY KEY,
  tenant_id      text NOT NULL REFERENCES tenants(tenant_id),
  case_id        text REFERENCES cases(case_id),
  release_id     text REFERENCES releases(release_id),
  metric         text NOT NULL,
  value          numeric(18,6) NOT NULL,
  unit           text NOT NULL,
  method         text NOT NULL CHECK (method IN ('prospective_cohort','rollout_comparison','direct_measurement','survey','timing_simulation')),
  cohort         text,
  observed_at    timestamptz NOT NULL,
  limitations    text[] NOT NULL DEFAULT '{}'
);

CREATE TABLE removal_requests (
  removal_id              text PRIMARY KEY,
  tenant_id               text NOT NULL REFERENCES tenants(tenant_id),
  requester_principal_id  text NOT NULL REFERENCES principals(principal_id),
  scope                   jsonb NOT NULL,
  legal_basis             text,
  state                   text NOT NULL CHECK (state IN ('RECEIVED','VALIDATED','INGESTION_STOPPED','IMPACT_COMPUTED','ON_HOLD','ACCESS_DISABLED','DERIVED_REMOVED','PROVIDER_CLEANUP_PENDING','BACKUPS_SCHEDULED','COMPLETED','REJECTED')),
  impact                  jsonb NOT NULL DEFAULT '{}'::jsonb,
  hold_reason             text,
  completion_evidence_ref text,
  received_at             timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE audit_log (
  seq            bigserial PRIMARY KEY,
  tenant_id      text NOT NULL,
  aggregate_type text NOT NULL,
  aggregate_id   text NOT NULL,
  from_state     text,
  to_state       text,
  event          text NOT NULL,
  reason         text NOT NULL,
  actor          text NOT NULL,
  at             timestamptz NOT NULL DEFAULT now(),
  evidence_refs  text[] NOT NULL DEFAULT '{}'
);
CREATE INDEX audit_log_aggregate_idx ON audit_log(aggregate_type, aggregate_id, seq);
-- audit_log is append-only: no UPDATE/DELETE grants exist for any service role (see roles-and-policies.sql)
