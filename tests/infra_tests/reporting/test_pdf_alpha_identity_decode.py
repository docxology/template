"""Actual valid native PDF identity and inverted Decode dictionary controls."""

from __future__ import annotations

import time
from io import BytesIO
from pathlib import Path

import pdfplumber
import pytest
from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, BooleanObject, FloatObject, NameObject, NumberObject
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from infrastructure.reporting.native_format_pdf_alpha_paint import (
    UnsupportedAlphaPaint,
    decode_native_rgba,
    decode_original_source_rgba,
)
from infrastructure.reporting.native_format_pdf_source_decode_bounds import SourceImageDecodeBudget
from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams


def original_pdf(mode: str) -> tuple[bytes, bytes]:
    image = Image.new(
        {"RGB": "RGB", "gray": "L", "SMask": "RGBA"}[mode], (4, 4), 96 if mode == "gray" else (30, 70, 110)
    )
    if mode == "SMask":
        image.putalpha(96)
    png = BytesIO()
    image.save(png, format="PNG")
    pdf = BytesIO()
    canvas = Canvas(pdf, pagesize=(120, 120), invariant=True)
    canvas.drawImage(ImageReader(BytesIO(png.getvalue())), 20, 20, width=40, height=40, mask="auto")
    canvas.showPage()
    canvas.save()
    return png.getvalue(), pdf.getvalue()


def declared_pdf(original: bytes, decode: tuple, *, mask: bool) -> bytes:
    reader = PdfReader(BytesIO(original))
    image = next(iter(reader.pages[0]["/Resources"]["/XObject"].values())).get_object()
    target = image["/SMask"].get_object() if mask else image
    values = [
        BooleanObject(value)
        if type(value) is bool
        else NumberObject(value)
        if type(value) is int
        else FloatObject(value)
        for value in decode
    ]
    target[NameObject("/Decode")] = ArrayObject(values)
    writer = PdfWriter()
    writer.add_page(reader.pages[0])
    stream = BytesIO()
    writer.write(stream)
    return stream.getvalue()


def native(pdf: bytes) -> dict:
    preflight_pdf_streams(pdf, deadline=time.monotonic() + 5, max_objects=4_000_000)
    with pdfplumber.open(BytesIO(pdf)) as document:
        assert len(document.pages) == 1 and len(document.pages[0].images) == 1
        return decode_native_rgba(
            document.pages[0].images[0]["stream"],
            deadline=time.monotonic() + 5,
            remaining_decoded_pixels=120_000_000,
            background_rgb=(255, 255, 255),
        )


@pytest.mark.parametrize("mode", ["RGB", "gray", "SMask"])
def test_actual_identity_decode_is_understood_and_retained(tmp_path: Path, mode: str) -> None:
    png, original = original_pdf(mode)
    decode = (0, 1) * (3 if mode == "RGB" else 1)
    changed = declared_pdf(original, decode, mask=mode == "SMask")
    assert changed != original
    (tmp_path / "original.pdf").write_bytes(original)
    (tmp_path / "explicit-identity.pdf").write_bytes(changed)
    source = decode_original_source_rgba(
        png, SourceImageDecodeBudget(1), deadline=time.monotonic() + 5, background_rgb=(255, 255, 255)
    )
    actual = native(changed)
    assert actual["rgba_sha256"] == source["rgba_sha256"]
    assert actual["soft_mask_decode" if mode == "SMask" else "image_decode"] == list(decode)


@pytest.mark.parametrize("decode", [(1, 0), (False, 1), (0, 0.75)])
def test_actual_inverted_boolean_or_nonidentity_mask_decode_is_refused(tmp_path: Path, decode: tuple) -> None:
    _, original = original_pdf("SMask")
    changed = declared_pdf(original, decode, mask=True)
    assert changed != original
    (tmp_path / "original.pdf").write_bytes(original)
    (tmp_path / "changed-mask-decode.pdf").write_bytes(changed)
    with pytest.raises(UnsupportedAlphaPaint, match="nonidentity Decode"):
        native(changed)
