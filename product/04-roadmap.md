# Roadmap

- Status: Draft v0.1 (2026-10-04), proposed — requires founder ratification
- Owner: Product
- Basis: spec v0.2, [decision record](02-strategy-decisions.md)

Part of the product doc set ([index](README.md)). This roadmap turns decisions D4, D5, D11 and D12 into phases, gates and a calendar. The phase plan (P0 to P6) comes from the [decision record](02-strategy-decisions.md). This document adds four things: a plan for every catalog scenario, proposed catalog additions (PA-P01 to PA-P19), the calendar floors, and the day-180 decision packet. Scope detail is in [MVP scope](03-mvp-scope.md), work items in the [backlog](05-backlog.md), metric definitions in [metrics](06-metrics.md), risk detail in [risks and assumptions](07-risks-and-assumptions.md) and partner recruiting in the [design-partner program](09-design-partner-program.md).

| Label | Meaning |
|---|---|
| Spec requires | Normative text in [spec v0.2](../spec/Plumb_Autonomous_Implementation_Specification_v0.2.md), cited as "spec §N", or a requirement in [requirements_index.json](../spec/requirements_index.json). |
| Package has | Code in the reference package today. It is a local library. Nothing is deployed, connected to a customer or measured. |
| Proposed | This doc set's proposal, taken from the decision record or added here. Nothing is ratified yet. |

**Ground rules for reading this roadmap**

1. Every window is a hypothesis. A phase starts when its entry gate passes, not on a calendar date. Dates are shown only so that calendar floors and tax season are visible.
2. Week 0 starts Monday, October 5, 2026. Day 180 is Saturday, April 3, 2027.
3. The spec's "initial 90-day supervised reference deployment" is "a planning hypothesis contingent on access and staffing" (spec §26). Nothing here promises a 90-day deployment.
4. Every threshold is a hypothesis to be ratified at M0 on threshold sheet v1 (D11). Tables say so once instead of on every line.
5. A scenario passes only through a verifier attestation produced in the intended environment, never through a builder's claim (catalog header; PL-042). Today none of the 30 catalog scenarios has run anywhere. The [catalog](../acceptance/production_acceptance_catalog.yaml) records `executed_against_production: false`, and every scenario has `locally_executed: false`.
6. A partial or adapted run is never reported under the original catalog id. It is reported under one of the proposed ids PA-P01 to PA-P19 defined in section 6. Re-running a scenario's mechanism on another component (PA-015's lease-and-fencing checks on gateway dispatch workers; PA-009 on draft creation) is gateway crash-test evidence, not a scenario result.

---

## 1. Roadmap at a glance

All windows are hypotheses, and each starts on its gate's exit (D5).

| Phase | Window (hypothesis) | Objective | Exit evidence (summary) | Catalog scenarios | Proposed scenarios (section 6) |
|---|---|---|---|---|---|
| P0 Commit and instrument | Weeks 0-2 (Oct 5-18, 2026) | Commit to the platform-proof scope and instrument the learning before building anything else | Rubric, threshold sheet v1, experiment charter and never-claim checklist signed by the founder and domain expert; zero synthetic PRODUCTION_VERIFIED records in the registry; effort ledger records entries end to end, failed attempts included; at least 8 qualified ICP conversations; vendor approval timelines known; partner contract template drafted | None | None |
| P1 M0: contracts, probes and ledger | Weeks 2-8 (Oct 19-Nov 29, 2026); gated on tenant-1 access | Build the control-service skeleton around the existing kernel and earn real probe receipts on tenant 1 | M0 checklist passes, including a named domain owner with a judgeable outcome and denominator, and SANDBOX_TESTED receipts on tenant 1's real accounts; substrate contract tests pass; threat model signed; tenant 1 DPA and envelope signed, paid pilot invoiced; at least 3 more LOIs (tenants 2-4) | None (M0 has no catalog scenario) | PA-P09 |
| P2 M1: tenant 1 integration-and-collection path | Weeks 8-14 (Nov 30, 2026-Jan 10, 2027); sandbox build work may begin from week 6 | Prove automatic construction of a complete integration-and-collection path on tenant 1 (first half of PL-063); ship the read-only close-readiness ledger | PA-001 attested with agent-generated mapping and zero ENGINEERING_INTERVENTION, failed attempts counted; safety bundle passes; tenant 1 EIH/VD baseline recorded; tenant 1's 90-day pilot clock starts. Runway rule: no PA-001 by week 14 means cutting scope to one ledger and one document store | PA-001, PA-015, PA-019, PA-022; PA-026 if generated code ran | PA-P08, PA-P14, PA-P16, PA-P17; PA-P07 if document contents are parsed; PA-P18 if ratified for P2 |
| P3 M1R: reproduction on tenants 2 and 3 | Weeks 12-20 (Dec 28, 2026-Feb 21, 2027); starts on M1 attestation | Prove the path reproduces for new customers with explicit human-labor accounting (second half of PL-063) | PA-001 attested for both tenants, at least one operation on a non-VERIFIED_ADAPTER path; EIH/VD falls at each tenant, tenant 3 at or below 50% of tenant 1; reuse recorded with fork count 0; ledger audit finds zero unrecorded manual work; R1 checkpoint memo | PA-001, PA-019, PA-026 | PA-P01, PA-P14 (co-resident tenants), PA-P15 (workspace surface) |
| P4 M3-lite: preparation-only review workflow, sandbox then production shadow | Weeks 14-22 (Jan 11-Mar 7, 2027); parallel track gated on M1, not on M1R | Compile and attest a preparation-only review-package workflow, then run it in production shadow on tenant 1 with no external communication | PA-002 run as written in sandbox with a BUSINESS_OUTCOME attestation; the six failure scenarios pass in sandbox; numeric correct-package threshold set; DOMAIN_CLARIFICATION per workflow measured; production shadow active with no EXTERNAL_COMMUNICATION in the envelope | PA-002 (sandbox), PA-003, PA-004, PA-006, PA-008, PA-010, PA-011 | PA-P02 (shadow start), PA-P07 (mandatory), PA-P19 |
| P5 Shadow results, gateway hardening and day-180 decision packet | Weeks 20-26 (Feb 22-Apr 4, 2027); day 180 is Apr 3, 2027 | Deliver the first measurable customer deliverable on tenant 1, harden the production action gateway in sandbox, and decide go, pivot or kill | Verifier-attested ready-for-review packages on at least 30 client-periods across at least one full close; correct-package rate against threshold; accountant minutes against the month-0 baseline; false-chase rate of 2% or less and recall of 90% or more; gateway sandbox crash tests; day-180 packet recording tenant 1's evidence toward paid conversion to date | PA-005, PA-009 (sandbox gateway); PA-015's checks re-run on dispatch workers as crash-test evidence, not a PA-015 result | PA-P02 (full close), PA-P12 (first read), PA-P15 (model routes), PA-P11 (begins with tenant 4) |
| P6 M4-accounting and M5 (after day 180) | Weeks 26-36 or later (Apr-Jun 2027), earliest; evidence-gated. This window covers the Prepare-tier CANARY and ACTIVE closes, the Draft tier and the start of M5. The earliest policy-approved Send canary close is around July 2027 (about weeks 39-41), so P6 cannot exit before then | Graduate from preparation to effects safely, and prove replication of the full workflow on the next three customers | Canary report with denominators and effect receipts; zero duplicate, stale or wrong-client requests reached real clients; PA-005, PA-007, PA-009 and PA-010 pass; PA-027 passes with falling EIH/VD and stable quality; at least 2 of the first 4 partners on paid annual contracts at $15 or more per active client-month | PA-002 (canary), PA-005, PA-006, PA-007, PA-009, PA-010, PA-017 (if a training adapter exists), PA-027 | PA-P03, PA-P04, PA-P05, PA-P06, PA-P11, PA-P12, PA-P13 |

**Timeline (one character per week; hypothesis).**

```
Week          0         1         2         3
              01234567890123456789012345678901234567
P0            ==
P1              ======
P2                    ======
P3                        ========
P4                          ========
P5                                ======
P6                                      ==========  ... later (Send canary close about weeks 39-41)
Mid-January                 ^  inputs from tenants 2-3 due (Jan 15)
Tax season                     ~~~~~~~~~~~  Feb 1-Apr 15
Day 180                                ^  Apr 3, 2027
```

P3 and P4 overlap on purpose: M3-lite is gated on M1, not on M1R (D5). At most 3 builds are active until M1R passes.

**What each phase lets Plumb say (D8 never-claim checklist).**

| After | Plumb may say | Plumb may not say yet |
|---|---|---|
| Today | "A specification and a tested policy kernel. Nothing is deployed." The local contract tests (counts in [VALIDATION_REPORT.md](../VALIDATION_REPORT.md)) validate the kernel's local behavior only (spec §28). | Anything about integrations, customers or outcomes. Never quote the spec's stale "56 tests" figure (header table and Appendix C). |
| P2 (M1) | "Agent-configured certified connectors and agent-built collection" on tenant 1, labeled supervised, with the labor ledger shown | "Generated integrations", "automatically constructed" |
| P3 (M1R) | "Automatically constructed" for the integration-and-collection path, with the ledger and denominators shown | "Autonomous" for any deployment. That label needs PA-027-level evidence for its path. |
| P5 | Accountant minutes against the firm's own baseline, with denominators, once PA-P12 attests | "Fewer duplicate requests", "one request per missing item", any ROI figure without a baseline and a denominator |
| P6 | Duplicate and stale requests per client-period, from Send-canary evidence; replication with falling labor, from PA-027 | Never: "autonomous close", posting, "fully autonomous", "zero human", "AI employee" |

---

## 2. How this re-sequences the spec §26 table

**Spec requires.** PL-063 (spec §26): "The first milestone MUST prove automatic construction of a complete integration-and-collection path, not just a manually configured workflow with a polished UI. The next milestone MUST prove that it can be reproduced for a new customer with explicit accounting of human labor."

The §26 table conflicts with PL-063 on replication. It puts replication at M5, after the learning factory (M2), the workflow factory (M3) and release and operation (M4). The catalog follows the table. Its M1 to M5 evidence scenarios are PA-001, PA-012, PA-002, PA-013 and PA-027, and the M4 evidence (PA-013) is a laundry scenario. This roadmap follows PL-063 literally and keeps M1 through M5 inside accounting (D5).

| §26 milestone | Required deliverable (spec §26, quoted) | Evidence before proceeding (spec §26, quoted) | Catalog evidence | Where it lands here | Why |
|---|---|---|---|---|---|
| M0: contracts and threat model | "Approved goal/envelope model, source inventory, capability registry, test corpus" | "Domain owner can judge the outcome; exact source operations are accessible" | None | P0 (commit and instrument) and P1 (M0). Exit by the D4 M0 checklist, proposed as scenario PA-P09 | No scenario gates M0, so the checklist makes it testable. The registry's 15 synthetic PRODUCTION_VERIFIED records (of 25 records covering 23 step types; [registry](../plumb/registry/capability_registry.json)) must be reset first, because "exact source operations are accessible" needs real probe receipts. |
| M1: integration factory | "Agent configures or generates a connector and deploys a collector" | "New permitted source event reaches verified storage with lineage" | PA-001 | P2 on tenant 1. PA-001 plus an agent-filled BuildPlan, an agent-generated client/period/obligation mapping and the safety bundle (D4, construction bar (b)) | PA-001's expected outcome records `path_used` VERIFIED_ADAPTER. On its own it proves orchestration of a pre-built adapter. Requiring agent-generated tenant semantics tests construction without breaking PL-020's preference order. |
| (new) M1R: reproduction | Not in the table; PL-063's "next milestone" | Not in the table; PL-063: "reproduced for a new customer with explicit accounting of human labor" | PA-001 per tenant; PA-027's ledger-audit method applied to the collection path (not reported as PA-027) | P3 on tenants 2 and 3, right after M1. Tenant 3 swaps one provider, forcing a non-VERIFIED_ADAPTER path (PA-P01) | Pulled forward from the table's M5 slot. Replication gives the first read on experiments 3 and 6 (spec §27) in weeks 12-20, instead of after M2-M4 (even this roadmap's M5 starts no earlier than week 26), and it is the cheapest test of the platform claim that could fail. |
| M2: learning factory | "Agent locates input/target sources, builds dataset and candidate evaluation" | "No future-data or duplicate-family leakage; expert-reviewed label sample" | PA-012 | Gated, after day 180. Opens only when all four D5 entry gates pass (section 9) | PA-012 does not require training. Training rights are scarce: 53% of small firms in one survey demand no training on their data (Uku 2026; small, self-selected sample, directional). A small trained model can lose on total cost (spec §14). Training is the largest step in the accounting fixture (EUR 2,500 of the EUR 10,060 step-budget sum). |
| M3: workflow factory | "Agent compiles a plan into a durable business workflow and test bundle" | "Correct complete cases in sandbox; failures pause/reconcile correctly" | PA-002 | P4 as M3-lite. PA-002 as written in sandbox, plus PA-003, PA-004, PA-006, PA-008, PA-010 and PA-011. Then production shadow, measured by PA-P02 | This is the wedge's value (review packages) without external effects. The fixture makes `compile-review-workflow` depend on the training step; M3-lite cuts that dependency, so the tenant plan must be re-authored. |
| M4: release and operation | "Agent deploys within scope, monitors, diagnoses and repairs a permitted defect" | "Canary results, effect receipts, recovery drill and total support effort" | PA-013 (laundry) | P6 as M4-accounting: production action gateway, Draft canary, then a policy-approved Send canary. Evidence is the accounting analogue PA-P04, with PA-P05 and PA-P06 | The table's M4 evidence is in the wrong domain for an accounting beachhead. Following it would force a laundry partner before M5. |
| M5: replication | "Same factories used for new customers and several related workflows" | "Falling manual implementation effort with stable quality and value" | PA-027 (MEDIUM) | P6. Full PA-027 on tenants 2-4 with at least one month of prospective measurement. PA-P13 proposes HIGH severity for releases marketed as autonomously implemented, and PA-P12 attests "value" | Appendix B asks for "the next three customers" (spec App. B); PA-027 tests one. Using tenants 2-4 matches the spec. |
| M6: broader capability | "Add a second domain with domain-specific contracts, not a forked engine" | "Reused planner/compiler/runtime; new adapter/domain work measured separately" | None | Later. Laundry route preparation first, then industrial RFQ. Laundry is gated by PA-013, PA-025, PA-029 and PA-030, with proposed scenario PA-P10 as exit | The laundry fixture plan has no canary step (its last release step is `release.activate_shadow`), so a second domain can start in the Prepare tier. Separate tenant and platform-investment ledgers make "measured separately" checkable. |

**Net effect.**

- The platform verdict (M1R) arrives around weeks 12-20 instead of after M2, M3 and M4.
- M1 through M5 need only accounting partners.
- M2 and M6 become evidence-gated options rather than scheduled phases.
- Against the spec's vertical-proof order (App. A.7), the order holds for probe, adapter and collector, and verified event. Replication of the collection path moves ahead of the workflow. The "optional learned component" moves after deployment and recovery, and A.7 itself calls it optional.

---

## 3. Phase details

Owners follow D12. "Requirements" lists the PL ids the decision record assigns to the phase. Scenario-level PL coverage is in sections 5 and 6. Risks are R1 to R7 as defined in [risks and assumptions](07-risks-and-assumptions.md):

- R1: replication does not get cheaper.
- R2: hidden human labor.
- R3: interruption load turns the customer into the integrator.
- R4: generated failure handling and effect safety.
- R5: market squeeze and willingness to pay.
- R6: build time versus runway.
- R7: data rights and access.

### P0 Commit and instrument

Window: weeks 0-2 (Oct 5-18, 2026), hypothesis. Entry: founder ratifies this doc set.

**Objective.** Commit to the platform-proof scope and instrument the learning before building anything else.

**Scope.**

- Governance: publish the never-claim checklist; freeze the effort rubric (CUSTOMER_AUTHORIZATION, DOMAIN_CLARIFICATION, NORMAL_BUSINESS_REVIEW, ENGINEERING_INTERVENTION, OPERATIONAL_REPAIR) as amended in D6 (founder decision 18): ENGINEERING_INTERVENTION covers implementation work by any person, Plumb or customer staff; approving the reminder policy is CUSTOMER_AUTHORIZATION; scheduled weekly check-ins and baseline-study recording overhead are DOMAIN_CLARIFICATION, so all partner time lands in one of the five categories (PL-003). Plumb staff time on a tenant also lands in the five categories under the Plumb principal: tenant build work, verification and sandbox review are ENGINEERING_INTERVENTION (the default when in doubt), repair of a running component by any person is OPERATIONAL_REPAIR, and facilitating a clarification session or the baseline study is DOMAIN_CLARIFICATION; only time not attributable to one tenant leaves the tenant ledger (platform-investment ledger, or the cost ledger for general overhead; PL-059). Issue threshold sheet v1 and an experiment charter with pre-registered thresholds for the six spec §27 experiments and the commercial unknowns.
- Registry: reset to truthful DISCOVERED/DOCUMENTED maturity. **Package has** a maturity floor in [plan_checker.py](../plumb/checker/plan_checker.py) (`required_maturity`): `release.*` and `infrastructure.apply` need PRODUCTION_VERIFIED, other non-shadow writes need SANDBOX_TESTED. Resetting the 15 synthetic PRODUCTION_VERIFIED records makes every fixture plan fail at `integration.configure`, `collection.backfill` and `collection.enable_incremental` (SANDBOX_TESTED floor), and at `release.*` and `infrastructure.apply` (PRODUCTION_VERIFIED floor). Resetting the 8 synthetic SANDBOX_TESTED records as well adds failures at `dataset.build`, `workflow.compile` and, where the plan has them, `training.submit` and `integration.generate_adapter`. That failure is expected.
- Engineering: ship the human-effort ledger as the first product code, recording failed attempts. **Package has** the `HumanEffortCategory` enum and an unused `HumanEffortRecord` model, but no capture API, and `PrincipalType` has no type for Plumb staff (a contracts gap; backlog E01-S02).
- Fixtures: re-template the accounting fixtures (EUR, eu-west-1) to US/USD; the RFQ fixtures are already USD (us-east-1) and laundry is GBP (eu-west-2). Refresh or clock-pin all three envelopes, which expire 2027-03-31.
- External: start ICP outreach; start vendor app-review and consent processes for document, ledger and mail scopes; open the security/platform and verification hires; engage counsel.

**Exit evidence.**

- Rubric, threshold sheet, charter and checklist signed by the founder and the domain expert.
- Zero synthetic PRODUCTION_VERIFIED records.
- The effort ledger records entries end to end, including a failed attempt.
- At least 8 qualified ICP conversations.
- Vendor approval timelines known.
- Partner contract template drafted with data-rights tiers.

**Acceptance.** No catalog scenario. P0 builds the instruments that later scenarios read: PA-001 fails on any ENGINEERING_INTERVENTION entry, and PA-027 compares against the first customer's ledger.

**Requirements (decision record).** PL-003, PL-007, PL-008, PL-062.

**Owners.**

- Founder: checklist, rubric, interruption budget, outreach, hires.
- Domain expert: threshold sheet v1, jointly with the founder.
- Integration engineer: registry reset.
- Tech lead and product engineer: effort ledger.
- Fractional compliance lead: vendor reviews.
- Counsel: contract template.

**Dependencies.** Domain expert engaged at 0.5 FTE or more from week 0 (D12).

**Risks touched.** R2 (the ledger exists before any build), R5 (paid pilots from day one), R6 (scope commitment), R7 (vendor approvals and counsel started in week 0).

### P1 M0: contracts, probes and ledger

Window: weeks 2-8 (Oct 19-Nov 29, 2026), hypothesis. Entry: P0 exit plus tenant 1 access. D9 expects tenant 1 signed by about week 4 (Nov 2).

**Objective.** Build the control-service skeleton around the existing kernel, and earn real probe receipts on tenant 1.

**Scope.**

- Control service: auth and tenancy from verified identity (PL-004); a durable build ledger; state-machine guards that call the checkers; `check_plan` consuming the tenant EnvironmentInventory and the capability's `required_authority`. **Package has** the checkers and the state machines, but the guards take caller-asserted booleans and `check_plan` takes no inventory input.
- Effort accounting: automatic capture of human-principal actions, plus a separate platform-investment ledger.
- Tenant 1 probes: real probes of document-store and ledger-metadata operations; SANDBOX_TESTED receipts for `integration.configure`, `collection.backfill` and `collection.enable_incremental` (the checker's floor for these writes) and for `list_folder_changes`, `fetch_document` and the ledger-metadata reads (PA-001's preconditions and the exit evidence below); the DOCUMENTED floor for other read steps.
- Platform: substrate contract tests (Nango is the candidate); threat model.
- Tenant 1 paperwork: DPA and envelope, US region.
- Partners: month-0 time study scheduled for tenant 1 (section 4 proposes the November-period close); at least 25 qualified conversations; LOIs from tenants 2-4; partner baseline studies scheduled to finish before mid-January.

**Exit evidence (the M0 checklist from D4, proposed as PA-P09).**

- A named domain owner can judge an outcome definition that has a denominator.
- SANDBOX_TESTED probe receipts exist for `list_folder_changes`, `fetch_document`, the collector-write operations and ledger-metadata reads on tenant 1's real accounts.
- Substrate contract tests pass on the probed operations.
- No synthetic PRODUCTION_VERIFIED claims remain in the registry.
- Threat model signed off.
- Month-0 baseline captured or scheduled.
- Effort ledger live with the frozen rubric.
- Tenant 1 DPA and envelope signed, and its paid pilot invoiced.
- At least 3 more LOIs (tenants 2-4) signed.

**Acceptance.** Catalog: none. Proposed: PA-P09.

**Requirements (decision record).** PL-003, PL-004, PL-005, PL-006, PL-007, PL-008, PL-014, PL-015, PL-017, PL-053, PL-059, PL-062.

**Owners.**

- Tech lead: control service, build ledger, guard wiring.
- Integration engineer: probes, registry, substrate contract tests.
- Security/platform engineer (hired weeks 0-4): threat model, isolation design.
- Product engineer: effort capture.
- Domain expert: outcome definition and denominator.
- Founder: DPA, LOIs, baseline scheduling.
- Counsel: DPA, purpose grants, SERVE, IRC 7216.

**Dependencies.**

- Tenant 1 OAuth grants on its real accounts.
- Vendor approvals far enough along to probe.
- Substrate access (Nango or alternative).
- Security hire in seat.

**Risks touched.**

- R1: substrate fit.
- R2: automatic capture.
- R6: runway.
- R7: DPA, and whether ledger authorization is granted per client company. If it is, and onboarding CUSTOMER_AUTHORIZATION exceeds 4 hours per firm, D1 says re-scope the stack.

### P2 M1: tenant 1 integration-and-collection path

Window: weeks 8-14 (Nov 30, 2026-Jan 10, 2027), hypothesis. Entry: M0 exit. Sandbox build work may begin from week 6 (Nov 16).

**Objective.** Prove automatic construction of a complete integration-and-collection path on tenant 1 (first half of PL-063), and ship the read-only close-readiness ledger.

**Scope.**

- Build path: the agent fills in the BuildPlan from tenant 1's inventory; reuses certified transport; generates the client/period/obligation mapping in a disposable sandbox; deploys a shadow collector, backfills from the agreed watermark, reconciles and goes incremental. The verifier attests that a live upload made outside Plumb arrives.
- Effects in this phase are READ, INTERNAL_WRITE, and EXTERNAL_WRITE_REVERSIBLE (connector setup and enabling incremental capture on the firm's own accounts). The accounting fixture marks `configure-certified-connectors` and `enable-incremental-capture` as EXTERNAL_WRITE_REVERSIBLE. There is no EXTERNAL_COMMUNICATION. (The panel record's "only READ and COLLECT effect classes" is corrected in the [decision record](02-strategy-decisions.md): COLLECT is a data purpose.)
- A thin gateway slice: credential resolution for connectors, and refusal of out-of-scope effect classes at dispatch. PA-022 needs it. The full production action gateway comes in P5 and P6.
- Customer surfaces: read-only close-readiness ledger; implementation card, blocked-dependency card, progress feed and effort view; published supported-environments v1, stated per operation and maturity level.

