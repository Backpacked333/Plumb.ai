# Design-Partner Program

- Status: Draft v0.1 (2026-10-04), proposed — requires founder ratification
- Owner: Product
- Basis: spec v0.2, [decision record](02-strategy-decisions.md)

Part of the product doc set ([index](README.md)). This document turns D9 (design-partner program and contract essentials) into an operating plan. It draws on D1 (ICP), D5 (sequencing and tax season), D6 (interruption budget and effort rubric), D7 (pilot terms) and D8 (never-claim checklist) in the [decision record](02-strategy-decisions.md), and applies the head of product's founder decisions 17 (Prepare-tier promotion and paid conversion) and 18 (effort-rubric amendment), both to ratify. Phases and gates are in the [roadmap](04-roadmap.md). The partner journey and product surfaces are in [MVP scope](03-mvp-scope.md), metric definitions in [metrics](06-metrics.md), kill criteria in [risks and assumptions](07-risks-and-assumptions.md), and competitive context in [market and positioning](08-market-and-positioning.md).

**How to read this document.**

| Label | Meaning |
|---|---|
| Spec | Required by [spec v0.2](../spec/Plumb_Autonomous_Implementation_Specification_v0.2.md) or the [acceptance catalog](../acceptance/production_acceptance_catalog.yaml). |
| Package | Present in the reference package today. It is a local library: nothing is deployed, connected to a customer or measured. |
| Proposed | This document's proposal, built on the decision record. Not yet ratified. |

**Nothing in this program has happened yet.** The repository records no partner conversation, LOI, signature, tenant, probe, time study or review package. Every count, date, price and threshold below is a hypothesis unless the spec states it. Each table says so once rather than on every line. Thresholds go into threshold sheet v1, which is ratified at M0 (P1).

**Program owner:** the founder. Design-partner sales is on the critical path (D12). A design-partner success lead is hired around week 12 only if the founder cannot cover partner operations. That person's minutes are logged, and they never wire integrations; if they do, it is ENGINEERING_INTERVENTION (D12).

---

## 1. Goals of the program

The program has four primary goals. Windows are hypotheses from the phased plan.

| # | Goal | What would settle it | Tenants | Phase | Basis |
|---|---|---|---|---|---|
| G1 | Prove PL-063 on three firms | **M1 on tenant 1:** PA-001 attested with an agent-generated mapping, the M1 safety bundle, and zero ENGINEERING_INTERVENTION in the attested run, with every failed attempt counted. **M1R on tenants 2 and 3:** PA-001 re-attested per tenant on the same engine with no fork; at least one operation on a non-VERIFIED_ADAPTER path (PA-P01); EIH/VD falling at each tenant, with tenant 3 at or below 50% of tenant 1; an audit that finds zero unrecorded manual work. | 1, 2, 3 | P2 (weeks 8-14), P3 (weeks 12-20) | PL-063 (spec §26 L404); PA-001; D4 |
| G2 | Prove M5 on the next three customers | Full PA-027 on tenants 2, 3 and 4, with at least one month of prospective measurement each: lower engineering intervention than tenant 1, a stable correct-package rate, and failed and blocked attempts in the denominator. | 2, 3, 4 | P6 (from week 26 at the earliest; the Apr-Jun 2027 window covers only the start of M5) | Spec §26 M5 row (L413); spec App. B L654 ("the next three customers"); PA-027 |
| G3 | Test willingness to pay | Paid pilots invoiced at signature, starting with tenant 1. At least 2 of the first 4 partners convert to paid annual contracts at $15 or more per active client-month; fewer than 2 fires the R5 trigger, and 3 of 5 is a target, never a kill. The price test covers $15, $25 and $35 plus a per-accepted-package unit, run with tenants 4-5 and new prospects. | 1 to 5 | Pilots from P1; tenant 1's evidence to date in the day-180 packet (P5); conversions from P6 (founder decision 17) | D7; R5 |
| G4 | Build the domain acceptance corpus | A protected evaluation corpus, segregated from tuning and repair examples and owned by the Plumb domain expert. It is built from accountant adjudications, the 100-pair attribution reviews and explicit accept, correct and amend decisions. The correct-package threshold is set against it at the P4 exit, and PA-027's "stable quality" is judged on it. | 1 to 5 | P2 onward | Spec §26 L416 (named owner for the domain acceptance corpus); PL-044 |

**Secondary reads.** These need no partner asks beyond those in section 8.

- Experiments 3 and 6 (spec §27): adapter-adaptation cost and maintainable reuse, read through EIH/VD, the hands-off build rate and artifact reuse by digest.
- Experiment 4: domain clarification per workflow, read from the focused-question queue against the budget.
- Experiment 1 proxy (D11): in two firms during tenant 2-3 onboarding, discovery from APIs and history alone is compared with the same plus a 2-hour structured shadowing session.
- The D1 mixed-stack thesis: the share of qualified prospects with materially mixed stacks, and whether they show more pain or willingness to pay (section 3).
- Month-0 baselines (section 9). Without them no time claim can be falsified.

**The corpus and data rights (proposed).** Contract term 2 (section 7) forbids cross-tenant use of a partner's examples, labels and weights (spec App. A.5 L570). The corpus therefore has two layers:

1. **Per-tenant protected sets.** Adjudicated client-periods from one firm, used only to evaluate that firm's releases under its EVALUATE grant, and kept apart from tuning and repair examples (PL-044).
2. **A shared domain corpus.** Cases the Plumb domain expert writes from recurring patterns, such as a statement spanning a period boundary or a document misfiled under the wrong client. These cases contain no customer data. Term 2 permits reuse of derived artifacts such as failure fixtures once they are stripped of customer data.

Using one firm's real examples to evaluate another firm's release would need a separate, opt-in permitted-use grant. Counsel to confirm.

**What the program is not.**

- It is not a services engagement. There are no per-customer delivery engineers (D12), and Plumb never bills hours (D7); its engineering stays a measured cost (ADR-010).
- It is not early access to a finished product. The readiness ledger, review surface and reports are still to be built ([backlog](05-backlog.md) epics E11, E13 and E14).
- No human-engineered deliverable is produced on partner data before the M1 isolation subset (PA-P14) and PA-019 pass (founder decision 13). Value before M1 is the month-0 baseline.
- There are no messages to the firm's clients, no posting and no training during the pilot. Only the Prepare tier runs before day 180.

---

## 2. Cohort design

### 2.1 Slots

Commitment dates and windows are hypotheses.

| Slot | Evidentiary role | Commitment target | Build window |
|---|---|---|---|
| Tenant 1 | M0 and M1. First-customer baseline for EIH/VD, first shadow close, and the first measurable deliverable (attested packages on at least 30 client-periods) | Signed paid pilot by about week 4 (early November 2026) | M0 weeks 2-8; M1 weeks 8-14; M3-lite weeks 14-22; shadow weeks 20-26 |
| Tenants 2 and 3 | M1R with controlled variation, then part of the M5 cohort | LOI by week 8 (Nov 29, 2026). Proposed: signed paid pilot before M1 attestation. Grants, domain clarifications and baseline studies collected before mid-January 2027 (D5). | M1R weeks 12-20, starting on M1 attestation. Shadow starts in P5 as their workflows activate; full-close readings may land after day 180 and are reported as pending. |
| Tenant 4 | Completes the "next three customers" for M5 | LOI by week 8. Proposed: signed before P5 starts (week 20). | Onboarding from P5 (weeks 20-26); build and M5 measurement in P6 |
| Tenant 5 | Reserve; the second-tenant peer for PA-017 (D9); price-test participant (D7) | LOI before M1 completes (about week 14) | Only when a slot opens or capacity allows. The full PA-017 run comes before any training job, in P6 only if a training adapter exists ([roadmap](04-roadmap.md) section 5). The PA-017 subsets (PA-P14, PA-P15) run earlier, with tenants 1-3 co-resident. |
| Optional roll-up slot (tenant 5 or a sixth slot; founder decision 16) | Channel probe with a PE- or VC-backed roll-up. Off the critical path; promoted to primary channel only if R5 fires. | Any time | Proposed: no build before M1R passes. Never counted as one of the "next three customers". |

**Capacity rules.**

- At most 3 active builds until M1R passes (D5, D9).
  - Proposed definition: an active build is a tenant whose build has started and is not yet VERIFIED, FAILED or CANCELLED.
  - Customer-side onboarding for later tenants (contract, grants, baseline) may proceed while three builds are active. Only build work waits.
- If the team cannot support 3 concurrent builds, cap at 2 (D5 revisit trigger).
- If tenant 2's onboarding takes more than 50% of engineering capacity for more than 3 weeks: pause tenant 3, find the root cause by failure class, and hold tenants 4-5 until engineering minutes per verified path fall (D9).
- If recruiting is easy and labor per firm falls fast, open a second cohort of 5 in Q2 2027 (D9).

### 2.2 Stack-variation matrix

The target profile is proposed. Providers are the D1 candidate families; the actual firm decides each cell. Practice-management (PM) tools are optional, read-only and not on the M1 or M1R path.

