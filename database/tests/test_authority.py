"""Executable checks for the RC1 storage authority boundary, not API authentication."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from typing import Any

import psycopg
import pytest
from psycopg import sql

ROLES = ["plumb_control", "plumb_runtime", "plumb_verifier", "plumb_builder", "plumb_reporting"]


@pytest.fixture(autouse=True)
def seed(admin: psycopg.Connection[Any]) -> None:
    admin.execute("TRUNCATE plumb.tenants CASCADE")
    admin.execute("""
        INSERT INTO plumb.tenants (tenant_id, display_name, region, kms_key_ref)
        VALUES ('t1', 'One', 'us', 'key:one'), ('t2', 'Two', 'us', 'key:two');
        INSERT INTO plumb.principals (principal_id, tenant_id, kind)
        VALUES ('p1', 't1', 'tenant_owner'), ('p2', 't2', 'tenant_owner');
        INSERT INTO plumb.autonomy_envelopes
            (envelope_id, version, tenant_id, owner_principal_id, body, content_digest, status, expires_at)
        VALUES ('e1', 1, 't1', 'p1', '{}', 'digest:one', 'active', now() + interval '1 day'),
               ('e2', 1, 't2', 'p2', '{}', 'digest:two', 'active', now() + interval '1 day');
        INSERT INTO plumb.releases (release_id, tenant_id, manifest, manifest_digest, policy_version, state)
        VALUES ('r1', 't1', '{}', 'digest:release1', '1', 'ACTIVE'),
               ('r2', 't2', '{}', 'digest:release2', '1', 'ACTIVE');
        INSERT INTO plumb.cases (case_id, tenant_id, workflow_id, case_key, release_id, state)
        VALUES ('c1', 't1', 'w', '{}', 'r1', 'ACTIVE'), ('c2', 't2', 'w', '{}', 'r2', 'ACTIVE');
        INSERT INTO plumb.action_intents
            (intent_id, tenant_id, case_id, obligation_epoch, operation_id, provider, account_ref,
             effect_slot, logical_action_id, payload_digest, payload_ref, expected_state_versions,
             authority, retry_class, compensation_class, effect_class)
        VALUES ('i1', 't1', 'c1', 1, 'gmail.send', 'gmail', 'acct', 'slot1', 'action1', 'digest:payload',
                'ref:payload', '{}', '{}', 'never', 'none', 'external_message');
    """)


def set_tenant(connection: psycopg.Connection[Any], tenant: str) -> None:
    connection.execute("SELECT set_config('plumb.tenant_id', %s, true)", (tenant,))


def test_every_table_has_forced_rls_and_an_owner_that_cannot_login(admin: psycopg.Connection[Any]) -> None:
    rows = admin.execute("""
        SELECT c.relname, a.attnotnull, c.relrowsecurity, c.relforcerowsecurity, r.rolname, r.rolcanlogin
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_roles r ON r.oid = c.relowner
        LEFT JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = 'tenant_id' AND NOT a.attisdropped
        WHERE n.nspname = 'plumb' AND c.relkind = 'r'
    """).fetchall()
    assert len(rows) >= 40
    assert [(name, not_null, rls, forced, owner, login) for name, not_null, rls, forced, owner, login in rows
            if (not_null, rls, forced, owner, login) != (True, True, True, 'plumb_migrator', False)] == []


def test_every_foreign_key_binds_both_tenant_ids(admin: psycopg.Connection[Any]) -> None:
    missing = admin.execute("""
        SELECT c.conrelid::regclass::text, c.conname
        FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE n.nspname = 'plumb' AND c.contype = 'f' AND NOT EXISTS (
            SELECT 1 FROM unnest(c.conkey, c.confkey) AS pair(child, parent)
            JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = pair.child
            JOIN pg_attribute b ON b.attrelid = c.confrelid AND b.attnum = pair.parent
            WHERE a.attname = 'tenant_id' AND b.attname = 'tenant_id'
        )
    """).fetchall()
    assert missing == []


@pytest.mark.parametrize("role", ROLES)
def test_service_roles_are_unprivileged(cluster: dict[str, Any], role: str) -> None:
    with psycopg.connect(**cluster, user=role) as connection:
        assert connection.execute("SELECT current_user").fetchone() == (role,)
        assert connection.execute("""
            SELECT rolsuper, rolbypassrls, rolcreatedb, rolcreaterole
            FROM pg_roles WHERE rolname = current_user
        """).fetchone() == (False, False, False, False)
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            connection.execute("SET ROLE plumb_migrator")


@pytest.mark.parametrize("tenant", [None, "", "t1", "t2"])
def test_tenant_reads_fail_closed(cluster: dict[str, Any], tenant: str | None) -> None:
    with psycopg.connect(**cluster, user="plumb_control") as connection:
        if tenant is not None:
            set_tenant(connection, tenant)
        expected = [(tenant,)] if tenant else []
        assert connection.execute("SELECT tenant_id FROM plumb.autonomy_envelopes").fetchall() == expected
        assert connection.execute("SELECT tenant_id FROM plumb.cases").fetchall() == expected
        assert connection.execute("SELECT tenant_id FROM plumb.principals").fetchall() == expected


def test_cross_tenant_insert_rejected(cluster: dict[str, Any]) -> None:
    with psycopg.connect(**cluster, user="plumb_control") as connection:
        set_tenant(connection, "t1")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            connection.execute("INSERT INTO plumb.principals (principal_id, tenant_id, kind) VALUES ('bad', 't2', 'employee')")


def test_same_tenant_write_allowed_and_other_tenant_update_hidden(cluster: dict[str, Any]) -> None:
    with psycopg.connect(**cluster, user="plumb_control") as connection:
        set_tenant(connection, "t1")
        connection.execute("INSERT INTO plumb.principals (principal_id, tenant_id, kind) VALUES ('p3', 't1', 'employee')")
        assert connection.execute("UPDATE plumb.principals SET active = false WHERE tenant_id = 't2'").rowcount == 0
        assert connection.execute("SELECT count(*) FROM plumb.principals").fetchone() == (2,)


def test_transaction_tenant_does_not_leak_to_next_transaction(cluster: dict[str, Any]) -> None:
    with psycopg.connect(**cluster, user="plumb_control") as connection:
        set_tenant(connection, "t1")
        connection.commit()
        assert connection.execute("SELECT count(*) FROM plumb.cases").fetchone() == (0,)


def test_cross_tenant_reference_rejected_even_when_rls_is_bypassed(admin: psycopg.Connection[Any]) -> None:
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        admin.execute("""
            INSERT INTO plumb.cases (case_id, tenant_id, workflow_id, case_key, release_id, state)
            VALUES ('bad', 't1', 'other', '{}', 'r2', 'ACTIVE')
        """)


@pytest.mark.parametrize("role, table", [
    ("plumb_builder", "approvals"), ("plumb_builder", "builds"),
    ("plumb_builder", "build_steps"), ("plumb_runtime", "cases"),
    ("plumb_runtime", "effects"), ("plumb_runtime", "releases"),
])
def test_workers_cannot_mutate_authoritative_lifecycle(cluster: dict[str, Any], role: str, table: str) -> None:
    with psycopg.connect(**cluster, user=role) as connection:
        set_tenant(connection, "t1")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            connection.execute(sql.SQL("UPDATE plumb.{} SET tenant_id = tenant_id").format(sql.Identifier(table)))


def insert_attestation(connection: psycopg.Connection[Any], identity: str) -> None:
    connection.execute("""
        INSERT INTO plumb.verification_attestations
            (attestation_id, tenant_id, check_id, check_version, criteria_version, artifact_digests,
             environment, data_role, outcome, verifier_identity, issued_at)
        VALUES ('a1', 't1', 'check', '1', '1', ARRAY['digest:one'], 'local', 'acceptance', 'pass', %s, now())
    """, (identity,))


def test_verifier_can_attest_but_not_forge_identity(cluster: dict[str, Any]) -> None:
    with psycopg.connect(**cluster, user="plumb_verifier") as connection:
        set_tenant(connection, "t1")
        with pytest.raises(psycopg.errors.InsufficientPrivilege), connection.transaction():
            connection.execute("SELECT set_config('plumb.service_identity', 'forged', true)")
            insert_attestation(connection, "forged")
        insert_attestation(connection, "plumb_verifier")
        assert connection.execute("SELECT verifier_identity FROM plumb.verification_attestations").fetchone() == ('plumb_verifier',)


@pytest.mark.parametrize("role", ["plumb_builder", "plumb_runtime", "plumb_control"])
def test_only_verifier_can_issue_attestations(cluster: dict[str, Any], role: str) -> None:
    with psycopg.connect(**cluster, user=role) as connection:
        set_tenant(connection, "t1")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            insert_attestation(connection, role)


@pytest.mark.parametrize("role", ROLES)
def test_attestation_outcome_is_immutable_to_services(cluster: dict[str, Any], role: str) -> None:
    with psycopg.connect(**cluster, user=role) as connection:
        set_tenant(connection, "t1")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            connection.execute("UPDATE plumb.verification_attestations SET outcome = 'pass'")


def test_control_can_invalidate_but_not_issue_an_attestation(cluster: dict[str, Any]) -> None:
    with psycopg.connect(**cluster, user="plumb_verifier") as connection:
        set_tenant(connection, "t1")
        insert_attestation(connection, "plumb_verifier")
    with psycopg.connect(**cluster, user="plumb_control") as connection:
        set_tenant(connection, "t1")
        assert connection.execute("UPDATE plumb.verification_attestations SET invalidated_at = now() WHERE attestation_id = 'a1'").rowcount == 1


@pytest.mark.parametrize("table", ["billable_units", "outcome_observations", "labor_records", "evidence_events"])
def test_reporting_cannot_read_raw_rows(cluster: dict[str, Any], table: str) -> None:
    with psycopg.connect(**cluster, user="plumb_reporting") as connection:
        set_tenant(connection, "t1")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            connection.execute(sql.SQL("SELECT * FROM plumb.{}").format(sql.Identifier(table)))


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("statement", ["UPDATE plumb.audit_log SET reason = 'changed'", "DELETE FROM plumb.audit_log", "TRUNCATE plumb.audit_log"])
def test_audit_is_append_only_for_services(cluster: dict[str, Any], role: str, statement: str) -> None:
    with psycopg.connect(**cluster, user=role) as connection:
        set_tenant(connection, "t1")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            connection.execute(statement)


def test_outbox_and_state_rollback_together(cluster: dict[str, Any], admin: psycopg.Connection[Any]) -> None:
    with psycopg.connect(**cluster, user="plumb_control") as connection:
        set_tenant(connection, "t1")
        connection.execute("UPDATE plumb.cases SET state = 'WAITING_REVIEW', version = 2 WHERE case_id = 'c1'")
        connection.execute("""
            INSERT INTO plumb.outbox (tenant_id, aggregate_type, aggregate_id, aggregate_version,
                event_id, event_type, schema_version, occurred_at, correlation_id)
            VALUES ('t1', 'case', 'c1', 2, 'event1', 'case.changed', '1', now(), 'correlation1')
        """)
        connection.rollback()
    assert admin.execute("SELECT state, version FROM plumb.cases WHERE case_id = 'c1'").fetchone() == ('ACTIVE', 1)
    assert admin.execute("SELECT count(*) FROM plumb.outbox").fetchone() == (0,)


@pytest.mark.parametrize("state", ["RESERVED", "UNKNOWN", "CONFIRMED"])
def test_effect_slot_is_unique_across_concurrent_connections(cluster: dict[str, Any], state: str) -> None:
    ready = Barrier(2, timeout=10)

    def reserve(index: int) -> str:
        try:
            with psycopg.connect(**cluster, user="plumb_control") as connection:
                set_tenant(connection, "t1")
                ready.wait()
                connection.execute("""
                    INSERT INTO plumb.effects (effect_id, tenant_id, intent_id, effect_slot, state, idempotency_key)
                    VALUES (%s, 't1', 'i1', 'slot1', %s, %s)
                """, (f"effect{index}", state, f"key{index}"))
            return "inserted"
        except psycopg.errors.UniqueViolation:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(reserve, [1, 2])) == ["conflict", "inserted"]
