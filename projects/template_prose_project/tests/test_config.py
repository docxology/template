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
