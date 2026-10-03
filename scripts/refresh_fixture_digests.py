#!/usr/bin/env python3
"""Recompute the content digests embedded in the fixture envelopes, plans and the registry.

The plan fixtures under ``fixtures/plans/`` carry their own ``content_digest``
and, in ``inputs``, the ``content_digest`` of the envelope they were compiled
against (``fixtures/envelopes/<scenario>.json``); every record of
``plumb/registry/capability_registry.json`` carries its own ``content_digest``
too. Hand-editing any of these JSON files invalidates those digests. This
script recomputes them in dependency order (envelope first, then the plan's
envelope input, then the plan itself; each registry record on its own) with
:func:`plumb.contracts.common.compute_artifact_digest`, the same function the
checker and the tests use.

Usage::

    python3 scripts/refresh_fixture_digests.py            # rewrite fixtures in place
    python3 scripts/refresh_fixture_digests.py --check    # exit 1 when any digest is stale

Only ``content_digest`` fields and the digest of the envelope input are
touched; every other byte of a fixture is left as written, and the JSON is
re-rendered with two-space indentation, which is how the fixtures are committed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from plumb.contracts.build_plan import BuildPlan  # noqa: E402
from plumb.contracts.capability import CapabilityRecord  # noqa: E402
from plumb.contracts.common import compute_artifact_digest  # noqa: E402
from plumb.contracts.envelope import AutonomyEnvelope  # noqa: E402

ENVELOPES = REPO_ROOT / "fixtures" / "envelopes"
PLANS = REPO_ROOT / "fixtures" / "plans"
REGISTRY = REPO_ROOT / "plumb" / "registry" / "capability_registry.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _render(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def refresh(check_only: bool = False) -> list[str]:
    """Refresh every fixture; return the names of the files whose digests changed."""
    changed: list[str] = []
    for envelope_path in sorted(ENVELOPES.glob("*.json")):
        envelope_data = _load(envelope_path)
        envelope = AutonomyEnvelope.model_validate(envelope_data)
        envelope_digest = compute_artifact_digest(envelope)
        if envelope_data.get("content_digest") != envelope_digest:
            envelope_data["content_digest"] = envelope_digest
            changed.append(envelope_path.name)
            if not check_only:
                envelope_path.write_text(_render(envelope_data), encoding="utf-8")

        plan_path = PLANS / envelope_path.name
        if not plan_path.exists():
            continue
        plan_data = _load(plan_path)
        for ref in plan_data.get("inputs", []):
            if ref.get("artifact_id") == envelope.envelope_id and ref.get("kind") == "AutonomyEnvelope":
                if ref.get("digest") != envelope_digest:
                    ref["digest"] = envelope_digest
                    if plan_path.name not in changed:
                        changed.append(plan_path.name)
        plan = BuildPlan.model_validate(plan_data)
        plan_digest = compute_artifact_digest(plan)
        if plan_data.get("content_digest") != plan_digest:
            plan_data["content_digest"] = plan_digest
            if plan_path.name not in changed:
                changed.append(plan_path.name)
        if plan_path.name in changed and not check_only:
            plan_path.write_text(_render(plan_data), encoding="utf-8")
    registry_data = _load(REGISTRY)
    registry_changed = False
    for entry in registry_data["capabilities"]:
        record_digest = compute_artifact_digest(CapabilityRecord.model_validate(entry))
        if entry.get("content_digest") != record_digest:
            entry["content_digest"] = record_digest
            registry_changed = True
    if registry_changed:
        changed.append(REGISTRY.name)
        if not check_only:
            REGISTRY.write_text(_render(registry_data), encoding="utf-8")
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="report stale digests without rewriting; exit 1 if any")
    args = parser.parse_args(argv)
    changed = refresh(check_only=args.check)
    if not changed:
        print("fixture digests are current")
        return 0
    verb = "stale" if args.check else "refreshed"
    print(f"{verb}: {', '.join(changed)}")
    return 1 if args.check else 0


if __name__ == "__main__":
    sys.exit(main())
