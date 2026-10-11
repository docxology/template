"""Actual PNG/native PDF soft-mask pixels and genuine altered-alpha controls."""

from __future__ import annotations

import time
from io import BytesIO
from pathlib import Path

import pdfplumber
import pytest
from PIL import Image, ImageDraw
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from infrastructure.reporting.native_format_pdf_alpha_paint import (
    UnsupportedAlphaPaint,
    decode_native_rgba,
    decode_original_source_rgba,
)
from infrastructure.reporting.native_format_pdf_source_decode_bounds import SourceImageDecodeBudget


def alpha_png(alpha: int = 96) -> bytes:
    image = Image.new("RGBA", (40, 32), (25, 55, 130, 255))
    ImageDraw.Draw(image).rectangle((20, 0, 39, 31), fill=(220, 75, 35, alpha))
    stream = BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def actual_pdf(path: Path, png: bytes, *, flatten: bool = False) -> bytes:
    if flatten:
        with Image.open(BytesIO(png)) as original:
            white = Image.new("RGBA", original.size, "white")
            flat = Image.alpha_composite(white, original).convert("RGB")
            output = BytesIO()
            flat.save(output, format="PNG")
            png = output.getvalue()
    canvas = Canvas(str(path), pagesize=(240, 180), invariant=True)
    canvas.drawImage(ImageReader(BytesIO(png)), 30, 30, width=120, height=96, mask="auto")
    canvas.showPage()
    canvas.save()
    return path.read_bytes()


def decoded_pdf(content: bytes, remaining: int = 120_000_000) -> dict:
    with pdfplumber.open(BytesIO(content)) as pdf:
        assert len(pdf.pages) == 1 and len(pdf.pages[0].images) == 1
        return decode_native_rgba(
            pdf.pages[0].images[0]["stream"],
            deadline=time.monotonic() + 5,
            remaining_decoded_pixels=remaining,
            background_rgb=(255, 255, 255),
        )


def original(content: bytes) -> dict:
    return decode_original_source_rgba(
        content, SourceImageDecodeBudget(1), deadline=time.monotonic() + 5, background_rgb=(255, 255, 255)
    )


def test_actual_original_alpha_and_native_soft_mask_have_exact_pixel_identity(tmp_path: Path) -> None:
    source = original(alpha_png())
    native = decoded_pdf(actual_pdf(tmp_path / "original.pdf", alpha_png()))
    assert source["alpha_extrema"] == [96, 255]
    assert native["rgba_sha256"] == source["rgba_sha256"]
    assert native["paint_rgb_sha256"] == source["paint_rgb_sha256"]
    assert native["consumed_decoded_pixels"] == 2 * 40 * 32


def test_actual_altered_alpha_and_flattened_native_cannot_supply_original_mask(tmp_path: Path) -> None:
    source = original(alpha_png())
    changed = decoded_pdf(actual_pdf(tmp_path / "changed-alpha.pdf", alpha_png(192)))
    flat = decoded_pdf(actual_pdf(tmp_path / "lost-mask.pdf", alpha_png(), flatten=True))
    assert changed["rgba_sha256"] != source["rgba_sha256"]
    assert changed["paint_rgb_sha256"] != source["paint_rgb_sha256"]
    assert flat["rgba_sha256"] != source["rgba_sha256"]
    assert flat["paint_rgb_sha256"] == source["paint_rgb_sha256"]


def test_transparent_original_requires_explicit_admitted_background() -> None:
    with pytest.raises(UnsupportedAlphaPaint, match="independently admitted solid background"):
        decode_original_source_rgba(alpha_png(), SourceImageDecodeBudget(1), deadline=time.monotonic() + 5)


def test_actual_native_mask_is_charged_before_aggregate_decode(tmp_path: Path) -> None:
    content = actual_pdf(tmp_path / "bounded-mask.pdf", alpha_png())
    with pytest.raises(ValueError, match="aggregate decoded-pixel"):
        decoded_pdf(content, remaining=40 * 32)
