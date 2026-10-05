# MVP Scope and Product Definition

- Status: Draft v0.1 (2026-10-04), proposed — requires founder ratification
- Owner: Product
- Basis: spec v0.2, [decision record](02-strategy-decisions.md)

Part of the product doc set ([index](README.md)). This document defines what the first design-partner deployment contains, how a firm moves through it, what each product surface must do, and what "done" means. It follows decisions D2, D3, D4 and D6 in the [decision record](02-strategy-decisions.md). Why the product exists and who it serves is in the [product brief](01-product-brief.md); sequencing and dates are in the [roadmap](04-roadmap.md); stories are in the [backlog](05-backlog.md); metric definitions are in [metrics](06-metrics.md).

Three kinds of statement appear, labeled where it matters:

| Label | Meaning |
|---|---|
| Spec requires | Normative text in [spec v0.2](../spec/Plumb_Autonomous_Implementation_Specification_v0.2.md), cited as "spec §N" or by requirement id. |
| Package has | Code in the reference package today: a local library checked by the local contract tests (counts in [VALIDATION_REPORT](../VALIDATION_REPORT.md); the spec's "56 tests" figure in its header table and Appendix C is stale). Nothing is deployed, connected to a customer or measured, and the tests do not validate models, business outcomes, tenant security, cloud isolation or third-party integrations (spec §28). |
| Proposed | This document's proposal, derived from the decision record. Not yet ratified. |

Every threshold, budget, price and date below is a hypothesis unless the spec states it. Each table says so once.

---

## 1. The MVP in one paragraph

The MVP is the **Prepare tier** (preparation-only, run in production shadow within the MVP) of **monthly-close evidence readiness**, delivered first to one design-partner accounting firm (tenant 1) and then reproduced on tenants 2 and 3 (D2, D3). Plumb connects the firm's ledger and document store through certified transport connectors, has its agent fill in the build plan and generate the client/period/obligation mapping, backfills 12-24 months of history, and keeps a **read-only close-readiness ledger**: for every recurring client-period, each required item is shown as PRESENT, CONFIRMED_ABSENT or UNKNOWN, with its provenance and, once mail history is connected, who already chased it. From P4 the same evidence feeds a preparation-only workflow that assembles **one verifier-attested, ready-for-review package per client-period** in production shadow. The reviewing accountant explicitly accepts, corrects or amends each package. The allowed effect classes are READ, INTERNAL_WRITE and EXTERNAL_WRITE_REVERSIBLE (connector setup and enabling incremental capture on the firm's own accounts, as in the accounting fixture), never EXTERNAL_COMMUNICATION. Nothing is sent to the firm's clients, nothing is posted to a ledger, no model is trained, and every human minute, the firm's and Plumb's, lands on a customer-visible ledger in five categories. The first measurable customer deliverable is attested packages on at least 30 client-periods in one full live close, compared against the firm's own month-0 time study (D2; P5 exit).

**What the firm gets in the MVP**

- A read-only close-readiness ledger that never shows "unknown" as "missing" (P2).
- A historical duplicate-chase baseline from 24 months of mail history, labeled historical and non-causal (P4).
- Ready-for-review packages in production shadow with a "what Plumb would have done" report against the accountants' actual decisions (P4-P5).
- A results-and-effort view with denominators, the five-category human-effort ledger and verification receipts (P2 effort; P5 package results).
- Ownership and export of every spec, test, evidence record, package and ledger entry (D9).

**What the firm does not get in the MVP**

- No consolidated requests to clients, as mailbox drafts or sends. Those are the Draft and Send tiers, gated on a production action gateway after day 180; the earliest Send canary close is around July 2027 (D3, D5, D6).
- No posting, no "autonomous close", no transaction categorization, no training, no screen capture, no tax-return data (section 9).

---

## 2. Scope by phase

D3 groups scope as "M0/M1", "phase 2 (M3-lite)" and "phase 3 (gated)". Mapped to the phased plan:

| D3 group | Phases | Milestones |
|---|---|---|
| IN for M0/M1 (tenant 1) | P0 Commit and instrument; P1 M0; P2 M1 | M0, M1 |
| Same scope reproduced | P3 M1R | M1R on tenants 2 and 3 |
| IN for phase 2 | P4 M3-lite | M3-lite |
| Gated, phase 3 | P5 shadow results + gateway hardening + day-180 decision (sandbox hardening only); P6 M4-accounting and M5 (release; the earliest Send canary close is around July 2027, after the P6 window) | M4-accounting, M5 |
| OUT for 180 days | none | M2 (gated learning factory) and M6 (second domain: laundry route preparation, then RFQ) are gated |

### 2.1 IN for P1-P2 (M0 and M1, tenant 1)

Every item is on the PL-063 critical path or protects it (D3).

| # | Item (D3) | Why it is in | Requirements | Package has today |
|---|---|---|---|---|
| a | EnvironmentInventory from real probes of document-store and ledger-metadata operations; a truthful registry that earns SANDBOX_TESTED probe receipts on tenant 1's real accounts for integration.configure, collection.backfill and collection.enable_incremental; DOCUMENTED for read steps, except that the P1 exit (and PA-001's preconditions) need SANDBOX_TESTED receipts for list_folder_changes, fetch_document and ledger-metadata reads | The plan checker's floor for non-shadow writes is SANDBOX_TESTED, so no plan can run on a truthful registry without these receipts. M0 evidence is "exact source operations are accessible" (spec §26) | PL-007, PL-008 | EnvironmentInventory and CapabilityRecord contracts; maturity floors in the plan checker; registry maturity is synthetic |
| b | Agent fills in the tenant BuildPlan from a registry template; check_plan wired to the tenant EnvironmentInventory and capability required_authority; state-machine guards call the checkers | M1 requires that the agent, not a person, produced the plan (D4). Today a plan can pass for an account that was never probed | PL-014, PL-015 | check_plan with 23 finding codes; no inventory input; guards are caller-asserted booleans |
| c | Durable build ledger and bounded repair | Restart without redoing verified effects; repair that cannot weaken tests or widen permissions | PL-017, PL-018 | BUILD and BUILD_STEP state machines; no ledger service |
| d | Integration factory: certified transport through a contract-tested substrate (Nango is the candidate); agent-generated semantic mappings (folder and naming conventions to client + period + obligation; chart-of-accounts conventions) as declarative config or generated code in a disposable sandbox | PL-020's preference order says reuse certified transport; tenant variation lives in semantics, so semantics must be agent-built (D3, D4) | PL-019, PL-020, PL-021, PL-022, PL-054 | IntegrationSpec contract with the 8 contract-test families; no adapters, no sandbox |
| e | Collection factory: shadow, backfill from an agreed watermark, reconcile, incremental, health | The collection path is the M1 artifact and the first customer value | PL-023, PL-024, PL-025 | CollectionSpec contract; no collector runtime |
| f | Evidence store with three time axes, fact status and scoped corrections | "Unknown is not absent" is the product's core promise | PL-009, PL-010, PL-011 | EvidencePacket contract, Presence and FactStatus enums; SQL design only |
| g | Thin independent verifier and the fault-injection harness | Nothing is "verified" without an attestation; most HIGH scenarios need fault injection | PL-042 | VerificationAttestation contract and release checker; no verifier service (ADR-007) |
| h | Effort accounting: a human-effort ledger that captures every human-principal action on tenant resources automatically; a separate platform-investment ledger; the autonomy metric | EIH/VD is the north star and must be measurable from the first M1 build | PL-003, PL-059, PL-062 | HumanEffortCategory enum; HumanEffortRecord model that nothing uses; no capture API (ADR-010) |
| i | Tenant isolation for database, API, object storage, cache, logs and exports | Tenant data is co-resident from M1 | PL-052 | Row-level security design in SQL, never executed |
| j | Minimum surfaces: the App. A §6 implementation card, blocked-dependency card, honest progress feed and results-and-effort view, plus the read-only close-readiness ledger (D2; not an App. A §6 surface) | The customer must see the work without editing a DAG; the ledger is the interim deliverable (D2) | PL-001, PL-005, PL-041 | None; no UI and no API object for any surface |
| k | Published "supported environments v1" list, per operation and maturity level | PL-002 applies "for supported environments", which the spec does not enumerate | PL-002, PL-007, PL-008 | None |
| l | Focused-question queue with a per-workflow budget | Missing business decisions must not stop unrelated work or turn into constant interruption | PL-041, PL-010 | None |

Proposed addition, derived from D6: a minimal **approvals inbox** for DATA_USE and IMPLEMENT_OPERATE decisions in P1-P2. The envelope, the source grants and the implementation card all need an authenticated place where the owner decides (section 4.6).

**P3 M1R** adds no product scope. It re-runs the same engine on tenants 2 and 3 with no code fork. Tenant 2 varies folder structure and chart-of-accounts conventions; tenant 3 swaps one provider so that at least one operation runs on a DECLARATIVE_CONFIG or GENERATED_CODE path (D3, D4). Until M1R passes, the claim is "agent-configured certified connectors and agent-built collection", never "automatically constructed" (D8).

### 2.2 IN for P4 (M3-lite)

| Item (D3) | Why it is in | Requirements | Package has today |
|---|---|---|---|
| Read-only mail history | Chase history in the ledger and the 24-month duplicate-chase baseline (D2) | PL-023, PL-053 | Mailbox grant in the fixture envelope (INSPECT, COLLECT only) |
| Preparation-only WorkflowSpec over certified primitives: deterministic obligation checks, engagement-checklist templates, general-model extraction through the gateway; no training | Produces the package. PL-035 separates read-only preparation from external effects | PL-035, PL-036 | WorkflowSpec contract; the accounting fixture's workflow step depends on a training step (section 7) |
| ReviewPackage contract (none exists today) | The thing the accountant reviews, the verifier attests and the firm pays for is undefined | PL-001, PL-010 | ArtifactKind value only (section 5) |
| Accountant sign-off surface with explicit accept/correct/amend capture | It doubles as the prospective correction collector and keeps the ADR-006 option open cheaply | PL-027, PL-040, PL-059 | ApprovalRecord supports CASE_LEVEL_BUSINESS with a case version; SQL `cases.review_state` |
| Narrow release executor on fixed approved templates, plus a platform qualification run that earns real PRODUCTION_VERIFIED receipts for release.create and release.activate_shadow before any tenant shadow | release.* steps have a PRODUCTION_VERIFIED floor, so shadow cannot start without it | PL-045, PL-046 | ReleaseManifest contract and release checker; no executor |
| Pause and kill from SHADOW and CANARY | Today the RELEASE machine allows PAUSED only from ACTIVE | PL-047 | State machine edge missing (section 7) |
| Explicit SERVE grant before the first shadow | No fixture envelope grants SERVE, yet every fixture plan passes | PL-053 | Not enforced (section 7) |

**After the MVP: Prepare-tier promotion (founder decision 17 in the [decision record](02-strategy-decisions.md), to ratify).** The preparation-only release goes SHADOW (at least one full close), then CANARY on a subset of client-periods whose accountants use the prepared packages in their real review, then ACTIVE, with no EXTERNAL_COMMUNICATION at any stage. A partner converts to paid annual after one full close in ACTIVE at or above the correct-package threshold (D7, D9). Tenant 1 is still in SHADOW at day 180, so the day-180 packet records its evidence to date and its conversion is expected in P6. Package gaps on this path: every `release.*` step needs PRODUCTION_VERIFIED, so the canary step must be qualified too (the registry's `release.canary` record is synthetic and the fixture's canary step is EXTERNAL_COMMUNICATION); the registry has no step type for promotion to ACTIVE, although the API proposal has `activateRelease`.

