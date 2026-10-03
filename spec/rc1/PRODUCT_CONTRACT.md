# Product contract

Plumb is an autonomous implementation engine for ordinary businesses: the customer supplies business priorities and authority; Plumb discovers useful interventions, designs them, performs the technical implementation, verifies it, deploys it, operates it and improves it. The requirements that make this contract binding are PR-001 to PR-020.

## 1. The promise, as outcomes

Given an AutonomyEnvelope and a goal, every attempt ends in exactly one of these states, each of which stays in the discovery and build denominators (PR-001, PR-015):

| Outcome | Meaning | Counts as verified deployment |
| --- | --- | --- |
| Operating intervention | A release is ACTIVE, new cases complete their predicate, attestations are current | Yes |
| Waiting for an external dependency | A precise ExternalDependency is open; unaffected work continued; the build resumes when resolved | No |
| Terminal implementation failure | A FailureDiagnostic explains what was attempted and why execution stopped | No |
| No beneficial intervention found | Discovery produced hypotheses; none cleared feasibility and value with evidence | No |
| Infeasible intervention | A hard constraint (authorization, legal, unavailable operation, impact class) blocks the only designs | No |
| Retired or superseded proposal | A later opportunity or capability replaced it | No |

## 2. What "implementation" includes (PR-002)

Configuring native software features; connecting accounts and applications; generating and adapting integration code; mapping fields and identities; constructing historical and prospective collectors; finding usable input, decision and outcome relationships; creating and validating datasets; selecting and configuring models, rules, retrieval, specialist services or optimizers; submitting training jobs where warranted; provisioning serving and runtime resources; generating workflows and review surfaces; testing; deployment; monitoring; bounded repair; retirement or replacement. All of these are performed by Plumb within the envelope. The customer retains authorization, legal and commercial commitments, business-policy clarification and professional sign-off (PR-006).

## 3. Scope tiers (PR-009)

| Tier | Content |
| --- | --- |
| Target capability | Broad discovery across roles and systems; the three opportunity routes; agent-built adaptation and new supported capability; learning-enabled components; higher-impact certified operations; sponsor portfolios; second and third domains |
| First release (certified) | Accounting evidence collection and review preparation at one firm: Google Workspace (Gmail threads and drafts, templated send after IG-001), Google Drive (listing, changes), QuickBooks Online (query, change capture, webhooks; read only), consolidated client requests under a reminder policy, a review-ready package with accountant sign-off through a Gmail draft and the companion surface; no ledger writes; coverage tiers exact template, new composition and agent adaptation for Drive folder mapping |
| Later certified coverage | QuickBooks writes under IC-012; Plaid statements after IG-005; practice-management tools; payroll providers; UI bridges with certified writes; field capture; other languages; on-premise; marketplace |

## 4. Three kinds of opportunity (PR-004)

Friction in existing work; an important outcome or obligation currently neglected; a useful new activity enabled by available technology. Each route needs evidence for the problem or objective, never for the solution's steps. The system must also recognise when removing a step, using an existing feature, changing a rule or doing nothing beats adding AI (PR-005).

## 5. Completion and billing (PR-008, PR-012)

| Predicate | Meaning | Release 1 |
| --- | --- | --- |
| review_package_prepared | All checklist items present or explicitly missing with a sent request; package digest recorded | Delivered, not billable |
| review_package_accepted | The accountant accepted the package bound to its digest | Delivered, billable |
| close_completed | Ledger closed for the period | Not delivered |
| posting_executed | A certified accounting write confirmed with receipt | Not delivered |

Implementation autonomy is reported from LaborRecords by category (PR-013); runtime automation is reported from case predicates and effect states. They are never combined into one number.

## 6. What Plumb never does

Act outside an approved envelope; bypass MFA, licensing, provider terms or unavailable endpoints; train on data without a training purpose; treat a model's output as approval, verification or completion; retry an ambiguous external effect without reconciliation; claim a deployment is autonomous while engineering intervention minutes are non-zero.
