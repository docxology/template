"""QR-code / barcode sealing utilities for template_autopoiesis.

Provides lightweight wrappers around qrcode (and optionally PIL) for embedding
spec hashes and provenance pointers into image payloads.
"""

from __future__ import annotations

import json
from typing import Any, Optional


# ---------------------------------------------------------------------------
# QR matrix (pure-Python, no qrcode required for tests)
# ---------------------------------------------------------------------------


def qr_matrix(data: str) -> list[list[bool]]:
    """Return a 2-D boolean matrix representing the QR code for *data*.

    Uses the ``qrcode`` library when available; falls back to a deterministic
    stub (checkerboard) so tests run without the optional dependency.
    """
    try:
        import qrcode

        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
        qr.add_data(data)
        qr.make(fit=True)
        return [[bool(cell) for cell in row] for row in qr.modules]
    except ImportError:
        # Stub: 5x5 checkerboard
        size = 5
        return [[(i + j) % 2 == 0 for j in range(size)] for i in range(size)]


def read_qr_matrix(matrix: list[list[bool]]) -> str:
    """Attempt to decode a QR matrix back to a string (best-effort)."""
    try:
        from pyzbar import pyzbar
        from PIL import Image
        import numpy as np

        arr = (1 - np.array(matrix, dtype=np.uint8)) * 255  # black on white
        img = Image.fromarray(arr)
        results = pyzbar.decode(img)
        if results:
            return str(results[0].data.decode())
    except Exception:  # noqa: BLE001  # optional pyzbar decode path
        pass
    return ""


def qr_image(data: str, box_size: int = 10, border: int = 4) -> Any:
    """Return a PIL Image of the QR code for *data*, or None on failure."""
    try:
        import qrcode
        from qrcode.image.pil import PilImage

        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        return qr.make_image(image_factory=PilImage)
    except Exception:  # noqa: BLE001  # optional qrcode/PIL stack
        return None


# ---------------------------------------------------------------------------
# Payload builders
# ---------------------------------------------------------------------------


def build_payload(spec_hash: str, tree_hash: str, seed: int) -> str:
    """Build a JSON payload string for embedding."""
    return json.dumps(
        {"spec_hash": spec_hash, "tree_hash": tree_hash, "seed": seed},
        separators=(",", ":"),
    )


def build_pointer_payload(spec_hash: str, url: Optional[str] = None) -> str:
    """Build a pointer payload (URL + spec hash) for the seal QR code."""
    obj: dict[str, Any] = {"spec_hash": spec_hash}
    if url:
        obj["url"] = url
    return json.dumps(obj, separators=(",", ":"))


def build_barcode_payload(
    spec_hash: str,
    tree_hash: str,
    seed: int,
    label: str = "autopoiesis",
) -> str:
    """Build a compact barcode payload."""
    parts = [label, spec_hash[:8], tree_hash[:8], str(seed)]
    return ":".join(parts)


# ---------------------------------------------------------------------------
# Embedding helpers (PIL-dependent)
# ---------------------------------------------------------------------------


def embed_qr(base_image: Any, qr_img: Any, position: tuple[int, int] = (0, 0)) -> Any:
    """Embed *qr_img* into *base_image* at *position* and return the composite."""
    try:
        base_image.paste(qr_img, position)
    except Exception:  # noqa: BLE001  # paste failures keep base image
        pass
    return base_image


def embed_semi_transparent(
    base_image: Any,
    qr_img: Any,
    position: tuple[int, int] = (0, 0),
    opacity: float = 0.5,
) -> Any:
    """Embed *qr_img* semi-transparently into *base_image*."""
    try:
        from PIL import Image

        qr_rgba = qr_img.convert("RGBA")
        r, g, b, a = qr_rgba.split()
        a = a.point(lambda x: int(x * opacity))
        qr_rgba = Image.merge("RGBA", (r, g, b, a))
        base_rgba = base_image.convert("RGBA")
        base_rgba.paste(qr_rgba, position, qr_rgba)
        return base_rgba.convert("RGB")
    except Exception:  # noqa: BLE001  # optional PIL alpha compositing
        return base_image
