# End-to-end traces

All identifiers are synthetic and match the fixtures. Steps that depend on real access are marked "integration gate", never given an invented receipt.

## 1. Primary trace: accounting evidence collection and review preparation (fixtures/accounting)

1. Authority: tenant tnt_barlowkim; owner prn_owner_01; grants grant_gmail_ops (discovery, implementation, operation), grant_qbo_main (plus evaluation, training), grant_drive_docs; envelope env_barlowkim_v3 (version 3; destinations mailbox:client_contacts and provider:quickbooks:realm_4011; effect classes include external_message but not external_record_write; auto-impact ceiling low; build cap $2,500; single action cap $5). Labour: customer_authorization 25 minutes.
2. Inventory inv_barlowkim_2026_09: Gmail threads and drafts account_verified; send sandbox_tested; Drive list account_verified; changes.watch sandbox_tested; QuickBooks query and CDC account_verified; webhooks sandbox_tested; attachable.create documented only; bank-feed For review recorded as not exposed.
3. Evidence: 12 months of mail threads and QuickBooks postings backfilled under discovery purpose; Drive folder listing shows a non-standard layout (client folders named by nickname and year). Coverage 0.83 for the request population.
4. Opportunity opp_doc_chase_01 (route friction): duplicate requests per obligation 0.31 (n = 412). Clarifications: checklist owner (answered: the engagement letter per client), whether partner re-sends are intentional (answered: sometimes; partner escalations are excluded from suppression), reminder cadence (7 days, max 3). Owner accepts the objective. Labour: domain_clarification 20 minutes.
5. Solution sol_doc_intake_v1: three candidates; cand_rules_plus_drafts selected; impact low; outcome review_package_accepted; no implement approval required (within ceiling).
6. Coverage decision: agent_adaptation (the Drive folder mapping) with exact_template for the rest.
7. Build plan_barlowkim_doc_intake_v1 validates with no errors (18 steps, $600). Execution: probes verify Gmail and QuickBooks; step_adapter_drive_folder_map generates an adapter that maps nickname-and-year folders to client and period using the engagement list and ledger names, with contract fixtures from sampled listings; step_test_adapter passes the kit; the analyst reviews the mapping diff (read scope only, no write) — labour engineering_intervention 0, business_review 15 minutes; collectors col_docs_v1 (Drive changes) and col_qbo_v1 (CDC every 20 days plus webhooks) deploy in SHADOW, backfill, reconcile counts within 0.5%, and each is activated only after a real new document and a real new posting flow through (integration gates IG-002, IG-003, IG-004). Dataset ds_categorization is built for the learning variant and parked. Workflow wf_barlowkim_doc_intake_v1 compiles (13 states, one action act_send_request with per-recipient budget 3). Protected scenarios run: wrong client, ambiguous period, already-received document, corrected statement, duplicate request, expired permission, provider timeout after send, changed approval, stale source. Infra preview and apply for the collector subscriptions and storage. Release rel_doc_intake_v1 composes eight digests; six checks attest.
8. Approval and release: activation does not require a release approval (impact low); the owner is shown the build card anyway and the fixture carries apr_release_doc_intake_v1 to show the binding. Shadow for 40 opportunities, canary on 5 clients, then ACTIVE.
9. Operation: on 2026-10-01 cases open per client and period; for Pine Street Bakery the reconciled evidence shows the August statement missing; a consolidated request is drafted; the standing policy allows auto-send after 30 days of reviewed drafts, so the first month routes to AWAIT_SEND_REVIEW; Nina approves in Gmail; the send is an ActionIntent int_send_req_0142_2026_08 with slot tnt_barlowkim|case_0142_2026_08|1|gmail.messages.send|contact_maria; the effect ledger records RESERVED → DISPATCHING → DISPATCHED → CONFIRMED with the Gmail message id (integration gate IG-001; the local harness shows the same transitions against the mock provider). The case waits durably; the statement arrives; validation matches client and period; the package is prepared; the accountant accepts it in the companion surface; case COMPLETED; billable unit unit_0142_2026_08_review_package_accepted.
10. Recovery event: a Gmail timeout after acceptance on another case produces UNKNOWN; reconciliation by the idempotency key finds the message; CONFIRMED without a second send.
11. Outcome: after two periods, duplicate requests per obligation measured prospectively by cohort; review minutes per case recorded; the monthly report shows projection, measurement and invoice side by side.
12. Labour accounting for this trace: customer_authorization 25, domain_clarification 20, business_review 15 plus per-case review, engineering_intervention 0, operational_repair 0, platform_engineering recorded separately for any primitive added.

