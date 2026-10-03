# Integration construction, configuration management and collection apparatus

Connectors are constructed up the ladder and trusted only per certified operation; collectors are generated apparatus that must converge, report their health and be verified by a real permitted event.

## 1. Connector ladder (construction order, SR-061)

| Rung | Method | Credentials and policy | Trust |
| --- | --- | --- | --- |
| 1 | Library adapter (Plumb-certified code) | Integration admin for setup; runtime credentials per operation | Certified operations only |
| 2 | Platform catalog (self-hosted Nango) with per-user auth | Nango management for setup; runtime via Plumb gateway | Certified operations only |
| 3 | Generated adapter from documentation and recorded shapes | Sandbox only until kit passes and an analyst reviews write scopes | Read after kit; write after review and probe |
| 4 | UI adapter (browser agent over observed paths) | Session owned by the integration manager; never bypasses MFA or licensing | Read-only unless the write operation is separately certified |
| 5 | Person | n/a | Measured like any step |

## 2. Credential classes (SR-062)

Source ingestion (read tokens), runtime actions (write tokens per operation), integration administration (OAuth app, subscriptions), SaaS configuration (admin settings) and infrastructure management (cloud) are separate vault namespaces with separate roles; no single principal holds more than one class for a tenant.

## 3. Connection model (SR-063)

ConnectionIntent (who asked, for which purpose) → Grantor (verified identity) → Tenant and client entity → Provider account (account_ref from provider identity, never a display name) → Workspace or realm → App registration → Scopes and entitlement → Auth status and token lifecycle (refresh, rotation, expiry) → Capabilities → Health → Revocation. Reconnect keeps the same connection id when the provider identity matches; a different identity is a substitution requiring the grantor's confirmation; duplicate connections to the same account merge; shared mailboxes and service accounts are connections owned by the tenant owner; a departed user's connection is paused at deprovisioning and the dependent workflows raise a dependency.

## 4. Generated adapters (SR-064)

Inputs: permitted documentation (fetched through the allow-list), schema samples from the authorized account, recorded fixtures where the grant permits, the operation contract (semantic ports), semantic mapping proposals, known errors. Outputs: typed client, credential references, contract tests, capability manifest, retry and reconciliation rules, version, deployment artifact. Verification: the kit (IC-010) plus a probe on the correct account; a successful HTTP 200 on another account or on a different operation proves nothing.

## 5. UI adapters (SR-065)

Supported surfaces are enumerated per provider; semantic selectors with assertions; one session owned by the integration manager; permission-respecting operation (the adapter never escalates); confirmation behaviour mirrors the provider's dialogs; evidence retention is a masked screenshot per action; layout drift disables the adapter and raises a dependency; rate limits at human speed; uncertain writes follow the effect protocol (UNKNOWN until read-back). A screenshot is not proof of final business state: the postcondition is read through an API or a second navigation.

## 6. First-release operations (IC-003)

