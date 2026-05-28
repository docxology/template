"""Tests for transmission bookend PDF page-span validation."""

from __future__ import annotations

from pathlib import Path

import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from infrastructure.publishing.transmission_page_check import (
    BEGIN_MARKER,
    END_MARKER,
    check_transmission_bookend_pages,
)


def _write_valid_bookend_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=letter)
    pdf.drawString(72, 720, BEGIN_MARKER)
    pdf.showPage()
    pdf.drawString(72, 720, "Body content")
    pdf.showPage()
    pdf.drawString(72, 720, END_MARKER)
    pdf.save()


class TestTransmissionPageCheck:
    def test_valid_begin_end_on_dedicated_pages(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "valid.pdf"
        _write_valid_bookend_pdf(pdf_path)
        result = check_transmission_bookend_pages(pdf_path)
        assert result.valid is True
        assert result.begin_pages == (1,)
        assert result.end_pages == (3,)

    def test_missing_begin_marker_fails(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "subdir" / "no_begin.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf = canvas.Canvas(str(pdf_path), pagesize=letter)
        pdf.drawString(72, 720, END_MARKER)
        pdf.save()
        result = check_transmission_bookend_pages(pdf_path)
        assert result.valid is False
        assert any("Missing" in issue and BEGIN_MARKER in issue for issue in result.issues)

    def test_begin_not_on_page_one_fails(self, tmp_path: Path) -> None:
        pdf_path = tmp_path / "late_begin.pdf"
        pdf = canvas.Canvas(str(pdf_path), pagesize=letter)
        pdf.drawString(72, 720, "Cover")
        pdf.showPage()
        pdf.drawString(72, 720, BEGIN_MARKER)
        pdf.showPage()
        pdf.drawString(72, 720, END_MARKER)
        pdf.save()
        result = check_transmission_bookend_pages(pdf_path)
        assert result.valid is False

    @pytest.mark.skipif(
        not Path(
            "projects/templates/template_code_project/output/pdf/"
            "template_code_project_combined.pdf"
        ).is_file(),
        reason="Rendered combined PDF not present",
    )
    def test_template_code_project_combined_pdf_when_present(self) -> None:
        pdf_path = Path(
            "projects/templates/template_code_project/output/pdf/"
            "template_code_project_combined.pdf"
        )
        result = check_transmission_bookend_pages(pdf_path)
        assert result.valid is True, result.issues
