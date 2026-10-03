# Plumb reconciled specification package 1.0-rc1

A reconciled, implementation-ready specification for Plumb.ai, built from Source A (product spec v1.0), Source B (engineering spec 0.2) and the master prompt. The engineering contracts exist as editable and machine-readable files; the reference code implements the hard contracts and is tested locally; nothing here is a deployed product.

Start with COMPARATIVE_REVIEW.md (what each source got right and wrong), RECONCILIATION_REGISTER.md (how each conflict was resolved), PRODUCT_CONTRACT.md (what Plumb promises), ARCHITECTURE.md (the chosen stack) and REQUIREMENTS.md (the IDs everything else cites). VERIFICATION_REPORT.md states exactly what was executed and the readiness verdicts.

## Layout

| Path | Contents |
| --- | --- |
| SOURCE_INVENTORY.md | What was read, executed, referenced, unavailable |
| COMPARATIVE_REVIEW.md | Critique of Source A and Source B and what the master prompt asks for instead (added file, mapped to the brief's reconciliation requirement) |
| RECONCILIATION_REGISTER.md | 28 entries with dispositions, selected behaviour, requirement ids, artifacts, tests |
| ASSUMPTIONS_AND_DECISIONS.md | ADR-001 to ADR-023 and assumptions AS-01 to AS-08 |
| PRODUCT_CONTRACT.md, ARCHITECTURE.md, GLOSSARY.md | Promise, stack and trust boundaries, terms and authority map |
| REQUIREMENTS.md, TRACEABILITY.csv | 260 requirements in six categories; generated matrix |
| spec/ | Fourteen subsystem specifications |
| contracts/ | canonical-models (Pydantic, schema source of truth), generated-json-schema (37 schemas), openapi.yaml (26 operations), event-contracts, state-machines (10 guarded tables) |
| database/ | Six PostgreSQL migrations, roles and RLS policies, invariants and indexes |
| reference/ | bounded-plan-validator, guarded-state-transitions, effect-protocol-harness, policy-gateway, collector-convergence (the last two are additions mapped to "guarded-state-transitions" and "effect-protocol-harness" in the brief's layout) |
| fixtures/ | accounting, industrial-rfq, laundry-routing, failure-cases (29 rejected fixtures with expected codes) |
| tests/ | contract, property-and-state-machine, adapter, security, integration-gated |
| acceptance/ | production-catalog.md, autonomy-benchmark.md, business-outcome-measurement.md, end-to-end-traces.md (added) |
| operations/ | deployment-runbook.md, incident-and-recovery.md, removal-and-offboarding.md |
| DELIVERY_PLAN.md | Work packages, sequencing, experiment register |
| VERIFICATION_REPORT.md | Executed checks, limits, adversarial review, readiness verdicts |
| MANIFEST.json | SHA-256 of every file |
| tools/ | gen_schemas.py, gen_fixtures.py, gen_traceability.py, build_manifest.py |

## Reproduce

```
python3 -m pip install "pydantic>=2.9" jsonschema pytest pyyaml hypothesis pglast openapi-spec-validator
python3 tools/gen_schemas.py
python3 tools/gen_fixtures.py
python3 tools/gen_traceability.py
python3 -m pytest -q
python3 tools/build_manifest.py
```

Tested with Python 3.12.3, pydantic 2.13.5, jsonschema 4.26.0, pytest 9.1.1, hypothesis 6.168.3, pglast 8.4 on Ubuntu 24.04. The integration-gated tests skip by design; their gates are IG-001 to IG-010 in tests/integration-gated/test_live_probes.py.

## Boundaries

No live provider was called, no database was provisioned, no model trained, no sandbox isolation tested, no customer data used. Numbers in the documents are proposals unless the text says measured. Legal statements are questions for qualified review, not assertions.
