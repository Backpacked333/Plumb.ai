"""Structural and coverage tests for the production acceptance catalog.

The catalog (``acceptance/production_acceptance_catalog.yaml``) specifies the
production gates that the local reference package cannot establish. These tests
do not execute any scenario; they prove that the catalog itself satisfies the
specification's obligations:

* PL-061: the release suite covers normal, boundary, corrupted-input,
  stale/revoked-access, duplicate/reordered-event, crash-after-dispatch,
  concurrent-actor, source-edit-after-approval and adversarial-instruction
  cases, and HIGH severity blocks activation.
* Appendix B: the nine failure cases of the first customer trace (wrong client,
  ambiguous period, already-received document, corrected statement, duplicate
  request, expired permission, provider timeout after send, changed approval,
  stale source) are all specified.
* Section 21 (PL-051, PL-054): prompt injection, malicious documents, forged
  tool descriptions, confused account identity, poisoned labels, unauthorized
  recipients and exfiltration attempts are all specified.
* Section 26 (PL-003, PL-062, PL-063): milestone evidence M1..M5 is specified
  with explicit human-labor accounting.
* PL-052, PL-054, PL-058: tenant isolation, secret egress and budget
  reservation scenarios exist and are HIGH severity.
* Section 28 / Appendix C: nothing in the catalog claims local execution.

``catalog_problems`` is a pure validator over the parsed YAML; the negative tests
mutate deep copies of the real catalog and assert that each MUST / MUST NOT rule
is reported.
"""

from __future__ import annotations

import copy
import re
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

import pytest
import yaml

CATALOG_RELATIVE_PATH = Path("acceptance") / "production_acceptance_catalog.yaml"

PL061_CATEGORIES: tuple[str, ...] = (
    "normal",
    "boundary",
    "corrupted_input",
    "stale_revoked_access",
    "duplicate_reordered_events",
    "crash_after_dispatch",
    "concurrent_actors",
    "source_edit_after_approval",
    "adversarial_instruction",
)
EXTRA_CATEGORIES: tuple[str, ...] = ("isolation", "economics")
CATEGORIES: tuple[str, ...] = PL061_CATEGORIES + EXTRA_CATEGORIES

SCENARIO_DOMAINS: tuple[str, ...] = ("accounting", "industrial_rfq", "laundry", "platform")
SEVERITIES: tuple[str, ...] = ("HIGH", "MEDIUM", "LOW")
REQUIRES_VOCABULARY: tuple[str, ...] = (
    "real_adapter",
    "isolation",
    "grants",
    "deployment",
    "prospective_outcome",
    "model",
    "training",
)

APPENDIX_B_FAILURE_CASES: tuple[str, ...] = (
    "wrong client",
    "ambiguous period",
    "already-received document",
    "corrected statement",
    "duplicate request",
    "expired permission",
    "provider timeout after send",
    "changed approval",
    "stale source",
)
SECTION_21_ADVERSARIAL_CASES: tuple[str, ...] = (
    "prompt injection",
    "malicious document",
    "forged tool description",
    "confused account identity",
    "poisoned label",
    "unauthorized recipient",
    "exfiltration",
)
MILESTONE_EVIDENCE: dict[str, tuple[str, ...]] = {
    "M1": ("source event", "verified storage", "lineage"),
    "M2": ("future", "duplicate-family", "label sample"),
    "M3": ("complete", "sandbox"),
    "M4": ("canary", "receipt", "recovery drill"),
    "M5": ("replication", "fresh customer", "labor"),
}

EXPECTED_SCENARIO_COUNT = 30
MINIMUM_HIGH_SEVERITY = 10
MINIMUM_PER_DOMAIN = 3
MINIMUM_STEPS = 3
MINIMUM_STEP_LENGTH = 40

