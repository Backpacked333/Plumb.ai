"""TrainingSpec (specification section 14).

Implements:

* PL-032: a TrainingSpec pins the dataset, base-model capability/version,
  training method, objective, resource/spend limits, stopping condition,
  output location, data-handling constraints and evaluation plan. The
  provider/method/modality combination is checked at build time and an
  unsupported combination fails *here*, at validation, before any provider job
  could be submitted.
* PL-033: ``submission_identity`` is a stable string persisted before
  submission so a lost response never launches a duplicate job. A completed
  provider job is a *candidate* artifact (:attr:`TrainingState.CANDIDATE`), not
  an approved production model: there is no approved state on this contract;
  promotion happens through evaluation and release (PL-034).
* PL-053 / section 2: data routing is explicit (selected fields, processor,
  region, retention, credential reference). Credential fields hold references,
  never secret values.

``method == NONE`` records the decision *not* to train: every provider-job field
must then be absent, so that a "no training" spec can never be submitted by
accident.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Annotated, Literal

from pydantic import AfterValidator, AwareDatetime, Field, field_validator, model_validator

from plumb.contracts.common import (
    ArtifactHeader,
    ArtifactKind,
    ArtifactRef,
    Budget,
    Identifier,
    NonEmptyStr,
    Region,
    ShortStr,
    StrictModel,
    TrainingState,
)


class TrainingMethod(str, Enum):
    """How a trained component is produced; NONE records the decision not to train."""

    API_FINETUNE = "API_FINETUNE"
    MANAGED_OPEN_MODEL = "MANAGED_OPEN_MODEL"
    NONE = "NONE"


_SECRET_MARKERS: tuple[str, ...] = ("secret", "password", "token=")
_BASE64_RUN = re.compile(r"[A-Za-z0-9+/=_-]{40,}")


def reject_secret_like(value: str) -> str:
    """Reject strings that look like a secret value rather than a reference to one.

    A reference contains none of ``secret``, ``password`` or ``token=`` and no
    run of 40+ base64-like characters with mixed case and digits.
    """
    lowered = value.lower()
    for marker in _SECRET_MARKERS:
        if marker in lowered:
            raise ValueError(f"value looks like a secret (contains {marker!r}); store a reference, not a value")
    for run in _BASE64_RUN.findall(value):
        if any(c.isupper() for c in run) and any(c.islower() for c in run) and any(c.isdigit() for c in run):
            raise ValueError("value looks like a secret (40+ characters of base64-like text)")
    return value


NonSecretRef = Annotated[ShortStr, AfterValidator(reject_secret_like)]
"""A short reference string that is rejected when it looks like a credential value."""


class BaseModelRef(StrictModel):
    """Pinned base model: provider, capability and exact version (PL-032)."""

    provider: ShortStr
    capability: ShortStr = Field(description="Provider capability used, e.g. 'text-classification-tuning'.")
    version: ShortStr = Field(description="Exact provider model version; never a mutable alias.")


class StoppingCondition(StrictModel):
    """Hard bounds on a training job; at least one bound is mandatory (PL-032)."""

    max_epochs: int | None = Field(default=None, ge=1)
    max_steps: int | None = Field(default=None, ge=1)
    max_elapsed_seconds: int | None = Field(default=None, ge=1)
    early_stopping_metric: ShortStr | None = None
    early_stopping_patience: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _has_a_hard_bound(self) -> "StoppingCondition":
        if self.max_epochs is None and self.max_steps is None and self.max_elapsed_seconds is None:
            raise ValueError("stopping_condition needs at least one of max_epochs, max_steps, max_elapsed_seconds")
        if self.early_stopping_patience is not None and self.early_stopping_metric is None:
            raise ValueError("early_stopping_patience requires early_stopping_metric")
        return self


class DataHandling(StrictModel):
    """Where and how the training data is processed (PL-032, PL-053)."""

    processor: Identifier = Field(description="Approved data processor id from the envelope.")
    region: Region
    retention: ShortStr = Field(description="Retention the processor is held to, e.g. 'delete_after_job'.")
    credential_ref: NonSecretRef = Field(description="Reference resolved by the gateway; never a secret value.")
    selected_fields: list[Identifier] = Field(
        default_factory=list, description="Dataset fields sent to the processor; empty means all row fields."
    )


class SupportedCombinationCheck(StrictModel):
    """Build-time record that provider/method/modality support was verified (PL-032)."""

    provider: ShortStr
    method: TrainingMethod
    modality: ShortStr = Field(description="E.g. 'text', 'image', 'tabular'.")
    supported: bool
    checked_at: AwareDatetime


class TrainingSpec(ArtifactHeader):
    """Complete, pinned description of one training decision (PL-032, PL-033)."""

    kind: Literal[ArtifactKind.TRAINING_SPEC] = ArtifactKind.TRAINING_SPEC
    dataset_ref: ArtifactRef = Field(description="Pinned DatasetManifest the job trains on.")
    method: TrainingMethod
    objective: NonEmptyStr
    evaluation_plan_ref: ArtifactRef = Field(description="Pinned plan the candidate will be evaluated against.")
    base_model: BaseModelRef | None = None
    budget: Budget | None = None
    stopping_condition: StoppingCondition | None = None
    output_location: NonSecretRef | None = Field(
        default=None, description="Where versioned artifacts are written, e.g. a registry path."
    )
    data_handling: DataHandling | None = None
    submission_identity: NonSecretRef | None = Field(
        default=None,
        description="Stable identity persisted before the provider job is submitted (PL-033).",
    )
    supported_combination_check: SupportedCombinationCheck | None = None
    state: TrainingState = Field(
        default=TrainingState.PLANNED,
        description="Lifecycle state. CANDIDATE is the end of a successful job; approval is a release decision.",
    )

    @field_validator("dataset_ref")
    @classmethod
    def _dataset_kind(cls, ref: ArtifactRef) -> ArtifactRef:
        if ref.kind != ArtifactKind.DATASET_MANIFEST:
            raise ValueError(f"dataset_ref must reference a DatasetManifest, not {ref.kind.value}")
        return ref

    @property
    def requires_provider_job(self) -> bool:
        return self.method != TrainingMethod.NONE

    def _provider_job_fields(self) -> dict[str, object]:
        return {
            "base_model": self.base_model,
            "budget": self.budget,
            "stopping_condition": self.stopping_condition,
            "output_location": self.output_location,
            "data_handling": self.data_handling,
            "submission_identity": self.submission_identity,
            "supported_combination_check": self.supported_combination_check,
        }

    @model_validator(mode="after")
    def _method_fields_are_consistent(self) -> "TrainingSpec":
        fields = self._provider_job_fields()
        if not self.requires_provider_job:
            present = sorted(name for name, value in fields.items() if value is not None)
            if present:
                raise ValueError(f"method NONE submits no provider job; remove: {', '.join(present)}")
            if self.state not in (TrainingState.PLANNED, TrainingState.CANCELLED):
                raise ValueError(f"method NONE cannot be in state {self.state.value}: there is no job to run")
            return self
        missing = sorted(name for name, value in fields.items() if value is None)
        if missing:
            raise ValueError(f"method {self.method.value} requires: {', '.join(missing)}")
        return self._check_supported_combination()

    def _check_supported_combination(self) -> "TrainingSpec":
        check = self.supported_combination_check
        base_model = self.base_model
        assert check is not None and base_model is not None  # guaranteed by the caller
        if not check.supported:
            raise ValueError(
                f"{check.provider}/{check.method.value}/{check.modality} is not a supported combination; "
                "unsupported combinations fail before a provider job is submitted"
            )
        if check.provider != base_model.provider:
            raise ValueError(
                f"supported_combination_check is for provider {check.provider!r} but base_model "
                f"names {base_model.provider!r}"
            )
        if check.method != self.method:
            raise ValueError(
                f"supported_combination_check verified method {check.method.value} but the spec "
                f"uses {self.method.value}"
            )
        return self


__all__ = [
    "TrainingMethod",
    "reject_secret_like",
    "NonSecretRef",
    "BaseModelRef",
    "StoppingCondition",
    "DataHandling",
    "SupportedCombinationCheck",
    "TrainingSpec",
]
