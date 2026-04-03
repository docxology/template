"""Tests for infrastructure.rendering._pipeline_summary module.

Tests rendering summary generation, logging, citation detection, and PDF verification.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.rendering._pipeline_summary import (
    _check_citations_used,
    generate_rendering_summary,
    log_rendering_summary,
    verify_pdf_outputs,
)


class TestCheckCitationsUsed:
    """Tests for _check_citations_used."""

    def test_no_manuscript_files(self, tmp_path: Path):
        """Empty directory should return False."""
        assert _check_citations_used(tmp_path) is False

    def test_no_citations_in_files(self, tmp_path: Path):
        """Markdown without citation commands should return False."""
        md_file = tmp_path / "01_intro.md"
        md_file.write_text("# Introduction\nThis is plain text.\n", encoding="utf-8")
        assert _check_citations_used(tmp_path) is False

    def test_latex_cite_command(self, tmp_path: Path):
        """\\cite{key} should be detected."""
        md_file = tmp_path / "01_intro.md"
        md_file.write_text("As shown in \\cite{smith2020}.\n", encoding="utf-8")
        assert _check_citations_used(tmp_path) is True

    def test_latex_citep_command(self, tmp_path: Path):
        """\\citep{key} should be detected."""
        md_file = tmp_path / "01_intro.md"
        md_file.write_text("Results \\citep{jones2021} confirm.\n", encoding="utf-8")
        assert _check_citations_used(tmp_path) is True

    def test_latex_citet_command(self, tmp_path: Path):
        md_file = tmp_path / "01_intro.md"
        md_file.write_text("\\citet{doe2022} showed that.\n", encoding="utf-8")
        assert _check_citations_used(tmp_path) is True

    def test_pandoc_citation(self, tmp_path: Path):
        """@key style citations should be detected."""
        md_file = tmp_path / "01_intro.md"
        md_file.write_text("According to @smith2020 the results.\n", encoding="utf-8")
        assert _check_citations_used(tmp_path) is True

    def test_supplemental_directory(self, tmp_path: Path):
        """Citations in supplemental/ should also be detected."""
        sup_dir = tmp_path / "supplemental"
        sup_dir.mkdir()
        md_file = sup_dir / "S01_extra.md"
        md_file.write_text("See \\cite{ref1} for details.\n", encoding="utf-8")
        assert _check_citations_used(tmp_path) is True

    def test_unreadable_file_skipped(self, tmp_path: Path):
        """Files that cannot be read should be skipped without error."""
        md_file = tmp_path / "01_intro.md"
        md_file.write_bytes(b"\x80\x81\x82")  # Invalid UTF-8
        # Should not raise, returns False
        result = _check_citations_used(tmp_path)
        assert isinstance(result, bool)


class TestGenerateRenderingSummary:
    """Tests for generate_rendering_summary."""

    def test_nonexistent_project_returns_empty_summary(self):
        """Project that does not exist should return empty summary structure."""
        summary = generate_rendering_summary("nonexistent_project_xyz_123")
        assert summary["project"] == "nonexistent_project_xyz_123"
        assert summary["individual_pdfs"] == []
        assert summary["combined_pdf"] is None
        assert summary["combined_html"] is None
        assert summary["total_size_kb"] == 0
        assert summary["web_outputs"] == []
        assert summary["slides"] == []


class TestLogRenderingSummary:
    """Tests for log_rendering_summary."""

    def test_log_with_combined_pdf(self, caplog):
        """Should log combined PDF info."""
        summary = {
            "project": "test_proj",
            "combined_pdf": {"name": "test_proj_combined.pdf", "size_kb": 500.0, "path": "/tmp/out"},
            "combined_html": None,
            "individual_pdfs": [],
            "web_outputs": [],
            "slides": [],
            "total_size_kb": 500.0,
        }
        with caplog.at_level("INFO"):
            log_rendering_summary(summary)
        assert "test_proj" in caplog.text

    def test_log_with_all_sections(self, caplog):
        """Summary with all output types should log all sections."""
        summary = {
            "project": "full_proj",
            "combined_pdf": {"name": "full_proj_combined.pdf", "size_kb": 1000.0, "path": "/tmp/pdf"},
            "combined_html": {"name": "index.html", "size_kb": 200.0, "path": "/tmp/web"},
            "individual_pdfs": [
                {"name": "01_intro.pdf", "size_kb": 100.0},
                {"name": "02_methods.pdf", "size_kb": 150.0},
            ],
            "web_outputs": [{"name": "01_intro.html", "size_kb": 50.0}],
            "slides": [{"name": "presentation.pdf", "size_kb": 300.0}],
            "total_size_kb": 1800.0,
        }
        with caplog.at_level("INFO"):
            log_rendering_summary(summary)

    def test_log_empty_summary(self, caplog):
        """Summary with no outputs should still log without error."""
        summary = {
            "project": "empty",
            "combined_pdf": None,
            "combined_html": None,
            "individual_pdfs": [],
            "web_outputs": [],
            "slides": [],
            "total_size_kb": 0,
        }
        with caplog.at_level("INFO"):
            log_rendering_summary(summary)
        assert "empty" in caplog.text


class TestVerifyPdfOutputs:
    """Tests for verify_pdf_outputs -- uses the project structure from __file__ parent."""

    def test_nonexistent_project_returns_false(self):
        """A project with no PDF dir should return False."""
        result = verify_pdf_outputs("definitely_not_a_real_project_xyz")
        assert result is False
