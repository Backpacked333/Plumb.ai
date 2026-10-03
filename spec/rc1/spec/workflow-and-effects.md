# Business runtime, obligations, coordination and the external action protocol

A WorkflowSpec defines case semantics; Temporal executes; PostgreSQL decides; every external effect goes through the effect ledger with a semantic slot, a lease, a verified receipt and an explicit UNKNOWN.

## 1. WorkflowSpec semantics

Case identity is the tuple of case_key_fields plus the obligation epoch; triggers create a case or route an event to an existing one (a second trigger for the same key and epoch is an event, never a second case). Inputs are typed ports with freshness requirements; a stale required source blocks the transition that needs it. States, transitions with guards and actions, durable waits, timers, joins and bounded loops are declared; terminal states have no outgoing transitions (schema-enforced). Completion is a named predicate evaluated on confirmed facts and confirmed effects. Human review is a state (WAITING_REVIEW) with a review item bound to the case version.

## 2. Case lifecycle (case.yaml)

CREATED → ACTIVE → WAITING_EXTERNAL or WAITING_REVIEW → ACTIVE → COMPLETED, FAILED or CANCELLED; COMPLETED → REOPENED (epoch + 1) → ACTIVE. A case pins its release; a release change does not alter an in-flight case unless a validated migration moves it. Overlapping periods are separate cases; late evidence for a completed case reopens it; retroactive changes to a source record raise evidence_changed, which invalidates open review items and recomputes.

## 3. Coordination at shared boundaries (SR-092)

Obligations have one owner workflow per epoch (unique index); a second workflow touching the same obligation attaches to the same case. Contact suppression and per-recipient budgets apply across channels through the gateway; two different messages to the same recipient about the same obligation epoch are a conflict, not a deduplication miss. Precedence between interventions is declared in the pack (reminders yield to an open partner escalation).

## 4. Humans changing records outside Plumb

Observed through collectors (version changes), conditionally updated where the provider supports it (QuickBooks SyncToken, Drive revisions), version-checked before dispatch (expected_state_versions); where no concurrency guarantee exists the permitted impact is lowered or review is required. Races the provider cannot eliminate are reported, not hidden.

## 5. Deterministic rules and degraded modes

Rules that encode established business constraints are compiled decision tables; a model may propose a rule or a decision, enforcement uses the approved representation. Before dispatch the runtime validates outputs, schemas, account scope, current state and authority. Degraded modes preserve the promised boundary: awaiting approval stays awaiting approval; a draft is not a sent message; provider acceptance is not delivery; a prepared package is not a closed ledger.

## 6. External action protocol (SR-080 to SR-092)

Objects: ActionIntent (slot, logical id, payload digest, epoch, target, expected versions, authority, reservation, retry and compensation class) and EffectRecord (attempts with lease and fencing token, receipts, postconditions, reconciliation, compensation link). Transition table: contracts/state-machines/effect.yaml. Reference: reference/effect-protocol-harness/ledger.py.

Transaction boundaries:

| Step | In the transaction | Outside |
| --- | --- | --- |
| Reserve | Intent row, effect row (RESERVED), reservation, outbox row, audit | nothing |
| Claim | Outbox CAS, lease insert with fencing token, attempt row, effect CAS to DISPATCHING, authority re-check | nothing |
| Dispatch | nothing | the provider call with the idempotency key |
| Acknowledge | Receipt insert (verified), attempt result, effect CAS to DISPATCHED or UNKNOWN or RESERVED under the fencing token | nothing |
| Postcondition | Effect CAS to CONFIRMED and reservation settle, or to UNKNOWN | the provider read |
| Reconcile | Reconciliation result and effect CAS | the provider lookup |
| Finalize | Reservation release or settle, usage record, outbox event | nothing |

Retry classes: natural_idempotent (a GET-like or set-to-value operation), provider_keyed (idempotency key honoured within a window; retries forbidden after the window), reconcilable (an external lookup can establish occurrence), not_retryable_after_ambiguity (no lookup can establish non-occurrence; UNKNOWN routes to NEEDS_HUMAN). Deduplication survives agent restarts, new workflow runs, release changes and retries because the slot index lives in the database. A changed body is a PAYLOAD_CONFLICT; a new reminder is a new obligation epoch; compensation is a new effect in its own slot and never deletes the original.

Guarded table highlights: UNKNOWN is never treated as FAILED; CANCEL_REQUESTED keeps a provider completion; revocation cancels RESERVED, cancel-requests DISPATCHING and retains everything later. What Plumb guarantees: at most one live effect per slot, no dispatch without current authority, no CONFIRMED without a verified receipt or read-back, no retry after ambiguity without reconciliation. What depends on the provider: idempotency windows, lookup authority, cancellation after acceptance.

Required tests (executed locally against the mock provider; production versions in acceptance/production-catalog.md): concurrent dispatchers and stale workers, provider eventual consistency, forged receipt, duplicate webhooks, changed payloads, provider outage, idempotency-window expiry, crash immediately after acceptance (AT-030 to AT-044).

## 7. PostgreSQL and Temporal handoff (IC-015)

Temporal activities call the control service with aggregate versions and idempotency keys; the control service commits transitions and outbox rows in one transaction; the workflow history stores returned versions only. Outbox dispatch is a separate consumer; if it is down, events queue (nothing is lost); if Temporal is down, no activity runs (nothing is dispatched); on recovery stale activity attempts are rejected by compare-and-set.

## 8. Omissions

Multi-case sagas spanning two tenants (a sponsor acting across firms) are not supported.
