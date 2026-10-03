# Glossary, entity relationships and authority map

## 1. Terms

| Term | Meaning |
| --- | --- |
| Tenant | One customer business with its own isolation boundary |
| Principal | An authenticated actor: platform operator, tenant owner, employee, domain approver, client grantor, sponsor, service identity, build worker, runtime worker, verifier, integration manager |
| SourceGrant | Layer-1 authority to read a provider account for stated purposes with retention and processor limits |
| AutonomyEnvelope | Layer-2 standing authority for implementation and operation: goals, scope, processors, destinations, effect classes, auto-impact ceiling, spend, expiry, escalation |
| Approval | A human decision bound to exact digests and prerequisite state with a single-use nonce (kinds: data_use, implement, release_activation, case_action, policy_change) |
| EnvironmentInventory | What is actually accessible: systems, accounts, operations with verification levels, history, update mechanisms |
| Capability | One operation on one provider account at a verification level (documented, locally tested, sandbox tested, account verified, production observed) |
| EvidenceEvent | One permissioned, time-stamped piece of evidence with a protection report and lineage |
| EvidencePacket | Permission-filtered evidence assembled for a purpose under a knowledge boundary |
| Fact | A derived statement about an object with status, evidence and source-of-record precedence |
| Obligation | Who owes what to whom for which case by when, under which rule version, with an epoch |
| OpportunitySpec | The business problem, population, baseline, hypothesis, benefit range, constraints and measurement plan |
| SolutionSpec | The selected whole-system design with candidates, decision record, outcome semantics and impact class |
| BuildPlan | Finite DAG of typed build steps with budgets, bounds and verification obligations |
| WorkflowSpec | Business runtime semantics: case identity, triggers, states, transitions, actions, waits, loops, completion predicate |
| ReleaseManifest | Immutable identity of the deployable composition with digests and required checks |
| VerificationAttestation | Verifier-issued evidence of a specific check against specific bytes, scope and criteria |
| ActionIntent / EffectRecord | Durable identity, authority and history of one external effect |
| OutcomeObservation | Evidence about the customer result, separate from technical success or billing |
| Blueprint | The customer-facing rendered view over the artifacts above for one intervention (not a stored mutable object) |
| Market | The operation-level capability registry |
| Tap | A declared source of labels with a backfill job and a live listener (a CollectionSpec whose purpose is evaluation or training) |
| Valve | A case-level human decision point (a WorkflowAction with requires_case_approval or a review state) |
| Domain pack | Ontology extension, obligations, predicates, rules, review surfaces and certified operations for one domain |
| Effect slot | tenant, case, obligation epoch, operation, target: the semantic identity of an external effect |
| Coverage tier | exact template, new composition, agent adaptation, agent new capability, unsupported |
| Agent levels L0 to L4 | Source A's explanatory labels for how much an agent acts on its own; never used for enforcement |

## 2. Entity relationships

Tenant has Principals, SourceGrants, AutonomyEnvelopes (versioned). An EnvironmentInventory is produced per tenant from grants and probes and holds Capabilities. EvidenceEvents link many-to-many to business objects; Facts cite EvidenceEvents; Obligations reference objects and an engagement. An OpportunitySpec cites an EvidencePacket; a SolutionSpec cites one OpportunitySpec and lists candidates; a BuildPlan cites one SolutionSpec and one envelope version; a Build executes a BuildPlan and owns Steps, Leases, Reservations, Dependencies and Diagnostics; Steps produce Artifacts (IntegrationSpec, CollectionSpec, DatasetManifest, TrainingSpec, ModelVersion, WorkflowSpec); a ReleaseManifest composes artifact digests and collects VerificationAttestations; Cases pin a release and own ActionIntents, EffectRecords, review items and BillableUnitRecords; OutcomeObservations cite cases or releases; LaborRecords cite builds or cases; RemovalRequests compute impact over all of the above.

## 3. Authority map

| Value | Authority | Who may set it |
| --- | --- | --- |
| tenant_id on any request | platform | Derived from the authenticated credential (SI-003) |
| Grant purposes, retention, scope | asserted | Client grantor or tenant owner through the OAuth flow |
| Provider account_ref | external | Verified provider identity at connection time |
| Envelope contents and version | asserted | Tenant owner, with a data_use approval |
| Capability verification level | platform | Verifier service after a probe |
| EvidenceEvent times and digest | external or platform | Source timestamps as observed; ingested_time by the platform |
| Fact status observed, inferred, stale, superseded | derived | Knowledge service |
| Fact status confirmed or disputed | asserted | Employee, analyst or domain approver |
| Obligation status, epoch | derived with asserted exemptions | Workflow runtime; exemption by domain approver |
| Opportunity objective_accepted_by | asserted | Tenant owner |
| SolutionSpec selected candidate | derived | Sourcer and Analyst agents, recorded with a decision record |
| Approval decision, nonce consumption | asserted | Authenticated approver; nonce by platform |
| Build and step states | platform | Control service through the guarded machine |
| StepResult | proposed | Build worker; never authoritative |
| Attestation outcome | platform | Verifier identity only |
| Release state | platform | Control service; activation requires approval when impact exceeds the envelope ceiling |
| ActionIntent effect slot and digests | platform | Gateway |
| Effect state | platform | Dispatcher through the guarded machine; NEEDS_HUMAN resolved by a domain approver |
| Case version | platform | Workflow runtime |
| BillableUnitRecord | platform | Billing service from case completion |
| LaborRecord | asserted | The person who did the work or the analyst recording it |
| OutcomeObservation | derived | Measurement service with a method and limitations |

## 4. Reference resolution, digests and schema evolution

A Ref names an object type, an id and the digest of the canonical bytes (DC-003). Aliases ("latest") are resolved to a digest before a run and the resolution is recorded on the Ref. Digests exclude fields named content_digest, manifest_digest, approval_id, signature and approvals, so an approval or signature can be attached without changing what it covers. Schema evolution is expand-only within a major version: a new optional field never changes existing digests because absent fields are not serialized; a renamed or removed field is a new schema_version and a new release schema version (SR-048). The Blueprint view renders the seven artifacts with their versions and the attestation status of each; its own view digest is informational and never approved.
