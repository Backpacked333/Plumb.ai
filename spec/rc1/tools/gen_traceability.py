"""Generate TRACEABILITY.csv from the requirement tables in REQUIREMENTS.md (single source of truth).
Run: python tools/gen_traceability.py
Columns: requirement_id, category, subsystem, sources, artifacts, verified_by
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID_RE = re.compile(r"^(PR|SR|IC|DC|SI|AT)-\d{3}$")
CATEGORY = {"PR": "product", "SR": "system", "IC": "integration_contract", "DC": "data_contract", "SI": "security_invariant", "AT": "acceptance_test"}


def rows():
    for line in (ROOT / "REQUIREMENTS.md").read_text().splitlines():
        if not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 6 or not ID_RE.match(cells[0]):
            continue
        rid, statement, subsystem, sources, artifacts, verified = cells
        yield {
            "requirement_id": rid,
            "category": CATEGORY[rid[:2]],
            "subsystem": subsystem,
            "sources": sources,
            "artifacts": artifacts,
            "verified_by": verified,
        }


def main():
    out = ROOT / "TRACEABILITY.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["requirement_id", "category", "subsystem", "sources", "artifacts", "verified_by"])
        w.writeheader()
        n = 0
        for r in rows():
            w.writerow(r)
            n += 1
    print(f"wrote {n} rows to {out}")


if __name__ == "__main__":
    main()
