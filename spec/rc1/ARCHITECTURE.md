# Architecture

One modular control service, isolated build workers, a trusted gateway and verifier, PostgreSQL as the authoritative store and bus, Temporal for durable execution. Logical trust boundaries are enforced even where services share a deployment. Every technology choice below ties to a requirement and an upgrade trigger (ASSUMPTIONS_AND_DECISIONS.md ADR-011 to ADR-016).

## 1. Logical domains and trust boundaries

| Domain | Owns | Trust | Credentials |
| --- | --- | --- | --- |
| Control service | Tenants, grants, envelopes, approvals, inventories, opportunities, solutions, builds and steps, releases, cases, ledgers; every guarded transition | Trusted | plumb_control DB role; no provider credentials |
| Evidence workers | Source reads through the connector runtime, capture normalization, protection classes, labeling, object resolution, process mining, OCEL export | Trusted, data-plane | plumb_runtime role scoped to ingestion operations; provider read tokens via vault |
| Engineering workers | Planning, generated adapters, mappings, collectors, datasets, experiments, workflow compilation; run inside disposable sandboxes | Untrusted output, bounded authority | plumb_builder role; sandbox-scoped capability grants; never production credentials |
| Verifier | Protected acceptance bundles, replay, shadow scoring, attestations, signing | Trusted root | plumb_verifier role; signing key in HSM or KMS; read access to artifacts and sandboxes |
| Policy and action gateway | Authorization of every operation with arguments, credential resolution, budgets, effect identity, outbox dispatch, receipts | Trusted root | plumb_runtime role; provider write tokens via vault, per operation |
| Business workers | Durable cases on Temporal, approved tool calls through the gateway, human waits | Trusted execution, no direct provider access | Call the gateway only |
| Artifact and learning services | Content-addressed artifacts, dataset manifests, training adapters, model gateway, registry (MLflow-class for model metadata only) | Trusted | plumb_control for metadata; provider training credentials via vault |
| Studio | Goals, evidence coverage, proposals, review, blockers, outcomes, costs; companion review surface | Untrusted client | User sessions; all mutations go through the control-plane API |
| Desktop agent and browser extension | Capture, on-device protection, local queue, worker controls | Untrusted client | Device identity certificate; sync of envelopes only |

A compromised engineering worker or a prompt-injected document can at most propose: it cannot issue an attestation (role has no INSERT on attestations), cannot decide an approval (nonce plus authenticated approver), cannot dispatch an effect (gateway re-checks authority with arguments), cannot widen an envelope (derived tasks are compiled against the same or narrower authority) and cannot reach a destination outside the egress allow-list. This is the property the adversarial catalog tests (acceptance/production-catalog.md, group Security and privacy).

## 2. Chosen initial stack

| Concern | Choice | Requirement | Upgrade trigger |
| --- | --- | --- | --- |
| Language and contracts | Python 3.12, Pydantic v2 models as schema source (DC-001); TypeScript for Studio and generated bindings | DC-001 | None |
| Authoritative store and event bus | PostgreSQL 16, schema plumb, outbox table, LISTEN/NOTIFY plus polling consumers | SR-012, SR-110 | ADR-011 trigger |
| Durable execution | Temporal; one workflow per case keyed by case id and release epoch; activities call the control service with idempotency keys | IC-015 | None |
| Integration substrate | Self-hosted Nango for OAuth, token lifecycle, sync deployment (rung 2); Plumb connector runtime in front | IC-009 | ADR-014 trigger |
| Sandboxes | Firecracker-class microVMs (provider-hosted) with egress allow-list, no persistent disk, scoped grants | SR-059, SI-009 | None |
| Coding-agent harness | Provider-neutral adapter; Claude Code and Agent SDK class or equivalent registered as a Market part | SR-059 | Per Market freshness |
| Infrastructure | Pulumi Automation API behind the deployment adapter | IC-014 | ADR-015 trigger |
| Models | Hosted APIs through the model gateway; provider fine-tuning via training adapters; no self-serving | ADR-016 | Utilization trigger |
| Object storage | S3-compatible, per-tenant prefix and KMS key, content-addressed artifacts | SI-002 | None |
| Secrets | Managed vault with per-tenant namespaces; short-lived leases to execution paths | SI-009 | None |
| Observability | OpenTelemetry traces and metrics with pinned conventions; no payloads by default | DC-025 | None |
| Compute | ECS or Nomad on VMs, single region us-east-1 | ADR-013 | ADR-013 trigger |

## 3. Data flow

