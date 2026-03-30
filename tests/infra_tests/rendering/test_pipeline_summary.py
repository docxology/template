"""Tests for infrastructure/rendering/_pipeline_summary.py.

Tests rendering pipeline summary and verification utilities.
Follows No Mocks Policy — all tests use real files and real execution.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.rendering._pipeline_summary import (
    _check_citations_used,
    generate_rendering_summary,
    log_rendering_summary,
    verify_pdf_outputs,
)


class TestGenerateRenderingSummary:
    """Test generate_rendering_summary() using real directory structures."""

    def test_returns_dict_with_expected_keys(self, tmp_path: Path) -> None:
        summary = generate_rendering_summary("nonexistent_project_xyz")
        assert "project" in summary
        assert "individual_pdfs" in summary
        assert "combined_pdf" in summary
        assert "combined_html" in summary
        assert "web_outputs" in summary
        assert "slides" in summary
        assert "total_size_kb" in summary

    def test_project_name_in_summary(self, tmp_path: Path) -> None:
        summary = generate_rendering_summary("nonexistent_project_xyz")
        assert summary["project"] == "nonexistent_project_xyz"

    def test_empty_summary_for_missing_project(self) -> None:
        """Missing project returns empty lists and zero size."""
        summary = generate_rendering_summary("_totally_missing_project_abc")
        assert summary["individual_pdfs"] == []
        assert summary["combined_pdf"] is None
        assert summary["combined_html"] is None
        assert summary["web_outputs"] == []
        assert summary["slides"] == []
        assert summary["total_size_kb"] == 0


class TestCheckCitationsUsed:
    """Test _check_citations_used() with real markdown files."""

    def test_returns_false_for_empty_directory(self, tmp_path: Path) -> None:
        assert _check_citations_used(tmp_path) is False

    def test_detects_cite_command(self, tmp_path: Path) -> None:
        (tmp_path / "section.md").write_text(r"See \cite{smith2020} for details.")
        assert _check_citations_used(tmp_path) is True

    def test_detects_citep_command(self, tmp_path: Path) -> None:
        (tmp_path / "section.md").write_text(r"As noted \citep{jones2019}")
        assert _check_citations_used(tmp_path) is True

    def test_no_citations_in_plain_text(self, tmp_path: Path) -> None:
        (tmp_path / "section.md").write_text("This is a plain text file without citations.")
        assert _check_citations_used(tmp_path) is False

    def test_ignores_non_md_files(self, tmp_path: Path) -> None:
        (tmp_path / "notes.txt").write_text(r"See \cite{smith2020}")
        assert _check_citations_used(tmp_path) is False

    def test_handles_supplemental_subdirectory(self, tmp_path: Path) -> None:
        supplemental = tmp_path / "supplemental"
        supplemental.mkdir()
        (supplemental / "appendix.md").write_text(r"\citet{author2021}")
        assert _check_citations_used(tmp_path) is True

    def test_handles_unreadable_file_gracefully(self, tmp_path: Path) -> None:
        """OSError on one file should not crash the check."""
        (tmp_path / "good.md").write_text("No citations here.")
        bad = tmp_path / "bad.md"
        bad.write_text("content")
        bad.chmod(0o000)
        try:
            result = _check_citations_used(tmp_path)
            assert isinstance(result, bool)
        finally:
            bad.chmod(0o644)


class TestLogRenderingSummary:
    """Test log_rendering_summary() — verifies it does not raise."""

    def test_logs_empty_summary_without_error(self) -> None:
        summary = {
            "project": "test_proj",
            "combined_pdf": None,
            "combined_html": None,
            "individual_pdfs": [],
            "web_outputs": [],
            "slides": [],
            "total_size_kb": 0,
        }
        log_rendering_summary(summary)  # should not raise

    def test_logs_full_summary_without_error(self) -> None:
        summary = {
            "project": "test_proj",
            "combined_pdf": {"name": "test_combined.pdf", "size_kb": 512.0, "path": "/out/test.pdf"},
            "combined_html": {"name": "index.html", "size_kb": 64.0, "path": "/out/index.html"},
            "individual_pdfs": [{"name": "01_intro.pdf", "size_kb": 128.0}],
            "web_outputs": [{"name": "01_intro.html", "size_kb": 32.0}],
            "slides": [{"name": "intro_slides.pdf", "size_kb": 256.0}],
            "total_size_kb": 992.0,
        }
        log_rendering_summary(summary)  # should not raise


class TestVerifyPdfOutputs:
    """Test verify_pdf_outputs() with real temp paths."""

    def test_returns_false_for_missing_pdf_dir(self) -> None:
        result = verify_pdf_outputs("_nonexistent_project_xyz")
        assert result is False
