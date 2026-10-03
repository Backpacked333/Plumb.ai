"""Guarded state transitions (SR-010, SR-011).

A transition is legal only if (state, event) exists in the table and every named guard returns True for the
supplied context. A failed guard is a refusal with the guard's name; an absent (state, event) pair is an
InvalidTransition. The engine never mutates aggregates itself: it returns a TransitionResult that the owning
service must persist atomically together with the listed writes (SR-012).

Guards are plain callables `guard(ctx: dict) -> bool` registered per machine. Unregistered guards fail closed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import yaml

TABLE_DIR = Path(__file__).resolve().parents[2] / "contracts" / "state-machines"

Guard = Callable[[dict], bool]


class InvalidTransition(Exception):
    def __init__(self, machine: str, state: str, event: str):
        super().__init__(f"{machine}: no transition for ({state}, {event})")
        self.machine, self.state, self.event = machine, state, event


class GuardFailed(Exception):
    def __init__(self, machine: str, state: str, event: str, guard: str, to_state: str):
        super().__init__(f"{machine}: ({state}, {event}) -> {to_state} refused by guard {guard}")
        self.guard, self.to_state = guard, to_state


class AmbiguousTransition(Exception):
    pass


@dataclass
class Transition:
    from_state: str
    event: str
    to_state: str
    guards: list[str]
    writes: list[str]
    emits: list[str]
    external_effects: str
    retryable: bool


@dataclass
class TransitionResult:
    machine: str
    from_state: str
    event: str
    to_state: str
    writes: list[str]
    emits: list[str]
    external_effects: str
    retryable: bool
    reason: str
    guards_passed: list[str] = field(default_factory=list)


class GuardedMachine:
    def __init__(self, name: str, table: dict, guards: dict[str, Guard]):
        self.name = name
        self.initial: str = table["initial"]
        self.terminal: set[str] = set(table["terminal"])
        self.states: list[str] = list(table["states"])
        self.transitions: list[Transition] = [
            Transition(
                from_state=t["from"],
                event=t["event"],
                to_state=t["to"],
                guards=list(t.get("guards", [])),
                writes=list(t.get("writes", [])),
                emits=list(t.get("emits", [])),
                external_effects=str(t.get("external_effects", "none")),
                retryable=bool(t.get("retryable", False)),
            )
            for t in table["transitions"]
        ]
        self.guards = guards
        self._check_table()

    @classmethod
    def load(cls, machine_file: str, guards: Optional[dict[str, Guard]] = None) -> "GuardedMachine":
        table = yaml.safe_load((TABLE_DIR / machine_file).read_text())
        return cls(table["machine"], table, guards or {})

    def _check_table(self) -> None:
        st = set(self.states)
        if self.initial not in st:
            raise ValueError(f"{self.name}: initial state missing")
        for t in self.transitions:
            if t.from_state not in st or t.to_state not in st:
                raise ValueError(f"{self.name}: transition references unknown state {t}")
            if t.from_state in self.terminal:
                raise ValueError(f"{self.name}: terminal state {t.from_state} has outgoing transition")
        reachable = {self.initial}
        changed = True
        while changed:
            changed = False
            for t in self.transitions:
                if t.from_state in reachable and t.to_state not in reachable:
                    reachable.add(t.to_state)
                    changed = True
        unreachable = st - reachable
        if unreachable:
            raise ValueError(f"{self.name}: unreachable states {sorted(unreachable)}")

    def candidates(self, state: str, event: str) -> list[Transition]:
        return [t for t in self.transitions if t.from_state == state and t.event == event]

    def fire(self, state: str, event: str, ctx: dict, reason: str) -> TransitionResult:
        """Evaluate guards; exactly one candidate must pass. Fail closed on unregistered guards."""
        if state in self.terminal:
            raise InvalidTransition(self.name, state, event)
        cands = self.candidates(state, event)
        if not cands:
            raise InvalidTransition(self.name, state, event)
        passing: list[tuple[Transition, list[str]]] = []
        last_failure: Optional[GuardFailed] = None
        for t in cands:
            ok, passed = True, []
            for g in t.guards:
                fn = self.guards.get(g)
                if fn is None or not fn(ctx):
                    ok = False
                    last_failure = GuardFailed(self.name, state, event, g, t.to_state)
                    break
                passed.append(g)
            if ok:
                passing.append((t, passed))
        if not passing:
            assert last_failure is not None
            raise last_failure
        if len(passing) > 1:
            raise AmbiguousTransition(f"{self.name}: ({state}, {event}) matched {len(passing)} transitions")
        t, passed = passing[0]
        if not reason or not reason.strip():
            raise ValueError("a persisted reason is required for every transition")
        return TransitionResult(
            machine=self.name,
            from_state=state,
            event=event,
            to_state=t.to_state,
            writes=t.writes,
            emits=t.emits,
            external_effects=t.external_effects,
            retryable=t.retryable,
            reason=reason,
            guards_passed=passed,
        )
