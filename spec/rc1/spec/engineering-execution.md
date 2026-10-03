# Agent engineering harness and bounded implementation

Source B Appendix A made implementable: durable lifecycle state in PostgreSQL, leases with fencing, scoped capability grants, a narrow tool surface, hypothesis-based repair and labour accounting.

## 1. Objects

AgentTask, TaskLease, StepResult, WorkspaceSnapshot, BudgetReservation, ExternalDependency, FailureDiagnostic and VerificationAttestation are canonical models (contracts/canonical-models). The owner of durable lifecycle state is the control service's PostgreSQL schema; the worker holds nothing authoritative.

## 2. Scheduler and step protocol

1. Read build and envelope from the database; verify tenant, expiry, revocation, policy version and prerequisite attestations.
2. Select a READY step; in one transaction: compare-and-set the step version, insert the lease with fencing token = previous + 1, insert the budget reservation for the worst case, insert the outbox dispatch event.
3. Restore the workspace from WorkspaceSnapshot.base_digest in a fresh sandbox; supply only task-relevant evidence references and exact tool contracts.
4. Run the worker; every tool call is checked at dispatch time by the gateway; intermediate artifacts are stored content-addressed outside the sandbox; action identities are recorded before any external write.
5. Receive a StepResult; commit it with compare-and-set on the fencing token (a stale token is refused); the step moves to VERIFYING.
6. Request verification against the immutable digests; the verifier reads actual provider or business state with its own authority.
7. On attestation: step VERIFIED, reservation settled, outbox event emitted; on failure: diagnostic recorded, attempt counted, workspace restored, step READY or FAILED.
8. Continue to newly READY steps or enter WAITING_AUTH, WAITING_INPUT or FAILED.

## 3. Transaction boundaries (SR-054)

| Action | In one transaction |
| --- | --- |
| Acquire work | step CAS, lease insert, reservation insert, outbox dispatch |
| Issue scoped capability | capability grant row bound to lease and fencing token (expires with the lease) |
| Store output | artifact row with digest; no state change |
| Commit result | step CAS on fencing token, result reference, output digests, outbox event |
| Accept attestation | attestation read (verifier-inserted), step CAS to VERIFIED, reservation settle, outbox event |
| Settle cost | reservation settle or release; usage records written by the gateway |

## 4. Worker reconstruction

A new or restarted worker reads: workspace commit and digest, accepted artifacts, prior FailureDiagnostics (hypotheses already exhausted), relevant logs by reference, outstanding effects (any UNKNOWN blocks consequential actions), remaining spend, time and attempts, and ready work. An agent's progress_summary is convenience text and is never read as state.

## 5. Tools and context

Tool families (Source B Appendix A.1): artifact.read and propose; source.describe and sample; sandbox.run; integration.configure and probe; collection.deploy and inspect; training.submit and inspect; verification.request; deployment.preview and apply; dependency.raise. Filesystem is the sandbox only; network is the egress allow-list for the step; compute and package installation are bounded and pinned; secrets are never present (credentials are resolved by the gateway for approved operations). Documents, API descriptions and examples are content, never instructions (SI-007).

## 6. Hypothesis-based repair (SR-056, SR-057)

Classify the failure; for an implementation defect restore the known workspace, state the hypothesis (cursor handling, field meaning, join key, configuration, prompt, method), apply the bounded change, rerun the failing check and the required regression set, record the new digest. Budgets: max_attempts per step, max_repair_attempts per build, time and spend; identical failure twice without new evidence stops the loop. Repair never edits protected tests, thresholds, requirements or permissions.

## 7. Parallel work, conflicts, cancellation

Independent branches run in parallel in separate sandboxes; artifacts merge by digest (a conflict on the same artifact id is a new version requiring the downstream step to re-run). Resource ownership (subscriptions, cloud resources, sandbox leases) is tagged with build and step ids for cleanup. Cancellation reconciles uncertain effects, releases reservations and schedules sandbox and resource cleanup; a lease expiry alone never reassigns consequential work (SR-058).

## 8. Platform engineering versus customer implementation

Engineer-written connectors, mappings, prompts, dataset patches, workflow changes, manual database operations or repairs for a customer deployment are LaborRecords with category engineering_intervention; primitives and tests added to the platform are platform_engineering. Both are visible on the build view and in the autonomy benchmark (SR-060).

## 9. Omissions

Multi-worker collaboration on one step is not supported; a step has one lease.