| Operation | Interface | Fields | Auth | Pagination and limits | Update mechanism | History | Errors | Sandbox differences | Probe | Verification status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| google_workspace:gmail.threads.list | Gmail API threads.list and get | thread id, message ids, headers, labels, body | OAuth, readonly scope | page tokens, quota units per call | history.list for incremental | Full mailbox history per grant | 403 quota, 401 token | none material | list one thread on the account | documented; IG-001 |
| google_workspace:gmail.drafts.create | drafts.create | message raw, thread id | OAuth, compose scope | n/a | n/a | n/a | 400 malformed | none | create and delete a draft | documented; IG-001 |
| google_workspace:gmail.messages.send | messages.send | raw message, thread id | OAuth, send scope limited by Plumb to template classes | n/a | n/a | n/a | 400, 429 | none | send to a tenant-owned test address | documented; IG-001 |
| google_drive:files.list, changes.watch | files.list, changes.list, changes.watch | file id, name, parents, modifiedTime, md5 | OAuth, readonly | page tokens, change tokens | changes.list with a start page token; watch channel renewals | Full | 404 channel, 401 | none | watch a test folder | documented; IG-002 |
| quickbooks_online:query.Purchase | Query API | Id, SyncToken, TxnDate, TotalAmt, AccountRef, EntityRef, MetaData | OAuth 2 with realm | 1,000 rows per query page | change data capture | Full history of posted entities | 401 token, 429 throttle | sandbox companies differ in data | query one entity | documented; IG-003 |
| quickbooks_online:cdc | CDC endpoint | changed entities since timestamp | OAuth 2 | 1,000 objects per response; 30-day look-back | poll every ≤ 20 days per entity set; webhooks for live | 30 days | same | same | CDC on a 1-day window | documented (Intuit docs); IG-003 |
| quickbooks_online:webhooks | Webhook subscription with HMAC verification | entity, id, operation, lastUpdated | app-level | n/a | push then fetch | n/a | signature failure | n/a | receive one event | documented; IG-004 |
| quickbooks_online bank-feed For review lines | not exposed by the public API | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | unsupported; never inferred from read access |
| plaid:statements | statements/list, statements/download, statements/refresh | statement id, account, period, PDF | Link consent per client | per account | STATEMENTS_REFRESH_COMPLETE webhook | up to 2 years, US depository, limited institutions | institution unsupported | sandbox returns a mock statement | list on a sandbox item | documented (Plaid docs); IG-005 |

Observable time axes per source: Gmail provides message internalDate (event_time) and history ids (available_time approximated by ingestion); Drive provides modifiedTime (source_recorded_time) and change tokens; QuickBooks provides TxnDate (event_time) and MetaData.LastUpdatedTime (source_recorded_time); available_time for CDC is the poll time at which the change first appeared.

## 7. Configuration as artifacts (SR-066)

A SaaS or integration configuration change records before and after state, exact resources, expected effects, authority, drift detection rule and reversal limits. At offboarding: OAuth apps are Plumb's and are revoked for the tenant; subscriptions are deleted; cloud resources tagged to the tenant are destroyed after the removal state machine; integration definitions are exported to the customer on request.

## 8. CollectionSpec and convergence (SR-067, SR-068, DC-010 to DC-016)

Watermark strategies: Gmail history ids; Drive change tokens; QuickBooks CDC polled at ≤ 20 days with a 2-hour overlap; Plaid webhooks plus daily list. Duplicates, late, reordered, deleted, corrected and tied-timestamp records are handled by version dedup, tombstones and overlap (reference/collector-convergence). Recovery: expired cursor → full resync; missed webhook → overlap poll catches it; partial sync → the watermark did not advance, so the next poll repeats; changed source schema → quarantine and a mapping repair; revoked permission → PAUSED and a dependency. Completeness is provable (CDC within look-back), bounded (overlap polling) or sampled (UI adapters). Downstream components block, degrade or go read-only on stale required inputs as declared in the WorkflowSpec source_freshness.

## 9. Deployment protocol

Profile source → generate code and configuration → provision storage → SHADOW capture to quarantine → BACKFILLING from the agreed watermark → RECONCILING counts and sampled identities → verify one actual permitted new event end to end (attestation chk_collector_live_event) → ACTIVE. A zero-error log or a successful scheduled job is not evidence (SR-069). The generated apparatus includes source adapters, schedules or subscriptions, transformation code, schema management, quality jobs, lineage emission, monitoring, retention and deletion handling.

## 10. Prospective decision journal

At every decision boundary the runtime records permitted input and context references, case and object versions, proposed action, actor or model and release identity, review state, correction and later outcome. Label provenance is explicit (LabelAuthority); a model-generated decision is never journaled as a human decision.

## 11. Omissions

Database CDC (Debezium-class) for customer-owned databases is specified by reference to Source B §11 and deferred; no first-release customer system is a database.
