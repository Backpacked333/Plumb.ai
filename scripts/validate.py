#!/usr/bin/env python3
"""Run every local check of the Plumb reference package and write the evidence.

Outputs
-------
VALIDATION_REPORT.md
    Executed checks and their results, the requirement coverage matrix built
    from ``@pytest.mark.requirements`` markers, and the explicit list of checks
    that are *not* executed locally (specification Appendix C).
MANIFEST.json
    SHA-256 digest and size of every delivered file.

Usage::

    python3 scripts/validate.py            # run everything, write both files
    python3 scripts/validate.py --no-write # run everything, print summary only

The script executes nothing outside this repository: no network, no provider,
no database other than the SQLite files the tests create under pytest's
tmp_path.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import platform
import re
import subprocess
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402
import pydantic  # noqa: E402
import yaml  # noqa: E402

REQ_PATTERN = re.compile(r"^PL-\d{3}$")

TEXT_PIN_FILES = {"test_requirements_index.py"}
"""Test files whose requirement markers pin specification text rather than enforce behaviour."""

ARTIFACT_INSPECTION_FILES = {
    "test_openapi.py",
    "test_sql_design.py",
    "test_schemas.py",
    "test_contract_registry.py",
    "test_acceptance_catalog.py",
    "test_product_docs.py",
}
"""Test files that inspect a delivered artifact (the OpenAPI document, the SQL design, the generated
schemas, the contract registry, the acceptance catalog) rather than exercise contract, checker,
ledger or state-machine behaviour. Their markers are reported in their own column so that
"locally tested" means a behaviour was executed."""

NOT_EXECUTED = [
    "Live API or connector calls",
    "Authentication/security integration tests",
    "PostgreSQL migration execution and role/grant review (sql/001_initial_design.sql is a design migration)",
    "Full OpenAPI and JSON Schema standards conformance beyond the local validator",
    "Cloud sandbox isolation, container signing, network policy and cloud IAM",
    "Model training or serving",
    "Live budget accounting against a provider",
    "Real external effects or distributed concurrency (the SQLite ledger is a single-process simulation)",
    "Production deployments and rollout stages",
    "Customer outcome measurements, label quality, source rights and business value",
]


class _Collector:
    """In-process pytest plugin recording outcomes and requirement markers."""

    def __init__(self) -> None:
        self.requirements: dict[str, set[str]] = defaultdict(set)
        self.text_pins: dict[str, set[str]] = defaultdict(set)
        self.inspections: dict[str, set[str]] = defaultdict(set)
        self.outcomes: dict[str, str] = {}
        self.per_file: dict[str, int] = defaultdict(int)
        self.unmarked: list[str] = []

    def pytest_collection_modifyitems(self, session, config, items):  # noqa: ANN001
        for item in items:
            ids: set[str] = set()
            for marker in item.iter_markers(name="requirements"):
                for value in marker.args:
                    if REQ_PATTERN.match(str(value)):
                        ids.add(str(value))
            if not ids:
                self.unmarked.append(item.nodeid)
            file_part = item.nodeid.split("::", 1)[0]
            # Tests in TEXT_PIN_FILES pin the normative wording of a requirement and tests in
            # ARTIFACT_INSPECTION_FILES inspect a delivered artifact; neither exercises the
            # requirement's behaviour, so both are reported in their own matrix columns.
            file_name = Path(file_part).name
            if file_name in TEXT_PIN_FILES:
                target = self.text_pins
            elif file_name in ARTIFACT_INSPECTION_FILES:
                target = self.inspections
            else:
                target = self.requirements
            for req in ids:
                target[req].add(item.nodeid)
            self.per_file[file_part] += 1

    def pytest_runtest_logreport(self, report):  # noqa: ANN001
        if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
            self.outcomes[report.nodeid] = report.outcome


def run_pytest() -> tuple[int, _Collector]:
    collector = _Collector()
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = pytest.main(["-q", "-p", "no:cacheprovider", str(REPO_ROOT / "tests")], plugins=[collector])
    collector.raw_output = buffer.getvalue()  # type: ignore[attr-defined]
    return int(code), collector


def run_subprocess(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def check_fixture_plans() -> list[dict]:
    from plumb.checker.plan_checker import check_plan
    from plumb.contracts.build_plan import BuildPlan
    from plumb.contracts.envelope import AutonomyEnvelope
    from plumb.registry.registry import CapabilityRegistry

    registry = CapabilityRegistry.default()
    results = []
    for plan_path in sorted((REPO_ROOT / "fixtures" / "plans").glob("*.json")):
        env_path = REPO_ROOT / "fixtures" / "envelopes" / plan_path.name
        plan = BuildPlan.model_validate_json(plan_path.read_text(encoding="utf-8"))
        envelope = AutonomyEnvelope.model_validate_json(env_path.read_text(encoding="utf-8"))
        report = check_plan(plan, envelope, registry)
        results.append(
            {
                "plan": plan_path.name,
                "steps": len(plan.steps),
                "ok": report.ok,
                "findings": len(report.findings),
                "topological_order_complete": bool(
                    report.topological_order and len(report.topological_order) == len(plan.steps)
                ),
            }
        )
    return results


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest() -> dict:
    skip_dirs = {".git", "__pycache__", ".pytest_cache", ".venv", "build", "dist"}
    files = []
    for path in sorted(REPO_ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(REPO_ROOT)
        if any(part in skip_dirs for part in rel.parts) or rel.name == "MANIFEST.json":
            continue
        if rel.suffix in {".pyc", ".sqlite3", ".db"}:
            continue
        files.append({"path": rel.as_posix(), "sha256": sha256_file(path), "bytes": path.stat().st_size})
    return {
        "package": "plumb-reference",
        "spec_version": "0.2",
        "digest_algorithm": "sha256",
        "file_count": len(files),
        "files": files,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-write", action="store_true", help="do not write VALIDATION_REPORT.md / MANIFEST.json")
    args = parser.parse_args(argv)

    started = datetime.now(timezone.utc)
    env = {
        "python": platform.python_version(),
        "pydantic": pydantic.VERSION,
        "pytest": pytest.__version__,
        "platform": platform.platform(),
    }

    # 1. Tests ---------------------------------------------------------------
    pytest_code, collector = run_pytest()
    outcomes = collector.outcomes
    passed = sum(1 for o in outcomes.values() if o == "passed")
    failed = sum(1 for o in outcomes.values() if o == "failed")
    skipped = sum(1 for o in outcomes.values() if o == "skipped")

    # 2. Schema generation check --------------------------------------------
    schema_code, schema_out = run_subprocess([sys.executable, "-m", "plumb.schemas_tool.generate", "--check"])
    top_level_schemas = sorted(p.name for p in (REPO_ROOT / "schemas").glob("*.json") if p.name != "index.json")
    supporting_schemas = sorted(p.name for p in (REPO_ROOT / "schemas" / "supporting").glob("*.json"))

    # 3. OpenAPI -------------------------------------------------------------
    openapi_mod = load_module(REPO_ROOT / "api" / "validate_openapi.py", "validate_openapi")
    openapi_result = openapi_mod.validate_document(REPO_ROOT / "api" / "openapi.yaml")

    # 4. Requirements index --------------------------------------------------
    index = json.loads((REPO_ROOT / "spec" / "requirements_index.json").read_text(encoding="utf-8"))
    requirements = index["requirements"]
    adrs = index.get("adrs", [])

    # 5. Acceptance catalog --------------------------------------------------
    catalog = yaml.safe_load((REPO_ROOT / "acceptance" / "production_acceptance_catalog.yaml").read_text(encoding="utf-8"))
    scenarios = catalog["scenarios"]
    acceptance_by_req: dict[str, list[str]] = defaultdict(list)
    for scenario in scenarios:
        for req in scenario.get("requirements", []):
            acceptance_by_req[req].append(scenario["id"])

    # 6. Fixture plans -------------------------------------------------------
    fixture_results = check_fixture_plans()

    # 7. Registry ------------------------------------------------------------
    from plumb.registry.registry import CapabilityRegistry

    registry = CapabilityRegistry.default()
    step_types = sorted(registry.step_types())

    overall_ok = (
        pytest_code == 0
        and failed == 0
        and schema_code == 0
        and openapi_result.get("spec_valid")
        and not openapi_result.get("unresolved_refs")
        and all(r["ok"] for r in fixture_results)
        and len(requirements) == 63
        and len(scenarios) == 30
        and len(top_level_schemas) == 17
    )

    covered = sorted(r for r in collector.requirements if REQ_PATTERN.match(r))
    all_ids = [r["id"] for r in requirements]
    uncovered = [r for r in all_ids if r not in collector.requirements]
    inspected_only = [r for r in uncovered if r in collector.inspections]

    finished = datetime.now(timezone.utc)

    # Report -----------------------------------------------------------------
    lines: list[str] = []
    lines.append("# Validation report\n")
    lines.append(
        "Plumb Autonomous Implementation System, reference package for specification v0.2 "
        "(October 2, 2026). Generated by `python3 scripts/validate.py`.\n"
    )
    lines.append(f"Run started {started.isoformat(timespec='seconds')}, finished {finished.isoformat(timespec='seconds')}.\n")
    lines.append(f"**Overall local result: {'PASS' if overall_ok else 'FAIL'}.**\n")
    lines.append("## Tested environment\n")
    lines.append("| Component | Version |\n|---|---|")
    for key, value in env.items():
        lines.append(f"| {key} | {value} |")
    lines.append("")
    lines.append("## Executed checks\n")
    lines.append("| Check | Executed result |\n|---|---|")
    lines.append(f"| Local contract and failure tests | {passed} passed; {failed} failed; {skipped} skipped (pytest exit code {pytest_code}) |")
    lines.append(f"| Top-level contract schemas | {len(top_level_schemas)} generated; generation check exit code {schema_code} ({'matches' if schema_code == 0 else 'DRIFT'}) |")
    lines.append(f"| Supporting schemas | {len(supporting_schemas)} generated |")
    lines.append(f"| API interface | {openapi_result.get('operations')} proposed operations; no running API server; validator {'valid' if openapi_result.get('spec_valid') else 'INVALID'} |")
    lines.append(f"| Local schema/API references | {openapi_result.get('resolved_refs')} resolved; {len(openapi_result.get('unresolved_refs') or [])} unresolved |")
    lines.append(
        "| Synthetic build plans | "
        + "; ".join(f"{r['plan'].removesuffix('.json')} ({r['steps']} steps, {'validated' if r['ok'] else 'FAILED'})" for r in fixture_results)
        + " |"
    )
    lines.append(f"| Capability registry | {len(step_types)} step types |")
    lines.append(f"| Normative requirements | {len(requirements)} indexed requirements; {len(adrs)} ADRs |")
    lines.append(f"| Production acceptance | {len(scenarios)} scenarios specified; none run against production |")
    lines.append(f"| Requirements with at least one local behavioural test | {len(covered)} of {len(all_ids)} |")
    lines.append(f"| Requirements covered only by artifact-inspection tests | {len(inspected_only)} |")
    lines.append("")
    lines.append("## Commands executed\n")
    lines.append("```")
    lines.append("python3 -m pytest -q")
    lines.append("python3 -m plumb.schemas_tool.generate --check")
    lines.append("python3 api/validate_openapi.py api/openapi.yaml --json")
    lines.append("python3 -m plumb.checker.cli plan fixtures/plans/<scenario>.json fixtures/envelopes/<scenario>.json")
    lines.append("```\n")
    lines.append("## Tests per file\n")
    lines.append("| Test file | Tests |\n|---|---|")
    for file, count in sorted(collector.per_file.items()):
        lines.append(f"| {file} | {count} |")
    lines.append("")
    if collector.unmarked:
        lines.append("Tests without a requirements marker:\n")
        for node in collector.unmarked:
            lines.append(f"- `{node}`")
        lines.append("")
    lines.append("## Requirement coverage matrix\n")
    lines.append(
        "A requirement is *locally tested* when at least one behavioural test carries its marker: a test that "
        "exercises a reference contract, checker, ledger or state machine. Tests in "
        "`tests/test_requirements_index.py` only pin the normative wording, and tests in "
        + ", ".join(f"`tests/{name}`" for name in sorted(ARTIFACT_INSPECTION_FILES))
        + " only inspect a delivered artifact (the OpenAPI document, the SQL design, the generated schemas, "
        "the registry, the acceptance catalog, the product documents); both are counted in their own columns and never make a "
        "requirement *locally tested*. A local test exercises the reference package, not the production "
        "behaviour; the acceptance column lists production acceptance scenarios that specify the real test. "
        "Requirements with neither are enforced only by the production gates named in the specification.\n"
    )
    lines.append(
        "| Requirement | Section | Local behavioural tests | Artifact-inspection tests | Text-pinning tests | Acceptance scenarios | Status |\n|---|---|---|---|---|---|---|"
    )
    for req in requirements:
        rid = req["id"]
        tests = sorted(collector.requirements.get(rid, set()))
        inspections = sorted(collector.inspections.get(rid, set()))
        pins = sorted(collector.text_pins.get(rid, set()))
        accept = sorted(acceptance_by_req.get(rid, []))
        if tests and accept:
            status = "locally tested + production scenario"
        elif tests:
            status = "locally tested"
        elif inspections and accept:
            status = "artifact inspected + production scenario"
        elif inspections:
            status = "artifact inspected only"
        elif accept:
            status = "production scenario only"
        else:
            status = "production gate only (no local check)"
        lines.append(
            f"| {rid} | {req['section']} | {len(tests)} | {len(inspections)} | {len(pins)} | {', '.join(accept) if accept else '-'} | {status} |"
        )
    lines.append("")
    if uncovered:
        lines.append("Requirements without a local behavioural test:\n")
        for rid in uncovered:
            note = " (artifact-inspection tests only)" if rid in inspected_only else ""
            lines.append(f"- {rid}{note}")
        lines.append("")
    lines.append("## Not executed locally\n")
    lines.append(
        "The following remain production gates. Passing the local tests does not validate "
        "Plumb's models, business outcomes, tenant security, cloud isolation or third-party integrations.\n"
    )
    for item in NOT_EXECUTED:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## OpenAPI validator output\n")
    lines.append("```json")
    lines.append(json.dumps({k: v for k, v in openapi_result.items() if k != "errors"}, indent=2, sort_keys=True))
    lines.append("```\n")
    if openapi_result.get("errors"):
        lines.append("Validator errors:\n")
        for err in openapi_result["errors"]:
            lines.append(f"- {err}")
        lines.append("")
    if schema_out:
        lines.append("## Schema generation check output\n")
        lines.append("```")
        lines.append(schema_out[-4000:])
        lines.append("```\n")
    if failed:
        lines.append("## Pytest output (failures)\n")
        lines.append("```")
        lines.append(getattr(collector, "raw_output", "")[-12000:])
        lines.append("```\n")

    report = "\n".join(lines)

    summary = {
        "overall_ok": overall_ok,
        "tests": {"passed": passed, "failed": failed, "skipped": skipped},
        "top_level_schemas": len(top_level_schemas),
        "supporting_schemas": len(supporting_schemas),
        "openapi_operations": openapi_result.get("operations"),
        "resolved_refs": openapi_result.get("resolved_refs"),
        "requirements": len(requirements),
        "adrs": len(adrs),
        "scenarios": len(scenarios),
        "registry_step_types": len(step_types),
        "fixture_plans": fixture_results,
        "requirements_locally_tested": len(covered),
        "requirements_without_local_test": uncovered,
        "requirements_inspected_only": inspected_only,
        "environment": env,
    }

    if not args.no_write:
        (REPO_ROOT / "VALIDATION_REPORT.md").write_text(report, encoding="utf-8")
        manifest = build_manifest()
        (REPO_ROOT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        summary["manifest_files"] = manifest["file_count"]

    print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
