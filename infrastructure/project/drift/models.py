"""Data models for template drift detection."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Finding:
    """Data container for Finding."""

    severity: str  # "ERROR" or "WARNING"
    project: str
    rule: str
    message: str


@dataclass
class Report:
    """Data container for Report."""

    findings: list[Finding] = field(default_factory=list)

    def add(self, sev: str, project: str, rule: str, message: str) -> None:
        """Add a finding to the report."""
        self.findings.append(Finding(sev, project, rule, message))

    def errors(self) -> list[Finding]:
        """Return the list of errors."""
        return [f for f in self.findings if f.severity == "ERROR"]

    def warnings(self) -> list[Finding]:
        """Return the list of warnings."""
        return [f for f in self.findings if f.severity == "WARNING"]