| Tenant | Ledger | Mail and docs suite | Document store | PM tool | Deliberate variation | Purpose |
|---|---|---|---|---|---|---|
| 1 | QBO and Xero clients (a mixed book, mostly QBO) | Google Workspace | Google Drive | None needed | The reference stack. The mixed book meets D1's "at least one cohort firm has both QBO and Xero clients" from the start. | M0 and M1; EIH/VD baseline; first shadow close. Runway rule: if PA-001 has not passed by week 14, cut to one ledger and one document store, and record the cut. |
| 2 | QBO and/or Xero (families already in tenant 1's stack) | Google Workspace | Google Drive | Karbon or Financial Cents, if used | Same provider families as tenant 1. Different folder structure and chart-of-accounts conventions (the PA-027 preconditions), plus a minor ledger API version difference if one exists. | M1R: tests agent-generated semantic mapping on reused certified transport. Gives the earliest R1 signal (tenant 2 against tenant 1). |
| 3 | As tenant 1 | Microsoft 365 | SharePoint/OneDrive | Any or none | One provider swap on the M1R path: the document store. It is chosen at M0 so that the integration factory has no verified adapter for its `list_folder_changes` and `fetch_document` operations, which forces a DECLARATIVE_CONFIG or GENERATED_CODE path (PA-P01). The mail difference only matters from M3-lite. | M1R: the first non-VERIFIED_ADAPTER path, with PA-026 and PA-019 re-run on it. Target: tenant 3 EIH/VD at or below 50% of tenant 1. |
| 4 | Families already exercised by tenants 1-3 | Google Workspace or Microsoft 365 | Drive or SharePoint/OneDrive | Any or none | No new provider family. New folder structure and chart-of-accounts conventions and, ideally, a minor ledger API difference (the PA-027 preconditions). | Completes the next three customers for M5. The cleanest PA-027 reading, because it is the first tenant expected to need no new primitive. Also a price-test participant. |
| 5 (reserve) | Families already exercised | Either | A store already exercised | Any | Chosen so it can back-fill tenant 2, 3 or 4 without changing that slot's variation | Reserve; PA-017 peer; price test |
| Roll-up (optional) | Varies across member firms | Mixed | Mixed | Mixed | Several stacks under one buyer | Channel probe (R5). Reported in onboarding order and flagged "off-matrix"; never excluded from EIH/VD reporting. |

**Substitution and locking rules (proposed).**

1. Provider capability is confirmed by M0 probes, never by vendor pages (PL-007, PL-008). Every cell must meet the catalog's assumptions: document-store webhooks plus overlap polling (PA-005), mail request-id lookup (PA-009) and provider sandboxes (PA-002).
   - A cell whose provider is known to fail them is re-cut before signature.
   - A failure first found at M0 becomes a recorded blocked attempt.
2. If no mixed-book firm is available as tenant 1 by week 4:
   - Tenant 1 is QBO-only, and tenant 2 follows it.
   - The mixed book moves to tenant 4.
   - Xero transport work is then booked as platform investment ahead of tenant 4, and named in tenant 4's PA-027 root-cause reading.
3. Tenant 3's swapped store may be Dropbox or SmartVault instead of SharePoint/OneDrive. What matters is that exactly one provider on the M1R path differs and has no verified adapter (so no VERIFIED_ADAPTER path is available).
4. Onboarding order and matrix slot lock when each envelope is signed. A decline produced by swapping a hard tenant for an easier one counts as an R1 fail (D11 reading rules).
5. A single-ecosystem firm whose native chase-and-match already works is normally a qualify-out. It can still take a slot if it wants Plumb to configure and verify those native features (the D1 exception) and its stack fits a cell. Every tenant gets a native-feature baseline anyway (PL-013).

**Why this design.**

- **The spec names the variation.** Appendix B's expansion test is "the same process on the next three customers: different folder structures, chart-of-account conventions and minor API differences, with the same core engine" (spec App. B L654), and PA-027's preconditions use the same three. D3 adds the provider swap, so a generated path runs before anyone says "automatically constructed" (D8 item 7).
- **Tenant 4 adds no provider family.** M5 should then read replication, not new-provider construction. New-provider work is measured separately as platform investment (D10).

---

## 3. Funnel targets

Targets and dates are hypotheses.

| Stage | Definition (proposed) | Target | By | Basis |
|---|---|---|---|---|
| ICP firms contacted | Firms that match the D1 profile on public information and are reached by outreach | At least 200 contacts across the message test | Week 8 (proposed) | D8 revisit trigger (message test across at least 200 ICP firm contacts) |
| Qualified conversations | A first call with the buyer or domain owner at a firm that clears every disqualifier and the sales-stage must-haves on known facts (section 4) | At least 8, then at least 25 | Week 2 (Oct 18, P0 exit), then week 8 (Nov 29) | P0 exit evidence; D9 |
| Tenant 1 signed | Pilot agreement and DPA signed; pilot fee invoiced | 1 | About week 4 (early November) | D9; P1 exit evidence |
| LOIs from tenants 2-4 | A signed LOI that names the slot, domain owner, reviewing accountant, baseline window and fee band | 3 | Week 8 | D9; P1 exit evidence ("at least 3 more LOIs") |
| Tenant 5 LOI | As above | 1 | Before M1 completes (about week 14) | D9 ("LOIs in hand before M1 completes") |
| Tenants 2 and 3 signed | LOI converted and fee invoiced; customer-side inputs complete before mid-January | 2 | Before M1 attestation (proposed) | D5, D9 |
| Tenant 4 signed | As above | 1 | Before week 20 (proposed) | P5 begins tenant 4 onboarding |

**Implied arithmetic (not a forecast).** Four committed firms (tenant 1 signed plus three LOIs) from 25 qualified conversations is a 16% rate from qualified conversation to commitment.

**What counts as a materially mixed stack (proposed working definition, recorded per call).** The client book spans both QBO and Xero, or close evidence for a typical client lives in at least three systems (ledger, mail, and a separate document store or portal).

**Pre-registered funnel triggers.**

| Trigger | When read | Response | Source |
|---|---|---|---|
| In the first 25 qualified calls, fewer than 30% of firms have materially mixed stacks, or mixed-stack firms show no more pain or willingness to pay than single-ledger firms | Week 8 | Narrow to QBO-centric firms whose evidence lives in email and drives | D1 |
| 60% or more of qualified prospects are single-ecosystem with chase-and-match covered | Week 8 | Re-open the vertical | D1 |
| Fewer than 4 LOIs on any terms | Week 10 (Dec 13) | Shift to the roll-up channel or re-open the vertical | D1 |
| Fewer than 2 paid pilot LOIs after about 30 qualified conversations | When reached | Offer a free pilot with a pre-committed conversion price and a measurable gate. Do not lower qualification. | D7, D9 |
| At least 3 of 5 qualified prospects choose native tools after a PL-013 comparison, or 50% or more of qualified mixed-stack prospects pick an incumbent head to head | Rolling | Apply the R5 response: pivot to the roll-up/MSP channel or per-package pricing, and re-examine the ICP before cutting price | R5 |
| Outcome-led framing gets more than 2x the qualified-meeting rate of verification-led framing among mixed-stack firms | After at least 200 contacts | Lead with the outcome and keep verification and the ledger as proof points. The never-claim checklist is not relaxed. | D8 |

**Pool and channels.** Census SUSB 2022 counts 2,015 CPA firms and 1,247 "other accounting" firms with 20-99 employees, plus about 13,400 CPA firms with 5-19 employees [M1]. These size bands do not match the 10-40-staff profile, so they bound outreach lists rather than size the ICP; the counts cover employer firms only, and NAICS 541219 includes non-bookkeeping firms. For firms with 11-30 professionals, hiring experienced staff is the #1 issue and managing workload and capacity is #3 (AICPA PCPS survey, secondary coverage) [M2].

Proposed channels are the founder's network and direct outreach. The market notes name the Karbon and Uku MCP servers and the Xero App Store as integration and distribution surfaces; their value as recruiting channels is untested.

For the roll-up slot: about 180 PE deals were made in accounting in 2025 (secondary source, partly paywalled) [M11], and some roll-ups build their own tools, for example Crete (since renamed Current), backed by Thrive (Reuters via syndication) [M12].

---

## 4. Qualification scorecard

Criteria come from D1 and D9. Weights and cut-offs are hypotheses.

### 4.1 Disqualifiers

Any one of these ends qualification.

| # | Disqualifier | Source |
|---|---|---|
| X1 | Solo or 2-4-person firm | D1 |
| X2 | Top-100 firm, or 100 or more staff (where Basis and FloQast compete) | D1 |
| X3 | Tax-only or seasonal practice, or in-scope sources hold tax-return information that cannot be excluded by folder or label (IRC 7216) | D1, D9 |
| X4 | Standardized on one ecosystem whose native chase-and-match already works (Xero Partner Hub/JAX/XeroForce, Intuit Accountant Suite, Double on one ledger), unless the firm wants Plumb to configure and verify those native features | D1 |
| X5 | Desktop or on-prem ledger, or NetSuite/Intacct | D1 |
| X6 | Evidence held in closed portals that cannot be probed | D1; PL-007, PL-008 |
| X7 | Document store known to lack webhooks plus overlap polling, or mail provider known to lack request-id lookup | D1; PA-005, PA-009 |
| X8 | Expects posting or an "autonomous close" | D1; spec §15 L248 |
| X9 | Will not grant read OAuth, name a domain owner with about 2 hours a week, run a 2-week baseline time study, or allow anonymized publication of labor-ledger data | D1 |
| X10 | Needs on-prem deployment or multiple regions | D1 |
| X11 | Wants hand-built bespoke work or hourly billing rather than the product (proposed; the services trap) | D7, D12; ADR-010 |
| X12 | Employs, or is affiliated with, Plumb's domain expert (proposed; conflict of interest) | D12 (the domain expert is not drawn from a design-partner firm) |

### 4.2 Must-haves

All are required. Sales-stage items (MH) are checked on the call and in the LOI. Provisional items (MP) can only be confirmed by M0 probes on the firm's real accounts. The labels are local to this document and are not milestones or phases.

| # | Must-have | Stage | Source |
|---|---|---|---|
| MH1 | Independent US accounting firm with 10-40 staff | Sales | D1 |
| MH2 | At least 60% of revenue from recurring bookkeeping/CAS | Sales | D1 |
| MH3 | At least 50 recurring monthly-close clients with 12-24 months of history | Sales | D1, D9 |
| MH4 | QBO and/or Xero client ledgers; Google Workspace or Microsoft 365 mail; a document store separate from the ledger (Drive, SharePoint/OneDrive, Dropbox or SmartVault) | Sales | D1 |
| MH5 | A named domain owner with about 2 hours a week and the authority to grant OAuth. This is the Firm owner or a CAS director the Firm owner names. | Sales | D1, D9 |
| MH6 | A named reviewing accountant | Sales | D9 |
| MH7 | Agrees to the 2-week baseline time study | Sales | D1, D9 |
| MH8 | Pays the pilot fee, invoiced at signature | Sales | D7, D9 |
| MH9 | Consents to publication of anonymized labor-ledger metrics, failures included | Sales | D1, D9 |
| MH10 | Accepts dependency and failure outcomes as normal outcomes | Sales | D9; PL-001 |
| MH11 | Agrees to a 100-pair attribution or label review | Sales | D9 |
| MH12 | Accepts the data terms: TRAIN off by default, tax-return information excluded, US region, mandatory accountant sign-off, no posting | Sales | D9 |
| MH13 | Fits an open slot in the stack-variation matrix | Sales | D9 |
| MH14 | Willing to be a reference (per call, with notice; section 13.1) | Sales | D9 |
| MP1 | Document store supports webhooks plus overlap polling | M0 probe | PA-005 |
| MP2 | Mail supports lookup by provider request id | M0 probe | PA-009 |
| MP3 | Provider sandboxes are available | M0 probe | PA-002 |
| MP4 | The exact operations can be probed on the firm's accounts | M0 probe | PL-007, PL-008; D9 |

### 4.3 Weighted criteria

Each criterion scores 0 (absent), 1 (partial or unclear) or 2 (clear evidence from past behavior).

| # | Criterion | Weight | Why | Source |
|---|---|---|---|---|
| W1 | Materially mixed stack (section 3 definition) | 3 | Tests the D1 thesis that mixed stacks are where single-ecosystem incumbents are weakest | D1 |
| W2 | Capacity pain shown by past behavior: unfilled roles, turned-away clients, overtime at close | 3 | The buying signal for a capacity product | D1; [M2] |
| W3 | Evidence assembly or chasing named, unprompted, as a top pain, with an example from a recent close | 3 | The wedge (D2) | D2; [M3] |
| W4 | Calendar fit for the slot. Tenants 2-3: grants and baseline possible before mid-January. Tenant 4: baseline possible after April 15. | 2 | Tax season slows customer-side inputs | D5 |
| W5 | Willing to be named in a case study under section 13, beyond the reference willingness MH14 requires | 2 | Reference value | D9 |
| W6 | Documented engagement checklists per client type | 2 | Lowers domain clarification (R3) | R3 |
| W7 | Will grant mailbox read scopes at P4 | 2 | Needed for the duplicate-chase baseline; refusals at 2 of 5 partners fire R7 | R7 |
| W8 | Decision speed: the signer is known and can sign within 4 weeks of the first call | 2 | Tenant 1 by week 4 | D9 |
| W9 | 24 months of history rather than 12 | 1 | Backfill depth | D1, D5 |
| W10 | Chasing happens by email Plumb could read, not only by phone or portal | 1 | Coverage of the historical baseline | D2 |
| W11 | Open to discussing an opt-in TRAIN grant later. Never a condition, and never traded for price. | 1 | The M2 gate needs TRAIN on at least 2 tenants | D5, D7 |

### 4.4 Scoring and decisions (proposed)

- The score is the sum of weight times score. The maximum is 44.
- 26 or more: invite to an LOI if a matching slot is open.
- 18-25: hold as reserve or nurture.
- Below 18: decline politely.
- Ties go to matrix fit, then calendar fit, then W1.
- The founder scores within 24 hours of the call and records evidence (a quote or fact) for each criterion. The Plumb domain expert reviews the score before any LOI.
- The first 25 qualified scorecards feed the D1 triggers in section 3.
- Case-study willingness (W5) and TRAIN openness (W11) never change the price (D7).

---

## 5. What partners give and get

**Partners give.** Amounts are hypotheses. Effort categories follow the D6 rubric as amended by the head of product (founder decision 18, to ratify): every minute of partner time lands in one of the five categories.

| What | Who at the firm | Amount | Effort category | Source |
|---|---|---|---|---|
| Grants and access: OAuth on ledger and document store; mail history in P4; SERVE before the first shadow | Firm owner or account admin | At most 2 hours of CUSTOMER_AUTHORIZATION during onboarding | CUSTOMER_AUTHORIZATION | D6, D9 |
| Domain-owner time | Domain owner | At most 5 questions per workflow at onboarding and at most 4 owner-hours in the first 30 days. Steady state: at most 1 batched request and 30 minutes of decision time a week. | DOMAIN_CLARIFICATION, CUSTOMER_AUTHORIZATION | D6 |
| Month-0 baseline | Reviewing accountant, bookkeepers | Two consecutive weeks of time diaries on at least 30 client-periods (section 9) | DOMAIN_CLARIFICATION (recording overhead only, section 9.7) | D2, D9 |
| 100-pair attribution or label review | Reviewing accountant | One sample of 100 pairs, about 2 hours | DOMAIN_CLARIFICATION | D6, D9 |
| Package review and sign-off in shadow | Reviewing accountant | Every cohort package, batched into at most one session a day | NORMAL_BUSINESS_REVIEW | D2, D6 |
| Feedback and a weekly check-in | Domain owner | 20 minutes a week | DOMAIN_CLARIFICATION, scheduled: reported beside the interruption budget, not inside it (section 8.4) | D9; D6 as amended |
| Pilot fee | Firm owner | $1,500-$3,000 by firm size | Not effort | D7 |
| Rights: anonymized labor-ledger publication (failures included), case-study rights, willingness to be a reference | Firm owner | Contract terms; section 13 | Not effort | D9 |
| Acceptance of dependency and failure outcomes as normal | Firm owner | Contract term | Not effort | D9; PL-001 |
| Experiment-1 shadowing session (tenants 2-3 only) | One staff member | 2 hours, once | DOMAIN_CLARIFICATION (proposed) | D11 |

**Partners get.** Nothing in this table exists today; each item arrives only when its gate passes.

| What | When (hypothesis) | Condition | Source |
|---|---|---|---|
| Implementation with no fee. Plumb absorbs all adaptation engineering and never bills hours; that engineering is measured, not billed (ADR-010). | From signature | Supported environments | D7, D9 |
| A month-0 baseline report of the firm's own assembly and review minutes | After the time study, before shadow | None | D2 |
| A read-only close-readiness ledger: each required item PRESENT, CONFIRMED_ABSENT or UNKNOWN, with provenance | From the M1 moment (tenant 1: about week 14) | Planned for P2 ([backlog](05-backlog.md) E11-S04) | D2; PL-010 |
| A historical duplicate-chase baseline, labeled historical and non-causal | After mail history is connected in P4 | Mailbox scopes granted | D2; spec §7 L136 |
| Verifier-attested ready-for-review packages and "what Plumb would have done" reports | From production shadow (tenant 1: about weeks 20-26) | P4 exit gates pass | D2 |
| A per-close partner report, and the firm's own labor ledger with Plumb's minutes included | Ledger visible from onboarding; report every close from shadow | None | D9, D10 |
| Year-one credit for the pilot fee, and a 24-month price lock at $15 Prepare | At conversion (expected from P6) | Graduation rule (section 12.1) | D7 |
| Founder access and roadmap influence | Throughout | None | D9 |
| Ownership and export of every artifact and test; a pre-agreed exit | Any time | None | D9 |

**What partners do not get.**

- Messages to their clients, posting, or any other accounting write to a ledger. The pilot runs in the Prepare tier, whose only external writes are connector setup and enabling incremental capture on the firm's own accounts (EXTERNAL_WRITE_REVERSIBLE). Draft and Send are gated: Draft starts no earlier than P6, and the earliest policy-approved Send canary close is around July 2027 (about weeks 39-41).
- Training on their data. TRAIN is off by default, M2 is gated, and there is no discount for training rights (D7).
- Hand-built deliverables on their data before PA-P14 and PA-019 pass.
- Security commitments beyond gates actually passed (contract term 8).
- A deployment described as "autonomous". It is labeled "supervised", with labor shown, until that path has PA-027-level evidence (D8).

---

## 6. Pilot commercial terms

The terms are D7 unless marked proposed. All prices are hypotheses.

| Term | Content |
|---|---|
| Pilot fee | $1,500-$3,000 by firm size, invoiced at signature so willingness to pay is tested from day one. Proposed bands: 10-19 staff $1,500; 20-29 staff $2,250; 30-40 staff $3,000. |
| Credit | Credited to year one on conversion |
| Refund | Only if Plumb misses the M0-agreed gate for Plumb-side reasons (section 6.1) |
| Pilot clock | 90 days, starting at the first attested collection path (that tenant's PA-001 attestation), because packages cannot exist before then. Tenant 1: about Jan 10 to Apr 10, 2027. The clock bounds the gate sheet (section 6.1), not the pilot: conversion needs a full ACTIVE close, which on the planned calendar comes after the clock ends, so the pilot terms continue at no further fee until conversion or exit (proposed). |
| Conversion | Annual at $15 Prepare per active client-month with a 24-month price lock, once the workflow has been ACTIVE through one full close at or above the correct-package threshold. The path to ACTIVE is SHADOW, then CANARY, then ACTIVE, with no EXTERNAL_COMMUNICATION (founder decision 17, to ratify; section 12.1). Tenant 1's conversion is expected in P6. |
| Annual terms | Firm minimum $500 a month; annual contract; no per-seat price; no implementation fee for supported environments. Prepare + Chase at $25 is offered only once Send ships. |
| Exit | Pre-agreed whether or not the gate is met (section 7, term 10) |
| Fallback | If there are fewer than 2 paid pilot LOIs after about 30 qualified conversations, offer a free pilot with a pre-committed conversion price and a measurable gate rather than lowering qualification |

### 6.1 The M0-agreed gate (proposed)

A one-page gate sheet is signed at each tenant's M0 exit.

| Field | Content |
|---|---|
| Gate A: collection path | PA-001 attested on this tenant with the M1 safety bundle (tenant 1) or the M1R conditions (tenants 2-3), by a date set at M0 |
| Gate B: first measurable deliverable | Verifier-attested ready-for-review packages on at least 30 cohort client-periods in one full shadow close. The correct-package rate is reported against the domain expert's threshold, within the 90-day clock. |
| Cohort | The agreed client-periods, the same cohort as the baseline (section 9.3) |
| Dependency accounting | Days in dependency, split by resolver (customer, vendor, Plumb), from the proposed build ledger's DependencyRecords. Gap: the `DependencyRecord` contract has no `resolved_at`, and its `resolver_role` cannot express a vendor ([metrics](06-metrics.md) §9.4). |
| Plumb-side miss | A gate missed where the cause is a Plumb-resolved dependency, Plumb-caused DEGRADED collection, a terminal failure, or package quality below the threshold |
| Not a Plumb-side miss | Days in customer-side dependencies. Proposed: vendor app-review or outage days extend the gate date day for day. |

**Refund rule (proposed).** The full pilot fee is refunded on a Plumb-side miss of Gate A or Gate B. It is also refunded if a provisional must-have (MP1-MP4 in section 4.2) fails at M0 probes, because qualification was Plumb's responsibility.

### 6.2 Billing after conversion (D7)

- Bill only client-months with an attested package (PL-001).
- Credit any package the accountant rejects as materially wrong.
- Credit client-months in which a Plumb-caused DEGRADED collector covered more than 20% of the period.
- Customer-side dependencies are not billed while open, though the firm minimum still applies. A client blocked for 2 cycles drops off the billable roster until resolved.
- Plumb-side blocks, vendor outages and terminal failures are never billed. The results view shows what was attempted and why it stopped.
- Native-setting outcomes (PL-013) bill at the same rate, so Plumb is never paid more for building more.

### 6.3 Price guardrail and price test (D7)

- **Guardrail.** Price at no more than one-third of measured value per client-month, taken from the results view. If measured value does not support $15, lower the price or exit the segment.
- **Measured value.** It comes from the partner's own baseline (section 9). The research found no reputable primary source for hours per client-month spent on close or chasing, so no ROI arithmetic is used in sales.
- **Price test.** Three list points ($15, $25, $35) and a per-accepted-package unit, run with tenants 4-5 and new prospects in P5.

**Market context (from the research notes).**

- Double prices per connected client. Its vendor page confirms the per-client model and a $200/month annual-commitment tier; tier prices of $10/$25/$50 per client-month come from secondary listings [M13].
- The Financial Cents Month-End Close add-on is $5 per client per month, from the vendor page [M13].
- Xenett is about $7.5 (AI Review) to $10 (Workflow) per client per month, with a $15 accruals-and-AI add-on, from vendor pages [M13].
- Average firm technology spend is about $21,000 a year (Intuit vendor survey) [M5].
- Only 6% of firms cite cost as their top AI barrier, against 41% for time to learn and implement (Financial Cents 2026 vendor survey) [M7].

---

## 7. Contract essentials

A counsel opinion comes before the first signature (D9). Fractional counsel is engaged for weeks 0-8 (D12). Every term gets standard counsel review. The "Counsel to confirm" column marks open points that need a specific answer.

| # | Term | Proposed content | Basis | Counsel to confirm | Package today |
|---|---|---|---|---|---|
| 1 | DPA with purpose-bound grants per source | Per source: INSPECT, COLLECT, TRANSFORM and EVALUATE at onboarding. TRAIN off by default, opt-in per source, tenant-only, no price discount. SERVE granted explicitly, per source, before the first production shadow. DPA schedule and envelope grants match; each names the granting human, policy version and expiry. No tenant-wide checkbox. | D9; founder decision 7; PL-053; spec §21 L328 | SERVE wording | `DataPurpose` defines INSPECT, COLLECT, TRANSFORM, EVALUATE, TRAIN, SERVE and EXPORT. No fixture envelope grants SERVE, and every fixture plan passes the checker without it, although the synthetic `release.activate_shadow` and `release.canary` registry records list it as required. |
| 2 | Cross-tenant use | No cross-tenant use of the partner's examples, labels or weights. Plumb may reuse derived engineering artifacts stripped of customer data: mapping patterns with applicability constraints, adapter tests, failure fixtures. The shared corpus layer (section 1) is limited to such artifacts. | D9; spec App. A.5 L570 | Yes: what "stripped of customer data" means; any opt-in corpus-contribution grant | Plan checker enforces purpose lineage. A cross-tenant reuse guard is a backlog story (E18-S05). |
| 3 | IRC 7216 | Tax-return information is excluded from source grants, enforced by folder and label exclusions and PL-053 purpose checks. The firm warrants it will not route such data. Including it later needs taxpayer consent obtained by the firm and reviewed by counsel. If counsel confirms monthly-close bookkeeping sources are outside 7216, the exclusion is relaxed for those sources. | D9; secondary compliance commentary [M10] | Yes | `ResourceScope` scopes by source, destination, processor and region only; exclusions inside a source are new (E18-S02) |
| 4 | Region and retention | US region pinning. Retention and deletion terms, with a deletion certificate. Derived data is quarantined or retired on a removal request. No promise of exact unlearning. | D9; spec §20 L318 | Yes: retention periods; certificate form | The envelope carries allowed regions. The accounting envelope and plan fixtures are EU/EUR (`eu-west-1`) and are re-templated to US/USD in P0; the RFQ fixtures are already USD (`us-east-1`) and laundry is GBP (`eu-west-2`). No deletion workflow exists (E18-S07). |
| 5 | Revocation semantics | Revoking a grant invalidates cached grants and queued dispatches within one minute. That is the bound PA-008 tests for an expired grant, applied here to revocation. If a provider accepted an action before revocation landed, deleting the local grant cannot undo it: the receipt is kept and remediation reconciled (spec §17 L276; PA-014, an industrial_rfq scenario whose accounting analogue is PA-P05). Until tested, the one-minute bound is stated as a target (term 8). | D9; spec §17 L276; PA-008; PA-014 | Yes: liability language for the race | `SourceGrant` has no `revoked_at`; the envelope and approval records do (E04-S03). Nothing enforces revocation at run time. In Prepare nothing is dispatched to clients; the race first matters at the Draft tier (PA-P05). |
| 6 | Labor-ledger disclosure | Plumb records every human minute on the tenant in the five categories, its own included. It may publish anonymized per-tenant metrics, including EIH/VD with failed attempts. The partner can see its ledger at any time and may audit it. Proposed anonymization: onboarding-order index and stack category only; no firm name, size band, location, staff or client identifiers. | D9; founder decision 11; PL-003, PL-062 | Yes: anonymization standard and re-identification risk in a cohort of five | A `HumanEffortRecord` contract exists. There is no effort-capture API or ledger yet (E01). |
| 7 | Business boundaries | Accountant sign-off on every package is mandatory, and a package reads "ready for review" until sign-off. No posting or other FINANCIAL_COMMITMENT. No client communication during the pilot. | D9; spec §15 L248; spec App. B L652 | No | The proposed Prepare envelope excludes EXTERNAL_COMMUNICATION and FINANCIAL_COMMITMENT ([MVP scope](03-mvp-scope.md) §3, step 2) |
| 8 | Security scope | Security commitments cover only gates actually passed, for example PA-019, PA-022 and PA-P14 at M1. Each commitment cites the scenario and the date it passed. No certification is claimed. | D9; spec §28 L450 | Yes. Partner security questionnaires go through the fractional compliance lead (D12). | No gate has passed. The package implements no container isolation, signing, network policy or cloud IAM (spec §19 L304). |
| 9 | Subprocessors | A list of model providers, each under no-training terms. Service-provider safeguards terms (for example the FTC Safeguards Rule) only as counsel confirms; the research notes do not source them. | D9 | Yes | None |
| 10 | Exit | 30-day termination at a close boundary, with credential revocation. Export in open formats (table below). A vendor-continuity clause. Exit pre-agreed whether or not the gate is met. | D9; Bench shutdown [M9]; Gartner exit-strategy advice [M8] | Yes: the vendor-continuity mechanism | No export exists (E11-S09) |

**Exit export formats (proposed).**

| Artifact | Format |
|---|---|
| IntegrationSpec, CollectionSpec, WorkflowSpec | JSON that validates against the package's published schemas ([IntegrationSpec](../schemas/IntegrationSpec.json), [CollectionSpec](../schemas/CollectionSpec.json), [WorkflowSpec](../schemas/WorkflowSpec.json)), with content digests |
| Tests | Test sources, fixtures and the latest run results for each test bundle |
| Evidence | EvidencePacket JSON ([schema](../schemas/EvidencePacket.json)) with provenance and time axes. Raw documents stay in, or are returned to, the firm's own store, because evidence references raw content rather than copying it (PL-009). |
| Verification | VerificationAttestation JSON ([schema](../schemas/VerificationAttestation.json)) |
| Review packages | JSON against the proposed ReviewPackage contract ([MVP scope](03-mvp-scope.md) §5; no schema exists today), plus a PDF rendering of each package |
| Labor ledger | CSV and JSON, one row per effort record (category, principal, minutes, description, recorded time), with attempt references |
| Envelope and approvals | AutonomyEnvelope and ApprovalRecord JSON ([schemas](../schemas/)) |

Open for counsel: how the EXPORT purpose applies to the firm's own copy (backlog E11-S09).

**LOI contents (proposed).** The slot; the named domain owner and reviewing accountant; stack confirmation; the baseline window; the fee band; a target signature date. Non-binding except for confidentiality.

---

## 8. Onboarding runbook

### 8.1 Who runs it on the Plumb side

| Role | Responsibilities in onboarding |
|---|---|
| Founder | Program owner: contract, kickoff, weekly check-ins, per-close report, gate review and conversion. Owns the never-claim checklist (D8). |
| Plumb domain expert | Outcome definition and cohort draw; runs the baseline time study; adjudication samples; sets the correct-package threshold at the P4 exit; owns the corpus |
| Plumb engineer/operator (integration engineer) | Probes and connectors. Any tenant-specific act is logged as ENGINEERING_INTERVENTION, and any fix to a running collector as OPERATIONAL_REPAIR (D3, D6). |
| Independent verifier (service + owner) | Attestations; monthly ledger audit; reports outside the build team (D12; ADR-007, PL-042) |
| Product engineer | Implementation card, progress feed, readiness ledger and review surface |
| Fractional compliance lead | Vendor app reviews for mail and document scopes, started in week 0; partner security reviews (D11 watch item; D12) |

### 8.2 Week by week from signature

Here "S" is the tenant's signature week; tenant 1's S is about week 4. Times are hypotheses. For tenants 2 and 3, steps 9 onward start at M1 attestation (P3), not at S+4; section 8.3 maps the calendar.

| Week | Step | What happens | Firm participants | Effort category | Firm time |
|---|---|---|---|---|---|
| S+0 | 1. Kickoff | Pilot agreement and DPA executed; fee invoiced; roles named; the firm sees its (empty) labor ledger | Firm owner | Signature: not a tenant-ledger entry (commercial, pre-tenant; a funnel metric, as in [MVP scope](03-mvp-scope.md) step 1). The rest of the call: DOMAIN_CLARIFICATION, scheduled, reported beside the budget (proposed) | 30 min |
| S+0 | 2. Envelope workshop | A 60-minute session in the implementation-card format of spec App. A.6 L578: what will change, which systems and data, which actions, maximum spend, the benefit hypothesis, and the owner decisions needed. **Decided:** the goal; an outcome definition with a denominator (the M0 row's "Domain owner can judge the outcome", spec §26 L408); per-source purposes (no TRAIN; SERVE deferred to P4); US region; spend cap; effect classes READ, INTERNAL_WRITE and EXTERNAL_WRITE_REVERSIBLE (the last only for connector setup and enabling incremental capture on the firm's own accounts), with no EXTERNAL_COMMUNICATION or FINANCIAL_COMMITMENT; tax-folder exclusions; expiry. Until the implementation card screen exists (E11-S03), the card is a document. | Firm owner (HUMAN_OWNER), domain owner | CUSTOMER_AUTHORIZATION | 60 min |
| S+1 | 3. Grants | OAuth consent per account, in each provider's own flow. Plumb never bypasses vendor approvals or MFA (spec §5 L106). Pending vendor app reviews show as blocked-dependency cards. | Firm owner or account admin | CUSTOMER_AUTHORIZATION | 30 min |
| S+1 to S+3 | 4. Inventory probes | The agent probes the exact operations on the firm's real accounts: `list_folder_changes`, `fetch_document`, collector writes and ledger metadata reads. It earns SANDBOX_TESTED probe receipts for all four (the P1 exit evidence). The collector-write receipts cover the plan's integration.configure, collection.backfill and collection.enable_incremental steps, whose checker floor is SANDBOX_TESTED; the checker's floor for read steps is DOCUMENTED, but PA-001's preconditions require SANDBOX_TESTED for the two document reads. Watch item: whether ledger authorization is granted per client company. | None | None expected | 0 |
| S+2 to S+3 | 5. Focused questions and cohort draw | **Questions:** conventions arrive through the queue, for example how folders map to clients, how period attribution works, which items each client type owes. **Cohort:** the domain expert draws the baseline cohort (section 9.3), and the firm records any vetoes. | Domain owner, Reviewing accountant | DOMAIN_CLARIFICATION | At most 5 questions per workflow; about 45 min plus 15 min for vetoes |
| S+2 to S+3 | 6. Baseline briefing | The domain expert explains the time diary | Reviewing accountant, Bookkeepers in the cohort | DOMAIN_CLARIFICATION | 30 min each |
| Next close (2 weeks between S+2 and S+8) | 7. Baseline time study | Section 9 | Reviewing accountant, Bookkeepers | DOMAIN_CLARIFICATION (recording overhead only) | Overhead below 5% of timed minutes |
| S+4 | 8. Tenant M0 exit and implementation card | **M0 exit:** the M0 checklist for this tenant passes (proposed scenario PA-P09). **Approvals:** the owner approves IMPLEMENT_OPERATE once for the collection path and confirms the backfill watermark. **Gate sheet:** signed (section 6.1). | Firm owner | CUSTOMER_AUTHORIZATION | 15 min |
| S+4 to S+10 | 9. Build | The agent fills in the BuildPlan from the inventory and reuses certified transport. It generates the client/period/obligation mapping and the CollectionSpec in a sandbox, then deploys a shadow collector, backfills 12-24 months, reconciles and goes incremental. The firm watches the progress feed. | None; may answer a new question | None expected. Any wiring, mapping or plan edit by a person, Plumb or firm staff, is ENGINEERING_INTERVENTION. | Within budget |
| About S+10 | 10. The M1 moment | A document added outside Plumb appears exactly once, attributed to the right client and period, with lineage, within the 5-minute health deadline, and the verifier attests (PA-001). The pilot clock starts (D7). The readiness ledger goes live. | Bookkeeper | None if a real client document arrives; DOMAIN_CLARIFICATION if a staff member stages the upload (proposed) | 5 min |
| S+10 to S+12 | 11. 100-pair attribution review | The reviewing accountant judges 100 sampled document-to-client/period attributions from the backfill. The result is the attribution-correctness reading (target 95% or more at the auto-accept threshold) and an input to the corpus. It is not the experiment-2 read-out (D11). | Reviewing accountant | DOMAIN_CLARIFICATION | About 2 hours |
| S+10 onward | 12. Readiness ledger in weekly use | Bookkeepers check held, confirmed-absent and unknown items per client-period. There are no send controls. Weekly use is tracked (D2 trigger: below half of active bookkeepers). | Bookkeepers | None (product use) | None required |
| S+10 to S+12 | 13. Mail history | One DATA_USE request for INSPECT and COLLECT on the mailbox, then a 24-month reminder backfill and the historical duplicate-chase baseline, labeled non-causal. If scopes are refused, fall back to document store plus ledger with a forwarding-address intake (R7). | Firm owner | CUSTOMER_AUTHORIZATION | 15 min |
| S+12 to S+16 | 14. Engagement-checklist questions | What each client type owes, proposed from templates and counted against the per-workflow budget (experiment 4) | Domain owner, Reviewing accountant | DOMAIN_CLARIFICATION | Within budget |
| About S+16 | 15. Workflow card and SERVE grant | One batched owner session: the implementation card for the preparation-only workflow (no messages, no ledger writes) and a per-source SERVE grant, required before the first shadow | Firm owner | CUSTOMER_AUTHORIZATION | 20 min |
| S+16 to S+18 | 16. Sandbox attestation | **Scenarios:** PA-002 as written in sandbox; PA-003, PA-004, PA-006, PA-008, PA-010 and PA-011 in sandbox; the parser-bounds adaptation PA-P07 and the prompt-injection adaptation PA-P19. **Threshold:** the domain expert sets the numeric correct-package threshold. The firm sees progress only. | A reviewer on the review surface, if the firm provides one | NORMAL_BUSINESS_REVIEW for the firm's reviewer | Small |
| S+18 to S+22 | 17. Shadow through the first full close | One package per eligible cohort client-period, marked "ready for review", with zero sends, plus the "what Plumb would have done" comparison (measured as PA-P02). The reviewing accountant explicitly accepts, corrects or amends each package. | Reviewing accountant | NORMAL_BUSINESS_REVIEW | At most one batched session a day; review minutes per package below the baseline (target) |
| About S+22 | 18. First full close report | A 30-minute walk-through of the per-close report (section 11.3) | Firm owner, Reviewing accountant | DOMAIN_CLARIFICATION, scheduled, reported beside the budget | 30 min |
| Gate review: S+22 to S+23, no later than the end of the 90-day clock. Promotion and conversion: the following closes (tenant 1: P6) | 19. Gate review, promotion and conversion | **Gate review:** Gates A and B are read against the gate sheet (section 6.1); a refund is assessed only for a Plumb-side miss. **Promotion** (founder decision 17, to ratify): after at least one full SHADOW close, the release moves to CANARY on a subset of client-periods whose accountants use the prepared packages in their real review, then to ACTIVE, with no EXTERNAL_COMMUNICATION at any stage. **Conversion:** after one full close in ACTIVE at or above the correct-package threshold (section 12.1). | Firm owner; Reviewing accountant | Gate review: DOMAIN_CLARIFICATION, scheduled (proposed). Any new owner decision on promotion: CUSTOMER_AUTHORIZATION. Canary and active package review: NORMAL_BUSINESS_REVIEW. The conversion signature: commercial, as in [MVP scope](03-mvp-scope.md) step 17. | 30 min for the gate review; review within the steady-state budget |

### 8.3 Calendar by tenant

Dates are hypotheses.

| Steps | Tenant 1 (S is about week 4) | Tenants 2-3 (S about weeks 9-11, proposed) | Tenant 4 (S before week 20, proposed) |
|---|---|---|---|
| 1-8: customer-side onboarding and tenant M0 | Nov 2-29, 2026 | December 2026 to mid-January 2027. All customer inputs before mid-January (D5). | P5 (Feb 22-Apr 4, 2027) |
| 7: baseline time study | The November close, about Nov 30-Dec 13 | The December close, first two weeks of January, finished by mid-January. It runs in parallel with M1R, so firm B still sees value (D5). | A close after April 15 (proposed) |
| 9-10: build and the M1 moment | Weeks 8-14, to about Jan 10, 2027 | From M1 attestation; M1R exit by about Feb 21 (weeks 12-20) | P6 |
| 13-17: M3-lite and shadow | Weeks 14-26 | Shadow starts in P5 as workflows activate. Full-close readings may land after day 180 and are reported as pending. | P6 |
| 19: gate review, promotion and conversion | Gate review about Apr 3-10, 2027 (day 180 to the end of the 90-day clock); the day-180 packet records tenant 1's evidence to date. CANARY on the next close; the earliest ACTIVE close is the April-period close, worked in early to mid May 2027, so conversion is expected in P6, about late May to June 2027 at the earliest ([roadmap](04-roadmap.md) close calendar) | After day 180 | After day 180 |

**Tax season (proposed rules).** US tax season runs from February to April 15 (D5).

- Tenants 2 and 3 finish grants, clarifications and baselines before mid-January.
- From February 1 to April 15, tenants 1-3 get no new onboarding asks beyond the steady-state budget, and a check-in may shrink to 10 minutes on request.
- Tenant 4's baseline runs on a close after April 15.
- **Calendar risk.** Tenant 1's first full shadow close falls on either the February close (assembled in early March) or the March close (assembled in early April, in the last fortnight before April 15). Mitigations:
  - Prefer the tenant-1 candidate with the highest CAS share.
  - Book review sessions in advance.
  - Report packages not yet signed off as pending, never as accepted.

### 8.4 Partner activities and their effort category

The rubric is D6 as amended by the head of product (founder decision 18, to ratify), frozen in P0 ([metrics](06-metrics.md) §6). Every minute of partner time lands in one of the five categories. Mappings marked proposed go beyond the amendment and need ratification with the rubric.

| Activity | Who | Category | Notes |
|---|---|---|---|
| Contract, DPA, pilot signature | Firm owner | Not a tenant-ledger entry | Commercial, pre-tenant; funnel metric ([MVP scope](03-mvp-scope.md) step 1) |
| Envelope decisions, OAuth consents, implementation cards, SERVE and mail grants, renewal of an expired grant, approval of the reminder policy (once requests ship, after day 180), revocation and exit actions | Firm owner or admin | CUSTOMER_AUTHORIZATION | D6 as amended. During onboarding, counts against the 2-hour budget |
| Off-surface time, for example a call to a vendor to unblock an app approval | Firm owner or admin | CUSTOMER_AUTHORIZATION | Entered manually at the check-in ([metrics](06-metrics.md) §6.3) |
| Focused questions on conventions and engagement checklists; cohort vetoes | Domain owner, Reviewing accountant | DOMAIN_CLARIFICATION | Cohort vetoes: proposed |
| 100-pair attribution or label review | Reviewing accountant | DOMAIN_CLARIFICATION | D6 |
| Baseline time-study recording overhead | Reviewing accountant, Bookkeepers | DOMAIN_CLARIFICATION | D6 as amended. The timed close work itself is not logged again (section 9.7) |
| Staged upload for the M1 verification; experiment-1 shadowing session | Bookkeeper; one staff member | DOMAIN_CLARIFICATION | Proposed |
| Package review and sign-off; later, per-case approvals when a materiality trigger fires and Draft-tier review | Reviewing accountant, Bookkeeper | NORMAL_BUSINESS_REVIEW | D6 |
| Using the readiness ledger | Bookkeepers | Not logged | Product use, not effort |
| Scheduled weekly check-ins; report walk-throughs and the gate review (proposed) | Domain owner; Firm owner and Reviewing accountant for walk-throughs | DOMAIN_CLARIFICATION, scheduled | D6 as amended. Reported beside the interruption budget, not inside it. A decision made in the call is logged in its own category, for example an authorization as CUSTOMER_AUTHORIZATION |
| Firm IT contact wires an integration, edits a mapping or writes workflow logic | Firm staff | ENGINEERING_INTERVENTION under the customer principal | D6 as amended (spec App. B L652: if a person manually wires the integrations or writes the production workflow, record that labor). Counted in EIH/VD and triaged as an interruption defect. Partners are asked never to do this. |

Plumb-side counterparts: any Plumb staff wiring, mapping, plan or workflow edit, or manual deploy is ENGINEERING_INTERVENTION, and fixing a running collector is OPERATIONAL_REPAIR (D6). The domain expert's time-study facilitation and the founder's check-ins go in the cost ledger ([metrics](06-metrics.md) §6.2). Gap: the contracts have no principal type for Plumb staff (`PrincipalType` covers human owners, reviewers and approvers plus service, agent, verifier and release-executor principals); one is needed before the effort ledger ships ([backlog](05-backlog.md) E01-S02).

### 8.5 Interruption budget

The budget comes from D6; every figure is a hypothesis. Overruns are logged and triaged as product defects. The budget counts unscheduled asks; scheduled time (weekly check-ins, report walk-throughs) is DOMAIN_CLARIFICATION reported beside it (D6 as amended).

| Stage | Item | Budget | R3 or D1 escalation |
|---|---|---|---|
| Onboarding | Owner authorization time | At most 2 hours of CUSTOMER_AUTHORIZATION | More than 4 hours per firm re-scopes the stack (D1) |
| Onboarding | Domain questions | At most 5 DOMAIN_CLARIFICATION questions per workflow | A median above 10 questions or 3 hours per workflow on tenant 3 fires R3 |
| Onboarding | Owner time in the first 30 days | At most 4 owner-hours | Clarification plus authorization above 3x budget at two partners fires R3 |
| Steady state | Owner requests | At most 1 batched owner request per tenant-week | Defect |
| Steady state | Owner decision time | At most 30 minutes a week | Above 60 minutes a week on tenant 3 fires R3 |
| Steady state | New domain questions | At most 2 per close after close 1 | Defect |
| Steady state | Reviewer approvals | Batched into at most one session a day | Defect |
| Steady state | Repeat asks | 0 | Defect, fixed before the next close |
| After calibration | Per-case approvals | At most 10% of requests | Review the materiality triggers |
| All stages | Review time | Accountant review minutes per package below baseline assembly-plus-review minutes | Commercial failure |

**First-30-day owner ask, as planned in section 8.2.**

- CUSTOMER_AUTHORIZATION: 60 + 30 + 15 = 105 minutes, within the 2-hour budget.
- DOMAIN_CLARIFICATION: about 60 minutes.
- Total: about 2 hours 45 minutes, within the 4-hour budget.
- Scheduled weekly check-ins add 60-80 minutes of DOMAIN_CLARIFICATION (three or four 20-minute sessions), reported beside the budget.
- If ledger authorization turns out to be granted per client company, the authorization figure grows with the client count. That is the D1 watch item.
- D6 does not define the window of the 2-hour authorization budget. Counting every grant through the SERVE grant (steps 2, 3, 8, 13 and 15) gives 140 minutes, over budget. Proposed reading: the 2-hour budget covers the collection path (steps 2-8), and the later mail and SERVE grants count against the steady-state budget.

---

## 9. Baseline time study protocol

This section is the field protocol for the measurement design in [metrics](06-metrics.md) §8.1. It exists because nothing in the spec or package captures accountant assembly time before deployment, and the market research found no reputable source for hours per client-month. Without it, any time-saving claim is unfalsifiable (D2).

| Element | Protocol (proposed) |
|---|---|
| Purpose | A falsifiable baseline for accountant minutes per client-period (D2), the denominator for the per-close comparison, and the input to the D7 price guardrail |
| Window | Two consecutive weeks covering one close period's assembly and review |
| When | Scheduled at the tenant's M0 exit and finished before production shadow. Tenants 2-3 finish before mid-January; tenant 4 runs after April 15. |
| Who records | Each staff member who works on a cohort client-period during the window records their own time |
| Who runs it | The firm's domain owner approves the protocol and cohort. The Plumb domain expert briefs participants, checks completeness daily and observes a sample. |
| Cohort size | At least 30 complete client-periods (D2). Proposed: draw 40 to allow for attrition. |

### 9.1 What is timed

| Code | Activity |
|---|---|
| ASSEMBLE | Gathering evidence and organizing it into a review-ready file: searching the inbox, drive and ledger, checking what is missing |
| REVIEW | Accountant review of the assembled file |
| CHASE | Requesting missing items from the client: emails, follow-ups, calls |
| REWORK | Fixes after review |
| OTHER | Close work outside evidence and packaging. Proposed sub-code OTHER-CATEGORIZE covers transaction categorization and reconciliation, so the D3 trigger can be read ("baseline time study shows accountant time is dominated by transaction categorization"). |

Counts per client-period:

- Number of requests sent to the client, and by whom.
- Requests for items already held. These are checked after the window against the backfilled document history once the collector exists; until then they are marked unverified.
- Days from period end to a complete file.

### 9.2 Who records and who observes

- **Recorders.** Reviewing accountants and bookkeepers on cohort client-periods.
- **Observation.** The Plumb domain expert directly observes at least 5 sessions per firm, across at least two roles (proposed), with staff consent, to calibrate the diaries. Agreement between diary and observation is reported.
- **Approval.** The domain owner signs off the cohort, the protocol and the final report.

### 9.3 Sampling

1. **Frame.** All recurring monthly-close clients in scope. Clients whose sources hold tax-return information or fall under other exclusions are removed, and the removals are recorded.
2. **Strata.** Ledger (QBO or Xero), the firm's own complexity rating (low, medium, high) and a transaction-volume band.
3. **Draw.** A proportional stratified random sample of 40 client-periods, with the random seed recorded. If fewer than 40 are eligible, all are taken.
4. **Vetoes.** The firm may veto a client with a recorded reason, such as client sensitivity. A replacement is drawn from the same stratum, and vetoes are reported.
5. **Reuse.** The same cohort is the shadow cohort for the first measurable deliverable, so the two readings compare like with like.

With about 30 client-periods per firm, results are reported as medians and interquartile ranges. No significance claims are made.

### 9.4 How it is recorded

The tool is a simple form or spreadsheet template supplied by Plumb. No Plumb product surface is needed; none exists before M1. Each work session is one row:

| Field | Rule |
|---|---|
| Date and minutes (or start and end time) | Required |
| Staff code and role | Pseudonymous staff code |
| Client-period code | Pseudonymous; the firm keeps the key |
| Activity code | One of section 9.1 |
| Requests sent | Count, for CHASE rows |
| Waiting or blocked | Yes or no |
| Note | Optional. Never client names, amounts or document content. |

Entries are submitted daily. The domain expert checks completeness the next business morning and follows up once. The data is covered by the DPA and stored in tenant storage.

Proposed optional field: the firm's loaded cost per hour by role. It is confidential, used only for the price guardrail and never published.

### 9.5 Data quality and freezing

- Completeness is reported as the share of cohort client-periods with entries for every relevant activity.
- Outliers are flagged, not deleted.
- A client-period with missing data stays in the denominator, marked "incomplete baseline".
- Protocol deviations are listed.
- The baseline report is signed by the domain owner and the Plumb domain expert and stored with a digest before shadow starts. It is never revised after shadow results are seen.

### 9.6 Output and use

- **Output.** Per-client-period distributions (median and interquartile range) by activity code and stratum; request counts; days to a complete file; data quality; limits.
- **Comparison.** In each shadow, canary and active close, accountant minutes per client-period on the same cohort and the same kind of close period. Where the firm agrees, add a comparable-cohort split inside the close (spec §7 L136; the contract's `MeasurementMethod` values STAGED_ROLLOUT and COMPARABLE_CASE_COHORTS).
- **Trigger.** It feeds the D2 trigger: in the first two shadow closes, accountant minutes per client-period fall by less than 25% against baseline, or packages are opened for less than 50% of in-scope client-periods, while chasing still dominates the time study.

### 9.7 Effort accounting

D6 as amended (founder decision 18, to ratify) classes baseline-study recording overhead (briefing, diary entries, observed sessions) as DOMAIN_CLARIFICATION. The close work being timed is the firm's ordinary work, not effort that Plumb caused, and is not logged again. The Plumb domain expert's time goes in the cost ledger ([metrics](06-metrics.md) §6.2). The overhead target is below 5% of timed minutes.

### 9.8 Known limits

Every report states these limits:

- Observer effect.
- A single close.
- Seasonality.
- Self-report bias.
- Chasing by phone or portal is invisible in later mail-based comparisons.

---

## 10. Discovery interview guide

This guide is for the full discovery interview. The short first-call screener is in [market and positioning](08-market-and-positioning.md) §5.6.

**Rules for the interviewer (proposed).**

- **Structure.** 45 minutes: about 35 minutes of discovery, then 10 minutes for the program and next step. No demo before the discovery questions are done.
- **Past behavior only.** Ask about the last close and specific events. Answers to "would you" questions do not count as evidence.
- **No suggestion.** Do not name Plumb features while asking, and do not suggest answers.
- **Recording.** Record verbatim quotes and numbers, and mark each as a fact (past behavior), an estimate or an opinion.
- **Data.** Never request or accept client data on the call. Screen shares hide client names.
- **Message test.** Alternate verification-led and outcome-led openings (D8), and log which one opened the call.
- **Scoring.** Score the scorecard (section 4) within 24 hours.

### A. Current close process

| # | Question | Listen for | Feeds |
|---|---|---|---|
| A1 | Walk me through how the firm closed last month for one typical recurring client, from period end to the reviewer's sign-off. | Steps, handoffs, where evidence comes from | W3, MH3 |
| A2 | Who touched that client's close, and what did each person do? | Who assembles and who reviews; candidate domain owner and reviewing accountant | MH5, MH6 |
| A3 | How many recurring monthly-close clients do you have now, and how many have been with you for 12 months or more? | At least 50; history depth | MH3, W9 |
| A4 | When a file is ready for review at your firm, what is in it? Could you show one on screen with client details hidden? | The firm's own package definition; use of checklists | W6 |

### B. Document chasing

| # | Question | Listen for | Feeds |
|---|---|---|---|
| B1 | Think of the last client whose documents arrived late. What happened, step by step? | Channels, number of follow-ups, who chased | W3, W10 |
| B2 | How does the team know which items are still outstanding for a client-period? | Spreadsheets, PM tool, memory | W6 |
| B3 | When did a client last get asked for something they had already sent? What happened next? | Frequency and consequence (the PA-005 failure class) | W3 |
| B4 | How is follow-up with a given client split across the team? | Duplicate chasing; whether anyone owns the obligation | W3 |

### C. Tools and stack

| # | Question | Listen for | Feeds |
|---|---|---|---|
| C1 | Which systems hold the evidence for a close today? | Ledgers, mail, document store, portal, PM tool | MH4, W1 |
| C2 | Roughly what share of clients is on QBO, on Xero, or on something else? | A mixed book; desktop ledgers | W1, X5 |
| C3 | Where do clients send or upload documents, and can you get files back out of each place? | Closed portals | X6 |
| C4 | Which reminders or automations have you set up in your current tools, and how are they working? | Native features already covering chase-and-match (PL-013) | X4 |
| C5 | Who in the firm has admin rights to those systems? | OAuth authority; per-client-company authorization | MH5 |

### D. Pain and cost

| # | Question | Listen for | Feeds |
|---|---|---|---|
| D1 | In the last close, how was time split between gathering documents, assembling files and reviewing them? How do you know? | Whether time is tracked; estimate versus measurement | W3 |
| D2 | What have you already tried to fix this, such as tools, hires, outsourcing or process changes? What happened? | Past spend and effort | W2 |
| D3 | What happened the last time a close ran late? | Consequences | W2 |
| D4 | What is stopping the firm from taking on more recurring clients right now? | Capacity constraint | W2 |
| D5 | If nothing new came along, what would the firm do about this in the next six months? | Real alternatives; urgency | W2, W8 |

### E. Trust and approval tolerance

| # | Question | Listen for | Feeds |
|---|---|---|---|
| E1 | Today, who has to approve anything sent to a client on the firm's behalf? Has that ever been relaxed for routine messages? | Approval culture (D6) | X8 |
| E2 | Tell me about the last time software got something wrong in your client work. How did you find out, and what changed? | Error tolerance; need for verification | Notes |
| E3 | When the firm adopted its current tools, what did you check before relying on their output? | How trust was built in practice | Notes |

### F. Data rights

| # | Question | Listen for | Feeds |
|---|---|---|---|
| F1 | What do your engagement letters say about third-party software processing client data? | Constraints on the DPA | MH12 |
| F2 | Do any folders or mailboxes used for monthly close also hold tax-return information? | Whether the 7216 exclusion is feasible | X3 |
| F3 | Have clients asked how their data is protected when the firm uses AI tools? What did you tell them? | Client pressure on data protection | MH12 |
| F4 | What is the firm's position on vendors using client data to train AI models? | TRAIN stance | W11, MH12 |

### G. Buying process

| # | Question | Listen for | Feeds |
|---|---|---|---|
| G1 | Tell me about the last software tool the firm bought for client work: who found it, who decided, how long it took and who signed. | Signer and cycle time | W8 |
| G2 | Who else would be involved in deciding to start a paid pilot with a new vendor? | Stakeholders | W8 |

### H. Willingness to pay

| # | Question | Listen for | Feeds |
|---|---|---|---|
| H1 | What does the firm spend today on software and outsourced help for monthly close, per month or per client? | The budget line, including outsourcing | Price guardrail |
| H2 | How do you price monthly bookkeeping or CAS to your clients? | Per-client mental model (D7) | Notes |
| H3 | (Closing, after a short description of the program.) Pilots are paid, $1,500-$3,000 by firm size, and credited to year one. What would need to be true for the firm to start one this quarter? | Commitment and objections | MH8 |

**Questions not to ask, and why.**

- "Is chasing your biggest problem?" It is leading.
- "Would you use a tool that ...?" and "How much would you pay for ...?" They are hypothetical; ask about past behavior and past spend instead.
- "Wouldn't it help if your packages were assembled automatically?" It is a pitch disguised as a question.

---

## 11. Weekly check-in and per-close report

### 11.1 Weekly check-in agenda (20 minutes, D9)

| Minutes | Item | Content |
|---|---|---|
| 0-3 | Since last week | Progress-feed highlights; what changed (release versions, new conventions) |
| 3-8 | Open requests and dependencies | **Requests:** at most one batched owner request. **Dependencies:** blocked-dependency cards by resolver and age; any customer-side dependency older than 14 days is flagged against the 30-day offboarding rule. |
| 8-11 | Off-surface time | Minutes the firm spent outside Plumb surfaces, entered into the ledger |
| 11-14 | Interruption budget | Owner decision minutes against the 30-minute budget; questions this close against budget; repeat asks (target 0) |
| 14-18 | Question of the week | Rotating and non-leading: usability, trust, value, approval tolerance. After shadow results: "Which kinds of requests would you let go out under a standing policy, and which would you want to see one by one?" |
| 18-20 | Next week | What Plumb will do, and anything the firm should expect |

**Rules.**

- No new asks are introduced verbally; decisions are made in the product surfaces.
- Check-in minutes are DOMAIN_CLARIFICATION, reported beside the interruption budget, not inside it (D6 as amended). A decision made in the call is logged in its own category.
- Owner: founder or success lead ([metrics](06-metrics.md) §10).

### 11.2 Program-level reads collected through check-ins

| Read | Pre-registered response | Source |
|---|---|---|
| Fewer than half of active bookkeepers at partner firms use the readiness ledger weekly, or at least 2 partners say they will not continue without sending | Run shadow packages in parallel with M1R | D2 |
| At least 2 of 3 partners make reminders a condition of continuing | Accelerate the gateway work, never skipping the HIGH scenarios | D3 |
| At least 2 of 3 partners refuse policy-level approval after seeing shadow results, or fewer than 2 of 5 partners opt into policy-level approval by close 3 | Keep per-case Draft as the default tier, price review minutes as a cost line, and offer Send only for types under a 2% edit rate | D6 |
| Sign-off lag exceeds 2 weeks | Switch the headline to attested ready-for-review packages, with the correction rate as a guardrail | D10 |
| Accepted-package metrics look healthy but partners do not renew | Switch the customer headline to retained paid client-months | D10 |

### 11.3 Per-close partner report template

The report is issued after each monthly close, starting with the first shadow close. Its audience is the Firm owner and the Reviewing accountant, and its owner is the founder. Contents follow [metrics](06-metrics.md) §10. Technical and commercial results sit in separate columns (spec §24 L382). The deployment is labeled "supervised" (D8).

| Section | Contents |
|---|---|
| Header | Firm (tenant index), close period, release tier (Prepare, Draft or Send) and stage (shadow, canary or active), release version, report version, the label "supervised" |
| 1. Outcomes (PL-001) | All eligible in-scope client-periods (the denominator). For each: attested ready-for-review; explicitly accepted without material correction; pending sign-off; actionable dependency (with resolver); terminal failure (what was tried and why it stopped) |
| 2. Co-headline | Accepted review packages, shown with the rate over all eligible client-periods and Plumb human minutes per accepted package (engineering and support shown separately) |
| 3. Quality | Correct-package rate against the domain expert's threshold; false-chase rate (target 2% or less); recall (target 90% or more); attribution correctness from the adjudication sample (target 95% or more); wrong-client attributions (count) |
| 4. Accountant time | Assembly-plus-review minutes per client-period against the frozen month-0 baseline (median and IQR, same cohort), shown only once the baseline exists; method and limits stated |
| 5. What Plumb would have done (shadow only) | The requests Plumb would have prepared, against what staff actually sent; items flagged missing that were already held |
| 6. Collection integrity | Changes seen exactly once and correctly attributed within the 5-minute health deadline; reconciliation gaps and duplicates; DEGRADED periods and their cause |
| 7. Labor ledger | The firm's minutes and Plumb's, by the five categories, for this close and cumulatively; EIH/VD to date for this tenant, failed attempts included; platform-investment hours triggered by this tenant, shown beside the ledger and never netted |
| 8. Interruption load | Owner decision minutes per week by decision type (DATA_USE, IMPLEMENT_OPERATE, CASE_LEVEL_BUSINESS); questions this close; repeat asks; per-case approval share once requests exist |
| 9. Open dependencies | By resolver and age, each with what resumes after it |
| 10. Billing basis | Pilot: none. After conversion: active client-months, credits, and blocked clients off the roster (D7). |
| 11. Context | The historical duplicate-chase baseline, labeled "historical, non-causal" |
| 12. What this report does not show | A fixed footer: no ROI or hours-saved figure without a baseline and a denominator; no claim about requests to clients before the Send canary has evidence; local tests and synthetic scenarios are not evidence |

---

## 12. Graduation and offboarding rules

### 12.1 Graduation to paid annual

**Rule (D9).** A partner graduates to paid annual once the workflow has been ACTIVE through one full close at or above the correct-package threshold. Conversion is at $15 Prepare per active client-month with a 24-month price lock, and the pilot fee is credited to year one (D7). The earliest credible renewal decision is about three closes after connection (D5).

**Promotion path (founder decision 17, decided by the head of product, to ratify).** Before day 180 the phased plan runs Prepare only in production shadow, and in the package's RELEASE state machine a release first reaches ACTIVE only from CANARY. A preparation-only release therefore goes:

1. SHADOW for at least one full close (the Gate B close, section 6.1);
2. CANARY on a subset of client-periods whose accountants use the prepared packages in their real review;
3. ACTIVE.

No stage has EXTERNAL_COMMUNICATION in the envelope. A partner converts to paid annual after one full close in ACTIVE at or above the correct-package threshold; billing then follows D7 (attested packages only, with credits). The day-180 packet records tenant 1's evidence to date, and tenant 1's conversion is expected in P6 (section 8.3). The path needs pause and kill from SHADOW and CANARY, PA-P02 passing, the HIGH scenarios passing in production, the canary step qualified at PRODUCTION_VERIFIED, and a registry step type for promotion to ACTIVE, which the package lacks ([roadmap](04-roadmap.md) P5; [MVP scope](03-mvp-scope.md) §10, open question 1).

### 12.2 Options at the gate review and each promotion (proposed)

| Option | When |
|---|---|
| Convert | The graduation rule is met: one full ACTIVE close at or above the threshold |
| Continue on pilot terms | Gate B is met and the release is still in SHADOW or CANARY on its way to ACTIVE (section 6) |
| Extend by one close, once, at no extra fee | The threshold was missed for a cause with a recorded fix, or reviewer unavailability left packages pending |
| Exit | Either party chooses not to continue. The pre-agreed exit applies, with export, deletion certificate, and a refund only for a Plumb-side miss (section 6.1). |

### 12.3 Tier graduation is separate

Moving a client and obligation type from the Draft tier to policy-approved Send follows the D6 calibration ladder: at least 2 closes and at least 20 drafts of that type, approve-without-edit of at least 95%, and material edits below 2% (hypotheses). Draft starts no earlier than P6, after the production gateway passes its gates. Because the ladder needs at least two Draft closes, the earliest policy-approved Send canary close is around July 2027 (about weeks 39-41; founder decision 14).

### 12.4 Offboarding triggers

| Trigger | Basis |
|---|---|
| Dependencies stay unresolved for more than 30 days. Proposed reading: dependencies whose resolver is the customer or a vendor; Plumb-side blocks are Plumb defects. | D9 |
| The firm's stack drifts outside the certified operations | D9 |
| The firm terminates on 30 days' notice at a close boundary | Contract term 10 |
| Material breach of the data terms, such as routing tax-return information. Proposed: immediate pause of collection from the affected source, then remediation; offboard on repetition. | Contract term 3 |
| A program-level pivot (for example R1 or R5) changes the cohort | D11 |

### 12.5 Offboarding procedure (proposed)

1. Written notice citing the trigger, with the open dependency or drift named.
2. A final per-close report.
3. Envelope revoked as a new version. Cached grants and queued work invalidated (one-minute target, contract term 5), and credentials revoked.
4. Export bundle delivered in the section 7 formats.
5. Deletion under the retention terms, with a deletion certificate. Derived data quarantined or retired; no exact-unlearning promise.
6. The ledger frozen with a digest.
7. Refund assessed against the gate sheet.
8. Exit interview.
9. The slot back-filled from the reserve without changing its variation. Onboarding order stays as it was.

### 12.6 Denominator rules

- **Blocked attempts stay in the denominator** (D9). Every eligible attempt of an offboarded or blocked tenant stays in:
  - the EIH/VD numerator;
  - the hands-off build-rate denominator;
  - the outcome mix, as an actionable dependency or a terminal failure (PL-001; PL-062).
- **No tenant is dropped from reporting.** A tenant with no verified deployment is reported as "N engineering hours, 0 verified deployments" in onboarding order, with the reason. It is never omitted.
- **Re-onboarding starts new attempts.** A tenant that returns later starts new attempts; the old ones stay.

---

## 13. Reference and publication rights; case-study criteria

### 13.1 Rights

| Use | Right | Partner approval | Basis |
|---|---|---|---|
| Anonymized per-tenant labor-ledger metrics, including EIH/VD with failed attempts | Contract right (term 6) | None per publication. The partner may flag re-identification risk. Audited figures only, published after each milestone audit (proposed). | D9; founder decision 11 |
| Named case study | The contract grants case-study rights | Proposed: the partner fact-checks the figures and approves named attribution and quotes in writing. If it declines naming, Plumb may publish the case anonymized. | D9 |
| Reference calls | Willingness to be a reference (must-have MH14) | Per call, with notice. Proposed cap: 2 calls a quarter. | D9 |
| Logo | Only inside an approved named case study | Written approval | D8 item 8 (no logo walls) |
| Quotes | Labeled as the partner's opinion, never as a measured result | Written approval | D8 |

### 13.2 Case-study admission criteria

Every criterion is required, and the founder applies the gate (D8).

1. Measured on the partner's own data in at least one full live close. Results are labeled with their stage (shadow, canary or active).
2. Every time figure compares against that firm's frozen month-0 baseline, on the same cohort and the same kind of close period, with the method and limits named (spec §7 L136).
3. Every rate shows its denominator: all eligible in-scope client-periods, including blocked, failed and late ones.
4. The firm's labor ledger is shown in the five categories, Plumb's minutes included. The deployment is labeled "supervised" unless that path has PA-027-level evidence.
5. Figures come from an audited period, either a monthly ledger audit or a milestone audit.
6. Claims match the released tier. In Prepare there are no claims about requests to clients.
7. A dollar value appears only after PA-P12 attests realized value for that firm. No ROI without a baseline and a denominator.
8. Technical and commercial results are reported separately (spec §24 L382).
9. Historical duplicate-chase figures, if shown, are labeled historical and non-causal, and never presented as a Plumb outcome (D2).
10. The case study passes the D8 never-claim checklist.

### 13.3 Claim ladder

| Stage | What may be said, with its evidence | What may not be said |
|---|---|---|
| Today, before M1 | What Plumb is building and how it will be measured | Any result; test counts; registry coverage |
| After M1 on tenant 1 | "Agent-configured certified connectors and agent-built collection"; the verified live event; tenant 1's ledger | "Automatically constructed"; "generated integrations" |
| After M1R | "Automatically constructed" for the collection path, with EIH/VD per tenant and the ledger | "Autonomous" without the ledger; any cross-industry claim |
| After the first full shadow close | Attested packages with their denominator; accountant minutes against the firm's own baseline, labeled shadow | "Fewer duplicate requests"; hours saved without a baseline; ROI |
| After Send-canary evidence (earliest Send canary close around July 2027) | Duplicate and stale requests per client-period; "one owner and one request per missing item" | Claims beyond the canary's denominator |
| After PA-027 (M5) | Replication with falling engineering effort, per tenant | "Fully autonomous"; "zero human" |

### 13.4 Never in a case study (D8)

- Local test counts. The local contract tests (counts in [VALIDATION_REPORT.md](../VALIDATION_REPORT.md)) grow with the package; never quote the spec's stale "56 tests" (header table and Appendix C). Local tests do not validate models, business outcomes, tenant security, cloud isolation or integrations (spec §28 L450).
- The three synthetic scenarios as evidence of cross-industry autonomy (spec §25 L398).
- 90 days as a commitment. It is a planning hypothesis (spec §26 L418).
- Product-video results (spec §29 L492).
- "Autonomous close" or posting. A package is "ready for review" until sign-off (spec §15 L248; App. B L652).
- "Fully autonomous", "zero human", "no humans needed" or "AI employee".
- Logo walls, or coverage taken from the registry. All 25 of its records (covering 23 step types), including the 15 marked PRODUCTION_VERIFIED, are synthetic placeholders ([registry](../plumb/registry/capability_registry.json)). Coverage is stated per operation at its maturity level (PL-007, PL-008).
- Exact unlearning (spec §20 L318).
- A claim that a message was not sent after the provider accepted it (PA-014).

---

## Open questions for founder ratification

1. **Mixed-book placement.** Tenant 1 as the mixed QBO and Xero firm (section 2.2), with tenant 4 as the fallback.
2. **Tenant 3's swapped provider.** The document store is recommended (SharePoint/OneDrive, or Dropbox or SmartVault).
3. **Pilot fee bands.** $1,500, $2,250 and $3,000 by staff band.
4. **The M0-agreed gate sheet.** Gates A and B; vendor delays extend the date day for day; a refund when a provisional must-have fails at M0.
5. **Prepare-tier promotion and conversion (founder decision 17).** Decided by the head of product and applied here (section 12.1); ratify with the decision record. Proposed here in addition: pilot terms continue at no further fee from the end of the 90-day clock until conversion or exit (section 6).
6. **Effort mappings beyond the amended rubric (founder decision 18).** The amendment settles scheduled check-ins, baseline recording overhead, customer-performed wiring and reminder-policy approval. Proposed here: the staged M1 upload, the experiment-1 shadowing session, the kickoff call, report walk-throughs and the gate review as DOMAIN_CLARIFICATION, with scheduled sessions reported beside the budget.
7. **The two-layer corpus.** Plus any opt-in cross-tenant corpus-contribution grant. Counsel to confirm.
8. **The anonymization standard** for labor-ledger publication. Counsel to confirm.
9. **Offboarding reading.** "Dependencies unresolved for more than 30 days" read as customer- or vendor-side only.
10. **Case-study rights.** Partner approval of named attribution and quotes, and a cap of 2 reference calls a quarter.
11. **Signing dates.** Tenants 2-3 signed before M1 attestation; tenant 4 before week 20, with its baseline after April 15.
12. **Scorecard weights and cut-offs.** Invite at 26 of 44; hold at 18-25.
13. **Window of the 2-hour authorization budget.** The collection path (steps 2-8), with the later mail and SERVE grants under the steady-state budget (section 8.5).

---

## Related documents

- [Product brief](01-product-brief.md): personas, the beachhead and the product promise.
- [Strategy decisions](02-strategy-decisions.md): D1 to D12 in full, including D9, and founder decisions 17 (Prepare-tier promotion) and 18 (effort-rubric amendment).
- [MVP scope](03-mvp-scope.md): the 18-step partner journey, surfaces, supported environments v1 and the ReviewPackage proposal.
- [Roadmap](04-roadmap.md): phase windows, exit evidence and the proposed scenarios PA-P01 to PA-P19.
- [Backlog](05-backlog.md): stories behind the surfaces and terms referenced here (E01, including E01-S02; E04-S03; E11; E14-S01; E16-S07; E18).
- [Metrics](06-metrics.md): EIH/VD, the co-headline, the effort rubric, the interruption budget and the baseline design.
- [Risks and assumptions](07-risks-and-assumptions.md): R1 to R7 and their pre-registered triggers.
- [Market and positioning](08-market-and-positioning.md): the competitive map and message tests.

---

## Sources

**Repository (verified for this document).**

- [Spec v0.2](../spec/Plumb_Autonomous_Implementation_Specification_v0.2.md): header table L15 and App. C L662 (the stale "56 tests"); §5 L106; §7 L136; §15 L248; §17 L276; §18 (PL-044 at L284); §19 L304; §20 L318; §21 L328; §24 L382; §25 L398; §26 L404, L408, L413, L416, L418; §28 L450; §29 L492; App. A.5 L570; App. A.6 L578; App. B L652, L654.
- [Requirements index](../spec/requirements_index.json): PL-001, PL-003, PL-007, PL-008, PL-009, PL-010, PL-013, PL-042, PL-044, PL-053, PL-062, PL-063; ADR-007, ADR-010.
- [Acceptance catalog](../acceptance/production_acceptance_catalog.yaml): PA-001 (test user uploads outside the platform; five-minute deadline; any ENGINEERING_INTERVENTION fails), PA-005 (webhooks plus overlap polling), PA-008 (one-minute invalidation of cached grants and queued dispatches for an expired grant), PA-009 (request-id lookup), PA-012 (100 input/label pairs to an accountant reviewer), PA-014 (an industrial_rfq scenario), PA-017 (two tenants), PA-027 (MEDIUM; preconditions; comparison with the first customer). Counts verified from `requires` tags: 19 of 30 scenarios need grants, 24 need real adapters.
- Code and fixtures:
  - [common.py](../plumb/contracts/common.py): `DataPurpose` with SERVE and EXPORT; `HumanEffortCategory`; `HumanEffortRecord`; `PrincipalType` (no Plumb-staff type); `DependencyRecord` (no `resolved_at`); `ResourceScope`; `BuildState`.
  - [envelope.py](../plumb/contracts/envelope.py): `SourceGrant` without `revoked_at`; `AutonomyEnvelope` with it. [approval.py](../plumb/contracts/approval.py): decision kinds and `revoked_at`. [opportunity.py](../plumb/contracts/opportunity.py): `MeasurementMethod`. [integration.py](../plumb/contracts/integration.py): `IntegrationPath`.
  - [machines.py](../plumb/statemachines/machines.py): RELEASE reaches ACTIVE from CANARY (or from PAUSED, which only ACTIVE reaches).
  - [capability registry](../plumb/registry/capability_registry.json): 25 synthetic records covering 23 step types (15 PRODUCTION_VERIFIED, 8 SANDBOX_TESTED, 2 DOCUMENTED); `release.activate_shadow` and `release.canary` require SERVE.
  - [schemas](../schemas/).
  - Fixtures: the [accounting envelope](../fixtures/envelopes/accounting_evidence_preparation.json) and plan are EUR/`eu-west-1`; the RFQ fixtures USD/`us-east-1`; laundry GBP/`eu-west-2`. All three envelopes expire 2027-03-31, none grants SERVE, and all three plans pass the plan checker.
  - [validation report](../VALIDATION_REPORT.md): the local test counts (not repeated here, because the suite grows).
- Doc set: the [decision record](02-strategy-decisions.md) (D1-D12; founder decisions 7, 11, 13, 14, 16, 17 and 18; R1, R3, R5, R7); the [roadmap](04-roadmap.md) for PA-P01, PA-P02, PA-P05, PA-P07, PA-P09, PA-P12, PA-P14, PA-P15 and PA-P19, and the close calendar; [metrics](06-metrics.md) for the amended rubric and the interruption budget.

**Market (from the research notes; vendor-reported and secondary items flagged).**

- [M1] US Census Bureau, Statistics of US Businesses 2022 (released April 2025). Employer firms only; NAICS 541219 includes non-bookkeeping firms. https://www2.census.gov/programs-surveys/susb/tables/2022/us_state_6digitnaics_2022.xlsx
- [M2] AICPA PCPS CPA Firm Top Issues Survey, June 2026: for firms with 11-30 professionals, hiring experienced staff is #1 and managing workload and capacity #3. Secondary coverage. https://www.cpapracticeadvisor.com/?p=185547
- [M3] Financial Cents 2025 State of Accounting Workflow Automation (vendor survey, 816 professionals): getting documents from clients is the biggest workflow issue; clients take 5 days on average to submit requested documents. https://financial-cents.com/?p=9086
- [M4] Uku AI in Accounting 2026 (small, self-selected sample; directional): 68% would hand document chasing to an AI agent first; 62% require approval before anything is sent; 53% demand no training on their data. https://getuku.com/ai-in-accounting-report/
- [M5] Intuit QuickBooks 2026 Accountant Technology Survey (vendor survey, 725 respondents, via CPA Practice Advisor): average tech spend about $21,000 a year; about 10 apps per firm. The notes also attribute to this source that 60% of clients ask accountants for proof of AI data protection. https://www.cpapracticeadvisor.com/2026/07/02/the-2026-accountant-technology-survey-turning-data-revelations-into-a-firm-of-the-future/185807/
- [M6] Ramp and CalCPA, Benchmarking the Modern CPA Firm 2026 (California only): top barrier is training and implementation time (31%); data security is the top client-facing concern (39%). https://ramp.com/reports/benchmarking-the-modern-cpa-firm-2026-or-calcpa-and-ramp
- [M7] Financial Cents State of AI in Accounting and Bookkeeping 2026 (vendor survey, n=486): time to learn and implement 41%, cost 6%; 20% report clear measurable ROI. https://financial-cents.com/?p=39931
- [M8] Gartner, Sep 29-30, 2026: predicts 70% of enterprises will abandon agentic AI built through vendor forward-deployed engineering by 2028, and advises defining IP ownership, knowledge transfer and an exit strategy from day one. Some details via secondary coverage. https://www.gartner.com/en/newsroom/press-releases/2026-09-29-gartner-predicts-70-percent-of-enterprises-will-abandon-agentic-ai-built-by-vendor-forward-deployed-engineering-by-2028
- [M9] Bench Accounting shut down on December 27, 2024 after raising $113M, leaving about 35,000 US customers. https://www.geekwire.com/2024/vancouver-fintech-company-bench-accounting-announces-sudden-shutdown/
- [M10] IRC 7216 consent obligations when tax-return data is disclosed to third-party AI systems. Secondary compliance commentary, not IRS guidance or legal advice; verify with counsel. https://my-cpe.com/blogs/ai-compliance-for-cpa-accounting-firms-irc-7216-aicpa-ftc
- [M11] CPA Trendlines PE deal tracker: about 180 PE deals in accounting in 2025. Partly paywalled; the 2025 count comes from search snippets. https://cpatrendlines.com/2026/03/01/pe-deal-tracker-for-feb-2026-57-deals-in-60-days/
- [M12] Crete Professionals Alliance, backed by Thrive Capital, plans to spend $500M on an AI-driven CPA roll-up; since renamed Current (market notes). Reuters via syndication. https://kfgo.com/2025/06/04/thrive-backed-accounting-firm-crete-to-spend-500-million-in-ai-roll-up/
- [M13] Per-client close-tool pricing:
  - Double: the vendor page confirms per-connected-client pricing and a $200/month annual-commitment tier; tier prices $10/$25/$50 come from secondary listings. https://doublehq.com/pricing
  - Financial Cents Month-End Close add-on: $5 per client per month (vendor page). https://financial-cents.com/pricing/
  - Xenett: about $7.5 (AI Review) or $10 (Workflow) per client per month, plus a $15 accruals-and-AI add-on (vendor pages). https://www.xenett.com/pricing
