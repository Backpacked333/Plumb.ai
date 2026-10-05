# Metrics and Measurement Plan

- Status: Draft v0.1 (2026-10-04), proposed — requires founder ratification
- Owner: Product
- Basis: spec v0.2, [decision record](02-strategy-decisions.md)

Part of the product doc set ([index](README.md)). This document defines what Plumb measures, how each number is computed, where the data comes from, when it first exists, and who owns it. It elaborates D6 (approvals, interruption budget, effort rubric), D10 (north star and supporting metrics) and the metric-based triggers across the [decision record](02-strategy-decisions.md) (section 4.6). Scope and surfaces are in [MVP scope](03-mvp-scope.md), phases in the [roadmap](04-roadmap.md), work items in the [backlog](05-backlog.md), kill criteria in [risks and assumptions](07-risks-and-assumptions.md), and partner obligations (baseline study, ledger publication) in the [design-partner program](09-design-partner-program.md).

**How to read this document.** Three kinds of statement are kept apart:

- **Spec** — what the [spec](../spec/Plumb_Autonomous_Implementation_Specification_v0.2.md) or the [acceptance catalog](../acceptance/production_acceptance_catalog.yaml) requires.
- **Package** — what the reference package in this repository implements today, verified in code.
- **Proposed** — what this document proposes.

**Nothing in this document has been measured.** There is no tenant, no effort ledger, no telemetry and no review surface. Every target is a hypothesis unless the spec states it. Decision-record targets go into threshold sheet v1, which the domain expert issues in P0 and which is ratified at the M0 exit (P1) by the domain expert and an external technical advisor. Each table says this once rather than on every line.

---

## 1. Measurement principles

| # | Principle | Source | What it means in practice |
|---|---|---|---|
| 1 | Denominators include failed, blocked and abandoned attempts | PL-062 (spec §25 L388); spec App. B L650; PA-027 | Every rate names its numerator and denominator. Excluded items stay in the denominator and are listed by reason. A tenant with logged hours and no verified deployment is reported as "N hours, 0 verified deployments", never dropped. |
| 2 | Technical and commercial success are recorded separately | spec §24 L382; PA-027 | A verified package the accountant does not use is a technical pass and a commercial miss. Reports carry both columns. |
| 3 | No ROI or hours-saved figure without a baseline and a denominator | spec §7 L136; D8 never-claim item 9 | Value is measured prospectively, by staged rollout or comparable case cohorts, against the month-0 time study. Historical replay supports no causal claim. Theoretical labor capacity, usable capacity and realized cash are reported separately (spec §7 L136). |
| 4 | Implementation autonomy is measured separately from runtime autonomy | ADR-010 (spec §27 L440); PL-062 | EIH/VD measures the human labor of building and keeping deployments working. A runtime measure, such as cases completed without a human, never stands in for it. |
| 5 | Plumb's own labor is measured | PL-059 (spec §24 L372); PL-003 | Plumb engineering, repair and support minutes are reported next to inference and infrastructure cost and next to the customer's review and rework. Deployments stay labeled "supervised", with their labor shown, until that path has PA-027-level evidence (D8). |
| 6 | Local test counts are never product metrics | spec §28 L450; D8 never-claim items 1 and 8 | The local contract tests (counts in the [validation report](../VALIDATION_REPORT.md); the spec's "56 tests" in its header table and Appendix C is stale), schema and API counts, and the [registry's](../plumb/registry/capability_registry.json) 25 synthetic capability records (23 step types; 15 marked PRODUCTION_VERIFIED) describe the reference package, not the product. |
| 7 | Thresholds are task-specific, pre-registered hypotheses | spec §24 L382; D11 reading rules | No universal 99% bar. Thresholds are not moved after results arrive. A change is a new, dated sheet version with reasons, applied prospectively. |
| 8 | Only verifier attestations count as "verified" | PL-042; ADR-007 | A build agent's completion claim, a deployment response or a green dashboard never counts. "Verified deployment" and "attested package" mean an independent verifier attestation exists. |
| 9 | Report per tenant, in onboarding order | D10; D11 | Pooled figures appear only beside the per-tenant view. Offboarded and blocked tenants stay in the report. A decline produced by cherry-picking easy tenants counts as a fail (D11). |
| 10 | Explicit acceptance, never absence of edits | spec App. B L624 | A package counts as accepted only after an explicit accept action on the review surface. |
| 11 | Provider delay is separated, and the end-to-end experience is still shown | spec §24 L380 | Plumb-controlled time and dependency time are split, and the customer's total elapsed time is always shown, "so exclusions cannot conceal unusable workflows". |

**Where measurement stands today (verified in code).**

| Capability | Spec | Package today | Proposed first phase |
|---|---|---|---|
| Human-effort ledger | PL-003, PL-062 | `HumanEffortCategory` enum ([common.py](../plumb/contracts/common.py) L235-242). `HumanEffortRecord` model (L611-618) is used nowhere in `plumb/`, has no JSON schema and no API. A `human_effort` table exists only in the unexecuted [SQL design](../sql/001_initial_design.sql) (L814-829). `PrincipalType` has no type for Plumb staff, so Plumb's own labor cannot yet be attributed by principal (gap). | Ledger is the first product code (P0); live with the frozen rubric at M0 (P1) |
| Platform-investment ledger | Not in spec; D3 and D10 | Absent | P1 |
| Outcome accounting | PL-059 | `OutcomeObservation` in the [OpenAPI proposal](../api/openapi.yaml) (L3612, read-only `listOutcomes`) and the SQL `outcome_observations` table. Nothing writes either. | P4 |
| Telemetry | PL-060 | Absent. `correlation_id` and `causation_id` exist only as fields on `EventEnvelope` and `ErrorEnvelope` ([api.py](../plumb/contracts/api.py)) and in the SQL outbox and jobs tables. | P1-P2 |
| Cost metering | PL-058, PL-059 | The checker verifies declared worst-case budgets only (spec §24 L370). `builds.reserved_minor_units` and `spent_minor_units` exist in SQL; nothing writes them. | P2 |
| Review timing and acceptance capture | PL-059; spec App. B L624 | Absent. `ReviewPackage` is an `ArtifactKind` value with no contract. | P4 |

---

## 2. North star: engineering-intervention hours per verified deployment (EIH/VD)

### 2.1 Definition

