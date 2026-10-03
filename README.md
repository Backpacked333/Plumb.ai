# Plumb Autonomous Implementation System: reference package

Reference contracts, checkers, an effect-ledger simulation and contract tests for the
**Plumb Autonomous Implementation System** engineering specification, version 0.2
(October 2, 2026). The normative text is `spec/Plumb_Autonomous_Implementation_Specification_v0.2.md`;
every requirement it states is indexed in `spec/requirements_index.json`.

**What this package is.** A specification and a reference implementation of selected
controls: typed Pydantic contracts, generated JSON Schemas, a control-plane OpenAPI
proposal, a PostgreSQL design migration, three synthetic build plans, a local reference
checker, a persistent SQLite effect ledger, aggregate state machines, a production
acceptance catalog and executable contract tests. It gives a founding engineering team a
concrete, reviewable starting point with fewer ambiguous interfaces.

**What this package is not.** It is not a deployed Plumb product. Nothing here connects to
a customer system, calls a model, trains weights, provisions infrastructure or talks to a
provider. Passing the local tests does not validate Plumb's models, business outcomes,
tenant security, cloud isolation or third-party integrations; those require the production
gates the specification defines (section 28, Appendix C). `VALIDATION_REPORT.md` records
exactly what was executed and what was not.

## Measured results in this environment

<!-- COUNTS:BEGIN -->
Measured by `python3 scripts/validate.py` on 2026-10-03 (Python 3.11.15, Pydantic 2.13.4, pytest 9.1.1):

| Check | Measured result |
|-------|-----------------|
| Local contract and failure tests | 819 passed, 0 failed, 0 skipped |
| Top-level contract schemas | 17 generated; generation matches the Pydantic models |
| Supporting schemas | 5 generated |
| API interface | 24 proposed operations; no running API server |
| Local schema/API references | 534 resolved, 0 unresolved |
| Synthetic build plans | accounting (22 steps), industrial RFQ (22 steps), laundry (21 steps); all validated with zero findings |
| Capability registry | 23 step types |
| Normative requirements | 63 indexed; 10 ADRs; 18 sources |
| Production acceptance | 30 scenarios specified; none run against production |
| Requirements with a local behavioural test | 55 of 63 (6 more are covered only by artifact-inspection tests; 2 only by acceptance scenarios) |

The full table, the per-requirement coverage matrix and the list of checks that are not executed
locally are in `VALIDATION_REPORT.md`; `MANIFEST.json` carries the SHA-256 digest of every file.
<!-- COUNTS:END -->

The specification's Appendix C quotes the figures of the original delivery (56 tests,
103 resolved references, Python 3.12.14, Pydantic 2.13.5). This package reports the values
measured here instead of echoing that table; the requirement, contract, operation and
scenario counts are structural and match the specification exactly.

## Quick start

Dependencies: Python 3.11 or newer, Pydantic 2.11 to 2.x, PyYAML, jsonschema,
openapi-spec-validator and pytest. No network access is needed after installation.

```bash
python3 -m pip install -e ".[test]"          # or: pip install pydantic pyyaml jsonschema openapi-spec-validator pytest

python3 -m pytest -q                         # all local contract and failure tests
python3 scripts/validate.py                  # every check; writes VALIDATION_REPORT.md and MANIFEST.json

# Reference checker CLI (exit 0 = no ERROR findings, 1 = findings, 2 = usage/parse error)
python3 -m plumb.checker.cli plan fixtures/plans/accounting_evidence_preparation.json \
                                  fixtures/envelopes/accounting_evidence_preparation.json
python3 -m plumb.checker.cli plan fixtures/invalid/cycle.json --json   # one file embedding plan + envelope; exit 1
python3 scripts/refresh_fixture_digests.py --check    # fixture and registry content digests are current

# Generated artifacts
python3 -m plumb.schemas_tool.generate --check        # schemas/ must match the Pydantic contracts
python3 api/validate_openapi.py api/openapi.yaml --json
python3 spec/build_requirements_index.py --check      # requirements index is reproducible from the spec text
```

## Package layout

