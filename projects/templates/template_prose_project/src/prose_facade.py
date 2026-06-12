"""Project-owned prose report contracts — no infrastructure imports."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class ProseMetricsLike(Protocol):
    word_count: int
    sentence_count: int
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    gunning_fog: float


@runtime_checkable
class QualityReportLike(Protocol):
    citation_count: int
    citation_density_per_1000: float
    hedge_count: int
    hedge_words: list[str]
    long_sentence_count: int
    passive_count: int
    word_count: int


@runtime_checkable
class StructureReportLike(Protocol):
    has_skipped_level: bool
    has_h1: bool
    headings: list[object]


@runtime_checkable
class FileReportLike(Protocol):
    name: str
    metrics: ProseMetricsLike
    quality: QualityReportLike
    structure: StructureReportLike


@runtime_checkable
class ManuscriptReportLike(Protocol):
    files: list[FileReportLike]
    total_words: int
    total_sentences: int
    total_paragraphs: int
    avg_flesch_reading_ease: float
    avg_flesch_kincaid_grade: float
    avg_gunning_fog: float
    citation_keys: list[str]

    def to_dict(self) -> dict[str, object]: ...


@dataclass(frozen=True)
class HeadingView:
    level: int
    title: str


def render_outline(structure: StructureReportLike) -> str:
    """Render a structure report as a plain-text bulleted outline."""
    lines: list[str] = []
    for heading in structure.headings:
        level = int(getattr(heading, "level", 1))
        title = str(getattr(heading, "title", heading))
        indent = "  " * (level - 1)
        lines.append(f"{indent}- {title}")
    return "\n".join(lines)


_BIB_KEY_RE = re.compile(r"@[A-Za-z]+\s*\{\s*([^,\s]+)", re.MULTILINE)


def parse_bib_keys(bib_path: Path) -> set[str]:
    """Extract citation keys from a BibTeX file without infrastructure."""
    if not bib_path.is_file():
        return set()
    text = bib_path.read_text(encoding="utf-8", errors="replace")
    return set(_BIB_KEY_RE.findall(text))


__all__ = [
    "FileReportLike",
    "HeadingView",
    "ManuscriptReportLike",
    "ProseMetricsLike",
    "QualityReportLike",
    "StructureReportLike",
    "parse_bib_keys",
    "render_outline",
]
