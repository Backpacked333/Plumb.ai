# Delivery plan

A thin complete vertical proof first, then progressive complexity inside the full loop. Dates are not readiness; each work package has an acceptance test and an effort range under the staffing assumption AS-06 (5 to 6 engineers plus a fractional domain expert).

## 1. Work packages

| WP | Deliverable | Owner skill | Depends on | Acceptance | Effort (engineer-weeks) | Risks |
| --- | --- | --- | --- | --- | --- | --- |
| WP-00 | Re-verify every external dependency claim against current primary documentation and the first customer's accounts; counsel review of §8 questions | Integration lead, counsel | none | Registry entries at documented level with access dates; legal gate recorded | 2 | Provider terms change |
| WP-01 | Trusted core: control service with guarded machines, PostgreSQL migrations under real roles, outbox, approvals with nonces, gateway, vault, audit | Distributed systems | WP-00 | AT-010, AT-050 to AT-056, AT-060 to AT-069 local; IG-008, IG-010 | 10 | Scope creep into Studio |
| WP-02 | Evidence and inventory: Gmail, Drive, QuickBooks ingestion through the connector runtime, protection classes, inventory probes, collector convergence, OCEL store | Data engineering | WP-01 | AT-083 to AT-087 local; IG-002, IG-003, IG-004 | 8 | QuickBooks CDC quirks |
| WP-03 | Engineering harness: sandboxes, leases, tool surface, rung-3 adapter generation for the Drive folder mapping, kit, labour recording | Agents and integration | WP-01, WP-02 | AT-053 to AT-057; IG-009 | 8 | Harness vendor changes |
| WP-04 | Workflow factory and runtime: compiler, Temporal runtime, effect ledger in PostgreSQL, Gmail send under policy, review surfaces (Gmail draft, companion) | Distributed systems, product | WP-01 to WP-03 | AT-020 to AT-044 local; IG-001 | 8 | Review-surface verification |
| WP-05 | Verifier: protected bundles, replay with knowledge boundary, shadow scoring, attestations, signing | Applied evaluation | WP-04 | AT-052, AT-091, AT-093 | 6 | Adjudicated truth availability |
| WP-06 | First-customer loop: inventory, evidenced opportunity, design, adapted integration, working collectors, generated workflow, checks, authorized deployment, new-case operation, recovery drill | All, domain expert | WP-01 to WP-05 | AT-098; the primary trace executed with real gates | 6 | Customer access lead time |
| WP-07 | Operations: monitors, kill switch, rollback, orphan cleanup, incident runbook drills, load test for AS-02 | Platform | WP-06 | AT-095; objectives measured | 4 | None |
| WP-08 | Learning branch: task definition, source search, dataset builder with leakage checks, training adapter, assist serving | Applied ML | WP-05 | AT-058, AT-092; IG-007 | 6 | Learnability |
| WP-09 | Replication on customers two and three with the benchmark | All | WP-06 | AT-097 | 6 | Selection bias |
| WP-10 | Higher-impact certified operation: QuickBooks attachable or posting under IC-012 | Integration, domain | WP-09 | AT-099 | 6 | Provider path validation |
| WP-11 | Studio completeness and sponsor view | Product | WP-04 | AT-100 | 6 | None |

Integration-access lead times (provider app review, OAuth verification, customer IT approvals) are tracked as dependencies on WP-00 and WP-06 and can exceed four weeks; domain-expert availability is a scheduled resource for WP-05, WP-06 and WP-10.

## 2. Sequencing

WP-00 → WP-01 → WP-02 and WP-03 in parallel → WP-04 → WP-05 → WP-06 (the thin complete loop) → WP-07 → WP-08 and WP-09 in parallel → WP-10 → WP-11 throughout. Nothing before WP-06 is a customer-facing milestone; capture tooling beyond the structured sources is EXP-01, not a work package.

## 3. Experiment register

| ID | Hypothesis | Setup | Data and access | Owner | Cap | Metric and denominator | Threshold | Default while unresolved | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EXP-01 | Richer observation adds deployable opportunities beyond structured records | Two discovery runs on the same firm: structured-only, then with enrolled desktop capture for two weeks | First customer; employee enrolment | Product | $3k, 4 weeks | Incremental accepted opportunities per firm; clarification questions per opportunity; implementation success; privacy objections; cost | ≥ 1 incremental deployable opportunity at ≤ 2x cost with no unresolved objection | Structured-only | Enrol capture by default or keep optional |
| EXP-02 | Inferred input and target joins are correct | 300 sampled joins audited by the accountant | QuickBooks backfill | ML | 20 expert hours | Join correctness per sampled pair | ≥ 95% | Prospective collector only | Enable historical labels |
| EXP-03 | Generated adapters are cheap and reliable enough | Five generated adapters across provider variants | Sandboxes | Integration | 3 weeks | Kit pass rate; repairs per adapter per quarter | ≥ 4 of 5 pass; ≤ 1 repair per quarter | Library adapters only | Expand rung 3 |
| EXP-04 | Semantic mapping is reliable | Folder and field mappings on three firms | Customer accounts | Data | 2 weeks | Mapping errors per 1,000 objects | ≤ 2 | Analyst review required | Remove review for low-risk mappings |
| EXP-05 | Fine-tuning earns a deployment advantage | Classical versus prompted versus fine-tuned on the categorization task | Dataset from WP-08 | ML | $1k | Accuracy at the abstention operating point and total cost per 1,000 decisions | Fine-tuned better on both | No training | Train |
| EXP-06 | Repair succeeds without humans | 30 induced faults (schema drift, cursor expiry, rate limits) | Staging | Agents | 2 weeks | Repairs completed within budget without intervention | ≥ 80% | Operator in the loop | Widen repair authority |
| EXP-07 | External reconciliation is safe | Fault injection on sends in the sandbox | Gmail sandbox | Distributed systems | 1 week | Duplicate sends per 1,000 faults | 0 | Not-retryable class default | Allow provider_keyed retries |
| EXP-08 | Clarification burden is acceptable | Count questions per opportunity across five firms | Customers | Product | 5 firms | Questions per accepted opportunity | ≤ 3 | Keep the cap | Adjust policy |
| EXP-09 | Maintenance cost is sustainable | Repairs and hours per deployment per quarter | Production | Platform | 2 quarters | Hours per deployment per quarter | ≤ 2 | Limit deployments | Scale |
| EXP-10 | Cross-customer reuse works without data reuse | Replication on customers two and three | Customers | All | WP-09 | Engineering minutes per deployment | Falling to < 240 | Analyst-assisted | Autonomous claim |

## 4. Reversible choices resolved now

Stack (ADR-011 to ADR-016), artifact model (ADR-017), authorization layers (ADR-018), protection classes (ADR-020), first-release predicate (ADR-021), execution architecture (ADR-022). Empirical uncertainties stay as the gates above.
