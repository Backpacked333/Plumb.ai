# Database invariants, indexes and migration order

The six migrations apply in numeric order; each is expand-only. They were parsed with pglast 8.4 for syntax and have not been applied to a PostgreSQL instance (VERIFICATION_REPORT.md). Role and RLS design is in roles-and-policies.sql.

## Invariants enforced in the schema

| Invariant | Mechanism | Requirement |
| --- | --- | --- |
| One live effect per effect slot | Partial unique index effects_one_live_per_slot (state not in CANCELLED, SUPERSEDED, FAILED_FINAL) | SR-082 |
| One active envelope version per envelope id | Partial unique index autonomy_envelopes_one_active | SR-002 |
| One active release per workflow | Partial unique index releases_one_active_per_workflow | SR-116 |
| One live lease per step | Partial unique index task_leases_one_live | SR-083 |
| Approvals cannot bind their own id | CHECK (NOT (approval_id = ANY (bound_digests))) | SR-052 |
| Nonce single use | UNIQUE (nonce) plus nonce_consumed_at | SI-011 |
| Confirmed facts carry no residual confidence | CHECK on facts | SR-032 |
| Receipt deduplication | UNIQUE (provider, provider_request_id) | SR-087 |
| Effect attempts are ordered and unique | UNIQUE (effect_id, attempt_no) | SR-083 |
| Case uniqueness per workflow, key and epoch | UNIQUE (tenant_id, workflow_id, case_key, obligation_epoch) | SR-034 |
| Obligation uniqueness per obligor, predicate, key and epoch | UNIQUE on obligations | SR-092 |
| Billable unit uniqueness per case, epoch, predicate | UNIQUE on billable_units | DC-024 |
| Training submission identity unique | UNIQUE (submission_identity) | SR-072 |
| Consumer processed events | PRIMARY KEY (consumer_id, event_id) in consumer_offsets | SR-113 |
| Outbox event uniqueness per aggregate version | UNIQUE (aggregate_type, aggregate_id, aggregate_version, event_type) | SR-110 |
| Audit append-only | No UPDATE or DELETE grants to any service role | DC-025 |

## Invariants enforced by the application (not expressible in DDL)

Guarded transitions (SR-010), argument-aware authorization (SI-005), knowledge-boundary leakage checks on datasets (SR-094), protection classes at ingestion (DC-005), tenant setting on connection checkout (SI-002).

## Indexes and rationale

Case lookups by tenant and state; external source identity on evidence events; ready steps; outstanding UNKNOWN effects; unpublished outbox rows; open dependencies and review items; attestations by digest (GIN). Large append-only tables (evidence_events, outbox, audit_log, usage_records) are partitioned by month only after measured need (Source B's rule), with the trigger at 50 million rows or a p95 insert latency over 20 ms.

## Migration rules

Expand, backfill, validate, contract. Readers and writers for a new column ship before the old column is dropped; old workers drain before contract; destructive migrations require an explicit approval and a verified restore. Rollback of a migration never re-runs effects: dispatch stays disabled until effect and case reconciliation confirms no duplicate actions (operations/incident-and-recovery.md).

## Tenant isolation testing

Isolation is tested with the actual runtime roles against PostgreSQL (IG-008): a plumb_runtime session with plumb.tenant_id set to tenant A must get zero rows from tenant B on every RLS table, plumb_builder must fail to INSERT into verification_attestations and approvals, plumb_reporting must fail to SELECT evidence_events. An in-memory substitute does not count.
