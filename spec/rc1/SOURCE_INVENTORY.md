# Source inventory

As of 2026-10-03. Everything below was read in full unless marked otherwise. Nothing was executed except the reference code in this package.

| Item | Form | Read | Executed | Status |
| --- | --- | --- | --- | --- |
| Source A: "Plumb System Specification v1.0" (Claude Doc, 23 sections, 3 drawings) | Prose spec with YAML Blueprint example, schemas appendix, roadmap | In full | n/a | Available |
| Source B: "Plumb Autonomous Implementation System, Engineering Specification 0.2" (PDF, 30 pages, PL-001 to PL-063, ADR-001 to ADR-010, Appendices A to C) | Normative engineering spec | In full, including tables and appendices | n/a | Available |
| Source B companion package (17 Pydantic contracts, 24-operation OpenAPI, SQL design, 3 synthetic plans, SQLite effect ledger, 56 local tests, MANIFEST) | Code archive referenced by Appendix C | Not available: only Appendix C's description was read | Not executed | Unavailable; its claims are treated as reported, not verified |
| Master prompt: "Plumb Master Specification Prompt" (35 sections) | Brief for this package | In full | n/a | Available |
| Plumb pitch video (English, 4 min 15 s) | Product scenario | Captions and screens read in an earlier session; treated as scenario, not evidence | n/a | Available |
| Vendor documentation consulted for dependency claims (see each spec file's Sources list): Intuit QuickBooks Online change data capture; Plaid Statements; Meta Wearables Device Access Toolkit; Nango and Composio comparisons; OCEL 2.0 specification; Anthropic Claude Code overview | Web pages opened in earlier research for Source A | Opened | n/a | Access dates recorded in the Sources lists; each claim carries verification_status documented only |
| Vendor documentation cited by Source B ([S01] to [S18]: Anthropic harness posts, Nango management MCP, Airbyte builder, Pulumi Automation API, LangGraph interrupts, MCP security best practices, Debezium, Feast, AWS CreateTrainingJob, MLflow registry, OpenLineage, PostgreSQL RLS, Google Workspace user data policy, OpenAPI 3.1.1, OpenTelemetry semconv, Temporal) | Cited by Source B | Not re-opened in this session; carried as Source B's citations | n/a | Referenced; re-verification is an open action in DELIVERY_PLAN.md (WP-00) |

## What this package executed

- Pydantic canonical models and JSON Schema generation (`tools/gen_schemas.py`).
- Fixture generation with model validation (`tools/gen_fixtures.py`).
- 114 local tests passing, 10 integration-gated tests skipped (`python3 -m pytest -q`), covering the bounded plan validator, guarded state tables, SQLite effect ledger, policy gateway, collector convergence and schema/fixture agreement.
- OpenAPI 3.1 validation with `openapi-spec-validator`.
- PostgreSQL DDL parsed with `pglast` (syntax only; never applied to a database).
- SHA-256 manifest of every file (`MANIFEST.json`).

## What this package did not do

No live provider was called, no OAuth consent was obtained, no migration was applied to PostgreSQL, no model was trained, no sandbox isolation was tested, no customer data was used. All identifiers in fixtures and traces are synthetic.
