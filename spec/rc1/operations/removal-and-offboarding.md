# Removal and offboarding

## 1. Removal state machine

contracts/state-machines/removal.yaml; guards in spec/privacy-and-security.md §5. Requests come from the tenant owner, a client grantor (for their own data) or an employee (for their capture data); identity and scope are validated before anything stops.

## 2. What is removed, what is retained

| Category | Action |
| --- | --- |
| Source rows (evidence events, documents) | Tombstoned; content refs deleted from object storage |
| Derived rows (facts, links, dataset rows, retrieval entries, caches) | Tombstoned by cascade |
| Datasets containing affected rows | Marked UNAVAILABLE with a lawful tombstone manifest (counts and lineage, no content) |
| Models trained on affected rows | Retired or retrained without the rows; no unlearning claim |
| Provider-side copies (processors) | Deletion requests recorded and confirmed or timed out with record |
| Backups | Expire within the 35-day rotation (AS-07); restores during that window re-apply tombstones before any access |
| Audit | Minimal lawful audit retained (ids, actor, reason, timestamps) |
| Legal hold | ON_HOLD only through authorized review with reason |

## 3. Offboarding a tenant

Removal request with scope tenant; OAuth tokens revoked and Plumb's app connections removed; subscriptions deleted; cloud resources destroyed; integration definitions and the OCEL export handed to the customer on request; billing closed with final billable units; the sponsor's aggregates retained only as aggregates.

## 4. Completion evidence

A signed completion record listing categories handled, provider confirmations, backup expiry dates and retained audit scope.
