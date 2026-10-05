# Plumb product documents

- Status: Draft v0.1 (2026-10-04), proposed — requires founder ratification
- Owner: Product
- Basis: [specification v0.2](../spec/Plumb_Autonomous_Implementation_Specification_v0.2.md), the reference package in this repository, and the [decision record](02-strategy-decisions.md)

These documents turn the engineering specification into a product plan: who Plumb is for first, what
the first release does, in which order the specification's milestones are proven, how success is
measured and what could make the plan wrong. They are proposals, not measurements. Nothing in them
has been run against a customer, and no number in them is an achieved result. Thresholds, prices and
dates are hypotheses until the founder ratifies them at M0.

## The plan on one page

**The bet.** Plumb is a platform only if the second and third customer need much less audited human
engineering than the first, with failed, blocked and abandoned builds counted (PL-003, PL-062,
ADR-010). Otherwise it is a services firm with good contracts. The first six months therefore buy
the cheapest test of PL-063 that could fail, while a paid design-partner cohort tests whether firms
will pay.

**Who first.** US accounting firms with 10 to 40 staff whose work leans to client accounting services
and bookkeeping, at least 50 recurring monthly-close clients, and a mixed stack (QBO and/or Xero,
Google Workspace or Microsoft 365, a separate document store). Firms standardized on one ecosystem
whose native chase-and-match already works are qualified out ([market](08-market-and-positioning.md)).

**What first.** Monthly-close evidence readiness, preparation-only: for every recurring client-period
Plumb knows which required documents are present, confirmed absent or unknown, with provenance, and
prepares one ready-for-review package for the accountant. No client communication until a production
action gateway passes the high-severity effect scenarios ([MVP scope](03-mvp-scope.md)).

**In what order** ([roadmap](04-roadmap.md)):

| Phase | Proves |
|---|---|
| P0 Commit and instrument | Effort ledger, threshold sheet and a truthful capability registry exist before any build |
| P1 M0 | Real probe receipts on the first firm's accounts; envelope and data agreement signed |
| P2 M1 | An agent-built, verifier-attested integration-and-collection path on firm 1 (PA-001 plus a safety bundle) |
| P3 M1R | The same path reproduced on firms 2 and 3 with less audited engineering: the second half of PL-063, pulled forward |
| P4 M3-lite | A preparation-only review-package workflow, attested in sandbox, then in production shadow |
| P5 Day-180 packet | Ready-for-review packages on at least 30 client-periods in a full close, measured against a month-0 baseline; go, pivot or kill |
| P6 M4-accounting and M5 | Draft, then policy-approved Send of consolidated requests; full replication on the next three customers (PA-027) |

**How success is measured** ([metrics](06-metrics.md)). North star: engineering-intervention hours
per verified deployment (EIH/VD), per new firm in onboarding order, with platform-investment hours
shown beside it and never netted. Customer co-headline: accepted review packages per month.

**How it is sold** ([market](08-market-and-positioning.md)). "Verified implementation" for accounting
firms: "Close-ready, with receipts." Hypothesis: $15 per active client-month for Prepare, $25 once
policy-approved sending ships, no seats, no implementation fee, and nothing billed for dependency or
failure outcomes.

**What we never claim.** That local tests validate models, outcomes, security or integrations; that
the synthetic scenarios show cross-industry autonomy; that 90 days is a commitment; an autonomous
close or posting; "fully autonomous" or "no humans needed"; integration coverage from the synthetic
registry; savings without a baseline and a denominator. The full checklist is decision D8 in the
[decision record](02-strategy-decisions.md).

## Documents

| Document | Answers | Read it if you are |
|---|---|---|
| [01 Product brief](01-product-brief.md) | What Plumb is, for whom, the promise, personas, principles, non-goals, where we are today | Anyone new to Plumb |
| [02 Strategy decisions](02-strategy-decisions.md) | Decisions D1 to D12 with rationale, alternatives and revisit triggers; founder decisions needed; where the panel disagreed | The founder; anyone challenging a decision |
| [03 MVP scope](03-mvp-scope.md) | What the first design-partner release contains, the end-to-end journey, the product surfaces, gaps in today's package | Engineering, design |
| [04 Roadmap](04-roadmap.md) | Phases P0 to P6, gates, calendar floors, a plan for every acceptance scenario, proposed catalog additions, staffing, the day-180 packet | Everyone |
| [05 Backlog](05-backlog.md) | Epics and stories with acceptance criteria; traceability of all 63 requirements | Engineering |
| [06 Metrics](06-metrics.md) | North star, metric catalog with denominators, guardrails, effort rubric, baseline protocol, instrumentation | Founder, engineering, investors |
| [07 Risks and assumptions](07-risks-and-assumptions.md) | Risks R1 to R7 with kill and pivot criteria, the six unresolved experiments, open questions | Founder, investors |
| [08 Market and positioning](08-market-and-positioning.md) | Competitive landscape with sources, ideal customer, positioning, messaging guardrails, pricing hypothesis | Founder, go-to-market |
| [09 Design-partner program](09-design-partner-program.md) | Cohort design, qualification, terms, contract essentials, onboarding runbook, interview guide | Founder, partner success |

Reading paths: the founder reads this page, then [02](02-strategy-decisions.md) (its founder-decisions
table first) and [04](04-roadmap.md). Engineering reads [03](03-mvp-scope.md), [05](05-backlog.md) and
[04](04-roadmap.md). Go-to-market reads [08](08-market-and-positioning.md),
[09](09-design-partner-program.md) and [01](01-product-brief.md).

## Conventions

- Requirements are cited as PL-001 to PL-063, decisions of the specification as ADR-001 to ADR-010 and
  production acceptance scenarios as PA-001 to PA-030, exactly as in
  [requirements_index.json](../spec/requirements_index.json) and the
  [acceptance catalog](../acceptance/production_acceptance_catalog.yaml).
- New acceptance scenarios proposed by these documents use the separate form PA-P01, PA-P02 and so on,
  and are defined in [04 Roadmap](04-roadmap.md) section 6. A partial or adapted run is never reported
  under the original catalog id.
- Each document separates what the specification requires, what the reference package already has and
  what the document proposes.
- Decisions are D1 to D12, phases P0 to P6 and risks R1 to R7 throughout.

## Keeping the documents honest

`tests/test_product_docs.py` checks that every requirement, ADR and scenario id named here exists, that
the backlog traces all 63 requirements, that the roadmap assigns all 30 catalog scenarios, that every
proposed PA-P id is defined in the roadmap and that every relative link resolves. Run it with
`python3 -m pytest tests/test_product_docs.py -q`. It checks traceability, not the strategy.

## How these documents were produced

Six readers extracted the product facts from the specification, the acceptance catalog and the code,
and two researchers surveyed the market with sourced web research (October 2026). Three strategists
then wrote independent proposals from different angles (platform proof, customer value, learning
velocity). Three judges scored them: a skeptical investor, the owner of a design-partner firm and a
principal engineer. The [decision record](02-strategy-decisions.md) synthesizes the winning proposal
with the best answers from the others. Each document was then drafted from that record and checked
against the specification, the catalog, the code and the market sources.
