# Product Backlog

- Status: Draft v0.1 (2026-10-04), proposed — requires founder ratification
- Owner: Product
- Basis: spec v0.2, [decision record](02-strategy-decisions.md)

Part of the product doc set ([index](README.md)). This backlog turns the [MVP scope](03-mvp-scope.md) and the phased plan in the [decision record](02-strategy-decisions.md) into epics and stories with testable acceptance criteria, each traced to requirements (PL), ADRs and acceptance scenarios (PA). Phase windows and the proposed catalog scenarios are in the [roadmap](04-roadmap.md); metric definitions are in [metrics](06-metrics.md); risks and kill criteria are in [risks and assumptions](07-risks-and-assumptions.md); partner obligations are in the [design-partner program](09-design-partner-program.md). Who the product is for is in the [product brief](01-product-brief.md).

Three kinds of statement appear, labeled where it matters:

| Label | Meaning |
|---|---|
| Spec requires | Normative text in [spec v0.2](../spec/Plumb_Autonomous_Implementation_Specification_v0.2.md), cited as "spec §N" or by requirement id, or a scenario in the [acceptance catalog](../acceptance/production_acceptance_catalog.yaml). |
| Package has | Code in the reference package today, named under "Starting point" with file paths. It is a local library with more than 800 local contract tests (counts in the [validation report](../VALIDATION_REPORT.md); the spec's "56 tests" in its header table and Appendix C is stale). Nothing is deployed or connected to a customer, no acceptance scenario has run against production, and the local tests do not validate models, business outcomes, tenant security, cloud isolation or integrations (spec §28). |
| Proposed | This backlog's proposal, derived from the decision record. Not ratified. |

Nothing in this backlog is built, deployed, validated or measured unless a "Package has" line says the local library provides it. Every threshold, budget, count and date is a hypothesis unless the spec or the catalog states it; each table says so once, and the thresholds are ratified in threshold sheet v1 (E24-S01).

---

## 1. How to read this backlog

### 1.1 Structure and ids

- **Epics** are E01 to E24. They are ordered roughly by when their first exit-critical work lands. E01, the effort ledger, comes first because the north star, engineering-intervention hours per verified deployment (EIH/VD), must be measurable from the first M1 build (D10).
- **Stories** are numbered within their epic: E01-S01, E01-S02 and so on. Ids are stable. A story that is dropped keeps its id and is marked "Withdrawn"; ids are never reused.
- **Each story** has a header line (id, title, phase, priority, trace), then three parts: *Story*, *Acceptance criteria* and *Starting point*.

### 1.2 Phases

Phases follow the decision record's phased plan exactly. Windows are hypotheses and start on the previous gate's exit.

| Phase | Name | Window (hypothesis) | Milestone |
|---|---|---|---|
| P0 | Commit and instrument | Weeks 0-2 (Oct 5-18, 2026) | none; governance and the effort ledger |
| P1 | M0: contracts, probes and ledger | Weeks 2-8 (Oct 19-Nov 29, 2026) | M0 |
| P2 | M1: tenant 1 integration-and-collection path | Weeks 8-14 (Nov 30, 2026-Jan 10, 2027) | M1 |
| P3 | M1R: reproduction on tenants 2 and 3 | Weeks 12-20 (Dec 28, 2026-Feb 21, 2027) | M1R |
| P4 | M3-lite: preparation-only review workflow, sandbox then production shadow | Weeks 14-22 (Jan 11-Mar 7, 2027) | M3-lite |
| P5 | Shadow results, gateway hardening and day-180 decision packet | Weeks 20-26 (Feb 22-Apr 4, 2027); day 180 is Apr 3, 2027 | none; first measurable deliverable |
| P6 | M4-accounting and M5 (after day 180) | Weeks 26-36 or later (Apr-Jun 2027), earliest. This window covers the Prepare-tier canary and ACTIVE closes, the Draft tier and the start of M5, not Send: the earliest policy-approved Send canary close is around July 2027 (about weeks 39-41), because the D6 calibration ladder needs at least two Draft closes | M4-accounting, M5 |
| Gated | Behind evidence gates, past P6 | Not scheduled | M2 (gated learning factory), M6 (second domain: laundry route preparation, then RFQ) |

Milestone labels M0 to M6 in the spec's §26 table keep their spec meaning. M1R and M3-lite are the decision record's labels: M1R is PL-063's "next milestone" pulled forward from the §26 M5 slot, and M3-lite is the preparation-only subset of §26 M3.

Release tiers: **Prepare** (preparation-only: shadow, then canary and ACTIVE with no external communication) is the MVP. **Draft** (mailbox drafts staff send) and **Send** (policy-approved sending, canary first) are gated on the production action gateway after day 180 (D3, D5); Send comes no earlier than about July 2027.

### 1.3 Priority

Priorities are Must, Should and Could. P0 to P6 are phase names only and are never used as priorities. Story headers write both, for example "Phase P2 · Priority Must". Priority is read against the story's own phase:

| Priority | Meaning |
|---|---|
| Must | Needed for the exit of the story's current phase. The phase cannot exit without it; most Must stories are named in, or directly produce, that phase's exit evidence in the decision record. |
| Should | Needed for the next phase, or in this phase's scope but not exit-critical. |
| Could | Later or gated: behind the Draft or Send gates, behind the M2 or M6 gates, or past P6. |

A story's phase is the phase whose exit needs it. Work may start earlier; for example, sandbox build work for M1 may begin from week 6 (decision record, P2). An epic's priority in the overview is the highest priority any of its stories carries in the epic's first phase.

### 1.4 Story fields

- **Story.** A user story in the form "As a <persona>, I want ... so that ...", using the canonical personas in section 1.6. A *System story* describes platform behavior with no direct human actor. An *Internal story* is governance or operating work owned by a named Plumb role.
- **Acceptance criteria.** Each criterion is testable and names its evidence:
  - finding codes of the existing checkers, for example CAPABILITY_MATURITY_INSUFFICIENT, PURPOSE_DENIED, APPROVAL_DIGEST_MISMATCH or OPERATING_PLAN_MISSING. New codes this backlog proposes are marked "(proposed code)";
  - lifecycle states of the seven state machines (spec §23), for example WAITING_AUTH, DEGRADED or UNKNOWN, and the 13 error classes of spec §22;
  - verifier attestations: a VerificationAttestation issued by a VERIFIER principal at a named level (SCHEMA_VALIDITY, ARTIFACT_INTEGRITY, INTEGRATION_BEHAVIOR, BUSINESS_OUTCOME or ECONOMIC_RESULT);
  - catalog scenarios. "PA-001 passes" means a verifier attestation produced in the intended environment, as the catalog requires; a builder's completion claim never counts.
- **Adaptations and proposals.** PA-013, PA-014, PA-016, PA-021, PA-023 and PA-024 are written for the laundry or industrial RFQ domains. Where this backlog runs them on accounting tenants, they are *accounting adaptations* and are never reported as passes of the original scenario (D4). Proposed catalog scenarios are defined and numbered PA-P01 to PA-P19 in the [roadmap](04-roadmap.md) section 6 (listed in E24-S05). This backlog cites them by those numbers; none is ever reported as the scenario it adapts.
- **Trace.** The requirement, ADR and scenario ids the story implements or is tested by.
- **Starting point.** What the reference package already provides, with file paths, or "None" for greenfield work.

### 1.5 Definition of done for every story (proposed)

1. The acceptance criteria are demonstrated in the environment they name: local, provider sandbox, or tenant production shadow.
2. Any completion state a customer can see is backed by a verifier attestation, never by an agent's message (spec App. A §6; PL-016, PL-042).
3. Every human minute spent on tenant resources while doing the work is in the effort ledger under the frozen rubric (PL-003; E01).
4. If a contract changed, the JSON Schemas are regenerated and `python3 -m plumb.schemas_tool.generate --check` passes; local tests pass; the OpenAPI validator reports zero unresolved references.
5. No secret, raw source content or other tenant's identifier appears in an artifact, log, trace or error (spec §22; PL-054).
6. Anything said about the work outside the team passes the never-claim checklist (D8; E24-S02).

### 1.6 Personas

Canonical names, as in the [product brief](01-product-brief.md):

| Persona | Role in the backlog |
|---|---|
| Firm owner | Buyer; HUMAN_OWNER of the envelope. Grants sources and purposes, approves implementation cards, answers firm-level conventions. |
| Reviewing accountant | Champion and primary user (HUMAN_REVIEWER, HUMAN_APPROVER). Reviews and signs off packages. |
| Bookkeeper | Secondary user. Uses the readiness ledger; later reviews and sends drafts. |
| Firm's client | Affected party, not a principal. No Plumb contact before the Draft and Send gates. |
| Plumb domain expert | Owns the domain acceptance corpus (spec §26) and the thresholds (D12). |
| Plumb engineer/operator | Builds primitives; every tenant-specific act is ENGINEERING_INTERVENTION or OPERATIONAL_REPAIR. |
| Independent verifier | The VERIFIER service and the verification engineer who owns it, outside the build team (ADR-007). |

---

## 2. Epic overview

Owner roles follow D12. Priorities follow section 1.3; phases and priorities are proposals.

| Id | Epic | Goal | First phase | Priority | PL ids | Owner role |
|---|---|---|---|---|---|---|
| E01 | Effort ledger and autonomy metric | Capture every human minute on tenant resources in five categories, automatically, and compute EIH/VD with failed attempts counted (ADR-010) | P0 | Must | PL-003, PL-059, PL-062 | Tech lead; rubric owned by the Founder |
| E02 | Truthful capability registry and probes | Registry maturity is true per account and operation; tenant 1 earns real probe receipts; supported environments v1 is published | P0 | Must | PL-007, PL-008 | Integration engineer (registry owner, spec §26) |
| E03 | Control service, tenancy and authentication | A running control service with verified identity, transactional state, an idempotent API and the M1 isolation subset | P1 | Must | PL-004, PL-006, PL-052, PL-055, PL-056, PL-057 | Tech lead; Security/platform engineer |
| E04 | Autonomy envelope and implementation card | The Firm owner authorizes a versioned envelope once and sees one card per intervention version | P1 | Must | PL-005, PL-040, PL-041 | Product engineer |
| E05 | Build plan compiler wiring and durable build ledger | The agent fills the plan; the compiler checks it against the tenant inventory and capability authority; builds run from a durable ledger with checker-wired guards | P1 | Must | PL-014, PL-015, PL-016, PL-017, PL-018, PL-057 | Tech lead |
| E06 | Sandbox, secrets and egress | Generated code and parsing run in disposable, credential-free sandboxes with mediated egress; hostile content cannot change authority | P1 | Must | PL-006, PL-019, PL-051, PL-054 | Security/platform engineer |
| E07 | Integration factory | Certified transport plus agent-generated semantic mapping, contract-tested before activation | P2 | Must | PL-002, PL-020, PL-021, PL-022 | Integration engineer |
| E08 | Collection factory and health | Shadow, backfill, reconcile, incremental and honest health; a live change proves the path | P2 | Must | PL-023, PL-024, PL-025 | Integration engineer |
| E09 | Evidence store, time axes and corrections | Provenance on three time axes; unknown never shown as absent; scoped, reversible corrections | P2 | Must | PL-009, PL-010, PL-011 | Tech lead |
| E10 | Independent verifier and fault-injection harness | Completion decided by an independent verifier; most HIGH scenarios executable | P2 | Must | PL-042, PL-043, PL-044, PL-061 (ADR-007) | Verification and acceptance-harness engineer |
| E11 | Customer surfaces | Implementation card, progress feed, blocked-dependency card, readiness ledger, results-and-effort view, focused-question queue | P2 | Must | PL-001, PL-003, PL-016, PL-025, PL-041, PL-059, PL-062 | Product engineer; fractional product designer |
| E12 | Opportunity library and OpportunitySpec | A vertical library in place of open-ended discovery; complete OpportunitySpecs with native-feature baselines | P2 | Must | PL-012, PL-013 | Founder; Plumb domain expert |
| E13 | Preparation-only workflow and ReviewPackage | One verifier-attested ready-for-review package per client-period, no external communication in production | P4 | Must | PL-001, PL-034, PL-035, PL-036 | Tech lead; Plumb domain expert |
| E14 | Review surface and prospective correction collector | Explicit accept/correct/amend capture that measures review minutes and keeps the ADR-006 option open | P1 | Must | PL-026, PL-027, PL-040, PL-059 | Product engineer; Plumb domain expert |
| E15 | Approvals model and policy-level approvals | Three §17 decisions, each asked once, bound and batched | P1 | Must | PL-040, PL-041 | Product engineer; Tech lead |
| E16 | Release executor, shadow, pause and kill | A narrow, qualified release executor; pause and kill from SHADOW and CANARY | P4 | Must | PL-045, PL-046, PL-047, PL-048 | Tech lead |
| E17 | Production action gateway and effect ledger | Outbox, leases and dispatch-time authority, revocation and pause checks before any Draft or Send (ADR-009) | P5 | Must | PL-037, PL-038, PL-039 | Tech lead (gateway owner, spec §26) |
| E18 | Data rights and purpose grants, incl. SERVE and TRAIN | Purpose grants enforced at plan and runtime; SERVE explicit; TRAIN opt-in; tax-return data excluded | P1 | Must | PL-053 | Tech lead; Fractional counsel |
| E19 | Telemetry and correlation | Correlated, content-free, tenant-scoped telemetry | P2 | Must | PL-060 | Security/platform engineer; SRE/on-call |
| E20 | Economics, budgets and cost accounting | Atomic reservations, metered cost, full-cost accounting and a billing basis | P2 | Must | PL-050, PL-058, PL-059 | Tech lead; Founder |
| E21 | Learning factory (gated M2) | Learning-data discovery, datasets, label audit and training only after the D5 gates | P5 | Must (memo only) | PL-026, PL-027, PL-028, PL-029, PL-030, PL-031, PL-032, PL-033, PL-034 (ADR-006) | Applied ML/eval engineer |
| E22 | Maintenance and repair | Monitors linked to cases and releases; logged manual operations; bounded repair after day 180 | P2 | Must | PL-018, PL-048, PL-049 | Tech lead; SRE/on-call |
| E23 | Second domain (M6, laundry) | Laundry route preparation on the same engine, then RFQ, with domain work measured separately | Gated | Could | PL-013, PL-035, PL-063 | Founder |
| E24 | Acceptance catalog and threshold sheet | Pre-registered thresholds, the never-claim gate, catalog proposals and the evidence packets | P0 | Must | PL-044, PL-061, PL-062, PL-063 | Founder; Plumb domain expert; Verification engineer |

### 2.1 Phase exit map

Each phase's exit evidence (decision record, abbreviated) and the Must stories that produce it.

| Phase | Exit evidence (abbreviated) | Must stories in this phase |
|---|---|---|
| P0 | Rubric, threshold sheet, charter and never-claim checklist signed; zero synthetic PRODUCTION_VERIFIED records; ledger records entries end to end including failed attempts; at least 8 qualified conversations; vendor approval timelines known; contract template drafted | E01-S01, E01-S02, E01-S03, E02-S01, E02-S08, E24-S01, E24-S02, E24-S03 |
| P1 | M0 checklist: judgeable outcome with a denominator; SANDBOX_TESTED receipts for list_folder_changes, fetch_document, collector-write operations and ledger-metadata reads on tenant 1's real accounts; substrate contract tests; threat model; effort ledger live; tenant 1 DPA, envelope and paid pilot; 3 more LOIs | E01-S04, E01-S05, E02-S02, E02-S03, E02-S04, E02-S05, E03-S01, E03-S02, E03-S04, E03-S06, E03-S08, E03-S09, E04-S01, E04-S02, E05-S01, E05-S02, E05-S03, E05-S04, E05-S05, E06-S02, E14-S01, E15-S03, E18-S01, E18-S02, E24-S04 |
| P2 | PA-001 attested with agent-generated mapping and zero ENGINEERING_INTERVENTION; safety bundle (PA-015, PA-019, PA-022; collector half of PA-005; health half of PA-011; PA-023 adaptation; PA-017 subset; PA-026 if generated code ran); readiness ledger and surfaces live; EIH/VD baseline recorded | E01-S06, E01-S07, E02-S06, E03-S05, E04-S04, E04-S05, E05-S06, E05-S07, E06-S01, E06-S03, E06-S04, E06-S05, E06-S07, E07-S01, E07-S02, E07-S03, E07-S04, E08-S01, E08-S02, E08-S03, E08-S04, E08-S05, E08-S07, E09-S01, E09-S02, E09-S03, E10-S01, E10-S02, E10-S03, E10-S04, E10-S07, E11-S01, E11-S02, E11-S03, E11-S04, E11-S05, E11-S06, E12-S02, E15-S01, E18-S03, E19-S01, E19-S02, E19-S03, E20-S01, E22-S01, E22-S02, E24-S07 |
| P3 | PA-001 attested on tenants 2 and 3 with at least one non-VERIFIED_ADAPTER operation; PA-026 and PA-019 on that path; PA-017 surfaces with co-resident tenants; EIH/VD trend; reuse rate with fork count 0; audit finds zero unrecorded work; experiment-1 proxy; R1 memo | E02-S07, E07-S05, E07-S07, E12-S06, E18-S05, E24-S08 |
| P4 | PA-002 as written in sandbox with a BUSINESS_OUTCOME attestation; PA-003, PA-004, PA-006, PA-008, PA-010, PA-011 in sandbox; PA-021 adaptation; numeric correct-package threshold; DOMAIN_CLARIFICATION measured; production shadow on tenant 1 with no EXTERNAL_COMMUNICATION | E06-S06, E06-S08, E08-S09, E09-S05, E09-S06, E10-S05, E10-S06, E13-S01, E13-S02, E13-S03, E13-S04, E13-S05, E13-S06, E13-S07, E14-S02, E14-S03, E14-S04, E14-S06, E15-S04, E16-S01, E16-S02, E16-S03, E16-S05, E18-S04 |
| P5 | Attested packages on at least 30 client-periods in one full close; correct-package rate, accountant minutes against baseline, false-chase and recall; owner time in budget; gateway sandbox crash tests (PA-005 dispatch-time re-check, PA-009, PA-015); pause and kill from SHADOW and CANARY; day-180 packet | E11-S08, E13-S08, E17-S01, E17-S02, E17-S03, E17-S04, E21-S01, E24-S09 |
| P6 | Canary report with receipts; zero duplicate, stale or wrong-client requests to real clients; PA-005, PA-007, PA-009, PA-010; PA-027; 2 of the first 4 partners on paid annual | E16-S07 (Prepare-tier canary to ACTIVE, which paid conversion needs; founder decision 17). The Draft and Send stories (E15-S06, E15-S07, E16-S08, E17-S05, E17-S06, E17-S07, E17-S08, E22-S04, E22-S05) stay Could until the day-180 packet says go; the P6 window (Apr-Jun 2027) covers the Prepare-tier canary and ACTIVE closes, the Draft tier and the start of M5, and the earliest Send canary close is around July 2027 (about weeks 39-41) |

The P2 row is long because M1 is the largest build: the collection path, the verifier, the sandbox and the first customer surfaces all land together. Many phase-P2 stories start in P1.

### 2.2 Key dependencies

- **E01 before any tenant build.** PA-001 fails on any ENGINEERING_INTERVENTION entry, which cannot be checked without the ledger, and PA-027 later compares against tenant 1's ledger figures.
- **E02 receipts gate every plan.** With a truthful registry, the plan checker's floors reject integration.configure, collection.backfill and collection.enable_incremental below SANDBOX_TESTED, and release.* and infrastructure.apply below PRODUCTION_VERIFIED ([plan_checker.py](../plumb/checker/plan_checker.py) `required_maturity`, lines 217-238). The same SANDBOX_TESTED floor applies to every non-shadow INTERNAL_WRITE step, so workflow.compile (P4), integration.generate_adapter (P3, tenant 3) and dataset.build and training.submit (gated) also need receipts.
- **E03 and E06-S02 before tenant 1's real-account probes.** Probing needs authenticated principals and a credential resolver.
- **E10 before any VERIFIED state.** No step, collector or release may read "verified" without an attestation.
- **E16-S02 and E18-S04 before the first tenant shadow.** release.activate_shadow needs PRODUCTION_VERIFIED, and serving needs an explicit SERVE grant.
- **E17 sandbox hardening in P5 before Draft in P6 and Send after it.** A mailbox draft is an external write (D3).
- **Fallback (D4 revisit trigger).** If sandbox and egress work slips more than 4 weeks, M1 is attested on PA-001 plus the rest of the bundle, and the generated-path requirement moves to tenant 3 (E07-S05).

---

## 3. Epics and stories

### E01 Effort ledger and autonomy metric

**Goal.** Every human minute spent on a tenant's resources, the firm's and Plumb's, is captured automatically in the five categories, and EIH/VD is computed per tenant with failed, blocked and abandoned attempts in the numerator (PL-003, PL-062, ADR-010).
**Why now.** The decision record makes the effort ledger the first product code (P0). PA-001 fails on any ENGINEERING_INTERVENTION entry and PA-027 compares replication against the first customer's ledger, so the ledger must exist before tenant 1's first build. Eight requirements have no local behavioral test, among them PL-003 and PL-062, which carry the business case ([validation report](../VALIDATION_REPORT.md)).
**Package has.** `HumanEffortCategory` with the five categories ([common.py](../plumb/contracts/common.py) lines 235-242); `HumanEffortRecord` (lines 611-618), exported but used nowhere; the SQL `human_effort` table with `build_id` and `case_id` but no attempt reference ([SQL design](../sql/001_initial_design.sql) lines 814-829); `listOutcomes`, read-only, whose `OutcomeObservation` carries one nullable `human_effort_category` ([openapi.yaml](../api/openapi.yaml) line 3612). No capture API and no autonomy computation.

**E01-S01 Freeze the effort rubric as a versioned artifact** — Phase P0 · Priority Must · Trace: PL-003, PL-062, ADR-010
- *Story.* Internal story (owner: Founder, with the Plumb domain expert): freeze the D6 rubric in week 1 so that every minute is categorized the same way on every tenant and the north star cannot drift.
- *Acceptance criteria.*
  1. Rubric v1 is the D6 rubric with the flagged amendment of founder decision 18 (to ratify). PL-003 requires all human effort by category, so every minute of partner time lands in exactly one of: CUSTOMER_AUTHORIZATION (grants, envelope decisions, approving the reminder policy); DOMAIN_CLARIFICATION (owner answers on conventions, label or attribution sample audits, baseline-study recording overhead, scheduled weekly check-ins); NORMAL_BUSINESS_REVIEW (per-case approvals, draft review, package sign-off); ENGINEERING_INTERVENTION (implementation work by any person, Plumb or firm staff: wiring, mapping, plan or workflow authoring or editing, manual deployment; spec App. B); OPERATIONAL_REPAIR (Plumb staff fixing a running collector or workflow).
  2. The gaps left in the [MVP scope](03-mvp-scope.md) open question 5 (Plumb staff time that is neither implementation nor repair, such as the domain expert facilitating the baseline study or a sandbox reviewer's time) are resolved in v1.
  3. Signed by the Founder and the Plumb domain expert (P0 exit evidence).
  4. Every effort entry stores the rubric version. A change after freeze creates a new version with a re-categorization note; existing entries are never edited in place.
- *Starting point.* The five-value enum in [common.py](../plumb/contracts/common.py). The rubric text is in D6.

**E01-S02 Principal types for Plumb staff** — Phase P0 · Priority Must · Trace: PL-003, PL-004, PL-040
- *Story.* System story: Plumb engineers, operators and the domain expert act as identifiable principals, so their minutes can be attributed truthfully and they can never pass as customer approvers.
- *Acceptance criteria.*
  1. `PrincipalType` gains staff types (proposed names: PLUMB_ENGINEER, PLUMB_OPERATOR, PLUMB_DOMAIN_EXPERT). `HUMAN_PRINCIPAL_TYPES` is unchanged, so `check_approval` still reports APPROVAL_NOT_HUMAN for a staff approver.
  2. The SQL `human_effort.principal_type` check list includes the new types; schemas regenerate and `--check` passes.
  3. A test shows a staff principal cannot be the `granted_by` of a SourceGrant, the approver of an ApprovalRecord or the `rollback_owner` of an OperatingPlan.
- *Starting point.* `PrincipalType` lists only customer, agent, service, verifier and release-executor types, and `HUMAN_PRINCIPAL_TYPES` holds the three customer types ([common.py](../plumb/contracts/common.py) lines 215-229); gap 3 in the [MVP scope](03-mvp-scope.md).

**E01-S03 Append-only effort ledger with attempt references** — Phase P0 · Priority Must · Trace: PL-003, PL-059, PL-062
- *Story.* As a Plumb engineer/operator, I want every effort entry tied to the tenant, build attempt and case it served, so that failed and abandoned attempts count against EIH/VD.
- *Acceptance criteria.*
  1. `HumanEffortRecord` v2 adds tenant, build id, step-attempt id, case id, side (FIRM or PLUMB), capture source (AUTO_CAPTURED or SELF_REPORTED), rubric version, start and end times. The SQL table gains the attempt reference.
  2. The ledger is append-only: an update is rejected; a correction is a new entry that references the original.
  3. An entry can be recorded against an attempt in FAILED, BLOCKED or CANCELLED state (P0 exit: "records entries end to end, including failed attempts").
  4. Minutes are integers of at least 0; descriptions contain no secrets (`reject_secret_like`).
- *Starting point.* `HumanEffortRecord` and the `human_effort` table, both unused.

**E01-S04 Automatic capture of human-principal actions** — Phase P1 · Priority Must · Trace: PL-003, PL-059
- *Story.* As a Firm owner, I want my authorizations, answers and reviews logged without anyone filling in a timesheet, so that the labor ledger I am shown is complete and I can audit it.
- *Acceptance criteria.*
  1. Every mutating control-service operation called by a human principal writes exactly one effort entry; a test enumerates the operations and fails on any that does not.
  2. Category is derived from the action: DATA_USE and IMPLEMENT_OPERATE decisions and reminder-policy approval → CUSTOMER_AUTHORIZATION; focused-question answers → DOMAIN_CLARIFICATION; package sign-off and per-case approvals → NORMAL_BUSINESS_REVIEW; any person's edit of a tenant plan, mapping or workflow, Plumb or firm staff → ENGINEERING_INTERVENTION; staff actions on a running collector or workflow → OPERATIONAL_REPAIR. Scheduled check-ins and baseline-study overhead, which happen off the surface, are recorded as DOMAIN_CLARIFICATION through E01-S08.
  3. Minutes are measured as active time on the surface; the idle cut-off is a threshold-sheet hypothesis.
  4. Staff access to tenant resources outside the control service goes through audited support access (E03-S06) and produces an entry.
  5. P1 exit: "the effort ledger is live with the frozen rubric".
- *Starting point.* None for capture.

**E01-S05 Separate platform-investment ledger** — Phase P1 · Priority Must · Trace: PL-062, ADR-010
- *Story.* Internal story (owner: Tech lead): work on reusable primitives is recorded apart from tenant work and tagged with the tenant that triggered it, so hours cannot migrate out of the tenant numerator.
- *Acceptance criteria.*
  1. Each entry carries the triggering tenant and the registry primitive, corpus item or harness component it produced.
  2. An entry cannot be in both ledgers. Moving an entry from the tenant ledger to the platform ledger needs the ledger auditor's sign-off and leaves a trail.
  3. Reports show platform-investment hours per triggering tenant beside EIH/VD and never subtract them.
- *Starting point.* None.

**E01-S06 EIH/VD, hands-off build rate and time to first verified event** — Phase P2 · Priority Must · Trace: PL-062, PL-002, PL-001, ADR-010
- *Story.* As the Firm owner, I want to see how many engineering hours Plumb spent per verified deployment on my firm, failures included, so that "supervised" and "automatic" mean something I can check.
- *Acceptance criteria.*
  1. EIH/VD per tenant in onboarding order: numerator is all ENGINEERING_INTERVENTION and OPERATIONAL_REPAIR minutes on the tenant's eligible attempts, including failed, abandoned and blocked ones; denominator is verifier-attested deployments (collection paths, then workflows) (D10).
  2. A test fixture with one failed and one verified attempt yields a higher EIH/VD than the verified attempt alone; a deployment without an attestation never enters the denominator.
  3. Hands-off build rate, repair attempts per verified deployment and time to first verified event (split into Plumb-controlled and dependency time) are computed from the build ledger.
  4. P2 exit: tenant 1's EIH/VD baseline and time to first verified event are recorded.
- *Starting point.* None.

**E01-S07 Ledger audit export and milestone invalidation** — Phase P2 · Priority Must · Trace: PL-003, PL-062, PL-063, PA-027
- *Story.* As the Firm owner, I want my firm's ledger exportable and audited by someone outside Plumb's delivery team, so that hidden labor cannot be presented as automation.
- *Acceptance criteria.*
  1. The ledger exports in an open format with entry digests, per tenant and per milestone.
  2. The auditor (Founder plus an external technical advisor, D12) records the result of applying PA-027's audit method at M1, M1R and M5, and monthly. This is not reported as a PA-027 pass.
  3. A recorded finding of unrecorded engineering marks the milestone invalid and requires a re-run; a second occurrence flags "external audit required before any external claim" (R2).
  4. M1 (P2 exit): the audit of tenant 1 is recorded, and any finding invalidates M1 (R2). P3 exit: the audit finds zero unrecorded manual work (decision record).
- *Starting point.* None. Audit tooling is E10-S07.

**E01-S08 Effort API and per-case effort in outcomes** — Phase P1 · Priority Should · Trace: PL-003, PL-059, PL-055
- *Story.* As a Plumb engineer/operator, I want to self-report off-platform work such as a support call through an API, so that it lands in the same ledger, visibly marked as self-reported.
- *Acceptance criteria.*
  1. Operations `recordEffort`, `listEffort` and `getAutonomyReport` exist in the OpenAPI document, with Idempotency-Key and tenant from authentication.
  2. Self-reported entries are flagged and shown separately from auto-captured ones; D10's revisit trigger (count only automatic capture if an audit finds miscategorization) can be applied by filter.
  3. `OutcomeObservation`'s single nullable category is replaced by a per-case breakdown by category.
  4. The Firm owner can read the firm's ledger; nobody can read another tenant's (404).
- *Starting point.* `listOutcomes` in [openapi.yaml](../api/openapi.yaml).

### E02 Truthful capability registry and probes

**Goal.** Registry maturity is true per account and exact operation, tenant 1 earns real probe receipts, and integration coverage is published per operation, never as a logo wall (PL-007, PL-008; D8).
**Why now.** P0 exit requires zero synthetic PRODUCTION_VERIFIED records. A truthful registry then blocks every fixture plan until receipts exist, so earning receipts is critical-path work, not bookkeeping (D3 correction).
**Package has.** [capability_registry.json](../plumb/registry/capability_registry.json): 25 records over 23 step types, 15 PRODUCTION_VERIFIED, 8 SANDBOX_TESTED, 2 DOCUMENTED, self-described as "Synthetic reference capability registry ... no entry establishes access to any real account". The loader refuses partial loads ([registry.py](../plumb/registry/registry.py)). `OperationCapability` requires `probe_receipt_ref` and `last_probed_at` above DOCUMENTED ([inventory.py](../plumb/contracts/inventory.py) lines 89-113); `EnvironmentInventory` and `CoverageReport` exist. `ProbeReceipt` is an ArtifactKind value with no contract ([common.py](../plumb/contracts/common.py) line 359). No prober.

**E02-S01 Reset the registry to truthful maturity** — Phase P0 · Priority Must · Trace: PL-008, PL-007
- *Story.* System story: the production registry claims only what a probe has established, so no plan, sales asset or investor document can read the synthetic records as real capability.
- *Acceptance criteria.*
  1. The production registry has zero PRODUCTION_VERIFIED and zero SANDBOX_TESTED records without a real probe receipt; every record is DISCOVERED or DOCUMENTED (P0 exit).
  2. The synthetic registry is kept as a clearly named test fixture, and existing local tests are pinned to it.
  3. Checking the fixture plans against the truthful registry reports CAPABILITY_MATURITY_INSUFFICIENT at integration.configure, collection.backfill, collection.enable_incremental, workflow.compile, dataset.build, training.submit and (RFQ and laundry) integration.generate_adapter (SANDBOX_TESTED floor), and at release.create, release.activate_shadow, release.canary and infrastructure.apply (PRODUCTION_VERIFIED floor). This was confirmed on 2026-10-04 by running `check_plan` on the three fixture plans with every registry record set to DOCUMENTED. The expected failure is recorded, not hidden.
- *Starting point.* The registry file and `required_maturity` in [plan_checker.py](../plumb/checker/plan_checker.py) lines 217-238.

**E02-S02 ProbeReceipt contract** — Phase P1 · Priority Must · Trace: PL-008
- *Story.* System story: every successful probe produces a digest-addressed receipt naming the account and exact operation without credential material, so maturity claims are auditable.
- *Acceptance criteria.*
  1. A `ProbeReceipt` contract subclassing `ArtifactHeader` records tenant, provider, external account id, exact operation, direction, response-shape digest, probed-at time and prober principal; schema generated.
  2. A receipt containing a token-shaped or key-shaped string is rejected by `reject_secret_like`.
  3. `OperationCapability.probe_receipt_ref` must resolve to a stored receipt whose account and operation match.
- *Starting point.* ArtifactKind `ProbeReceipt`; `OperationCapability` validators.

**E02-S03 Maturity promotion only through receipts and attestations** — Phase P1 · Priority Must · Trace: PL-008, PL-042, ADR-003
- *Story.* System story: maturity rises only through evidence, never by editing a file.
- *Acceptance criteria.*
  1. SANDBOX_TESTED for an account and operation requires a receipt from a successful probe of that exact operation plus a verifier attestation. PRODUCTION_VERIFIED requires an attested production run (for release.*, the platform qualification run, E16-S02).
  2. A registry or inventory change that raises maturity without both is refused, and every maturity change is audited.
  3. Maturity is never set from fixtures (founder decision default, decision record).
- *Starting point.* Loader validation in [registry.py](../plumb/registry/registry.py).

**E02-S04 Inventory prober for tenant 1's document store and ledger metadata** — Phase P1 · Priority Must · Trace: PL-007, PL-008, PL-002
- *Story.* As the Firm owner, I want Plumb to show exactly which operations work on my firm's accounts before it proposes a build, so that nothing is promised from a vendor page.
- *Acceptance criteria.*
  1. Probes run on tenant 1's real accounts for `list_folder_changes`, `fetch_document`, folder and metadata listing, change-notification registration and removal (the integration.configure and collection.enable_incremental writes) and ledger-metadata reads (client companies, chart of accounts, period metadata).
  2. P1 exit: SANDBOX_TESTED receipts for `list_folder_changes`, `fetch_document`, the collector-write operations and the ledger-metadata reads. Other read steps need only the DOCUMENTED floor.
  3. The result is an `EnvironmentInventory` with a `CoverageReport`; an operation never probed stays DISCOVERED or DOCUMENTED.
  4. If ledger authorization is granted per client company, the inventory records it and the expected onboarding CUSTOMER_AUTHORIZATION minutes; above 4 hours per firm the D1 revisit trigger fires.
  5. No credential appears in any receipt, inventory, log or error.
- *Starting point.* `EnvironmentInventory`, `ApplicationRecord`, `OperationCapability`, `CoverageReport` ([inventory.py](../plumb/contracts/inventory.py)); `startInventoryJob` and `getInventoryJob` in the OpenAPI proposal.

**E02-S05 Substrate contract tests** — Phase P1 · Priority Must · Trace: PL-008, PL-020, PL-022
- *Story.* Internal story (owner: Integration engineer): the candidate transport substrate (Nango) passes Plumb's contract tests on the probed operations before anything is built on it (spec §3).
- *Acceptance criteria.*
  1. P1 exit: substrate contract tests pass on the probed operations.
  2. A build-versus-buy memo records the result, pricing exposure and whether development and runtime credentials stay separate (D12 revisit trigger for the security hire).
  3. A failed operation is recorded as unsupported for that provider, not worked around by hand.
- *Starting point.* Contract-test families in [integration.py](../plumb/contracts/integration.py) lines 46-61.

**E02-S06 Supported environments v1** — Phase P2 · Priority Must · Trace: PL-002, PL-007, PL-008
- *Story.* As the Firm owner, I want a published list of exactly which operations Plumb supports at which maturity, so that I know what I am buying.
- *Acceptance criteria.*
  1. Published per operation: provider family, operation, effect class, maturity, receipt reference and last-probed date, generated from the registry and inventories, never hand-edited.
  2. No logos. Anything absent is reported as CAPABILITY_UNSUPPORTED or a dependency, never as hidden manual work.
  3. The D1 and D9 qualification constraints are stated: document stores need webhooks plus overlap polling (PA-005), mail needs request-id lookup (PA-009).
  4. Published by P2 exit (decision record, P2 scope).
- *Starting point.* The operation table in the [MVP scope](03-mvp-scope.md) section 6.

**E02-S07 Per-tenant re-probe and the tenant 3 provider swap** — Phase P3 · Priority Must · Trace: PL-007, PL-008
- *Story.* System story: tenants 2 and 3 earn their own receipts, and a swapped provider starts from DISCOVERED.
- *Acceptance criteria.*
  1. Each tenant's inventory has its own receipts; no receipt is reused across accounts.
  2. Tenant 3's swapped provider has receipts for every operation in its plan before `check_plan` passes.
  3. A receipt older than the re-probe window (threshold-sheet hypothesis), or a provider API version change, marks the operation for re-probe.
- *Starting point.* `last_probed_at` on `OperationCapability`.

**E02-S08 Vendor app review and consent tracking** — Phase P0 · Priority Must · Trace: PL-007
- *Story.* Internal story (owner: Fractional compliance lead): Google and Microsoft app review and consent for document, ledger and mail scopes start in week 0, because Plumb never bypasses vendor approvals (spec §5).
- *Acceptance criteria.*
  1. P0 exit: approval timelines are known for every scope in the D3 plan.
  2. Each pending approval is visible as a dependency on the affected operations, with its expected date.
  3. If mail scopes are not approved by M3-lite, the R7 fallback (document store plus ledger, with a forwarding-address intake for mail) is planned.
- *Starting point.* None.

### E03 Control service, tenancy and authentication

**Goal.** A running control service, built around the existing kernel, that derives tenant and principal from verified authentication, persists state transactionally, exposes an idempotent API and isolates tenants on the M1 surfaces (PL-004, PL-006, PL-052, PL-055, PL-056, PL-057).
**Why now.** Every other epic runs through it. P1 scope starts with auth and tenancy (PL-004), and the PA-017 subset must pass before a second tenant's data arrives (D4).
**Package has.** An [OpenAPI proposal](../api/openapi.yaml) with 24 operations and conventions for tenant-from-OIDC, 404 not 403, Idempotency-Key (at most 255 characters), If-Match with 412 and cursors (limit at most 200) (lines 14-43); a bearer scheme only, with no per-operation roles; a placeholder host. A [PostgreSQL design](../sql/001_initial_design.sql) with 29 tables, row-level security on 27, and app, migrator and platform-admin roles, never executed. `OperationContext` ([common.py](../plumb/contracts/common.py) lines 530-539), used nowhere. Request bodies are full artifacts with client-supplied `producer`, `created_at` and `content_digest`.

**E03-S01 Control-service skeleton on PostgreSQL** — Phase P1 · Priority Must · Trace: PL-055, PL-057, PL-052, ADR-002, ADR-004
- *Story.* System story: a Python control service with the package's Pydantic contracts, an HTTP API and PostgreSQL (spec §3) is the single lifecycle owner, so state survives replaced agent sessions.
- *Acceptance criteria.*
  1. `sql/001_initial_design.sql` executes on a disposable PostgreSQL 15+ instance under migration tooling.
  2. An integration test confirms row-level security is enabled and forced on every tenant table and that `plumb_app` cannot bypass it (the existing tests only inspect the SQL text).
  3. Long-running mutations return 202 with a durable `JobEnvelope`; the same Idempotency-Key and payload return the original job; a different payload returns 409 PAYLOAD_CONFLICT (PL-055).
  4. Job status survives a service restart.
- *Starting point.* The SQL design; `JobEnvelope` and `ErrorEnvelope` ([api.py](../plumb/contracts/api.py)).

**E03-S02 Verified identity and OperationContext on every operation** — Phase P1 · Priority Must · Trace: PL-004, PL-056, PA-017
- *Story.* As the Firm owner, I want every action on my firm's data attributed to an authenticated person or agent, a purpose and a budget, so that nothing happens anonymously.
- *Acceptance criteria.*
  1. Tenant and principal come from the verified OIDC token. A path or body tenant that differs from the authenticated tenant gets 404, never 403 (the API surface of PA-017).
  2. Every write constructs and persists an `OperationContext` (tenant, principal, purpose, resource scope, capability version, policy version, budget allocation); a request missing any field is rejected before any side effect.
  3. Errors never reveal another tenant's identifiers or resource existence (PL-056).
- *Starting point.* `OperationContext`; API conventions.

**E03-S03 Request DTOs separate from stored artifacts** — Phase P1 · Priority Should · Trace: PL-004, PL-055, PL-056
- *Story.* System story: clients submit requests; the server assigns producer, timestamps, versions and digests, so client claims never overwrite server-assigned state (spec §22).
- *Acceptance criteria.*
  1. Each mutating operation has a request schema without `producer`, `created_at`, `version` or `content_digest`.
  2. A request that tries to set them is rejected; the stored artifact's digest is recomputed server side.
  3. The OpenAPI document and its parity tests are updated.
- *Starting point.* `ArtifactHeader` ([common.py](../plumb/contracts/common.py) line 573); [test_openapi.py](../tests/test_openapi.py).

**E03-S04 Role-scoped authorization and credential separation** — Phase P1 · Priority Must · Trace: PL-006, PL-004, ADR-001, PA-022
- *Story.* System story: the customer product API and the internal worker API are separate, and management, execution and policy-administration credentials are separate (PL-006), so a build agent can never act as an owner or administrator.
- *Acceptance criteria.*
  1. A principal-type by operation matrix is enforced and tested; a BUILD_AGENT or RUNTIME_AGENT token cannot call envelope, approval or registry-administration operations.
  2. A runtime credential cannot call integration-management operations; a deployment credential is not a runtime credential (spec §2).
  3. Platform policy changes are possible only through the policy-administration role, never through a customer implementation job (spec §4).
- *Starting point.* The bearer scheme in [openapi.yaml](../api/openapi.yaml) lines 963-972.

**E03-S05 Tenant isolation for the M1 surfaces** — Phase P2 · Priority Must · Trace: PL-052, PL-056, PL-004, PA-017
- *Story.* As the Firm owner, I want proof that no other firm can reach my data in Plumb's database, API, storage, caches, logs or exports before any other firm's data arrives.
- *Acceptance criteria.*
  1. P2 exit: PA-017's database, API, object-storage, cache, log and export checks pass with a verifier attestation, reported as isolation subset A (PA-P14), never as a PA-017 pass.
  2. Object storage is content-addressed under tenant prefixes; cache keys carry the tenant; exports are scoped.
  3. Every use of the platform-admin bypass is recorded in the admin audit table and alarmed (PA-017 expectation).
  4. P3 exit: the same checks re-run with co-resident tenants 2 and 3. Full PA-017 (all nine surfaces) runs before any training job (E21).
- *Starting point.* Roles (lines 74-85) and RLS policies and grants (lines 832-1062) in the [SQL design](../sql/001_initial_design.sql); the SQL header states that merely enabling RLS is not a complete isolation design.

**E03-S06 Missing persistence tables** — Phase P1 · Priority Must · Trace: PL-057, PL-052, PL-001
- *Story.* System story: dependencies, connection intents and support access are persisted, so blocked work can resume and staff access is auditable.
- *Acceptance criteria.*
  1. P1 tables: dependencies, connection intents, integrations, users and principals, consent, budget ledger, admin audit, platform investment. P4 tables: workflows, monitors and alerts, review packages, focused questions, conventions.
  2. Each tenant table uses composite (tenant_id, id) keys, tenant-inclusive foreign keys and forced row-level security.
  3. A `DependencyRecord` persists and is queryable by resolver role and blocked step.
- *Starting point.* Gap 9 in the [MVP scope](03-mvp-scope.md); `DependencyRecord` ([common.py](../plumb/contracts/common.py) lines 593-608).

**E03-S07 API contract v0.3: close the read and lifecycle holes** — Phase P1 · Priority Should · Trace: PL-055, PL-056, PL-047
- *Story.* As a Plumb engineer/operator building the surfaces, I want a GET for every job and resource the product shows, so that no surface depends on reading the database directly.
- *Acceptance criteria.*
  1. Added: `listBuilds`, a generic `getJob`, `getDatasetJob` and `getEvaluation` (if used). Domain operations are specified with their epics: opportunities (E12-S04), authorization requests (E15-S02), effort (E01-S08), releases including rollback and retire (E16-S04), actions (E17-S03), review packages, questions and conventions (E13-S01, E11-S06).
  2. Every operation returning 202 has a matching GET for its job.
  3. The validator reports zero unresolved references; parity tests cover every new contract-mirroring component; every new mutating operation takes Idempotency-Key, and every versioned resource takes If-Match.
- *Starting point.* 24 operations; gap 8 in the [MVP scope](03-mvp-scope.md).

**E03-S08 Event protocol and audited, transactional transitions** — Phase P1 · Priority Must · Trace: PL-057, PL-056, ADR-004
- *Story.* System story: every authoritative state change is transactional, versioned and auditable, and events are delivered at least once with deduplication, so restarts never double-apply work.
- *Acceptance criteria.*
  1. Events carry the spec §22 fields (event id, tenant, aggregate id and version, type, occurred and recorded times, correlation and causation ids, schema version, payload reference).
  2. A duplicated event is processed once (deduplication in the same local transaction, using `processed_events`); ordering is guaranteed per aggregate only.
  3. Every transition persists a `Transition` record with reason and guard; a transition without a reason is refused.
- *Starting point.* `Transition`, `IllegalTransition`, `GuardFailed` in [machines.py](../plumb/statemachines/machines.py); `EventEnvelope` ([api.py](../plumb/contracts/api.py)); `outbox` and `processed_events` tables.

**E03-S09 Single US region** — Phase P1 · Priority Must · Trace: PL-005, PL-052
- *Story.* As the Firm owner, I want my data processed and stored only in the US region named in my envelope.
- *Acceptance criteria.*
  1. Tenant home region and all storage, processing and model routing are pinned to one US region.
  2. A plan step targeting another region fails `check_plan` with SCOPE_EXCEEDED (regions are part of the step's resource scope).
  3. The accounting fixture envelope's `eu-west-1` is replaced in templates (E24-S03).
- *Starting point.* `tenants.home_region` in the SQL design; `allowed_regions` on the envelope.

### E04 Autonomy envelope and implementation card

**Goal.** The Firm owner authorizes a versioned envelope once, from an opinionated accounting template, and sees one implementation card per intervention version; Plumb proceeds inside the envelope and asks only when a boundary is crossed (PL-005, PL-040, PL-041).
**Why now.** P1 exit requires tenant 1's envelope signed. The card is a minimum App. A §6 surface for P2 (D3 (j)).
**Package has.** `AutonomyEnvelope` ([envelope.py](../plumb/contracts/envelope.py) lines 127-245): versioned, tied to a HUMAN_OWNER, with `revoked_at`; `purposes_for` never infers TRAIN from INSPECT or COLLECT. `SourceGrant` (lines 83-101) has no `revoked_at`, although the SQL `source_grants` table does. `createEnvelope` and `getEnvelope` only. The [accounting envelope fixture](../fixtures/envelopes/accounting_evidence_preparation.json) is EU/EUR (`eu-west-1`), expires 2027-03-31 and allows EXTERNAL_COMMUNICATION and INFRASTRUCTURE_CHANGE. The fixture plans carry a pre-existing IMPLEMENT_OPERATE approval as a plan input.

**E04-S01 Accounting Prepare envelope template** — Phase P1 · Priority Must · Trace: PL-005, PL-053, PL-036
- *Story.* As the Firm owner, I want a ready-made envelope for monthly-close evidence preparation, so that I do not have to understand effect classes to authorize Plumb safely.
- *Acceptance criteria.*
  1. Template: one US region; sources are the ledger and the document store (tax-return folders excluded), with the mailbox added at P4; purposes INSPECT, COLLECT, TRANSFORM, EVALUATE; TRAIN absent; SERVE added explicitly before the first shadow (E18-S04); allowed effect classes READ, INTERNAL_WRITE and EXTERNAL_WRITE_REVERSIBLE (only for connector setup and enabling incremental capture on the firm's own accounts, as the accounting fixture marks integration.configure and collection.enable_incremental), and never EXTERNAL_COMMUNICATION; a spending limit with escalation at 80% of the limit; an expiry.
  2. `check_plan` against a plan containing an EXTERNAL_COMMUNICATION or FINANCIAL_COMMITMENT step reports EFFECT_CLASS_DENIED.
  3. Tenant 1's envelope is created from the template and signed by its HUMAN_OWNER through an authenticated decision (E15-S03).
- *Starting point.* The accounting envelope fixture.

**E04-S02 Envelope authoring, plain-language rendering and history** — Phase P1 · Priority Must · Trace: PL-005, PL-040
- *Story.* As the Firm owner, I want every envelope field explained in plain language and every change kept as a new version, so that I know what I authorized and when.
- *Acceptance criteria.*
  1. Every field renders with plain copy; there is no "Allow AI" button (spec §17).
  2. Saving creates a new version with If-Match; a stale version returns 412.
  3. A `listEnvelopeVersions` operation returns the history; revocation is a new version, as the package design intends.
- *Starting point.* `createEnvelope`, `getEnvelope`; [REFERENCE_PACKAGE_DESIGN.md](../docs/REFERENCE_PACKAGE_DESIGN.md) (revocation as a new version).

**E04-S03 Single-grant revocation** — Phase P1 · Priority Should · Trace: PL-005, PL-053, PL-041, PA-008
- *Story.* As the Firm owner, I want to withdraw one source, such as the mailbox, without re-authorizing everything else.
- *Acceptance criteria.*
  1. `SourceGrant` gains `revoked_at`, matching the SQL table; `purposes_for` excludes a revoked grant at evaluation time.
  2. Cached grant material and queued work for that source are invalidated within one minute (the PA-008 expectation), and its collectors move to PAUSED with the reason "grant revoked".
  3. Other sources' collectors continue, and the owner is never asked to re-approve still-valid grants.
- *Starting point.* `SourceGrant`, `purposes_for` ([envelope.py](../plumb/contracts/envelope.py)).

**E04-S04 Implementation card object and API** — Phase P2 · Priority Must · Trace: PL-005, PL-012, PL-040, PL-041, PL-058
- *Story.* As the Firm owner, I want one concise card per intervention showing what changes, which data, which actions, the maximum spend, the expected benefit and the decision I own, so that I decide once.
- *Acceptance criteria.*
  1. Card fields as in the [MVP scope](03-mvp-scope.md) section 4.1, derived from the BuildPlan, envelope, EnvironmentInventory and OpportunitySpec; one maximum spend figure plus the escalation trigger.
  2. Envelope covers the intervention and the card is unchanged: no decision is requested and the card shows "Proceeding under your envelope v<n>".
  3. A new processor raises exactly one IMPLEMENT_OPERATE request naming the boundary crossed.
  4. The resulting ApprovalRecord has decision kind IMPLEMENT_OPERATE, a HUMAN_OWNER approver, an authenticated decision reference and the card's digest as subject; an agent-written approval-shaped record is rejected (APPROVAL_AGENT_SUPPLIED).
- *Starting point.* OpportunitySpec and ApprovalRecord contracts; the fixture approval input `apr-acct-implement-operate-review-workflow`.

**E04-S05 Envelope-boundary detection** — Phase P2 · Priority Must · Trace: PL-041, PL-005, PL-040
- *Story.* System story: Plumb continues automatically inside existing authority and asks again only when a change crosses a processor, region, permission, spend-cap or irreversible-action boundary (spec §17; D6).
- *Acceptance criteria.*
  1. One test per boundary type raises a request; changes inside all five raise none.
  2. A bounded repair that produces a new artifact digest without changing any card field raises no request.
  3. Each request shows an impact diff against the approved version and the actual test evidence.
- *Starting point.* None.

**E04-S06 Escalation conditions enforced at run time** — Phase P2 · Priority Should · Trace: PL-005, PL-058, PL-001
- *Story.* As the Firm owner, I want Plumb to stop and ask before projected spend passes the trigger I set.
- *Acceptance criteria.*
  1. Projected worst-case spend above 80% of the envelope limit (the fixture's escalation condition) moves the build to WAITING_AUTH with a DependencyRecord of class BUDGET_EXCEEDED, resolver HUMAN_OWNER.
  2. Completed work is kept; declining ends in an actionable dependency, not a failure.
- *Starting point.* `escalation_conditions` on the envelope; BUILD machine WAITING_AUTH.

### E05 Build plan compiler wiring and durable build ledger

**Goal.** The build agent fills a tenant BuildPlan from a registry template; the compiler checks it against the tenant's EnvironmentInventory and each capability's required authority; the build runs from a durable ledger whose state-machine guards are computed by the checkers, with bounded repair (PL-014, PL-015, PL-016, PL-017, PL-018, PL-057).
**Why now.** D3 (b) and (c). M1 requires an agent-filled plan (D4 condition 2), and today a plan passes for an account whose operation was never probed.
**Package has.** `check_plan(plan, envelope, registry, now)` with 23 finding codes ([plan_checker.py](../plumb/checker/plan_checker.py) lines 249-297); no inventory parameter; capability `required_authority` is never read; an ApprovalRecord input is required, by kind only, for infrastructure.apply and never validated. Seven state machines whose guards are `flag()` and `present()` predicates over a caller-supplied context ([machines.py](../plumb/statemachines/machines.py) lines 77-84). `AgentTask`, `StepResult` and `check_result_against_task` ([protocol.py](../plumb/contracts/protocol.py)). SQL `builds`, `build_steps`, `build_step_attempts`. 28 malformed-plan fixtures in [fixtures/invalid](../fixtures/invalid) cover the 23 codes. The fixture plans are hand-authored.

**E05-S01 check_plan consumes the tenant EnvironmentInventory** — Phase P1 · Priority Must · Trace: PL-007, PL-008, PL-015, ADR-003
- *Story.* System story: a plan is valid only for operations that were actually probed on this tenant's accounts at the maturity the step needs.
- *Acceptance criteria.*
  1. `check_plan` takes the tenant's EnvironmentInventory. A step whose operation is absent for its account reports INVENTORY_OPERATION_UNPROBED (proposed code); a probed operation below the step's floor reports CAPABILITY_MATURITY_INSUFFICIENT.
  2. A plan with no inventory reports INVENTORY_MISSING (proposed code) for any production step (PL-007: inventory before any production build).
  3. One malformed-plan fixture per new code is added; the fixture plans pass against a matching synthetic inventory.
- *Starting point.* `check_plan`; `EnvironmentInventory`.

**E05-S02 check_plan enforces capability required_authority and approval validity** — Phase P1 · Priority Must · Trace: PL-015, PL-040, PL-014
- *Story.* System story: a step runs only with the authority its capability declares, and every approval it consumes is valid, not merely present.
- *Acceptance criteria.*
  1. Each `required_authority` entry (for example `approval:IMPLEMENT_OPERATE`, `approval:CASE_LEVEL_BUSINESS`, `source_grant:COLLECT`) must be satisfied by the envelope or a plan input; otherwise AUTHORITY_MISSING (proposed code).
  2. The accounting fixture's `canary-consolidated-reminders` step, whose only approval input is `apr-acct-implement-operate-review-workflow` (IMPLEMENT_OPERATE) while `cap.release.canary.executor` requires CASE_LEVEL_BUSINESS as well, now fails.
  3. ApprovalRecord inputs are checked with `check_approval`; APPROVAL_EXPIRED, APPROVAL_DIGEST_MISMATCH and the other approval codes surface in the plan report.
- *Starting point.* `required_authority` on every registry record ([capability_registry.json](../plumb/registry/capability_registry.json)); `check_approval` ([approval_checker.py](../plumb/checker/approval_checker.py) line 62).

**E05-S03 State-machine guards call the checkers** — Phase P1 · Priority Must · Trace: PL-016, PL-057, PL-042, PL-029, PL-047
- *Story.* System story: guard values are computed by the control service from checkers and stored records, never accepted from a caller, so the kernel's safety rules hold in production.
- *Acceptance criteria.*
  1. BUILD_STEP VERIFYING→VERIFIED requires a stored VerificationAttestation from a VERIFIER principal for the step's output digest. BUILD VERIFYING→VERIFIED requires every required step VERIFIED in the ledger.
  2. DATASET MATERIALIZING→VERIFIED requires `check_dataset` with no ERROR. RELEASE CANDIDATE→VERIFIED and every edge into ACTIVE require `check_release` with no ERROR, and `authority_current` is computed from `check_approval` and an active envelope.
  3. COLLECTOR PAUSED→ACTIVE computes `coverage_restored` from reconciliation; BUILD_STEP repair edges compute `repair_budget_remaining` from the ledger.
  4. No public or worker interface accepts guard flags; a request asserting `checker_ok` for a failing manifest is refused with GuardFailed (STATE_CONFLICT). Each guarded edge of the seven machines has a test.
- *Starting point.* Guards in [machines.py](../plumb/statemachines/machines.py) (for example lines 282, 312, 341, 366, 398); `check_dataset`, `check_release`, `check_approval`.

**E05-S04 Durable build ledger and scheduler** — Phase P1 · Priority Must · Trace: PL-017, PL-016, PL-057, PA-015, ADR-002
- *Story.* System story: every build keeps a durable ledger (goal, step state, artifact hashes, workspace commit, completed and failed checks, remaining budget, next eligible work), and the scheduler runs the App. A §2 loop, so a restart never redoes verified work.
- *Acceptance criteria.*
  1. Loop per step: verify envelope and attestations; acquire a lease and reserve worst-case cost; run in an isolated workspace; receive a proposed result; verify independently; commit by compare-and-set with the fencing token plus an outbox event; continue or enter a named dependency or failure state.
  2. Killing a worker mid-step and restarting reconstructs progress without redoing verified external effects.
  3. A late commit with a stale fencing token is rejected (`check_result_against_task` reasons).
  4. P2 exit: PA-015 passes for the create-collector management call: exactly one collector at the provider and budget settled once.
- *Starting point.* BUILD and BUILD_STEP machines; `check_result_against_task`; `build_steps_ready_idx` in the SQL design.

**E05-S05 Bounded agent harness** — Phase P1 · Priority Must · Trace: PL-016, PL-019, PL-006, PL-014
- *Story.* System story: build agents receive bounded AgentTasks and return proposals, never authority or verification.
- *Acceptance criteria.*
  1. Each AgentTask carries digest-pinned inputs, permitted capabilities, scope, remaining budget, workspace base digest and fencing token; credential-named fields are rejected.
  2. A StepResult with fields named like verification or attestation is rejected; an agent cannot produce an ApprovalRecord or VerificationAttestation.
  3. Model calls go through the gateway to approved processors only (E06-S08); proposed subtasks compile against the same or narrower authority (App. A §1).
- *Starting point.* `AgentTask`, `StepResult`, `FORBIDDEN_TASK_FIELD_MARKERS`, `FORBIDDEN_RESULT_FIELD_MARKERS` ([protocol.py](../plumb/contracts/protocol.py)).

**E05-S06 Prepare-tier plan template and agent plan filling** — Phase P2 · Priority Must · Trace: PL-014, PL-002, PL-003, PL-063
- *Story.* As a Plumb engineer/operator, I want the agent, not me, to fill tenant 1's build plan, so that the M1 run counts as automatic construction.
- *Acceptance criteria.*
  1. A registry template for the collection path holds the PA-001 step sequence (inventory.probe, integration.configure, integration.contract_test, collection.deploy_shadow, collection.backfill, collection.reconcile, collection.enable_incremental, verification.request) and nothing from the training or canary branches of the accounting fixture.
  2. The BUILD_AGENT fills accounts, sources, folders, the proposed watermark and budgets from the inventory; the plan passes `check_plan` with zero findings against tenant 1's envelope and inventory.
  3. Any human edit creates an ENGINEERING_INTERVENTION entry and a new plan digest; the attested M1 run has none (D4 condition 2).
- *Starting point.* The [accounting plan fixture](../fixtures/plans/accounting_evidence_preparation.json) (22 steps; gap 13 in the [MVP scope](03-mvp-scope.md)).

**E05-S07 Bounded repair with failure classification** — Phase P2 · Priority Must · Trace: PL-018, PL-001, PL-062
- *Story.* System story: repair is bounded by count, spend and elapsed time, keeps diagnostics, and cannot weaken tests, widen permissions or change the success metric.
- *Acceptance criteria.*
  1. Every failure is classified into one `FailureClass`; MISSING_AUTHORIZATION and MISSING_BUSINESS_DECISION are never retried and become DependencyRecords.
  2. Exceeding the attempt limit yields RETRY_EXHAUSTED and a terminal-failure outcome naming what was tried (PL-001); ATTEMPTS_EXCEEDED applies at plan check.
  3. A repair whose patch changes a protected test bundle digest, an allowlist or a threshold is rejected; a new artifact digest invalidates verification bound to the old one.
  4. Every attempt, including failed ones, appears in the ledger and in EIH/VD (E01-S06).
- *Starting point.* `FailureClass` ([common.py](../plumb/contracts/common.py) lines 263-273); REPAIR_BUDGET_GUARD in [machines.py](../plumb/statemachines/machines.py).

**E05-S08 Active-build cap** — Phase P2 · Priority Should · Trace: PL-017
- *Story.* Internal story (owner: Tech lead): at most 3 active builds run until M1R passes (D5, D9), so the team is not swamped.
- *Acceptance criteria.*
  1. A fourth build waits in VALIDATED with an explicit reason shown in the progress feed.
  2. The cap is configurable and drops to 2 if the D5 revisit trigger fires.
- *Starting point.* None.

### E06 Sandbox, secrets and egress

**Goal.** Generated code and document parsing run in disposable, credential-free sandboxes with mediated egress; secrets stay out of prompts, artifacts and telemetry; untrusted content cannot change authority (PL-006, PL-019, PL-051, PL-054).
**Why now.** PA-019 and PA-022 are in the M1 safety bundle; PA-026 applies on the first tenant where generated code runs; the PA-021 adaptation is mandatory by M3-lite (D4). PA-021 and PA-026 have no local analogue, so they need early infrastructure spikes.
**Package has.** `reject_secret_like`, a heuristic applied to every `*_ref` field and to error texts ([common.py](../plumb/contracts/common.py) line 107); AgentTask rejects credential-named fields. No sandbox, egress proxy, vault, webhook receiver or artifact scanner ([validation report](../VALIDATION_REPORT.md), "Not executed locally").

**E06-S01 Disposable build sandbox** — Phase P2 · Priority Must · Trace: PL-019, ADR-001, ADR-002
- *Story.* As the Firm owner, I want any code Plumb generates for my firm to run where it cannot reach production credentials, so that a bad mapping cannot leak or damage my data.
- *Acceptance criteria.*
  1. Each task runs in an isolated container or VM with scoped filesystem and network; it is destroyed afterwards, and authoritative state lives outside it.
  2. No production credential is mounted; a test confirms none is reachable from the workspace.
  3. A P1 spike decides managed versus self-built; if a managed sandbox passes PA-019 and PA-026 in M0 contract tests, the D12 revisit trigger applies to the security hire.
- *Starting point.* None.

**E06-S02 Credential resolver and vault** — Phase P1 · Priority Must · Trace: PL-006, PL-054, ADR-001, PA-019
- *Story.* System story: credentials are resolved only by the gateway for approved operations, with development and runtime credentials separate, so probes in P1 never expose a token.
- *Acceptance criteria.*
  1. Agents receive credential references, never values, and never general production administrator credentials (PL-006).
  2. PA-019's marker scan of prompts, artifacts, logs, traces and errors finds no credential (asserted in P1 for probes; PA-019 passes at P2 exit).
  3. Development and runtime credentials for the same provider are distinct, and each is limited to its operations.
- *Starting point.* `SourceRef` carries no credentials; secret heuristics.

**E06-S03 Egress proxy with per-operation allowlists** — Phase P2 · Priority Must · Trace: PL-054, PL-019, PA-019, PA-026
- *Story.* System story: sandbox network egress is mediated and allowlisted per operation, with SSRF and DNS controls.
- *Acceptance criteria.*
  1. Non-allowlisted, link-local and metadata hosts are denied with SCOPE_DENIED naming the operation (PA-019).
  2. DNS-encoded lookups and HTTPS posts to unlisted hosts are blocked (PA-026 paths a and b); redirects are not followed.
  3. Allowlists change only through platform policy, never through a repair (PA-026).
- *Starting point.* None.

**E06-S04 Hardened webhook receiver** — Phase P2 · Priority Must · Trace: PL-054, PL-024, PA-019
- *Story.* System story: document-store webhooks are verified, bounded and never trusted as authoritative state.
- *Acceptance criteria.*
  1. An invalid signature, a valid webhook replayed after six minutes (window: five minutes) and a 2 MiB payload (cap: 1 MiB) are each rejected with a distinct reason (PA-019).
  2. Callback registration to internal addresses is rejected.
  3. An incomplete signed webhook triggers an authoritative fetch through the allowlisted endpoint only.
- *Starting point.* None.

**E06-S05 Artifact scanner and exfiltration tests** — Phase P2 · Priority Must · Trace: PL-019, PL-054, PL-053, PL-006, PA-026
- *Story.* System story: generated code cannot exfiltrate tenant data through network, DNS, artifacts, model prompts or logs.
- *Acceptance criteria.*
  1. PA-026 passes on the first tenant where generated code runs: P2 if tenant 1's mapping needs generated code; otherwise P3, on tenant 3's provider swap (D4).
  2. Records written into a test-fixture artifact are caught, the step fails verification and the artifact is quarantined; the failure is classified IMPLEMENTATION_DEFECT with diagnostics kept.
  3. Evidence collected under COLLECT cannot be exported without EXPORT.
- *Starting point.* None (no local analogue).

**E06-S06 Parser sandbox for client documents** — Phase P4 · Priority Must · Trace: PL-019, PL-051, PL-054, PA-021
- *Story.* As the Reviewing accountant, I want a malicious or malformed client file to be quarantined, not opened in a way that harms the firm.
- *Acceptance criteria.*
  1. P4 exit: the accounting adaptation of PA-021's parser bounds (PA-P07) passes on client PDFs; it is not claimed as PA-021.
  2. Each parse runs with CPU, memory, time and page limits, no egress and no writes outside the workspace; type is detected by content; external connections are never followed; the sandbox is destroyed after each document.
  3. Unsafe files yield DATA_QUALITY_FAILED and a quarantine shown to the Reviewing accountant or Bookkeeper; a repair never disables the limits.
  4. If M1 parses document contents (for example to attribute by entity name), this story moves to P2 (D4).
- *Starting point.* None (no local analogue).

**E06-S07 Hostile-content containment and forged tool descriptions** — Phase P2 · Priority Must · Trace: PL-051, PL-014, PL-008, PL-006, PA-022
- *Story.* System story: documents, emails, API descriptions and tool descriptions are content; capability, scope and effect class come only from the registry and the envelope.
- *Acceptance criteria.*
  1. P2 exit: PA-022 passes. A forged tool description yields UNSUPPORTED_STEP_TYPE or UNKNOWN_CAPABILITY; the capability stays DOCUMENTED without a receipt; no credential is resolved; the attempt is logged with the description's digest.
  2. In the P4 sandbox, instructions embedded in a client PDF change no attribution authority, recipient or verification standard (PA-P19, the accounting analogue of PA-020, in the protected suite, E10-S06).
- *Starting point.* Registry-backed compiler (`UNKNOWN_CAPABILITY`, `UNSUPPORTED_STEP_TYPE` in [plan_checker.py](../plumb/checker/plan_checker.py)).

**E06-S08 Model gateway with per-tenant processor approval** — Phase P4 · Priority Must · Trace: PL-006, PL-053, PL-054, PA-026
- *Story.* As the Firm owner, I want my firm's documents sent only to model providers I approved, under no-training terms.
- *Acceptance criteria.*
  1. A prompt to a processor not in the envelope is refused (PA-026 path d).
  2. Each model call records tenant, case, model version and correlation id, with no content in ordinary telemetry (E19-S02).
  3. The subprocessor list matches the DPA (D9 item 9).
- *Starting point.* `approved_processors` on the envelope ([envelope.py](../plumb/contracts/envelope.py) line 141).

### E07 Integration factory

**Goal.** Reuse certified transport through a contract-tested substrate, and have the agent generate the tenant-specific semantics (folder and naming conventions to client + period + obligation; chart-of-accounts conventions) as declarative config or sandboxed generated code, contract-tested before activation (PL-002, PL-020, PL-021, PL-022).
**Why now.** This is the first half of PL-063 and the M1 construction bar the decision record chose (D4, option (b)): PA-001 alone proves only orchestration of a pre-built adapter, so the mapping must be agent-generated. Until M1R passes, the only permitted claim is "agent-configured certified connectors and agent-built collection" (D8).
**Package has.** `IntegrationSpec` ([integration.py](../plumb/contracts/integration.py) lines 258-328): path preference, explicit unit, currency, timezone and null semantics, a cursor strategy with overlap, and activation only after the 8 contract-test families (plus 2 for writes); `IntegrationPath` (VERIFIED_ADAPTER, DECLARATIVE_CONFIG, GENERATED_CODE, UI_ADAPTER) and `MaintenanceExposure`. No adapters, substrate integration or contract-test runner.

**E07-S01 Certified transport connectors through the substrate** — Phase P2 · Priority Must · Trace: PL-020, PL-021, PL-002, PA-001
- *Story.* System story: the agent configures certified connectors for tenant 1's document store and ledger metadata, recording the path used and its maintenance exposure.
- *Acceptance criteria.*
  1. The integration.configure step produces an IntegrationSpec declaring provider and account, exact operations, authentication reference, scopes, mappings, cursor strategy, rate limits, retry semantics, deletion behavior, effect class, verification probes and schema-drift handling (PL-021).
  2. `path_used` is VERIFIED_ADAPTER for transport, as PA-001 requires and PL-020's preference order allows.
  3. The configuration change is a deployable artifact with before and after state, affected resources and reversal limits (spec §10).
- *Starting point.* `IntegrationSpec`; substrate contract tests (E02-S05).

**E07-S02 Contract-test runner and account boundaries** — Phase P2 · Priority Must · Trace: PL-022, PL-021, PL-007, PL-008
- *Story.* System story: no adapter activates until the contract-test families pass against the provider sandbox and the tenant's account, with the results attested.
- *Acceptance criteria.*
  1. The runner executes pagination, empty_pages, duplicates, rate_limiting, authorization_failure, malformed_responses, schema_changes and account_boundaries; write adapters add business_state_verification and uncertain_write_behavior.
  2. Activation is refused unless every required family passes (the IntegrationSpec validator); a verifier attests the results.
  3. P2 exit: the accounting adaptation of PA-023's account_boundaries contract test (PA-P08: two client companies at one ledger provider) passes, and is not claimed as PA-023.
- *Starting point.* `WRITE_CONTRACT_TESTS` and the family list in [integration.py](../plumb/contracts/integration.py).

**E07-S03 Agent-generated client/period/obligation mapping** — Phase P2 · Priority Must · Trace: PL-002, PL-020, PL-021, PL-063, PA-001
- *Story.* As the Reviewing accountant, I want each document in the firm's folders filed to the right client, period and obligation without anyone at Plumb hand-wiring my firm's conventions.
- *Acceptance criteria.*
  1. The BUILD_AGENT generates the mapping from inventory samples, as declarative config (preferred) or generated code in the sandbox (E06-S01); its digest is pinned in the CollectionSpec.
  2. The mapping is contract-tested with semantic fixtures drawn from the tenant's own samples and attested before use.
  3. Low-confidence mappings raise focused questions (E11-S06) rather than defaulting.
  4. P2 exit (D4 conditions 2 to 4): zero human edits in the attested run; any edit to the mapping is an ENGINEERING_INTERVENTION entry and puts that attempt in the denominator.
  5. If tenant 1's semantics map fully through declarative config, that is accepted as construction evidence (D4 revisit trigger).
- *Starting point.* `FieldMapping` and the semantics models in [integration.py](../plumb/contracts/integration.py).

**E07-S04 Semantic mapping verification** — Phase P2 · Priority Must · Trace: PL-021, PL-022
- *Story.* System story: units, currency, time zone, identifiers, enums, lifecycle states and null semantics are checked, never assumed (spec §10).
- *Acceptance criteria.*
  1. Period boundaries are computed in the firm's time zone; a statement dated at a month boundary is tested.
  2. A mapping of minor units into a major-unit field without a conversion factor is rejected (local analogue: `test_cents_to_dollars_without_conversion_factor_rejected`).
  3. Provisional identities are never substituted for confirmed client identities (spec §6).
- *Starting point.* `UnitSemantics`, `CurrencySemantics`, `TimezoneSemantics`, `NullSemantics`.

**E07-S05 A non-VERIFIED_ADAPTER path at tenant 3** — Phase P3 · Priority Must · Trace: PL-020, PL-002, PL-063, PL-019, PA-001, PA-019, PA-026
- *Story.* Internal story (owner: Integration engineer): tenant 3's deliberate provider swap forces at least one operation onto a DECLARATIVE_CONFIG or GENERATED_CODE path, so the "automatically constructed" claim rests on more than pre-built adapters.
- *Acceptance criteria.*
  1. P3 exit: PA-001 attested on tenant 3 with at least one operation whose `path_used` is DECLARATIVE_CONFIG or GENERATED_CODE; PA-026 and PA-019 re-run on that path.
  2. Same engine for all tenants: fork count 0.
  3. The run is recorded as PA-P01, the proposed generated-path variant of PA-001 ([roadmap](04-roadmap.md)); the PA-001 attestations for tenants 2 and 3 are recorded separately.
  4. integration.generate_adapter (an INTERNAL_WRITE step in the fixture plans, SANDBOX_TESTED floor) earns its receipt and attestation before tenant 3's plan passes `check_plan` (E02-S07).
- *Starting point.* `IntegrationPath`.

**E07-S06 Schema-drift detection and quarantine** — Phase P2 · Priority Should · Trace: PL-021, PL-025, PL-048
- *Story.* System story: a changed source schema is quarantined, not interpreted.
- *Acceptance criteria.*
  1. A renamed or retyped field on the document-store or ledger metadata pauses only the affected collection, publishes `failure_state`, and writes nothing of the new shape.
  2. Unaffected sources continue.
  3. The incident is classified SOURCE_SCHEMA_CHANGE and routed to Plumb, repaired manually and logged as OPERATIONAL_REPAIR until E22-S04 exists.
- *Starting point.* `SchemaDriftHandling` in [integration.py](../plumb/contracts/integration.py).

**E07-S07 Artifact reuse by digest across tenants** — Phase P3 · Priority Must · Trace: PL-063, PL-062, PL-053
- *Story.* Internal story (owner: Integration engineer): mapping patterns, collection templates, adapter tests and failure fixtures, stripped of customer data, are reused by digest, so reuse can be measured (experiment 6).
- *Acceptance criteria.*
  1. P3 exit: artifact reuse rate by digest is recorded with fork count 0; the target of 60% or more by tenant 3 is a hypothesis.
  2. Reused artifacts contain no tenant identifiers or data (scanner check, E18-S05).
- *Starting point.* Digest-addressed artifacts (`ArtifactRef`).

### E08 Collection factory and health

**Goal.** For each permitted source: shadow, backfill from an agreed watermark, reconcile, go incremental, publish honest health, and prove the path with a live change (PL-023, PL-024, PL-025).
**Why now.** The collection path is both the M1 artifact and the interim customer deliverable (D2): a document a client drops into the firm's folder appears exactly once, attributed to the right client and period, with lineage, within the 5-minute health deadline.
**Package has.** `CollectionSpec` with watermark, backfill boundary, idempotent event identity, mandatory reconciliation, webhook-must-fetch and a 4-signal `HealthContract` ([collection.py](../plumb/contracts/collection.py) lines 91-219). The COLLECTOR machine runs PLANNED, SHADOW, BACKFILLING, RECONCILING, ACTIVE, and allows DEGRADED and PAUSED only from ACTIVE (PAUSED also from DEGRADED); PAUSED→ACTIVE is guarded by `coverage_restored` ([machines.py](../plumb/statemachines/machines.py) lines 324-345). SQL `collectors` design. No collector runtime.

**E08-S01 Purpose-justified CollectionSpec generation** — Phase P2 · Priority Must · Trace: PL-023, PL-053, PL-063
- *Story.* System story: the agent generates a CollectionSpec that names the objective, sources, fields, join strategy, incremental mechanism, retention, destination, access policy, quality checks and evidence of permitted purpose.
- *Acceptance criteria.*
  1. Produced by the BUILD_AGENT and contract-tested (D4 condition 3).
  2. Fields not needed by the objective are refused; tax-return folders are excluded (E18-S02).
  3. Every source in the spec has COLLECT granted, or the plan check reports PURPOSE_DENIED.
- *Starting point.* `CollectionSpec`.

**E08-S02 Shadow deployment and backfill from the agreed watermark** — Phase P2 · Priority Must · Trace: PL-024, PL-017
- *Story.* As the Firm owner, I want to confirm how far back Plumb reads my history, so that collection matches what I agreed.
- *Acceptance criteria.*
  1. The proposed watermark (12-24 months) is shown on the implementation card and confirmed by the Firm owner (proposed answer to MVP open question 3).
  2. The collector moves PLANNED→SHADOW→BACKFILLING; results in shadow are labeled "not yet trusted".
  3. A worker killed during backfill resumes from its persisted cursor without duplicates.
- *Starting point.* `Watermark`, `BackfillBoundary`, `SourceCursor`.

**E08-S03 Reconcile counts and sampled identities** — Phase P2 · Priority Must · Trace: PL-024
- *Story.* System story: before going incremental, stored counts and sampled identities are reconciled against the source.
- *Acceptance criteria.*
  1. Source count equals stored distinct count; sampled identities match.
  2. A mismatch returns RECONCILING→BACKFILLING; a persistent mismatch blocks collection.enable_incremental with DATA_QUALITY_FAILED.
- *Starting point.* `Reconciliation`; RECONCILING→BACKFILLING edge.

**E08-S04 Incremental capture with backfill and live convergence** — Phase P2 · Priority Must · Trace: PL-024, PL-025, PA-005
- *Story.* As a Bookkeeper, I want a document to appear once, even when the provider sends its notification late or twice, so that I never chase something the firm already holds.
- *Acceptance criteria.*
  1. Webhooks plus overlapping polling windows, idempotent event identity, explicit reordering and correction policies.
  2. P2 exit: the collector half of PA-005 (PA-P16) passes: a delayed webhook, overlap polling and a duplicated delivery yield exactly one event, and a stale "deleted" webhook triggers an authoritative fetch.
  3. Only document stores with webhooks plus overlap polling are supported (D1 qualification).
- *Starting point.* `IncrementalMechanism`, `ReorderingPolicy`, `CorrectionPolicy`.

**E08-S05 Collector health publication** — Phase P2 · Priority Must · Trace: PL-025, PL-010, PL-048, PA-011
- *Story.* As the Reviewing accountant, I want to see when a source has gone quiet, so that an unknown item is never read as missing or as received.
- *Acceptance criteria.*
  1. Each collector publishes freshness, lag, completeness and failure state.
  2. P2 exit: the health half of PA-011 (PA-P17) passes: with the provider endpoint blocked, the collector is DEGRADED with freshness, lag and failure state published within five minutes of its (five-minute) health deadline, and dependent items show Presence UNKNOWN with fact status STALE, never CONFIRMED_ABSENT.
  3. On restore, it reconciles from its watermark with overlap; PAUSED→ACTIVE only when `coverage_restored` is computed true (E05-S03).
- *Starting point.* `HealthContract`.

**E08-S06 Pause and degrade during shadow and backfill** — Phase P2 · Priority Should · Trace: PL-025, PL-057, PA-008
- *Story.* System story: a grant that expires, or a source that fails, during shadow, backfill or reconciliation is represented truthfully.
- *Acceptance criteria.*
  1. The COLLECTOR machine gains edges from SHADOW, BACKFILLING and RECONCILING to PAUSED and DEGRADED, and a resume edge back to the paused stage guarded by `coverage_restored`. Today those states can only move forward or to RETIRED.
  2. An expiring mailbox grant during backfill moves that collector to PAUSED with "grant expired" and leaves others running (the PA-008 pattern).
- *Starting point.* The COLLECTOR transition table ([machines.py](../plumb/statemachines/machines.py) lines 324-345).

**E08-S07 Live-change verification of the collection path** — Phase P2 · Priority Must · Trace: PL-063, PL-002, PL-009, PL-023, PL-024, PA-001
- *Story.* As the Firm owner, I want proof on my own data that a document added outside Plumb is filed correctly, before Plumb calls the path working.
- *Acceptance criteria.*
  1. P2 exit: PA-001 passes as written with a verifier attestation: exactly one evidence event with every PL-009 field and lineage to the IntegrationSpec, CollectionSpec and build-step digests within the 5-minute health deadline; the client and period obligation record changed; `path_used` VERIFIED_ADAPTER; build VERIFIED; zero ENGINEERING_INTERVENTION entries, CUSTOMER_AUTHORIZATION allowed.
  2. A deployed schedule or a successful deployment response without the observed event never passes.
  3. Tenant 1's 90-day pilot clock starts at this attestation (D7).
- *Starting point.* PA-001 in the [catalog](../acceptance/production_acceptance_catalog.yaml) line 125; live-change injector (E10-S04).

**E08-S08 Read-only mail-history collector and historical baseline** — Phase P4 · Priority Should · Trace: PL-023, PL-024, PL-053
- *Story.* As the Firm owner, I want to see how often the firm chased the same client for the same item in the last 24 months, clearly labeled as history, not as Plumb's result.
- *Acceptance criteria.*
  1. INSPECT and COLLECT only; no write scope is requested.
  2. 24 months of reminder history attributed to client-period-obligation; the duplicate-chase baseline is labeled "historical, non-causal" (spec §7) and never counted as a PL-001 outcome.
  3. If at least 2 of 5 partners refuse mailbox scopes, or vendor approval is not granted by M3-lite, a forwarding-address intake replaces it (R7).
- *Starting point.* The fixture mailbox grant (INSPECT, COLLECT).

**E08-S09 Explicit block and degrade per obligation** — Phase P4 · Priority Must · Trace: PL-025, PL-010, PA-011
- *Story.* As the Reviewing accountant, I want a package to say "waiting for source coverage" rather than guess when a source is stale.
- *Acceptance criteria.*
  1. The Plumb domain expert defines block versus degrade per obligation type.
  2. P4 exit: PA-011 passes in sandbox for the workflow: the step blocks explicitly, the readiness verdict is BLOCKED_STALE_SOURCE, and the alert links the affected cases and release.
- *Starting point.* None.

### E09 Evidence store, time axes and corrections

**Goal.** Evidence keeps provenance on three time axes; derived facts carry status; unknown absence never reads as confirmed absence; corrections are scoped and reversible (PL-009, PL-010, PL-011; ADR-005).
**Why now.** "Unknown is not absent" is the product's core promise (D2), and the readiness ledger is built on it from P2.
**Package has.** `EvidenceEvent`, `DerivedFact`, `ResolutionCandidate`, `ScopedCorrection`, `ObjectResolution`, `ObjectLink` and `EvidencePacket` with `facts_as_of` ([evidence.py](../plumb/contracts/evidence.py) lines 59-322); `Presence` (PRESENT, CONFIRMED_ABSENT, UNKNOWN) and `FactStatus` ([common.py](../plumb/contracts/common.py) lines 285-301); SQL `evidence_events`, `objects`, `object_links`, `facts`. No store or resolution engine.

**E09-S01 Evidence event store on three time axes** — Phase P2 · Priority Must · Trace: PL-009, ADR-005, PA-001
- *Story.* System story: every evidence event keeps source identity, external record and version, tenant, event, observation and availability times, content digest, access policy reference, retention class and extraction version; raw content is referenced, not copied.
- *Acceptance criteria.*
  1. PA-001's inspection of the event fields and lineage passes (with E08-S07).
  2. A later backfill improves current history but does not change what a `facts_as_of` query returns for an earlier instant (the spec's August, September, October example as a test).
  3. Raw content lives in tenant-prefixed, content-addressed storage (E03-S05).
- *Starting point.* `EvidenceEvent`; local analogue `test_event_preserves_time_axes_and_references_raw_content`.

**E09-S02 Derived facts with status and presence** — Phase P2 · Priority Must · Trace: PL-010
- *Story.* As the Reviewing accountant, I want each required item marked PRESENT, CONFIRMED_ABSENT or UNKNOWN with its evidence, so that I can trust a "missing" flag.
- *Acceptance criteria.*
  1. Every obligation fact carries supporting evidence, derivation version, validity interval and a status (OBSERVED, INFERRED, CONFIRMED, DISPUTED, STALE, SUPERSEDED).
  2. CONFIRMED_ABSENT requires an authoritative reference: a recorded human confirmation or an authoritative source record. Inference alone never yields it (validator; proposed answer to MVP open question 4).
  3. Confidence never substitutes for source authority.
- *Starting point.* `DerivedFact`, `Presence`, `FactStatus`.

**E09-S03 Client and period resolution with candidates** — Phase P2 · Priority Must · Trace: PL-011, PL-010, PA-003
- *Story.* As the Reviewing accountant, I want a misfiled statement shown with both possible clients, not silently filed under the folder owner.
- *Acceptance criteria.*
  1. Ambiguous attributions keep all candidates as INFERRED or DISPUTED below the auto-accept threshold (threshold-sheet hypothesis); neither obligation counts as satisfied; a focused question is raised (E11-S06).
  2. Merge and split history is kept; provisional ids never replace confirmed client identities.
  3. PA-003 itself is attested in the P4 sandbox (E10-S05).
- *Starting point.* `ResolutionCandidate`, `ObjectResolution`, `MergeRecord`, `SplitRecord`.

**E09-S04 Scoped, reversible corrections with an impact set** — Phase P2 · Priority Should · Trace: PL-011
- *Story.* As the Reviewing accountant, I want to fix one attribution without changing every similar document, and see what a correction will touch before I apply it.
- *Acceptance criteria.*
  1. A correction applies only to its subject (local analogue `test_correction_is_scoped_never_global`).
  2. The impact set is computed and previewed; dependent facts and packages are revalidated on apply; the correction can be reversed.
  3. Resolving PA-003's case moves exactly one document link and recomputes the impact set for both clients.
- *Starting point.* `ScopedCorrection`.

**E09-S05 Corrected statements supersede, never overwrite** — Phase P4 · Priority Must · Trace: PL-009, PL-010, PA-006
- *Story.* System story: a corrected source document creates a new event; the prior fact becomes SUPERSEDED and the case version increments.
- *Acceptance criteria.*
  1. The data side of PA-006: external version 2 stored as a new event; the earlier fact SUPERSEDED, not overwritten; the case advances one version.
  2. The package is recomputed (E13-S07) and the change is visible in the audit trail.
- *Starting point.* External-version fields on `EvidenceEvent`.

**E09-S06 Answers become versioned conventions** — Phase P4 · Priority Must · Trace: PL-011, PL-041, PL-010, PA-004
- *Story.* As the Firm owner, I want to answer a convention question once and never be asked it again.
- *Acceptance criteria.*
  1. P4 exit: PA-004 passes in sandbox: only the affected case waits in WAITING_INPUT; the answer is stored as a versioned policy input; the next statement of the same shape is attributed without a new question.
  2. Repeat-ask rate is 0; a convention is asked again only if its inputs change, and then the difference is shown.
- *Starting point.* None (conventions table, E03-S06).

### E10 Independent verifier and fault-injection harness

**Goal.** An organizationally independent verifier decides completion from actual state, and a fault-injection harness makes the HIGH-severity scenarios executable (PL-042, PL-043, PL-044, PL-061; ADR-007).
**Why now.** Every VERIFIED step and every release gate needs an attestation, and 24 of 30 scenarios need real adapters; most HIGH scenarios need fault injection, which is effectively an unlisted product (D12). The verification engineer is hired by about week 6 (hypothesis) and reports outside the build team.
**Package has.** `VerificationAttestation` ([verification.py](../plumb/contracts/verification.py) line 85): a VERIFIER principal distinct from the producer, evidence at the attested level, a protected bundle digest. `check_release` consumes attestations by recomputed digest ([release_checker.py](../plumb/checker/release_checker.py) line 94); ADVERSARIAL_TESTS_MISSING is only a WARNING, enforced by check name (lines 50-60). The registry's `plumb-verifier` records refer to a service that does not exist. No harness.

**E10-S01 Thin verifier service** — Phase P2 · Priority Must · Trace: PL-042, PL-016, ADR-007
- *Story.* As the Independent verifier, I want to issue attestations from actual artifacts and external state with my own credentials, so that no builder can certify its own work.
- *Acceptance criteria.*
  1. Each attestation records verifier identity and version, input artifact digest, evidence, result, timestamp, environment and scope.
  2. A BUILD_AGENT or RUNTIME_AGENT attempt to write an attestation is rejected; the implementation job cannot write to the verifier.
  3. Attestations are immutable; `check_release` reports ATTESTATION_NOT_INDEPENDENT for any attestation whose producer is the assessed builder.
  4. Build starts in P1; live by P2 exit.
- *Starting point.* `VerificationAttestation`, `check_release`.

**E10-S02 Protected bundle store** — Phase P2 · Priority Must · Trace: PL-044, PL-018, ADR-007
- *Story.* System story: test bundles and holdouts are unreadable and unwritable by builders, and a failed protected test returns only a controlled diagnostic category.
- *Acceptance criteria.*
  1. An access test from a builder workspace to the bundle store fails.
  2. A failed protected check returns a category, not the holdout contents.
  3. Bundle digests are pinned in attestations; a repair that changes a bundle digest is rejected (E05-S07).
- *Starting point.* `protected_bundle_digest` on attestations.

**E10-S03 Fault-injection harness v1** — Phase P2 · Priority Must · Trace: PL-061, PL-024, PL-025, PL-017, PA-005, PA-011, PA-015
- *Story.* As the Independent verifier, I want to delay and duplicate webhooks, block endpoints, freeze workers and advance clocks against provider sandboxes, so that M1's safety scenarios can actually run.
- *Acceptance criteria.*
  1. Injections: webhook delay and duplication, network-boundary block, worker freeze without request cancellation, process kill, clock advance.
  2. P2 exit: the harness drives the collector half of PA-005, the health half of PA-011 and PA-015.
  3. Every injection is logged with a correlation id (E19-S01).
  4. P5 extends it with post-acceptance timeouts for PA-009 (E17-S04).
- *Starting point.* None.

**E10-S04 Live-change injector for PA-001** — Phase P2 · Priority Must · Trace: PL-042, PL-063, PA-001
- *Story.* As the Independent verifier, I want to upload a test document as a user outside Plumb and check the resulting evidence and obligation record myself.
- *Acceptance criteria.*
  1. The upload uses a test identity with access to the permitted folder only, agreed with the Firm owner.
  2. The verifier queries the evidence store and object layer directly and attests the result (E08-S07); the test document is removed afterwards by the same identity.
- *Starting point.* PA-001 steps in the [catalog](../acceptance/production_acceptance_catalog.yaml).

**E10-S05 Appendix B failure set in the protected sandbox suite** — Phase P4 · Priority Must · Trace: PL-043, PL-061, PL-042, PA-002, PA-003, PA-004, PA-006, PA-008, PA-010, PA-011
- *Story.* As the Reviewing accountant, I want the workflow proven against the failures that would embarrass the firm (wrong client, ambiguous period, corrected statement, expired permission, changed approval, stale source) before it touches real cases.
- *Acceptance criteria.*
  1. The protected suite holds the nine Appendix B failure cases; by content they correspond to PA-003, PA-004, PA-005, PA-006, PA-007, PA-008, PA-009, PA-010 and PA-011 (an inference; the catalog does not label them).
  2. P4 exit: PA-002 receives a BUSINESS_OUTCOME attestation, and PA-003, PA-004, PA-006, PA-008, PA-010 and PA-011 pass in sandbox. The gateway-dependent PA-005 and PA-009 sandbox runs are P5 (E17); PA-007 needs a canary and is P6.
  3. R4 rule: if generated workflows fail more than 10% of these cases after bounded repair across two tenants, Plumb stops generating workflow logic and uses certified template workflows (threshold is a hypothesis).
- *Starting point.* Catalog scenarios; local reference checks named in each scenario.

**E10-S06 Adversarial suite as a blocking gate** — Phase P4 · Priority Must · Trace: PL-061, PL-043, PL-051
- *Story.* System story: adversarial tests run on the actual gateway and sandbox before customer deployment, and a HIGH-severity failure blocks activation.
- *Acceptance criteria.*
  1. The production gate treats a missing or failed adversarial check as blocking; the local checker's ADVERSARIAL_TESTS_MISSING warning remains a warning.
  2. Accounting adversarial cases include PA-P19 (instructions embedded in client documents or email), forged recipients and confused client identity.
  3. A release with a failing HIGH scenario cannot move past SHADOW.
- *Starting point.* `ADVERSARIAL_TESTS_MISSING` in [release_checker.py](../plumb/checker/release_checker.py).

**E10-S07 Ledger-audit tooling** — Phase P2 · Priority Must · Trace: PL-003, PL-062, PA-027
- *Story.* Internal story (owner: Verification engineer, for the ledger auditor): Plumb's engineering activity sources are reconciled against the effort ledger, so that unrecorded work is found by evidence, not by asking.
- *Acceptance criteria.*
  1. The tooling compares repository commits, deploy logs, support-access sessions (admin audit) and change records touching a tenant against that tenant's ENGINEERING_INTERVENTION and OPERATIONAL_REPAIR entries, and lists unmatched activity.
  2. It produces the audit record E01-S07 consumes, at M1, M1R, M5 and monthly.
- *Starting point.* None.

**E10-S08 Segregated domain acceptance corpus** — Phase P4 · Priority Should · Trace: PL-044, PL-043
- *Story.* As the Plumb domain expert, I want a protected accounting corpus of representative real cases, separate from tuning and repair examples, so that package quality is measured honestly.
- *Acceptance criteria.*
  1. The corpus registry records the source, segregation statement and refresh date of every case; it is refreshed when repeated use risks overfitting.
  2. Synthetic cases are labeled and never cited as business performance (PL-044).
  3. Verifier calibration against the domain expert's judgments is recorded per release.
- *Starting point.* `EvaluationReport` requires held-out splits and denominators ([evaluation.py](../plumb/contracts/evaluation.py)).

### E11 Customer surfaces

**Goal.** The minimum App. A §6 surfaces: progress feed, blocked-dependency card, implementation card, read-only close-readiness ledger, results-and-effort view and focused-question queue (D3 (j), (l)). Detailed behavior is specified in the [MVP scope](03-mvp-scope.md) section 4; this epic holds the delivery stories.
**Why now.** The readiness ledger is the interim deliverable at M1 (D2), and the customer must see the work without editing a DAG (spec App. A §6).
**Package has.** None of these surfaces, and no API object for any of them. Building blocks: build, step and collector state enums; `listBuildEvents` and `listOutcomes` in the [OpenAPI proposal](../api/openapi.yaml); `DependencyRecord`; `group_missing_authorizations` ([approval_checker.py](../plumb/checker/approval_checker.py) line 210).

**E11-S01 Honest progress feed** — Phase P2 · Priority Must · Trace: PL-016, PL-017, PL-003, PL-042, PL-057, PA-001
- *Story.* As the Firm owner, I want plain-language progress during the build that never calls something done before it is verified.
- *Acceptance criteria.*
  1. States come only from persisted build-ledger events; a deployment response without an attestation renders "Being verified", never "Verified".
  2. Every ENGINEERING_INTERVENTION and OPERATIONAL_REPAIR entry on a build appears in its feed with minutes.
  3. After a worker restart the feed is rebuilt with no gap.
  4. The words "done", "complete", "live" and "autonomous" never appear without the evidence that permits them.
- *Starting point.* `BuildState`, `BuildStepState`, `CollectorState`; `listBuildEvents`.

**E11-S02 Blocked-dependency card** — Phase P2 · Priority Must · Trace: PL-001, PL-041, PL-017, PL-056, PA-004, PA-008, PA-011
- *Story.* As the Firm owner, I want any block to name exactly what is missing, who can resolve it and what resumes, with completed work kept.
- *Acceptance criteria.*
  1. Fields: what is blocked, exact missing item (names, never values), why (error and failure class), one resolver, one action, what resumes, since when, billing state (D7).
  2. Plain-language copy exists for all 13 error classes; missing authority never offers a generic retry.
  3. Unrelated work continues; requests are grouped per resolver and error class (E15-S02).
  4. The PA-008 card fields (MISSING_AUTHORIZATION, exact source and purposes, resolver HUMAN_OWNER, blocked steps, resumes_after) render correctly; PA-008 itself is attested in P4.
- *Starting point.* `DependencyRecord`, `ErrorClass`, `FailureClass`.

**E11-S03 Implementation card screen** — Phase P2 · Priority Must · Trace: PL-005, PL-041, PL-040
- *Story.* As the Firm owner, I want to read one card and approve or decline the intervention in under five minutes (hypothesis).
- *Acceptance criteria.*
  1. Renders the E04-S04 object; a changed card shows the impact diff and test evidence.
  2. Approve goes through IdP step-up (E15-S03); declining leaves a resumable dependency.
  3. Usability test with the tenant 1 Firm owner before P2 exit; time to decision recorded as CUSTOMER_AUTHORIZATION.
- *Starting point.* None.

**E11-S04 Read-only close-readiness ledger** — Phase P2 · Priority Must · Trace: PL-009, PL-010, PL-011, PL-024, PL-025, PA-001, PA-003, PA-005, PA-011
- *Story.* As a Bookkeeper, I want one view of every recurring client-period showing what is held, confirmed absent or unknown, with sources, so that I stop hunting for documents.
- *Acceptance criteria.*
  1. One row per in-scope client-period and one per obligation within it, with presence, fact status, provenance and source health.
  2. UNKNOWN is never shown as "Missing"; a stale source shows Presence UNKNOWN with fact status STALE and "waiting for source coverage" (PA-011).
  3. A document added outside Plumb appears exactly once (PA-001); duplicated notifications do not duplicate it (PA-005 collector half); a misfiled statement shows both candidates (PA-003 pattern).
  4. No request, draft or send controls before the Draft tier ships.
  5. Weekly active use by Bookkeepers is measured (D2 revisit trigger: under half of active bookkeepers weekly).
- *Starting point.* Evidence contracts (E09).

**E11-S05 Results-and-effort view** — Phase P2 · Priority Must · Trace: PL-003, PL-059, PL-062, PL-001, PL-041
- *Story.* As the Firm owner, I want to see every human minute spent on my firm, by category and side, next to the outcomes, so that I can judge the value and see the labor.
- *Acceptance criteria.*
  1. P2 panels: effort ledger by category, person, side, build and close with failed, blocked and abandoned attempts; EIH/VD with platform-investment hours beside it, never netted; outcome mix per goal (PL-001); time to first verified event split; interruption load; a "supervised" label.
  2. P5 panels: eligible client-periods, attested packages, accepted packages (co-headline) with rate, correct-package rate, accountant minutes against the month-0 baseline, Plumb minutes per accepted package, cost per package.
  3. Every rate shows numerator and denominator with exclusions kept; no hours-saved or ROI figure without a baseline and denominator; the historical baseline is labeled non-causal; technical and commercial success are separate.
- *Starting point.* `listOutcomes`; `OutcomeObservation`.

**E11-S06 Focused-question queue with a budget** — Phase P2 · Priority Must · Trace: PL-041, PL-010, PL-011, PL-003, PA-003, PA-004
- *Story.* As the Firm owner, I want only questions whose answer changes the plan, each with the evidence and the consequence of each answer, batched into my weekly session.
- *Acceptance criteria.*
  1. Each question shows the evidence, the candidates, the consequence of each answer, who should answer, what is blocked (only the affected cases, in WAITING_INPUT) and what happens if unanswered (the item stays UNKNOWN).
  2. Budget per workflow (hypotheses, D6): at most 5 DOMAIN_CLARIFICATION questions at onboarding, at most 2 new per close after close 1, repeat-ask rate 0; overruns create a defect automatically.
  3. Answers are recorded as DOMAIN_CLARIFICATION minutes and stored as conventions (E09-S06).
- *Starting point.* `ResolutionCandidate`; `ScopedCorrection`.

**E11-S07 Chase-history column and historical duplicate-chase report** — Phase P4 · Priority Should · Trace: PL-010, PL-059
- *Story.* As a Bookkeeper, I want to see who already chased a client for an item, so that two of us do not ask twice.
- *Acceptance criteria.*
  1. The readiness ledger shows staff member, date and message reference per obligation from mail history (E08-S08); before P4 it reads "Chase history not connected".
  2. The 24-month report shows duplicate chases per client-period-obligation, re-requests for documents already held and days to receive, labeled historical and non-causal.
- *Starting point.* None.

**E11-S08 "What Plumb would have done" shadow report** — Phase P5 · Priority Must · Trace: PL-001, PL-059, PL-043, PA-003, PA-005
- *Story.* As the Firm owner, I want shadow packages compared with my accountants' actual decisions, so that moving from shadow to the Prepare canary (founder decision 17) rests on evidence.
- *Acceptance criteria.*
  1. Per client-period: correct package or not; false-chase rate (items flagged missing that were held); missing-item recall; wrong-client attribution; each with denominators and exclusions kept.
  2. P5 exit measures for tenant 1: at least 30 client-periods in one full close; false-chase rate of 2% or less and recall of 90% or more (proposed thresholds).
  3. The effect ledger shows zero DISPATCHED effects for the shadow release.
- *Starting point.* None.

**E11-S09 Customer export** — Phase P2 · Priority Should · Trace: PL-052, PL-053, PL-003
- *Story.* As the Firm owner, I want to export everything Plumb built and recorded for my firm in open formats, so that I can leave at any time.
- *Acceptance criteria.*
  1. Export covers IntegrationSpec, CollectionSpec, WorkflowSpec, tests, evidence, packages and the labor ledger (D9 exit terms).
  2. The export contains no other tenant's identifiers (PA-017 export surface). How the EXPORT purpose applies to the firm's own copy is an open question for counsel; until it is settled, export checks an EXPORT grant on each source (PL-053).
- *Starting point.* None.

### E12 Opportunity library and OpportunitySpec

**Goal.** Replace open-ended discovery with a vertical opportunity library in which Plumb still writes a complete OpportunitySpec with current-process and native-feature baselines; "configure the firm's native reminders" is a delivered intervention (PL-012, PL-013; D3).
**Why now.** The implementation card's benefit hypothesis needs an OpportunitySpec from P2, and the R5 trigger reads the native-feature comparisons.
**Package has.** `OpportunitySpec` ([opportunity.py](../plumb/contracts/opportunity.py) line 182): requires CURRENT_PROCESS and NATIVE_FEATURE comparisons, a prospective measurement plan (STAGED_ROLLOUT or COMPARABLE_CASE_COHORTS), overlap references and auto-rejection when the net-value upper bound is not positive; `InterventionKind` includes NATIVE_SETTING and REMOVE_STEP. `startOpportunityDiscovery` and `listOpportunities` are proposed; there is no `getOpportunity` or `selectOpportunity`, although the SQL has `opportunities.selected_at`. No discovery logic.

**E12-S01 Accounting opportunity library v1** — Phase P2 · Priority Should · Trace: PL-012, PL-013
- *Story.* As the Plumb domain expert, I want a curated set of accounting interventions with obligation templates, so that discovery starts from proven shapes.
- *Acceptance criteria.*
  1. Entries: close-readiness collection path; preparation-only review package; native reminder configuration in the firm's existing tools; consolidated request drafts (gated); consolidated policy-approved sends (gated).
  2. Each entry instantiates a complete OpportunitySpec that passes the contract's validators.
- *Starting point.* `OpportunitySpec`; the fixture `opp-acct-missing-evidence-review-package` plan input.

**E12-S02 OpportunitySpec for tenant 1's collection path** — Phase P2 · Priority Must · Trace: PL-012, PL-001
- *Story.* As the Firm owner, I want the expected benefit of the collection path stated as a measurable hypothesis before I approve it.
- *Acceptance criteria.*
  1. States objective, eligible client-periods, baseline (month-0 time study reference, E14-S01), evidence coverage, proposed change, dependencies, expected benefit range, failure cost, review cost and a prospective measurement plan.
  2. It is an input to the tenant 1 plan and feeds the implementation card.
- *Starting point.* `OpportunitySpec`, `MeasurementPlan`, `BenefitRange`.

**E12-S03 Native-feature baseline comparison for the review workflow** — Phase P4 · Priority Should · Trace: PL-013, PL-012, PL-031
- *Story.* As the Firm owner, I want Plumb to tell me when my existing tools already do the job, and configure them instead of building something new.
- *Acceptance criteria.*
  1. The candidate system is compared with the current process and the firm's native features (for example Xero or Financial Cents reminders and checklists), on review time and errors as well as cost.
  2. If native configuration suffices, Plumb configures and verifies it and records a verified NATIVE_SETTING intervention, billed at the same rate (D7).
  3. Each comparison is stored for the R5 trigger (at least 3 of 5 qualified prospects choosing native tools after a PL-013 comparison) and as evidence for PA-P11, the proposed opportunity-selection scenario (recommended from tenant 4's onboarding in P5, required in P6).
- *Starting point.* `CandidateSystem`, `REQUIRED_COMPARISON_KINDS`.

**E12-S04 Opportunity read and selection API** — Phase P2 · Priority Should · Trace: PL-012, PL-055
- *Story.* As the Firm owner, I want to see proposed opportunities, including rejected and blocked ones, and select one through its implementation card.
- *Acceptance criteria.*
  1. `getOpportunity` and `selectOpportunity` exist; selection sets `opportunities.selected_at` and starts the implementation card flow.
  2. REJECTED_NEGATIVE_VALUE and BLOCKED opportunities are shown with their reasons and blocking conditions.
- *Starting point.* `OpportunityStatus`; SQL `opportunities`.

**E12-S05 Portfolio overlap record** — Phase P6 · Priority Could · Trace: PL-012
- *Story.* As the Firm owner, I want projected benefits across opportunities summed without double counting.
- *Acceptance criteria.*
  1. The overlap record prevents two opportunities claiming the same labor; enabling work such as the mapping is credited to the portfolio it unlocks (spec §7).
- *Starting point.* Overlap references on `OpportunitySpec`.

**E12-S06 Experiment-1 proxy: structured shadowing** — Phase P3 · Priority Must · Trace: PL-007, PL-012
- *Story.* Internal story (owner: Founder): during tenant 2 and 3 onboarding, compare opportunities found from APIs and history alone with the same plus a 2-hour structured shadowing session (D11).
- *Acceptance criteria.*
  1. Count deployable, feasibility-passing opportunities per firm in each arm; shadowing minutes are logged as DOMAIN_CLARIFICATION.
  2. P3 exit: the result is recorded. If shadowing adds at least 1 such opportunity per firm in both firms, a consented, event-triggered capture pilot is planned after M5; otherwise capture stays out.
- *Starting point.* None.

**E12-S07 Blocked-opportunity backlog with targeted re-evaluation** — Phase P6 · Priority Could · Trace: PL-012, PL-049, PL-050
- *Story.* As the Firm owner, I want blocked opportunities to say what would unlock them, and to be re-evaluated when that changes.
- *Acceptance criteria.*
  1. Blockers are stated as requirements (model accuracy, price ceiling, an API operation, enough labeled cases, a missing authorization) (spec §20).
  2. A registry maturity change triggers re-evaluation of linked opportunities only; no broad daily re-evaluation.
- *Starting point.* `BlockingCondition` in [opportunity.py](../plumb/contracts/opportunity.py).

### E13 Preparation-only workflow and ReviewPackage

**Goal.** A preparation-only WorkflowSpec over certified primitives produces one verifier-attested ready-for-review package per client-period, attested in sandbox (PA-002 as written) and then run in production shadow with no external communication (PL-001, PL-034, PL-035, PL-036; D3 phase 2).
**Why now.** The package is what the verifier attests, what the Reviewing accountant signs off and what the firm pays for (D7), and it does not exist as a contract. P4 exit and the P5 first measurable deliverable depend on it.
**Package has.** `WorkflowSpec` with case identity, triggers, typed inputs, states, bounds, durable waits, human decision points and deterministic rules ([workflow.py](../plumb/contracts/workflow.py) line 209). `ReviewPackage` exists only as an ArtifactKind value ([common.py](../plumb/contracts/common.py) line 371); no capability produces it and no API reads it. SQL `cases.review_state` (NONE, READY_FOR_REVIEW, APPROVED, REJECTED). In the [accounting plan fixture](../fixtures/plans/accounting_evidence_preparation.json), `compile-review-workflow` depends on `train-categorization-candidate`.

**E13-S01 ReviewPackage contract** — Phase P4 · Priority Must · Trace: PL-001, PL-010, PL-040, PL-042, PL-053
- *Story.* As the Reviewing accountant, I want each package to be a defined, versioned record of every required item with its evidence, so that what I sign is exactly what was attested.
- *Acceptance criteria.*
  1. A Pydantic contract subclassing `ArtifactHeader` with the fields in the [MVP scope](03-mvp-scope.md) section 5 (client, period, case id and version, obligations with presence, fact status and evidence ids, readiness verdict, `facts_as_of`, source freshness, attestation reference, review state and outcome, sign-off reference, pinned versions, supersedes, close deadline, billing flag); JSON Schema generated and `--check` passes.
  2. Validators: CONFIRMED_ABSENT needs an authoritative reference; the readiness verdict agrees with the obligation list; APPROVED needs a sign-off record not produced by an agent; an item from an excluded source makes the package invalid; the attestation producer is a VERIFIER distinct from the workflow.
  3. A registry capability declares ReviewPackage as a workflow output; `listReviewPackages`, `getReviewPackage` and `recordReviewDecision` operations exist.
- *Starting point.* `ArtifactKind.REVIEW_PACKAGE`; `cases.review_state` in the [SQL design](../sql/001_initial_design.sql).

**E13-S02 Obligation engine with engagement-checklist templates** — Phase P4 · Priority Must · Trace: PL-036, PL-010, PL-035
- *Story.* As the Reviewing accountant, I want the list of documents each client owes each period derived from the firm's engagements, not guessed.
- *Acceptance criteria.*
  1. Obligations per client-period come from engagement-checklist templates approved by the Plumb domain expert, the agent-generated mapping and the firm's conventions.
  2. Obligation checks are deterministic code outside model text (PL-036).
  3. A client with no matching template raises a focused question; nothing defaults to "nothing owed".
- *Starting point.* `DeterministicRule` in [workflow.py](../plumb/contracts/workflow.py).

**E13-S03 Preparation workflow template without training** — Phase P4 · Priority Must · Trace: PL-035, PL-014, PL-032
- *Story.* System story: the registry template the agent fills for M3-lite has no dataset, training or reminder-canary steps (D3: no training.submit for 180 days).
- *Acceptance criteria.*
  1. The workflow compile step depends only on collection outputs, templates and conventions; no `training.submit` step exists in the template.
  2. The P4 release steps are release.create and release.activate_shadow only (the Prepare canary and promotion to ACTIVE are added in P6, E16-S07); no EXTERNAL_COMMUNICATION effect class appears anywhere in the production template.
  3. The filled plan passes `check_plan` against tenant 1's envelope and inventory.
- *Starting point.* The accounting plan fixture's 22 steps (gap 13 in the [MVP scope](03-mvp-scope.md)).

**E13-S04 Compile the preparation-only WorkflowSpec** — Phase P4 · Priority Must · Trace: PL-035, PL-036, PL-016, PL-003
- *Story.* System story: the agent compiles a WorkflowSpec declaring case identity, triggers, typed inputs, states, transitions, allowed operations, iteration, time and cost bounds, durable waits, human decision points and completion conditions, with read-only preparation separated from external effects.
- *Acceptance criteria.*
  1. Production variant: resolve client and period, reconcile evidence, consolidate missing items, validate received documents, prepare the package, await sign-off. Requests are prepared, never dispatched.
  2. The sandbox variant adds check request authority, send through the sandbox mail adapter and a durable wait, for PA-002.
  3. Produced by the BUILD_AGENT (`workflow.compile`); any person's authoring or edit, Plumb or firm staff, is ENGINEERING_INTERVENTION. DOMAIN_CLARIFICATION per workflow is measured against the budget (P4 exit; experiment 4).
  4. workflow.compile is an INTERNAL_WRITE step with a SANDBOX_TESTED floor, so its capability earns a sandbox receipt and a verifier attestation (E02-S03) before the tenant plan can pass `check_plan`.
- *Starting point.* `WorkflowSpec`, `HumanDecisionPoint`, `DurableWait`.

**E13-S05 General-model extraction through the gateway, pinned per case** — Phase P4 · Priority Must · Trace: PL-034, PL-036, PL-031, ADR-008
- *Story.* System story: document extraction and classification use an approved general model through the gateway, with the model version pinned per case and every output validated before use; no training.
- *Acceptance criteria.*
  1. The model alias resolves to an immutable version per case; `check_release` reports no MODEL_ALIAS_UNRESOLVED.
  2. A harness-forced model assertion that contradicts source authority is rejected by the deterministic validate step (the PA-003 step).
  3. The choice of deterministic checks plus a general model, and not training, is recorded with its cost and review-time rationale (PL-031, applied without the learning factory).
- *Starting point.* `is_immutable_model_version` ([release.py](../plumb/contracts/release.py) line 116).

**E13-S06 PA-002 as written in sandbox** — Phase P4 · Priority Must · Trace: PL-001, PL-016, PL-035, PL-042, PL-043, PL-061, PA-002
- *Story.* As the Reviewing accountant, I want one complete accounting case proven end to end in a sandbox, stopping at my sign-off, before anything runs on real cases.
- *Acceptance criteria.*
  1. P4 exit: PA-002 passes as written on sandbox copies of the sources: one consolidated request listing exactly the two missing documents and referencing the earlier request, sent once through the sandbox mail adapter with a stored provider request id; the durable wait resumes without a worker restart; "ready for review" before sign-off and "complete" after; no accounting write; a BUSINESS_OUTCOME attestation from a VERIFIER principal; a replayed trigger sends nothing.
  2. Production results are never reported as PA-002; production shadow is measured against PA-P02, the proposed preparation-mode variant of PA-002 (shadow start in P4, full close in P5).
- *Starting point.* PA-002 in the [catalog](../acceptance/production_acceptance_catalog.yaml) line 185.

**E13-S07 Stale-input recomputation** — Phase P4 · Priority Must · Trace: PL-036, PL-037, PL-040, PA-006
- *Story.* As the Reviewing accountant, I want a package rebuilt when a corrected document arrives, and my earlier sign-off not carried over to the new version.
- *Acceptance criteria.*
  1. The runtime owns a case state version; a source change after preparation that adds items recomputes the package and sends it for review; a change that only removes items recomputes automatically (D6).
  2. P4 exit: PA-006 passes in sandbox: the prepared version-7 action is refused with STATE_CONFLICT, the item list is recomputed, and the approval bound to the old digest does not carry over.
- *Starting point.* `expected_state_version` on `ActionIntent` ([effect.py](../plumb/contracts/effect.py) line 108); case versions in the SQL `cases` table.

**E13-S08 Attested packages in a full live close (first measurable deliverable)** — Phase P5 · Priority Must · Trace: PL-001, PL-042, PL-059, PL-063
- *Story.* As the Firm owner, I want verifier-attested ready-for-review packages for at least 30 of my client-periods in one real close, compared with my accountants' actual work, so that the move from shadow to the Prepare canary, and later paid conversion, rests on evidence (founder decision 17).
- *Acceptance criteria.*
  1. Every package shown as ready carries an attestation covering its digest; a package without one never reads READY_FOR_REVIEW.
  2. P5 exit for tenant 1: attested packages on at least 30 client-periods across at least one full close; correct-package rate against the domain expert's threshold, exclusions in the denominator; accountant minutes against the month-0 baseline (E14-S06); false-chase and recall reported (E11-S08).
  3. Zero external sends during shadow (effect ledger shows no DISPATCHED effects).
  4. Tenants 2 and 3 shadows are started; their full-close readings may land after day 180 and are reported as pending.
- *Starting point.* None.

### E14 Review surface and prospective correction collector

**Goal.** The Reviewing accountant reviews each package and explicitly accepts, corrects or amends it; the surface measures review minutes against a month-0 baseline and doubles as the prospective correction collector, keeping the ADR-006 option open cheaply (PL-026, PL-027, PL-040, PL-059).
**Why now.** The co-headline (accepted review packages per month) and the time-saving claim both need explicit acceptance and a baseline (D2, D10). Nothing captures accountant assembly time before deployment today (D2).
**Package has.** `ApprovalRecord` with `decision_kind` CASE_LEVEL_BUSINESS, which requires `case_version` ([approval.py](../plumb/contracts/approval.py) lines 64-100); `LabelKind.CORRECTION` and `LabelKind.EXPERT_DECISION` ([common.py](../plumb/contracts/common.py) lines 314-321); SQL `cases.review_state`. No review queue or surface.

**E14-S01 Month-0 baseline time study** — Phase P1 · Priority Must · Trace: PL-059, PL-012, PL-003
- *Story.* As the Firm owner, I want my accountants' current assembly and review minutes measured before shadow starts, so that any time-saving claim can be checked against my own firm.
- *Acceptance criteria.*
  1. A 2-week protocol, run by the partner with the Plumb domain expert, records assembly-plus-review minutes per client-period with its denominator.
  2. M0 exit: captured or scheduled for tenant 1; partner studies for tenants 2 and 3 scheduled to finish before mid-January.
  3. The study's recording overhead is logged as DOMAIN_CLARIFICATION (rubric v1, E01-S01).
- *Starting point.* None.

**E14-S02 Package review view** — Phase P4 · Priority Must · Trace: PL-001, PL-010, PL-035, PA-002
- *Story.* As the Reviewing accountant, I want each package to open with its verdict, attestation, items, evidence links and versions in one place.
- *Acceptance criteria.*
  1. Header: client, period, readiness verdict, attestation badge with receipt, prepared-at time, source freshness, versions; items with presence, fact status, evidence and extracted values; open dependencies; version history; in shadow, the "what Plumb would have done" panel.
  2. Reads "Ready for review" until sign-off and "Signed off" after; never "closed" or "close complete".
  3. No accounting write occurs: the envelope and plan contain no FINANCIAL_COMMITMENT effect class.
- *Starting point.* None.

**E14-S03 Explicit accept, correct and amend, with a bound sign-off** — Phase P4 · Priority Must · Trace: PL-027, PL-040, PL-001, PA-002, PA-010
- *Story.* As the Reviewing accountant, I want to accept, correct or amend each item and sign off the package, and have my sign-off apply only to the version I saw.
- *Acceptance criteria.*
  1. Only an explicit decision counts as acceptance; a package with no decision is never counted as accepted (spec App. B; PL-027).
  2. Sign-off creates an ApprovalRecord with decision kind CASE_LEVEL_BUSINESS bound to the package digest, case version, policy version and expiry, through IdP step-up; an agent-produced sign-off is rejected (APPROVAL_AGENT_SUPPLIED).
  3. A correction creates a new package version that supersedes the old one; an amendment after sign-off links to the signed version.
  4. Active review minutes are recorded as NORMAL_BUSINESS_REVIEW.
- *Starting point.* `ApprovalRecord`, `check_approval`.

**E14-S04 Material-correction rubric** — Phase P4 · Priority Must · Trace: PL-059, PL-043
- *Story.* As the Plumb domain expert, I want one written definition of a material correction, so that "accepted without material correction" means the same at every firm.
- *Acceptance criteria.*
  1. Initial definition for ratification: a change of client or period attribution, adding or removing an obligation item, or changing an item's presence. Wording edits are not material.
  2. Each correction is tagged material or not; the rubric is versioned.
  3. A double-coded sample measures reviewer disagreement; above 20% triggers the D10 revisit (threshold is a hypothesis).
  4. P4 exit: the numeric correct-package threshold is set alongside the rubric.
- *Starting point.* None.

**E14-S05 Prospective correction collector** — Phase P4 · Priority Should · Trace: PL-026, PL-027, PL-053, ADR-006
- *Story.* System story: each prepared item stores its input snapshot and case id, and the Reviewing accountant's decision is stored as a label under the same case id, so future learning data accumulates from normal work.
- *Acceptance criteria.*
  1. Labels use LabelKind CORRECTION or EXPERT_DECISION with the reviewed outcome; absence of an edit never creates a label.
  2. Labels are stored only for sources with EVALUATE granted and are never used for training in v1 (TRAIN absent).
  3. The count of explicit accept and correct events is reported toward the M2 gate (at least 500, D5).
- *Starting point.* `LabelKind`, `LabelStatus`.

**E14-S06 Review timing against the baseline** — Phase P4 · Priority Must · Trace: PL-059, PL-003
- *Story.* As the Firm owner, I want review minutes per package measured automatically and compared with the month-0 baseline.
- *Acceptance criteria.*
  1. Active review time per package is captured without manual logging; the idle exclusion rule is a threshold-sheet hypothesis.
  2. The results view reports accountant assembly-plus-review minutes per client-period against the baseline, with the denominator.
  3. D2 revisit check: a fall of less than 25% in the first two shadow closes, or packages opened for less than 50% of in-scope client-periods, is flagged (hypotheses).
- *Starting point.* None.

**E14-S07 Batched review sessions** — Phase P5 · Priority Should · Trace: PL-041, PL-059
- *Story.* As the Reviewing accountant, I want review requests batched into at most one session a day, so that review does not fragment my day (D6 hypothesis).
- *Acceptance criteria.*
  1. Notifications are batched per reviewer per day, except a block that threatens a close deadline, which is raised at once and counted.
  2. Reviewer interruptions per tenant-week are reported in the interruption-load metric.
- *Starting point.* None.

### E15 Approvals model and policy-level approvals

**Goal.** Each of the three spec §17 decisions (DATA_USE, IMPLEMENT_OPERATE, CASE_LEVEL_BUSINESS) is asked once, by the right person, bound to exact bytes and versions, batched within an interruption budget; policy-level reminder approval comes later with materiality triggers (PL-040, PL-041; D6).
**Why now.** The envelope signature in P1 and the implementation card in P2 need an authenticated place to decide. Approvals are worthless without verified identity.
**Package has.** `check_approval` with 11 codes, including APPROVAL_NOT_HUMAN, APPROVAL_AGENT_SUPPLIED, APPROVAL_DIGEST_MISMATCH, APPROVAL_POLICY_STALE, APPROVAL_EXPIRED and APPROVAL_REVOKED ([approval_checker.py](../plumb/checker/approval_checker.py) line 62); `DecisionKind` with the three kinds; `AuthorizationRequest` and `group_missing_authorizations`, one request per resolver role and error class (lines 196-237). `ApprovalRecord` carries `subject_digest`, `case_version`, `policy_version`, `authenticated_decision_ref`, `expires_at`, `revoked_at`. `resolveBuildDependency` is the only API path that yields an ApprovalRecord ([openapi.yaml](../api/openapi.yaml) line 398). No inbox, no step-up.

**E15-S01 Approvals inbox for DATA_USE and IMPLEMENT_OPERATE** — Phase P2 · Priority Must · Trace: PL-040, PL-041, PL-053
- *Story.* As the Firm owner, I want one inbox that tells me which kind of decision is being asked, what changes, why, what is blocked and when it expires, so that I never face a vague "Allow AI" button.
- *Acceptance criteria.*
  1. Every request shows the decision type and owner, what will change, why, the missing authority, the blocked work, an impact diff, the actual test evidence, the expiry, and approve and decline.
  2. DATA_USE is asked once per source and purpose; IMPLEMENT_OPERATE once per intervention version and again only at an envelope boundary (E04-S05).
  3. The Firm owner is never asked to re-approve authority that is still valid (PL-041).
- *Starting point.* `DecisionKind`; MVP surface spec in the [MVP scope](03-mvp-scope.md) section 4.6.

**E15-S02 Authorization requests as a first-class resource** — Phase P1 · Priority Should · Trace: PL-041, PL-001, PL-017
- *Story.* System story: the grouped output of `group_missing_authorizations` becomes a persisted resource with endpoints, so related missing authorizations reach the owner as one concrete request.
- *Acceptance criteria.*
  1. `listAuthorizationRequests`, `getAuthorizationRequest` and `decideAuthorizationRequest` exist; requests are grouped per resolver role and error class.
  2. Granting a request resolves every grouped dependency and resumes its blocked steps; completed work is kept while waiting.
  3. Authority already granted never appears in a request; `first_raised_at` is preserved.
- *Starting point.* `AuthorizationRequest`, `group_missing_authorizations` ([approval_checker.py](../plumb/checker/approval_checker.py) lines 196-237).

**E15-S03 Approval capture with step-up and binding** — Phase P1 · Priority Must · Trace: PL-040, PL-004, PA-010
- *Story.* System story: an ApprovalRecord is minted only by the approvals service from an authenticated human decision, and `check_approval` runs on every use.
- *Acceptance criteria.*
  1. Each decision goes through an IdP step-up that produces `authenticated_decision_ref`; an approval-shaped record from a build or runtime agent is rejected (APPROVAL_AGENT_SUPPLIED).
  2. APPROVAL_DIGEST_MISMATCH, APPROVAL_POLICY_STALE, APPROVAL_EXPIRED, APPROVAL_REVOKED and APPROVAL_TENANT_MISMATCH block use and surface as blocked-dependency reasons.
  3. Tenant 1's envelope and DPA-linked grants are signed through this path (P1 exit). PA-010 is attested in the P4 sandbox.
- *Starting point.* `ApprovalRecord`, `check_approval`.

**E15-S04 Revocation and expiry propagation** — Phase P4 · Priority Must · Trace: PL-040, PL-041, PL-053, PA-008, PA-010
- *Story.* As the Firm owner, I want a revoked or expired permission to stop future work promptly, with one precise renewal request.
- *Acceptance criteria.*
  1. P4 exit: PA-008 passes in sandbox: within the health deadline the collector is PAUSED or DEGRADED ("grant expired"); dispatch returns SCOPE_DENIED or POLICY_STALE with no provider call; cached grants and queued work are invalidated within one minute; the DependencyRecord carries MISSING_AUTHORIZATION, the exact source and purposes, resolver HUMAN_OWNER, blocked steps and resumes_after; after renewal, collection resumes from its cursor without re-backfill.
  2. P4 exit: PA-010 passes in sandbox, including revocation of a queued action before provider invocation and asking once for the changed bytes only.
- *Starting point.* `expires_at` and `revoked_at` on grants, approvals and envelopes.

**E15-S05 Interruption-budget metering** — Phase P2 · Priority Should · Trace: PL-041, PL-003, PL-059
- *Story.* As the Firm owner, I want Plumb to hold itself to a budget for how often it interrupts me, and treat overruns as its own defects.
- *Acceptance criteria.*
  1. Owner and reviewer decision minutes per tenant-week by decision type; DOMAIN_CLARIFICATION questions per workflow; repeat-ask rate (target 0); share of requests needing per-case approval.
  2. Budget (hypotheses, D6): onboarding at most 2 hours of CUSTOMER_AUTHORIZATION and at most 4 owner-hours in the first 30 days; steady state at most 1 batched owner request per tenant-week and at most 30 minutes of owner decision time a week.
  3. The budget counts unscheduled asks; scheduled time, such as the weekly check-in, is reported beside it as DOMAIN_CLARIFICATION, never inside it (founder decision 18).
  4. An overrun opens a defect automatically. P5 exit: owner decision time within budget and repeat asks 0. The R3 trigger values are in [risks and assumptions](07-risks-and-assumptions.md).
- *Starting point.* None.

**E15-S06 Policy-level reminder approval with materiality triggers** — Phase P6 · Priority Could · Trace: PL-040, PL-041, PL-037, PA-006, PA-010, PA-011
- *Story.* As the Firm owner, I want to approve a reminder policy once and be asked case by case only when something material is different.
- *Acceptance criteria.*
  1. The policy covers template class, at most one consolidated request per client-period-obligation epoch, a follow-up cap, quiet hours and recipient of record; a standing supersession policy covers wording-only edits within a template class; a template-class change bumps the policy version and needs one re-approval. Approving or re-approving the policy is logged as CUSTOMER_AUTHORIZATION.
  2. Each D6 materiality trigger (an item with Presence UNKNOWN, or with fact status STALE, DISPUTED or INFERRED below threshold, a new or off-record recipient, out-of-template content or amounts or tax identifiers, first-ever request to a client, third or later request in an epoch, after a complaint, sensitive client, cadence cap exceeded, items added after preparation) has a test forcing a CASE_LEVEL_BUSINESS approval.
  3. A stale source blocks instead of asking (PA-011). PA-006 and PA-010 pass against draft creation (Draft gate, D4), and PA-P03, the proposed policy-level variant of PA-010, passes before any policy-level Send (earliest canary close around July 2027).
- *Starting point.* `check_approval`; `policy_version` on approvals.

**E15-S07 Calibration ladder from Draft to Send** — Phase P6 · Priority Could · Trace: PL-040, PL-059
- *Story.* As the Firm owner, I want a client and obligation type to move to policy-level sending only after my staff have approved its drafts unchanged for long enough.
- *Acceptance criteria.*
  1. Graduation per client and obligation type after at least 2 closes and at least 20 drafts, with approve-without-edit of at least 95% and material edits below 2% (hypotheses, D6).
  2. A breach reverts that type to per-case approval; graduation decisions are logged with their evidence.
- *Starting point.* None.

### E16 Release executor, shadow, pause and kill

**Goal.** A narrow release executor on fixed approved templates, qualified on a Plumb-owned production tenant, takes the preparation workflow into production shadow; pause and kill work from SHADOW and CANARY; every release carries an operating plan (PL-045, PL-046, PL-047, PL-048).
**Why now.** release.activate_shadow has a PRODUCTION_VERIFIED floor, so shadow cannot start without a qualified executor (D3 correction). Today a shadow or canary release cannot be paused.
**Package has.** `ReleaseManifest` with 9 component slots, rollout SHADOW then CANARY then ACTIVE, canary fraction strictly between 0 and 1, in-flight pinning and a human rollback owner ([release.py](../plumb/contracts/release.py) line 210); `OperatingPlan` requiring all 7 monitors (lines 145-168); `InfrastructurePlan` ([infrastructure.py](../plumb/contracts/infrastructure.py) line 86); `check_release`. The RELEASE machine allows PAUSED only from ACTIVE; SHADOW can move only to CANARY or RETIRED, and CANARY only to ACTIVE, ROLLED_BACK or RETIRED ([machines.py](../plumb/statemachines/machines.py) lines 398-421), while `pauseRelease` promises to block new effects immediately ([openapi.yaml](../api/openapi.yaml) line 801). No `getRelease`, `listReleases`, rollback or retire operation. No executor.

**E16-S01 Narrow release executor and tenant 1 production shadow** — Phase P4 · Priority Must · Trace: PL-045, PL-046, PL-047, PL-035
- *Story.* System story: a release executor with a short-lived grant applies only fixed, approved templates, and takes tenant 1's preparation workflow into production shadow.
- *Acceptance criteria.*
  1. Infrastructure comes only from approved templates with preview, cost estimate, state lock, ownership tags and rollback classification; an apply without a preview reports PRECONDITION_MISSING.
  2. The ReleaseManifest binds workflow, connector, collector, model, prompt, policy, schema, infrastructure and evaluation versions by digest; the builder cannot replace a verified artifact under the same identifier.
  3. P4 exit: production shadow is active on tenant 1 with no EXTERNAL_COMMUNICATION in the envelope.
- *Starting point.* `ReleaseManifest`, `InfrastructurePlan`, `check_release`.

**E16-S02 Platform qualification run for release.create and release.activate_shadow** — Phase P4 · Priority Must · Trace: PL-008, PL-046, PL-042
- *Story.* Internal story (owner: Tech lead): before any tenant shadow, the executor runs on a Plumb-owned production tenant and earns real PRODUCTION_VERIFIED receipts with a verifier attestation.
- *Acceptance criteria.*
  1. Receipts and the attestation exist for release.create and release.activate_shadow; maturity is raised only through E02-S03.
  2. A tenant shadow plan passes the PRODUCTION_VERIFIED floor only after this run.
  3. infrastructure.apply also has a PRODUCTION_VERIFIED floor, and the accounting fixture's release.create depends on an infrastructure.apply step. Either the P4 template provisions no per-tenant infrastructure (serving runs on platform infrastructure recorded as platform investment), which keeps the Prepare envelope to READ, INTERNAL_WRITE and EXTERNAL_WRITE_REVERSIBLE (E04-S01), or infrastructure.apply is qualified in the same run, which also adds INFRASTRUCTURE_CHANGE to the envelope. The Founder records the choice before P4 starts.
- *Starting point.* `cap.release.create.executor` and `cap.release.activate_shadow.executor` records (synthetic today).

**E16-S03 Pause and kill from SHADOW and CANARY** — Phase P4 · Priority Must · Trace: PL-047, PL-057, PL-043
- *Story.* As the Firm owner, I want to pause or stop a release at any stage, including shadow and canary, and keep seeing what it did.
- *Acceptance criteria.*
  1. RELEASE gains SHADOW→PAUSED, CANARY→PAUSED and SHADOW→ROLLED_BACK, plus resume edges from PAUSED back to the paused stage; resuming into ACTIVE still requires `authority_current` and `attestations_accepted`.
  2. `pauseRelease` from SHADOW and from CANARY returns 200 with state PAUSED; a paused release takes no new cases and produces no new effects (the gateway check is E17-S02), while visibility and recovery remain.
  3. P5 exit: pause and kill from SHADOW and CANARY pass the gateway sandbox crash tests.
- *Starting point.* The RELEASE transition table ([machines.py](../plumb/statemachines/machines.py) lines 398-421).

**E16-S04 Release read and lifecycle operations** — Phase P4 · Priority Should · Trace: PL-047, PL-055, PL-056
- *Story.* As a Plumb engineer/operator, I want to read, roll back and retire releases through the API.
- *Acceptance criteria.*
  1. `getRelease`, `listReleases`, `rollbackRelease` and `retireRelease` exist; ROLLED_BACK and RETIRED are reachable through the API.
  2. State changes take If-Match (412 when stale) and Idempotency-Key.
- *Starting point.* `createRelease`, `activateRelease`, `pauseRelease`.

**E16-S05 Operating plan bound to every release** — Phase P4 · Priority Must · Trace: PL-048, PL-043
- *Story.* System story: no release activates without monitors for connector freshness, schema change, execution failure, quality drift, review burden, cost and outcome, a human rollback owner and a review capacity per day.
- *Acceptance criteria.*
  1. `check_release` reports no OPERATING_PLAN_MISSING for the tenant 1 shadow release.
  2. The REVIEW_BURDEN monitor uses `review_capacity_per_day`; the rollback owner is the Firm owner or a person they name, never a staff or agent principal.
  3. Monitors are live during shadow (E22-S01).
- *Starting point.* `OperatingPlan`, `MonitorKind`.

**E16-S06 Version resolution and in-flight pinning** — Phase P4 · Priority Should · Trace: PL-047, PL-034, ADR-008
- *Story.* System story: new cases use the resolved release version; cases in flight stay on their release and model version unless a validated migration moves them.
- *Acceptance criteria.*
  1. A case started on release N completes on N after N+1 activates.
  2. A migration requires a validated migration plan.
- *Starting point.* `in_flight_pinning` on `ReleaseManifest`.

**E16-S07 Prepare-tier promotion: SHADOW, CANARY, ACTIVE (founder decision 17, to ratify)** — Phase P6 · Priority Must · Trace: PL-047, PL-008
- *Story.* As the Firm owner, I want Plumb's package to become the working package of record, first for a bounded share of my client-periods and then for all in scope, still with nothing sent, once shadow results justify it.
- *Acceptance criteria.*
  1. The path is SHADOW for at least one full close, then CANARY on a subset of client-periods whose accountants use the prepared packages in their real review, then ACTIVE, with no EXTERNAL_COMMUNICATION at any stage ([MVP scope](03-mvp-scope.md) open question 1; founder decision 17 in the [decision record](02-strategy-decisions.md)).
  2. Canary fraction strictly between 0 and 1; ACTIVE only from CANARY with `authority_current` and `attestations_accepted`.
  3. release.canary is qualified at PRODUCTION_VERIFIED for this preparation-only use, and a registry step type for promotion to ACTIVE is added and qualified (the registry has release.create, release.activate_shadow and release.canary only).
  4. Conversion rule: a partner converts to paid annual after one full close in ACTIVE at or above the correct-package threshold (D7, D9). The day-180 packet records tenant 1's evidence to date; tenant 1's conversion is expected in P6, and it feeds the P6 exit evidence (2 of the first 4 partners on paid annual).
- *Starting point.* `RolloutStage` validators in [release.py](../plumb/contracts/release.py).

**E16-S08 Canary release for the Send tier** — Phase P6 · Priority Could · Trace: PL-047, PL-061, PA-007
- *Story.* System story: the Send canary runs on at most 20% of client-periods for at least one close, beside an ACTIVE release (decision record, P6). Its earliest close is around July 2027 (about weeks 39-41), after two Draft closes (E15-S07).
- *Acceptance criteria.*
  1. release.canary for sending has PRODUCTION_VERIFIED receipts and the CASE_LEVEL_BUSINESS authority its capability requires (E05-S02).
  2. Concurrent ACTIVE and CANARY releases exist, which PA-007 needs (E17-S07).
- *Starting point.* `cap.release.canary.executor`.

### E17 Production action gateway and effect ledger

**Goal.** A production gateway with a transactional outbox, leases and dispatch-time authority, revocation and pause checks, hardened in sandbox in P5 and released for the Draft tier in P6 and then the Send canary, whose earliest close is around July 2027 (PL-037, PL-038, PL-039; ADR-009).
**Why now.** External effects wait for a real gateway (D3): the effect ledger is a SQLite simulation and a canary cannot be paused. P5 hardens it in sandbox so that the day-180 packet can decide Draft and Send on evidence.
**Package has.** [effect_ledger.py](../plumb/ledger/effect_ledger.py), a single-process SQLite simulation: `reserve` (line 389) persists the intent keyed on the effect slot with PayloadConflict, TargetConflict and EffectUnknown; `mark_dispatched` records the lease first; `confirm`, `fail_final`, `reconcile`, `compensate`; `outstanding()` (line 670). On the idempotent path it only reports `authority_matches` (line 430); it never validates authority or checks release pause or envelope revocation. `ActionIntent` carries the slot, payload digest, expected state version, authority reference and deployment version ([effect.py](../plumb/contracts/effect.py) line 101). SQL `effects`, `effect_transitions` and `outbox` mirror it. `dispatchAction` and `reconcileAction` are proposed; no `getAction`.

**E17-S01 PostgreSQL effect ledger with a transactional outbox** — Phase P5 · Priority Must · Trace: PL-037, PL-039, PL-057
- *Story.* System story: the effect ledger runs on PostgreSQL with intent and dispatch work written atomically through an outbox.
- *Acceptance criteria.*
  1. The behaviors covered by [test_effect_ledger.py](../tests/test_effect_ledger.py) pass against the PostgreSQL implementation.
  2. Slot deduplication survives worker restarts and release changes; the idempotency key derives from the action identity, never the payload.
- *Starting point.* `EffectLedger`; SQL `effects`, `effect_transitions`, `outbox`.

**E17-S02 Dispatch-time authority, revocation, pause and state checks** — Phase P5 · Priority Must · Trace: PL-037, PL-040, PL-047, PL-053, PL-006, PA-005
- *Story.* As the Firm owner, I want every action re-checked at the moment of dispatch, so that nothing goes out after I revoke, pause, or the facts change.
- *Acceptance criteria.*
  1. Before reserve and again before dispatch, the gateway checks: the ApprovalRecord is valid for the payload digest (`check_approval`); the envelope is active and not revoked; the source grants are current; the release is not PAUSED, ROLLED_BACK or RETIRED; the case state version equals `expected_state_version`; the obligation is still unsatisfied. Any failure means no provider call.
  2. P5 exit: PA-005's dispatch-time re-check passes in sandbox: when the document arrived before the scheduled request, nothing is sent and the slot is released or FAILED_FINAL, never DISPATCHED.
  3. A revoked approval cancels a queued dispatch before provider invocation; the gateway fails closed for writes (spec §24).
- *Starting point.* `reserve`, `authority_matches` and `state_version_matches` in [effect_ledger.py](../plumb/ledger/effect_ledger.py).

**E17-S03 Distributed leases, fencing and outstanding actions** — Phase P5 · Priority Must · Trace: PL-038, PL-057, PL-017, PA-015
- *Story.* System story: the dispatcher records its lease before the provider call, and a replacement worker reconciles outstanding effects before new work.
- *Acceptance criteria.*
  1. P5 exit: PA-015's lease-and-fencing checks are re-run in sandbox on gateway dispatch workers for draft creation and sends, reported as a mechanism re-run, not a second PA-015 pass: a frozen worker's late commit with a stale token is rejected; the replacement lists outstanding DISPATCHED and UNKNOWN effects first.
  2. `getAction` and `listOutstandingActions` exist.
- *Starting point.* `mark_dispatched`, `outstanding()`.

**E17-S04 UNKNOWN reconciliation by provider request id** — Phase P5 · Priority Must · Trace: PL-038, PL-039, PL-057, PA-009
- *Story.* As the Firm's client, I want never to receive the same request twice because a server timed out.
- *Acceptance criteria.*
  1. The mail adapter stores provider request ids and supports message lookup (a D1 qualification constraint).
  2. P5 exit: PA-009 passes as written (sends) against the sandbox gateway, and the same check on draft creation is recorded as Draft-gate crash-test evidence, not as a PA-009 result: DISPATCHED→UNKNOWN on a post-acceptance timeout; after a kill and restart, lookup reconciles to CONFIRMED with exactly one message; "no such request" leads to FAILED_FINAL and a new attempt of the same action id and slot.
- *Starting point.* `mark_unknown`, `reconcile` in [effect_ledger.py](../plumb/ledger/effect_ledger.py).

**E17-S05 Draft tier: consolidated request drafts in the firm's mailbox** — Phase P6 · Priority Could · Trace: PL-037, PL-039, PL-040, PL-047, PA-005, PA-006, PA-009, PA-010, PA-015
- *Story.* As a Bookkeeper, I want Plumb to place one consolidated request per client in my mailbox as a draft that I review and send.
- *Acceptance criteria.*
  1. Draft creation is an EXTERNAL_WRITE_REVERSIBLE effect with SANDBOX_TESTED maturity and effect-slot deduplication.
  2. Draft release gate (D4): PA-005's dispatch-time re-check, PA-009 and PA-015 behaviors, PA-006 and PA-010 approval binding, and pause and kill from CANARY, all against draft creation.
  3. Draft canary runs for at least one close; staff edits are recorded for the calibration ladder (E15-S07).
- *Starting point.* None.

**E17-S06 Send tier: policy-approved Send canary** — Phase P6 · Priority Could · Trace: PL-037, PL-038, PL-039, PL-061, PA-002, PA-005, PA-007, PA-009, PA-010
- *Story.* As the Firm owner, I want approved request types sent under my policy, one per client-period-obligation epoch, with one owner across staff.
- *Acceptance criteria.*
  1. Not before the D6 ladder has graduated a type (E15-S07), so the earliest Send canary close is around July 2027. Send release gate (D4): full PA-002 in canary; PA-005; PA-007; PA-009; PA-010; accounting adaptations of PA-014's revocation race (PA-P05, E17-S08) and PA-016's schema-drift repair (PA-P06, E22-S04); a recovery drill (E22-S05); recorded support effort. Together with the canary report these form PA-P04, the proposed M4-accounting evidence.
  2. P6 exit: a canary report with denominators and effect receipts; zero duplicate, stale or wrong-client requests reached real clients.
  3. R4 rules: one real-client duplicate, stale or wrong-client request halts sends and reverts to Draft; two within 90 days remove Send for two quarters.
- *Starting point.* None.

**E17-S07 One obligation, one owner across staff and workflows** — Phase P6 · Priority Could · Trace: PL-039, PL-037, PA-007
- *Story.* As a Bookkeeper, I want my task list to show one shared obligation and its single owner, so that two of us never chase the same client for the same item.
- *Acceptance criteria.*
  1. PA-007 passes: two triggers within one second from ACTIVE and CANARY releases yield one action owner and one provider request, including when the second worker crashes between reserve and dispatch.
  2. Both Bookkeepers see the single shared obligation.
- *Starting point.* `EffectSlot` (tenant, case, obligation, epoch, operation, target) in [effect.py](../plumb/contracts/effect.py) line 60.

**E17-S08 Revocation race handled truthfully** — Phase P6 · Priority Could · Trace: PL-038, PL-040, PL-041
- *Story.* As the Firm owner, I want to be told plainly when a message was accepted by the provider before my revocation landed, and offered a remediation.
- *Acceptance criteria.*
  1. PA-P05, the accounting adaptation of PA-014 (not claimed as PA-014): the ledger orders acceptance before revocation, ends CONFIRMED with the receipt, and creates a remediation obligation under a new approved epoch.
  2. The product never claims a message was not sent after the provider accepted it (D8 item 11); follow-ups are blocked until new authority exists.
- *Starting point.* `compensate` requires CONFIRMED and keeps the original receipt.

### E18 Data rights and purpose grants, including SERVE and TRAIN

**Goal.** Purpose grants per source are captured in the DPA and envelope, enforced at plan time and at run time, SERVE is explicit before the first shadow, TRAIN is opt-in and off by default, and tax-return information is excluded (PL-053, PL-005; D9).
**Why now.** Tenant 1's DPA and envelope are P1 exit evidence. The package never enforces SERVE, so the contract and the checker must settle it before shadow (founder decision default).
**Package has.** `SourceGrant` purposes; `purposes_for` never infers TRAIN or EXPORT from read purposes ([envelope.py](../plumb/contracts/envelope.py) line 234); purpose inheritance along data lineage with PURPOSE_DENIED ([plan_checker.py](../plumb/checker/plan_checker.py) `_check_purposes`, line 872); DISALLOWED_SOURCE_USE in the dataset checker. Gap: a step that touches no source is checked only for TRAIN and EXPORT (lines 888-909), and the release.activate_shadow and release.canary steps have no declared or inherited sources, so the SERVE purpose that `cap.release.activate_shadow.executor` and `cap.release.canary.executor` require is never matched against a grant; no fixture envelope grants SERVE, yet every fixture plan passes ([README](../README.md) line 164).

**E18-S01 Purpose grants in the DPA and envelope** — Phase P1 · Priority Must · Trace: PL-053, PL-005
- *Story.* As the Firm owner, I want to grant each source only the uses I agree to, in my contract and in Plumb's configuration alike.
- *Acceptance criteria.*
  1. Per source: INSPECT, COLLECT, TRANSFORM and EVALUATE at onboarding; TRAIN off by default, opt-in per source and tenant-only; SERVE explicit before the first shadow; no price discount for training rights (D7).
  2. Envelope grants match the DPA schedule; each names the granting human, policy version and expiry; no tenant-wide checkbox (spec §21).
  3. P1 exit: tenant 1's DPA and envelope are signed.
- *Starting point.* `SourceGrant`, `DataPurpose`.

**E18-S02 Tax-return exclusion** — Phase P1 · Priority Must · Trace: PL-053, PL-023
- *Story.* As the Firm owner, I want tax-return information kept out of Plumb entirely, so that the firm does not take on IRC 7216 obligations by accident (counsel to confirm, D9).
- *Acceptance criteria.*
  1. Folder and label exclusions are declared on the source grant (proposed field); access to an excluded path is refused and logged.
  2. Any package item traced to an excluded source makes the package invalid (E13-S01 validator).
  3. A counsel opinion is obtained before the first signature; the firm's warranty is in the contract.
- *Starting point.* `ResourceScope` scopes by source, destination, processor and region only ([common.py](../plumb/contracts/common.py) line 512); exclusions inside a source are new.

**E18-S03 Purpose enforcement at run time** — Phase P2 · Priority Must · Trace: PL-053, PL-023
- *Story.* System story: purposes are enforced when data is collected, transformed, evaluated and exported, not only at plan check, and derived data inherits its sources' restrictions.
- *Acceptance criteria.*
  1. A collector refuses a source or field without COLLECT (PURPOSE_DENIED); evaluation data from a source without EVALUATE is rejected.
  2. Derived artifacts carry their source lineage, and their permitted purposes are the intersection of their sources' grants.
  3. Evidence granted COLLECT only cannot be exported (PA-026 expectation).
- *Starting point.* `_check_purposes` lineage logic; dataset checker `DISALLOWED_SOURCE_USE`.

**E18-S04 SERVE enforced before the first shadow** — Phase P4 · Priority Must · Trace: PL-053, PL-046, PL-015
- *Story.* As the Firm owner, I want Plumb to need my explicit permission before a running workflow serves my data, separate from permission to read it.
- *Acceptance criteria.*
  1. Release steps inherit the sources of the workflow, collector and integration components they bind, through the ReleaseManifest, or declare them explicitly.
  2. Checked against its own envelope (no SERVE grant), the accounting fixture plan reports PURPOSE_DENIED at `activate-shadow-processing` and `canary-consolidated-reminders`; with per-source SERVE grants it passes.
  3. P4 exit: tenant 1's SERVE grant is recorded and enforced before its first shadow.
- *Starting point.* [plan_checker.py](../plumb/checker/plan_checker.py) lines 888-909; registry `required_purposes`.

**E18-S05 Cross-tenant reuse guard** — Phase P3 · Priority Must · Trace: PL-053, PL-052
- *Story.* As the Firm owner, I want my examples, labels and data never used for another firm, while Plumb may reuse engineering patterns stripped of my data (D9 item 2; spec App. A §5).
- *Acceptance criteria.*
  1. Only engineering artifacts (mapping patterns with applicability constraints, adapter tests, failure fixtures) move across tenants, and a scanner confirms they contain no tenant identifiers or content.
  2. Any attempt to reuse examples, labels or weights across tenants is refused.
- *Starting point.* None.

**E18-S06 Vendor-terms version per data-use decision** — Phase P2 · Priority Should · Trace: PL-053
- *Story.* System story: each data-use decision records the vendor-terms version it relied on, and a terms change triggers re-evaluation of the affected operations (spec §21).
- *Acceptance criteria.*
  1. Grants record the vendor-terms version, for example the Google Workspace user-data policy in force.
  2. A terms change lists the affected grants and operations for review.
- *Starting point.* None.

**E18-S07 Data removal: quarantine, retire, stop serving** — Phase P4 · Priority Should · Trace: PL-053, PL-030
- *Story.* As the Firm owner, I want a removal request to find everything derived from the data and quarantine or retire it, with a deletion certificate.
- *Acceptance criteria.*
  1. Lineage identifies affected artifacts; affected datasets become UNAVAILABLE; packages follow the agreed retention terms; a deletion certificate is issued (D9).
  2. No exact-unlearning promise appears anywhere (spec §20; D8 item 10).
- *Starting point.* DATASET machine fan-in to UNAVAILABLE ([machines.py](../plumb/statemachines/machines.py)).

**E18-S08 TRAIN opt-in flow** — Phase Gated (M2) · Priority Could · Trace: PL-053, PL-032
- *Story.* As the Firm owner, I want to opt a specific source into training for my firm only, knowing exactly what it allows.
- *Acceptance criteria.*
  1. TRAIN is granted per source by the Firm owner and never inferred from read purposes (the `purpose_denied_train_from_read` fixture case stays rejected).
  2. The grant appears on the implementation card of any intervention that uses it.
- *Starting point.* [fixtures/invalid/purpose_denied_train_from_read.json](../fixtures/invalid/purpose_denied_train_from_read.json).

### E19 Telemetry and correlation

**Goal.** Operational telemetry correlates tenant, goal, build, case, release, step, model call and external action, contains no sensitive content by default, and is tenant-scoped (PL-060).
**Why now.** PA-019 checks that telemetry carries correlation ids and no content or secrets, and PA-017's log surface is in the M1 subset. PL-060 is covered today only by artifact inspection.
**Package has.** None. The [validation report](../VALIDATION_REPORT.md) lists PL-060 as artifact-inspection only.

**E19-S01 Correlated telemetry pipeline** — Phase P2 · Priority Must · Trace: PL-060, PA-019
- *Story.* As a Plumb engineer/operator, I want one trace from a source event to the package row and any action it caused, so that I can diagnose a case without reading customer content.
- *Acceptance criteria.*
  1. Every span and log line carries tenant, goal, build, case, release, step, model-call and action ids where applicable.
  2. The telemetry conventions version is pinned and recorded, because the OpenTelemetry GenAI conventions are still evolving (spec §24).
  3. A test trace joins a fault-injection event (E10-S03) to the resulting state change.
- *Starting point.* None.

**E19-S02 Content-free by default, with redaction** — Phase P2 · Priority Must · Trace: PL-060, PL-054, PA-019, PA-026
- *Story.* System story: telemetry never carries document content, message bodies or secrets unless a specific, approved diagnostic needs it.
- *Acceptance criteria.*
  1. PA-019's telemetry check passes: correlation ids present, no content and no secrets.
  2. A debug log line containing record content is redacted or dropped and raises a finding (PA-026 path e).
- *Starting point.* Error-text screening in [api.py](../plumb/contracts/api.py) (`ErrorEnvelope`).

**E19-S03 Tenant-scoped logs and operator access** — Phase P2 · Priority Must · Trace: PL-060, PL-052, PA-017
- *Story.* As the Firm owner, I want Plumb's operators to see my firm's logs only when working on my firm, and never another firm's data in mine.
- *Acceptance criteria.*
  1. The PA-017 log check passes in the M1 subset: zero cross-tenant overlap.
  2. Operator log access is scoped per tenant and recorded in the admin audit table.
- *Starting point.* None.

**E19-S04 Service-level measurement** — Phase P4 · Priority Should · Trace: PL-060, PL-059, PL-025
- *Story.* As a Plumb engineer/operator, I want the spec's proposed service targets measured before the first shadow.
- *Acceptance criteria.*
  1. Measured: monthly control-plane availability (target 99.9%), p95 event-to-case propagation (target under 60 seconds), staleness visible within 5 minutes of the health deadline, and fail-closed writes (spec §24 proposed targets).
  2. Provider delay is reported separately, and an end-to-end customer measure (time from source change to updated package) is reported so exclusions cannot hide unusable workflows.
- *Starting point.* None.

**E19-S05 Content-free product analytics** — Phase P2 · Priority Should · Trace: PL-060
- *Story.* Internal story (owner: Founder): measure whether Bookkeepers and the Reviewing accountant actually use the readiness ledger and the packages, without collecting their content.
- *Acceptance criteria.*
  1. Weekly active Bookkeepers on the readiness ledger and the share of in-scope client-periods whose package was opened are reported per tenant (D2 revisit triggers).
  2. Events carry ids and surface names only.
- *Starting point.* None.

### E20 Economics, budgets and cost accounting

**Goal.** Budgets are reserved atomically before work starts, actual cost is metered, full cost (including all Plumb labor) is accounted per verified deployment and per active client-month, and the billing basis follows D7's rules (PL-050, PL-058, PL-059).
**Why now.** Reservation mechanics are needed from the first M1 build (PA-015 settles budget once). Full-cost accounting drives the price guardrail and the R5 pivot trigger.
**Package has.** Declared worst-case budget checks in the plan checker, nested in every dimension (`_check_budgets`, [plan_checker.py](../plumb/checker/plan_checker.py) line 946); PL-058's text notes the reference checker does not meter a live provider. SQL `builds.reserved_minor_units` and `spent_minor_units`, which nothing writes. `OutcomeObservation` with `model_calls`, `completed`, `correct`, `realized_value` and `review_minutes`.

**E20-S01 Atomic budget reservation** — Phase P2 · Priority Must · Trace: PL-058, PL-017
- *Story.* As the Firm owner, I want Plumb never to spend past the build budget I approved, even when steps run in parallel.
- *Acceptance criteria.*
  1. Worst-case cost is reserved before each step starts; actual charges are recorded and unused reservations released.
  2. Concurrent reservations never exceed the build budget; two workers racing for the last unit of budget yield exactly one success; a step without budget waits with BUDGET_EXCEEDED rather than failing.
  3. These are PA-018's reservation mechanics without training, proposed as PA-P18 (recommended for P2; the Founder chooses P2 or P6); PA-018 itself also needs a training job and stays gated (E21-S07).
- *Starting point.* `Budget` on steps and plans; `_check_budgets`.

**E20-S02 Cost metering against provider charges** — Phase P2 · Priority Should · Trace: PL-058, PL-059
- *Story.* Internal story (owner: Founder): inference, substrate and infrastructure cost is recorded per build and per case and reconciled with invoices.
- *Acceptance criteria.*
  1. `builds.spent_minor_units` is written from metered charges; per-case cost is attributable.
  2. Monthly reconciliation with provider invoices stays within a tolerance set in the threshold sheet (hypothesis).
- *Starting point.* SQL `builds` columns.

**E20-S03 Full-cost and value accounting** — Phase P5 · Priority Should · Trace: PL-059, PL-062
- *Story.* Internal story (owner: Founder): model calls, completed cases, correct outcomes and realized value are kept apart, with customer review and Plumb labor costed beside inference and infrastructure.
- *Acceptance criteria.*
  1. Per tenant and per active client-month: inference, infrastructure and Plumb labor at loaded rates (from the effort ledger), plus customer review minutes.
  2. Technical and commercial success are reported separately (spec §24).
  3. Tenant 1's figures give the first read of PA-P12, the proposed economic-result attestation, in P5; no external value claim is made before it passes (D8 item 9).
- *Starting point.* `OutcomeObservation` fields.

**E20-S04 Billing basis: active client-months and credits** — Phase P5 · Priority Should · Trace: PL-001, PL-059, PL-013
- *Story.* As the Firm owner, I want to be billed only for client-months where Plumb delivered an attested package, with credits applied automatically.
- *Acceptance criteria.*
  1. A billable active client-month is an in-scope client-period with a verifier-attested ready-for-review package; native-setting outcomes bill at the same rate (D7). Prices are hypotheses (Prepare $15, Prepare + Chase $25 per active client-month).
  2. Credits are derived, never set by hand: a package rejected as materially wrong; a Plumb-caused DEGRADED collector covering more than 20% of the period; open customer-side dependencies (the firm minimum still applies); Plumb-side blocks, vendor outages and terminal failures are never billed.
  3. The billing export gives the reason for every credit.
- *Starting point.* `billing` field proposed on the ReviewPackage (E13-S01).

**E20-S05 Fully loaded cost per verified deployment and gross margin** — Phase P6 · Priority Should · Trace: PL-059, PL-062
- *Story.* Internal story (owner: Founder): the true cost to serve each firm is computed, so that pricing is judged against it.
- *Acceptance criteria.*
  1. Fully loaded cost per verified deployment and gross margin per active client-month include failed attempts and supervised delivery.
  2. The R5 trigger (cost above 2x price at tenant 4 with no downward trend) is computed and reported.
- *Starting point.* None.

**E20-S06 Model or provider changes evaluated on the full system** — Phase P4 · Priority Should · Trace: PL-050, PL-043
- *Story.* System story: a cheaper model or provider is adopted only after the complete workflow is re-evaluated on review load, latency, data terms and failure rates.
- *Acceptance criteria.*
  1. A model or provider change request without a full-system evaluation report is refused at release.
  2. The report compares current and candidate on the domain acceptance corpus (E10-S08); price alone is recorded as insufficient.
- *Starting point.* `EvaluationReport` ([evaluation.py](../plumb/contracts/evaluation.py)).

### E21 Learning factory (gated M2)

**Goal.** Locate input and target data, build point-in-time datasets, audit labels and, only if justified on total cost, train and promote a component, all after the D5 gates (PL-026, PL-027, PL-028, PL-029, PL-030, PL-031, PL-032, PL-033, PL-034; ADR-006).
**Why now.** Only the go/no-go memo is in plan (P5). Everything else waits behind all four D5 entry gates: audited join precision of at least 90% on a PA-012-style 100-pair accountant sample; TRAIN grants on at least 2 tenants; at least 500 explicit accept/correct events; and either classification errors at 25% or more of review minutes or a candidate comparison showing a reviewer-time gain (hypotheses, ratified by the Plumb domain expert). Training is the largest step in the accounting plan (EUR 2,500 of the EUR 10,060 step-budget sum), PA-012 does not require it, and idle dedicated capacity can make the trained path lose on total cost (spec §14).
**Package has.** `check_dataset` with FUTURE_INFORMATION, TARGET_LEAK, DUPLICATE_FAMILY_ACROSS_SPLITS, QUARANTINED_ROW_IN_TRAINING, DISALLOWED_SOURCE_USE and other codes ([dataset_checker.py](../plumb/checker/dataset_checker.py) line 78); `DatasetManifest`, `TrainingSpec` and `EvaluationReport` contracts. `TaskDefinition` and `ModelVersion` are ArtifactKind values without contracts. No runtime.

**E21-S01 M2 go/no-go memo** — Phase P5 · Priority Must · Trace: PL-026, PL-027, PL-031, PA-012
- *Story.* Internal story (owner: Applied ML/eval engineer, with the Plumb domain expert): the day-180 packet states, with numbers and denominators, whether each D5 entry gate is met.
- *Acceptance criteria.*
  1. Each of the four gates reports its measured value against its ratified threshold; the join-precision read-out uses a PA-012-style 100-pair accountant sample on tenants that grant TRAIN or EVALUATE (experiment 2), not client attribution accuracy.
  2. Signed by the Plumb domain expert; "no-go" is a normal outcome, not a company kill (R7).
- *Starting point.* Accept and correct counts from E14-S05.

**E21-S02 TaskDefinition contract and learning planner** — Phase Gated (M2) · Priority Could · Trace: PL-026
- *Story.* System story: the learning planner states the task (decision-time input, output, objective, error costs, eligible cases, expected use) before choosing data.
- *Acceptance criteria.*
  1. A `TaskDefinition` contract exists; dataset discovery is refused without one.
  2. Document-completeness labels are never mixed into categorization (spec App. B).
- *Starting point.* ArtifactKind `TaskDefinition` ([common.py](../plumb/contracts/common.py) line 364).

**E21-S03 Source-candidate table and join validation** — Phase Gated (M2) · Priority Could · Trace: PL-026, PL-027
- *Story.* As the Plumb domain expert, I want usable pairs, ambiguous joins and missing documents counted, not assumed, and ambiguous or disputed labels quarantined.
- *Acceptance criteria.*
  1. Counts are measured on the tenant's history; joins are validated independently on representative cases.
  2. Ambiguous, inconsistent and disputed labels are QUARANTINED; lack of complaint is never treated as correctness.
- *Starting point.* `LabelStatus` quarantine values.

**E21-S04 Point-in-time dataset builder** — Phase Gated (M2) · Priority Could · Trace: PL-028, PL-029, PL-030
- *Story.* System story: dataset rows use values known at decision time, splits answer stated questions, and manifests are immutable and honest about deleted sources.
- *Acceptance criteria.*
  1. Zero FUTURE_INFORMATION, TARGET_LEAK and DUPLICATE_FAMILY_ACROSS_SPLITS findings; rows with UNKNOWN_AVAILABILITY are excluded with reasons.
  2. DATASET reaches VERIFIED only through `check_dataset` (E05-S03); a manifest whose sources were deleted becomes UNAVAILABLE.
- *Starting point.* `check_dataset`, `DatasetManifest`.

**E21-S05 Label audit and M2 evidence** — Phase Gated (M2) · Priority Could · Trace: PL-027, PL-029, PL-053, PA-012
- *Story.* As the Reviewing accountant, I want a sample of labels reviewed before any dataset is trusted.
- *Acceptance criteria.*
  1. PA-012 passes: 100 input/label pairs reviewed into a label-audit report; disagreement above the task threshold keeps the manifest out of VERIFIED; no rows from a source without TRAIN.
- *Starting point.* PA-012 in the [catalog](../acceptance/production_acceptance_catalog.yaml) line 647.

**E21-S06 Candidate comparison on total cost** — Phase Gated (M2) · Priority Could · Trace: PL-031, PL-013
- *Story.* As the Firm owner, I want a trained component used only if it beats the simpler options on errors, review time and total cost.
- *Acceptance criteria.*
  1. Rules or native configuration, a prompted general model, retrieval, specialist APIs and training are compared on the complete workflow, including review effort and serving utilization.
- *Starting point.* `CandidateSystem` comparisons in [opportunity.py](../plumb/contracts/opportunity.py).

**E21-S07 TrainingSpec execution and training adapter** — Phase Gated (M2) · Priority Could · Trace: PL-032, PL-033, PL-052, PL-058, PA-017, PA-018, PA-024
- *Story.* System story: training runs only from a pinned TrainingSpec, through an adapter that persists submission identity, after full tenant isolation is proven.
- *Acceptance criteria.*
  1. Full PA-017 passes before any training job (D4).
  2. PA-018 passes (atomic reservation and no duplicate training job); an accounting adaptation of PA-024's poisoned-label test passes (not claimed as PA-024).
  3. A completed provider job is a CANDIDATE, never a production model.
- *Starting point.* `TrainingSpec`; TRAINING machine guard `submission_identity_persisted`.

**E21-S08 Model promotion gate** — Phase Gated (M2) · Priority Could · Trace: PL-034, PL-043, ADR-008
- *Story.* System story: a model is promoted only with a held-out evaluation, a quality and cost comparison, a registry version, a compatible serving interface and a deployment policy.
- *Acceptance criteria.*
  1. A `ModelVersion` contract exists; promotion goes through a release with a BUSINESS_OUTCOME attestation; MODEL_ALIAS_UNRESOLVED blocks.
  2. Drift triggers evaluation, never automatic promotion (spec App. B).
- *Starting point.* `check_release` HELD_OUT_EVALUATION_MISSING and MODEL_ALIAS_UNRESOLVED.

### E22 Maintenance and repair

**Goal.** Monitors link failures to cases and releases from P2; manual operations are logged truthfully until a maintenance agent exists; bounded repair through new change plans arrives after day 180 (PL-018, PL-048, PL-049).
**Why now.** Collectors running from P2 need health alerts (PA-011), and the shadow release in P4 needs the seven monitors (`check_release` OPERATING_PLAN_MISSING). The maintenance agent itself is out for 180 days; ops stay manual and logged (D3).
**Package has.** `OperatingPlan` and `MonitorKind` ([release.py](../plumb/contracts/release.py) lines 124-168). PL-049 has no local test at all ([validation report](../VALIDATION_REPORT.md)). No monitoring.

**E22-S01 Monitoring linked to cases and releases** — Phase P2 · Priority Must · Trace: PL-048, PL-025, PA-011
- *Story.* As the Reviewing accountant, I want an alert about a failing source to name the clients and packages it affects, not just a global uptime number.
- *Acceptance criteria.*
  1. P2: collector health alerts link to affected client-periods; the health half of PA-011 passes (with E08-S05).
  2. P4: all seven monitor kinds are live for the shadow release, and REVIEW_BURDEN and COST alerts route to the escalation contact.
- *Starting point.* `MonitorKind`.

**E22-S02 Logged manual operations** — Phase P2 · Priority Must · Trace: PL-003, PL-049, PL-062
- *Story.* As the Firm owner, I want any manual fix Plumb makes to my firm's running setup to appear in my ledger.
- *Acceptance criteria.*
  1. Every staff change to a tenant's running system goes through a change record that writes an effort entry: manual deploys as ENGINEERING_INTERVENTION, fixes to running collectors or workflows as OPERATIONAL_REPAIR (D3).
  2. A change made without a change record is detected by the audit tooling (E10-S07).
- *Starting point.* None.

**E22-S03 Failure-contract triage** — Phase P4 · Priority Should · Trace: PL-049, PL-018
- *Story.* System story: every incident starts by naming which contract failed (access, schema, data quality, business rule, model behavior or infrastructure) before choosing reconnection, a human decision or repair (spec §20).
- *Acceptance criteria.*
  1. Every incident record carries its failed contract and failure class; the blocked-dependency card shows them.
- *Starting point.* `FailureClass`.

**E22-S04 Schema-drift repair through a new change plan** — Phase P6 · Priority Could · Trace: PL-049, PL-018, PL-021
- *Story.* System story: a drift on an accounting source is repaired by a new change plan with a bounded budget, and the verification gates re-run.
- *Acceptance criteria.*
  1. PA-P06, the accounting adaptation of PA-016 (not claimed as PA-016): the affected path is quarantined; the change plan runs integration.generate_adapter, integration.contract_test and collection.reconcile within its repair budget; the verifier rejects a widened mapping without the needed conversion; quarantined records are reprocessed only after verification.
  2. The repair never alters a live policy, evaluation threshold or authorized processor (PL-049).
- *Starting point.* None.

**E22-S05 Recovery drill** — Phase P6 · Priority Could · Trace: PL-038, PL-017, PL-059
- *Story.* Internal story (owner: SRE/on-call): before the Send canary, a drill kills the dispatcher after the provider accepts a draft or send and shows nothing is created twice.
- *Acceptance criteria.*
  1. The effect goes UNKNOWN, is reconciled, and the drill report lists receipts and the support effort recorded; the report is part of PA-P04's evidence.
- *Starting point.* None.

**E22-S06 Maintenance agent** — Phase Gated (past P6) · Priority Could · Trace: PL-049, PL-050
- *Story.* System story: a maintenance agent proposes and applies permitted repairs, such as a backward-compatible field addition, inside the current envelope with bounded attempts.
- *Acceptance criteria.*
  1. Local behavioral tests exist for PL-049 (none today); every repair repeats the applicable verification gates.
  2. It never restores a green status by changing a policy, threshold or processor.
- *Starting point.* None.

### E23 Second domain (M6, laundry)

**Goal.** Add laundry route preparation on the same planner, compiler and runtime, then RFQ, with new adapter and domain work measured separately (spec §26 M6 row; D5). Gated by M5 evidence and by PA-013, PA-025, PA-029 and PA-030. All stories are Could.
**Package has.** The [laundry plan fixture](../fixtures/plans/laundry_route_preparation.json) (21 steps, GBP), which stops at release.activate_shadow because external communication is not allowed; the RFQ plan fixture (22 steps, USD). Both are synthetic and show representational reuse, not cross-industry autonomy (spec §25).

**E23-S01 M6 entry memo and scenario** — Phase Gated (M6) · Priority Could · Trace: PL-063, PL-062
- *Story.* Internal story (owner: Founder): the M6 decision cites M5 evidence, and PA-P10, the proposed M6 scenario in the [roadmap](04-roadmap.md), defines "reused planner, compiler and runtime; new domain work measured separately".
- *Acceptance criteria.*
  1. Domain work is recorded in the platform-investment ledger, tenant work in the tenant ledger; fork count 0.
- *Starting point.* None.

**E23-S02 Route-plan contract** — Phase Gated (M6) · Priority Could · Trace: PL-035, PL-001
- *Story.* As a laundry dispatcher (persona to be defined at M6), I want the prepared route plan defined as a contract, as the ReviewPackage is for accounting.
- *Acceptance criteria.*
  1. Contract and validators exist; physical execution is an explicit human step and the system never reports garments as moved (PA-029).
- *Starting point.* None.

**E23-S03 Laundry shadow-only release** — Phase Gated (M6) · Priority Could · Trace: PL-013, PL-035, PL-051, PA-025, PA-029, PA-030
- *Story.* System story: the laundry workflow runs in shadow with a routing solver and no external communication.
- *Acceptance criteria.*
  1. PA-029 passes (exact capacity feasible; overload pauses with options; publication only after approval).
  2. PA-030 passes (LOW severity; reordered and duplicated telematics converge).
  3. PA-025 passes before any publication (unauthorized recipients receive nothing).
- *Starting point.* Laundry envelope and plan fixtures.

**E23-S04 Laundry canary** — Phase Gated (M6) · Priority Could · Trace: PL-047, PL-049, PA-013
- *Story.* System story: the laundry release canaries on at most 2 of 9 vehicles for 3 days with receipts, a recovery drill and a repaired defect.
- *Acceptance criteria.*
  1. PA-013 passes as written in its own domain.
- *Starting point.* None.

**E23-S05 RFQ domain scenarios** — Phase Gated (after laundry) · Priority Could · Trace: PL-021, PL-040, PL-051, PA-014, PA-016, PA-020, PA-021, PA-023, PA-024, PA-028
- *Story.* System story: draft quotation preparation for an industrial distributor, with binding quotes left to a human commercial decision.
- *Acceptance criteria.*
  1. PA-014, PA-016, PA-020, PA-021, PA-023, PA-024 and PA-028 run as written in the RFQ domain; earlier accounting adaptations are never counted toward them.
- *Starting point.* RFQ envelope and plan fixtures.

### E24 Acceptance catalog and threshold sheet

**Goal.** Thresholds are pre-registered before evidence arrives; external claims pass a formal never-claim gate; catalog gaps (M0, M6, generated paths, policy-level approvals, accounting analogues) are proposed; and each milestone decision is a written packet citing the ledger and attestations (PL-044, PL-061, PL-062, PL-063).
**Why now.** Every threshold is a hypothesis to ratify at M0 (D11 reading rules), and the never-claim checklist is a P0 deliverable owned by the Founder (D8).
**Package has.** The [acceptance catalog](../acceptance/production_acceptance_catalog.yaml) with 30 scenarios (27 HIGH, 2 MEDIUM, 1 LOW), none run against production; [test_acceptance_catalog.py](../tests/test_acceptance_catalog.py) checks structure and the M1-M5 evidence titles. Synthetic [fixture envelopes](../fixtures/envelopes) whose grants and envelopes all expire 2027-03-31: the accounting envelope and plan are EU/EUR (`eu-west-1`), the RFQ fixtures USD (`us-east-1`) and the laundry fixtures GBP (`eu-west-2`); [refresh_fixture_digests.py](../scripts/refresh_fixture_digests.py).

**E24-S01 Threshold sheet v1 and experiment charter** — Phase P0 · Priority Must · Trace: PL-062, PL-063
- *Story.* Internal story (owner: Plumb domain expert, with the Founder): every threshold the plan relies on is written down and signed before the first build, so results cannot be rationalized afterwards.
- *Acceptance criteria.*
  1. Covers the six spec §27 experiments and the commercial unknowns, including: tenant 3 EIH/VD at or below 50% of tenant 1 (review at 75% or more); hands-off build rate of at least 50%; reuse of at least 60% with zero forks; false-chase rate of 2% or less, recall of 90% or more, attribution correctness of 95% or more at the auto-accept threshold; the interruption budget (D6); the M2 gates (D5). All are hypotheses.
  2. P0 exit: signed by the Founder and the Plumb domain expert; ratified at M0 with an external technical advisor.
  3. Changes are new versions with reasons; windows are not extended when two triggers fire at once (D11).
- *Starting point.* Founder decisions in the decision record.

**E24-S02 Never-claim checklist as a release gate for words** — Phase P0 · Priority Must · Trace: PL-003, PL-062, PL-063
- *Story.* Internal story (owner: Founder): sales, marketing and investor materials pass the D8 never-claim checklist before use.
- *Acceptance criteria.*
  1. P0 exit: the 12-item checklist is published (local tests do not validate models, outcomes, security or integrations; synthetic scenarios are not cross-industry autonomy; 90 days is a hypothesis; video results are not evidence; no autonomous close or posting; never "fully autonomous" or "AI employee"; "automatically constructed" only after M1R; no logo walls; no ROI without baseline and denominator; no exact unlearning; never claim a message unsent after provider acceptance; claims match the released tier).
  2. Every external asset has a recorded checklist review; the checklist is never relaxed under any result (D8).
- *Starting point.* D8.

**E24-S03 Re-template fixtures to US/USD and handle expiry** — Phase P0 · Priority Must · Trace: PL-005
- *Story.* Internal story (owner: Tech lead): the accounting fixtures match the US beachhead and do not break CI when their envelopes expire.
- *Acceptance criteria.*
  1. The accounting envelope and plan are re-templated from EUR and `eu-west-1` to USD and a US region, digests refreshed with `scripts/refresh_fixture_digests.py`, and all local tests pass.
  2. The checker CLI and local tests pass when run with a clock at or after 2027-03-31, either because expiries were refreshed or because tests pin the evaluation instant.
- *Starting point.* [Accounting envelope fixture](../fixtures/envelopes/accounting_evidence_preparation.json); README note on `ENVELOPE_INACTIVE` after 2027-03-31.

**E24-S04 M0 exit checklist as a gate** — Phase P1 · Priority Must · Trace: PL-063, PL-007, PL-008
- *Story.* Internal story (owner: Founder): no catalog scenario covers M0, so the D4 M0 checklist is tracked with evidence links.
- *Acceptance criteria.*
  1. Each item links to its evidence: named domain owner; judgeable outcome definition with a denominator; SANDBOX_TESTED receipts on tenant 1's real accounts; zero synthetic PRODUCTION_VERIFIED records; threat model signed off; month-0 baseline captured or scheduled; effort ledger live with the frozen rubric; tenant 1 DPA and envelope signed.
  2. The M0 exit decision is recorded with the date and signatories, as the evidence for PA-P09, the proposed M0 scenario (re-run at each tenant's onboarding).
- *Starting point.* None.

**E24-S05 Proposed catalog changes** — Phase P1 · Priority Should · Trace: PL-061, PL-063, PA-001, PA-002, PA-010, PA-013, PA-014, PA-016, PA-021, PA-023, PA-027
- *Story.* Internal story (owner: Verification engineer): the catalog gaps the decision record found are written as proposed scenarios, numbered in the [roadmap](04-roadmap.md), so they cannot be mistaken for catalog scenarios.
- *Acceptance criteria.*
  1. Proposals PA-P01 to PA-P19 as defined in the [roadmap](04-roadmap.md) section 6, covering the D4 list (PA-027 at HIGH for any release marketed as autonomously implemented, PA-P13; the generated-path, preparation-mode and policy-level variants PA-P01, PA-P02 and PA-P03; accounting analogues of PA-013, PA-014, PA-016, PA-021 and PA-023 as PA-P04 to PA-P08; M0 and M6 scenarios PA-P09 and PA-P10) and the coverage gaps (PA-P11 opportunity selection, PA-P12 economic result, PA-P14 to PA-P18 staged subsets, PA-P19 prompt injection in accounting documents).
  2. Each is written in catalog shape (preconditions, steps, expected outcome, severity, requires) and is never reported as the original scenario.
  3. The catalog file and its tests change only after Founder ratification.
- *Starting point.* Catalog structure and [test_acceptance_catalog.py](../tests/test_acceptance_catalog.py).

**E24-S06 Staged PA-017 test plan** — Phase P1 · Priority Should · Trace: PL-052, PA-017
- *Story.* Internal story (owner: Security/platform engineer): PA-017 is split into an M1 subset (database, API, object storage, cache, logs, exports) and the full nine-surface run before any training job, because tenant data is co-resident from M1 while training jobs and model routes come much later.
- *Acceptance criteria.*
  1. Subset A is PA-P14 (P2, re-run in P3 with co-resident tenants); subset B is PA-P15, run surface by surface before a second tenant's data reaches it (workspaces in P3 if generated code runs, model routes in P5, training jobs before the first training job), as the [roadmap](04-roadmap.md) plans.
  2. Each subset references PA-017's steps exactly; nothing is reported as a PA-017 pass until all nine surfaces pass.
- *Starting point.* PA-017 in the [catalog](../acceptance/production_acceptance_catalog.yaml) line 901.

**E24-S07 Scenario execution ledger** — Phase P2 · Priority Must · Trace: PL-061, PL-042, PL-044
- *Story.* As the Independent verifier, I want every scenario run recorded with its environment, tenant, attestation and whether it was an adaptation, so that milestone claims trace to evidence.
- *Acceptance criteria.*
  1. No scenario is marked passed without an attestation produced in the intended environment.
  2. Adaptations and proposed variants are tagged and excluded from catalog pass counts; synthetic runs are tagged and never cited as business performance (PL-044).
- *Starting point.* `locally_executed` and `executed_against_production` flags in the catalog.

**E24-S08 R1 checkpoint memo at M1R** — Phase P3 · Priority Must · Trace: PL-062, PL-063, PL-002
- *Story.* Internal story (owner: Founder): at M1R exit, a memo reads the pre-registered R1 criteria against the evidence.
- *Acceptance criteria.*
  1. Reports EIH/VD per tenant in onboarding order (failed attempts included), platform-investment hours beside it, hands-off build rate, reuse rate and fork count, each with its root cause by failure class.
  2. States whether any R1 trigger fired (tenant 3 at or above 75% of tenant 1; hands-off rate below 50% on tenants 2 and 3; reuse below 60%; any fork) and the response.
  3. "Automatically constructed" may be used only if M1R passed and the audit found zero unrecorded work (D8 item 7).
- *Starting point.* E01-S06, E01-S07.

**E24-S09 Day-180 decision packet** — Phase P5 · Priority Must · Trace: PL-063, PL-062, PL-059
- *Story.* Internal story (owner: Founder): on day 180 (Apr 3, 2027, hypothesis) the go, pivot or kill decisions are made against the pre-registered thresholds, in writing.
- *Acceptance criteria.*
  1. Covers PL-063 evidence (M1 and M1R); EIH/VD and reuse across three tenants with failed attempts; tenant 1 shadow results; tenant 1's evidence to date toward paid conversion, which is expected in P6 after one full ACTIVE close at or above the correct-package threshold (founder decision 17; E16-S07); the experiment-1 proxy; the M2 go/no-go (E21-S01); go/no-go on the Draft tier and the M4-accounting canary, each against its threshold.
  2. Every number cites a ledger entry, an attestation or a measured study; the packet passes the never-claim checklist.
- *Starting point.* None.

---

## 4. Requirement traceability matrix

One row for every requirement in [requirements_index.json](../spec/requirements_index.json), in order. Columns:

- **Stories**: the main stories that implement or test the requirement (a story may trace more ids than are listed here).
- **Phase first addressed**: the earliest phase in which such a story is scheduled (proposed). Where this differs from the phases the decision record's phased plan lists for the requirement, the notes say so.
- **Status today**: from the [validation report](../VALIDATION_REPORT.md) coverage matrix. "Behavioral test (n)" means n local behavioural tests (the report's term) exercise the reference contract, checker, ledger or state machine; "Artifact inspection only" means tests only inspect a delivered artifact; "None" means only production acceptance scenarios specify it. No requirement is validated in production; no scenario has run.
- **Notes**: acceptance scenarios and their phase, deferrals and reasons.

| PL id | Short title (spec section) | Stories | Phase first addressed | Status today | Notes |
|---|---|---|---|---|---|
| PL-001 | Three explicit outcomes per authorized goal; a recommendation never counts as done (§1) | E03-S06, E15-S02, E05-S07, E11-S02, E11-S05, E13-S01, E13-S08, E20-S04 | P1 | Behavioral test (6) | Dependencies persisted and grouped from P1; outcome mix reported from P2; the record lists P4, where the package becomes the first business outcome. Billing only on verified outcomes (D7). PA-002, PA-004, PA-008 at P4; PA-029 laundry (M6) |
| PL-002 | Ordinary implementation tasks without a human engineer, for supported environments (§1) | E02-S04, E02-S06, E05-S06, E07-S01, E07-S03, E07-S05, E08-S07 | P1 | None (acceptance scenarios only) | The record lists P2; inventory probes start in P1. "Supported environments" is defined by E02-S06. PA-001 at P2 and P3; PA-P01 at P3; PA-027 at P6 (M5) |
| PL-003 | All human effort recorded in five categories; no autonomy claim over hidden work (§1) | E01-S01, E01-S02, E01-S03, E01-S04, E01-S07, E10-S07, E22-S02 | P0 | Artifact inspection only | First product code (P0). PA-027's audit method is applied at M1, M1R and M5; the formal PA-027 pass is P6 |
| PL-004 | Full operation context; tenant from verified authentication (§4) | E01-S02, E03-S02, E03-S03, E03-S04, E15-S03 | P0 | Behavioral test (6) | P0 is the staff principal types; verified identity is P1, as the record lists. PA-017 API surface at P2 |
| PL-005 | Versioned, owner-tied envelope that derived tasks cannot widen (§4) | E24-S03, E04-S01, E04-S02, E04-S03, E04-S05, E04-S06, E03-S09 | P0 | Behavioral test (83) | P0 is fixture re-templating; the tenant envelope is P1, as the record lists. PA-008 at P4; PA-025 laundry (M6) |
| PL-006 | No production admin credentials for agents; separate management, execution and policy capabilities (§4) | E03-S04, E05-S05, E06-S02, E06-S08, E17-S02 | P1 | Behavioral test (1) | PA-022 at P2; PA-026 on the first tenant where generated code runs (P2 or P3) |
| PL-007 | EnvironmentInventory before any production build (§5) | E02-S01, E02-S04, E02-S07, E02-S08, E05-S01 | P0 | Behavioral test (12) | PA-001 precondition (P2). PA-023 is RFQ; its account-boundaries test runs as an accounting adaptation at P2 |
| PL-008 | Discovered, documented, sandbox-tested and production-verified distinguished per account and operation; credential-safe probes (§5) | E02-S01, E02-S02, E02-S03, E02-S04, E02-S07, E16-S02 | P0 | Behavioral test (60) | Zero synthetic PRODUCTION_VERIFIED at P0 exit; tenant receipts P1; release.* PRODUCTION_VERIFIED from the qualification run (P4). PA-022 at P2 |
| PL-009 | Evidence events with provenance and three time axes (§6) | E09-S01, E09-S05, E08-S07 | P2 | Behavioral test (5) | PA-001 at P2; PA-006 at P4; PA-030 laundry (M6) |
| PL-010 | Derived-fact status; unknown absence distinct from confirmed absence (§6) | E09-S02, E09-S03, E08-S05, E08-S09, E11-S04, E13-S01 | P2 | Behavioral test (6) | PA-011 health half at P2 and full in sandbox at P4; PA-003, PA-004, PA-006 at P4; PA-028 RFQ (M6) |
| PL-011 | Ambiguous candidates, merge and split history, scoped reversible corrections (§6) | E09-S03, E09-S04, E09-S06, E11-S06 | P2 | Behavioral test (5) | PA-003 and PA-004 at P4 |
| PL-012 | Complete OpportunitySpec with a prospective measurement plan (§7) | E14-S01, E12-S01, E12-S02, E12-S04, E12-S05, E04-S04 | P1 | Behavioral test (13) | The record's phased plan lists no phase. Open-ended discovery is replaced by a vertical library (D3). Only PA-027 covers it (P6); PA-P11 is proposed to close the gap |
| PL-013 | Non-ML and native-configuration candidates compared with the current process and a native-feature baseline (§7) | E12-S01, E12-S03, E21-S06 | P2 | Behavioral test (5) | The record lists no phase. Native-setting outcomes bill at the same rate (D7). Only PA-029 covers it (laundry, M6); PA-P11 is proposed for accounting |
| PL-014 | Finite typed BuildPlan; unsupported step types rejected (§8) | E05-S02, E05-S05, E05-S06, E06-S07, E13-S03 | P1 | Behavioral test (67) | PA-022 at P2; PA-018 needs a training job (gated) |
| PL-015 | Compiler checks ids, dependencies, I/O, artifacts, authority, region and purpose, effect class, budget and verification (§8) | E05-S01, E05-S02, E18-S04 | P1 | Behavioral test (61) | Proposed codes INVENTORY_OPERATION_UNPROBED, INVENTORY_MISSING, AUTHORITY_MISSING. Only PA-018 covers it (gated) |
| PL-016 | Execution from persisted state; a step is verified only after the required checks (§8) | E05-S03, E05-S04, E10-S01, E11-S01, E13-S06 | P1 | Behavioral test (58) | The record lists P2; guard wiring is in its P1 scope. PA-015 at P2; PA-002 at P4 |
| PL-017 | Durable build ledger; restart without redoing verified effects (§9) | E05-S04, E08-S02, E10-S03, E17-S03, E20-S01 | P1 | Behavioral test (2) | PA-015 at P2 (collector creation), with a mechanism re-run on gateway dispatch workers at P5; PA-009 at P5 (sandbox gateway); PA-013 laundry (M6) |
| PL-018 | Bounded repair that keeps diagnostics and cannot weaken tests or widen permissions (§9) | E05-S07, E10-S02, E22-S03, E22-S04 | P2 | Behavioral test (35) | PA-016 is RFQ; its accounting adaptation is P6 (E22-S04) |
| PL-019 | Generated code in an isolated, disposable build environment (§9) | E05-S05, E06-S01, E06-S05, E06-S06, E07-S05 | P1 | Behavioral test (8) | The record lists P2; the harness boundary starts in P1. PA-026 on the first generated-code tenant; PA-021 adaptation at P4 |
| PL-020 | Integration path preference, recorded with maintenance exposure (§10) | E02-S05, E07-S01, E07-S03, E07-S05 | P1 | Behavioral test (5) | The record lists P2; substrate contract tests start in P1. PA-001 expects VERIFIED_ADAPTER (P2); a non-VERIFIED_ADAPTER path at tenant 3 (P3) |
| PL-021 | IntegrationSpec declares account, operations, scopes, mappings, cursors, retries, deletion, effect class, probes and drift handling (§10) | E07-S01, E07-S02, E07-S04, E07-S06, E22-S04 | P2 | Behavioral test (7) | PA-016 and PA-023 are RFQ; accounting adaptations at P6 and P2 |
| PL-022 | Adapter contract tests before activation (§10) | E02-S05, E07-S02, E07-S04 | P1 | Behavioral test (3) | The record lists P2; substrate contract tests start in P1. PA-001 at P2; PA-023 account-boundaries adaptation at P2 |
| PL-023 | Purpose-justified CollectionSpec (§11) | E18-S02, E08-S01, E08-S08, E18-S03 | P1 | Behavioral test (2) | P1 is the tax-return exclusion; collector specs at P2, as the record lists. PA-001 at P2 |
| PL-024 | Backfill and live capture converge without silent gaps or duplicates (§11) | E08-S02, E08-S03, E08-S04, E06-S04, E10-S03 | P2 | Behavioral test (7) | PA-005 collector half (PA-P16) at P2; PA-030 laundry (M6) |
| PL-025 | Collectors publish health; downstream work blocks or degrades explicitly (§11) | E08-S05, E08-S06, E08-S09, E22-S01, E07-S06 | P2 | Behavioral test (4) | PA-011 health half (PA-P17) at P2, full in sandbox at P4; PA-005 at P2 and P5 |
| PL-026 | Learning task stated before data; label kinds distinguished (§12) | E14-S05, E21-S01, E21-S02, E21-S03 | P4 (partial); otherwise deferred (M2 gated) | Behavioral test (1) | Deferred: the learning factory is out for 180 days (D3). P4 only stores input snapshots and reviewed decisions under the case id; the TaskDefinition waits for the D5 gates. PA-012 gated |
| PL-027 | Joins validated; ambiguous and disputed labels quarantined; no silent acceptance as correctness (§12) | E14-S03, E14-S05, E21-S03, E21-S05 | P4 | Behavioral test (4) | P4 enforces explicit acceptance in review; dataset join validation and quarantine are deferred to M2. PA-012 gated; PA-024 RFQ |
| PL-028 | Point-in-time training and evaluation rows (§13) | E21-S04 | Deferred (M2 gated) | Behavioral test (15) | Deferred past P6: no dataset materialization until the D5 entry gates pass. PA-012 gated |
| PL-029 | No future information, cross-split near-duplicates or disallowed source uses (§13) | E05-S03, E21-S04, E21-S05 | Deferred (M2 gated); guard wiring P1 | Behavioral test (18) | The DATASET guard calls `check_dataset` from P1 (E05-S03); datasets themselves wait for M2. PA-012 gated; PA-030 laundry |
| PL-030 | Immutable, reproducible manifests; UNAVAILABLE when sources are deleted (§13) | E21-S04, E18-S07 | Deferred (M2 gated); data-removal path P4 | Behavioral test (18) | Manifests wait for M2; the removal workflow marks affected datasets UNAVAILABLE from P4. PA-012 gated |
| PL-031 | Solution method chosen on task performance and total operating cost (§14) | E13-S05, E12-S03, E21-S01, E21-S06 | P4 (partial) | Behavioral test (4) | The record lists no phase. P4 records why deterministic checks plus a general model, not training; the full candidate comparison is M2. PA-012 gated |
| PL-032 | Pinned TrainingSpec; unsupported combinations fail before submission (§14) | E13-S03, E18-S08, E21-S07 | Deferred (M2 gated) | Behavioral test (29) | Deferred past P6: no TrainingSpec execution or training.submit for 180 days (D3), and only after the M2 go. E13-S03 keeps training out of templates. PA-024 RFQ |
| PL-033 | Training adapter lifecycle with persisted submission identity (§14) | E21-S07 | Deferred (M2 gated) | Behavioral test (5) | Deferred past P6 for the same reason (D3). PA-018 gated |
| PL-034 | Gated model promotion; aliases resolve to immutable versions per case (§14) | E13-S05, E16-S06, E21-S08 | P4 (alias pinning); promotion deferred | Behavioral test (27) | Per-case pinning applies to the general model in P4 (ADR-008); trained-model promotion waits for M2. PA-013 laundry |
| PL-035 | Complete WorkflowSpec; read-only preparation separated from external effects (§15) | E13-S02, E13-S03, E13-S04, E13-S06, E16-S01 | P4 | Behavioral test (7) | PA-002 at P4 (sandbox); PA-P02 in production shadow (P4, full close P5); PA-025 and PA-029 laundry (M6) |
| PL-036 | Deterministic rules outside model text; outputs validated before tool execution (§15) | E04-S01, E13-S02, E13-S04, E13-S05, E13-S07 | P1 | Behavioral test (3) | P1 is the envelope excluding FINANCIAL_COMMITMENT; workflow rules at P4, as the record lists. PA-003 at P4; PA-020 RFQ; PA-029 laundry |
| PL-037 | Persisted action intent; no redispatch of a slot with a changed payload (§16) | E13-S07, E17-S01, E17-S02, E17-S05, E17-S06 | P4 | Behavioral test (16) | The record lists P5; P4 uses the case state version for stale-input recomputation. PA-006 at P4; PA-005 dispatch-time re-check at P5; PA-007 in the Send canary (P6, earliest close around July 2027); PA-028 RFQ |
| PL-038 | Ambiguous outcomes enter UNKNOWN and are reconciled before retry (§16) | E17-S03, E17-S04, E17-S08, E22-S05 | P5 | Behavioral test (22) | PA-015 at P2, with a mechanism re-run at P5; PA-009 at P5 (sandbox gateway) and P6 (gate); PA-014 RFQ, adapted at P6 |
| PL-039 | Deduplication across restarts and releases; cross-workflow obligation ownership (§16) | E17-S01, E17-S04, E17-S07 | P5 | Behavioral test (11) | PA-005 and PA-009 at P5 and P6; PA-007 in the P6 Send canary, earliest close around July 2027 (needs concurrent ACTIVE and CANARY releases) |
| PL-040 | Approvals bound to digest, case version, policy version, approver and expiry, from an authenticated decision (§17) | E01-S02, E15-S03, E15-S01, E15-S04, E14-S03, E04-S04, E05-S02, E17-S02 | P0 | Behavioral test (41) | P0 is the rule that staff cannot approve; approval capture at P1; the record lists P4. PA-006 and PA-010 at P4; PA-014 and PA-028 RFQ |
| PL-041 | Continue within authority; group missing authorizations; never re-ask valid authority (§17) | E15-S02, E15-S01, E15-S05, E04-S05, E11-S02, E11-S06 | P1 | Behavioral test (7) | The record lists P4; owner decisions start at onboarding. PA-004, PA-008, PA-010 at P4; PA-014 RFQ |
| PL-042 | Verification inspects artifacts and state; records verifier, digest, evidence, result and environment (§18) | E02-S03, E05-S03, E10-S01, E10-S04, E24-S07 | P1 | Behavioral test (19) | The record lists P2; the verifier build starts in P1. PA-002 at P4 |
| PL-043 | Release includes structural, integration and business checks, adversarial tests and an operating plan (§18) | E10-S05, E10-S06, E16-S05, E13-S06, E20-S06 | P4 | Behavioral test (46) | PA-002 at P4; PA-013 laundry (M6), with an accounting analogue proposed |
| PL-044 | Evaluation data segregated from tuning and repair; controlled diagnostics (§18) | E10-S02, E10-S08, E24-S07 | P2 | Behavioral test (6) | The record lists P4; protected bundles are needed for M1 attestations. PA-024 RFQ (gated) |
| PL-045 | Infrastructure from approved templates with preview, cost, lock, tags and rollback class before apply (§19) | E16-S01 | P4 | Behavioral test (14) | Fixed approved templates only; generic infrastructure generation is iced (section 5). PA-013 laundry |
| PL-046 | ReleaseManifest binds every component version by digest (§19) | E16-S01, E16-S02, E18-S04 | P4 | Behavioral test (14) | PA-013 laundry, with an accounting analogue proposed |
| PL-047 | Shadow, canary, active, paused, rolled-back and retired; pinning; pause blocks new effects (§19) | E05-S03, E16-S03, E16-S04, E16-S06, E16-S07, E17-S02 | P1 | Behavioral test (11) | P1 is guard wiring for release edges; pause and kill from SHADOW and CANARY at P4, as the record lists. PA-013 laundry |
| PL-048 | Monitors for every active intervention, linked to cases and releases (§20) | E08-S05, E22-S01, E16-S05, E07-S06 | P2 | Behavioral test (1) | The record lists P6; collectors need health alerts from P2 and the P4 shadow release needs the seven-monitor operating plan (OPERATING_PLAN_MISSING). PA-011 at P2 and P4; PA-016 RFQ |
| PL-049 | Maintenance agent creates a new change plan, repeats the gates and never silently restores green (§20) | E22-S02, E22-S03, E22-S04, E22-S06 | P2 (manual stand-in); agent deferred past P6 | None (acceptance scenarios only) | Deferred: the maintenance agent is out for 180 days (D3). Manual operations are logged from P2; change-plan repair of schema drift at P6, which the record lists. PA-013 laundry; PA-016 RFQ |
| PL-050 | Model or provider changes evaluated on the full system, not on price (§20) | E20-S06, E12-S07, E22-S06 | P4 | Behavioral test (1) | The record lists no phase; it applies from the first general-model use. PA-027 at P6 |
| PL-051 | Untrusted inputs cannot change authority, permissions, destinations or the verification standard (§21) | E06-S07, E06-S06, E10-S06 | P2 | Artifact inspection only | The record lists no phase; PA-022 is in the M1 bundle (P2); PA-P07 and PA-P19 at P4. PA-020, PA-021 RFQ; PA-025 laundry |
| PL-052 | Tenant isolation across database, storage, search, caches, workspaces, training, model routes, logs and exports (§21) | E03-S01, E03-S05, E03-S06, E18-S05, E19-S03, E24-S06 | P1 | Behavioral test (1) | The record lists P2. PA-P14 at P2, with co-resident tenants at P3; PA-P15 surface by surface; full PA-017 before any training job (gated) |
| PL-053 | Purpose authorization enforced end to end; no training permission inferred from read (§21) | E18-S01, E18-S02, E18-S03, E18-S04, E18-S05, E18-S07, E15-S04 | P1 | Behavioral test (54) | SERVE before the first shadow (P4). PA-008 at P4; PA-026 at P2 or P3; PA-012 and PA-024 gated |
| PL-054 | Secrets out of prompts, artifacts and telemetry; mediated egress; webhook defenses (§21) | E06-S02, E06-S03, E06-S04, E06-S05, E19-S02 | P1 | Behavioral test (19) | The record lists P2; credential resolution is needed for P1 probes. PA-019 at P2; PA-026 at P2 or P3; PA-021 adaptation at P4 |
| PL-055 | Asynchronous, idempotent long-running mutations (§22) | E03-S01, E03-S03, E03-S07, E01-S08 | P1 | Behavioral test (5) | The record lists no phase. Only PA-018 covers it (gated) |
| PL-056 | Optimistic concurrency, non-revealing errors, stable cursors (§22) | E03-S02, E03-S03, E03-S05, E03-S07, E03-S08 | P1 | Behavioral test (2) | The record lists no phase. PA-017 API surface at P2 |
| PL-057 | Transactional, versioned, auditable state transitions (§23) | E03-S08, E05-S03, E05-S04, E17-S01, E17-S03 | P1 | Behavioral test (65) | The record lists P5; the durable build ledger and audited transitions are in its P1 scope. PA-015 at P2; PA-009 at P5 |
| PL-058 | Atomic cost reservation before work; actuals recorded; unused released (§24) | E20-S01, E20-S02, E04-S04, E04-S06 | P2 | Behavioral test (39) | The record lists no phase. Reservation mechanics are tested from P2 as PA-P18 (Founder chooses P2 or P6); PA-018 gated |
| PL-059 | Customer review and Plumb labor measured beside inference and infrastructure; value distinguished (§24) | E01-S03, E01-S04, E14-S01, E14-S06, E11-S05, E20-S03, E20-S04 | P0 | Artifact inspection only | The record lists P1. PA-P12 first read at P5; PA-027 at P6; PA-013 laundry |
| PL-060 | Correlated telemetry without sensitive content; pinned conventions (§24) | E19-S01, E19-S02, E19-S03, E19-S04 | P2 | Artifact inspection only | The record lists no phase. PA-019 and the PA-017 log surface at P2 |
| PL-061 | Release suite covers the nine case categories; high-severity failures block activation (§25) | E24-S05, E10-S03, E10-S05, E10-S06, E24-S07 | P1 | Behavioral test (4) | The record lists P6. Catalog proposals start in P1, the harness and scenario execution ledger in P2, and the protected suite and blocking rule apply to the P4 shadow release, where PA-002 traces PL-061. PA-013 laundry |
| PL-062 | Implementation-autonomy metric counts manual engineering and failed eligible builds (§25) | E01-S01, E01-S05, E01-S06, E01-S07, E10-S07, E24-S08, E24-S09 | P0 | Artifact inspection only | EIH/VD is the north star (D10). PA-027 at P6; PA-P13 raises it to HIGH for any release marketed as autonomously implemented |
| PL-063 | First milestone proves automatic construction; the next proves reproduction with labor accounted (§26) | E24-S01, E05-S06, E07-S03, E08-S07, E07-S05, E24-S08, E24-S09 | P0 | Artifact inspection only | Governance at P0; first half at M1 (P2, PA-001); second half at M1R (P3), pulled forward from the §26 M5 slot (D5). PA-027 at P6 |

### 4.1 Where this backlog departs from the decision record, and why

The decision record is the source of truth; these are the places where its own text points two ways, and how this backlog resolves them. Items 1 to 7 change no decision; item 8 lists the corrections and amendments the [decision record](02-strategy-decisions.md) carries for founder ratification.

1. **Phase lists.** The phased plan lists no phase for 17 requirements: PL-012, PL-013, PL-026, PL-027, PL-028, PL-029, PL-030, PL-031, PL-032, PL-033, PL-034, PL-050, PL-051, PL-055, PL-056, PL-058 and PL-060. The matrix assigns each one, or marks it deferred with the reason.
2. **Work the record schedules earlier than its phase lists.** The record's P1 scope includes state-machine guards that call the checkers and a durable build ledger, yet PL-016 is listed from P2, PL-057 from P5 and PL-047 from P4. Collectors need monitors from P2 and the P4 shadow release needs an operating plan, yet PL-048 is listed only in P6. PA-002 (P4) traces PL-061, which is listed only in P6. The matrix follows the scope.
3. **Read-step maturity.** D3 (a) says DOCUMENTED for read steps, while the P1 exit evidence asks for SANDBOX_TESTED receipts for `list_folder_changes`, `fetch_document` and ledger-metadata reads. E02-S04 targets SANDBOX_TESTED for those named reads (PA-001's precondition) and the DOCUMENTED floor for other reads.
4. **PA-021 adaptation timing.** D4 requires it "whenever document contents are parsed; mandatory by M3-lite", but the P2 exit evidence omits it. E06-S06 is P4, and moves to P2 if M1 parses contents.
5. **Maintenance agent.** D3 keeps it out for 180 days, while P6 lists PL-049. The backlog reads P6 as change-plan repair of schema drift (the PA-016 adaptation) with logged manual operations before it, and keeps the agent itself past P6 (E22-S06).
6. **Gaps found while verifying the code, not named in the record.** The COLLECTOR machine has no PAUSED or DEGRADED edge from SHADOW, BACKFILLING or RECONCILING (E08-S06). `ResourceScope` scopes whole sources (plus destinations, processors and regions), so excluding tax-return folders inside a document store needs a new field (E18-S02). Plumb staff have no principal type (E01-S02, also raised in the [MVP scope](03-mvp-scope.md)).
7. **Maturity floors beyond the record's list.** D3 and P0 name integration.configure, collection.backfill and collection.enable_incremental (SANDBOX_TESTED) and release.* and infrastructure.apply (PRODUCTION_VERIFIED) as the steps a truthful registry blocks. Running the checker shows workflow.compile, dataset.build, training.submit and integration.generate_adapter are blocked too, because every non-shadow INTERNAL_WRITE step has the SANDBOX_TESTED floor. workflow.compile matters for P4 (E13-S04) and integration.generate_adapter for P3 (E07-S05). The record's qualification run covers release.create and release.activate_shadow but not infrastructure.apply, which the accounting fixture's release depends on; E16-S02 makes that choice explicit.
8. **Corrections and amendments applied.** M1 and the Prepare tier use the READ, INTERNAL_WRITE and EXTERNAL_WRITE_REVERSIBLE effect classes (connector setup and enabling incremental capture on the firm's own accounts) and never EXTERNAL_COMMUNICATION; the record's "only READ and COLLECT effect classes" is an error, because COLLECT is a data purpose (E04-S01). The D6 materiality trigger reads "Presence UNKNOWN, or fact status STALE" (E15-S06). The effort rubric follows the amended D6 (founder decision 18; E01-S01, E01-S04, E15-S05). Prepare-tier promotion and paid conversion follow founder decision 17, so E16-S07 is a P6 Must story. The P6 window (Apr-Jun 2027) covers the Prepare canary and ACTIVE closes, the Draft tier and the start of M5; the earliest Send canary close is around July 2027 (about weeks 39-41), because the D6 ladder needs at least two Draft closes. Only the accounting fixtures are EU/EUR and are re-templated to US/USD (E24-S03).

---

## 5. Icebox: explicitly not now

Each item is out of the plan for at least 180 days, or for good. "Reopened by" names the evidence that would bring it back (D3, D5, D8, D9, D12). Thresholds are hypotheses.

| Item | Why not now | Reopened by |
|---|---|---|
| Training, TrainingSpec execution and the learning factory beyond the prospective correction collector | Largest plan step (EUR 2,500 of EUR 10,060); PA-012 does not need it; training rights are scarce; the trained path can lose on total cost (spec §14) | All four D5 M2 entry gates, read in the M2 go/no-go memo (E21-S01) |
| Transaction categorization | Not the wedge goal (missing evidence plus the package) | The baseline shows categorization dominates accountant time, TRAIN grants exist on at least 2 tenants and at least 500 explicit corrections show classification errors at 25% or more of review minutes (D3) |
| Screen or visual capture | About 34.6 GB/day raw per 100 employees (spec §24); experiment 1 unresolved (spec §27) | More than 20% of obligations stay UNKNOWN after two closes because of off-system handoffs, or the experiment-1 proxy is positive (E12-S06); then a consented, event-triggered pilot after M5 |
| Posting and any FINANCIAL_COMMITMENT | Accountant sign-off is mandatory; posting is a separate capability excluded unless specifically granted (spec App. B) | A new envelope decision by the Firm owner, never a silent widening |
| "Autonomous close", "fully autonomous", "AI employee" or "zero human" in any wording | A review-ready package is not an autonomous financial close (spec §15); never-claim checklist (D8) | Not reopened |
| Open-ended opportunity discovery | Replaced by a vertical library with complete OpportunitySpecs and native-feature baselines (E12) | D3 revisit triggers |
| UI adapters | Last in PL-020's preference order; highest maintenance exposure | A specifically supported adapter on an explicit allowlist, with its maintenance exposure priced |
| Generic infrastructure generation | Fixed approved templates only (PL-045) | Not in the 180-day plan |
| The maintenance agent | Ops stay manual and logged (E22-S02) | After P6, once change-plan repair (E22-S04) has run on accounting sources (E22-S06) |
| Tax-return information in any source | IRC 7216 consent obligations (secondary commentary; counsel to confirm, D9) | Counsel confirms monthly-close sources are outside 7216; then only those sources |
| Multi-region, on-prem, desktop ledgers, NetSuite and Intacct | One US region; D1 qualify-outs | Not in the 180-day plan |
| Second domains (M6: laundry route preparation, then RFQ) | Platform verdict first (E23) | M5 evidence, then PA-013, PA-025, PA-029 and PA-030 |
| Draft and Send before day 180 | A mailbox draft is an external write; the gateway is not built (D3) | At least 2 of 3 partners make reminders a condition of continuing; even then PA-005, PA-007, PA-009 and PA-010 are never skipped |
| Customer editing of plans, mappings or workflows | The normal interface never requires editing a DAG (spec App. A §6); any edit, by Plumb or firm staff, is ENGINEERING_INTERVENTION | Not reopened for the normal interface |
| A surface for the firm's clients | The client is an affected party, not a principal | Send tier, and then only messages under the approved policy |
| Integrations outside supported environments v1 | Coverage is stated per operation at its maturity (D8) | A probe receipt for the operation on the customer's account (E02) |
| A logo-wall integration page | Never-claim item 8 (D8) | Not reopened |
| Exact-unlearning promises | Spec §20 | Not reopened |
| Per-customer delivery engineers, and human-built deliverables on partner data before the M1 isolation subset and PA-019 pass ("Disclosed-Labor Mode") | Their time is ENGINEERING_INTERVENTION by definition, the services trap (D12); rejected in the record's dissent | Not reopened |
| Hourly or per-seat billing features | Rewards hidden labor; fights the firm's tech budget (D7) | D7 revisit triggers (for example, firms strongly preferring flat fees move to per-client tiers, not seats) |
| Broad daily re-evaluation of every model on every customer | Neither necessary nor economical (spec §20) | Not reopened; targeted re-evaluation only (E12-S07) |
| SOC 2, FTC Safeguards Rule work and Google restricted-scope verification as product scope | Not in the spec or the research notes; kept as "counsel or compliance to confirm" (decision record dissent) | Counsel or the compliance lead confirms a requirement |
| Roll-up channel features | One optional slot off the critical path (D1, D9) | R5 fires and the roll-up channel becomes primary |

---

## Related documents

- [Product brief](01-product-brief.md): problem, personas, principles and where the package stands today.
- [Strategy decisions](02-strategy-decisions.md): D1 to D12, the phased plan, the north star and the top risks.
- [MVP scope](03-mvp-scope.md): surface specifications, the proposed ReviewPackage contract, supported environments v1 and the gap list these stories close.
- [Roadmap](04-roadmap.md): phase windows, exit evidence and the numbered proposed scenarios.
- [Metrics](06-metrics.md): EIH/VD, accepted review packages per month and supporting metrics.
- [Risks and assumptions](07-risks-and-assumptions.md): R1 to R7 with kill and pivot criteria.
- [Market and positioning](08-market-and-positioning.md): category, competitors and the never-claim checklist in context.
- [Design-partner program](09-design-partner-program.md): partner selection, contract essentials and obligations.

