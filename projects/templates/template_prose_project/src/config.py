"""Typed access to ``manuscript/config.yaml`` for the prose project.

The loader is **strict**: unknown top-level keys, unknown nested keys
under ``prose``/``bibliography``/``report``, and out-of-band invariants
(e.g. ``target_grade_level_min`` ≥ ``target_grade_level_max``) raise
``ValueError`` with both the offending value and the allowed set quoted
in the message. This is the public contract documented in
``docs/faq.md``; ``tests/test_config.py`` asserts on substrings of those
messages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Known-key registries (kept here so the validator is the single source of
# truth; if you add a field below, list its YAML key here too).
# ---------------------------------------------------------------------------

_KNOWN_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
    {
        "paper",
        "authors",
        "publication",  # accepted-but-ignored (forward-compat with sibling)
        "keywords",
        "metadata",  # accepted-but-ignored (forward-compat with sibling)
        "manuscript_dir",
        "prose",
        "bibliography",
        "report",
        "render",  # accepted-but-ignored (parsed by infrastructure.rendering.config)
    }
)
_KNOWN_PROSE_KEYS: frozenset[str] = frozenset(
    {
        "target_grade_level_min",
        "target_grade_level_max",
        "long_sentence_threshold",
        "citation_density_min_per_1000",
        "require_h1_per_section",
        "forbid_skipped_levels",
        "preset",
    }
)


# Named editorial profiles. A ``prose.preset`` key applies these defaults for
# any knob the YAML does not set explicitly; explicit keys always win.
# "lenient" is the bundled exemplar's permissive band (its own abstract must
# pass its own gate); "strict" is the forkable starting point also shown in
# manuscript/config.yaml.example.
PROSE_PRESETS: dict[str, dict[str, float | int | bool]] = {
    "lenient": {
        "target_grade_level_min": 10.0,
        "target_grade_level_max": 18.0,
        "long_sentence_threshold": 35,
        "citation_density_min_per_1000": 0.0,
        "require_h1_per_section": True,
        "forbid_skipped_levels": True,
    },
    "strict": {
        "target_grade_level_min": 12.0,
        "target_grade_level_max": 16.0,
        "long_sentence_threshold": 30,
        "citation_density_min_per_1000": 3.0,
        "require_h1_per_section": True,
        "forbid_skipped_levels": True,
    },
}
_KNOWN_BIBLIOGRAPHY_KEYS: frozenset[str] = frozenset({"references_path", "fail_on_missing", "fail_on_unused"})
_KNOWN_REPORT_KEYS: frozenset[str] = frozenset(
    {"output_path", "include_per_file_table", "include_outline", "include_quality_flags"}
)


def _validate_keys(section: str, raw: dict[str, Any], allowed: frozenset[str]) -> None:
    """Raise ValueError if ``raw`` contains any key not in ``allowed``."""
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise ValueError(f"Unknown {section} key(s) in config: {unknown}. Allowed: {sorted(allowed)}")


@dataclass
class ProseAnalysisConfig:
    """Knobs for the prose-analysis stage."""

    target_grade_level_min: float = 10.0
    target_grade_level_max: float = 18.0
    long_sentence_threshold: int = 35
    citation_density_min_per_1000: float = 0.0
    require_h1_per_section: bool = True
    forbid_skipped_levels: bool = True
    preset: str | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ProseAnalysisConfig":
        """Build from a ``prose:`` YAML mapping, applying a named preset first.

        A ``preset`` key selects a profile from :data:`PROSE_PRESETS`; any
        knob explicitly present in *raw* wins over the preset value. An
        unknown preset name raises ``ValueError`` with the allowed set
        quoted, matching the strict-loader contract.
        """
        preset_name = raw.get("preset")
        if preset_name is not None:
            if preset_name not in PROSE_PRESETS:
                raise ValueError(
                    f"Unknown prose preset {preset_name!r}. Allowed: {sorted(PROSE_PRESETS)}"
                )
            values = dict(PROSE_PRESETS[preset_name])
            values.update({k: v for k, v in raw.items() if k != "preset"})
        else:
            values = dict(raw)
        return cls(
            target_grade_level_min=float(values.get("target_grade_level_min", 10.0)),
            target_grade_level_max=float(values.get("target_grade_level_max", 18.0)),
            long_sentence_threshold=int(values.get("long_sentence_threshold", 35)),
            citation_density_min_per_1000=float(values.get("citation_density_min_per_1000", 0.0)),
            require_h1_per_section=bool(values.get("require_h1_per_section", True)),
            forbid_skipped_levels=bool(values.get("forbid_skipped_levels", True)),
            preset=preset_name,
        )

    def __post_init__(self) -> None:
        if self.target_grade_level_min >= self.target_grade_level_max:
            raise ValueError(
                f"target_grade_level_min ({self.target_grade_level_min}) must be < "
                f"target_grade_level_max ({self.target_grade_level_max})"
            )
        if self.long_sentence_threshold <= 0:
            raise ValueError(f"long_sentence_threshold must be > 0, got {self.long_sentence_threshold}")
        if self.citation_density_min_per_1000 < 0:
            raise ValueError(f"citation_density_min_per_1000 must be ≥ 0, got {self.citation_density_min_per_1000}")


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
        """Process from dict."""
        _validate_keys("top-level", data, _KNOWN_TOP_LEVEL_KEYS)
        paper = data.get("paper", {}) or {}
        prose_raw = data.get("prose", {}) or {}
        bib_raw = data.get("bibliography", {}) or {}
        report_raw = data.get("report", {}) or {}
        _validate_keys("prose", prose_raw, _KNOWN_PROSE_KEYS)
        _validate_keys("bibliography", bib_raw, _KNOWN_BIBLIOGRAPHY_KEYS)
        _validate_keys("report", report_raw, _KNOWN_REPORT_KEYS)

        return cls(
            title=str(paper.get("title") or "Prose Review Project"),
            authors=list(data.get("authors") or []),
            keywords=list(data.get("keywords") or []),
            manuscript_dir=str(data.get("manuscript_dir") or "manuscript"),
            prose=ProseAnalysisConfig.from_dict(prose_raw),
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
