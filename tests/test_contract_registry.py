"""Tests for the contract registry exported by ``plumb.contracts``.

The registry is the single place where the 17 top-level contracts (design
section 3), their pinned artifact kinds (section 8) and the five supporting
records are enumerated. These tests prove that every entry is a strict
``ArtifactHeader`` subclass with a ``Literal`` kind, that the kinds are unique
and resolvable through :func:`plumb.contracts.contract_for_kind`, that the
shared vocabularies match the normative lists of sections 22 and 23
(PL-055 .. PL-057), that the label-kind vocabulary keeps the five kinds of
PL-026 distinct, and that no module of the package carries a secret-like
literal (PL-054).
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path
from typing import Literal, get_args, get_origin

import pytest

import plumb.contracts as contracts
from plumb.contracts import (
    SUPPORTING_CONTRACTS,
    TOP_LEVEL_CONTRACTS,
    DatasetRow,
    LabelDefinition,
    contract_for_kind,
    pinned_kind,
)
from plumb.contracts.common import (
    ArtifactHeader,
    ArtifactKind,
    BuildState,
    BuildStepState,
    CollectorState,
    DatasetState,
    EffectState,
    ErrorClass,
    LabelKind,
    ReleaseState,
    StrictModel,
    TrainingState,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_DIR = REPO_ROOT / "plumb"

EXPECTED_TOP_LEVEL_ORDER = [
    "AutonomyEnvelope",
    "CapabilityRecord",
    "EnvironmentInventory",
    "EvidencePacket",
    "OpportunitySpec",
    "BuildPlan",
    "IntegrationSpec",
    "CollectionSpec",
    "DatasetManifest",
    "TrainingSpec",
    "WorkflowSpec",
    "EvaluationReport",
    "InfrastructurePlan",
    "ReleaseManifest",
    "ActionIntent",
    "ApprovalRecord",
    "VerificationAttestation",
]
EXPECTED_SUPPORTING_ORDER = ["JobEnvelope", "ErrorEnvelope", "EventEnvelope", "AgentTask", "StepResult"]

# Specification section 22, verbatim order.
SPEC_ERROR_CLASSES = [
    "AUTH_REQUIRED",
    "SCOPE_DENIED",
    "PURPOSE_DENIED",
    "POLICY_STALE",
    "STATE_CONFLICT",
    "PAYLOAD_CONFLICT",
    "BUDGET_EXCEEDED",
    "CAPABILITY_UNSUPPORTED",
    "SOURCE_STALE",
    "DATA_QUALITY_FAILED",
    "VERIFICATION_FAILED",
    "EFFECT_UNKNOWN",
    "RETRY_EXHAUSTED",
]

# Specification section 23 lifecycle table, verbatim order.
SPEC_LIFECYCLES: dict[type, list[str]] = {
    BuildState: ["DRAFT", "VALIDATED", "RUNNING", "WAITING_AUTH", "WAITING_INPUT", "VERIFYING", "VERIFIED", "FAILED", "CANCELLED"],
    BuildStepState: ["PENDING", "READY", "RUNNING", "VERIFYING", "VERIFIED", "FAILED", "BLOCKED", "CANCELLED"],
    CollectorState: ["PLANNED", "SHADOW", "BACKFILLING", "RECONCILING", "ACTIVE", "DEGRADED", "PAUSED", "RETIRED"],
    DatasetState: ["PROPOSED", "MATERIALIZING", "QUARANTINED", "VERIFIED", "SUPERSEDED", "UNAVAILABLE"],
    TrainingState: ["PLANNED", "SUBMITTED", "RUNNING", "CANDIDATE", "FAILED", "CANCELLED"],
    ReleaseState: ["CANDIDATE", "VERIFIED", "SHADOW", "CANARY", "ACTIVE", "PAUSED", "ROLLED_BACK", "RETIRED"],
    EffectState: ["RESERVED", "DISPATCHED", "UNKNOWN", "CONFIRMED", "FAILED_FINAL", "COMPENSATED"],
}

# A literal "looks like a secret" when a credential marker carries a value: the bare
# marker words are the detection vocabulary of the *_ref validators and are not secrets.
SECRET_LIKE_PATTERNS = [
    re.compile(r"password\s*[:=]\s*['\"]?[A-Za-z0-9+/_\-!@#$%^&*]{4,}", re.IGNORECASE),
    re.compile(r"secret=\s*['\"]?[A-Za-z0-9+/_\-]{4,}", re.IGNORECASE),
    re.compile(r"BEGIN PRIVATE KEY"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]


def secret_like_hits(text: str) -> list[str]:
    """Return every substring of ``text`` that matches a secret-like pattern."""
    return [match.group(0) for pattern in SECRET_LIKE_PATTERNS for match in pattern.finditer(text)]


# ---------------------------------------------------------------------------
# Registry structure
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-004")
def test_top_level_registry_has_the_17_contracts_in_design_order() -> None:
    assert list(TOP_LEVEL_CONTRACTS) == EXPECTED_TOP_LEVEL_ORDER
    assert len(TOP_LEVEL_CONTRACTS) == 17
    assert len({id(cls) for cls in TOP_LEVEL_CONTRACTS.values()}) == 17


@pytest.mark.requirements("PL-004")
@pytest.mark.parametrize("name", EXPECTED_TOP_LEVEL_ORDER)
def test_every_top_level_contract_is_a_strict_artifact_header(name: str) -> None:
    cls = TOP_LEVEL_CONTRACTS[name]
    assert cls.__name__ == name
    assert issubclass(cls, ArtifactHeader)
    assert issubclass(cls, StrictModel)
    assert cls.model_config.get("extra") == "forbid"
    assert cls is not ArtifactHeader


@pytest.mark.requirements("PL-004")
@pytest.mark.parametrize("name", EXPECTED_TOP_LEVEL_ORDER)
def test_every_top_level_contract_pins_kind_with_a_literal_default(name: str) -> None:
    cls = TOP_LEVEL_CONTRACTS[name]
    field = cls.model_fields["kind"]
    assert get_origin(field.annotation) is Literal, f"{name}.kind must be a Literal"
    (allowed,) = get_args(field.annotation)
    assert allowed == ArtifactKind(name)
    assert field.default == ArtifactKind(name)
    assert pinned_kind(cls) is ArtifactKind(name)
    assert pinned_kind(cls).value == name


@pytest.mark.requirements("PL-004")
def test_pinned_kinds_are_unique_and_cover_the_first_17_artifact_kinds() -> None:
    kinds = [pinned_kind(cls) for cls in TOP_LEVEL_CONTRACTS.values()]
    assert len(set(kinds)) == 17
    assert [kind.value for kind in kinds] == EXPECTED_TOP_LEVEL_ORDER
    assert [member.value for member in list(ArtifactKind)[:17]] == EXPECTED_TOP_LEVEL_ORDER


@pytest.mark.requirements("PL-004")
def test_contract_for_kind_resolves_every_top_level_kind_and_rejects_others() -> None:
    for name, cls in TOP_LEVEL_CONTRACTS.items():
        assert contract_for_kind(ArtifactKind(name)) is cls
        assert contract_for_kind(name) is cls  # plain string values are accepted too
    non_contract_kinds = [kind for kind in ArtifactKind if kind.value not in TOP_LEVEL_CONTRACTS]
    assert non_contract_kinds, "ArtifactKind should list supporting artifact kinds beyond the 17 contracts"
    for kind in non_contract_kinds:
        with pytest.raises(KeyError):
            contract_for_kind(kind)
    with pytest.raises(KeyError):
        contract_for_kind("NotAnArtifactKind")


@pytest.mark.requirements("PL-004")
def test_every_contract_is_importable_from_the_package_namespace() -> None:
    for name, cls in {**TOP_LEVEL_CONTRACTS, **SUPPORTING_CONTRACTS}.items():
        assert name in contracts.__all__
        assert getattr(contracts, name) is cls
        assert cls.__module__.startswith("plumb.contracts.")
    for name in contracts.__all__:
        assert hasattr(contracts, name), f"__all__ names {name} which the package does not define"


@pytest.mark.requirements("PL-055", "PL-057")
def test_supporting_registry_lists_the_five_records_which_are_not_artifacts() -> None:
    assert list(SUPPORTING_CONTRACTS) == EXPECTED_SUPPORTING_ORDER
    for name, cls in SUPPORTING_CONTRACTS.items():
        assert cls.__name__ == name
        assert issubclass(cls, StrictModel)
        assert not issubclass(cls, ArtifactHeader), f"{name} is exchanged, not stored as an artifact"
        assert "kind" not in cls.model_fields
    assert not set(SUPPORTING_CONTRACTS) & set(TOP_LEVEL_CONTRACTS)


@pytest.mark.requirements("PL-004")
def test_top_level_contracts_reject_unknown_fields_and_wrong_kinds() -> None:
    envelope_cls = TOP_LEVEL_CONTRACTS["AutonomyEnvelope"]
    with pytest.raises(ValueError):
        envelope_cls.model_validate({"unexpected_field": 1})
    schema = envelope_cls.model_json_schema(mode="validation")
    assert schema["additionalProperties"] is False
    assert schema["properties"]["kind"]["const"] == "AutonomyEnvelope"


# ---------------------------------------------------------------------------
# Shared vocabularies (sections 22 and 23)
# ---------------------------------------------------------------------------


@pytest.mark.requirements("PL-055", "PL-056")
def test_error_classes_match_the_13_of_section_22() -> None:
    assert [member.value for member in ErrorClass] == SPEC_ERROR_CLASSES
    assert len(ErrorClass) == 13
    assert all(member.name == member.value for member in ErrorClass)


@pytest.mark.requirements("PL-057")
@pytest.mark.parametrize("enum_cls", list(SPEC_LIFECYCLES), ids=lambda cls: cls.__name__)
def test_lifecycle_enums_match_section_23_exactly(enum_cls: type) -> None:
    assert [member.value for member in enum_cls] == SPEC_LIFECYCLES[enum_cls]
    assert all(member.name == member.value for member in enum_cls)


@pytest.mark.requirements("PL-026")
def test_label_kinds_distinguish_the_five_kinds_of_pl_026() -> None:
    assert [member.value for member in LabelKind] == [
        "OBSERVED_OUTCOME",
        "EXPERT_DECISION",
        "CORRECTION",
        "PREFERENCE",
        "WEAK_PROXY",
    ]
    assert len(set(LabelKind)) == 5
    # Every dataset row and label definition carries the distinction, so a manifest
    # cannot present a weak proxy or a correction as an observed outcome.
    assert DatasetRow.model_fields["label_kind"].annotation is LabelKind
    assert DatasetRow.model_fields["label_kind"].is_required()
    assert LabelDefinition.model_fields["label_kind"].annotation is LabelKind
    with pytest.raises(ValueError):
        LabelDefinition(text="settled within the period", label_kind="OUTCOME", maturation_window_days=0)


@pytest.mark.requirements("PL-057")
def test_the_seven_aggregates_of_section_23_are_all_modelled() -> None:
    assert len(SPEC_LIFECYCLES) == 7
    assert {cls.__name__ for cls in SPEC_LIFECYCLES} == {
        "BuildState",
        "BuildStepState",
        "CollectorState",
        "DatasetState",
        "TrainingState",
        "ReleaseState",
        "EffectState",
    }


# ---------------------------------------------------------------------------
# No secrets in the package (PL-054)
# ---------------------------------------------------------------------------


def _package_files() -> list[Path]:
    files = [path for path in PACKAGE_DIR.rglob("*") if path.is_file() and path.suffix in {".py", ".json"}]
    assert files, "the plumb package must contain modules to scan"
    return sorted(files)


@pytest.mark.requirements("PL-054")
def test_no_module_under_plumb_contains_a_secret_like_literal() -> None:
    offenders: dict[str, list[str]] = {}
    for path in _package_files():
        hits = secret_like_hits(path.read_text(encoding="utf-8"))
        if hits:
            offenders[str(path.relative_to(REPO_ROOT))] = hits
    assert not offenders, f"secret-like literals found: {offenders}"


@pytest.mark.requirements("PL-054")
def test_secret_scan_recognises_planted_secrets() -> None:
    planted = inspect.cleandoc(
        """
        DB_PASSWORD = "hunter2-not-a-real-value"
        url = "https://example.invalid/callback?secret=abcd1234"
        -----BEGIN PRIVATE KEY-----
        access_key = "AKIAABCDEFGHIJKLMNOP"
        """
    )
    hits = secret_like_hits(planted)
    assert len(hits) == 4, hits
    # The detection vocabulary used by the *_ref validators is not itself a secret.
    assert secret_like_hits('_SECRET_MARKERS = ("secret", "password", "token=")') == []
    assert secret_like_hits('re.compile(r"secret|password|token=")') == []
