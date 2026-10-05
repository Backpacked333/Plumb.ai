# Strategy Decision Record

- Status: Draft v0.1 (2026-10-04), proposed — requires founder ratification
- Owner: Product
- Basis: [spec v0.2](../spec/Plumb_Autonomous_Implementation_Specification_v0.2.md), [decision record](02-strategy-decisions.md) (this document is the readable rendering of the strategy panel's decision record), [acceptance catalog](../acceptance/production_acceptance_catalog.yaml), [requirements index](../spec/requirements_index.json)
- Elaborated in: [product brief](01-product-brief.md), [MVP scope](03-mvp-scope.md), [roadmap](04-roadmap.md), [backlog](05-backlog.md), [metrics](06-metrics.md), [risks and assumptions](07-risks-and-assumptions.md), [market and positioning](08-market-and-positioning.md), [design-partner program](09-design-partner-program.md). Index: [README](README.md).

This record holds the twelve strategy decisions (D1-D12) that the rest of the product doc set builds on. Where a sibling document and this record disagree, this record governs until the founder ratifies a change.

## How to read this record

Three kinds of statement appear here. Where the difference matters, the text says which one it is.

| Label | Meaning | How it is cited |
|---|---|---|
| Spec requires | Normative text in spec v0.2 (Oct 2, 2026) | PL-001..PL-063, ADR-001..ADR-010, "spec §n"; line numbers only where verified against the file |
| Package implements | Code or data in the local reference package (`plumb/`, `fixtures/`, `acceptance/`, `api/`), verified on 2026-10-04 | File paths |
| Proposed | What this record decides | Decision ids D1-D12 |

Ground truth about the package, as of 2026-10-04:

- The reference package implements a deterministic policy kernel: typed contracts, a registry-backed plan checker, approval, release and dataset checkers, a SQLite effect ledger and the state machines. [VALIDATION_REPORT.md](../VALIDATION_REPORT.md) reports 819 passing local tests.
- Nothing is deployed. None of the 30 catalog scenarios has run against production; the catalog says so itself (`executed_against_production: false`). The value-producing loop (inventory, connect, collect, plan, execute, verify, release, measure) is not built (research notes: implementation-reality).
- The capability registry is synthetic. Its 25 entries include 15 marked PRODUCTION_VERIFIED, and none of them establishes access to a real account ([capability_registry.json](../plumb/registry/capability_registry.json)).

Conventions:

- Every number in a decision (thresholds, prices, windows, staffing weeks, funnel counts) is a hypothesis unless it is quoted from the spec. Each table says so once. Hypotheses are pre-registered in threshold sheet v1 at M0 and change only through the revisit triggers.
- Week 0 starts Oct 5, 2026. Day 180 is Apr 3, 2027.
- Milestone labels used across the doc set: M0, M1, M1R, M3-lite, M4-accounting, M5, M2 (gated learning factory) and M6 (second domain: laundry route preparation, then RFQ). When this record says "the spec §26 table", it means the spec's own M0-M6 milestone table.
- Phases P0-P6 follow the phased plan in D5.
- Release tiers: Prepare (preparation-only, shadow), Draft (mailbox drafts that staff send), Send (policy-approved sending, canary first).
- Proposed new acceptance scenarios get ids in the [roadmap](04-roadmap.md). This record describes them in words and never reports them under a catalog id.

## How this record was produced

**Three independent proposals.** Each was written against the same sources: the spec, the acceptance catalog, the reference package and eight research-note files. Each used a different lens.

| Proposal | Lens | Biggest bet, as its author stated it |
|---|---|---|
| platform-proof | Buy the cheapest test of PL-063 that could fail | Agent-performed adaptation makes the second and third firm's integration-and-collection path much cheaper in audited engineering than the first (spec §27 experiments 3 and 6) |
| customer-value | Sell a monthly outcome a firm can feel | Mixed-stack CAS firms will pay about $15-$25 per active client-month for verified review packages, and the same engine reproduces with falling engineering minutes |
| learning-velocity | Resolve the §27 experiments and commercial unknowns fastest | Five paying, deliberately different firms run under a fully disclosed labor ledger are the cheapest way to earn the right to build the factory |

**Three judges.** Each scored every proposal independently on the same six criteria:

- Judge 1, a skeptical investor (seed to Series A). The deciding question: does day 180 produce credible evidence that firms 2 and 3 need clearly less human engineering than firm 1, with failed builds counted?
- Judge 2, a design-partner firm owner: a 15-person US bookkeeping and CAS firm on mixed QBO and Xero, Gmail, Drive and Karbon. The questions: would I sign, would I trust it with client communication, and would I pay?
- Judge 3, a principal engineer. The question: which plan is the most faithful and buildable path to the PL-063 proof? This judge checked load-bearing claims against the spec, the catalog, the accounting fixture and `plan_checker.required_maturity`.

**Scores by criterion, summed over the three judges:**

| Criterion | platform-proof | customer-value | learning-velocity |
|---|---|---|---|
| Spec fidelity | 27 | 24 | 21 |
| Customer value | 18 | 27 | 22 |
| Risk reduction | 27 | 21 | 23 |
| Small-team feasibility | 18 | 12 | 15 |
| Measurability | 27 | 24 | 27 |
| Market realism | 21 | 25 | 23 |
| **Total** | **138** | **133** | **131** |

**Totals by judge:**

| Proposal | Judge 1 (investor) | Judge 2 (firm owner) | Judge 3 (engineer) | Sum |
|---|---|---|---|---|
| platform-proof | 46 | 46 | 46 | 138 |
| customer-value | 45 | 44 | 44 | 133 |
| learning-velocity | 43 | 43 | 45 | 131 |

Platform-proof won every judge's total. Judge 3 ranked learning-velocity above customer-value for its experiment discipline.

**Synthesis.** The synthesis did not adopt the winner wholesale. For each decision it took the best-judged answer as the spine, then grafted in the strongest specific elements of the other two proposals. It also corrected the errors the judges found (listed under [Errors corrected during synthesis](#errors-corrected-during-synthesis)).

| Decision | Judge 1 pick | Judge 2 pick | Judge 3 pick | Spine used |
|---|---|---|---|---|
| D1 | platform-proof | platform-proof | platform-proof | platform-proof |
| D2 | customer-value | customer-value | platform-proof | customer-value, sequenced after platform-proof's readiness ledger |
| D3 | platform-proof | platform-proof | platform-proof | platform-proof |
| D4 | platform-proof | platform-proof | platform-proof | platform-proof |
| D5 | platform-proof | platform-proof | platform-proof | platform-proof |
| D6 | platform-proof | customer-value | learning-velocity | synthesis of all three |
| D7 | customer-value | customer-value | customer-value | customer-value |
| D8 | platform-proof | customer-value | customer-value | customer-value, with platform-proof's formal gate |
| D9 | platform-proof | platform-proof | platform-proof | platform-proof |
| D10 | platform-proof | platform-proof | platform-proof | platform-proof |
| D11 | platform-proof | platform-proof | platform-proof | platform-proof |
| D12 | platform-proof | platform-proof | platform-proof | platform-proof |

**Status: proposed.** Nothing in this record is ratified. The founder ratifies it through the [Founder decisions needed](#founder-decisions-needed) table, most items in P0.

## Strategy thesis

Plumb is a platform only if the second and third accounting firm need much less audited human engineering than the first, with failed, blocked and abandoned builds counted (PL-003, PL-062, ADR-010). If they don't, Plumb is a services firm with good contracts.

The first 26 weeks therefore buy the cheapest test of PL-063 that could fail. In parallel, a paid design-partner cohort tests whether firms will pay.

- **Beachhead.** US accounting firms of 10-40 staff that lean to client accounting services (CAS) and bookkeeping. They run mixed stacks (QBO and/or Xero, Google Workspace or Microsoft 365, a separate document store) and have at least 50 recurring monthly-close clients.
- **Wedge.** Monthly-close evidence readiness, shipped preparation-only.
- **Sequence.**
  - M0: a truthful registry, real SANDBOX_TESTED probe receipts on tenant 1's accounts, and a live effort ledger with a frozen rubric.
  - M1 on tenant 1: PA-001 plus a safety bundle. The agent fills in the BuildPlan and generates the client/period/obligation mapping on certified transport.
  - M1R right after, on tenants 2 and 3. Stack variation is designed in, and a provider swap forces a non-VERIFIED_ADAPTER path. This is PL-063's "next milestone", pulled forward from the M5 slot in the spec §26 table.
  - M3-lite: a preparation-only review-package workflow. PA-002 is attested in sandbox, then the workflow runs in production shadow with no external communication.
- **First measurable customer deliverable.** Verifier-attested ready-for-review packages on at least 30 client-periods in a full live close, measured against a month-0 time study.
- **Gating.**
  - Mailbox drafts, then policy-approved sends, come only after a production action gateway passes the HIGH-severity effect scenarios. That is after day 180.
  - Training, screen capture, posting, tax-return data and second domains wait behind evidence gates.
- **Commercial model.** Customers pay per active client-month for attested packages. Plumb never bills its own engineering.
- **North star.** Engineering-intervention hours per verified deployment (EIH/VD), reported per tenant in onboarding order. Platform-investment hours are shown beside it and never netted.
- **Honesty rules.**
  - Every threshold is a hypothesis, ratified at M0.
  - 90 days remains a hypothesis (spec §26 L418).
  - No claim exceeds its evidence, under the never-claim list (D8).

## Decisions at a glance

| ID | Title | Decision in one line | Spine |
|---|---|---|---|
| D1 | Beachhead and ICP | US CAS and bookkeeping-leaning firms, 10-40 staff, at least 50 recurring monthly-close clients, on mixed stacks | platform-proof |
| D2 | Wedge workflow and first measurable deliverable | Monthly-close evidence readiness, preparation-only. A readiness ledger at M1, then attested ready-for-review packages on at least 30 client-periods in the first full shadow close | customer-value |
| D3 | MVP scope (in/out) and generated vs certified paths | Build only the PL-063 path and what protects it. Put the gateway, Draft and Send behind evidence gates. Keep training, capture, posting, tax data and second domains out for 180 days | platform-proof |
| D4 | Definition of proof: M0 exit, M1, M1R and release bundles | M1 is PA-001 plus an agent-filled plan, an agent-generated mapping and a safety bundle. No "automatically constructed" claim before M1R | platform-proof |
| D5 | Milestone sequencing and calendar floors | M0, M1, M1R, M3-lite, M4-accounting, M5, then M2 and M6 behind gates. At least one close per stage | platform-proof |
| D6 | Approval granularity, interruption budget and effort rubric | Policy-level approval with materiality triggers and mandatory package sign-off. The Draft tier is the calibration ladder. Numeric interruption budget; rubric frozen in week 1 | synthesis |
| D7 | Pricing, unit of value and pilot terms | Per active client-month: Prepare $15, Prepare + Chase $25. Bill only attested packages. Paid pilot of $1,500-$3,000, credited to year one | customer-value |
| D8 | Positioning, category and never-claim guardrails | "Verified implementation" and "Close-ready, with receipts", with a 12-item never-claim checklist as a formal gate | customer-value |
| D9 | Design-partner program and contract essentials | Five accounting firms, each with an evidentiary role, LOIs signed before M1 completes. Contracts settle SERVE, TRAIN, IRC 7216, revocation, ledger publication and exit | platform-proof |
| D10 | North star and supporting metrics | EIH/VD per tenant in onboarding order. Customer co-headline: accepted review packages per month | platform-proof |
| D11 | Top risks and kill/pivot criteria | R1-R7, each with pre-registered kill or pivot criteria | platform-proof |
| D12 | Team gaps and hiring timing | Security/platform engineer in weeks 0-4 and an independent verification engineer by week 6. Eval hire re-scoped. No per-customer delivery engineers | platform-proof |

---

## D1 Beachhead and ICP

### Decision

Beachhead: independent US accounting firms whose revenue leans to client accounting services (CAS) and bookkeeping.

**Profile** (all thresholds are hypotheses):

| Attribute | Qualify in |
|---|---|
| Staff | 10-40 |
| Revenue mix | At least 60% from recurring bookkeeping or CAS, so the Feb-Apr tax season does not stall the domain owner |
| Clients | At least 50 recurring monthly-close clients with 12-24 months of history |
| Ledgers | QBO and/or Xero client ledgers |
| Mail | Google Workspace or Microsoft 365 |
| Documents | A store separate from the ledger: Drive, SharePoint/OneDrive, Dropbox or SmartVault |
| Practice management (optional, read-only) | Karbon, Financial Cents or Double |
| Region | One US region. The accounting fixtures are EUR/eu-west-1 and must be re-templated (see [corrections](#corrected-or-clarified-while-rendering-this-record)) |

**Roles** (canonical personas):

| Persona | Who at the firm | Role in the product |
|---|---|---|
| Firm owner (buyer) | Managing partner, COO or CAS director | HUMAN_OWNER of the autonomy envelope; grants authority and approves the implementation card |
| Reviewing accountant (champion, primary user) | The reviewing manager or senior accountant who assembles packages today | Reviews and signs off review packages |
| Bookkeeper (secondary user) | Staff who chase clients | Needs one shared obligation owner across staff |
| Firm's client (affected party, not a principal) | The firm's small-business clients | Receives requests only once the Draft or Send tier ships |

**Cohort design: vary stacks on purpose.**

- Tenants 1 and 2 share provider families but differ in folder structure and chart-of-accounts conventions. These are the PA-027 preconditions.
- Tenant 3 swaps one provider.
- At least one cohort firm has both QBO and Xero clients.
- One optional slot for a PE- or VC-backed roll-up, as a channel probe off the critical path.

**Qualify out:**

1. Solo and 2-4-person firms.
2. Top-100 and 100+-staff firms, where Basis and FloQast compete.
3. Tax-only or seasonal practices, and any in-scope source holding tax-return information (IRC 7216).
4. Firms standardized on one ecosystem whose native chase-and-match already works (Xero Partner Hub/JAX/XeroForce, Intuit Accountant Suite, Double on one ledger), unless they want Plumb to configure and verify those native features.
5. Desktop or on-prem ledgers, and NetSuite/Intacct.
6. Evidence held in closed portals that cannot be probed (PL-007, PL-008).
7. Document stores without webhooks plus overlap polling, and mail providers without request-id lookup. PA-005 and PA-009 cannot pass on them.
8. Firms expecting posting or an "autonomous close".
9. Firms that will not do all of the following: grant read OAuth, name a domain owner with about 2 hours a week, run a 2-week baseline time study, and allow anonymized publication of labor-ledger data.
10. Firms needing on-prem or multi-region.

### Rationale

**Why accounting fits a platform proof.** The proof needs many tenants that are similar but not identical, and an outcome a domain owner can judge (the M0 evidence in the spec §26 table). Accounting has the spec's most complete trace (spec Appendix B). It also holds 13 of the 30 catalog scenarios, including the M1, M2, M3 and M5 evidence scenarios (PA-001, PA-012, PA-002 and PA-027).

**The pain is documented** (survey sources, mostly vendor-run):

- Getting documents from clients is the top workflow problem. The source gives a rank only, no percentage (Financial Cents 2025, 816 professionals [M3]).
- 68% would hand chasing to an agent first. The sample is small and self-selected, so treat it as directional (Uku 2026 [M4]).
- Hiring experienced staff is the #1 issue for firms with 11-30 professionals (AICPA PCPS, June 2026 [M2]).
- The top adoption barrier is implementation time: 41% in Financial Cents 2026 [M6] and 31% in Ramp/CalCPA [M7]. Cost is cited by only 6% [M6].

**The segment is countable.** Census SUSB 2022 shows about 13.4k CPA firms with 5-19 employees, and about 3.3k CPA and other-accounting firms with 20-99 employees (2,015 plus 1,247). These are employer firms only [M1].

**Mixed stacks are the opening.** Firms average about 10 apps, and 48% call their setup functional but fragmented (Intuit 2026 survey, vendor-run [M5]). Incumbents optimize inside one ledger. Basis reports penetration concentrated in the top 25 and top 150 firms (vendor-reported [M8]).

**A recorded tension.** 88% of accounting professionals already use AI for at least one service [M5]. Spec §1 L49, by contrast, targets "an ordinary business with little or no existing AI". In this segment Plumb's value is implementation and verification, not first exposure to AI.

### Alternatives considered

- 5-30 staff with at least 40 clients (customer-value, learning-velocity). A broader pool, but a weaker capacity-pain signal.
- A single-ecosystem, QBO-centric focus. Faster to certify and a larger pool, but it runs head-on into Intuit's Accountant Suite, which is free during its introductory period [M14].
- Laundry route preparation (learning-velocity's alternative). Daily cycles and a shadow-only plan, but only 4 catalog scenarios and no market research.
- Industrial RFQ. 7 catalog scenarios, no market notes.
- PE roll-ups as the primary buyer. Procurement drag, and they build in-house (Current, formerly Crete [M31]).
- Canada or the UK first. Xero dominance makes much of those markets a qualify-out.

### Revisit trigger

- In the first 25 qualified calls, fewer than 30% of firms have materially mixed stacks, or mixed-stack firms show no more pain or willingness to pay than single-ledger firms. Then: narrow to QBO-centric firms whose evidence lives in email and drives.
- 60% or more of qualified prospects are single-ecosystem with chase-and-match covered. Then: re-open the vertical.
- Fewer than 4 LOIs on any terms by week 10. Then: shift to the roll-up channel or re-open the vertical.
- M0 probes show ledger authorization is granted per client company, pushing onboarding CUSTOMER_AUTHORIZATION above 4 hours per firm. Then: re-scope the stack.

### Sources

PL-002, PL-007, PL-008; PA-005 (catalog L338), PA-009 (catalog L519), PA-027 preconditions (catalog L1363-1416); spec §1 (L49), spec Appendix B (L590-654; L654 is the next-three-customers expansion test); [accounting envelope fixture](../fixtures/envelopes/accounting_evidence_preparation.json) (`allowed_regions` eu-west-1, EUR spending limit). Research notes: market-accounting, market-implementation, acceptance-and-index. Market: [M1]-[M8], [M14], [M31].

---

## D2 Wedge workflow and first measurable deliverable

### Decision

**Wedge: monthly-close evidence readiness.** For every recurring client-period, Plumb knows which required documents are PRESENT, CONFIRMED_ABSENT or UNKNOWN, with provenance, and who has already chased them. PL-010 requires unknown absence to stay distinguishable from confirmed absence, and the package already has a `Presence` enum with exactly these three values. Plumb then prepares one ready-for-review package per client-period (the spec Appendix B goal). It starts preparation-only.

Visible results arrive in this order:

| # | Result | What it is | Constraints |
|---|---|---|---|
| 0 | Month-0 baseline | A 2-week time study of accountant assembly and review minutes. The firm owner runs it with Plumb's domain expert before shadow, so the time-saving claim can be falsified | Before shadow |
| 1 | The M1 moment, and the interim deliverable | A read-only close-readiness ledger built on the PA-001 collection path. A document a client drops into the firm's folder appears exactly once, attributed to the right client and period, with lineage, within the 5-minute health deadline | Uses only the READ and COLLECT effect classes, so the first value needs no gateway writes and none of the HIGH-severity effect scenarios. The platform proof and the customer value are the same artifact |
| 2 | Historical duplicate-chase baseline | Once mail-history read is connected (phase 2), a 24-month reminder backfill shows duplicate chases per client-period-obligation, re-requests for documents already held, and days to receive | Labeled historical and non-causal (spec §7 L136). Never counted as a PL-001 outcome |
| 3 | First measurable deliverable | In the first full live close after the preparation-only workflow enters production shadow: verifier-attested ready-for-review packages on an agreed cohort of at least 30 client-periods per firm, with zero external sends, compared with the accountants' actual decisions in a "what Plumb would have done" report | Measures: correct-package rate; accountant assembly-plus-review minutes against the month-0 study; false-chase rate (PA-005 class); missing-item recall; wrong-client attribution (PA-003 class) |
| 4 | Gated | First, consolidated requests as mailbox drafts that staff send (Draft). Then policy-approved sends (Send): one per client-period-obligation epoch, with one owner across staff | After the production gateway passes its gates (D4) |

The cohort size of 30 and all quality targets are hypotheses.

### Rationale

**What incumbents do and do not offer.** Chase-and-remind is table stakes. Per-client close add-ons and practice-management seats run from about $5 a month (Financial Cents close add-on) to $99 a month (Karbon monthly seat) [M11], [M12]. Intuit's Accountant Suite is free during its introductory period (in the US per a secondary source) [M14]. Xero Partner Hub offers Document Requests that chase and match, at undisclosed pricing [M15]. What incumbents do not produce across a mixed stack is a provenance-backed package that separates unknown from confirmed absence (PL-010). That separation is what stops "please send the document you already sent" (PA-005, PA-011).

**Why the collection path is the first deliverable.** PL-063 makes the collection path the first thing to prove. Making it the interim deliverable avoids a throwaway demo.

**Grounding in the spec and fixtures.** PL-035 separates read-only preparation from external effects. The accounting fixture already has a shadow step (`activate-shadow-processing`) that compares outputs with the accountant's actual decisions. The fixture's goal metric is measured "prospectively against the pre-deployment baseline".

**The baseline closes a gap.** The appendices notes observe that nothing captures accountant assembly time before deployment.

**Correction to customer-value.** Its pre-sale baseline "within days of consent" assumed a reminder-history backfill collector that does not exist until phase 2.

### Alternatives considered

- Lead with policy-approved chasing. Chasing is a commodity, and it puts the HIGH effect scenarios first.
- Make the readiness board alone the billable deliverable (learning-velocity). PL-001 does not count a recommendation as an outcome, and firms may see only a report.
- Drafts from close #1 (customer-value's fallback). Impossible before the production effect ledger exists.
- Platform-proof's ordering, readiness ledger then shadow report, without the 30-client-period package target. Weaker customer pull.

### Revisit trigger

- Fewer than half of active bookkeepers at partner firms use the readiness ledger weekly, or at least 2 partners say they will not continue without sending. Then: run shadow packages in parallel with M1R.
- In the first two shadow closes, accountant minutes per client-period fall by less than 25% against baseline, or packages are opened in Plumb for less than 50% of in-scope client-periods, while chasing still dominates the time study. Then: promote the Draft tier to lead deliverable as soon as the production gateway passes its Draft gates. Those gates are never skipped.

### Sources

PL-001, PL-009, PL-010, PL-025, PL-035; PA-001, PA-003, PA-005, PA-011; spec §7 (L136, no causal claims from historical replay); spec Appendix B (L596 goal and deliverable; L612 collection path proven only by an observed live change); [accounting plan fixture](../fixtures/plans/accounting_evidence_preparation.json) (`activate-shadow-processing`); [accounting envelope fixture](../fixtures/envelopes/accounting_evidence_preparation.json) (`goals.success_metric`); `plumb/contracts/common.py` (`Presence`). Research notes: market-accounting (positioning), appendices (missing baseline instrumentation; shadow report). Market: [M11], [M12], [M14], [M15].

---

## D3 MVP scope (in/out) and generated vs certified paths

### Decision

**IN for M0/M1 (tenant 1):**

- (a) EnvironmentInventory with real probes of document-store and ledger-metadata operations (PL-007, PL-008).
  - A truthful registry that earns SANDBOX_TESTED probe receipts on tenant 1's real accounts for `integration.configure`, `collection.backfill` and `collection.enable_incremental`. That is the checker's floor for non-shadow writes.
  - DOCUMENTED is the checker's floor for read steps. PA-001's preconditions, however, require SANDBOX_TESTED inventory records for `list_folder_changes` and `fetch_document`, so M0 earns SANDBOX_TESTED for those two reads as well.
- (b) An agent fills in the tenant BuildPlan from a registry template.
  - `check_plan` is wired to the tenant EnvironmentInventory and to capability `required_authority` (PL-014, PL-015).
  - State-machine guards call the checkers.
- (c) A durable build ledger and bounded repair (PL-017, PL-018).
- (d) Integration factory (PL-019, PL-020, PL-021, PL-022, PL-054):
  - Certified transport connectors through a contract-tested substrate. Nango is the candidate.
  - Agent-generated semantic mappings, as declarative config or as generated code in a disposable sandbox. They map folder and naming conventions to client+period+obligation, and cover chart-of-accounts conventions.
- (e) Collection factory: shadow, backfill from an agreed watermark, reconcile, incremental, health (PL-023, PL-024, PL-025).
- (f) Evidence store with three time axes, fact status and scoped corrections (PL-009, PL-010, PL-011).
- (g) A thin independent verifier and the fault-injection harness (PL-042, ADR-007).
- (h) Effort accounting (PL-003, PL-059, PL-062, ADR-010):
  - A human-effort ledger that automatically captures every human-principal action on tenant resources.
  - A separate platform-investment ledger.
  - The autonomy metric.
- (i) The database, API, object-storage, cache, log and export subset of tenant isolation (PL-052).
- (j) The minimum Appendix A.6 surfaces: implementation card, blocked-dependency card, honest progress feed, results-and-effort view, read-only close-readiness ledger.
- (k) A published "supported environments v1" list, stated per operation and maturity level.
- (l) A focused-question queue with a per-workflow budget.

**IN for phase 2 (M3-lite):**

- Read-only mail history.
- A preparation-only WorkflowSpec over certified primitives (PL-035, PL-036): deterministic obligation checks, engagement-checklist templates, and general-model extraction through the gateway. No training.
- A ReviewPackage contract. Today the package has only a `REVIEW_PACKAGE` artifact-kind label, with no contract behind it.
- An accountant sign-off surface that captures explicit accept, correct or amend. It doubles as the prospective correction collector and keeps the ADR-006 option open cheaply.
- A narrow release executor on fixed approved templates (PL-045), plus a platform qualification run. That run earns real PRODUCTION_VERIFIED receipts for `release.create` and `release.activate_shadow` (the checker's floor) before any tenant shadow.
- Pause and kill from SHADOW and CANARY (PL-047). Today the package's RELEASE machine allows PAUSED only from ACTIVE.
- An explicit SERVE grant before the first shadow.

**IN for phase 3 (gated, mostly after day 180):**

- A production action gateway: outbox, leases, and dispatch-time authority, revocation and pause checks (PL-037, PL-038, PL-039).
- Draft tier: a consolidated request created in the owner's mailbox. That is an EXTERNAL_WRITE_REVERSIBLE effect, needing SANDBOX_TESTED maturity and effect-slot dedup, so it sits behind the production effect ledger.
- Send tier: a policy-approved canary.

**OUT for 180 days:**

- The learning factory beyond the prospective collector: no `training.submit` and no TrainingSpec execution (PL-032, PL-033).
- Transaction categorization.
- Screen or visual capture.
- Posting and any FINANCIAL_COMMITMENT.
- Open-ended discovery. It is replaced by a vertical opportunity library in which Plumb still writes a complete OpportunitySpec with a native-feature baseline (PL-012, PL-013). Plumb may conclude "configure the firm's Xero or Financial Cents reminders", and that counts as a delivered intervention.
- UI adapters.
- Generic infrastructure generation.
- The maintenance agent. Operations stay manual and are logged: manual deploys as ENGINEERING_INTERVENTION, fixes to running collectors as OPERATIONAL_REPAIR.
- Tax-return data.
- Multi-region.
- Second domains.

**GENERATED vs CERTIFIED:**

- Follow PL-020's preference order and reuse certified transport.
- Require tenant-specific semantics to be agent-generated.
- Deliberately swap one provider at tenant 3, so a non-VERIFIED_ADAPTER path is exercised before any "automatic construction" claim.

**Maturity floors on the accounting fixture plan.** The package's `required_maturity` function sets these floors. They were verified on 2026-10-04 by running the checker against a registry reset to DOCUMENTED.

| Step types in the accounting plan | Effect class | Floor (package) | How it is earned (proposed) |
|---|---|---|---|
| `inventory.probe`, `source.profile`, `integration.contract_test`, `collection.reconcile`, `dataset.discover_sources`, `dataset.label_audit`, `evaluation.run`, `workflow.test_bundle`, `infrastructure.preview`, `verification.request` | READ | DOCUMENTED | M0 probes. PA-001 additionally needs SANDBOX_TESTED inventory records for `list_folder_changes` and `fetch_document` |
| `collection.deploy_shadow` | INTERNAL_WRITE | DOCUMENTED (shadow exemption) | M0 |
| `integration.configure`, `collection.enable_incremental` | EXTERNAL_WRITE_REVERSIBLE | SANDBOX_TESTED | M0 sandbox probe receipts on tenant 1 |
| `collection.backfill` | INTERNAL_WRITE (not shadow) | SANDBOX_TESTED | M0 |
| `workflow.compile` | INTERNAL_WRITE | SANDBOX_TESTED | A sandbox receipt before the M3-lite build (added while rendering; see corrections) |
| `dataset.build`, `training.submit` | INTERNAL_WRITE | SANDBOX_TESTED | Out of scope until M2 |
| `release.create`, `release.activate_shadow`, `release.canary` | release.* | PRODUCTION_VERIFIED | Platform qualification run in M3-lite for create and activate_shadow; canary at M4-accounting |
| `infrastructure.apply` | INFRASTRUCTURE_CHANGE | PRODUCTION_VERIFIED | The same qualification run, if the tenant plan keeps the fixture's serving-infrastructure step |
| `dependency.raise` | INTERNAL_WRITE | DOCUMENTED | Already sufficient |

### Rationale

**Why each item is in or out.** Every IN item sits on the PL-063 critical path or protects it. Every OUT item is something the spec or the market says is optional, unproven or blocked.

**Training stays out.**

- It is the largest step in the accounting plan: EUR 2,500 of the EUR 10,060 step-budget sum (verified in the fixture).
- PA-012 does not require training. Its `requires` tags are real_adapter, grants and model.
- If serving a small model needs idle dedicated capacity, its total cost can exceed a general model API (spec §14 L232).
- 53% of surveyed small firms refuse training on their data (Uku 2026, directional [M4]).

**Capture stays out.** Raw capture is about 34.6 GB/day per 100 employees (spec §24 L378), and experiment 1 is unresolved.

**External effects wait for a real gateway.** The package's effect ledger is a SQLite simulation, and its RELEASE machine cannot pause a canary. Starting preparation-only keeps PA-005, PA-006, PA-007 and PA-009 off the path to first value.

**Correction to platform-proof.** A truthful registry blocks more than `release.*` and `infrastructure.apply`. Configure, backfill and enable_incremental also need SANDBOX_TESTED, so M0 must earn those receipts. And `release.activate_shadow` needs PRODUCTION_VERIFIED, which puts a release-executor bootstrap on the shadow critical path.

**Correction to customer-value and learning-velocity.** A mailbox draft is an external write. It is not an action with "no external effect".

### Alternatives considered

- The full Appendix B plan including training, as in the fixture.
- Learning-velocity's draft-to-mailbox in M3, ahead of the production gateway. Rejected: it is an external write without a production effect ledger.
- Learning first, to showcase ADR-006.
- Capture-based discovery.
- Months of generic platform construction first. Spec Appendix A.7 (L586) says to build vertical proofs in dependency order instead.
- Deferring the release executor entirely (learning-velocity). Rejected: shadow and canary need release activation and pause.

### Revisit trigger

- The baseline time study shows accountant time is dominated by transaction categorization, TRAIN grants exist on at least 2 tenants, and there are at least 500 explicit corrections with classification errors at 25% or more of review minutes. Then: open M2 earlier.
- At least 2 of 3 partners make reminders a condition of continuing. Then: accelerate the gateway work, never skipping the HIGH scenarios.
- More than 20% of obligations stay UNKNOWN after two closes because of off-system handoffs. Then: run a bounded, event-triggered capture experiment.

### Sources

PL-007, PL-008, PL-012, PL-013, PL-014, PL-015, PL-017, PL-018, PL-019, PL-020, PL-021, PL-022, PL-023, PL-024, PL-025, PL-032, PL-033, PL-035, PL-036, PL-037, PL-038, PL-039, PL-042, PL-045, PL-047, PL-052, PL-053, PL-054; ADR-006, ADR-007, ADR-010; PA-001 (preconditions), PA-012; [plan_checker.py](../plumb/checker/plan_checker.py) (`required_maturity`, L217-238); [accounting plan fixture](../fixtures/plans/accounting_evidence_preparation.json) (configure and enable_incremental are EXTERNAL_WRITE_REVERSIBLE; backfill is INTERNAL_WRITE; training EUR 2,500 of 10,060; "No adapter code is generated for this customer"); [machines.py](../plumb/statemachines/machines.py) (RELEASE transitions); spec §14 (L232), §24 (L378), §27 (L442), Appendix A.7 (L586-588). Research notes: implementation-reality (registry has 15 synthetic PRODUCTION_VERIFIED entries; SERVE never enforced; ReviewPackage has no contract; the ledger does not check pause or authority). Market: [M4].

---

## D4 Definition of proof: M0 exit, M1, M1R and release bundles

### Decision

**M0 exit checklist.** No catalog scenario covers M0.

- A named domain owner.
- An outcome definition the owner can judge, with a denominator.
- SANDBOX_TESTED probe receipts for the exact operations on tenant 1's real accounts.
- No synthetic PRODUCTION_VERIFIED claims left in the registry.
- Threat model signed off.
- Month-0 baseline captured or scheduled.
- Effort ledger live with the frozen rubric.
- Tenant 1 DPA and envelope signed.

**M1 (the first half of PL-063), tenant 1.** M1 passes only when all of these hold:

1. PA-001 passes as written, with a verifier attestation. `path_used` VERIFIED_ADAPTER is acceptable for transport, because PL-020 requires preferring it.
2. The agent filled in the BuildPlan from the tenant's EnvironmentInventory. Any human-authored or human-edited tenant plan or mapping is logged as ENGINEERING_INTERVENTION.
3. The client/period/obligation mapping and the CollectionSpec were agent-generated and contract-tested. Declarative config is acceptable.
4. The attested run has zero ENGINEERING_INTERVENTION, and every earlier failed eligible attempt is in the denominator.
5. The safety bundle passes:
   - PA-015, PA-019 and PA-022.
   - The collector half of PA-005: backfill/live convergence, webhook dedup and authoritative fetch. It is reported as a partial run, not as a PA-005 pass.
   - The health half of PA-011, also reported as partial.
   - An accounting adaptation of PA-023's account_boundaries contract test. PA-023 itself is an industrial_rfq scenario needing two ERP accounts, so it is not claimed as passed.
   - The PA-017 surfaces for database, API, object storage, cache, logs and exports, before any second tenant's data arrives.
   - An accounting adaptation of PA-021's parser bounds whenever document contents are parsed. Mandatory by M3-lite.
   - PA-026 on the first tenant where generated code runs.

**Claim rule until M1R.** Say "agent-configured certified connectors and agent-built collection". Never say "generated integrations" or "automatically constructed".

**M1R (the second half of PL-063, "the next milestone"), tenants 2 and 3:**

- PA-001 re-attested per tenant, on the same engine, with no code fork.
- At least one operation on a DECLARATIVE_CONFIG or GENERATED_CODE path (tenant 3's provider swap), with PA-026 and PA-019 re-run on it.
- PA-027's ledger-audit and denominator method applied to the integration-and-collection path. This is not reported as a PA-027 pass, which also requires review-package quality and first-month review hours.
- The PA-017 surfaces re-run with co-resident tenants.

**M1R pass hypothesis:**

- Engineering-intervention hours per verified path, counted across all attempts, fall at each tenant, with tenant 3 at or below 50% of tenant 1.
- Platform-investment hours triggered by each tenant are reported and never netted.
- An auditor outside the delivery team finds zero unrecorded manual work.
- Only then may Plumb say "automatically constructed".

**Release bundles by tier.** Bundle membership is the decision. All numeric gates are hypotheses.

| Tier / milestone | Catalog scenarios that must pass | Adaptations run, never reported as the catalog id | Environment |
|---|---|---|---|
| Prepare (M3-lite) | PA-002 as written in sandbox, where its single send goes only through the sandbox mail adapter against sandbox copies of the sources; PA-003, PA-004, PA-006, PA-008, PA-010, PA-011 | PA-021 parser bounds on client PDFs. A preparation-mode variant of PA-002 is proposed to the catalog and is never reported as PA-002 | Sandbox, then production shadow with no EXTERNAL_COMMUNICATION in the envelope |
| Draft | Against draft creation on the production gateway: PA-005's dispatch-time re-check; PA-009 and PA-015 behaviors; PA-006 and PA-010 approval binding | None | Production gateway; pause and kill from CANARY must work |
| Send (M4-accounting) | Full PA-002 in canary; PA-005; PA-007, which needs concurrent ACTIVE and CANARY releases; PA-009; PA-010 | The PA-014 revocation-race mechanism and a PA-016-style schema-drift repair on an accounting source. Both are RFQ-domain scenarios, run as accounting adaptations | Canary, plus a recovery drill and recorded support effort |
| M5 | Full PA-027 on the next three customers (tenants 2-4), with at least one month of prospective measurement; full PA-017 before any training job | None | Production |

**Labeling:**

- Never call a deployment "autonomous" without showing its ledger.
- Label deployments "supervised", with their labor shown, until that path has PA-027-level evidence.

**Proposed catalog changes.** Ids for the new variants are assigned in the [roadmap](04-roadmap.md).

- Raise PA-027 from MEDIUM to HIGH for any release marketed as autonomously implemented.
- Add a generated-path PA-001 variant, a preparation-mode PA-002 variant and a policy-level PA-010 variant.
- Add accounting analogues of PA-013, PA-014, PA-016, PA-021 and PA-023.
- Add M0 and M6 scenarios.

### Rationale

**PA-001 alone is not enough.** On its own, PA-001 proves only that Plumb can orchestrate a pre-built adapter (acceptance-and-index notes, tension 3). PL-063 asks for "automatic construction", and Appendix A.7 lists a "generated adapter and collector" in its vertical-proof order (L586). Both ask for more.

**Variation lives in semantic mapping.** Tenants differ in folder structures, chart-of-accounts conventions and minor API versions (spec Appendix B L654; PA-027 preconditions). Requiring an agent-generated mapping tests the right thing without breaking PL-020's preference order.

**What the bundle, the staging and the two ledgers buy.**

- The safety bundle stops PA-001 from passing on an unsafe collector.
- Staging PA-017 resolves its dependency on training: its `requires` tags include training.
- Two ledgers enforce the spec §26 table's M6 rule that new adapter and domain work is "measured separately".

**Corrections to the proposals.**

- All three listed RFQ-domain scenarios (PA-014, PA-016, PA-021, PA-023) as if they could pass on accounting tenants.
- Customer-value counted a preparation-mode PA-002 as PA-002.
- Platform-proof did not say that PA-002's send runs only in sandbox.
- PA-007 can pass only at the canary.

### Alternatives considered

- PA-001 as written satisfies M1, with the generated path only at M1R (customer-value, learning-velocity). Lower M1 scope, but it proves orchestration only.
- Require connector code generation at M1. Contradicts PL-020.
- Replicate on one tenant only (customer-value's firm B). A single comparison, with no trend.

### Revisit trigger

- Tenant 1's semantics map fully through declarative configuration. Then: accept DECLARATIVE_CONFIG as the construction evidence, and move PA-026 to the first tenant needing generated code.
- Sandbox and egress infrastructure slips more than 4 weeks. Then: attest M1 on PA-001 plus the rest of the bundle, and move the generated-path requirement to tenant 3 in M1R.
- Every partner is fully covered by certified connectors plus declarative config. Then: measure mapping and config reuse instead of code generation.

### Sources

PL-020 (spec §10 L170), PL-022 (spec §10 L174), PL-063 (spec §26 L404); PA-001 (catalog L125-183: `path_used` VERIFIED_ADAPTER; any ENGINEERING_INTERVENTION fails), PA-002 (catalog L185-241: send through the sandbox mail adapter), PA-007 (catalog L425-470: rel_13 ACTIVE and rel_14 CANARY), PA-014 (catalog L758), PA-016 (catalog L848), PA-021 (catalog L1102) and PA-023 (catalog L1188), all industrial_rfq; PA-027 (catalog L1363-1416, MEDIUM); PA-005, PA-006, PA-008, PA-009, PA-010, PA-011, PA-013, PA-015, PA-017, PA-019, PA-022, PA-026; spec Appendix A.7 (L586); spec §26 table, M6 row (L414). Research notes: acceptance-and-index (minimal M1 bundle; staged PA-017; PA-027 severity).

---

## D5 Milestone sequencing and calendar floors

### Decision

**Order:**

1. M0.
2. M1: tenant 1 integration and collection.
3. M1R: the same path on tenants 2 and 3. This is PL-063's "next milestone", moved forward from the spec §26 table's M5 position.
4. M3-lite: a preparation-only review workflow, sandbox then production shadow. It runs as a parallel track once M1 passes.
5. M4-accounting: production action gateway, Draft tier, then a policy-approved Send canary of consolidated requests.
6. M5: full PA-027 on the next three customers, tenants 2-4.
7. M2: learning factory, gated.
8. M6: a second domain, laundry route preparation, whose fixture plan already stops at shadow. Gated by PA-013, PA-025, PA-029 and PA-030. RFQ comes after.

Re-anchoring M4 on accounting means M1 through M5 need only accounting partners.

**Calendar floors:**

- Backfill and reconcile 12-24 months of history per tenant.
- Shadow for at least one full monthly close. The fixture's 1,209,600 s (14 days) is a `max_elapsed_seconds` budget: an upper bound, not a floor.
- Draft for at least one close.
- Canary for at least one close. The fixture's 1,814,400 s (21 days) is also an upper bound.
- PA-027 needs at least one month of live operation after verified deployment.
- The monthly cadence allows about 6 closes in 180 days.
- The earliest credible renewal decision is about three closes after connection.

One corollary was added while rendering. Both fixture budgets are shorter than the one-close floor, and the fixture plan's total budget is 5,184,000 s (60 days). A real tenant plan that runs shadow and canary for a full close each needs larger step and total budgets than the fixture.

**Tax season and concurrency:**

- US tax season (Feb to Apr 15) slows customer-side inputs. Collect tenants 2 and 3's grants, domain clarifications and baseline studies before mid-January.
- Firm B runs its baseline close in parallel with M1R, so it still sees value.
- At most 3 active builds until M1R passes.

**Result:**

- Tenant 1 shadow results land around weeks 20-26.
- A second tenant's full-close shadow reading may land after day 180.
- The Send canary and M5 cannot finish before about weeks 30-36, even if everything goes right.
- "90 days" stays a hypothesis.

**M2 entry gates.** All are required. The domain expert ratifies the thresholds.

- Audited join precision of at least 90% on a PA-012-style 100-pair accountant sample.
- TRAIN grants on at least 2 tenants.
- At least 500 explicit accept/correct events.
- Either classification errors account for at least 25% of review minutes, or a candidate comparison shows a reviewer-time gain.

**Phase map.** All windows are hypotheses, and each window starts on its gate's exit. The [roadmap](04-roadmap.md) holds the full phase plan and assigns every catalog scenario to a phase.

| Phase | Window | Objective | Key exit evidence | Catalog scenarios |
|---|---|---|---|---|
| P0 Commit and instrument | Weeks 0-2 (Oct 5-18, 2026) | Commit to the platform-proof scope and instrument the learning before building anything else | Rubric, threshold sheet, experiment charter and never-claim checklist signed by the founder and domain expert; zero synthetic PRODUCTION_VERIFIED records; effort ledger records entries end to end, including failed attempts; at least 8 qualified ICP conversations; vendor approval timelines known; partner contract template drafted with data-rights tiers | None |
| P1 M0: contracts, probes and ledger | Weeks 2-8 (Oct 19-Nov 29, 2026); gated on tenant-1 access | Build the control-service skeleton around the existing kernel, and earn real probe receipts on tenant 1 | M0 checklist passes, including SANDBOX_TESTED receipts for `list_folder_changes`, `fetch_document`, the collector-write operations and ledger-metadata reads; substrate contract tests pass; tenant 1 DPA and envelope signed and paid pilot invoiced; at least 3 more LOIs (tenants 2-4) | None (M0 has no catalog scenario) |
| P2 M1: tenant 1 integration-and-collection path | Weeks 8-14 (Nov 30, 2026-Jan 10, 2027); sandbox build work may begin from week 6 | Prove automatic construction on tenant 1; ship the read-only close-readiness ledger | PA-001 attested as in D4, plus the safety bundle; tenant 1's EIH/VD baseline; time to first verified event, split into Plumb-controlled and dependency time; tenant 1's 90-day pilot clock starts. Runway rule: if PA-001 has not passed by week 14, cut scope to one ledger and one document store | PA-001, PA-005 (collector half), PA-011 (health half), PA-015, PA-017 (surface subset), PA-019, PA-022, PA-026 (if generated code ran) |
| P3 M1R: reproduction on tenants 2 and 3 | Weeks 12-20 (Dec 28, 2026-Feb 21, 2027); starts on M1 attestation | Prove the path reproduces for new customers with explicit labor accounting | PA-001 for both tenants with at least one non-VERIFIED_ADAPTER operation; PA-026 and PA-019 on the generated path; PA-017 surfaces with co-resident tenants; EIH/VD falls, tenant 3 at or below 50% of tenant 1; reuse recorded with fork count 0; audit finds zero unrecorded manual work; experiment-1 proxy recorded; R1 checkpoint memo | PA-001, PA-017, PA-019, PA-026 |
| P4 M3-lite | Weeks 14-22 (Jan 11-Mar 7, 2027); parallel track gated on M1, not on M1R | Compile and attest a preparation-only review-package workflow, then run it in production shadow on tenant 1 | PA-002 run as written in sandbox with a BUSINESS_OUTCOME attestation; PA-003, PA-004, PA-006, PA-008, PA-010 and PA-011 pass in sandbox; PA-021 parser-bounds adaptation passes; numeric correct-package threshold set; DOMAIN_CLARIFICATION per workflow measured; production shadow active with no EXTERNAL_COMMUNICATION | PA-002, PA-003, PA-004, PA-006, PA-008, PA-010, PA-011 |
| P5 Shadow results, gateway hardening and day-180 decision packet | Weeks 20-26 (Feb 22-Apr 4, 2027); day 180 is Apr 3, 2027 | Deliver the first measurable customer deliverable on tenant 1, harden the gateway in sandbox, and decide go, pivot or kill | Attested packages on at least 30 client-periods across a full close; correct-package rate against threshold; minutes against baseline; false-chase rate of 2% or less and recall of 90% or more; tenants 2-3 shadow started; owner time within budget, repeat asks 0; gateway sandbox crash tests; day-180 packet | PA-005, PA-009, PA-015 |
| P6 M4-accounting and M5 | Weeks 26-36 or later (Apr-Jun 2027), earliest; evidence-gated | Graduate from preparation to effects safely, and prove replication of the full workflow on the next three customers | Canary report with denominators and effect receipts; zero duplicate, stale or wrong-client requests reached real clients; PA-005, PA-007, PA-009 and PA-010 pass; PA-027 passes; at least 2 of the first 4 partners on paid annual at $15 or more per active client-month | PA-002, PA-005, PA-007, PA-009, PA-010, PA-017, PA-027 |

### Rationale

**PL-063 conflicts with the spec §26 table.** PL-063 says the milestone after the first must prove reproduction for a new customer. The table instead places replication at M5, after M2-M4. Following the table delays the platform verdict by months.

**Early replication is the cheapest learning.** It gives the first read on experiment 3 (cheap adapter adaptation) and experiment 6 (maintainable reuse).

**The table's M4 evidence is in the wrong domain.** PA-013 is a laundry scenario. Following it would force a second-domain partner before M5.

**Learning waits.**

- PA-012 does not need training.
- Training rights are scarce.
- The trained path often loses on total cost.

**Corrections to platform-proof.**

- The fixture's shadow and canary durations are upper bounds, not floors.
- With M3-lite exiting around week 22, a two-tenant full-close shadow gate by day 180 would likely slip. The day-180 packet therefore commits to tenant 1 only.

### Alternatives considered

- The spec table's order: M1, then M2, M3, M4 and M5. It replicates the full stack, but it delays the platform verdict and needs a laundry partner for M4.
- Customer-value's Send canary inside 180 days. Rejected: the gateway is not built, and the plan would have to compress tax season and the calendar floors.
- Learning-velocity's option to fold M1R into M5 if adaptation turns out trivial. Kept as a revisit trigger.

### Revisit trigger

- M1 shows the path is mostly substrate configuration, with less than 1 hour of adaptation variance between firms. Then: fold M1R into M5 and invest in M3 depth.
- M1R shows near-zero intervention, but M3-lite on tenants 2 and 3 shows that workflow authoring dominates engineering minutes. Then: treat M5 as the platform verdict, and market M1R only as "collection path reproduced".
- The team cannot support 3 concurrent builds. Then: cap at 2.

### Sources

PL-063 (spec §26 L404) against the spec §26 table (L406-414); spec §26 (L418, 90-day hypothesis); spec §14 (L232); spec Appendix A.7 (L586); [accounting plan fixture](../fixtures/plans/accounting_evidence_preparation.json) (`activate-shadow-processing` max_elapsed_seconds 1,209,600; `canary-consolidated-reminders` 1,814,400; plan total 5,184,000); [laundry plan fixture](../fixtures/plans/laundry_route_preparation.json) (ends at `release.activate_shadow`); PA-012 (requires real_adapter, grants and model, not training); PA-013 (laundry; canary on at most 2 of 9 vehicles for 3 days), PA-025, PA-029, PA-030; PA-027 (first-month measurement). Research notes: acceptance-and-index (tension 1, replication at M5; tension 2, M4 in laundry; calendar floors), implementation-reality (laundry plan stops at shadow).

---

## D6 Approval granularity, interruption budget and effort rubric

### Decision

**Default:** policy-level approval, with case-level approval only when a materiality rule fires, plus accountant sign-off on every review package. The UI names which spec §17 decision is being asked and who owns it.

**The three decisions.** The package's approval contract already defines these three decision kinds.

| Decision kind | When it is asked | Notes |
|---|---|---|
| DATA_USE | Once per source and purpose at onboarding: INSPECT, COLLECT, TRANSFORM, EVALUATE | TRAIN is separate, opt-in and off by default. SERVE is explicit (PL-053) |
| IMPLEMENT_OPERATE | Once per intervention version, through the implementation card | Asked again only when a change crosses an envelope boundary: processor, region, permissions, spend cap, or irreversible-action policy. Missing authorizations are batched with `group_missing_authorizations` (PL-041) |
| CASE_LEVEL_BUSINESS | Review-package sign-off, plus any request that trips a materiality rule | Logged as NORMAL_BUSINESS_REVIEW |

**Reminder policy.** It is approved once and rebound on each policy-version bump.

- It covers: the template class; at most one consolidated request per client-period-obligation epoch; a follow-up cap; quiet hours; and recipient = contact of record.
- A standing supersession policy covers wording-only edits within a template class (PL-037).
- A template-class change bumps the policy version. That needs one policy re-approval, not per-case approvals (PL-040).

**Materiality triggers that force per-case approval:**

- Any listed item with Presence UNKNOWN, or with fact status STALE, DISPUTED, or INFERRED below the auto-accept threshold (the PA-003 and PA-004 patterns).
- A new or off-record recipient.
- Content outside the template class, or a payload containing amounts or tax identifiers.
- The first-ever request to a client.
- A third or later request in the same obligation epoch.
- Any request after a client complaint.
- A client the firm has flagged as sensitive.
- A request that would exceed the cadence cap.
- A source change after preparation that adds items. Changes that only remove items recompute automatically.

A stale source blocks the send instead of asking (PA-011).

**Calibration ladder: the Draft tier is the materiality instrument.**

- Every draft is reviewed and sent by staff.
- A client and obligation type graduates to policy-level Send only after at least 2 closes and at least 20 drafts of that type, with approve-without-edit of at least 95% and material edits below 2%. Material edits are changes to the recipient, item list, client or period. These numbers are hypotheses.
- The gateway still enforces approvals bound to digest and policy version. PA-006 and PA-010 must pass, and a policy-level PA-010 variant is proposed to the catalog.

**Interruption budget.** All values are hypotheses. Overruns are logged and triaged as product defects.

| Stage | Budget |
|---|---|
| Onboarding | At most 2 hours of CUSTOMER_AUTHORIZATION; at most 5 DOMAIN_CLARIFICATION questions per workflow; at most 4 owner-hours in the first 30 days |
| Steady state | At most 1 batched owner request per tenant-week; at most 30 minutes a week of owner decision time; at most 2 new domain questions per close after close 1; reviewer approvals batched into at most one session a day; repeat-ask rate 0 |
| After calibration | At most 10% of requests need per-case approval |
| Review cost | Accountant review minutes per package stay below baseline assembly-plus-review minutes |

**Effort rubric (frozen in week 1).** These are the five spec categories (PL-003), with the assignments Appendix B leaves open.

| Category | Includes |
|---|---|
| CUSTOMER_AUTHORIZATION | Grants and envelope decisions |
| DOMAIN_CLARIFICATION | Owner answers on conventions; label or attribution sample audits; participation in the baseline time study |
| NORMAL_BUSINESS_REVIEW | Per-case approvals, draft review and package sign-off |
| ENGINEERING_INTERVENTION | Any Plumb staff wiring, mapping, plan or workflow authoring or editing, and manual deployment |
| OPERATIONAL_REPAIR | Plumb staff fixing a running collector or workflow |

### Rationale

**The spec supports a standing policy.** Spec §17 (L272) lets an owner approve a recurring reminder policy once, and Appendix B sends consolidated reminders under an approved policy (L598, L634).

**Per-case approval on everything breaks the promise.** It brings back the interruption PL-041 forbids, and it adds review minutes that count against value (PL-059).

**Firms still want gates.** 62% of surveyed firms require approval before anything is sent (Uku 2026, directional [M4]). The Draft tier satisfies that literally while producing the evidence needed to relax it.

**The rubric fills a gap.** Appendix B never assigns categories to label audits or per-case approvals.

**Part of the plumbing exists in the package.** `approval_checker.py` defines the three decision kinds and `group_missing_authorizations`. Nothing wires them to a product surface yet.

**How the design was assembled.** The judges split three ways on this decision. The design keeps platform-proof's structure, budget and rubric, learning-velocity's triggers, and customer-value's Draft edit-rate graduation.

### Alternatives considered

- Per-case approval on every request (PA-006 and PA-010 as written). Safest, but high interruption and review cost.
- Platform-proof: the first 20 canary reminders approved per case, then policy-level approval once agreement reaches 95%.
- Customer-value: graduation when the Draft edit rate stays below 2% over a full close.
- Learning-velocity: policy-level approval offered after 2 cycles at 95% or more approve-without-edit.

### Revisit trigger

Any of the following keeps per-case Draft as the default tier, with review minutes priced as a cost line and Send offered only for types under a 2% edit rate:

- Accountant agreement with Plumb-prepared requests stays below 95% in shadow.
- At least 2 of 3 partners refuse policy-level approval after seeing shadow results.
- Staff edit more than 10% of drafts.
- Fewer than 2 of 5 partners opt into policy-level approval by close 3.

### Sources

PL-003, PL-037, PL-040, PL-041, PL-053, PL-059; PA-003, PA-004, PA-006, PA-010, PA-011; spec §17 (L268-276; three decisions at L272; no vague "Allow AI" button at L274); spec Appendix B (L598, L634); [approval_checker.py](../plumb/checker/approval_checker.py) and `plumb/contracts/approval.py` (DATA_USE, IMPLEMENT_OPERATE, CASE_LEVEL_BUSINESS; `group_missing_authorizations`); `plumb/contracts/common.py` (`Presence`, `FactStatus`). Research notes: appendices (approval granularity; effort-rubric gap), spec-17-29 (missing interruption metrics; materiality rules). Market: [M4], [M19].

---

## D7 Pricing, unit of value and pilot terms

### Decision

**Unit of value: the active client-month.** An active client-month is a recurring in-scope client-period for which Plumb delivered a verifier-attested ready-for-review package.

**List hypothesis** (all prices are hypotheses):

| Tier | What it includes | Price |
|---|---|---|
| Prepare | Readiness ledger, review package, later drafts | $15 per active client-month |
| Prepare + Chase | Adds policy-approved consolidated sending with cross-staff dedupe, once Send ships | $25 per active client-month |

- Annual contract, a firm minimum of $500/month, and no per-seat price.
- No implementation fee for supported environments. Plumb absorbs its own engineering interventions and never bills by the hour (ADR-010).

**Billing rules (PL-001):**

- Bill only client-months with an attested package.
- Credit any package the accountant rejects as materially wrong.
- Credit client-months in which a Plumb-caused DEGRADED collector covered more than 20% of the period.
- Customer-side dependencies are not billed while open, though the firm minimum still applies. A client blocked for 2 cycles drops off the billable roster until resolved.
- Plumb-side blocks, vendor outages and terminal failures are never billed. The results view shows each one, with what was attempted and why it stopped.
- Native-setting outcomes (PL-013) bill at the same rate, so Plumb is never paid more for building more.
- No price discount in exchange for training rights.

**Price guardrail.** Price at no more than one-third of measured value per client-month, taken from the results view. If measured value does not support $15, lower the price or exit the segment.

**Pilot terms:**

- A paid design-partner pilot of $1,500-$3,000, by firm size, invoiced at signature, so willingness to pay is tested from day one.
- Credited to year one. Refundable only if Plumb misses the M0-agreed gate for Plumb-side reasons.
- The 90-day pilot clock starts at the first attested collection path, because packages cannot exist before then.
- Partners convert to annual at $15 Prepare with a 24-month price lock, once the workflow has been ACTIVE through one full close at or above the correct-package threshold.
- Exit is pre-agreed whether or not the gate is met.

**Price test.** Three list points ($15, $25, $35) and a per-accepted-package alternative unit, run with tenants 4-5 and new prospects.

### Rationale

**Benchmarks** (from the market notes; flags in [market sources](#market-sources)):

- Double: $10/$25/$50 per client-month. These tier prices come from secondary listings. Double's own page confirms only the per-connected-client model and a $200/month annual-commitment tier [M9].
- Xenett: about $7.5-$15 per client-month [M10]. Financial Cents month-end close add-on: $5 per client-month [M11].
- Practice-management seats: $19-$99 per user-month [M11], [M12], [M13]. Intuit Accountant Suite: no charge during its introductory period [M14].
- Average firm tech spend is about $21k a year, and 80% of firms outsource at least one service (Intuit 2026 survey, vendor-run [M5]).
- SMB agency AI builds cost about $4.5k-$25k (a vendor-written guide, low reliability [M32]).

**Why per-client, outcome-based pricing.**

- Per-client pricing mirrors how firms package their own services. Double reports 150% NDR on that model (vendor-reported [M9]).
- Outcome billing puts PL-001 into practice and rewards PL-013 behavior.
- Gartner (Apr 2026) expects buyers to move toward paying for workflow results (secondary coverage [M16]).
- Cost is the least-cited adoption barrier, at 6% [M6].

**What this fixes.**

- Platform-proof's design took no revenue until the first attested path, leaving willingness to pay untested.
- The record avoids unsourced ROI arithmetic, because the market notes found no reputable source for hours per client-month.

### Alternatives considered

- Platform-proof: no fee, then a $500/month platform fee after the first attested path; $20-$35 list price; $750 minimum.
- Learning-velocity: a $750/month flat pilot for up to 60 clients; a $15-$35 band.
- Per-seat pricing. It fights a roughly $21k tech budget and positions Plumb as one more app.
- Free pilots. Faster recruiting, but no willingness-to-pay signal.
- Hourly implementation. It rewards hidden labor.

### Revisit trigger

- Fewer than 2 of the first 4 partners convert to annual at $15 or more. Then: re-examine the ICP (capacity-constrained firms, roll-ups) before cutting price.
- Pilot time studies show measured value under about $45 per client-month. Then: cap Chase at $15 or fold it into Prepare.
- Fully loaded cost per active client-month at tenant 4 exceeds 2x price with no downward trend. Then: re-price (per package, or firm tiers) or move to the roll-up/MSP channel.
- Firms strongly prefer flat fees. Then: move to per-client tiers with outcome credits.
- Fewer than 2 paid pilot LOIs after about 30 qualified conversations. Then: offer a free pilot with a pre-committed conversion price and a measurable gate, rather than lowering qualification.

### Sources

PL-001, PL-003, PL-013, PL-059, PL-062; ADR-010. Research notes: market-accounting (Double secondary pricing and 150% NDR; Xenett; Financial Cents add-on; Karbon; Content Snare; Intuit Accountant Suite; $21k tech spend; 80% outsource; caveat: no reputable hours-per-client-month source), market-implementation (Gartner Apr 2026; Financial Cents Aug 2026 cost barrier of 6%; agency builds $4.5k-$25k, low reliability), spec-1-7 (pricing should reward outcomes, not build count). Market: [M5], [M6], [M9]-[M14], [M16], [M32].

---

## D8 Positioning, category and never-claim guardrails

### Decision

**Category:** "verified implementation" for accounting firms, glossed as "implementation you can audit".

- Avoid "agentic implementation platform" (superglue uses it [M26]), "AI employee" and "fully autonomous".

**Headline:** "Plumb connects the tools your firm already uses and builds your month-end evidence workflow for you, then proves it works on your own data: every document traced to its source, a review package ready for your accountant, and a receipt for every hour a human spent."

- Add "one owner and one request per missing item" only once the Send canary has evidence.

**Short form:** "Close-ready, with receipts."

**Proof points:**

- Accountant minutes measured against the firm's own baseline.
- Correct-package rate, with denominators that include failures.
- The per-deployment labor ledger across the five effort categories.
- Engineering hours per verified deployment, including failed attempts.
- Verification receipts.
- Duplicate and stale requests per client-period, once requests ship.

**Never-claim checklist.** This is a formal gate for sales, marketing and investor materials. The founder owns it.

| # | Never claim | Basis |
|---|---|---|
| 1 | That local tests validate models, business outcomes, tenant security, cloud isolation or third-party integrations. Quote the current [VALIDATION_REPORT.md](../VALIDATION_REPORT.md) count (819 today) only as local test results, and never quote Appendix C's stale 56 | spec §28 L450; Appendix C |
| 2 | Cross-industry autonomy from the three synthetic scenarios. They show representational reuse | spec §25 L398 |
| 3 | 90 days as anything but a planning hypothesis | spec §26 L418 |
| 4 | Product-video results as evidence | spec §29 L492 |
| 5 | An "autonomous close", or any posting. A package is "ready for review" until sign-off | spec §15 L248; Appendix B L652 |
| 6 | "Fully autonomous", "zero human", "no humans needed" or "AI employee". No autonomy claim if any hidden human implementation occurred. Deployments are labeled "supervised", with labor shown, until that path has PA-027-level evidence | PL-003; PA-027 |
| 7 | "Automatically constructed" before M1R. Until then: "agent-configured certified connectors and agent-built collection" | PL-063; D4 |
| 8 | Logo walls. Integration coverage is stated per operation at its maturity level, never taken from the synthetic registry, whose PRODUCTION_VERIFIED entries are synthetic | PL-007, PL-008 |
| 9 | Any hours-saved or ROI figure without a baseline and a denominator, or any causal claim from historical replay | spec §7 L136 |
| 10 | Exact unlearning | spec §20 L318 |
| 11 | That a message was not sent after the provider accepted it | PA-014 |
| 12 | Anything beyond the released tier. No "fewer duplicate requests" outcome before Send-canary evidence | D4 release tiers |

**Competitive framing:**

| Competitor class | Examples | Framing |
|---|---|---|
| Practice-management suites | Karbon, Financial Cents, TaxDome | "Keep your PM tool; Plumb makes your whole stack work together and proves it." Integrate through the Karbon and Uku MCP servers [M12], [M13], and configure native reminders when they are enough |
| Ledger-native agents | Xero JAX/XeroForce, Intuit Accountant Suite, Double | "Excellent inside one ledger; Plumb is for firms whose evidence spans ledgers, inboxes and drives." A Xero-only firm should use Xero |
| DIY builders | Zapier, n8n, Make, Copilot Studio, XeroForce's builder | "They make you the systems integrator; we implement and keep it running." OpenAI's Agent Builder shutdown on Nov 30, 2026 is the churn example [M22] |
| FDEs and agencies | Forward-deployed engineering teams, boutique agencies | "Customer-owned specs, tests and adapters, an itemized labor ledger, and an exit path." Gartner predicts 70% of enterprises will abandon agentic AI built through vendor FDE by 2028 (secondary coverage [M17]) |

### Rationale

**"Autonomous" is now a liability.**

- Trust in fully autonomous agents fell from 43% to 27% in one year (Capgemini [M19]).
- Gartner warns of "agent washing" (search summary [M18]).
- Builder.ai collapsed after reports that its "AI" relied on human engineers (press reports [M20]).
- The FTC's Operation AI Comply continues to pursue deceptive AI claims (law-firm analysis [M21]).

**Agent-built integrations are becoming table stakes.** Nango's Management MCP, Membrane and Make's Maia all claim a version of it (vendor claims [M27], [M28], [M29]).

**The two claims no competitor makes.** Neither market scan found a competitor offering the labor ledger or independent verification. That is absence of evidence from a US-only web search, not proof. The two claims answer stated objections: trust and accuracy (21% [M6]) and fear of errors (35%, vendor survey of 128 [M23]).

**Chasing is a commodity.** Leading with chasing would put Plumb in a $5-$99 category.

**Correction to customer-value's headline.** Rule 12 fixes it. That headline promised "one request per missing item", but requests ship after day 180.

### Alternatives considered

- An outcome-led headline ("never chase a client twice"; "stop chasing, close faster").
- "Autonomous" framing, as used by Pilot ("zero human intervention", vendor claim [M30]) and Basis. Rejected.
- Platform-proof's headline, which leads with the same category.

### Revisit trigger

- Message-test on landing pages and first calls across at least 200 ICP firm contacts.
- If outcome-led framing gets more than 2x the qualified-meeting rate of verification-led framing among mixed-stack firms: lead with the outcome, and keep verification and the ledger as proof points.
- The never-claim checklist is not relaxed under any result.

### Sources

PL-003, PL-007, PL-008, PL-062, PL-063; PA-014, PA-027; spec §7 (L136), §15 (L248), §20 (L318), §25 (L398), §26 (L418), §28 (L450), §29 (L492); spec Appendix A.6 (L580, avoid statuses that obscure manual engineering); Appendix B (L652); [capability_registry.json](../plumb/registry/capability_registry.json) (description: synthetic). Research notes: market-implementation (Capgemini; Gartner agent washing and the Sep 2026 FDE prediction; Builder.ai; FTC; superglue naming; OpenAI Agent Builder; Accounting Seed; Financial Cents), market-accounting (Karbon Kai/MCP, Uku MCP, Xero JAX/XeroForce, Intuit Accountant Suite, Double), appendices (Appendix C figures stale). Market: [M6], [M12], [M13], [M17]-[M23], [M26]-[M30].

---

## D9 Design-partner program and contract essentials

### Decision

**Size and roles.** Sign 5 accounting firms, with LOIs in hand before M1 completes, so replication never waits on sales.

| Slot | Evidentiary role |
|---|---|
| Tenant 1 | M0 and M1 |
| Tenants 2 and 3 | M1R, with the controlled stack variation from D1 |
| Tenant 4 | Completes the "next three customers" for M5 |
| Tenant 5 | Reserve, and the second-tenant peer for PA-017 |
| Optional roll-up slot | Channel probe, off the critical path |

At most 3 active builds until M1R passes.

**Funnel hypothesis:**

- At least 25 qualified conversations by week 8.
- Tenant 1 signed by about week 4.
- LOIs from tenants 2-4 by week 8.

**Selection:**

- The D1 ICP.
- A named domain owner with about 2 hours a week and the authority to grant OAuth.
- A named reviewing accountant.
- At least 50 recurring clients with 12-24 months of history.
- Providers that meet the catalog assumptions: a document store with webhooks plus overlap polling, mail with request-id lookup, and provider sandboxes.
- Exact operations that can be probed in M0.
- A slot in the stack-variation matrix.
- Agreement to a 2-week baseline time study.
- Payment of the pilot fee.
- Acceptance of dependency and failure outcomes as normal.
- Consent to publish anonymized labor-ledger metrics, failures included.
- A 100-pair attribution or label review.
- Willingness to be a reference.

**Partners give:** grants and access; domain-owner time within the interruption budget; the baseline; feedback; a 20-minute weekly check-in; case-study rights.

**Partners get:** implementation with no fee; the 24-month price lock; the readiness ledger and shadow reports; founder access; roadmap influence; Plumb absorbing all adaptation engineering; ownership and export of every artifact and test.

**Contract essentials.** Get a counsel opinion before the first signature.

1. **DPA with purpose-bound grants per source** (INSPECT, COLLECT, TRANSFORM, EVALUATE).
   - TRAIN off by default, opt-in per source, tenant-only.
   - SERVE granted explicitly before the first shadow. This settles the open SERVE question (PL-053). The package defines a SERVE purpose, but no checker enforces it, and no fixture envelope grants it.
2. **Cross-tenant use.** No cross-tenant use of the partner's examples, labels or weights. Plumb may reuse derived engineering artifacts stripped of customer data: mapping patterns with applicability constraints, adapter tests, failure fixtures. Replication depends on this (spec Appendix A.5 L570).
3. **IRC 7216.**
   - Tax-return information is excluded from source grants, enforced by folder and label exclusions and PL-053 purpose checks.
   - The firm warrants it will not route such data.
   - Including it later needs taxpayer consent obtained by the firm and reviewed by counsel.
4. **Region and retention.**
   - US region pinning.
   - Retention and deletion terms, with a deletion certificate.
   - Derived data is quarantined or retired. No exact-unlearning promise.
5. **Revocation semantics.**
   - Cached grants and queued dispatches are invalidated within one minute, as in PA-008.
   - The terms cover the race where a provider accepts an action before revocation lands (PA-014).
6. **Labor-ledger disclosure.** Plumb records and may publish anonymized effort data. The partner may audit its own ledger.
7. **Business boundaries.** Accountant sign-off is mandatory, and there is no posting.
8. **Security scope.** Security commitments cover only the gates actually passed.
9. **Subprocessors.**
   - A list of model providers, each under no-training terms.
   - Service-provider safeguards terms (for example the FTC Safeguards Rule) only as counsel confirms. The research notes do not source them.
10. **Exit.**
    - 30-day termination at a close boundary, with credential revocation.
    - Export in open formats of IntegrationSpec, CollectionSpec, WorkflowSpec, tests, evidence, packages and the labor ledger.
    - A vendor-continuity clause (the Bench lesson [M24]).
    - Exit pre-agreed whether or not the gate is met.

**Program rules:**

- A partner graduates to paid annual once the workflow has been ACTIVE through one full close at or above the correct-package threshold.
- A partner is offboarded if its dependencies stay unresolved for more than 30 days or its stack drifts outside the certified operations. Those builds are recorded as blocked attempts in the denominator.

The full program, including the selection scorecard, is in the [design-partner program](09-design-partner-program.md).

### Rationale

**Access is the critical path.** 19 of the 30 catalog scenarios need real grants from authenticated humans, and 24 need real adapters (verified from the catalog's `requires` tags).

**Each tenant has an evidentiary role.**

- PA-027 needs a verified first customer plus a fresh one.
- Appendix B asks for replication on the next three customers (L654).
- PA-017 needs a second tenant.

**Data-rights terms decide whether replication is legal** (spec Appendix A.5 L570).

- TRAIN off by default matches the 53% of surveyed firms who refuse training [M4].
- The tax exclusion matches the IRC 7216 signal (secondary commentary; verify with counsel [M25]).
- 60% of clients ask their accountants for proof of AI data protection [M5].

**Continuity and serving.**

- Bench's abrupt shutdown affected about 35,000 US customers [M24].
- Gartner advises defining an exit strategy from day one (secondary coverage [M17]).
- The package never enforces SERVE today, so the contract has to settle it.

### Alternatives considered

- Customer-value: 5 partners in staggered waves on paid pilots, with a roll-up as firm E.
- Learning-velocity: 5 firms plus an optional 6th from 12-15 conversations (judged optimistic), run in Disclosed-Labor Mode (rejected).
- Perfect tenant 1 before recruiting. Delays replication.
- 10 or more firms for statistical power. Would swamp a 5-7 person team.

### Revisit trigger

- Tenant 2's onboarding takes more than 50% of engineering capacity for more than 3 weeks. Then: pause tenant 3, find the root cause by failure class, and hold tenants 4-5 until engineering minutes per verified path fall.
- Fewer than 2 paid pilot LOIs after about 30 qualified conversations. Then: offer a free pilot with a pre-committed conversion price.
- Counsel confirms monthly-close bookkeeping sources are outside 7216. Then: relax the exclusion for those sources.
- Recruiting is easy and labor per firm falls fast. Then: open a second cohort of 5 in Q2 2027.

### Sources

PL-052, PL-053; PA-008 (one-minute invalidation), PA-014, PA-017, PA-027; spec Appendix A.5 (L570); spec Appendix B (L654); spec §20 (L318); [accounting envelope fixture](../fixtures/envelopes/accounting_evidence_preparation.json) (grants include no SERVE); `plumb/contracts/common.py` (`DataPurpose.SERVE`, defined but not checked by `plan_checker.py`). Research notes: acceptance-and-index (real_adapter 24 and grants 19 of 30; provider assumptions; design-partner tenants needed), implementation-reality (SERVE never enforced; SourceGrant lacks `revoked_at`), market-accounting (IRC 7216, secondary; Uku 53%; 60% data-protection asks; Bench), market-implementation (Gartner FDE exit advice; Current/Crete). Market: [M4], [M5], [M17], [M24], [M25].

---

## D10 North star and supporting metrics

### Decision

**North star: engineering-intervention hours per verified deployment (EIH/VD)**, reported per new tenant in onboarding order.

- Numerator: all ENGINEERING_INTERVENTION and OPERATIONAL_REPAIR minutes logged against a tenant's eligible build attempts. That includes failed, abandoned and blocked attempts, and any time spent hand-authoring or editing that tenant's plan or mapping.
- Denominator: verifier-attested deployments for that tenant, collection paths first and then workflows.
- Platform-investment hours triggered by each tenant are reported beside it and never netted.
- Trajectory hypothesis: falls with every tenant; tenant 3 at or below 50% of tenant 1; trending toward zero by tenants 4-5.

**Customer co-headline, from M3-lite onward: accepted review packages per month.**

- A package counts when it reached ready-for-review before the firm's close deadline, the accountant explicitly accepted it without material correction, and attribution to the wrong client was zero. Absence of edits does not count as acceptance.
- It is always shown with its rate over all eligible in-scope client-periods, including blocked and terminally failed ones, and with Plumb human minutes per accepted package.

**Supporting metrics.** Targets are hypotheses, ratified in threshold sheet v1. Full definitions are in [metrics](06-metrics.md).

| Metric | Definition (short) | Denominator | Target or trigger |
|---|---|---|---|
| Hands-off build rate | Eligible build attempts reaching VERIFIED with zero ENGINEERING_INTERVENTION and zero OPERATIONAL_REPAIR | All eligible attempts started, including failed, blocked and abandoned ones | Below 50% on tenants 2-3 triggers the R1 review |
| Artifact reuse rate and fork count | Mappings, collection templates and workflow components reused unmodified, matched by digest | All artifacts in the new tenant's deployment | 60% or more by tenant 3; fork count 0 |
| Outcome mix per authorized goal | Verified interventions, actionable dependencies and terminal failures (PL-001), plus median days in dependency by resolver (customer, vendor, Plumb) | Authorized goals | Reported |
| Time to first verified event | Calendar days from envelope signature to an attested PA-001-style event, split into Plumb-controlled and dependency time; also days to the first accepted package | Per tenant | Reported |
| Collection integrity | Source changes (injected or natural) appearing exactly once, correctly attributed, within the 5-minute health deadline; reconciliation gaps and duplicates; staleness visible within 5 minutes | All sampled source changes | Gaps and duplicates 0 (PL-024) |
| Missing-item quality | False-chase rate; recall; attribution correctness at the auto-accept threshold, with coverage | Items flagged missing; true missing items; audited samples | False-chase 2% or less; recall 90% or more; attribution 95% or more. Not the experiment-2 read-out |
| Correct review-package rate and accountant minutes | Packages judged complete and correctly attributed, next to assembly-plus-review minutes against the month-0 study | Eligible client-periods in shadow or active, exclusions kept | Threshold set by the domain expert at M3-lite |
| Interruption load | Owner and reviewer decision minutes per tenant-week by decision kind; DOMAIN_CLARIFICATION per workflow; decay of close n against close 1; repeat-ask rate; share needing per-case approval | Per tenant-week and per workflow | D6 budget; repeat asks 0 |
| Client-request integrity (once Draft or Send ships) | Duplicate requests per client-period-obligation against the 24-month baseline; stale or incorrect requests | Per client-period-obligation and per 100 requests | Duplicates 0 |
| Fully loaded cost per verified deployment, and gross margin per active client-month | Inference, infrastructure and all Plumb labor, including failed attempts and supervised delivery | Verified deployments; active client-months | Pivot if above 2x price at tenant 4 with no downward trend |
| Commercial conversion | Pilot-to-paid conversion at list price; realized price per active client-month; logo retention | Pilots completed; active partners | Pivot if fewer than 2 of the first 4 convert at $15 or more |

The effort-category rubric is frozen in week 1 (D6). Effort is captured automatically and audited at M1, M1R and M5, and monthly.

### Rationale

**EIH/VD encodes the spec's central claim.** PL-062 requires counting manual engineering and failed builds. PA-027's pass test is lower engineering intervention than the first customer. EIH/VD encodes both.

**It can be measured early.** EIH/VD works from the first M1 build, unlike north stars built on accepted packages.

**It is hard to game.** Failed attempts add minutes without adding deployments, so they push the number up. The separate platform-investment ledger stops hours migrating out of the tenant ledger.

**Guardrails on quality, interruption and reuse.**

- Quality metrics stop labor reductions from being bought with worse outcomes.
- Interruption metrics cover the spec §17 promise, for which the spec defines no metric.
- The reuse rate reads out experiment 6.
- The spec rejects a universal 99% bar (spec §24 L382), so every threshold is a task-specific hypothesis.

**What exists today.** The package has no effort-capture API. Its OutcomeObservation carries a single nullable effort category (research notes: implementation-reality). Every metric above is proposed, and none has been measured.

### Alternatives considered

- Customer-value: accepted review packages per month as the north star. Customer-felt, but monthly, lagging, and unmeasurable before M3.
- Learning-velocity: accepted client-periods per week paired with human minutes. Can be bought with disclosed labor.
- Runtime-autonomy metrics. Insufficient under PL-062 and ADR-010.

### Revisit trigger

- EIH/VD improves while customer-facing outcomes (collection integrity, correct-package rate, review minutes) stall, or partners churn. Then: promote accepted review packages per month to north star, and keep EIH/VD as a platform-health gate.
- A ledger audit finds miscategorization. Then: count only automatically captured effort.
- Sign-off lag exceeds 2 weeks, or reviewers disagree on "material" more than 20% of the time in a double-coded sample. Then: use attested ready-for-review packages with the correction rate as a guardrail, plus a material-correction rubric.
- Accepted-package metrics look healthy but partners do not renew. Then: switch the customer headline to retained paid client-months.

### Sources

PL-001, PL-003, PL-010, PL-024, PL-041, PL-059, PL-062; ADR-010; PA-001, PA-003, PA-005, PA-027 (comparison against the first customer; the denominator includes failed and blocked builds); spec Appendix B (L650-652, success and its denominator); spec §24 (L380, five-minute staleness visibility; L382, task-specific targets). Research notes: spec-17-29 (interruption metrics missing; no numeric autonomy target), implementation-reality (no effort-capture API).

---

## D11 Top risks and kill/pivot criteria

### Decision

There are five primary risks and two operational ones. Each is tied to a spec §27 experiment or a commercial unknown, and measured with the D10 metrics.

**Reading rules:**

- Thresholds are pre-registered at M0.
- Each threshold is read together with its root cause, against the stack-variation matrix.
- A failure traced to a primitive that is now in the registry, and that later tenants do not need, counts as a pass in progress.
- A decline produced by cherry-picking easy tenants counts as a fail.
- Windows are not extended when two triggers fire at once.

**The risks.** Likelihood and impact are the panel's judgment; every threshold is a hypothesis. Detail and owners are in [risks and assumptions](07-risks-and-assumptions.md).

| Risk | Likelihood | Impact | Mitigation | Kill or pivot criterion |
|---|---|---|---|---|
| R1: Replication does not get cheaper, so Plumb is a services business (experiments 3 and 6) | Medium-High. Adapter-adaptation cost and cross-customer reuse are unresolved, and tenant variance is real | Existential. Without falling EIH/VD there is no platform claim (PL-062, ADR-010) | Controlled stack-variation matrix; agent-generated tenant semantics on certified transport; verified builds feed reusable primitives into the registry; separate platform-investment ledger; root-cause analysis by failure class at each checkpoint | At the M1R checkpoint, any of: tenant 3's EIH/VD at or above 75% of tenant 1's; hands-off build rate on tenants 2 and 3 below 50%; artifact reuse below 60%; any code fork. Response: freeze new milestone work for 4 weeks and find the root cause. If tenant 4 still shows no decline, pivot: sell the factory as tooling for human implementers (MSPs, VARs, roll-ups) and drop the autonomous-implementation claim, or become an honestly priced verified-implementation service |
| R2: Hidden human labor presented as autonomy (PL-003; the Builder.ai pattern) | Medium. Commercial pressure during the supervised first delivery (spec §1 L51) | Existential to credibility. It invalidates every PL-062 claim and invites AI-washing enforcement | Automatic capture of human-principal actions; customer-visible ledger; separate platform-investment ledger; an auditor outside the delivery team at M1, M1R and M5, plus a monthly audit of the delivery team's account using PA-027's method; no per-customer delivery engineers; the never-claim checklist | Any unrecorded engineering found in an audit invalidates the milestone and forces a re-run. A second occurrence triggers an external audit before any external claim |
| R3: Interruption load turns the customer into the systems integrator (experiment 4) | Medium. Engagement checklists may not be inferable, and conventions vary by firm | High. Breaks "without constant interruption" and erodes the value case | Engagement-checklist templates; focused-question queue with a budget; answers become versioned conventions (PA-004); `group_missing_authorizations` batching; the D6 budget, with overruns triaged as defects | On tenant 3, any of: median DOMAIN_CLARIFICATION per workflow above 10 questions or 3 hours; steady-state owner decision time above 60 minutes a week; owner clarification plus authorization above 3x the budget at two partners. Response: pivot to a fixed vertical template with firm-level defaults, narrow the ICP to firms with documented engagement checklists, and stop claiming self-discovery in this vertical. If owner minutes exceed measured accountant savings, kill the wedge |
| R4: Generated failure handling is unreliable and causes an effect-safety incident (experiment 5) | Medium. The package's effect ledger is a SQLite simulation, and a canary cannot be paused today | High. One duplicate, stale or wrong-client email can cost a partner its client, and cost Plumb the partner | Preparation-only first, Draft before Send; production gateway with outbox, leases and dispatch-time authority, revocation and pause checks; pause and kill from CANARY; the protected verifier against the Appendix B failure set; any HIGH-severity failure blocks activation (PL-061) | After bounded repair, generated workflows fail more than 10% of the protected Appendix B failure cases (PA-003, PA-004, PA-005, PA-006, PA-007, PA-008, PA-009, PA-010, PA-011) across two tenants: stop generating workflow logic, use only certified template workflows, and never claim "generated workflows". One real-client duplicate, stale or wrong-client request in canary: halt sends, revert to Draft, run root-cause analysis. Two such incidents within 90 days: Send leaves the product for two quarters, and preparation-only becomes the product |
| R5: Market squeeze and low willingness to pay (Intuit's free suite, Xero Document Requests, Double's 4,000+ firms, Basis and Digits moving down-market, commoditized agent-built connectors) | Medium-High | High. A proven platform that cannot be sold | Qualify out single-ecosystem firms; run a PL-013 native-feature baseline and configure native tools when they are enough; lead with verified packages, not chasing; per-client outcome pricing; paid pilots from day one; a roll-up channel probe | Any of: at least 3 of 5 qualified prospects choose native tools after a PL-013 comparison; 50% or more of qualified mixed-stack prospects pick an incumbent head-to-head; fewer than 2 of the first 4 partners convert to annual at $15 or more per active client-month; fully loaded cost per active client-month at tenant 4 above 2x price with no downward trend. Response: pivot to the roll-up/MSP channel or per-package pricing, and re-examine the ICP before cutting price |
| R6: Build time versus runway. The value loop is not built, and the verifier, fault-injection harness and gateway are unlisted products | High | High. Evidence arrives after the money runs out | Wrap the existing policy kernel rather than rewriting; follow the vertical-proof order (Appendix A.7); keep certified operations narrow; make the security and verification hires early; cap concurrency at 3 builds; windows start on gate exit | PA-001 has not passed on tenant 1 by week 14: cut scope to one ledger and one document store instead of adding platform. M1R has not passed by week 24: the day-180 memo must choose between a reduced-scope extension and the R1 pivot |
| R7: Data rights and access block the evidence (refused mailbox scopes, vendor app-review delays, IRC 7216, 53% of firms refusing training) | Medium | Medium-High. Delays M3-lite and the duplicate-chase baseline, and blocks M2 | Start vendor app reviews in week 0; TRAIN off by default; exclude tax-return information; counsel opinion before first signature; keep a forwarding-address intake as a fallback | At least 2 of 5 partners refuse mailbox scopes, or vendor approval for mail scopes is not granted by M3-lite: run on document store plus ledger, with a forwarding-address intake for mail. Fewer than 2 tenants grant TRAIN: M2 stays deferred, which is not a company kill. Counsel finds IRC 7216 blocks monthly-close sources at most ICP firms: re-scope sources or the ICP |

**Experiment 1 (richer observation)** gets a cheap proxy test. In 2 firms, compare discovery from APIs and history alone with the same plus a 2-hour structured shadowing session.

- If shadowing adds at least 1 deployable, feasibility-passing opportunity per firm in both firms: plan a consented, event-triggered capture pilot after M5.
- Otherwise: keep capture out.

**Experiment 2 (inferred input/target join correctness)** gates M2 only. It is measured on a PA-012-style 100-pair accountant sample, on tenants that grant TRAIN or EVALUATE. Client/period attribution accuracy is a separate quality metric, not the experiment-2 read-out.

**Watch items:**

- Vendor app-review and consent approvals for mail and document scopes cannot be bypassed (spec §5 L106; Workspace data-use restrictions, spec §21 L328). Start them in week 0.
- Tax-season availability.
- Whether ledger authorization is granted per client company.

### Rationale

**What the risks decide.**

- R1 and R2 decide whether a platform exists at all.
- R3 and R4 decide whether "without constant interruption" and safe effects survive contact with real firms.
- R5 decides whether a proven platform sells.
- R6 and R7 decide whether the evidence arrives at all.

**Why pre-registration.** Spec §27 (L442) lists six experiments that remain necessary. Pre-registering thresholds stops the pivot decision from being rationalized after the fact.

**Correction to learning-velocity.** It used a document-attribution sample as the experiment-2 read-out. Attribution is not the inferred input/target join that experiment 2 measures (PL-027).

### Alternatives considered

- No pre-registered thresholds. Risks rationalizing results after the fact.
- Statistical power through 10 or more tenants. The team cannot support it.
- Learning-velocity's triggers (reuse at least 60%; at least 3 of 5 convert). Reuse is kept; conversion is harmonized to 2 of the first 4.
- Customer-value's triggers (the week-12 PA-001 runway rule; the trust-incident rule). Both kept, the runway rule at week 14.

### Revisit trigger

- Variance between firms is high but the trend clearly improves (the 4th and 5th firms beat the 3rd by a wide margin), and only one trigger fired. Then: extend the decision window by one cohort.
- Interventions on tenant 3 come from primitives now in the registry. Then: treat it as a pass in progress.

### Sources

PL-003, PL-013, PL-027, PL-061, PL-062; PA-003, PA-004, PA-005, PA-006, PA-007, PA-008, PA-009, PA-010, PA-011, PA-012; spec §1 (L51), §5 (L106, never bypass vendor approvals, MFA or licensing), §21 (L328), §27 (L442). Research notes: market-implementation (Builder.ai; Nango and Membrane commoditization; Gartner FDE prediction), market-accounting (Basis and Digits down-market; Intuit and Xero bundling; Double), spec-8-16 (recast experiments as learning milestones with kill/pivot criteria). Market: [M4], [M8], [M9], [M14], [M15], [M20].

---

## D12 Team gaps and hiring timing

### Decision

Spec Appendix A.7 (L584) lists five roles: a technical lead (durable execution and enforcement), an integration engineer, an applied ML/evaluation engineer, a product engineer and a domain expert. It names no PM, designer, SRE, security or verification owner. Gaps and timing, all hypotheses:

| When | Role | Scope |
|---|---|---|
| Week 0 | Founder | Product lead and owner of design-partner sales, since sales is on the critical path. Owns the threshold sheet (with the domain expert), the effort rubric, the interruption budget and the never-claim checklist |
| Week 0 | Tech lead | Action gateway, scheduler and effect ledger |
| Week 0 | Integration engineer | Capability registry, certified connectors and collectors |
| Week 0 | Product engineer | A.6 surfaces, readiness ledger, review surface |
| Week 0 | Domain expert | A part-time CPA with CAS experience, at 0.5 FTE or more. Owns the domain acceptance corpus and thresholds. Not drawn from a design-partner firm |
| Weeks 0-4 | Security/platform infrastructure engineer | Sandbox, egress proxy, secrets, isolation and IAM. PA-019, PA-026 and the PA-017 surfaces are in the M1 bundle, and PA-021 and PA-026 have no local analogue |
| Weeks 0-8 | Fractional counsel | DPA, purpose grants, SERVE, IRC 7216 and labor-ledger publication |
| Weeks 0-4 | Fractional compliance lead | Vendor scope verification (Google and Microsoft app review for mail and document scopes) and partner security reviews |
| By week 6 | Verification and acceptance-harness engineer, reporting outside the build team (ADR-007, PL-042) | The verifier, the fault-injection harness (an unlisted product that most HIGH-severity scenarios need) and ledger-audit tooling |
| Weeks 4-16 | Fractional product designer | Implementation card, blocked-dependency card, readiness ledger and review surface |
| Around week 12 | Applied ML/eval hire, re-scoped to evaluation | Review-package correctness, verifier calibration, the protected corpus under PL-044; owner of the data and learning contracts. Training expertise only after an M2 go |
| Around week 12, only if needed | Design-partner success lead | Only if the founder cannot cover partner operations. Their minutes are logged, and they never wire integrations; if they do, it is ENGINEERING_INTERVENTION |
| By about week 22 | SRE/on-call coverage | Before the Draft tier or any external-effect canary |

**Gates:**

- An independent ledger auditor (the founder plus an external technical advisor) at M1, M1R and M5.
- A monthly audit of the delivery team's account against the ledger.

**Spec §26 owners** (spec §26 L416 requires named owners):

| Area | Owner |
|---|---|
| Capability registry | Integration engineer |
| Action gateway | Tech lead |
| Data and learning contracts | Eval engineer; the tech lead holds them until that hire |
| Domain acceptance corpus | Domain expert |

**Do not hire per-customer delivery engineers.** Their time is ENGINEERING_INTERVENTION by definition, and they are the services trap.

**Defer the first sales hire** until 2 paid conversions.

### Rationale

**A.7 leaves gaps that gate evidence.** It names no PM, designer, SRE, security or verification owner. Yet 5 HIGH-severity security and isolation scenarios (PA-017, PA-019, PA-021, PA-022, PA-026) sit on or near the M1 path.

**Specific roles are forced by the spec.**

- The verifier must be organizationally independent of the builder (ADR-007, PL-042).
- The fault-injection harness is effectively a separate product.
- With the learning factory deferred, ML capacity is better spent on evaluation.
- Spec §26 (L416): the hard work "is not merely prompt writing".

**Correction to customer-value.** It hired security at week 8, too late for a week-12 M1 bundle.

### Alternatives considered

- Combine roles as A.7 allows: security into the tech lead, verification into the eval engineer.
- Customer-value: defer the ML/eval hire until the M2 trigger; a success lead by week 12; security by week 8.
- Learning-velocity: a dedicated delivery engineer whose logged minutes are the experiment. Rejected as the services trap.
- Buy security from a compliance-automation vendor.

### Revisit trigger

- M0 contract tests show a managed sandbox or substrate covers egress and isolation well enough to pass PA-019 and PA-026 (for example, Nango's separation of development and runtime credentials plus a hosted sandbox). Then: delay the dedicated security hire until before the Draft tier.
- The founder cannot cover sales and product. Then: hire a design-partner lead before the verification engineer.
- Partner onboarding stays within the interruption budget without a success lead. Then: keep that function with the founder.

### Sources

PL-042, PL-044; ADR-007; PA-017, PA-019, PA-021, PA-022, PA-026; spec Appendix A.7 (L584-588); spec §26 (L416, four named owners and required skills). Research notes: acceptance-and-index (the fault-injection harness is an unlisted product; PA-021 and PA-026 have no local analogue), appendices (no PM, designer, SRE or security role listed), market-implementation (Nango Management MCP keeps development and runtime credentials separate [M27]).

---

## Founder decisions needed

Every default is the panel's recommendation and every number is a hypothesis. "Decide by" names the phase whose work depends on the decision.

| # | Decision | Options | Recommended default | Decide by |
|---|---|---|---|---|
| 1 | M1 construction bar | (a) PA-001 as written on certified transport (customer-value, learning-velocity). (b) PA-001 plus an agent-filled plan and an agent-generated client/period/obligation mapping (platform-proof; chosen by all three judges) | (b). Declarative config counts as construction evidence, and PA-026 joins at the first tenant where generated code runs. If sandbox and egress work slips more than 4 weeks, fall back automatically to (a), plus a generated-path requirement at tenant 3 | P0 |
| 2 | Replication timing | (a) M1R right after M1, reading PL-063 literally. (b) At M5, as in the spec §26 table. (c) Fold M1R into M5 if adaptation proves trivial | (a), on tenants 2 and 3. Also propose to the catalog that PA-027 become HIGH severity for any release marketed as autonomously implemented | P0 |
| 3 | Pilot commercial terms | (a) Paid pilot of $1,500-$3,000, credited to year one (customer-value). (b) No fee, then $500/month after the first attested path (platform-proof). (c) $750/month flat for up to 60 clients (learning-velocity). (d) Free pilot | (a), invoiced at signature, refundable only for Plumb-side gate misses. The 90-day clock starts at the first attested collection path. Conversion at $15 Prepare with a 24-month price lock. If fewer than 2 paid LOIs come from about 30 qualified conversations, offer a free pilot with a pre-committed conversion price rather than lowering qualification | P0, before tenant 1 signs (about week 4) |
| 4 | List price and price test | (a) Prepare $15 and Prepare + Chase $25, $500 minimum (customer-value). (b) $20-$35, $750 minimum (platform-proof). (c) $15-$35 band, $400 minimum (learning-velocity). (d) Per seat | (a): annual, no seats, no implementation fee. Test $15, $25 and $35, plus a per-accepted-package unit, with tenants 4-5 and new prospects. Price at no more than one-third of measured value | P1, before the tenant 2-4 LOIs; the test runs in P5 |
| 5 | Approval default | (a) Per-case approval on every request. (b) Policy-level approval with materiality triggers, mandatory package sign-off and the Draft calibration ladder. Graduation variants: the first 20 canary reminders per case; a Draft edit rate under 2% over a close; 2 cycles at 95% or more | (b), with the D6 triggers and the ladder: 2 closes, at least 20 drafts per type, approve-without-edit of at least 95%, material edits below 2%. Make per-case approval the default if fewer than 2 of 3 partners accept policy-level approval after seeing shadow results | P4, before production shadow; reconfirm in the P5 packet |
| 6 | Threshold sheet v1 | Ratify the defaults, or adopt proposal alternatives (for example 95% join correctness, TRAIN from at least 30% of firms, 3 of 5 conversion as a kill) | Ratified at M0 by the domain expert and an external technical advisor. Tenant 3 EIH/VD at or below 50% of tenant 1, with the pivot review at 75% or more. Hands-off build rate of at least 50%. Artifact reuse of at least 60% with zero forks. False-chase rate of 2% or less; recall of 90% or more; attribution correctness of 95% or more at the auto-accept threshold. Correct-package threshold set by the domain expert. Interruption budget as in D6; M2 gates as in D5 | Issued in P0; ratified at the P1 (M0) exit |
| 7 | SERVE purpose | (a) An explicit per-source SERVE grant, enforced by the plan checker. (b) Status quo: SERVE stays implied; the package defines it, no checker enforces it, and every fixture plan passes without it | (a): require it in the DPA and envelope before the first production shadow, and make the plan checker enforce it | P0 for the contract template; enforced before the P4 shadow |
| 8 | Release-executor bootstrap | (a) A narrow release executor on fixed approved templates (PL-045), qualified on a Plumb-owned production tenant. (b) Defer the executor and log manual releases as ENGINEERING_INTERVENTION (learning-velocity). (c) Generic infrastructure generation | (a): `release.create` and `release.activate_shadow` earn real PRODUCTION_VERIFIED receipts, with a verifier attestation, before any tenant shadow. Maturity is never set from fixtures | P2 to decide; the qualification run happens in P4 |
| 9 | IRC 7216 scope | (a) Exclude tax-return information from v1 source grants. (b) Include it, with taxpayer consent flows | (a), with a counsel opinion before the first signature. Relax only for monthly-close sources, and only if counsel confirms they are out of scope | P0 |
| 10 | Data rights and reuse | (a) TRAIN off by default, opt-in per source, tenant-only. (b) TRAIN as a pilot condition, or traded for a discount | (a). Cross-tenant reuse limited to engineering artifacts stripped of customer data. No price discount for training rights | P0 |
| 11 | Labor-ledger publication | (a) Customer-visible ledger, plus the right to publish anonymized per-tenant EIH/VD, failed attempts included. (b) Customer-visible only. (c) Internal only | (a) | P0 |
| 12 | Early hires | (a) A security/platform engineer in weeks 0-4 and an independent verification engineer by week 6. (b) Combine those roles into the tech lead and eval engineer, as A.7 allows. (c) Security around week 8 (customer-value) | (a). Delay the security hire until before the Draft tier only if a managed sandbox passes PA-019 and PA-026 in M0 contract tests | P0 |
| 13 | Early human-built value (learning-velocity's Disclosed-Labor Mode) | (a) No human-engineered deliverables on partner data before the M1 isolation subset and PA-019 pass. (b) Disclosed-Labor Mode from weeks 2-8 | (a). Customer value before M1 comes from the month-0 baseline and the read-only readiness ledger | P0 |
| 14 | Timing of external effects | (a) Draft and Send canaries after day 180, gated on the production gateway. (b) Draft and a Send canary inside 26 weeks (customer-value). (c) Draft-to-mailbox in M3, before the gateway (learning-velocity) | (a). Revisit only if 2 of 3 partners make reminders a condition of continuing, and even then never skip PA-005, PA-007, PA-009 and PA-010 | P5, in the day-180 packet |
| 15 | Region and fixtures | (a) A single US region. (b) US plus a Canada fast-follow. (c) Multi-region | (a). Re-template the EUR/eu-west-1 accounting fixtures to US/USD, and refresh or clock-pin fixture envelopes that expire 2027-03-31, which falls inside the 180-day window | P0 |
| 16 | Roll-up channel | (a) One optional roll-up slot, off the critical path. (b) A roll-up as the primary buyer. (c) None | (a), as tenant 5 or a sixth slot. Promote it to primary channel only if R5 fires | P1, at cohort signing |

## Where the panel disagreed

- **Overall ranking.** Platform-proof won every judge's total: 46, 46 and 46, for 138. Customer-value scored 45, 44 and 44 (133); learning-velocity 43, 43 and 45 (131). Judge 3 ranked learning-velocity above customer-value for its experiment discipline. The record uses platform-proof's spine for D1, D3, D4, D5, D9, D10, D11 and D12, customer-value's answers for D2, D7 and D8, and a synthesis for D6.
- **M1 construction bar.** Platform-proof requires an agent-generated semantic mapping at M1. Customer-value and learning-velocity accept PA-001 as written and push the generated path to M1R. All three judges preferred platform-proof but flagged the scope risk. The record keeps the stricter bar, with an explicit fallback if the sandbox slips more than 4 weeks.
- **D2 first deliverable.** Judges 1 and 2 preferred customer-value: verified packages on 30 or more client-periods in the first live close. Judge 3 preferred platform-proof: the M1 readiness ledger as the first deliverable, since it needs only READ and COLLECT. The record sequences both, readiness ledger first and then packages. It also corrects customer-value's "baseline within days of consent", which depended on a collector that does not exist yet.
- **D6 approvals split three ways.** Judge 1 chose platform-proof (structure, budget, rubric). Judge 2 chose customer-value (Draft tier with edit-rate graduation). Judge 3 chose learning-velocity (the most precise materiality triggers). The record merges all three. Its graduation thresholds (2 closes, 95% approve-without-edit, under 2% material edits) are a compromise to ratify, not a consensus.
- **D8 messaging.** Judge 1 preferred platform-proof's checklist. Judges 2 and 3 preferred customer-value's "Close-ready, with receipts" and its fuller never-claim list. The record adopts customer-value's framing with platform-proof's formal gate and named owner. It also restricts the headline, because "one request per missing item" cannot be claimed before the Send canary.
- **North star.** Customer-value proposed accepted review packages per month. Learning-velocity proposed accepted client-periods per week, paired with human minutes. The judges chose platform-proof's EIH/VD. Accepted packages become a customer-facing co-headline from M3-lite, because EIH/VD is invisible to customers.
- **Replication inside 180 days.** Customer-value measured only one replication tenant (firm B) by day 180. The record follows platform-proof with two tenants and a designed provider swap, so the day-180 platform evidence is a trend rather than a single comparison.
- **Timing of external effects.** Customer-value put a Draft close and a Send canary (passing PA-005, PA-007, PA-009 and PA-010) inside 26 weeks. All three judges called that infeasible for a small team starting from an unbuilt gateway, with tax-season reviewer constraints. The record moves Draft and Send after day 180.
- **Disclosed-Labor Mode and the delivery-engineer role (learning-velocity) are rejected.** In that mode, humans would build readiness boards on partners' real data before the isolation, secret and egress gates pass. That contradicts the proposal's own security timing. It also drifts toward the FDE/services pattern that a Builder.ai-wary investor will discount. The idea of disclosing all labor survives, in the customer-visible ledger.
- **ICP size.** Platform-proof proposed 10-40 staff, 60% or more CAS revenue and 50 or more clients. Customer-value and learning-velocity proposed 5-30 staff with 40 or more clients. The record keeps platform-proof's profile, for tax-season resilience and history depth. The 60% CAS threshold may shrink the pool, because most small CPA firms do both CAS and tax.
- **ML/eval hire timing.** Platform-proof hires around week 12, re-scoped to evaluation. Customer-value defers until the M2 trigger. The record hires around week 12 for evaluation only, because review-package correctness and verifier calibration are needed for M3-lite.
- **Pricing structure.** Platform-proof: no fee, then a $500/month platform fee after the first attested path, a $20-$35 list price and a $750 minimum. Learning-velocity: $750/month flat. Customer-value: a paid, credited, refundable pilot, $15/$25 tiers and a $500 minimum. All three judges chose customer-value. The record starts the pilot clock at the first attested path, because packages cannot exist before then.
- **M2 gate thresholds.** Platform-proof proposed 90% join precision and TRAIN on at least 2 tenants. Learning-velocity proposed 95% join correctness and TRAIN from at least 30% of firms. Customer-value proposed 500 or more corrections and classification errors at 25% or more of review minutes. The record combines them at the lower precision bar, pending the domain expert.
- **Willingness-to-pay threshold.** Customer-value: at least 2 of the first 4 partners convert at $15. Learning-velocity: at least 3 of 5, and internally inconsistent across its own sections. The record uses 2 of the first 4 as the pivot trigger, and 3 of 5 as a target, never as a kill.
- **Compliance items.** Learning-velocity's FTC Safeguards Rule/WISP, SOC 2 and Google restricted-scope verification are plausible, but appear in neither the spec nor the research notes. They are kept only as "counsel or compliance to confirm", alongside the spec-grounded vendor-approval rule (spec §5 L106) and the Workspace data-use restrictions (spec §21 L328).

## Errors corrected during synthesis

### Errors in the proposals, corrected by the panel

- Platform-proof claimed that only `release.*` and `infrastructure.apply` are blocked by a truthful registry. In fact `integration.configure`, `collection.backfill` and `collection.enable_incremental` also need SANDBOX_TESTED.
- Platform-proof and learning-velocity read the fixture's 14-day shadow and 21-day canary budgets as durations. Both are `max_elapsed_seconds` upper bounds.
- All three listed industrial_rfq scenarios as passable on accounting tenants: PA-021 and PA-023, plus PA-014 and PA-016 in customer-value and learning-velocity. They are now accounting adaptations and are kept out of the pass lists.
- Customer-value reported a preparation-mode PA-002 as PA-002. PA-002 is now run as written in sandbox, and the preparation variant is a proposed catalog change.
- Customer-value and learning-velocity scheduled mailbox drafts, an external write, before the production effect ledger.
- Platform-proof listed PA-007 before any ACTIVE plus CANARY release could exist.
- Platform-proof left a release-executor bootstrap gap for `release.activate_shadow`, which needs PRODUCTION_VERIFIED.
- Gate windows overlapped their own gates. They now start on gate exit.
- Learning-velocity used an attribution sample as the experiment-2 read-out.
- Customer-value used unsourced ROI arithmetic, and stated "verified adapters are LOW exposure" as fact. The package's `MaintenanceExposure` enum defines LOW, MEDIUM and HIGH, but no mapping from integration path to exposure.
- Platform-proof's day-180 two-tenant shadow gate would likely slip, so the packet now commits to tenant 1.

### Corrected or clarified while rendering this record

These points were verified against the repository on 2026-10-04. Where the panel's record was imprecise, this document uses the corrected wording.

1. **Fixture region and currency.** The record says "the fixtures are EU/EUR (eu-west-1)". Only the accounting fixtures are: the accounting envelope and plan are EUR with `allowed_regions` eu-west-1. The industrial RFQ envelope is already USD/us-east-1, and the laundry envelope is GBP/eu-west-2. The P0 re-templating task therefore applies to the accounting fixtures. The malformed-plan fixtures in `fixtures/invalid/` also use eu-west-1; they exercise checker rules and do not need re-templating for the product. Separately, PA-001's catalog preconditions name region "eu" and fixture identifiers. Running PA-001 on a US tenant substitutes the tenant's identifiers and region. This record treats that as instance parameters, not a scenario change, and flags it for the catalog owner.
2. **Envelope expiry 2027-03-31.** Confirmed: all three fixture envelopes, and every source grant in them, expire at 2027-03-31T00:00:00Z. That is day 177 of the plan, inside the 180-day window. One clarification: the plan checker evaluates authority at the later of the plan's `planned_at` (2026-10-02T08:00Z) and an explicit `now`. The local suite therefore does not start failing on that date, and `tests/test_fixture_plans.py` already exercises after-expiry behavior with a pinned clock. Running the checker CLI with `--now 2027-04-01T00:00:00Z` fails with ENVELOPE_INACTIVE. The refresh matters for any envelope templated from the fixtures, and for any run against a real clock. The malformed-plan fixtures carry an earlier envelope expiry, 2027-01-01, and are pinned the same way.
3. **Shadow and canary budgets.** Confirmed: `activate-shadow-processing` has `max_elapsed_seconds` 1,209,600 (14 days), and `canary-consolidated-reminders` has 1,814,400 (21 days). Both are upper bounds. Corollary added to D5: both budgets fall short of the one-close floor, and the plan's total budget is 5,184,000 s (60 days). A real tenant plan needs larger step and total budgets.
4. **Maturity floors.** Confirmed: `required_maturity` (plan_checker.py L217-238; the record cited L215-238) gives `release.*` and `infrastructure.apply` PRODUCTION_VERIFIED, `dependency.raise` DOCUMENTED, READ steps and shadow deployments DOCUMENTED, and every other step SANDBOX_TESTED. With the registry reset to DOCUMENTED, the accounting plan fails at ten steps. The record names seven of them (configure, backfill, enable_incremental, infrastructure.apply and the three release steps). It omits `dataset.build`, `training.submit` and `workflow.compile`. The first two are out of scope. `workflow.compile` is on the M3-lite path and needs a SANDBOX_TESTED receipt before the M3-lite build, as added to the D3 table.
5. **Read-step maturity.** D3 says "DOCUMENTED for read steps", while the P1 exit evidence requires SANDBOX_TESTED receipts for `list_folder_changes`, `fetch_document` and the ledger-metadata reads. Both hold. DOCUMENTED is the checker's floor, but PA-001's preconditions require SANDBOX_TESTED inventory records for the two document reads. This document states both.
6. **Registry composition.** The registry has 25 entries: 15 PRODUCTION_VERIFIED, 8 SANDBOX_TESTED and 2 DOCUMENTED. Its own description calls all of them synthetic placeholders. The P0 reset therefore covers every entry, not only the 15.
7. **Materiality trigger wording.** The record lists "Presence UNKNOWN or STALE". In the package, STALE is a `FactStatus` value; `Presence` has only PRESENT, CONFIRMED_ABSENT and UNKNOWN. D6 renders the trigger as "Presence UNKNOWN, or fact status STALE, DISPUTED, or INFERRED below the auto-accept threshold".
8. **Market wording on bundling.** The record says "Xero and Intuit bundle it free". The market notes support a narrower claim. Intuit Accountant Suite entry tiers are no-charge during the introductory period (explicit for the UK and Australia; the US per a secondary source). Xero Partner Hub Document Requests exist, but their pricing is not disclosed. D2 uses the narrower wording.
9. **Test count.** 819 is the count in the current VALIDATION_REPORT.md, and it will change as tests are added. Never-claim item 1 is worded so that it does not go stale.
10. **RELEASE state machine.** Confirmed: PAUSED is reachable only from ACTIVE. CANARY can already move to ROLLED_BACK, so a canary can be rolled back but not paused. SHADOW can only advance to CANARY or retire. "Pause and kill from SHADOW and CANARY" therefore needs a PAUSED transition from both states and a rollback transition from SHADOW.

## References

### Repository sources

- [Spec v0.2](../spec/Plumb_Autonomous_Implementation_Specification_v0.2.md) (675 lines; line numbers cited above were checked against this file).
- [Requirements index](../spec/requirements_index.json): 63 requirements, 10 ADRs.
- [Production acceptance catalog](../acceptance/production_acceptance_catalog.yaml): 30 scenarios (13 accounting, 7 industrial_rfq, 6 platform, 4 laundry), none executed against production.
- [Accounting plan fixture](../fixtures/plans/accounting_evidence_preparation.json), [accounting envelope fixture](../fixtures/envelopes/accounting_evidence_preparation.json), [laundry plan fixture](../fixtures/plans/laundry_route_preparation.json), [RFQ envelope fixture](../fixtures/envelopes/industrial_rfq_preparation.json), [laundry envelope fixture](../fixtures/envelopes/laundry_route_preparation.json).
- [plan_checker.py](../plumb/checker/plan_checker.py), [approval_checker.py](../plumb/checker/approval_checker.py), [capability_registry.json](../plumb/registry/capability_registry.json), [machines.py](../plumb/statemachines/machines.py), [effect_ledger.py](../plumb/ledger/effect_ledger.py).
- [VALIDATION_REPORT.md](../VALIDATION_REPORT.md), [README.md](../README.md).

### Research notes

These are the panel's working inputs, held outside the repository:

- Eight reader notes: spec-1-7, spec-8-16, spec-17-29, appendices, acceptance-and-index, implementation-reality, market-accounting, market-implementation.
- The three strategy proposals (platform-proof, customer-value, learning-velocity).
- The three judgments.

### Market sources

All market facts come from the panel's market notes. The flags are: vendor-run or vendor-reported, secondary (reported by someone other than the originator, or seen through search summaries), and directional (small or self-selected sample).

| Ref | Fact used | Source | Flag |
|---|---|---|---|
| M1 | About 13.4k CPA firms with 5-19 employees; 2,015 CPA and 1,247 other-accounting firms with 20-99 employees | Census SUSB 2022, https://www2.census.gov/programs-surveys/susb/tables/2022/us_state_6digitnaics_2022.xlsx | Employer firms only; excludes nonemployers |
| M2 | Hiring experienced staff is the #1 issue for firms with 11-30 professionals | AICPA PCPS Top Issues Survey via CPA Practice Advisor, June 23, 2026, https://www.cpapracticeadvisor.com/?p=185547 | Secondary report |
| M3 | Getting documents from clients is the biggest workflow issue (816 respondents) | Financial Cents 2025 State of Accounting Workflow Automation, https://financial-cents.com/?p=9086 | Vendor survey; rank only, no percentage |
| M4 | 68% want an agent to chase documents; 62% require approval before sending; 53% demand no training on their data | Uku AI in Accounting 2026, https://getuku.com/ai-in-accounting-report/ | Vendor survey; small, self-selected sample; directional |
| M5 | 88% use AI for at least one service; about 10 apps; 48% fragmented; $21k average tech spend; 80% outsource at least one service; 60% of clients ask for proof of AI data protection | Intuit QuickBooks 2026 Accountant Technology Survey via CPA Practice Advisor, July 2, 2026, https://www.cpapracticeadvisor.com/2026/07/02/the-2026-accountant-technology-survey-turning-data-revelations-into-a-firm-of-the-future/185807/ | Vendor survey (725 respondents) |
| M6 | Top barriers: time to learn and implement 41%, trust and accuracy 21%, cost 6% | Financial Cents State of AI in Accounting and Bookkeeping 2026, https://financial-cents.com/?p=39931 | Vendor survey (486 respondents) |
| M7 | Top barrier is training and implementation time (31%) | Ramp and CalCPA 2026, https://ramp.com/reports/benchmarking-the-modern-cpa-firm-2026-or-calcpa-and-ramp | Vendor co-branded; California only |
| M8 | Basis works with about 30% of the top 25 firms and 20% of the top 150 | CPA Practice Advisor, Feb 24, 2026, https://www.cpapracticeadvisor.com/2026/02/24/basis-raises-100-million-to-deploy-ai-agents-for-accounting-firms/178759/ | Vendor-reported |
| M9 | Double: 4,000+ firms and 150% NDR; per-connected-client pricing and a $200/month annual-commitment tier; $10/$25/$50 tier prices | https://www.cpapracticeadvisor.com/2025/12/13/double-raises-6-5-million-series-a/174948/; https://doublehq.com/pricing; tier prices from https://www.capterra.com/p/10012825/Keeper/ | NDR and firm count vendor-reported; tier prices secondary |
| M10 | Xenett about $7.5-$15 per client-month | https://www.xenett.com/pricing | Vendor pricing page |
| M11 | Financial Cents seats $19-$89 per user-month; month-end close add-on $5 per client-month | https://financial-cents.com/pricing/ | Vendor pricing page |
| M12 | Karbon seats $59-$99 per user-month; Kai and a public MCP server | https://karbonhq.com/pricing/; https://karbonhq.com/resources/karbon-launches-kai/ | Vendor pages; Kai in early access |
| M13 | Uku seats $19-$99 per user-month; Uku MCP | https://getuku.com/pricing/ | Vendor pricing page |
| M14 | Intuit Accountant Suite entry tiers at no charge during the introductory period | https://www.cpapracticeadvisor.com/?p=171765; US pricing via https://my-cpe.com/insights/news-and-insights/technology/intuit-rolls-out-smartest-ai-accountant-suite-for-next-gen-accounting | US no-charge status from a secondary source |
| M15 | Xero Partner Hub Document Requests chase, remind and match; JAX and XeroForce | https://itbrief.co.uk/story/xero-expands-ai-tools-for-accountants-small-firms | Secondary coverage; pricing not disclosed |
| M16 | Buyers moving from assistive AI toward platforms that commit to workflow results by 2028 | Gartner, Apr 2, 2026, https://www.gartner.com/en/newsroom/press-releases/2026-04-02-gartner-expects-most-enterprises-to-abandon-assistive-ai-for-outcome-focused-workflow-by-2028 | Page returned 403; from title and secondary coverage |
| M17 | 70% of enterprises will abandon agentic AI built by vendor FDE by 2028; define IP ownership and an exit strategy from day one | Gartner, Sep 29, 2026, https://www.gartner.com/en/newsroom/press-releases/2026-09-29-gartner-predicts-70-percent-of-enterprises-will-abandon-agentic-ai-built-by-vendor-forward-deployed-engineering-by-2028; details via https://techstrong.ai/articles/gartner-warns-70-of-vendor-built-ai-agent-projects-face-abandonment-by-2028/ | Secondary coverage |
| M18 | "Agent washing" warning | Gartner, Jun 25, 2025, https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027 | Search summary |
| M19 | Trust in fully autonomous agents fell from 43% to 27% | Capgemini Research Institute, https://www.capgemini.com/insights/research-library/ai-agents/ | Publication date not stated on page |
| M20 | Builder.ai bankruptcy after reports its "AI" relied on human engineers | https://www.techspot.com/news/108173-builderai-collapses-after-revelation-ai-since-2017-really-hundreds-engineers.html | Press report |
| M21 | FTC Operation AI Comply continues to pursue deceptive AI claims | https://www.hklaw.com/en/insights/publications/2026/08/operation-ai-comply-2-years-later-continued-enforcement | Law-firm analysis |
| M22 | OpenAI Agent Builder shuts down Nov 30, 2026 | https://developers.openai.com/api/docs/deprecations | Vendor notice |
| M23 | 35% fear errors or hallucinations | Accounting Seed 2026, https://www.accountingseed.com/resources/the-state-of-ai-in-accounting-2026 | Vendor survey (128 respondents) |
| M24 | Bench shut down Dec 27, 2024, leaving about 35,000 US customers | https://www.geekwire.com/2024/vancouver-fintech-company-bench-accounting-announces-sudden-shutdown/ | Press report |
| M25 | IRC 7216 consent obligations for tax-return data disclosed to AI systems | https://my-cpe.com/blogs/ai-compliance-for-cpa-accounting-firms-irc-7216-aicpa-ftc | Secondary compliance commentary; not legal advice; verify with counsel |
| M26 | superglue describes itself as "an agentic implementation platform" | https://superglue.ai/ | Vendor self-description |
| M27 | Nango Management MCP lets coding agents create integrations; separates development and runtime credentials | https://nango.dev/blog/how-to-build-ai-agent-integrations-using-the-nango-management-mcp | Vendor |
| M28 | Membrane Agent builds integrations from prompts | https://getmembrane.com/articles/all/announcing-membrane-the-era-of-self-integrations | Vendor |
| M29 | Make Maia turns plain language into configured scenarios | https://www.make.com/en/blog/maia-conversational-ai-coworker-for-ai-agents-and-automation | Vendor; launch date from a secondary source |
| M30 | Pilot's "fully autonomous" AI Accountant, "zero human intervention" | https://www.cpapracticeadvisor.com/2026/02/04/pilot-rolls-out-fully-autonomous-ai-accountant/177453/ | Vendor claim |
| M31 | Current (formerly Crete), a Thrive-backed roll-up building tools in-house | https://www.cpapracticeadvisor.com/2026/06/03/crete-professionals-alliance-rebrands-as-current/184461/; https://finance.yahoo.com/news/thrive-backed-accounting-firm-crete-130200467.html | Press reports |
| M32 | SMB agency AI builds about $4.5k-$25k | Vendor-written guide; URLs as recorded in the market notes: https://www.layer3labs.io/ai-consulting-for-small-business, https://aiimplementationcompanies.com/ | Low reliability |

The market notes also record a gap: no reputable primary source exists for hours per client-month spent on close or document chasing. That is why this record contains no ROI arithmetic.
