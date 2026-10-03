# Evidence, business knowledge and temporal truth

Evidence is source-first; observation fills gaps and earns its scope. Every evidence event carries five time axes, a protection report and lineage; facts carry status and source-of-record precedence; obligations have a lifecycle; entity corrections are scoped and reversible.

## 1. When each evidence source is appropriate

| Source | Use when | Not sufficient for |
| --- | --- | --- |
| APIs and event logs | The system of record exposes history and changes (QuickBooks, Drive, mail) | Off-system handoffs, decisions made in spreadsheets, physical context |
| Documents | Checklists, engagement letters, policies, templates | Timing of work |
| Short interviews | Authoritative owner of a checklist, whether a repeated reminder is intentional, who approves | Statistics |
| Desktop and browser signals | Inventory shows gaps (undocumented tools, re-keying, manual transfers) or EXP-01 shows incremental value | Proof that work did not happen |
| Field evidence (later) | Physical constraints | Release 1 |

## 2. Desktop and browser capture contract

| Item | Specification |
| --- | --- |
| Supported OS | macOS 14 and later; Windows 11; Chromium-based browsers for the extension |
| Permissions | macOS Accessibility and Screen Recording; Windows UI Automation; the installer explains each before the OS prompt |
| User-visible state | Menu-bar or tray indicator (recording, paused, excluded app); the same state is visible in Studio My week |
| Exclusions | Default deny lists: personal email, banking, password managers, health, messaging, HR portals; worker-editable allow and deny lists by app and domain; private browser windows are never captured |
| Private sessions | Any window classified personal is dropped on device before any processing |
| Local queue | Encrypted SQLite (per-device key in the OS keychain); envelopes only; frames deleted within 60 s of labeling |
| Offline | Capture continues to the local queue up to 72 hours of envelopes; sync resumes with ordered delivery |
| Duplicate suppression | Perceptual-hash change detection; envelope ids are deterministic from device, timestamp and content digest |
| Device identity | Per-device certificate issued at enrolment; revocation invalidates sync and triggers remote wipe of the queue |
| Upgrades | Signed packages; a failed upgrade keeps capture paused, never silently degraded |
| Revocation and deletion | Worker or admin revocation stops capture within one sync cycle; worker deletion of an envelope tombstones it everywhere (DC-021) |
| Resource envelope (proposed targets on reference hardware: M2 MacBook Air 16 GB; Windows i5 16 GB) | ≤ 8% average CPU, ≤ 600 MB resident, ≤ 3% battery per hour, ≤ 200 KB per day upstream, ≤ 2 GB local disk; local models must run on-device; if not, labeling defers to a cloud path only for the accessibility and DOM modalities, never frames |

## 3. Raw-to-derived pipeline per modality

| Modality | Raw stays | Derived | Policy on correction after raw deletion |
| --- | --- | --- | --- |
| Screen frames | Device only, deleted in 60 s | Envelope with action, mentions, masked text | Relabeling re-derives only from the envelope; where the envelope lacks the needed detail the fact is marked unrecoverable, never silently restored |
| Accessibility and DOM | Device only | Structured elements, field names, URL host | Same as frames |
| Message bodies | Cloud, under grant, protection classes applied | Thread facts, request outcomes | Re-derivable while the body is retained |
| Document attachments | Cloud, under grant | Extraction with field confidence | Re-derivable while retained |
| Externally hosted recordings | Provider-hosted; transcript ingested under grant with the recording notice verified | Transcript facts | Re-derivable while the provider retains it |
| Runtime proof artifacts | Cloud, masked screenshots for UI adapters | Effect evidence | Retained with the effect |

## 4. Protection classes (DC-005, DC-006)

| Class | Applied to | Behaviour |
| --- | --- | --- |
| OMIT | Government ids, card numbers, bank account numbers outside an authorized posting path, passwords | Never stored; the protection report records that a value was omitted |
| TOKENIZE | Person names in free text, free-text identifiers | Deterministic per-tenant pseudonym; the token map is in the protected source-reference store |
| PROTECTED_REFERENCE | Recipient addresses, client contact details, provider account identifiers, document ids | Stored encrypted; resolvable only by the credentialed execution path at dispatch (so a masked address can still be sent to) |
| CLEAR | Amounts, dates, periods, categories, statuses, object identifiers inside the tenant | Business semantics preserved |

## 5. Coverage and work spans (SR-025, SR-026)

Coverage is a matrix: employee × role × application × workflow × interval × object population, each cell complete, bounded, sampled or unknown. A paused agent, an unavailable source, an empty page or a stale connector sets cells to unknown and lowers the confidence of any opportunity that depends on them. Work spans are segmented into dwell, observed interaction, hands-on work (interaction density above the baseline), asynchronous wait, interruption, concurrent task (overlapping spans are split by focus), and unobserved. Censoring (a span cut by the observation window) and sample bias (which employees enrolled) are reported with every timing claim; window durations are never summed into recoverable labour.

## 6. Ontology: stable core, domain extensions, tenant mappings

Core types: Party, Person, System, Document, Obligation, Case, Request, Transaction, Deadline, Engagement. The accounting pack extends them (Client, Period, Close, Statement, ReviewPackage). Tenant mappings bind external ids and aliases to objects. Derived facts are versioned by derivation_version. The event and link tables keep the OCEL 2.0 shape and export OCEL JSON (DC-008); obligations, policies and action state live in their own tables.

## 7. Source-of-record precedence and fact status

Per predicate the pack names the authoritative source (ledger balances from QuickBooks; document presence from Drive plus mail attachments; request history from mail). Status moves observed → inferred → confirmed by a human, disputed by a conflicting source, stale when past validity, superseded by a newer fact. A high-confidence inference never overrides a confirmed or external record; a correction creates a new fact and supersedes the old one with a scoped impact set.

## 8. Obligations

Created from the engagement checklist and period calendar (recurrence); exempt by a domain approver with reason; partially satisfied when some evidence items are present; satisfied when the fulfillment predicate holds on confirmed facts; expired when past due without exemption; reopened (epoch + 1) on a retroactive change or late evidence; superseded when the engagement or rule version changes. The epoch is part of every effect slot, so a reopened obligation permits a new request without colliding with the old one.

## 9. Temporal truth

event_time (when it happened), valid_from and valid_to (when the fact holds), source_recorded_time (when the source wrote it), available_time (when the source could first serve it), ingested_time (when Plumb received it). Per source the observable subset is documented in spec/integrations-and-collectors.md §6; unknown times are null. A decision at time T may use only evidence with available_time ≤ T; a later backfill improves the current model of history but never widens a past knowledge boundary.

## 10. Entity resolution

Order: exact external id, account-specific alias, evidence-backed candidate scoring, human confirmation when the top candidate is below 0.85 or the gap to the runner-up is below 0.10, reversible merge and split. Before a correction is applied the impact set (facts, datasets, pending approvals, open cases, effects) is computed and shown; the correction is scoped (person, tenant, vertical) and replayed over the scope only. No global string replacement; conflation of clients is reversible because object_attribute_history keeps every prior binding.

## 11. Retrieval and context assembly

Permission-filtered by tenant, compartment and purpose; structured state queries for numbers, approvals, identities and action state; provenance retrieval for any fact; EvidencePackets record coverage, freshness and truncation; when needed evidence cannot fit or be retrieved the packet is marked truncated and the consuming step must either narrow the question or raise a dependency, never answer from a lossy summary.

## 12. Omissions

Multilingual capture and field devices are out of release 1; the interview modality has no structured schema beyond text and attribution.
