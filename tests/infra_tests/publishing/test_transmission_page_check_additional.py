"""Additional tests for transmission bookend PDF page-span validation.

Targets the branches below 60%: end marker on multiple pages, overflow
detection, both markers on page 1, missing end marker, CLI main(), and
validate_transmission_bookend_pages().
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from infrastructure.publishing.transmission_page_check import (
    BEGIN_MARKER,
    END_MARKER,
    OVERFLOW_MARKER,
    check_transmission_bookend_pages,
    validate_transmission_bookend_pages,
)


def _make_pdf(path: Path, pages: list[str]) -> None:
    """Create a real PDF with one page per string in *pages*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=letter)
    for text in pages:
        pdf.drawString(72, 720, text)
        pdf.showPage()
    pdf.save()


class TestTransmissionPageCheckEdgeCases:
    """Test edge cases that exercise uncovered branches."""

    def test_missing_pdf_returns_invalid(self, tmp_path: Path) -> None:
        result = check_transmission_bookend_pages(tmp_path / "nonexistent.pdf")
        assert result.valid is False
        assert result.page_count == 0
        assert "PDF not found" in result.issues[0]

    def test_empty_pdf_returns_invalid(self, tmp_path: Path) -> None:
        """A PDF with zero pages should fail."""
        pdf_path = tmp_path / "empty.pdf"
        pdf = canvas.Canvas(str(pdf_path), pagesize=letter)
        pdf.save()  # saves with 0 pages
        result = check_transmission_bookend_pages(pdf_path)
        assert result.valid is False
        assert result.page_count == 0

    def test_missing_end_marker_fails(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "no_end.pdf"
        _make_pdf(pdf_path, [BEGIN_MARKER, "body content"])
        result = check_transmission_bookend_pages(pdf_path)
        assert result.valid is False
        assert any("Missing" in i and END_MARKER in i for i in result.issues)

    def test_end_marker_not_on_last_page_fails(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "early_end.pdf"
        _make_pdf(pdf_path, [BEGIN_MARKER, END_MARKER, "trailing content"])
        result = check_transmission_bookend_pages(pdf_path)
        assert result.valid is False
        assert any("must be on last page" in i for i in result.issues)

    def test_end_marker_spans_multiple_pages_fails(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "multi_end.pdf"
        _make_pdf(pdf_path, [BEGIN_MARKER, END_MARKER, END_MARKER])
        result = check_transmission_bookend_pages(pdf_path)
        assert result.valid is False
        assert any("spans multiple pages" in i for i in result.issues)

    def test_both_markers_on_page_one_fails(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "both_page1.pdf"
        _make_pdf(pdf_path, [f"{BEGIN_MARKER} {END_MARKER}", "body"])
        result = check_transmission_bookend_pages(pdf_path)
        assert result.valid is False
        assert any("Page 1 contains both" in i for i in result.issues)

    def test_begin_marker_repeated_fails(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "repeated_begin.pdf"
        _make_pdf(pdf_path, [BEGIN_MARKER, BEGIN_MARKER, END_MARKER])
        result = check_transmission_bookend_pages(pdf_path)
        assert result.valid is False
        assert any("repeated on page" in i for i in result.issues)

    def test_end_marker_appears_before_final_page_fails(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "early_end_repeat.pdf"
        # END_MARKER on page 2 and page 3 (last), but page 2 is before final
        _make_pdf(pdf_path, [BEGIN_MARKER, END_MARKER, END_MARKER])
        result = check_transmission_bookend_pages(pdf_path)
        assert result.valid is False
        assert any("appears before final page" in i for i in result.issues)

    def test_overflow_marker_on_page_two_detected(self, tmp_path: Path) -> None:
        """Begin bookend overflow: integrity strip marker on page 2."""
        pdf_path = tmp_path / "overflow.pdf"
        _make_pdf(pdf_path, [BEGIN_MARKER, OVERFLOW_MARKER, END_MARKER])
        result = check_transmission_bookend_pages(pdf_path)
        assert result.valid is False
        assert any("overflow" in i.lower() for i in result.issues)

    def test_html_comment_markers_detected(self, tmp_path: Path) -> None:
        """Markers wrapped in HTML comments should still be detected."""
        pdf_path = tmp_path / "comment_markers.pdf"
        _make_pdf(
            pdf_path,
            [f"<!-- {BEGIN_MARKER} -->", "body", f"<!-- {END_MARKER} -->"],
        )
        result = check_transmission_bookend_pages(pdf_path)
        assert result.valid is True

    def test_valid_single_page_with_both_markers_not_possible(self, tmp_path: Path) -> None:
        """A 1-page PDF with both markers should fail (both on page 1)."""
        pdf_path = tmp_path / "single_page.pdf"
        _make_pdf(pdf_path, [f"{BEGIN_MARKER} {END_MARKER}"])
        result = check_transmission_bookend_pages(pdf_path)
        assert result.valid is False

    def test_valid_two_page_bookends(self, tmp_path: Path) -> None:
        """Minimal valid case: begin on page 1, end on page 2."""
        pdf_path = tmp_path / "minimal_valid.pdf"
        _make_pdf(pdf_path, [BEGIN_MARKER, END_MARKER])
        result = check_transmission_bookend_pages(pdf_path)
        assert result.valid is True
        assert result.begin_pages == (1,)
        assert result.end_pages == (2,)
        assert result.page_count == 2


class TestValidateTransmissionBookendPages:
    """Test the validate wrapper that logs results."""

    def test_validate_valid_pdf_returns_true(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "valid.pdf"
        _make_pdf(pdf_path, [BEGIN_MARKER, "body", END_MARKER])
        assert validate_transmission_bookend_pages(pdf_path) is True

    def test_validate_invalid_pdf_returns_false(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "invalid.pdf"
        _make_pdf(pdf_path, ["no markers at all"])
        assert validate_transmission_bookend_pages(pdf_path) is False

    def test_validate_missing_pdf_returns_false(self, tmp_path: Path) -> None:
        assert validate_transmission_bookend_pages(tmp_path / "missing.pdf") is False


class TestTransmissionPageCheckCLI:
    """Test the CLI main() entry point via subprocess."""

    def test_cli_valid_pdf_exits_zero(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "valid.pdf"
        _make_pdf(pdf_path, [BEGIN_MARKER, "body", END_MARKER])
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.publishing.transmission_page_check", str(pdf_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "OK" in result.stdout

    def test_cli_invalid_pdf_exits_nonzero(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "invalid.pdf"
        _make_pdf(pdf_path, ["no markers"])
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.publishing.transmission_page_check", str(pdf_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert "FAIL" in result.stderr

    def test_cli_missing_pdf_exits_nonzero(self, tmp_path: Path) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.publishing.transmission_page_check", str(tmp_path / "missing.pdf")],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
