"""Aggregate prose reports across a whole manuscript.

Run :func:`analyze_manuscript` over a manuscript directory and get back
a :class:`ManuscriptReport` whose JSON form is suitable for CI artefacts
or downstream rendering.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from infrastructure.prose.analysis import (
    ProseMetrics,
    QualityReport,
    StructureReport,
    analyze_quality,
    analyze_structure,
    compute_metrics,
)
from infrastructure.prose.markdown import normalise_for_prose, read_manuscript_dir


@dataclass
class FileReport:
    """Per-file prose report."""

    name: str
    metrics: ProseMetrics
    structure: StructureReport
    quality: QualityReport

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "metrics": self.metrics.to_dict(),
            "structure": self.structure.to_dict(),
            "quality": self.quality.to_dict(),
        }


@dataclass
class ManuscriptReport:
    """Aggregate report for an entire manuscript directory."""

    files: list[FileReport] = field(default_factory=list)
    total_words: int = 0
    total_sentences: int = 0
    total_paragraphs: int = 0
    avg_flesch_reading_ease: float = 0.0
    avg_flesch_kincaid_grade: float = 0.0
    avg_gunning_fog: float = 0.0
    citation_keys: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "total_words": self.total_words,
            "total_sentences": self.total_sentences,
            "total_paragraphs": self.total_paragraphs,
            "avg_flesch_reading_ease": self.avg_flesch_reading_ease,
            "avg_flesch_kincaid_grade": self.avg_flesch_kincaid_grade,
            "avg_gunning_fog": self.avg_gunning_fog,
            "citation_keys": list(self.citation_keys),
            "files": [f.to_dict() for f in self.files],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


def analyze_text(
    name: str,
    raw_text: str,
    *,
    long_sentence_threshold: int = 35,
) -> FileReport:
    """Analyze a single text blob and return a :class:`FileReport`.

    Args:
        name: File name for the report (used as the report key).
        raw_text: Raw markdown text to analyse.
        long_sentence_threshold: Sentences with strictly more than this
            many words are flagged as long sentences in the
            :class:`QualityReport`. Default ``35``.
    """
    plain = normalise_for_prose(raw_text)
    return FileReport(
        name=name,
        metrics=compute_metrics(plain),
        structure=analyze_structure(raw_text),
        quality=analyze_quality(plain, long_sentence_threshold=long_sentence_threshold),
    )


def analyze_files(
    files: Mapping[str, str],
    *,
    long_sentence_threshold: int = 35,
) -> ManuscriptReport:
    """Build a :class:`ManuscriptReport` from a ``{filename: text}`` mapping.

    Args:
        files: Mapping of ``filename → markdown text``.
        long_sentence_threshold: Forwarded to :func:`analyze_text`.
    """
    file_reports = [
        analyze_text(name, text, long_sentence_threshold=long_sentence_threshold)
        for name, text in files.items()
    ]

    total_words = sum(f.metrics.word_count for f in file_reports)
    total_sentences = sum(f.metrics.sentence_count for f in file_reports)
    total_paragraphs = sum(f.metrics.paragraph_count for f in file_reports)

    n = max(1, len(file_reports))
    weighted = lambda key: round(
        sum(getattr(f.metrics, key) * f.metrics.word_count for f in file_reports)
        / max(1, total_words),
        2,
    )
    avg_fre = weighted("flesch_reading_ease") if total_words else 0.0
    avg_fkgl = weighted("flesch_kincaid_grade") if total_words else 0.0
    avg_fog = weighted("gunning_fog") if total_words else 0.0

    citation_keys: list[str] = []
    seen: set[str] = set()
    for f in file_reports:
        for k in f.quality.citation_keys:
            if k not in seen:
                seen.add(k)
                citation_keys.append(k)

    return ManuscriptReport(
        files=file_reports,
        total_words=total_words,
        total_sentences=total_sentences,
        total_paragraphs=total_paragraphs,
        avg_flesch_reading_ease=avg_fre,
        avg_flesch_kincaid_grade=avg_fkgl,
        avg_gunning_fog=avg_fog,
        citation_keys=citation_keys,
    )


def analyze_manuscript(
    manuscript_dir: Path | str,
    *,
    long_sentence_threshold: int = 35,
) -> ManuscriptReport:
    """Read every Markdown file in *manuscript_dir* and analyse it.

    Args:
        manuscript_dir: Directory containing markdown files.
        long_sentence_threshold: Words-per-sentence cutoff above which
            a sentence is flagged as long. Forwarded to
            :func:`analyze_files`.
    """
    files = read_manuscript_dir(manuscript_dir)
    return analyze_files(files, long_sentence_threshold=long_sentence_threshold)


def write_report(report: ManuscriptReport, output_path: Path | str) -> Path:
    """Persist *report* as pretty-printed JSON."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report.to_json(), encoding="utf-8")
    return out
