"""Traceability tests for the product-management documents in ``product/``.

The product documents (brief, strategy decisions, MVP scope, roadmap, backlog,
metrics, risks, market and design-partner program) are derived from the
normative specification and the production acceptance catalog. These tests do
not judge the product strategy; they keep the documents traceable to the
artifacts they cite:

* every requirement (PL-xxx), ADR (ADR-xxx) and acceptance scenario (PA-xxx)
  id named in a product document exists in ``spec/requirements_index.json`` or
  ``acceptance/production_acceptance_catalog.yaml``;
* the backlog traces every one of the 63 requirements (section 26, PL-063:
  the delivery sequence must account for the whole specification);
* the roadmap assigns every one of the 30 acceptance scenarios to a phase
  (PL-061, PL-063);
* proposed scenarios use the separate ``PA-Pnn`` form and are defined in the
  roadmap, so they cannot be mistaken for catalog scenarios;
* the index links every document and every relative link resolves.

``product_doc_problems`` is a pure validator over the document texts; the
negative tests mutate copies of the real documents and assert that each rule
is reported.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Mapping

import pytest
import yaml

from tests.conftest import REPO_ROOT

PRODUCT_DIR = REPO_ROOT / "product"
INDEX_DOC = "README.md"
BACKLOG_DOC = "05-backlog.md"
ROADMAP_DOC = "04-roadmap.md"
EXPECTED_DOCS: tuple[str, ...] = (
    INDEX_DOC,
    "01-product-brief.md",
    "02-strategy-decisions.md",
    "03-mvp-scope.md",
    ROADMAP_DOC,
    BACKLOG_DOC,
    "06-metrics.md",
    "07-risks-and-assumptions.md",
    "08-market-and-positioning.md",
    "09-design-partner-program.md",
)

REQUIREMENT_ID = re.compile(r"\bPL-\d{3}\b")
ADR_ID = re.compile(r"\bADR-\d{3}\b")
SCENARIO_ID = re.compile(r"\bPA-\d{3}\b")
PROPOSED_SCENARIO_ID = re.compile(r"\bPA-P\d{2}\b")
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
EXTERNAL_LINK = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|#)", re.IGNORECASE)
STATUS_LINE = re.compile(r"^\W*Status\W+Draft", re.MULTILINE)


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


def _unknown_ids(name: str, text: str, pattern: re.Pattern[str], known: set[str], label: str) -> list[str]:
    return [f"{name}: unknown {label} {found}" for found in sorted(set(pattern.findall(text)) - known)]


def _link_problems(name: str, text: str, base: Path) -> list[str]:
    problems: list[str] = []
    for target in MARKDOWN_LINK.findall(text):
        if EXTERNAL_LINK.match(target):
            continue
        path = target.split("#", 1)[0]
        if path and not (base / path).exists():
            problems.append(f"{name}: broken link {target}")
    return problems


def product_doc_problems(
    docs: Mapping[str, str],
    *,
    requirement_ids: set[str],
    adr_ids: set[str],
    scenario_ids: set[str],
    base: Path,
) -> list[str]:
    """Return every traceability problem in ``docs`` (file name -> Markdown text)."""
    problems = [f"missing document {name}" for name in EXPECTED_DOCS if name not in docs]
    roadmap = docs.get(ROADMAP_DOC, "")
    defined_proposals = set(PROPOSED_SCENARIO_ID.findall(roadmap))
    for name, text in sorted(docs.items()):
        if not text.startswith("# "):
            problems.append(f"{name}: must start with a level-1 heading")
        if name != INDEX_DOC and not STATUS_LINE.search(text):
            problems.append(f"{name}: missing 'Status: Draft' line")
        problems += _unknown_ids(name, text, REQUIREMENT_ID, requirement_ids, "requirement")
        problems += _unknown_ids(name, text, ADR_ID, adr_ids, "ADR")
        problems += _unknown_ids(name, text, SCENARIO_ID, scenario_ids, "acceptance scenario")
        for proposal in sorted(set(PROPOSED_SCENARIO_ID.findall(text)) - defined_proposals):
            problems.append(f"{name}: proposed scenario {proposal} is not defined in {ROADMAP_DOC}")
        problems += _link_problems(name, text, base)
    if BACKLOG_DOC in docs:
        traced = set(REQUIREMENT_ID.findall(docs[BACKLOG_DOC]))
        problems += [f"{BACKLOG_DOC}: requirement {req} is not traced" for req in sorted(requirement_ids - traced)]
    if ROADMAP_DOC in docs:
        planned = set(SCENARIO_ID.findall(roadmap))
        problems += [f"{ROADMAP_DOC}: scenario {sid} is not assigned" for sid in sorted(scenario_ids - planned)]
    if INDEX_DOC in docs:
        linked = {target.split("#", 1)[0] for target in MARKDOWN_LINK.findall(docs[INDEX_DOC])}
        problems += [f"{INDEX_DOC}: does not link {name}" for name in EXPECTED_DOCS if name != INDEX_DOC and name not in linked]
    return problems


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def docs() -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(PRODUCT_DIR.glob("*.md"))}


@pytest.fixture(scope="module")
def known_ids() -> dict[str, set[str]]:
    index = json.loads((REPO_ROOT / "spec" / "requirements_index.json").read_text(encoding="utf-8"))
    catalog = yaml.safe_load((REPO_ROOT / "acceptance" / "production_acceptance_catalog.yaml").read_text(encoding="utf-8"))
    return {
        "requirement_ids": {req["id"] for req in index["requirements"]},
        "adr_ids": {adr["id"] for adr in index["adrs"]},
        "scenario_ids": {scenario["id"] for scenario in catalog["scenarios"]},
    }


def problems_for(docs: Mapping[str, str], known_ids: dict[str, set[str]], base: Path = PRODUCT_DIR) -> list[str]:
    return product_doc_problems(docs, base=base, **known_ids)


# ---------------------------------------------------------------------------
# The delivered documents
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-061", "PL-063")
def test_product_documents_are_traceable(docs: dict[str, str], known_ids: dict[str, set[str]]) -> None:
    assert problems_for(docs, known_ids) == []


@pytest.mark.requirements("PL-063")
def test_identifier_sets_match_the_specification(known_ids: dict[str, set[str]]) -> None:
    assert len(known_ids["requirement_ids"]) == 63
    assert len(known_ids["adr_ids"]) == 10
    assert len(known_ids["scenario_ids"]) == 30


@pytest.mark.requirements("PL-063")
def test_every_expected_document_exists_and_nothing_else(docs: dict[str, str]) -> None:
    assert sorted(docs) == sorted(EXPECTED_DOCS)


# ---------------------------------------------------------------------------
# Negative tests: each rule is reported
# ---------------------------------------------------------------------------


def _with(docs: Mapping[str, str], name: str, text: str) -> dict[str, str]:
    mutated = dict(docs)
    mutated[name] = text
    return mutated


@pytest.mark.requirements("PL-063")
def test_unknown_requirement_adr_and_scenario_ids_are_reported(docs: dict[str, str], known_ids: dict[str, set[str]]) -> None:
    text = docs["01-product-brief.md"] + "\nSee PL-064, ADR-011 and PA-031.\n"
    problems = problems_for(_with(docs, "01-product-brief.md", text), known_ids)
    assert "01-product-brief.md: unknown requirement PL-064" in problems
    assert "01-product-brief.md: unknown ADR ADR-011" in problems
    assert "01-product-brief.md: unknown acceptance scenario PA-031" in problems


@pytest.mark.requirements("PL-063")
def test_untraced_requirement_is_reported(docs: dict[str, str], known_ids: dict[str, set[str]]) -> None:
    text = re.sub(r"\bPL-049\b", "PL-0xx", docs[BACKLOG_DOC])
    problems = problems_for(_with(docs, BACKLOG_DOC, text), known_ids)
    assert f"{BACKLOG_DOC}: requirement PL-049 is not traced" in problems


@pytest.mark.requirements("PL-061", "PL-063")
def test_unassigned_scenario_is_reported(docs: dict[str, str], known_ids: dict[str, set[str]]) -> None:
    text = re.sub(r"\bPA-030\b", "PA-0xx", docs[ROADMAP_DOC])
    problems = problems_for(_with(docs, ROADMAP_DOC, text), known_ids)
    assert f"{ROADMAP_DOC}: scenario PA-030 is not assigned" in problems


@pytest.mark.requirements("PL-061")
def test_undefined_proposed_scenario_is_reported(docs: dict[str, str], known_ids: dict[str, set[str]]) -> None:
    text = docs["03-mvp-scope.md"] + "\nSee PA-P99.\n"
    problems = problems_for(_with(docs, "03-mvp-scope.md", text), known_ids)
    assert f"03-mvp-scope.md: proposed scenario PA-P99 is not defined in {ROADMAP_DOC}" in problems


@pytest.mark.requirements("PL-063")
def test_broken_relative_link_is_reported_and_external_links_are_ignored(
    docs: dict[str, str], known_ids: dict[str, set[str]]
) -> None:
    text = docs["06-metrics.md"] + "\n[gone](10-missing.md) [web](https://example.org/x) [anchor](#metrics)\n"
    problems = problems_for(_with(docs, "06-metrics.md", text), known_ids)
    assert problems == ["06-metrics.md: broken link 10-missing.md"]


@pytest.mark.requirements("PL-063")
def test_missing_document_status_and_index_link_are_reported(docs: dict[str, str], known_ids: dict[str, set[str]]) -> None:
    mutated = {name: text for name, text in docs.items() if name != "09-design-partner-program.md"}
    mutated[INDEX_DOC] = docs[INDEX_DOC].replace("(07-risks-and-assumptions.md)", "(07-risks-and-assumptions.md#x)")
    mutated[INDEX_DOC] = re.sub(r"\]\(08-market-and-positioning\.md[^)]*\)", "]()", mutated[INDEX_DOC])
    mutated["06-metrics.md"] = re.sub(r"Status(\W+)Draft", r"State\1Draft", docs["06-metrics.md"])
    problems = problems_for(mutated, known_ids)
    assert "missing document 09-design-partner-program.md" in problems
    assert f"{INDEX_DOC}: does not link 08-market-and-positioning.md" in problems
    assert f"{INDEX_DOC}: does not link 07-risks-and-assumptions.md" not in problems
    assert "06-metrics.md: missing 'Status: Draft' line" in problems