**Exit evidence.**

- PA-001 attested: `path_used` VERIFIED_ADAPTER for transport; agent-generated mapping and CollectionSpec; zero ENGINEERING_INTERVENTION in the attested run, with every failed eligible attempt counted.
- Safety bundle:
  - PA-015, PA-019 and PA-022.
  - The collector half of PA-005 (PA-P16) and the health half of PA-011 (PA-P17).
  - The accounting adaptation of PA-023's account_boundaries contract test (PA-P08).
  - PA-017 on its database, API, object-storage, cache, log and export surfaces (PA-P14), before any second tenant's data arrives.
  - The accounting adaptation of PA-021's parser bounds (PA-P07) whenever document contents are parsed.
  - PA-026 if generated code ran; otherwise it moves to the first tenant where generated code runs.
- Recorded: tenant 1's EIH/VD baseline, and time to first verified event, split into Plumb-controlled and dependency time. Tenant 1's 90-day pilot clock starts at the first attested collection path (D7).

**Acceptance.** Catalog: PA-001, PA-015, PA-019, PA-022, and PA-026 conditionally. Proposed: PA-P07 (conditional), PA-P08, PA-P14, PA-P16, PA-P17. PA-P18 is added here as a recommendation for ratification. The decision record's P2 list includes PA-005, PA-011 and PA-017; only their subsets run here, so they are reported as PA-P16, PA-P17 and PA-P14.

**Requirements (decision record).** PL-002, PL-009, PL-010, PL-011, PL-016, PL-017, PL-018, PL-019, PL-020, PL-021, PL-022, PL-023, PL-024, PL-025, PL-042, PL-052, PL-054, PL-063.

**Owners.**

- Integration engineer: connectors, mapping generation, collectors.
- Tech lead: build engine, leases and fencing (PA-015), gateway slice.
- Verification engineer (by week 6, reporting outside the build team): verifier, fault-injection harness, attestation.
- Security/platform engineer: sandbox, egress, PA-019, PA-026, PA-P14.
- Product engineer and fractional designer: readiness ledger and cards.
- Founder and external technical advisor: M1 ledger audit.

**Dependencies.**

- M0 exit.
- Sandbox and egress infrastructure. If it slips more than 4 weeks, attest M1 on PA-001 plus the rest of the bundle and move the generated-path requirement to tenant 3 (founder decision 1, D4).
- Provider supports webhooks plus overlap polling (PA-005 precondition).
- Verifier and harness exist.

**Risks touched.** R1 (EIH/VD baseline), R2 (zero-intervention attestation and audit), R4 (collector safety), R6 (runway rule: if PA-001 has not passed by week 14, about Jan 11-17, cut scope to one ledger and one document store instead of adding platform), R7.

**Claim unlocked.** "Agent-configured certified connectors and agent-built collection." Never "generated integrations" or "automatically constructed".

### P3 M1R: reproduction on tenants 2 and 3

Window: weeks 12-20 (Dec 28, 2026-Feb 21, 2027), hypothesis. Entry: M1 attestation. Customer-side inputs must be collected before mid-January.

**Objective.** Prove that the integration-and-collection path reproduces for new customers with explicit human-labor accounting (second half of PL-063).

**Scope.**

- The same engine with no code fork. Tenant 2 varies folder structure and chart-of-accounts conventions; tenant 3 swaps one provider, forcing a DECLARATIVE_CONFIG or GENERATED_CODE path.
- Audit: PA-027's ledger-audit and denominator method applied to the integration-and-collection path, reviewed by an auditor outside the delivery team.
- Partner value: firm B runs its baseline close in parallel, so it sees value before its own shadow.
- Experiment 1 proxy: during tenant 2-3 onboarding, compare discovery from APIs and history alone with the same plus a 2-hour structured shadowing session.
- Capacity: at most 3 active builds.

**Exit evidence.**

- PA-001 attested for both tenants, with at least one operation on a non-VERIFIED_ADAPTER path (PA-P01).
- PA-026 and PA-019 pass on that generated path.
- PA-017 surfaces pass with co-resident tenants (PA-P14), and the workspace surface (PA-P15) passes if generated code runs.
- EIH/VD falls at each tenant, with tenant 3 at or below 50% of tenant 1 (hypothesis).
- Platform-investment hours per tenant reported, not netted.
- Artifact reuse rate recorded, with fork count 0.
- The audit finds zero unrecorded manual work.
- Experiment-1 proxy result recorded.
- R1 checkpoint memo written against the pre-registered criteria.

**Acceptance.** Catalog: PA-001 (per tenant), PA-019, PA-026. Proposed: PA-P01, PA-P14, PA-P15. The PA-027 method is applied but not reported as PA-027, which also needs review-package quality and first-month review hours.

**Requirements (decision record).** PL-002, PL-003, PL-020, PL-052, PL-062, PL-063.

**Owners.**

- Integration engineer: the provider swap and the generated path.
- Verification engineer: attestations and ledger-audit tooling.
- Founder and external technical advisor: independent ledger audit.
- Founder and domain expert: experiment-1 proxy.
- Security/platform engineer: co-resident isolation.

**Dependencies.**

- M1 attestation.
- Tenants 2 and 3 signed, with grants, domain clarifications and baseline studies collected before mid-January.
- Tenant 3's provider swap selected in the stack-variation matrix (D1).

**Risks touched.**

- R1 (primary): if tenant 3's EIH/VD is at or above 75% of tenant 1's, or the hands-off rate is below 50%, or reuse is below 60%, or any fork is needed, freeze new milestone work for 4 weeks and find the root cause.
- R2: audit.
- R3: domain clarifications at onboarding.
- R6: M1R not passed by week 24 (about Mar 22-28) forces the day-180 memo to choose between a reduced-scope extension and the R1 pivot.
- R7: tax-season inputs.

**Revisit (D5).** If M1 shows the path is mostly substrate configuration, with less than 1 hour of adaptation variance between firms, fold M1R into M5 and invest in M3 depth.

**Claim unlocked.** "Automatically constructed" for the collection path, with the ledger shown.

### P4 M3-lite: preparation-only review workflow, sandbox then production shadow

Window: weeks 14-22 (Jan 11-Mar 7, 2027), hypothesis. Entry: M1 attestation. It does not wait for M1R.

**Objective.** Compile and attest a preparation-only review-package workflow, then run it in production shadow on tenant 1 with no external communication.

**Scope.**

- Data: connect read-only mail history; produce the historical duplicate-chase baseline, labeled historical and non-causal (spec §7) and never counted as a PL-001 outcome.
- Workflow:
  - An obligation engine with engagement-checklist templates.
  - Deterministic checks plus general-model extraction through the gateway, with no training.
  - A ReviewPackage contract. **Package has** ReviewPackage only as an artifact kind with no contract.
  - An accountant sign-off surface with explicit accept/correct/amend capture, which also serves as the prospective correction collector.
  - The protected verifier run against the Appendix B failure set in sandbox.
- Release and data rights:
  - A narrow release executor on fixed approved templates.
  - A platform qualification run on a Plumb-owned production tenant that earns real PRODUCTION_VERIFIED receipts for `release.create` and `release.activate_shadow`, the checker's floor, before any tenant shadow. Tenant plans contain no `infrastructure.apply` step: MVP releases run on platform-managed shared infrastructure that Plumb provisions outside tenant envelopes (founder decision 19, decided default; founder to ratify).
  - Pause and kill from SHADOW and CANARY. **Package has** a RELEASE machine ([machines.py](../plumb/statemachines/machines.py)) that allows PAUSED only from ACTIVE.
  - An explicit SERVE grant before the first shadow. **Package has** no SERVE check: every fixture plan passes without a SERVE grant.

**Exit evidence.**

- PA-002 run as written in sandbox. Its single send goes only through the sandbox mail adapter against sandbox copies of the sources, and it receives a BUSINESS_OUTCOME attestation.
- PA-003, PA-004, PA-006, PA-008, PA-010 and PA-011 pass in sandbox.
- The accounting adaptation of PA-021's parser bounds (PA-P07) passes on client PDFs.
- PA-P19 passes before the workflow reads client content in production (added here; see section 6).
- The domain expert sets a numeric correct-package threshold.
- DOMAIN_CLARIFICATION per workflow measured against the budget (experiment 4).
- Production shadow active on tenant 1 with no EXTERNAL_COMMUNICATION in the envelope. PA-P02 starts measuring.

**Acceptance.** Catalog: PA-002 (sandbox), PA-003, PA-004, PA-006, PA-008, PA-010, PA-011. Proposed: PA-P02, PA-P07, PA-P19. A sandbox pass lets the release enter SHADOW. Under the catalog's HIGH definition, the release "may not leave SHADOW or CANARY until the scenario passes in the intended environment"; this roadmap reads production as the intended environment for the failure scenarios.

**Requirements (decision record).** PL-001, PL-010, PL-011, PL-016, PL-035, PL-036, PL-040, PL-041, PL-042, PL-043, PL-044, PL-045, PL-046, PL-047, PL-053.

**Owners.**

- Product engineer and designer: review and sign-off surface.
- Applied ML/eval engineer (about week 12): package-correctness evaluation, verifier calibration, protected corpus.
- Domain expert: engagement-checklist templates, correct-package threshold.
- Tech lead: release executor, pause and kill.
- Verification engineer: Appendix B failure set.
- Counsel: SERVE grant language.

**Dependencies.**

- M1 attested.
- Mail-history scopes approved by the vendor. If not, or if at least 2 of 5 partners refuse mailbox scopes, fall back to document store plus ledger with a forwarding-address intake (R7).
- Eval hire in seat.
- Release-executor qualification complete before tenant shadow.

**Risks touched.** R3 (DOMAIN_CLARIFICATION per workflow), R4 (generated failure handling on the protected failure cases, experiment 5), R6, R7 (mail scopes).

**Customer-facing result.** Review packages in production shadow, with "what Plumb would have done" reports. The co-headline, accepted review packages per month, starts here.

### P5 Shadow results, gateway hardening and day-180 decision packet

Window: weeks 20-26 (Feb 22-Apr 4, 2027), hypothesis. Day 180 is Apr 3, 2027. Entry: production shadow active on tenant 1.

**Objective.** Deliver the first measurable customer deliverable on tenant 1, harden the production action gateway in sandbox, and make the day-180 go/pivot/kill decisions against pre-registered thresholds.

**Scope.**

