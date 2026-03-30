"""Barcode image generators (QR code, Code128).

Lazy-imports ``qrcode``, ``python-barcode``, and ``reportlab`` to generate
barcode images in PNG and SVG formats.

Part of the infrastructure steganography layer (Layer 1).
"""

from __future__ import annotations

import io

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

# ── Lazy imports ─────────────────────────────────────────────────────────


def _get_qrcode():
    try:
        import qrcode  # type: ignore[import-untyped]
        return qrcode
    except ImportError as e:
        raise ImportError(
            "The 'qrcode' package is required for QR code generation. "
            "Install it with: pip install qrcode[pil]"
        ) from e


def _get_barcode():
    try:
        import barcode  # type: ignore[import-untyped]
        return barcode
    except ImportError as e:
        raise ImportError(
            "The 'python-barcode' package is required for linear barcode generation. "
            "Install it with: pip install python-barcode"
        ) from e


def _get_reportlab():
    try:
        from reportlab.lib.units import inch, mm  # type: ignore[import-untyped]
        from reportlab.pdfgen import canvas as rl_canvas  # type: ignore[import-untyped]
        from reportlab.lib.utils import ImageReader  # type: ignore[import-untyped]
        return rl_canvas, inch, mm, ImageReader
    except ImportError as e:
        raise ImportError(
            "The 'reportlab' package is required for barcode rendering. "
            "Install it with: pip install reportlab"
        ) from e


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
    from barcode.writer import SVGWriter  # type: ignore[import-untyped]

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
    logger.debug(f"Code128 barcode generated for data: {data[:30]}...")
    return buf.getvalue()
