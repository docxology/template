"""Actual every-occurrence slide ink and every-page native layout observations."""

from __future__ import annotations

import hashlib
import math
import time
from io import BytesIO
from typing import Any

from infrastructure.reporting.native_format_content_contracts import text_tokens
from infrastructure.reporting.native_format_pdf_reference_parity import inspect_pdf_reference_parity
from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams
from infrastructure.reporting.native_slide_source import SlideSourceContract


def _subsequence(wanted: tuple[str, ...], actual: tuple[str, ...]) -> bool:
    index = 0
    for token in actual:
        if index < len(wanted) and wanted[index] == token:
            index += 1
    return index == len(wanted)


def inspect_slide_source_paint(
    marked_pdf: bytes,
    rasters: tuple[bytes, ...],
    contract: SlideSourceContract,
    bindings: tuple[dict[str, Any], ...],
    *,
    deadline: float,
    source_images: dict[str, bytes] | None = None,
) -> dict[str, Any]:
    """Every marker needs exact source text or native shape/image paint and ink.

    A source/reference page equality alone cannot discharge this function.
    Tags originate only in the independently rebuilt marked source. All original
    source markers, native glyphs, image draws, clipping and page rasters count.
    """
    import pdfplumber
    from PIL import Image, ImageStat
    from pypdf import PdfReader

    preflight_pdf_streams(marked_pdf, deadline=deadline, max_objects=4_000_000)
    if len(marked_pdf) + sum(map(len, rasters)) > 256 * 1024 * 1024:
        raise ValueError("slide source paint exceeds original finite input bytes")
    by_mcid = {row["mcid"]: row for row in bindings}
    if len(by_mcid) != len(bindings) or len(bindings) > 10_000:
        raise ValueError("slide source paint marker inventory is ambiguous or unbounded")
    expected = {row.identity: row for row in contract.occurrences}
    if any(row["identity"] not in expected or row["ordinal"] != row["mcid"] for row in bindings):
        raise ValueError("slide source paint marker differs from original source")
    findings: list[dict[str, Any]] = []
    blockers = list(contract.blockers)
    observations = []
    native_images: dict[int, dict[str, tuple[tuple[int, int], str]]] = {}
    pdf_reader = PdfReader(BytesIO(marked_pdf), strict=True)
    for ordinal, pdf_page in enumerate(pdf_reader.pages, 1):
        records = {}
        for native_picture in pdf_page.images:
            if native_picture.image is None or native_picture.image.width * native_picture.image.height > 20_000_000:
                raise ValueError("native source image exceeds original full-pixel bound")
            native_pixels = native_picture.image.convert("RGBA")
            records[native_picture.name.rsplit(".", 1)[0]] = (
                native_pixels.size,
                hashlib.sha256(native_pixels.tobytes()).hexdigest(),
            )
        native_images[ordinal] = records
    totals: dict[int, dict[str, Any]] = {}
    object_count = 0
    with pdfplumber.open(BytesIO(marked_pdf)) as paint_document:
        if not paint_document.pages or len(paint_document.pages) > 500 or len(paint_document.pages) != len(rasters):
            raise ValueError("slide source paint requires every original page raster")
        for ordinal, (page, data) in enumerate(zip(paint_document.pages, rasters, strict=True), 1):
            if time.monotonic() >= deadline:
                raise TimeoutError("slide source paint exhausted original deadline")
            with Image.open(BytesIO(data)) as raster:
                if raster.format != "PNG" or raster.width * raster.height > 60_000_000:
                    raise ValueError("slide source paint needs bounded original PNG pixels")
                if abs(raster.width - page.width * 150 / 72) > 2 or abs(raster.height - page.height * 150 / 72) > 2:
                    raise ValueError("slide source paint raster has a different native page/DPI")
                raster_pixels = raster.convert("RGB")
                local: dict[int, dict[str, list[Any]]] = {}
                for kind, objects in (
                    ("glyph", page.chars),
                    ("vector", [*page.lines, *page.rects, *page.curves]),
                    ("image", page.images),
                ):
                    object_count += len(objects)
                    if object_count > 4_000_000:
                        raise ValueError("slide source paint exceeded its original native object bound")
                    for obj in objects:
                        box = tuple(float(obj[k]) for k in ("x0", "top", "x1", "bottom"))
                        if not all(math.isfinite(v) for v in box):
                            raise ValueError("native projected object has nonfinite geometry")
                        if kind in {"glyph", "image"} and (
                            box[0] < -0.25
                            or box[1] < -0.25
                            or box[2] > page.width + 0.25
                            or box[3] > page.height + 0.25
                        ):
                            findings.append(
                                {"code": "slides.layout.crop", "page": ordinal, "kind": kind, "box_pt": list(box)}
                            )
                        mcid = obj.get("mcid")
                        if mcid is None:
                            # All native glyphs still undergo clipping, even
                            # page-number/navigation/theme-generated content.
                            continue
                        if type(mcid) is not int or mcid not in by_mcid or obj.get("tag") != "Span":
                            raise ValueError("native slide source contains undeclared or non-source marker paint")
                        group = local.setdefault(mcid, {"glyph": [], "vector": [], "image": []})
                        group[kind].append(obj)
                page_rows = []
                for mcid, group in sorted(local.items()):
                    binding = by_mcid[mcid]
                    occurrence = expected[binding["identity"]]
                    aggregate = totals.setdefault(
                        mcid, {"tokens": [], "glyphs": 0, "vectors": 0, "images": 0, "pages": []}
                    )
                    aggregate["tokens"].extend(text_tokens("".join(str(g.get("text", "")) for g in group["glyph"])))
                    for kind, plural in (("glyph", "glyphs"), ("vector", "vectors"), ("image", "images")):
                        aggregate[plural] += len(group[kind])
                    aggregate["pages"].append(ordinal)
                    for glyph in group["glyph"]:
                        if float(glyph["size"]) + 0.05 < occurrence.minimum_font_pt * (
                            0.3 if occurrence.kind == "math" else 1.0
                        ):
                            findings.append(
                                {
                                    "code": "slides.typography.font",
                                    "identity": occurrence.identity,
                                    "page": ordinal,
                                    "observed_pt": glyph["size"],
                                    "minimum_pt": occurrence.minimum_font_pt,
                                }
                            )
                    if (
                        occurrence.kind == "math"
                        and group["glyph"]
                        and max(float(g["size"]) for g in group["glyph"]) + 0.05 < occurrence.minimum_font_pt * 0.6
                    ):
                        findings.append(
                            {
                                "code": "slides.typography.font",
                                "identity": occurrence.identity,
                                "page": ordinal,
                                "minimum_base_math_pt": occurrence.minimum_font_pt * 0.6,
                            }
                        )
                    objects = [*group["glyph"], *group["vector"], *group["image"]]
                    if objects:
                        bounds = (
                            min(float(x["x0"]) for x in objects),
                            min(float(x["top"]) for x in objects),
                            max(float(x["x1"]) for x in objects),
                            max(float(x["bottom"]) for x in objects),
                        )
                        crop = raster_pixels.crop(
                            (
                                max(0, int(bounds[0] * 150 / 72) - 1),
                                max(0, int(bounds[1] * 150 / 72) - 1),
                                min(raster_pixels.width, math.ceil(bounds[2] * 150 / 72) + 1),
                                min(raster_pixels.height, math.ceil(bounds[3] * 150 / 72) + 1),
                            )
                        )
                        if not crop.width or not crop.height or max(ImageStat.Stat(crop).var) < 1.0:
                            findings.append(
                                {"code": "slides.visual.invisible", "identity": occurrence.identity, "page": ordinal}
                            )
                    if occurrence.kind == "image" and source_images and occurrence.target in source_images:
                        with Image.open(BytesIO(source_images[occurrence.target])) as source:
                            if source.width * source.height > 20_000_000:
                                raise ValueError("source image exceeds original full-pixel bound")
                            pixels_source = source.convert("RGBA")
                            source_identity = (pixels_source.size, hashlib.sha256(pixels_source.tobytes()).hexdigest())
                        if (
                            len(group["image"]) != 1
                            or native_images[ordinal].get(str(group["image"][0]["name"])) != source_identity
                        ):
                            findings.append(
                                {"code": "slides.source.image.pixels", "identity": occurrence.identity, "page": ordinal}
                            )
                    page_rows.append(
                        {
                            "identity": occurrence.identity,
                            "mcid": mcid,
                            "glyph_count": len(group["glyph"]),
                            "vector_count": len(group["vector"]),
                            "image_count": len(group["image"]),
                        }
                    )
                observations.append(
                    {
                        "page": ordinal,
                        "size_pt": [page.width, page.height],
                        "raster_sha256": hashlib.sha256(data).hexdigest(),
                        "source_paint": page_rows,
                    }
                )
    for mcid, binding in by_mcid.items():
        occurrence = expected[binding["identity"]]
        actual = totals.get(mcid)
        if actual is None:
            findings.append({"code": "slides.source.paint.missing", "identity": occurrence.identity})
            continue
        if occurrence.kind in {"text", "code", "reference"} and not _subsequence(
            occurrence.tokens, tuple(actual["tokens"])
        ):
            findings.append({"code": "slides.source.text", "identity": occurrence.identity})
        if occurrence.kind == "image":
            if actual["images"] != 1:
                findings.append({"code": "slides.source.image.draw", "identity": occurrence.identity})
            if source_images is None or occurrence.target not in source_images:
                blockers.append(f"{occurrence.identity}: exact original source image pixel witness required")
    with pdfplumber.open(BytesIO(marked_pdf)) as link_document:
        links = {str(item.get("uri", "")) for page in link_document.pages for item in page.hyperlinks}
    for occurrence in contract.occurrences:
        if (
            occurrence.kind == "link"
            and occurrence.target.startswith(("https://", "http://"))
            and occurrence.target not in links
        ):
            findings.append({"code": "slides.source.link.target", "identity": occurrence.identity})
    return {
        "schema_version": "template-native-slide-source-paint-v1",
        "contract": contract.record(),
        "pages": observations,
        "occurrences": [{"identity": by_mcid[k]["identity"], **v} for k, v in sorted(totals.items())],
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }


def inspect_manuscript_slide_reference(
    candidate_pdf: bytes,
    candidate_rasters: tuple[bytes, ...],
    reference_pdf: bytes,
    reference_rasters: tuple[bytes, ...],
    marked_pdf: bytes,
    marked_rasters: tuple[bytes, ...],
    contract: SlideSourceContract,
    bindings: tuple[dict[str, Any], ...],
    *,
    deadline: float,
    source_images: dict[str, bytes] | None = None,
) -> dict[str, Any]:
    """Conjunctive complete source paint, instrumentation and candidate acceptance."""
    from infrastructure.reporting.native_office_reference_visual import inspect_office_reference_projection

    source = inspect_slide_source_paint(
        marked_pdf, marked_rasters, contract, bindings, deadline=deadline, source_images=source_images
    )
    # MCID tags have no rendered identity. The independent parity oracle keeps
    # every glyph/vector and actual page pixels to prove zero-glyph marks did
    # not change the source reference projection.
    noninterference = inspect_pdf_reference_parity(
        marked_pdf, reference_pdf, marked_rasters, reference_rasters, deadline=deadline
    )
    native = inspect_office_reference_projection(
        reference_pdf, reference_rasters, candidate_pdf, candidate_rasters, deadline=deadline
    )
    findings = [*source["findings"], *noninterference["findings"], *native["findings"]]
    blockers = list(source["blockers"])
    return {
        "schema_version": "template-native-manuscript-slide-acceptance-v1",
        "source_paint": source,
        "instrumentation_noninterference": noninterference,
        "native_parity": native,
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }
