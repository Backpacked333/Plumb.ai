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
and bookkeeping (at least 60% of revenue), at least 50 recurring monthly-close clients with 12-24
months of history, and a mixed stack (QBO and/or Xero, Google Workspace or Microsoft 365, a separate
document store). Firms standardized on one ecosystem whose native chase-and-match already works are
qualified out ([market](08-market-and-positioning.md)).

**What first.** Monthly-close evidence readiness, preparation-only: for every recurring client-period
Plumb knows which required documents are present, confirmed absent or unknown, with provenance, and
prepares one ready-for-review package for the accountant. The Prepare tier uses only the READ,
INTERNAL_WRITE and EXTERNAL_WRITE_REVERSIBLE effect classes (connector setup and incremental capture on
the firm's own accounts), never EXTERNAL_COMMUNICATION. No client communication until a production
action gateway passes the high-severity effect scenarios, which is after day 180; staff-sent mailbox
drafts come first, and the earliest policy-approved Send canary close is around July 2027
([MVP scope](03-mvp-scope.md)).

**In what order** ([roadmap](04-roadmap.md)):

| Phase | Proves |
|---|---|
| P0 Commit and instrument | Effort ledger, threshold sheet and a truthful capability registry exist before any build |
| P1 M0 | Real probe receipts on the first firm's accounts; envelope and data agreement signed |
| P2 M1 | An agent-built, verifier-attested integration-and-collection path on firm 1 (PA-001 plus a safety bundle) |
| P3 M1R | The same path reproduced on firms 2 and 3 with less audited engineering: the second half of PL-063, pulled forward |
| P4 M3-lite | A preparation-only review-package workflow, attested in sandbox, then in production shadow |
| P5 Day-180 packet | Verifier-attested ready-for-review packages on at least 30 client-periods in a full shadow close, measured against a month-0 baseline; go, pivot or kill. The packet records tenant 1's evidence toward paid conversion to date |
| P6 M4-accounting and M5 | In the Apr-Jun 2027 window (earliest): the Prepare tier's canary and ACTIVE closes and tenant 1's expected paid conversion, the Draft tier (mailbox drafts staff send), and the start of full replication on the next three customers (PA-027). The policy-approved Send canary needs two Draft closes first, so its earliest close is around July 2027 (about weeks 39-41) |

**How success is measured** ([metrics](06-metrics.md)). North star: engineering-intervention hours
per verified deployment (EIH/VD), per new firm in onboarding order, with platform-investment hours
shown beside it and never netted. Customer co-headline: accepted review packages per month.

**How it is sold** ([market](08-market-and-positioning.md)). "Verified implementation" for accounting
firms: "Close-ready, with receipts." Hypothesis: $15 per active client-month for Prepare, $25 once
policy-approved sending ships, annual, with a $500 monthly firm minimum, no seats and no implementation
fee. Only attested packages are billed: customer-side dependencies are not billed while open (the
minimum still applies), and Plumb-side blocks and failures never are. Design partners pay a
$1,500-$3,000 pilot fee at signature and convert to paid annual after one full close with the workflow
ACTIVE at or above the correct-package threshold; tenant 1's conversion is expected in P6 (a founder
decision to ratify).

**What we never claim.** That local tests validate models, outcomes, security or integrations; that
the synthetic scenarios show cross-industry autonomy; that 90 days is a commitment; an autonomous
close or posting; "fully autonomous" or "no humans needed"; integration coverage from the synthetic
registry; savings without a baseline and a denominator; anything beyond the released tier. The full
12-item checklist is decision D8 in the [decision record](02-strategy-decisions.md).

## Decisions the founder needs to make first

These block P0-P2. Each line gives the decision (its row number and decide-by phase) and the
recommended default; the full table, with options, is in the
[decision record](02-strategy-decisions.md#founder-decisions-needed).

- **M1 construction bar (1, P0).** PA-001 plus an agent-filled plan and an agent-generated mapping;
  fall back to PA-001 as written if sandbox work slips more than 4 weeks.
- **Replication timing (2, P0).** M1R on tenants 2 and 3 right after M1, not deferred to M5.
- **Effort rubric (18, P0 week 1).** Ratify the amended D6 rubric: every human minute on a tenant,
  customer or Plumb staff, lands in one of the five categories with its principal, Plumb time
  defaulting to ENGINEERING_INTERVENTION when in doubt; add a Plumb-staff principal type.
- **Pilot terms and pricing (3, 4 and 21, P0-P1).** A $1,500-$3,000 paid pilot credited to year
  one, a 90-day clock from the first attested path and pilot terms at no further fee until
  conversion; $15 Prepare, $25 Prepare + Chase, $500 minimum.
- **Data rights, IRC 7216 and SERVE (7, 9 and 10, P0).** An explicit per-source SERVE grant the
  checker enforces; tax-return information excluded from v1; TRAIN off by default, opt-in per source.
- **Early hires (12, P0).** A security/platform engineer in weeks 0-4 and an independent
  verification engineer by week 6.

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
