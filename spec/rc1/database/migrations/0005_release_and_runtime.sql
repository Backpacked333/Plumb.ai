-- 0005: releases, attestations, cases, review items, intents, effects, outbox, receipts, consumer offsets.
SET search_path TO plumb;

CREATE TABLE releases (
  release_id       text PRIMARY KEY,
  tenant_id        text NOT NULL REFERENCES tenants(tenant_id),
  build_id         text REFERENCES builds(build_id),
  manifest         jsonb NOT NULL,
  manifest_digest  text NOT NULL,
  policy_version   text NOT NULL,
  state            text NOT NULL CHECK (state IN ('CANDIDATE','VERIFIED','APPROVED','SHADOW','CANARY','ACTIVE','PAUSED','ROLLED_BACK','RETIRED')),
  approval_id      text REFERENCES approvals(approval_id),
  rolled_back_to   text REFERENCES releases(release_id),
  activated_at     timestamptz,
  reason           text,
  version          integer NOT NULL DEFAULT 1,
  UNIQUE (tenant_id, manifest_digest)
);
CREATE UNIQUE INDEX releases_one_active_per_workflow ON releases(tenant_id, (manifest->>'workflow_id')) WHERE state = 'ACTIVE';

CREATE TABLE verification_attestations (
  attestation_id     text PRIMARY KEY,
  tenant_id          text NOT NULL REFERENCES tenants(tenant_id),
  check_id           text NOT NULL,
  check_version      text NOT NULL,
  criteria_version   text NOT NULL,
  artifact_digests   text[] NOT NULL CHECK (cardinality(artifact_digests) >= 1),
  input_digests      text[] NOT NULL DEFAULT '{}',
  environment        text NOT NULL,
  account_scope      text[] NOT NULL DEFAULT '{}',
  data_role          text NOT NULL,
  outcome            text NOT NULL CHECK (outcome IN ('pass','pass_with_limitations','fail','inconclusive')),
  evidence_refs      text[] NOT NULL DEFAULT '{}',
  verifier_identity  text NOT NULL,
  issued_at          timestamptz NOT NULL,
  expires_at         timestamptz,
  invalidated_at     timestamptz,
  limitations        text[] NOT NULL DEFAULT '{}',
  signature          text
);
CREATE INDEX attestations_digest_idx ON verification_attestations USING gin (artifact_digests);

CREATE TABLE cases (
  case_id          text PRIMARY KEY,
  tenant_id        text NOT NULL REFERENCES tenants(tenant_id),
  workflow_id      text NOT NULL,
  case_key         jsonb NOT NULL,
  release_id       text NOT NULL REFERENCES releases(release_id),
  state            text NOT NULL CHECK (state IN ('CREATED','ACTIVE','WAITING_EXTERNAL','WAITING_REVIEW','COMPLETED','FAILED','CANCELLED','REOPENED')),
  version          integer NOT NULL DEFAULT 1,
  obligation_epoch integer NOT NULL DEFAULT 1,
  wait_until       timestamptz,
  completed_at     timestamptz,
  reason           text,
  UNIQUE (tenant_id, workflow_id, case_key, obligation_epoch)
);
CREATE INDEX cases_tenant_state_idx ON cases(tenant_id, state);

CREATE TABLE review_items (
  review_item_id          text PRIMARY KEY,
  tenant_id               text NOT NULL,
  case_id                 text NOT NULL REFERENCES cases(case_id),
  surface                 text NOT NULL,
  item_digest             text NOT NULL,
  case_version_at_creation integer NOT NULL,
  nonce                   text NOT NULL UNIQUE,
  status                  text NOT NULL CHECK (status IN ('open','decided','invalidated','expired','reassigned')),
  assigned_role           text NOT NULL,
  assigned_principal_id   text,
  decided_by              text,
  decision                text,
  decided_at              timestamptz,
  expires_at              timestamptz NOT NULL
);
CREATE INDEX review_items_open_idx ON review_items(tenant_id, status) WHERE status = 'open';

