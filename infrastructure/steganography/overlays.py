"""Watermark and text overlay generation.

Creates transparent overlay pages using reportlab that are merged on top of
the original PDF pages.  Techniques include diagonal watermark text,
invisible Unicode metadata layers, and page-footer document-ID stamps.
"""

from __future__ import annotations

import io
import math
from pathlib import Path
from typing import Optional, Tuple

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# ── Lazy imports ─────────────────────────────────────────────────────────

def _get_reportlab():
    """Lazily import reportlab components."""
    try:
        from reportlab.lib.pagesizes import letter  # type: ignore
        from reportlab.lib.units import inch  # type: ignore
        from reportlab.pdfgen import canvas as rl_canvas  # type: ignore
        return rl_canvas, letter, inch
    except ImportError:
        raise ImportError(
            "The 'reportlab' package is required for overlay generation. "
            "Install it with: pip install reportlab"
        )


# ── Public API ───────────────────────────────────────────────────────────


def create_watermark_overlay(
    page_width: float,
    page_height: float,
    text: str = "CONFIDENTIAL",
    opacity: float = 0.08,
    color_rgb: Tuple[int, int, int] = (128, 128, 128),
    font_size: int = 60,
    repeat_count: int = 5,
) -> bytes:
    """Generate a single-page PDF with a repeating diagonal watermark.

    Args:
        page_width: Target page width in points.
        page_height: Target page height in points.
        text: Watermark text string.
        opacity: Alpha transparency (0.0 = invisible, 1.0 = opaque).
        color_rgb: RGB colour tuple (0–255 per channel).
        font_size: Font size in points.
        repeat_count: Number of text repetitions distributed vertically.

    Returns:
        PDF bytes of the one-page overlay.
    """
    rl_canvas, _letter, _inch = _get_reportlab()

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(page_width, page_height))

    c.saveState()
    # Set transparency
    c.setFillColorRGB(
        color_rgb[0] / 255.0,
        color_rgb[1] / 255.0,
        color_rgb[2] / 255.0,
        alpha=opacity,
    )
    c.setFont("Helvetica-Bold", font_size)

    # Diagonal angle
    angle = 45
    diagonal = math.sqrt(page_width**2 + page_height**2)

    # Distribute watermark text across the page
    y_step = page_height / (repeat_count + 1)
    for i in range(1, repeat_count + 1):
        c.saveState()
        c.translate(page_width / 2, y_step * i)
        c.rotate(angle)
        c.drawCentredString(0, 0, text)
        c.restoreState()

    c.restoreState()
    c.save()

    return buf.getvalue()


def create_footer_overlay(
    page_width: float,
    page_height: float,
    document_id: str,
    page_number: int,
    total_pages: int,
    hash_short: str = "",
    font_size: int = 6,
) -> bytes:
    """Generate a page-footer overlay with document ID, page number, and hash.

    Args:
        page_width: Target page width in points.
        page_height: Target page height in points.
        document_id: Unique document identifier string.
        page_number: Current page number (1-indexed).
        total_pages: Total number of pages.
        hash_short: Short hash string (first 16 chars) overlaid in footer.
        font_size: Font size for footer text.

    Returns:
        PDF bytes of the one-page footer overlay.
    """
    rl_canvas, _letter, _inch = _get_reportlab()

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(page_width, page_height))

    c.saveState()
    c.setFillColorRGB(0.4, 0.4, 0.4, alpha=0.5)
    c.setFont("Courier", font_size)

    y_pos = 8  # points from bottom
    left_text = f"DOC-ID: {document_id}"
    centre_text = f"Page {page_number}/{total_pages}"
    right_text = f"SHA256: {hash_short}" if hash_short else ""

    c.drawString(10, y_pos, left_text)
    c.drawCentredString(page_width / 2, y_pos, centre_text)
    if right_text:
        c.drawRightString(page_width - 10, y_pos, right_text)

    c.restoreState()
    c.save()

    return buf.getvalue()


def create_invisible_text_overlay(
    page_width: float,
    page_height: float,
    hidden_text: str,
) -> bytes:
    """Create an overlay with invisible (render-mode 3) text.

    The text is present in the PDF content stream and selectable/searchable
    but rendered with invisible ink.  Useful for embedding metadata that
    survives copy-paste or text extraction.

    Args:
        page_width: Target page width in points.
        page_height: Target page height in points.
        hidden_text: Text to embed invisibly.

    Returns:
        PDF bytes of the one-page overlay.
    """
    rl_canvas, _letter, _inch = _get_reportlab()

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(page_width, page_height))

    c.saveState()
    # Render mode 3 = invisible (no fill, no stroke)
    c.setFont("Helvetica", 1)  # 1-point — practically invisible even if rendered
    c.setFillColorRGB(1, 1, 1, alpha=0)  # Fully transparent fallback
    text_obj = c.beginText(0, 0)
    text_obj.setTextRenderMode(3)  # Invisible
    text_obj.textLine(hidden_text)
    c.drawText(text_obj)
    c.restoreState()
    c.save()

    return buf.getvalue()
