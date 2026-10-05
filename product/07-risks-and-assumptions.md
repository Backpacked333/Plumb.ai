# Risks, Assumptions and Open Questions

- Status: Draft v0.1 (2026-10-04), proposed — requires founder ratification
- Owner: Product
- Basis: spec v0.2, [decision record](02-strategy-decisions.md)

Part of the product doc set ([index](README.md)). This document expands D11 (top risks and kill/pivot criteria) of the [decision record](02-strategy-decisions.md), together with the risk-bearing parts of D1, D2, D5, D6, D7, D8 and D9. It holds the risk register (R1-R7), the six experiments that spec §27 leaves open, the assumption map, the open product questions and the watch items. It ends with the never-claim checklist, treated as a risk control. Metric definitions are in [metrics](06-metrics.md), work items in the [backlog](05-backlog.md), phase windows and proposed acceptance scenarios (PA-P01 to PA-P19) in the [roadmap](04-roadmap.md), scope in [MVP scope](03-mvp-scope.md), positioning in [market and positioning](08-market-and-positioning.md), and partner contract terms in the [design-partner program](09-design-partner-program.md).

**How to read this document.** Three kinds of statement are kept apart:

| Label | Meaning |
|---|---|
| Spec requires | Normative text in [spec v0.2](../spec/Plumb_Autonomous_Implementation_Specification_v0.2.md) or a scenario in the [acceptance catalog](../acceptance/production_acceptance_catalog.yaml). Cited as "spec §N", with line numbers only where verified against the file. |
| Package has | Code or data in the reference package today, verified on 2026-10-04 and named by file path. |
| Proposed | This document's proposal, derived from the decision record. Not ratified. |

**Nothing here has been measured.** There is no tenant, no effort ledger and no deployed service. Likelihood and impact ratings are the strategy panel's judgment, not data. Every threshold is a hypothesis from the decision record unless the spec or the catalog states it. All of them go into threshold sheet v1 (backlog E24-S01), issued in P0 and ratified at the M0 exit.

**Where things stand (verified 2026-10-04).**

- The reference package is a deterministic policy kernel: typed contracts, plan, approval, release and dataset checkers, a SQLite effect ledger and seven state machines. Its local contract tests (more than 800; counts in [VALIDATION_REPORT.md](../VALIDATION_REPORT.md)) do not, under spec §28 (L450), validate models, business outcomes, tenant security, cloud isolation or integrations. The spec's own "56 tests" figure (header table and Appendix C) is stale.
- None of the 30 catalog scenarios has run against production. The catalog itself records `executed_against_production: false`.
- The [capability registry](../plumb/registry/capability_registry.json) describes itself as synthetic. Of its 25 records (covering 23 step types), 15 are marked PRODUCTION_VERIFIED, and none establishes access to a real account.
- The value-producing loop (inventory, connect, collect, plan, execute, verify, release, measure) is not built.

---

## 1. Pre-registration rule

Spec §27 (L442) lists six experiments that "remain necessary", and the decision record adds commercial unknowns. A pivot decision that is taken only after the results are in can be rationalized. So every threshold that decides a risk or an experiment is written down before the data exists (D11).

### 1.1 What is pre-registered, and when

| Artifact | Content | Owner | Issued | Ratified |
|---|---|---|---|---|
| Threshold sheet v1 (E24-S01) | Every numeric trigger in section 2; the experiment thresholds in section 3; the D5 M2 entry gates; the D6 interruption budget and Draft-to-Send ladder; the D10 targets; the D7 commercial triggers; the correct-package threshold (set by the domain expert at the P4 exit, then frozen) | Plumb domain expert, co-owned by the founder (D12) | P0 (weeks 0-2) | M0 exit (P1), by the domain expert and an external technical advisor |
| Experiment charter | The six spec §27 experiments as written in section 3: hypothesis, test, metric, threshold, decision, phase, failure response | Founder | P0, with the threshold sheet | M0 exit |
| Effort rubric v1 | The five categories (CUSTOMER_AUTHORIZATION, DOMAIN_CLARIFICATION, NORMAL_BUSINESS_REVIEW, ENGINEERING_INTERVENTION, OPERATIONAL_REPAIR) and their boundary cases, as D6 amended by founder decision 18 (to ratify) ([metrics](06-metrics.md) section 6) | Founder, with the domain expert | Frozen in week 1 (P0) | Signed at P0 exit |
| Never-claim checklist | The twelve items in section 7 | Founder | Published in P0 | Not relaxed under any result (D8) |

**Changing a threshold (proposed).** After ratification, a threshold changes only through a new, dated sheet version that states the reason, and only for readings taken after the change. No threshold changes once the data it judges is visible. Old versions stay in the record, and every report names the version in force. The decision record's revisit triggers are the only route to changing a decision itself.

### 1.2 Reading rules (D11)

| # | Rule (D11) | What it means in practice (proposed) | Guard against misuse (proposed) |
|---|---|---|---|
| 1 | Each threshold is read together with its root cause, against the stack-variation matrix | Every trigger reading comes with a breakdown of engineering minutes and failed attempts by failure class (PL-018; spec App. A.3). It also names the tenant's slot in the D1 matrix: tenant 1 is the baseline stack; tenant 2 shares provider families but differs in folder structure and chart-of-accounts conventions; tenant 3 swaps one provider. | The root cause explains a number. It never replaces the number in the report. |
| 2 | A failure traced to a primitive that is now in the registry, and that later tenants do not need, counts as a pass in progress | Example: tenant 3's engineering went into a webhook-dedup primitive that tenant 4 then reuses unchanged. That reads as "pass in progress", not as an R1 fail. | The primitive must exist in the registry with a digest, contract tests and applicability constraints (a platform-investment ledger entry, E01-S05). The hours stay in the tenant's EIH/VD and are never netted (D10). The reading changes the decision, not the number. If the next tenant still needs the same work, the reading reverts to fail. |
| 3 | A decline produced by cherry-picking easy tenants counts as a fail | Swapping a hard tenant for an easy one to make the trend fall is reported as a failed trigger. | Onboarding order and matrix slot are locked when each envelope is signed. Offboarded and blocked tenants stay in the report with their hours (D9; [metrics](06-metrics.md) section 2.3). |
| 4 | Windows are not extended when two triggers fire at once | Two triggers firing together means the response in section 2 runs on schedule. | The only extension the record allows (D11 revisit trigger): variance between firms is high, the trend clearly improves (the 4th and 5th firms beat the 3rd by a wide margin), and only one trigger fired. Then the window extends by one cohort, once. |

**Who reads, and what counts as firing (proposed).** The founder reads triggers with the domain expert and an external technical advisor, in writing: the R1 checkpoint memo at M1R (P3) and the day-180 decision packet (P5) ([roadmap](04-roadmap.md) section 9). A trigger fires only on an instrumented metric reported with its denominator, per tenant ([metrics](06-metrics.md) section 4.6). A trigger that cannot be read is reported as "not readable". That is an instrumentation gap to close, never a pass.

---

## 2. Risk register

The seven risks come from the decision record. In its words, R1 and R2 decide whether a platform exists at all, R3 and R4 whether "without constant interruption" and safe effects survive contact with real firms, R5 whether a proven platform sells, and R6 and R7 whether the evidence arrives at all. The record names no owners, so the owners below are **proposed**, using the D12 roles. Likelihood and impact are the panel's judgment, and all thresholds are hypotheses.

