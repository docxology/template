"""Tests for infrastructure/reporting/page_rendering.py.

Covers: extract_pdf_pages_as_images and rendering helpers with real PDF files.

No mocks used — all tests use real PDF files created with reportlab, and real PIL.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.exceptions import FileNotFoundError as InfraFileNotFoundError


class TestExtractPdfPagesAsImages:
    """Test extract_pdf_pages_as_images with real PDFs."""

    def _create_pdf(self, path: Path, text: str = "Hello World", pages: int = 1):
        """Create a real PDF with reportlab."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        c = canvas.Canvas(str(path), pagesize=letter)
        for i in range(pages):
            c.setFont("Helvetica", 12)
            c.drawString(72, 720, f"{text} - Page {i + 1}")
            c.drawString(72, 700, "This is test content for coverage testing.")
            if i < pages - 1:
                c.showPage()
        c.save()

    def test_single_page_pdf(self, tmp_path):
        """Should extract images from single-page PDF."""
        from infrastructure.reporting.page_rendering import extract_pdf_pages_as_images

        pdf_path = tmp_path / "test.pdf"
        self._create_pdf(pdf_path, "Test Content")

        images = extract_pdf_pages_as_images(pdf_path, dpi=72)
        assert len(images) >= 1
        # Each image should be a PIL Image
        assert images[0].width > 0
        assert images[0].height > 0

    def test_multi_page_pdf(self, tmp_path):
        """Should extract images from multi-page PDF."""
        from infrastructure.reporting.page_rendering import extract_pdf_pages_as_images

        pdf_path = tmp_path / "multi.pdf"
        self._create_pdf(pdf_path, "Multi Page", pages=3)

        images = extract_pdf_pages_as_images(pdf_path, dpi=72)
        assert len(images) == 3

    def test_nonexistent_pdf_raises(self, tmp_path):
        """Should raise FileNotFoundError for missing PDF."""
        from infrastructure.reporting.page_rendering import extract_pdf_pages_as_images

        with pytest.raises(InfraFileNotFoundError):
            extract_pdf_pages_as_images(tmp_path / "nonexistent.pdf")

    def test_custom_dpi(self, tmp_path):
        """Should accept custom DPI parameter."""
        from infrastructure.reporting.page_rendering import extract_pdf_pages_as_images

        pdf_path = tmp_path / "dpi_test.pdf"
        self._create_pdf(pdf_path, "DPI Test")

        images = extract_pdf_pages_as_images(pdf_path, dpi=150)
        assert len(images) >= 1
