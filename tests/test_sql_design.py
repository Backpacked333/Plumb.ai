"""Structural tests for the PostgreSQL design migration ``sql/001_initial_design.sql``.

The migration is a design artifact that is never executed here (specification
section 23, Appendix C), so these tests parse the SQL text. They check the
section 23 lifecycles as CHECK constraints, tenant isolation via row level
security on every tenant table (PL-052), the at-least-once outbox with consumer
deduplication (section 22), effect-slot uniqueness and transition audit
(PL-037, PL-039, PL-057), approval bindings (PL-040), idempotent jobs (PL-055)
and the role separation the specification requires (PL-052).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SQL_PATH = REPO_ROOT / "sql" / "001_initial_design.sql"

DESIGN_TABLES = {
    "tenants",
    "envelopes",
    "source_grants",
    "capabilities",
    "artifacts",
    "evidence_events",
    "objects",
    "object_links",
    "facts",
    "goals",
    "opportunities",
    "builds",
    "build_steps",
    "build_step_attempts",
    "datasets",
    "dataset_rows",
    "training_jobs",
    "evaluations",
    "approvals",
    "releases",
    "cases",
    "effects",
    "effect_transitions",
    "outbox",
    "processed_events",
    "outcome_observations",
    "human_effort",
}
PLATFORM_TABLES = {"tenants", "capabilities"}

LIFECYCLES = {
    "builds": ["DRAFT", "VALIDATED", "RUNNING", "WAITING_AUTH", "WAITING_INPUT", "VERIFYING", "VERIFIED", "FAILED", "CANCELLED"],
    "build_steps": ["PENDING", "READY", "RUNNING", "VERIFYING", "VERIFIED", "FAILED", "BLOCKED", "CANCELLED"],
    "collectors": ["PLANNED", "SHADOW", "BACKFILLING", "RECONCILING", "ACTIVE", "DEGRADED", "PAUSED", "RETIRED"],
    "datasets": ["PROPOSED", "MATERIALIZING", "QUARANTINED", "VERIFIED", "SUPERSEDED", "UNAVAILABLE"],
    "training_jobs": ["PLANNED", "SUBMITTED", "RUNNING", "CANDIDATE", "FAILED", "CANCELLED"],
    "releases": ["CANDIDATE", "VERIFIED", "SHADOW", "CANARY", "ACTIVE", "PAUSED", "ROLLED_BACK", "RETIRED"],
    "effects": ["RESERVED", "DISPATCHED", "UNKNOWN", "CONFIRMED", "FAILED_FINAL", "COMPENSATED"],
}
HUMAN_EFFORT_CATEGORIES = ["CUSTOMER_AUTHORIZATION", "DOMAIN_CLARIFICATION", "NORMAL_BUSINESS_REVIEW", "ENGINEERING_INTERVENTION", "OPERATIONAL_REPAIR"]
ERROR_CLASSES = [
    "AUTH_REQUIRED", "SCOPE_DENIED", "PURPOSE_DENIED", "POLICY_STALE", "STATE_CONFLICT", "PAYLOAD_CONFLICT",
    "BUDGET_EXCEEDED", "CAPABILITY_UNSUPPORTED", "SOURCE_STALE", "DATA_QUALITY_FAILED", "VERIFICATION_FAILED",
    "EFFECT_UNKNOWN", "RETRY_EXHAUSTED",
]

CREATE_TABLE_RE = re.compile(r"CREATE TABLE\s+(?:IF NOT EXISTS\s+)?(?:plumb\.)?(\w+)\s*\(", re.IGNORECASE)


def _strip_comments(sql: str) -> str:
    return "\n".join(line for line in sql.splitlines() if not line.strip().startswith("--"))


def _statements(sql: str) -> list[str]:
    """Top-level statements split on ';' outside of $$ bodies and quotes, comments removed."""
    text = _strip_comments(sql)
    statements: list[str] = []
    buffer: list[str] = []
    in_dollar = False
    in_quote = False
    index = 0
    while index < len(text):
        char = text[index]
        if text.startswith("$$", index):
            in_dollar = not in_dollar
            buffer.append("$$")
            index += 2
            continue
        if char == "'" and not in_dollar:
            in_quote = not in_quote
        if char == ";" and not in_dollar and not in_quote:
            statement = "".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []
        else:
            buffer.append(char)
        index += 1
    tail = "".join(buffer).strip()
    if tail:
        statements.append(tail)
    return statements


def _table_bodies(sql: str) -> dict[str, str]:
    """Table name -> text between the outermost parentheses of its CREATE TABLE."""
    bodies: dict[str, str] = {}
    for match in CREATE_TABLE_RE.finditer(sql):
        depth = 1
        index = match.end()
        while depth and index < len(sql):
            if sql[index] == "(":
                depth += 1
            elif sql[index] == ")":
                depth -= 1
            index += 1
        bodies[match.group(1).lower()] = sql[match.end() : index - 1]
    return bodies


def _check_values(body: str, column: str) -> list[str]:
    """Values of the ``CHECK (<column> IN (...))`` constraint for ``column``."""
    match = re.search(rf"CHECK\s*\(\s*{column}\s+IN\s*\(([^)]*)\)", body, re.IGNORECASE | re.DOTALL)
    assert match, f"no IN-list CHECK constraint on column {column}"
    return re.findall(r"'([^']*)'", match.group(1))


@pytest.fixture(scope="module")
def sql() -> str:
    return SQL_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def statements(sql: str) -> list[str]:
    return _statements(sql)


@pytest.fixture(scope="module")
def tables(sql: str) -> dict[str, str]:
    return _table_bodies(sql)


# --------------------------------------------------------------------------
# File framing
# --------------------------------------------------------------------------


@pytest.mark.requirements("PL-057", "PL-052")
def test_header_declares_design_migration_and_rls_caveat(sql: str) -> None:
    header = sql[: sql.index("BEGIN;")]
    assert "DESIGN" in header and "NOT been executed" in header
    assert "PL-052" in header
    assert "owner/superuser" in header
    assert "BYPASSRLS" in header


@pytest.mark.requirements("PL-057")
def test_file_is_one_transaction(statements: list[str]) -> None:
    assert statements[0].upper() == "BEGIN"
    assert statements[-1].upper() == "COMMIT"
    assert sum(1 for s in statements if s.upper() in {"BEGIN", "COMMIT"}) == 2


@pytest.mark.requirements("PL-057")
def test_partitioning_is_a_comment_only(sql: str) -> None:
    assert re.search(r"after measured need", sql, re.IGNORECASE)
    assert not re.search(r"PARTITION\s+BY\s+(RANGE|LIST|HASH)", _strip_comments(sql), re.IGNORECASE)
    assert "PARTITION OF" not in _strip_comments(sql).upper()


# --------------------------------------------------------------------------
# Tables and keys
# --------------------------------------------------------------------------


@pytest.mark.requirements("PL-057", "PL-052")
def test_every_design_table_is_created(tables: dict[str, str]) -> None:
    missing = DESIGN_TABLES - set(tables)
    assert not missing, f"design §9 tables missing: {sorted(missing)}"
    assert "collectors" in tables, "section 23 lists a collector lifecycle; a collectors table is required"
    assert "jobs" in tables, "PL-055 needs a durable job table keyed by idempotency key"


@pytest.mark.requirements("PL-052", "PL-004")
def test_every_table_except_platform_tables_has_tenant_id(tables: dict[str, str]) -> None:
    for name, body in tables.items():
        has_tenant = re.search(r"^\s*tenant_id\s+plumb\.tenant_id\s+NOT NULL", body, re.MULTILINE | re.IGNORECASE)
        if name in PLATFORM_TABLES:
            assert not has_tenant, f"{name} is platform-level and must not carry tenant_id"
        else:
            assert has_tenant, f"{name} lacks a NOT NULL tenant_id column"
            assert re.search(r"REFERENCES plumb\.tenants\s*\(id\)", body), f"{name}.tenant_id must reference tenants"


@pytest.mark.requirements("PL-052", "PL-057")
def test_primary_keys_are_tenant_qualified(tables: dict[str, str]) -> None:
    for name, body in tables.items():
        if name in PLATFORM_TABLES:
            continue
        match = re.search(r"PRIMARY KEY\s*\(([^)]*)\)", body, re.IGNORECASE)
        assert match, f"{name} has no composite primary key"
        columns = [c.strip() for c in match.group(1).split(",")]
        if name == "processed_events":
            assert columns == ["consumer", "event_id"], "consumer dedup key must be (consumer, event_id)"
        else:
            assert columns[0] == "tenant_id", f"{name} primary key must start with tenant_id: {columns}"


@pytest.mark.requirements("PL-052")
def test_every_foreign_key_between_tenant_tables_includes_tenant_id(tables: dict[str, str]) -> None:
    for name, body in tables.items():
        for match in re.finditer(r"FOREIGN KEY\s*\(([^)]*)\)\s*REFERENCES\s+plumb\.(\w+)\s*\(([^)]*)\)", body, re.IGNORECASE):
            local = [c.strip() for c in match.group(1).split(",")]
            remote = [c.strip() for c in match.group(3).split(",")]
            assert local[0] == "tenant_id" and remote[0] == "tenant_id", f"{name} -> {match.group(2)} FK is not tenant-qualified"
            assert len(local) == len(remote)


# --------------------------------------------------------------------------
# Section 23 lifecycles and other CHECK constraints
# --------------------------------------------------------------------------


@pytest.mark.requirements("PL-057", "PL-047", "PL-038")
@pytest.mark.parametrize("table", sorted(LIFECYCLES))
def test_state_check_constraints_match_section_23(tables: dict[str, str], table: str) -> None:
    assert _check_values(tables[table], "state") == LIFECYCLES[table]


@pytest.mark.requirements("PL-057")
def test_effect_transitions_audit_from_to_reason(tables: dict[str, str]) -> None:
    body = tables["effect_transitions"]
    assert _check_values(body, "to_state") == LIFECYCLES["effects"]
    assert re.search(r"from_state\s+TEXT\s+CHECK\s*\(\s*from_state IS NULL OR from_state IN", body)
    assert re.search(r"reason\s+TEXT\s+NOT NULL CHECK \(length\(reason\) > 0\)", body)
    assert "action_id" in body and "actor_principal_id" in body


@pytest.mark.requirements("PL-057")
def test_every_lifecycle_table_persists_a_reason_and_row_version(tables: dict[str, str]) -> None:
    for table in LIFECYCLES:
        body = tables[table]
        assert re.search(r"state_reason\s+TEXT\s+NOT NULL", body), f"{table} lacks a persisted state_reason"
        assert re.search(r"row_version\s+BIGINT\s+NOT NULL DEFAULT 1", body), f"{table} lacks row_version for compare-and-set"


@pytest.mark.requirements("PL-057", "PL-056")
def test_row_version_triggers_exist_for_versioned_aggregates(sql: str) -> None:
    for table in ("envelopes", "builds", "build_steps", "collectors", "datasets", "training_jobs", "releases", "cases", "effects", "jobs"):
        assert re.search(rf"CREATE TRIGGER {table}_row_version BEFORE UPDATE ON plumb\.{table}", sql), table
    assert "CREATE FUNCTION plumb.bump_row_version()" in sql


@pytest.mark.requirements("PL-037", "PL-039")
def test_effects_slot_is_unique_and_payload_digest_separate(sql: str, tables: dict[str, str]) -> None:
    body = tables["effects"]
    assert re.search(r"CREATE UNIQUE INDEX effects_slot_key_idx\s+ON plumb\.effects \(tenant_id, slot_key\)", sql)
    for column in ("slot_key", "payload_digest", "expected_state_version", "authority_ref", "deployment_version", "idempotency_key", "supersedes_action_id", "provider_request_id", "external_id"):
        assert re.search(rf"^\s*{column}\s", body, re.MULTILINE), f"effects lacks {column}"
    assert "deployment_version" not in re.search(r"CREATE UNIQUE INDEX effects_slot_key_idx[^;]*", sql).group(0), "dedup must not depend on the release"
    assert re.search(r"CONSTRAINT effects_confirmed_has_receipt CHECK \(state NOT IN \('CONFIRMED', 'COMPENSATED'\) OR receipt_digest IS NOT NULL\)", body)


@pytest.mark.requirements("PL-038", "PL-039")
def test_outstanding_effects_partial_index(sql: str) -> None:
    assert re.search(
        r"CREATE INDEX effects_outstanding_idx ON plumb\.effects \(tenant_id, state\) WHERE state IN \('DISPATCHED', 'UNKNOWN'\)",
        sql,
    )


@pytest.mark.requirements("PL-057")
def test_job_readiness_partial_index(sql: str) -> None:
    assert re.search(
        r"CREATE INDEX build_steps_ready_idx ON plumb\.build_steps \(tenant_id, build_id, state\) WHERE state = 'READY'",
        sql,
    )


@pytest.mark.requirements("PL-057")
def test_outbox_and_processed_events_implement_at_least_once_with_dedup(sql: str, tables: dict[str, str]) -> None:
    outbox = tables["outbox"]
    for column in ("aggregate_id", "aggregate_version", "event_type", "occurred_at", "recorded_at", "correlation_id", "causation_id", "schema_version", "payload_ref", "published_at"):
        assert re.search(rf"^\s*{column}\s", outbox, re.MULTILINE), f"outbox lacks {column}"
    assert re.search(r"UNIQUE \(tenant_id, aggregate_type, aggregate_id, aggregate_version\)", outbox)
    assert re.search(r"CREATE INDEX outbox_unpublished_idx ON plumb\.outbox \(tenant_id, recorded_at\) WHERE published_at IS NULL", sql)
    processed = tables["processed_events"]
    assert re.search(r"PRIMARY KEY \(consumer, event_id\)", processed)


@pytest.mark.requirements("PL-009", "PL-024")
def test_external_source_identity_index_and_time_axes(sql: str, tables: dict[str, str]) -> None:
    assert re.search(
        r"CREATE UNIQUE INDEX evidence_events_external_identity_idx\s+ON plumb\.evidence_events \(tenant_id, source_id, external_record_id, external_version\)",
        sql,
    )
    body = tables["evidence_events"]
    assert re.search(r"CHECK \(availability_time >= observation_time\)", body)


@pytest.mark.requirements("PL-047", "PL-035")
def test_case_lookup_indexes(sql: str) -> None:
    assert re.search(r"CREATE INDEX cases_release_state_idx ON plumb\.cases \(tenant_id, release_id, workflow_state\)", sql)
    assert re.search(r"CREATE INDEX cases_external_subject_idx ON plumb\.cases \(tenant_id, external_subject_key\)", sql)


@pytest.mark.requirements("PL-057")
def test_build_step_attempts_carry_lease_and_fencing(tables: dict[str, str]) -> None:
    body = tables["build_step_attempts"]
    for column in ("lease_owner", "lease_expires_at", "fencing_token", "attempt_no", "reserved_minor_units"):
        assert re.search(rf"^\s*{column}\s", body, re.MULTILINE), column
    assert re.search(r"fencing_token\s+BIGINT\s+NOT NULL", body)
    assert re.search(r"UNIQUE \(tenant_id, build_id, step_id, fencing_token\)", body)
    steps = tables["build_steps"]
    assert re.search(r"CONSTRAINT build_steps_verified_needs_attestation CHECK \(state <> 'VERIFIED' OR verifier_attestation_artifact_id IS NOT NULL\)", steps)


@pytest.mark.requirements("PL-040")
def test_approvals_bind_digest_versions_approver_and_expiry(tables: dict[str, str]) -> None:
    body = tables["approvals"]
    assert re.search(r"subject_digest\s+plumb\.sha256_digest NOT NULL", body)
    assert re.search(r"^\s*case_version\s+INTEGER", body, re.MULTILINE)
    assert re.search(r"policy_version\s+plumb\.semver NOT NULL", body)
    assert re.search(r"expires_at\s+TIMESTAMPTZ NOT NULL", body)
    assert re.search(r"^\s*revoked_at\s+TIMESTAMPTZ", body, re.MULTILINE)
    assert _check_values(body, "approver_principal_type") == ["HUMAN_OWNER", "HUMAN_REVIEWER", "HUMAN_APPROVER"]
    assert _check_values(body, "decision_kind") == ["DATA_USE", "IMPLEMENT_OPERATE", "CASE_LEVEL_BUSINESS"]
    assert "CHECK (expires_at > approved_at)" in body


@pytest.mark.requirements("PL-030")
def test_datasets_unavailable_reason_is_tied_to_state(tables: dict[str, str]) -> None:
    body = tables["datasets"]
    assert re.search(r"^\s*unavailable_reason\s+TEXT", body, re.MULTILINE)
    assert "CHECK ((state = 'UNAVAILABLE') = (unavailable_reason IS NOT NULL))" in body


@pytest.mark.requirements("PL-027", "PL-028", "PL-029")
def test_dataset_rows_enforce_point_in_time_and_quarantine_rules(tables: dict[str, str]) -> None:
    body = tables["dataset_rows"]
    assert "CHECK (input_availability_time <= decision_time)" in body
    assert "CHECK (label_status = 'ACCEPTED' OR exclusion_reason IS NOT NULL)" in body
    assert "CHECK (split <> 'train' OR label_status = 'ACCEPTED')" in body
    assert _check_values(body, "label_status") == ["ACCEPTED", "QUARANTINED_AMBIGUOUS", "QUARANTINED_INCONSISTENT", "QUARANTINED_DISPUTED", "REJECTED"]
    assert _check_values(body, "split") == ["train", "validation", "test_temporal", "test_client_disjoint"]


@pytest.mark.requirements("PL-033")
def test_training_jobs_persist_submission_identity(tables: dict[str, str]) -> None:
    body = tables["training_jobs"]
    assert re.search(r"^\s*submission_identity\s+TEXT", body, re.MULTILINE)
    assert "UNIQUE (tenant_id, submission_identity)" in body
    assert "CHECK (state = 'PLANNED' OR submission_identity IS NOT NULL)" in body


@pytest.mark.requirements("PL-034")
def test_releases_carry_resolved_model_version(tables: dict[str, str]) -> None:
    assert re.search(r"^\s*resolved_model_version\s+TEXT", tables["releases"], re.MULTILINE)


@pytest.mark.requirements("PL-003", "PL-059")
def test_human_effort_and_outcome_categories(tables: dict[str, str]) -> None:
    assert _check_values(tables["human_effort"], "category") == HUMAN_EFFORT_CATEGORIES
    outcomes = tables["outcome_observations"]
    for column in ("case_id", "release_id", "model_calls", "completed", "correct", "realized_value_minor_units", "realized_value_currency", "review_minutes", "human_effort_category"):
        assert re.search(rf"^\s*{column}\s", outcomes, re.MULTILINE), column
    match = re.search(r"human_effort_category IN \(([^)]*)\)", outcomes)
    assert match and re.findall(r"'([^']*)'", match.group(1)) == HUMAN_EFFORT_CATEGORIES


@pytest.mark.requirements("PL-055")
def test_jobs_are_idempotent_per_tenant_with_payload_digest(tables: dict[str, str]) -> None:
    body = tables["jobs"]
    assert "UNIQUE (tenant_id, idempotency_key)" in body
    assert re.search(r"payload_digest\s+plumb\.sha256_digest NOT NULL", body)
    # Job status vocabulary mirrors plumb.contracts.api.JobStatus (the OpenAPI JobStatus component too).
    from plumb.contracts.api import JobStatus

    assert set(_check_values(body, "status")) == {status.value for status in JobStatus}
    assert _check_values(body, "status") == ["PENDING", "RUNNING", "WAITING", "SUCCEEDED", "FAILED"]
    match = re.search(r"error_class IN \(([^)]*)\)", body)
    assert match and re.findall(r"'([^']*)'", match.group(1)) == ERROR_CLASSES


# --------------------------------------------------------------------------
# Row level security and roles (PL-052)
# --------------------------------------------------------------------------


@pytest.mark.requirements("PL-052")
def test_every_tenant_table_has_enabled_and_forced_rls_with_tenant_policy(sql: str, tables: dict[str, str]) -> None:
    for name in tables:
        if name in PLATFORM_TABLES:
            assert not re.search(rf"ALTER TABLE plumb\.{name} ENABLE ROW LEVEL SECURITY", sql), name
            continue
        assert re.search(rf"ALTER TABLE plumb\.{name} ENABLE ROW LEVEL SECURITY;", sql), f"{name} lacks ENABLE ROW LEVEL SECURITY"
        assert re.search(rf"ALTER TABLE plumb\.{name} FORCE ROW LEVEL SECURITY;", sql), f"{name} lacks FORCE ROW LEVEL SECURITY"
        policy = re.search(
            rf"CREATE POLICY {name}_tenant_isolation ON plumb\.{name}\s+USING \(tenant_id = current_setting\('plumb\.tenant_id', true\)\)\s+WITH CHECK \(tenant_id = current_setting\('plumb\.tenant_id', true\)\)",
            sql,
        )
        assert policy, f"{name} lacks a tenant isolation policy with USING and WITH CHECK"


@pytest.mark.requirements("PL-052")
def test_rls_statement_count_matches_tenant_table_count(sql: str, tables: dict[str, str]) -> None:
    tenant_tables = set(tables) - PLATFORM_TABLES
    code = _strip_comments(sql)
    assert len(re.findall(r"ENABLE ROW LEVEL SECURITY", code)) == len(tenant_tables)
    assert len(re.findall(r"FORCE ROW LEVEL SECURITY", code)) == len(tenant_tables)
    assert len(re.findall(r"CREATE POLICY", code)) == len(tenant_tables)


@pytest.mark.requirements("PL-052", "PL-006")
def test_roles_are_separated_and_granted(sql: str) -> None:
    for role in ("plumb_app", "plumb_migrator", "plumb_platform_admin"):
        assert re.search(rf"CREATE ROLE {role} NOLOGIN", sql), f"role {role} is not created"
    assert "CREATE ROLE plumb_platform_admin NOLOGIN NOINHERIT BYPASSRLS" in sql
    assert "BYPASSRLS" not in re.search(r"CREATE ROLE plumb_app[^;]*", sql).group(0)
    assert "BYPASSRLS" not in re.search(r"CREATE ROLE plumb_migrator[^;]*", sql).group(0)
    assert "CREATE SCHEMA IF NOT EXISTS plumb AUTHORIZATION plumb_migrator" in sql
    assert re.search(r"GRANT USAGE ON SCHEMA plumb TO plumb_app", sql)
    assert re.search(r"GRANT SELECT, INSERT ON\s+plumb\.artifacts,", sql), "artifacts must be append-only for the service role"
    app_grants = [s for s in _statements(sql) if s.upper().startswith("GRANT") and s.rstrip().upper().endswith("TO PLUMB_APP")]
    assert app_grants
    for grant in app_grants:
        assert "DELETE" not in grant.upper(), "plumb_app must never hold DELETE"
        assert "ALL PRIVILEGES" not in grant.upper()


@pytest.mark.requirements("PL-052")
def test_rls_fails_closed_without_tenant_setting_is_documented(sql: str) -> None:
    assert "fails closed" in sql
    assert "SET LOCAL plumb.tenant_id" in sql
