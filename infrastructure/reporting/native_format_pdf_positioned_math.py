"""Independent equation interpretation at complete-source XeTeX paint positions.

Source-only marked whole-reference positions locate repeated equations; an
independently constructed source-engine equation reference determines expected
glyphs, relative geometry and ink. Matching whole writers alone never passes.
Original process/SDK/source/reproduction custody is admitted by the caller.
"""

from __future__ import annotations

import hashlib
import math
import re
import time
from io import BytesIO
from typing import Any, cast

from infrastructure.reporting.native_format_pdf_positions import (
    instrument_source_math_positions,
    source_math_paint_from_pdf,
)
from infrastructure.reporting.native_format_scientific_math import reference_math_glyphs, scientific_math_from_ast
from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams

SCHEMA = "template-native-pdf-source-positioned-math-v1"


def _font(glyph: dict[str, Any]) -> str:
    return re.sub(r"^[A-Z]{6}\+", "", str(glyph["fontname"]))


def _box(glyphs: list[dict[str, Any]]) -> list[float]:
    if not glyphs:
        raise ValueError("source-positioned equation has no actual glyph paint")
    values = [float(glyph[key]) for glyph in glyphs for key in ("x0", "x1", "top", "bottom", "size")]
    if any(not math.isfinite(value) for value in values):
        raise ValueError("source-positioned equation glyph bounds are not finite")
    return [
        min(glyph["x0"] for glyph in glyphs),
        min(glyph["top"] for glyph in glyphs),
        max(glyph["x1"] for glyph in glyphs),
        max(glyph["bottom"] for glyph in glyphs),
    ]


