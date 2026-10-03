# Customer experience, the human work contract, metering and billing

The normal user sees goals, evidence coverage, proposed changes, expected outcomes, authority, progress, blockers, review items, costs, incidents and measured results. Nobody edits SQL, DAGs, prompts or training containers (PR-003).

## 1. Studio views

Capture, Review, Week, Ontology, Process, Opportunities, Market, Builder, Replay and Workflows (Source A's nine, with Replay and Workflows merged into Operations). The Builder view renders the Blueprint as a build card.

## 2. Principal journeys

| Journey | Entry condition | Visible state | Primary action | Backend mutation | Role | Acknowledgement | Failure state | Resumability | Audit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Owner sets priorities | Verified identity | Goals, calendar, intervention classes, spend caps | Save and draft envelope | createEnvelope | tenant_owner | Draft shown with pending approval | Validation errors inline | Draft persists | audit_log |
| Owner approves envelope | Draft exists | Diff of scope, processors, destinations, spend | Decide (nonce) | decideApproval; activateEnvelope | tenant_owner | Envelope active | 409 on consumed nonce or changed draft | Re-request approval | approvals |
| Grantor connects a source | Consent request exists | Provider consent screen, purposes, retention | Consent in provider | recordGrant | client_grantor or owner | Grant active with account identity | Provider error; unsupported institution fallback | Retry consent | source_grants |
| Employee enrols capture | Notice acknowledged | Scope, exclusions, pause state, retention | Enrol, pause, scope | device enrolment; grant for device | employee | Indicator state | Permission denied by OS | Re-run installer | audit_log |
| Owner accepts an objective | Opportunity evidenced | Why panel, coverage, benefit range, alternatives, falsifiers | Accept objective | acceptObjective | tenant_owner | Status objective_accepted | 412 on stale version | Reload | opportunities |
| Owner reviews a build card | Solution selected | What changes in which systems, affected people and accounts, allowed actions, data destinations, budget, evidence, uncertainty, needed decisions | Approve implement (if required) or start | createBuild; decideApproval | tenant_owner | Build running or waiting | Validation 422 with pass codes | Resume from state | builds |
| Respondent resolves a dependency | Dependency open | Question, evidence, options with consequences, who may answer | Resolve with scope | resolveDependency | respondent role | Build resumed | 403 wrong role | Open until resolved | external_dependencies |
| Worker reviews a request draft | Case WAITING_REVIEW | Draft, evidence, recipient, items | Approve, correct, reject | decideReviewItem | assigned role | Case resumes | 409 case changed; item invalidated | New item | review_items |
| Accountant signs off a package | Package ready | Package digest, items, evidence, prior corrections | Accept or return | decideReviewItem | domain_approver | Case COMPLETED | 409 on changed evidence | New item | review_items, billable_units |
| Owner reads outcomes and costs | Release active | Units, review minutes, failures, effects, ledgers, outcome observations with method | Read; export | listOutcomes; getLedger | tenant_owner | n/a | Empty state | n/a | n/a |
| Operator handles an incident | Alert | Affected cases, clients, releases, effects | Pause, reconcile, resume | transitionRelease; reconcileEffect | platform_operator | Transition applied | Guard refused with reason | Open incident | audit_log |
| Sponsor views portfolio | Sponsor principal | Per firm: top opportunity, build status, replay result, hours returned, cost per unit; small-cohort suppression | Read | reporting views | sponsor | n/a | Suppressed cells | n/a | audit_log |

Empty, partial-data, loading, no-op, failed, revoked, stale and conflicting states are specified per journey in the Studio component library; keyboard operation and screen-reader labels are required for every review action; review decisions are reachable from the existing tool (Gmail draft or a link to the companion surface).

## 3. Build card contents

Goal and evidence coverage; what will change in which systems; affected people and accounts; allowed actions and effect classes; data destinations and processors; maximum spend; expected benefit hypothesis with range; uncertainty and falsifiers; test evidence; needed decisions grouped; no "Allow AI" button.

## 4. Worker contract

Capture controls, evidence corrections (scoped, with the downstream impact shown), domain-policy clarifications, review queue. Pause behaviour and observation gaps are never an employee-performance score; no per-person productivity reporting exists.

## 5. Review surfaces (IC-013)

Gmail draft (native, verified): the drafted request sits in the worker's Drafts with a Plumb header; sending inside Gmail is recorded by the thread watcher as a human send, not an automated effect. Plumb companion surface: authenticated, reached from the email or Studio, used for package sign-off and corrections. No native QuickBooks review queue is claimed.

## 6. Professional sign-off and delegation

Assigned role with optional named principal; delegation by the owner with expiry; unavailable reviewers escalate after the SLA to the escalation route; duplicate decisions hit the consumed nonce; changed evidence invalidates the item; reassignment records both principals; a model never resolves an authority dispute.

## 7. Ledgers (SR-123, DC-023)

| Ledger | Producer | Identity | Attribution | Corrections | Aggregation |
| --- | --- | --- | --- | --- | --- |
| Provider usage | Model gateway, connector runtime, training and infra adapters | usage_id | case, build, release, part | correction_of row | Daily per tenant |
| Plumb operating cost | Cost service | cost_id | category, period | New row | Monthly |
| Human labour | Studio and operator tooling | record_id | build or case, category | New row | Per build and release |
| Business outcomes | Measurement service | observation_id | case or release, method | New row with limitations | Per cohort |
| Billable units | Billing service from case completion | unit_id | case, epoch, predicate, release | credited or superseded status | Monthly invoice |

Reservations are atomic per build step and per effect; hard caps are enforced on controllable spend; provider charges that arrive late are estimates until settled; cancellation releases unspent reservations and records charges the provider cannot stop.

## 8. Billing predicate and edge cases (PR-012, DC-024)

Release 1 bills review_package_accepted once per case, obligation epoch and predicate. Failed cases, partial delivery and prepared-but-not-accepted packages do not bill; reopen supersedes the unit for the new epoch; duplicate triggers cannot create a second case; overlapping workflows cannot double-bill the same obligation. Credits are rows. Prices from Source A (per-unit fee in the low tens of dollars; pass-through at cost; portfolio licence) are proposals adopted as the initial price list; commercial guarantees are proposals requiring the mechanics in acceptance/business-outcome-measurement.md.

## 9. Workload and cost model

See ARCHITECTURE.md §7 for first customer, early multi-tenant and target scale with arithmetic and sensitivity.

## 10. Omissions

Localization and accessibility conformance level are not specified beyond keyboard and screen-reader requirements.
