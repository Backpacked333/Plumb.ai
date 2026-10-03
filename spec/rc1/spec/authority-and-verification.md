# Authority, approvals, data-use enforcement and independent verification

Three authorization layers, an argument-aware gateway, revocation that fails closed, and a Verifier that owns the tests, the truth and the signing key.

## 1. Principals and resources

Principals: platform operator, tenant owner, employee, domain approver, client grantor, sponsor, service identity, build worker, runtime worker, verifier, integration manager. Scopes: tenant, business entity, engagement, provider account, object, field, action, purpose, processor, destination, region, time, spend. Role changes and deprovisioning invalidate approvals and pause connections owned by the departed principal. Resource identifiers and tenant identity are derived from authentication or checked against authority; a model's output never supplies them (SI-003).

## 2. Three layers (SR-014)

| Layer | Decision | Object | Within standing authority |
| --- | --- | --- | --- |
| Observation and data use | Which sources, which purposes, how long, which processors | SourceGrant plus data_use approval of the envelope | Profiling, collection for granted purposes |
| Implementation and operation | Whether to build and operate a described intervention | AutonomyEnvelope; Approval(implement) on the SolutionSpec digest when impact exceeds the auto ceiling; Approval(release_activation) on the ReleaseManifest digest likewise | Build steps, collectors, low-impact releases proceed automatically |
| Case-specific business decision | Whether this action happens on this case | Approval(case_action) bound to the payload digest and case version, or a review item decision | Auto steps whose action declares requires_case_approval false |

A material scope expansion, a new processor, a new commitment class or a new high-impact effect requires the appropriate authority and raises a dependency rather than proceeding.

## 3. Approval objects (SR-016, SI-011)

Bind exact digests and prerequisite state; carry approver, policy version, expiry and a single-use nonce. Links: a GET renders; a POST with the nonce and an authenticated session decides; prefetchers cannot decide; forwarded links fail authentication; a second click finds the nonce consumed (409). Email or chat previews never execute a mutation; "approved" written in a message body is content (gateway test AT-066).

## 4. Revocation (SI-012)

A revocation event reaches: queued effects (cancelled), in-flight effects (cancel requested, provider completion retained), cached capability grants (invalidated), workers (next tool call denied), dependent releases (paused when the revoked grant is a required source), collectors (paused). Writes fail closed while propagation runs; the propagation report is returned by the API. Current prohibitions are enforced; historical policy versions are retained for audit only.

## 5. Gateway (SI-005)

Checks per intent: tenant from credential; case and release in tenant; release active; operation declared in the release; envelope active and version current; effect class, processor and spend within envelope; grants active with operation purpose; approval bound, unexpired, unrevoked, approver role allowed, case version unchanged; for messages the recipient in the client's authorized contacts, template class, attachment scope within the case, per-recipient budget, no commitment class; for record writes the exact provider account and no raw SQL. Reference: reference/policy-gateway/gateway.py.

## 6. Verifier independence (SI-013)

The Verifier owns the protected check bundles, the adjudicated truth, the pass thresholds and the signing key; the builder role cannot read them or insert attestations (roles-and-policies.sql). Acceptance criteria are authored by the domain owner with the platform team; domain truth comes from expert adjudication; ambiguity is adjudicated by the domain approver and recorded. The verifier receives its own credentials to read provider state.

## 7. Verification modes (SR-093)

| Mode | Question answered | Cannot establish |
| --- | --- | --- |
| Development tests | Does the artifact behave as its author expects | Correctness against the business |
| Integration contract tests | Does the adapter honour the provider contract on fixtures or sandbox | Account-level availability |
| Protected acceptance | Does the system produce the adjudicated right result on untouched cases | Business value |
| Adversarial tests | Does a hostile input obtain an effect outside scope | Completeness of the threat model |
| Decision replay | Would the system have decided as the adjudicated truth, given the knowledge boundary | Client behaviour, timing |
| Operational simulation | Does the runtime handle failure paths (crash, timeout, revocation) | Provider behaviour in production |
| Shadow | Does the live system diverge from humans on live cases, without acting | Outcome |
| Canary | Do bounded live actions meet gates | Long-run value |
| Prospective measurement | Did the outcome change for the cohort | Causality beyond the design's power |

## 8. Attestation and denominators (SR-099)

Every attestation names the check, criteria version, digests, environment, account scope, data role, outcome, evidence, verifier identity, time, expiry and limitations. Denominators are task-specific: opportunities for failure per class, error severity, risk slices, uncertainty bounds, calibration, abstention and review burden are reported; "zero high-severity errors observed" is a gate, not a claim of zero risk. Sample sizes follow AS-03 (at least 25 opportunities per high-severity failure class in canary; shadow until 40 opportunities for the top three classes).

## 9. Protected acceptance and repair (SR-097)

The builder sees a diagnostic category and a controlled subset; rows exposed to repair are flagged and leave acceptance; refresh policy: rotate 20% of the set per quarter and after any repair cycle that touched more than 5% of rows; representative audits sample confidently accepted automatic actions.

## 10. Disagreement versus error (SR-096)

Where humans were inconsistent or later corrected, acceptance uses adjudicated truth or marks the case ambiguous; the system may improve on history; matching history is not the objective.

## 11. Omissions

Multi-party approvals (two signatures) are not modelled; a policy_change approval kind exists but its workflow is not specified beyond the gateway refusing builder-applied policy.
