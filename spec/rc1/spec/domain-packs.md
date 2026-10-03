# Domain packs and first-release scope

The accounting pack is specified at the level of business objects and allowed operations. RFQ and routing packs are specified as contracts that reuse the engine, not as supported releases.

## 1. Accounting pack objects

| Object | Definition | Authority |
| --- | --- | --- |
| Client | The firm's client entity with external ids in the ledger and mail | Ledger for identity; owner for engagement |
| Engagement | Services and the authoritative checklist (who may change it: the engagement owner) | Owner |
| Period | Fiscal month per client | Calendar |
| Obligation | A checklist item for a client and period with a fulfillment predicate | Pack rules plus checklist |
| Document | Statement, receipt, payroll report, invoice; identified by approved semantic identity (client, period, type), not by name and week | Drive, mail attachments |
| Transaction | Posted ledger entry | Ledger (authoritative) |
| Request | A consolidated missing-item message under the reminder policy | Workflow |
| Review package | The assembled evidence with a digest | Workflow |
| Posting proposal | A suggested categorization or entry (not delivered in release 1) | Workflow (later) |
| Approval | Accountant sign-off bound to the package digest | Domain approver |
| Completion | review_package_accepted | Predicate |

## 2. Document collection and review preparation rules

Already-present documents are never requested; wrong client or period (semantic identity mismatch) is flagged for review; duplicates are deduplicated by content digest and identity; amendments supersede with the amended flag; partial uploads keep the obligation partially satisfied; unsupported banks fall back to a request; inaccessible sources raise a dependency; existing reminder history (including human sends) counts against the per-recipient budget; requests are consolidated per client and period; freshness windows apply before packaging; sign-off binds the package digest.

## 3. First-release intervention

Resolve client and period; reconcile existing evidence across Drive, mail and the ledger; consolidate missing items; draft a consolidated request; send under the standing reminder policy or after review; wait durably; validate arrivals; prepare the package; obtain sign-off. This is enough native and low-impact action (one external message class) to test the product rather than a collection of drafts.

## 4. Accounting write contract (IC-012, SR-121)

Before any posting operation is certified: transaction semantics documented per provider path; expert-approved validation rules; test coverage for transfers, refunds, pending-to-posted changes, existing entries, split records, multicurrency, changed charts of accounts, locked periods and reconciliation state; the native-match workaround (post then let the feed match) validated for the specific provider, bank and business path before enablement; every write behind a case approval with a certified undo or compensation; integration gates IG-003 and IG-005 passed.

## 5. Industrial RFQ pack (representational test)

Objects: RFQ, line, SKU, unit of measure, price list with freshness, customer, quote draft, commercial approval. Contract: unit and SKU normalization (cases versus eaches) with explicit conversion factors; price freshness within 24 hours; commercial authority (who may approve terms) before any binding quote; physical fulfillment and credit decisions remain outside software's action capability. Fixture: fixtures/industrial-rfq.

## 6. Laundry routing pack (representational test)

Objects: order, stop, vehicle, driver shift, depot, route plan. Contract: hard constraints (capacity, time windows, shifts) configured in the solver; changing orders re-solve within a bounded loop; publication authority before routes reach drivers; physical execution and exceptions remain human. Fixture: fixtures/laundry-routing.

## 7. Omissions

Tax notice triage and payroll questions (Source A's processes) are not specified in release 1.
