"""Bootstrap the RC1 schema and authority boundary into an empty database."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import psycopg

ROOT = Path(__file__).resolve().parents[1]


def bootstrap(connection: psycopg.Connection[Any]) -> None:
    """Apply roles, source migrations and hardening atomically; never reset existing data."""
    paths = [ROOT / "database/roles.sql"]
    paths.extend(sorted((ROOT / "spec/rc1/database/migrations").glob("*.sql")))
    paths.extend(sorted((ROOT / "database/migrations").glob("*.sql")))
    with connection.transaction():
        for path in paths:
            connection.execute(path.read_text())


def main() -> None:
    dsn = os.environ.get("PLUMB_DATABASE_URL")
    if not dsn:
        raise SystemExit("Set PLUMB_DATABASE_URL to an administrator connection for a new dedicated database cluster.")
    with psycopg.connect(dsn, autocommit=True) as connection:
        bootstrap(connection)
    print("Applied RC1 baseline and tenant authority hardening.")


if __name__ == "__main__":
    main()
