"""Typed, secret-free promotion reports shared by promotion contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SecurityTodoFinding:
    """A location-only security TODO finding safe to print publicly."""

    finding_id: str
    path: str
    line: int


@dataclass(frozen=True)
class PromotionGateReport:
    """Result of evaluating one candidate and its security attestation."""

    project: str
    attestation: str
    findings: tuple[SecurityTodoFinding, ...]
    errors: tuple[str, ...]

    @property
    def eligible(self) -> bool:
        """Return whether the candidate satisfies every security condition."""
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-serializable representation."""
        return {
            "project": self.project,
            "attestation": self.attestation,
            "eligible": self.eligible,
            "findings": [asdict(finding) for finding in self.findings],
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class PromotionAttestation:
    """Validated, non-secret promotion evidence for orchestration."""

    project: str
    source_commit: str
    reviewer: str
    checks: dict[str, bool]
    risk_acceptance: dict[str, str] | None

    @property
    def approved(self) -> bool:
        """Return whether promotion is complete or explicitly risk-accepted."""
        return all(self.checks.values()) or self.risk_acceptance is not None

    def to_dict(self) -> dict[str, object]:
        """Return a stable, secret-free representation for audit output."""
        return {
            "project": self.project,
            "source_commit": self.source_commit,
            "reviewer": self.reviewer,
            **self.checks,
            "risk_acceptance": self.risk_acceptance,
            "approved": self.approved,
        }


@dataclass(frozen=True)
class PromotionCompositeReport:
    """Combined orchestration-attestation and candidate-security result."""

    attestation: PromotionAttestation
    security: PromotionGateReport

    @property
    def eligible(self) -> bool:
        """Return true only when both independent contracts pass."""
        return self.attestation.approved and self.security.eligible

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-safe aggregate without source content."""
        return {
            "eligible": self.eligible,
            "attestation": self.attestation.to_dict(),
            "security": self.security.to_dict(),
        }


__all__ = [
    "PromotionAttestation",
    "PromotionCompositeReport",
    "PromotionGateReport",
    "SecurityTodoFinding",
]
