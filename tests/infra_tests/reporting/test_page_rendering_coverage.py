"""Tests for infrastructure.reporting.page_rendering — comprehensive coverage."""

import pytest



class TestExtractPdfPagesAsImages:
    def test_file_not_found(self, tmp_path):
        from infrastructure.reporting.page_rendering import extract_pdf_pages_as_images

        with pytest.raises(Exception) as exc_info:
            extract_pdf_pages_as_images(tmp_path / "nonexistent.pdf")
        assert "not found" in str(exc_info.value).lower()

    def test_valid_pdf_with_text(self, tmp_path):
        """Create a real PDF with reportlab and extract pages."""
        from reportlab.pdfgen import canvas

        pdf_path = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf_path))
        c.setFont("Helvetica", 12)
        c.drawString(100, 700, "Hello World - Test Page 1")
        c.showPage()
        c.drawString(100, 700, "Test Page 2")
        c.showPage()
        c.save()

        from infrastructure.reporting.page_rendering import extract_pdf_pages_as_images

        images = extract_pdf_pages_as_images(pdf_path)
        assert len(images) == 2
        # Each should be a PIL Image
        from PIL import Image
        for img in images:
            assert isinstance(img, Image.Image)

    def test_single_page_pdf(self, tmp_path):
        from reportlab.pdfgen import canvas

        pdf_path = tmp_path / "single.pdf"
        c = canvas.Canvas(str(pdf_path))
        c.drawString(100, 700, "Single page content")
        c.save()

        from infrastructure.reporting.page_rendering import extract_pdf_pages_as_images

        images = extract_pdf_pages_as_images(pdf_path)
        assert len(images) == 1


class TestRenderPagesSimple:
    def test_renders_pages(self, tmp_path):
        """Test the simple rendering fallback directly."""
        from reportlab.pdfgen import canvas
        from pypdf import PdfReader

        pdf_path = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf_path))
        c.drawString(100, 700, "Line one of text")
        c.drawString(100, 685, "Line two of text that is a bit longer")
        c.save()

        reader = PdfReader(pdf_path)
        from infrastructure.reporting.page_rendering import _render_pages_simple

        images = _render_pages_simple(reader, dpi=72)
        assert len(images) == 1
        from PIL import Image
        assert isinstance(images[0], Image.Image)
        # At 72 DPI: 8.5 * 72 = 612, 11 * 72 = 792
        assert images[0].size == (612, 792)

    def test_renders_multiple_pages(self, tmp_path):
        from reportlab.pdfgen import canvas
        from pypdf import PdfReader

        pdf_path = tmp_path / "multi.pdf"
        c = canvas.Canvas(str(pdf_path))
        for i in range(3):
            c.drawString(100, 700, f"Page {i + 1} content")
            c.showPage()
        c.save()

        reader = PdfReader(pdf_path)
        from infrastructure.reporting.page_rendering import _render_pages_simple

        images = _render_pages_simple(reader, dpi=72)
        assert len(images) == 3

    def test_long_lines_truncated(self, tmp_path):
        from reportlab.pdfgen import canvas
        from pypdf import PdfReader

        pdf_path = tmp_path / "long.pdf"
        c = canvas.Canvas(str(pdf_path))
        c.drawString(50, 700, "A" * 200)  # Very long line
        c.save()

        reader = PdfReader(pdf_path)
        from infrastructure.reporting.page_rendering import _render_pages_simple

        images = _render_pages_simple(reader, dpi=72)
        assert len(images) == 1


class TestRenderPagesWithReportlab:
    def test_renders_pages(self, tmp_path):
        from reportlab.pdfgen import canvas
        from pypdf import PdfReader

        pdf_path = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf_path))
        c.drawString(100, 700, "Some text content")
        c.save()

        reader = PdfReader(pdf_path)
        from infrastructure.reporting.page_rendering import _render_pages_with_reportlab

        images = _render_pages_with_reportlab(reader, dpi=72)
        assert len(images) == 1
        from PIL import Image
        assert isinstance(images[0], Image.Image)

    def test_empty_page(self, tmp_path):
        from reportlab.pdfgen import canvas
        from pypdf import PdfReader

        pdf_path = tmp_path / "empty.pdf"
        c = canvas.Canvas(str(pdf_path))
        c.showPage()  # Empty page
        c.save()

        reader = PdfReader(pdf_path)
        from infrastructure.reporting.page_rendering import _render_pages_with_reportlab

        images = _render_pages_with_reportlab(reader, dpi=72)
        assert len(images) == 1