| ID | Risk | Tied to | Likelihood | Impact | Lead indicator ([metrics](06-metrics.md)) | Trigger (short form) | First readable | Owner (proposed) |
|---|---|---|---|---|---|---|---|---|
| R1 | Replication does not get cheaper, so Plumb is a services business | Experiments 3 and 6 | Medium-High | Existential | EIH/VD; hands-off build rate; artifact reuse rate and fork count | Tenant 3 EIH/VD at or above 75% of tenant 1; hands-off below 50%; reuse below 60%; any fork | P2 baseline; P3 trigger | Founder |
| R2 | Hidden human labor presented as autonomy | PL-003 | Medium | Existential to credibility | Ledger audit findings; share of effort captured automatically | Any unrecorded engineering found in an audit | P0 ledger; P2 first milestone audit | Founder |
| R3 | Interruption load turns the customer into the systems integrator | Experiment 4 | Medium | High | Interruption load | Median clarification above 10 questions or 3 hours per workflow on tenant 3; owner time above 60 minutes a week; more than 3x budget at two partners | P1 onboarding; P4 workflow | Product engineer |
| R4 | Generated failure handling is unreliable and causes an effect-safety incident | Experiment 5 | Medium | High | Protected failure-case pass rate; client-request integrity | More than 10% of protected cases fail across two tenants; one real-client incident in canary | P4 sandbox; P6 Draft canary; Send canary not before about July 2027 | Tech lead |
| R5 | Market squeeze and low willingness to pay | Commercial unknown | Medium-High | High | Commercial conversion; design-partner funnel; measured value per active client-month | 3 of 5 prospects choose native tools; 50% pick an incumbent; fewer than 2 of first 4 convert at $15 or more; cost above 2x price at tenant 4 | P0 funnel; P6 conversion (tenant 1's evidence to date in the day-180 packet) | Founder |
| R6 | Build time versus runway | Commercial unknown | High | High | Milestone attestation dates; time to first verified event | PA-001 not passed on tenant 1 by week 14; M1R not passed by week 24 | P2 | Founder |
| R7 | Data rights and access block the evidence | Commercial unknown | Medium | Medium-High | Source grants by source and purpose | 2 of 5 partners refuse mailbox scopes, or no vendor approval by M3-lite; fewer than 2 TRAIN grants; counsel finds IRC 7216 blocks sources | P0 vendor timelines; P4 | Founder |

### 2.1 R1: Replication does not get cheaper

**Description.** Tenants 2 and 3 need about as much audited human engineering as tenant 1, so EIH/VD does not fall. In the strategy thesis's words, Plumb would then be "a services firm with good contracts".

**Cause.**
- Experiments 3 and 6 are open: whether agents "can adapt existing adapters cheaply enough", and "the rate of maintainable reuse across customers" (spec §27 L442).
- Real tenant variance: "different folder structures, chart-of-account conventions and minor API differences" (spec App. B L654).
- PA-001 accepts `path_used` VERIFIED_ADAPTER, so passing it alone proves orchestration of a pre-built adapter, not construction. The accounting plan fixture states that "No adapter code is generated for this customer" ([fixture](../fixtures/plans/accounting_evidence_preparation.json)).
- The package has no integration factory, collector or artifact store to reuse from.

**Likelihood and impact.** Medium-High; existential (PL-062, ADR-010).

**Early-warning indicators** (names from [metrics](06-metrics.md)):
- EIH/VD per tenant in onboarding order. The earliest signal is tenant 2 against tenant 1, before tenant 3 starts.
- Hands-off build rate.
- Artifact reuse rate and fork count.
- Implementation-autonomy report: repair attempts per verified deployment, by failure class.
- Platform-investment hours triggered per tenant. These are healthy only if the next tenant reuses the primitives they produced.
- The D9 capacity signal: tenant 2's onboarding takes more than 50% of engineering capacity for more than 3 weeks.

**Mitigations.**
- Controlled stack-variation matrix (D1; [design-partner program](09-design-partner-program.md)).
- Agent-generated tenant semantics on certified transport (E07; E07-S03).
- A deliberate provider swap at tenant 3, forcing a non-VERIFIED_ADAPTER path (E07-S05; PA-P01).
- Verified builds feed reusable primitives into the registry (E02; reuse by digest, E07-S07).
- A separate platform-investment ledger (E01-S05).
- Root-cause analysis by failure class at each checkpoint (E05-S07).
- At most 3 active builds until M1R passes (E05-S08).

**Kill or pivot criterion (pre-registered, D11).** At the M1R checkpoint, any of: tenant 3's EIH/VD at or above 75% of tenant 1's; hands-off build rate on tenants 2 and 3 below 50%; artifact reuse below 60%; any code fork. Response: freeze new milestone work for 4 weeks and find the root cause. If tenant 4 still shows no decline, pivot: sell the factory as tooling for human implementers (MSPs, VARs, roll-ups) and drop the autonomous-implementation claim, or become an honestly priced verified-implementation service.

**Owner (proposed).** Founder, accountable. Integration engineer (registry owner under D12; spec §26 L416 asks for a named owner), responsible for reuse. Verification and acceptance-harness engineer, who computes EIH/VD outside the build team.

**Linked ids.** PL-002, PL-003, PL-020, PL-062, PL-063; ADR-010; PA-001, PA-027; PA-P01, PA-P13.

### 2.2 R2: Hidden human labor presented as autonomy

**Description.** Plumb staff, or the customer's staff, do implementation work that is never recorded or is put in the wrong category, and a deployment is presented as more autonomous than it was. Spec requires: Plumb "MUST NOT call a deployment autonomous if a person secretly performed the implementation behind the interface" (PL-003, spec §1 L47).

**Cause.**
- Spec §1 (L51) allows a supervised first delivery, and there is commercial pressure to look autonomous during it.
- PA-001 fails on any ENGINEERING_INTERVENTION entry. That condition rewards keeping work off the ledger.
- Package has: the `HumanEffortCategory` enum and a `HumanEffortRecord` model in [common.py](../plumb/contracts/common.py) and a `human_effort` table in the [SQL design](../sql/001_initial_design.sql), but no running ledger, no API operation that records effort and no capture. `PrincipalType` has no type for Plumb staff, so staff effort cannot be told apart from the customer's by principal type (gap).
- Other leak paths: work in provider admin consoles, tenant work relabeled as platform investment, and customer IT staff doing the wiring (ENGINEERING_INTERVENTION under the D6 rubric as amended by founder decision 18).
- Market context: Builder.ai went bankrupt after reports that its "AI" relied on hundreds of human engineers (secondary coverage, May-June 2025), and the FTC's Operation AI Comply continues to pursue deceptive AI claims (law-firm analysis, Aug 2026). Sources are at the end.

**Likelihood and impact.** Medium; existential to credibility. It would invalidate every PL-062 claim and expose Plumb to AI-washing enforcement.

**Early-warning indicators.**
- Ledger audit findings: unrecorded, miscategorized and mistimed entries ([metrics](06-metrics.md) section 6.4).
- Share of ENGINEERING_INTERVENTION and OPERATIONAL_REPAIR minutes captured automatically (the ledger-health measure).
- Disagreement rate in the double-coded audit sample.
- Platform-investment entries that name no registry primitive or digest.
- Commits, deploy logs or provider admin sessions on a tenant with no matching ledger entry.
- A tenant window showing zero engineering minutes alongside a spike of platform-investment hours.

**Mitigations.**
- Automatic capture of human-principal actions (E01-S04) in an append-only ledger with attempt references (E01-S03).
- A separate platform-investment ledger (E01-S05).
- Ledger-audit tooling (E10-S07) and milestone invalidation (E01-S07).
- An auditor outside the delivery team at M1, M1R and M5, plus a monthly audit of the delivery team's account using PA-027's method (D12).
- A customer-visible ledger in the results-and-effort view (E11-S05).
- No per-customer delivery engineers (D12).
- Agents get no general administrator credentials and the gateway resolves credentials for approved operations (PL-006). Human console access outside it is logged as break-glass access (proposed; [metrics](06-metrics.md) section 2.3).
- The never-claim checklist (section 7; E24-S02).

**Kill or pivot criterion (pre-registered, D11).** Any unrecorded engineering found in an audit invalidates the milestone and forces a re-run. A second occurrence triggers an external audit before any external claim.

**Owner (proposed).** Founder: never-claim checklist, and the milestone audits with an external technical advisor. Verification and acceptance-harness engineer: the monthly audit, reporting outside the build team (ADR-007).

**Linked ids.** PL-002, PL-003, PL-006, PL-059, PL-062; ADR-007, ADR-010; PA-001, PA-027; PA-P09, PA-P13.

### 2.3 R3: Interruption load turns the customer into the systems integrator

**Description.** Domain clarifications, authorizations and approvals pile up until the firm owner and the reviewing accountant are effectively doing integration work. That breaks the promise in the spec §17 title, "without constant interruption" (L266), and lets owner minutes consume the value. Spec requires that human boundaries "must not turn into a requirement for the customer to become a systems integrator" (spec §1 L51).

**Cause.**
- Experiment 4 is open: "the amount of domain clarification per workflow" (spec §27 L442).
- The engagement checklist may not be inferable from sources. Spec App. B (L602) then asks the owner a focused question.
- Conventions vary by firm.
- Binding approvals to exact digests (PL-040) means a source edit or policy bump invalidates them, which can bring back the interruptions PL-041 forbids. PA-006 and PA-010 as written are per-case approvals.
- Ledger authorization may be granted per client company (watch item, section 6).
- Tax season leaves reviewers with less time.

**Likelihood and impact.** Medium; high.

**Early-warning indicators.**
- Interruption load: DOMAIN_CLARIFICATION questions per workflow and the decay ratio of close n against close 1; owner decision minutes per tenant-week by decision type (DATA_USE, IMPLEMENT_OPERATE, CASE_LEVEL_BUSINESS); owner requests per tenant-week; repeat-ask rate; per-case approval share. The budget counts unscheduled asks; scheduled weekly check-ins and baseline-study recording overhead are DOMAIN_CLARIFICATION and reported beside it (founder decision 18).
- CUSTOMER_AUTHORIZATION minutes per firm at onboarding. Above 4 hours re-scopes the stack (D1).
- Outcome mix per authorized goal: median days in dependency with the customer as resolver.
- Review burden: accountant minutes per package against the month-0 baseline.

**Mitigations.**
- Engagement-checklist templates (E13-S02).
- A focused-question queue with a per-workflow budget (E11-S06).
- Answers become versioned conventions (E09-S06; PA-004).
- Batching with `group_missing_authorizations`. Package has it in [approval_checker.py](../plumb/checker/approval_checker.py), called only by the local tests; wiring it to a product surface is E15.
- Interruption-budget metering (E15-S05).
- Policy-level approval with D6 materiality triggers (E15-S06; PA-P03).
- Batched review sessions (E14-S07).
- The ICP floor of at least 60% recurring CAS revenue, so tax season does not absorb the domain owner (D1).

**Kill or pivot criterion (pre-registered, D11).** On tenant 3, any of: median DOMAIN_CLARIFICATION per workflow above 10 questions or 3 hours; steady-state owner decision time above 60 minutes a week; owner clarification plus authorization above 3x the budget at two partners. Response: pivot to a fixed vertical template with firm-level defaults, narrow the ICP to firms with documented engagement checklists, and stop claiming self-discovery in this vertical. If owner minutes exceed measured accountant savings, kill the wedge.

**Timing note (inconsistency recorded).** The trigger is read on tenant 3, but tenant 3's review workflow only starts shadow in P5, so its workflow-level reading may land after day 180. Earlier readings: tenant 3's collection-path clarification during M1R (P3), and tenant 1's workflow clarification at the P4 exit. If tenant 3's workflow reading is not available for the day-180 packet, it is reported as pending, not as passed.

**Owner (proposed).** Product engineer: the queue and the instrumentation. Founder: owns the interruption budget (D12). Plumb domain expert: owns the engagement-checklist templates.

**Linked ids.** PL-003, PL-010, PL-011, PL-040, PL-041; PA-003, PA-004, PA-006, PA-008, PA-010; PA-P03.

### 2.4 R4: Generated failure handling and effect safety

**Description.** Generated workflow logic mishandles a failure, and a duplicate, stale or wrong-client request reaches a real client once Draft or Send ships, or a wrong package reaches the accountant. One such email can cost a partner its client, and cost Plumb the partner.

**Cause.**
- Experiment 5 is open: "the reliability of generated failure handling" (spec §27 L442).
- Package has: a SQLite effect ledger that "does not implement a production outbox, distributed leases or provider guarantees" (spec §16 L264).
- Package has: a RELEASE state machine that allows PAUSED only from ACTIVE, so a CANARY release cannot be paused, only promoted, rolled back or retired ([machines.py](../plumb/statemachines/machines.py)). The [effect ledger](../plumb/ledger/effect_ledger.py) does not check release pause before dispatch; on authority it only flags a divergent `authority_ref` and leaves the re-check to the dispatcher.
- Temporal "does not supply a business-level exactly-once guarantee for arbitrary external APIs" (spec §3 L84).
- A provider without request-id lookup leaves an UNKNOWN effect that only a human can reconcile.
- A mailbox draft is an external write, not an action without external effect (D3).

**Likelihood and impact.** Medium; high.

**Early-warning indicators.**
- Protected failure-case pass rate: in sandbox in P4, against the sandbox gateway in P5.
- Client-request integrity, read as "would-have-sent" in the P5 shadow reports and for real from P6.
- False-chase rate and collection integrity.
- Revocation-to-stop latency and pause-to-block latency.
- Draft calibration: the material-edit rate per client and obligation type.

**Mitigations.**
- Preparation-only first; Draft before Send (D3).
- The production action gateway: a PostgreSQL effect ledger with outbox, distributed leases, dispatch-time authority, revocation, pause and state checks, and UNKNOWN reconciliation (E17: E17-S01, E17-S02, E17-S03, E17-S04).
- Pause and kill from SHADOW and CANARY (E16-S03).
- The protected verifier with the Appendix B failure set (E10-S05) and the fault-injection harness (E10-S03).
- Any HIGH-severity failure blocks activation (PL-061).
- The D6 calibration ladder from Draft to Send (E15-S07).
- The revocation race handled truthfully (E17-S08; PA-P05).

**Kill or pivot criterion (pre-registered, D11).**
- After bounded repair, generated workflows fail more than 10% of the protected Appendix B failure cases (PA-003, PA-004, PA-005, PA-006, PA-007, PA-008, PA-009, PA-010, PA-011) across two tenants: stop generating workflow logic, use only certified template workflows, and never claim "generated workflows".
- One real-client duplicate, stale or wrong-client request in canary: halt sends, revert to Draft, and run root-cause analysis.
- Two such incidents within 90 days: Send leaves the product for two quarters, and preparation-only becomes the product.

**Owner (proposed).** Tech lead (action gateway owner under D12; spec §26 L416). The verification engineer owns the protected verifier. SRE/on-call joins by about week 22, before any Draft or canary (D12).

**Linked ids.** PL-036, PL-037, PL-038, PL-039, PL-042, PL-047, PL-061; ADR-009; PA-003, PA-004, PA-005, PA-006, PA-007, PA-008, PA-009, PA-010, PA-011, PA-015; PA-P02, PA-P03, PA-P04, PA-P05.

### 2.5 R5: Market squeeze and willingness to pay

**Description.** The platform works, but firms choose free or cheap native tools or incumbents, or will not pay $15 per active client-month (hypothesis, D7).

**Cause** (market facts from the research notes; vendor-reported and secondary items flagged):
- Intuit Accountant Suite, launched Oct 28, 2025, with Books Close at Scale in beta. It is free during the introductory period in the UK, and in the US per a secondary source.
- Xero Partner Hub Document Requests chase clients and match documents to transactions (announced July-August 2026; vendor-reported via trade press).
- Double claims 4,000+ North American firms and 150% NDR (vendor-reported, Dec 2025).
- Basis ($100M at a $1.15B valuation, Feb 24, 2026) and Digits could move down-market.
- Agent-built connectors are becoming table stakes: Nango Management MCP, Membrane, superglue (vendor-reported).
- Chase-and-remind tools sell at $5-$99 a month, and the average firm tech spend is about $21,000 a year (Intuit 2026 survey, vendor-run).
- No reputable primary source exists for the hours a firm spends per client-month on close or chasing (market-accounting notes), so the value case is unproven until the month-0 study.

**Likelihood and impact.** Medium-High; high. A proven platform that cannot be sold.

**Early-warning indicators.**
- Design-partner funnel: qualified conversations, LOIs and paid pilots. Fewer than 2 paid LOIs after about 30 qualified conversations is a D7 trigger.
- The share of the first 25 qualified calls with materially mixed stacks. Below 30% narrows the ICP (D1).
- Head-to-head outcomes against native tools after a PL-013 comparison (funnel outcomes).
- Readiness-ledger and package adoption.
- Measured value per active client-month. Under about $45 caps Chase at $15 or folds it into Prepare (D7).
- Commercial conversion.
- Fully loaded cost per verified deployment, and gross margin per active client-month.
- The message-test meeting rate by framing (D8).

**Mitigations.**
- Qualify out single-ecosystem firms whose native chase-and-match already works (D1; [design-partner program](09-design-partner-program.md)).
- A native-feature baseline in every OpportunitySpec, configuring native tools when they are enough (E12; E12-S03; PA-P11).
- Lead with verified packages, not chasing ([market and positioning](08-market-and-positioning.md)).
- Per-client outcome pricing and a billing basis tied to attested packages (E20; D7).
- Paid pilots from day one, and a roll-up channel probe (D9).
- The price guardrail: no more than one-third of measured value, attested before any external value claim (PA-P12).

**Kill or pivot criterion (pre-registered, D11).** Any of: at least 3 of 5 qualified prospects choose native tools after a PL-013 comparison; 50% or more of qualified mixed-stack prospects pick an incumbent head-to-head; fewer than 2 of the first 4 partners convert to annual at $15 or more per active client-month; fully loaded cost per active client-month at tenant 4 above 2x price with no downward trend. Response: pivot to the roll-up/MSP channel or per-package pricing, and re-examine the ICP before cutting price. "3 of 5 convert" is a target, never a kill (dissent record).

**Owner (proposed).** Founder.

**Linked ids.** PL-001, PL-012, PL-013, PL-059; PA-P11, PA-P12.

### 2.6 R6: Build time versus runway

**Description.** The evidence (M1, M1R and the first measurable deliverable) arrives after the money runs out.

**Cause.**
- The value loop is not built.
- The verifier, the fault-injection harness and the production gateway are products the spec does not list as deliverables.
- PA-021 and PA-026 are HIGH severity and have no local analogue (`local_reference_check: null` in the catalog).
- Calendar floors: shadow needs at least one full close, and a monthly cadence allows about 6 closes in 180 days (D5).
- US tax season (February to April 15) overlaps the shadow period.
- Two hires sit on the M1 path.
- Fixture durations are upper bounds, not schedules.
- "An initial 90-day supervised reference deployment is a planning hypothesis contingent on access and staffing" (spec §26 L418).

**Likelihood and impact.** High; high.

**Early-warning indicators.**
- Milestone attestation dates against windows: PA-001 by week 14, M1R by week 24 (build ledger plus verifier).
- Time to first verified event, split into Plumb-controlled and dependency time.
- Hiring dates: security/platform engineer by about week 4, verification engineer by week 6 (D12).
- Sandbox and egress slip of more than 4 weeks, which triggers the D4 fallback.
- Open dependencies by resolver and age.

**Mitigations.**
- Wrap the existing policy kernel rather than rewriting it (E05-S01, E05-S02, E05-S03).
- Follow the vertical-proof order (spec App. A.7 L586).
- Keep certified operations narrow and published per operation (E02-S06).
- Make the security and verification hires early (D12).
- Cap concurrency at 3 builds (E05-S08).
- Windows start on gate exit.
- The D4 fallback: attest M1 on PA-001 plus the rest of the bundle, and move the generated-path requirement to tenant 3.

**Kill or pivot criterion (pre-registered, D11).** PA-001 has not passed on tenant 1 by week 14: cut scope to one ledger and one document store instead of adding platform. M1R has not passed by week 24: the day-180 memo must choose between a reduced-scope extension and the R1 pivot.

**Owner (proposed).** Founder. The tech lead owns build scope.

**Linked ids.** PL-019, PL-042, PL-061, PL-063; PA-001, PA-019, PA-021, PA-026; PA-P07, PA-P14.

### 2.7 R7: Data rights and access block the evidence

**Description.** Grants, vendor approvals or legal limits block the sources the evidence depends on: mail history for M3-lite and the duplicate-chase baseline, TRAIN for M2, and tax-adjacent folders.

**Cause.**
- Partners may refuse mailbox scopes.
- Spec requires that Plumb "must not bypass vendor approvals, MFA, licensing or unavailable endpoints" (spec §5 L106).
- Google's Workspace policy restricts "uses beyond the specific user's personalized model", and "Vendor terms can change" (spec §21 L328).
- IRC 7216 governs tax-return information shared with third-party AI systems (secondary compliance commentary; verify with counsel).
- 53% of small firms demand no model training on their data. This comes from a small, self-selected survey and is directional only (Uku 2026); the decision record states it without the caveat.
- Package has: SERVE is never enforced. No fixture envelope grants SERVE, yet every fixture plan passes. The `SourceGrant` contract has no `revoked_at` ([envelope.py](../plumb/contracts/envelope.py)), so revoking a single grant is not modeled.

**Likelihood and impact.** Medium; Medium-High. It delays M3-lite and the duplicate-chase baseline, and blocks M2.

**Early-warning indicators.**
- Source grants by source and purpose: refused requests, and the count of TRAIN grants.
- Vendor approval status against the timeline known at the P0 exit (E02-S08).
- Outcome mix per authorized goal: dependency days with the vendor as resolver.
- Status of the counsel opinion.
- Share of in-scope folders removed by the tax-return exclusion.

**Mitigations.**
- Start vendor app reviews in week 0 (E02-S08).
- Purpose grants in the DPA and envelope (E18-S01).
- TRAIN off by default and opt-in per source (E18-S08).
- Exclude tax-return information (E18-S02).
- Enforce SERVE before the first shadow (E18-S04).
- A cross-tenant reuse guard (E18-S05).
- A counsel opinion before the first signature (D9).
- A forwarding-address intake as the mail fallback (E08-S08).

**Kill or pivot criterion (pre-registered, D11).** At least 2 of 5 partners refuse mailbox scopes, or vendor approval for mail scopes is not granted by M3-lite: run on document store plus ledger, with a forwarding-address intake for mail. Fewer than 2 tenants grant TRAIN: M2 stays deferred, which is not a company kill. Counsel finds IRC 7216 blocks monthly-close sources at most ICP firms: re-scope the sources or the ICP.

**Owner (proposed).** Founder, with fractional counsel and the fractional compliance lead (D12). The tech lead owns enforcement (E18).

**Linked ids.** PL-023, PL-040, PL-041, PL-053; PA-008, PA-012; PA-P05, PA-P15.

---

## 3. The six unresolved experiments of spec §27

Spec §27 (L442), quoted exactly: "Experiments that remain necessary: whether richer observation materially improves deployable discovery; the rate at which inferred input/target joins are correct; whether agents can adapt existing adapters cheaply enough; the amount of domain clarification per workflow; the reliability of generated failure handling; and the rate of maintainable reuse across customers. None of these is resolved by the existence of a coding-agent API."

Every experiment below has a pre-registered threshold (section 1). All thresholds are hypotheses. With at most five tenants in the cohort, every reading is a directional trend, not a statistical result (D11 rejected 10 or more tenants as unsupportable). The reading rules in section 1.2 apply.

| # | Spec wording (exact) | Risk | First read | Decision it informs |
|---|---|---|---|---|
| 1 | "whether richer observation materially improves deployable discovery" | Scope and cost (D3) | P3 | Whether capture enters the roadmap after M5 |
| 2 | "the rate at which inferred input/target joins are correct" | R7 (M2 rights) | P5, if grants exist | M2 go/no-go |
| 3 | "whether agents can adapt existing adapters cheaply enough" | R1 | P3 | PL-063 platform verdict; "automatically constructed" claim |
| 4 | "the amount of domain clarification per workflow" | R3 | P4 (tenant 1) | Self-discovery claim; template pivot; wedge kill |
| 5 | "the reliability of generated failure handling" | R4 | P4-P6 | Generated versus template workflows; Draft and Send go |
| 6 | "the rate of maintainable reuse across customers" | R1 | P3; M5 (starts in P6) | M5 and M6 ("not a forked engine") |

### 3.1 Experiment 1: "whether richer observation materially improves deployable discovery"

| Element | Plan |
|---|---|
| Hypothesis | For monthly-close evidence readiness, structured sources (APIs plus 12-24 months of history) are enough for deployable discovery. Richer observation adds little. |
| Cheapest credible test | The D11 proxy (E12-S06). During tenant 2 and 3 onboarding, compare discovery from APIs and history alone against the same plus a 2-hour structured shadowing session. No screen capture is built. |
| Metric | Deployable, feasibility-passing opportunities per firm in each arm. Shadowing minutes are logged as DOMAIN_CLARIFICATION. |
| Threshold (hypothesis) | Shadowing adds at least 1 deployable, feasibility-passing opportunity per firm, in both firms |
| Decision it informs | Whether capture belongs in the product. Capture costs about 34.6 GB/day raw per 100 employees (spec §24 L378), and the spec prefers historical data and API events "when sufficient" (spec §5 L110). |
| Phase | P3 (M1R onboarding); reported in the day-180 packet |
| If the hypothesis fails (threshold met) | Plan a consented, event-triggered capture pilot after M5, with the enrollment controls spec §5 (L110) requires: scope, pause, exclusions, retention and a coverage report |
| If it holds | Keep capture out. A second route stays open (D3 revisit trigger): if more than 20% of obligations stay UNKNOWN after two closes because of off-system handoffs, run a bounded, event-triggered capture experiment. |
| Limits | Two firms. The 2-hour session is a proxy for capture, not capture itself. |

### 3.2 Experiment 2: "the rate at which inferred input/target joins are correct"

| Element | Plan |
|---|---|
| Hypothesis | On tenants that grant TRAIN or EVALUATE, Plumb's inferred joins between transaction or document context and the accountant-confirmed classification are precise enough to build a learning dataset without heavy expert review |
| Cheapest credible test | A PA-012-style sample of 100 input/label pairs reviewed by an accountant (D5, D11). Explicit accept and correct events come from the review surface's prospective correction collector (E14-S05). No training job is needed to measure join precision. |
| Metric | Audited join precision on the 100-pair sample. Client/period attribution accuracy is a separate quality metric (missing-item quality) and is not this read-out (D11). |
| Threshold (hypothesis) | At least 90% join precision (D5; the domain expert ratifies) |
| Decision it informs | M2 go/no-go. All four D5 gates are required: join precision of at least 90%; TRAIN grants on at least 2 tenants; at least 500 explicit accept/correct events; and either classification errors account for at least 25% of review minutes, or a candidate comparison shows a reviewer-time gain. |
| Phase | The M2 go/no-go memo in P5 (E21-S01), if grants and events exist by then; otherwise after day 180 |
| If it fails | M2 stays deferred. The baseline workflow continues without training (spec App. B L624: "The baseline workflow can operate while useful training data accumulates"), and the collector keeps accumulating explicit decisions. Not a company kill. |
| Limits | The measurement is not a PA-012 pass. PA-012 itself is the gated M2 evidence and is not claimed in P0-P6 ([roadmap](04-roadmap.md) section 5). |

### 3.3 Experiment 3: "whether agents can adapt existing adapters cheaply enough"

| Element | Plan |
|---|---|
| Hypothesis | Adapting certified transport plus agent-generated semantic mapping to a new firm's stack takes less audited engineering with each tenant, including for a swapped provider |
| Cheapest credible test | M1R on tenants 2 and 3, right after M1, with designed variation. Tenant 2 changes folder structure and chart-of-accounts conventions; tenant 3 swaps one provider, forcing a DECLARATIVE_CONFIG or GENERATED_CODE path (PA-P01). It is cheaper than waiting for the M5 slot in the spec §26 table, because it needs only the collection path (D5). |
| Metric | EIH/VD per tenant in onboarding order, failed, blocked and abandoned attempts included; hands-off build rate; repair attempts per verified deployment; platform-investment hours triggered, shown beside the metric and never netted |
| Threshold (hypothesis) | Target: tenant 3 at or below 50% of tenant 1. R1 review at 75% or more. Hands-off build rate of at least 50% on tenants 2 and 3. |
| Decision it informs | The PL-063 platform verdict. Whether Plumb may say "automatically constructed" (D8 item 7). Pace of tenant 4-5 onboarding (D9). |
| Phase | P3, in the R1 checkpoint memo; repeated in the day-180 packet |
| If it fails | The R1 response (section 2.1) |
| Limits | Three tenants. A pass in progress is possible under reading rule 2. The audit must find zero unrecorded manual work, or the reading is void. |

### 3.4 Experiment 4: "the amount of domain clarification per workflow"

| Element | Plan |
|---|---|
| Hypothesis | Per workflow, domain clarification fits the D6 budget: at most 5 DOMAIN_CLARIFICATION questions at onboarding, at most 2 new questions per close after close 1, and zero repeat asks |
| Cheapest credible test | No separate experiment. Count questions and minutes in the focused-question queue and the effort ledger during M3-lite on tenant 1 (P4), then on tenants 2 and 3. Engagement-checklist templates (E13-S02) are the intervention being tested. |
| Metric | Interruption load: DOMAIN_CLARIFICATION questions and minutes per workflow, the decay ratio of close n against close 1, and the repeat-ask rate |
| Threshold (hypothesis) | Within budget. R3 fires on tenant 3 under the section 2.3 criterion. |
| Decision it informs | Whether "Plumb discovers and implements" holds in this vertical, or Plumb moves to a fixed template with firm-level defaults and a narrower ICP. If owner minutes exceed measured accountant savings, the wedge is killed. |
| Phase | P4 exit for tenant 1 (decision record, P4 exit evidence); P5-P6 for tenant 3's workflow, which may be pending at day 180 (section 2.3) |
| If it fails | The R3 response (section 2.3) |
| Limits | Tenant 1's reading is a baseline, not the trigger. Questions answered once and stored as conventions (PA-004) count once. |

### 3.5 Experiment 5: "the reliability of generated failure handling"

| Element | Plan |
|---|---|
| Hypothesis | After bounded repair, generated workflow logic handles the protected Appendix B failure cases: wrong client, ambiguous period, already-received document, corrected statement, duplicate request, expired permission, provider timeout after send, changed approval and stale source |
| Cheapest credible test | Run the protected verifier before any external effect exists. In sandbox in P4: PA-003, PA-004, PA-006, PA-008, PA-010, PA-011. Against the sandbox gateway in P5: PA-005 and PA-009. PA-007 needs concurrent ACTIVE and CANARY releases, so it cannot pass before the Send canary (earliest close around July 2027, after the P6 window). The fault-injection harness (E10-S03) makes these cases runnable. |
| Metric | Protected failure-case pass rate, per tenant, on generated workflow logic. A certified template workflow is reported separately, so template passes are not counted as generated passes. |
| Threshold (hypothesis) | More than 10% of the cases failing across two tenants triggers R4 |
| Decision it informs | Whether Plumb keeps generating workflow logic or uses only certified template workflows. Draft and M4-accounting go/no-go at day 180. |
| Phase | P4 (tenant 1, sandbox); P5 (gateway sandbox; second tenant's workflow); P6 (production gateway and Draft canary); Send canary from about July 2027 |
| If it fails | Stop generating workflow logic, use only certified template workflows, and never claim "generated workflows" (section 2.4) |
| Limits | The "across two tenants" reading needs a second tenant's workflow, which starts in P5, so it may land after day 180. Any HIGH-severity failure blocks activation anyway (PL-061), whatever the rate. |

### 3.6 Experiment 6: "the rate of maintainable reuse across customers"

| Element | Plan |
|---|---|
| Hypothesis | Artifacts built for one firm (mappings, collection templates, later workflow components) are reused unchanged by later firms on the same engine, and keep working without per-tenant forks or growing repair |
| Cheapest credible test | Digest comparison of each new tenant's deployment against the registry at M1R (collection path, tenants 2 and 3), then at M5 (full workflow, tenants 2-4) (E07-S07). **Proposed addition:** a maintainability read, using post-verification OPERATIONAL_REPAIR minutes per deployed component (the split view in [metrics](06-metrics.md) section 2.1) over each component's first months in operation. |
| Metric | Artifact reuse rate and fork count; post-verification OPERATIONAL_REPAIR minutes per deployed component (proposed) |
| Threshold (hypothesis) | Reuse of at least 60% by tenant 3, with fork count 0; any fork triggers R1. The decision record sets no maintainability threshold. This document proposes setting one at the M1 audit, once real repair data exists, and not before. |
| Decision it informs | M5 ("Falling manual implementation effort with stable quality and value", spec §26 L413) and M6 ("not a forked engine", spec §26 L414). How much to invest in the registry. |
| Phase | P3 first read; full read at M5, which starts in P6 and may finish after it |
| If it fails | The R1 response (section 2.1) |
| Limits | Reuse at deployment time is not the same as maintainability over time. The decision record's metric reads only the first, which is why the repair read above is proposed. |

---

## 4. Assumption map

Each assumption names the evidence available today, with its source, and the test that would confirm or break it. Market evidence comes from the research notes; vendor-run surveys and secondary sources are flagged, and URLs are in the Sources section. Phases are hypotheses.

### 4.1 Desirability

| # | Assumption | Evidence today (source) | Test | Phase | Risk |
|---|---|---|---|---|---|
| A-D1 | Mixed-stack firms of 10-40 staff feel month-end evidence pain strongly enough to act | Getting documents from clients is the #1 workflow issue (Financial Cents 2025, 816 professionals; vendor survey). About 10 apps per firm and 48% "functional but fragmented" (Intuit 2026, n=725; vendor survey). Hiring is the #1 issue for 11-30-professional firms (AICPA PCPS, June 2026). | D1 trigger: at least 30% of the first 25 qualified calls have materially mixed stacks, and those firms show more pain or willingness to pay than single-ledger firms | P0-P1 | R5 |
| A-D2 | Firms want an agent to take evidence chasing and preparation off their staff | 68% would hand chasing to an AI agent first, but zero firms fully trust AI (Uku 2026; small self-selected sample, directional) | Paid LOIs; partner retention through the first shadow close | P1-P5 | R5 |
| A-D3 | Reviewing accountants value a provenance-backed ready-for-review package more than a checklist | None direct. An inference: incumbents sell chase-and-remind, but none produces cross-stack packages that separate unknown from confirmed absence (market-accounting notes) | D2 trigger: packages opened for at least 50% of in-scope client-periods, and accountant minutes falling at least 25% against baseline in the first two shadow closes | P4-P5 | R5 |
| A-D4 | Partners accept preparation-only (no sending) until after day 180 | 62% require human approval before anything is sent or filed (Uku 2026, directional), which supports gating. Chasing is also the most-wanted task, which cuts the other way. | D2 and D3 triggers: at least 2 partners say they will not continue without sending; fewer than half of active bookkeepers use the readiness ledger weekly | P2-P5 | R5, R4 |
| A-D5 | Verification and a visible labor ledger persuade buyers more than autonomy claims | Trust in fully autonomous agents fell from 43% to 27% (Capgemini; page undated, about July 2025). Trust and accuracy is a top barrier for 21% (Financial Cents 2026; vendor survey). Fear of errors is cited by 35% (Accounting Seed, n=128). | D8 message test across at least 200 ICP contacts. If outcome-led framing gets more than 2x the qualified-meeting rate, lead with the outcome. | P0-P2 | R5 |
| A-D6 | Firm owners will grant read OAuth, name a domain owner with about 2 hours a week, run a 2-week baseline study and allow anonymized ledger publication | None. These are qualify-out criteria (D1 item 9) | Selection funnel conversion (D9) | P0-P1 | R3, R7 |

### 4.2 Viability

| # | Assumption | Evidence today (source) | Test | Phase | Risk |
|---|---|---|---|---|---|
| A-V1 | Firms will pay $15 per active client-month for Prepare, with a $500 firm minimum | Per-client close tools: Double $10/$25/$50 per client-month (secondary listings; the vendor page confirms only the per-client model); Xenett about $7.5 (AI Review) or $10 (Workflow), plus a $15 accruals-and-AI add-on; the Financial Cents close add-on $5. Cost is the least-cited adoption barrier at 6% (Financial Cents, Aug 2026; vendor survey). | Paid pilot of $1,500-$3,000 invoiced at signature; at least 2 paid LOIs from about 30 qualified conversations; at least 2 of the first 4 partners convert at $15 or more; price test at $15, $25 and $35 plus a per-accepted-package unit (D7) | P1; P5-P6 | R5 |
| A-V2 | Measured value is at least 3x price, about $45 per client-month | None. No reputable primary source for hours per client-month (market-accounting notes) | Month-0 time study (E14-S01) against shadow-close timing; the PA-P12 economic-result attestation | P5 | R5 |
| A-V3 | Fully loaded cost to serve falls to at most 2x price by tenant 4, or trends down | None. Plumb labor has not been measured. | Fully loaded cost per verified deployment, and gross margin per active client-month (E20) | P5-P6 | R1, R5 |
| A-V4 | The ICP pool is large enough after its filters (10-40 staff, at least 60% recurring CAS revenue, at least 50 recurring clients, mixed stack) | Census SUSB 2022 (employer firms only): about 13.4k CPA firms with 5-19 employees, and about 3.3k CPA and other-accounting firms with 20-99 (derived from the Census table). The 60% CAS filter is untested and may shrink the pool, because most small CPA firms do both CAS and tax (dissent record). | Qualification rate in the funnel; at least 25 qualified conversations by week 8 (D9) | P0-P1 | R5 |
| A-V5 | Partners convert to paid annual after one full close in ACTIVE, and renew | None | Conversion under the Prepare-tier promotion path (founder decision 17, to ratify): SHADOW for at least one full close, CANARY on client-periods whose accountants use the packages in their real review, then ACTIVE; conversion after one full ACTIVE close at or above the correct-package threshold. The day-180 packet records tenant 1's evidence to date; its conversion is expected in P6. The earliest credible renewal decision is about three closes after connection (D5). | P6 | R5 |
| A-V6 | Firms accept native-setting outcomes billed at the same rate (D7) | None | PA-P11 cases; billing feedback at conversion | P6 | R5 |

### 4.3 Feasibility

| # | Assumption | Evidence today (source) | Test | Phase | Risk |
|---|---|---|---|---|---|
| A-F1 | Certified transport through a contract-tested substrate (Nango is the candidate) covers tenant 1's exact document-store and ledger-metadata operations | Spec requires: substrates are candidates and "each adapter must pass Plumb's contract tests before use" (spec §3 L84). Nango says its Management MCP is "still growing toward the full public API" (vendor-reported). The registry is synthetic. | Substrate contract tests (E02-S05) and SANDBOX_TESTED probe receipts on tenant 1's real accounts (E02-S04) | P1 | R1, R6 |
| A-F2 | Tenant semantics (folder conventions to client, period and obligation; chart-of-accounts conventions) can be agent-generated, with zero ENGINEERING_INTERVENTION in the attested run | None. The accounting fixture generates no adapter code. | PA-001 under the D4 conditions (E07-S03) | P2 | R1 |
| A-F3 | Partner providers meet the catalog's assumptions: webhooks plus overlap polling (PA-005), mail request-id lookup (PA-009), provider sandboxes (PA-002) | Catalog preconditions only | Qualification calls and M0 probes | P0-P1 | R4, R6 |
| A-F4 | Ledger authorization is not granted per client company, or still fits within 4 hours of CUSTOMER_AUTHORIZATION per firm | Unknown | M0 probes; CUSTOMER_AUTHORIZATION minutes per firm; PA-P08 | P1-P2 | R3 |
| A-F5 | A production action gateway can be built and crash-tested in sandbox by day 180 | Package has a SQLite simulation only (spec §16 L264), and its RELEASE machine cannot pause a CANARY release | P5 gateway sandbox crash tests (PA-005 dispatch-time re-check, PA-009, PA-015); pause and kill from SHADOW and CANARY (E16-S03) | P5 | R4, R6 |
| A-F6 | A narrow release executor can earn real PRODUCTION_VERIFIED receipts for release.create and release.activate_shadow before any tenant shadow | Package has: `required_maturity` in [plan_checker.py](../plumb/checker/plan_checker.py) puts release.* at PRODUCTION_VERIFIED | Platform qualification run (E16-S02) | P4 | R6 |
| A-F7 | The team can stand up the verifier and the fault-injection harness by P2 | The harness is a product the spec does not list, and PA-021 and PA-026 have no local analogue (catalog) | E10-S01 and E10-S03 by the P2 exit; verification hire by week 6 | P1-P2 | R6 |
| A-F8 | A 12-24 month backfill completes within provider rate limits | The fixture's 21,600 s is an upper bound; real time is unmeasured | Tenant 1 backfill and reconcile (E08-S02, E08-S03) | P2 | R6 |

### 4.4 Usability

| # | Assumption | Evidence today (source) | Test | Phase | Risk |
|---|---|---|---|---|---|
| A-U1 | The firm owner completes onboarding authorization in at most 2 hours of CUSTOMER_AUTHORIZATION and at most 4 owner-hours in the first 30 days | None | Effort ledger at onboarding (D6 budget) | P1-P2 | R3 |
| A-U2 | An owner with no AI background understands envelope fields (effect classes, processors, regions) from a plain-language implementation card | None. The spec gives no envelope UX (research notes: spec-1-7). Spec App. A.6 describes the card's content. | Card comprehension in onboarding sessions; repeat-ask rate 0 (E04-S02, E11-S03) | P1 | R3 |
| A-U3 | Accountants record explicit accept, correct or amend without extra work; sign-off lag stays under 2 weeks; "material" is coded consistently | Spec App. B (L624): "Lack of an edit is weak evidence unless the workflow establishes explicit reviewed acceptance" | E14-S03 and E14-S04. D10 trigger: lag above 2 weeks, or more than 20% disagreement on "material" in a double-coded sample | P4-P5 | R3 |
| A-U4 | Review minutes per package stay below baseline assembly-plus-review minutes | None | Review timing against the month-0 study (E14-S06) | P4-P5 | R3, R5 |
| A-U5 | The blocked-dependency card gets dependencies resolved without Plumb staff calls | None | Median days in dependency by resolver; Plumb support minutes per tenant (E11-S02) | P1-P2 | R3, R6 |
| A-U6 | Bookkeepers adopt one shared obligation owner and stop chasing outside Plumb once requests ship | Spec App. B (L614): "A per-person list of emails is insufficient." Plumb cannot stop emails sent outside it (research notes: appendices). | Draft-tier request data against the historical duplicate-chase baseline | P6 | R4 |

### 4.5 Legal

| # | Assumption | Evidence today (source) | Test | Phase | Risk |
|---|---|---|---|---|---|
| A-L1 | IRC 7216 tax-return information can be kept out of monthly-close sources through folder and label exclusions | Secondary compliance commentary only, not IRS guidance or legal advice (my-cpe) | Counsel opinion before the first signature; exclusion enforcement (E18-S02) | P0-P1 | R7 |
| A-L2 | Google and Microsoft app review for mail and document scopes completes before M3-lite | Spec §5 (L106) and §21 (L328). The specific verification requirements for restricted scopes are not sourced in the research notes. | Vendor review tracking from week 0 (E02-S08); timelines known at the P0 exit | P0-P4 | R7 |
| A-L3 | Partners consent to anonymized labor-ledger publication, failures included | None | D9 selection criterion; contract clause | P1 | R2, R5 |
| A-L4 | Contracts permit reuse across tenants of derived engineering artifacts stripped of customer data | Spec App. A.5 (L570): "Cross-customer examples, labels and weights require their own permitted-use basis." Reusable patterns are kept separate from customer records. | Counsel review; reuse-guard scanner (E18-S05) | P1-P3 | R1, R7 |
| A-L5 | Partners grant an explicit SERVE purpose before the first shadow | Package never enforces SERVE (research notes: implementation-reality) | DPA clause (E18-S01); plan-checker enforcement (E18-S04) | P4 | R7 |
| A-L6 | Partners accept the revocation semantics: cached grants and queued dispatches invalidated within one minute, and a provider-accepted action keeps its receipt | PA-008 states the one-minute invalidation. Spec §17 (L276) says only "promptly" and describes the race. | PA-008 in P4; PA-P05 in P6; DPA review by counsel | P1-P6 | R4, R7 |
| A-L7 | No further regulatory obligation blocks the pilots | Service-provider safeguards terms (for example the FTC Safeguards Rule) and SOC 2 requests are plausible, but appear in neither the spec nor the research notes (dissent record). They stay "counsel or compliance to confirm". | Counsel; partner security reviews | P0-P1 | R7 |

---

## 5. Open product questions

Each question has a recommended default (proposed) and an owner. The default applies until the founder ratifies or changes it. Q14 records a head-of-product decision awaiting ratification, not a proposal. "Decide by" is the latest phase in which the answer is still cheap.

| # | Question | Why it matters | Recommended default (proposed) | Owner | Decide by | Linked ids |
|---|---|---|---|---|---|---|
| Q1 | Who decides payload supersession for wording changes on the same effect slot, and can a standing policy pre-authorize some classes? | Spec requires that the same effect slot is not redispatched with a changed payload "without an explicit supersession decision" (spec §16 L254). Without a standing policy, every template edit becomes an interruption (R3). | A standing supersession policy covers wording-only edits within an approved template class (D6). "Wording-only" is a deterministic diff rule: no change to recipient, item list, client, period, obligation, amounts, identifiers or attachments. Anything else is a template-class change: the policy version bumps and needs one policy re-approval (PL-040). The gateway enforces it at dispatch; tested by PA-P03. | Founder (policy) with the domain expert (template classes); tech lead (enforcement) | P4 | PL-037, PL-039, PL-040; PA-006, PA-010; PA-P03 |
| Q2 | What does the correction UX look like, including an impact preview? | PL-011 requires an impact set and scoped, reversible corrections (spec §6 L118). A correction without a preview can silently move documents between clients. | Every correction shows its impact set before it applies: facts, packages, conventions and plans affected. Corrections are scoped to a named context (client, source, period range), never global, and keep their history. Firm-staff corrections are DOMAIN_CLARIFICATION; Plumb-staff corrections on tenant data are ENGINEERING_INTERVENTION. (E09-S04) | Product engineer, with the fractional product designer | P2 | PL-010, PL-011; PA-003, PA-004 |
| Q3 | How does discovery-driven collection get purpose-justified? | Collection "must be justified by the active customer use case" (PL-023, spec §11 L184), and the learning task comes before the data (PL-026, spec §12 L198). This conflicts with "collect everything, discover later". | No speculative collection. Discovery uses INSPECT on metadata and representative records only. Every collection names the OpportunitySpec and objective it serves, and a new source or purpose needs a new DATA_USE decision. The vertical opportunity library (D3) predefines purposes for the wedge. Learning-data discovery waits for the M2 gates and a written task definition. (E08-S01, E18-S03) | Founder with counsel; tech lead (enforcement) | P1 | PL-012, PL-023, PL-026, PL-053 |
| Q4 | What is the revocation-to-stop SLO? | Spec §17 (L276) says approval expiry "must stop future actions promptly" without a number. Partners will ask in security reviews. | Cached grants and queued dispatches invalidated within 1 minute (as in PA-008, and the D9 contract term). Collector PAUSED or DEGRADED within the 5-minute health deadline. Zero provider calls under revoked authority. In a race, the receipt is kept and remediation opened (PA-P05). Offered as a customer commitment only after PA-008 passes in production. Single-grant revocation needs a `revoked_at` on SourceGrant (E04-S03, E15-S04). | Tech lead; founder for the contract | P1 (DPA) | PL-040, PL-041, PL-053; PA-008, PA-014; PA-P05 |
| Q5 | What does the customer see when the gateway fails closed? | Spec §24 (L380) proposes "policy-gateway failure closed for writes". Customers will read held effects as an outage. | Reads and preparation continue while writes are held. Each held effect shows "held, not sent", the reason, the affected client-periods, who can act and the expected resume. Held items are re-checked at dispatch (the PA-005 re-check) and expire with their approval rather than flushing late. A Plumb-side hold is never billed (D7). Gateway availability is tracked internally, separately from the 99.9% control-plane target. | Product engineer; tech lead | P5 (before Draft) | PL-025, PL-037, PL-047; PA-005, PA-011 |
| Q6 | Which labor data is customer-facing and which stays internal? | PL-059 and PL-062 require measuring Plumb's own labor. The ledger is both a proof point (D8) and commercially sensitive. | The firm sees its own full ledger in all five categories, including Plumb engineering and repair minutes and failed attempts (E11-S05). Loaded rates, salaries, named staff and other tenants' data stay internal. Public anonymized per-tenant EIH/VD is published only after a milestone audit, under the contract's publication right (D9). | Founder | P1 (contract) | PL-003, PL-059, PL-062 |
| Q7 | What may be reused across tenants? | Spec App. A.5 (L570): cross-customer examples, labels and weights need their own permitted-use basis. Replication (R1) depends on reusing engineering patterns. | No cross-tenant use of examples, labels or weights. Reuse of derived engineering artifacts stripped of customer data (mapping patterns with applicability constraints, adapter tests, failure fixtures), granted by contract. Promotion to the registry needs a scanner check and review by the verification engineer (E18-S05). | Counsel; integration engineer | P1 | PL-052, PL-053 |
| Q8 | How is the firm's client measured, given it is not a principal? | The client receives every request, but the spec measures only duplicate requests (spec App. B; research notes: appendices). | Measure client-request integrity (duplicates, stale and wrong-client requests), requests per client per close, and days to receive. No tracking pixels or read receipts. Client identities never appear in telemetry (PL-060). The historical baseline is labeled non-causal. | Product engineer; domain expert | P4 | PL-039, PL-059, PL-060; PA-005, PA-007 |
| Q9 | What is the IRC 7216 scope? | Tax-return information shared with third-party AI systems carries consent obligations (secondary commentary; verify with counsel). | Exclude tax-return information from v1 source grants through folder and label exclusions and PL-053 purpose checks. The firm warrants it will not route such data. Counsel opinion before the first signature. Relax only for monthly-close sources that counsel confirms are out of scope (D9). (E18-S02) | Founder with counsel | P0-P1 | PL-023, PL-053 |
| Q10 | Who sets task-specific thresholds, and through what surface? | Spec §24 (L382): "No universal 99% score". Each release sets its own denominators and thresholds, and the release gate cannot work without an owner. | The domain expert authors threshold sheet versions, ratified with an external technical advisor. Stored as a versioned artifact the build team cannot edit (protected bundle store, E10-S02). Changes apply prospectively (section 1.1). | Plumb domain expert | P0 | PL-044, PL-061 |
| Q11 | What exactly is an obligation, and an obligation epoch? | Effect-slot identity is "tenant + case + obligation epoch + operation + target" (spec §16 L260). If the domain model is wrong, deduplication is wrong. | Obligation = client + period + one required item from the engagement checklist. Epoch = one consolidated request cycle per close; follow-ups within the cadence cap stay in the epoch. A deliberate new reminder opens a new approved epoch. | Domain expert; tech lead | P4 | PL-037, PL-039; PA-007 |
| Q12 | What do "block" and "degrade" mean per obligation when coverage is missing? | PL-025: workflows "MUST block or degrade explicitly", and a stopped collector must never make an obligation look satisfied or unsatisfied (spec §11 L188) | Missing coverage shows Presence UNKNOWN with fact status STALE, never CONFIRMED_ABSENT. The package is marked "coverage incomplete" with the affected sources, and request steps block (PA-011). A client-month where a Plumb-caused DEGRADED collector covered more than 20% of the period is credited (D7). (E08-S09) | Product engineer; domain expert | P2 | PL-010, PL-025; PA-011; PA-P17 |
| Q13 | Should an accounting write ever follow the package? | Spec §15 (L248): "Whether an accounting write follows is an explicit policy choice." | No posting and no FINANCIAL_COMMITMENT. Any future posting is a new envelope decision with accountant approval, never a silent widening. | Founder | Not planned | PL-005, PL-035 |
| Q14 | How is wiring done by the customer's own staff categorized? | Spec App. B (L652): "If a person manually wires the integrations ... record that labor." The record's D6 rubric limited ENGINEERING_INTERVENTION to Plumb staff. | Decided by the head of product as a flagged amendment to D6 (founder decision 18, to ratify): ENGINEERING_INTERVENTION covers implementation work by any person, Plumb or customer staff. Customer wiring is logged under the customer principal, counted in EIH/VD and triaged as an interruption-budget defect ([metrics](06-metrics.md) section 6.2). The contracts still need a Plumb-staff principal type (gap). | Founder | P0 (rubric freeze) | PL-002, PL-003 |

Related questions answered elsewhere: how a Prepare workflow becomes ACTIVE (founder decision 17), where the review surface lives, who confirms the backfill watermark, and what establishes CONFIRMED_ABSENT ([MVP scope](03-mvp-scope.md) section 10). Approving the reminder policy is CUSTOMER_AUTHORIZATION (founder decision 18). The deployment unit and the abandonment rule are open in [metrics](06-metrics.md) (open questions).

---

## 6. Watch items

### 6.1 Operating watch items

| Item | Why it matters | Signal | Owner | Response |
|---|---|---|---|---|
| Vendor app review and consent for mail and document scopes (Google Workspace, Microsoft 365), and ledger app registration | Spec requires: Plumb "must not bypass vendor approvals, MFA, licensing or unavailable endpoints" (spec §5 L106). Workspace terms restrict uses beyond a user's personalized model and can change (spec §21 L328). Mail history is on the P4 critical path. | Approval timelines known at the P0 exit; status reviewed weekly (E02-S08); the vendor-terms version recorded per data-use decision (E18-S06) | Fractional compliance lead | Start in week 0 (Oct 5, 2026). Not granted by M3-lite: the R7 fallback |
| US tax season, February to April 15 | Overlaps the P4-P5 shadow period, when reviewing accountants must adjudicate packages (D5) | Partner response latency; review queue age; sign-off lag | Founder | Collect tenant 2-3 grants, clarifications and baseline studies before mid-January; batch review sessions; the 60% CAS-revenue ICP floor |
| Ledger authorization per client company | If QBO or Xero access is granted per client company, onboarding authorization may blow the budget (D1). It also defines account boundaries (PA-P08). | CUSTOMER_AUTHORIZATION minutes per firm in M0 | Integration engineer | Above 4 hours per firm: re-scope the stack (D1 trigger) |
| Fixture envelopes expire 2027-03-31 | Package has: all three envelope fixtures expire then, and the checker returns ENVELOPE_INACTIVE from that date. The accounting envelope and plan are also EU/EUR (`eu-west-1`); the RFQ fixtures are USD (`us-east-1`) and laundry GBP (`eu-west-2`). | CI and demo runs dated near the expiry | Integration engineer | Refresh or clock-pin in P0, alongside re-templating the accounting fixtures to US/USD (E24-S03) |
| Substrate dependencies (Nango, Airbyte, Temporal, Pulumi Automation API) | Candidates only; each must pass contract tests (spec §3 L84) | Contract-test results; vendor deprecations | Integration engineer; tech lead | A failing substrate keeps its operations at DOCUMENTED |

### 6.2 Competitive and market moves

Dates and claims come from the research notes, checked against sources dated before Oct 4, 2026. Capabilities are as described by vendors and were not independently tested. Several 2026 launches may not yet be generally available. The founder runs a monthly scan, and any move that bears on an R5 trigger goes to the weekly metrics review.

| Move (date) | What was announced | Risk it feeds | What we watch for | Our response |
|---|---|---|---|---|
| Karbon Kai, early access (June 3, 2026) | An "AI coworker" with agentic workflows, "agentic period close checks" and a public MCP server; Kai pricing not disclosed (vendor-reported) | R5 | General availability; whether close checks reach evidence outside Karbon (document stores, ledger detail, mail history) | "Keep your PM tool; Plumb makes your whole stack work together and proves it" (D8). Integrate through Karbon's MCP server. |
| Xero JAX, Partner Hub and XeroForce (announced at Xerocon London July 9, 2026; reported Aug 20, 2026) | Document Requests that chase clients, send reminders and match documents to transactions; month-end readiness view; XeroForce custom agent builder with a month-end agent; pricing not disclosed (vendor-reported via trade press) | R5 | Pricing; reach beyond Xero data; adoption by mixed-stack firms | Qualify out Xero-only firms (D1 item 4), or offer to configure and verify the native features (PL-013). "A Xero-only firm should use Xero" (D8). |
| Intuit QuickBooks AI agents (July 1, 2025) and Intuit Accountant Suite (Oct 28, 2025) | Accounting, Payments, Finance and Customer agents; Books Close at Scale (beta); document sharing "coming soon". UK version free during introduction (Feb 11, 2026); US "no charge during introductory period" per a secondary source. | R5 ($0 price anchor) | End of the free introduction; document collection reaching general availability; cross-ledger support | Qualify out QBO-only firms whose native chase-and-match works. Lead with mixed stacks and verified packages. |
| Basis Series B (Feb 24, 2026) | $100M at a $1.15B valuation; works with about 30% of the top 25 firms and 20% of the top 150; claims 20-50% efficiencies (vendor-reported) | R5 (down-market move) | A small-firm or CAS-focused offer; partner channels; small-firm pricing | Compete on verification, cross-stack implementation and the labor ledger, not model capability |
| Digits Autonomous General Ledger (Mar 2025) and Accounting Agents (June 2025) | Agents that run whole workflows with human pauses; a partner program with wholesale pricing; requires clients to migrate to its ledger (vendor-reported) | R5 | Firm adoption of client migration | Plumb is not a ledger; it works over the firm's existing systems |
| Double (formerly Keeper): rebrand Oct 2025; $6.5M Series A Dec 11, 2025 | 4,000+ North American firms and 150% NDR (vendor-reported); per-client pricing | R5 (price anchor, installed base) | Cross-ledger evidence features; AI chasing | Double plus one ledger is a qualify-out, unless the firm wants Plumb to configure and verify |
| TaxDome Atlas (general availability end of Q3 2026, vendor-stated) | An agent acting across clients, jobs and invoices; tax-intake oriented | R5 (weak) | Expansion from tax intake into monthly close | Tax-only firms are already a qualify-out (D1 item 3) |
| Pilot "fully autonomous AI Accountant" (Feb 4, 2026) | Claims "zero human intervention" (vendor claim) | R5 (end-client substitute); positioning | Small-firm client churn to direct-to-SMB services | Contrast with an audited labor ledger. Plumb never makes this claim (section 7, item 6). |
| Current, formerly Crete Professionals Alliance (rebrand June 2026) | A Thrive-backed roll-up with a reported $500M acquisition plan (June 2025, Reuters via syndication); builds tools in-house; reports 31% tax-prep time savings (vendor-reported) | R5; channel | Whether roll-ups buy rather than build | One optional roll-up slot, off the critical path; promoted to primary channel only if R5 fires (D9) |
| Agent-built integrations commoditizing: Nango Management MCP (Sep 4, 2026), Membrane (Nov 18, 2025), superglue | Coding agents create and deploy integrations; superglue calls itself "an agentic implementation platform" (all vendor-reported) | R5 (differentiation); R1 (a cheaper substrate helps adaptation cost) | Substrate pricing and contract-test results | Differentiate above connectors: verification, the envelope, effect integrity and the labor ledger. Category "verified implementation", not "agentic implementation platform" (D8). |
| OpenAI Agent Builder shutdown (announced June 3, 2026; shutdown Nov 30, 2026) | A model vendor's visual agent builder withdrawn less than 14 months after launch | R6 (substrate churn) | Deprecations by any substrate Plumb depends on | Provider-neutral harness, contract tests and customer-owned specs, tests and adapters |
| Gartner prediction on forward-deployed engineering (Sep 29-30, 2026) | 70% of enterprises will abandon agentic AI built through vendor FDE by 2028; advises IP ownership, knowledge transfer and an exit strategy (via secondary coverage; the Gartner page returned 403) | R2 (buyers will ask whether Plumb is FDE work behind a UI) | Procurement checklists asking for ownership and exit terms | The labor ledger as proof; customer-owned artifacts; pre-agreed exit (D9) |
| FTC Operation AI Comply (law-firm analysis, Aug 18, 2026) | Enforcement against deceptive AI capability claims continues two years in | R2 | New actions against "autonomous" or "AI employee" claims | The never-claim checklist (section 7) |

---

## 7. Never-claim checklist as a risk control

**Control.** The never-claim checklist is a formal gate on what Plumb says outside the team (D8). It mitigates R2 directly, since it stops overstated autonomy reaching the market, and R5 indirectly, since buyers distrust "autonomous" claims (section 4.1, A-D5).

| Element | Definition |
|---|---|
| Owner | Founder (D8, D12) |
| Enforcement point | Before any external artifact leaves Plumb: sales decks and scripts, the website and landing pages, investor updates and data rooms, per-close partner reports, case studies, LOI and contract text, demo scripts, job postings that describe the product, and public anonymized ledger publications. The backlog's definition of done also applies it to anything said about the work outside the team (E24-S02; backlog section 1.5, item 6). |
| Published | P0 (decision record, phased plan) |
| Rule of change | "The never-claim checklist is not relaxed under any result" (D8). Items 7 and 12 change their allowed wording only when the named evidence exists. |

| # | Never claim | Say instead | What changes the allowed wording | Source |
|---|---|---|---|---|
| 1 | That local tests validate models, business outcomes, tenant security, cloud isolation or integrations. Never quote the spec's stale "56 tests" (header table and Appendix C). | "A reference package whose local contract tests (counts in VALIDATION_REPORT.md) check its contracts and checkers. None validates production behavior." Take any count from the current report. | Nothing changes this. Production claims need verifier-attested catalog scenarios. | spec §28 L450; VALIDATION_REPORT.md |
| 2 | Cross-industry autonomy from the three synthetic scenarios | "The contracts represent three domains. Accounting is the only domain in scope." | Per domain only: M6 evidence (PA-P10) for laundry | spec §25 L398 |
| 3 | 90 days as a delivery commitment | "A planning hypothesis contingent on access and staffing", plus each tenant's measured time to first verified event | Never becomes a promise | spec §26 L418 |
| 4 | Product-video results as evidence | Nothing. Do not use them. | Never | spec §29 L492 |
| 5 | An "autonomous close", or posting | "Ready for review" until the accountant signs off; no ledger writes | A new envelope decision for posting, if ever (Q13) | spec §15 L248; spec App. B L652 |
| 6 | "Fully autonomous", "zero human", "no humans needed", "AI employee"; any autonomy claim where hidden human implementation occurred | "Supervised", with the labor ledger shown | PA-027-level evidence for that path (PA-P13 when marketed as autonomously implemented). The banned phrases stay banned. | PL-003; spec §1 L47 |
| 7 | "Automatically constructed" or "generated integrations" before M1R | "Agent-configured certified connectors and agent-built collection" | M1R passes, including the zero-unrecorded-work audit (D4) | D4; D8 |
| 8 | Logo walls; integration coverage taken from the synthetic registry | Coverage per operation at its maturity level ("supported environments v1", E02-S06) | Real probe receipts and attestations, per operation | PL-007, PL-008; capability_registry.json (15 of 25 synthetic records marked PRODUCTION_VERIFIED) |
| 9 | Any hours-saved or ROI figure without a baseline and a denominator; causal claims from historical replay | Accountant minutes against the firm's month-0 baseline, with denominators; the duplicate-chase history labeled "historical, non-causal" | PA-P12 attests realized value before any external value claim | spec §7 L136 |
| 10 | Exact unlearning from trained weights | "Quarantine, retire and stop serving, with lineage evidence" | Never | spec §20 L318 |
| 11 | That a message was not sent after the provider accepted it | "The receipt is retained and a remediation is open" | Never | spec §17 L276; PA-014 (accounting analogue PA-P05) |
| 12 | Claims beyond the released tier, such as "fewer duplicate requests" before Send-canary evidence (earliest Send canary close around July 2027), or the D8 headline's "one owner and one request per missing item" | The Prepare tier's verified outcomes only | Send-canary evidence (PA-P04, PA-007) | D8 item 12 |

**Mechanics (proposed).**

- **Claim register.** Every external quantitative or capability claim is logged with its evidence: an attestation id, an audited ledger window, a metric with its denominator and threshold-sheet version, or, for market facts, the source URL, date and a vendor-reported or secondary flag. A claim with no register entry does not ship.
- **Review.** The founder signs off each artifact. For investor and public materials, the external technical advisor spot-checks the numbers at each milestone audit.
- **Market facts.** Market statistics are never presented as Plumb traction ([metrics](06-metrics.md) section 10.1). Small or vendor-run surveys keep their caveat wherever they are quoted.
- **Violations.** A claim found in breach is withdrawn or corrected and logged as an incident with its root cause. If it overstated autonomy or hid labor, the ledger window behind it is re-audited under R2.
- **Training.** Anyone who speaks to prospects, partners or investors reads the checklist before their first call. Sales scripts are reviewed like any other artifact.

---

## Related documents

- [Decision record](02-strategy-decisions.md): D1-D12, the phased plan, R1-R7 as decided, and founder decisions 17 (Prepare-tier promotion) and 18 (effort-rubric amendment).
- [Product brief](01-product-brief.md): problem, personas and principles.
- [MVP scope](03-mvp-scope.md): what is in and out, and the product's own open questions.
- [Roadmap](04-roadmap.md): phase windows, the day-180 packet and PA-P01 to PA-P19.
- [Backlog](05-backlog.md): the epics and stories cited as mitigations.
- [Metrics](06-metrics.md): definitions of every indicator named here.
- [Market and positioning](08-market-and-positioning.md): category, messaging and competitive framing.
- [Design-partner program](09-design-partner-program.md): selection, contract essentials and exit terms.

## Sources

**Repository (verified for this document on 2026-10-04).**

- [Spec v0.2](../spec/Plumb_Autonomous_Implementation_Specification_v0.2.md): §1 L47, L51; §3 L84; §5 L106, L110; §6 L118; §7 L136; §11 L184, L188; §12 L198; §15 L248; §16 L254, L260, L264; §17 L266, L270, L272, L274, L276; §20 L318; §21 L328; §24 L378, L380, L382; §25 L398; §26 L404, L413, L414, L416, L418; §27 L440, L442; §28 L450; §29 L492; App. A.5 L570; App. A.6 L578; App. A.7 L586, L588; App. B L596, L602, L614, L624, L652, L654; the stale "56 tests" in the header table (L15) and App. C (L662).
- [Requirements index](../spec/requirements_index.json): every PL id cited above, checked against its text; ADR-007, ADR-009, ADR-010.
- [Acceptance catalog](../acceptance/production_acceptance_catalog.yaml): PA-001, PA-002, PA-003, PA-004, PA-005, PA-006, PA-007, PA-008 (one-minute invalidation), PA-009, PA-010, PA-011, PA-012, PA-014, PA-015, PA-019, PA-021 and PA-026 (no local analogue), PA-027; `executed_against_production: false`.
- Code and data: [capability_registry.json](../plumb/registry/capability_registry.json) (synthetic; 25 records covering 23 step types, 15 marked PRODUCTION_VERIFIED), [plan_checker.py](../plumb/checker/plan_checker.py) (`required_maturity`), [machines.py](../plumb/statemachines/machines.py) (RELEASE allows PAUSED only from ACTIVE), [effect_ledger.py](../plumb/ledger/effect_ledger.py) (no pause check; divergent `authority_ref` flagged only), [approval_checker.py](../plumb/checker/approval_checker.py) (`group_missing_authorizations`), [envelope.py](../plumb/contracts/envelope.py) (SourceGrant has no `revoked_at`), [common.py](../plumb/contracts/common.py) (`HumanEffortCategory`, `HumanEffortRecord`, `PrincipalType` with no Plumb-staff type, `Presence`, `FactStatus`), [001_initial_design.sql](../sql/001_initial_design.sql) (`human_effort` table), [accounting plan fixture](../fixtures/plans/accounting_evidence_preparation.json), envelope fixtures for [accounting](../fixtures/envelopes/accounting_evidence_preparation.json) (`eu-west-1`, EUR), [RFQ](../fixtures/envelopes/industrial_rfq_preparation.json) (`us-east-1`, USD) and [laundry](../fixtures/envelopes/laundry_route_preparation.json) (`eu-west-2`, GBP), all expiring 2027-03-31; [VALIDATION_REPORT.md](../VALIDATION_REPORT.md) (local test counts).
- Research notes (strategy panel inputs): spec-1-7, spec-8-16, spec-17-29, appendices, acceptance-and-index, implementation-reality, market-accounting, market-implementation.

**Market (from the research notes; vendor-reported and secondary items flagged).**

- Financial Cents, 2025 State of Accounting Workflow Automation (vendor survey, 816 professionals): https://financial-cents.com/?p=9086
- Financial Cents, State of AI in Accounting and Bookkeeping 2026 (vendor survey, n=486; Aug 2026): https://financial-cents.com/?p=39931
- Uku, AI in Accounting 2026 (small, self-selected sample; directional; fielded May-June 2026): https://getuku.com/ai-in-accounting-report/
- Intuit QuickBooks 2026 Accountant Technology Survey (vendor survey, n=725; July 2, 2026): https://www.cpapracticeadvisor.com/2026/07/02/the-2026-accountant-technology-survey-turning-data-revelations-into-a-firm-of-the-future/185807/
- AICPA PCPS CPA Firm Top Issues Survey (June 23, 2026): https://www.cpapracticeadvisor.com/?p=185547
- Census SUSB 2022 (employer firms; released Apr 10, 2025): https://www2.census.gov/programs-surveys/susb/tables/2022/us_state_6digitnaics_2022.xlsx
- Accounting Seed, State of AI in Accounting 2026 (n=128): https://www.accountingseed.com/resources/the-state-of-ai-in-accounting-2026
- Capgemini Research Institute, AI agents (page undated; about July 2025 per coverage): https://www.capgemini.com/insights/research-library/ai-agents/
- Builder.ai collapse (secondary coverage, May-June 2025): https://www.techspot.com/news/108173-builderai-collapses-after-revelation-ai-since-2017-really-hundreds-engineers.html
- FTC Operation AI Comply, two years on (law-firm analysis, Aug 18, 2026): https://www.hklaw.com/en/insights/publications/2026/08/operation-ai-comply-2-years-later-continued-enforcement
- IRC 7216 and AI tools (secondary compliance commentary; verify with counsel): https://my-cpe.com/blogs/ai-compliance-for-cpa-accounting-firms-irc-7216-aicpa-ftc
- Double pricing model (vendor page; tier prices from secondary listings): https://doublehq.com/pricing ; Double Series A (Dec 2025; vendor-reported figures): https://www.cpapracticeadvisor.com/2025/12/13/double-raises-6-5-million-series-a/174948/
- Xenett pricing: https://www.xenett.com/pricing ; Financial Cents pricing: https://financial-cents.com/pricing/
- Karbon Kai launch (vendor, June 3, 2026): https://karbonhq.com/resources/karbon-launches-kai/
- Xero JAX, Partner Hub and XeroForce (trade press, Aug 20, 2026; vendor-reported): https://itbrief.co.uk/story/xero-expands-ai-tools-for-accountants-small-firms
- Intuit Accountant Suite launch (Oct 2025): https://www.cpapracticeadvisor.com/?p=171765 ; UK launch, free during introduction (Feb 2026): https://itbrief.co.uk/story/intuit-debuts-ai-native-accountant-suite-for-uk-firms ; US introductory pricing (secondary): https://my-cpe.com/insights/news-and-insights/technology/intuit-rolls-out-smartest-ai-accountant-suite-for-next-gen-accounting
- Basis Series B (Feb 24, 2026; penetration and efficiency figures vendor-reported): https://www.cpapracticeadvisor.com/2026/02/24/basis-raises-100-million-to-deploy-ai-agents-for-accounting-firms/178759/
- Digits Accounting Agents (June 2025; vendor-reported): https://www.cpapracticeadvisor.com/2025/06/23/digits-rolls-out-ai-agents-for-accounting-workflows/163521/
- TaxDome summer 2026 update (vendor): https://taxdome.com/blog/webinar-recap-and-qa-summer-update-2026
- Pilot AI Accountant (Feb 4, 2026; vendor claim): https://www.cpapracticeadvisor.com/2026/02/04/pilot-rolls-out-fully-autonomous-ai-accountant/177453/
- Current (formerly Crete) rebrand (June 2026): https://www.cpapracticeadvisor.com/2026/06/03/crete-professionals-alliance-rebrands-as-current/184461/ ; Crete $500M plan (Reuters via syndication, June 4, 2025): https://kfgo.com/2025/06/04/thrive-backed-accounting-firm-crete-to-spend-500-million-in-ai-roll-up/
- Nango Management MCP guide (vendor, Sep 4, 2026): https://nango.dev/blog/how-to-build-ai-agent-integrations-using-the-nango-management-mcp
- Membrane launch (vendor, Nov 18, 2025): https://getmembrane.com/articles/all/announcing-membrane-the-era-of-self-integrations ; superglue (vendor site): https://superglue.ai/
- OpenAI deprecations, Agent Builder shutdown Nov 30, 2026 (announced June 3, 2026): https://developers.openai.com/api/docs/deprecations
- Gartner on forward-deployed engineering (Sep 29-30, 2026; page returned 403, details via secondary coverage): https://www.gartner.com/en/newsroom/press-releases/2026-09-29-gartner-predicts-70-percent-of-enterprises-will-abandon-agentic-ai-built-by-vendor-forward-deployed-engineering-by-2028 ; https://techstrong.ai/articles/gartner-warns-70-of-vendor-built-ai-agent-projects-face-abandonment-by-2028/
- Research-note finding: no reputable primary source was found for hours per client-month spent on close or document chasing (market-accounting notes).
