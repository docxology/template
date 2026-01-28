"""Manuscript overview generation for executive reports.

This module generates visual overviews of manuscript PDFs by extracting all pages
as images and arranging them in a grid layout. Each page is rendered as a thumbnail
with page numbers, arranged in a 4-column grid.

Part of the infrastructure reporting layer (Layer 1) - reusable across projects.
"""

from __future__ import annotations

import math
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


def extract_pdf_pages_as_images(
    pdf_path: Path, dpi: int = 300
) -> List["PIL.Image.Image"]:
    """Extract each PDF page as a PIL Image.

    Uses pypdf to read PDF pages and renders them as images.
    Falls back to simplified text-based rendering if full rendering unavailable.

    Args:
        pdf_path: Path to the PDF file
        dpi: Resolution for image rendering (default: 300)

    Returns:
        List of PIL Images, one per PDF page

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If PDF is corrupted or has no pages
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("pypdf library required for PDF processing")

    # Read PDF
    try:
        reader = PdfReader(pdf_path)
        if len(reader.pages) == 0:
            raise ValueError(f"PDF has no pages: {pdf_path}")

        logger.info(f"Extracting {len(reader.pages)} pages from {pdf_path.name}")
    except Exception as e:
        raise ValueError(f"Failed to read PDF {pdf_path}: {e}")

    images = []

    # Try advanced rendering first (reportlab)
    try:
        images = _render_pages_with_reportlab(reader, dpi)
    except Exception as e:
        logger.warning(
            f"Advanced rendering failed, falling back to simple rendering: {e}"
        )
        try:
            images = _render_pages_simple(reader, dpi)
        except Exception as e2:
            logger.error(f"Simple rendering also failed: {e2}")
            raise ValueError(f"Failed to render PDF pages: {e2}")

    return images


def _render_pages_with_reportlab(
    reader: "PdfReader", dpi: int
) -> List["PIL.Image.Image"]:
    """Render PDF pages using reportlab for high-quality output."""
    try:
        import os
        import tempfile

        from PIL import Image
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas
    except ImportError:
        raise ImportError("reportlab and PIL required for advanced rendering")

    images = []

    for i, page in enumerate(reader.pages):
        # Create a temporary PDF for this page
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name

        try:
            # Create single-page PDF with reportlab
            c = canvas.Canvas(temp_pdf_path, pagesize=letter)
            c.setFont("Helvetica", 10)

            # Extract text from pypdf page
            page_text = page.extract_text()

            # Simple text rendering (could be enhanced)
            lines = page_text.split("\n")
            y_position = 750  # Start near top

            for line in lines[:50]:  # Limit lines to fit page
                if line.strip():
                    c.drawString(50, y_position, line[:80])  # Limit line length
                    y_position -= 12
                    if y_position < 50:
                        break

            # Add page number
            c.drawString(50, 30, f"Page {i + 1}")

            c.save()

            # Convert to PIL Image
            try:
                from pdf2image import convert_from_path

                page_images = convert_from_path(
                    temp_pdf_path, dpi=dpi, first_page=1, last_page=1
                )
                if page_images:
                    images.append(page_images[0])
                else:
                    # Fallback: create blank image
                    img = Image.new("RGB", (800, 1100), color="white")
                    images.append(img)
            except ImportError:
                # Fallback: create text-based image
                img = Image.new("RGB", (800, 1100), color="white")
                from PIL import ImageDraw, ImageFont

                draw = ImageDraw.Draw(img)
                try:
                    font = ImageFont.truetype("Helvetica", 12)
                except:
                    font = ImageFont.load_default()

                y_pos = 50
                for line in lines[:30]:
                    if line.strip():
                        draw.text((50, y_pos), line[:60], fill="black", font=font)
                        y_pos += 15
                        if y_pos > 1050:
                            break

                draw.text((50, 1070), f"Page {i + 1}", fill="black", font=font)
                images.append(img)

        finally:
            # Clean up temp file
            try:
                os.unlink(temp_pdf_path)
            except:
                pass

    return images


def _render_pages_simple(reader: "PdfReader", dpi: int) -> List["PIL.Image.Image"]:
    """Render PDF pages using simple text extraction and PIL drawing."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise ImportError("PIL required for PDF rendering")

    images = []

    for i, page in enumerate(reader.pages):
        # Create blank page image (standard letter size at given DPI)
        width = int(8.5 * dpi)  # 8.5 inches
        height = int(11 * dpi)  # 11 inches
        img = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(img)

        # Try to load a font
        try:
            font = ImageFont.truetype("Helvetica", 12)
        except:
            font = ImageFont.load_default()

        # Extract and render text
        try:
            page_text = page.extract_text()
            lines = page_text.split("\n")

            y_position = 50
            for line in lines[:40]:  # Limit lines
                if line.strip():
                    # Handle very long lines
                    line = line[:80] + "..." if len(line) > 80 else line
                    draw.text((50, y_position), line, fill="black", font=font)
                    y_position += 15
                    if y_position > height - 100:
                        break

        except Exception as e:
            logger.warning(f"Failed to extract text from page {i+1}: {e}")

        # Add page number
        draw.text((50, height - 50), f"Page {i + 1}", fill="black", font=font)

        images.append(img)

    return images


def create_page_grid(
    images: List["PIL.Image.Image"],
    cols: int = 4,
    padding: int = 10,
    max_thumb_size: Tuple[int, int] = (600, 800),
) -> "PIL.Image.Image":
    """Arrange page images in a grid layout.

    Args:
        images: List of PIL Images (one per page)
        cols: Number of columns in grid (default: 4)
        padding: Padding between thumbnails in pixels (default: 10)
        max_thumb_size: Maximum size for each thumbnail (width, height) (default: 600x800)

    Returns:
        Single PIL Image containing the grid layout
    """
    if not images:
        raise ValueError("No images provided for grid creation")

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise ImportError("PIL required for image processing")
    """Arrange page images in a grid layout.

    Args:
        images: List of PIL Images (one per page)
        cols: Number of columns in grid (default: 4)
        padding: Padding between thumbnails in pixels (default: 10)
        max_thumb_size: Maximum size for each thumbnail (width, height) (default: 600x800)

    Returns:
        Single PIL Image containing the grid layout
    """
    if not images:
        raise ValueError("No images provided for grid creation")

    # Calculate grid dimensions
    num_images = len(images)
    rows = math.ceil(num_images / cols)

    # Resize images to fit grid cells
    thumb_width, thumb_height = max_thumb_size
    resized_images = []

    for img in images:
        # Maintain aspect ratio
        img_ratio = img.width / img.height
        if img.width > img.height:
            # Landscape or square
            new_width = min(img.width, thumb_width)
            new_height = int(new_width / img_ratio)
            if new_height > thumb_height:
                new_height = thumb_height
                new_width = int(new_height * img_ratio)
        else:
            # Portrait
            new_height = min(img.height, thumb_height)
            new_width = int(new_height * img_ratio)
            if new_width > thumb_width:
                new_width = thumb_width
                new_height = int(new_width / img_ratio)

        # Resize image
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        resized_images.append(resized)

    # Calculate grid dimensions
    grid_width = cols * (thumb_width + padding) + padding
    grid_height = rows * (thumb_height + padding) + padding

    # Create grid image
    grid_img = Image.new("RGB", (grid_width, grid_height), color="white")
    draw = ImageDraw.Draw(grid_img)

    # Try to load font for page numbers
    try:
        font = ImageFont.truetype("Helvetica", 10)
    except:
        font = ImageFont.load_default()

    # Place images in grid
    for i, img in enumerate(resized_images):
        row = i // cols
        col = i % cols

        x = col * (thumb_width + padding) + padding
        y = row * (thumb_height + padding) + padding

        # Center image in cell if smaller than max size
        cell_center_x = x + thumb_width // 2
        cell_center_y = y + thumb_height // 2
        img_x = cell_center_x - img.width // 2
        img_y = cell_center_y - img.height // 2

        # Paste image
        grid_img.paste(img, (img_x, img_y))

        # Add page number label
        label = f"Page {i + 1}"
        draw.text((img_x + 5, img_y + 5), label, fill="black", font=font)

    # Add title
    title = f"Manuscript Overview - {num_images} Pages"
    try:
        title_font = ImageFont.truetype("Helvetica-Bold", 16)
    except:
        title_font = ImageFont.load_default()

    draw.text((padding, padding // 2), title, fill="black", font=title_font)

    return grid_img


def generate_manuscript_overview(
    pdf_path: Path, output_dir: Path, project_name: str, dpi: int = 300
) -> Dict[str, Path]:
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
        raise ValueError(f"No pages extracted from {pdf_path}")

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
    except Exception as e:
        logger.warning(f"Failed to save PDF overview: {e}")
        # Don't fail the whole operation if PDF save fails
        pdf_output_path = None

    result = {png_path.name: png_path}
    if pdf_output_path and pdf_output_path.exists():
        result[pdf_output_path.name] = pdf_output_path

    return result


def _save_image_as_pdf(image: "PIL.Image.Image", pdf_path: Path, title: str) -> None:
    """Save a PIL Image as a PDF file using reportlab."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas
    except ImportError:
        raise ImportError("reportlab required for PDF output")

    # Create PDF with the image
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    # Calculate scaling to fit page
    page_width, page_height = letter
    img_width, img_height = image.size

    # Scale to fit page with margins
    margin = 50
    available_width = page_width - 2 * margin
    available_height = page_height - 2 * margin

    scale_x = available_width / img_width
    scale_y = available_height / img_height
    scale = min(scale_x, scale_y)

    new_width = img_width * scale
    new_height = img_height * scale

    # Center on page
    x = (page_width - new_width) / 2
    y = (page_height - new_height) / 2

    # Convert PIL image to reportlab ImageReader
    img_reader = ImageReader(image)

    # Draw image
    c.drawImage(img_reader, x, y, width=new_width, height=new_height)

    # Add title
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(page_width / 2, page_height - 30, title)

    c.save()


def generate_all_manuscript_overviews(
    summary: "ExecutiveSummary", output_dir: Path, repo_root: Path
) -> Dict[str, Path]:
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

        # Try multiple locations and filename patterns for the manuscript PDF
        pdf_paths = [
            repo_root / "output" / project_name / f"{project_name}_combined.pdf",
            repo_root
            / "output"
            / project_name
            / "project_combined.pdf",  # legacy naming
            repo_root
            / "output"
            / project_name
            / "pdf"
            / f"{project_name}_combined.pdf",
            repo_root / "output" / project_name / "pdf" / "project_combined.pdf",
            repo_root
            / "projects"
            / project_name
            / "output"
            / "pdf"
            / "project_combined.pdf",
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
            overview_files = generate_manuscript_overview(
                pdf_path, output_dir, project_name
            )
            all_files.update(overview_files)
            logger.info(
                f"Generated overview files for {project_name}: {list(overview_files.keys())}"
            )
        except Exception as e:
            logger.warning(
                f"Failed to generate manuscript overview for {project_name}: {e}"
            )
            continue

    return all_files