REQUIRED_FIELD_TYPES: dict[str, type | tuple[type, ...]] = {
    "id": str,
    "title": str,
    "category": str,
    "scenario": str,
    "requirements": list,
    "preconditions": list,
    "steps": list,
    "expected_outcome": str,
    "severity": str,
    "requires": list,
    "locally_executed": bool,
    "local_reference_check": (str, type(None)),
}
REQUIRED_HEADER_FIELDS: tuple[str, ...] = (
    "catalog_version",
    "generated_for_spec",
    "executed_against_production",
    "production_execution_note",
    "severity_definitions",
    "requires_definitions",
    "category_definitions",
    "scenario_domains",
    "scenarios",
)

SCENARIO_ID = re.compile(r"^PA-(\d{3})$")
PL_ID = re.compile(r"^PL-(\d{3})$")
PL_MIN, PL_MAX = 1, 63
FINDING_CODE = re.compile(r"^[A-Z][A-Z0-9_]+$")
LOCAL_TEST_NAME = re.compile(r"^test_[a-z0-9_]+$")
SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"password\s*[=:]", re.IGNORECASE),
    re.compile(r"\btoken=", re.IGNORECASE),
    re.compile(r"api[_-]?key\s*[=:]", re.IGNORECASE),
    re.compile(r"BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
)


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


def _scenario_text(scenario: Mapping[str, Any]) -> str:
    parts = [str(scenario.get("title", "")), str(scenario.get("expected_outcome", ""))]
    for key in ("preconditions", "steps"):
        value = scenario.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
    return " ".join(parts).lower()


def _header_problems(catalog: Mapping[str, Any]) -> list[str]:
    problems: list[str] = []
    for field in REQUIRED_HEADER_FIELDS:
        if field not in catalog:
            problems.append(f"header: missing field {field}")
    if catalog.get("catalog_version") != "0.2":
        problems.append("header: catalog_version must be '0.2'")
    if catalog.get("generated_for_spec") != "0.2":
        problems.append("header: generated_for_spec must be '0.2'")
    if catalog.get("executed_against_production") is not False:
        problems.append("header: executed_against_production must be false")
    note = catalog.get("production_execution_note")
    if not isinstance(note, str) or "production" not in note.lower() or "none" not in note.lower():
        problems.append("header: production_execution_note must state that none were executed against production")
    definitions = catalog.get("category_definitions")
    if not isinstance(definitions, Mapping):
        problems.append("header: category_definitions must be a mapping")
    else:
        for category in CATEGORIES:
            if not isinstance(definitions.get(category), str) or not definitions[category].strip():
                problems.append(f"header: category_definitions lacks a definition for {category}")
        for extra in sorted(set(definitions) - set(CATEGORIES)):
            problems.append(f"header: category_definitions defines unknown category {extra}")
    for key, vocabulary in (
        ("severity_definitions", SEVERITIES),
        ("requires_definitions", REQUIRES_VOCABULARY),
        ("scenario_domains", SCENARIO_DOMAINS),
    ):
        mapping = catalog.get(key)
        if not isinstance(mapping, Mapping) or set(mapping) != set(vocabulary):
            problems.append(f"header: {key} must define exactly {sorted(vocabulary)}")
    return problems


def _scenario_problems(index: int, scenario: Any) -> list[str]:
    problems: list[str] = []
    label = f"scenario[{index}]"
    if not isinstance(scenario, Mapping):
        return [f"{label}: must be a mapping"]
    label = str(scenario.get("id", label))
    for field, expected_type in REQUIRED_FIELD_TYPES.items():
        if field not in scenario:
            problems.append(f"{label}: missing field {field}")
        elif not isinstance(scenario[field], expected_type) or (
            expected_type is str and not scenario[field].strip()
        ):
            problems.append(f"{label}: field {field} has wrong type or is blank")
    for extra in sorted(set(scenario) - set(REQUIRED_FIELD_TYPES)):
        problems.append(f"{label}: unknown field {extra}")
    if problems:
        return problems

    if not SCENARIO_ID.match(scenario["id"]):
        problems.append(f"{label}: id must match PA-nnn")
    if scenario["category"] not in CATEGORIES:
        problems.append(f"{label}: unknown category {scenario['category']}")
    if scenario["scenario"] not in SCENARIO_DOMAINS:
        problems.append(f"{label}: unknown scenario domain {scenario['scenario']}")
    if scenario["severity"] not in SEVERITIES:
        problems.append(f"{label}: invalid severity {scenario['severity']}")
    if scenario["locally_executed"] is not False:
        problems.append(f"{label}: locally_executed must be false")

    requirements = scenario["requirements"]
    if not requirements:
        problems.append(f"{label}: requirements must not be empty")
    for requirement in requirements:
        match = PL_ID.match(str(requirement))
        if not match or not PL_MIN <= int(match.group(1)) <= PL_MAX:
            problems.append(f"{label}: requirement {requirement!r} is not in PL-001..PL-063")
    if len(set(requirements)) != len(requirements):
        problems.append(f"{label}: duplicate requirement ids")

    requires = scenario["requires"]
    if not requires:
        problems.append(f"{label}: requires must name at least one production prerequisite")
    for item in requires:
        if item not in REQUIRES_VOCABULARY:
            problems.append(f"{label}: unknown requires entry {item!r}")
    if len(set(requires)) != len(requires):
        problems.append(f"{label}: duplicate requires entries")

    if not scenario["preconditions"] or not all(
        isinstance(item, str) and item.strip() for item in scenario["preconditions"]
    ):
        problems.append(f"{label}: preconditions must be a non-empty list of strings")
    steps = scenario["steps"]
    if len(steps) < MINIMUM_STEPS:
        problems.append(f"{label}: at least {MINIMUM_STEPS} concrete steps are required")
    for position, step in enumerate(steps):
        if not isinstance(step, str) or len(step.strip()) < MINIMUM_STEP_LENGTH:
            problems.append(f"{label}: step {position} is not a concrete instruction")

    reference = scenario["local_reference_check"]
    if reference is not None and not (FINDING_CODE.match(reference) or LOCAL_TEST_NAME.match(reference)):
        problems.append(f"{label}: local_reference_check must be a finding code or a test_ name")
    return problems


def _coverage_problems(scenarios: list[Mapping[str, Any]]) -> list[str]:
    problems: list[str] = []
    ids = [str(scenario.get("id")) for scenario in scenarios]
    expected_ids = [f"PA-{n:03d}" for n in range(1, EXPECTED_SCENARIO_COUNT + 1)]
    if ids != expected_ids:
        problems.append(
            f"coverage: expected exactly {EXPECTED_SCENARIO_COUNT} contiguous ids PA-001..PA-{EXPECTED_SCENARIO_COUNT:03d}"
        )
    titles = [str(scenario.get("title", "")).strip().lower() for scenario in scenarios]
    for title, count in Counter(titles).items():
        if count > 1:
            problems.append(f"coverage: duplicate title {title!r}")

    categories = Counter(str(scenario.get("category")) for scenario in scenarios)
    for category in CATEGORIES:
        if categories[category] == 0:
            problems.append(f"coverage: category {category} has no scenario")

    domains = Counter(str(scenario.get("scenario")) for scenario in scenarios)
    for domain in SCENARIO_DOMAINS:
        if domains[domain] < MINIMUM_PER_DOMAIN:
            problems.append(f"coverage: domain {domain} has fewer than {MINIMUM_PER_DOMAIN} scenarios")

    high = sum(1 for scenario in scenarios if scenario.get("severity") == "HIGH")
    if high < MINIMUM_HIGH_SEVERITY:
        problems.append(f"coverage: fewer than {MINIMUM_HIGH_SEVERITY} HIGH severity scenarios")

    for keyword in APPENDIX_B_FAILURE_CASES:
        if not any(keyword in title for title in titles):
            problems.append(f"coverage: Appendix B failure case {keyword!r} missing from titles")
    for keyword in SECTION_21_ADVERSARIAL_CASES:
        if not any(keyword in title for title in titles):
            problems.append(f"coverage: section 21 adversarial case {keyword!r} missing from titles")
    for milestone, phrases in MILESTONE_EVIDENCE.items():
        matching = [
            scenario
            for scenario in scenarios
            if f"{milestone.lower()} evidence" in str(scenario.get("title", "")).lower()
        ]
        if len(matching) != 1:
            problems.append(f"coverage: exactly one '{milestone} evidence' scenario is required")
            continue
        text = _scenario_text(matching[0])
        for phrase in phrases:
            if phrase not in text:
                problems.append(f"coverage: {milestone} scenario does not mention {phrase!r}")
    return problems


def catalog_problems(catalog: Mapping[str, Any]) -> list[str]:
    """Return every rule violation in a parsed catalog; an empty list means valid."""
    problems = _header_problems(catalog)
    scenarios = catalog.get("scenarios")
    if not isinstance(scenarios, list):
        problems.append("scenarios must be a list")
        return problems
    for index, scenario in enumerate(scenarios):
        problems.extend(_scenario_problems(index, scenario))
    well_formed = [scenario for scenario in scenarios if isinstance(scenario, Mapping)]
    problems.extend(_coverage_problems(well_formed))
    return problems


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def catalog_path(repo_root: Path) -> Path:
    return repo_root / CATALOG_RELATIVE_PATH


@pytest.fixture(scope="module")
def catalog(catalog_path: Path) -> dict[str, Any]:
    with catalog_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    assert isinstance(loaded, dict)
    return loaded


@pytest.fixture(scope="module")
def scenarios(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    return catalog["scenarios"]


def _by_id(scenarios: list[dict[str, Any]], scenario_id: str) -> dict[str, Any]:
    return next(scenario for scenario in scenarios if scenario["id"] == scenario_id)


def _find_by_title(scenarios: list[dict[str, Any]], keyword: str) -> dict[str, Any]:
    matches = [scenario for scenario in scenarios if keyword in scenario["title"].lower()]
    assert len(matches) == 1, f"expected exactly one scenario titled with {keyword!r}, found {len(matches)}"
    return matches[0]


# ---------------------------------------------------------------------------
# Positive tests: the shipped catalog
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-061")
def test_catalog_is_valid(catalog: dict[str, Any]) -> None:
    assert catalog_problems(catalog) == []


@pytest.mark.requirements("PL-061")
def test_header_declares_version_spec_and_unexecuted_status(catalog: dict[str, Any]) -> None:
    assert catalog["catalog_version"] == "0.2"
    assert catalog["generated_for_spec"] == "0.2"
    assert catalog["executed_against_production"] is False
    note = catalog["production_execution_note"].lower()
    assert "none of these scenarios were executed against production" in note
    assert set(catalog["category_definitions"]) == set(CATEGORIES)
    assert set(catalog["scenario_domains"]) == set(SCENARIO_DOMAINS)
    assert set(catalog["severity_definitions"]) == set(SEVERITIES)
    assert "block" in catalog["severity_definitions"]["HIGH"].lower()
    assert "activation" in catalog["severity_definitions"]["HIGH"].lower()


@pytest.mark.requirements("PL-061")
def test_exactly_thirty_contiguous_scenario_ids(scenarios: list[dict[str, Any]]) -> None:
    assert len(scenarios) == EXPECTED_SCENARIO_COUNT
    assert [scenario["id"] for scenario in scenarios] == [f"PA-{n:03d}" for n in range(1, 31)]


@pytest.mark.requirements("PL-061")
def test_every_scenario_has_required_fields_with_types(scenarios: list[dict[str, Any]]) -> None:
    for scenario in scenarios:
        assert set(scenario) == set(REQUIRED_FIELD_TYPES), scenario["id"]
        for field, expected_type in REQUIRED_FIELD_TYPES.items():
            assert isinstance(scenario[field], expected_type), (scenario["id"], field)
        assert scenario["title"].strip() and scenario["expected_outcome"].strip(), scenario["id"]
        assert all(isinstance(item, str) and item.strip() for item in scenario["preconditions"]), scenario["id"]
        assert all(isinstance(item, str) and item.strip() for item in scenario["steps"]), scenario["id"]


@pytest.mark.requirements("PL-061")
def test_steps_are_concrete_not_prose_summaries(scenarios: list[dict[str, Any]]) -> None:
    for scenario in scenarios:
        assert len(scenario["preconditions"]) >= 1, scenario["id"]
        assert len(scenario["steps"]) >= MINIMUM_STEPS, scenario["id"]
        for step in scenario["steps"]:
            assert len(step.strip()) >= MINIMUM_STEP_LENGTH, (scenario["id"], step)
        text = _scenario_text(scenario)
        assert any(verb in text for verb in ("confirm", "observe", "inspect", "expect")), scenario["id"]


@pytest.mark.requirements("PL-061")
def test_all_nine_pl061_categories_and_both_extra_categories_present(scenarios: list[dict[str, Any]]) -> None:
    present = Counter(scenario["category"] for scenario in scenarios)
    for category in PL061_CATEGORIES:
        assert present[category] >= 1, category
    for category in EXTRA_CATEGORIES:
        assert present[category] >= 1, category
    assert set(present) <= set(CATEGORIES)


@pytest.mark.requirements("PL-061", "PL-043")
def test_appendix_b_failure_cases_are_found_by_title_keyword(scenarios: list[dict[str, Any]]) -> None:
    for keyword in APPENDIX_B_FAILURE_CASES:
        scenario = _find_by_title(scenarios, keyword)
        assert scenario["scenario"] == "accounting", keyword
        assert scenario["severity"] == "HIGH", keyword


@pytest.mark.requirements("PL-051", "PL-054", "PL-061")
def test_section_21_adversarial_cases_are_present(scenarios: list[dict[str, Any]]) -> None:
    for keyword in SECTION_21_ADVERSARIAL_CASES:
        scenario = _find_by_title(scenarios, keyword)
        assert scenario["category"] in {"adversarial_instruction", "corrupted_input", "isolation"}, keyword
    assert "PL-051" in _find_by_title(scenarios, "prompt injection")["requirements"]
    assert "PL-051" in _find_by_title(scenarios, "forged tool description")["requirements"]
    assert "PL-054" in _find_by_title(scenarios, "exfiltration")["requirements"]


@pytest.mark.requirements("PL-003", "PL-062", "PL-063")
def test_milestone_evidence_scenarios_present(scenarios: list[dict[str, Any]]) -> None:
    for milestone, phrases in MILESTONE_EVIDENCE.items():
        scenario = _find_by_title(scenarios, f"{milestone.lower()} evidence")
        text = _scenario_text(scenario)
        for phrase in phrases:
            assert phrase in text, (milestone, phrase)
    m1 = _find_by_title(scenarios, "m1 evidence")
    assert "PL-063" in m1["requirements"]
    m5 = _find_by_title(scenarios, "m5 evidence")
    assert {"PL-003", "PL-062", "PL-063"} <= set(m5["requirements"])
    assert "engineering_intervention" in _scenario_text(m5)


@pytest.mark.requirements("PL-061")
def test_all_requirement_ids_are_in_range_and_every_requirement_is_referenced(
    scenarios: list[dict[str, Any]],
) -> None:
    referenced: set[str] = set()
    for scenario in scenarios:
        assert scenario["requirements"], scenario["id"]
        assert len(set(scenario["requirements"])) == len(scenario["requirements"]), scenario["id"]
        for requirement in scenario["requirements"]:
            match = PL_ID.match(requirement)
            assert match and PL_MIN <= int(match.group(1)) <= PL_MAX, (scenario["id"], requirement)
            referenced.add(requirement)
    assert referenced == {f"PL-{n:03d}" for n in range(PL_MIN, PL_MAX + 1)}


@pytest.mark.requirements("PL-061")
def test_severity_values_valid_and_at_least_ten_high(scenarios: list[dict[str, Any]]) -> None:
    severities = Counter(scenario["severity"] for scenario in scenarios)
    assert set(severities) <= set(SEVERITIES)
    assert severities["HIGH"] >= MINIMUM_HIGH_SEVERITY


@pytest.mark.requirements("PL-061")
def test_locally_executed_is_false_everywhere(scenarios: list[dict[str, Any]]) -> None:
    for scenario in scenarios:
        assert scenario["locally_executed"] is False, scenario["id"]


@pytest.mark.requirements("PL-061")
def test_requires_uses_the_closed_vocabulary(scenarios: list[dict[str, Any]]) -> None:
    for scenario in scenarios:
        assert scenario["requires"], scenario["id"]
        assert set(scenario["requires"]) <= set(REQUIRES_VOCABULARY), scenario["id"]
        assert len(set(scenario["requires"])) == len(scenario["requires"]), scenario["id"]


@pytest.mark.requirements("PL-061")
def test_each_scenario_domain_present(scenarios: list[dict[str, Any]]) -> None:
    domains = Counter(scenario["scenario"] for scenario in scenarios)
    assert set(domains) == set(SCENARIO_DOMAINS)
    for domain in SCENARIO_DOMAINS:
        assert domains[domain] >= MINIMUM_PER_DOMAIN, domain


@pytest.mark.requirements("PL-061")
def test_local_reference_checks_name_existing_tests_or_finding_codes(
    scenarios: list[dict[str, Any]], repo_root: Path
) -> None:
    own_file = Path(__file__).resolve()
    test_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((repo_root / "tests").glob("test_*.py"))
        if path.resolve() != own_file
    )
    # A finding code must be emitted by a checker in this package; the design document alone is not enough.
    code_sources = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted((repo_root / "plumb" / "checker").glob("*.py"))
    )
    for scenario in scenarios:
        reference = scenario["local_reference_check"]
        if reference is None:
            continue
        if LOCAL_TEST_NAME.match(reference):
            assert f"def {reference}(" in test_sources, (scenario["id"], reference)
        else:
            assert FINDING_CODE.match(reference), (scenario["id"], reference)
            assert f'"{reference}"' in code_sources, (scenario["id"], reference)