### 2.3 Gated (D3 phase 3): production action gateway, Draft, Send

Not part of the MVP. P5 hardens the gateway in sandbox only; release is P6, after day 180 (D3, D5).

| Item | Gate before it ships | Requirements | Earliest phase |
|---|---|---|---|
| Production action gateway: outbox, leases, dispatch-time authority, revocation and pause checks | Sandbox crash tests in P5 for draft creation and sends: PA-005's dispatch-time re-check, PA-009 (as written for sends) and PA-015's lease-and-fencing checks re-run on dispatch workers (a mechanism re-run, not a PA-015 result); pause and kill from SHADOW and CANARY | PL-037, PL-038, PL-039 | P5 (sandbox), P6 (production) |
| Draft tier: consolidated request created in the firm's mailbox, sent by staff | A mailbox draft is an EXTERNAL_WRITE_REVERSIBLE effect: SANDBOX_TESTED maturity, effect-slot dedup and the production effect ledger. Draft release passes PA-005's dispatch-time re-check, PA-009 and PA-015 behaviors, PA-006 and PA-010 approval binding, and pause and kill from CANARY (D4) | PL-037, PL-040, PL-047 | P6 |
| Send tier: policy-approved canary of consolidated requests | Full PA-002 in canary, PA-005, PA-007, PA-009, PA-010, plus accounting adaptations of PA-014 and PA-016, a recovery drill and recorded support effort (D4). Each client and obligation type graduates through the D6 calibration ladder, which needs at least two Draft closes | PL-037, PL-038, PL-039, PL-040, PL-061 | P6 at the earliest; the first Send canary close is around July 2027 (about weeks 39-41), after the "Apr-Jun 2027" P6 window, which covers the Draft tier and the start of M5 |

### 2.4 OUT for 180 days

Follows D3 exactly. The single list, with reasons, affected requirements and reopen triggers, is in section 9.

### 2.5 Generated vs certified paths

Follow PL-020's preference order and reuse certified transport. Require tenant-specific semantics (client/period/obligation mapping, chart-of-accounts conventions) to be agent-generated, as declarative config or generated code. Swap one provider at tenant 3 so a non-VERIFIED_ADAPTER path runs, with PA-026 and PA-019 re-run on it, before any "automatically constructed" claim (D3, D4). If tenant 1's semantics map fully through declarative config, that is accepted as construction evidence and PA-026 moves to the first tenant where generated code runs (D4 revisit trigger).

---

## 3. End-to-end design-partner journey

Grounded in spec Appendix B, adapted to the Prepare tier. Appendix B is a synthetic acceptance trace, not an execution log; nothing below has happened yet.

**How Appendix B maps to the MVP**

| Appendix B stage | MVP treatment |
|---|---|
| Goal and authority | Steps 2-3. Posting excluded. The reminder policy is not requested in Prepare |
| Discovery and integration | Steps 5-8 |
| Collection apparatus | Steps 8-10. Shared obligation ownership is visible historically (step 11); one owner per send waits for the Send tier |
| Find and construct the learning data | Out, except the prospective correction collector inside the review surface (step 15) |
| Choose and construct the working solution | Step 13: deterministic checks and general-model extraction compared on errors and review time; no trained candidate; native-feature baseline in the OpportunitySpec |
| Test, deploy, operate and improve | Steps 13-14: protected verifier and shadow. The preparation-only canary and ACTIVE follow in P6 (step 17); sends, send canaries and UNKNOWN reconciliation of real sends are gated |
| Success and its denominator | Step 16 |
| Expansion test | P3 M1R (collection path) and P6 M5 (full workflow) |

### 3.1 Summary

Phase windows are hypotheses from the phased plan.

