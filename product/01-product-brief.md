# Product Brief

- Status: Draft v0.1 (2026-10-04), proposed — requires founder ratification
- Owner: Product
- Basis: spec v0.2, [decision record](02-strategy-decisions.md)

Part of the product doc set ([index](README.md)). The normative source is [spec v0.2](../spec/Plumb_Autonomous_Implementation_Specification_v0.2.md) (October 2, 2026, prepared for Roy Salman). Requirement texts are in [requirements_index.json](../spec/requirements_index.json) and acceptance scenarios in the [acceptance catalog](../acceptance/production_acceptance_catalog.yaml).

**How to read this brief.** Three kinds of statement appear, and they are labeled where it matters:

| Label | Meaning |
|---|---|
| Spec requires | Normative text in spec v0.2, cited as "spec §N" or by requirement id. |
| Package has | Code in the reference package today. It is a local library; nothing is deployed, connected to a customer or measured. |
| Proposed | This doc set's proposal, taken from the decision record (D1 to D12). Not yet ratified. |

Every threshold, price and date in this brief is a hypothesis unless the spec states it.

---

## 1. Summary

Plumb's product contract is to perform the implementation of useful automation for small businesses that cannot do it themselves: connect the tools a business already uses, build the collection and workflow on top of them, prove the result works on the customer's own data, keep it running, and record every minute a human spent along the way (spec §1; PL-001, PL-002, PL-003). The first market is independent US accounting firms of 10 to 40 staff that lean to client accounting services (CAS) and bookkeeping, run mixed stacks and have at least 50 recurring monthly-close clients (D1). The first workflow is monthly-close evidence readiness, shipped preparation-only. For each client-period Plumb will show which required items are present, confirmed absent or unknown, with provenance, and prepare one verifier-attested, ready-for-review package for the reviewing accountant (D2). Nothing goes to a firm's clients until a production action gateway has passed its safety scenarios, which is after day 180; the earliest policy-approved Send canary close is around July 2027 (D3, D5, D6). The company-level bet is that the second and third firms need much less engineering than the first. We measure that as engineering-intervention hours per verified deployment (EIH/VD), with failed attempts counted (PL-062, ADR-010, D10). Today Plumb is a normative spec plus a locally tested policy kernel. The value loop is not built and no customer has been onboarded (section 11).

---

## 2. The problem

### 2.1 Small businesses use AI, but rarely inside their operations

- AI use among US businesses was 17-20% between December 2025 and May 2026. It rose at firms with 20 or more employees but did not change significantly at firms under 20 (US Census Bureau, Business Trends and Outlook Survey) [M1].
- 76% of small businesses use AI, but only 14% have fully integrated it into core operations, and 73% say they would benefit from more training and implementation resources (Goldman Sachs 10,000 Small Businesses survey, n=1,256) [M2].

These two sources define "use" differently and survey different samples, so their percentages should not be compared. Both point the same way: AI rarely reaches day-to-day operations in small firms.

### 2.2 Implementation, not price, is the barrier

- In small accounting and bookkeeping firms (n=486, mostly 2-30 people), the top barrier to AI is time to learn and implement (41%). Cost is cited by 6%. Only 20% report clear, measurable ROI (Financial Cents, August 2026) [M3].
- Among 400+ California CPA-firm professionals, the top barrier is training and implementation time (31%), and only 10% have generative AI integrated across operations (Ramp and CalCPA, 2026) [M4].
- Today's options leave the implementation either with the customer (do-it-yourself agent builders) or with people whose cost scales with headcount (agencies, forward-deployed engineers). See section 7.

The spec answers this with the product contract itself. Humans supply authority and domain judgment at narrow, explicit boundaries, and those boundaries "must not turn into a requirement for the customer to become a systems integrator" (spec §1).

### 2.3 In accounting firms, month-end evidence is the pain

- Getting documents from clients is the #1 workflow issue, ahead of manual administrative tasks. Clients take 5 days on average to submit requested documents (Financial Cents 2025 report, 816 professionals) [M5].
- Hiring experienced staff is the #1 issue for CPA firms with 11-30 professionals, and managing workload and capacity is #3 (AICPA PCPS Top Issues Survey, June 2026) [M6].
- Firms run about 10 apps, 48% call their setup functional but fragmented, accountants lose about 5 hours a week to data re-entry, and 80% of firms outsource at least one service (Intuit QuickBooks 2026 Accountant Technology Survey, n=725) [M7].
- 68% of firms want an AI agent to chase clients for missing documents, the top task they would delegate; 62% require human approval before anything is sent or filed, and 53% demand no model training on their data (Uku AI in Accounting 2026; a small, self-selected sample, so directional only) [M8].

Chase-and-remind is already table stakes (section 7). What incumbents do not produce across a mixed stack is a provenance-backed package that keeps "unknown" separate from "confirmed absent" (PL-010). That separation is what stops "please send the document you already sent", the failure class tested by PA-005 and PA-011 (D2).

### 2.4 A tension we record rather than hide

Spec §1 starts from "an ordinary business with little or no existing AI." The beachhead is not AI-naive: 88% of accounting professionals use AI for at least one client service, although only 30% have it fully embedded [M7]. For these firms Plumb's value is implementation and verification across their whole stack, not a first exposure to AI (D1).

### 2.5 What we do not know

The market research found no reputable primary source for the hours a firm spends per client-month on close assembly or chasing. This brief therefore states no hours-saved or ROI figure. Each design partner runs a 2-week month-0 time study before shadow, so any time-saving claim can be falsified (D2, D7).

---

## 3. The product promise

### 3.1 Plumb performs the implementation

Given an authorized business goal and an autonomy envelope, and for supported environments, Plumb must do the engineering itself (spec requires, PL-001, PL-002): inventory inspection, source profiling, schema mapping, integration setup, collection deployment, evaluation dataset construction, workflow assembly, deployment and monitoring. The customer grants access, answers focused domain questions and reviews business results. Those inputs are a different kind of human effort, and they are recorded separately from engineering (PL-002, PL-003).

For the first firms this means the following (proposed, D3):

1. Plumb configures certified transport connectors for the firm's ledger, mail and document store.
2. An agent fills in the tenant's BuildPlan from the firm's EnvironmentInventory and generates the client/period/obligation mapping.
3. Plumb deploys a shadow collector, backfills 12-24 months from an agreed watermark, reconciles source counts and switches to incremental capture.
4. A preparation-only workflow assembles review packages; the accountant signs off.

