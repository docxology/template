"""PDF validator paths and the validate_markdown aggregate facade tests (split from test_transmission_validation.py)."""

from __future__ import annotations

from pathlib import Path
import pytest
from infrastructure.core.exceptions import PDFValidationError
from infrastructure.core.logging import DiagnosticSeverity
from infrastructure.validation.content.markdown_validator import validate_markdown
from infrastructure.validation.content.pdf_validator import (
    extract_text_from_pdf,
    scan_for_issues,
    validate_pdf_rendering,
)
from ._transmission_validation_helpers import (
    _write_md,
    _make_real_pdf,
)


class TestPdfValidatorPaths:
    """``pdf_validator`` — missing, corrupt, and valid PDF paths."""

    def test_missing_pdf_raises(self, tmp_path: Path) -> None:
        with pytest.raises(PDFValidationError, match="PDF file not found"):
            extract_text_from_pdf(tmp_path / "nonexistent.pdf")

    def test_too_small_file_raises(self, tmp_path: Path) -> None:
        """A file under 1000 bytes is flagged as likely corrupted."""
        small = tmp_path / "tiny.pdf"
        small.write_bytes(b"%PDF-1.4\nshort")
        with pytest.raises(PDFValidationError, match="too small"):
            extract_text_from_pdf(small)

    def test_corrupt_pdf_raises_extraction_failure(self, tmp_path: Path) -> None:
        """A >1KB non-PDF file fails all extraction methods."""
        corrupt = tmp_path / "corrupt.pdf"
        corrupt.write_text("This is not a PDF. " * 200, encoding="utf-8")
        with pytest.raises(PDFValidationError, match="Failed to extract text"):
            extract_text_from_pdf(corrupt)

    def test_valid_pdf_extracts_text(self, tmp_path: Path) -> None:
        pdf = _make_real_pdf(tmp_path / "valid.pdf", ["Hello World", "Second Page"])
        text = extract_text_from_pdf(pdf)
        assert "Hello World" in text
        assert "Second Page" in text

    def test_validate_pdf_rendering_report_structure(self, tmp_path: Path) -> None:
        pdf = _make_real_pdf(tmp_path / "report.pdf", ["Title Here", "Body Text"])
        report = validate_pdf_rendering(pdf, n_words=5)
        assert "pdf_path" in report
        assert "issues" in report
        assert "first_words" in report
        assert "summary" in report
        assert report["summary"]["has_issues"] is False
        assert report["summary"]["word_count"] <= 5
        assert "Title" in report["first_words"]

    def test_validate_pdf_rendering_detects_issues(self, tmp_path: Path) -> None:
        pdf = _make_real_pdf(
            tmp_path / "issues.pdf",
            ["Intro ?? ref", "[WARNING] problem", "Error: Bad thing"],
        )
        report = validate_pdf_rendering(pdf)
        assert report["summary"]["has_issues"] is True
        assert report["issues"]["unresolved_references"] > 0
        assert report["issues"]["warnings"] > 0
        assert report["issues"]["errors"] > 0

    def test_validate_pdf_rendering_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(PDFValidationError, match="PDF file not found"):
            validate_pdf_rendering(tmp_path / "nope.pdf")

    def test_scan_for_issues_all_categories(self) -> None:
        text = "?? ref\n[WARNING] w\nError: Bad\n[?] cite\n${VAR} placeholder"
        issues = scan_for_issues(text)
        assert issues["unresolved_references"] >= 1
        assert issues["warnings"] >= 1
        assert issues["errors"] >= 1
        assert issues["missing_citations"] >= 1
        assert issues["unresolved_placeholders"] >= 1
        assert issues["total_issues"] == sum(
            issues[k]
            for k in (
                "unresolved_references",
                "warnings",
                "errors",
                "missing_citations",
                "unresolved_placeholders",
            )
        )

    def test_scan_for_issues_clean_text(self) -> None:
        issues = scan_for_issues("This is clean text with no issues.")
        assert issues["total_issues"] == 0

    def test_scan_for_issues_scientific_error_not_flagged(self) -> None:
        """Scientific 'error:' terms should not trigger false-positive errors."""
        text = "final error: 1.2e-6\nstandard error: 0.03\n"
        issues = scan_for_issues(text)
        assert issues["errors"] == 0


class TestValidateMarkdownFacade:
    """``validate_markdown`` — aggregate facade and error paths."""

    def test_nonexistent_directory_raises(self, tmp_path: Path) -> None:
        from infrastructure.core.exceptions import FileNotFoundError

        with pytest.raises(FileNotFoundError):
            validate_markdown(tmp_path / "nonexistent", tmp_path)

    def test_empty_directory_returns_no_problems(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        problems, exit_code = validate_markdown(manuscript, tmp_path)
        assert problems == []
        assert exit_code == 0

    def test_clean_manuscript_no_problems(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "# Title\n\nClean content here.\n")
        problems, exit_code = validate_markdown(manuscript, tmp_path)
        assert problems == []
        assert exit_code == 0

    def test_problems_non_strict_exit_zero(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(
            manuscript,
            "test.md",
            "![missing](nope.png)\n\\[bracket math\\]\n\\eqref{eq:gone}\n",
        )
        problems, exit_code = validate_markdown(manuscript, tmp_path, strict=False)
        assert exit_code == 0
        assert len(problems) >= 3

    def test_problems_strict_with_errors_exit_one(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "![missing](nope.png)\n")
        problems, exit_code = validate_markdown(manuscript, tmp_path, strict=True)
        assert exit_code == 1
        assert len(problems) >= 1
        assert any(p.severity == DiagnosticSeverity.ERROR for p in problems)

    def test_strict_with_only_warnings_exit_zero(self, tmp_path: Path) -> None:
        """Strict mode only returns exit 1 when there are ERROR-level problems."""
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(manuscript, "test.md", "Math: $$inline$$\n")
        problems, exit_code = validate_markdown(manuscript, tmp_path, strict=True)
        assert exit_code == 0
        assert len(problems) >= 1
        assert all(p.severity != DiagnosticSeverity.ERROR for p in problems)

    def test_full_validation_flow_clean(self, tmp_path: Path) -> None:
        """End-to-end: images, refs, math, pitfalls, citations all pass."""
        output_dir = tmp_path / "output" / "figures"
        output_dir.mkdir(parents=True)
        (output_dir / "fig.png").write_text("fake")

        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        _write_md(
            manuscript,
            "test.md",
            "# Section {#sec:test}\n\n"
            "![Fig](../output/figures/fig.png)\n\n"
            "\\begin{equation}\\label{eq:test}\nx^2\n\\end{equation}\n\n"
            "See \\eqref{eq:test} and [section](#sec:test).\n",
        )
        (manuscript / "references.bib").write_text("@article{k, title={K}}\n", encoding="utf-8")
        problems, exit_code = validate_markdown(manuscript, tmp_path)
        assert exit_code == 0
        assert problems == []
