# Assumptions and decisions

Architectural decisions are proposals adopted for this package; they are resolved for engineering unless an experiment in DELIVERY_PLAN.md names them as open. Source B's ADR-001 to ADR-010 are adopted unchanged. ADR-011 onward are new.

## Adopted from Source B

| ADR | Decision |
| --- | --- |
| ADR-001 | Engineering credentials are separate from runtime credentials. |
| ADR-002 | Plan state and artifacts live outside the agent workspace. |
| ADR-003 | Typed contracts and a registry-backed compiler bound generated prose into inspectable operations. |
| ADR-004 | One durable lifecycle owner per aggregate. |
| ADR-005 | Facts carry provenance and multiple time axes. |
| ADR-006 | Learning setup is a generated deployment, not customer homework. |
| ADR-007 | Promotion is gated independently of the builder. |
| ADR-008 | Model aliases resolve to immutable versions per case. |
| ADR-009 | Uncertain external effects are UNKNOWN, never retried blindly. |
| ADR-010 | Implementation autonomy is measured separately from runtime autonomy. |

## New decisions

| ADR | Decision | Rationale | Upgrade or reversal trigger |
| --- | --- | --- | --- |
| ADR-011 | PostgreSQL 16 is the authoritative lifecycle store and the event bus (outbox table with LISTEN/NOTIFY and polling consumers). No Kafka or NATS in release 1. | One source of truth for transitions and events; the first-customer workload (ARCHITECTURE.md §7) is far below the point where a broker pays for itself. | Sustained > 500 events/s for 7 days, or > 3 consumers needing independent replay beyond 7 days, or a second region. |
| ADR-012 | Temporal (self-hosted or Cloud) executes business cases and build steps; every authoritative transition is committed in PostgreSQL by the control service with compare-and-set; Temporal histories are never the source of truth. | Durable waits, timers and retries are solved problems; two authorities for one lifecycle cause ambiguous retries (B ADR-004). | None planned; a second orchestrator is forbidden. |
| ADR-013 | Compute is container services (ECS or Nomad on VMs) with one region (us-east-1); no Kubernetes in release 1. | Operational burden; no requirement needs it. | > 25 services, multi-region, or a platform team of 4 or more. |
| ADR-014 | Self-hosted Nango is the rung-2 substrate for OAuth, token lifecycle and sync deployment; Plumb's connector runtime and gateway sit in front of it and own policy. Airbyte is deferred. | Reuses a documented management surface without ceding the trust boundary (B [S03]). | Nango cannot represent a required provider or its per-user auth; then a rung-3 adapter is generated. |
| ADR-015 | Infrastructure changes go through Pulumi Automation API behind a narrow deployment adapter (preview, update, refresh) with delegated short-lived credentials, state lock and ownership tags. | Programmatic preview and apply with a stable approval boundary (B [S05]). | Provider or module unsupported by Pulumi; then a reviewed Terraform module path with the same adapter contract. |
| ADR-016 | No dedicated model serving in release 1: hosted APIs through the model gateway, provider fine-tuning jobs through training adapters; multi-adapter self-serving only when a tenant's steady traffic exceeds 50% utilization of one accelerator for 30 days. | A small model at low utilization is not cheaper than an API (B§14). | The utilization trigger, or a data-terms requirement no hosted provider meets. |
| ADR-017 | The Blueprint is a rendered view over seven artifacts with their own digests; approvals are detached. | Independent lifecycles and no self-referential digests (R-02). | None. |
| ADR-018 | Three authorization layers with per-operation argument-aware enforcement; agent levels are labels. | R-03, R-04. | None. |
| ADR-019 | Source-first evidence; desktop capture earns its scope through EXP-01. | R-17. | EXP-01 result. |
| ADR-020 | Four field protection classes replace blanket masking. | R-06. | None. |
| ADR-021 | Release 1 delivers review_package_accepted; accounting writes are a later certified operation. | R-13, R-19. | IC-012 tests pass and the domain owner approves. |
| ADR-022 | Trusted interpreter over validated primitives; code generation only for rung-3 adapters, verified independently. | M§11. | A certified primitive library covering 90% of steps in three verticals. |
| ADR-023 | Contracts in Python with Pydantic as the single schema source; TypeScript bindings are generated, never hand-written. | DC-001. | None. |

## Assumptions (proposed until measured)

| ID | Assumption | Where used | How it is tested |
| --- | --- | --- | --- |
| AS-01 | First customer: 10 to 50 employees, QuickBooks Online, Google Workspace, Drive; roughly 100 to 200 monthly obligations; 1,000 meaningful events per employee per day. | ARCHITECTURE.md §7 | Inventory of the first customer |
| AS-02 | Proposed service objectives: 99.9% monthly control-plane availability; p95 event-to-case propagation under 60 s; connector staleness visible within 5 minutes of its deadline; kill switch stops new dispatch within 60 s; revocation propagates within 60 s. | ARCHITECTURE.md §6 | Load tests in WP-07 |
| AS-03 | Replay and shadow sample sizes are set by opportunities for failure (at least 25 opportunities for each high-severity failure class in canary; shadow until 40 opportunities for the top three failure classes), not by a universal count. | spec/authority-and-verification.md | Per release, recorded in the attestation |
| AS-04 | Unit costs per customer per month at first-customer scale are in the low hundreds of dollars of provider usage; see ARCHITECTURE.md §7 for arithmetic and sensitivity. | ARCHITECTURE.md | Ledgers after month 1 |
| AS-05 | Per-customer manual engineering falls below 4 hours per deployment by the third replication customer. | acceptance/autonomy-benchmark.md | Benchmark |
| AS-06 | Staffing: 5 to 6 engineers plus a fractional domain expert (DELIVERY_PLAN.md). | DELIVERY_PLAN.md | Hiring |
| AS-07 | Backup rotation window is 35 days; removal of backups completes within it. | operations/removal-and-offboarding.md | Drill |
| AS-08 | Legal questions listed in spec/privacy-and-security.md §8 need qualified review before the first production customer; no jurisdiction rule in this package is asserted as law. | spec/privacy-and-security.md | Counsel review gate |