Until replication on tenants 2 and 3 passes (M1R), we describe this as "agent-configured certified connectors and agent-built collection", never as "automatically constructed" (D4, D8).

### 3.2 Three outcomes, and nothing else

Every authorized goal ends in exactly one of three outcomes (spec requires, PL-001). A recommendation, generated prompt or code archive alone never counts as complete.

Billing in this table is proposed (D7) and every figure is a hypothesis.

| Outcome (PL-001) | What the customer sees | Billing treatment (proposed) |
|---|---|---|
| A verified operating intervention | The result, its verifier attestation and its receipts, in the results-and-effort view | After paid conversion, billed per active client-month that yields an attested package |
| An actionable external dependency with a preserved, resumable build | A blocked-dependency card naming the exact missing consent, policy or input, who can resolve it and what resumes; completed work is kept | Customer-side blocks are not billed while open (the firm minimum still applies); Plumb-side and vendor blocks are never billed |
| A terminal failure that explains what was attempted and why execution stopped | What was tried, the failure class and why it stopped | Never billed |

Configuring a native feature the firm already owns, such as its Xero or Financial Cents reminders, is a valid verified intervention when it is the cheapest adequate option (PL-013). It bills at the same rate, so Plumb is never paid more for building more (D7). Pricing is per active client-month: Prepare $15 and Prepare + Chase $25, annual, with a $500 monthly firm minimum, no seats and no implementation fee (hypotheses; details in the [decision record](02-strategy-decisions.md)). Design partners pay a pilot fee at signature and convert to paid annual after one full close with the workflow ACTIVE at or above the correct-package threshold; tenant 1's conversion is expected in P6 (a founder decision to ratify; section 3.6).

### 3.3 Supported environments, stated honestly

PL-002 applies "for supported environments", which the spec does not enumerate. Proposed (D3): publish a "supported environments v1" list stated per operation and per capability maturity level (discovered, documented, sandbox-tested, production-verified; PL-008), backed by real probe receipts on the customer's own accounts (PL-007). Anything outside the list becomes a dependency or a backlog item, never hidden manual work.

### 3.4 Honest effort accounting

Plumb records all human effort, the partner's and its own, in five categories (spec requires, PL-003). The rubric below is proposed (D6, with clarifications that amend D6 and are flagged in the [decision record](02-strategy-decisions.md)) and is frozen in P0 so the numbers stay comparable across tenants.

| Category | Includes (proposed rubric) |
|---|---|
| CUSTOMER_AUTHORIZATION | Grants, consents and envelope decisions; approving the reminder policy (amends D6) |
| DOMAIN_CLARIFICATION | Owner answers on conventions; label or attribution sample audits; baseline-study recording overhead (the timed close work itself is not logged again); scheduled weekly check-ins (amends D6) |
| NORMAL_BUSINESS_REVIEW | Per-case approvals, draft review and package sign-off |
| ENGINEERING_INTERVENTION | Implementation work by any person, Plumb or customer staff (amends D6; spec Appendix B: "If a person manually wires the integrations or writes the production workflow, record that labor"): wiring, mapping, plan or workflow authoring or editing; manual deployment |
| OPERATIONAL_REPAIR | Plumb staff fixing a running collector or workflow |

The interruption budget (D6) counts unscheduled asks; scheduled check-in time is reported beside it. The package's principal types have no type for Plumb staff, so one must be added before their effort can be captured (a contract gap).

The ledger is customer-visible. A deployment is labeled "supervised", with its labor shown, until that path has PA-027-level evidence (D4, D8). Plumb never calls a deployment autonomous if a person secretly performed the implementation behind the interface (PL-003).

### 3.5 What "done" means: verified, not deployed

A deployment is not an outcome. Spec §18 defines completion evidence by artifact type. A collector needs a source change and the resulting authorized event. An integration needs a required operation on the intended account. A workflow needs a complete case and its external receipts. A business claim needs prospective measured outcomes, with review and rework counted. The verifier inspects actual state rather than trusting the agent's claim, and the implementation job cannot write to the verifier (PL-042, ADR-007).

In the accounting wedge:

- The collection path counts as working only after a document the firm adds outside Plumb is observed, its authoritative content is fetched, and the right client/period record is verified as changed. PA-001 waits at most the configured five-minute health deadline for that event (spec Appendix B; PA-001).
- A package is "ready for review" until the accountant signs off. It is never reported as an autonomous close (spec §15).
- For the customer, done means an attested package the accountant explicitly accepted without material correction. Accepted review packages per month is the customer co-headline metric, always shown with its rate over all eligible client-periods and with Plumb human minutes per accepted package (D10; [metrics](06-metrics.md)).

### 3.6 Release tiers

Plumb's external effects grow only as evidence accrues (proposed, D3, D4, D6). Phase windows are hypotheses.

