"""Independent actual-PDF literal, table-cell and decoded-source figure witnesses.

This observer interprets original source text, grids and asset pixels directly.
Whole-reference equality remains separate and cannot replace an occurrence's
native semantic witness. Native math/citation/raw/cover/domain obligations are
reported explicitly until their independently replayed components are attached.
"""

from __future__ import annotations

import hashlib
import math
import time
from io import BytesIO
from typing import TYPE_CHECKING, Any, TypedDict, cast

from infrastructure.reporting.native_format_pdf_oracles import inspect_pdf_content
from infrastructure.reporting.native_format_pdf_source_decode_bounds import SourceImageDecodeBudget
from infrastructure.reporting.native_format_pdf_semantic_plan import PDFSemanticPlan
from infrastructure.reporting.native_format_pdf_source_layout import inspect_pdf_source_pagebreaks
from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage


class _NativeFigure(TypedDict):
    page: int
    box: list[float]
    image: PILImage
    sha256: str
    page_width: float
    page_height: float


SCHEMA = "template-native-pdf-independent-source-witness-v1"


def _budget(deadline: float) -> None:
    if not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("PDF source witness exhausted its original finite deadline")


def inspect_pdf_table_geometry(
    plan: PDFSemanticPlan,
    text: dict[str, Any],
    *,
    deadline: float,
    scientific_boxes: dict[str, tuple[int, list[float]]] | None = None,
) -> dict[str, Any]:
    """Interpret source row/column ownership using actual matched glyph boxes.

    Empty cells, spans and scientific-only cells require original structural
    position witnesses. They never disappear because visible neighbours match.
    Complete native page/reference layout remains an additional requirement.
    """
    matches = {row["block_id"]: row["word_indices"] for row in text["matches"]}
    words = {row["word_index"]: row for row in text["supported_words"]}
    observations = []
    findings = []
    blockers = []
    extra = scientific_boxes or {}
    for table in plan.tables:
        columns: dict[int, list[tuple[float, float]]] = {}
        previous: tuple[int, float] | None = None
        for row in table["rows"]:
            _budget(deadline)
            cells = []
            for cell in row["cells"]:
                if cell["row_span"] != 1 or cell["column_span"] != 1:
                    blockers.append(
                        f"{cell['identity']}: source table spans require independent native structural positions"
                    )
                independent = [extra[identity] for identity in cell["occurrence_ids"] if identity in extra]
                if not cell["text_ids"] and not independent:
                    blockers.append(
                        f"{cell['identity']}: empty/scientific-only source cell requires "
                        "independent native structural position"
                    )
                    continue
                if any(identity not in matches for identity in cell["text_ids"]):
                    findings.append({"code": "pdf.table.cell.missing", "identity": cell["identity"]})
                    continue
                indices = sorted({index for identity in cell["text_ids"] for index in matches[identity]})
                selected = [words[index] for index in indices]
                pages = {word["page"] for word in selected} | {page for page, _ in independent}
                if len(pages) != 1:
                    blockers.append(f"{cell['identity']}: source cell split across pages requires structural positions")
                    continue
                boxes = [word["box_pt"] for word in selected] + [box for _, box in independent]
                box = [
                    min(item[0] for item in boxes),
                    min(item[1] for item in boxes),
                    max(item[2] for item in boxes),
                    max(item[3] for item in boxes),
                ]
                cells.append(
                    {
                        "identity": cell["identity"],
                        "column": cell["column"],
                        "page": next(iter(pages)),
                        "box_pt": box,
                        "word_indices": indices,
                    }
                )
                columns.setdefault(cell["column"], []).append((box[0], box[2]))
            if not cells:
                continue
            pages = {cell["page"] for cell in cells}
            if len(pages) != 1:
                findings.append({"code": "pdf.table.row.page", "identity": table["identity"], "row": row["row"]})
                continue
            for left, right in zip(cells, cells[1:]):
                if left["box_pt"][2] >= right["box_pt"][0] - 0.5:
                    findings.append({"code": "pdf.table.columns.overlap", "identity": right["identity"]})
                if max(left["box_pt"][1], right["box_pt"][1]) >= min(left["box_pt"][3], right["box_pt"][3]):
                    findings.append({"code": "pdf.table.row.alignment", "identity": right["identity"]})
            position = (cells[0]["page"], min(cell["box_pt"][1] for cell in cells))
            if previous is not None and position <= previous:
                findings.append({"code": "pdf.table.rows.order", "identity": table["identity"], "row": row["row"]})
            previous = position
            observations.append(
                {"table_identity": table["identity"], "row": row["row"], "group": row["group"], "cells": cells}
            )
        for column in sorted(columns):
            if (
                column + 1 in columns
                and max(end for _, end in columns[column]) >= min(start for start, _ in columns[column + 1]) - 0.5
            ):
                findings.append({"code": "pdf.table.column.grid", "identity": table["identity"], "column": column})
    return {"rows": observations, "findings": findings, "blockers": blockers}


