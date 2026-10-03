"""Aggregate state machines (specification section 23).

Implements:

* PL-057: every aggregate exposes a transition function with guards and a
  persisted, non-empty reason. A :class:`Transition` is the auditable record
  of one state change (``from_state``, ``to_state``, ``reason``, ``at`` and the
  guard that admitted it). Absent edges raise :class:`IllegalTransition`
  (``STATE_CONFLICT``); failed guards raise :class:`GuardFailed`, which is an
  :class:`IllegalTransition` carrying the guard name.
* Guards fixed by the specification and the design contract:

  - Build ``VERIFYING -> VERIFIED`` requires ``required_steps_verified`` (PL-016).
  - Build step ``VERIFYING -> VERIFIED`` requires a ``verifier_attestation``;
    a worker's completion claim is not enough (PL-016, PL-042).
  - Build step repair edges (``VERIFYING -> RUNNING``, ``FAILED -> READY``)
    require ``repair_budget_remaining`` (PL-018).
  - Collector ``PAUSED -> ACTIVE`` requires ``coverage_restored`` (PL-025).
  - Dataset ``MATERIALIZING -> VERIFIED`` requires ``checker_ok`` (PL-029);
    any dataset state may become ``UNAVAILABLE`` (PL-030).
  - Training ``PLANNED -> SUBMITTED`` requires ``submission_identity_persisted``
    (PL-033).
  - Release ``CANDIDATE -> VERIFIED`` requires ``attestations_accepted``; every
    edge into ``ACTIVE`` requires ``authority_current`` and
    ``attestations_accepted`` (PL-040, PL-043, PL-047).
  - Effect ``-> CONFIRMED`` requires an ``external_receipt``; ``UNKNOWN`` is left
    only through a matching ``reconciliation_result``; ``CONFIRMED ->
    COMPENSATED`` requires a ``compensation_receipt`` (PL-037, PL-038, PL-039,
    ADR-009).

Terminal states are derived from the edge set: a state with no outgoing edge
is terminal (Build VERIFIED/FAILED/CANCELLED, Effect FAILED_FINAL/COMPENSATED,
Release RETIRED, ...).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Generic, NamedTuple, TypeVar

from pydantic import AwareDatetime, ConfigDict

from plumb.contracts.common import (
    BuildState,
    BuildStepState,
    CollectorState,
    DatasetState,
    EffectState,
    ErrorClass,
    NonEmptyStr,
    ReleaseState,
    StrictModel,
    TrainingState,
    utcnow,
)

S = TypeVar("S", bound=Enum)


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------


class Guard(NamedTuple):
    """A named predicate over the transition context."""

    name: str
    predicate: Callable[[Mapping[str, Any]], bool]


def flag(*keys: str) -> Guard:
    """Guard satisfied when every named context key is exactly ``True``."""
    return Guard(" and ".join(keys), lambda context: all(context.get(key) is True for key in keys))


def present(key: str) -> Guard:
    """Guard satisfied when the named context key holds a truthy value (a receipt, an attestation)."""
    return Guard(key, lambda context: bool(context.get(key)))


def equals(key: str, value: object) -> Guard:
    """Guard satisfied when the named context key equals ``value``."""
    return Guard(f"{key} == {value!r}", lambda context: context.get(key) == value)


def all_of(*guards: Guard) -> Guard:
    """Guard satisfied when every component guard is satisfied."""
    return Guard(
        " and ".join(guard.name for guard in guards),
        lambda context: all(guard.predicate(context) for guard in guards),
    )


# ---------------------------------------------------------------------------
# Records and errors
# ---------------------------------------------------------------------------


class Transition(StrictModel):
    """Auditable record of one state change (PL-057)."""

    model_config = ConfigDict(frozen=True)

    machine: str
    from_state: str
    to_state: str
    reason: NonEmptyStr
    at: AwareDatetime
    guard: str | None = None


class StateMachineError(Exception):
    """Base class for state-machine errors."""


class UnknownState(StateMachineError, ValueError):
    """A value that is not a state of the machine was supplied."""


class MissingReason(StateMachineError, ValueError):
    """A transition was requested without a reason (PL-057)."""


class IllegalTransition(StateMachineError):
    """The requested edge does not exist for this aggregate (``STATE_CONFLICT``)."""

    error_class: ErrorClass = ErrorClass.STATE_CONFLICT

    def __init__(self, machine: str, from_state: str, to_state: str, detail: str | None = None) -> None:
        self.machine = machine
        self.from_state = from_state
        self.to_state = to_state
        self.detail = detail
        message = f"{machine}: no transition {from_state} -> {to_state}"
        super().__init__(f"{message} ({detail})" if detail else message)


class GuardFailed(IllegalTransition):
    """The edge exists but its guard rejected the context; carries the guard name."""

    def __init__(self, machine: str, from_state: str, to_state: str, guard_name: str) -> None:
        self.guard_name = guard_name
        super().__init__(machine, from_state, to_state, detail=f"guard failed: {guard_name}")


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------


class StateMachine(Generic[S]):
    """An aggregate lifecycle: a closed set of states and guarded edges between them."""

    def __init__(
        self,
        name: str,
        states: type[S],
        transitions: Mapping[tuple[S, S], Guard | None],
    ) -> None:
        for source, target in transitions:
            if not isinstance(source, states) or not isinstance(target, states):
                raise ValueError(f"{name}: edge {source!r} -> {target!r} uses a state outside {states.__name__}")
            if source is target:
                raise ValueError(f"{name}: self-loop on {source.value} is not a transition")
        self.name = name
        self.states = states
        self._transitions: Mapping[tuple[S, S], Guard | None] = MappingProxyType(dict(transitions))

    def _as_state(self, value: S | str) -> S:
        if isinstance(value, self.states):
            return value
        try:
            return self.states(value)
        except ValueError as exc:
            raise UnknownState(f"{self.name}: {value!r} is not a {self.states.__name__}") from exc

    def edges(self) -> list[tuple[S, S]]:
        """All edges, in definition order."""
        return list(self._transitions)

    def has_edge(self, current: S | str, target: S | str) -> bool:
        return (self._as_state(current), self._as_state(target)) in self._transitions

    def guard_for(self, current: S | str, target: S | str) -> Guard | None:
        """The guard on an edge (``None`` when unguarded); raises :class:`IllegalTransition` if absent."""
        source, destination = self._as_state(current), self._as_state(target)
        if (source, destination) not in self._transitions:
            raise IllegalTransition(self.name, source.value, destination.value)
        return self._transitions[(source, destination)]

    def targets_from(self, current: S | str) -> frozenset[S]:
        source = self._as_state(current)
        return frozenset(target for origin, target in self._transitions if origin is source)

    def terminal_states(self) -> frozenset[S]:
        """States with no outgoing edge."""
        sources = {origin for origin, _ in self._transitions}
        return frozenset(state for state in self.states if state not in sources)

    def is_terminal(self, state: S | str) -> bool:
        return self._as_state(state) in self.terminal_states()

    def transition(
        self,
        current: S | str,
        target: S | str,
        context: Mapping[str, Any] | None,
        reason: str,
        *,
        at: datetime | None = None,
    ) -> Transition:
        """Validate and describe the move ``current -> target``.

        Raises :class:`MissingReason` for an empty reason, :class:`IllegalTransition`
        for an absent edge and :class:`GuardFailed` when the edge's guard rejects
        ``context``. The caller persists the returned :class:`Transition`.
        """
        if not reason or not reason.strip():
            raise MissingReason(f"{self.name}: a transition requires a non-empty reason")
        source, destination = self._as_state(current), self._as_state(target)
        if (source, destination) not in self._transitions:
            detail = f"{source.value} is terminal" if self.is_terminal(source) else None
            raise IllegalTransition(self.name, source.value, destination.value, detail)
        guard = self._transitions[(source, destination)]
        if guard is not None and not guard.predicate(context or {}):
            raise GuardFailed(self.name, source.value, destination.value, guard.name)
        return Transition(
            machine=self.name,
            from_state=source.value,
            to_state=destination.value,
            reason=reason,
            at=at if at is not None else utcnow(),
            guard=guard.name if guard is not None else None,
        )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"StateMachine({self.name!r}, {self.states.__name__}, {len(self._transitions)} edges)"


def _unguarded(pairs: Iterable[tuple[S, S]]) -> dict[tuple[S, S], Guard | None]:
    return {pair: None for pair in pairs}


def _fan_in(sources: Iterable[S], target: S) -> dict[tuple[S, S], Guard | None]:
    """Unguarded edges from each source into one target (cancellation, retirement, ...)."""
    return _unguarded((source, target) for source in sources)


# ---------------------------------------------------------------------------
# Build (section 23, PL-016)
# ---------------------------------------------------------------------------

_B = BuildState
BUILD: StateMachine[BuildState] = StateMachine(
    "build",
    BuildState,
    {
        **_unguarded(
            [
                (_B.DRAFT, _B.VALIDATED),
                (_B.VALIDATED, _B.RUNNING),
                (_B.RUNNING, _B.WAITING_AUTH),
                (_B.WAITING_AUTH, _B.RUNNING),
                (_B.RUNNING, _B.WAITING_INPUT),
                (_B.WAITING_INPUT, _B.RUNNING),
                (_B.RUNNING, _B.VERIFYING),
                (_B.VERIFYING, _B.RUNNING),  # repair after a failed verification
                (_B.VERIFYING, _B.FAILED),
                (_B.RUNNING, _B.FAILED),
                (_B.WAITING_AUTH, _B.FAILED),  # dependency refused or expired
                (_B.WAITING_INPUT, _B.FAILED),
            ]
        ),
        (_B.VERIFYING, _B.VERIFIED): flag("required_steps_verified"),
        **_fan_in(
            [_B.DRAFT, _B.VALIDATED, _B.RUNNING, _B.WAITING_AUTH, _B.WAITING_INPUT, _B.VERIFYING],
            _B.CANCELLED,
        ),
    },
)

# ---------------------------------------------------------------------------
# Build step (section 23, PL-016, PL-018, PL-042)
# ---------------------------------------------------------------------------

_S = BuildStepState
REPAIR_BUDGET_GUARD = flag("repair_budget_remaining")
BUILD_STEP: StateMachine[BuildStepState] = StateMachine(
    "build_step",
    BuildStepState,
    {
        **_unguarded(
            [
                (_S.PENDING, _S.READY),
                (_S.READY, _S.RUNNING),
                (_S.RUNNING, _S.VERIFYING),
                (_S.VERIFYING, _S.FAILED),
                (_S.RUNNING, _S.FAILED),
                (_S.RUNNING, _S.BLOCKED),  # dependency raised
                (_S.BLOCKED, _S.READY),  # dependency resolved
                (_S.BLOCKED, _S.FAILED),  # dependency unresolvable
            ]
        ),
        (_S.VERIFYING, _S.VERIFIED): present("verifier_attestation"),
        (_S.VERIFYING, _S.RUNNING): REPAIR_BUDGET_GUARD,
        (_S.FAILED, _S.READY): REPAIR_BUDGET_GUARD,
        **_fan_in([_S.PENDING, _S.READY, _S.RUNNING, _S.VERIFYING, _S.BLOCKED, _S.FAILED], _S.CANCELLED),
    },
)

# ---------------------------------------------------------------------------
# Collector (section 23, PL-024, PL-025)
# ---------------------------------------------------------------------------

_C = CollectorState
COLLECTOR: StateMachine[CollectorState] = StateMachine(
    "collector",
    CollectorState,
    {
        **_unguarded(
            [
                (_C.PLANNED, _C.SHADOW),
                (_C.SHADOW, _C.BACKFILLING),
                (_C.BACKFILLING, _C.RECONCILING),
                (_C.RECONCILING, _C.BACKFILLING),  # reconciliation found gaps
                (_C.RECONCILING, _C.ACTIVE),
                (_C.ACTIVE, _C.DEGRADED),
                (_C.DEGRADED, _C.ACTIVE),
                (_C.ACTIVE, _C.PAUSED),
                (_C.DEGRADED, _C.PAUSED),
            ]
        ),
        (_C.PAUSED, _C.ACTIVE): flag("coverage_restored"),
        **_fan_in(
            [_C.PLANNED, _C.SHADOW, _C.BACKFILLING, _C.RECONCILING, _C.ACTIVE, _C.DEGRADED, _C.PAUSED],
            _C.RETIRED,
        ),
    },
)

# ---------------------------------------------------------------------------
# Dataset (section 23, PL-029, PL-030)
# ---------------------------------------------------------------------------

_D = DatasetState
DATASET: StateMachine[DatasetState] = StateMachine(
    "dataset",
    DatasetState,
    {
        **_unguarded(
            [
                (_D.PROPOSED, _D.MATERIALIZING),
                (_D.MATERIALIZING, _D.QUARANTINED),
                (_D.QUARANTINED, _D.MATERIALIZING),
                (_D.VERIFIED, _D.SUPERSEDED),
            ]
        ),
        (_D.MATERIALIZING, _D.VERIFIED): flag("checker_ok"),
        **_fan_in([_D.PROPOSED, _D.MATERIALIZING, _D.QUARANTINED, _D.VERIFIED, _D.SUPERSEDED], _D.UNAVAILABLE),
    },
)

# ---------------------------------------------------------------------------
# Training (section 23, PL-033)
# ---------------------------------------------------------------------------

_T = TrainingState
TRAINING: StateMachine[TrainingState] = StateMachine(
    "training",
    TrainingState,
    {
        (_T.PLANNED, _T.SUBMITTED): flag("submission_identity_persisted"),
        **_unguarded(
            [
                (_T.SUBMITTED, _T.RUNNING),
                (_T.SUBMITTED, _T.FAILED),  # provider rejected the submission
                (_T.RUNNING, _T.CANDIDATE),
                (_T.RUNNING, _T.FAILED),
            ]
        ),
        **_fan_in([_T.PLANNED, _T.SUBMITTED, _T.RUNNING], _T.CANCELLED),
    },
)

# ---------------------------------------------------------------------------
# Release (section 23, PL-040, PL-043, PL-047)
# ---------------------------------------------------------------------------

_R = ReleaseState
RELEASE_ACTIVE_GUARD = flag("authority_current", "attestations_accepted")
RELEASE: StateMachine[ReleaseState] = StateMachine(
    "release",
    ReleaseState,
    {
        (_R.CANDIDATE, _R.VERIFIED): flag("attestations_accepted"),
        **_unguarded(
            [
                (_R.VERIFIED, _R.SHADOW),
                (_R.SHADOW, _R.CANARY),
                (_R.ACTIVE, _R.PAUSED),
                (_R.CANARY, _R.ROLLED_BACK),
                (_R.ACTIVE, _R.ROLLED_BACK),
                (_R.PAUSED, _R.ROLLED_BACK),
            ]
        ),
        (_R.CANARY, _R.ACTIVE): RELEASE_ACTIVE_GUARD,
        (_R.PAUSED, _R.ACTIVE): RELEASE_ACTIVE_GUARD,
        **_fan_in(
            [_R.CANDIDATE, _R.VERIFIED, _R.SHADOW, _R.CANARY, _R.ACTIVE, _R.PAUSED, _R.ROLLED_BACK],
            _R.RETIRED,
        ),
    },
)

# ---------------------------------------------------------------------------
# Effect (section 16, section 23, PL-037..PL-039, ADR-009)
# ---------------------------------------------------------------------------

_E = EffectState
EFFECT: StateMachine[EffectState] = StateMachine(
    "effect",
    EffectState,
    {
        **_unguarded(
            [
                (_E.RESERVED, _E.DISPATCHED),
                (_E.RESERVED, _E.FAILED_FINAL),  # released without dispatch
                (_E.DISPATCHED, _E.UNKNOWN),  # timeout / ambiguous outcome
                (_E.DISPATCHED, _E.FAILED_FINAL),  # provider definitively rejected the request
            ]
        ),
        (_E.DISPATCHED, _E.CONFIRMED): present("external_receipt"),
        (_E.UNKNOWN, _E.CONFIRMED): all_of(equals("reconciliation_result", "CONFIRMED"), present("external_receipt")),
        (_E.UNKNOWN, _E.FAILED_FINAL): equals("reconciliation_result", "FAILED_FINAL"),
        (_E.CONFIRMED, _E.COMPENSATED): present("compensation_receipt"),
    },
)

MACHINES: Mapping[str, StateMachine[Any]] = MappingProxyType(
    {machine.name: machine for machine in (BUILD, BUILD_STEP, COLLECTOR, DATASET, TRAINING, RELEASE, EFFECT)}
)
"""All aggregate machines keyed by aggregate name."""


def machine_for(aggregate_name: str) -> StateMachine[Any]:
    """Look up a machine by aggregate name (``build``, ``build_step``, ``collector``, ...).

    Case-insensitive; spaces and hyphens are treated as underscores, so
    ``"Build step"`` and ``"build-step"`` both resolve to :data:`BUILD_STEP`.
    """
    key = aggregate_name.strip().lower().replace("-", "_").replace(" ", "_")
    try:
        return MACHINES[key]
    except KeyError:
        raise KeyError(f"unknown aggregate {aggregate_name!r}; known aggregates: {', '.join(MACHINES)}") from None


__all__ = [
    "Guard",
    "flag",
    "present",
    "equals",
    "all_of",
    "Transition",
    "StateMachineError",
    "UnknownState",
    "MissingReason",
    "IllegalTransition",
    "GuardFailed",
    "StateMachine",
    "REPAIR_BUDGET_GUARD",
    "RELEASE_ACTIVE_GUARD",
    "BUILD",
    "BUILD_STEP",
    "COLLECTOR",
    "DATASET",
    "TRAINING",
    "RELEASE",
    "EFFECT",
    "MACHINES",
    "machine_for",
]
