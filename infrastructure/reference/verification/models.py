"""Data models for reference-existence verification.

These models back a deterministic anti-hallucination gate: given the references
a manuscript *claims* to cite (parsed from its ``.bib`` file), resolve each one
against external bibliographic indices (Crossref / OpenAlex / arXiv) and report
whether the cited work actually exists and whether its metadata matches.

The status taxonomy is a deterministically-checkable distillation of the
five-way hallucination taxonomy described by the Academic Research Skills
project (https://github.com/Imbad0202/academic-research-skills, CC-BY-NC-4.0):
*truth fabrication*, *partial appropriation*, *implied/parametric/semantic
hallucination*. We map those qualitative categories onto what a ``.bib`` entry
plus an index lookup can prove or disprove. No ARS code is vendored; this is an
original, Apache-2.0 implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "BLOCKING_STATUSES",
    "ReferenceVerdict",
    "VerificationReport",
    "VerificationStatus",
]


class VerificationStatus(str, Enum):
    """Outcome of verifying one cited reference.

    Ordering note: this is *not* a severity ordinal; callers decide which
    statuses block via :data:`BLOCKING_STATUSES`.
    """

    OK = "ok"
    """Resolved against an index and the metadata matches the cited entry."""

    MISMATCH = "mismatch"
    """Resolved, but title / author / year disagree beyond tolerance — the
    citation points at a real record that is not the one described (partial
    appropriation / semantic distortion)."""

    FABRICATED = "fabricated"
    """A resolvable identifier (DOI or arXiv id) was present but no index
    returned a matching record — the cited work does not appear to exist
    (truth fabrication)."""

    UNVERIFIABLE = "unverifiable"
    """No resolvable identifier and a title search was inconclusive — cannot be
    confirmed or refuted. A warning, not a pass."""

    UNCHECKED = "unchecked"
    """Offline (network disabled) and not in cache — deliberately distinct from
    OK so a skipped check never launders into a clean result."""

    ANACHRONISM = "anachronism"
    """Temporal-integrity failure: the cited year post-dates the manuscript /
    as-of year, i.e. the manuscript cites a work not yet published."""


# Statuses that should fail a verification gate by default. UNVERIFIABLE and
# UNCHECKED are honest "could not confirm" outcomes and warn rather than fail.
BLOCKING_STATUSES: frozenset[VerificationStatus] = frozenset(
    {
        VerificationStatus.FABRICATED,
        VerificationStatus.MISMATCH,
        VerificationStatus.ANACHRONISM,
    }
)


@dataclass
class ReferenceVerdict:
    """The verification result for a single cited reference."""

    citation_key: str
    status: VerificationStatus
    detail: str
    doi: str | None = None
    arxiv_id: str | None = None
    resolved_via: str | None = None
    """Which index confirmed the record: ``crossref`` / ``openalex`` /
    ``arxiv`` / ``cache`` / ``None`` when unresolved."""
    title_similarity: float | None = None
    issues: list[str] = field(default_factory=list)

    @property
    def is_ok(self) -> bool:
        return self.status is VerificationStatus.OK

    @property
    def is_blocking(self) -> bool:
        return self.status in BLOCKING_STATUSES

    def to_dict(self) -> dict[str, Any]:
        return {
            "citation_key": self.citation_key,
            "status": self.status.value,
            "detail": self.detail,
            "doi": self.doi,
            "arxiv_id": self.arxiv_id,
            "resolved_via": self.resolved_via,
            "title_similarity": self.title_similarity,
            "issues": list(self.issues),
        }


@dataclass
class VerificationReport:
    """Aggregate report over every cited reference in a manuscript."""

    verdicts: list[ReferenceVerdict] = field(default_factory=list)
    network_used: bool = False

    def counts(self) -> dict[str, int]:
        """Return a status → count map covering every status (zeros included)."""
        out = {s.value: 0 for s in VerificationStatus}
        for verdict in self.verdicts:
            out[verdict.status.value] += 1
        return out

    @property
    def blocking(self) -> list[ReferenceVerdict]:
        return [v for v in self.verdicts if v.is_blocking]

    @property
    def has_blocking(self) -> bool:
        return any(v.is_blocking for v in self.verdicts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "network_used": self.network_used,
            "counts": self.counts(),
            "has_blocking": self.has_blocking,
            "verdicts": [v.to_dict() for v in self.verdicts],
        }

    def summary_line(self) -> str:
        """One-line human summary, e.g. ``42 refs: 38 ok, 1 fabricated, ...``."""
        counts = self.counts()
        parts = [f"{counts[s.value]} {s.value}" for s in VerificationStatus if counts[s.value]]
        total = len(self.verdicts)
        body = ", ".join(parts) if parts else "none"
        return f"{total} refs: {body}"
