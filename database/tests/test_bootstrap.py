"""Bootstrap provenance and non-destructive failure behavior."""

import hashlib
import json
from pathlib import Path
from typing import Any

import psycopg
import pytest

from database.bootstrap import bootstrap


def test_rc1_snapshot_is_unchanged() -> None:
    root = Path(__file__).resolve().parents[2] / "spec/rc1"
    manifest = json.loads((root / "MANIFEST.json").read_text())
    assert len(manifest["files"]) == manifest["file_count"] == 165
    for name, metadata in manifest["files"].items():
        content = (root / name).read_bytes()
        assert hashlib.sha256(content).hexdigest() == metadata["sha256"], name
        assert len(content) == metadata["bytes"], name


def test_bootstrap_refuses_existing_roles_without_resetting_data(admin: psycopg.Connection[Any]) -> None:
    before = admin.execute("SELECT count(*) FROM plumb.tenants").fetchone()
    with pytest.raises(psycopg.errors.DuplicateObject):
        bootstrap(admin)
    assert admin.execute("SELECT count(*) FROM plumb.tenants").fetchone() == before