@pytest.mark.requirements("PL-052")
def test_tenant_isolation_scenario_covers_every_pl052_surface(scenarios: list[dict[str, Any]]) -> None:
    scenario = _find_by_title(scenarios, "tenant isolation")
    assert scenario["category"] == "isolation"
    assert scenario["severity"] == "HIGH"
    assert "PL-052" in scenario["requirements"]
    assert "isolation" in scenario["requires"]
    text = _scenario_text(scenario)
    for surface in (
        "database",
        "object storage",
        "search",
        "cache",
        "workspace",
        "training job",
        "model route",
        "logs",
        "export",
    ):
        assert surface in text, surface
    assert "404" in text and "rls" in text


@pytest.mark.requirements("PL-058", "PL-033", "PL-055")
def test_budget_reservation_scenario_exercises_concurrent_steps(scenarios: list[dict[str, Any]]) -> None:
    scenario = _find_by_title(scenarios, "budget reservation")
    assert scenario["category"] == "economics"
    assert scenario["severity"] == "HIGH"
    assert "PL-058" in scenario["requirements"]
    text = _scenario_text(scenario)
    assert "atomic" in text and "concurrent" in text and "released" in text
    assert "submission identity" in text


@pytest.mark.requirements("PL-054")
def test_secret_egress_scenario_covers_ssrf_and_webhook_signature(scenarios: list[dict[str, Any]]) -> None:
    scenario = _find_by_title(scenarios, "secret egress")
    assert scenario["severity"] == "HIGH"
    assert "PL-054" in scenario["requirements"]
    text = _scenario_text(scenario)
    for term in ("ssrf", "signature", "replay", "allowlist", "payload"):
        assert term in text, term


@pytest.mark.requirements("PL-040", "PL-041", "PL-038")
def test_revocation_race_lease_expiry_and_schema_drift_scenarios_exist(
    scenarios: list[dict[str, Any]],
) -> None:
    race = _find_by_title(scenarios, "revocation race")
    assert race["category"] == "concurrent_actors"
    assert "receipt" in _scenario_text(race) and "remediation" in _scenario_text(race)

    lease = _find_by_title(scenarios, "lease expiry")
    assert lease["category"] == "crash_after_dispatch"
    lease_text = _scenario_text(lease)
    assert "reconcile" in lease_text and "fencing" in lease_text
    assert lease["scenario"] == "platform"

    drift = _find_by_title(scenarios, "schema drift")
    assert drift["category"] == "corrupted_input"
    drift_text = _scenario_text(drift)
    assert "quarantine" in drift_text
    assert "unaffected" in drift_text or "continues" in drift_text


@pytest.mark.requirements("PL-054")
def test_catalog_contains_no_secret_like_values(catalog_path: Path) -> None:
    text = catalog_path.read_text(encoding="utf-8")
    for pattern in SECRET_PATTERNS:
        assert pattern.search(text) is None, pattern.pattern


# ---------------------------------------------------------------------------
# Negative tests: the validator rejects catalogs that break a MUST / MUST NOT
# ---------------------------------------------------------------------------


def _mutated(catalog: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(catalog)


@pytest.mark.requirements("PL-061")
def test_validator_rejects_a_locally_executed_claim(catalog: dict[str, Any]) -> None:
    broken = _mutated(catalog)
    broken["scenarios"][4]["locally_executed"] = True
    problems = catalog_problems(broken)
    assert any("PA-005" in problem and "locally_executed" in problem for problem in problems)

    broken_header = _mutated(catalog)
    broken_header["executed_against_production"] = True
    assert any("executed_against_production" in problem for problem in catalog_problems(broken_header))


@pytest.mark.requirements("PL-061")
def test_validator_rejects_a_missing_pl061_category(catalog: dict[str, Any]) -> None:
    broken = _mutated(catalog)
    for scenario in broken["scenarios"]:
        if scenario["category"] == "crash_after_dispatch":
            scenario["category"] = "normal"
    problems = catalog_problems(broken)
    assert "coverage: category crash_after_dispatch has no scenario" in problems

    unknown = _mutated(catalog)
    unknown["scenarios"][0]["category"] = "happy_path"
    assert any("unknown category happy_path" in problem for problem in catalog_problems(unknown))


@pytest.mark.requirements("PL-061")
def test_validator_rejects_requirement_ids_outside_pl_001_to_pl_063(catalog: dict[str, Any]) -> None:
    for bad in ("PL-000", "PL-064", "PL-61", "ADR-001", 61):
        broken = _mutated(catalog)
        broken["scenarios"][2]["requirements"].append(bad)
        problems = catalog_problems(broken)
        assert any("PA-003" in problem and "not in PL-001..PL-063" in problem for problem in problems), bad

    empty = _mutated(catalog)
    empty["scenarios"][2]["requirements"] = []
    assert any("requirements must not be empty" in problem for problem in catalog_problems(empty))


@pytest.mark.requirements("PL-061")
def test_validator_rejects_wrong_count_gaps_and_duplicates(catalog: dict[str, Any]) -> None:
    extra = _mutated(catalog)
    extra["scenarios"].append(copy.deepcopy(extra["scenarios"][-1]) | {"id": "PA-031", "title": "Extra"})
    assert any("exactly 30 contiguous ids" in problem for problem in catalog_problems(extra))

    gap = _mutated(catalog)
    gap["scenarios"][10]["id"] = "PA-099"
    assert any("exactly 30 contiguous ids" in problem for problem in catalog_problems(gap))

    fewer = _mutated(catalog)
    del fewer["scenarios"][0]
    assert any("exactly 30 contiguous ids" in problem for problem in catalog_problems(fewer))

    duplicate_title = _mutated(catalog)
    duplicate_title["scenarios"][1]["title"] = duplicate_title["scenarios"][0]["title"]
    assert any("duplicate title" in problem for problem in catalog_problems(duplicate_title))


@pytest.mark.requirements("PL-061")
def test_validator_rejects_invalid_severity_requires_and_fields(catalog: dict[str, Any]) -> None:
    severity = _mutated(catalog)
    severity["scenarios"][0]["severity"] = "CRITICAL"
    assert any("invalid severity CRITICAL" in problem for problem in catalog_problems(severity))

    requires = _mutated(catalog)
    requires["scenarios"][0]["requires"] = ["real_adapter", "magic"]
    assert any("unknown requires entry 'magic'" in problem for problem in catalog_problems(requires))

    missing = _mutated(catalog)
    del missing["scenarios"][0]["expected_outcome"]
    assert any("missing field expected_outcome" in problem for problem in catalog_problems(missing))

    extra_field = _mutated(catalog)
    extra_field["scenarios"][0]["executed_by"] = "someone"
    assert any("unknown field executed_by" in problem for problem in catalog_problems(extra_field))

    wrong_type = _mutated(catalog)
    wrong_type["scenarios"][0]["steps"] = "do everything"
    assert any("field steps has wrong type" in problem for problem in catalog_problems(wrong_type))

    vague = _mutated(catalog)
    vague["scenarios"][0]["steps"] = ["run it", "check it", "done"]
    assert any("is not a concrete instruction" in problem for problem in catalog_problems(vague))

    reference = _mutated(catalog)
    reference["scenarios"][0]["local_reference_check"] = "see the ledger tests"
    assert any("local_reference_check must be" in problem for problem in catalog_problems(reference))


@pytest.mark.requirements("PL-061", "PL-043")
def test_validator_rejects_a_missing_appendix_b_or_section_21_case(catalog: dict[str, Any]) -> None:
    broken = _mutated(catalog)
    _by_id(broken["scenarios"], "PA-009")["title"] = "Mail adapter outage handling"
    problems = catalog_problems(broken)
    assert "coverage: Appendix B failure case 'provider timeout after send' missing from titles" in problems

    adversarial = _mutated(catalog)
    _by_id(adversarial["scenarios"], "PA-020")["title"] = "Hidden text in an inbound email"
    assert "coverage: section 21 adversarial case 'prompt injection' missing from titles" in catalog_problems(
        adversarial
    )


@pytest.mark.requirements("PL-063", "PL-062")
def test_validator_rejects_missing_or_hollow_milestone_evidence(catalog: dict[str, Any]) -> None:
    renamed = _mutated(catalog)
    _by_id(renamed["scenarios"], "PA-001")["title"] = "First collector goes live"
    assert "coverage: exactly one 'M1 evidence' scenario is required" in catalog_problems(renamed)

    hollow = _mutated(catalog)
    m5 = _by_id(hollow["scenarios"], "PA-027")
    m5["title"] = "M5 evidence: the next customer is deployed"
    m5["steps"] = [
        "Run the implementation for the new customer and record that it completed successfully.",
        "Compare the elapsed time with the first customer and write the result into the report.",
        "Confirm the deployment is active and the owner has been informed of the outcome.",
    ]
    m5["expected_outcome"] = "The new customer is deployed."
    m5["preconditions"] = ["A new customer exists."]
    problems = catalog_problems(hollow)
    for phrase in MILESTONE_EVIDENCE["M5"]:
        assert f"coverage: M5 scenario does not mention {phrase!r}" in problems


@pytest.mark.requirements("PL-061")
def test_validator_rejects_header_without_category_definitions_or_version(catalog: dict[str, Any]) -> None:
    no_definitions = _mutated(catalog)
    del no_definitions["category_definitions"]["economics"]
    assert any("lacks a definition for economics" in problem for problem in catalog_problems(no_definitions))

    wrong_version = _mutated(catalog)
    wrong_version["catalog_version"] = "0.1"
    assert "header: catalog_version must be '0.2'" in catalog_problems(wrong_version)

    no_note = _mutated(catalog)
    no_note["production_execution_note"] = "All scenarios passed."
    assert any("production_execution_note" in problem for problem in catalog_problems(no_note))

    too_few_high = _mutated(catalog)
    for scenario in too_few_high["scenarios"]:
        scenario["severity"] = "LOW"
    assert any("fewer than 10 HIGH" in problem for problem in catalog_problems(too_few_high))
