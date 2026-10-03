"""Generate the committed JSON Schemas of the Plumb contracts (design section 1).

Usage::

    python -m plumb.schemas_tool.generate [--out schemas] [--check]

Without ``--check`` the tool writes one JSON Schema (draft 2020-12, Pydantic
``mode="validation"``) per contract:

* ``<out>/<ContractName>.json`` for the 17 top-level contracts of
  :data:`plumb.contracts.TOP_LEVEL_CONTRACTS`;
* ``<out>/supporting/<Name>.json`` for the 5 supporting contracts of
  :data:`plumb.contracts.SUPPORTING_CONTRACTS`;
* ``<out>/index.json`` listing every schema with its relative path and the
  SHA-256 digest of the file as written.

Every file is rendered deterministically (sorted keys, two-space indent,
trailing newline) so that a committed schema can be compared byte for byte
with fresh generation. ``--check`` performs that comparison and exits ``1`` on
any stale, missing or unexpected file; this is how the test-suite and
``scripts/validate.py`` prove that the committed schemas match the models
(specification section 28: the delivered artifacts are reproducible from the
contracts, PL-004 .. PL-047 as cited by the individual contract modules).
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from plumb import SPEC_VERSION
from plumb.contracts import SUPPORTING_CONTRACTS, TOP_LEVEL_CONTRACTS, pinned_kind

SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
"""JSON Schema dialect Pydantic v2 emits; declared explicitly on every file."""

ID_BASE = f"https://plumb.example/schemas/{SPEC_VERSION}/"
"""Prefix of every ``$id``; the remainder is the file's path relative to the output directory."""

SUPPORTING_DIR = "supporting"
INDEX_FILE = "index.json"
DEFAULT_OUT = Path(__file__).resolve().parents[2] / "schemas"

EXIT_OK = 0
EXIT_DRIFT = 1


def first_docstring_line(model: type[BaseModel]) -> str:
    """The first line of the class docstring, used as the schema ``description``."""
    doc = inspect.cleandoc(model.__doc__ or "")
    for line in doc.splitlines():
        if line.strip():
            return line.strip()
    return model.__name__


def build_schema(model: type[BaseModel], relative_path: str) -> dict[str, Any]:
    """Validation-mode JSON Schema of ``model`` with the package's ``$schema``/``$id``/title/description."""
    schema = model.model_json_schema(mode="validation")
    schema["$schema"] = SCHEMA_DIALECT
    schema["$id"] = ID_BASE + relative_path
    schema["title"] = model.__name__
    schema["description"] = first_docstring_line(model)
    return schema


def render(document: Mapping[str, Any]) -> str:
    """Deterministic rendering: sorted keys, two-space indent, trailing newline."""
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def schema_paths() -> dict[str, str]:
    """Map every contract name to the relative path of its schema file."""
    paths = {name: f"{name}.json" for name in TOP_LEVEL_CONTRACTS}
    paths.update({name: f"{SUPPORTING_DIR}/{name}.json" for name in SUPPORTING_CONTRACTS})
    return paths


def build_index(rendered: Mapping[str, str]) -> dict[str, Any]:
    """The ``index.json`` document: name, kind, path and digest of every schema file."""
    paths = schema_paths()
    return {
        "schema_version": SPEC_VERSION,
        "dialect": SCHEMA_DIALECT,
        "id_base": ID_BASE,
        "top_level": [
            {
                "name": name,
                "kind": pinned_kind(contract).value,
                "path": paths[name],
                "sha256": sha256_text(rendered[paths[name]]),
            }
            for name, contract in TOP_LEVEL_CONTRACTS.items()
        ],
        "supporting": [
            {"name": name, "path": paths[name], "sha256": sha256_text(rendered[paths[name]])}
            for name in SUPPORTING_CONTRACTS
        ],
    }


def generate_all() -> dict[str, str]:
    """Render every schema file plus the index, keyed by path relative to the output directory."""
    paths = schema_paths()
    rendered: dict[str, str] = {}
    for name, contract in TOP_LEVEL_CONTRACTS.items():
        rendered[paths[name]] = render(build_schema(contract, paths[name]))
    for name, contract in SUPPORTING_CONTRACTS.items():
        rendered[paths[name]] = render(build_schema(contract, paths[name]))
    rendered[INDEX_FILE] = render(build_index(rendered))
    return rendered


def write_schemas(out_dir: Path) -> list[Path]:
    """Write every schema file under ``out_dir`` and return the paths written."""
    written: list[Path] = []
    for relative, text in generate_all().items():
        target = out_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        written.append(target)
    return written


def committed_json_files(out_dir: Path) -> set[str]:
    """Relative paths of the JSON files present where the generator writes."""
    found: set[str] = set()
    if not out_dir.is_dir():
        return found
    for path in out_dir.glob("*.json"):
        found.add(path.name)
    for path in (out_dir / SUPPORTING_DIR).glob("*.json"):
        found.add(f"{SUPPORTING_DIR}/{path.name}")
    return found


def check_schemas(out_dir: Path) -> list[str]:
    """Return one line per difference between the committed files and fresh generation."""
    expected = generate_all()
    problems: list[str] = []
    for relative, text in expected.items():
        target = out_dir / relative
        if not target.is_file():
            problems.append(f"missing: {relative}")
            continue
        if target.read_text(encoding="utf-8") != text:
            problems.append(f"stale: {relative}")
    for relative in sorted(committed_json_files(out_dir) - set(expected)):
        problems.append(f"unexpected: {relative}")
    return problems


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m plumb.schemas_tool.generate",
        description="Write (or verify) the JSON Schemas of the 17 top-level and 5 supporting contracts.",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory (default: schemas/)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write; exit 1 if any committed file differs from fresh generation",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out_dir: Path = args.out
    if args.check:
        problems = check_schemas(out_dir)
        if problems:
            print(f"schemas in {out_dir} differ from the contracts:")
            for problem in problems:
                print(f"  {problem}")
            return EXIT_DRIFT
        print(f"schemas in {out_dir} match the contracts ({len(generate_all()) - 1} schemas + {INDEX_FILE})")
        return EXIT_OK
    written = write_schemas(out_dir)
    print(f"wrote {len(written)} files under {out_dir}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
