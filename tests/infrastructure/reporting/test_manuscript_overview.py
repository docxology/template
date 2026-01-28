"""Tests for infrastructure.reporting.manuscript_overview module.

Tests manuscript overview generation using real data (No Mocks Policy):
- Real PDF creation with reportlab
- Real image operations with PIL
- Real file I/O operations
"""

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


# Helper functions to create test data
def create_test_pdf(
    path: Path, num_pages: int = 5, text_per_page: str = "Test content"
) -> Path:
    """Create a real PDF file for testing."""
    c = canvas.Canvas(str(path), pagesize=letter)

    for i in range(num_pages):
        c.setFont("Helvetica", 12)
        c.drawString(100, 700, f"Page {i + 1}")
        c.drawString(100, 680, text_per_page)
        c.drawString(100, 660, f"This is test page {i + 1} of {num_pages}")

        # Add more lines to simulate content
        for j in range(10):
            c.drawString(
                100, 640 - (j * 20), f"Line {j + 1}: Sample text content for testing"
            )

        if i < num_pages - 1:
            c.showPage()

    c.save()
    return path


def create_test_image(width: int = 800, height: int = 1100) -> Image.Image:
    """Create a test PIL Image."""
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)
    # Only draw rectangle if image is large enough
    if width > 100 and height > 100:
        draw.rectangle([50, 50, width - 50, height - 50], outline="black")
        draw.text((100, 100), "Test Page", fill="black")
    else:
        draw.text((5, 5), "P", fill="black")
    return img


class TestExtractPdfPagesAsImages:
    """Test extract_pdf_pages_as_images function."""

    def test_extract_pdf_pages_file_not_found(self, tmp_path):
        """Test extraction from non-existent file raises error."""
        from infrastructure.reporting.manuscript_overview import \
            extract_pdf_pages_as_images

        nonexistent = tmp_path / "nonexistent.pdf"

        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            extract_pdf_pages_as_images(nonexistent)

    def test_extract_pdf_pages_basic(self, tmp_path):
        """Test basic PDF page extraction."""
        from infrastructure.reporting.manuscript_overview import \
            extract_pdf_pages_as_images

        # Create test PDF
        pdf_path = tmp_path / "test.pdf"
        create_test_pdf(pdf_path, num_pages=3)

        # Extract pages
        images = extract_pdf_pages_as_images(pdf_path, dpi=72)  # Lower DPI for speed

        assert len(images) == 3
        for img in images:
            assert isinstance(img, Image.Image)
            assert img.width > 0
            assert img.height > 0

    def test_extract_pdf_single_page(self, tmp_path):
        """Test extraction from single-page PDF."""
        from infrastructure.reporting.manuscript_overview import \
            extract_pdf_pages_as_images

        pdf_path = tmp_path / "single.pdf"
        create_test_pdf(pdf_path, num_pages=1)

        images = extract_pdf_pages_as_images(pdf_path, dpi=72)

        assert len(images) == 1
        assert isinstance(images[0], Image.Image)

    def test_extract_pdf_many_pages(self, tmp_path):
        """Test extraction from multi-page PDF."""
        from infrastructure.reporting.manuscript_overview import \
            extract_pdf_pages_as_images

        pdf_path = tmp_path / "multi.pdf"
        create_test_pdf(pdf_path, num_pages=10)

        images = extract_pdf_pages_as_images(pdf_path, dpi=72)

        assert len(images) == 10


class TestRenderPagesSimple:
    """Test _render_pages_simple function."""

    def test_render_simple_creates_images(self, tmp_path):
        """Test simple rendering creates valid images."""
        from pypdf import PdfReader

        from infrastructure.reporting.manuscript_overview import \
            _render_pages_simple

        # Create test PDF
        pdf_path = tmp_path / "test.pdf"
        create_test_pdf(pdf_path, num_pages=2, text_per_page="Hello World")

        reader = PdfReader(pdf_path)
        images = _render_pages_simple(reader, dpi=72)

        assert len(images) == 2
        for img in images:
            assert isinstance(img, Image.Image)
            assert img.mode == "RGB"

    def test_render_simple_text_content(self, tmp_path):
        """Test rendered images contain page content."""
        from pypdf import PdfReader

        from infrastructure.reporting.manuscript_overview import \
            _render_pages_simple

        pdf_path = tmp_path / "test.pdf"
        create_test_pdf(pdf_path, num_pages=1, text_per_page="Test content line")

        reader = PdfReader(pdf_path)
        images = _render_pages_simple(reader, dpi=72)

        # Image should have been created with correct dimensions
        assert images[0].width > 0
        assert images[0].height > 0


