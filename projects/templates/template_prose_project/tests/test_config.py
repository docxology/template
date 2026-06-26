"""Tests for src.config — typed YAML loader."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from src.config import (
    BibliographyConfig,
    ProjectConfig,
    ProseAnalysisConfig,
    ReportConfig,
    load_project_config,
)


def _write(path: Path, body: str) -> Path:
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


def test_minimal_config(tmp_path: Path):
    cfg = _write(
        tmp_path / "config.yaml",
        """
        paper:
          title: "Demo"
        """,
    )
    config = load_project_config(cfg)
    assert config.title == "Demo"
    assert config.prose.target_grade_level_min == 10.0
    assert config.bibliography.fail_on_missing is True


def test_explicit_thresholds(tmp_path: Path):
    cfg = _write(
        tmp_path / "config.yaml",
        """
        paper: {title: "X"}
        prose:
          target_grade_level_min: 8.0
          target_grade_level_max: 14.0
          long_sentence_threshold: 20
          citation_density_min_per_1000: 7.5
        bibliography:
          fail_on_missing: false
          fail_on_unused: true
        """,
    )
    config = load_project_config(cfg)
    assert config.prose.target_grade_level_min == 8.0
    assert config.prose.target_grade_level_max == 14.0
    assert config.prose.long_sentence_threshold == 20
    assert config.prose.citation_density_min_per_1000 == 7.5
    assert config.bibliography.fail_on_missing is False
    assert config.bibliography.fail_on_unused is True


def test_top_level_must_be_mapping(tmp_path: Path):
    cfg = _write(tmp_path / "config.yaml", "- not\n- a\n- mapping\n")
    with pytest.raises(ValueError, match="mapping"):
        load_project_config(cfg)


def test_direct_construction():
    config = ProjectConfig(
        title="X",
        prose=ProseAnalysisConfig(target_grade_level_min=5.0),
        bibliography=BibliographyConfig(references_path="refs.bib"),
        report=ReportConfig(),
    )
    assert config.prose.target_grade_level_min == 5.0
    assert config.bibliography.references_path == "refs.bib"


def test_report_keys(tmp_path: Path):
    cfg = _write(
        tmp_path / "config.yaml",
        """
        paper: {title: "X"}
        report:
          output_path: "custom/path.md"
          include_outline: false
        """,
    )
    config = load_project_config(cfg)
    assert config.report.output_path == "custom/path.md"
    assert config.report.include_outline is False


def test_unknown_top_level_key_rejected(tmp_path: Path):
    """Strict loader: a typoed top-level key surfaces, doesn't silently drop."""
    cfg = _write(
        tmp_path / "config.yaml",
        """
        paper: {title: "X"}
        prose_typo:
          target_grade_level_min: 8.0
        """,
    )
    with pytest.raises(ValueError, match=r"Unknown top-level key\(s\) in config: \['prose_typo'\]"):
        load_project_config(cfg)


def test_unknown_prose_key_rejected(tmp_path: Path):
    """Strict loader: a typoed nested prose key surfaces."""
    cfg = _write(
        tmp_path / "config.yaml",
        """
        paper: {title: "X"}
        prose:
          target_grade_level_minimum: 8.0   # typo: should be target_grade_level_min
        """,
    )
    with pytest.raises(ValueError, match=r"Unknown prose key\(s\)"):
        load_project_config(cfg)


def test_unknown_bibliography_key_rejected(tmp_path: Path):
    cfg = _write(
        tmp_path / "config.yaml",
        """
        paper: {title: "X"}
        bibliography:
          references_path: "manuscript/refs.bib"
          fail_on_missin: true   # typo
        """,
    )
    with pytest.raises(ValueError, match=r"Unknown bibliography key"):
        load_project_config(cfg)


def test_unknown_report_key_rejected(tmp_path: Path):
    cfg = _write(
        tmp_path / "config.yaml",
        """
        paper: {title: "X"}
        report:
          include_outliner: false   # typo
        """,
    )
    with pytest.raises(ValueError, match=r"Unknown report key"):
        load_project_config(cfg)


def test_grade_level_invariant_min_lt_max():
    """ProseAnalysisConfig __post_init__ rejects min >= max."""
    with pytest.raises(ValueError, match=r"target_grade_level_min .* must be < target_grade_level_max"):
        ProseAnalysisConfig(target_grade_level_min=20.0, target_grade_level_max=10.0)


def test_long_sentence_threshold_must_be_positive():
    """ProseAnalysisConfig __post_init__ rejects threshold ≤ 0."""
    with pytest.raises(ValueError, match=r"long_sentence_threshold must be > 0"):
        ProseAnalysisConfig(long_sentence_threshold=0)


