"""Valid real lossless RGB/gray/mask samples may begin with JPEG magic bytes."""

from __future__ import annotations

import time
from io import BytesIO
from pathlib import Path

import pdfplumber
import pytest
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from infrastructure.reporting.native_format_pdf_alpha_paint import decode_native_rgba, decode_original_source_rgba
from infrastructure.reporting.native_format_pdf_source_decode_bounds import SourceImageDecodeBudget
from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams


@pytest.mark.parametrize("mode", ["RGB", "gray", "SMask"])
def test_real_lossless_raw_magic_prefix_is_not_misclassified_as_jpeg(tmp_path: Path, mode: str) -> None:
    if mode == "RGB":
        image = Image.new("RGB", (2, 2), (255, 216, 25))
    elif mode == "gray":
        image = Image.new("L", (2, 2), 255)
        image.putpixel((1, 0), 216)
    else:
        image = Image.new("RGBA", (2, 2), (30, 70, 110, 255))
        image.putpixel((1, 0), (30, 70, 110, 216))
    png = BytesIO()
    image.save(png, format="PNG")
    source = decode_original_source_rgba(
        png.getvalue(), SourceImageDecodeBudget(1), deadline=time.monotonic() + 5, background_rgb=(255, 255, 255)
    )
    path = tmp_path / f"raw-{mode}.pdf"
    canvas = Canvas(str(path), pagesize=(120, 120), invariant=True)
    canvas.drawImage(ImageReader(BytesIO(png.getvalue())), 20, 20, width=40, height=40, mask="auto")
    canvas.showPage()
    canvas.save()
    pdf = path.read_bytes()
    preflight_pdf_streams(pdf, deadline=time.monotonic() + 5, max_objects=4_000_000)
    with pdfplumber.open(BytesIO(pdf)) as document:
        from pdfminer.pdftypes import resolve1

        stream = document.pages[0].images[0]["stream"]
        actual = resolve1(stream.attrs["SMask"]) if mode == "SMask" else stream
        assert actual.get_data().startswith(b"\xff\xd8")
        native = decode_native_rgba(
            stream,
            deadline=time.monotonic() + 5,
            remaining_decoded_pixels=120_000_000,
            background_rgb=(255, 255, 255),
        )
    assert native["rgba_sha256"] == source["rgba_sha256"]
    assert native["paint_rgb_sha256"] == source["paint_rgb_sha256"]
