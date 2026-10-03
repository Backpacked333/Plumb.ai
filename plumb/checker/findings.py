"""Findings shared by every local checker.

A checker never executes anything. It inspects persisted artifacts and returns
a :class:`CheckReport` whose findings are typed with the initial error classes
of the control-plane protocol (specification section 22). ``CheckReport.ok`` is
true only when no finding has severity ``ERROR``.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field

from plumb.contracts.common import ErrorClass, StrictModel


class Severity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class Finding(StrictModel):
    """One rule violation (or advisory) discovered by a checker."""

    code: str = Field(description="Stable machine code, e.g. DEPENDENCY_CYCLE.")
    error_class: ErrorClass
    message: str
    severity: Severity = Severity.ERROR
    step_id: str | None = Field(default=None, description="Build step this finding is about, if any.")
    subject_id: str | None = Field(
        default=None, description="Row, component or other subject identifier, if any."
    )
    details: dict[str, Any] = Field(default_factory=dict)

    def __str__(self) -> str:  # pragma: no cover - convenience
        where = f" [{self.step_id or self.subject_id}]" if (self.step_id or self.subject_id) else ""
        return f"{self.severity.value} {self.code} ({self.error_class.value}){where}: {self.message}"


class CheckReport(StrictModel):
    """Result of a checker run."""

    checker: str
    subject: str = Field(description="Identifier of the artifact that was checked.")
    findings: list[Finding] = Field(default_factory=list)
    topological_order: list[str] | None = Field(
        default=None, description="Step order when the checked graph is acyclic."
    )
    summary: dict[str, Any] = Field(default_factory=dict)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == Severity.WARNING]

    @property
    def ok(self) -> bool:
        return not self.errors

    def codes(self) -> set[str]:
        return {f.code for f in self.findings}

    def has(self, code: str) -> bool:
        return any(f.code == code for f in self.findings)

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    def render(self) -> str:
        lines = [f"{self.checker}: {self.subject}: {'OK' if self.ok else 'FAILED'}"]
        for finding in self.findings:
            lines.append("  " + str(finding))
        return "\n".join(lines)


__all__ = ["Severity", "Finding", "CheckReport"]
