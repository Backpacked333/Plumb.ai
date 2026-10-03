# PostgreSQL authority foundation

This is the first bounded part of WP-01, not a running control-plane API.

## Run the checks

Use Python 3.12 and PostgreSQL 16. From the repository root:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[test,database,spec]' ruff mypy
.venv/bin/python -m pytest tests
.venv/bin/python -m pytest -c spec/rc1/pytest.ini spec/rc1/tests
PLUMB_PG_BIN=/path/to/postgresql16/bin .venv/bin/python -m pytest database/tests
.venv/bin/python -m ruff check database
.venv/bin/python -m mypy --ignore-missing-imports database
```

On Homebrew, the PostgreSQL path is `/opt/homebrew/opt/postgresql@16/bin`;
on Ubuntu it is usually `/usr/lib/postgresql/16/bin`. The database tests create a
private disposable cluster, bind only a Unix socket in a mode-0700 directory, and
stop it afterward. Local trust authentication is confined to that directory. No
provider accounts, persistent server, network listener or production DSN is used.
Missing PostgreSQL fails the database suite rather than silently skipping it.

## Apply to an empty development database

Set `PLUMB_DATABASE_URL` to an administrator connection for a **new dedicated
cluster**, then run `python -m database.bootstrap` from the repository root.
Roles are cluster-wide. The command is intentionally not an upgrade or reset tool:
an existing role/schema causes failure, with the whole bootstrap rolled back.
It never drops existing data. Configure service-role credentials and authenticated
connections separately before deploying anything; no production authentication
configuration is supplied here.

Order, in one transaction:

1. `database/roles.sql` creates non-superuser service roles and a NOLOGIN owner.
2. The six original `spec/rc1/database/migrations/*.sql` files create the schema.
3. `database/migrations/0007_tenant_authority.sql` hardens it and grants access.

Do **not** apply the archived `spec/rc1/database/roles-and-policies.sql`: it is
preserved as review input, not the operational policy. Likewise, `sql/` remains
the incompatible historical v0.2 design.

## What is enforced

- All 52 tables have a non-null tenant, ENABLE/FORCE RLS and a non-login owner.
- Four child/queue tables gain tenant columns; every foreign key binds tenant IDs.
- No tenant context, or an empty context, reads no rows. Cross-tenant writes fail.
- Service roles cannot bypass RLS, create roles or become the schema owner.
- Only control mutates lifecycle state; builder/runtime submit proposals through
  the future control API rather than directly modifying builds, cases or effects.
- Evidence ingestion, receipt recording and consumer-offset commits also belong
  to `plumb_control` in this slice. Runtime workers submit evidence/receipt proposals
  to that future trusted service, which must check authority and atomically commit
  the corresponding state/audit/outbox changes. Direct runtime inserts are denied;
  no ingestion endpoint, dispatcher or event consumer is implemented yet.
- Only verifier inserts attestations. A restrictive policy binds issuer identity
  to the database role, not a caller-settable service-identity variable. Control
  may invalidate an attestation, but cannot rewrite its outcome or signature.
- Audit rows are append-only to service roles; required sequence grants work.
- Reporting has no raw-table access; aggregate views remain to be implemented.
- Existing effect-slot uniqueness rejects concurrent live reservations, including
  UNKNOWN and CONFIRMED slots. State and outbox writes can roll back atomically.

## Trust limits and next work

`plumb.tenant_id` is transaction-local context set by a **trusted service after
authentication**. PostgreSQL clients can set custom variables themselves, so RLS
does not authenticate a tenant. Never distribute service credentials or arbitrary
SQL access to customers, generated adapters or untrusted build workers. The test
also checks that `SET LOCAL` context does not leak across pooled transactions.

This slice does not implement authenticated requests, authorization guards, approval
nonce consumption, immutable artifact updates, automatic outbox publication,
effect dispatch/reconciliation, egress policy, protected dataset-role separation,
credential vaults, signatures or tenant-safe object storage. The reference gateway
and digest/contract inconsistencies remain open and must be reconciled before use.
The SQL tests prove a local storage boundary, not production security or readiness.

Future migrations must include RLS, tenant-bound keys and role grants; the catalog
tests fail if new tables or foreign keys omit them. A real versioned migration runner
and populated-database upgrade tests are required before operating a deployment.
