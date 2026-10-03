# Comparative review of Source A and Source B

Verdict: Source B is the right foundation for engineering because it gets the trust model, effect protocol, artifact separation and verification independence right; Source A is the right foundation for the product because it keeps the customer journey, observation design, Studio surfaces and domain specificity that B dropped. Neither is build-ready alone, and the master prompt's reconciliation list names the exact seams. This package keeps B's enforcement and A's product, and resolves the sixteen seams in RECONCILIATION_REGISTER.md.

## Source A (v1.0 product and system specification)

Strongest contributions kept here: the six-step journey and its vocabulary; worker-controlled desktop capture with on-device redaction; the OCEL 2.0 map with provenance on every fact; leak detectors and the data-asset inventory ("where the training data lies"); the Market registry with verification levels; data taps including the valve tap; replay before go-live; nine Studio views; a concrete accounting pack with the QuickBooks "For review" limit called out; per-unit pricing.

Defects that block engineering from A as written:

1. One mutable YAML Blueprint carries build, workflow, authority, release and acceptance. A change to a prompt invalidates an approval of the workflow and nothing says so. The approval hash is computed over an object that contains the approval.
2. Fixed agent autonomy levels (L0 to L4) describe agents, not operations. Nothing enforces them; a "Builder at L2" is a label.
3. Authorization is conflated: one Blueprint approval covers build and deploy; valves cover case actions; there is no object binding a decision to exact digests, case version, expiry and anti-replay.
4. "Raw data stays on the device" is asserted while messages, documents and call transcripts are cloud-ingested in the same section.
5. Masking before storage destroys semantics an authorized action needs (a real recipient address, an amount, an account to post against).
6. "Deleting an event deletes it everywhere" sits beside immutable datasets, seven-year meter retention and trained adapters.
7. Replay against "what the humans did" treats historical behaviour as ground truth, and the timing counterfactual ("day four, not fourteen") is presented beside it as if it were the same kind of evidence.
8. Replay failures send the divergent cases back to the Builder, which contaminates the acceptance set.
9. "Case key as workflow id gives idempotency for free" is false for external effects; a second reminder with a different body is not deduplicated.
10. "Kill switch restores the previous state within a minute" promises restoration of an external world that cannot be restored; sent messages stay sent.
11. The billable unit "client close completed" is not what the first release delivers; it delivers a review package.
12. Phase 0 is ninety days of observation-only tooling before any implementation loop runs, which is exactly the failure the master prompt names.
13. Thresholds (95%, 97%, 0 wrong postings, 420 cases, 14 shadow days) are asserted without a rationale tied to opportunities for failure.

## Source B (v0.2 engineering specification)

Strongest contributions kept here: separation of engineering credentials from runtime credentials (ADR-001); artifacts and plan state outside the agent workspace (ADR-002); typed BuildPlan with a registry-backed compiler (ADR-003); one durable lifecycle owner (ADR-004); multiple time axes with provenance (ADR-005); learning setup as a generated deployment (ADR-006); independent promotion gates (ADR-007); immutable model identity per case (ADR-008); explicit UNKNOWN for uncertain effects (ADR-009); autonomy measured separately from runtime automation (ADR-010); the failure classification table; the three authorization decisions; the first customer trace with its denominator.

Gaps that keep B from being build-ready:

1. Lifecycles are enumerated but transitions are not specified (PL-057 says "each service implements a transition function" without giving one). This package supplies the tables in contracts/state-machines and an engine that refuses anything not in them.
2. The observation layer is reduced to a paragraph; desktop permissions, worker controls, exclusions, offline queues and deletion are absent.
3. Product vocabulary, Studio surfaces, Market, taps, valves and domain packs are gone, which makes the customer experience section thin and the first-release scope abstract.
4. Technology is left as candidates (Nango, Airbyte, Pulumi, MLflow, OPA optional). The master prompt requires a choice with upgrade triggers.
5. Obligations are named but their lifecycle (creation, recurrence, exemption, partial satisfaction, expiry, reopening, supersession) is not defined; the effect slot depends on an obligation epoch that B never specifies.
6. Approval objects lack anti-replay semantics for links, nonces, prefetch and duplicate clicks.
7. Removal is a sentence; there is no removal state machine, no backup policy, no treatment of trained components.
8. The completion predicate distinction (review package prepared versus close completed) is raised but not turned into billing mechanics.
9. The companion package is described, not available; its 56 tests cannot be inspected.

## What the master prompt asks for instead

A reconciled package with: stable requirement IDs across six categories and a traceability matrix; one system model of eleven artifacts with an authority map; three authorization layers; three discovery routes; observation that earns its scope through an experiment; obligations and temporal truth; a typed intermediate representation with validation passes and rejected fixtures; an implementable agent protocol with leases and fencing; certified operations rather than vendor logos; generated collection apparatus with convergence rules; learning data found and validated per task; protected acceptance separate from repair; a complete effect protocol with UNKNOWN; an argument-aware gateway; immutable releases; a removal lifecycle; metering ledgers kept apart from billing; domain contracts; APIs and persistence with transition tables; reuse rules; end-to-end traces; an adversarial acceptance catalog; a thin complete vertical proof early; an autonomy benchmark with frozen denominators; and separate readiness verdicts. This package is organized to those headings.
