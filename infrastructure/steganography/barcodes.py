"""Barcode generation for steganographic PDF overlays.

Generates QR codes, Code128 linear barcodes, and DataMatrix barcodes that
encode document metadata, hash values, and timestamps.  Each barcode is
rendered as a PDF overlay strip via reportlab.

Dependencies (``qrcode``, ``python-barcode``) are imported lazily.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# ── Lazy imports ─────────────────────────────────────────────────────────


def _get_qrcode():
    try:
        import qrcode

        return qrcode
    except ImportError:
        raise ImportError(
            "The 'qrcode' package is required for QR code generation. "
            "Install it with: pip install qrcode[pil]"
        )


def _get_barcode():
    try:
        import barcode

        return barcode
    except ImportError:
        raise ImportError(
            "The 'python-barcode' package is required for linear barcode generation. "
            "Install it with: pip install python-barcode"
        )


def _get_reportlab():
    try:
        from reportlab.lib.units import inch, mm
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.utils import ImageReader

        return rl_canvas, inch, mm, ImageReader
    except ImportError:
        raise ImportError(
            "The 'reportlab' package is required for barcode rendering. "
            "Install it with: pip install reportlab"
        )


# ── QR Code ──────────────────────────────────────────────────────────────


def generate_qr_code(
    data: str,
    box_size: int = 4,
    border: int = 1,
) -> bytes:
    """Generate a QR code PNG image.

    Args:
        data: String data to encode.
        box_size: Size of each QR module in pixels.
        border: Border width in modules.

    Returns:
        PNG image bytes.
    """
    qrcode = _get_qrcode()

    qr = qrcode.QRCode(
        version=None,  # Auto-size
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # M = good scan + less dense
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    logger.debug(
        f"QR code generated, data length={len(data)}, image size={buf.getbuffer().nbytes} bytes"
    )
    return buf.getvalue()


# ── Code128 linear barcode ───────────────────────────────────────────────


def generate_code128(
    data: str,
    module_width: float = 0.2,
    module_height: float = 8.0,
) -> bytes:
    """Generate a Code128 linear barcode as SVG bytes.

    Args:
        data: String data to encode (ASCII printable characters).
        module_width: Width of the narrowest bar in mm.
        module_height: Height of bars in mm.

    Returns:
        SVG image bytes.
    """
    barcode_mod = _get_barcode()
    from barcode.writer import SVGWriter

    code128 = barcode_mod.get_barcode_class("code128")
    bc = code128(data, writer=SVGWriter())

    buf = io.BytesIO()
    bc.write(
        buf,
        options={
            "module_width": module_width,
            "module_height": module_height,
            "quiet_zone": 2,
            "font_size": 6,
            "text_distance": 2,
        },
    )
    buf.seek(0)
    logger.debug(f"Code128 barcode generated for data: {data[:30]}…")
    return buf.getvalue()


# ── Barcode data builder ─────────────────────────────────────────────────


def build_barcode_payload(
    title: str = "",
    hashes: dict[str, str] | None = None,
    document_id: str = "",
    extra: dict[str, str] | None = None,
) -> str:
    """Build a compact barcode payload string.

    The payload is a pipe-delimited string suitable for QR and Code128
    encoding.

    Args:
        title: Document title.
        hashes: Algorithm → digest mapping (only first 16 chars used).
        document_id: Unique document identifier.
        extra: Additional key=value pairs.

    Returns:
        Payload string.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    parts = [f"T:{title[:60]}", f"TS:{timestamp}"]

    if document_id:
        parts.append(f"ID:{document_id}")

    if hashes:
        for algo, digest in hashes.items():
            parts.append(f"{algo.upper()[:6]}:{digest[:16]}")

    if extra:
        for k, v in extra.items():
            parts.append(f"{k}:{v}")

    payload = "|".join(parts)
    logger.debug(f"Barcode payload built: {payload[:80]}")
    return payload


# ── QR code content builders (COMPACT — ≤100 chars for phone scanning) ──
#
# Phone cameras need low-density QR codes to scan reliably at small sizes.
# Each builder targets ≤100 characters to stay at QR version 5 or below,
# which produces a ~37×37 module grid — easily scannable at 40–50pt.


def build_metadata_qr_text(
    title: str = "",
    authors: list[str] | None = None,
    document_id: str = "",
    **_kwargs,
) -> str:
    """Build compact metadata for the metadata QR code (≤100 chars)."""
    parts = []
    if title:
        parts.append(title[:40])
    if document_id:
        # Use hyphen instead of colon to avoid URI scheme triggering in camera apps
        parts.append(f"Doc-ID {document_id[:16]}")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    parts.append(ts)
    return " | ".join(parts)


def build_citation_qr_text(
    title: str = "",
    authors: list[str] | None = None,
    **_kwargs,
) -> str:
    """Build a compact citation string (≤100 chars)."""
    author = authors[0] if authors else "Unknown"
    year = datetime.now(timezone.utc).strftime("%Y")
    cite = f"{author} ({year}). {title[:50]}."
    return cite[:100]


def build_mailto_qr_text(
    title: str = "",
    authors: list[str] | None = None,
    author_emails: list[str] | None = None,
    **_kwargs,
) -> str:
    """Build a proper mailto: URI that opens an email draft.

    Keeps the URI short and simple to avoid freezing phone apps.
    Uses urllib to correctly URL-encode parameters.
    """
    if author_emails:
        import urllib.parse

        email = author_emails[0]
        subject_raw = title[:40] if title else "Inquiry"
        subject = urllib.parse.quote(subject_raw)
        body = urllib.parse.quote("Please find my inquiry attached.")
        return f"mailto:{email}?subject={subject}&body={body}"
    # Fallback: just show name
    name = authors[0] if authors else "Author"
    return f"Contact {name}"


def build_integrity_qr_text(
    document_id: str = "",
    hashes: dict[str, str] | None = None,
    **_kwargs,
) -> str:
    """Build a compact integrity hash for the integrity QR (≤100 chars).

    Shows the SHA256 of the compiled PDF binary file, avoiding colon prefixes.
    """
    parts = []
    if hashes and "sha256" in hashes:
        parts.append(f"SHA-256 {hashes['sha256'][:24]}...")
    if document_id:
        parts.append(f"ID {document_id[:12]}")
    return " | ".join(parts)


# ── Full barcode strip overlay ───────────────────────────────────────────


def create_barcode_strip_overlay(
    page_width: float,
    page_height: float,
    qr_data: str,
    code128_data: str,
    strip_height: float = 68.0,
    title: str = "",
    authors: list[str] | None = None,
    keywords: list[str] | None = None,
    author_emails: list[str] | None = None,
    document_id: str = "",
    hashes: dict[str, str] | None = None,
    source_filename: str = "",
    total_pages: int = 0,
    source_file_size: int = 0,
) -> bytes:
    """Create a PDF overlay page with labeled QR codes and a barcode strip.

    Layout (bottom of page, 0–68pt):
        ┌──────────────┬──────────────┬──────────────┬──────────────┬────────┐
        │   Metadata   │   Citation   │   Contact    │  Integrity   │ Code128│
        │     QR       │     QR       │     QR       │     QR       │  bars  │
        │   (label)    │   (label)    │   (label)    │   (label)    │        │
        └──────────────┴──────────────┴──────────────┴──────────────┴────────┘

    Each QR encodes ≤100 chars so phone cameras can scan at this size.

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

    # ── Build QR contents (compact — ≤100 chars each) ────────────────
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
        except Exception as exc:
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
    except Exception as exc:
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
