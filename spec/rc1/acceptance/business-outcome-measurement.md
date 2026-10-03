# Business outcome measurement

Outcome claims come only from prospective measurement; technical success and billing are separate. Simulated removal of waiting time is never evidence of a client's response.

## 1. Metrics for the accounting pack

| Metric | Definition | Denominator | Design |
| --- | --- | --- | --- |
| Duplicate requests per obligation | Requests for the same obligation epoch from any sender | Obligations closed in the period | Cohort by client; pre-period baseline from backfill |
| Review minutes per case | Reviewer time on review items plus package sign-off | Completed cases | Direct measurement from review items with self-reported minutes |
| Days to package accepted | From period start to review_package_accepted | Completed cases | Cohort; seasonality controlled by comparing the same month in the prior year |
| Rework | Packages returned after sign-off | Accepted packages | Direct |
| Escalations | Cases reaching ESCALATED | Cases | Direct |

## 2. Designs

Staged rollout (canary clients versus the rest) gives a within-period comparison; where the whole firm is live, pre and post comparison with the prior year's same months controls seasonality; case mix (client size, document count) is recorded as a covariate; policy changes (checklist edits, reminder cadence) are recorded as policy eras and analysed separately.

## 3. Attribution limits

Reported with every observation: cohort size, missing covariates, policy changes during the window, external events (a client's own bank change), and whether the design supports a causal statement. Financial realization (cash saved, revenue gained) is reported only when the owner supplies the realization (a hire not made, capacity sold).

## 4. Reconciliation of projection, measurement and invoice (PR-020)

Projection: OpportunitySpec expected_benefit range. Measurement: OutcomeObservations with method and limitations. Invoice: BillableUnitRecords. The monthly report shows all three side by side with their definitions; a credit is issued when the measured cycle time is worse than baseline for a full period (proposal from Source A, adopted as a mechanic).
