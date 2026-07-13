"""Project-owned prose report contracts — no infrastructure imports.

Protocol definitions (``ManuscriptReportLike``, ``FileReportLike``, …)
decouple ``src/`` from ``infrastructure/prose`` so the domain layer stays
importable without the full infrastructure tree.

Two free functions live here for the same reason:

* :func:`render_outline` — format a :class:`StructureReportLike` as a
  plain-text bulleted outline without touching infrastructure.
* :func:`parse_bib_keys` — extract BibTeX citation keys via a lightweight
  regex so :mod:`src.pipeline.checks` can cross-check citations without
  importing :mod:`infrastructure.reference.citation`.  The full
  ``infrastructure.reference.citation.parse_bibfile`` parser is used by the
  scripts layer and handles all BibTeX dialect edge-cases; this helper is
  deliberately minimal and is used only for the cross-check gate.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class ProseMetricsLike(Protocol):
    """Data container for ProseMetricsLike."""

    word_count: int
    sentence_count: int
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    gunning_fog: float


@runtime_checkable
class QualityReportLike(Protocol):
    """Data container for QualityReportLike."""

    citation_count: int
    citation_density_per_1000: float
    hedge_count: int
    hedge_words: list[str]
    long_sentence_count: int
    passive_count: int
    word_count: int


@runtime_checkable
class StructureReportLike(Protocol):
    """Data container for StructureReportLike."""

    has_skipped_level: bool
    has_h1: bool
    headings: list[object]


@runtime_checkable
class FileReportLike(Protocol):
    """Data container for FileReportLike."""

    name: str
    metrics: ProseMetricsLike
    quality: QualityReportLike
    structure: StructureReportLike


@runtime_checkable
class ManuscriptReportLike(Protocol):
    """Data container for ManuscriptReportLike."""

    files: list[FileReportLike]
    total_words: int
    total_sentences: int
    total_paragraphs: int
    avg_flesch_reading_ease: float
    avg_flesch_kincaid_grade: float
    avg_gunning_fog: float
    citation_keys: list[str]

    def to_dict(self) -> dict[str, object]:
        """Serialize this object to a plain dict for JSON output."""
        ...


@dataclass(frozen=True)
class HeadingView:
    """Lightweight heading snapshot for rendering and testing."""

    level: int
    title: str


def render_outline(structure: StructureReportLike) -> str:
    """Render a structure report as a plain-text bulleted outline.

    Each heading is indented by ``2 * (level - 1)`` spaces so the outline
    mirrors the logical nesting of the document.  Falls back to
    ``str(heading)`` when the heading object has no ``title`` attribute
    (rare in practice but possible when adapting non-standard protocols).
    """
    lines: list[str] = []
    for heading in structure.headings:
        level = int(getattr(heading, "level", 1))
        title = str(getattr(heading, "title", heading))
        indent = "  " * (level - 1)
        lines.append(f"{indent}- {title}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# BibTeX key extraction
# ---------------------------------------------------------------------------
# Matches @<entrytype>{<key>, … — intentionally excludes @comment blocks
# because @comment{…} bodies are free-form text, not citation keys.
# For full BibTeX dialect support use infrastructure.reference.citation.parse_bibfile.
# ---------------------------------------------------------------------------

_BIB_KEY_RE = re.compile(
    r"@(?!comment\b)[A-Za-z]+\s*\{\s*([^,\s]+)",
    re.MULTILINE | re.IGNORECASE,
)


def parse_bib_keys(bib_path: Path) -> set[str]:
    """Extract citation keys from a BibTeX file without infrastructure.

    Uses a lightweight regex rather than a full BibTeX parser.  ``@comment``
    blocks are skipped so preamble comments do not produce spurious keys.

    Args:
        bib_path: Path to the ``.bib`` file.  Returns an empty set when the
            path does not point to an existing file (e.g. the bib is missing
            or the path points to a directory).

    Returns:
        Set of citation key strings found in the file.  For production use
        prefer :func:`infrastructure.reference.citation.parse_bibfile`, which
        handles the full BibTeX dialect.
    """
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
