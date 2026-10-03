-- 0003: inventory, capabilities, opportunities, solutions, artifacts, builds, steps, leases, budgets, dependencies.
SET search_path TO plumb;

CREATE TABLE artifacts (
  artifact_id      text NOT NULL,
  version          integer NOT NULL,
  tenant_id        text NOT NULL REFERENCES tenants(tenant_id),
  kind             text NOT NULL,
  content_digest   text NOT NULL,
  object_ref       text NOT NULL,
  producer         text NOT NULL,
  schema_version   text NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (artifact_id, version),
  UNIQUE (tenant_id, content_digest)
);
CREATE TABLE artifact_aliases (
  tenant_id    text NOT NULL,
  alias        text NOT NULL,
  artifact_id  text NOT NULL,
  version      integer NOT NULL,
  updated_at   timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, alias),
  FOREIGN KEY (artifact_id, version) REFERENCES artifacts(artifact_id, version)
);

CREATE TABLE environment_inventories (
  inventory_id   text PRIMARY KEY,
  tenant_id      text NOT NULL REFERENCES tenants(tenant_id),
  produced_at    timestamptz NOT NULL,
  body           jsonb NOT NULL,
  content_digest text NOT NULL
);

CREATE TABLE capabilities (
  tenant_id           text NOT NULL REFERENCES tenants(tenant_id),
  operation_id        text NOT NULL,
  account_ref         text NOT NULL,
  kind                text NOT NULL,
  verification_level  text NOT NULL CHECK (verification_level IN ('documented','locally_tested','sandbox_tested','account_verified','production_observed')),
  verified_at         timestamptz,
  verified_by         text,
  expires_at          timestamptz,
  limits              jsonb NOT NULL DEFAULT '{}'::jsonb,
  limitations         text[] NOT NULL DEFAULT '{}',
  evidence_ref        text,
  PRIMARY KEY (tenant_id, operation_id, account_ref)
);

CREATE TABLE opportunities (
  opportunity_id   text PRIMARY KEY,
  tenant_id        text NOT NULL REFERENCES tenants(tenant_id),
  route            text NOT NULL CHECK (route IN ('friction','unmet_obligation','new_capability')),
  body             jsonb NOT NULL,
  status           text NOT NULL CHECK (status IN ('hypothesis','evidenced','objective_accepted','infeasible','no_beneficial_intervention','superseded','retired')),
  objective_accepted_by text REFERENCES principals(principal_id),
  version          integer NOT NULL DEFAULT 1,
  content_digest   text NOT NULL
);

CREATE TABLE coverage_decisions (
  decision_id      text PRIMARY KEY,
  tenant_id        text NOT NULL,
  opportunity_id   text NOT NULL REFERENCES opportunities(opportunity_id),
  tier             text NOT NULL CHECK (tier IN ('exact_template','new_composition','agent_adaptation','agent_new_capability','unsupported')),
  criteria_version text NOT NULL,
  decided_at       timestamptz NOT NULL,
  rationale        text NOT NULL
);

CREATE TABLE solutions (
  solution_id      text PRIMARY KEY,
  tenant_id        text NOT NULL REFERENCES tenants(tenant_id),
  opportunity_id   text NOT NULL REFERENCES opportunities(opportunity_id),
  body             jsonb NOT NULL,
  impact_class     text NOT NULL CHECK (impact_class IN ('low','medium','high')),
  content_digest   text NOT NULL,
  implement_approval_id text REFERENCES approvals(approval_id)
);

CREATE TABLE builds (
  build_id         text PRIMARY KEY,
  tenant_id        text NOT NULL REFERENCES tenants(tenant_id),
  solution_id      text NOT NULL REFERENCES solutions(solution_id),
  envelope_id      text NOT NULL,
  envelope_version integer NOT NULL,
  plan_digest      text,
  state            text NOT NULL CHECK (state IN ('DRAFT','VALIDATED','RUNNING','WAITING_AUTH','WAITING_INPUT','VERIFYING','VERIFIED','FAILED','CANCELLED')),
  version          integer NOT NULL DEFAULT 1,
  reason           text,
  repair_attempts  integer NOT NULL DEFAULT 0,
  max_repair_attempts integer NOT NULL DEFAULT 5,
  started_at       timestamptz,
  verified_at      timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (envelope_id, envelope_version) REFERENCES autonomy_envelopes(envelope_id, version)
);
CREATE INDEX builds_tenant_state_idx ON builds(tenant_id, state);

CREATE TABLE build_steps (
  build_id         text NOT NULL REFERENCES builds(build_id),
  step_id          text NOT NULL,
  tenant_id        text NOT NULL,
  step_type        text NOT NULL,
  state            text NOT NULL CHECK (state IN ('PENDING','READY','RUNNING','RECONCILING','VERIFYING','VERIFIED','FAILED','BLOCKED','CANCELLED')),
  attempt_no       integer NOT NULL DEFAULT 0,
  max_attempts     integer NOT NULL,
  fencing_token    bigint NOT NULL DEFAULT 0,
  result_ref       text,
  output_digests   text[] NOT NULL DEFAULT '{}',
  verified_at      timestamptz,
  reason           text,
  PRIMARY KEY (build_id, step_id)
);
CREATE INDEX build_steps_ready_idx ON build_steps(tenant_id, state) WHERE state = 'READY';

CREATE TABLE task_leases (
  lease_id       text PRIMARY KEY,
  tenant_id      text NOT NULL,
  build_id       text NOT NULL,
  step_id        text NOT NULL,
  worker_id      text NOT NULL,
  fencing_token  bigint NOT NULL,
  acquired_at    timestamptz NOT NULL DEFAULT now(),
  expires_at     timestamptz NOT NULL,
  released_at    timestamptz,
  FOREIGN KEY (build_id, step_id) REFERENCES build_steps(build_id, step_id)
);
CREATE UNIQUE INDEX task_leases_one_live ON task_leases(build_id, step_id) WHERE released_at IS NULL;

CREATE TABLE budget_reservations (
  reservation_id text PRIMARY KEY,
  tenant_id      text NOT NULL,
  build_id       text NOT NULL REFERENCES builds(build_id),
  step_id        text,
  attempt_no     integer NOT NULL,
  reserved_minor bigint NOT NULL CHECK (reserved_minor >= 0),
  currency       char(3) NOT NULL,
  settled_minor  bigint,
  status         text NOT NULL CHECK (status IN ('reserved','settled','released'))
);
CREATE INDEX budget_reservations_build_idx ON budget_reservations(build_id, status);

CREATE TABLE external_dependencies (
  dependency_id      text PRIMARY KEY,
  tenant_id          text NOT NULL REFERENCES tenants(tenant_id),
  build_id           text NOT NULL REFERENCES builds(build_id),
  step_id            text,
  kind               text NOT NULL CHECK (kind IN ('authorization','business_decision','access','commitment','unsupported_capability')),
  question           text NOT NULL,
  options            jsonb NOT NULL DEFAULT '[]'::jsonb,
  respondent_role    text NOT NULL,
  default_after_hours integer,
  default_option     text,
  status             text NOT NULL CHECK (status IN ('open','resolved','withdrawn')),
  resolution         text,
  resolution_scope   text CHECK (resolution_scope IN ('this_build','this_tenant','this_vertical')),
  resolved_by        text REFERENCES principals(principal_id),
  resolved_at        timestamptz,
  version            integer NOT NULL DEFAULT 1
);
CREATE INDEX external_dependencies_open_idx ON external_dependencies(tenant_id, status) WHERE status = 'open';

CREATE TABLE failure_diagnostics (
  diagnostic_id  text PRIMARY KEY,
  tenant_id      text NOT NULL,
  build_id       text NOT NULL REFERENCES builds(build_id),
  step_id        text,
  attempt_no     integer NOT NULL,
  failure_class  text NOT NULL,
  hypothesis     text NOT NULL,
  change_made    text,
  tests_to_rerun text[] NOT NULL DEFAULT '{}',
  evidence_refs  text[] NOT NULL DEFAULT '{}',
  created_at     timestamptz NOT NULL DEFAULT now()
);
