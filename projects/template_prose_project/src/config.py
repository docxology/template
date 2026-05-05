"""Typed access to ``manuscript/config.yaml`` for the prose project."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ProseAnalysisConfig:
    """Knobs for the prose-analysis stage."""

    target_grade_level_min: float = 10.0
    target_grade_level_max: float = 18.0
    long_sentence_threshold: int = 35
    citation_density_min_per_1000: float = 0.0
    require_h1_per_section: bool = True
    forbid_skipped_levels: bool = True


@dataclass
class BibliographyConfig:
    """Knobs for the citation-bibliography cross-check."""

    references_path: str = "manuscript/references.bib"
    fail_on_missing: bool = True
    fail_on_unused: bool = False


@dataclass
class ReportConfig:
    """Final review-report assembly."""

    output_path: str = "output/review_report.md"
    include_per_file_table: bool = True
    include_outline: bool = True
    include_quality_flags: bool = True


@dataclass
class ProjectConfig:
    """Top-level prose-project configuration."""

    title: str
    authors: list[dict[str, str]] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    manuscript_dir: str = "manuscript"
    prose: ProseAnalysisConfig = field(default_factory=ProseAnalysisConfig)
    bibliography: BibliographyConfig = field(default_factory=BibliographyConfig)
    report: ReportConfig = field(default_factory=ReportConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectConfig":
        paper = data.get("paper", {}) or {}
        prose_raw = data.get("prose", {}) or {}
        bib_raw = data.get("bibliography", {}) or {}
        report_raw = data.get("report", {}) or {}

        return cls(
            title=str(paper.get("title") or "Prose Review Project"),
            authors=list(data.get("authors") or []),
            keywords=list(data.get("keywords") or []),
            manuscript_dir=str(data.get("manuscript_dir") or "manuscript"),
            prose=ProseAnalysisConfig(
                target_grade_level_min=float(prose_raw.get("target_grade_level_min", 10.0)),
                target_grade_level_max=float(prose_raw.get("target_grade_level_max", 18.0)),
                long_sentence_threshold=int(prose_raw.get("long_sentence_threshold", 35)),
                citation_density_min_per_1000=float(prose_raw.get("citation_density_min_per_1000", 0.0)),
                require_h1_per_section=bool(prose_raw.get("require_h1_per_section", True)),
                forbid_skipped_levels=bool(prose_raw.get("forbid_skipped_levels", True)),
            ),
            bibliography=BibliographyConfig(
                references_path=str(bib_raw.get("references_path") or "manuscript/references.bib"),
                fail_on_missing=bool(bib_raw.get("fail_on_missing", True)),
                fail_on_unused=bool(bib_raw.get("fail_on_unused", False)),
            ),
            report=ReportConfig(
                output_path=str(report_raw.get("output_path") or "output/review_report.md"),
                include_per_file_table=bool(report_raw.get("include_per_file_table", True)),
                include_outline=bool(report_raw.get("include_outline", True)),
                include_quality_flags=bool(report_raw.get("include_quality_flags", True)),
            ),
        )


def load_project_config(path: Path | str) -> ProjectConfig:
    """Load a :class:`ProjectConfig` from *path* (YAML)."""
    text = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config {path} must be a YAML mapping at the top level")
    return ProjectConfig.from_dict(data)