def test_citation_density_must_be_nonneg():
    """ProseAnalysisConfig __post_init__ rejects negative citation density."""
    with pytest.raises(ValueError, match=r"citation_density_min_per_1000 must be ≥ 0"):
        ProseAnalysisConfig(citation_density_min_per_1000=-1.0)


def test_known_top_level_metadata_keys_accepted(tmp_path: Path):
    """Accepted-but-ignored keys (publication, metadata) don't trigger the strict gate."""
    cfg = _write(
        tmp_path / "config.yaml",
        """
        paper: {title: "X"}
        publication:
          doi: "10.5281/zenodo.000"
          year: "2026"
        metadata:
          license: "MIT"
        """,
    )
    config = load_project_config(cfg)
    assert config.title == "X"


class TestConfigNegativeControls:
    """Negative controls for config validation — every invalid input must raise
    ValueError with a message that identifies the offending key or value.

    Guards against the failure mode where a typo or unknown key silently
    drops configuration without surfacing an error.
    """

    def test_grade_level_min_equals_max_rejected(self):
        """min == max is invalid (not strictly less than)."""
        with pytest.raises(ValueError, match=r"must be <"):
            ProseAnalysisConfig(target_grade_level_min=12.0, target_grade_level_max=12.0)

    def test_long_sentence_threshold_negative_rejected(self):
        with pytest.raises(ValueError, match=r"must be > 0"):
            ProseAnalysisConfig(long_sentence_threshold=-5)

    def test_citation_density_exactly_zero_accepted(self):
        """Zero is a valid floor (disables the check)."""
        cfg = ProseAnalysisConfig(citation_density_min_per_1000=0.0)
        assert cfg.citation_density_min_per_1000 == 0.0

    def test_empty_yaml_produces_defaults(self, tmp_path: Path):
        """An empty YAML file must produce default values, not raise."""
        cfg = _write(tmp_path / "config.yaml", "")
        config = load_project_config(cfg)
        assert config.title == "Prose Review Project"
        assert config.prose.target_grade_level_min == 10.0

    def test_null_paper_section_uses_default_title(self, tmp_path: Path):
        """paper: null → title defaults to 'Prose Review Project'."""
        cfg = _write(
            tmp_path / "config.yaml",
            """
            paper: ~
            """,
        )
        config = load_project_config(cfg)
        assert config.title == "Prose Review Project"

    def test_null_prose_section_uses_defaults(self, tmp_path: Path):
        """prose: null → all prose thresholds default."""
        cfg = _write(
            tmp_path / "config.yaml",
            """
            paper: {title: "X"}
            prose: ~
            """,
        )
        config = load_project_config(cfg)
        assert config.prose.target_grade_level_min == 10.0
        assert config.prose.long_sentence_threshold == 35

    def test_unknown_bibliography_key_message_names_offender(self, tmp_path: Path):
        """Error message must quote the offending key so the fork author knows what to fix."""
        cfg = _write(
            tmp_path / "config.yaml",
            """
            paper: {title: "X"}
            bibliography:
              totally_unknown_key: true
            """,
        )
        with pytest.raises(ValueError, match=r"totally_unknown_key"):
            load_project_config(cfg)

    def test_render_key_is_ignored_not_rejected(self, tmp_path: Path):
        """render: is accepted-but-ignored (parsed by infrastructure.rendering.config)."""
        cfg = _write(
            tmp_path / "config.yaml",
            """
            paper: {title: "X"}
            render:
              formats:
                pdf: true
                html: false
            """,
        )
        config = load_project_config(cfg)
        assert config.title == "X"

    def test_from_dict_rejects_list_at_top_level(self, tmp_path: Path):
        """A YAML file whose root is a list raises ValueError (not mapping)."""
        cfg = _write(tmp_path / "config.yaml", "- a\n- b\n")
        with pytest.raises(ValueError, match="mapping"):
            load_project_config(cfg)

    def test_from_dict_all_known_report_keys(self, tmp_path: Path):
        """All four known report keys round-trip without error."""
        cfg = _write(
            tmp_path / "config.yaml",
            """
            paper: {title: "X"}
            report:
              output_path: "out/r.md"
              include_per_file_table: false
              include_outline: false
              include_quality_flags: false
            """,
        )
        config = load_project_config(cfg)
        assert config.report.output_path == "out/r.md"
        assert config.report.include_per_file_table is False
        assert config.report.include_outline is False
        assert config.report.include_quality_flags is False
