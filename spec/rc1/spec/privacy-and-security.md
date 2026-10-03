# Security, privacy, rights and the removal lifecycle

The safe property: a compromised reasoning step cannot obtain an effect outside its enforced capability and data scope. Isolation is layered, secrets never meet generated code, source rights are a registry, and removal is a state machine that tells the truth about trained weights.

## 1. Data-flow threat model

| Flow | Threat | Control | Test |
| --- | --- | --- | --- |
| Capture → device store | Frames exfiltrated | Device-only frames, 60 s deletion, encrypted queue, device cert | AT-080 |
| Device → cloud | Envelope tampering, replay | Signed envelopes, deterministic ids, dedup | AT-080 |
| Ingestion of documents and mail | Malicious documents, prompt injection | Content is data (SI-007); parsing limits; no instruction authority from content | AT-066; catalog Security |
| Registry updates | Untrusted API descriptions | Quarantine; updater has no destination or permission authority | AT-071 |
| Generated code | Secret leakage, supply chain, SSRF | Sandbox without secrets; pinned dependencies; egress allow-list; dependency scanning | IG-009 |
| Training | Poisoned labels, forbidden purpose | Label authority, audits, purpose checks at dataset build | AT-092; AT-063 |
| Serving | Compartment leak via weights or cache | Audience lists, compartment-aware cache keys | AT-094 |
| Execution | Confused client identity, unauthorized destination | Argument-aware gateway, protected references resolved per case | AT-065; AT-069 |
| Verification | Builder forging attestations | Role separation, signing key in HSM, digests | AT-052; AT-053 |
| Logs and support access | Payload leakage | Payloads off by default; support access is a time-boxed grant with audit | DC-025 |
| Export and sponsor reporting | Over-disclosure | Aggregates only; raw never granted | SI-014 |
| Insider misuse | Operator reads customer data | Break-glass with approval, audit and expiry | catalog |

## 2. Enforceable boundaries (SI-002)

Database rows (RLS plus roles), object storage (prefix plus key), retrieval indexes (namespace per tenant and compartment), caches (keys include tenant, compartment, purpose, release), workspaces (one sandbox per step), queues (per-tenant topics on the outbox), logs (tenant tag, no payloads), model adapters (per tenant), training jobs (per tenant credentials), sponsor reporting (aggregate views). Tenant isolation is distinct from client and employee permissions inside a tenant (compartments).

## 3. Identities, secrets and supply chain (SI-009, SI-010)

Restricted service identities per role; credential resolution by the gateway at dispatch; short-lived grants bound to leases; token rotation per provider policy; package pinning and dependency scanning; build provenance and artifact signing; protected verifier keys; network policy with egress allow-lists; parsing limits; webhook signature verification, replay defence and bounded payloads; SSRF controls on every fetch destination. The trusted platform itself updates through signed releases with a controlled patch process and a rollback plan; a buggy gateway is patched through the same release gates with an operator-approved emergency path.

## 4. Source-rights registry (DC-022)

Per source and purpose: collection, transformation, evaluation, training, inference, export, cross-customer reuse, support access; the provider terms version in force; the grant that permits each. Permission to read is never permission to train or disclose; user consent does not override provider terms; a change in terms triggers re-evaluation of affected operations.

## 5. Removal lifecycle (removal.yaml, SR-126 to SR-130)

RECEIVED → VALIDATED (identity and scope) → INGESTION_STOPPED (collectors paused, subscriptions suspended) → IMPACT_COMPUTED (datasets, models, indexes, caches, backups, pending approvals, open cases) → optional ON_HOLD by authorized review → ACCESS_DISABLED (serving routes and indexes disabled) → DERIVED_REMOVED (tombstones cascade; datasets UNAVAILABLE with lawful tombstone manifests) → PROVIDER_CLEANUP_PENDING (deletion requests to processors recorded, confirmed or timed out with record) → BACKUPS_SCHEDULED (expiry within the 35-day rotation, AS-07) → COMPLETED (minimal lawful audit retained; completion evidence issued). Distinct operations: source deletion, derived-data deletion, model retirement, retraining, provider deletion requests, supported unlearning if a provider offers it. No promise of exact instant removal from weights; while remediation is pending, affected models are retired or quarantined and routes disabled (SR-128).

## 6. Adversarial scenarios owned here

Prompt injection in documents and API docs; unauthorized recipient; malicious attachment; SSRF destination; secret in generated code or logs; dependency compromise; model, retrieval or cache compartment leak; sponsor requesting raw evidence; removal affecting datasets, models and backups. Each is a named scenario in acceptance/production-catalog.md.

## 7. What is implemented versus release-blocking

Implemented in reference: argument-aware gateway checks, receipt verification, digest and detached approvals. Unimplemented and release-blocking: sandbox isolation and egress enforcement (IG-009), RLS under real roles (IG-008), artifact signing, HSM-held verifier keys, SSRF controls, dependency scanning pipeline, break-glass access workflow.

## 8. Legal and contractual questions needing qualified review (AS-08)

| Question | Operational rule affected | Owner | Release gate |
| --- | --- | --- | --- |
| Employee electronic monitoring notice requirements in the customer's jurisdictions | Enrolment notice templates; capture cannot start without acknowledgement | Counsel with the product owner | Before any desktop enrolment |
| Call and meeting recording consent across the parties' locations (not only the line's registered location) | Transcript ingestion gated per call on the provider's consent evidence | Counsel | Before recording ingestion |
| Use and disclosure limits on tax return information held by a preparer | Purpose and processor restrictions for any tax document; not reducible to zero-retention routing | Counsel with the domain owner | Before tax documents enter any model path |
| Safeguards obligations of financial-data handlers and how Plumb's controls map to the customer's program | Documentation deliverable | Security lead | Before first production customer |
| Biometric and field capture rules | Field capture remains out of scope | Counsel | Before any field pilot |
| Provider developer terms (Google Workspace user data policy, Intuit, Plaid) on data use beyond the user's own purposes | Source-rights registry entries; pooled or cross-customer learning forbidden by default | Security lead | Before any pooled learning |
| Non-US deployments (GDPR assessments, works councils, Israel's 2025 privacy amendments) | Out of release 1 | Counsel | Before any non-US customer |

Nothing in this table is asserted as the law; each is an interpretation to be resolved by qualified review.
