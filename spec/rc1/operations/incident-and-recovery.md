# Incident response and disaster recovery

## 1. Detection and classification

Alerts from monitors (connector freshness, schema change, execution failure, quality drift, review burden, cost, outcome). Classify the failed contract first: access (expired or revoked), schema (drift), data quality (quarantine growth), business rule (correction rate on one class), model behaviour (drift on a slice), infrastructure (latency, errors). A model-quality problem is distinguished from source staleness and from a mapping drift by the collector health rows and the diagnostic category.

## 2. Impact assessment

Identify the exact cases, clients, releases, datasets and external effects affected (correlation ids). Report per case; global uptime never substitutes.

## 3. Containment

Pause the affected release (kill switch: new dispatch stops within 60 s; in-flight listed within 5 minutes); tighten valves one notch; keep unaffected releases running; never widen authority or weaken acceptance to contain.

## 4. Notification

Customer notice within 72 hours for incidents touching their data or effects; the notice lists affected cases and the remediation plan; sponsors receive aggregates only.

## 5. Corrective work and reactivation

A repair is a new release through the normal gates; domain review for any business-rule change; reactivation only after the acceptance set is refreshed if repair exposed rows.

## 6. Backup and restore

PostgreSQL continuous archiving with point-in-time recovery; object storage versioning; proposed RPO 5 minutes, RTO 4 hours (AS-02 companion). Restore procedure: restore internal state; keep dispatch disabled; reconcile effects against provider state for the gap window (every effect in RESERVED, DISPATCHING, DISPATCHED or UNKNOWN is looked up by idempotency key); reconcile cases against receipts; only then re-enable dispatch. A consistent backup can still be unsafe to resume against the external world, so dispatch stays off until reconciliation completes. Drills quarterly.

## 7. Resource cleanup

Sandboxes, subscriptions, cloud resources, training jobs and serving endpoints carry build and tenant tags; the orphan detector runs daily; providers that cannot stop charges immediately are recorded with the expected final charge.
