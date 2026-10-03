"""Package consistency (AT-004, AT-005, AT-006): every requirement traced, every traced path exists, OpenAPI and
event contracts agree with the canonical schemas and state tables."""
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
ID_RE = re.compile(r"\b(PR|SR|IC|DC|SI|AT)-\d{3}\b")
PATH_RE = re.compile(r"^[A-Za-z0-9_./-]+\.(md|py|yaml|json|csv|sql)$|^[A-Za-z0-9_./-]+/$|^(fixtures|tests|contracts|database|spec|reference|acceptance|operations|tools)(/[A-Za-z0-9_.-]+)*$")


def _rows():
    with (ROOT / "TRACEABILITY.csv").open() as f:
        return list(csv.DictReader(f))


def _defined_ids():
    ids = set()
    for line in (ROOT / "REQUIREMENTS.md").read_text().splitlines():
        if line.startswith("| ") and re.match(r"^\| (PR|SR|IC|DC|SI|AT)-\d{3} \|", line):
            ids.add(line.split("|")[1].strip())
    return ids


def test_traceability_is_current(tmp_path):
    code = (ROOT / "tools" / "gen_traceability.py").read_text().replace('out = ROOT / "TRACEABILITY.csv"', f'out = Path(r"{tmp_path}") / "t.csv"').replace("ROOT = Path(__file__).resolve().parents[1]", f'ROOT = Path(r"{ROOT}")')
    (tmp_path / "gen.py").write_text(code)
    subprocess.run([sys.executable, str(tmp_path / "gen.py")], check=True, cwd=ROOT, capture_output=True)
    assert (tmp_path / "t.csv").read_text() == (ROOT / "TRACEABILITY.csv").read_text()


def test_every_requirement_is_traced_and_every_traced_id_is_defined():
    defined = _defined_ids()
    traced = {r["requirement_id"] for r in _rows()}
    assert defined == traced, f"untraced {sorted(defined - traced)} / undefined {sorted(traced - defined)}"
    assert len(defined) >= 150


def test_referenced_ids_in_requirements_exist():
    defined = _defined_ids()
    text = (ROOT / "REQUIREMENTS.md").read_text() + (ROOT / "RECONCILIATION_REGISTER.md").read_text()
    referenced = set(m.group(0) for m in ID_RE.finditer(text))
    missing = referenced - defined
    assert not missing, f"referenced but undefined: {sorted(missing)}"


def test_traced_paths_exist():
    missing = []
    for r in _rows():
        for cell in (r["artifacts"], r["verified_by"]):
            for token in [t.strip() for t in cell.split(";")]:
                tok = token.split("#")[0].strip()
                if tok and PATH_RE.match(tok) and not (ROOT / tok).exists():
                    missing.append((r["requirement_id"], tok))
    assert not missing, missing


def test_ids_referenced_in_reference_code_are_defined():
    defined = _defined_ids()
    referenced = set()
    for p in list((ROOT / "reference").rglob("*.py")) + list((ROOT / "contracts" / "canonical-models").rglob("*.py")) + list((ROOT / "tests").rglob("*.py")):
        referenced |= {m.group(0) for m in ID_RE.finditer(p.read_text())}
    missing = referenced - defined
    assert not missing, f"code references undefined requirement ids: {sorted(missing)}"


def test_openapi_canonical_refs_and_conventions():
    from openapi_spec_validator import validate
    spec = yaml.safe_load((ROOT / "contracts" / "openapi.yaml").read_text())
    validate(spec)
    index = json.loads((ROOT / "contracts" / "generated-json-schema" / "index.json").read_text())

    def walk(node):
        if isinstance(node, dict):
            if "x-plumb-canonical-model" in node:
                assert node["x-plumb-canonical-model"] in index, node["x-plumb-canonical-model"]
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(spec)
    for path, item in spec["paths"].items():
        for method, op in item.items():
            if method != "post":
                continue
            params = [p.get("$ref", "") + p.get("name", "") for p in op.get("parameters", [])]
            is_action = ":" in path
            assert is_action or any("idempotencyKey" in p for p in params), f"{path} POST without Idempotency-Key"
            if is_action and "{" in path.split(":")[0] and not path.endswith(":decide") and not path.endswith(":revoke") and not path.endswith(":reconcile"):
                assert any("ifMatch" in p for p in params), f"{path} state change without If-Match"
            if "202" in op["responses"]:
                assert "Accepted" in json.dumps(op["responses"]["202"])


def test_event_contracts_reference_known_aggregates_and_tables():
    ev = yaml.safe_load((ROOT / "contracts" / "event-contracts" / "events.yaml").read_text())
    aggregates = set()
    for f in (ROOT / "contracts" / "state-machines").glob("*.yaml"):
        aggregates.add(yaml.safe_load(f.read_text())["aggregate"])
    aggregates |= {"evidence_event", "grant"}
    for e in ev["event_types"]:
        assert e["aggregate"] in aggregates, e
        assert e["consumers"], e
    sql = "\n".join(p.read_text() for p in (ROOT / "database" / "migrations").glob("*.sql"))
    for table in ("outbox", "outbox_dead_letter", "consumer_offsets", "effects", "receipts", "verification_attestations", "billable_units", "labor_records"):
        assert f"CREATE TABLE {table} (" in sql, table
    assert "WHERE state NOT IN ('CANCELLED','SUPERSEDED','FAILED_FINAL')" in sql  # one live effect per slot
