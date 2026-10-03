"""Capability registry: the closed vocabulary of step types the planner may use.

Implements (specification v0.2):

* PL-014: unsupported step types are rejected rather than interpreted. The
  registry is the authority on which ``step_type`` values exist and which
  capabilities implement them; the checker consults :meth:`CapabilityRegistry.step_type_known`.
* PL-008: every entry is validated through
  :class:`~plumb.contracts.capability.CapabilityRecord` on load, so a record
  claiming a tested maturity without a probe receipt can never enter the
  registry. Loading fails loudly (:class:`RegistryError`) on any invalid entry
  or duplicate ``capability_id``; a partially loaded registry is never returned.
* Appendix A section 5: records carry tested environment, failure modes,
  required authority and maintenance burden, available to the planner through
  :meth:`CapabilityRegistry.capabilities_for_step_type`.

The packaged ``capability_registry.json`` is synthetic reference data: it names
plausible providers and operations but establishes nothing about any real account.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from plumb.contracts.capability import CapabilityRecord

DEFAULT_REGISTRY_PATH = Path(__file__).with_name("capability_registry.json")
"""Location of the packaged registry file."""

REGISTRY_ENTRIES_KEY = "capabilities"
"""Top-level key holding the list of capability records in the JSON file."""


class RegistryError(ValueError):
    """Raised when a registry file or entry is malformed. Nothing is loaded partially."""


class CapabilityRegistry:
    """Read-only lookups over validated :class:`CapabilityRecord` entries."""

    def __init__(self, records: Iterable[CapabilityRecord]) -> None:
        self._by_id: dict[str, CapabilityRecord] = {}
        self._by_step_type: dict[str, list[CapabilityRecord]] = {}
        for record in records:
            if record.capability_id in self._by_id:
                raise RegistryError(f"duplicate capability_id {record.capability_id!r}")
            self._by_id[record.capability_id] = record
            self._by_step_type.setdefault(record.step_type, []).append(record)

    # -- construction -----------------------------------------------------------

    @classmethod
    def from_file(cls, path: str | Path) -> "CapabilityRegistry":
        """Load and validate a registry JSON file; raise :class:`RegistryError` on any defect."""
        file_path = Path(path)
        try:
            raw = json.loads(file_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise RegistryError(f"registry file not found: {file_path}") from exc
        except json.JSONDecodeError as exc:
            raise RegistryError(f"registry file {file_path} is not valid JSON: {exc}") from exc
        return cls(cls._parse_entries(raw, str(file_path)))

    @classmethod
    def default(cls) -> "CapabilityRegistry":
        """The registry packaged with this distribution."""
        return cls.from_file(DEFAULT_REGISTRY_PATH)

    @staticmethod
    def _parse_entries(raw: Any, source: str) -> list[CapabilityRecord]:
        if not isinstance(raw, dict) or not isinstance(raw.get(REGISTRY_ENTRIES_KEY), list):
            raise RegistryError(
                f"registry {source} must be an object with a {REGISTRY_ENTRIES_KEY!r} list"
            )
        records: list[CapabilityRecord] = []
        for index, entry in enumerate(raw[REGISTRY_ENTRIES_KEY]):
            label = entry.get("capability_id", f"#{index}") if isinstance(entry, dict) else f"#{index}"
            try:
                records.append(CapabilityRecord.model_validate(entry))
            except ValidationError as exc:
                raise RegistryError(f"invalid capability entry {label!r} in {source}: {exc}") from exc
        return records

    # -- lookups ----------------------------------------------------------------

    def step_type_known(self, step_type: str) -> bool:
        """True when at least one capability implements ``step_type`` (PL-014)."""
        return step_type in self._by_step_type

    def get(self, capability_id: str) -> CapabilityRecord | None:
        return self._by_id.get(capability_id)

    def capabilities_for_step_type(self, step_type: str) -> list[CapabilityRecord]:
        """Records implementing ``step_type`` in file order; empty for an unknown step type."""
        return list(self._by_step_type.get(step_type, []))

    def step_types(self) -> set[str]:
        return set(self._by_step_type)

    def capability_ids(self) -> set[str]:
        return set(self._by_id)

    def records(self) -> list[CapabilityRecord]:
        """All records in file order."""
        return list(self._by_id.values())

    def __len__(self) -> int:
        return len(self._by_id)

    def __iter__(self) -> Iterator[CapabilityRecord]:
        return iter(self._by_id.values())

    def __contains__(self, capability_id: object) -> bool:
        return capability_id in self._by_id


def load_registry(path: str | Path | None = None) -> CapabilityRegistry:
    """Load the registry at ``path``, or the packaged default when ``path`` is None."""
    if path is None:
        return CapabilityRegistry.default()
    return CapabilityRegistry.from_file(path)


__all__ = [
    "DEFAULT_REGISTRY_PATH",
    "REGISTRY_ENTRIES_KEY",
    "RegistryError",
    "CapabilityRegistry",
    "load_registry",
]
