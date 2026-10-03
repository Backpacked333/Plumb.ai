"""Disposable PostgreSQL cluster: real service logins, no TCP or external database."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import psycopg
import pytest

from database.bootstrap import bootstrap


@pytest.fixture(scope="session")
def cluster(tmp_path_factory: pytest.TempPathFactory) -> Iterator[dict[str, Any]]:
    configured = os.environ.get("PLUMB_PG_BIN")
    initdb = str(Path(configured) / "initdb") if configured else shutil.which("initdb")
    if not initdb or not Path(initdb).is_file():
        pytest.fail("PostgreSQL 16 is required: set PLUMB_PG_BIN to its bin directory")
    binaries = Path(initdb).parent
    version = subprocess.check_output([initdb, "--version"], text=True)
    if " 16." not in version:
        pytest.fail(f"Expected PostgreSQL 16, found {version.strip()}")
    root = tmp_path_factory.mktemp("plumb-pg")
    root.chmod(0o700)
    data = root / "data"
    with tempfile.TemporaryDirectory(prefix="plumb-pg-") as socket:
        environment = {**os.environ, "LC_ALL": "C"}
        subprocess.run(
            [initdb, "-D", str(data), "-U", "postgres", "-A", "trust", "--no-locale", "-E", "UTF8"],
            check=True, capture_output=True, text=True, env=environment,
        )
        options = f"-h '' -k {socket} -p 5432"
        subprocess.run(
            [str(binaries / "pg_ctl"), "-D", str(data), "-l", str(root / "server.log"),
             "-o", options, "-w", "start"], check=True, capture_output=True, text=True, env=environment,
        )
        connection: dict[str, Any] = {"host": socket, "port": 5432, "dbname": "postgres"}
        try:
            with psycopg.connect(**connection, user="postgres", autocommit=True) as admin:
                bootstrap(admin)
            yield connection
        finally:
            subprocess.run(
                [str(binaries / "pg_ctl"), "-D", str(data), "-m", "immediate", "-w", "stop"],
                check=True, capture_output=True, text=True,
            )


@pytest.fixture
def admin(cluster: dict[str, Any]) -> Iterator[psycopg.Connection[Any]]:
    with psycopg.connect(**cluster, user="postgres", autocommit=True) as connection:
        yield connection