| Path | Contents | Specification |
|------|----------|---------------|
| `spec/` | Normative Markdown, reproducible requirements index (63 PL requirements, 10 ADRs, 18 sources) and its build script | whole document, section 28 |
| `plumb/contracts/` | 17 top-level typed contracts plus supporting API, event and protocol records; `common.py` holds the shared primitives | sections 4 to 19, 22, Appendix A |
| `plumb/registry/` | Capability registry (23 step types) and loader | PL-007, PL-008, ADR-003, Appendix A.5 |
| `plumb/checker/` | Plan, dataset, approval and release checkers with typed findings; CLI | PL-014 to PL-016, PL-027 to PL-030, PL-040 to PL-046, PL-053, PL-058 |
| `plumb/ledger/` | SQLite effect ledger: slot deduplication, payload conflicts, UNKNOWN reconciliation | PL-037 to PL-039, PL-057, ADR-009 |
| `plumb/statemachines/` | Guarded transition functions for the seven aggregates | section 23 |
| `plumb/schemas_tool/`, `schemas/` | JSON Schema generation and the generated schemas | section 28 |
| `api/` | OpenAPI 3.1 proposal (24 operations) and its local validator | section 22, PL-055, PL-056 |
| `sql/` | PostgreSQL design migration (not executed) | section 23, PL-052, PL-057 |
| `fixtures/` | Three synthetic envelopes and build plans; malformed plans for checker tests | section 25, Appendix B |
| `acceptance/` | Production acceptance catalog, 30 scenarios, none executed locally | PL-061, section 25 |
| `tests/` | Contract and failure tests; every test is marked with the requirements it exercises | Appendix C |
| `scripts/validate.py`, `scripts/refresh_fixture_digests.py` | Runs everything and writes `VALIDATION_REPORT.md` and `MANIFEST.json`; recomputes fixture and registry digests | section 28 |
| `docs/REFERENCE_PACKAGE_DESIGN.md` | The design contract that fixes module names and interfaces | derived |

## The 17 top-level contracts

AutonomyEnvelope, CapabilityRecord, EnvironmentInventory, EvidencePacket, OpportunitySpec,
BuildPlan, IntegrationSpec, CollectionSpec, DatasetManifest, TrainingSpec, WorkflowSpec,
EvaluationReport, InfrastructurePlan, ReleaseManifest, ActionIntent, ApprovalRecord and
VerificationAttestation. Each subclasses `ArtifactHeader` (tenant, kind, schema version,
immutable version, content digest, producer, evidence links; specification section 8), forbids
unknown fields, and encodes the MUST rules of its section as validators. Supporting records
(JobEnvelope, ErrorEnvelope, EventEnvelope, AgentTask, StepResult) are generated under
`schemas/supporting/`.

Conventions worth knowing before writing fixtures:

- Money is integer minor units plus an ISO 4217 code; there are no floating-point amounts.
- Evidence carries three time axes (event, observation, availability). Datasets are checked
  against availability time, never event time (PL-029, ADR-005).
- Fields named `*_ref` or `*_refs` hold references, never values. One helper,
  `plumb.contracts.common.reject_secret_like`, rejects anything that looks like a secret
  (secret/password/token markers, AWS key and JWT shapes, long hex or base64 runs); the
  authentication and authority fields and the operator-facing texts of `ErrorEnvelope` use the
  same helper, and storage references must follow a `scheme://` grammar (PL-054, PL-009).
- Timestamps are timezone-aware; a naive datetime is a validation error.
- Approvals of a release bind to `ReleaseManifest.approval_subject_digest()`, the manifest's
  canonical digest without its own approval references, which avoids a circular digest.
- Idempotency keys of actions derive from the logical action identity, never from the payload.

## What the local checks enforce

