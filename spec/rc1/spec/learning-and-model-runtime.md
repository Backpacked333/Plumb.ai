# Finding learning data, datasets, training, serving and routing

Training is one candidate, not a ritual. The task is defined before data is searched; labels carry authority; datasets respect knowledge boundaries and roles; serving routes by purpose, compartment and release; confidence is calibrated per task.

## 1. Task definition first (SR-070)

Information available at prediction time, target meaning, eligible population, intended deployment (auto, assist, abstain), error costs by class, observation lag, evaluation method. Categorization, extraction, routing, ranking, drafting and optimization are different tasks with different metrics; a quote acceptance is not fulfillment and a quick reply is not the desired outcome.

## 2. Finding candidate sources (SR-071)

Search authorized sources for decision and outcome boundaries; profile fields; propose joins on stable keys; audit representative matches with the domain expert; quarantine ambiguous pairs. The source-candidate table records location, semantics, stable keys, permitted uses, accessible history, label quality, revision behaviour, confidence and evidence. Example output: "11,200 usable input/target pairs, 1,800 ambiguous joins, missing source documents for the remainder" plus a CollectionSpec to improve coverage.

## 3. Label authority and maturity

| Authority | Meaning | Use |
| --- | --- | --- |
| historical_decision | What someone did in a system | Training candidate after consistency check |
| reviewed_approval | A reviewer confirmed a proposal | Training and regression |
| expert_adjudicated | A domain expert decided the right answer | Acceptance truth |
| correction | A reviewer corrected a proposal | High-value training; acceptance after adjudication |
| preference | Which of two outputs was preferred | Drafting tasks |
| behavioral_response | A client replied within N days | Effectiveness, not correctness |
| business_outcome | Period closed, quote won | Outcome models |
| model_generated | A model's own output | Never a label |

Labels mature per task: a confirmed categorization may be amended later; the maturation window is declared in the task definition and provisional labels are excluded from acceptance.

## 4. Sparse or unusable history (SR-075)

Sparse history, missing input snapshots, undocumented decisions, ambiguous actors, outdated policies or labels unusable for the purpose lead to a non-trained baseline (rules, native configuration, prompted model with assist) plus a prospective collector. That is an implemented learning path and is reported as such, not as a failed promise.

## 5. Human labeling inside normal work

Review items in the existing tool show the proposal, the evidence and one-click accept, correct or reject; the decision is journaled with case version. Automatic successes are audited by stratified random sampling with recorded sampling probabilities, so a review queue of hard cases is never mistaken for production quality.

## 6. Dataset rows, roles and splits (DC-017 to DC-020)

Row contract: example id, family id, tenant and compartment, input snapshot references, decision time, availability evidence, target evidence, label authority and status, policy version, transformation version, allowed purposes, inclusion or exclusion reason. Roles: training, development, calibration, regression, protected acceptance, prospective monitoring; rows exposed to repair leave acceptance. Splits: temporal (future performance), family-disjoint (near-duplicate transactions), client-disjoint (new clients), stratified; each states its question. Manifests are immutable with pins, counts, distributions, maturity and rejections; a removed source makes a dataset UNAVAILABLE with a tombstone manifest.

## 7. Drift and feedback loops

The intervention changes the data-generating process: correction rates fall when review coverage falls, not only when quality rises; the monitoring role tracks review coverage, sampling and policy eras. Training and serving feature parity is tested; the end-to-end workflow is evaluated, not only the model.

## 8. Paths and training adapters (IC-011)

Deterministic or native; prompted; retrieval; specialist API; optimizer; classical training; fine-tuning. Training adapters implement capability discovery (task, base model, method, data format, licensing, region, limits), submission with persisted identity, status, cancellation, checkpoint semantics where the provider offers them, artifacts, evaluation, cleanup and cost settlement. A lost submission response moves to SUBMISSION_UNKNOWN and is reconciled by the submission identity before any resubmission (SR-072).

## 9. Versioning, routing, caching (SR-073, SR-076, SR-079)

Model and prompt versions are immutable; aliases resolve per case; cache keys include purpose, tenant, compartment, release, source freshness and policy version; fallbacks are declared per task and never use a forbidden processor or an untested behaviour; a retired pinned endpoint fails the task to assist mode and raises a dependency. The strongest identity a hosted provider exposes is recorded; behavioural drift on a hosted model is detected by the monitoring role and triggers re-evaluation.

## 10. Audience and compartments (SR-077)

A model carrying restricted client information declares its serving audience; principals outside it are routed to a compartment-safe model or to assist; retrieval ACLs do not solve knowledge in weights, so pooled models across restricted compartments are not built unless the task abstraction is non-memorizing and the domain owner approves.

## 11. Calibration and abstention (SR-078)

Confidence is estimated per task on the calibration role, reported per slice, and used for routing thresholds that are set by error cost; raw self-reported confidence never gates an auto action.

## 12. Omissions

No specific base model or provider is named as the choice; the Market records candidates with their terms, and the SolutionSpec records the selection per tenant.