def inspect_pdf_positioned_math(
    pdf: bytes,
    rasters: tuple[bytes, ...],
    ast_bytes: bytes,
    *,
    source_tex: bytes,
    instrumented_pdf: bytes,
    interpreted_pdf: bytes,
    interpreted_rasters: tuple[bytes, ...],
    deadline: float,
) -> dict[str, Any]:
    """Recompute the source ledger and compare original glyph/vector/ink bytes.

    Source equations whose writer fragment cannot be independently located,
    rotated pages, empty/multiline markers and unmatched context typography
    retain blockers. No receipt's claimed Math count or pass bit is accepted.
    """
    import pdfplumber
    from PIL import Image, ImageChops, ImageStat

    if type(deadline) not in {int, float} or not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("positioned PDF math requires an original finite deadline")
    if sum(map(len, (*rasters, *interpreted_rasters))) > 256 * 1024 * 1024:
        raise ValueError("positioned PDF mathematics exceeds its aggregate raster-byte budget")
    for content in (pdf, instrumented_pdf, interpreted_pdf):
        preflight_pdf_streams(content, deadline=deadline, max_objects=4_000_000)
    nodes = scientific_math_from_ast(ast_bytes)
    _, bindings, position_blockers = instrument_source_math_positions(source_tex.decode(), nodes)
    if position_blockers or len(bindings) != len(nodes):
        return {
            "schema_version": SCHEMA,
            "status": "blocked",
            "observations": [],
            "findings": [],
            "blockers": list(position_blockers),
            "source_ast_sha256": hashlib.sha256(ast_bytes).hexdigest(),
        }
    paint_rows = source_math_paint_from_pdf(instrumented_pdf, bindings, deadline=deadline)
    interpreted = reference_math_glyphs(interpreted_pdf, nodes)
    if len(paint_rows) != len(nodes) or len(interpreted) != len(nodes):
        raise ValueError("complete source and independent equation occurrence sets differ")
    paint = {row["identity"]: row for row in paint_rows}
    observations = []
    findings = []
    blockers = []
    consumed: set[tuple[int, int]] = set()
    glyph_indexes: dict[int, dict[tuple[Any, ...], list[tuple[int, dict[str, Any]]]]] = {}
    with pdfplumber.open(BytesIO(pdf)) as document:
        if not document.pages or len(document.pages) > 500 or len(document.pages) != len(rasters):
            raise ValueError("positioned mathematics requires bounded every-page native rasters")
        if sum(len(page.chars) for page in document.pages) > 2_000_000:
            raise ValueError("positioned mathematics exceeds its native glyph budget")
        for node, reference in zip(nodes, interpreted, strict=True):
            if time.monotonic() >= deadline:
                raise TimeoutError("source-positioned mathematics exhausted its original deadline")
            row = paint.get(node.identity)
            if row is None or reference["identity"] != node.identity:
                raise ValueError("source-positioned equation identity differs from original AST")
            page_number = row["page"]
            if type(page_number) is not int or not 1 <= page_number <= len(document.pages):
                raise ValueError("original equation paint page is outside native pages")
            page = document.pages[page_number - 1]
            if page.rotation != 0 or page.mediabox[:2] != (0, 0):
                blockers.append(f"{node.identity}: equation rotation/origin requires independent geometry")
                continue
            if (page.width, page.height) != (row["width_pt"], row["height_pt"]):
                findings.append({"code": "pdf.math.page.layout", "identity": node.identity})
                continue
            actual = []
            indices = []
            if page_number not in glyph_indexes:
                glyph_index: dict[tuple[Any, ...], list[tuple[int, dict[str, Any]]]] = {}
                for index, glyph in enumerate(page.chars):
                    if index % 1024 == 0 and time.monotonic() >= deadline:
                        raise TimeoutError("source-positioned mathematics exhausted its glyph-index budget")
                    key = (glyph["text"], _font(glyph), round(float(glyph["x0"]) * 10), round(float(glyph["top"]) * 10))
                    glyph_index.setdefault(key, []).append((index, glyph))
                glyph_indexes[page_number] = glyph_index
            for wanted in row["glyphs"]:
                if not str(wanted["text"]).strip():
                    continue
                xkey, ykey = round(float(wanted["x0"]) * 10), round(float(wanted["top"]) * 10)
                nearby = [
                    candidate
                    for dx in (-1, 0, 1)
                    for dy in (-1, 0, 1)
                    for candidate in glyph_indexes[page_number].get(
                        (wanted["text"], _font(wanted), xkey + dx, ykey + dy), []
                    )
                ]
                candidates = [
                    (index, glyph)
                    for index, glyph in nearby
                    if all(
                        abs(float(glyph[key]) - float(wanted[key])) <= 0.05
                        for key in ("x0", "x1", "top", "bottom", "size")
                    )
                ]
                if len(candidates) != 1 or (page_number, candidates[0][0]) in consumed:
                    findings.append({"code": "pdf.math.source.position", "identity": node.identity})
                    break
                index, glyph = candidates[0]
                consumed.add((page_number, index))
                actual.append(glyph)
                indices.append(index)
            if len(actual) != sum(bool(str(glyph["text"]).strip()) for glyph in row["glyphs"]):
                continue
            wanted = reference["glyphs"]
            if len(actual) != len(wanted) or [(glyph["text"], _font(glyph)) for glyph in actual] != [
                (glyph["text"], _font(glyph)) for glyph in wanted
            ]:
                findings.append({"code": "pdf.math.interpretation", "identity": node.identity})
                continue
            native_box = _box(actual)
            source_box = _box(wanted)
            scale = max(glyph["size"] for glyph in actual) / max(glyph["size"] for glyph in wanted)
            if abs(scale - 1) > 0.02:
                findings.append({"code": "pdf.math.font", "identity": node.identity})
            error = max(
                abs((glyph[key] - native_box[axis]) - (expected[key] - source_box[axis]) * scale)
                for glyph, expected in zip(actual, wanted, strict=True)
                for key, axis in (("x0", 0), ("x1", 0), ("top", 1), ("bottom", 1))
            )
            if error > 0.6:
                findings.append({"code": "pdf.math.geometry", "identity": node.identity})
            # The full source marks distinguish mathematical rules (fraction,
            # radicals, delimiters) from neighbouring text. Candidate vectors
            # must retain every original marked painted rule at its source position.
            native_vectors = [item for group in (page.lines, page.rects, page.curves) for item in group]
            for vector in row["vectors"]:
                keys = ("object_type", "linewidth", "fill", "stroke", "path", "non_stroking_color", "stroking_color")
                vector_candidates = [
                    item
                    for item in native_vectors
                    if all(item.get(key) == vector.get(key) for key in keys)
                    and all(abs(float(item[key]) - float(vector[key])) <= 0.05 for key in ("x0", "x1", "top", "bottom"))
                ]
                if len(vector_candidates) != 1:
                    findings.append({"code": "pdf.math.vector", "identity": node.identity})
            crop = list(map(float, page.cropbox))
            if (
                native_box[0] < crop[0] - 0.5
                or native_box[1] < crop[1] - 0.5
                or native_box[2] > crop[2] + 0.5
                or native_box[3] > crop[3] + 0.5
            ):
                findings.append({"code": "pdf.math.crop", "identity": node.identity})
                continue
            if not 1 <= reference["page"] <= len(interpreted_rasters):
                raise ValueError("independent equation reference lacks original page raster")
            with (
                Image.open(BytesIO(rasters[page_number - 1])) as pixels,
                Image.open(BytesIO(interpreted_rasters[reference["page"] - 1])) as source_pixels,
            ):
                if (
                    pixels.format != "PNG"
                    or source_pixels.format != "PNG"
                    or max(pixels.width * pixels.height, source_pixels.width * source_pixels.height) > 60_000_000
                    or abs(pixels.width - page.width * 150 / 72) > 2
                    or abs(pixels.height - page.height * 150 / 72) > 2
                ):
                    raise ValueError("positioned mathematics requires bounded original 150dpi PNGs")
                native_roi = cast(tuple[int, int, int, int], tuple(int(value * 150 / 72) for value in native_box))
                source_roi = cast(tuple[int, int, int, int], tuple(int(value * 150 / 72) for value in source_box))
                if (
                    native_roi[0] >= native_roi[2]
                    or native_roi[1] >= native_roi[3]
                    or source_roi[0] >= source_roi[2]
                    or source_roi[1] >= source_roi[3]
                ):
                    raise ValueError("positioned mathematics has no localized ink region")
                region = pixels.convert("L").crop(native_roi)
                expected_region = source_pixels.convert("L").crop(source_roi).resize(region.size)
                low, high = cast(tuple[int, int], region.getextrema())
                if high - low < 32:
                    findings.append({"code": "pdf.math.invisible", "identity": node.identity})
                errors = []
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        shifted = Image.new("L", expected_region.size, 255)
                        shifted.paste(expected_region, (dx, dy))
                        errors.append(ImageStat.Stat(ImageChops.difference(region, shifted)).mean[0])
                pixel_error = min(errors)
                if pixel_error > 12:
                    findings.append({"code": "pdf.math.pixels", "identity": node.identity})
            observations.append(
                {
                    "identity": node.identity,
                    "source": node.source,
                    "page": page_number,
                    "glyph_indices": indices,
                    "box_pt": native_box,
                    "geometry_error_pt": error,
                    "scale": scale,
                    "pixel_error": pixel_error,
                    "marked_vectors": len(row["vectors"]),
                }
            )
    return {
        "schema_version": SCHEMA,
        "source_ast_sha256": hashlib.sha256(ast_bytes).hexdigest(),
        "pdf_sha256": hashlib.sha256(pdf).hexdigest(),
        "source_tex_sha256": hashlib.sha256(source_tex).hexdigest(),
        "instrumented_pdf_sha256": hashlib.sha256(instrumented_pdf).hexdigest(),
        "interpreted_pdf_sha256": hashlib.sha256(interpreted_pdf).hexdigest(),
        "raster_sha256": [hashlib.sha256(raw).hexdigest() for raw in rasters],
        "interpreted_raster_sha256": [hashlib.sha256(raw).hexdigest() for raw in interpreted_rasters],
        "observations": observations,
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }
