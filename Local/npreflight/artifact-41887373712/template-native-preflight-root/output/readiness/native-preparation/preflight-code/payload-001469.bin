"""Stable data models for publication-readiness reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class PublicationFinding:
    """One deterministic or advisory publication-audit finding."""

    project: str
    path: str
    diagnostic_code: str
    severity: str
    status: str
    message: str
    evidence: str = ""
    remediation: str = ""
    line: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return asdict(self)


@dataclass(frozen=True)
class PublicationAuditReport:
    """Repository-derived publication audit with deterministic serialization."""

    schema_version: str
    projects: tuple[str, ...]
    findings: tuple[PublicationFinding, ...] = field(default_factory=tuple)

    @property
    def blocking_findings(self) -> tuple[PublicationFinding, ...]:
        """Return findings that must block a strict publication gate."""
        return tuple(finding for finding in self.findings if finding.status == "fail")

    @property
    def review_findings(self) -> tuple[PublicationFinding, ...]:
        """Return non-blocking findings requiring human review."""
        return tuple(finding for finding in self.findings if finding.status == "review_required")

    @property
    def status(self) -> str:
        """Return pass, review, or fail."""
        if self.blocking_findings:
            return "fail"
        if self.review_findings:
            return "review"
        return "pass"

    def to_dict(self) -> dict[str, Any]:
        """Return a stable JSON payload without timestamps or machine paths."""
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "projects": list(self.projects),
            "summary": {
                "finding_count": len(self.findings),
                "blocking_count": len(self.blocking_findings),
                "review_required_count": len(self.review_findings),
            },
            "findings": [finding.to_dict() for finding in self.findings],
        }
