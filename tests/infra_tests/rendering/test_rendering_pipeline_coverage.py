"""Tests for infrastructure/rendering/pipeline.py.

Covers: pure helper functions (_resolve_manuscript_dir, _validate_latex_packages,
_log_manuscript_composition) that don't require LaTeX or pandoc.

No mocks used — all tests use real files, real dataclass instances, and real logic.
"""

from __future__ import annotations



from infrastructure.rendering.pipeline import (
    _resolve_manuscript_dir,
    _validate_latex_packages,
    _log_manuscript_composition,
)
from infrastructure.rendering.latex_validation import ValidationReport


class TestResolveManuscriptDir:
    """Test _resolve_manuscript_dir directory selection logic."""

    def test_prefers_injected_dir_with_md_files(self, tmp_path):
        """Should prefer output/manuscript/ when it has .md files."""
        project_root = tmp_path / "project"
        injected = project_root / "output" / "manuscript"
        injected.mkdir(parents=True)
        (injected / "01_intro.md").write_text("# Intro")
        (project_root / "manuscript").mkdir(parents=True)
        (project_root / "manuscript" / "01_intro.md").write_text("# Intro")

        result = _resolve_manuscript_dir(project_root)
        assert result == injected

    def test_fallback_to_manuscript_dir(self, tmp_path):
        """Should fall back to manuscript/ when injected dir has no .md files."""
        project_root = tmp_path / "project"
        (project_root / "output" / "manuscript").mkdir(parents=True)
        # No .md files in injected dir
        manuscript = project_root / "manuscript"
        manuscript.mkdir(parents=True)
        (manuscript / "01_intro.md").write_text("# Intro")

        result = _resolve_manuscript_dir(project_root)
        assert result == manuscript

    def test_fallback_when_injected_dir_absent(self, tmp_path):
        """Should fall back to manuscript/ when output/manuscript/ doesn't exist."""
        project_root = tmp_path / "project"
        manuscript = project_root / "manuscript"
        manuscript.mkdir(parents=True)

        result = _resolve_manuscript_dir(project_root)
        assert result == manuscript

    def test_returns_manuscript_path_even_if_nonexistent(self, tmp_path):
        """Should return manuscript/ path even when nothing exists."""
        project_root = tmp_path / "project"
        project_root.mkdir(parents=True)

        result = _resolve_manuscript_dir(project_root)
        assert result == project_root / "manuscript"


class TestValidateLatexPackages:
    """Test _validate_latex_packages with pre-built ValidationReport objects."""

    def test_all_packages_available(self):
        """Should return 0 when all required packages are available."""
        report = ValidationReport(
            all_required_available=True,
            required_packages=[],
            optional_packages=[],
            missing_required=[],
            missing_optional=[],
        )
        assert _validate_latex_packages(report=report) == 0

    def test_missing_required_packages(self):
        """Should return 1 when required packages are missing."""
        report = ValidationReport(
            all_required_available=False,
            required_packages=[],
            optional_packages=[],
            missing_required=["multirow", "cleveref"],
            missing_optional=[],
        )
        assert _validate_latex_packages(report=report) == 1

    def test_missing_optional_packages(self):
        """Should return 0 with warnings when optional packages are missing."""
        report = ValidationReport(
            all_required_available=True,
            required_packages=[],
            optional_packages=[],
            missing_required=[],
            missing_optional=["enumitem", "tcolorbox"],
        )
        assert _validate_latex_packages(report=report) == 0


class TestLogManuscriptComposition:
    """Test _log_manuscript_composition with real files."""

    def test_log_md_files(self, tmp_path):
        """Should log markdown file composition."""
        f1 = tmp_path / "01_intro.md"
        f1.write_text("# Introduction\n\nSome text here.\n")
        f2 = tmp_path / "02_methods.md"
        f2.write_text("# Methods\n\nMore detailed text.\n")

        # Should not raise
        _log_manuscript_composition([f1, f2])

    def test_log_tex_files(self, tmp_path):
        """Should log LaTeX file composition."""
        f1 = tmp_path / "preamble.tex"
        f1.write_text("\\documentclass{article}\n")

        _log_manuscript_composition([f1])

    def test_log_mixed_files(self, tmp_path):
        """Should log both markdown and LaTeX files."""
        f1 = tmp_path / "01_intro.md"
        f1.write_text("# Intro\n")
        f2 = tmp_path / "preamble.tex"
        f2.write_text("\\documentclass{article}\n")

        _log_manuscript_composition([f1, f2])

    def test_log_empty_list(self):
        """Should handle empty file list gracefully."""
        _log_manuscript_composition([])