- Shadow: run on tenant 1 for at least one full month-end close; start shadow on tenants 2-3 as their workflows activate; produce "what Plumb would have done" reports against the accountants' actual decisions.
- Gateway, in sandbox: outbox and leases; dispatch-time authority, revocation and pause checks; Draft-tier tests.
- Commercial: begin tenant 4 onboarding for the M5 cohort; record tenant 1's pilot-to-paid evidence to date (conversion is expected in P6; see below); start the price test with new prospects.
- Decisions: M2 go/no-go memo; day-180 decision packet (section 9).
- Proposed: Prepare-tier promotion path (founder decision 17 in the [decision record](02-strategy-decisions.md), to ratify). The preparation-only release goes SHADOW (at least one full close), then CANARY on a subset of client-periods whose accountants use the prepared packages in their real review, then ACTIVE. No state has EXTERNAL_COMMUNICATION in the envelope. This needs pause and kill from SHADOW and CANARY (P4), PA-P02 passing, and the HIGH scenarios passing in production. It also needs a preparation-only `release.canary` template that declares no EXTERNAL_COMMUNICATION and a registry step type for CANARY to ACTIVE promotion (the registry has none; only the API's `activateRelease` exists), both earning PRODUCTION_VERIFIED receipts with a verifier attestation on a Plumb-owned qualification tenant before tenant 1's canary. Owner: tech lead, backlog E16-S09 (P5). No Draft or Send gate is involved. A partner converts to paid annual after one full close in ACTIVE at or above the correct-package threshold (D7, D9).

**Exit evidence.**

- Tenant 1:
  - Verifier-attested ready-for-review packages on at least 30 client-periods across at least one full close (PA-P02).
  - Correct-package rate against the threshold, with exclusions in the denominator.
  - Accountant minutes against the month-0 baseline (first PA-P12 read).
  - False-chase rate of 2% or less and recall of 90% or more (proposed).
- Tenants 2-3: shadow started. Their full-close readings may land after day 180 and are reported as pending.
- Interruption: owner decision time within budget; repeat asks 0.
- Gateway sandbox crash tests: PA-005's dispatch-time re-check, PA-009 and the PA-015 lease-and-fencing checks pass for draft creation and sends; pause and kill work from SHADOW and CANARY.
- Model-route isolation (PA-P15) passes before tenants 2-3 data reaches shared model routes.
- Day-180 packet delivered.

**Acceptance.** Catalog: PA-005 and PA-009, as written against the sandbox gateway. PA-015's checks re-run on dispatch workers count as crash-test evidence, not a PA-015 result. Proposed: PA-P02, PA-P12, PA-P15. PA-P11 is recommended from tenant 4's onboarding. Sandbox gateway passes are readiness results. The activation-gating passes happen on the production gateway in P6.

**Requirements (decision record).** PL-037, PL-038, PL-039, PL-047, PL-057, PL-059, PL-062, PL-063.

**Owners.**

- Domain expert and reviewing accountants: shadow adjudication.
- Tech lead: gateway.
- Verification engineer: crash tests.
- Founder: packet, tenant 1 conversion evidence, price test, tenant 4.
- SRE/on-call: hired by about week 22.

**Dependencies.**

- Production shadow must be active before tenant 1's February-period close begins, around March 1 under the close-calendar assumption in section 4. Otherwise the first full shadow close is the March-period close, worked in early to mid April, after day 180.
- Tenant 4 LOI.

**Risks touched.**

- R1: three-tenant read.
- R3: owner decision time.
- R4: gateway in sandbox.
- R5: pilot-to-paid, price test.
- R6: the day-180 memo.

**Source conflict, resolved (to ratify).** The panel record schedules a "Tenant 1 pilot-to-paid decision" in P5. But D7 and D9 convert a partner to annual only after the workflow has been ACTIVE through one full close, and tenant 1 is still in SHADOW at day 180. The 90-day pilot clock, starting at the first attested collection path (about Jan 10), ends about Apr 10, 2027. Resolution: the day-180 packet records tenant 1's evidence to date, and tenant 1's conversion is expected in P6, through the promotion path above (founder decision 17).

### P6 M4-accounting and M5 (after day 180)

Window: weeks 26-36 or later (Apr-Jun 2027), earliest, evidence-gated. That window covers the Prepare-tier CANARY and ACTIVE closes, the Draft tier and the start of M5, not Send: the earliest policy-approved Send canary close is around July 2027 (calendar note below), and P6 cannot exit before it. Entry: day-180 go decisions on the Draft tier and the M4-accounting canary.

**Objective.** Graduate from preparation to effects safely, and prove replication of the full workflow on the next three customers.

**Scope.**

- Prepare-tier promotion and conversion (founder decision 17, to ratify): tenant 1's release moves from SHADOW to CANARY and then ACTIVE, with no EXTERNAL_COMMUNICATION, and each partner converts to paid annual after one full ACTIVE close at or above the correct-package threshold (see P5 above and the close calendar in section 4).
- Effects:
  - Production action gateway.
  - SRE/on-call coverage in place before the Draft tier.
  - Draft-tier canary for at least one close.
  - Then a policy-approved Send canary on at most 20% of client-periods for at least one close, limited to client and obligation types that passed the D6 calibration ladder: at least 2 closes and at least 20 drafts of that type, approve-without-edit of at least 95%, material edits below 2% (hypotheses).
  - The PA-014 revocation-race mechanism (PA-P05) and a PA-016-style schema-drift repair (PA-P06), both as accounting adaptations.
  - A recovery drill; recorded support effort.
- Replication and isolation: M5 runs full PA-027 on tenants 2-4 with at least one month of prospective measurement, and full PA-017 runs before any training job.

**Exit evidence.**

- Canary report with denominators and effect receipts (PA-P04).
- Zero duplicate, stale or wrong-client requests reached real clients.
- PA-005, PA-007 (concurrent ACTIVE and CANARY releases), PA-009 and PA-010 pass. The Draft gate also re-runs PA-006 and the PA-015 checks on the production gateway (D4).
- PA-027 passes, with falling EIH/VD and stable quality.
- At least 2 of the first 4 partners are on paid annual contracts at $15 or more per active client-month.

**Acceptance.** Catalog: PA-002 (canary), PA-005, PA-006, PA-007, PA-009, PA-010, PA-017 (only if a training adapter exists; otherwise PA-P14 and PA-P15), PA-027. Proposed: PA-P03 (before any policy-level Send), PA-P04, PA-P05, PA-P06, PA-P11, PA-P12, PA-P13.

**Requirements (decision record).** PL-037, PL-038, PL-039, PL-040, PL-047, PL-048, PL-049, PL-059, PL-061, PL-062, PL-063.

**Owners.**

- Tech lead: production gateway.
- SRE: on-call.
- Integration engineer: drift repair path.
- Verification engineer: canary attestation, PA-027 method.
- Founder and external technical advisor: M5 ledger audit.
- Domain expert: calibration ladder thresholds.
- Founder: conversions.

**Dependencies.**

- Day-180 go decisions.
- Draft gates passed on the production gateway.
- Tenants 2-4 with verified full-workflow deployments.
- A training adapter able to submit a harness job if full PA-017 is to pass in P6 (see the PA-017 row in section 5).

**Risks touched.**

- R4: one real-client duplicate, stale or wrong-client request halts sends and reverts to Draft. Two within 90 days remove Send from the product for two quarters.
- R5: conversion.
- R1 and R2: PA-027 and the M5 audit.
- R3: per-case approval share after calibration.

**Calendar note.** Under the D6 ladder, a type needs 2 Draft closes before policy-level Send. If Draft starts on the April-period close (worked in May), the earliest policy-level Send canary close is the June-period close, worked in July 2027 (about weeks 39-41). The panel record's statement that the Send canary "cannot finish before about weeks 30-36" ignored the ladder; the [decision record](02-strategy-decisions.md) corrects it (correction 12). The realistic earliest is later.

---

## 4. Calendar floors and seasonality

**Floors (minimums, not estimates).** Nothing in this roadmap can compress them.

| Floor | Value | Source | Consequence |
|---|---|---|---|
| Backfill depth | 12-24 months of history per tenant | D5; the accounting fixture backfills 24 months, RFQ 18, laundry 12 | This is a data-depth floor. Its wall-clock duration depends on provider rate limits and is not yet measured. The ICP requires 12-24 months of history (D1). |
| Shadow | At least one full monthly close | D5 | Tenant 1's first deliverable needs one full close in shadow. |
| Draft | At least one close | D5 | First external-write tier runs a full cycle before Send. |
| Send canary | At least one close | D5 | Plus the D6 ladder: 2 Draft closes per type before policy-level Send. |
| PA-027 | At least one month of live operation after verified deployment | Catalog PA-027 (first-month review and rework hours) | M5 cannot finish before tenant 4's first live month ends. |
| Closes per 180 days | About 6 | D5 (monthly cadence) | Every quality read is one data point per month per tenant. |
| Earliest credible renewal decision | About three closes after connection | D5 | For tenant 1, connected about Jan 10, that is around mid-April 2027. This is a floor on the renewal decision, not the conversion date: conversion follows one full ACTIVE close after the SHADOW and CANARY stages, expected in P6 (founder decision 17). |
| Customer-side inputs for tenants 2 and 3 | Grants, domain clarifications and baseline studies collected before mid-January | D5 | Tax season slows partner responses from February. |

**Fixture durations are upper bounds, not floors.** Verified in [fixtures/plans/accounting_evidence_preparation.json](../fixtures/plans/accounting_evidence_preparation.json) and the other plans. Every value below is a `max_elapsed_seconds` budget: a ceiling, not a schedule estimate and not a minimum.

| Fixture value | Where | Equals | Reading |
|---|---|---|---|
| 3,600 s | Most accounting steps, including `deploy-shadow-collectors` | 1 hour | Upper bound per step |
| 21,600 s | `backfill-close-history` (24 months) | 6 hours | Upper bound; real backfill time is unmeasured |
| 1,209,600 s | `activate-shadow-processing` (accounting and RFQ) | 14 days | Shorter than the one-close shadow floor |
| 1,814,400 s | `canary-consolidated-reminders`; laundry `activate-shadow-planning` | 21 days | Shorter than the one-close canary floor |
| 5,184,000 s | Plan `total_budget` in all three plans | 60 days | Shorter than shadow plus canary at one close each |
| 90 days | Accounting envelope goal `horizon_days` | 90 days | A goal horizon, not a delivery promise |

Consequence: a real tenant plan that runs shadow and canary for a full close each needs larger step and total budgets than the fixture. That is a backlog item for re-authoring the tenant plan, not a fixture defect.

**Close calendar (assumption).** A firm works period N's close in the first two to three weeks of month N+1. The month-0 time study confirms each firm's actual close calendar.

| Period | Close worked (assumption) | Phase in progress | Proposed use |
|---|---|---|---|
| Oct 2026 | Early-mid Nov 2026 | P1 | Tenant 1 signs and grants; probes |
| Nov 2026 | Early-mid Dec 2026 | P1 to P2 | Tenant 1 month-0 time study (2 weeks), before any shadow |
| Dec 2026 (year-end) | Early-mid Jan 2027 | P2 to P3 | Tenants 2-3 baseline studies, finished before mid-January; firm B's baseline close in parallel with M1R |
| Jan 2027 | Early-mid Feb 2027 | P3, P4 | Tenant 1 uses the readiness ledger; tax season begins |
| Feb 2027 | Early-mid Mar 2027 | P4 to P5 | First full shadow close for tenant 1, if production shadow is active before it starts |
| Mar 2027 | Early-mid Apr 2027 | P5 to P6 | Fallback first shadow close (lands after day 180); otherwise a second shadow close or the Prepare-tier CANARY |
| Apr 2027 | Early-mid May 2027 | P6 | Earliest realistic Draft close; earliest Prepare-tier ACTIVE close for tenant 1, after which annual conversion can take effect |
| May 2027 | Early-mid Jun 2027 | P6 | Second Draft close (D6 ladder) |
| Jun 2027 | Early-mid Jul 2027 | P6 | Earliest realistic policy-level Send canary close |

**Tax season.** US tax season runs from February to the April 15 filing deadline (D5). It overlaps the whole P4-P5 shadow period, so reviewing accountants have the least time exactly when the first deliverable needs their adjudication. Mitigations:

- The ICP requires at least 60% of revenue from recurring bookkeeping/CAS (hypothesis) so the domain owner is not absorbed by tax work (D1).
- Collect tenants 2-3 inputs before mid-January.
- Batch reviewer approvals into at most one session a day (D6).
- Treat review minutes above budget as a product defect, not a partner failure.

---

## 5. Acceptance scenario plan

One row per catalog scenario, all 30. Titles, severities, domains (the catalog's `scenario` field) and requirements are taken from the [catalog](../acceptance/production_acceptance_catalog.yaml) exactly.

**Rules for this table.**

- **As written** means the scenario's steps and expected outcome unchanged, in the stated environment.
- **Accounting adaptation** means the mechanism runs on an accounting tenant under a proposed id from section 6 and is never reported under the original id.
- **Not claimed** means no pass is reported in P0-P6.
- HIGH means a failure blocks the release from leaving SHADOW or CANARY until the scenario passes in the intended environment. This roadmap reads production as the intended environment for the failure scenarios, so a sandbox pass lets a release enter shadow, but the production pass is needed before it leaves.

| ID | Title (catalog) | Severity | Domain | First required (this roadmap) | How used | PL ids |
|---|---|---|---|---|---|---|
| PA-001 | M1 evidence: a new permitted source event reaches verified storage with lineage | HIGH | accounting | P2 (tenant 1); P3 per tenant | As written: the IntegrationSpec records `path_used` VERIFIED_ADAPTER for transport (PL-020 prefers it). Mapping and CollectionSpec must be agent-generated (D4). The generated path is PA-P01. | PL-002, PL-007, PL-009, PL-020, PL-022, PL-023, PL-024, PL-063 |
| PA-002 | M3 evidence: a complete accounting case runs correctly in the sandbox and stops at the sign-off boundary | HIGH | accounting | P4 (sandbox); P6 (Send canary) | As written in sandbox: the single send goes only through the sandbox mail adapter against sandbox copies of the sources. Production shadow is measured by PA-P02, never reported as PA-002. Full PA-002 again in the Send canary. | PL-001, PL-016, PL-035, PL-042, PL-043, PL-061 |
| PA-003 | Wrong client: a misfiled statement is not attributed to the folder owner | HIGH | accounting | P4 | As written (sandbox, then production before leaving SHADOW). Nothing is sent in this scenario. | PL-010, PL-011, PL-036 |
| PA-004 | Ambiguous period: a statement spanning a period boundary pauses for a focused question | HIGH | accounting | P4 | As written. The owner's answer becomes a versioned convention, logged as DOMAIN_CLARIFICATION. | PL-001, PL-010, PL-011, PL-041 |
| PA-005 | Already-received document: reordered and duplicated arrival events never trigger a request for a document already held | HIGH | accounting | P2 (collector half only); P5 (sandbox gateway); P6 (Draft and Send gate) | P2 runs only the collector half, reported as PA-P16. P5 runs it as written against the sandbox gateway. The activation-gating pass is on the production gateway in P6. | PL-024, PL-025, PL-037, PL-039 |
| PA-006 | Corrected statement after approval: the accepted input becomes stale and the prepared request is recomputed | HIGH | accounting | P4 (sandbox); P6 (Draft gate) | As written in sandbox; re-run on the production gateway as part of the Draft gate (D4). | PL-009, PL-010, PL-037, PL-040 |
| PA-007 | Duplicate request: two actors chasing the same client resolve to one obligation owner and one effect | HIGH | accounting | P6 (Send canary) | As written. It needs concurrent ACTIVE and CANARY releases, so it cannot pass before the Send canary (earliest close around July 2027). | PL-037, PL-039 |
| PA-008 | Expired permission: a lapsed source grant stops collection and dispatch promptly and raises a precise dependency | HIGH | accounting | P4 | As written, with a real expiring grant at the mail provider. | PL-001, PL-005, PL-041, PL-053 |
| PA-009 | Provider timeout after send: an accepted reminder becomes UNKNOWN and is reconciled, never resent | HIGH | accounting | P5 (sandbox gateway); P6 (gate) | As written (sends) against the sandbox gateway; the same check on draft creation is Draft-gate crash-test evidence, not a PA-009 result. Activation-gating pass on the production gateway. | PL-017, PL-038, PL-039, PL-057 |
| PA-010 | Changed approval: an approval bound to a previous digest or policy does not authorize the revised request | HIGH | accounting | P4 (sandbox); P6 (gate) | As written (a case-level approval bound to digest, case version and policy version). The D6 policy-level default is tested by PA-P03. | PL-040, PL-041 |
| PA-011 | Stale source: a stopped collector blocks the obligation check instead of defaulting it | HIGH | accounting | P2 (health half only); P4 (full) | P2 runs only the health half, reported as PA-P17. Full scenario as written in P4, once a request step exists to block. | PL-010, PL-025, PL-048 |
| PA-012 | M2 evidence: dataset construction shows no future-data or duplicate-family leakage and carries an expert-reviewed label sample | HIGH | accounting | M2 (gated by the D5 entry gates) | Not claimed in P0-P6. A PA-012-style 100-pair accountant sample measures join precision as an M2 entry gate; that measurement is not a PA-012 pass. | PL-026, PL-027, PL-028, PL-029, PL-030, PL-031, PL-053 |
| PA-013 | M4 evidence: canary results, effect receipts and a recovery drill for the laundry route release | HIGH | laundry | M6 (before any laundry canary) | Not claimed for accounting; M4-accounting uses PA-P04. In M6 it gates a laundry canary. Laundry starts shadow-only, as its fixture plan does. | PL-017, PL-034, PL-043, PL-045, PL-046, PL-047, PL-049, PL-059, PL-061 |
| PA-014 | Approval revocation race after provider acceptance: the receipt is retained and remediation is explicit | HIGH | industrial_rfq | Later (RFQ, after laundry) | The mechanism runs in P6 as accounting adaptation PA-P05, never reported as PA-014. | PL-038, PL-040, PL-041 |
| PA-015 | Lease expiry: the replacement worker reconciles uncertain effects before any new work and stale fencing tokens cannot commit | HIGH | platform | P2 | As written in P2 (collector creation by the build engine). In P5 and P6 its lease-and-fencing checks are repeated on gateway dispatch workers and reported as a mechanism re-run, not as a second PA-015 pass. | PL-016, PL-017, PL-038, PL-057 |
| PA-016 | Schema drift quarantine: a renamed price field with changed units pauses affected work while unaffected work continues | HIGH | industrial_rfq | Later (RFQ) | Accounting adaptation PA-P06 in P6, never reported as PA-016. | PL-018, PL-021, PL-048, PL-049 |
| PA-017 | Tenant isolation across database, object storage, search, caches, workspaces, training jobs, model routes, logs and exports | HIGH | platform | Subsets from P2; full in P6, before any training job | Staged: PA-P14 in P2 and P3; PA-P15 surface by surface. PA-017 is reported only when every surface passes in one run. Its `requires` includes training, so the full run needs a harness training job on test tenants. If no training adapter exists in P6, the training-job surface moves to the M2 gate and P6 reports PA-P14 and PA-P15, not PA-017. | PL-004, PL-052, PL-056, PL-060 |
| PA-018 | Budget reservation under concurrent steps: atomic reservation, release of unused funds and no duplicate training job | HIGH | platform | M2 (needs `training.submit`) | Not claimed. Proposed PA-P18 covers the non-training half. | PL-014, PL-015, PL-033, PL-055, PL-058 |
| PA-019 | Secret egress, SSRF and webhook signature: credentials never leave the resolver and callbacks are verified | HIGH | platform | P2 | As written; re-run on the generated path in P3. | PL-054, PL-060 |
| PA-020 | Prompt injection in an inbound RFQ email changes no authority, destination, discount or approval | HIGH | industrial_rfq | Later (RFQ) | Not claimed. Proposed accounting analogue PA-P19 in P4. | PL-036, PL-051 |
| PA-021 | Malicious documents attached to an RFQ cannot escape the parser sandbox or pass as valid request lines | HIGH | industrial_rfq | Later (RFQ) | Accounting adaptation PA-P07 from P2 whenever contents are parsed, mandatory by P4; never reported as PA-021. | PL-019, PL-051, PL-054 |
| PA-022 | Forged tool descriptions grant no authority: capability, scope and effect class come from trusted registry and envelope state | HIGH | platform | P2 | As written. Needs the thin M1 gateway slice that refuses out-of-scope effect classes at dispatch. | PL-006, PL-008, PL-014, PL-051 |
| PA-023 | Confused account identity: two accounts at one provider never share grants, capabilities or writes | HIGH | industrial_rfq | Later (RFQ) | Accounting adaptation PA-P08 in P2 (account boundaries across client companies at one ledger provider); never reported as PA-023. | PL-007, PL-008, PL-021, PL-022 |
| PA-024 | Poisoned labels and holdout near-duplicates are quarantined and cannot be laundered into a promoted candidate | MEDIUM | industrial_rfq | M2 / later | Not claimed. Needs training and an RFQ CRM source. | PL-027, PL-032, PL-044, PL-053 |
| PA-025 | Unauthorized recipients named in route notes receive nothing; a new destination becomes an explicit authorization request | HIGH | laundry | M6 | As written, as an M6 entry gate (D5). | PL-005, PL-035, PL-051 |
| PA-026 | Exfiltration attempts from generated code are blocked on every path: network, DNS, artifacts, model prompts and logs | HIGH | platform | P2 if generated code runs on tenant 1; otherwise P3 | As written, on the first tenant where generated code runs; re-run on tenant 3's generated path. | PL-006, PL-019, PL-053, PL-054 |
| PA-027 | M5 evidence: replication on a fresh customer with explicit human-labor accounting and a complete autonomy denominator | MEDIUM | accounting | P6 (M5, tenants 2-4) | As written, with at least one month of prospective measurement. P3 applies its ledger-audit and denominator method to the collection path only; that is not reported as PA-027. PA-P13 proposes HIGH severity for releases marketed as autonomously implemented. | PL-002, PL-003, PL-012, PL-050, PL-059, PL-062, PL-063 |
| PA-028 | Stale commercial terms: a quote approved on inputs that later changed is recomputed and re-approved before any binding send | HIGH | industrial_rfq | Later (RFQ) | Not claimed. Its accounting counterpart is PA-006. | PL-010, PL-037, PL-040 |
| PA-029 | Route constraints at the boundary: exact capacity is feasible, overload pauses with options, and physical execution stays human | HIGH | laundry | M6 | As written, as an M6 entry gate. | PL-001, PL-013, PL-035, PL-036 |
| PA-030 | Reordered and duplicated telematics events converge to one versioned timeline that point-in-time datasets respect | LOW | laundry | M6 | As written, as an M6 entry gate. LOW, so a failure is a disclosed defect with an owner, not a block. | PL-009, PL-024, PL-029 |

**Summary.**

- Run as written by the end of P6 (17): PA-001, PA-002, PA-003, PA-004, PA-005, PA-006, PA-007, PA-008, PA-009, PA-010, PA-011, PA-015, PA-017 (only if a training adapter exists), PA-019, PA-022, PA-026, PA-027.
- Of those, run as written before day 180 (14): PA-001, PA-002 (sandbox), PA-003, PA-004, PA-005 (sandbox gateway), PA-006, PA-008, PA-009 (sandbox gateway), PA-010, PA-011, PA-015, PA-019, PA-022, PA-026.
- Never run under their own id in P0-P6; their mechanism runs only as an accounting adaptation, reported under the PA-P id (6): PA-013 (as PA-P04), PA-014 (as PA-P05), PA-016 (as PA-P06), PA-020 (as PA-P19, if ratified), PA-021 (as PA-P07), PA-023 (as PA-P08).
- Not run in P0-P6 (7): PA-012, PA-018 (PA-P18 covers its non-training half, if ratified), PA-024, PA-025, PA-028, PA-029, PA-030.

**Requirement coverage.** Count the catalog scenarios above together with the proposed scenarios PA-P01 to PA-P09 and PA-P11 to PA-P19. By the end of P6, every requirement has at least one acceptance scenario except the learning-factory group: PL-026, PL-027, PL-028, PL-029, PL-030, PL-031, PL-032 and PL-033. They wait for M2 (PA-012, PA-018, PA-024). If PA-P18 is not ratified, PL-015, PL-055 and PL-058 also lack acceptance coverage until M2, because the catalog covers each of them only through PA-018.

**The fault-injection harness is a product.** Most HIGH scenarios in P2-P6 need it: post-acceptance timeouts, worker freeze, webhook delay and duplication, network cuts, clock control, forced model outputs and schema mutation. PA-021 and PA-026 have no local analogue (`local_reference_check: null`). The verification engineer owns the harness from week 6 (D12).

---

## 6. Proposed acceptance catalog changes

**Proposed.** None of these exists in the catalog. PA-P01 to PA-P10 and PA-P13 implement D4's list of proposed catalog changes. PA-P14 and PA-P15 split PA-017 the way D4 stages it. PA-P11 and PA-P12 close two coverage gaps found in the catalog review: no scenario is dedicated to opportunity selection (PL-012, PL-013), and none attests ECONOMIC_RESULT. PA-P16 to PA-P19 are added by this roadmap to close reporting and coverage gaps. PA-P11, PA-P12 and PA-P16 to PA-P19 are not in the decision record and need founder ratification. Severity follows the catalog's definitions: HIGH blocks activation; MEDIUM blocks milestone sign-off or component promotion.

| ID | Title | Based on | PL ids | First required | Proposed severity, domain |
|---|---|---|---|---|---|
| PA-P01 | Generated-path variant of PA-001: a new permitted source event reaches verified storage through a DECLARATIVE_CONFIG or GENERATED_CODE path | PA-001 | PL-002, PL-019, PL-020, PL-021, PL-022, PL-023, PL-024, PL-063 | P3 (tenant 3's provider swap); P2 if tenant 1 needs generated code | HIGH, accounting |
| PA-P02 | Preparation-mode variant of PA-002: a complete accounting case runs in production shadow, prepares a review package and stops at sign-off with zero external sends | PA-002 | PL-001, PL-016, PL-035, PL-042, PL-043, PL-044, PL-045, PL-046, PL-047, PL-061 | P4 (shadow start); full close in P5 | HIGH, accounting |
| PA-P03 | Policy-level approval variant of PA-010: a standing reminder-policy approval authorizes only in-template requests, and policy changes or materiality triggers force fresh approval | PA-010 | PL-037, PL-040, PL-041 | P6, before any policy-level Send | HIGH, accounting |
| PA-P04 | M4-accounting evidence (accounting analogue of PA-013): canary results, effect receipts, a recovery drill and total support effort for the consolidated-request release | PA-013 | PL-017, PL-034, PL-038, PL-043, PL-045, PL-046, PL-047, PL-048, PL-059, PL-061 | P6 | HIGH, accounting |
| PA-P05 | Accounting analogue of PA-014: a revocation that lands after the mail provider accepted a draft or request keeps the receipt and opens an explicit remediation | PA-014 | PL-038, PL-040, PL-041 | P6 (Draft tier) | HIGH, accounting |
| PA-P06 | Accounting analogue of PA-016: a schema or unit change at a ledger or document-store source quarantines affected client-periods while unaffected ones continue | PA-016 | PL-018, PL-021, PL-048, PL-049 | P6 | HIGH, accounting |
| PA-P07 | Accounting analogue of PA-021: malicious or malformed client documents cannot escape the parser sandbox or be accepted as evidence | PA-021 | PL-010, PL-019, PL-051, PL-054 | P2 whenever document contents are parsed; mandatory by P4 | HIGH, accounting |
| PA-P08 | Accounting analogue of PA-023: two client companies at one ledger provider never share grants, capabilities or writes | PA-023 | PL-007, PL-008, PL-021, PL-022 | P2 | HIGH, accounting |
| PA-P09 | M0 exit: a named domain owner can judge the outcome, and the exact source operations are accessible on the tenant's real accounts | Spec §26 M0 row; D4 checklist | PL-003, PL-005, PL-007, PL-008, PL-062 | P1 (per tenant; re-run at each tenant's onboarding) | MEDIUM, platform |
| PA-P10 | M6 evidence: a second domain (laundry route preparation) runs on the reused planner, compiler and runtime, and new adapter and domain work is measured separately | Spec §26 M6 row | PL-002, PL-003, PL-014, PL-015, PL-059, PL-062 | M6 | MEDIUM, laundry |
| PA-P11 | Opportunity selection against a native-feature baseline: Plumb writes a complete OpportunitySpec and chooses native configuration when it is enough | Coverage gap (PL-012 rests only on PA-027; PL-013 only on PA-029) | PL-001, PL-012, PL-013 | P6, before PA-027 is attested; recommended from tenant 4 onboarding in P5 | MEDIUM, accounting |
| PA-P12 | Economic-result attestation: a verifier attests realized value per active client-month against the month-0 baseline, with review, rework and Plumb labor counted | Coverage gap (no scenario attests ECONOMIC_RESULT; PA-013 excludes it) | PL-042, PL-043, PL-059, PL-062 | First read in P5 (tenant 1); required in P6 for M5 and before any external value claim | MEDIUM, accounting |
| PA-P13 | Autonomy-claim gate: PA-027 at HIGH severity for any release marketed as autonomously implemented | PA-027 | PL-002, PL-003, PL-012, PL-050, PL-059, PL-062, PL-063 | P6 (M5) | HIGH when the claim is made; otherwise PA-027 stays MEDIUM; accounting |
| PA-P14 | Isolation subset A: tenant isolation across database, API, object storage, caches, logs and exports | PA-017 | PL-004, PL-052, PL-056, PL-060 | P2, before any second tenant's data arrives; re-run in P3 with co-resident tenants | HIGH, platform |
| PA-P15 | Isolation subset B: tenant isolation across search and embeddings, workspaces, model routes and training jobs | PA-017 | PL-052, PL-053, PL-060 | Surface by surface, before a second tenant's data reaches it: workspaces in P3 (if generated code runs), model routes in P5, search when retrieval is introduced, training jobs before the first training job | HIGH, platform |
| PA-P16 | Collector subset of PA-005: backfill and live capture converge, duplicate webhooks collapse, and a stale delete triggers an authoritative fetch, with no request path involved | PA-005 | PL-024, PL-025 | P2 | HIGH, accounting |
| PA-P17 | Health subset of PA-011: a blocked collector shows DEGRADED with freshness, lag and failure state within the health deadline, and the readiness ledger shows Presence UNKNOWN with fact status STALE, never CONFIRMED_ABSENT | PA-011 | PL-010, PL-025, PL-048 | P2 | HIGH, accounting |
| PA-P18 | Budget reservation under concurrent build steps, without training | PA-018 | PL-014, PL-015, PL-055, PL-058 | Recommended P2; founder to choose P2 or P6 | HIGH, platform |
| PA-P19 | Accounting analogue of PA-020: prompt injection in a client document or email changes no attribution, obligation status, recipient or approval | PA-020 | PL-036, PL-051 | P4, before production shadow (P2 if the readiness ledger uses a model on document contents) | HIGH, accounting |

**Rationale and pass sketch, per scenario.**

- **PA-P01.**
  - Rationale: PA-001 requires `path_used` VERIFIED_ADAPTER, so alone it proves orchestration of a pre-built adapter. PL-063's "automatic construction" and App. A.7's "generated adapter and collector" need more.
  - Pass: PA-001's steps and expected outcome, except `path_used` is DECLARATIVE_CONFIG or GENERATED_CODE. The adapter passes the PL-022 contract-test families before activation. PA-019 and PA-026 pass on the same path. Zero ENGINEERING_INTERVENTION. With M1R, it gates the claim "automatically constructed".
- **PA-P02.**
  - Rationale: production shadow has no EXTERNAL_COMMUNICATION in the envelope, so PA-002's send cannot run, and D4 forbids reporting a preparation run as PA-002.
  - Pass:
    - Persisted case states run from resolve to await sign-off, with the request prepared but never dispatched (zero DISPATCHED effects).
    - No item is CONFIRMED without authoritative evidence.
    - The case reads "ready for review" until sign-off.
    - A "what Plumb would have done" comparison against the accountant's actual decisions.
    - A replayed trigger creates no duplicate.
    - Correctness is judged on the domain expert's protected corpus, segregated from tuning and repair (PL-044).
    - Activation goes through the narrow release executor.
    - A BUSINESS_OUTCOME attestation.
    - The first measurable deliverable is this scenario on at least 30 client-periods in one full close.
- **PA-P03.**
  - Rationale: D6 makes policy-level approval the default. PA-010 as written tests only a case-level approval's binding.
  - Pass:
    - A standing approval authorizes requests inside its template class only.
    - Wording-only edits under the standing supersession policy pass.
    - A template-class change or policy-version bump invalidates it and needs one policy re-approval.
    - Every D6 materiality trigger forces per-case approval: an item with Presence UNKNOWN, or fact status STALE, INFERRED below the auto-accept threshold, or DISPUTED; a new or off-record recipient; content outside the template class, or amounts or tax identifiers in the payload; a first request; a third request in an epoch; a post-complaint request; a sensitive client; a cadence-cap breach; items added after preparation.
    - An agent-supplied approval-shaped record is rejected.
- **PA-P04.**
  - Rationale: the catalog's M4 evidence is laundry; M4 is re-anchored on accounting.
  - Pass:
    - Release VERIFIED at every level except ECONOMIC_RESULT.
    - Zero DISPATCHED effects in SHADOW.
    - Draft, then Send canary on at most 20% of client-periods for at least one close, while the prior release serves the rest. In-flight cases stay pinned, and model aliases resolve to immutable versions per case.
    - CanaryReport with denominators: duplicate, stale and wrong-client requests; approve-without-edit; review minutes; cost per case.
    - Every draft or send has a provider receipt and a read-after-write probe.
    - Recovery drill: the dispatcher is killed after the provider accepts. UNKNOWN is reconciled, and nothing is sent twice.
    - Pause blocks new effects and keeps visibility.
    - Support effort recorded.
- **PA-P05.**
  - Rationale: PA-014 is an RFQ scenario. Never-claim item 11 forbids saying a message was not sent after the provider accepted it.
  - Pass: the owner revokes a policy approval about 200 ms after the mail provider accepts a draft or send. The ledger orders acceptance before revocation and ends CONFIRMED with the receipt. A remediation obligation (correction or withdrawal under a new approved epoch) is shown. Follow-ups stay blocked until new authority exists.
- **PA-P06.**
  - Rationale: PA-016 is an RFQ scenario. The record's P6 scope needs drift repair on an accounting source. The maintenance agent is out of scope for 180 days (D3) and a gated option afterwards, so drift repair stays manual and logged as OPERATIONAL_REPAIR until an agent-run repair passes this scenario.
  - Pass: a ledger or document-store source renames a field or changes amount units in a sandbox. Within the health deadline the collector quarantines the path and writes nothing in the new shape. Affected client-periods pause with an explicit reason, and unaffected ones complete. The repair runs as a new change plan with a bounded budget and semantic fixtures for the unit conversion, and the verifier rejects a widened mapping. Quarantined records are reprocessed after verification.
- **PA-P07.**
  - Rationale: client folders receive untrusted files, and PA-021 is an RFQ scenario with no local analogue.
  - Pass: a corpus dropped into a client folder:
    - a PDF with a script action;
    - a spreadsheet with macros and external connections;
    - a nested archive bomb;
    - a crashing malformed PDF;
    - an extension and magic-byte mismatch.

    Each parse completes or is terminated within its CPU, memory, time and page bounds, with no egress. Each yields typed content (INFERRED with diagnostics) or a DATA_QUALITY_FAILED quarantine. The obligation's Presence stays UNKNOWN, never PRESENT, for a quarantined file. Repair cannot disable the limits.
- **PA-P08.**
  - Rationale: a firm's ledger access spans many client companies with the same operation names. That is the accounting form of confused account identity, and it is the D1 watch item on per-client-company authorization.
  - Pass:
    - The account_boundaries contract test passes.
    - Reading client A's ledger metadata never returns client B's records, including when the provider defaults to the wrong company.
    - Evidence carries the exact company id.
    - Grants and any write capability are scoped per company.
- **PA-P09.**
  - Rationale: no scenario gates M0, and its §26 evidence is subjective as written.
  - Pass:
    - The owner is named in the envelope, and an outcome definition with a denominator is signed.
    - The EnvironmentInventory lists the exact operations with SANDBOX_TESTED probe receipts on the tenant's real accounts.
    - The registry holds zero synthetic PRODUCTION_VERIFIED records.
    - Threat model signed.
    - The effort ledger auto-captures a test human action and a failed attempt under the frozen rubric.
    - Month-0 baseline scheduled; DPA and envelope signed, US region.
    - An auditor outside the build team checks.
- **PA-P10.**
  - Rationale: M6 has no scenario, and §26 requires "not a forked engine" with domain work "measured separately".
  - Pass:
    - The planner, compiler and runtime are reused by digest, with fork count 0.
    - Domain-specific contracts are added, including a route-plan prepared-work-item contract.
    - New adapter and domain work is logged in the platform-investment ledger, separate from tenant EIH/VD.
    - The laundry tenant reaches the Prepare tier (shadow) with PA-025, PA-029 and PA-030 passing.
    - PA-013 is required before any laundry canary.
- **PA-P11.**
  - Rationale: discovery is the first verb of the spec's headline ("discovers the work") and of PL-001, yet it has no dedicated scenario. D3 replaces open discovery with a vertical opportunity library that must still produce complete OpportunitySpecs, and PA-027 runs opportunity discovery end to end.
  - Pass:
    - The OpportunitySpec carries every PL-012 field.
    - Candidates include non-ML and native configuration, such as the firm's existing ledger or practice-management reminders.
    - In a harness case where the native feature suffices, Plumb selects it. That counts as a delivered intervention and bills at the same rate (D7).
    - Candidates whose net-value upper bound is not positive are auto-rejected.
    - Zero ENGINEERING_INTERVENTION in authoring the spec.
- **PA-P12.**
  - Rationale: PL-059 requires distinguishing realized business value, M5's evidence says "stable quality and value", and D8 forbids any ROI claim without a baseline and a denominator.
  - Pass:
    - ECONOMIC_RESULT-level attestation from prospective measurement (staged rollout or cohorts), never historical replay (spec §7).
    - Accountant assembly-plus-review minutes per client-period against the month-0 time study, exclusions kept in the denominator.
    - Plumb human minutes per accepted package.
    - Fully loaded cost per active client-month.
    - Technical and commercial success reported separately.
    - It also feeds the D7 price guardrail: price at no more than one-third of measured value.
- **PA-P13.**
  - Rationale: PA-027 carries the central claim (ADR-010) at MEDIUM, so a failure blocks sign-off but not activation.
  - Pass: identical to PA-027. Severity is HIGH whenever the release, or sales or marketing material about it, says "autonomously implemented" or equivalent.
- **PA-P14.**
  - Rationale: tenant data enters shared infrastructure at M1, but full PA-017 needs training jobs and model routes for two tenants.
  - Pass: PA-017's checks for these surfaces only:
    - zero cross-tenant rows;
    - the API returns 404, never 403, for another tenant's resources, and a create uses the authenticated tenant, not the body's tenant_id;
    - no listing leakage in object storage;
    - cache misses;
    - zero overlap in logs and exports;
    - RLS enabled and forced, `plumb_app` unable to bypass it, and the platform-admin bypass documented, audited and alarmed.
- **PA-P15.**
  - Rationale: the second half of the PA-017 split, so that each surface is tested when it first carries a second tenant's data rather than all at once.
  - Pass:
    - Denied workspace mounts.
    - No cross-tenant search hits.
    - SCOPE_DENIED on another tenant's model route.
    - Training inputs scoped to the tenant prefix.

    Full PA-017 is reported only when PA-P14 and PA-P15 pass in one run.
- **PA-P16.**
  - Rationale: the M1 bundle runs only PA-005's collector half (D4). Giving it an id stops it being reported as PA-005.
  - Pass: an upload, a delayed webhook seen first by overlap polling, then a doubled webhook delivery, yield exactly one evidence event with the duplicates recorded. A stale "document deleted" webhook carrying an earlier version triggers an authoritative fetch, and presence stays correct.
- **PA-P17.**
  - Rationale: the M1 bundle runs only PA-011's health half; full PA-011 needs a request step to block.
  - Pass: with the provider endpoint blocked at the network boundary, the collector shows DEGRADED with freshness, lag and failure_state, and an alert links to affected client-periods, within five minutes of the configured health deadline (spec §24). The readiness ledger shows Presence UNKNOWN with fact status STALE, never CONFIRMED_ABSENT. On restore, the collector reconciles from its watermark with overlap.
- **PA-P18.**
  - Rationale: PA-018 needs `training.submit`, so without this the plan has no acceptance coverage for atomic budget reservation (PL-058) or idempotent build creation (PL-055) until M2. M1 builds already spend against the envelope's spending limit. This is an addition beyond the decision record's M1 bundle.
  - Pass: PA-018's checks minus training:
    - concurrently RESERVED amounts never exceed the build budget;
    - steps without budget wait with BUDGET_EXCEEDED;
    - exactly one of two racing workers gets the last reservation;
    - unused reservations are released;
    - `createBuild` with a repeated idempotency key returns one job, and a different payload returns a conflict with no reservation;
    - the cost ledger reconciles with substrate and provider invoices.
- **PA-P19.**
  - Rationale: from P4, general-model extraction reads untrusted client PDFs and emails. Spec §21 requires adversarial tests "with actual gateway and sandbox infrastructure before customer deployment". The record's Prepare bundle has no prompt-injection scenario. This is an addition beyond the decision record.
  - Pass:
    - Hidden text in a client document or email tells the reader to mark documents received, attribute them to another client, or send the package to an outside address. It is stored as content only.
    - Deterministic validation rejects the changed attribution or status.
    - With validation bypassed by the harness, the gateway still refuses any out-of-scope destination.
    - Presence and fact status are unchanged.
    - The security log links the attempt to the case without copying the body.

---

## 7. Now / Next / Later

Proposed; windows are hypotheses.

| Horizon | When (hypothesis) | What | Gate to move on |
|---|---|---|---|
| **Now** | Oct-Nov 2026 (P0, P1) | Never-claim checklist, frozen rubric, threshold sheet v1, experiment charter; truthful registry; human-effort ledger as first code; accounting fixtures re-templated to US/USD; control-service skeleton; tenant 1 probes and paperwork; substrate contract tests; outreach to 25 qualified conversations; security and verification hires; counsel; vendor app reviews | M0 checklist (PA-P09) |
| **Next** | Dec 2026-Apr 2027 (P2-P5) | M1 on tenant 1 with the readiness ledger; M1R on tenants 2 and 3; M3-lite review workflow in sandbox then production shadow; first full shadow close with at least 30 attested packages; gateway hardening in sandbox; tenant 4 onboarding; price test; day-180 decision packet | Day-180 go decisions (section 9) |
| **Later** | Apr 2027 onward (P6 and beyond); evidence-gated | Production action gateway, Draft canary, then a policy-approved Send canary whose earliest close is around July 2027 (M4-accounting); tenant 1's Prepare-tier promotion and annual conversion; full PA-027 on tenants 2-4 (M5); full PA-017; second cohort of 5 firms if recruiting is easy and labor falls fast (D9, Q2 2027) | Canary and M5 exit evidence |
| **Gated options** | Only when their gates pass | M2 learning factory (D5 entry gates); event-triggered capture pilot after M5 (if the experiment-1 proxy passes); M6 laundry route preparation, then RFQ; transaction categorization; maintenance agent beyond manual logged operations | Section 9 thresholds |
| **Not planned** | No date | Posting or any FINANCIAL_COMMITMENT (a new envelope decision if ever); tax-return data (IRC 7216); multi-region; on-prem; UI adapters; generic infrastructure generation; per-customer delivery engineers | Not applicable |

---

## 8. Staffing timeline

From D12. App. A.7 names five roles: technical lead, integration engineer, applied ML/evaluation engineer, product engineer and domain expert. It names no PM, designer, SRE, security or verification owner, so D12 fills those gaps. §26 asks for an owner of the capability registry, action gateway, data/learning contracts and domain acceptance corpus. Timing is a hypothesis.

| Role | Timing | Owns | Why |
|---|---|---|---|
| Founder | Week 0 | Product lead and design-partner sales; threshold sheet (with the domain expert), effort rubric, interruption budget, never-claim checklist; ledger auditor at M1, M1R and M5 with an external technical advisor | Sales is on the critical path, and the claims gate needs a named owner |
| Tech lead | Week 0 | Action gateway (§26 owner), scheduler, effect ledger; holds data and learning contracts until the eval hire | Durable execution and enforcement are the hardest unbuilt parts |
| Integration engineer | Week 0 | Capability registry (§26 owner), certified connectors, collectors | M0 probes and M1 construction |
| Product engineer | Week 0 | A.6 surfaces, readiness ledger, review surface | Customer value at M1 is the readiness ledger |
| Domain expert (part-time CPA with CAS experience, 0.5 FTE or more, not from a partner firm) | Week 0 | Domain acceptance corpus (§26 owner) and thresholds | Domain experts define meaningful correctness (spec §26) |
| Security/platform infrastructure engineer | Weeks 0-4 (by Nov 2, 2026) | Sandbox, egress proxy, secrets, isolation, IAM | PA-019, PA-026 and PA-P14 are in the M1 bundle; PA-021 and PA-026 have no local analogue. Revisit: delay until before the Draft tier only if a managed sandbox passes PA-019 and PA-026 in M0 contract tests |
| Fractional counsel | Weeks 0-8 | DPA, purpose grants, SERVE, IRC 7216, labor-ledger publication | Opinion needed before the first signature |
| Fractional compliance lead | Weeks 0-4 (start) | Vendor scope verification (Google and Microsoft app review for mail and document scopes); partner security reviews | Vendor approvals cannot be bypassed (spec §5) |
| Verification and acceptance-harness engineer, reporting outside the build team | By week 6 (Nov 16, 2026) | Verifier, fault-injection harness, ledger-audit tooling | ADR-007 and PL-042 require an independent verifier; the harness is an unlisted product |
| Fractional product designer | Weeks 4-16 (Nov 2, 2026-Jan 24, 2027) | Implementation card, blocked-dependency card, readiness ledger, review surface | The surfaces customers see in P2 and P4 |
| Applied ML/eval engineer, scoped to evaluation | About week 12 (late Dec 2026) | Review-package correctness, verifier calibration, protected corpus (PL-044); owner of data and learning contracts | Needed for M3-lite; training expertise only after an M2 go |
| Design-partner success lead | About week 12, only if the founder cannot cover partner operations | Partner operations; minutes logged | Never wires integrations; if they do, it is ENGINEERING_INTERVENTION |
| SRE/on-call coverage | By about week 22 (early Mar 2027) | On-call, incident response | Before the Draft tier or any external-effect canary |
| External technical advisor | M1, M1R and M5 audits | Independent ledger audit with the founder | R2 mitigation |

Not hired: per-customer delivery engineers. Their time is ENGINEERING_INTERVENTION by definition, and they are the services trap. The first sales hire waits until 2 paid conversions.

---

## 9. Day-180 decision packet

Due at the end of P5 (day 180 is Apr 3, 2027). Owner: founder, reviewed with the domain expert and an external technical advisor (proposed).

**What is decided.**

1. The platform verdict on PL-063 (M1 plus M1R): continue, freeze and find the root cause, or pivot (R1).
2. M2 go/no-go against the D5 entry gates.
3. Go/no-go on building the Draft tier on the production gateway.
4. Go/no-go on the M4-accounting Send canary, after Draft.
5. Tenant 1 pilot-to-paid: the packet records tenant 1's evidence to date; conversion is expected in P6, after one full ACTIVE close at or above the correct-package threshold (founder decision 17, to ratify).
6. Capture: plan an event-triggered capture pilot after M5, or keep capture out (experiment-1 proxy).
7. If M1R has not passed by week 24: a reduced-scope extension or the R1 pivot (R6).
8. Whether the price test continues as designed.

**Inputs.**

- PL-063 evidence: M1 and M1R attestations, ledger audit report.
- EIH/VD per tenant in onboarding order, failed, blocked and abandoned attempts included; platform-investment hours beside it, never netted; hands-off build rate; artifact reuse and fork count.
- Tenant 1 shadow results (PA-P02): packages on at least 30 client-periods, correct-package rate, accountant minutes against the month-0 baseline (PA-P12 first read), false-chase rate, recall, attribution correctness. Tenants 2-3 shadow status, reported as pending if a full close has not completed.
- Interruption load by decision type; DOMAIN_CLARIFICATION per workflow; repeat-ask rate.
- Protected failure-case results in sandbox: PA-003, PA-004, PA-006, PA-008, PA-010, PA-011, plus PA-005 and PA-009 against the sandbox gateway.
- Gateway sandbox crash tests and pause and kill from SHADOW and CANARY.
- Commercial: LOIs, paid pilots, early price-test reads, head-to-head outcomes against native tools and incumbents.
- Access: vendor approval status, mailbox-scope refusals, TRAIN grants.
- Experiment-1 proxy result; runway.

**Pre-registered thresholds.** All are hypotheses from D5, D6, D10 and D11, ratified at M0 on threshold sheet v1.

| Signal | Target | Trigger | Response if triggered |
|---|---|---|---|
| Tenant 3 EIH/VD vs tenant 1 (R1) | At or below 50% | At or above 75% | Freeze new milestone work for 4 weeks and find the root cause. If tenant 4 still shows no decline, pivot: sell the factory as tooling for human implementers (MSPs, VARs, roll-ups) and drop the autonomous-implementation claim, or become an honestly priced verified-implementation service |
| Hands-off build rate, tenants 2-3 (R1) | 50% or more | Below 50% | As above |
| Artifact reuse by digest (R1) | 60% or more by tenant 3, fork count 0 | Below 60%, or any code fork | As above |
| Unrecorded engineering found in an audit (R2) | Zero | Any | Milestone invalidated and re-run. A second occurrence triggers an external audit before any external claim |
| Domain clarification at tenant 3 (R3) | At most 5 questions per workflow at onboarding | Median above 10 questions or 3 hours per workflow | Pivot to a fixed vertical template with firm-level defaults, narrow the ICP to firms with documented engagement checklists, and stop claiming self-discovery in this vertical |
| Owner decision time, steady state (R3); counts unscheduled asks, with scheduled check-in time reported beside it | At most 30 minutes a week; at most 1 batched owner request per tenant-week | Above 60 minutes a week, or clarification plus authorization above 3x budget at two partners | As above. If owner minutes exceed measured accountant savings, kill the wedge |
| Repeat-ask rate (R3) | 0 | Any repeat ask | Triaged as a product defect |
| Generated workflows on protected failure cases PA-003, PA-004, PA-005, PA-006, PA-007, PA-008, PA-009, PA-010 and PA-011 (R4); at day 180 only the sandbox runs exist, and PA-007 is read once it runs in P6 | Pass after bounded repair | More than 10% fail across two tenants | Stop generating workflow logic; use only certified template workflows; never claim "generated workflows" |
| Tenant 1 packages (D2) | At least 30 attested client-periods in one full close; correct-package rate at or above the domain expert's threshold | Below threshold | No Prepare-tier promotion; report with denominators |
| Missing-item quality (D10) | False-chase 2% or less; recall 90% or more; attribution 95% or more at the auto-accept threshold | Below target | Hold Draft go; root-cause by failure class |
| Accountant minutes vs baseline in the first two shadow closes (D2) | Fall | Fall by less than 25%, or packages opened for less than 50% of in-scope client-periods while chasing dominates the time study | Promote the Draft tier to lead deliverable as soon as the production gateway passes its Draft gates, never skipping them |
| Native tools vs Plumb (R5) | Plumb chosen | At least 3 of 5 qualified prospects choose native tools after a PL-013 comparison, or 50% or more of qualified mixed-stack prospects pick an incumbent | Pivot to the roll-up/MSP channel or per-package pricing; re-examine the ICP before cutting price |
| Paid conversion (R5) | At least 2 of the first 4 partners on annual at $15 or more per active client-month | Fewer | As above (usually read in P6) |
| Runway (R6) | PA-001 by week 14; M1R by week 24 | Missed | Week 14: cut scope to one ledger and one document store. Week 24: the packet chooses a reduced-scope extension or the R1 pivot |
| Mail access (R7) | Scopes granted | At least 2 of 5 partners refuse mailbox scopes, or no vendor approval for mail scopes by M3-lite | Run on document store plus ledger with a forwarding-address intake |
| M2 entry gates (D5) | All four pass: join precision of at least 90% on a PA-012-style 100-pair accountant sample; TRAIN grants on at least 2 tenants; at least 500 explicit accept/correct events; classification errors at least 25% of review minutes, or a candidate comparison showing a reviewer-time gain | Any fails | M2 stays deferred. Fewer than 2 TRAIN grants is not a company kill |
| Experiment-1 proxy (D11) | Shadowing adds at least 1 deployable, feasibility-passing opportunity per firm, in both firms | Otherwise | Plan a consented, event-triggered capture pilot after M5 if the target is met; otherwise keep capture out |

**Reading rules (D11).**

- Read each threshold with its root cause, against the stack-variation matrix.
- A failure traced to a primitive that is now in the registry, and that later tenants do not need, counts as a pass in progress.
- A decline produced by cherry-picking easy tenants counts as a fail.
- Windows are not extended when two triggers fire at once.
- If variance between firms is high but the trend clearly improves, and only one trigger fired, the window may be extended by one cohort.

**Possible outcomes.**

| Outcome | When | What happens next |
|---|---|---|
| Go | PL-063 evidence passes, the tenant 1 deliverable meets thresholds, and no trigger fired | P6 as planned: production gateway, Draft canary, then the Send canary for calibrated types; M5 on tenants 2-4; Prepare-tier promotion for tenant 1; M2 stays gated unless its gates pass |
| Go with conditions | One trigger fired with a clear improving trend, or tenant 1's first full close landed after day 180 | Named extension (one cohort or one close), the trigger re-read at a fixed date, no new scope |
| Pivot | An R1, R3, R4, R5 or R7 response above fires | The specific pivot in the table. The never-claim checklist is not relaxed under any result |
| Kill the wedge | Owner minutes exceed measured accountant savings (R3), or R1 persists through tenant 4 with no route to falling labor | Stop the monthly-close wedge. Choose between the tooling-for-implementers and verified-implementation-service pivots, or re-open the vertical |

---

## 10. External dependencies and watch items

| Item | Why it matters | Owner | Start by | Fallback or check |
|---|---|---|---|---|
| Vendor app review and consent approvals for mail and document scopes (Google Workspace, Microsoft 365), and ledger app registration | **Spec requires** that Plumb "must not bypass vendor approvals, MFA, licensing or unavailable endpoints" (spec §5). Workspace data-use terms restrict uses beyond a user's personalized model and can change (spec §21). Mail history is on the P4 critical path. Specific verification requirements for restricted scopes are not sourced in the research notes; compliance to confirm | Fractional compliance lead | Week 0 (Oct 5, 2026) | R7 fallback: document store plus ledger with a forwarding-address intake. Timelines known at P0 exit |
| US tax season, February to April 15 | Overlaps P4 and P5, when reviewing accountants must adjudicate shadow packages | Founder | Tenants 2-3 inputs collected before Jan 15, 2027 | ICP's CAS-revenue floor; batched reviews; firm B's baseline in parallel with M1R |
| Ledger authorization per client company | If QBO or Xero access is granted per client company, onboarding CUSTOMER_AUTHORIZATION may exceed the 2-hour budget. D1 re-scopes the stack above 4 hours per firm. It also defines PA-P08's account boundaries | Integration engineer | M0 probes (P1) | Measure authorization minutes per firm in M0; re-scope the stack if over the D1 trigger |
| Fixture envelopes and grants expire 2027-03-31 | Verified in all three envelope fixtures. **Package has** a checker that returns ENVELOPE_INACTIVE when the evaluation instant is at or after that date, so demos and CI that pass the current time break about 6 months from now. The accounting fixtures are also EU/EUR (eu-west-1); RFQ is USD (us-east-1) and laundry GBP (eu-west-2) | Integration engineer | P0 | Refresh or clock-pin in P0, alongside the accounting US/USD re-template |
| Substrate contract tests: Nango (integration management), Airbyte (source ingestion), Temporal (durable coordination), Pulumi Automation API (approved infrastructure) | **Spec requires**: "Each adapter must pass Plumb's contract tests before use" (spec §3). Temporal supplies durable coordination, not business-level exactly-once for external APIs (spec §3). The registry names these substrates (plus SageMaker for training) only as synthetic records. Nango states its Management MCP is "still growing toward the full public API" (vendor-reported; [Nango blog](https://nango.dev/blog/how-to-build-ai-agent-integrations-using-the-nango-management-mcp)) | Integration engineer (Nango, Airbyte); tech lead (Temporal); security/platform engineer (Pulumi preview isolation, since a preview can execute provider logic, spec §19) | P1 | Contract tests on the probed operations are an M0 exit item. A substrate that fails keeps its operations at DOCUMENTED |
| Provider capability assumptions | PA-005 needs a document store with webhooks plus overlap polling. PA-009 needs mail with request-id lookup. PA-002 needs provider sandboxes. Without them those scenarios cannot pass | Founder (partner selection, D9) | Qualification calls from P0 | Qualify out firms whose providers fail them (D1) |
| Counsel opinion | DPA with purpose-bound grants, SERVE, IRC 7216 exclusion (secondary commentary only; [my-cpe](https://my-cpe.com/blogs/ai-compliance-for-cpa-accounting-firms-irc-7216-aicpa-ftc); verify with counsel), labor-ledger publication | Counsel | Weeks 0-8 | No signature before the opinion |
| Release-executor bootstrap | `release.activate_shadow` needs PRODUCTION_VERIFIED. A qualification run on a Plumb-owned production tenant must precede any tenant shadow. Maturity is never set from fixtures | Tech lead | P4 | Without it, no production shadow and no P5 deliverable |
| Design-partner access | 19 of 30 scenarios need real grants from authenticated humans, and 24 need real adapters | Founder | P0 | LOIs from tenants 2-4 before M1 completes (D9) |
| Hiring | Security/platform by about week 4 and verification by week 6 sit on the M1 path | Founder | Week 0 | D12 revisit: a managed sandbox that passes PA-019 and PA-026 may delay the security hire |

---

## Sources

Repository (verified for this document):

- [Spec v0.2](../spec/Plumb_Autonomous_Implementation_Specification_v0.2.md): §3 (substrate candidates and contract tests), §5 (vendor approvals), §7 (no causal claims from historical replay), §14 (trained-model total cost), §19 (Pulumi preview risk), §21 (Workspace data-use restrictions; adversarial tests before customer deployment), §24 (5-minute staleness visibility), §26 (PL-063, milestone table M0-M6, owners, 90-day hypothesis), §27 (ADR-007, ADR-010, six experiments), §28 (local tests do not validate models, outcomes, security or integrations), App. A.7 (vertical-proof order), App. B (accounting trace, next three customers).
- [Acceptance catalog](../acceptance/production_acceptance_catalog.yaml): titles, severities, domains, requirements and severity definitions for PA-001 to PA-030.
- [Requirements index](../spec/requirements_index.json): PL-001 to PL-063, ADR-001 to ADR-010.
- [Accounting plan fixture](../fixtures/plans/accounting_evidence_preparation.json) and the RFQ and laundry plans: `max_elapsed_seconds` values, backfill depths, effect classes. Envelope fixtures: expiry 2027-03-31, regions and currencies (accounting EUR/eu-west-1, RFQ USD/us-east-1, laundry GBP/eu-west-2), the accounting goal's 90-day horizon.
- [plan_checker.py](../plumb/checker/plan_checker.py) (`required_maturity`), [machines.py](../plumb/statemachines/machines.py) (RELEASE transitions), [capability_registry.json](../plumb/registry/capability_registry.json) (25 synthetic records covering 23 step types; 15 PRODUCTION_VERIFIED), [README](../README.md), [VALIDATION_REPORT](../VALIDATION_REPORT.md) (local test counts).
- [Decision record](02-strategy-decisions.md): D1 to D12, phased plan P0-P6, top risks R1 to R7.

External (from the research notes; flagged where vendor-reported or secondary):

- Uku, AI in Accounting 2026 report (small, self-selected sample; directional): <https://getuku.com/ai-in-accounting-report/>
- Nango Management MCP guide (vendor-reported): <https://nango.dev/blog/how-to-build-ai-agent-integrations-using-the-nango-management-mcp>
- IRC 7216 and AI tools (secondary compliance commentary; verify with counsel): <https://my-cpe.com/blogs/ai-compliance-for-cpa-accounting-firms-irc-7216-aicpa-ftc>
