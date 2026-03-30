"""PDF page rendering to PIL images.

Extracts pages from PDF files and renders them as PIL Images using either
reportlab (high-quality) or simple text-based rendering (fallback).

Part of the infrastructure reporting layer (Layer 1) - reusable across projects.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from infrastructure.core.exceptions import FileNotFoundError, PDFValidationError
from infrastructure.core.logging.utils import get_logger

if TYPE_CHECKING:
    import PIL.Image
    from pypdf import PdfReader

logger = get_logger(__name__)


def extract_pdf_pages_as_images(pdf_path: Path, dpi: int = 300) -> list["PIL.Image.Image"]:
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
        raise FileNotFoundError(f"PDF file not found: {pdf_path}", context={"file": str(pdf_path)})

    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise ImportError("pypdf library required for PDF processing") from e

    # Read PDF
    try:
        reader = PdfReader(pdf_path)
        if len(reader.pages) == 0:
            raise PDFValidationError(f"PDF has no pages: {pdf_path}")

        logger.info(f"Extracting {len(reader.pages)} pages from {pdf_path.name}")
    except PDFValidationError:
        raise
    except (OSError, ValueError) as e:
        raise PDFValidationError(f"Failed to read PDF {pdf_path}: {e}") from e

    images = []

    # Try advanced rendering first (reportlab)
    try:
        images = _render_pages_with_reportlab(reader, dpi)
    except (ImportError, OSError, ValueError) as e:  # noqa: BLE001 — fall back to simple rendering path
        logger.warning(f"Advanced rendering failed, falling back to simple rendering: {e}")
        try:
            images = _render_pages_simple(reader, dpi)
        except (OSError, ValueError, RuntimeError, ImportError) as e2:
            logger.error(f"Simple rendering also failed: {e2}")
            raise PDFValidationError(f"Failed to render PDF pages: {e2}") from e2

    return images


def _render_pages_with_reportlab(reader: "PdfReader", dpi: int) -> list["PIL.Image.Image"]:
    """Render PDF pages using reportlab for high-quality output."""
    try:
        import os
        import tempfile

        from PIL import Image
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.utils import ImageReader  # noqa: F401
        from reportlab.pdfgen import canvas
    except ImportError as e:
        raise ImportError("reportlab and PIL required for advanced rendering") from e

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

                page_images = convert_from_path(temp_pdf_path, dpi=dpi, first_page=1, last_page=1)
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
                except OSError as e:
                    logger.debug(f"Could not load Helvetica font: {e}")
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
            except OSError as e:
                logger.debug(f"Failed to clean up temp file {temp_pdf_path}: {e}")

    return images


def _render_pages_simple(reader: "PdfReader", dpi: int) -> list["PIL.Image.Image"]:
    """Render PDF pages using simple text extraction and PIL drawing."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as e:
        raise ImportError("PIL required for PDF rendering") from e

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
        except OSError as e:
            logger.debug(f"Could not load Helvetica font: {e}")
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

        except (OSError, ValueError, KeyError) as e:
            logger.warning(f"Failed to extract text from page {i + 1}: {e}")

        # Add page number
        draw.text((50, height - 50), f"Page {i + 1}", fill="black", font=font)

        images.append(img)

    return images
