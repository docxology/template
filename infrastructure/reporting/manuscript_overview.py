"""Manuscript overview generation for executive reports.

This module generates visual overviews of manuscript PDFs by extracting all pages
as images and arranging them in a grid layout. Each page is rendered as a thumbnail
with page numbers, arranged in a 4-column grid.

Part of the infrastructure reporting layer (Layer 1) - reusable across projects.

Implementation split across:
- ``page_rendering``: PDF page extraction and rendering
- ``page_grid``: Grid layout and PDF export
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from infrastructure.core.exceptions import PDFValidationError
from infrastructure.core.logging.utils import get_logger

# Re-export all public symbols so existing imports continue to work
from infrastructure.reporting.page_grid import _save_image_as_pdf, create_page_grid
from infrastructure.reporting.page_rendering import (
    _render_pages_simple,
    _render_pages_with_reportlab,
    extract_pdf_pages_as_images,
)

if TYPE_CHECKING:
    import PIL.Image

    from infrastructure.reporting.executive_reporter import ExecutiveSummary

logger = get_logger(__name__)

__all__ = [
    "extract_pdf_pages_as_images",
    "_render_pages_with_reportlab",
    "_render_pages_simple",
    "create_page_grid",
    "_save_image_as_pdf",
    "generate_manuscript_overview",
    "generate_all_manuscript_overviews",
]


def generate_manuscript_overview(
    pdf_path: Path, output_dir: Path, project_name: str, dpi: int = 300
) -> dict[str, Path]:
    """Generate manuscript overview images (PNG and PDF) for a project.

    Args:
        pdf_path: Path to the manuscript PDF
        output_dir: Directory to save output files
        project_name: Name of the project (for filename)
        dpi: Resolution for rendering (default: 300)

    Returns:
        Dictionary mapping format to output file path

    Raises:
        FileNotFoundError: If PDF doesn't exist
        ValueError: If PDF processing fails
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating manuscript overview for {project_name}")

    # Extract page images
    try:
        page_images = extract_pdf_pages_as_images(pdf_path, dpi)
    except Exception as e:
        logger.error(f"Failed to extract pages from {pdf_path}: {e}")
        raise

    if not page_images:
        raise PDFValidationError(f"No pages extracted from {pdf_path}")

    logger.info(f"Extracted {len(page_images)} page images")

    # Create grid layout
    try:
        grid_image = create_page_grid(page_images, cols=4)
    except Exception as e:
        logger.error(f"Failed to create page grid: {e}")
        raise

    # Save PNG
    png_path = output_dir / f"manuscript_overview_{project_name}.png"
    try:
        grid_image.save(png_path, "PNG", dpi=(dpi, dpi))
        logger.info(f"Saved PNG overview: {png_path}")
    except Exception as e:
        logger.error(f"Failed to save PNG: {e}")
        raise

    # Save PDF
    pdf_output_path = output_dir / f"manuscript_overview_{project_name}.pdf"
    try:
        # Convert PIL image to PDF using reportlab
        _save_image_as_pdf(grid_image, pdf_output_path, project_name)
        logger.info(f"Saved PDF overview: {pdf_output_path}")
    except Exception as e:  # noqa: BLE001 — PDF output is optional; PNG is the primary deliverable
        logger.warning(f"Failed to save PDF overview: {e}")
        # Don't fail the whole operation if PDF save fails
        pdf_output_path = None

    result = {png_path.name: png_path}
    if pdf_output_path and pdf_output_path.exists():
        result[pdf_output_path.name] = pdf_output_path

    return result


def generate_all_manuscript_overviews(
    summary: "ExecutiveSummary", output_dir: Path, repo_root: Path
) -> dict[str, Path]:
    """Generate manuscript overviews for all projects in the executive summary.

    Args:
        summary: ExecutiveSummary containing project information
        output_dir: Directory to save overview files
        repo_root: Root directory of the repository

    Returns:
        Dictionary mapping filenames to output file paths
    """
    all_files = {}

    for project in summary.project_metrics:
        project_name = project.name

        # Try standard locations for the manuscript PDF.
        pdf_paths = [
            repo_root / "output" / project_name / f"{project_name}_combined.pdf",
            repo_root / "output" / project_name / "pdf" / f"{project_name}_combined.pdf",
        ]

        pdf_path = None
        for candidate_path in pdf_paths:
            if candidate_path.exists():
                pdf_path = candidate_path
                break

        if not pdf_path:
            logger.warning(
                f"Manuscript PDF not found for project {project_name}, skipping overview generation"
            )
            continue

        try:
            logger.info(f"Generating manuscript overview for {project_name}")
            overview_files = generate_manuscript_overview(pdf_path, output_dir, project_name)
            all_files.update(overview_files)
            logger.info(
                f"Generated overview files for {project_name}: {list(overview_files.keys())}"
            )
        except (OSError, ImportError, ValueError, PDFValidationError) as e:
            logger.warning(f"Failed to generate manuscript overview for {project_name}: {e}")
            continue

    return all_files
