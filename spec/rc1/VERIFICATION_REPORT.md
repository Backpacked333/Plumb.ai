# Verification report

As of 2026-10-03. This report states what was executed in this environment, what each check establishes and cannot establish, the adversarial design review, and separate readiness verdicts. Nothing was run against a live provider, a PostgreSQL instance, a sandbox or a customer.

## 1. Environment

Python 3.12.3 pydantic 2.13.5 pytest 9.1.1 hypothesis 6.168.3 pglast v8.4 jsonschema 4.26.0 openapi-spec-validator 0.9.0, Ubuntu 24.04 container, no network access to providers.

## 2. Executed commands and results

| Command | Result |
| --- | --- |
| `python3 tools/gen_schemas.py` | generated 37 schemas into /mnt/user-data/outputs/plumb-spec/contracts/generated-json-schema |
| `python3 tools/gen_fixtures.py` | wrote fixtures; failure cases: 29 |
| `python3 tools/gen_traceability.py` | wrote 260 rows to /mnt/user-data/outputs/plumb-spec/TRACEABILITY.csv |
| `python3 -m pytest -q` | 121 passed, 10 skipped in 9.10s |
| OpenAPI validation (`openapi_spec_validator.validate`) | valid, operations: 26 |
| PostgreSQL DDL parse (`pglast.parse_sql`) | database/migrations/0001_tenancy_and_authority.sql 13 statements; database/migrations/0002_evidence_and_knowledge.sql 14 statements; database/migrations/0003_discovery_and_build.sql 19 statements; database/migrations/0004_collection_and_learning.sql 9 statements; database/migrations/0005_release_and_runtime.sql 19 statements; database/migrations/0006_ledgers_removal_audit.sql 11 statements; database/roles-and-policies.sql 67 statements |
| `python3 tools/build_manifest.py` | see MANIFEST.json (SHA-256 per file, computed over the real files) |

Test breakdown: contract (schemas, fixtures, state tables, traceability, OpenAPI, events, plan validator on 3 accepted and 24 rejected plans), property and state machine (effect ledger scenarios AT-030 to AT-044 including a hypothesis property test over random claim, crash, expire, reconcile, restart sequences; guarded machines AT-050 to AT-056), security (gateway AT-060 to AT-069), adapter (collector convergence AT-083, AT-084, AT-086, AT-087; mock provider contract subset of IC-010). The 10 skipped tests are the integration gates IG-001 to IG-010, each skipped with its reason.

## 3. What each validator establishes and does not

| Check | Establishes | Does not establish |
| --- | --- | --- |
| Pydantic models and generated JSON Schema | Fixtures agree with the normative shapes; unknown fields are rejected; semantic port rules hold | Semantic correctness of any customer artifact |
| Plan validator | The twelve passes reject the catalogued defects and accept the three reference plans | Safety or correctness of generated adapter code |
| Guarded machines | Every tested transition requires its guards; invalid transitions and unregistered guards fail closed | That production services call the engine on every path |
| SQLite effect ledger | Slot deduplication across restarts, payload conflict and supersession, fencing, UNKNOWN reconciliation, receipt verification, revocation, cancellation, window expiry, compensation against a scripted provider | PostgreSQL isolation, distributed leases, real provider behaviour under partitions |
| Gateway | Argument-aware denial reasons for the catalogued authority and destination scenarios | Deployment-time credential resolution, SSRF, egress |
| Collector convergence | Version dedup, tombstones, overlap, resync, outage versus absence against a mock source | Provider pagination and look-back behaviour in production |
| OpenAPI validation | Structural validity of the 26-operation proposal and canonical-model references | Serialization compatibility or a running server |
| pglast | DDL syntax for six migrations and the roles file | Grants, RLS behaviour, performance; migrations were never applied |
| Traceability test | Every requirement is traced, every traced path exists, ids cited in code and the register are defined | That the prose is correct |

## 4. Not executed (release-blocking where marked)

Live API or connector calls (blocking: IG-001 to IG-005); OAuth consent flows; PostgreSQL migrations, roles and RLS behaviour (blocking: IG-008); sandbox isolation and egress enforcement (blocking: IG-009); artifact signing and HSM-held verifier keys (blocking); SSRF controls and dependency scanning (blocking); training adapter submission and reconciliation (IG-007); infrastructure preview and apply (IG-006); revocation propagation on a deployed control service (IG-010); load and chaos tests for AS-02; customer outcome measurement; counsel review of the legal questions (blocking before first production customer).

## 5. Cross-document consistency review

Reviewed as a customer owner, worker, integration engineer, data engineer, ML evaluator, security engineer, domain professional, on-call operator and a newly joining engineer. Issues found and resolved during the package build:

| Issue | Resolution |
| --- | --- |
| The effect machine listed CONFIRMED as terminal while allowing compensation from it | CONFIRMED is settled, not terminal; terminal states are CANCELLED, SUPERSEDED, FAILED_FINAL, COMPENSATED |
| Port resolution matched only direct dependencies, so a profile step's ports could not feed a step two edges away | Ports resolve to the nearest transitive producer; the accounting plan validates |
| The cross-tenant fixture resolved as a missing reference rather than a cross-tenant reference | The artifact registry carries a foreign-tenant artifact so P2 and P7 are exercised separately |
| REQUIREMENTS.md cited bare file names; the traceability test could not resolve them | Full paths everywhere; the test now enforces existence |
| OpenAPI flow-style descriptions containing commas broke parsing | Quoted; validation passes |
| Source A's "kill switch restores state" and "deleting an event deletes it everywhere" were inherited in early drafts | Replaced by the four-mechanism model and the removal state machine (R-07, R-12) |
| Source B's "review package versus close" distinction had no billing mechanics | BillableUnitRecord predicate equals the workflow completion predicate; unique per case, epoch and predicate (R-13) |
| Approval anti-replay had no mechanism | Nonce column with single-use semantics, POST-only decisions, 409 on reuse (SI-011) |

## 6. Adversarial design review

| Question | Answer in this design | Evidence |
| --- | --- | --- |
| Does any generated field create authority? | No. Approvals, attestations and completion are platform or human fields; StepResult is a proposal; the builder role has no INSERT on attestations or approvals | SI-001; roles-and-policies.sql; AT-053 |
| Can a builder alter its own definition of success? | No. Protected bundles, thresholds and keys belong to the Verifier role; repair cannot edit tests (SR-057); exposed rows leave acceptance | SI-013; AT-093 (gated) |
| Can stale approval authorize changed data? | No. Approvals bind digests and case version; a change invalidates (approval.yaml); the gateway re-checks digest and version at dispatch | AT-050; AT-062 |
| Can one tenant or client identifier leak into another path? | Tenant from credential; RLS under NOBYPASSRLS roles (unverified until IG-008); compartments on rows and models; caches keyed by compartment | SI-002; AT-061; AT-070 (gated) |
| Can a retry duplicate an external effect? | One live effect per slot (partial unique index); UNKNOWN until reconciliation; provider-keyed retries forbidden after the window; property test over random fault sequences | AT-031 to AT-044 |
| Can an apparently healthy collector be missing records? | Coverage state is three-valued; activation requires a real event; the watermark never advances past observed records; an empty page is not absence | AT-084; AT-087; IG-002 |
| Can a model train on a task it was not permitted to learn? | Purposes are checked at plan validation (P7) and dataset build; read is not train | SI-004; AT-022; AT-063 |
| Can a correction contaminate historical evaluation? | Corrections are scoped with impact sets; rows exposed to repair leave acceptance; knowledge boundaries are per input | SR-033; SR-094; SR-097 |
| Can a cheaper fallback violate processor or quality constraints? | Fallbacks are declared per task and pass the same processor checks; a forbidden fallback degrades to assist | SR-073; AT-072 (gated) |
| Can rollback claim to erase irreversible effects? | No. Four separate mechanisms; irreversible actions remain in audit with compensation as a new effect | SR-118; SR-119; AT-042 |
| Can a restore replay old business actions? | Dispatch stays disabled after restore until effect and case reconciliation; slots are global | operations/incident-and-recovery.md §6 |
| Can a reported success hide manual implementation? | Every human minute is a LaborRecord; "autonomous" requires zero engineering_intervention minutes; eligibility is frozen before outcome | PR-013; PR-014; AT-097 |
| Can the proposed first release produce actual business value? | It removes duplicate chasing with one external message class and delivers an accepted review package; value is measured prospectively, not assumed | PRODUCT_CONTRACT.md §3; acceptance/business-outcome-measurement.md |
| Were full capabilities quietly replaced by templates, manual configuration or recommendations? | The first release includes an agent-generated adaptation (Drive folder mapping) and a working collector; recommendation-only outputs are not a completion outcome | PR-001; acceptance/end-to-end-traces.md §1 |

Every normal and failure-path statement in REQUIREMENTS.md has an owner (subsystem), a state (the relevant machine), a contract (model or schema) and a test (local or catalogued). External dependencies are supported by documentation and marked with account-level verification requirements; none is certified.

## 7. Readiness verdicts

| Gate | Verdict | Basis |
| --- | --- | --- |
| Specification completeness | PASS for engineering start, with named omissions | 260 traced requirements; 14 subsystem specs; traces; catalog; omissions listed per spec file |
| Reference-artifact validation | PASS (local) | 121 passed, 10 skipped in 9.10s; schemas, OpenAPI and DDL syntax validated; SHA-256 manifest |
| Integration readiness | UNVERIFIED | IG-001 to IG-007 not run; no account-level verification exists |
| Security readiness | UNVERIFIED, with release-blocking items | Isolation, sandbox egress, signing, SSRF, dependency scanning unimplemented; counsel review pending |
| Customer-production readiness | FAIL (not built) | No deployed services; no customer; the thin complete loop (WP-06) has not been executed |

The specification is ready for an engineering team to start; the product remains unbuilt.