Nontrivial adaptation: the Drive folder mapping adapter is generated, tested and reviewed, not selected from a template; the agent infers the mapping from engagement names and ledger customers, verifies it on sampled listings and has authority to deploy it because the envelope covers Drive read scope and storage:tenant destinations.

## 2. No-training variant

Identical to §1 with step_discover_labels, step_build_dataset and step_experiment removed from the plan; the release delivers the same predicate. This variant proves the product is an implementation engine.

## 3. Learning-enabled variant

Adds the task definition tsk_categorization_v1 (input: bank line description, amount, payee, prior categorizations known at decision time; target: account; deployment assist). The planner locates 36 months of postings (historical_decision authority), joins by transaction id and document link, quarantines 1,800 ambiguous joins (illustrative), builds ds_categorization with temporal and family-disjoint splits, audits a sample with the accountant, evaluates a classical model and a prompted model, and submits a provider fine-tuning job only if the trained candidate wins on measured performance and total cost (integration gate IG-007). The serving path is assist-only until IC-012 certifies a posting operation; the categorization suggestion appears in the review package.

## 4. Additional traces

| Trace | Stimulus | Expected path |
| --- | --- | --- |
| Insufficient data | Fewer than a usable number of consistent labels for the task | Non-trained baseline plus prospective collector; reported as an implemented learning path |
| Missing grant resolved later | Drive grant absent at build start | AT-057 |
| Provider timeout after acceptance | Gmail send times out | UNKNOWN → reconcile → CONFIRMED; no second send |
| External record change after approval | Client contact changed in the ledger after a draft was approved | expected_state_versions mismatch → STATE_CONFLICT → new review item |
| Schema drift and repair | Drive adds a field and renames parents | Collector DEGRADED → mapping repair with a new transformation version → kit → ACTIVE |
| Cancellation and cleanup | Owner cancels a build mid-way | Uncertain effects reconciled; reservations released; sandbox and subscriptions cleaned |
| Source-rights removal | Client withdraws Drive consent | Removal state machine; collector paused; datasets UNAVAILABLE; adapter retrained without the client |
| New capability unlocking an opportunity | Plaid Statements verified for a client's bank | Route new_capability → obligation bank_statement_received becomes fetchable → new build within envelope |

## 5. RFQ and routing traces (same engine, different packs)

RFQ (fixtures/industrial-rfq): inventory verifies NetSuite item search and pricing and Microsoft 365 mail; the adapter normalizes units and SKU; the workflow parses, normalizes, prices with a 24-hour freshness guard, drafts and waits for commercial approval; completion quote_draft_approved; no binding quote is sent by software. Routing (fixtures/laundry-routing): orders and trips collected; solver configured with hard constraints; plan drafted; publication requires approval; completion routes_published; physical execution stays human. Both plans validate locally; neither has been executed.

## 6. Fresh-customer replication trace

A second firm with year-first folder names, client ids embedded in file names, a different chart, a 10-day reminder cadence and 18 months of history. The same factories run; the adapter is regenerated (not re-used by replacing tenant ids), the checklist is clarified in two questions, the acceptance set is rebuilt from the firm's own adjudicated cases. Every manual intervention is counted and reported in the benchmark.
