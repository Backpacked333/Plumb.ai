# Release, infrastructure, desired-state reconciliation, reliability and reuse

A release is an immutable verified composition; rollout is gated; infrastructure changes are constrained; kill switch, rollback, restoration and compensation are four different things; reliability and reuse are measured.

## 1. Release composition and invalidation (SR-115)

Components: workflow, connectors, collectors, models, prompts, rules, schemas, policies, infrastructure plan, plus the acceptance evidence references. Required digests: every component; the manifest digest excludes approvals. A change to any component makes a new release; attestations bound to the old digests are invalidated; a release is rejected when a required attestation was produced for different bytes or a different scope.

## 2. Lifecycle (release.yaml)

CANDIDATE → VERIFIED (attestations from the verifier identity on the manifest digest) → APPROVED (activation approval when required) → SHADOW → CANARY → ACTIVE → PAUSED → ACTIVE; ACTIVE or PAUSED → ROLLED_BACK (previous compatible release re-activated, in-flight cases pinned or migrated) → RETIRED. Build authorization, build execution, release verification and release approval are separate from case and effect lifecycles.

## 3. Infrastructure operations (SR-117, IC-014)

Resource templates and reviewed modules only; the deployment adapter performs preview, diff, cost estimate, state lock, ownership tags, delegated short-lived credentials, apply and post-apply verification; preview is run in the sandbox with the same egress controls because it executes program logic.

## 4. Desired and observed state (SR-120)

For integrations, collectors, subscriptions, serving resources, review surfaces and workflows the control service stores desired state and a reconciler compares observed state at the health interval. Drift that is safe to repair automatically (a renewed watch channel, a re-subscribed webhook) is repaired within bounds and recorded; unauthorized customer or provider changes raise a dependency; resources tagged to a cancelled or failed build are cleaned up by the cleanup job with orphan detection daily.

## 5. Database and workflow evolution

Expand, backfill, validate, contract; old workers drain before contract; schema compatibility checked by the compiler (SR-048); a new release never re-runs effects from a prior release (slots are global) and never switches behaviour inside an approval-sensitive case (pinning).

## 6. Four separate mechanisms (SR-118, SR-119)

| Mechanism | What it does | What it cannot do |
| --- | --- | --- |
| Kill switch | Stops new dispatches within 60 s; lists in-flight requests within 5 minutes | Stop a request the provider already accepted |
| Code and configuration rollback | Re-activates the previous compatible release | Change external records |
| State restoration | Restores internal state from backup; dispatch stays disabled until effect and case reconciliation prevents duplicates | Undo external effects |
| Compensating business action | A new authorized effect (retraction, correction) | Make the original disappear from the audit |

## 7. Reliability

Tenant fairness by per-tenant queues; quotas and rate limits per tenant and provider; priority scheduling (revocations and kill switches first, review deliveries second, builds last); backpressure by bounded outbox consumers; burst onboarding throttled by backfill windows; long-running jobs checkpoint by watermark; dead-letter after five attempts; queue retention 90 days; overload sheds builds before runtime. Degraded read-only operation when the policy or credential service is unavailable; writes fail closed (SI-015).

## 8. Reuse and compounding (SR-125)

Reusable assets: verified adapters, semantic mappings (without customer values), collection patterns, task definitions, workflow primitives, domain rules, evaluation fixtures (synthetic), repair knowledge, cost and maintenance evidence. Each carries provenance, version, applicability constraints (provider version, scopes, pack), certification level, owner and invalidation conditions. A template applied to a new customer is rechecked for field semantics, client identity, chart and policy differences, permissions, account capabilities, costs and acceptance criteria. A successful repair becomes a library candidate through a platform engineer's review and kit runs across supported configurations; affected deployments receive it as a new release. Reuse is measured by implementation effort and maintenance per capability class, not by aggregate deployments.

## 9. Omissions

Blue-green infrastructure and multi-region failover are not specified.
