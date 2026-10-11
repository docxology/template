"""Every-page glyph, vector and pixel parity for an admitted source reference."""

from __future__ import annotations

import hashlib
import math
import re
import time
from io import BytesIO
from typing import Any
from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams


def _glyph(glyph: dict[str, Any]) -> tuple[Any, ...]:
    values = tuple(float(glyph[key]) for key in ("x0", "x1", "top", "bottom", "size"))
    if not all(math.isfinite(value) for value in values):
        raise ValueError("native full-source glyph geometry is not finite")
    text = str(glyph["text"])
    if text.startswith("(cid:"):
        raise ValueError("native full-source glyph identity is unresolved")
    return (text, re.sub(r"^[A-Z]{6}\+", "", str(glyph["fontname"])), *values)


def _vector(item: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "object_type",
        "x0",
        "x1",
        "top",
        "bottom",
        "linewidth",
        "fill",
        "stroke",
        "stroking_color",
        "non_stroking_color",
        "dash",
        "path",
    )
    return {key: item.get(key) for key in keys}


def inspect_pdf_reference_parity(
    pdf_bytes: bytes,
    reference_bytes: bytes,
    raster_bytes: tuple[bytes, ...],
    reference_rasters: tuple[bytes, ...],
    *,
    deadline: float,
) -> dict[str, Any]:
    """Compare every native page to independently reconstructed source output.

    The caller must authenticate the reference's complete original source/tool
    custody. Identical native output cannot discharge an unobserved source node,
    unresolved domain obligation or unsupported source projection by itself.
    """
    import pdfplumber
    from PIL import Image, ImageChops

    if len(pdf_bytes) + len(reference_bytes) > 128 * 1024 * 1024:
        raise ValueError("full-source native PDF bytes exceed their finite budget")
    if sum(map(len, (*raster_bytes, *reference_rasters))) > 256 * 1024 * 1024:
        raise ValueError("full-source native page pixels exceed their finite budget")
    preflight_pdf_streams(pdf_bytes, deadline=deadline, max_objects=4_000_000)
    preflight_pdf_streams(reference_bytes, deadline=deadline, max_objects=4_000_000)
    findings: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    total_glyphs = 0
    total_vectors = 0
    with pdfplumber.open(BytesIO(pdf_bytes)) as native, pdfplumber.open(BytesIO(reference_bytes)) as reference:
        if not native.pages or max(len(native.pages), len(reference.pages)) > 500:
            raise ValueError("full-source native reference exceeds its page budget")
        if len(native.pages) != len(reference.pages):
            return {
                "schema_version": "template-native-full-source-pdf-parity-v1",
                "status": "fail",
                "findings": [{"code": "pdf.reference.pages"}],
                "pages": [],
            }
        if len(raster_bytes) != len(native.pages) or len(reference_rasters) != len(reference.pages):
            raise ValueError("full-source comparison requires every original page raster")
        for ordinal, (page, expected) in enumerate(zip(native.pages, reference.pages, strict=True), 1):
            if time.monotonic() >= deadline:
                raise TimeoutError("full-source native comparison exhausted its original deadline")
            actual_glyphs, expected_glyphs = [_glyph(g) for g in page.chars], [_glyph(g) for g in expected.chars]
            total_glyphs += len(actual_glyphs) + len(expected_glyphs)
            if total_glyphs > 4_000_000:
                raise ValueError("full-source comparison exceeds its complete glyph budget")
            dimensions = (page.width, page.height, page.rotation, tuple(page.mediabox))
            wanted_dimensions = (expected.width, expected.height, expected.rotation, tuple(expected.mediabox))
            if dimensions != wanted_dimensions:
                findings.append({"code": "pdf.reference.layout", "page": ordinal})
            glyph_match = len(actual_glyphs) == len(expected_glyphs) and all(
                actual[:2] == wanted[:2]
                and all(abs(a - b) <= 0.05 for a, b in zip(actual[2:], wanted[2:], strict=True))
                for actual, wanted in zip(actual_glyphs, expected_glyphs, strict=True)
            )
            if not glyph_match:
                findings.append({"code": "pdf.reference.glyphs", "page": ordinal})
            total_vectors += sum(
                len(items)
                for items in (page.lines, page.rects, page.curves, expected.lines, expected.rects, expected.curves)
            )
            if total_vectors > 4_000_000:
                raise ValueError("full-source comparison exceeds its complete vector budget")

            def links(native_page: Any) -> list[tuple[Any, ...]]:
                result = []
                for annotation in native_page.hyperlinks:
                    geometry = tuple(float(annotation[key]) for key in ("x0", "top", "x1", "bottom"))
                    if not all(math.isfinite(value) for value in geometry):
                        raise ValueError("native full-source Link annotation has nonfinite geometry")
                    result.append((annotation["uri"], *geometry))
                    if len(result) > 100_000:
                        raise ValueError("native full-source Link annotation census exceeds its finite budget")
                return result

            actual_links, expected_links = links(page), links(expected)
            links_match = actual_links == expected_links
            if not links_match:
                findings.append({"code": "pdf.reference.links", "page": ordinal})
            vectors = [_vector(item) for items in (page.lines, page.rects, page.curves) for item in items]
            expected_vectors = [
                _vector(item) for items in (expected.lines, expected.rects, expected.curves) for item in items
            ]
            if vectors != expected_vectors:
                findings.append({"code": "pdf.reference.vectors", "page": ordinal})
            with (
                Image.open(BytesIO(raster_bytes[ordinal - 1])) as pixels,
                Image.open(BytesIO(reference_rasters[ordinal - 1])) as wanted,
            ):
                if (
                    pixels.format != "PNG"
                    or wanted.format != "PNG"
                    or max(pixels.width * pixels.height, wanted.width * wanted.height) > 60_000_000
                ):
                    raise ValueError("full-source comparison requires bounded original PNG page pixels")
                for image, native_page in ((pixels, page), (wanted, expected)):
                    if (
                        abs(image.width - native_page.width * 150 / 72) > 2
                        or abs(image.height - native_page.height * 150 / 72) > 2
                    ):
                        raise ValueError("full-source comparison requires exact 150dpi native page dimensions")
                pixel_match = (
                    pixels.size == wanted.size
                    and ImageChops.difference(pixels.convert("RGB"), wanted.convert("RGB")).getbbox() is None
                )
                if not pixel_match:
                    findings.append({"code": "pdf.reference.pixels", "page": ordinal})
            pages.append(
                {
                    "page": ordinal,
                    "glyph_count": len(actual_glyphs),
                    "reference_glyph_count": len(expected_glyphs),
                    "glyphs_match": glyph_match,
                    "links_match": links_match,
                    "vectors_match": vectors == expected_vectors,
                    "pixels_match": pixel_match,
                    "raster_sha256": hashlib.sha256(raster_bytes[ordinal - 1]).hexdigest(),
                    "reference_raster_sha256": hashlib.sha256(reference_rasters[ordinal - 1]).hexdigest(),
                }
            )
    return {
        "schema_version": "template-native-full-source-pdf-parity-v1",
        "status": "fail" if findings else "pass",
        "input_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        "reference_sha256": hashlib.sha256(reference_bytes).hexdigest(),
        "findings": findings,
        "pages": pages,
    }