CREATE TABLE action_intents (
  intent_id              text PRIMARY KEY,
  tenant_id              text NOT NULL REFERENCES tenants(tenant_id),
  case_id                text NOT NULL REFERENCES cases(case_id),
  obligation_id          text REFERENCES obligations(obligation_id),
  obligation_epoch       integer NOT NULL,
  operation_id           text NOT NULL,
  provider               text NOT NULL,
  account_ref            text NOT NULL,
  effect_slot            text NOT NULL,
  logical_action_id      text NOT NULL UNIQUE,
  payload_digest         text NOT NULL,
  payload_ref            text NOT NULL,
  expected_state_versions jsonb NOT NULL,
  authority              jsonb NOT NULL,
  cost_reservation_id    text,
  retry_class            text NOT NULL,
  compensation_class     text NOT NULL,
  effect_class           text NOT NULL,
  supersedes_intent_id   text REFERENCES action_intents(intent_id),
  created_at             timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE effects (
  effect_id             text PRIMARY KEY,
  tenant_id             text NOT NULL REFERENCES tenants(tenant_id),
  intent_id             text NOT NULL REFERENCES action_intents(intent_id),
  effect_slot           text NOT NULL,
  state                 text NOT NULL CHECK (state IN ('RESERVED','DISPATCHING','DISPATCHED','UNKNOWN','CONFIRMED','NOT_OCCURRED','CONFLICT','NEEDS_HUMAN','CANCEL_REQUESTED','CANCELLED','SUPERSEDED','FAILED_FINAL','COMPENSATION_PENDING','COMPENSATED')),
  attempt_no            integer NOT NULL DEFAULT 0,
  max_attempts          integer NOT NULL DEFAULT 3,
  reconcile_attempts    integer NOT NULL DEFAULT 0,
  fencing_token         bigint NOT NULL DEFAULT 0,
  idempotency_key       text NOT NULL UNIQUE,
  first_dispatched_at   timestamptz,
  reconciliation        text,
  compensation_effect_id text REFERENCES effects(effect_id),
  reason                text,
  version               integer NOT NULL DEFAULT 1
);
-- One live effect per semantic slot, across restarts and releases (SR-082)
CREATE UNIQUE INDEX effects_one_live_per_slot ON effects(tenant_id, effect_slot) WHERE state NOT IN ('CANCELLED','SUPERSEDED','FAILED_FINAL');
CREATE INDEX effects_unknown_idx ON effects(tenant_id) WHERE state = 'UNKNOWN';

CREATE TABLE effect_attempts (
  attempt_id          bigserial PRIMARY KEY,
  effect_id           text NOT NULL REFERENCES effects(effect_id),
  attempt_no          integer NOT NULL,
  lease_id            text NOT NULL,
  fencing_token       bigint NOT NULL,
  idempotency_key     text NOT NULL,
  started_at          timestamptz NOT NULL,
  finished_at         timestamptz,
  result              text CHECK (result IN ('accepted','rejected','timeout','crashed','cancelled')),
  provider_request_id text,
  UNIQUE (effect_id, attempt_no)
);

CREATE TABLE receipts (
  receipt_id          text PRIMARY KEY,
  tenant_id           text NOT NULL,
  effect_id           text NOT NULL REFERENCES effects(effect_id),
  provider            text NOT NULL,
  provider_request_id text NOT NULL,
  provider_object_id  text,
  signature_valid     boolean NOT NULL,
  received_at         timestamptz NOT NULL DEFAULT now(),
  raw_ref             text,
  UNIQUE (provider, provider_request_id)
);

CREATE TABLE outbox (
  outbox_id        bigserial PRIMARY KEY,
  tenant_id        text NOT NULL,
  aggregate_type   text NOT NULL,
  aggregate_id     text NOT NULL,
  aggregate_version integer NOT NULL,
  event_id         text NOT NULL UNIQUE,
  event_type       text NOT NULL,
  schema_version   text NOT NULL,
  occurred_at      timestamptz NOT NULL,
  recorded_at      timestamptz NOT NULL DEFAULT now(),
  correlation_id   text NOT NULL,
  causation_id     text,
  payload          jsonb NOT NULL DEFAULT '{}'::jsonb,
  tombstone        boolean NOT NULL DEFAULT false,
  claimed_by       text,
  claimed_at       timestamptz,
  fencing_token    bigint,
  published_at     timestamptz,
  UNIQUE (aggregate_type, aggregate_id, aggregate_version, event_type)
);
CREATE INDEX outbox_unpublished_idx ON outbox(outbox_id) WHERE published_at IS NULL;

CREATE TABLE outbox_dead_letter (
  dead_id      bigserial PRIMARY KEY,
  event_id     text NOT NULL,
  consumer_id  text NOT NULL,
  last_error   text NOT NULL,
  attempts     integer NOT NULL,
  parked_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE consumer_offsets (
  consumer_id      text NOT NULL,
  event_id         text NOT NULL,
  processed_at     timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (consumer_id, event_id)
);