def inspect_pdf_source_figures(
    pdf: bytes,
    rasters: tuple[bytes, ...],
    plan: PDFSemanticPlan,
    assets: dict[str, tuple[str, bytes]],
    *,
    deadline: float,
) -> dict[str, Any]:
    """Bind source image identity to embedded pixels, native bounds and page ink.

    The caller admits exact original asset paths/bytes through SourceDATA and
    hydrated provenance. SVG/PDF/CMYK/alpha/ICC/animated assets retain blockers.
    A reference's equal image stream alone cannot satisfy decoded source pixels.
    """
    import pdfplumber
    from pdfminer.pdftypes import resolve1
    from pdfminer.psparser import PSLiteral
    from PIL import Image, ImageChops, ImageOps, ImageStat

    _budget(deadline)
    expected_rows = [row for row in plan.occurrences if row["kind"] == "Image"]
    source_decode_budget = SourceImageDecodeBudget(len(expected_rows))
    if set(assets) != {row["identity"] for row in expected_rows}:
        raise ValueError("source figure asset closure omitted or invented an occurrence")
    if sum(len(content) for _, content in assets.values()) > 64 * 1024 * 1024:
        raise ValueError("source figure asset closure exceeds its finite byte budget")
    expected: dict[str, tuple[str, bytes, PILImage]] = {}
    blockers = []
    findings = []
    observations = []
    for row in expected_rows:
        _budget(deadline)
        path, content = assets[row["identity"]]
        try:
            with Image.open(BytesIO(content)) as image:
                source_decode_budget.admit_header(image.width, image.height)
                if (
                    image.format not in {"PNG", "JPEG", "WEBP"}
                    or getattr(image, "n_frames", 1) != 1
                    or image.mode == "CMYK"
                    or image.info.get("icc_profile")
                ):
                    blockers.append(
                        f"{row['identity']}: source vector/animated/CMYK/ICC figure requires "
                        "independent decoder projection"
                    )
                    continue
                source = ImageOps.exif_transpose(image).convert("RGBA")
                if source.getchannel("A").getextrema() != (255, 255):
                    blockers.append(
                        f"{row['identity']}: source figure alpha requires independently interpreted compositing"
                    )
                    continue
                expected[row["identity"]] = (path, content, source.convert("RGB").copy())
        except (OSError, SyntaxError):
            blockers.append(f"{row['identity']}: source figure requires a real supported independent decoder")
    native: list[_NativeFigure] = []
    with pdfplumber.open(BytesIO(pdf)) as document:
        if not document.pages or len(document.pages) > 500 or len(document.pages) != len(rasters):
            raise ValueError("source figure observer requires every actual native page/raster")
        decoded_pixels = 0
        for page_number, page in enumerate(document.pages):
            _budget(deadline)
            if page.rotation or page.mediabox[:2] != (0, 0):
                blockers.append(f"page {page_number + 1}: source figure rotation/origin projection unsupported")
            for native_image in page.images:
                _budget(deadline)
                stream = native_image["stream"]
                attrs = resolve1(stream.attrs)
                width, height = attrs.get("Width"), attrs.get("Height")
                if (
                    type(width) is not int
                    or type(height) is not int
                    or width <= 0
                    or height <= 0
                    or width * height > 60_000_000
                ):
                    raise ValueError("embedded source image dimensions exceed their finite budget")
                decoded_pixels += width * height
                if decoded_pixels > 120_000_000:
                    raise ValueError("complete embedded image decode exceeds its aggregate pixel budget")
                colorspace = resolve1(attrs.get("ColorSpace"))
                if attrs.get("SMask") or attrs.get("Mask") or attrs.get("Decode") is not None:
                    blockers.append(
                        f"page {page_number + 1}: native masked/transformed figure requires independent compositing"
                    )
                    continue
                if (
                    not isinstance(colorspace, PSLiteral)
                    or colorspace.name not in {"DeviceRGB", "DeviceGray"}
                    or attrs.get("BitsPerComponent") != 8
                ):
                    blockers.append(
                        f"page {page_number + 1}: native figure colorspace/depth requires "
                        "independent decoder projection"
                    )
                    continue
                decoded = stream.get_data()
                if len(decoded) > 180_000_000:
                    raise ValueError("embedded native image decode exceeds its finite byte budget")
                if decoded.startswith(b"\xff\xd8"):
                    with Image.open(BytesIO(decoded)) as embedded:
                        embedded.load()
                        if embedded.size != (width, height):
                            raise ValueError("native JPEG decoded dimensions differ from original image dictionary")
                        actual = embedded.convert("RGB").copy()
                else:
                    mode = "RGB" if colorspace.name == "DeviceRGB" else "L"
                    channels = 3 if mode == "RGB" else 1
                    if len(decoded) != width * height * channels:
                        blockers.append(
                            f"page {page_number + 1}: native figure decoded stride requires independent projection"
                        )
                        continue
                    actual = Image.frombytes(mode, (width, height), decoded).convert("RGB")
                box = [float(native_image[key]) for key in ("x0", "top", "x1", "bottom")]
                if not all(math.isfinite(value) for value in box) or box[0] >= box[2] or box[1] >= box[3]:
                    raise ValueError("actual native source image omitted finite positive bounds")
                native.append(
                    {
                        "page": page_number,
                        "box": box,
                        "image": actual,
                        "sha256": hashlib.sha256(actual.tobytes()).hexdigest(),
                        "page_width": page.width,
                        "page_height": page.height,
                    }
                )
                if len(native) > 20_000:
                    raise ValueError("native source figure occurrence budget exceeded")
    used = set()
    for identity, (path, source_bytes, source) in expected.items():
        _budget(deadline)
        digest = hashlib.sha256(source.tobytes()).hexdigest()
        candidates = [
            (index, item)
            for index, item in enumerate(native)
            if index not in used and item["image"].size == source.size and item["sha256"] == digest
        ]
        if len(candidates) != 1:
            findings.append({"code": "pdf.figure.source", "identity": identity, "candidates": len(candidates)})
            continue
        index, item = candidates[0]
        used.add(index)
        box = item["box"]
        if box[0] < 0 or box[1] < 0 or box[2] > item["page_width"] or box[3] > item["page_height"]:
            findings.append({"code": "pdf.figure.crop", "identity": identity})
            continue
        if abs((box[2] - box[0]) / (box[3] - box[1]) - source.width / source.height) > 0.02:
            findings.append({"code": "pdf.figure.distortion", "identity": identity})
        with Image.open(BytesIO(rasters[item["page"]])) as pixels:
            if (
                pixels.format != "PNG"
                or pixels.width * pixels.height > 60_000_000
                or abs(pixels.width - item["page_width"] * 150 / 72) > 2
                or abs(pixels.height - item["page_height"] * 150 / 72) > 2
            ):
                raise ValueError("figure native page raster lacks bounded exact 150dpi geometry")
            roi = tuple((math.floor if axis < 2 else math.ceil)(value * 150 / 72) for axis, value in enumerate(box))
            region = pixels.convert("RGB").crop(cast(tuple[int, int, int, int], roi))
            projected = source.resize(region.size, Image.Resampling.LANCZOS)
            error = sum(ImageStat.Stat(ImageChops.difference(projected, region)).mean) / 3
            if error > 24:
                findings.append({"code": "pdf.figure.visual", "identity": identity})
        observations.append(
            {
                "identity": identity,
                "source": {"path": path, "sha256": hashlib.sha256(source_bytes).hexdigest()},
                "decoded_source_sha256": digest,
                "decoded_native_sha256": item["sha256"],
                "page": item["page"] + 1,
                "box_pt": box,
                "region_mean_error": error,
            }
        )
    return {"figures": observations, "findings": findings, "blockers": blockers}