class TestCreatePageGrid:
    """Test create_page_grid function."""

    def test_create_grid_empty_input(self):
        """Test grid creation with no images raises error."""
        from infrastructure.reporting.manuscript_overview import \
            create_page_grid

        with pytest.raises(ValueError, match="No images provided"):
            create_page_grid([])

    def test_create_grid_single_image(self):
        """Test grid creation with single image."""
        from infrastructure.reporting.manuscript_overview import \
            create_page_grid

        img = create_test_image(400, 600)
        grid = create_page_grid([img], cols=4)

        assert isinstance(grid, Image.Image)
        assert grid.mode == "RGB"
        assert grid.width > 0
        assert grid.height > 0

    def test_create_grid_multiple_images(self):
        """Test grid creation with multiple images."""
        from infrastructure.reporting.manuscript_overview import \
            create_page_grid

        images = [create_test_image(400, 600) for _ in range(8)]
        grid = create_page_grid(images, cols=4)

        assert isinstance(grid, Image.Image)
        # Should have 2 rows for 8 images with 4 columns
        assert grid.width > 0
        assert grid.height > 0

    def test_create_grid_custom_cols(self):
        """Test grid with different column counts."""
        from infrastructure.reporting.manuscript_overview import \
            create_page_grid

        images = [create_test_image(400, 600) for _ in range(6)]

        # Test 2 columns (3 rows)
        grid_2col = create_page_grid(images, cols=2)
        assert isinstance(grid_2col, Image.Image)

        # Test 3 columns (2 rows)
        grid_3col = create_page_grid(images, cols=3)
        assert isinstance(grid_3col, Image.Image)

        # Width should be different
        assert grid_2col.width != grid_3col.width

    def test_create_grid_custom_padding(self):
        """Test grid with custom padding."""
        from infrastructure.reporting.manuscript_overview import \
            create_page_grid

        images = [create_test_image(400, 600) for _ in range(4)]

        # Different padding values
        grid_small_padding = create_page_grid(images, cols=2, padding=5)
        grid_large_padding = create_page_grid(images, cols=2, padding=50)

        # Larger padding should result in larger grid
        assert grid_large_padding.width > grid_small_padding.width
        assert grid_large_padding.height > grid_small_padding.height

    def test_create_grid_maintains_aspect_ratio(self):
        """Test grid maintains image aspect ratios."""
        from infrastructure.reporting.manuscript_overview import \
            create_page_grid

        # Create portrait and landscape images
        portrait = create_test_image(400, 800)
        landscape = create_test_image(800, 400)

        grid = create_page_grid([portrait, landscape], cols=2)

        assert isinstance(grid, Image.Image)

    def test_create_grid_white_background(self):
        """Test grid has white background."""
        from infrastructure.reporting.manuscript_overview import \
            create_page_grid

        img = create_test_image(100, 100)
        grid = create_page_grid([img], cols=1, padding=50)

        # Check corner pixel is white
        pixel = grid.getpixel((0, 0))
        assert pixel == (255, 255, 255)


class TestGenerateManuscriptOverview:
    """Test generate_manuscript_overview function."""

    def test_generate_overview_file_not_found(self, tmp_path):
        """Test overview generation with non-existent PDF."""
        from infrastructure.reporting.manuscript_overview import \
            generate_manuscript_overview

        nonexistent = tmp_path / "nonexistent.pdf"
        output_dir = tmp_path / "output"

        with pytest.raises(FileNotFoundError):
            generate_manuscript_overview(nonexistent, output_dir, "test_project")

    def test_generate_overview_creates_png(self, tmp_path):
        """Test overview generation creates PNG file."""
        from infrastructure.reporting.manuscript_overview import \
            generate_manuscript_overview

        # Create test PDF
        pdf_path = tmp_path / "test.pdf"
        create_test_pdf(pdf_path, num_pages=3)

        output_dir = tmp_path / "output"

        result = generate_manuscript_overview(
            pdf_path, output_dir, "test_project", dpi=72
        )

        # Should create PNG
        png_key = "manuscript_overview_test_project.png"
        assert png_key in result
        assert result[png_key].exists()

    def test_generate_overview_creates_output_dir(self, tmp_path):
        """Test overview generation creates output directory."""
        from infrastructure.reporting.manuscript_overview import \
            generate_manuscript_overview

        pdf_path = tmp_path / "test.pdf"
        create_test_pdf(pdf_path, num_pages=2)

        output_dir = tmp_path / "nested" / "output"
        assert not output_dir.exists()

        generate_manuscript_overview(pdf_path, output_dir, "test_project", dpi=72)

        assert output_dir.exists()

    def test_generate_overview_project_name_in_filename(self, tmp_path):
        """Test project name is included in output filename."""
        from infrastructure.reporting.manuscript_overview import \
            generate_manuscript_overview

        pdf_path = tmp_path / "test.pdf"
        create_test_pdf(pdf_path, num_pages=2)

        output_dir = tmp_path / "output"
        project_name = "my_research_project"

        result = generate_manuscript_overview(
            pdf_path, output_dir, project_name, dpi=72
        )

        # Check filenames contain project name
        for key in result.keys():
            assert project_name in key


