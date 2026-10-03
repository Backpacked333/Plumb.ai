"""Typed contracts of the Plumb reference package (specification v0.2).

This package exposes every contract class and two ordered registries:

* :data:`TOP_LEVEL_CONTRACTS` maps the 17 top-level contract names of design
  section 3, in table order, to the classes that implement them. Every entry
  subclasses :class:`~plumb.contracts.common.ArtifactHeader` and pins its
  ``kind`` to the matching :class:`~plumb.contracts.common.ArtifactKind`
  (section 8: every stored artifact is typed, versioned and digest-addressed).
* :data:`SUPPORTING_CONTRACTS` maps the five supporting records (section 22
  job, error and event envelopes; Appendix A agent task and step result).

:func:`contract_for_kind` resolves an :class:`ArtifactKind` to the contract
that parses artifacts of that kind, which is how the schema generator, the
checkers and the artifact store agree on one class per kind.

Requirements implemented by the contracts re-exported here are cited in the
docstrings of the individual modules (PL-004 .. PL-047, PL-053, PL-055 ..
PL-058).
"""

from __future__ import annotations

from plumb.contracts.api import ErrorEnvelope, EventEnvelope, JobEnvelope, JobStatus
from plumb.contracts.approval import ApprovalRecord, DecisionKind
from plumb.contracts.build_plan import BuildPlan, BuildStep, StepInput, StepOutput, VerificationObligation
from plumb.contracts.capability import CapabilityRecord, MaintenanceBurden
from plumb.contracts.collection import CollectionSpec, HealthContract
from plumb.contracts.common import ArtifactHeader, ArtifactKind, StrictModel
from plumb.contracts.dataset import DatasetCounts, DatasetManifest, DatasetRow, LabelDefinition, SplitRule
from plumb.contracts.effect import (
    ActionIntent,
    ActionReceipt,
    EffectSlot,
    ReconciliationOutcome,
    ReconciliationResult,
)
from plumb.contracts.envelope import AutonomyEnvelope, Goal, SourceGrant
from plumb.contracts.evaluation import CandidateComparison, EvaluationReport, Metric, SegregationStatement
from plumb.contracts.evidence import DerivedFact, EvidenceEvent, EvidencePacket, ObjectLink, ObjectResolution
from plumb.contracts.infrastructure import InfrastructurePlan, ResourceChange
from plumb.contracts.integration import FieldMapping, IntegrationOperation, IntegrationSpec
from plumb.contracts.inventory import ApplicationRecord, CoverageReport, EnvironmentInventory, OperationCapability
from plumb.contracts.opportunity import OpportunitySpec
from plumb.contracts.protocol import AgentTask, StepResult, check_result_against_task
from plumb.contracts.release import ReleaseComponent, ReleaseManifest, RolloutStage
from plumb.contracts.training import BaseModelRef, DataHandling, TrainingMethod, TrainingSpec
from plumb.contracts.verification import AttestationResult, CheckOutcome, CheckResult, VerificationAttestation
from plumb.contracts.workflow import WorkflowOperation, WorkflowSpec

TOP_LEVEL_CONTRACTS: dict[str, type[ArtifactHeader]] = {
    "AutonomyEnvelope": AutonomyEnvelope,
    "CapabilityRecord": CapabilityRecord,
    "EnvironmentInventory": EnvironmentInventory,
    "EvidencePacket": EvidencePacket,
    "OpportunitySpec": OpportunitySpec,
    "BuildPlan": BuildPlan,
    "IntegrationSpec": IntegrationSpec,
    "CollectionSpec": CollectionSpec,
    "DatasetManifest": DatasetManifest,
    "TrainingSpec": TrainingSpec,
    "WorkflowSpec": WorkflowSpec,
    "EvaluationReport": EvaluationReport,
    "InfrastructurePlan": InfrastructurePlan,
    "ReleaseManifest": ReleaseManifest,
    "ActionIntent": ActionIntent,
    "ApprovalRecord": ApprovalRecord,
    "VerificationAttestation": VerificationAttestation,
}
"""The 17 top-level contracts of design section 3, in table order."""

SUPPORTING_CONTRACTS: dict[str, type[StrictModel]] = {
    "JobEnvelope": JobEnvelope,
    "ErrorEnvelope": ErrorEnvelope,
    "EventEnvelope": EventEnvelope,
    "AgentTask": AgentTask,
    "StepResult": StepResult,
}
"""Supporting records that are exchanged but are not stored artifacts (section 22, Appendix A)."""


def pinned_kind(contract: type[ArtifactHeader]) -> ArtifactKind:
    """Return the ``kind`` a top-level contract pins through its ``Literal`` default."""
    default = contract.model_fields["kind"].default
    if not isinstance(default, ArtifactKind):
        raise TypeError(f"{contract.__name__} does not pin kind to an ArtifactKind default")
    return default


_CONTRACT_BY_KIND: dict[ArtifactKind, type[ArtifactHeader]] = {
    pinned_kind(contract): contract for contract in TOP_LEVEL_CONTRACTS.values()
}


def contract_for_kind(kind: ArtifactKind) -> type[ArtifactHeader]:
    """Return the top-level contract class that parses artifacts of ``kind``.

    Raises :class:`KeyError` for a kind that is not a top-level contract (for
    example ``ArtifactKind.PROBE_RECEIPT``, which steps produce but which has
    no contract of its own in this package).
    """
    try:
        return _CONTRACT_BY_KIND[ArtifactKind(kind)]
    except (KeyError, ValueError) as exc:
        raise KeyError(f"no top-level contract is registered for artifact kind {kind!r}") from exc


__all__ = [
    # registries and helpers
    "TOP_LEVEL_CONTRACTS",
    "SUPPORTING_CONTRACTS",
    "contract_for_kind",
    "pinned_kind",
    "check_result_against_task",
    # shared primitives used by the registries
    "ArtifactHeader",
    "ArtifactKind",
    "StrictModel",
    # top-level contracts (design section 3 order)
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
    # supporting contracts
    "JobEnvelope",
    "ErrorEnvelope",
    "EventEnvelope",
    "AgentTask",
    "StepResult",
    # component models and vocabularies named by the design document
    "Goal",
    "SourceGrant",
    "MaintenanceBurden",
    "ApplicationRecord",
    "OperationCapability",
    "CoverageReport",
    "EvidenceEvent",
    "DerivedFact",
    "ObjectResolution",
    "ObjectLink",
    "StepInput",
    "StepOutput",
    "VerificationObligation",
    "BuildStep",
    "IntegrationOperation",
    "FieldMapping",
    "HealthContract",
    "DatasetRow",
    "LabelDefinition",
    "SplitRule",
    "DatasetCounts",
    "TrainingMethod",
    "BaseModelRef",
    "DataHandling",
    "WorkflowOperation",
    "Metric",
    "CandidateComparison",
    "SegregationStatement",
    "ResourceChange",
    "ReleaseComponent",
    "RolloutStage",
    "EffectSlot",
    "ActionReceipt",
    "ReconciliationOutcome",
    "ReconciliationResult",
    "DecisionKind",
    "CheckOutcome",
    "AttestationResult",
    "CheckResult",
    "JobStatus",
]