| Element | Definition |
|---|---|
| Formula | EIH/VD(tenant) = (ENGINEERING_INTERVENTION minutes + OPERATIONAL_REPAIR minutes logged against the tenant's eligible build attempts and deployed components, cumulative to date) / 60 / (verifier-attested deployments for the tenant) |
| Numerator includes | All ENGINEERING_INTERVENTION and OPERATIONAL_REPAIR minutes on the tenant, by anyone, Plumb or customer staff (D6 as amended, founder decision 18), including: failed, abandoned and blocked attempts; any time hand-authoring or editing the tenant's plan, mapping, CollectionSpec or WorkflowSpec (D4); manual deployments (D3); repairs to the tenant's running collectors and workflows; re-runs forced by an audit finding; a design-partner success lead's minutes whenever they wire anything (D12) |
| Numerator excludes (reported elsewhere, never dropped) | CUSTOMER_AUTHORIZATION, DOMAIN_CLARIFICATION and NORMAL_BUSINESS_REVIEW (interruption load, section 7, and review cost, section 4.4). Platform-investment hours (beside the metric). Plumb non-engineering support time, such as check-ins and onboarding calls (cost ledger, sections 4.3 and 4.4). |
| Denominator | Verifier-attested deployments for the tenant: integration-and-collection paths in M1 and M1R, then workflows from M3-lite (D10). Reported by deployment type and combined. |
| Companion | Platform-investment hours triggered by the tenant, shown in the next column and never netted (D10) |
| Grain | Per tenant, in onboarding order. Cumulative to date, plus a per-phase view. Hours to one decimal; the ledger stores minutes. |
| Trajectory hypothesis | Falls with every tenant. Tenant 3 at or below 50% of tenant 1 (M1R pass hypothesis, D4). R1 pivot review if tenant 3 is at or above 75% of tenant 1. Trending toward zero by tenants 4-5 (D10). |
| Phase available | Ledger records entries end to end in P0 and is live with the frozen rubric at M0 (P1). Tenant 1 baseline at M1 (P2). First trend at M1R (P3). Workflow deployments from P4. |
| Owner | Founder: definition, rubric and reporting (D12). Verification and acceptance-harness engineer: computation and ledger-audit tooling, reporting outside the build team (D12, ADR-007). |

**Term definitions (proposed; frozen in rubric v1).**

- **Eligible build attempt.** A build created for an authorized goal of the tenant within the in-scope workflow (one `builds` row from a `createBuild` job), counted from creation until it is VERIFIED, FAILED or CANCELLED, or the tenant is offboarded. Superseded attempts count.
- **Abandoned attempt.** CANCELLED, or no state change for 14 days while not waiting on a customer or vendor dependency.
- **Blocked attempt.** In WAITING_AUTH or WAITING_INPUT at reporting time, or ended because a dependency was never resolved. Builds of a partner offboarded under D9 are recorded as blocked attempts.
- **Verified deployment.** One integration-and-collection path per source system per tenant (for example, document store; ledger metadata), attested PA-001-style; or one workflow per workflow type per tenant, attested through PA-P02 in shadow and later PA-002 in canary. Re-attesting an existing deployment after a repair does not add a deployment. Cross-tenant comparisons use the same set of source systems, and each report lists the deployments counted.
- **Deployed component.** Any collector, connector configuration or workflow release that a verified deployment brought into operation for the tenant. OPERATIONAL_REPAIR on it counts against that tenant for as long as it runs. A split view shows build-phase minutes and post-verification minutes, so deferring repairs past a milestone gains nothing.
- **Platform-investment work.** Work whose product is a reusable primitive in the registry or platform: it has applicability constraints, contract tests and a digest, and it ships through the platform change process rather than a customer implementation job (spec §4 L96; App. A.7 L588). Each entry is tagged with the tenant that triggered it. If it is unclear whether work is tenant-specific or reusable, it goes in the tenant ledger.

**Worked example (invented numbers, not an estimate).** A tenant's document-store path takes three attempts. Two fail after 600 and 420 minutes of ENGINEERING_INTERVENTION (debugging and re-running). The third verifies with zero ENGINEERING_INTERVENTION in its run, so PA-001's condition holds. In the first week, 60 minutes of OPERATIONAL_REPAIR restart a stuck collector. Numerator: 600 + 420 + 60 = 1,080 minutes, or 18.0 hours. Denominator: 1. EIH/VD = 18.0. A reusable webhook-dedup primitive built during the same onboarding (900 minutes) is shown beside it as 15.0 platform-investment hours. A success-only report would have shown 0 hours.

**Report template (proposed; no data exists).**

| Tenant (onboarding order) | Stack variation (D1) | Attempts: verified / failed / blocked / abandoned | EI min | OR min | Verified deployments (path / workflow) | EIH/VD | % of tenant 1 | Platform-investment h triggered | Audit status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Baseline stack | | | | | | 100% | | |
| 2 | Same provider families; different folder and chart-of-accounts conventions | | | | | | | | |
| 3 | One provider swapped (non-VERIFIED_ADAPTER path) | | | | | | | | |

### 2.2 Why this is the north star

- **It encodes the spec's central claim.** PL-062 requires counting manual engineering and failed eligible builds, and ADR-010 separates implementation autonomy from runtime autonomy. PA-027's pass test is "lower engineering intervention" than the first customer, with failed and blocked builds in the denominator.
- **It separates a platform from a services firm.** If tenants 2 and 3 need as much audited engineering as tenant 1, Plumb is a services business (strategy thesis; R1).
- **It is readable early.** It exists from the first M1 build. Accepted packages cannot exist before M3-lite (D10 alternatives).
- **Failure pushes it up.** Failed attempts add minutes without adding deployments, so success-only reporting cannot hide them.
- **It answers the market's distrust.** Trust in fully autonomous agents fell from 43% to 27% in one year (Capgemini). Builder.ai went bankrupt after reports that human engineers stood behind its "AI" (press report). An audited, per-tenant labor number is what a skeptical buyer or investor can check. Sources are at the end.

It is not customer-visible on its own, which is why accepted review packages per month is the customer co-headline (section 3). If EIH/VD improves while collection integrity, correct-package rate or review minutes stall, or partners churn, accepted packages becomes the north star and EIH/VD remains a platform-health gate (D10 revisit trigger).

### 2.3 How EIH/VD can be gamed, and the countermeasures

| Gaming vector | Effect | Countermeasure (proposed unless cited) |
|---|---|---|
| Logging engineering as DOMAIN_CLARIFICATION or NORMAL_BUSINESS_REVIEW | Numerator too low | Category is set by rule from principal type, action and resource, not chosen freely. Plumb staff principals cannot log the three customer categories (this needs the Plumb-staff principal type the contracts lack). Double-coded audit sample (section 6.4). If an audit finds miscategorization, only automatically captured effort counts (D10 revisit trigger). |
| Moving tenant work into the platform-investment ledger | Numerator too low | Platform-investment entries must name the registry primitive they produced, with digest, contract tests and applicability constraints. Every entry carries a triggering tenant and is reported beside EIH/VD. Unclear cases default to the tenant ledger. Reviewed at each audit. |
| Not logging manual work | Numerator too low; invalidates PL-003 | Automatic capture of every human-principal action on tenant resources (D3). Agents get no general administrator credentials and the gateway resolves credentials for approved operations (PL-006); any human console session outside it is break-glass access and is logged (proposed). Monthly audit of the delivery team's account against the ledger using PA-027's method, plus milestone audits at M1, M1R and M5 (D12). Any unrecorded engineering invalidates the milestone and forces a re-run; a second occurrence triggers an external audit before any external claim (R2). |
| Working outside the platform (local scripts, provider admin consoles) | Numerator too low | Break-glass access is logged automatically as ENGINEERING_INTERVENTION or OPERATIONAL_REPAIR. Auditors reconcile provider and substrate admin logs, deploy logs and commit history against the ledger. |
| Splitting one deployment into several | Denominator too high | The deployment unit is fixed in rubric v1 (section 2.1). Re-attestations do not count. Reports list each deployment counted. |
| Choosing easy tenants, or dropping hard ones | Trend flatters | Fixed stack-variation matrix (D1). Onboarding order is locked when each envelope is signed. Offboarded tenants stay in the report with their hours (D9, D11). |
| Resetting or hiding failed attempts | Numerator too low | Each build attempt and step attempt is its own row (`builds` and `build_step_attempts` in the SQL design), and the ledger is append-only (proposed). Effort entries reference build and step-attempt ids (proposed; section 9.5). |
| Doing tenant-specific engineering before the build "starts" | Numerator too low | The tenant ledger opens at LOI signature. Any tenant-specific artifact produced earlier is logged retroactively, with the reason. |
| Letting the customer's staff do the wiring | Numerator too low; turns the customer into the integrator | Spec App. B L652 says to record the labor of "a person" who manually wires integrations. Under the amended D6 rubric (founder decision 18, to ratify), customer-performed wiring is ENGINEERING_INTERVENTION under the customer principal: it counts in EIH/VD and is triaged as an interruption-budget defect (spec §1 L51; App. A.7 L588). |
| Loosening verification so more deployments attest | Denominator too high | The verifier is organizationally independent and not writable by the build (PL-042, ADR-007). The builder cannot change tests or thresholds (spec App. A.1). Thresholds are pre-registered. |

---

## 3. Customer co-headline: accepted review packages per month

**Definition (D10).** Count the client-periods in the month where all of these hold:

1. A verifier-attested package reached READY_FOR_REVIEW before the firm's close deadline.
2. The reviewing accountant explicitly accepted it without material correction. Absence of edits does not count as acceptance (spec App. B L624).
3. The package has zero wrong-client attribution.

The count is always shown with two companions:

- **Acceptance rate** = accepted packages / all eligible in-scope client-periods for that close. The denominator includes client-periods that were blocked, terminally failed, not prepared, or prepared after the deadline.
- **Plumb human minutes per accepted package** = all Plumb staff minutes attributed to the tenant for that close / accepted packages. Shown in two parts: engineering (ENGINEERING_INTERVENTION plus OPERATIONAL_REPAIR from the effort ledger) and support (tenant-attributed support and Plumb domain-expert minutes from the cost ledger). This stops disclosed labor from inflating the count.

The accountant's own review minutes per accepted package are shown beside these, against the month-0 baseline (section 8).

**Counting rules (proposed).**

| Rule | Detail |
|---|---|
| Month | The firm's close cycle for a period, not the calendar month in which sign-off happens |
| Eligible in-scope client-period | A recurring client in the agreed cohort (at least 30 per firm for the first measurable deliverable, D2) with a period due in the close |
| Shadow, canary and active | A preparation-only release goes SHADOW (at least one full close; P4-P5), then CANARY on a subset of client-periods whose accountants use the prepared packages in their real review, then ACTIVE, with no EXTERNAL_COMMUNICATION at any stage (founder decision 17, to ratify). Counts are reported per stage ("shadow-accepted", canary, active) and never pooled. |
| Pending sign-off | Packages not yet decided at report time are shown as pending, not as accepted or rejected. If sign-off lag exceeds 2 weeks, or reviewers disagree on "material" more than 20% of the time in a double-coded sample, switch the headline to attested ready-for-review packages, with correction rate as a guardrail plus a material-correction rubric (D10 revisit trigger). |
| Material correction (initial proposal; the domain expert ratifies the rubric) | Material: any change to client, period or obligation list (a required item added or removed); any change to an item's presence status (PRESENT, CONFIRMED_ABSENT, UNKNOWN); any change to a document's attribution; any change to an amount or identifier carried in the package. Not material: notes, ordering, formatting. |
| Relationship to billing | Different unit. D7 bills an active client-month for each verifier-attested package and credits packages the accountant rejects as materially wrong. The co-headline counts explicit acceptance. Both are reported. A partner converts to paid annual only after one full close in ACTIVE at or above the correct-package threshold (D7, D9; founder decision 17). |

**Illustrative arithmetic (not a result).** A firm has 60 eligible client-periods in a close. 45 packages reach ready-for-review on time and 38 are explicitly accepted without material correction, with no wrong-client attribution. The report reads "38 accepted (63% of 60 eligible)", not "84% acceptance" (38 of 45 prepared).

**Phase and owner.** First readable at M3-lite shadow (P4). First full-close reading on tenant 1 in P5, as part of the first measurable deliverable. Owner: founder. The domain expert owns the material-correction rubric. The product engineer owns the sign-off surface's explicit accept, correct and amend capture. If accepted-package metrics look healthy but partners do not renew, the customer headline switches to retained paid client-months (D10 revisit trigger).

---

## 4. Metric catalog

All targets in this section are hypotheses from the decision record (or marked as proposed here), ratified in threshold sheet v1 at M0. Values marked "spec" are the spec's own. "Phase" is the first phase in which the metric can be read; phases are defined in the [roadmap](04-roadmap.md). Owners use the D12 roles. The applied ML/eval engineer (a planned hire around week 12) owns evaluation metrics, and the tech lead holds them until then. SRE coverage (planned by about week 22) owns service targets, and the tech lead holds them until then.

### 4.1 Implementation metrics (platform proof)

| Metric | Definition / formula | Denominator | Data source / instrumentation | Phase | Target (hypothesis) | Owner |
|---|---|---|---|---|---|---|
| EIH/VD (north star) | Section 2 | Verifier-attested deployments per tenant | Effort ledger (auto-capture) + platform-investment ledger + durable build ledger + VerificationAttestation records | P1 ledger; P2 tenant 1 baseline; P3 trend | Falls each tenant; tenant 3 ≤ 50% of tenant 1; R1 review at ≥ 75% | Founder; verification engineer computes |
| Hands-off build rate | Eligible build attempts that reach VERIFIED with zero ENGINEERING_INTERVENTION and zero OPERATIONAL_REPAIR | All eligible attempts started, including failed, blocked and abandoned | Build ledger (`builds`, `build_step_attempts`) joined to the effort ledger by build id (`human_effort.build_id` in the SQL design) | P2; meaningful P3 | ≥ 50% on tenants 2-3; below triggers the R1 review | Tech lead |
| Artifact reuse rate and fork count | Mappings, collection templates and workflow components reused unmodified, matched by content digest, in a new tenant's deployment. Fork count = engine code branches specific to one tenant. | All artifacts in the new tenant's deployment | Artifact store digests (`ArtifactHeader.content_digest` exists in contracts; no artifact store exists) + repository branch audit | P3 | ≥ 60% by tenant 3; forks = 0 (any fork triggers R1) | Integration engineer |
| Outcome mix per authorized goal | Count of verified interventions, actionable dependencies and terminal failures (PL-001), plus median days in dependency split by resolver (customer, vendor, Plumb) | Authorized goals | Build ledger + DependencyRecord. Gap: the contract has `raised_at` but no `resolved_at`, and `resolver_role` is a PrincipalType that cannot express "vendor" (section 9.4). | P1-P2 | Every goal ends in exactly one of the three outcomes; no numeric target for dependency days until P2 data | Product engineer |
| Time to first verified event | Calendar days from envelope signature to an attested PA-001-style event, split into Plumb-controlled time and dependency time. Also days to the first accepted package. | Per tenant | Build ledger timestamps + DependencyRecord intervals + verifier attestations | P2 (first package P4-P5) | None numeric. The 90-day deployment figure is a planning hypothesis (spec §26 L418); the 90-day pilot clock starts at the first attested path (D7). | Founder |
| Implementation-autonomy report (PL-062 components) | End-to-end build completion rate (VERIFIED / eligible attempts); intervention hours; repair attempts per verified deployment (attempts after the first, by failure class); cost per verified deployment | Eligible attempts; verified deployments | Build ledger + effort ledger + cost metering | P2 | Spec sets no numeric target; reported per tenant | Founder |
| Protected failure-case pass rate | Share of the protected Appendix B failure cases (PA-003, PA-004, PA-005, PA-006, PA-007, PA-008, PA-009, PA-010, PA-011, as applicable to the tier) that a generated workflow passes after bounded repair | Failure cases run, per tenant | Verifier runs in sandbox (P4); production gateway (P6) | P4 | Failing more than 10% across two tenants stops generated workflow logic (R4) | Verification engineer |

### 4.2 Quality and customer-outcome metrics

| Metric | Definition / formula | Denominator | Data source / instrumentation | Phase | Target (hypothesis) | Owner |
|---|---|---|---|---|---|---|
| Accepted review packages per month (co-headline) | Section 3 | All eligible in-scope client-periods | Review surface with explicit accept, correct and amend capture (absent) + verifier attestations + effort and cost ledgers | P4 shadow; P5 full close; Prepare-tier CANARY and ACTIVE in P6 | No numeric target until the domain expert sets the correct-package threshold (P4 exit) | Founder |
| Collection integrity | Source changes, injected by the verifier or arriving naturally, that appear exactly once, correctly attributed to client and period, within the 5-minute health deadline. Plus reconciliation gaps and duplicates (PL-024), and the share of health deadlines where staleness was visible within 5 minutes (spec §24 L380). | All sampled source changes; all health-deadline misses | Verifier injection harness + collector health fields (`collectors.freshness_seconds`, `lag_seconds`, `failure_state`, `health_deadline_seconds` in the SQL design) | P2 | Exactly-once and correct attribution on all sampled changes; gaps and duplicates = 0; staleness visible within 5 minutes on every miss (spec) | Integration engineer |
| Missing-item quality | False-chase rate: items flagged missing that were already held. Recall: true missing items flagged. Attribution correctness at the auto-accept threshold, with coverage. Not the experiment-2 read-out (D11). | False-chase: all items flagged missing. Recall: true missing items per accountant ground truth. Attribution: audited samples. | Accountant adjudication samples + review surface + readiness ledger (P2) | P2 (readiness ledger, sampled); P5 (full close) | False-chase ≤ 2%; recall ≥ 90%; attribution ≥ 95% (proposed, D10) | Domain expert (ground truth); eval engineer (computation) |
| Correct review-package rate and accountant minutes | Packages judged complete and correctly attributed by the verifier and the accountant, shown next to accountant assembly-plus-review minutes per client-period against the month-0 time study. Measured prospectively by staged rollout or cohorts; technical and commercial success reported separately. | Eligible client-periods in shadow, canary or active, with exclusions kept in the denominator | Review-surface timing + verifier + month-0 time study (section 8) | P4; P5 full close | Correct-package threshold set by the domain expert (P4 exit). Accountant review minutes per package below baseline assembly-plus-review minutes (D6). | Domain expert (threshold); eval engineer |
| Interruption load | Owner and reviewer decision minutes per tenant-week, by decision type (DATA_USE, IMPLEMENT_OPERATE, CASE_LEVEL_BUSINESS). DOMAIN_CLARIFICATION questions per workflow; decay ratio of close n against close 1; repeat-ask rate; share of requests needing per-case approval. | Per tenant-week; per workflow | Effort ledger by category + approval records (`approvals.decision_kind` in the SQL design) + approval-request records (absent) | P1 (onboarding) | Section 7 budget; repeat-ask rate = 0 (PL-041) | Product engineer; founder owns the budget |
| Client-request integrity (once drafts or sends ship) | Duplicate requests per client-period-obligation; stale or incorrect requests (asking for a document already held, or the wrong client) | Per client-period-obligation; per 100 requests | Effect ledger (`slot_key`, `obligation_id`, `obligation_epoch`, `provider_request_id`) + provider message logs; compared with the 24-month historical baseline (section 8.2) | P6: Draft tier first; the policy-approved Send canary's earliest close is around July 2027 (P5 as "would-have-sent" in shadow reports) | Duplicates = 0; zero duplicate, stale or wrong-client requests reach real clients (P6 exit) | Tech lead |
| Readiness-ledger and package adoption | Share of active bookkeepers at partner firms who use the readiness ledger weekly; share of in-scope client-periods whose package is opened in Plumb | Active bookkeepers; in-scope client-periods | Product usage events (no content) | P2; P4 | D2 triggers: fewer than half of bookkeepers using the ledger weekly runs shadow packages in parallel with M1R; packages opened for under 50% of client-periods in the first two shadow closes (section 4.6) promotes the Draft tier once its gates pass | Product engineer |

### 4.3 Economics and commercial metrics

| Metric | Definition / formula | Denominator | Data source / instrumentation | Phase | Target (hypothesis) | Owner |
|---|---|---|---|---|---|---|
| Fully loaded cost per verified deployment, and gross margin per active client-month | Inference + infrastructure + all Plumb labor at loaded rates, including failed attempts and supervised delivery. Restated per active client-month for gross margin. | Verified deployments; active client-months | Cost metering (absent; spec §24 L370) + effort and cost ledgers at loaded rates | P2 (per deployment); P5 (per client-month) | Pivot trigger: cost per active client-month above 2x price at tenant 4 with no downward trend (D7, R5) | Founder |
| Measured value per active client-month | (Baseline accountant minutes per client-period − current accountant minutes per client-period, review and rework included) × the firm's stated loaded hourly cost. Internal only until PA-P12 attests it. | Active client-months in the measured cohort | Month-0 time study + review-surface timing + firm-supplied cost input | P5 (first internal read) | Price at no more than one-third of measured value (D7). Under about $45 per client-month caps Chase at $15 or folds it into Prepare (D7 trigger). | Founder |
| Commercial conversion | Pilot-to-paid conversion at list price; realized price per active client-month; logo retention | Pilots completed; active partners | Billing records | P1 (pilot invoiced at M0 exit); conversion from P6, after one full close in ACTIVE at or above the correct-package threshold (tenant 1 expected in P6; founder decision 17) | Pivot trigger: fewer than 2 of the first 4 partners convert at $15 or more per active client-month (D7, R5). 3 of 5 is a target, never a kill (dissent record). | Founder |
| Design-partner funnel | Qualified ICP conversations; LOIs; paid pilots signed | Per week, cumulative | CRM | P0 | At least 8 qualified conversations by P0 exit; at least 25 by week 8; tenant 1 signed by about week 4; tenants 2-4 LOIs by week 8 (D9, phased plan) | Founder |

### 4.4 Spec-required outcome accounting (PL-059, PL-062)

| Metric | Definition / formula | Denominator | Data source / instrumentation | Phase | Target | Owner |
|---|---|---|---|---|---|---|
| Model calls, completed cases, correct outcomes, realized value (PL-059) | Four separate counts per case and per release, never merged: model calls; completed cases; correct outcomes (null until the maturation window closes); realized value in minor units | Per case; per release; per close | `OutcomeObservation` (OpenAPI L3612; SQL `outcome_observations`) written by the workflow runtime and review surface. Gap: one nullable `human_effort_category` per case cannot carry multi-category effort (section 9.4). | P4 | Spec sets none. Realized value is reported externally only after PA-P12 attests it. | Eval engineer (tech lead until hired) |
| Customer review and rework minutes (PL-059) | Accountant review minutes per package; rework minutes (amend after accept); bookkeeper minutes on the obligation | Per package; per client-period | Review surface timing + effort ledger (NORMAL_BUSINESS_REVIEW) | P4 | Below baseline (D6) | Product engineer |
| Plumb implementation and support labor (PL-059) | All Plumb staff minutes by tenant: ENGINEERING_INTERVENTION and OPERATIONAL_REPAIR (effort ledger), plus support, onboarding and domain-expert minutes (cost ledger) | Per tenant-month; per verified deployment; per accepted package | Effort ledger + cost ledger | P1 | Reported, never netted | Founder |
| Technical vs commercial success (spec §24 L382) | For each release and close: technical result (attested, correct) and commercial result (accepted, used, billed, renewed) in separate columns | Per release; per close | Verifier + review surface + billing | P4 | Both always reported | Founder |

### 4.5 Service targets (spec §24)

The spec's service targets, quoted exactly (spec §24 L380): "Proposed initial service targets: 99.9% monthly control-plane availability; p95 internal event-to-case propagation below 60 seconds after ingestion; visible connector staleness within five minutes of the configured health deadline; durable restart without losing acknowledged intents; and policy-gateway failure closed for writes. Report provider delay separately and also report end-to-end customer experience so exclusions cannot conceal unusable workflows."

**Proposed.** These are tracked internally from the phase shown. They are not offered to partners as contractual commitments during pilots. D9 limits security commitments to gates actually passed, the same discipline applies to service levels, and SRE coverage is planned only by about week 22 (D12).

| Target (spec wording) | Measurement definition (proposed) | Data source / instrumentation | Phase | Owner |
|---|---|---|---|---|
| 99.9% monthly control-plane availability | Minutes the control-plane API answered authenticated health and read probes successfully / minutes in the month, excluding nothing; planned maintenance is shown separately, not excluded | External synthetic probe + control-service telemetry | P1-P2 (control service exists) | Tech lead; SRE from about week 22 |
| p95 internal event-to-case propagation below 60 seconds after ingestion | p95 of (case state updated) − (evidence event `recorded_at`) per tenant per day. Before cases exist, the proxy is event-to-evidence-store latency against the 5-minute health deadline (PA-001). | `EventEnvelope.occurred_at` and `recorded_at` + case version timestamps, correlated by `correlation_id` | P2 proxy; P4 | Tech lead |
| Visible connector staleness within five minutes of the configured health deadline | Share of health-deadline misses where DEGRADED status, freshness, lag and failure state appear, linked to affected cases and releases, within 5 minutes (PA-P17, PA-011) | Collector health fields + alert records + fault injection | P2 | Integration engineer |
| Durable restart without losing acknowledged intents | Acknowledged intents lost across injected crashes and restarts = 0. Build ledger: PA-015 behaviors. Gateway: PA-009 and PA-015 for draft creation and sends. | Fault-injection harness + build and effect ledgers | P2 (build ledger); P5 (gateway in sandbox); P6 (production) | Tech lead |
| Policy-gateway failure closed for writes | Writes dispatched while the policy gateway was unavailable or degraded = 0; every such attempt is refused and recorded | Gateway decision log + fault injection | P5 sandbox; P6 production | Tech lead |
| Report provider delay separately | Elapsed time attributed to provider latency, outages and vendor approvals, shown separately from Plumb-controlled time | DependencyRecord intervals + provider call telemetry | P2 | Tech lead |
| Report end-to-end customer experience | Customer-visible elapsed times shown with no exclusions: time to first verified event; source change to readiness-ledger update; period end to package ready-for-review; time blocked waiting on authorization | Build ledger + collector health + review surface | P2; P4 | Product engineer |

### 4.6 Pre-registered triggers and the metric that reads each

Every metric-based trigger in the decision record needs an instrumented metric, or it cannot fire.

| Trigger (source) | Metric that reads it | Section |
|---|---|---|
| Tenant 3 EIH/VD ≥ 75% of tenant 1; hands-off rate < 50%; reuse < 60%; any fork (R1) | EIH/VD; hands-off build rate; artifact reuse and fork count | 2; 4.1 |
| Any unrecorded engineering found in an audit (R2) | Ledger audit findings | 6.4 |
| Median DOMAIN_CLARIFICATION per workflow > 10 questions or 3 hours; steady-state owner decision time > 60 minutes a week; owner clarification plus authorization > 3x budget at two partners (R3; all on tenant 3) | Interruption load | 7 |
| Generated workflows fail > 10% of protected failure cases across two tenants; any real-client duplicate, stale or wrong-client request in canary; two within 90 days (R4) | Protected failure-case pass rate; client-request integrity | 4.1; 5 |
| ≥ 3 of 5 qualified prospects choose native tools after a PL-013 comparison; ≥ 50% of qualified mixed-stack prospects pick an incumbent head-to-head; < 2 of the first 4 partners convert at $15 or more; cost per active client-month > 2x price at tenant 4 with no downward trend (R5) | Commercial conversion; fully loaded cost; funnel outcomes | 4.3 |
| PA-001 not passed on tenant 1 by week 14; M1R not passed by week 24 (R6) | Milestone attestation dates (build ledger + verifier) | 4.1; 10 |
| ≥ 2 of 5 partners refuse mailbox scopes, or vendor approval for mail scopes is not granted by M3-lite; fewer than 2 tenants grant TRAIN (R7) | Source grants by source and purpose (AutonomyEnvelope contract) | 9.4 |
| Onboarding CUSTOMER_AUTHORIZATION > 4 hours per firm (D1) | Interruption load (CUSTOMER_AUTHORIZATION minutes) | 7 |
| In the first two shadow closes, accountant minutes per client-period fall < 25% against baseline, or packages are opened for < 50% of client-periods, while chasing still dominates the time study (D2) | Correct-package rate and accountant minutes; adoption | 4.2 |
| > 20% of obligations UNKNOWN after two closes because of off-system handoffs (D3) | Readiness-ledger presence distribution by reason | 4.2 |
| M2 gates: join precision ≥ 90% on a PA-012-style 100-pair sample; TRAIN on ≥ 2 tenants; ≥ 500 explicit accept/correct events; classification errors ≥ 25% of review minutes, or a candidate comparison shows a reviewer-time gain (D5) | Label-audit sample; grant records; review-surface decision counts; review-minute coding | 4.2; 9.4 |
| Draft-to-Send graduation: ≥ 2 closes, ≥ 20 drafts per type, approve-without-edit ≥ 95%, material edits < 2% (D6). D6 revisit: shadow agreement with Plumb-prepared requests < 95%; staff edit > 10% of drafts; ≥ 2 of 3 partners refuse policy-level approval after shadow; < 2 of 5 opt in by close 3 | Draft calibration; "what Plumb would have done" comparison; approval records | 5; 10 |
| Sign-off lag > 2 weeks, or reviewer disagreement on "material" > 20% in a double-coded sample; healthy accepted-package metrics but partners do not renew (D10 revisit) | Co-headline counting rules; logo retention | 3; 4.3 |
| Measured value < about $45 per client-month (D7) | Measured value per active client-month | 4.3 |
| Outcome-led framing gets > 2x the qualified-meeting rate of verification-led framing across ≥ 200 ICP contacts (D8) | Message-test meeting rate by framing (CRM) | 4.3 |
| < 30% of the first 25 qualified calls have materially mixed stacks; < 4 LOIs by week 10 (D1); < 2 paid pilot LOIs after about 30 qualified conversations (D7, D9) | Design-partner funnel (CRM) | 4.3 |
| Tenant 2's onboarding takes > 50% of engineering capacity for > 3 weeks (D9) | ENGINEERING_INTERVENTION hours per week against team capacity | 2; 6 |

---

## 5. Guardrail metrics

Guardrails are metrics that must not get worse while EIH/VD improves. A tripped guardrail is acted on whatever the north star says. Thresholds are hypotheses for ratification in threshold sheet v1.

| Guardrail | Definition | Denominator | Trip threshold (hypothesis) | Action when tripped | Phase | Source |
|---|---|---|---|---|---|---|
| Client-request integrity: duplicates | A second request for the same client-period-obligation in the same epoch, from any staff member or release (PA-007) | Per client-period-obligation; per 100 requests | Any duplicate reaching a real client in canary | Halt sends, revert to Draft, run root-cause analysis. Two incidents within 90 days: Send leaves the product for two quarters (R4). | P6 (Send canary; earliest close around July 2027) | Effect ledger slots + provider message log |
| Client-request integrity: stale requests | A request for a document already held when the request was dispatched (PA-005); dispatch-time re-check result | Per 100 requests | Any reaching a real client | As above | P6; "would-have-sent" in P5 | Effect ledger + evidence `availability_time` |
| Client-request integrity: wrong-client requests | A request or package attributed to the wrong client (PA-003) | Per 100 requests; per package | Any reaching a real client; any in a package excludes it from the co-headline | As above; package credited (D7) | P2 (attribution); P6 (requests) | Verifier + adjudication |
| False-chase rate | Items flagged missing that were already held (PA-005 class) | All items flagged missing | > 2% in a close | Blocks Draft-tier graduation for the affected type; defect triage | P2 (readiness ledger); P5 (shadow) | Adjudication sample + readiness ledger |
| Review burden (PL-048) | Accountant review minutes per package; correction rate; rework rate (amend after accept); review queue age | Per package; per close | Review minutes per package ≥ baseline assembly-plus-review minutes (D6); correction rate threshold set by the domain expert | Treated as a commercial failure even if technically green; defect triage; D2 response if sustained | P4 | Review surface; PL-048 monitor per active intervention |
| Interruption budget | Batched owner requests per tenant-week; repeat asks (requests for authority still valid at request time, which PL-041 forbids); per-case approval share (CASE_LEVEL_BUSINESS approvals / prepared requests) | Tenant-weeks; owner requests; prepared requests per close | Any item over its section 7 budget: > 1 owner request a week in steady state; any repeat ask; > 10% per-case approvals after calibration (D6) | Product defect; repeat asks fixed before the next close; per-case overruns review the materiality triggers and D6 revisit triggers | P1 (P6 for per-case approvals) | Approval-request records (absent); `approvals.decision_kind` |
| Draft calibration | Approve-without-edit rate; material-edit rate (recipient, item list, client or period) per client and obligation type | Drafts per type | Graduation needs ≥ 2 closes, ≥ 20 drafts, ≥ 95% approve-without-edit, < 2% material edits. Staff editing > 10% of drafts keeps per-case Draft as the default (D6). | Type stays on Draft | P6 | Mailbox draft vs sent diff (provider metadata) + review records |
| Revocation-to-stop latency | Time from grant or approval revocation or expiry to: cached grants and queued dispatches invalidated; collector PAUSED or DEGRADED; zero provider calls under the revoked authority. A provider acceptance that lands before the revocation is a race: the receipt is kept and remediation opened (PA-014, PA-P05). | Revocation events | Invalidation within 1 minute, as in PA-008 and the D9 contract term; collector stopped within the health deadline. The spec says only "promptly" (spec §17 L276), so the 1 minute is a hypothesis anchored on PA-008. | Severity-1 defect; blocks the Draft tier | P2 (collection); P5-P6 (dispatch) | Grant and approval records + gateway decision log + fault injection |
| Pause-to-block latency (proposed) | Time from pause or kill of a SHADOW or CANARY release to refusal of the next new effect, with visibility kept (PL-047) | Pause events | Next effect refused, zero dispatched after the pause is acknowledged | Blocks canary | P5 sandbox; P6. The package's RELEASE machine allows PAUSED only from ACTIVE today (D3 adds pause and kill from SHADOW and CANARY) | Release state + gateway log |
| Collection integrity | Section 4.2 | Sampled changes | Any duplicate or reconciliation gap | Collector held in SHADOW; defect | P2 | Verifier harness |

---

## 6. Human-effort rubric

**Spec.** PL-003 requires all human effort to be recorded by category, in five categories, and forbids calling a deployment autonomous if a person secretly did the implementation. Appendix B does not assign label audits or per-case approvals to a category. D6 fills that gap. The rubric below is D6 as amended by the head of product (founder decision 18, to ratify; the amendments are marked): ENGINEERING_INTERVENTION covers implementation work by any person, Plumb or customer staff (spec App. B L652); approving the reminder policy is CUSTOMER_AUTHORIZATION; scheduled weekly check-ins and baseline-study recording overhead are DOMAIN_CLARIFICATION. Every minute of partner time lands in one of the five categories. Plumb staff time that is neither engineering nor repair (support, verification, running the time study) goes to the cost ledger, tagged by tenant, and is reported beside the categories (PL-059).

**Proposed governance.** The rubric is frozen in week 1 (P0) and signed by the founder (owner, D12) and the domain expert. Amendments are versioned, dated and applied prospectively. Every ledger entry carries the rubric version, and reports disclose any amendment in force.

### 6.1 The five categories

| Category | What counts (D6 as amended) | Accounting examples | Does not count here | Typical principal | Capture | In EIH/VD? |
|---|---|---|---|---|---|---|
| CUSTOMER_AUTHORIZATION | Grants and envelope decisions | OAuth consent for QBO or Xero, Google Workspace or Microsoft 365 mail, and Drive, SharePoint, Dropbox or SmartVault; signing the envelope (US region, spend cap, INSPECT/COLLECT/TRANSFORM/EVALUATE purposes, the explicit SERVE grant); approving the implementation card; renewing an expired grant (PA-008); approving the reminder policy (amended) | Answering domain questions; reviewing packages | Firm owner (HUMAN_OWNER) | Automatic: connection-intent start to completion; time on the approval surface | No |
| DOMAIN_CLARIFICATION | Owner answers on conventions; label or attribution sample audits; baseline-study recording overhead; scheduled weekly check-ins (amended) | Answering "statements are attributed by closing date minus one day" (PA-004); resolving a misfiled statement between two clients (PA-003); confirming a client's engagement checklist; the 100-pair attribution review (D9); keeping the month-0 time diary (the overhead only, not the timed work); the partner's 20-minute weekly check-in (D9) | Plumb staff editing a mapping (that is ENGINEERING_INTERVENTION) | Firm owner, reviewing accountant, bookkeeper | Automatic for the focused-question queue and sample-review surface; manual for recording overhead and check-ins (entered at the check-in, checked by the Plumb domain expert) | No |
| NORMAL_BUSINESS_REVIEW | Per-case approvals, draft review and package sign-off | Reviewing a package with accept, correct or amend; reviewing and sending a Draft-tier mailbox draft; a case-level approval when a materiality trigger fires | Answering a convention question (DOMAIN_CLARIFICATION) | Reviewing accountant (HUMAN_REVIEWER, HUMAN_APPROVER); bookkeeper | Automatic on the review surface. Mailbox drafts: created-to-sent interval from provider metadata, with a sampled self-report to estimate active minutes. | No; it is review cost (PL-059) |
| ENGINEERING_INTERVENTION | Implementation work by any person, Plumb or customer staff: wiring, mapping, plan or workflow authoring or editing, and manual deployment (amended; the record said "Plumb staff") | Hand-editing the tenant BuildPlan; writing a folder-naming rule for client, period and obligation; editing a CollectionSpec; manually configuring a substrate connection; a manual deploy; editing an engagement-checklist template for one firm; debugging a failed attempt and changing its configuration; fixing a probe by hand; a firm's IT contact wiring an integration | Building a reusable registry primitive (platform-investment ledger); verifier work that does not change the build | Any Plumb staff (no `PrincipalType` exists for them yet); customer staff under their own principal | Automatic for actions through the control plane, operator console and deployment adapter; manual timer entry for off-system work (reading logs, local debugging) | Yes |
| OPERATIONAL_REPAIR | Plumb staff fixing a running collector or workflow | Restarting a stuck collector; re-running reconcile after a provider outage; replaying a webhook; patching a mapping after schema drift until PA-P06 passes (manual operations are logged, D3) | Fixing an attempt that has not yet verified (ENGINEERING_INTERVENTION) | Plumb engineer/operator | As for ENGINEERING_INTERVENTION | Yes |

### 6.2 Boundary cases

| Case | Category or ledger | Basis |
|---|---|---|
| Reviewing accountant's 100-pair label or attribution audit | DOMAIN_CLARIFICATION | D6 |
| Reviewing accountant's per-case approval | NORMAL_BUSINESS_REVIEW | D6 |
| Firm owner approves the reminder policy once | CUSTOMER_AUTHORIZATION | D6 as amended (founder decision 18) |
| Firm's IT contact wires an integration or edits a mapping | ENGINEERING_INTERVENTION under the customer principal, counted in EIH/VD and triaged as an interruption defect | D6 as amended (founder decision 18); spec App. B L652 ("a person"); App. A.7 L588 |
| Partner's domain owner in the scheduled weekly check-in | DOMAIN_CLARIFICATION, reported beside the interruption budget, not inside it | D6 as amended (founder decision 18) |
| Plumb domain expert authors a generic engagement-checklist template | Platform-investment ledger, tagged with the triggering tenant | Section 2.1 |
| Plumb domain expert edits that template for one firm | ENGINEERING_INTERVENTION | D6 |
| Plumb domain expert runs the month-0 time study | Cost ledger (baseline measurement), not EIH/VD | Section 8 |
| Verification engineer runs attestations | Cost ledger (verification). If they change the tenant's build: ENGINEERING_INTERVENTION. | ADR-007 |
| Design-partner success lead on a check-in | Cost ledger (support). If they wire anything: ENGINEERING_INTERVENTION. | D12 |
| Vendor app review for mail and document scopes | Platform-investment ledger, unless tenant-specific | D11 watch item |
| Re-running a milestone after an audit finding | ENGINEERING_INTERVENTION for every minute of the re-run | R2 |

### 6.3 Who logs, and automatic vs manual capture

| Source of effort | How it is captured (proposed) | Who enters it |
|---|---|---|
| Human-principal actions on Plumb surfaces (consent, approvals, focused questions, review) | Automatic. Each authenticated human request on a tenant resource emits an effort event. Active minutes come from surface session telemetry with an idle cutoff (5 minutes, hypothesis). Category is set by rule. | No one; the ledger writes it |
| Plumb staff actions through the control plane, operator console or deployment adapter | Automatic, as above, with build, attempt, step and case ids attached | No one |
| Break-glass access to a tenant's provider consoles | Automatic session log, defaulting to ENGINEERING_INTERVENTION, or OPERATIONAL_REPAIR for a running component | Staff confirm or correct the category, with the change audited |
| Off-system Plumb work (log reading, local debugging, design for one tenant) | Manual timer in the operator console, entered the same day. A non-empty description is required (as `HumanEffortRecord.description` already demands), referencing artifact ids and never client content. | The person who did the work |
| Customer time off Plumb surfaces (calling a vendor to unlock app approval; time-study recording overhead; the check-in itself) | Manual. Prompted at the 20-minute weekly check-in (D9). | Firm owner or partner, entered by the founder or success lead |
| Mailbox draft review (Draft tier) | Provider timestamps plus a sampled self-report | Reviewing accountant (sample) |

The share of ENGINEERING_INTERVENTION and OPERATIONAL_REPAIR minutes captured automatically is reported as a ledger-health measure. Its target is set at the M1 audit, once there is data.

### 6.4 Audit procedure

| Step | Monthly ledger audit (internal) | Milestone audit (M1, M1R, M5) |
|---|---|---|
| Auditor | Verification and acceptance-harness engineer, reporting outside the build team (D12) | Independent ledger auditor: founder plus an external technical advisor (D12) |
| 1. Freeze | Snapshot the period's effort, platform-investment and build ledgers, recording a digest | Same, for the milestone window |
| 2. Gather the delivery team's account | Commits and pull requests, tickets, deploy logs, substrate and provider admin logs, break-glass logs, calendar entries for tenant work | Same, plus interviews with each person who touched the tenant |
| 3. Reconcile | Match every tenant-touching activity to a ledger entry (PA-027's method: manual wiring or workflow authoring not recorded as ENGINEERING_INTERVENTION fails) | Same, over every attempt in the denominator |
| 4. Double-code | Second coder re-categorizes a 10% sample (proposed); disagreements resolved against the rubric | 100% of ENGINEERING_INTERVENTION and OPERATIONAL_REPAIR entries reviewed |
| 5. Check platform-investment entries | Each entry names its registry primitive, digest and triggering tenant | Same |
| 6. Report | Counts of unrecorded, miscategorized and mistimed entries | Pass or fail against the pre-registered criteria; at M1R also the R1 checkpoint memo |
| Consequence | Any unrecorded engineering is escalated as a milestone-invalidating finding (R2). Miscategorization switches EIH/VD to automatically captured effort only (D10). | Milestone invalidated and re-run on any unrecorded engineering. A second occurrence triggers an external audit before any external claim (R2). |

---

## 7. Interruption budget

**Spec.** §17's title promises autonomy "without constant interruption", and PL-041 forbids asking again for valid authority, but the spec defines no interruption metric. **Proposed** (from D6): the budget below, every figure a hypothesis. Overruns are logged and triaged as product defects. The budget counts unscheduled asks; scheduled time, such as the 20-minute weekly check-in (D9), is logged as DOMAIN_CLARIFICATION and reported beside the budget, not inside it (D6 as amended).

The budget limits interruptions; it does not remove approvals. Firms want gates: in a small, self-selected vendor survey (directional), 62% of firms require human approval before anything is sent or filed (Uku 2026).

| Stage | Budget item | Hypothesis (D6) | Measured as | Escalation |
|---|---|---|---|---|
| Onboarding | Owner authorization time | ≤ 2 hours CUSTOMER_AUTHORIZATION | Effort ledger, per firm | > 4 hours per firm re-scopes the stack (D1) |
| Onboarding | Domain questions | ≤ 5 DOMAIN_CLARIFICATION questions per workflow | Focused-question queue | Median > 10 questions or 3 hours on tenant 3 fires R3 |
| Onboarding | Owner time, first 30 days | ≤ 4 owner-hours | Effort ledger, all customer categories, excluding scheduled check-ins | Clarification plus authorization > 3x budget at two partners fires R3 |
| Steady state | Owner requests | ≤ 1 batched owner request per tenant-week | Approval-request records | Defect |
| Steady state | Owner decision time | ≤ 30 minutes a week | Effort ledger by decision type | > 60 minutes a week on tenant 3 fires R3 |
| Steady state | New domain questions | ≤ 2 per close after close 1; decay ratio of close n against close 1 reported | Focused-question queue | Defect |
| Steady state | Reviewer approvals | Batched into ≤ 1 session a day | Review-surface sessions | Defect |
| Steady state | Repeat asks | 0 | Requests checked against valid authority at request time | Defect, fixed before the next close |
| After calibration | Per-case approvals | ≤ 10% of requests | `approvals.decision_kind` | Review materiality triggers |
| All stages | Review time | Accountant review minutes per package below baseline assembly-plus-review minutes | Review surface vs month-0 study | Commercial failure (section 5) |

**Definitions (proposed).**

- An **owner request** is one batched notification that needs an owner decision. Missing authorizations are grouped with `group_missing_authorizations` (PL-041), which exists in [approval_checker.py](../plumb/checker/approval_checker.py) but is called only by the local tests.
- **Decision type** is recorded for each request as DATA_USE, IMPLEMENT_OPERATE or CASE_LEVEL_BUSINESS, the `DecisionKind` values in `plumb/contracts/approval.py`. The request UI names the decision and its owner (D6; spec §17 L272-274).
- A **repeat ask** is a request for authority that was valid when the request was raised.

The budget is the instrument for experiment 4 (amount of domain clarification per workflow, spec §27 L442). DOMAIN_CLARIFICATION per workflow is measured against it at the M3-lite exit (P4).

---

## 8. Baseline measurement protocol

**Why.** The accounting envelope fixture's success metric is measured "prospectively against the pre-deployment baseline" ([fixture](../fixtures/envelopes/accounting_evidence_preparation.json)). Nothing in the spec or package captures accountant assembly time before deployment. The market research found no reputable primary source for hours per client-month spent on close or on document chasing. In a vendor survey of accounting and bookkeeping professionals, mostly at small firms, only 20% reported clear, measurable ROI from AI (Financial Cents 2026, n=486). Without a baseline, any time-saving claim is unfalsifiable.

### 8.1 Month-0 two-week time study (proposed design)

| Element | Design |
|---|---|
| Who runs it | The partner firm, with the Plumb domain expert (D2) |
| When | Scheduled at the M0 exit (an M0 checklist item: "captured or scheduled") and completed before production shadow. For tenants 2 and 3, completed before mid-January, ahead of tax season (D5). |
| Window | Two consecutive weeks covering the firm's month-end assembly and review activity |
| Cohort | The same agreed cohort of at least 30 in-scope client-periods later measured in shadow (D2) |
| What is recorded per client-period | Accountant assembly minutes; accountant review minutes; rework minutes after review; bookkeeper chasing minutes and number of client requests sent; requests for items already held (checked afterward against the document store); days from period end to a complete package |
| Method | A timer or time diary with fixed activity codes (ASSEMBLE, REVIEW, CHASE, REWORK, OTHER) tagged by client-period. The domain expert directly observes a small sample of sessions, with staff consent, to calibrate self-reports. |
| Case-mix tags | Ledger (QBO or Xero), number of accounts, transaction volume band, client complexity as rated by the firm. These enable comparable-cohort analysis (spec §7 L136). |
| Data-quality rules | Completeness is reported (share of cohort client-periods with entries). Outliers are flagged, not deleted. Diary-to-observation agreement is reported. |
| Output | Per-client-period distributions (median and interquartile range, not only means), by activity code and case-mix tag |
| Effort accounting | Firm staff's recording overhead (keeping the diary, the briefing) is DOMAIN_CLARIFICATION (D6 as amended); the timed assembly and review work is the firm's normal work and is not logged again. The Plumb domain expert's time goes in the cost ledger. |
| Known limits | Observer effect; one close only; seasonality. Comparisons therefore use the same kind of close period and the same cohort, and every report states these limits. |

**Comparison method (proposed).** In each shadow, canary and active close, measure accountant minutes on Plumb-prepared packages against the month-0 baseline. Where the firm agrees, also run a comparable-cohort split within the same close: client-periods assembled from Plumb packages versus client-periods assembled the old way, stratified by case-mix tag. This is the staged-rollout or comparable-cohort method the spec asks for (spec §7 L136), and it matches the contract's `MeasurementMethod` values (STAGED_ROLLOUT, COMPARABLE_CASE_COHORTS).

### 8.2 Historical duplicate-chase baseline

| Element | Design |
|---|---|
| When | Once read-only mail history is connected in M3-lite (P4; "phase 2" in D2 and D3) |
| Data | A 24-month backfill of reminder history from the mail source, joined to document arrival events on client, period and obligation |
| Measures | Duplicate chases per client-period-obligation (more than one request in the same epoch, from any staff member); re-requests for documents already held (request sent after the document's `availability_time`); days to receive |
| Label | Always "historical, non-causal" (spec §7 L136). Never counted as a PL-001 outcome (D2). Never presented as a Plumb result. |
| Use | The comparison baseline for client-request integrity once the Draft tier (P6) and the Send canary (earliest close around July 2027) ship, and context for partners in the per-close report |
| Known limits | Chasing by phone or portal is invisible. Bookkeepers who keep chasing outside Plumb confound later comparisons; one shared obligation owner (spec App. B L614) only covers requests that go through Plumb. If mailbox scopes are refused, the forwarding-address fallback (R7) lowers coverage, and coverage is reported. |

### 8.3 Other baselines

- **EIH/VD baseline:** tenant 1's ledger at M1 (P2). PA-027 compares later tenants with the first customer.
- **Native-feature baseline:** every OpportunitySpec compares against the current process and a native-feature baseline (PL-013). A delivered native configuration counts as an intervention and bills at the same rate (D7).
- **Days to receive:** a vendor survey reports that clients take 5 days on average to submit requested documents (Financial Cents 2025). That is context only; each firm's own figure comes from 8.1 and 8.2.

---

## 9. Instrumentation requirements

### 9.1 Correlation identifiers (PL-060)

**Spec.** "Operational telemetry MUST correlate tenant, goal, build, case, release, step, model call and external action without logging sensitive content by default" (PL-060, spec §24 L374).

| Identifier | Present in contracts or SQL design today | Where (verified) | Gap |
|---|---|---|---|
| Tenant | Yes | `ArtifactHeader` tenant; composite `(tenant_id, id)` keys throughout the SQL design | None at the data level; no telemetry pipeline |
| Goal | Yes | Envelope `goals[].goal_id`; `builds.goal_id` | Not carried on effort entries |
| Build | Yes | `builds`, `build_steps`; `human_effort.build_id` | None |
| Case | Yes | `cases`; `effects.case_id`; `outcome_observations.case_id`; `human_effort.case_id` | None |
| Release | Yes | `releases`; `cases.release_id`; `outcome_observations.release_id` | Not carried on effort entries |
| Step / attempt | Partly | `build_steps.step_id`; `build_step_attempts.id` | `human_effort` has `build_id` but no step or step-attempt reference, so effort cannot be tied to a step or a repair attempt (hands-off build rate per build can use `build_id`) |
| Model call | No | `OutcomeObservation.model_calls` is a count only | A model-call id from the model gateway is needed |
| External action | Yes (design and SQLite simulation) | `effects` slot key, `provider_request_id`, receipts; [effect ledger](../plumb/ledger/effect_ledger.py) | Production gateway absent |
| Correlation and causation | Yes | `EventEnvelope.correlation_id` and `causation_id`; `ErrorEnvelope.correlation_id`; SQL `outbox` and `jobs` | No tracing or metrics pipeline exists |

### 9.2 No sensitive content by default

- Telemetry, metrics and effort entries carry identifiers, digests, counts and durations. They never carry document content, email bodies, amounts, tax identifiers or client names (PL-060; PA-019's marker scan; PA-020, an RFQ scenario with the accounting analogue PA-P19, logs an injection attempt without copying the email body).
- Events carry `payload_ref`, never the payload, as the `EventEnvelope` contract already enforces. Errors never include secrets, source content or other tenants' identifiers (spec §22).
- Effort-entry descriptions reference artifact and case ids and are screened like other free text in the contracts (`reject_secret_like`). Proposed: no client names in descriptions.
- Review-surface timing stores durations and decision types, not the content reviewed.
- Metrics stores are tenant-isolated on the same surfaces as PA-P14 (database, API, object storage, caches, logs, exports) before a second tenant's data arrives.

### 9.3 Pinned telemetry conventions

The spec says to pin telemetry conventions because the OpenTelemetry GenAI conventions are still evolving (PL-060; source S17). **Proposed:** pin the semantic-conventions version in effect when the control service is built (P1), record that version in every telemetry resource, and treat a convention upgrade as a planned, tested migration with a before-and-after comparison of each metric it feeds.

### 9.4 Existing contracts: what carries metric fields, and the gaps

| Contract or table | What it carries (verified) | Gap for this plan |
|---|---|---|
| `HumanEffortCategory` ([common.py](../plumb/contracts/common.py) L235-242) | The five categories | None |
| `HumanEffortRecord` (common.py L611-618) | `category`, `principal`, `minutes`, `description`, `recorded_at` | Used nowhere in `plumb/`; no JSON schema; no API. No tenant, build, attempt, step or case reference; no capture method; no rubric version. `principal` takes a `PrincipalType`, which has no Plumb-staff type |
| SQL `human_effort` ([SQL design](../sql/001_initial_design.sql) L814-829, unexecuted) | `category`, `principal_type`, `minutes`, `build_id`, `case_id` | No attempt or step id, capture method, rubric version or audit status. `principal_type` allows only the eight `PrincipalType` values, none for Plumb staff. `tenant_id` is required and there is no platform-investment ledger table. |
| `OutcomeObservation` ([OpenAPI](../api/openapi.yaml) L3612) and SQL `outcome_observations` | `model_calls`, `completed`, `correct` (null until maturation), `realized_value`, `review_minutes`, one nullable `human_effort_category` | One category per case cannot hold multi-category effort. No explicit-acceptance field or material-correction flag. `listOutcomes` is read-only; nothing writes observations. |
| `DependencyRecord` (common.py L593-608) | `failure_class`, `error_class`, `missing_authority`, `resolver_role`, `blocked_step_ids`, `resumes_after`, `raised_at` | No `resolved_at`, so time in dependency cannot be computed. `resolver_role` cannot express "vendor". |
| `SourceGrant` ([envelope.py](../plumb/contracts/envelope.py)) and SQL `source_grants` | Per-source purposes (INSPECT, COLLECT, TRANSFORM, EVALUATE, TRAIN, SERVE, EXPORT), granting principal, `granted_at`, `expires_at`; the SQL table adds `revoked_at` | The contract has no `revoked_at`, so revoking a single grant, and revocation-to-stop latency, are not modeled in the contract. Nothing records a refused grant request, which the R7 trigger needs. |
| SQL `approvals` | `decision_kind` (DATA_USE, IMPLEMENT_OPERATE, CASE_LEVEL_BUSINESS), approver, `approved_at`, `expires_at`, `revoked_at` | No approval-request record (requested-at, batch id), so decision latency, owner requests per week and repeat asks cannot be computed |
| SQL `build_step_attempts` | `attempt_no`, `outcome`, `failure_class`, reserved and actual minor units | Sufficient for repair attempts and outcome mix once a build ledger writes it |
| SQL `builds` | `goal_id`, `state`, `failure_class`, `reserved_minor_units`, `spent_minor_units` | Nothing writes the cost columns; no metering |
| SQL `collectors` | `freshness_seconds`, `lag_seconds`, `completeness`, `failure_state`, `health_deadline_seconds` | No link to alert records (no monitors table) |
| SQL `cases` | `review_state` (NONE, READY_FOR_REVIEW, APPROVED, REJECTED) | No accepted-with-correction state. No ReviewPackage contract (`ReviewPackage` is only an `ArtifactKind` value). |
| SQL `effects` and the SQLite effect ledger | SQL: slot key, obligation id and epoch, provider request id, receipt digests. SQLite: slot key (which encodes obligation and epoch), provider request id, receipts | Sufficient for client-request integrity; production gateway absent |
| `ArtifactHeader.content_digest` | Content digest per artifact | No artifact store, so reuse-by-digest cannot be computed yet |
| `VerificationAttestation` | Attestation contract | No verifier service |

### 9.5 New instrumentation (proposed; stories in the [backlog](05-backlog.md))

1. **Effort ledger service (P0-P1).** Middleware that writes an effort entry for every authenticated human-principal action on a tenant resource. Operator console with a timer for manual entries. Proposed entry fields: entry id; tenant id (null for platform investment); ledger (TENANT or PLATFORM_INVESTMENT); category (one of the five); principal id and type (with a new Plumb-staff principal type); minutes; started and ended times; capture method (AUTO, MANUAL, AUDIT_ADJUSTMENT); goal, build, attempt, step, case and release ids where applicable; triggering tenant (platform entries); registry primitive digest (platform entries); rubric version; description (no content); audit status.
2. **Platform-investment ledger (P1).** Same store, with a separate ledger value and reporting path.
3. **Approval-request records and decision-type tagging (P1).** Requested-at, batch id, decision kind, owner, and a validity check at request time (repeat asks).
4. **Dependency resolution timestamps and resolver class (P1).** `resolved_at` plus a customer, vendor or Plumb resolver class on DependencyRecord.
5. **Review surface capture (P4).** Explicit accept, correct and amend with a material-correction flag; active review time; the ReviewPackage contract.
6. **Model-call identity (P4).** The model gateway assigns an id to every call and links it to the case and step.
7. **Cost metering (P2).** Provider charges and infrastructure cost written against reservations (PL-058), plus labor at loaded rates.
8. **Time-study tool (P1).** Timer or diary with activity codes and cohort tagging.
9. **Metrics computation and report job (P2).** Owned by the verification engineer, reading ledgers and attestations, never written by the build team.
10. **Audit tooling (P2, before the M1 audit).** Reconciliation of commits, deploy logs, substrate and provider admin logs and break-glass sessions against the ledger.

---

## 10. Reporting cadence and audiences

| Report | Cadence | Audience | Contents | Owner | Rules |
|---|---|---|---|---|---|
| Internal metrics review | Weekly | Founding team | EIH/VD per tenant to date with platform-investment hours; attempts by outcome; open dependencies by resolver and age; interruption-budget status; guardrails; collection integrity; ledger capture health; budget overruns logged as defects | Founder | Per tenant, failures included; no pooled-only views |
| Partner check-in | Weekly, 20 minutes (D9) | Partner's domain owner | Open requests and dependencies; readiness-ledger status; off-surface customer time (for the ledger) | Founder or success lead | The partner's time is DOMAIN_CLARIFICATION, reported beside the interruption budget, not inside it (D6 as amended) |
| Per-close partner report | After each monthly close | Firm owner, reviewing accountant | Accepted packages with rate over all eligible client-periods; Plumb human minutes per accepted package; accountant minutes against the month-0 baseline (only once the baseline exists); false-chase, recall and attribution from the adjudication sample; in shadow, the "what Plumb would have done" comparison; that firm's labor ledger by category, Plumb's included; open dependencies; billing basis (active client-months and credits); deployment labeled "supervised" | Founder | Technical and commercial results in separate columns; historical duplicate-chase figures labeled non-causal |
| Monthly ledger audit | Monthly | Founder; build team | Section 6.4 findings | Verification engineer | Outside the build team |
| Milestone audit report | At M1, M1R and M5 | Founder, external technical advisor, investors on request | Ledger reconciliation and the zero-unrecorded-work finding; EIH/VD, hands-off rate, reuse and fork count against pre-registered thresholds; the R1 checkpoint memo at M1R | Independent ledger auditor (D12) | A milestone with an unrecorded-engineering finding is reported as invalidated |
| Day-180 decision packet | Once, P5 (day 180 is Apr 3, 2027) | Founder; board and investors | PL-063 evidence (M1 + M1R); EIH/VD and reuse across 3 tenants, failed attempts included; tenant 1 shadow results; tenant 1's evidence toward conversion to date (conversion is expected in P6, after a full close in ACTIVE; founder decision 17) and other commercial data (pilots, LOIs); experiment-1 proxy; M2 go/no-go against the D5 gates; Draft and M4-accounting canary go/no-go, each against its threshold. Tenants 2-3 full-close readings marked pending if not yet available. | Founder | Every number with its denominator and pre-registered threshold |
| Investor update | Monthly (proposed) | Investors | EIH/VD per tenant in onboarding order with failed attempts and platform-investment hours; milestone status against gates; LOIs, paid pilots and conversion; accepted packages with denominators once they exist; risk triggers that fired | Founder | Passes the D8 never-claim checklist (founder-owned gate) before sending |
| Anonymized ledger publication | After each milestone audit (proposed) | Public | Per-tenant anonymized EIH/VD, failures included, under the contract's publication right (D9; founder decision 11) | Founder | Audited figures only |

### 10.1 Metrics we will not report

| We will not report | Why |
|---|---|
| Local test counts (see [VALIDATION_REPORT.md](../VALIDATION_REPORT.md)), schema, API or requirement-coverage counts as product progress, or the spec's stale "56 tests" (header table and Appendix C) | Local tests do not validate models, outcomes, security, isolation or integrations (spec §28 L450; D8 item 1) |
| Registry PRODUCTION_VERIFIED counts, integration logos or "supported apps" totals | All 25 registry records (23 step types) are synthetic placeholders, including the 15 marked PRODUCTION_VERIFIED. Coverage is stated per operation at its maturity level (PL-007, PL-008; D8 item 8). |
| Hours saved, ROI or dollar value without a baseline and a denominator; any causal claim from historical replay; realized value externally before PA-P12 attests it | Spec §7 L136; D8 item 9 |
| Success-only rates, or an autonomy percentage that omits failed, blocked or abandoned attempts | PL-062 |
| Runtime automation rates presented as implementation autonomy | ADR-010 |
| EIH/VD netted against platform-investment hours, or pooled without the per-tenant view | D10 |
| A count of "autonomous" deployments, or any deployment called autonomous without its ledger | PL-003; D8 item 6 |
| "Fewer duplicate requests" before Send-canary evidence (earliest Send canary close around July 2027); the historical duplicate-chase baseline presented as a Plumb outcome | D8 item 12; D2 |
| "Automatically constructed" figures before M1R | D8 item 7 |
| Product-video results, or results from the three synthetic scenarios as cross-industry evidence | Spec §29 L492; spec §25 L398 |
| A model extraction score as a business outcome | Spec §18 L286: it belongs to one verification level only |
| Absence of edits as acceptance | Spec App. B L624 |
| Model calls, events processed or messages sent as value metrics | PL-059 separates model calls from correct outcomes and realized value |
| 90 days as a delivery commitment | Spec §26 L418 |
| General market adoption statistics as Plumb traction | Not Plumb's evidence |

---

## Open questions for founder ratification

The effort-rubric amendment (customer-performed wiring as ENGINEERING_INTERVENTION, reminder-policy approval as CUSTOMER_AUTHORIZATION, check-ins and baseline recording overhead as DOMAIN_CLARIFICATION, and a Plumb-staff principal type) and the Prepare-tier promotion path are decided by the head of product and ratified with the decision record (founder decisions 18 and 17); they are not reopened here.

1. **Plumb's non-engineering labor.** Support, verification and time-study minutes go to the cost ledger outside the five categories (section 6). Confirm that this, with PL-059 reporting, meets PL-003's "all human effort".
2. **Deployment unit.** One path per source system per tenant, and one workflow per workflow type per tenant (section 2.1)?
3. **Abandonment rule.** 14 days without a state change while not waiting on a dependency?
4. **Initial material-correction rubric** (section 3), pending the domain expert.
5. **Revocation-to-stop SLO** of 1 minute, anchored on PA-008, as a customer-facing number in security reviews.
6. **Investor-update cadence** (monthly proposed) and **anonymized publication** after each milestone audit.

---

## Sources

**Repository (verified for this document).**

- [Spec v0.2](../spec/Plumb_Autonomous_Implementation_Specification_v0.2.md): header table L15 and App. C L662 (the stale "56"); §1 L47, L51; §4 L96; §7 L136; §17 L266-276; §18 L286; §20 L308; §22 L344; §24 L370-382; §25 L386-398; §26 L404-418; §27 L440-442; §28 L450; §29 L492; App. A.1 L514; App. A.7 L588; App. B L614, L624, L650-654.
- [Requirements index](../spec/requirements_index.json): PL-001, PL-003, PL-006, PL-007, PL-008, PL-013, PL-024, PL-041, PL-042, PL-047, PL-048, PL-058, PL-059, PL-060, PL-062, PL-063; ADR-007, ADR-010.
- [Acceptance catalog](../acceptance/production_acceptance_catalog.yaml): PA-001 (L125-183), PA-002, PA-003 to PA-011 (the protected accounting failure cases; PA-008's one-minute invalidation, PA-011's five-minute health deadline), PA-012 (100-pair sample), PA-014, PA-015, PA-019, PA-020, PA-027 (L1363-1416).
- Code: [common.py](../plumb/contracts/common.py), [envelope.py](../plumb/contracts/envelope.py), [api.py](../plumb/contracts/api.py), [approval.py](../plumb/contracts/approval.py), [opportunity.py](../plumb/contracts/opportunity.py) (`MeasurementMethod`), [approval_checker.py](../plumb/checker/approval_checker.py), [machines.py](../plumb/statemachines/machines.py), [effect_ledger.py](../plumb/ledger/effect_ledger.py), [capability registry](../plumb/registry/capability_registry.json), [OpenAPI proposal](../api/openapi.yaml), [SQL design](../sql/001_initial_design.sql), [accounting envelope fixture](../fixtures/envelopes/accounting_evidence_preparation.json), [validation report](../VALIDATION_REPORT.md).
- Doc set: [decision record](02-strategy-decisions.md) (D1-D12, phased plan, north_star_and_metrics, R1-R7, founder decisions 17 and 18, and its list of corrections); [roadmap](04-roadmap.md) for PA-P02, PA-P05, PA-P06, PA-P12, PA-P14, PA-P17, PA-P19.

**Market (from the research notes; vendor-reported and secondary items flagged).**

- Capgemini Research Institute: trust in fully autonomous AI agents fell from 43% to 27%. Page undated; coverage places it around July 2025. https://www.capgemini.com/insights/research-library/ai-agents/
- Builder.ai bankruptcy after reports that its "AI" relied on human engineers (press report, May-June 2025). https://www.techspot.com/news/108173-builderai-collapses-after-revelation-ai-since-2017-really-hundreds-engineers.html
- FTC Operation AI Comply continues to pursue deceptive AI capability claims (law-firm analysis, Aug 2026). https://www.hklaw.com/en/insights/publications/2026/08/operation-ai-comply-2-years-later-continued-enforcement
- Financial Cents State of AI in Accounting and Bookkeeping 2026 (vendor survey, n=486, mostly 2-30-person firms plus solo practitioners; Aug 2026): 20% of respondents report clear, measurable ROI from AI. https://financial-cents.com/?p=39931
- Financial Cents 2025 workflow report (vendor survey, 816 professionals; April 2025): clients take 5 days on average to submit requested documents. https://financial-cents.com/?p=9086
- Uku AI in Accounting 2026 (vendor survey of "dozens" of mostly 1-10-person firms in 8 countries; small, self-selected sample; directional): 62% of firms require human approval before anything is sent or filed. https://getuku.com/ai-in-accounting-report/
- Research-note finding: no reputable primary source was found for hours per client-month spent on close or document chasing (market-accounting notes).
