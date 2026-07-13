"""Static integrity QR strip for transmission bookend pages."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger
from infrastructure.steganography.barcode_generators import generate_qr_code
from infrastructure.steganography.barcode_payload import (
    build_barcode_payload,
    build_citation_qr_text,
    build_integrity_qr_text,
    build_mailto_qr_text,
    build_metadata_qr_text,
)
from infrastructure.publishing.transmission_models import TransmissionContext

logger = get_logger(__name__)

STRIP_FILENAME = "transmission_integrity_strip.png"
MANIFEST_FILENAME = "transmission_manifest.json"

_LABEL_FONT_SIZE = 11
_QR_SIZE = 128
_QR_BOX_SIZE = 8
_QR_BORDER = 2
_LABEL_HEIGHT = 14
_MARGIN = 8
_SPACING = 10
_CODE128_HEIGHT = 104
_CODE128_WIDTH = 250
MIN_STRIP_WIDTH = 750
MIN_STRIP_HEIGHT = 200


def _author_names(authors: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for author in authors:
        if isinstance(author, dict) and author.get("name"):
            names.append(str(author["name"]))
    return names


def _author_emails(authors: list[dict[str, Any]]) -> list[str | None]:
    emails: list[str | None] = []
    for author in authors:
        if isinstance(author, dict):
            email = author.get("email")
            emails.append(str(email) if email else None)
    return emails


def _document_id(context: TransmissionContext) -> str:
    if context.pdf_sha256:
        return context.pdf_sha256[:16]
    if context.doi:
        return context.doi.rsplit(".", maxsplit=1)[-1][:16]
    return ""


def _load_font(size: int) -> Any:
    from PIL import ImageFont

    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _metadata_qr_text(context: TransmissionContext, authors: list[str], document_id: str) -> str:
    parts: list[str] = []
    if context.title:
        parts.append(context.title[:40])
    if context.zenodo_record_url:
        parts.append(context.zenodo_record_url[:40])
    elif context.github_release_url:
        parts.append(context.github_release_url[:40])
    if document_id:
        parts.append(f"Doc-ID {document_id[:16]}")
    base = (
        " | ".join(parts)
        if parts
        else build_metadata_qr_text(
            title=context.title,
            authors=authors,
            document_id=document_id,
        )
    )
    return base[:100]


def _citation_qr_text(context: TransmissionContext, authors: list[str]) -> str:
    if context.doi:
        return f"doi:{context.doi}"[:100]
    if context.github_release_url:
        return context.github_release_url[:100]
    return build_citation_qr_text(title=context.title, authors=authors)


def _integrity_qr_text(context: TransmissionContext, document_id: str, hashes: dict[str, str]) -> str:
    parts: list[str] = []
    if hashes.get("sha256"):
        parts.append(f"SHA-256 {hashes['sha256'][:24]}")
    if hashes.get("sha512"):
        parts.append(f"SHA-512 {hashes['sha512'][:24]}")
    if context.doi:
        parts.append(f"DOI {context.doi[:32]}")
    if document_id:
        parts.append(f"ID {document_id[:12]}")
    if parts:
        return " | ".join(parts)[:100]
    return build_integrity_qr_text(document_id=document_id, hashes=hashes)


def _url_qr_text(url: str | None, fallback: str) -> str:
    if url:
        return url[:100]
    return fallback[:100]


def build_transmission_manifest_payload(context: TransmissionContext) -> dict[str, Any]:
    """Structured manifest fields written to ``transmission_manifest.json``."""
    return {
        "title": context.title,
        "version": context.version,
        "doi": context.doi,
        "github_release_url": context.github_release_url,
        "github_repository": context.github_repository,
        "zenodo_record_url": context.zenodo_record_url,
        "pdf_sha256": context.pdf_sha256,
        "pdf_sha512": context.pdf_sha512,
        "published": context.published,
    }


def compact_manifest_json(context: TransmissionContext) -> str:
    """Compact JSON string for ManifestJSON QR (<=100 chars)."""
    payload = {
        "t": (context.title or "")[:24],
        "v": context.version or "",
        "d": (context.doi or "")[:32],
        "s": (context.pdf_sha256 or "")[:16],
    }
    return json.dumps(payload, separators=(",", ":"))[:100]


def write_transmission_manifest(output_path: Path, context: TransmissionContext) -> Path:
    """Write structured transmission manifest JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(build_transmission_manifest_payload(context), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    logger.info("Wrote transmission manifest: %s", output_path)
    return output_path


def _generate_code128_image(data: str, target_width: int, target_height: int) -> Any:
    from PIL import Image

    from infrastructure.steganography.barcode_generators import _get_barcode

    barcode_mod = _get_barcode()
    from barcode.writer import ImageWriter

    code128 = barcode_mod.get_barcode_class("code128")
    safe_data = "".join(ch for ch in data if 32 <= ord(ch) <= 126)[:48]
    bc = code128(safe_data, writer=ImageWriter())
    buf = io.BytesIO()
    bc.write(
        buf,
        options={
            "module_width": 0.18,
            "module_height": 6.0,
            "quiet_zone": 1,
            "font_size": 0,
            "write_text": False,
        },
    )
    buf.seek(0)
    image = Image.open(buf).convert("RGB")
    return image.resize((target_width, target_height), Image.Resampling.LANCZOS)


def _paste_qr_row(
    image: Any,
    draw: Any,
    font: Any,
    *,
    y_offset: int,
    items: list[tuple[str, str]],
    x_start: int,
) -> int:
    from PIL import Image

    x_cursor = x_start
    for label, data in items:
        qr_png = generate_qr_code(data, box_size=_QR_BOX_SIZE, border=_QR_BORDER)
        qr_image: Image.Image = Image.open(io.BytesIO(qr_png))
        if qr_image.size != (_QR_SIZE, _QR_SIZE):
            qr_image = qr_image.resize((_QR_SIZE, _QR_SIZE), Image.Resampling.LANCZOS)
        image.paste(qr_image, (x_cursor, y_offset))
        label_x = x_cursor + _QR_SIZE / 2
        draw.text((label_x, y_offset + _QR_SIZE + 1), label, fill=(60, 60, 60), font=font, anchor="mt")
        x_cursor += _QR_SIZE + _SPACING
    return x_cursor


def write_transmission_barcode_strip(
    output_path: Path,
    *,
    context: TransmissionContext,
    authors: list[dict[str, Any]],
) -> None:
    """Composite a dual-row labeled QR + Code128 strip PNG for bookend pages."""
    from PIL import Image, ImageDraw

    author_names = _author_names(authors)
    author_emails = _author_emails(authors)
    document_id = _document_id(context)
    hashes: dict[str, str] = {}
    if context.pdf_sha256:
        hashes["sha256"] = context.pdf_sha256
    if context.pdf_sha512:
        hashes["sha512"] = context.pdf_sha512

    code128_data = build_barcode_payload(
        title=context.title,
        hashes=hashes,
        document_id=document_id,
        extra={
            "DOI": (context.doi or "")[:32],
            "GH": (context.github_release_url or "")[:32],
        },
    )

    row1 = [
        ("Metadata", _metadata_qr_text(context, author_names, document_id)),
        ("Citation", _citation_qr_text(context, author_names)),
        ("Contact", build_mailto_qr_text(title=context.title, authors=author_names, author_emails=author_emails)),
        ("Integrity", _integrity_qr_text(context, document_id, hashes)),
    ]
    row2 = [
        ("Zenodo", _url_qr_text(context.zenodo_record_url, "pending")),
        ("GitHub", _url_qr_text(context.github_release_url, context.github_repository or "pending")),
        ("Manifest", compact_manifest_json(context)),
    ]

    row_width = 4 * _QR_SIZE + 3 * _SPACING + _CODE128_WIDTH + _MARGIN * 2
    row2_width = 3 * _QR_SIZE + 2 * _SPACING + _CODE128_WIDTH + _MARGIN * 2
    width = max(row_width, row2_width)
    height = _MARGIN * 2 + (_QR_SIZE + _LABEL_HEIGHT) * 2 + 6

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = _load_font(_LABEL_FONT_SIZE)

    row1_y = _MARGIN
    row2_y = _MARGIN + _QR_SIZE + _LABEL_HEIGHT + 4

    _paste_qr_row(image, draw, font, y_offset=row1_y, items=row1, x_start=_MARGIN)
    row2_end = _paste_qr_row(image, draw, font, y_offset=row2_y, items=row2, x_start=_MARGIN)

    code128_image = _generate_code128_image(code128_data, _CODE128_WIDTH, _CODE128_HEIGHT)
    code128_x = width - _MARGIN - _CODE128_WIDTH
    image.paste(code128_image, (code128_x, row1_y))
    draw.text((code128_x, row1_y + _CODE128_HEIGHT + 2), "Code128", fill=(80, 80, 80), font=font)
    draw.text((row2_end + 4, row2_y + _QR_SIZE // 2), code128_data[:36], fill=(100, 100, 100), font=font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG")
    logger.info("Wrote transmission integrity strip: %s (%dx%d)", output_path, width, height)
