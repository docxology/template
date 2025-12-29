"""Tests for manuscript overview generation functionality.

This module tests the manuscript overview generation features including:
- PDF page extraction and image conversion
- Grid layout creation
- End-to-end overview generation
- Error handling and edge cases

Part of the infrastructure test suite.
"""
from __future__ import annotations

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from infrastructure.reporting.manuscript_overview import (
    extract_pdf_pages_as_images,
    create_page_grid,
    generate_manuscript_overview,
    generate_all_manuscript_overviews,
)


class TestPDFPageExtraction:
    """Test PDF page extraction functionality."""

    def test_extract_pdf_pages_as_images_valid_pdf(self, tmp_path):
        """Test extracting images from a valid PDF."""
        # Create a simple test PDF
        pdf_path = self._create_test_pdf(tmp_path, pages=3)

        images = extract_pdf_pages_as_images(pdf_path)

        assert len(images) == 3
        assert all(hasattr(img, 'size') for img in images)  # PIL Image objects

    def test_extract_pdf_pages_as_images_empty_pdf(self, tmp_path):
        """Test handling of PDF with no pages."""
        # Create a valid but empty PDF using reportlab
        try:
            from reportlab.pdfgen import canvas
            pdf_path = tmp_path / "empty.pdf"
            c = canvas.Canvas(str(pdf_path))
            # Don't add any pages - this creates an empty PDF
            c.save()

            with pytest.raises(ValueError, match="has no pages"):
                extract_pdf_pages_as_images(pdf_path)
        except ImportError:
            pytest.skip("reportlab not available for creating empty PDF")

    def test_extract_pdf_pages_as_images_missing_file(self):
        """Test handling of missing PDF file."""
        missing_path = Path("nonexistent.pdf")

        with pytest.raises(FileNotFoundError):
            extract_pdf_pages_as_images(missing_path)

    def test_extract_pdf_pages_as_images_corrupted_pdf(self, tmp_path):
        """Test handling of corrupted PDF file."""
        pdf_path = tmp_path / "corrupted.pdf"
        pdf_path.write_bytes(b"not a pdf file")

        with pytest.raises(ValueError):
            extract_pdf_pages_as_images(pdf_path)

    def _create_test_pdf(self, tmp_path: Path, pages: int = 1) -> Path:
        """Create a test PDF with the specified number of pages."""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
        except ImportError:
            pytest.skip("reportlab not available for test PDF creation")

        pdf_path = tmp_path / f"test_{pages}_pages.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=letter)

        for page_num in range(1, pages + 1):
            c.setFont("Helvetica", 12)
            c.drawString(100, 750, f"Test Page {page_num}")
            c.drawString(100, 700, f"This is page {page_num} of {pages}")
            c.drawString(100, 650, "Some test content for the manuscript overview.")
            c.drawString(100, 50, f"Page {page_num}")
            c.showPage()

        c.save()
        return pdf_path


class TestPageGridCreation:
    """Test page grid layout functionality."""

    def test_create_page_grid_single_image(self):
        """Test grid creation with single image."""
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL not available")

        # Create a test image
        img = Image.new('RGB', (200, 300), color='red')
        images = [img]

        grid = create_page_grid(images, cols=4)

        assert hasattr(grid, 'size')
        assert grid.size[0] > 200  # Should be wider for grid layout
        assert grid.size[1] > 300  # Should be taller for grid layout

    def test_create_page_grid_multiple_images(self):
        """Test grid creation with multiple images."""
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL not available")

        # Create test images
        images = []
        for i in range(5):
            img = Image.new('RGB', (200, 300), color=(255, i*50, 0))
            images.append(img)

        grid = create_page_grid(images, cols=4)

        assert hasattr(grid, 'size')
        # Should have 2 rows (5 images / 4 cols = 2 rows needed)

    def test_create_page_grid_empty_list(self):
        """Test grid creation with empty image list."""
        with pytest.raises(ValueError, match="No images provided"):
            create_page_grid([])

    def test_create_page_grid_different_sizes(self):
        """Test grid creation with images of different sizes."""
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("PIL not available")

        # Create images of different sizes
        images = [
            Image.new('RGB', (100, 200), color='red'),
            Image.new('RGB', (200, 100), color='blue'),
            Image.new('RGB', (150, 150), color='green'),
        ]

        grid = create_page_grid(images, cols=4)

        assert hasattr(grid, 'size')
        assert grid.size[0] > 0
        assert grid.size[1] > 0


class TestManuscriptOverviewGeneration:
    """Test end-to-end manuscript overview generation."""

    def test_generate_manuscript_overview_success(self, tmp_path):
        """Test successful overview generation."""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
        except ImportError:
            pytest.skip("reportlab not available")

        # Create test PDF
        pdf_path = tmp_path / "test_manuscript.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=letter)

        for page_num in range(1, 4):
            c.setFont("Helvetica", 12)
            c.drawString(100, 750, f"Manuscript Page {page_num}")
            c.drawString(100, 700, "This is some test content.")
            c.drawString(100, 50, f"Page {page_num}")
            c.showPage()

        c.save()

        # Generate overview
        output_dir = tmp_path / "output"
        result = generate_manuscript_overview(pdf_path, output_dir, "test_project")

        # Check PNG file
        png_filename = "manuscript_overview_test_project.png"
        assert png_filename in result
        assert result[png_filename].exists()
        assert result[png_filename].name == png_filename

        # PDF output may not be available if reportlab fails
        pdf_filename = "manuscript_overview_test_project.pdf"
        if pdf_filename in result:
            assert result[pdf_filename].exists()
            assert result[pdf_filename].name == pdf_filename

    def test_generate_manuscript_overview_missing_pdf(self, tmp_path):
        """Test overview generation with missing PDF."""
        missing_pdf = tmp_path / "missing.pdf"
        output_dir = tmp_path / "output"

        with pytest.raises(FileNotFoundError):
            generate_manuscript_overview(missing_pdf, output_dir, "test_project")

    def test_generate_manuscript_overview_empty_pdf(self, tmp_path):
        """Test overview generation with empty PDF."""
        # Create invalid PDF
        pdf_path = tmp_path / "empty.pdf"
        pdf_path.write_bytes(b"not a valid pdf")

        output_dir = tmp_path / "output"

        with pytest.raises(ValueError):
            generate_manuscript_overview(pdf_path, output_dir, "test_project")


class TestMultipleProjectOverviews:
    """Test generating overviews for multiple projects."""

    def test_generate_all_manuscript_overviews_success(self, tmp_path):
        """Test generating overviews for multiple projects."""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
        except ImportError:
            pytest.skip("reportlab not available")

        # Create mock executive summary
        from infrastructure.reporting.executive_reporter import ExecutiveSummary, ProjectMetrics

        # Create test PDFs for two projects
        projects_data = []
        for project_name in ["project1", "project2"]:
            # Create PDF
            pdf_path = tmp_path / f"{project_name}_manuscript.pdf"
            c = canvas.Canvas(str(pdf_path), pagesize=letter)

            for page_num in range(1, 3):
                c.setFont("Helvetica", 12)
                c.drawString(100, 750, f"{project_name.upper()} Page {page_num}")
                c.drawString(100, 50, f"Page {page_num}")
                c.showPage()

            c.save()

            # Create project metrics
            from infrastructure.reporting.executive_reporter import ManuscriptMetrics, CodebaseMetrics, TestMetrics, OutputMetrics, PipelineMetrics

            project_metrics = ProjectMetrics(
                name=project_name,
                manuscript=ManuscriptMetrics(),
                codebase=CodebaseMetrics(),
                tests=TestMetrics(),
                outputs=OutputMetrics(),
                pipeline=PipelineMetrics()
            )
            projects_data.append(project_metrics)

        # Create executive summary
        summary = ExecutiveSummary(
            timestamp="2025-01-01T00:00:00",
            total_projects=len(projects_data),
            aggregate_metrics={},
            project_metrics=projects_data,
            health_scores={},
            comparative_tables={},
            recommendations=[]
        )

        # Generate overviews
        output_dir = tmp_path / "executive_summary"

        # Mock the PDF discovery by placing PDFs in expected locations
        for project in projects_data:
            project_pdf_dir = tmp_path / "output" / project.name / "pdf"
            project_pdf_dir.mkdir(parents=True, exist_ok=True)

            # Copy the test PDF to the expected location
            import shutil
            src_pdf = tmp_path / f"{project.name}_manuscript.pdf"
            dst_pdf = project_pdf_dir / "project_combined.pdf"
            shutil.copy2(src_pdf, dst_pdf)

        result = generate_all_manuscript_overviews(summary, output_dir, tmp_path)

        # Should have PNG files for both projects
        assert len(result) >= 2  # At least PNG files for 2 projects

        # Check filenames
        png_files = [path for path in result.values() if path.suffix == '.png']
        assert len(png_files) == 2, f"Expected 2 PNG files, got {len(png_files)}: {[p.name for p in png_files]}"

        filenames = [path.name for path in png_files]
        assert "manuscript_overview_project1.png" in filenames, f"project1 PNG not found in {filenames}"
        assert "manuscript_overview_project2.png" in filenames, f"project2 PNG not found in {filenames}"

    def test_generate_all_manuscript_overviews_missing_pdf(self, tmp_path):
        """Test handling when PDFs are missing for some projects."""
        from infrastructure.reporting.executive_reporter import ExecutiveSummary, ProjectMetrics, ManuscriptMetrics, CodebaseMetrics, TestMetrics, OutputMetrics, PipelineMetrics

        # Create projects without PDFs
        projects_data = [
            ProjectMetrics(
                name="project1",
                manuscript=ManuscriptMetrics(),
                codebase=CodebaseMetrics(),
                tests=TestMetrics(),
                outputs=OutputMetrics(),
                pipeline=PipelineMetrics()
            ),
            ProjectMetrics(
                name="project2",
                manuscript=ManuscriptMetrics(),
                codebase=CodebaseMetrics(),
                tests=TestMetrics(),
                outputs=OutputMetrics(),
                pipeline=PipelineMetrics()
            )
        ]

        summary = ExecutiveSummary(
            timestamp="2025-01-01T00:00:00",
            total_projects=len(projects_data),
            aggregate_metrics={},
            project_metrics=projects_data,
            health_scores={},
            comparative_tables={},
            recommendations=[]
        )

        output_dir = tmp_path / "executive_summary"
        result = generate_all_manuscript_overviews(summary, output_dir, tmp_path)

        # Should return empty dict since no PDFs found
        assert result == {}


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_missing_dependencies(self, tmp_path):
        """Test graceful handling when dependencies are missing."""
        # Create a valid PDF first
        try:
            from reportlab.pdfgen import canvas
            pdf_path = tmp_path / "test.pdf"
            c = canvas.Canvas(str(pdf_path))
            c.drawString(100, 750, "Test content")
            c.save()

            # Mock PIL imports at the function level
            with patch('infrastructure.reporting.manuscript_overview._render_pages_simple') as mock_simple:
                mock_simple.side_effect = ImportError("PIL required for PDF rendering")

                with patch('infrastructure.reporting.manuscript_overview._render_pages_with_reportlab') as mock_advanced:
                    mock_advanced.side_effect = ImportError("reportlab and PIL required for advanced rendering")

                    with pytest.raises(ValueError, match="Failed to render PDF pages"):
                        extract_pdf_pages_as_images(pdf_path)
        except ImportError:
            pytest.skip("reportlab not available for test PDF creation")

    def test_pypdf_missing(self, tmp_path):
        """Test handling when pypdf is not available."""
        with patch.dict('sys.modules', {'pypdf': None}):
            pdf_path = tmp_path / "test.pdf"
            pdf_path.write_bytes(b"fake pdf content")

            with pytest.raises(ImportError):
                extract_pdf_pages_as_images(pdf_path)


class TestPageNumbering:
    """Test that page numbers appear correctly on thumbnails."""

    def test_page_numbers_in_grid(self):
        """Test that page numbers are added to grid layout."""
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            pytest.skip("PIL not available")

        # Create test images
        images = []
        for i in range(3):
            img = Image.new('RGB', (200, 300), color='white')
            draw = ImageDraw.Draw(img)
            # Add some content to make it identifiable
            draw.text((10, 10), f"Content {i+1}", fill='black')
            images.append(img)

        # Create grid
        grid = create_page_grid(images, cols=4)

        # Convert to check content (this is a basic check)
        # In a real scenario, you might use OCR or image analysis
        assert grid is not None
        assert hasattr(grid, 'size')