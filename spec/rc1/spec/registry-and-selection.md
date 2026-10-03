# Market registry and full-system selection

The Market is an operation- and task-level capability registry; claims carry a verification level and expire; selection compares whole systems; capability deltas generate new opportunities.

## 1. Entry contract (IC-001)

Provider, release identity, environment and account eligibility, exact operations, input and output semantic types, permissions and scopes, data purposes, residency and processor constraints, limits (rate, page, look-back, payload), pricing basis with source URL and date, support status, documentation source, test evidence (which kit, which account, when), known failures, maintenance burden (observed repairs per quarter), freshness policy (re-verify interval; invalidation triggers).

## 2. Verification levels and expiry (SR-036)

| Level | Established by | Expires |
| --- | --- | --- |
| documented | A documentation page was read | 30 days |
| locally_tested | The adapter contract kit passed against recorded fixtures | On adapter or kit change |
| sandbox_tested | The kit passed against the provider sandbox | 90 days or provider release |
| account_verified | A probe succeeded on the customer's account for the exact operation | 30 days or on scope, entitlement or terms change |
| production_observed | The operation executed in production with a verified receipt | Rolling 30 days |

A change in provider version, terms version, account entitlement or observed API behaviour invalidates the affected level; the compiler then rejects dependent plans until re-verified (E_CAPABILITY_UNAVAILABLE).

## 3. Acquisition, normalization, quarantine (SR-037)

Registry updates come from documentation crawls, provider changelogs, kit runs and production receipts. Crawled text and tool descriptions are untrusted: they are normalized into the entry schema by a parser, scored for consistency with prior entries and quarantined on disagreement until a person releases them. The updater role can write registry rows only; it has no access to envelopes, grants, destinations or policies.

## 4. Selection over complete systems (SR-074)

Inputs: the OpportunitySpec, the inventory, the data-asset profile, the envelope. Search: enumerate candidate systems from the solution classes, prune by hard constraints (authorization, data terms, residency, unavailable operations, impact class), estimate joint error behaviour from kit results and learnability profiles, estimate total cost (setup, staff effort, review, provider usage, idle capacity, maintenance), run bounded experiments (budgeted, on held-out tenant samples) where the decision turns on measured performance. Output: SolutionSpec with candidates, decision record and experiment evidence. There is no rule that fine-tunes below or above a sample count; training competes on measured task performance and total cost.

## 5. Targeted re-evaluation

Triggers: a relevant capability change (price, deprecation, new operation), an observed failure class, new labels crossing the learnability floor, changed business economics (volume, review cost). Not a daily sweep of every provider.

## 6. Capability-to-opportunity loop

Capability delta → affected business patterns (which pack steps use the operation class) → eligible tenants and existing blockers that name it → new hypothesis (route new_capability) → feasibility probe → evaluation budget → authorization check (within envelope or a new dependency) → build. The loop must create new interventions, not only cheaper swaps; a swap inside an existing workflow is a release change evaluated against the whole system (SR-073).

## 7. Omissions

Pricing negotiation and vendor contracting are outside the registry; it records terms, it does not sign them.
