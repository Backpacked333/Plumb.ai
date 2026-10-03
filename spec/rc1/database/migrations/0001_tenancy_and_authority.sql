-- 0001: tenancy, principals, grants, envelopes, approvals. Expand-only. Tenant columns are NOT NULL everywhere.
CREATE SCHEMA IF NOT EXISTS plumb;
SET search_path TO plumb;

CREATE TABLE tenants (
  tenant_id        text PRIMARY KEY,
  display_name     text NOT NULL,
  region           text NOT NULL,
  kms_key_ref      text NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE principals (
  principal_id     text PRIMARY KEY,
  tenant_id        text NOT NULL REFERENCES tenants(tenant_id),
  kind             text NOT NULL CHECK (kind IN ('platform_operator','tenant_owner','employee','domain_approver','client_grantor','sponsor','service_identity','build_worker','runtime_worker','verifier','integration_manager')),
  display_name     text,
  roles            text[] NOT NULL DEFAULT '{}',
  active           boolean NOT NULL DEFAULT true,
  deprovisioned_at timestamptz
);
CREATE INDEX principals_tenant_idx ON principals(tenant_id);

CREATE TABLE source_grants (
  grant_id             text PRIMARY KEY,
  tenant_id            text NOT NULL REFERENCES tenants(tenant_id),
  grantor_principal_id text NOT NULL REFERENCES principals(principal_id),
  provider             text NOT NULL,
  account_ref          text NOT NULL,
  entity_scope         text[] NOT NULL DEFAULT '{}',
  field_scope          text[] NOT NULL DEFAULT '{}',
  purposes             text[] NOT NULL,
  processors_allowed   text[] NOT NULL DEFAULT '{}',
  regions_allowed      text[] NOT NULL DEFAULT '{}',
  retention_days       integer NOT NULL CHECK (retention_days >= 1),
  history_from         timestamptz,
  granted_at           timestamptz NOT NULL,
  expires_at           timestamptz,
  status               text NOT NULL CHECK (status IN ('active','expired','revoked')),
  terms_version        text,
  revoked_at           timestamptz,
  UNIQUE (tenant_id, provider, account_ref, grantor_principal_id, granted_at)
);
CREATE INDEX source_grants_tenant_status_idx ON source_grants(tenant_id, status);

CREATE TABLE autonomy_envelopes (
  envelope_id          text NOT NULL,
  version              integer NOT NULL CHECK (version >= 1),
  tenant_id            text NOT NULL REFERENCES tenants(tenant_id),
  owner_principal_id   text NOT NULL REFERENCES principals(principal_id),
  body                 jsonb NOT NULL,
  content_digest       text NOT NULL,
  approval_id          text,
  status               text NOT NULL CHECK (status IN ('draft','active','expired','revoked')),
  expires_at           timestamptz NOT NULL,
  created_at           timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (envelope_id, version)
);
-- at most one active version per envelope id
CREATE UNIQUE INDEX autonomy_envelopes_one_active ON autonomy_envelopes(envelope_id) WHERE status = 'active';

CREATE TABLE approvals (
  approval_id            text PRIMARY KEY,
  tenant_id              text NOT NULL REFERENCES tenants(tenant_id),
  kind                   text NOT NULL CHECK (kind IN ('data_use','implement','release_activation','case_action','policy_change')),
  bound_digests          text[] NOT NULL CHECK (cardinality(bound_digests) >= 1),
  prerequisite_state     jsonb NOT NULL DEFAULT '{}'::jsonb,
  scope                  jsonb NOT NULL DEFAULT '{}'::jsonb,
  approver_principal_id  text NOT NULL REFERENCES principals(principal_id),
  policy_version         text NOT NULL,
  nonce                  text NOT NULL UNIQUE,
  nonce_consumed_at      timestamptz,
  requested_at           timestamptz NOT NULL,
  decided_at             timestamptz,
  expires_at             timestamptz NOT NULL,
  decision               text CHECK (decision IN ('granted','denied')),
  status                 text NOT NULL CHECK (status IN ('REQUESTED','GRANTED','DENIED','EXPIRED','REVOKED','INVALIDATED')),
  invalidation_reason    text,
  version                integer NOT NULL DEFAULT 1,
  CHECK (NOT (approval_id = ANY (bound_digests)))
);
CREATE INDEX approvals_tenant_status_idx ON approvals(tenant_id, status);

CREATE TABLE revocations (
  revocation_id   bigserial PRIMARY KEY,
  tenant_id       text NOT NULL REFERENCES tenants(tenant_id),
  subject_kind    text NOT NULL CHECK (subject_kind IN ('grant','approval','envelope')),
  subject_id      text NOT NULL,
  revoked_by      text NOT NULL REFERENCES principals(principal_id),
  revoked_at      timestamptz NOT NULL DEFAULT now(),
  propagation     jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX revocations_subject_idx ON revocations(subject_kind, subject_id);
