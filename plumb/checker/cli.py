"""Command-line entry point for the local reference checkers (design section 1).

Usage::

    python -m plumb.checker.cli plan <plan.json> <envelope.json> [--registry PATH] [--now ISO-8601] [--json]
    python -m plumb.checker.cli dataset <manifest.json> [--json]

Exit codes: ``0`` when the report has no ERROR finding, ``1`` when it has at
least one, ``2`` on a usage error, an unreadable or malformed input file or a
registry that fails to load. The CLI only parses artifacts and runs a checker;
it never executes a plan (PL-014, PL-015, PL-028..PL-030).

The ``dataset`` subcommand imports ``plumb.checker.dataset_checker`` lazily so
that the ``plan`` subcommand works even when that module is unavailable.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from plumb.checker.findings import CheckReport

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2

_ModelT = TypeVar("_ModelT", bound=BaseModel)


class CliError(Exception):
    """A usage, input or configuration problem; reported on stderr with exit code 2."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m plumb.checker.cli",
        description="Run a Plumb reference checker over persisted artifacts. Nothing is executed.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="{plan,dataset}")

    plan = subparsers.add_parser("plan", help="check a BuildPlan against an AutonomyEnvelope")
    plan.add_argument("plan", type=Path, help="BuildPlan JSON file")
    plan.add_argument("envelope", type=Path, help="AutonomyEnvelope JSON file")
    plan.add_argument("--registry", type=Path, default=None, help="capability registry JSON (default: packaged)")
    plan.add_argument(
        "--now",
        default=None,
        help="timezone-aware ISO-8601 instant to evaluate authority at (default: the plan's planned_at)",
    )
    plan.add_argument("--json", action="store_true", help="print the report as JSON instead of text")

    dataset = subparsers.add_parser("dataset", help="check a DatasetManifest")
    dataset.add_argument("manifest", type=Path, help="DatasetManifest JSON file")
    dataset.add_argument("--json", action="store_true", help="print the report as JSON instead of text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse already printed usage or help
        return _exit_code(exc.code)
    try:
        if args.command == "plan":
            report = _run_plan(args)
        else:
            report = _run_dataset(args)
    except CliError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    _print_report(report, as_json=args.json)
    return EXIT_OK if report.ok else EXIT_FINDINGS


def _run_plan(args: argparse.Namespace) -> CheckReport:
    from plumb.checker.plan_checker import check_plan
    from plumb.contracts.build_plan import BuildPlan
    from plumb.contracts.envelope import AutonomyEnvelope
    from plumb.registry.registry import RegistryError, load_registry

    plan = _parse(BuildPlan, args.plan)
    envelope = _parse(AutonomyEnvelope, args.envelope)
    try:
        registry = load_registry(args.registry)
    except RegistryError as exc:
        raise CliError(str(exc)) from exc
    now = _parse_instant(args.now) if args.now is not None else None
    try:
        return check_plan(plan, envelope, registry, now=now)
    except ValueError as exc:
        raise CliError(str(exc)) from exc


def _run_dataset(args: argparse.Namespace) -> CheckReport:
    try:
        from plumb.checker.dataset_checker import check_dataset
        from plumb.contracts.dataset import DatasetManifest
    except ImportError as exc:
        raise CliError(f"the dataset checker is not available in this installation: {exc}") from exc
    return check_dataset(_parse(DatasetManifest, args.manifest))


def _parse(model: type[_ModelT], path: Path) -> _ModelT:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CliError(f"cannot read {path}: {exc.strerror or exc}") from exc
    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CliError(f"{path} is not valid JSON: {exc}") from exc
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise CliError(f"{path} is not a valid {model.__name__}:\n{exc}") from exc


def _parse_instant(text: str) -> datetime:
    try:
        value = datetime.fromisoformat(text)
    except ValueError as exc:
        raise CliError(f"--now must be an ISO-8601 instant, got {text!r}") from exc
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise CliError("--now must carry a timezone offset (for example 2026-10-02T00:00:00Z)")
    return value


def _print_report(report: CheckReport, *, as_json: bool) -> None:
    if as_json:
        payload = {"ok": report.ok, **report.model_dump(mode="json")}
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(report.render())


def _exit_code(code: object) -> int:
    """argparse exits with 0 for --help and 2 for a usage error; normalise anything else to 2."""
    if code is None:
        return EXIT_OK
    if isinstance(code, int):
        return code
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
