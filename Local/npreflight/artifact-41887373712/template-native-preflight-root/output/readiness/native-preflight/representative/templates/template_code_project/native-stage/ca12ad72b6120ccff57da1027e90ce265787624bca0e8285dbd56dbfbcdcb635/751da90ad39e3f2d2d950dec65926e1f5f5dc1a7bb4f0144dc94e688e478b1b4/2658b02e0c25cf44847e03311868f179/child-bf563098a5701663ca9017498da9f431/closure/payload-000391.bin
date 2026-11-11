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


def _as_int(value: object, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        return int(value)
    return default


def _as_float(value: object, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        return float(value)
    return default


@dataclass
class FileReport:
    """Per-file prose report."""

    name: str
    metrics: ProseMetrics
    structure: StructureReport
    quality: QualityReport

    def to_dict(self) -> dict[str, object]:
        """Serialize this object to a plain dict for JSON output."""
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
        """Serialize this object to a plain dict for JSON output."""
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
        """Serialize this object to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> ManuscriptReport:
        """Reconstruct a report from :meth:`to_dict` / on-disk JSON."""
        from infrastructure.prose.analysis import (
            Heading,
            ProseMetrics,
            QualityReport,
            Section,
            StructureReport,
        )

        files: list[FileReport] = []
        raw_files = payload.get("files")
        if not isinstance(raw_files, list):
            raw_files = []
        for f in raw_files:
            if not isinstance(f, Mapping):
                continue
            metrics_raw = f.get("metrics")
            if not isinstance(metrics_raw, Mapping):
                continue
            metrics = ProseMetrics(**dict(metrics_raw))
            s_data = f.get("structure")
            if not isinstance(s_data, Mapping):
                s_data = {}
            headings = [Heading(**dict(h)) for h in s_data.get("headings") or [] if isinstance(h, Mapping)]
            sections: list[Section] = []
            raw_sections = s_data.get("sections")
            if not isinstance(raw_sections, list):
                raw_sections = []
            for sec, hd in zip(raw_sections, headings):
                if not isinstance(sec, Mapping):
                    continue
                sections.append(
                    Section(
                        heading=hd,
                        body="",
                        word_count=int(sec.get("word_count", 0)),
                    )
                )
            struct = StructureReport(
                headings=headings,
                sections=sections,
                total_words=int(s_data.get("total_words", 0)),
                max_depth=int(s_data.get("max_depth", 0)),
                has_h1=bool(s_data.get("has_h1", False)),
                has_skipped_level=bool(s_data.get("has_skipped_level", False)),
            )
            q_data = f.get("quality")
            if not isinstance(q_data, Mapping):
                q_data = {}
            quality = QualityReport(
                passive_count=int(q_data.get("passive_count", 0)),
                passive_sentences=[str(x) for x in q_data.get("passive_sentences") or []],
                hedge_count=int(q_data.get("hedge_count", 0)),
                hedge_words=[str(x) for x in q_data.get("hedge_words") or []],
                citation_count=int(q_data.get("citation_count", 0)),
                citation_keys=[str(x) for x in q_data.get("citation_keys") or []],
                long_sentence_count=int(q_data.get("long_sentence_count", 0)),
                long_sentences=[str(x) for x in q_data.get("long_sentences") or []],
                word_count=int(q_data.get("word_count", 0)),
                citation_density_per_1000=float(q_data.get("citation_density_per_1000", 0.0)),
                hedge_density_per_1000=float(q_data.get("hedge_density_per_1000", 0.0)),
                passive_density_per_1000=float(q_data.get("passive_density_per_1000", 0.0)),
            )
            files.append(
                FileReport(
                    name=str(f.get("name", "")),
                    metrics=metrics,
                    structure=struct,
                    quality=quality,
                )
            )

        citation_keys_raw = payload.get("citation_keys")
        if not isinstance(citation_keys_raw, list):
            citation_keys_raw = []

        return cls(
            files=files,
            total_words=_as_int(payload.get("total_words")),
            total_sentences=_as_int(payload.get("total_sentences")),
            total_paragraphs=_as_int(payload.get("total_paragraphs")),
            avg_flesch_reading_ease=_as_float(payload.get("avg_flesch_reading_ease")),
            avg_flesch_kincaid_grade=_as_float(payload.get("avg_flesch_kincaid_grade")),
            avg_gunning_fog=_as_float(payload.get("avg_gunning_fog")),
            citation_keys=[str(x) for x in citation_keys_raw],
        )


def load_report_json(path: Path | str) -> ManuscriptReport:
    """Load a :class:`ManuscriptReport` from on-disk JSON."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Manuscript report JSON must be an object: {path}")
    return ManuscriptReport.from_dict(payload)


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
        analyze_text(name, text, long_sentence_threshold=long_sentence_threshold) for name, text in files.items()
    ]

    total_words = sum(f.metrics.word_count for f in file_reports)
    total_sentences = sum(f.metrics.sentence_count for f in file_reports)
    total_paragraphs = sum(f.metrics.paragraph_count for f in file_reports)

    def weighted(metric_key: str) -> float:
        """Return the weighted aggregate score."""
        num = round(
            sum(float(getattr(f.metrics, metric_key)) * float(f.metrics.word_count) for f in file_reports)
            / max(1, total_words),
            2,
        )
        return float(num)

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