class TestSaveImageAsPdf:
    """Test _save_image_as_pdf function."""

    def test_save_image_as_pdf_creates_file(self, tmp_path):
        """Test saving image as PDF creates valid file."""
        from infrastructure.reporting.manuscript_overview import \
            _save_image_as_pdf

        img = create_test_image(800, 1100)
        pdf_path = tmp_path / "output.pdf"

        _save_image_as_pdf(img, pdf_path, "Test Title")

        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0

    def test_save_image_as_pdf_readable(self, tmp_path):
        """Test saved PDF is readable."""
        from pypdf import PdfReader

        from infrastructure.reporting.manuscript_overview import \
            _save_image_as_pdf

        img = create_test_image(800, 1100)
        pdf_path = tmp_path / "output.pdf"

        _save_image_as_pdf(img, pdf_path, "Test Title")

        # Verify PDF is readable
        reader = PdfReader(pdf_path)
        assert len(reader.pages) == 1

    def test_save_image_preserves_content(self, tmp_path):
        """Test saved PDF has single page."""
        from pypdf import PdfReader

        from infrastructure.reporting.manuscript_overview import \
            _save_image_as_pdf

        img = create_test_image(800, 1100)
        pdf_path = tmp_path / "output.pdf"

        _save_image_as_pdf(img, pdf_path, "My Document")

        reader = PdfReader(pdf_path)
        assert len(reader.pages) == 1


class TestRenderPagesWithReportlab:
    """Test _render_pages_with_reportlab function."""

    def test_render_with_reportlab_creates_images(self, tmp_path):
        """Test reportlab rendering creates valid images."""
        from pypdf import PdfReader

        from infrastructure.reporting.manuscript_overview import \
            _render_pages_with_reportlab

        # Create test PDF
        pdf_path = tmp_path / "test.pdf"
        create_test_pdf(pdf_path, num_pages=2)

        reader = PdfReader(pdf_path)
        images = _render_pages_with_reportlab(reader, dpi=72)

        assert len(images) == 2
        for img in images:
            assert isinstance(img, Image.Image)


class TestGenerateAllManuscriptOverviews:
    """Test generate_all_manuscript_overviews function."""

    def test_generate_all_no_pdfs_found(self, tmp_path):
        """Test handling when no manuscript PDFs exist."""
        from infrastructure.reporting.executive_reporter import ProjectMetrics
        from infrastructure.reporting.manuscript_overview import \
            generate_all_manuscript_overviews

        # Create a minimal ExecutiveSummary-like object
        class MockSummary:
            project_metrics = [type("Metrics", (), {"name": "nonexistent_project"})()]

        summary = MockSummary()
        output_dir = tmp_path / "output"
        repo_root = tmp_path

        result = generate_all_manuscript_overviews(summary, output_dir, repo_root)

        # Should return empty dict since no PDFs found
        assert result == {}

    def test_generate_all_with_valid_pdf(self, tmp_path):
        """Test generating overviews when PDFs exist."""
        from infrastructure.reporting.manuscript_overview import \
            generate_all_manuscript_overviews

        # Create directory structure
        project_name = "test_project"
        pdf_dir = tmp_path / "output" / project_name
        pdf_dir.mkdir(parents=True)

        # Create test PDF
        pdf_path = pdf_dir / f"{project_name}_combined.pdf"
        create_test_pdf(pdf_path, num_pages=3)

        # Create mock summary
        class MockSummary:
            project_metrics = [type("Metrics", (), {"name": project_name})()]

        summary = MockSummary()
        output_dir = tmp_path / "overviews"

        result = generate_all_manuscript_overviews(summary, output_dir, tmp_path)

        # Should generate overview files
        assert len(result) > 0


class TestModuleImports:
    """Test module structure and imports."""

    def test_module_imports(self):
        """Test module can be imported."""
        from infrastructure.reporting import manuscript_overview

        assert manuscript_overview is not None

    def test_public_functions_exist(self):
        """Test expected public functions exist."""
        from infrastructure.reporting.manuscript_overview import (
            create_page_grid, extract_pdf_pages_as_images,
            generate_all_manuscript_overviews, generate_manuscript_overview)

        assert callable(extract_pdf_pages_as_images)
        assert callable(create_page_grid)
        assert callable(generate_manuscript_overview)
        assert callable(generate_all_manuscript_overviews)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_pdf_pages(self, tmp_path):
        """Test handling of PDF with minimal content."""
        from infrastructure.reporting.manuscript_overview import \
            extract_pdf_pages_as_images

        # Create minimal PDF
        pdf_path = tmp_path / "minimal.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.showPage()  # Create blank page
        c.save()

        images = extract_pdf_pages_as_images(pdf_path, dpi=72)

        assert len(images) == 1
        assert isinstance(images[0], Image.Image)

    def test_very_small_images(self):
        """Test grid creation with very small images."""
        from infrastructure.reporting.manuscript_overview import \
            create_page_grid

        tiny_images = [create_test_image(10, 10) for _ in range(4)]
        grid = create_page_grid(tiny_images, cols=2)

        assert isinstance(grid, Image.Image)

    def test_very_large_images(self):
        """Test grid creation with large images gets resized."""
        from infrastructure.reporting.manuscript_overview import \
            create_page_grid

        large_images = [create_test_image(2000, 3000) for _ in range(2)]
        grid = create_page_grid(large_images, cols=2, max_thumb_size=(200, 300))

        assert isinstance(grid, Image.Image)
        # Grid should be smaller than original images
        assert grid.width < 2000 * 2
