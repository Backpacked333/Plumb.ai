-- 0002: evidence events, business objects, facts, obligations, OCEL-style links, identity candidates.
SET search_path TO plumb;

CREATE TABLE evidence_events (
  event_id             text PRIMARY KEY,
  tenant_id            text NOT NULL REFERENCES tenants(tenant_id),
  source_provider      text NOT NULL,
  source_account_ref   text NOT NULL,
  external_record_id   text,
  external_version     text,
  modality             text NOT NULL CHECK (modality IN ('screen','accessibility','dom','message','document','recording','api_record','runtime_proof','interview')),
  event_time           timestamptz,
  valid_from           timestamptz,
  valid_to             timestamptz,
  source_recorded_time timestamptz,
  available_time       timestamptz,
  ingested_time        timestamptz NOT NULL DEFAULT now(),
  content_digest       text NOT NULL,
  content_ref          text,
  access_policy_ref    text NOT NULL,
  retention_class      text NOT NULL,
  extraction_version   text NOT NULL,
  protection           jsonb NOT NULL DEFAULT '{}'::jsonb,
  labels               jsonb NOT NULL DEFAULT '{}'::jsonb,
  tombstoned_at        timestamptz,
  UNIQUE (tenant_id, source_provider, source_account_ref, external_record_id, external_version)
);
CREATE INDEX evidence_events_tenant_time_idx ON evidence_events(tenant_id, event_time);
CREATE INDEX evidence_events_tenant_ingested_idx ON evidence_events(tenant_id, ingested_time);

CREATE TABLE business_objects (
  object_id        text PRIMARY KEY,
  tenant_id        text NOT NULL REFERENCES tenants(tenant_id),
  object_type      text NOT NULL,
  external_ids     jsonb NOT NULL DEFAULT '{}'::jsonb,
  attributes       jsonb NOT NULL DEFAULT '{}'::jsonb,
  identity_status  text NOT NULL CHECK (identity_status IN ('provisional','confirmed','merged','split')),
  merged_into      text REFERENCES business_objects(object_id),
  version          integer NOT NULL DEFAULT 1,
  updated_at       timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX business_objects_tenant_type_idx ON business_objects(tenant_id, object_type);

CREATE TABLE object_attribute_history (
  object_id        text NOT NULL REFERENCES business_objects(object_id),
  tenant_id        text NOT NULL,
  attribute        text NOT NULL,
  value            jsonb,
  valid_from       timestamptz NOT NULL,
  valid_to         timestamptz,
  evidence_event_id text REFERENCES evidence_events(event_id),
  PRIMARY KEY (object_id, attribute, valid_from)
);

CREATE TABLE event_object_links (
  event_id     text NOT NULL REFERENCES evidence_events(event_id),
  object_id    text NOT NULL REFERENCES business_objects(object_id),
  tenant_id    text NOT NULL,
  qualifier    text NOT NULL,
  confidence   numeric(4,3) CHECK (confidence BETWEEN 0 AND 1),
  PRIMARY KEY (event_id, object_id, qualifier)
);

CREATE TABLE object_object_links (
  from_object_id text NOT NULL REFERENCES business_objects(object_id),
  to_object_id   text NOT NULL REFERENCES business_objects(object_id),
  tenant_id      text NOT NULL,
  qualifier      text NOT NULL,
  valid_from     timestamptz NOT NULL,
  valid_to       timestamptz,
  PRIMARY KEY (from_object_id, to_object_id, qualifier, valid_from)
);

CREATE TABLE identity_candidates (
  candidate_id   bigserial PRIMARY KEY,
  tenant_id      text NOT NULL,
  surface        text NOT NULL,
  object_id      text NOT NULL REFERENCES business_objects(object_id),
  score          numeric(4,3) NOT NULL,
  evidence_event_id text REFERENCES evidence_events(event_id),
  status         text NOT NULL CHECK (status IN ('candidate','confirmed','rejected')),
  decided_by     text,
  decided_at     timestamptz
);

CREATE TABLE facts (
  fact_id            text PRIMARY KEY,
  tenant_id          text NOT NULL REFERENCES tenants(tenant_id),
  subject_object_id  text NOT NULL REFERENCES business_objects(object_id),
  predicate          text NOT NULL,
  value              jsonb,
  status             text NOT NULL CHECK (status IN ('observed','inferred','confirmed','disputed','stale','superseded')),
  evidence_event_ids text[] NOT NULL CHECK (cardinality(evidence_event_ids) >= 1),
  derivation_version text NOT NULL,
  confidence         numeric(4,3),
  valid_from         timestamptz,
  valid_to           timestamptz,
  source_of_record   text,
  superseded_by      text,
  CHECK (status <> 'confirmed' OR confidence IS NULL OR confidence = 1)
);
CREATE INDEX facts_subject_predicate_idx ON facts(subject_object_id, predicate) WHERE status IN ('observed','inferred','confirmed');

CREATE TABLE obligations (
  obligation_id          text PRIMARY KEY,
  tenant_id              text NOT NULL REFERENCES tenants(tenant_id),
  obligor_object_id      text NOT NULL REFERENCES business_objects(object_id),
  obligee_object_id      text NOT NULL REFERENCES business_objects(object_id),
  engagement_object_id   text REFERENCES business_objects(object_id),
  case_key               jsonb NOT NULL,
  rule_version           text NOT NULL,
  fulfillment_predicate  text NOT NULL,
  due_at                 timestamptz,
  status                 text NOT NULL CHECK (status IN ('open','partially_satisfied','satisfied','exempt','expired','reopened','superseded')),
  epoch                  integer NOT NULL DEFAULT 1 CHECK (epoch >= 1),
  recurrence             text,
  version                integer NOT NULL DEFAULT 1,
  UNIQUE (tenant_id, obligor_object_id, fulfillment_predicate, case_key, epoch)
);
CREATE INDEX obligations_open_idx ON obligations(tenant_id, status, due_at);
