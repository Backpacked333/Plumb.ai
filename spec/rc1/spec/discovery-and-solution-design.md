# Opportunity discovery and solution design

Discovery turns business evidence into an OpportunitySpec with a falsifiable hypothesis, then into a SolutionSpec chosen from complete candidate systems. Evidence is required for the problem; new steps need a justified design (PR-004).

## 1. Three routes

| Route | Signals | Evidence requirement |
| --- | --- | --- |
| Friction | Repetition, waits, duplicate contacts, rework, inconsistent classification, manual transfer, interruptions | Measured on the affected population with coverage and intervals |
| Unmet obligation | Obligations open past due, missed checklist items, controls never performed, outcomes nobody owns | Obligation records and the owner's confirmation that the obligation matters |
| New capability | A Market delta (new operation, API, model) that makes a previously infeasible or unperformed activity feasible | The capability's verified operation and a feasibility probe on the tenant's accounts |

## 2. Hypothesis generator

For each candidate: affected case population (a query), current outcome with denominator, suspected bottleneck, business-policy dependencies, known exceptions, evidence coverage, expected intervention, credible alternatives, expected downside, review burden, falsifiers. A repeated review may be an intentional control: duplicate-looking touches are a hypothesis to confirm with the owner, never assumed waste.

## 3. Feasibility probes

Before scoring, the Sourcer probes: authorization (grants and envelope cover the sources, destinations and effect classes), data (history available, join keys exist), operations (required capabilities verified at the needed level), impact class acceptable. A failed probe keeps the opportunity as a backlog entry with its blocking requirement (model accuracy, price ceiling, missing operation, missing labels, missing authorization).

## 4. Active clarification policy

Ask at most three decision-relevant questions per opportunity, each with the evidence and the consequence of each answer, routed to the authorized respondent (checklist owner, reminder-policy owner, approver). Answers persist with scope (this build, this tenant, this vertical) and are never asked again within scope. Conflicting answers are preserved as a dispute and routed to the owner. Unknown business policy is never replaced with confident inference.

## 5. Portfolio scoring

Opportunities are scored as portfolios: shared prerequisites (identity normalization unlocks several), mutual exclusions, bottleneck movement (fixing step A makes step B the constraint), workload displacement (review burden elsewhere), benefit overlap (two reminders claiming the same hours), change burden per role. Hard constraints are gates, not weights.

## 6. Benefit ranges and measurement

Benefit is a range over a horizon: time theoretically removed, time usable elsewhere, service capacity, contribution, cash savings, each distinct. The measurement plan names the metric, denominator, cohort or rollout design, seasonality and policy-change controls, review and rework accounting and attribution limits. Observational replay never establishes financial realization or causality (SR-095).

## 7. Candidate-solution search

Candidates are complete systems, not per-step cheapest parts: native configuration, process removal, deterministic rules, classical model, general-model workflow, retrieval, specialist API, optimizer, trained component, do nothing. Each candidate records joint error behaviour, latency, exception handling, staff effort, integration and setup cost, idle serving capacity, maintenance and data constraints. The SolutionSpec keeps baseline, selected design, rejected alternatives with reasons, experiment evidence and a decision record.

## 8. Worked example (fixtures/accounting)

Route friction; population "obligations with fulfillment_predicate bank_statement_received since 2026-01"; baseline duplicate requests per obligation 0.31 (0.24 to 0.38, n = 412, twelve months of mail and call backfill); hypothesis "document presence is invisible to the person sending reminders"; alternatives native reminders only, do nothing; selected cand_rules_plus_drafts (deterministic checklist, Drive folder adapter, QuickBooks change capture, drafted consolidated request); trained categorizer deferred to the learning-enabled variant because it serves a different deliverable.

## 9. Omissions

Benefit estimation models for revenue-side opportunities (RFQ) are specified only as ranges; no pricing model is included.
