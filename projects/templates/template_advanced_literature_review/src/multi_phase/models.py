"""Data models for phase-aware literature-search provenance."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from literature.models import Paper


@dataclass
class PhaseMetadata:
    """Metadata for a search phase execution."""

    phase_id: str
    name: str
    description: str
    start_time: float
    end_time: float | None = None
    queries_executed: list[str] = field(default_factory=list)
    papers_discovered: int = 0
    papers_after_deterministic_filters: int = 0
    papers_after_llm_filters: int = 0
    papers_final: int = 0
    deterministic_filters_applied: dict[str, Any] = field(default_factory=dict)
    llm_filters_applied: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)


@dataclass
class PhasedPaper:
    """A paper plus the phase-level provenance accumulated for it."""

    paper: Paper
    discovered_in_phase: str
    phases_found_in: list[str] = field(default_factory=list)
    deterministic_filters_passed: dict[str, bool] = field(default_factory=dict)
    llm_filters_passed: dict[str, str] = field(default_factory=dict)
    cross_phase_citations: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure the discovery phase is always present in provenance."""
        if self.discovered_in_phase not in self.phases_found_in:
            self.phases_found_in.insert(0, self.discovered_in_phase)


__all__ = ["PhaseMetadata", "PhasedPaper"]