| # | Step | Phase | Primary actor | Effort category logged | Key artifacts |
|---|---|---|---|---|---|
| 1 | Qualify and sign | P0-P1 | Firm owner | None (pre-tenant, commercial) | Contract, DPA (outside the artifact store) |
| 2 | Authorize the envelope | P1 | Firm owner | CUSTOMER_AUTHORIZATION | AutonomyEnvelope, ApprovalRecord (DATA_USE) |
| 3 | Connect accounts | P1 | Firm owner | CUSTOMER_AUTHORIZATION | Connection intent, DependencyRecord if blocked |
| 4 | Month-0 baseline time study | P1 | Reviewing accountant, Plumb domain expert | DOMAIN_CLARIFICATION (firm participants' recording overhead) | Baseline study record (proposed) |
| 5 | Inventory and probe | P1 | Plumb (agent) | None expected | EnvironmentInventory, ProbeReceipt, CapabilityRecord |
| 6 | Focused questions on conventions | P1-P2 | Firm owner, Reviewing accountant | DOMAIN_CLARIFICATION | Versioned conventions (proposed) |
| 7 | Plan and implementation card | P2 | Firm owner | CUSTOMER_AUTHORIZATION | BuildPlan, ApprovalRecord (IMPLEMENT_OPERATE) |
| 8 | Build the integration-and-collection path | P2 | Plumb (agent) | None expected; any implementation act by a person, Plumb or firm staff, is ENGINEERING_INTERVENTION | IntegrationSpec, AdapterConfiguration, TestBundle, CollectionSpec, EvidencePacket, QualityReport, VerificationReceipt |
| 9 | Verified live event (the M1 moment) | P2 | Independent verifier | None | VerificationAttestation, EvidenceEvent |
| 10 | Read-only close-readiness ledger in use | P2 onward | Bookkeeper, Reviewing accountant | None required | EvidencePacket facts |
| 11 | Connect mail history | P4 | Firm owner | CUSTOMER_AUTHORIZATION | ApprovalRecord (DATA_USE), CollectionSpec, baseline report |
| 12 | Workflow implementation card and SERVE grant | P4 | Firm owner | CUSTOMER_AUTHORIZATION | ApprovalRecord (IMPLEMENT_OPERATE), ApprovalRecord (DATA_USE), AutonomyEnvelope |
| 13 | Compile and attest in sandbox | P4 | Plumb (agent), Independent verifier, Plumb domain expert | NORMAL_BUSINESS_REVIEW (sandbox reviewer); any workflow authoring by a person is ENGINEERING_INTERVENTION | WorkflowSpec, TestBundle, ReleaseManifest, VerificationAttestation, ReviewPackage (sandbox) |
| 14 | Production shadow | P4-P5 | Plumb | None required | ReleaseManifest (SHADOW), ReviewPackage, VerificationAttestation, shadow report |
| 15 | Review and sign-off, every close | P4-P5 | Reviewing accountant | NORMAL_BUSINESS_REVIEW | ReviewPackage versions, ApprovalRecord (CASE_LEVEL_BUSINESS) as sign-off record |
| 16 | Results after the first full close | P5 | Firm owner, Reviewing accountant | None | Results report, outcome records |
| 17 | Promotion to ACTIVE and pilot-to-paid (after the MVP) | P6 | Firm owner, Reviewing accountant | NORMAL_BUSINESS_REVIEW (canary packages); conversion itself is commercial | ReleaseManifest (CANARY, ACTIVE), annual contract |
| 18 | Revocation or exit | Any | Firm owner | CUSTOMER_AUTHORIZATION | New envelope version, export bundle |

### 3.2 Step detail

**Step 1. Qualify and sign** (P0-P1)
- Actor: Firm owner (buyer). Plumb founder runs sales (D12).
- Sees/does: a qualification call against the D1 profile and qualify-outs; names a domain owner with about 2 hours a week and a reviewing accountant; signs the DPA and pilot (paid pilot of $1,500-$3,000 by firm size, invoiced at signature, hypothesis, D7); agrees to the 2-week baseline study and anonymized publication of labor-ledger data (D9).
- Plumb does: assigns a slot in the stack-variation matrix; confirms the providers meet the catalog assumptions (document store with webhooks plus overlap polling; mail with request-id lookup; provider sandboxes).
- Artifacts: contract and DPA, held outside the artifact store.
- Effort: not a tenant-ledger entry; tracked as a funnel metric.
- Ids: none (D1, D7, D9).

**Step 2. Authorize the envelope** (P1)
- Actor: Firm owner as HUMAN_OWNER.
- Sees/does: a plain-language envelope summary and one DATA_USE request per source in the approvals inbox. Approves: the goal and its success measure; per-source purposes INSPECT, COLLECT, TRANSFORM and EVALUATE (TRAIN off and not requested; SERVE deferred to step 12); destination (tenant storage); processors; US region; spending cap and escalation trigger; allowed effect classes READ, INTERNAL_WRITE and EXTERNAL_WRITE_REVERSIBLE, the last only for connector setup and enabling incremental capture on the firm's own accounts (no EXTERNAL_COMMUNICATION, no FINANCIAL_COMMITMENT); tax-folder exclusions; expiry.
- Plumb does: records each decision as an approval bound to the envelope digest and policy version; never infers TRAIN from read access.
- Artifacts: AutonomyEnvelope; ApprovalRecord (DATA_USE).
- Effort: CUSTOMER_AUTHORIZATION (onboarding budget: at most 2 hours, hypothesis, D6).
- Ids: PL-004, PL-005, PL-040, PL-053.

**Step 3. Connect accounts** (P1)
- Actor: Firm owner, or the firm's account administrator.
- Sees/does: completes OAuth consent per account in the provider's own flow; Plumb never bypasses vendor approvals or MFA.
- Plumb does: creates a connection intent per account. If an account is inaccessible or a vendor app review is pending, it raises a blocked-dependency card naming the scope, the resolver and what resumes, and continues unrelated work.
- Artifacts: connection intent (API-level only today); DependencyRecord when blocked.
- Effort: CUSTOMER_AUTHORIZATION.
- Ids: PL-006, PL-041. Watch item: if ledger authorization is granted per client company, onboarding authorization may exceed 4 hours per firm, which triggers a D1 re-scope.

**Step 4. Month-0 baseline time study** (P1, finished before shadow; 2 weeks)
- Actor: Reviewing accountant and staff; Plumb domain expert facilitates.
- Sees/does: records assembly-plus-review minutes per client-period on a sample of client-periods.
- Plumb does: stores the baseline with its denominator so later time claims can be falsified (D2).
- Artifacts: baseline study record (proposed; no contract exists).
- Effort: the firm participants' recording overhead is DOMAIN_CLARIFICATION (D6 rubric as amended, founder decision 18). The Plumb domain expert's facilitation is Plumb staff time that the rubric does not place, and Plumb staff have no principal type today; see open questions 5 and 6.
- Ids: PL-059.

**Step 5. Inventory and probe** (P1)
- Actor: Plumb build agent; Firm owner watches the progress feed.
- Sees/does: a progress line such as "Accounts probed: 2 of 2. Operations tested on your accounts: <n>" (illustrative copy).
- Plumb does: tests the exact operations on each account (list folder changes, fetch document, ledger metadata reads); identifies client ids, periods, folders and request status; checks whether an engagement checklist can be inferred. Earns SANDBOX_TESTED receipts on tenant 1's real accounts for the collector writes (section 6). A test that reads an invoice does not establish access to bank statements (spec App. B).
- Artifacts: EnvironmentInventory; ProbeReceipt; updated CapabilityRecords.
- Effort: none expected. Any wiring by a person, Plumb or firm staff, is ENGINEERING_INTERVENTION.
- Ids: PL-002, PL-007, PL-008; PA-022 (forged tool descriptions grant nothing).

**Step 6. Focused questions on conventions** (P1-P2)
- Actor: Firm owner (firm conventions) and Reviewing accountant (attribution examples).
- Sees/does: answers focused questions in the queue, for example how folders map to clients, how statements spanning a month boundary are attributed, or which items each client type owes.
- Plumb does: continues unrelated work; stores each answer as a versioned convention applied to future cases.
- Artifacts: versioned conventions (proposed; no contract exists).
- Effort: DOMAIN_CLARIFICATION (at most 5 questions per workflow at onboarding, hypothesis, D6).
- Ids: PL-010, PL-011, PL-041; PA-003, PA-004 patterns.

**Step 7. Plan and implementation card** (P2)
- Actor: Firm owner.
- Sees/does: the implementation card for the collection path (section 4.1). Approves IMPLEMENT_OPERATE once and confirms the backfill watermark (proposed placement).
- Plumb does: the agent fills in the BuildPlan from a registry template using the EnvironmentInventory; check_plan, wired to the inventory and required_authority, must pass first.
- Artifacts: BuildPlan; ApprovalRecord (IMPLEMENT_OPERATE).
- Effort: CUSTOMER_AUTHORIZATION.
- Ids: PL-005, PL-014, PL-015, PL-040, PL-041, PL-058.

**Step 8. Build the integration-and-collection path** (P2)
- Actor: Plumb build agent; Firm owner watches the progress feed.
- Sees/does: progress lines such as "Folder conventions mapped to <n> clients", "History loading from <watermark>", "Counts reconciled: 0 gaps" (illustrative copy).
- Plumb does: configures certified transport connectors (VERIFIED_ADAPTER path); generates the client/period/obligation mapping and CollectionSpec in a disposable sandbox; runs contract tests (pagination, empty pages, duplicates, rate limiting, authorization failure, malformed responses, schema changes, account boundaries); deploys a shadow collector; backfills from the watermark; reconciles source counts; enables incremental capture.
- Artifacts: IntegrationSpec; AdapterConfiguration (or AdapterCode); TestBundle; VerificationReceipt; CollectionSpec; EvidencePacket; QualityReport.
- Effort: target zero ENGINEERING_INTERVENTION. Any human-authored or human-edited plan or mapping, by Plumb or firm staff, is logged as ENGINEERING_INTERVENTION, and every failed eligible attempt is counted: its minutes in the EIH/VD numerator, the attempt itself in the hands-off build rate's denominator (D4, D10).
- Ids: PL-016, PL-017, PL-018, PL-019, PL-020, PL-021, PL-022, PL-023, PL-024, PL-025, PL-054; PA-015, PA-019, PA-026 (if generated code ran).

**Step 9. Verified live event: the M1 moment** (P2)
- Actor: Independent verifier. A firm staff member adds a document outside Plumb.
- Sees/does: the progress feed shows "Collector verified: a statement added at 10:02 appeared at 10:04, filed to <client>, June 2026" (illustrative copy), with the attestation receipt.
- Plumb does: the verifier observes the event, confirms the authoritative content was fetched and the client/period record changed, within the 5-minute health deadline, and attests. A deployment response without the observed event does not pass (PA-001).
- Artifacts: VerificationAttestation (INTEGRATION_BEHAVIOR level); EvidenceEvent with lineage to the IntegrationSpec, CollectionSpec and build-step digests.
- Effort: none (CUSTOMER_AUTHORIZATION entries are allowed; any ENGINEERING_INTERVENTION fails PA-001).
- Ids: PL-002, PL-009, PL-042, PL-063; PA-001 plus the M1 safety bundle (section 8). The 90-day pilot clock starts here (D7).

**Step 10. Read-only close-readiness ledger in use** (P2 onward)
- Actor: Bookkeeper and Reviewing accountant.
- Sees/does: open the ledger per client-period to see what is held, what is confirmed absent and what is unknown (section 4.4). No request or send controls.
- Plumb does: keeps the ledger current from incremental capture; shows collector health; turns a stale source into "Unknown", never "Missing".
- Artifacts: EvidencePacket facts and object resolutions.
- Effort: none required. A correction goes through the focused-question queue (DOMAIN_CLARIFICATION).
- Ids: PL-010, PL-024, PL-025; PA-005 (collector half), PA-011 (health half).

**Step 11. Connect mail history** (P4)
- Actor: Firm owner.
- Sees/does: one DATA_USE request for INSPECT and COLLECT on the mailbox.
- Plumb does: backfills 24 months of reminder history; adds "who chased, when" to the ledger; produces the historical duplicate-chase baseline (duplicate chases per client-period-obligation, re-requests for documents already held, days to receive), labeled historical and non-causal and never counted as a PL-001 outcome (D2, spec §7). If mailbox scopes are refused or vendor approval is late, fall back to document store plus ledger with a forwarding-address intake (R7).
- Artifacts: ApprovalRecord (DATA_USE); mail CollectionSpec; EvidencePacket; baseline report.
- Effort: CUSTOMER_AUTHORIZATION.
- Ids: PL-023, PL-053.

**Step 12. Workflow implementation card and SERVE grant** (P4)
- Actor: Firm owner.
- Sees/does: one batched session: the implementation card for the preparation-only workflow (packages prepared inside Plumb, no messages, no ledger writes) and a DATA_USE request for SERVE on each source the workflow reads, required before the first shadow.
- Plumb does: batches both into that session; `group_missing_authorizations` groups per resolver and error class, so they may remain two requests within it.
- Artifacts: ApprovalRecord (IMPLEMENT_OPERATE); ApprovalRecord (DATA_USE); new AutonomyEnvelope version.
- Effort: CUSTOMER_AUTHORIZATION.
- Ids: PL-040, PL-041, PL-053.

**Step 13. Compile and attest in sandbox** (P4)
- Actor: Plumb build agent; Independent verifier; Plumb domain expert; a reviewer on the authenticated review surface (PA-002 precondition).
- Sees/does: the firm sees progress only. The domain expert sets the numeric correct-package threshold.
- Plumb does: compiles the preparation-only WorkflowSpec from certified primitives (deterministic obligation checks, engagement-checklist templates, general-model extraction through the gateway); runs the protected verifier against the Appendix B failure set; runs PA-002 as written in sandbox, whose single send goes only through the sandbox mail adapter against sandbox copies; creates the release on the qualified release executor.
- Artifacts: WorkflowSpec; TestBundle; VerificationAttestation (BUSINESS_OUTCOME level); ReleaseManifest; sandbox ReviewPackages.
- Effort: NORMAL_BUSINESS_REVIEW for the sandbox reviewer (proposed; open question 5 if the reviewer is Plumb staff). Workflow authoring or editing by any person, Plumb or firm staff, is ENGINEERING_INTERVENTION.
- Ids: PL-035, PL-036, PL-042, PL-043, PL-044, PL-045, PL-046, PL-061; PA-002, PA-003, PA-004, PA-006, PA-008, PA-010, PA-011, plus the accounting adaptation of PA-021's parser bounds.

**Step 14. Production shadow** (P4-P5)
- Actor: Plumb; Firm owner can pause or kill.
- Sees/does: packages appear in the review surface per eligible client-period, marked "ready for review", plus a "what Plumb would have done" report listing the requests it would have prepared, compared with what the accountants actually did.
- Plumb does: runs the release in SHADOW on live inputs with no EXTERNAL_COMMUNICATION in the envelope; attests each package before showing it as ready.
- Artifacts: ReleaseManifest (SHADOW); ReviewPackage; VerificationAttestation per package; shadow report.
- Effort: none required beyond review.
- Ids: PL-016, PL-035, PL-047.

**Step 15. Review and sign-off, every close** (P4-P5)
- Actor: Reviewing accountant (HUMAN_REVIEWER or HUMAN_APPROVER).
- Sees/does: opens each package, checks every item's status and evidence, and explicitly accepts, corrects or amends; signs off (section 4.5).
- Plumb does: binds the sign-off to the package digest and case version; turns corrections into a new package version and, where they express a convention, a focused question; records review minutes.
- Artifacts: ReviewPackage versions; ApprovalRecord (CASE_LEVEL_BUSINESS) as the sign-off record; ScopedCorrection records.
- Effort: NORMAL_BUSINESS_REVIEW; DOMAIN_CLARIFICATION if a new convention question arises.
- Ids: PL-001, PL-010, PL-011, PL-040, PL-059; PA-002, PA-003, PA-006.

**Step 16. Results after the first full close** (P5)
- Actor: Firm owner and Reviewing accountant.
- Sees/does: the results-and-effort view (section 4.7): eligible client-periods, attested packages (target at least 30), packages accepted without material correction, correct-package rate against the threshold, accountant minutes against the month-0 baseline, false-chase rate and recall from the shadow report, failures and why they stopped, cost, and the five-category ledger.
- Plumb does: computes every rate with its denominator, exclusions included.
- Artifacts: results report (proposed); outcome records.
- Effort: none.
- Ids: PL-001, PL-003, PL-059, PL-062.

**Step 17. Promotion to ACTIVE and pilot-to-paid** (P6, after the MVP; founder decision 17, to ratify)
- Actor: Reviewing accountant (canary packages); Firm owner (conversion).
- Sees/does: after at least one full SHADOW close, the release moves to CANARY on a subset of client-periods whose accountants use the prepared packages in their real review, then to ACTIVE; no EXTERNAL_COMMUNICATION at any stage. After one full close in ACTIVE at or above the correct-package threshold, the owner converts to annual Prepare at $15 per active client-month with a 24-month price lock (hypothesis, D7). The day-180 packet records tenant 1's evidence to date; its conversion is expected in P6. The earliest credible renewal decision is about three closes after connection (D5).
- Plumb does: promotes only when the stage gate passes, with pause and kill available from SHADOW and CANARY; bills only client-months with an attested package, with the D7 credits.
- Artifacts: ReleaseManifest (CANARY, then ACTIVE); annual contract.
- Effort: NORMAL_BUSINESS_REVIEW for canary package review; the conversion itself is commercial.
- Ids: PL-001, PL-047.

**Step 18. Revocation or exit** (any time)
- Actor: Firm owner.
- Sees/does: revokes a grant or terminates on 30 days' notice at a close boundary (D9).
- Plumb does: invalidates cached grants and queued dispatches (target: within one minute, the bound PA-008 sets for an expired grant, applied to revocation by D9); revokes credentials; exports IntegrationSpec, CollectionSpec, WorkflowSpec, tests, evidence, packages and the labor ledger in open formats.
- Artifacts: new AutonomyEnvelope version; export bundle.
- Effort: CUSTOMER_AUTHORIZATION.
- Ids: PL-040, PL-041, PL-053; PA-008.

The firm's client is not a principal and appears in no step: in the Prepare tier Plumb never contacts them.

---

## 4. Product surfaces

**Rules shared by every surface (proposed; each traces to the spec):**

1. A state reads "verified" only when a VerificationAttestation exists for it. "Deployed", "configured" and "set up" describe work in progress, never completion (PL-016, PL-042; PA-001: a successful deployment response without the observed event does not pass).
2. Manual engineering is shown, never hidden: spec App. A §6 says to avoid statuses that obscure manual engineering work. Deployments are labeled "supervised", with labor shown, until that path has PA-027-level evidence (PL-003; D8).
3. The normal interface never requires editing a DAG, writing SQL or choosing a training container (spec App. A §6).
4. Every human-principal action on tenant resources writes an effort entry automatically (PL-003).
5. Copy never contains secrets, raw source content or another tenant's identifiers (spec §22).
6. Package has: none of these surfaces exists. There is no UI and no API object for any of them.

### 4.1 Implementation card

**Purpose.** One concise statement of an intervention before its build starts, so the owner decides once (spec App. A §6).

**Fields.** The first six come from spec App. A §6; the last two are proposed additions.

| Field | Content | Source | Illustrative example: tenant 1 collection path |
|---|---|---|---|
| What will change | Every change outside Plumb's own storage, in plain language | BuildPlan steps and effect classes | "Plumb registers change notifications on your client folders and starts copying document metadata and content into your Plumb storage. No file in your systems is edited, moved or deleted. Nothing is sent to anyone." |
| Systems and data it uses | Accounts, sources, purposes, fields, history depth, exclusions | EnvironmentInventory, envelope grants, CollectionSpec | "Document store (client folders, tax folders excluded); ledger (client list, chart of accounts, period metadata); history from the watermark you confirm (12-24 months). Purposes: inspect, collect, transform, evaluate." |
| Actions it may take | Allowed effect classes per operation, plus what it never does | BuildPlan, envelope `allowed_effect_classes` | "Read; write to Plumb storage; register and remove change notifications (reversible). Never: send messages, post to the ledger, change permissions." |
| Maximum spend and escalation trigger | One maximum, and the point at which Plumb stops and asks | BuildPlan `total_budget`, envelope `spending_limit` and `escalation_conditions` | "Up to $<plan budget> for this build, inside your $<cap> cap. Plumb stops and asks if projected worst-case spend passes 80% of the cap." |
| Expected benefit hypothesis | Baseline, expected change and how it is measured, stated as a hypothesis | OpportunitySpec (current-process and native-feature baselines, prospective measurement plan) | "Each document added to a client folder is filed to the right client and period within 5 minutes, with its source. Measured from the first verified event; not promised." |
| Owner decision needed | The decision type, its owner and what happens on approve or decline; or "none, proceeding under your envelope" | Approval checker decision kinds; DependencyRecords | "Implement and operate. Owner: you, as firm owner. Approve once for this version." |
| Done means (proposed) | The completion evidence the verifier will check | BuildPlan verification obligations | "A document added outside Plumb arrives once, correctly attributed, within the 5-minute health deadline (PA-001)." |
| Human effort expected (proposed) | Expected firm minutes by category, and that any Plumb engineering will appear in the ledger | Interruption budget (D6) | "Consent for 2 accounts and up to 5 questions on folder conventions. Any Plumb engineering time appears in your ledger." |

**When it is shown and when the decision is skipped (proposed, combining spec App. A §6, spec §17 and D6):**

- A card is generated and visible in the progress feed for every intervention version, including those that need no decision.
- It requests an IMPLEMENT_OPERATE decision on the first version of each intervention (collection path in P2; preparation workflow in P4), and again only when a change crosses an envelope boundary: processor, region, permissions, spend cap or irreversible-action policy (D6, spec §17).
- It proceeds without asking, shown as "Proceeding under your envelope v<n>", when the standing envelope covers purpose, scope, destination and budget and a valid IMPLEMENT_OPERATE approval covers a card whose fields are unchanged. A bounded repair that produces a new artifact digest without changing any card field is in this case.
- The approval binds to the card's digest, the policy version and an expiry (PL-040). Plumb never asks again for an authorization that is still valid (PL-041).

**Rules.** No "Allow AI" button. A changed card shows an impact diff against the approved version and the actual test evidence (spec §17). Declining leaves the build as a resumable dependency with completed work kept, not as a failure. The maximum spend is one number, not three; the fixture shows why (envelope limit EUR 15,000, plan budget EUR 12,000, step budgets summing to EUR 10,060, escalation at 80% of the limit).

**Acceptance notes.**
- Given an envelope that covers the intervention and an unchanged card, no decision is requested and the card is still visible.
- Given a new processor, exactly one IMPLEMENT_OPERATE request is raised, naming the boundary crossed.
- The resulting ApprovalRecord has decision kind IMPLEMENT_OPERATE, a HUMAN_OWNER approver and an authenticated decision reference; an approval-shaped record written by an agent is rejected (PA-010 behavior).
- No catalog scenario tests the card directly; PA-010's binding rules apply to the record it produces.

**Package has.** OpportunitySpec and ApprovalRecord contracts. The fixture plans carry a pre-existing IMPLEMENT_OPERATE approval as a plan input (`apr-acct-implement-operate-review-workflow` in the [accounting plan](../fixtures/plans/accounting_evidence_preparation.json)). No API operation mints one except `resolveBuildDependency`.

**Ids.** PL-005, PL-012, PL-013, PL-040, PL-041, PL-058.

### 4.2 Progress feed

**Purpose.** Honest, plain-language progress during a build (spec App. A §6). States come only from persisted build-ledger events; "verified" comes only from verifier attestations, never from an agent's message (PL-016).

**Build states** (BuildState in [common.py](../plumb/contracts/common.py), spec §23):

| State | Customer label | Example copy |
|---|---|---|
| DRAFT | Planning | "Drafting the build plan from your account inventory." |
| VALIDATED | Plan checked | "Plan checked against your envelope: 8 steps, maximum $<budget>." |
| RUNNING | Working | "Mapping folder conventions to clients and periods (step 3 of 8)." |
| WAITING_AUTH | Waiting for you: authorization | "Waiting for read access to the 'Clients 2026' folder. You can grant it. Collection for 12 clients resumes after." Links to the blocked-dependency card |
| WAITING_INPUT | Waiting for an answer | "One question about period attribution. Other clients continue." Links to the focused-question queue |
| VERIFYING | Being verified | "The independent verifier is checking that a new document arrives." |
| VERIFIED | Verified | "Collector verified: a statement added at 10:02 appeared at 10:04, filed to <client>, June 2026. Receipt <attestation id>." Requires an attestation |
| FAILED | Stopped | "Stopped after 3 attempts: <what was tried>, <failure class>. Completed work is kept." |
| CANCELLED | Cancelled | "Cancelled by <person> on <date>." |

**Step states** (BuildStepState) use the same vocabulary: PENDING and READY read "Queued", RUNNING "Working", VERIFYING "Being verified", VERIFIED "Verified" (attestation required), FAILED "Stopped", BLOCKED links to the blocked-dependency card, CANCELLED "Cancelled".

**Collector states** (CollectorState):

| State | Customer label | Example copy |
|---|---|---|
| PLANNED | Planned | "Collector planned for the document store." |
| SHADOW | Collecting, not yet trusted | "Collecting in shadow. Results are not used yet." |
| BACKFILLING | Loading history | "Loading history from <watermark>: 14,200 of about 30,000 items." |
| RECONCILING | Checking counts | "Comparing stored counts with the source." |
| ACTIVE | Live, awaiting verification; then Verified live | "Live, awaiting verification" until the attestation exists; then "Verified live. Last event 3 minutes ago." |
| DEGRADED | Degraded | "No events for 12 minutes. Items that depend on this source show Unknown." |
| PAUSED | Paused | "Paused: grant for the mailbox expired." |
| RETIRED | Retired | "Retired on <date>." |

**Copy rules.** Never "done", "complete" or "live" without an attestation; never "autonomous". Manual work appears inline, for example: "Plumb engineer edited the folder mapping (25 min, ENGINEERING_INTERVENTION)."

**Acceptance notes.**
- A successful deployment response with no attestation renders "Being verified", never "Verified" (mirrors PA-001's pass rule).
- Every ENGINEERING_INTERVENTION or OPERATIONAL_REPAIR entry on a build appears in its feed.
- After a worker restart the feed is rebuilt from persisted events with no gap (PL-017).

**Package has.** The state enums; seven guarded state machines whose guards are caller-asserted booleans; `listBuildEvents` in the [OpenAPI proposal](../api/openapi.yaml) with no server.

**Ids.** PL-003, PL-016, PL-017, PL-042, PL-057; PA-001.

### 4.3 Blocked-dependency card

**Purpose.** When work stops, state the exact missing consent, policy or input, who can resolve it and what resumes, with completed work kept (spec App. A §6; PL-001, PL-041).

**Fields** (from DependencyRecord in [common.py](../plumb/contracts/common.py), plus proposed billing state):

| Field | Source | Rule |
|---|---|---|
| What is blocked | `blocked_step_ids`, mapped to plain language | Name the clients, periods or steps affected |
| Exact missing item | `missing_authority` | Names of grants, consents or decisions, never values |
| Why | `error_class` and `failure_class` | Plain-language copy per class (table below) |
| Who can resolve | `resolver_role`, mapped to a persona | One named resolver |
| One action | Consent flow, approval or answer | A single button; no generic retry for missing authority |
| What resumes after | `resumes_after` | Required on every customer-facing card |
| Since when | `raised_at` | Shown as elapsed time |
| Billing state (proposed, D7) | Resolver side | Customer-side blocks not billed while open (firm minimum still applies); Plumb-side and vendor blocks never billed |

**Error classes** ([common.py](../plumb/contracts/common.py) `ErrorClass`, the 13 initial classes of spec §22). Copy is proposed.

| Error class | Typical MVP cause | Plain-language copy | Who resolves | Owner action | What resumes |
|---|---|---|---|---|---|
| AUTH_REQUIRED | Provider token revoked or consent withdrawn | "Plumb lost access to <account>. Reconnect it to resume collection." | Firm owner or account admin | Reconnect through the consent flow | Collection from its saved cursor, no re-backfill |
| SCOPE_DENIED | Operation outside the granted scope or the envelope | "Plumb needs read access to the folder '<name>' to check June documents for 4 clients." | Firm owner | Grant the scope (an envelope boundary) | Checks for the affected clients |
| PURPOSE_DENIED | Source used for a purpose it was not granted, such as SERVE before shadow | "Using your document store to prepare review packages needs your permission to serve it in a running workflow. Nothing else changes." | Firm owner | Grant the purpose (DATA_USE) | Shadow activation |
| POLICY_STALE | Approval bound to an older policy version, or an expired grant | "Your approval was for policy 2.1. The policy is now 2.2 (see changes). Approve the new version to continue." | Firm owner; Reviewing accountant for case-level | Re-approve the changed bytes only | The paused step |
| STATE_CONFLICT | Case changed after it was prepared or approved, such as a corrected statement | "A corrected statement arrived after this package was prepared. Plumb rebuilt it; please review the new version." | Plumb recomputes; then Reviewing accountant | Review the new version | Sign-off |
| PAYLOAD_CONFLICT | Same effect slot or idempotency key with a different payload | Operator-only in Prepare. In Draft and Send: "A different version of this request already exists; Plumb did not create a second one." | Plumb operator | None | Not applicable |
| BUDGET_EXCEEDED | A step needs more than the remaining reservation, or projected spend passes the escalation trigger | "This build would pass the spending cap you set ($<cap>). Raise the cap or let Plumb stop here; completed work is kept." | Firm owner | Raise the cap (an envelope boundary) or decline | Remaining steps |
| CAPABILITY_UNSUPPORTED | Operation not on the supported-environments list for this account | "Your <provider> account does not support <operation> in a way Plumb has tested. Plumb is trying <alternative>." | Plumb | None | When a primitive is added; never billed |
| SOURCE_STALE | Collector stale or degraded (PA-011) | "No new data from <source> for 12 minutes. Items that depend on it show Unknown, not Missing. Plumb is on it." | Plumb operator (OPERATIONAL_REPAIR), or the firm owner if access was lost | None, unless reconnect is needed | Re-evaluation of affected items after reconcile |
| DATA_QUALITY_FAILED | Unreadable or unsafe file quarantined, or a reconciliation mismatch | "We could not read 'stmt_june.pdf' safely, so it is quarantined. Upload a new copy or mark it reviewed." | Reviewing accountant or Bookkeeper | Replace the file or confirm | The item's status |
| VERIFICATION_FAILED | Verifier attestation FAIL | "Independent verification failed: the test document was filed to the wrong period. Plumb is repairing it (attempt 2 of 3)." | Plumb | None | Re-verification; never billed |
| EFFECT_UNKNOWN | Ambiguous provider outcome after dispatch | In production Prepare only the reversible connector-setup writes (for example registering change notifications) can end ambiguous; operator-facing, resolved by re-reading the provider's state. Sandbox, Draft and Send: "Confirming whether the provider created the draft. Nothing is re-sent until confirmed." | Plumb | None | After reconciliation (PA-009) |
| RETRY_EXHAUSTED | Bounded repair used up | "Plumb stopped after 3 attempts: <what was tried, failure class>. This step ended as a failure; completed work is kept." | Plumb engineer review (logged if they intervene) | None | A new build attempt; a terminal outcome under PL-001 |

**Failure classes to resolver** (FailureClass): MISSING_AUTHORIZATION goes to the Firm owner; MISSING_BUSINESS_DECISION goes to the focused-question queue; UNSUPPORTED_CAPABILITY, IMPLEMENTATION_DEFECT and POOR_MODEL_QUALITY go to Plumb; SOURCE_SCHEMA_CHANGE goes to Plumb, repaired manually and logged as OPERATIONAL_REPAIR because there is no maintenance agent; TRANSIENT_INFRASTRUCTURE is retried automatically and shown only if retries run out; EXHAUSTED_RESOURCES goes to the Firm owner when it is budget, otherwise to Plumb.

**Rules.** Requests are grouped per resolver and error class with `group_missing_authorizations` and batched under the interruption budget (section 4.6). Unrelated work continues. Plumb never asks again for an authorization that is still valid.

**Acceptance notes.**
- PA-008: an expired mailbox grant yields a card with MISSING_AUTHORIZATION, the exact source and purposes, resolver HUMAN_OWNER, the blocked steps and `resumes_after`; other collectors continue; after renewal, collection resumes from its cursor without re-backfill.
- PA-004: the affected case enters WAITING_INPUT with a precise dependency while other cases continue.
- PA-011: a stale source blocks explicitly ("waiting for source coverage") instead of defaulting.

**Package has.** The DependencyRecord contract; `group_missing_authorizations` in [approval_checker.py](../plumb/checker/approval_checker.py); `resolveBuildDependency` and `createConnectionIntent` in the OpenAPI proposal. No dependencies table and no card.

**Ids.** PL-001, PL-017, PL-041, PL-056; PA-004, PA-008, PA-011.

### 4.4 Close-readiness ledger

**Purpose.** The interim deliverable from P2 (D2): for every recurring client-period, what is held, what is confirmed absent and what is unknown, with provenance. Read-only.

**Key fields.**

| Element | Content |
|---|---|
| Rows | One per in-scope client-period (client by month), one per obligation within it, regardless of how many staff chased it |
| Obligation set | From the agent-generated client/period/obligation mapping and the owner's answers in P2; from engagement-checklist templates in P4 |
| Presence | PRESENT, CONFIRMED_ABSENT or UNKNOWN (`Presence` in [common.py](../plumb/contracts/common.py)) |
| Fact status | OBSERVED, INFERRED, CONFIRMED, DISPUTED, STALE or SUPERSEDED (`FactStatus`) |
| Provenance | Source and account, external record id and version, event, observation and availability times, link to the raw content (PL-009) |
| Who chased | Staff member, date and message reference from mail history (P4). Before P4: "Chase history not connected" |
| Source health | Per source: freshness, lag, completeness and failure state (PL-025) |
| Row summary | Counts by presence; time since last change |

**Display rules (proposed).**
- UNKNOWN is never shown as "Missing". Copy: "Unknown: not seen in <sources> as of <time>."
- CONFIRMED_ABSENT requires authoritative evidence: a recorded human confirmation or an authoritative source record. Inference alone never yields CONFIRMED_ABSENT (open question 4).
- If any source an obligation depends on is stale, the item shows Presence UNKNOWN with fact status STALE and "waiting for source coverage" (PA-011).
- An INFERRED fact below the auto-accept threshold, or a DISPUTED one, shows every candidate and does not count as PRESENT for the folder owner; it raises a focused question (PA-003).
- Superseded versions stay visible in history; corrections are scoped and reversible (PL-011).
- No request, draft or send controls until the Draft tier ships.

**Acceptance notes.**
- PA-001: a document added outside Plumb appears exactly once, attributed to the right client and period, within the 5-minute health deadline.
- PA-005 (collector half): delayed and duplicated webhooks plus overlap polling produce exactly one event; a stale "deleted" webhook triggers an authoritative fetch.
- PA-011 (health half): a blocked endpoint shows DEGRADED with freshness and lag within the health deadline, and affected items show Presence UNKNOWN with fact status STALE.
- PA-003: a misfiled statement is not attributed to the folder owner.
- Usage is instrumented: D2's revisit trigger needs weekly use by at least half of active bookkeepers.

**Package has.** Presence and FactStatus enums; EvidenceEvent, DerivedFact, ObjectResolution and ScopedCorrection in [evidence.py](../plumb/contracts/evidence.py); SQL designs for evidence events, objects and facts. No collector or object resolution.

**Ids.** PL-009, PL-010, PL-011, PL-024, PL-025; PA-001, PA-003, PA-005, PA-011.

### 4.5 Review surface

**Purpose.** One package per client-period for the reviewing accountant, with explicit decision capture. It doubles as the prospective correction collector (spec App. B; D3).

**Package view.** Header: client, period, readiness verdict, verifier attestation badge with receipt, prepared-at time, source freshness at preparation, versions. Items: for each obligation, presence, fact status, evidence links, extracted values with their sources, and Plumb's note. A "what Plumb would have done" panel in shadow. Open dependencies. Version history.

**Decisions.**

| Level | Decision | Captured as |
|---|---|---|
| Item | Accept | Accepted value with input snapshot and case id |
| Item | Correct (client, period, presence or value) with a reason | Correction; becomes a new package version |
| Item | Amend after sign-off | Later amendment linked to the signed version |
| Package | Sign off; sign off with corrections; reject as materially wrong | ApprovalRecord with decision kind CASE_LEVEL_BUSINESS bound to the package digest, case version, policy version and expiry |

**Rules (proposed).**
- Only explicit acceptance counts. No edit is not acceptance (spec App. B; PL-027). The co-headline counts packages accepted without material correction and with zero wrong-client attribution (D10).
- Material correction, initial definition for the domain expert to ratify: a change of client or period attribution, adding or removing an obligation item, or changing an item's presence. Wording edits are not material.
- The package reads "Ready for review" until sign-off, then "Signed off" (the catalog's "complete"). Never "closed" or "close complete". No accounting write occurs: spec §15 makes any write an explicit policy choice, and posting is out of scope.
- Sign-off comes from an authenticated human, never from an agent-supplied value (PL-040).
- A source change after sign-off creates a new package version; the earlier sign-off does not carry over (PA-006 pattern).
- Corrections that express a convention raise a focused question so they become versioned conventions and are not asked again (PA-004).
- Active review time per package is recorded as NORMAL_BUSINESS_REVIEW minutes, the input to accountant minutes against baseline.
- Correction records are stored as labels for evaluation and the M2 gate (at least 500 explicit accept/correct events, D5). They are never used for training in v1.
- Location: Plumb-hosted in the MVP (open question 2).

**Acceptance notes.**
- PA-002: "ready for review" before sign-off and "complete" after it; no accounting write; BUSINESS_OUTCOME attestation by a VERIFIER principal; a replayed trigger produces no duplicate.
- PA-006: a corrected statement after approval makes the accepted input stale, and the earlier approval does not carry over.
- PA-010: an approval bound to an old digest or policy does not authorize the revised package; the reviewer is asked once, for the changed bytes only.

**Package has.** No ReviewPackage contract. ApprovalRecord requires a case version for CASE_LEVEL_BUSINESS decisions ([approval.py](../plumb/contracts/approval.py)); the SQL `cases` table has `review_state` NONE, READY_FOR_REVIEW, APPROVED, REJECTED ([SQL design](../sql/001_initial_design.sql)); `LabelKind` includes CORRECTION. No review queue.

**Ids.** PL-001, PL-010, PL-027, PL-035, PL-040, PL-042, PL-059; PA-002, PA-003, PA-006, PA-010.

### 4.6 Approvals inbox

**Purpose.** One place where each human decision is asked, labeled with which of the three spec §17 decisions it is and who owns it.

| Decision (spec §17) | DecisionKind | What it covers in the MVP | Owner | When asked | Asked again when |
|---|---|---|---|---|---|
| Use particular data | DATA_USE | Per source and purpose: INSPECT, COLLECT, TRANSFORM, EVALUATE at onboarding (P1); mailbox INSPECT and COLLECT (P4); SERVE before the first shadow (P4). TRAIN is separate, off by default and not requested in v1 | Firm owner (HUMAN_OWNER) | Once per source and purpose | Expiry, a new source or a new purpose |
| Implement and operate an intervention | IMPLEMENT_OPERATE | Via the implementation card: collection path (P2); preparation workflow (P4) | Firm owner (HUMAN_OWNER) | Once per intervention version | A change crosses an envelope boundary: processor, region, permissions, spend cap or irreversible-action policy |
| Case-level business approval | CASE_LEVEL_BUSINESS | Package sign-off, decided in the review surface and listed here as pending. After the MVP, any request that trips a D6 materiality trigger (for example an item with Presence UNKNOWN, or fact status STALE) also needs per-case approval; in the Draft tier staff review every draft anyway | Reviewing accountant (HUMAN_REVIEWER or HUMAN_APPROVER) | Each package; materiality triggers once requests ship (P6 at the earliest) | Package or policy version changes |

The reminder policy, needed only for the Send tier, is approved once by the Firm owner and rebound on each policy-version bump (D6); that approval is logged as CUSTOMER_AUTHORIZATION (D6 rubric as amended, founder decision 18).

**Every request shows** the decision type and owner; what will change; why it is needed; what authority is missing; which work is blocked; an impact diff; the actual test evidence; the expiry; approve and decline. No "Allow AI" button (spec §17).

**Batching and budget** (hypotheses, D6). Requests are grouped one per resolver and error class (`group_missing_authorizations`). Onboarding: at most 2 hours of CUSTOMER_AUTHORIZATION and at most 4 owner-hours in the first 30 days. Steady state: at most 1 batched owner request per tenant-week, at most 30 minutes a week of owner decision time, reviewer approvals batched into at most one session a day, repeat-ask rate 0. The budget counts unscheduled asks; scheduled weekly check-in time is DOMAIN_CLARIFICATION and is reported beside it (D6 as amended). A block that threatens a close deadline may be raised at once and counts against the budget (proposed). Overruns are logged and triaged as product defects.

**Authentication.** Each decision goes through an identity-provider step-up that produces the `authenticated_decision_ref`. An approval-shaped record produced by a build or runtime agent is rejected (PL-040).

**Acceptance notes.**
- PA-008: renewal through an authenticated consent flow; the owner is never asked to re-approve still-valid authority.
- PA-010: approval bound to digest, case version, policy version and expiry; revocation cancels a queued dispatch; an agent-written approval is rejected; the changed bytes are asked once.
- Interruption load is measured per tenant-week by decision type ([metrics](06-metrics.md)).

**Package has.** DecisionKind and ApprovalRecord; `check_approval` with 11 finding codes; `group_missing_authorizations`. No approvals endpoint, no inbox, no step-up.

**Ids.** PL-040, PL-041, PL-053; PA-006, PA-008, PA-010.

### 4.7 Results-and-effort view

**Purpose.** After activation, show eligible cases, correct outcomes, review effort, failures and cost with supporting records (spec App. A §6), next to the customer-visible human-effort ledger (PL-003; D8).

| Panel | Content | First phase (hypothesis) |
|---|---|---|
| Human-effort ledger | Minutes in each of CUSTOMER_AUTHORIZATION, DOMAIN_CLARIFICATION, NORMAL_BUSINESS_REVIEW, ENGINEERING_INTERVENTION and OPERATIONAL_REPAIR; by person and side (firm or Plumb; Plumb staff need a principal type first, gap 3), by build and by close; failed, blocked and abandoned attempts included; drill-down to each entry | P2 |
| Autonomy | This tenant's EIH/VD: ENGINEERING_INTERVENTION and OPERATIONAL_REPAIR minutes over verifier-attested deployments; platform-investment hours shown beside it, never netted; "supervised" label | P2 |
| Outcome mix | Per authorized goal: verified interventions, actionable dependencies, terminal failures (PL-001), with what was attempted and why it stopped; days in dependency by resolver | P2 |
| Time to first verified event | Calendar days from envelope signature, split into Plumb-controlled and dependency time | P2 |
| Package outcomes | Eligible in-scope client-periods (blocked and failed included); attested ready-for-review packages; accepted without material correction (co-headline) with its rate; correct-package rate against the threshold; packages ready before the firm's close deadline | P5 |
| Review effort | Accountant assembly-plus-review minutes per client-period against the month-0 baseline; Plumb human minutes per accepted package | P5 |
| Missing-item quality | From the shadow report: false-chase rate, missing-item recall, wrong-client attribution | P5 |
| Cost | Inference and infrastructure cost per package | P5 |
| Interruption load | Owner and reviewer decision minutes per week by decision type; questions per workflow; repeat-ask rate | P2 |
| Billing | Billable active client-months and D7 credits (rejected packages; a Plumb-caused DEGRADED collector over more than 20% of the period; customer-side blocks) | After conversion |

**Rules.** Every rate shows its numerator and denominator, with exclusions kept in the denominator. No hours-saved or ROI figure without a baseline and a denominator. The historical duplicate-chase baseline is labeled "historical, non-causal" and is never counted as an outcome (spec §7). Technical and commercial success are shown separately (spec §24).

**Acceptance notes.**
- Every human-principal action on tenant resources produces an effort entry without manual logging (proposed test, P1).
- The ledger reconciles with the delivery team's own account under PA-027's audit method at M1, M1R and M5, run by an auditor outside the delivery team (D12). This is not a PA-027 pass.
- EIH/VD is computed with failed attempts in the numerator and only attested deployments in the denominator.

**Package has.** The HumanEffortCategory enum; a HumanEffortRecord model nothing uses; SQL `human_effort` and `outcome_observations` tables; `listOutcomes`, read-only, whose OutcomeObservation carries one nullable effort category. No capture API and no autonomy computation.

**Ids.** PL-001, PL-003, PL-059, PL-062; ADR-010; PA-001 (ledger check), PA-027 (method).

### 4.8 Focused-question queue

**Purpose.** Turn missing business decisions into focused questions with evidence and consequences, without stopping unrelated work; answers become versioned conventions (spec App. B; App. A §3).

**Fields.** The question; the evidence (document link; candidates with scores); the consequence of each answer, as the set of cases that would change; who should answer (Firm owner for firm conventions, Reviewing accountant for attribution of a specific item); what is blocked (only the affected cases, in WAITING_INPUT); what happens if unanswered (the item stays UNKNOWN; nothing defaults); budget status ("3 of 5 onboarding questions used").

**Budget per workflow** (hypotheses, D6): at most 5 DOMAIN_CLARIFICATION questions per workflow at onboarding; at most 2 new questions per close after close 1; repeat-ask rate 0. Overruns are product defects. The R3 trigger is a median above 10 questions or 3 hours per workflow on tenant 3 ([risks](07-risks-and-assumptions.md)).

**Rules.** Never ask what the evidence can answer. Batch non-blocking questions into the owner's weekly session. Store each answer as a versioned policy input that applies to future cases of the same shape. Corrections are scoped to the subject they concern (PL-011). Ask again only if the convention's inputs change, and then show the difference.

**Acceptance notes.**
- PA-003: the question names the document, both client candidates and the consequence of each choice; DOMAIN_CLARIFICATION effort is recorded; nothing is attributed until the human decides.
- PA-004: only the affected case waits; the answer is stored as a versioned policy input; the next statement of the same shape is attributed without a new question.

**Package has.** Nothing for the queue. ObjectResolution candidates and ScopedCorrection in [evidence.py](../plumb/contracts/evidence.py) support the data side.

**Ids.** PL-003, PL-010, PL-011, PL-041; PA-003, PA-004.

---

## 5. Proposed ReviewPackage contract

**Status today (verified).** `ReviewPackage` exists only as an `ArtifactKind` value in [common.py](../plumb/contracts/common.py) (and the generated schemas, the OpenAPI artifact-kind enum and the SQL check list that mirror it). There is no contract class, no capability in the [registry](../plumb/registry/capability_registry.json) produces one, and no API operation reads or writes one. The accounting plan's `compile-review-workflow` step describes preparing "the review package" but outputs only a WorkflowSpec and ServingConfiguration.

**Proposal.** A digest-addressed artifact subclassing `ArtifactHeader` (tenant, kind, schema version, immutable version, content digest, producer, evidence links), following the package's conventions: extra fields forbidden, timezone-aware datetimes, money in minor units.

| Field | Proposed type | Rule |
|---|---|---|
| `package_id` | Identifier | Stable across versions of the same client-period |
| `client_object_id` | Identifier | Resolved client object; never a free-text name |
| `period` | Start, end and period key | Accounting period, normally a month |
| `case_id`, `case_version` | Identifier, integer of at least 1 | The workflow case and the version this package was prepared from |
| `obligations` | List of obligation items | Each item: `obligation_id`; obligation type (template reference); `presence` (Presence); `fact_status` (FactStatus); `evidence_event_ids`; `fact_ids`; provenance summary; chase-history references (P4); `auto_accepted` flag with confidence |
| `prepared_items` | List | Extracted values and checks, each with supporting evidence ids and fact status (PL-010) |
| `open_requests` | List | Prepare: requests Plumb would have prepared, never dispatched. Draft and Send: ActionIntent references |
| `open_dependencies` | DependencyRecord ids | Anything blocking readiness |
| `readiness_verdict` | READY_FOR_REVIEW, NOT_READY or BLOCKED_STALE_SOURCE | Computed deterministically (PL-036): READY_FOR_REVIEW only if every required obligation is PRESENT or CONFIRMED_ABSENT, no dependency is open and every contributing source was fresh at preparation; BLOCKED_STALE_SOURCE when a required source is stale; otherwise NOT_READY with the blocking items listed |
| `facts_as_of` | Datetime | Knowledge boundary used to prepare the package |
| `source_freshness` | Per source: last event and watermark | Shown in the review header |
| `verification_attestation_ref` | Attestation id and digest | Attestation must cover this package's digest; required before the package is shown as ready |
| `review_state` | NONE, READY_FOR_REVIEW, APPROVED, REJECTED | Reuses the SQL `cases.review_state` vocabulary |
| `review_outcome` | ACCEPTED, ACCEPTED_WITH_CORRECTION, AMENDED, REJECTED, plus a `material_correction` flag | Set only by an explicit human decision |
| `signoff_record_ref` | ApprovalRecord id | CASE_LEVEL_BUSINESS, bound to this package's digest and `case_version` |
| `versions` | Digests of the WorkflowSpec, ReleaseManifest, mapping, conventions (policy-input version) and any model version used | Every input that could change the package is pinned |
| `supersedes` | Previous package version id | A correction or source change creates a new version; the old one is kept |
| `close_deadline` | Datetime | The firm's close deadline, used by the co-headline |
| `billing` | Billable flag and credit reason | Derived, never set by hand: attested, in scope and not credited under D7 |

**Validators (proposed).**
- CONFIRMED_ABSENT requires an authoritative evidence reference.
- `readiness_verdict` must agree with the obligation list.
- `review_state` APPROVED requires `signoff_record_ref`, and that record must not be agent-produced.
- A package containing an item from an excluded source (for example tax-return folders) is invalid (PL-053).
- The producer of `verification_attestation_ref` must be a VERIFIER principal distinct from the workflow that produced the package (PL-042).

**Why it matters.** The ReviewPackage is the unit that ties three things together. It is what the verifier attests (PL-042), what the accountant signs off (PL-040), and what the firm pays for: an active client-month is a recurring in-scope client-period with a verifier-attested ready-for-review package (D7). It is also the unit of outcome measurement: accepted review packages per month and the correct-package rate are counted over ReviewPackages, with all eligible client-periods as the denominator (D10).

**Work to add it (P4, proposed).** A Pydantic contract and generated JSON Schema; a capability that produces it (a workflow output); storage as an artifact row with kind ReviewPackage plus a query table; API operations to list packages, get one and record a review decision. See the [backlog](05-backlog.md).

---

## 6. Supported environments v1

**What the spec requires.** PL-002 applies "for supported environments", which the spec does not enumerate. PL-007 requires an EnvironmentInventory before a production build, and PL-008 requires discovered, documented, sandbox-tested and production-verified capability to be distinguished per account and operation. A vendor page saying an API exists does not establish that this customer's account can use it.

**What this doc proposes (D3 (k)).** Publish "supported environments v1" at P2 as a per-operation list: provider, account, operation, maturity, probe receipt reference and last-probed date. Never a logo wall. Anything outside the list becomes a dependency or a backlog item, never hidden manual work.

**Maturity floors (verified in [plan_checker.py](../plumb/checker/plan_checker.py), `required_maturity`, lines 217-238).** release.* and infrastructure.apply need PRODUCTION_VERIFIED. dependency.raise needs DOCUMENTED. READ steps need DOCUMENTED. collection.deploy_shadow with READ or INTERNAL_WRITE needs DOCUMENTED. Every other step, including INTERNAL_WRITE steps such as collection.backfill and any external write, needs SANDBOX_TESTED.

**Operation table.** Provider families are the D1 candidates; operation names are proposed Plumb operation names (PA-001 uses `list_folder_changes` and `fetch_document`). Status today is "not probed" for every provider row; Plumb-internal rows have only synthetic registry entries. Targets are hypotheses.

| Source and provider family (candidates) | Operation | Effect class | Phase needed | Checker floor | MVP target | Status today |
|---|---|---|---|---|---|---|
| Document store: Google Drive, SharePoint/OneDrive, Dropbox or SmartVault | `list_folder_changes` | READ | P1-P2 | DOCUMENTED | SANDBOX_TESTED on tenant 1's account (PA-001 precondition; P1 exit) | Not probed |
| Document store | `fetch_document` (authoritative content) | READ | P1-P2 | DOCUMENTED | SANDBOX_TESTED (PA-001 precondition; P1 exit) | Not probed |
| Document store | Folder and metadata listing for inventory (inventory.probe) | READ | P1 | DOCUMENTED | DOCUMENTED | Not probed |
| Document store | Register and remove change notifications; connector configuration (integration.configure, collection.enable_incremental) | EXTERNAL_WRITE_REVERSIBLE (as in the fixture plan) | P1-P2 | SANDBOX_TESTED | SANDBOX_TESTED on tenant 1's account (D3; P1 exit) | Not probed |
| Ledger: QBO or Xero | Ledger metadata reads: client companies, chart of accounts, period metadata | READ | P1-P2 | DOCUMENTED | SANDBOX_TESTED on tenant 1's account (P1 exit) | Not probed |
| Ledger | Any write or posting | FINANCIAL_COMMITMENT | Out | Not applicable | Not supported | Excluded |
| Mail: Google Workspace or Microsoft 365 | Mail history read: list and fetch message metadata | READ | P4 | DOCUMENTED | DOCUMENTED (D3); proposed SANDBOX_TESTED before production collection, matching document reads | Not probed |
| Mail | Message lookup by provider request id | READ | P5 (sandbox), P6 | DOCUMENTED | SANDBOX_TESTED; required by PA-009 | Not probed |
| Mail | Create draft in the firm's mailbox | EXTERNAL_WRITE_REVERSIBLE | P6 (Draft) | SANDBOX_TESTED | SANDBOX_TESTED plus the production gateway and effect-slot dedup (D3) | Not probed |
| Mail | Send message | EXTERNAL_COMMUNICATION | P6 (Send) | SANDBOX_TESTED | SANDBOX_TESTED; the release.canary step itself needs PRODUCTION_VERIFIED | Not probed |
| Practice management (optional): Karbon, Financial Cents or Double | Read tasks and checklists | READ | Optional | DOCUMENTED | DOCUMENTED | Not probed |
| Plumb-internal | collection.deploy_shadow | INTERNAL_WRITE | P2 | DOCUMENTED | DOCUMENTED | Registry entry synthetic |
| Plumb-internal | collection.backfill | INTERNAL_WRITE | P2 | SANDBOX_TESTED | SANDBOX_TESTED on tenant 1's account (D3) | Registry entry synthetic |
| Plumb-internal | collection.reconcile, integration.contract_test, verification.request | READ | P2 | DOCUMENTED | DOCUMENTED | Registry entries synthetic |
| Plumb-internal | workflow.compile | INTERNAL_WRITE | P4 | SANDBOX_TESTED | SANDBOX_TESTED before the M3-lite build | Registry entry synthetic |
| Plumb-internal | infrastructure.apply (only if the Prepare template keeps the fixture's serving-infrastructure step) | INFRASTRUCTURE_CHANGE in the fixture | P4 | PRODUCTION_VERIFIED | Prefer no per-tenant infrastructure: the Prepare envelope allows only READ, INTERNAL_WRITE and EXTERNAL_WRITE_REVERSIBLE. Otherwise qualify it in the same run and widen the envelope by an explicit decision | Registry entry synthetic |
| Plumb-internal | release.create, release.activate_shadow | INTERNAL_WRITE | P4 | PRODUCTION_VERIFIED | PRODUCTION_VERIFIED from a platform qualification run on a Plumb-owned production tenant, with a verifier attestation, before any tenant shadow (D3) | Registry entries synthetic |
| Plumb-internal | release.canary | EXTERNAL_COMMUNICATION in the fixture; INTERNAL_WRITE for the preparation-only canary | P6 (Prepare-tier canary, then Send) | PRODUCTION_VERIFIED | PRODUCTION_VERIFIED | Registry entry synthetic |

**Notes.**
- The registry in the package describes itself as "synthetic"; its providers and operations are placeholders and no entry establishes access to any real account. It holds 25 capability records covering 23 step types (two step types have two records each); 15 records claim PRODUCTION_VERIFIED, 8 SANDBOX_TESTED and 2 DOCUMENTED. P0 resets all of them to DISCOVERED or DOCUMENTED, after which the fixture plans fail at the SANDBOX_TESTED and PRODUCTION_VERIFIED floors until real receipts exist.
- Qualification constraints (D1, D9): the document store must support webhooks plus overlap polling (PA-005), and mail must support request-id lookup (PA-009). Provider sandboxes are needed for PA-002.
- Watch item (D11): whether ledger authorization is granted per client company. If so, onboarding authorization rises with the client count.
- Nango is the candidate transport substrate (D3). No substrate contract test has run; P1 exit requires them on the probed operations.

---

## 7. Gaps in today's reference package that block the MVP

Each gap was checked against the code on 2026-10-04. Closing phases are proposed; stories are in the [backlog](05-backlog.md).

| # | Gap | Evidence | Why it blocks the MVP | Close in |
|---|---|---|---|---|
| 1 | The value loop is not built: no control service, authentication or tenancy, connectors, collectors, sandbox, verifier, fault-injection harness, release executor, workflow runtime or UI | [README](../README.md); [VALIDATION_REPORT](../VALIDATION_REPORT.md) | Every journey step depends on them; the proposal is to build M0 and M1 as greenfield services that wrap the kernel rather than rewrite it | P1-P4 |
| 2 | No human-effort capture. HumanEffortRecord is defined and exported but used nowhere; no API records effort; OutcomeObservation carries one nullable `human_effort_category`; the SQL `human_effort` table has no attempt reference and there is no platform-investment ledger | [common.py](../plumb/contracts/common.py) lines 611-618; [openapi.yaml](../api/openapi.yaml) `OutcomeObservation` (line 3612); [SQL design](../sql/001_initial_design.sql) lines 814-829 | EIH/VD and the customer-visible ledger cannot exist; PA-001's "zero ENGINEERING_INTERVENTION" cannot be checked | P0-P1 |
| 3 | No principal type for Plumb staff. PrincipalType lists HUMAN_OWNER, HUMAN_REVIEWER, HUMAN_APPROVER, SERVICE, BUILD_AGENT, RUNTIME_AGENT, VERIFIER and RELEASE_EXECUTOR; nothing represents a Plumb engineer, operator or domain expert | [common.py](../plumb/contracts/common.py) lines 215-223 | Effort records require a principal; ENGINEERING_INTERVENTION and OPERATIONAL_REPAIR minutes cannot be attributed to Plumb staff truthfully | P0-P1 |
| 4 | The plan checker takes no EnvironmentInventory and ignores capability `required_authority` | [plan_checker.py](../plumb/checker/plan_checker.py) `check_plan` (lines 249-254: plan, envelope, registry, now) | A plan can pass for an account whose operation was never probed (PL-007, PL-008); D3 (b) requires the wiring | P1 |
| 5 | State-machine guards are caller-asserted booleans; no checker is called | [machines.py](../plumb/statemachines/machines.py) (for example `checker_ok`, `attestations_accepted`) | Safety holds only if the control service wires the checkers (D3 (b)) | P1 |
| 6 | Registry maturity is synthetic: 15 of its 25 capability records (covering 23 step types) claim PRODUCTION_VERIFIED | [capability_registry.json](../plumb/registry/capability_registry.json) line 3 | No coverage claim can come from it (D8); a truthful reset blocks every plan until receipts are earned | P0 reset; P1 and P4 receipts |
| 7 | No API object for the implementation card or authorization requests; no approvals endpoint; no identity-provider step-up. `resolveBuildDependency` is the only operation that yields an ApprovalRecord, and `group_missing_authorizations` is not exposed | [openapi.yaml](../api/openapi.yaml) (24 operations; `resolveBuildDependency` line 398); [approval_checker.py](../plumb/checker/approval_checker.py) line 210 | The owner has nowhere to decide; sections 4.1 and 4.6 cannot ship | P1-P2 |
| 8 | Missing read and lifecycle endpoints: no `listBuilds`, `getRelease`, `listReleases`, rollback, retire, `getAction`, `getOpportunity`, `selectOpportunity`, `getDatasetJob` or `getEvaluation`; no case, review-package, question, convention or effort endpoints | [openapi.yaml](../api/openapi.yaml) | Surfaces cannot read state; PL-047's rolled-back and retired states are unreachable through the API | P1-P4 |
| 9 | Missing persistence: no tables for connection intents, dependencies, integrations, workflows, monitors, users or principals, consent, budget ledger or admin audit; none for review packages, focused questions and conventions, or platform investment. The design has never run on PostgreSQL | [SQL design](../sql/001_initial_design.sql) (29 tables) | Dependencies, conventions and packages cannot be stored; PA-004 needs versioned policy-input storage | P1, P4 |
| 10 | No ReviewPackage contract (section 5) | [common.py](../plumb/contracts/common.py) line 371 (enum value only) | The package, its sign-off, billing and the co-headline have no data model | P4 |
| 11 | The RELEASE machine allows PAUSED only from ACTIVE. SHADOW can only advance to CANARY or retire; CANARY can roll back, promote or retire, but not pause. The API's `pauseRelease` promises an immediate block | [machines.py](../plumb/statemachines/machines.py) lines 399-421; [openapi.yaml](../api/openapi.yaml) `pauseRelease` (line 801) | Pause and kill from SHADOW and CANARY is P4 scope (PL-047) | P4 |
| 12 | SERVE is not enforced in practice: the synthetic `release.activate_shadow` and `release.canary` records require SERVE, but the release steps declare no sources, no fixture envelope grants SERVE, and every fixture plan passes | [README](../README.md) line 164; [accounting envelope](../fixtures/envelopes/accounting_evidence_preparation.json) | The explicit SERVE grant before shadow (P4) has no enforcement | P4 |
| 13 | The accounting fixture plan includes training and a reminder canary: `compile-review-workflow` depends on `train-categorization-candidate`, `canary-consolidated-reminders` is EXTERNAL_COMMUNICATION, and the envelope allows EXTERNAL_COMMUNICATION | [accounting plan](../fixtures/plans/accounting_evidence_preparation.json); [accounting envelope](../fixtures/envelopes/accounting_evidence_preparation.json) | The registry template the agent fills must be a Prepare template without training or canary sends | P0-P1, P4 |
| 14 | The accounting envelope and plan are EU/EUR (`eu-west-1`); the RFQ fixtures are USD (`us-east-1`) and laundry GBP (`eu-west-2`). All three envelopes and their grants expire 2027-03-31, inside the 180-day window | [accounting envelope](../fixtures/envelopes/accounting_evidence_preparation.json) (grant expiries lines 46, 63 and 78; region and envelope expiry lines 106-109); [README](../README.md) line 167 | One US region is required (D1), so the accounting fixtures are re-templated to US/USD. After expiry, any check run at the current time reports ENVELOPE_INACTIVE; the local tests keep passing because they evaluate at each plan's `planned_at` | P0 |
| 15 | SourceGrant has no `revoked_at`, while the SQL `source_grants` table does | [envelope.py](../plumb/contracts/envelope.py) line 83 | Revoking a single grant, such as the mailbox, needs a whole new envelope version; affects step 18 | P1 |
| 16 | The effect ledger is a single-process SQLite simulation; it does not check release pause or envelope revocation and only reports `authority_matches` | [effect_ledger.py](../plumb/ledger/effect_ledger.py) (`reserve`, line 389) | Not a Prepare blocker; it blocks the Draft and Send tiers | P5-P6 |

Also relevant: eight requirements have no local behavioral test: PL-002, PL-003, PL-049, PL-051, PL-059, PL-060, PL-062 and PL-063, among them the ones that carry the business case; six of the eight have artifact-inspection tests only ([VALIDATION_REPORT](../VALIDATION_REPORT.md)). No acceptance scenario has run against production.

---

## 8. MVP definition of done

The MVP is done when sections 8.1 to 8.4 hold for tenant 1 and the day-180 decision packet is written. The packet records tenant 1's evidence toward conversion to date; promotion to ACTIVE and conversion come in P6 (step 17). Thresholds are hypotheses set or ratified at M0, except where the catalog states them. Partial runs and proposed catalog variants (generated-path PA-001, preparation-mode PA-002, policy-level PA-010, accounting analogues of PA-013, PA-014, PA-016, PA-021 and PA-023) are numbered PA-Pnn in the [roadmap](04-roadmap.md) and are never reported as the original scenarios; the ids below are the roadmap's.

### 8.1 P2 exit: M1 on tenant 1

- [ ] PA-001 attested by the verifier: path_used VERIFIED_ADAPTER for transport; agent-filled BuildPlan; agent-generated mapping and CollectionSpec; zero ENGINEERING_INTERVENTION in the attested run; every failed eligible attempt counted.
- [ ] Safety bundle: PA-015, PA-019 and PA-022 pass.
- [ ] The collector half of PA-005 (backfill and live convergence, webhook dedup, authoritative fetch; PA-P16) and the health half of PA-011 (PA-P17) pass.
- [ ] Accounting adaptation of PA-023's account_boundaries contract test passes (PA-P08; not claimed as PA-023).
- [ ] Tenant isolation passes on the database, API, object-storage, cache, log and export surfaces (PA-P14, a subset of PA-017; full PA-017 comes before any training job).
- [ ] PA-026 passes if generated code ran; otherwise it moves to the first tenant where it runs.
- [ ] If M1 parses document contents, the accounting adaptation of PA-021's parser bounds (PA-P07) passes (D4).
- [ ] Surfaces live for tenant 1: read-only close-readiness ledger, implementation card, blocked-dependency card, progress feed, effort view, focused-question queue and the DATA_USE and IMPLEMENT_OPERATE parts of the approvals inbox, each meeting its acceptance notes in section 4.
- [ ] Supported environments v1 published per operation and maturity.
- [ ] Recorded: tenant 1's EIH/VD baseline and time to first verified event, split into Plumb-controlled and dependency time. The 90-day pilot clock has started.
- [ ] Ledger audited by the independent ledger auditor; zero unrecorded manual work.

### 8.2 P4 exit: M3-lite

- [ ] PA-002 run as written in sandbox, its single send only through the sandbox mail adapter, with a BUSINESS_OUTCOME attestation.
- [ ] PA-003, PA-004, PA-006, PA-008, PA-010 and PA-011 pass in sandbox.
- [ ] Accounting adaptation of PA-021's parser bounds passes on client PDFs (PA-P07).
- [ ] If ratified, the roadmap's prompt-injection analogue of PA-020 for client documents (PA-P19) passes before production shadow.
- [ ] ReviewPackage contract shipped (section 5); review surface captures explicit accept, correct and amend.
- [ ] Release executor qualified: real PRODUCTION_VERIFIED receipts for release.create and release.activate_shadow with a verifier attestation, before any tenant shadow.
- [ ] Pause and kill work from SHADOW and CANARY.
- [ ] Explicit SERVE grant recorded and enforced before the first shadow.
- [ ] The Plumb domain expert has set a numeric correct-package threshold and the material-correction rubric.
- [ ] DOMAIN_CLARIFICATION per workflow measured against the budget.
- [ ] Production shadow active on tenant 1 with no EXTERNAL_COMMUNICATION in the envelope; PA-P02 starts measuring.

### 8.3 P5 exit: the first measurable deliverable

- [ ] Verifier-attested ready-for-review packages on at least 30 client-periods across at least one full close (PA-P02).
- [ ] Correct-package rate reported against the threshold, exclusions in the denominator.
- [ ] Accountant minutes reported against the month-0 baseline.
- [ ] False-chase rate of 2% or less and missing-item recall of 90% or more (proposed).
- [ ] Owner decision time within budget; repeat asks 0.
- [ ] Tenants 2 and 3 shadow started; their full-close readings may land after day 180 and are reported as pending.
- [ ] Gateway sandbox crash tests pass for draft creation and sends: PA-005's dispatch-time re-check, PA-009 (as written for sends; the same check on draft creation is Draft-gate crash-test evidence) and PA-015's lease-and-fencing checks re-run on dispatch workers (not reported as a PA-015 result). These prepare P6; they do not ship Draft or Send.

### 8.4 Cross-cutting

- [ ] Every claim in partner-facing material passes the never-claim checklist (D8). In particular: no "autonomous close", no posting, "supervised" with labor shown, "automatically constructed" only after M1R, and no ROI without a baseline and a denominator.
- [ ] No surface shows "verified" without an attestation.
- [ ] The customer can export its specs, tests, evidence, packages and labor ledger in open formats.
- [ ] Registry contains zero synthetic PRODUCTION_VERIFIED records.

---

## 9. Explicitly out of scope and why

These hold for at least 180 days. This is the single out-of-scope list (section 2.4 points here). Each item records why, the requirements it defers or constrains, and what evidence would reopen it (D3, D5).

| Out of scope | Why | Requirements affected | Reopened by |
|---|---|---|---|
| Consolidated requests to clients, as mailbox drafts or sends (Draft and Send tiers) | A draft is an external write; the effect ledger is a SQLite simulation and a canary cannot be paused today. Starting preparation-only keeps PA-005, PA-006, PA-007 and PA-009 off the path to first value | PL-037, PL-038, PL-039 | The D4 Draft and Send gates after day 180 (earliest Send canary close around July 2027). Accelerated only if at least 2 of 3 partners make reminders a condition of continuing, never skipping the HIGH scenarios |
| Learning factory beyond the prospective correction collector (M2): no training.submit, no TrainingSpec execution | Training is the largest step in the accounting plan (EUR 2,500 of the EUR 10,060 step-budget sum); PA-012 does not require it; training rights are scarce; idle dedicated capacity can make the trained path lose on total cost (spec §14) | PL-032, PL-033 | All four M2 entry gates in D5 |
| Transaction categorization | Does not serve the wedge goal (missing evidence plus the package); M2 entry gates not met (D5) | PL-026, PL-031 | Baseline shows categorization dominates accountant time, TRAIN grants on at least 2 tenants and at least 500 explicit corrections with classification errors at 25% or more of review minutes (D3) |
| Screen or visual capture | About 34.6 GB/day raw per 100 employees (spec §24); experiment 1 unresolved (spec §27) | PL-007 (coverage disclosure only) | More than 20% of obligations still UNKNOWN after two closes because of off-system handoffs, or the D11 shadowing proxy test |
| Posting and any FINANCIAL_COMMITMENT | Accountant sign-off is mandatory; posting is a separate capability excluded unless specifically granted (spec App. B) | PL-005, PL-036 | A new envelope decision, never a silent widening |
| "Autonomous close" in any wording | A review-ready package is not an autonomous financial close (spec §15) | None | Not reopened |
| Open-ended opportunity discovery | Replaced by a vertical opportunity library in which Plumb still writes a complete OpportunitySpec with a native-feature baseline. Plumb may conclude "configure the firm's Xero or Financial Cents reminders", and that counts as a delivered intervention | PL-012, PL-013 | Revisit triggers in D3 |
| UI adapters and generic infrastructure generation | UI adapters are last in PL-020's preference order, with the highest maintenance exposure; infrastructure comes from fixed approved templates only | PL-020, PL-045 | Revisit triggers in D3 |
| Maintenance agent | Ops stay manual and logged: manual deploys as ENGINEERING_INTERVENTION, fixes to running collectors as OPERATIONAL_REPAIR. Monitors are still required for anything running | PL-049 (PL-048 still applies) | Revisit triggers in D3 |
| Tax-return information | IRC 7216 consent obligations (counsel to confirm, D9); enforced by folder and label exclusions and purpose checks | PL-053 | Counsel confirms monthly-close sources are outside 7216 (D9) |
| Multi-region and on-prem | One US region; the accounting fixtures are EU/EUR (`eu-west-1`) and must be re-templated to US/USD | PL-005, PL-052 | Not in the 180-day plan |
| Second domains (M6) | Platform verdict first; gated behind M5 evidence and PA-013, PA-025, PA-029 and PA-030 (D5) | PL-063 (replication first) | M5 evidence; then laundry route preparation, then RFQ |
| Customer editing of plans, mappings or workflows | The interface must not require editing a DAG (spec App. A §6); any such edit, by Plumb or firm staff, is ENGINEERING_INTERVENTION | PL-002, PL-003 | Not reopened for the normal interface |
| A surface for the firm's clients | The client is an affected party, not a principal; Plumb does not contact them in Prepare | None | Send tier, and then only as messages under the approved policy |
| Integrations outside supported environments v1 | Coverage is stated per operation at its maturity | PL-007, PL-008 | A probe receipt for the operation on the customer's account |
| Per-customer delivery engineers | Their time is ENGINEERING_INTERVENTION by definition; it is the services trap (D12) | PL-003 | Not reopened |

---

## 10. Open questions for founder ratification

1. **How a Prepare workflow becomes ACTIVE (founder decision 17, to ratify).** D7 and D9 convert a partner to annual once the workflow has been ACTIVE through one full close at or above the correct-package threshold, but the phased plan runs Prepare only in production shadow before day 180, and a release reaches ACTIVE only from CANARY. Decided path: SHADOW for at least one full close, then CANARY on a subset of client-periods whose accountants use the prepared packages in their real review, then ACTIVE, with no EXTERNAL_COMMUNICATION at any stage; conversion follows one full ACTIVE close at or above the threshold. The day-180 packet records tenant 1's evidence to date, and tenant 1's conversion is expected in P6. This needs the canary step qualified at PRODUCTION_VERIFIED and a registry step type for promotion to ACTIVE (section 2.2).
2. **Where the review surface lives.** Plumb-hosted in the MVP (proposed), rather than the "generated UI/review integration" inside the firm's own tools that spec App. B mentions.
3. **Who confirms the backfill watermark.** The spec says "an agreed watermark" (spec §11) without naming who agrees. Proposed: the Firm owner, on the implementation card.
4. **What establishes CONFIRMED_ABSENT.** Proposed: a recorded human confirmation or an authoritative source record; inference never does.
5. **Effort-rubric gaps.** The amended D6 rubric (founder decision 18) settles partner time: ENGINEERING_INTERVENTION covers implementation work by any person, Plumb or firm staff; approving the reminder policy is CUSTOMER_AUTHORIZATION; scheduled weekly check-ins and baseline-study recording overhead are DOMAIN_CLARIFICATION. It still does not place Plumb staff time that is neither implementation nor repair, such as the domain expert's facilitation of the baseline study or a Plumb sandbox reviewer's time. Proposed ([metrics](06-metrics.md) section 6 and its open question 1): such time goes to a tenant-tagged cost ledger reported beside the five categories (PL-059); the founder confirms that this meets PL-003's "all human effort" when the rubric is frozen in P0.
6. **A principal type for Plumb staff** (gap 3 in section 7), needed before the effort ledger ships.

---

## Related documents

- [Product brief](01-product-brief.md): problem, personas, principles and the surfaces at a glance.
- [Strategy decisions](02-strategy-decisions.md): D1 to D12 in full.
- [Roadmap](04-roadmap.md): phase windows, exit evidence and the proposed catalog scenarios.
- [Backlog](05-backlog.md): stories that close the gaps in section 7.
- [Metrics](06-metrics.md): EIH/VD, the co-headline and supporting metrics.
- [Risks and assumptions](07-risks-and-assumptions.md): R1 to R7 and their triggers.
- [Design-partner program](09-design-partner-program.md): selection, commitments and contract essentials.
- Sources in the repository: [spec v0.2](../spec/Plumb_Autonomous_Implementation_Specification_v0.2.md), [requirements index](../spec/requirements_index.json), [acceptance catalog](../acceptance/production_acceptance_catalog.yaml), [reference package design](../docs/REFERENCE_PACKAGE_DESIGN.md).
