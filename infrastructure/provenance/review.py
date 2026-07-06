"""Provenance review — severity-graded findings over the DAG.

Provides a :class:`Review` class that records :class:`Finding` objects
against specific provenance nodes, with a severity system inspired by code
review workflows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """Severity level for a review finding."""

    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


@dataclass(frozen=True)
class Finding:
    """A single review finding attached to a provenance node.

    Attributes:
        node_id: The provenance node this finding is about.
        severity: Severity level.
        code: Short machine-readable identifier, e.g. ``"missing_hash"``.
        message: Human-readable description.
        metadata: Optional extra context.
    """

    node_id: str
    severity: Severity
    code: str
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "metadata": dict(self.metadata),
        }


@dataclass
class ReviewResult:
    """Aggregated result of a review pass.

    Attributes:
        passed: ``True`` when no ``error`` or ``critical`` findings were raised.
        findings: All findings across all nodes.
    """

    findings: list[Finding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """``True`` when no error or critical findings are present."""
        return not any(f.severity in (Severity.error, Severity.critical) for f in self.findings)

    def by_severity(self, severity: Severity) -> list[Finding]:
        """Return findings filtered by *severity*."""
        return [f for f in self.findings if f.severity == severity]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "findings": [f.to_dict() for f in self.findings],
        }


class Review:
    """Accumulator for provenance review findings.

    Usage::

        review = Review()
        review.record(Finding(
            node_id="abc123",
            severity=Severity.warning,
            code="missing_abstract",
            message="Source node has no abstract.",
        ))
        result = review.result()
        print(result.passed)  # True (only a warning)
    """

    def __init__(self) -> None:
        self._findings: list[Finding] = []

    def record(self, finding: Finding) -> None:
        """Add *finding* to this review."""
        self._findings.append(finding)

    def findings_for_node(self, node_id: str) -> list[Finding]:
        """Return all findings for *node_id*."""
        return [f for f in self._findings if f.node_id == node_id]

    def result(self) -> ReviewResult:
        """Materialise a :class:`ReviewResult` from accumulated findings."""
        return ReviewResult(findings=list(self._findings))

    def clear(self) -> None:
        """Remove all accumulated findings."""
        self._findings.clear()

    def __len__(self) -> int:
        return len(self._findings)

    def __repr__(self) -> str:
        return f"Review(findings={len(self._findings)})"


def review_provenance_store(store: Any) -> ReviewResult:
    """Run a standard review pass over a :class:`~Provenance` store.

    Checks performed:

    * Every :class:`~infrastructure.provenance.models.ArtifactNode` should
      have a ``content_hash``.
    * Every :class:`~infrastructure.provenance.models.SourceNode` should
      have a non-empty ``uri``.
    * Every :class:`~infrastructure.provenance.models.ClaimNode` should have
      a ``confidence`` > 0.
    * Every :class:`~infrastructure.provenance.models.RunNode` should record
      an ``exit_code``.

    Args:
        store: A :class:`~infrastructure.provenance.store.Provenance` instance.

    Returns:
        A :class:`ReviewResult`.
    """
    from infrastructure.provenance.models import (
        ArtifactNode,
        ClaimNode,
        RunNode,
        SourceNode,
    )

    review = Review()
    for node in store.list():
        if isinstance(node, ArtifactNode) and not node.content_hash:
            review.record(
                Finding(
                    node_id=node.node_id,
                    severity=Severity.warning,
                    code="missing_hash",
                    message=f"ArtifactNode '{node.label}' has no content_hash.",
                )
            )
        elif isinstance(node, SourceNode) and not node.uri:
            review.record(
                Finding(
                    node_id=node.node_id,
                    severity=Severity.error,
                    code="missing_uri",
                    message=f"SourceNode '{node.label}' has no URI.",
                )
            )
        elif isinstance(node, ClaimNode) and node.confidence <= 0.0:
            review.record(
                Finding(
                    node_id=node.node_id,
                    severity=Severity.warning,
                    code="zero_confidence",
                    message=f"ClaimNode '{node.label}' has confidence=0.",
                )
            )
        elif isinstance(node, RunNode) and node.exit_code is None:
            review.record(
                Finding(
                    node_id=node.node_id,
                    severity=Severity.info,
                    code="missing_exit_code",
                    message=f"RunNode '{node.label}' has no exit_code.",
                )
            )
    return review.result()


__all__ = [
    "Finding",
    "Review",
    "ReviewResult",
    "Severity",
    "review_provenance_store",
]
