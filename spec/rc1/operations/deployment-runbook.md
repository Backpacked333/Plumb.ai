# Deployment runbook

Proposed procedure for the first environments; nothing here has been executed.

## 1. Environments

dev (shared, synthetic data), staging (provider sandboxes, synthetic tenants), production (one region). Each has its own PostgreSQL, Temporal namespace, vault namespace, object store buckets and sandbox pool.

## 2. Bootstrapping a new environment

1. Apply migrations 0001 to 0006 with the migrator role; verify with the isolation test (IG-008) using the runtime roles.
2. Deploy the control service, gateway, verifier (with its key in KMS or HSM), evidence workers, build orchestrator, outbox consumers, Temporal workers, Studio.
3. Register Market entries for the certified operations at documented level; run the adapter kit against sandboxes to reach sandbox_tested.
4. Create the platform operator principal; create a synthetic tenant; run the accounting fixture plan end to end in staging against sandboxes.

## 3. Releasing a Plumb platform version

Signed artifacts with SBOM; expand migrations first; deploy readers and writers; drain old workers; contract migrations in a later release; the verifier is released separately from the builder; the gateway has an emergency patch path requiring two operator approvals.

## 4. Releasing a customer intervention

The release machine (release.yaml) governs: VERIFIED → APPROVED (if required) → SHADOW (until AS-03 opportunities) → CANARY (5 clients, 25 opportunities per high-severity failure class) → ACTIVE. Rollout halts automatically on any high-severity scenario failure.

## 5. Daily operations

Check the collector health view; reconcile UNKNOWN effects older than one hour; review open dependencies past SLA; confirm outbox lag under 60 s; run the orphan detector; review the Market expiries due.

## 6. Checklists

Pre-activation: attestations current; approval bound; envelope active; shadow and canary gates recorded; kill-switch drill performed in the last 90 days. Post-activation: first ten cases audited; effect receipts verified; usage within budget.