def inspect_pdf_source_witness(
    pdf: bytes,
    rasters: tuple[bytes, ...],
    plan: PDFSemanticPlan,
    *,
    assets: dict[str, tuple[str, bytes]],
    deadline: float,
    citation_reference: dict[str, Any] | None = None,
    mathematical_inputs: dict[str, Any] | None = None,
    full_source_reference: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Observe source semantics directly; preserve every unobserved source form.

    The outer reader must admit full_source_reference's genuine original source,
    compiler, FLS, hydration and SDK custody before passing its bytes here.
    A candidate-derived PDF/AUX or asserted pass bit cannot supply that closure.
    """
    _budget(deadline)
    preflight_pdf_streams(pdf, deadline=deadline, max_objects=4_000_000)
    literal = inspect_pdf_content(pdf, rasters, plan.text_contract(), deadline=deadline)
    note = inspect_pdf_content(pdf, rasters, plan.text_contract(notes=True), deadline=deadline) if plan.notes else None
    figures = inspect_pdf_source_figures(pdf, rasters, plan, assets, deadline=deadline)
    reference_literal = reference_figures = whole_page_parity = None
    if full_source_reference is not None:
        from infrastructure.reporting.native_format_pdf_reference_parity import inspect_pdf_reference_parity

        if (
            set(full_source_reference) != {"pdf", "rasters", "source_plan_digest"}
            or full_source_reference["source_plan_digest"] != plan.digest
        ):
            raise ValueError("whole-source PDF reference differs from the independently rebuilt source plan")
        reference_pdf, reference_rasters = full_source_reference["pdf"], full_source_reference["rasters"]
        reference_literal = inspect_pdf_content(
            reference_pdf, reference_rasters, plan.text_contract(), deadline=deadline
        )
        reference_figures = inspect_pdf_source_figures(
            reference_pdf, reference_rasters, plan, assets, deadline=deadline
        )
        whole_page_parity = inspect_pdf_reference_parity(
            pdf, reference_pdf, rasters, reference_rasters, deadline=deadline
        )
    from infrastructure.reporting.native_format_pdf_figure_positions import bind_pdf_figure_positions

    from infrastructure.reporting.native_pdf_literal_roles import inspect_pdf_literal_roles

    literal_roles = inspect_pdf_literal_roles(plan, literal, reference_literal, whole_page_parity, deadline=deadline)
    pagebreaks = inspect_pdf_source_pagebreaks(plan, literal, deadline=deadline)
    citations = None
    equations = None
    if citation_reference is not None:
        from infrastructure.reporting.native_pdf_citation_replay import inspect_natbib_citations

        if citation_reference["inputs"]["ast_sha256"] != plan.source_ast_sha256:
            raise ValueError("PDF citation reference differs from original source AST")
        citations = inspect_natbib_citations(pdf, rasters, citation_reference, deadline=deadline)
    if mathematical_inputs is not None:
        from infrastructure.reporting.native_format_pdf_positioned_math import inspect_pdf_positioned_math

        if (
            set(mathematical_inputs)
            != {"ast_bytes", "source_tex", "instrumented_pdf", "interpreted_pdf", "interpreted_rasters"}
            or hashlib.sha256(mathematical_inputs["ast_bytes"]).hexdigest() != plan.source_ast_sha256
        ):
            raise ValueError("PDF mathematical inputs differ from original source AST")
        equations = inspect_pdf_positioned_math(pdf, rasters, deadline=deadline, **mathematical_inputs)
    figure_positions = bind_pdf_figure_positions(
        plan,
        literal,
        figures,
        reference_literal=reference_literal,
        reference_figures=reference_figures,
        whole_page_parity=whole_page_parity,
        deadline=deadline,
        equations=equations,
    )
    scientific_boxes = {row["identity"]: (row["page"], row["box_pt"]) for row in figures["figures"] if row["covered"]}
    if equations is not None:
        scientific_boxes.update({row["identity"]: (row["page"], row["box_pt"]) for row in equations["observations"]})
    tables = inspect_pdf_table_geometry(plan, literal, deadline=deadline, scientific_boxes=scientific_boxes)
    blockers = [*plan.blockers, *literal["blockers"], *tables["blockers"], *figures["blockers"]]
    findings = [*literal["findings"], *tables["findings"], *figures["findings"]]
    if note is not None:
        blockers.extend(note["blockers"])
        findings.extend(note["findings"])
    for component in (
        citations,
        equations,
        pagebreaks,
        figure_positions,
        reference_literal,
        reference_figures,
        literal_roles,
    ):
        if component is not None:
            blockers.extend(component["blockers"])
            findings.extend(component["findings"])
    if whole_page_parity is not None:
        findings.extend(whole_page_parity["findings"])
    mathematically_observed = {row["identity"] for row in equations["observations"]} if equations else set()
    literal_roles_observed = {row["identity"] for row in literal_roles["observations"]}
    pagebreaks_observed = {row["identity"] for row in pagebreaks["observations"]}
    for row in plan.occurrences:
        kind = row["kind"]
        if kind in {"Code", "CodeBlock", "Link"} and row["identity"] in literal_roles_observed:
            continue
        if kind == "Math" and row["identity"] in mathematically_observed:
            continue
        if kind == "Cite" and "citation_reference_id" in row and citations is not None:
            continue
        if kind in {"RawBlock", "RawInline"} and row["identity"] in pagebreaks_observed:
            continue
        if kind in {"RawBlock", "RawInline"} and "raw_citation_reference_ids" in row and citations is not None:
            # Exact supported raw natbib source commands have a genuine native
            # label/glyph/ink witness, surrounding source text and full layout.
            # Residual/raw macro/state nodes never receive this ledger entry.
            if whole_page_parity is not None:
                continue
            blockers.append(f"{row['identity']}: supported raw natbib requires every-page original source parity")
            continue
        if kind in {
            "Math",
            "Cite",
            "RawInline",
            "RawBlock",
            "Note",
            "Link",
            "Superscript",
            "Subscript",
            "Code",
            "CodeBlock",
            "HorizontalRule",
        }:
            blockers.append(
                f"{row['identity']}: source {kind} requires independently replayed native semantic/layout witness"
            )
    _budget(deadline)
    return {
        "schema_version": SCHEMA,
        "source_plan_digest": plan.digest,
        "pdf_sha256": hashlib.sha256(pdf).hexdigest(),
        "raster_sha256": [hashlib.sha256(raw).hexdigest() for raw in rasters],
        "literal": literal,
        "literal_roles": literal_roles,
        "notes": note,
        "tables": tables,
        "figures": figures,
        "figure_positions": figure_positions,
        "source_reference_literal": reference_literal,
        "source_reference_figures": reference_figures,
        "whole_page_parity": whole_page_parity,
        "citations": citations,
        "equations": equations,
        "pagebreaks": pagebreaks,
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }
