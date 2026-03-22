"""Watermark and text overlay generation.

Creates transparent overlay pages using reportlab that are merged on top of
the original PDF pages.  Techniques include diagonal watermark text,
tiled QR code overlays, invisible Unicode metadata layers, and page-footer
document-ID stamps.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class FooterConfig:
    """Parameters for the two-line page-footer overlay."""

    document_id: str = ""
    page_number: int = 1
    total_pages: int = 1
    hash_short: str = ""
    title: str = ""
    authors: str = ""
    source_filename: str = ""
    source_file_size: int = 0
    font_size: int = 5


# ── Lazy imports ─────────────────────────────────────────────────────────


def _get_reportlab():
    """Lazily import reportlab components."""
    try:
        from reportlab.lib.pagesizes import letter  # type: ignore[import-untyped]
        from reportlab.lib.units import inch  # type: ignore[import-untyped]
        from reportlab.pdfgen import canvas as rl_canvas  # type: ignore[import-untyped]
        return rl_canvas, letter, inch
    except ImportError:
        raise ImportError(
            "The 'reportlab' package is required for overlay generation. "
            "Install it with: pip install reportlab"
        ) from None


# ── Public API ───────────────────────────────────────────────────────────


def create_watermark_overlay(
    page_width: float,
    page_height: float,
    text: str = "CONFIDENTIAL",
    opacity: float = 0.08,
    color_rgb: tuple[int, int, int] = (128, 128, 128),
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
    c.setFillColorRGB(
        color_rgb[0] / 255.0,
        color_rgb[1] / 255.0,
        color_rgb[2] / 255.0,
        alpha=opacity,
    )
    c.setFont("Helvetica-Bold", font_size)

    angle = 45
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


def create_qr_overlay(
    page_width: float,
    page_height: float,
    qr_data: str,
    opacity: float = 0.06,
    qr_size: float = 72.0,
    spacing: float = 36.0,
) -> bytes:
    """Generate a tiled QR code overlay across the entire page.

    Creates a grid of semi-transparent QR codes, each encoding the same
    document metadata.  This produces an information-dense overlay that
    embeds verifiable data across the page surface.

    Args:
        page_width: Target page width in points.
        page_height: Target page height in points.
        qr_data: String data to encode in each QR tile.
        opacity: Alpha transparency for the QR tiles.
        qr_size: Size of each QR tile in points (default 72 = 1 inch).
        spacing: Gap between tiles in points.

    Returns:
        PDF bytes of the one-page overlay.
    """
    rl_canvas_mod, _letter, _inch = _get_reportlab()
    try:
        from reportlab.lib.utils import ImageReader  # type: ignore[import-untyped]
        from infrastructure.steganography.barcodes import generate_qr_code
    except ImportError as exc:
        raise ImportError(
            "QR overlay requires optional dependencies: uv sync --group steganography"
        ) from exc

    qr_png = generate_qr_code(qr_data, box_size=4, border=1)

    buf = io.BytesIO()
    c = rl_canvas_mod.Canvas(buf, pagesize=(page_width, page_height))

    c.saveState()
    c.setFillAlpha(opacity)

    # Tile QR codes across the page — leave margins for footer/barcode areas
    margin_bottom = 82  # clear the barcode strip + footer area
    margin_top = 36
    margin_x = 18

    step = qr_size + spacing
    x = margin_x
    while x + qr_size <= page_width - margin_x:
        y = margin_bottom
        while y + qr_size <= page_height - margin_top:
            qr_reader = ImageReader(io.BytesIO(qr_png))
            c.drawImage(
                qr_reader,
                x=x,
                y=y,
                width=qr_size,
                height=qr_size,
                preserveAspectRatio=True,
                mask="auto",
            )
            y += int(step)
        x += int(step)

    c.restoreState()
    c.save()

    return buf.getvalue()


def create_footer_overlay(
    page_width: float,
    page_height: float,
    cfg: FooterConfig | None = None,
    *,
    document_id: str = "",
    page_number: int = 1,
    total_pages: int = 1,
    hash_short: str = "",
    title: str = "",
    authors: str = "",
    source_filename: str = "",
    source_file_size: int = 0,
    font_size: int = 5,
) -> bytes:
    """Generate a two-line footer overlay with comprehensive document metrics.

    The footer sits ABOVE the barcode strip (which occupies 0–58pt).

    Layout (two lines):
        Line 1:  Title                                          Author(s)
        Line 2:  ID: <short> | Source: <file> | <size> | Page N/M | SHA256 (source): <hash> | <ts>

    Args:
        page_width: Target page width in points.
        page_height: Target page height in points.
        cfg: Footer configuration dataclass. If omitted, keyword fields build a :class:`FooterConfig`.

        document_id: Short document identifier (when ``cfg`` is omitted).
        page_number: Current page (1-based).
        total_pages: Total pages in document.
        hash_short: Short hash string for the metrics line.
        title: Document title (first footer line).
        authors: Author string (right side of first line).
        source_filename: Original filename for metrics.
        source_file_size: Byte size of source file.
        font_size: Footer font size in points.

    Returns:
        PDF bytes of the one-page footer overlay.
    """
    if cfg is None:
        cfg = FooterConfig(
            document_id=document_id,
            page_number=page_number,
            total_pages=total_pages,
            hash_short=hash_short,
            title=title,
            authors=authors,
            source_filename=source_filename,
            source_file_size=source_file_size,
            font_size=font_size,
        )

    rl_canvas, _letter, _inch = _get_reportlab()
    from datetime import datetime, timezone

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(page_width, page_height))

    c.saveState()

    # Clear the bottom 90pt so our steganography footer is pristine.
    c.setFillColorRGB(1, 1, 1, alpha=1.0)
    c.rect(0, 0, page_width, 90, fill=1, stroke=0)

    separator_y = 70
    line2_y = 74  # lower line (metrics)
    line1_y = 82  # upper line (title/author)
    margin = 18

    c.setStrokeColorRGB(0.65, 0.65, 0.65, alpha=0.5)
    c.setLineWidth(0.4)
    c.line(margin, separator_y, page_width - margin, separator_y)

    c.setFillColorRGB(0.3, 0.3, 0.3, alpha=0.7)

    c.setFont("Helvetica", cfg.font_size)
    title_short = cfg.title[:55] + "…" if len(cfg.title) > 55 else cfg.title
    if title_short:
        c.drawString(margin, line1_y, title_short)
    if cfg.authors:
        c.drawRightString(page_width - margin, line1_y, cfg.authors)

    c.setFont("Courier", cfg.font_size - 0.5)

    parts = []

    id_short = cfg.document_id[:12] if len(cfg.document_id) > 12 else cfg.document_id
    parts.append(f"ID: {id_short}")

    if cfg.source_filename:
        fn_short = (
            cfg.source_filename[:20] + "…" if len(cfg.source_filename) > 20 else cfg.source_filename
        )
        parts.append(f"Source: {fn_short}")

    if cfg.source_file_size:
        if cfg.source_file_size >= 1024 * 1024:
            size_str = f"{cfg.source_file_size / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{cfg.source_file_size / 1024:.1f} KB"
        parts.append(size_str)

    parts.append(f"Page {cfg.page_number}/{cfg.total_pages}")

    if cfg.hash_short:
        parts.append(f"SHA256 (compiled PDF): {cfg.hash_short}")

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    parts.append(ts)

    metrics_text = "  │  ".join(parts)
    c.drawString(margin, line2_y, metrics_text)

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