1. A grantor connects a provider; the OAuth callback verifies provider identity and records a SourceGrant (purposes, retention, processors).
2. The inventory job probes each granted account through the connector runtime and records Capabilities with verification levels.
3. Evidence workers backfill and watch sources through collectors (CollectionSpecs under a discovery purpose), apply protection classes, label, resolve objects and write EvidenceEvents, objects, links, Facts and Obligations.
4. Discovery assembles EvidencePackets under a knowledge boundary and produces OpportunitySpecs through the three routes; the owner accepts an objective.
5. The Sourcer searches whole-system candidates against the Market and produces a SolutionSpec with a decision record; an implement approval is required when impact exceeds the envelope ceiling.
6. The compiler produces a BuildPlan, validates it (twelve passes) and the build runs: steps are leased with fencing tokens, executed in sandboxes, results committed, attestations requested.
7. The Verifier runs protected checks and issues attestations; a ReleaseManifest composes the digests.
8. Release activation requires current authority; shadow and canary gates apply; the runtime creates cases on triggers, waits durably, asks for review through verified surfaces and dispatches ActionIntents through the gateway and effect ledger.
9. Every effect's receipt and postcondition, every review decision, every usage record flow back as evidence, taps, ledgers and outcome observations.

## 4. Handoff between PostgreSQL and Temporal (IC-015)

Temporal executes; PostgreSQL decides. A Temporal activity that changes lifecycle state calls the control service with the aggregate version and an idempotency key; the control service fires the guarded machine, commits the state and the outbox event in one transaction and returns the new version. The Temporal workflow stores only the returned version in its history. If Temporal is unavailable, no state changes (nothing is lost; cases wait). If PostgreSQL is unavailable, activities fail closed and retry with backoff; nothing is dispatched. On recovery a workflow re-reads the aggregate version before continuing; a stale history step is a no-op because the control service's compare-and-set rejects it.

## 5. Tenancy and isolation (SI-002)

Rows carry tenant_id; RLS with FORCE applies to every tenant table; service roles have NOBYPASSRLS and own nothing; the migrator owns tables and has no login during operation; the application sets plumb.tenant_id from the authenticated credential at connection checkout; object storage uses per-tenant prefixes and keys; retrieval indexes, caches, workspaces, queues, logs, adapters and training jobs are namespaced by tenant and compartment. Client-level permissions within a tenant are enforced by permission compartments on evidence and dataset rows and by audience lists on models (SR-077).

## 6. Service objectives (proposed, AS-02)

| Objective | Target | Measurement | Exclusion |
| --- | --- | --- | --- |
| Control-plane availability | 99.9% monthly | Synthetic probes on read and write paths | Provider outages reported separately |
| Event-to-case propagation | p95 under 60 s from ingestion | Outbox recorded_at to case transition | None |
| Connector staleness visible | within 5 minutes of the health deadline | Health rows | None |
| Kill switch | new dispatch stops within 60 s; in-flight requests listed within 5 minutes | Drill | Provider completion after acceptance is reported, not prevented |
| Revocation propagation | queued dispatches cancelled within 60 s | Drill | None |
| Approval handling | review item delivered within 5 minutes; expiry enforced to the second | Audit | None |
| Policy or credential service unavailable | reads continue, writes fail closed | Chaos test | None |

Error budget response: a breached objective pauses rollouts of new releases for that tenant until the postmortem is filed.

## 7. Workload model and cost arithmetic (proposed, AS-01, AS-04)

First customer: 30 employees x 1,000 meaningful events per day = 30,000 events per day, 0.35 per second average, about 7 per second at a 20x peak; 150 obligations per month; 150 cases per month with roughly 10 effects each = 1,500 effects per month. Early multi-tenant: 20 tenants, 600,000 events per day, 7 per second average, 140 per second peak. Proposed target: 100 tenants x 50 employees x 1,000 events = 5 million events per day, 58 per second average, 1,160 per second peak (Source B's sizing); at that point ADR-011's trigger is reached and a broker is justified.

Provider usage at first-customer scale: labeling 30,000 events per day at a blended $0.0005 per event = $15 per day; document extraction 300 pages per month at $0.01 = $3; drafting 150 requests at $0.02 = $3; evaluation and replay reruns on changed versions only, under $50 per month; sandbox hours for builds under $40 per build. Sensitivity: labeling dominates and scales with capture scope, which is why EXP-01 decides whether desktop capture is enrolled. Storage: events at 2 KB each = 60 MB per day, 22 GB per year before retention. Retention of frames is zero (device only).

## 8. Observability and correlation

Every trace carries tenant, goal, build, case, client or account, release, step, model call, verification, external effect and human intervention ids. Decision rationales are stored as short evidence-referenced records, not as hidden model deliberations. Payloads are off by default; a debug mode with explicit approval and expiry can capture masked payloads for one case.

## 9. Omissions

Multi-region, data residency outside the US, on-premise, and a public API for third parties are out of scope; the design does not preclude them.
