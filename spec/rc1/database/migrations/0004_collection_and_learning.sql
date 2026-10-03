-- 0004: integrations, collectors and health, datasets, rows, training jobs, model versions.
SET search_path TO plumb;

CREATE TABLE integrations (
  integration_id        text PRIMARY KEY,
  tenant_id             text NOT NULL REFERENCES tenants(tenant_id),
  provider              text NOT NULL,
  account_ref           text NOT NULL,
  connection_grantor_id text NOT NULL REFERENCES principals(principal_id),
  rung                  smallint NOT NULL CHECK (rung BETWEEN 1 AND 5),
  body                  jsonb NOT NULL,
  auth_ref              text NOT NULL,
  capability_manifest_digest text,
  maintenance_exposure  text NOT NULL CHECK (maintenance_exposure IN ('library','generated','ui_bridge')),
  health                text NOT NULL DEFAULT 'unknown',
  version               integer NOT NULL DEFAULT 1
);

CREATE TABLE collectors (
  collection_id       text PRIMARY KEY,
  tenant_id           text NOT NULL REFERENCES tenants(tenant_id),
  integration_id      text NOT NULL REFERENCES integrations(integration_id),
  body                jsonb NOT NULL,
  state               text NOT NULL CHECK (state IN ('PLANNED','SHADOW','BACKFILLING','RECONCILING','ACTIVE','DEGRADED','PAUSED','RETIRED')),
  watermark           timestamptz,
  backfill_from       timestamptz,
  transformation_version text NOT NULL,
  deployment_ref      text,
  activated_at        timestamptz,
  reason              text,
  version             integer NOT NULL DEFAULT 1
);

CREATE TABLE collector_health (
  collection_id    text NOT NULL REFERENCES collectors(collection_id),
  observed_at      timestamptz NOT NULL,
  freshness_s      integer,
  lag_s            integer,
  coverage_state   text NOT NULL CHECK (coverage_state IN ('complete','bounded','sampled','unknown')),
  quarantine_count integer NOT NULL DEFAULT 0,
  failures         integer NOT NULL DEFAULT 0,
  PRIMARY KEY (collection_id, observed_at)
);

CREATE TABLE datasets (
  dataset_id          text NOT NULL,
  version             integer NOT NULL,
  tenant_id           text NOT NULL REFERENCES tenants(tenant_id),
  task_definition_ref text NOT NULL,
  manifest            jsonb NOT NULL,
  manifest_digest     text,
  state               text NOT NULL CHECK (state IN ('PROPOSED','MATERIALIZING','QUARANTINED','VERIFIED','SUPERSEDED','UNAVAILABLE')),
  unavailable_reason  text,
  successor           text,
  PRIMARY KEY (dataset_id, version)
);

CREATE TABLE dataset_rows (
  dataset_id             text NOT NULL,
  dataset_version        integer NOT NULL,
  example_id             text NOT NULL,
  family_id              text NOT NULL,
  tenant_id              text NOT NULL,
  permission_compartment text NOT NULL,
  role                   text NOT NULL CHECK (role IN ('training','development','calibration','regression','protected_acceptance','prospective_monitoring')),
  input_snapshot_refs    text[] NOT NULL,
  decision_time          timestamptz NOT NULL,
  availability_evidence  text NOT NULL,
  target_evidence        text NOT NULL,
  label_authority        text NOT NULL,
  label_status           text NOT NULL CHECK (label_status IN ('provisional','mature','amended','disputed')),
  policy_version         text NOT NULL,
  transformation_version text NOT NULL,
  allowed_purposes       text[] NOT NULL,
  exclusion_reason       text,
  exposed_to_repair      boolean NOT NULL DEFAULT false,
  PRIMARY KEY (dataset_id, dataset_version, example_id),
  FOREIGN KEY (dataset_id, dataset_version) REFERENCES datasets(dataset_id, version)
);
CREATE INDEX dataset_rows_family_idx ON dataset_rows(dataset_id, dataset_version, family_id);

CREATE TABLE training_jobs (
  training_id          text PRIMARY KEY,
  tenant_id            text NOT NULL REFERENCES tenants(tenant_id),
  dataset_id           text NOT NULL,
  dataset_version      integer NOT NULL,
  spec                 jsonb NOT NULL,
  submission_identity  text NOT NULL UNIQUE,
  provider_job_id      text,
  state                text NOT NULL CHECK (state IN ('PLANNED','SUBMITTED','SUBMISSION_UNKNOWN','RUNNING','CANDIDATE','FAILED','CANCELLED')),
  reservation_id       text REFERENCES budget_reservations(reservation_id),
  reason               text,
  FOREIGN KEY (dataset_id, dataset_version) REFERENCES datasets(dataset_id, version)
);

CREATE TABLE model_versions (
  model_version_id   text PRIMARY KEY,
  tenant_id          text NOT NULL REFERENCES tenants(tenant_id),
  training_id        text REFERENCES training_jobs(training_id),
  provider_identity  text NOT NULL,
  strongest_identity text NOT NULL,
  artifact_digest    text,
  serving_audience   text[] NOT NULL,
  evaluation_ref     text,
  status             text NOT NULL CHECK (status IN ('candidate','promoted','retired','quarantined'))
);