| Tier | What Plumb does | Gate before the tier ships | Earliest phase |
|---|---|---|---|
| Prepare (preparation-only) | Read-only close-readiness ledger, then review packages with "what Plumb would have done" reports. A package release goes SHADOW (at least one full close), then CANARY on a subset of client-periods whose accountants use the prepared packages in their real review, then ACTIVE. Effect classes: READ, INTERNAL_WRITE and EXTERNAL_WRITE_REVERSIBLE (connector setup and enabling incremental capture on the firm's own accounts); no EXTERNAL_COMMUNICATION at any stage. This corrects the decision record's "READ and COLLECT" wording (COLLECT is a data purpose). | Ledger: M1 (PA-001 plus the safety bundle). Packages: PA-002 run as written in sandbox, plus PA-003, PA-004, PA-006, PA-008, PA-010, PA-011 and the PA-021 parser-bounds adaptation | P2 M1 (ledger); P4 M3-lite and P5 (packages in shadow); canary, then ACTIVE, after the first full shadow close (late P5 to P6) |
| Draft (mailbox drafts staff send) | Consolidated requests created as drafts in the firm's mailbox. Staff review and send every one. | The production action gateway passes PA-005's dispatch-time re-check, the PA-009 and PA-015 behaviors, PA-006 and PA-010 approval binding, and pause and kill from canary | P6, after day 180 |
| Send (policy-approved sending, canary first) | One consolidated request per client-period-obligation epoch, with one owner across staff, under an approved reminder policy | Full PA-002 in canary, plus PA-005, PA-007, PA-009 and PA-010, accounting adaptations of PA-014 and PA-016, and a recovery drill. Each client and obligation type graduates from Draft only through the D6 calibration ladder (at least two Draft closes and 20 drafts of that type) | After the P6 Draft closes: the earliest Send canary close is around July 2027 (about weeks 39-41) |

---

## 4. Who it is for

Beachhead (proposed, D1; thresholds are hypotheses):

| Attribute | Profile |
|---|---|
| Firm | Independent US accounting firm, 10-40 staff, at least 60% of revenue from recurring bookkeeping/CAS, so February-April tax season does not stall the domain owner |
| Book | At least 50 recurring monthly-close clients with 12-24 months of history |
| Stack | QBO and/or Xero client ledgers; Google Workspace or Microsoft 365 mail; a document store separate from the ledger (Drive, SharePoint/OneDrive, Dropbox or SmartVault); optionally Karbon, Financial Cents or Double, read-only |
| Region | One US region |
| Buyer | Managing partner, COO or CAS director, acting as HUMAN_OWNER of the envelope |
| Champion and primary user | The reviewing manager or senior accountant who assembles packages today |
| Commitments | Grants read OAuth; names a domain owner with about 2 hours a week; runs a 2-week baseline time study; pays a pilot fee; allows anonymized publication of labor-ledger data |

**Qualify out (D1):** solo and 2-4-person firms; top-100 and 100+-staff firms; tax-only or seasonal practices and any in-scope source holding tax-return information; firms standardized on one ecosystem whose native chase-and-match already works (unless they want Plumb to configure and verify those native features); desktop or on-prem ledgers and NetSuite/Intacct; evidence in closed portals that cannot be probed; document stores or mail providers that cannot meet the catalog's assumptions (webhooks plus overlap polling; request-id lookup); firms expecting posting or an "autonomous close"; firms needing on-prem or multi-region.

**The pool is countable.** Census SUSB 2022 counts 48,511 CPA firms with fewer than 20 employees, about 13,400 of them with 5-19, plus 2,015 CPA firms and 1,247 "other accounting" firms with 20-99 employees [M9]. These are employer firms only, the size bands do not match the 10-40-staff profile, and they include tax-heavy firms, so they indicate the order of magnitude of the pool; they do not size the ICP.

Why accounting first, the competitive map and the message tests are in [market and positioning](08-market-and-positioning.md). How the five design partners are selected and what they sign is in the [design-partner program](09-design-partner-program.md).

---

## 5. Personas

The firm's client is an affected party, not a principal. Their effort is not a PL-003 category, and they own no decision inside Plumb.

| Persona | Goals | Pains | Decisions they own | How Plumb serves them |
|---|---|---|---|---|
| **Firm owner** (buyer; HUMAN_OWNER of the envelope). Managing partner, COO or CAS director. | Grow recurring clients without matching headcount; predictable closes; protect client relationships and client data | Hiring and capacity [M6]; about 10 fragmented apps [M7]; no time to implement [M3]; AI claims they cannot audit; clients asking for proof of AI data protection [M7] | Goals; envelope contents (sources and purposes, processors, region, spend cap, allowed effect classes, expiry, escalation); DATA_USE and IMPLEMENT_OPERATE approvals; the reminder policy once Send ships; pause and revocation; pilot and contract | One implementation card per intervention; batched requests within the interruption budget (at most 1 unscheduled batched owner request per tenant-week, with scheduled check-in time reported beside it; hypotheses, D6); results-and-effort view with the labor ledger; Plumb absorbs its own engineering (D7); export and a pre-agreed exit (D9) |
| **Reviewing accountant** (champion, primary user; HUMAN_REVIEWER and HUMAN_APPROVER). Reviewing manager or senior accountant. | A complete, correctly attributed package per client-period at the start of review; fewer assembly and review minutes; keep sign-off authority | Hand assembly from inbox, drive and ledger; items missing, misfiled or already received; fear of AI errors (35% of surveyed finance professionals) [M10] | Package sign-off (accept, correct, amend); case-level approvals when a materiality rule fires (D6); answers that become versioned conventions; draft review where the firm assigns it | Close-readiness ledger; review surface showing each item as PRESENT, CONFIRMED_ABSENT or UNKNOWN with provenance; a correction captured once and reused (PA-004); approvals batched into at most one session a day (hypothesis, D6) |
| **Bookkeeper** (secondary user) | Know what is missing per client and who is already chasing it; stop hunting for documents | Duplicate chasing across staff; re-requesting documents already received; per-person reminder lists ("A per-person list of emails is insufficient", spec Appendix B) | The spec names none. Day-to-day client contact today; in the Draft tier, staff review and send drafts (D6) | Documents attributed to the right client and period (PA-001, PA-003); held vs missing in the readiness ledger; chase history once mail-history read is connected (P4); one shared obligation with one owner (spec Appendix B; PA-007) once requests ship |
| **Firm's client** (affected party, not a principal) | Be asked once, clearly, only for what is actually missing | Duplicate, stale or wrong-client requests | Supplies documents. No decision inside Plumb | No request reaches a client before the Draft gates pass, and then staff send every draft; Plumb sends nothing itself before the Send canary. Then one consolidated request per client-period-obligation epoch (PA-002, PA-005, PA-007); client-request integrity is a tracked metric (D10) |
| **Plumb domain expert**. Part-time CPA with CAS experience, 0.5 FTE or more, not drawn from a design-partner firm (D12). | Define meaningful correctness so packages can be judged | The spec sets no universal numeric quality bar ("No universal 99% score defines safe financial posting, identity resolution and route planning alike", spec §24); reviewers may disagree on what is "material" | Owns the domain acceptance corpus (spec §26); co-owns threshold sheet v1 with the founder; sets the numeric correct-package threshold (P4 exit); ratifies the M2 gates (D5) | A protected, segregated evaluation corpus (PL-044); adjudication samples from the review surface. Corpus and threshold work is platform investment; any edit to a tenant's mapping or plan is ENGINEERING_INTERVENTION (D6, D10) |
| **Plumb engineer/operator**. Tech lead, integration engineer, product engineer, security/platform engineer (D12). | Build primitives once so each new tenant needs fewer of them | Pressure to hand-wire during a supervised first delivery (spec §1); manual operations before a maintenance agent exists | Platform changes through the registry and platform policy, never applied through a customer implementation job (spec §4) | Auto-captured effort ledger plus a separate platform-investment ledger; bounded repair (PL-018); every tenant-specific act logged as ENGINEERING_INTERVENTION or OPERATIONAL_REPAIR. No per-customer delivery engineers (D12) |
| **Independent verifier** (service + owner). The VERIFIER principal, owned by a verification and acceptance-harness engineer who reports outside the build team (D12; hire by about week 6, hypothesis). | Decide completion from actual external state | Builders self-certifying; synthetic tests mistaken for business evidence (PL-044) | Issues PASS or FAIL attestations bound to artifact digest, scope and environment; decides whether a step or release is VERIFIED (PL-042, ADR-007) | Protected test bundles the builder cannot read or write; the fault-injection harness; ledger-audit tooling. A separate ledger auditor (founder plus an external technical advisor) reviews the labor ledger at M1, M1R and M5 (D12) |

Notes:
- The spec's accounting fixture names the owner a "finance controller" ([envelope fixture](../fixtures/envelopes/accounting_evidence_preparation.json)). In this doc set the canonical name is Firm owner.
- Principal types come from the package contracts: HUMAN_OWNER, HUMAN_REVIEWER, HUMAN_APPROVER, VERIFIER and others. The firm's client has no principal type, consistent with its role as an affected party. Plumb staff have none either, which is a contract gap (section 3.4).

---

## 6. Jobs to be done

"First served" names the phase and tier in which Plumb starts doing the job (proposed; windows are hypotheses; see the [roadmap](04-roadmap.md)).

| # | Persona | Job statement | First served |
|---|---|---|---|
| J1 | Firm owner | When we take on more recurring clients without hiring, I want month-end evidence gathered and checked across the tools we already use, so reviewers spend their time on judgment instead of collection. | P2 M1 (readiness ledger); P4-P5 (packages in shadow) |
| J2 | Firm owner | When I let software touch client data, I want to grant bounded authority once, per source and purpose, and see exactly what was done and by whom, so I can answer my clients' data-protection questions. | P1 M0 and P2 M1 (envelope, implementation card, effort ledger) |
| J3 | Firm owner | When I pay for implementation, I want to pay only for outcomes verified on our own data and to keep every spec, test and export if we leave, so we carry no hidden services bill and no lock-in. | Paid pilot contract (P1); per-client-month billing once the partner converts to paid annual, after one full close with the workflow ACTIVE at or above threshold (tenant 1 expected in P6) |
| J4 | Reviewing accountant | When I open a client's close, I want one package that shows which required items are present, confirmed absent or unknown, with links to the source, so I don't assemble it by hand or miss something. | P4 M3-lite (sandbox, then production shadow); P5 (first full shadow close) |
| J5 | Reviewing accountant | When I correct something, I want the correction captured once and applied as a convention, so I am not asked the same question next month. | P4 M3-lite |
| J6 | Reviewing accountant | When something will go to a client, I want to approve a policy rather than every message and be pulled in only on material exceptions, so I keep control without becoming the bottleneck. | P6 (Draft); policy-level Send no earlier than about July 2027 |
| J7 | Bookkeeper | When I am about to chase a client, I want to know whether the document already arrived and whether a colleague already asked, so the client never gets the same request twice. | P2 (held vs missing); P4 (chase history); Send canary, about July 2027 at the earliest (one owner on sends) |
| J8 | Bookkeeper | When a client finally sends documents, I want them filed against the right client and period automatically, so I stop hunting through inboxes and folders. | P2 M1 |

---

## 7. Value proposition and differentiation

**Category (proposed, D8):** verified implementation for accounting firms, glossed as "implementation you can audit." We avoid "agentic implementation platform" (superglue already uses it [M13]), "AI employee" and "fully autonomous."

**Headline (proposed, D8):** "Plumb connects the tools your firm already uses and builds your month-end evidence workflow for you, then proves it works on your own data: every document traced to its source, a review package ready for your accountant, and a receipt for every hour a human spent." The line "one owner and one request per missing item" is added only once the Send canary has evidence.

**Short form:** "Close-ready, with receipts."

### 7.1 Five differentiators

| Differentiator | What it means for the firm | Spec basis | Status today |
|---|---|---|---|
| Verified implementation | Nothing is "done" until an independent verifier attests it against the firm's own systems; receipts are visible | PL-001, PL-042, PL-043, ADR-007; spec §18 | Package has the attestation contract and a release checker that matches attestations by digest. No verifier service exists |
| Labor ledger | Every human minute, the firm's and Plumb's, recorded in five categories with failed attempts included; the firm can audit its own ledger | PL-003, PL-059, PL-062, ADR-010 | Package has the category enum and an effort-record model that nothing uses; there is no capture API. Proposed as the first product code (P0) |
| Autonomy envelope | The owner sets the limits once. Plumb works inside them and asks only at the boundary, naming the decision type and its owner | PL-005, PL-040, PL-041, PL-053 | Package has the envelope contract and an approval checker that can group missing authorizations into one request. No authoring UX or approvals endpoint |
| Cross-system obligation identity | One record per client, period and obligation across ledger, mail and documents; unknown kept separate from confirmed absent; one owner and one request per obligation epoch | PL-009, PL-010, PL-011, PL-037, PL-039; spec Appendix B | Package has the evidence contract and a single-process SQLite effect-ledger simulation with effect-slot dedup. No collector or object-resolution service |
| Native-first and remove-step | Plumb compares any build against the firm's current process and its native features, and may conclude "configure what you own" or "remove this step" | PL-013, PL-031; spec §1 | Package's OpportunitySpec requires both baselines (current process and native feature) and forces a rejected or blocked status when the net-value upper bound is not positive. No discovery engine. Proposed: a vertical opportunity library instead of open-ended discovery (D3) |

Agent-built integrations are becoming table stakes: Nango's Management MCP, Membrane and Make's Maia all claim a version of it [M12]. Plumb's defensible layer sits above the connectors. In both market scans, no competitor reviewed publishes a labor ledger or independent verification receipts. That is absence of evidence from limited web searches, not proof. Trust in fully autonomous agents fell from 43% to 27% in one year (Capgemini) [M11], which is why the proof points lead and "autonomous" does not.

### 7.2 Against the alternatives

Prices are vendor-listed unless flagged; competitor capabilities are as described by vendors and were not tested.

| Alternative | Examples | What they do well | What they leave to the firm | Plumb's position (D8) |
|---|---|---|---|---|
| Practice-management suites | Karbon ($59-$99 per user/month), Financial Cents ($19-$89 per user/month; close add-on $5 per client/month), TaxDome [M14] | Workflow, portals and automated client reminders; adding agents and MCP servers | Configuring checklists and automations; evidence that lives outside their own data | "Keep your PM tool; Plumb makes your whole stack work together and proves it." Integrate through the Karbon and Uku MCP servers, and configure native reminders when they are enough |
| Ledger-native agents and close tools | Xero JAX, Document Requests and XeroForce; Intuit Accountant Suite (free during introduction, secondary source); Double (per connected client; $10/$25/$50 tiers from secondary listings) [M15] | Excellent inside one ledger, including chase-and-match | Evidence spanning ledgers, inboxes and drives; books split across QBO and Xero | "Excellent inside one ledger; Plumb is for firms whose evidence spans ledgers, inboxes and drives." A Xero-only firm should use Xero (qualify-out) |
| Do-it-yourself agent builders | Zapier (Pro from $19.99/month billed annually), n8n, Make, Microsoft Copilot Studio [M16] | Cheap and flexible; plain-language build copilots | Finding the opportunity, data plumbing, testing and maintenance; platform churn (OpenAI's Agent Builder is scheduled to shut down on November 30, 2026) [M17] | "They make you the systems integrator; we implement and keep it running." |
| Forward-deployed engineers, agencies, MSPs | OpenAI consulting (reported $10M minimum); SMB agencies ($4.5k-$25k per first build, low-reliability source); MSPs (91% offer or use AI) [M18] | Human judgment and custom builds | Cost that scales with headcount, dependency and handoff risk. Gartner predicts 70% of enterprises will abandon agentic AI built through vendor FDEs by 2028 (via secondary coverage) [M19] | "Customer-owned specs, tests and adapters, an itemized labor ledger, and an exit path." |
| Outsourced or offshore staff | 80% of firms outsource at least one service [M7] | Flexible labor | The same manual assembly, done elsewhere | Compared per accepted package on cost and quality, using the labor ledger (proposed) |

The full competitive map, including Basis, Digits, Pilot and the roll-up channel, is in [market and positioning](08-market-and-positioning.md).

---

## 8. Product principles

Each principle traces to the spec. Where a principle rests on a decision-record choice rather than a spec requirement, that is stated.

| # | Principle | What it means in the product | Traces to |
|---|---|---|---|
| 1 | Done means a verified outcome | No step, build or package is shown as done until the independent verifier attests it against actual external state. Deployed is not done. A package is "ready for review" until sign-off. | PL-001, PL-016, PL-042, PL-043, ADR-007 |
| 2 | Continue within the envelope; pause with a precise, resumable dependency | Inside granted authority, work proceeds without asking. Outside it, Plumb stops that branch, names the exact missing consent, policy or input, who resolves it and what resumes, keeps completed work and continues unrelated work. | PL-005, PL-017, PL-041, ADR-002; spec §4 |
| 3 | Preparation before effects | Read and prepare first. Mailbox drafts only after a production gateway passes its scenarios; policy-approved sends only after draft calibration; canary first, with pause and kill; any HIGH-severity failure blocks activation. | PL-035, PL-036, PL-047, PL-061 |
| 4 | Separate decision types; no vague "Allow AI" button | Every request names which of the three decisions it is (DATA_USE, IMPLEMENT_OPERATE, CASE_LEVEL_BUSINESS) and who owns it. Approvals bind to digest, case version, policy version and expiry. A valid authorization is never asked for twice. | PL-040, PL-041; spec §17 |
| 5 | Honest effort accounting | Every human-principal action on tenant resources is captured in the five categories, including failed, blocked and abandoned attempts, and the ledger is customer-visible. | PL-002, PL-003, PL-059 |
| 6 | No autonomy or coverage claim without evidence | No deployment is called autonomous without its ledger; "supervised" until PA-027-level evidence. Integrations are stated per operation at their maturity level, never as a logo wall. | PL-003, PL-007, PL-008, PL-062, PL-063, ADR-010 |
| 7 | Unknown is not absent | Every fact carries provenance, time axes and a status. Plumb never asks for an item it cannot show is missing. Corrections are scoped and reversible. | PL-009, PL-010, PL-011, ADR-005 |
| 8 | One obligation, one owner, one effect | Duplicate prevention lives at the client-period-obligation epoch, across staff, restarts and releases. An ambiguous send becomes UNKNOWN and is reconciled, never resent. | PL-037, PL-038, PL-039, ADR-009 |
| 9 | Cheapest adequate intervention | Native settings first; remove a step before automating it; never force the highest available model into every step; a cheaper model is adopted only after full-system evaluation. | PL-013, PL-031, PL-050; spec §1 |
| 10 | The customer owns the artifacts and can exit | Specs, tests, adapters, evidence, packages and the ledger are typed, digest-addressed artifacts kept outside any agent session. The right to export them in open formats and a pre-agreed exit are contract terms (D9), not spec requirements. | ADR-002, ADR-003, PL-046; D9 |
| 11 | Data rights by purpose | Grants are per source and per purpose. Read never implies train. TRAIN is off by default and opt-in per source; SERVE is granted explicitly before the first shadow; tax-return information is excluded in v1 (D9). | PL-052, PL-053, PL-054 |
| 12 | One durable lifecycle owner | Authoritative state lives in the control service's ledger and state machines, not in an agent's memory. One orchestrator owns each operation. | ADR-004, PL-016, PL-057 |

---

## 9. Product surfaces at a glance

Spec Appendix A §6 describes the goal and evidence view, the implementation card, the progress feed, the blocked-dependency view and the results view. The close-readiness ledger, review surface, approvals inbox and focused-question queue come from spec Appendix B, spec §17 and the decision record (D2, D3, D6). The goal and evidence view is folded into the implementation card and the results view. None of these surfaces exists in the package; there is no UI and no API object for any of them. Details and acceptance criteria are in [MVP scope](03-mvp-scope.md).

| Surface | One line | Basis | First phase (hypothesis) |
|---|---|---|---|
| Implementation card | Before a build: what will change, which systems and data, what actions it may take, maximum spend, the benefit hypothesis and any owner decision; proceeds without asking if the envelope already covers it | Spec App. A §6; PL-005, PL-041 | P2 M1 |
| Progress feed | Plain-language progress from build-ledger events; a step reads "verified" only after a verifier attestation, and manual engineering is shown, never hidden | Spec App. A §6 (attestation derivation proposed); PL-016 | P2 M1 |
| Blocked-dependency card | The exact missing consent, policy or input, who can resolve it and what resumes; completed work is retained | Spec App. A §6; PL-001, PL-041 | P2 M1 |
| Close-readiness ledger | Per client-period, each required item as PRESENT, CONFIRMED_ABSENT or UNKNOWN with provenance; read-only; chase history added once mail-history read is connected | Proposed (D2, D3); PL-010 | P2 M1 (read-only); P4 (chase history) |
| Review surface | One review package per client-period with evidence links and fact status; explicit accept, correct or amend; doubles as the prospective correction collector | Spec App. B (deliverable); proposed (no ReviewPackage contract exists) | P4 M3-lite |
| Approvals inbox | Batched requests labeled with decision type and owner, each with an impact diff and the test evidence | Spec §17; proposed (no approvals endpoint exists) | P2 M1 (data use, implement and operate); P6 (case-level request approvals, with Draft; package sign-off is in the review surface from P4) |
| Results-and-effort view | Eligible cases, correct outcomes, review effort, failures and cost, plus the human-effort ledger by category and EIH/VD | Spec App. A §6 and App. B; PL-003, PL-059 | P2 M1 (effort); P5 (package results) |
| Focused-question queue | Domain questions with evidence and consequences, under a per-workflow budget; answers become versioned conventions | Spec App. B; PA-004; proposed budget (D6) | P1 M0 and P2 M1 |

---

## 10. Non-goals and boundaries

These hold for at least the first 180 days. Each has a stated basis and, where one exists, the evidence that would reopen it.

| Boundary | Why | Basis | Reopened by |
|---|---|---|---|
| No posting and no FINANCIAL_COMMITMENT effect | Accountant sign-off is mandatory; posting is a separate capability, excluded unless specifically granted | Spec App. B; D3, D9 | A new envelope decision, never a silent widening |
| No "autonomous close" | A review-ready package is not an autonomous financial close | Spec §15; D8 | Not reopened |
| No screen or visual capture | Experiment 1 (richer observation) is unresolved; raw capture is about 34.6 GB/day per 100 employees | Spec §24, §27; D3 | More than 20% of obligations still UNKNOWN after two closes because of off-system handoffs, or the D11 shadowing proxy test (D3, D11) |
| No training in v1 (no training.submit, no TrainingSpec execution) | PA-012 does not need training; training rights are scarce; the trained path can lose on total cost | Spec §14; D3, D5 | All four M2 entry gates (D5) |
| No tax-return information | IRC 7216 consent obligations (secondary commentary; counsel to confirm) | D9 | A counsel opinion on monthly-close sources |
| No logo-wall integration claims | A logo is not an operation capability; the registry's PRODUCTION_VERIFIED entries are synthetic | PL-007, PL-008; D8 | Never; coverage is stated per operation |
| No cross-industry claims | The three synthetic scenarios show representational reuse, not cross-industry autonomy | Spec §25; D8 | M6 evidence on a second domain |
| No per-customer delivery engineers | Their time is ENGINEERING_INTERVENTION by definition; it is the services trap | D12 | Not reopened |
| No mailbox drafts or client sends before the gateway gates | A mailbox draft is an external write (EXTERNAL_WRITE_REVERSIBLE) that needs effect-slot dedup and the production effect ledger; a send is EXTERNAL_COMMUNICATION | D3, D4 | Draft and Send gates (section 3.6) |
| No transaction categorization, open-ended discovery, UI adapters, generic infrastructure generation, maintenance agent, multi-region or second domain | Off the PL-063 critical path, or unproven | D3, D5 | Revisit triggers in D3 and D5 |

**Never-claim checklist (D8, owned by the founder).** It applies to sales, marketing, investor and partner material derived from this brief:

1. Local tests do not validate models, business outcomes, tenant security, cloud isolation or integrations (spec §28). Never quote the spec's stale figure of 56 passing tests (section 11).
2. The three synthetic scenarios are not cross-industry autonomy (spec §25).
3. 90 days is a planning hypothesis (spec §26).
4. Product-video results are not evidence (spec §29).
5. No "autonomous close" and no posting; a package is "ready for review" until sign-off.
6. Never "fully autonomous", "zero human", "no humans needed" or "AI employee"; deployments are "supervised", with labor shown, until PA-027-level evidence.
7. "Automatically constructed" only after M1R.
8. No logo walls; registry PRODUCTION_VERIFIED entries are synthetic.
9. No hours-saved or ROI figure without a baseline and a denominator, and no causal claim from historical replay (spec §7).
10. No exact unlearning (spec §20).
11. Never claim a message was not sent after the provider accepted it (PA-014).
12. Claims match the released tier: no "fewer duplicate requests" before Send-canary evidence.

---

## 11. Where we are today

The repository holds a normative engineering spec (v0.2, October 2, 2026) and a reference package. Nothing is deployed. The [README](../README.md) and [VALIDATION_REPORT](../VALIDATION_REPORT.md) record exactly what was executed.

| Area | Spec requires | Package has (local library, tested) | Not built |
|---|---|---|---|
| Contracts and rules | Typed contracts and a registry-backed compiler (ADR-003) | 17 contracts plus 5 supporting records with generated JSON Schemas; plan, dataset, approval and release checkers | The wiring: state-machine guards do not call the checkers; the plan checker ignores the tenant EnvironmentInventory and capability required_authority |
| Capability registry | Maturity per operation, backed by probes (PL-007, PL-008) | 25 records over 23 step types ([registry](../plumb/registry/capability_registry.json)); its 15 PRODUCTION_VERIFIED entries are synthetic placeholders | Real probe receipts; a reset to truthful maturity is planned for P0 |
| External effects | Intent persisted before dispatch, UNKNOWN reconciliation, dedup across restarts and releases (PL-037, PL-038, PL-039) | A single-process SQLite effect-ledger simulation with slot dedup, payload conflicts and UNKNOWN reconciliation | The production gateway: outbox, leases, dispatch-time authority, revocation and pause checks |
| Lifecycles | Seven aggregate lifecycles with transactional transitions (spec §23, PL-057); pause that blocks new effects (PL-047) | Seven guarded state machines | The RELEASE machine allows PAUSED only from ACTIVE, so a shadow or canary release cannot be paused |
| Data rights | Purpose-bound grants (PL-053) | Per-source purpose grants in the envelope; the plan checker never infers TRAIN or EXPORT from INSPECT or COLLECT | SERVE is never enforced: no fixture envelope grants it, yet every fixture plan passes |
| API and persistence | Asynchronous, idempotent API (PL-055); isolation across every layer (PL-052) | An [OpenAPI proposal](../api/openapi.yaml) with 24 operations and no server; a PostgreSQL design that has never been executed | Control service, authentication, tenancy |
| Value loop | Inventory, connect, collect, verify, build the workflow, release, measure | None of it | Connectors, collectors, sandbox, verifier, workflow runtime, review package (ReviewPackage is named as an artifact kind but has no contract), release executor, effort capture, UI |

What the evidence does and does not show:

- **The local contract tests pass** (more than 800; current counts in [VALIDATION_REPORT](../VALIDATION_REPORT.md)). They validate the policy kernel's local behavior only, not models, outcomes, tenant security, cloud isolation or integrations (spec §28). The spec's header table and Appendix C report 56 passing tests; that figure is stale and is never quoted.
- 55 of 63 requirements have a local behavioral test. The eight without one include the requirements that carry the business case (PL-002, PL-003, PL-059, PL-062 and PL-063); the other three are PL-049, PL-051 and PL-060.
- 30 acceptance scenarios are specified in the [catalog](../acceptance/production_acceptance_catalog.yaml); none has run against production.
- The three synthetic plans ([accounting](../fixtures/plans/accounting_evidence_preparation.json), industrial RFQ, laundry) show representational reuse, not cross-industry autonomy (spec §25). Only the accounting envelope and plan are EU/EUR (eu-west-1); the RFQ fixtures are USD (us-east-1) and laundry GBP (eu-west-2). All three envelopes expire 2027-03-31. Re-templating the accounting fixtures to US/USD and refreshing or clock-pinning the envelopes are proposed for P0.
- In short, the package is a solid policy kernel; none of the value-producing loop is built. The proposal is to build M0 and M1 as greenfield services that wrap the kernel rather than rewrite it.

What comes next (proposed; windows are hypotheses and start on gate exit; full plan in the [roadmap](04-roadmap.md) and [backlog](05-backlog.md)):

| Phase | Window (hypothesis) | Customer-visible result |
|---|---|---|
| P0 Commit and instrument | Weeks 0-2 (Oct 5-18, 2026) | None yet; never-claim checklist, frozen effort rubric, truthful registry, effort ledger as first product code |
| P1 M0: contracts, probes and ledger | Weeks 2-8 (Oct 19-Nov 29, 2026) | Tenant 1 envelope and DPA; real probe receipts on its accounts |
| P2 M1: tenant 1 integration-and-collection path | Weeks 8-14 (Nov 30, 2026-Jan 10, 2027) | Read-only close-readiness ledger; implementation card, blocked-dependency card, progress feed, effort view |
| P3 M1R: reproduction on tenants 2 and 3 | Weeks 12-20 (Dec 28, 2026-Feb 21, 2027) | The same path on two more firms, with the ledger audited |
| P4 M3-lite: preparation-only review workflow, sandbox then production shadow | Weeks 14-22 (Jan 11-Mar 7, 2027) | Review packages in production shadow on tenant 1 |
| P5 Shadow results, gateway hardening and day-180 decision packet | Weeks 20-26 (Feb 22-Apr 4, 2027) | Verifier-attested packages on at least 30 client-periods in one full close, against the month-0 baseline; the day-180 packet records tenant 1's evidence to date |
| P6 M4-accounting and M5 (after day 180) | Weeks 26-36 or later (Apr-Jun 2027), earliest | Draft tier and the start of M5 (full-workflow replication on tenants 2-4); tenant 1's paid conversion expected. The earliest policy-approved Send canary close comes after two Draft closes, around July 2027 (about weeks 39-41) |

The bets this plan tests are the seven top risks in [risks and assumptions](07-risks-and-assumptions.md): R1 replication does not get cheaper; R2 hidden human labor; R3 interruption load turns the customer into the integrator; R4 generated failure handling and effect safety; R5 market squeeze and willingness to pay; R6 build time versus runway; R7 data rights and access.

---

## 12. Glossary

| Term | Meaning |
|---|---|
| Autonomy envelope | The versioned, owner-authorized delegation: goals, source scope and purposes, approved destinations and processors, allowed effect classes, spending limits, deployment environments, regions, expiry and escalation conditions. A derived task cannot widen it (PL-005). |
| Effect class | The kind of change an operation makes: READ, INTERNAL_WRITE, EXTERNAL_WRITE_REVERSIBLE, EXTERNAL_WRITE_IRREVERSIBLE, EXTERNAL_COMMUNICATION, FINANCIAL_COMMITMENT, INFRASTRUCTURE_CHANGE, DESTRUCTIVE. The envelope lists which are allowed. |
| Data purpose | What a source may be used for: INSPECT, COLLECT, TRANSFORM, EVALUATE, TRAIN, SERVE, EXPORT. Granted per source by a human; TRAIN is never inferred from read access (PL-053). |
| Verified / attestation | A step, build or release is VERIFIED only when the independent verifier records an attestation (verifier identity and version, input digest, evidence, result, timestamp, environment) after inspecting actual state (PL-042). Verification has five levels: schema validity, artifact integrity, integration behavior, business outcome, economic result (spec §18). |
| Dependency outcome | The second PL-001 outcome: work paused on a named missing authorization, business decision or capability, with its resolver and resume point, and with completed work preserved. |
| Client-period | One client's books for one accounting period, normally a month. The unit the readiness ledger, review packages and billing are organized around. |
| Obligation | Something that must exist by a deadline under an engagement, together with what establishes completion (spec §6). For example, client X's June bank statement. |
| Obligation epoch | The approved generation of an action for an obligation. The effect slot is tenant + case + obligation epoch + operation + target; a changed message body is not automatically a new authorized reminder, and a deliberate new reminder belongs to a new approved epoch (spec §16). |
| Ready for review | A package awaiting mandatory accountant sign-off. Never reported as complete or as a close (spec §15, Appendix B). |
| EIH/VD | The north star: engineering-intervention hours per verified deployment. Numerator: all ENGINEERING_INTERVENTION and OPERATIONAL_REPAIR minutes on a tenant's eligible build attempts, failed, blocked and abandoned ones included. Denominator: verifier-attested deployments for that tenant. Reported per tenant in onboarding order, with platform-investment hours shown beside it and never netted (D10). |
| Accepted review packages per month | The customer co-headline: client-periods whose attested package the accountant explicitly accepted without material correction, with zero wrong-client attribution, shown with its rate over all eligible client-periods (D10). |
| Active client-month | The pricing unit: a recurring in-scope client-period for which Plumb delivered a verifier-attested ready-for-review package. Prepare $15, Prepare + Chase $25 (hypotheses, D7). |
| Shadow / canary | Release states (PL-047). Shadow runs on live inputs and compares outputs with the accountant's actual decisions, with no external effect. Canary runs the release for real on a bounded share of cases while the previous release stays available (spec Appendix B). For a preparation-only release, accountants on a subset of client-periods use the prepared packages in their real review, still with no EXTERNAL_COMMUNICATION; for Send, effects reach at most 20% of client-periods (proposed). |
| Release tiers | Prepare (preparation-only: shadow, then canary and active, never EXTERNAL_COMMUNICATION), Draft (mailbox drafts staff send), Send (policy-approved sending, canary first). See section 3.6. |
| Certified vs generated path | PL-020's preference order for each operation: a verified existing adapter (VERIFIED_ADAPTER), then supported declarative configuration (DECLARATIVE_CONFIG), then generated code for a documented operation (GENERATED_CODE), and finally a specifically supported UI adapter (UI_ADAPTER). "Certified" means reused, contract-tested transport; "generated" means produced by the agent for this tenant and contract-tested in a sandbox. |
| Capability maturity ladder | DISCOVERED, DOCUMENTED, SANDBOX_TESTED, PRODUCTION_VERIFIED, recorded per account and exact operation (PL-008). A vendor page saying an API exists does not establish that this customer's account can use it. |
| Human-effort categories | CUSTOMER_AUTHORIZATION, DOMAIN_CLARIFICATION, NORMAL_BUSINESS_REVIEW, ENGINEERING_INTERVENTION, OPERATIONAL_REPAIR (PL-003; rubric in section 3.4). |

---

## Sources

Market facts come from the doc set's research notes, which were checked against search results dated before October 4, 2026. Vendor-run surveys and vendor claims are flagged; "secondary" means the figure was confirmed through coverage rather than the original page.

- [M1] US Census Bureau, AI use in businesses (BTOS), May 26, 2026: https://census.gov/library/stories/2026/05/ai-use-businesses.html. The AI question was revised in November 2025, so earlier rates are not comparable.
- [M2] Goldman Sachs 10,000 Small Businesses survey, March 17, 2026: https://www.goldmansachs.com/pressroom/press-releases/2026/small-businesses-embrace-ai-but-need-training-and-support-to-fully-harness-it. Page returned 403 to the researcher; figures confirmed via CPA Practice Advisor and Fortune (secondary).
- [M3] Financial Cents, State of AI in Accounting and Bookkeeping 2026, n=486, August 2026: https://financial-cents.com/?p=39931. Vendor-run survey.
- [M4] Ramp and CalCPA, Benchmarking the Modern CPA Firm 2026: https://ramp.com/reports/benchmarking-the-modern-cpa-firm-2026-or-calcpa-and-ramp. Vendor and association survey; California only.
- [M5] Financial Cents, State of Accounting Workflow Automation 2025, n=816, April 2025: https://financial-cents.com/?p=9086. Vendor-run; the report ranks the finding #1 without a percentage.
- [M6] AICPA PCPS CPA Firm Top Issues Survey, June 23, 2026, via CPA Practice Advisor: https://www.cpapracticeadvisor.com/?p=185547 (secondary).
- [M7] Intuit QuickBooks 2026 Accountant Technology Survey, n=725, via CPA Practice Advisor, July 2, 2026: https://www.cpapracticeadvisor.com/2026/07/02/the-2026-accountant-technology-survey-turning-data-revelations-into-a-firm-of-the-future/185807/. Vendor-run survey (secondary).
- [M8] Uku, AI in Accounting 2026, fielded May-June 2026: https://getuku.com/ai-in-accounting-report/. Small, self-selected sample; directional.
- [M9] US Census Bureau, Statistics of U.S. Businesses 2022 (NAICS 541211 and 541219), released April 10, 2025: https://www2.census.gov/programs-surveys/susb/tables/2022/us_state_6digitnaics_2022.xlsx. Employer firms only.
- [M10] Accounting Seed, The State of AI in Accounting 2026, n=128 finance professionals: https://www.accountingseed.com/resources/the-state-of-ai-in-accounting-2026. Vendor-run survey.
- [M11] Capgemini Research Institute, AI agents research (around July 2025): https://www.capgemini.com/insights/research-library/ai-agents/. Publication date not stated on the page.
- [M12] Agent-built integrations: Nango Management MCP guide, September 4, 2026, https://nango.dev/blog/how-to-build-ai-agent-integrations-using-the-nango-management-mcp; Membrane launch, https://getmembrane.com/articles/all/announcing-membrane-the-era-of-self-integrations; Make Maia, https://www.make.com/en/blog/maia-conversational-ai-coworker-for-ai-agents-and-automation. Vendor claims.
- [M13] superglue self-description as "an agentic implementation platform": https://superglue.ai/. Vendor claim.
- [M14] Practice-management pricing: Karbon https://karbonhq.com/pricing/; Financial Cents https://financial-cents.com/pricing/. TaxDome pricing is from secondary listings and is not quoted here.
- [M15] Ledger-native tools: Xero, August 20, 2026, https://itbrief.co.uk/story/xero-expands-ai-tools-for-accountants-small-firms; Intuit Accountant Suite launch, https://www.cpapracticeadvisor.com/?p=171765 (free introductory pricing comes from a secondary source); Double pricing model, https://doublehq.com/pricing (the $10/$25/$50 tier prices are from secondary listings, not the vendor page).
- [M16] Zapier pricing, as fetched October 2026: https://zapier.com/pricing.
- [M17] OpenAI deprecations, Agent Builder shutdown on November 30, 2026: https://developers.openai.com/api/docs/deprecations.
- [M18] OpenAI consulting minimum (reported), https://the-decoder.com/openai-is-charging-at-least-10-million-per-client-for-its-enterprise-ai-consulting-services/; SMB agency build costs (vendor-written guide, low reliability), https://www.layer3labs.io/ai-consulting-for-small-business; Informa 2026 MSP 501, September 29, 2026, https://www.channelinsider.com/ai/msp-ai-revenue-growth-2026/.
- [M19] Gartner prediction on vendor FDE-built agentic AI, September 29-30, 2026: https://www.gartner.com/en/newsroom/press-releases/2026-09-29-gartner-predicts-70-percent-of-enterprises-will-abandon-agentic-ai-built-by-vendor-forward-deployed-engineering-by-2028. Page returned 403; details via https://techstrong.ai/articles/gartner-warns-70-of-vendor-built-ai-agent-projects-face-abandonment-by-2028/ (secondary).
