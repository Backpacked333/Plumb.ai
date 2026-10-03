# Autonomy benchmark

Implementation autonomy is measured over all eligible attempted deployments, with eligibility frozen before the outcome is known, every human action counted by category and three generalization levels reported separately. A platform with good runtime automation and high per-customer manual implementation does not meet the central claim.

## 1. Eligibility

An attempt is eligible when: a CoverageDecision exists before execution; the tenant's envelope was active; the inventory recorded the required operations at account_verified or the gap was declared. Eligibility is never revised after the outcome. Blocked, failed, abandoned and partially manual attempts remain in the denominator.

## 2. Measures per attempt

| Measure | Definition | Source |
| --- | --- | --- |
| Discovery acceptance | Owner accepted the objective of a Plumb-generated opportunity | opportunities |
| Correct problem formulation | The accepted objective matched the measured bottleneck after outcome measurement | outcome observations |
| Source and capability verification | Required operations reached account_verified without engineer intervention | capabilities, labor |
| Integration construction | Integrations reached certified operation (rung and labour recorded) | integrations, labor |
| Collector construction | Collectors reached ACTIVE with live-event attestation | collectors, attestations |
| Dataset validity | Dataset VERIFIED with leakage checks and label audit | datasets |
| Workflow completion | Release VERIFIED; cases complete their predicate | releases, cases |
| Release success | ACTIVE without rollback within 30 days | releases |
| Recovery success | A defined fault (lease loss, timeout after acceptance, schema change) handled without engineer intervention | effects, diagnostics, labor |
| Prospective outcome | Outcome observations reach the measurement plan's threshold | outcome observations |
| Elapsed time | Envelope active to release ACTIVE | timestamps |
| Provider cost | Usage ledger for the build and first 30 days | usage |
| Human work by category | Minutes per LaborCategory | labor |

## 3. Reporting

| Level | Attempts | Verified deployments | Median engineering minutes | Attempts with zero engineering minutes | Recovery success | Outcome met |
| --- | --- | --- | --- | --- | --- | --- |
| Repeat of a certified template | | | | | | |
| New composition of known capabilities | | | | | | |
| Agent-built adaptation or new capability | | | | | | |

The table is filled only from recorded attempts; no projected rows.

## 4. Replication benchmark

Run on the second and third customers with varied folder structures, identifiers, chart conventions, reminder policies, data quality and accessible history; core acceptance logic is independent from the builder; customers are not selected for cleanliness. Target (AS-05, proposed): median engineering minutes below 240 by the third customer with stable quality and outcome.

## 5. The decisive benchmark

Given authorized accounts and broad priorities and no engineer-authored customer workflow, Plumb identifies a supported opportunity, constructs and verifies the solution, obtains only necessary authority and domain input, operates on new cases and recovers from a defined fault. Every human action, unsuccessful attempt and material limitation is counted and published with the result.
