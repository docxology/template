"""Barcode generation for steganographic PDF overlays.

Generates QR codes, Code128 linear barcodes, and DataMatrix barcodes that
encode document metadata, hash values, and timestamps.  Each barcode is
rendered as a PDF overlay strip via reportlab.

Dependencies (``qrcode``, ``python-barcode``) are imported lazily.

Implementation split across:
- ``barcode_generators``: QR code and Code128 image generation
- ``barcode_payload``: Compact text payload builders
"""

from __future__ import annotations

import io
from datetime import datetime, timezone

from infrastructure.core.logging.utils import get_logger

# Re-export all public symbols so existing imports continue to work
from infrastructure.steganography.barcode_generators import (
    _get_reportlab,
    generate_code128,
    generate_qr_code,
)
from infrastructure.steganography.barcode_payload import (
    build_barcode_payload,
    build_citation_qr_text,
    build_integrity_qr_text,
    build_mailto_qr_text,
    build_metadata_qr_text,
)

logger = get_logger(__name__)

__all__ = [
    # barcode_generators
    "generate_qr_code",
    "generate_code128",
    # barcode_payload
    "build_barcode_payload",
    "build_metadata_qr_text",
    "build_citation_qr_text",
    "build_mailto_qr_text",
    "build_integrity_qr_text",
    # this module
    "create_barcode_strip_overlay",
]


# ── Full barcode strip overlay ───────────────────────────────────────────


def create_barcode_strip_overlay(
    page_width: float,
    page_height: float,
    qr_data: str,
    code128_data: str,
    strip_height: float = 68.0,
    title: str = "",
    authors: list[str] | None = None,
    keywords: list[str | None] = None,
    author_emails: list[str | None] = None,
    document_id: str = "",
    hashes: dict[str, str] | None = None,
    source_filename: str = "",
    total_pages: int = 0,
    source_file_size: int = 0,
) -> bytes:
    """Create a PDF overlay page with labeled QR codes and a barcode strip.

    Layout (bottom of page, 0-68pt):
        +--------------+--------------+--------------+--------------+--------+
        |   Metadata   |   Citation   |   Contact    |  Integrity   | Code128|
        |     QR       |     QR       |     QR       |     QR       |  bars  |
        |   (label)    |   (label)    |   (label)    |   (label)    |        |
        +--------------+--------------+--------------+--------------+--------+

    Each QR encodes <=100 chars so phone cameras can scan at this size.

    Args:
        page_width: Target page width in points.
        page_height: Target page height in points.
        qr_data: Fallback data for backward compatibility.
        code128_data: Data for Code128 barcode.
        strip_height: Height of the barcode strip area in points.
        title: Document title for QR content.
        authors: Author names for QR content.
        keywords: Keywords for QR content.
        author_emails: Author emails for mailto QR.
        document_id: Document ID for integrity QR.
        hashes: Hash digests for integrity QR.
        source_filename: Original PDF filename.
        total_pages: Total page count.
        source_file_size: Original PDF file size in bytes.

    Returns:
        PDF bytes of the one-page overlay.
    """
    rl_canvas_mod, _inch, _mm, ImageReader = _get_reportlab()

    buf = io.BytesIO()
    c = rl_canvas_mod.Canvas(buf, pagesize=(page_width, page_height))

    # ── Layout constants ─────────────────────────────────────────────
    label_font_size = 5
    label_y = 6  # label text baseline (near page bottom, moved up from 4)
    qr_y = label_y + label_font_size + 5  # QR starts confidently above label (approx 16pt)
    qr_size = strip_height - qr_y - 2  # fill remaining strip height (approx 50pt)

    # Distribute QR codes evenly across available width
    n_qr = 4
    code128_width = 100  # reserve space for Code128 on the right
    margin = 14
    available_width = page_width - code128_width - margin * 2
    qr_spacing = (available_width - n_qr * qr_size) / (n_qr - 1) if n_qr > 1 else 0
    if qr_spacing < 8:
        qr_spacing = 8

    # ── Build QR contents (compact -- <=100 chars each) ────────────────
    qr_items = []

    # 1. Metadata QR
    meta_text = build_metadata_qr_text(
        title=title,
        authors=authors,
        document_id=document_id,
    )
    qr_items.append(("Metadata", meta_text))

    # 2. Citation QR
    cite_text = build_citation_qr_text(title=title, authors=authors)
    qr_items.append(("Citation", cite_text))

    # 3. Contact QR (mailto: link)
    contact_text = build_mailto_qr_text(
        title=title,
        authors=authors,
        author_emails=author_emails,
    )
    qr_items.append(("Contact", contact_text))

    # 4. Integrity QR (compact hash)
    integrity_text = build_integrity_qr_text(
        document_id=document_id,
        hashes=hashes,
    )
    qr_items.append(("Integrity", integrity_text))

    # ── Draw QR codes with labels ────────────────────────────────────
    x_cursor = margin

    for label, data in qr_items:
        try:
            qr_png = generate_qr_code(data, box_size=3, border=1)
            qr_reader = ImageReader(io.BytesIO(qr_png))
            c.drawImage(
                qr_reader,
                x=x_cursor,
                y=qr_y,
                width=qr_size,
                height=qr_size,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception as exc:  # noqa: BLE001 — reportlab rendering exceptions vary by backend
            logger.warning(f"QR code rendering failed for {label}: {exc}")

        # Label centred below QR
        c.saveState()
        c.setFont("Helvetica", label_font_size)
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.drawCentredString(x_cursor + qr_size / 2, label_y, label)
        c.restoreState()

        x_cursor += int(qr_size + qr_spacing)

    # ── Code128 barcode bars (right side) ────────────────────────────
    barcode_x_start = page_width - code128_width - margin + 10
    try:
        c.saveState()
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.3)

        safe_data = "".join(ch for ch in code128_data if 32 <= ord(ch) <= 126)[:40]
        bar_x = barcode_x_start
        bar_bottom = qr_y + 4
        bar_top = qr_y + qr_size - 4
        for ch in safe_data:
            bar_width = (ord(ch) % 3 + 1) * 0.5
            c.line(bar_x, bar_bottom, bar_x, bar_top)
            bar_x += bar_width + 0.5

        # Label below bars
        c.setFont("Courier", 3)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawString(barcode_x_start, label_y, safe_data[:40])
        c.restoreState()
    except Exception as exc:  # noqa: BLE001 — reportlab rendering exceptions vary by backend
        logger.warning(f"Code128 rendering failed: {exc}")

    # ── Timestamp (far right, vertically centred) ────────────────────
    c.saveState()
    c.setFont("Courier", 3.5)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    c.drawRightString(page_width - 6, qr_y + qr_size + 2, ts)
    c.restoreState()

    c.save()
    return buf.getvalue()
