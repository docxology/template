"""Assay module: validate claims against evidence (the assaying stage).

An assay tests whether each manuscript claim has supporting evidence.
In metallurgy, assaying determines the gold content of a sample.
In manuscript composition, assaying verifies that every claim is backed
by a citation, figure, table, or computed artifact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class ClaimRecord:
    """A manuscript claim with its evidence status."""

    claim_id: str
    statement: str
    evidence_type: str  # "citation", "figure", "table", "computation", "none"
    evidence_ref: str
    supported: bool

    def __post_init__(self) -> None:
        if not self.claim_id:
            raise ValueError("claim_id must not be empty")
        if self.evidence_type not in ("citation", "figure", "table", "computation", "none"):
            raise ValueError(
                f"evidence_type must be one of citation/figure/table/computation/none, got '{self.evidence_type}'"
            )


@dataclass
class AssayReport:
    """Result of assaying a set of claims."""

    claims: list[ClaimRecord] = field(default_factory=list)

    @property
    def total_claims(self) -> int:
        return len(self.claims)

    @property
    def supported_claims(self) -> int:
        return sum(1 for c in self.claims if c.supported)

    @property
    def unsupported_claims(self) -> int:
        return sum(1 for c in self.claims if not c.supported)

    @property
    def support_rate(self) -> float:
        """Fraction of claims with supporting evidence."""
        if not self.claims:
            return 0.0
        return self.supported_claims / self.total_claims

    @property
    def assay_purity(self) -> float:
        """Purity fraction derived from claim support rate.

        A perfect assay (all claims supported) yields 1.0 purity.
        Each unsupported claim reduces purity proportionally.
        """
        return self.support_rate

    @property
    def is_passing(self) -> bool:
        """An assay passes when all claims are supported."""
        return self.unsupported_claims == 0 and self.total_claims > 0


def assay_claims(claims: Sequence[ClaimRecord]) -> AssayReport:
    """Run an assay on a sequence of claims.

    Returns an AssayReport summarizing support rates and purity.
    """
    return AssayReport(claims=list(claims))


def compute_assay_purity(claims: Sequence[ClaimRecord]) -> float:
    """Compute the purity fraction from an assay of claims.

    Convenience function: purity = supported_claims / total_claims.
    Returns 0.0 if no claims.
    """
    if not claims:
        return 0.0
    supported = sum(1 for c in claims if c.supported)
    return supported / len(claims)


__all__ = [
    "ClaimRecord",
    "AssayReport",
    "assay_claims",
    "compute_assay_purity",
]
