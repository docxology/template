"""Dataclasses for area corpus, handbook structure, and synthesis results."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """Thematic bucket used to route evidence into handbook sections."""

    id: str
    label: str
    description: str


@dataclass(frozen=True)
class EvidenceItem:
    """Single piece of reviewed evidence tied to a theme."""

    id: str
    statement: str
    theme: str
    weight: float
    source_label: str
    reviewed_at: str


@dataclass(frozen=True)
class AreaCorpus:
    """Versioned collection of themes and evidence for one area."""

    area_id: str
    area_label: str
    version: str
    themes: tuple[Theme, ...]
    evidence: tuple[EvidenceItem, ...]


@dataclass(frozen=True)
class HandbookSection:
    """One handbook chapter with optional theme linkage."""

    section_id: str
    title: str
    depth: int
    theme_ids: tuple[str, ...]


@dataclass(frozen=True)
class SynthesisResult:
    """Outline plus per-section evidence rollups and gap analysis."""

    corpus: AreaCorpus
    sections: tuple[HandbookSection, ...]
    evidence_by_section: dict[str, tuple[EvidenceItem, ...]]
    gaps: tuple[str, ...]
    scores: dict[str, float]
    gap_threshold: float
