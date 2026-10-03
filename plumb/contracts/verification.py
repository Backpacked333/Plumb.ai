"""VerificationAttestation: evidence produced by an independent verifier (specification section 18).

Implements:

* PL-042: verification inspects the artifact or the resulting system state, not
  an agent's completion claim. Each attestation records verifier identity and
  version, the input artifact digest, per-check evidence, result, timestamp
  and environment. The verifier must not be writable by the implementation job
  it assesses: ``verifier`` must be a ``VERIFIER`` principal distinct from
  ``assessed_producer``, and the artifact ``producer`` can never be a build or
  runtime agent at all, let alone the assessed job (attestations are records
  issued by the verifier, not fields any builder may fill; Appendix A section 3).
* PL-043: passing unit tests cannot substitute for verifying a real effect in
  the intended environment. A ``PASS`` attestation needs at least one passing
  check *at the attested level* backed by evidence; a check that is ``PASS``
  without ``evidence_refs`` is rejected.
* PL-044: the protected test bundle is identified by digest
  (``protected_bundle_digest``) so that a release can prove which protected
  checks were run without exposing the holdout.

Cross-artifact rules (does the attestation match the component bytes and scope
of a release?) belong to :mod:`plumb.checker.release_checker`.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from plumb.contracts.common import (
    AGENT_PRINCIPAL_TYPES,
    ArtifactHeader,
    ArtifactKind,
    Identifier,
    NonEmptyStr,
    NonSecretRef,
    Principal,
    PrincipalType,
    ResourceScope,
    SemVer,
    Sha256Digest,
    ShortStr,
    StrictModel,
    VerificationLevel,
)


class CheckOutcome(str, Enum):
    """Result of one check inside an attestation."""

    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


class AttestationResult(str, Enum):
    """Overall result of an attestation; FAIL whenever any check failed."""

    PASS = "PASS"
    FAIL = "FAIL"


class CheckResult(StrictModel):
    """One verifier check with the evidence that supports its outcome (PL-042)."""

    name: Identifier = Field(description="Stable check name, e.g. contract_tests or adversarial_prompt_injection.")
    level: VerificationLevel
    result: CheckOutcome
    evidence_refs: list[NonSecretRef] = Field(
        default_factory=list, description="References to logs, receipts or observed state; required for PASS."
    )
    detail: NonEmptyStr | None = Field(default=None, description="Human-readable detail; required when SKIPPED.")

    @model_validator(mode="after")
    def _check_evidence(self) -> "CheckResult":
        if self.result is CheckOutcome.PASS and not self.evidence_refs:
            raise ValueError(f"check {self.name!r} is PASS without evidence; a bare claim is not verification (PL-042)")
        if self.result is CheckOutcome.SKIPPED and self.detail is None:
            raise ValueError(f"check {self.name!r} is SKIPPED without a detail explaining why")
        return self


class VerificationAttestation(ArtifactHeader):
    """Independent verification of one artifact digest in one environment and scope (PL-042, PL-043)."""

    kind: Literal[ArtifactKind.VERIFICATION_ATTESTATION] = ArtifactKind.VERIFICATION_ATTESTATION
    verifier: Principal = Field(description="The verifier identity; must be a VERIFIER principal.")
    verifier_version: SemVer
    input_artifact_digest: Sha256Digest = Field(description="Exact bytes that were verified.")
    level: VerificationLevel = Field(description="Highest verification level this attestation establishes.")
    checks: list[CheckResult] = Field(min_length=1)
    result: AttestationResult
    timestamp: AwareDatetime
    environment: ShortStr = Field(description="Environment the checks ran against, e.g. sandbox or production.")
    protected_bundle_digest: Sha256Digest = Field(description="Digest of the protected test bundle that was run.")
    assessed_producer: Principal = Field(description="Principal of the implementation job whose output is assessed.")
    scope: ResourceScope = Field(
        default_factory=ResourceScope, description="Sources, destinations, processors and regions the verification covered."
    )

    @model_validator(mode="after")
    def _check_independence_and_result(self) -> "VerificationAttestation":
        if self.verifier.principal_type is not PrincipalType.VERIFIER:
            raise ValueError(
                f"verifier must be a VERIFIER principal, not {self.verifier.principal_type.value} (PL-042)"
            )
        if self.producer.principal_type in AGENT_PRINCIPAL_TYPES:
            raise ValueError(
                f"an attestation cannot be produced by a {self.producer.principal_type.value}; verifier attestations "
                "are separate records issued by the verifier, not fields a builder may fill (PL-042)"
            )
        if self.verifier.principal_id == self.assessed_producer.principal_id:
            raise ValueError(
                "verifier must not be the principal it assesses; the verifier cannot be writable by the "
                "implementation job (PL-042)"
            )
        if self.producer.principal_id == self.assessed_producer.principal_id:
            raise ValueError(
                "an attestation cannot be produced by the job it assesses; attestations are issued by the "
                "verifier, not filled in by the builder (PL-042)"
            )
        names = [check.name for check in self.checks]
        repeated = sorted({name for name in names if names.count(name) > 1})
        if repeated:
            raise ValueError(f"check names must be unique; repeated: {', '.join(repeated)}")
        failed = [check.name for check in self.checks if check.result is CheckOutcome.FAIL]
        if failed and self.result is not AttestationResult.FAIL:
            raise ValueError(f"result must be FAIL when any check failed; failed checks: {', '.join(failed)}")
        if self.result is AttestationResult.PASS:
            passing_at_level = [
                check.name
                for check in self.checks
                if check.result is CheckOutcome.PASS and check.level is self.level
            ]
            if not passing_at_level:
                raise ValueError(
                    f"a PASS attestation at level {self.level.value} needs at least one passing check at that "
                    "level; checks at lower levels cannot substitute (PL-043)"
                )
        return self

    def passed_checks(self) -> list[CheckResult]:
        """Checks that passed with evidence."""
        return [check for check in self.checks if check.result is CheckOutcome.PASS]


__all__ = ["CheckOutcome", "AttestationResult", "CheckResult", "VerificationAttestation"]