The checkers and tests make the following requirement subset executable: the structural and
authority rules of build plans (unique ids, dependencies, cycles, registry-backed step types,
capability maturity and artifact kinds, input and output compatibility, infrastructure
preconditions, envelope tenant, version, goal, expiry and revocation, scope, effect classes,
data-purpose grants including purposes inherited through data lineage, worst-case budgets
nested in every dimension, attempt bounds, verification obligations, deployment environments);
dataset time and split rules (future information, target leaks, temporal hold-out ordering,
duplicate ids and families across splits, quarantined rows, label-kind consistency, weak
proxies, unpinned sources, count mismatches, undeclared source use and, with an envelope,
grant resolution per purpose); approval binding (digest, tenant, policy version, decision kind,
case version, expiry, revocation, human approver, no agent-supplied records); release gating
(attestations for the exact bytes, scope and every rollout environment, recomputed digests,
independent verifiers, required verification levels read from the checks that passed, held-out
evaluation, operating plan with the PL-048 monitors, resolved model versions, shadow-first
rollout); persistent effect identity (deduplication across restarts and releases, payload and
target conflicts, explicit supersession, request-id binding, rejection evidence, reasons on every
transition, UNKNOWN that leaves only through reconciliation); and the guarded lifecycle
transitions of section 23.

`VALIDATION_REPORT.md` separates requirements exercised by behavioural tests from those covered
only by text-pinning tests (`tests/test_requirements_index.py`) or artifact-inspection tests
(`tests/test_openapi.py`, `tests/test_sql_design.py`, `tests/test_schemas.py`,
`tests/test_contract_registry.py`, `tests/test_acceptance_catalog.py`; the lists are
`TEXT_PIN_FILES` and `ARTIFACT_INSPECTION_FILES` in `scripts/validate.py`): a marker on such a
test pins the specification text or inspects a delivered artifact, it does not mean the behaviour
is enforced here.

Not executed locally: live API or connector calls; authentication and security integration
tests; PostgreSQL migration and roles; full OpenAPI and JSON Schema standards conformance;
cloud sandbox isolation; training and serving; live budget accounting; real external effects
or distributed concurrency; production deployments; customer outcome measurements. The
acceptance catalog specifies those tests; `VALIDATION_REPORT.md` lists per requirement which
local tests and which acceptance scenarios cover it.

## Fixtures and scenarios

`fixtures/plans/` holds one build plan per reference scenario of specification section 25:
accounting evidence preparation (Appendix B), industrial RFQ preparation and laundry route
preparation. Each plan passes the checker with zero findings against its envelope in
`fixtures/envelopes/`. The envelopes encode the production boundary of each scenario as
authority that is simply absent (no FINANCIAL_COMMITMENT for the accounting tenant, no
irreversible writes for binding quotes, no physical execution and no external communication
for routes, which is why the laundry plan stops at `release.activate_shadow` and has no
`release.canary` step) and each plan carries a `dependency.raise` step recording the human
decision that remains. No grant includes SERVE and the release steps list no sources; the
accounting plan narrows the data flowing into the categorization dataset to the ledger with
`StepInput.source_ids`, because mailbox and document-store grants do not cover TRAIN.
Envelopes and grants expire on 2027-03-31; checking a plan with `--now` at or after that
instant reports `ENVELOPE_INACTIVE` by design. Business data and identifiers are synthetic.

Plans embed their own content digest and the digest of their envelope; after editing a fixture
run `python3 scripts/refresh_fixture_digests.py` (or `--check`), which also refreshes the
registry record digests. Run the tests from the repository root.

`fixtures/invalid/` holds one malformed plan per defect family (cycle, unknown dependency,
unsupported step type, unsupported artifact kind, missing precondition, unauthorised goal,
unverifiable prerequisite, scope and purpose violations, oversized budgets, missing
verification and so on). Each file embeds `plan`, `envelope` and `expected_codes`, and the
CLI accepts such a file as its single argument; the checker tests are data-driven over them.

## Extending the package

- Add a step type by adding a `CapabilityRecord` to `plumb/registry/capability_registry.json`;
  the checker rejects any step whose type or capability is absent (PL-014, ADR-003).
- Add a contract rule as a Pydantic validator when it is a local fact of one artifact, and as
  a checker finding when it needs another artifact (the envelope, the registry, attestations).
- Re-run `python3 -m plumb.schemas_tool.generate` after changing a contract, then
  `python3 scripts/validate.py` to refresh the report and manifest.
- Keep secrets, production data and real identifiers out of every file; the tests scan for
  secret-looking literals.
