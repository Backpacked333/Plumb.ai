"""Shared pytest configuration for the Plumb reference package.

Every test declares the specification requirements it exercises with
``@pytest.mark.requirements("PL-014", "PL-015")``. ``scripts/validate.py``
collects these markers to build the requirement coverage matrix in
``VALIDATION_REPORT.md``; a requirement without a marker is reported as *not
locally enforced*.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "fixtures"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "requirements(*ids): specification requirement ids (PL-xxx) exercised by the test",
    )


def load_fixture(relative_path: str) -> Any:
    """Load a JSON fixture relative to the ``fixtures/`` directory."""
    path = FIXTURES_DIR / relative_path
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR
