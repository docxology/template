"""Actual PDF text, glyph geometry and localized raster observations.

The supported claim is ordered text presence and bounded visibility of its word
regions. Mathematical projection, full layout and domain visual fidelity remain
separate blocked obligations.
"""

from __future__ import annotations

import hashlib
import math
import time
from importlib.metadata import version
from io import BytesIO
from typing import Any, cast

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_content_contracts import (
    NativeContentContract,
    content_contract_from_bytes,
    text_tokens,
)

PDF_ORACLE_SCHEMA = "template-native-pdf-content-observation-v1"
PDF_CONTROL_SCHEMA = "template-native-pdf-valid-control-v1"
PDF_POLICY: dict[str, Any] = {
    "schema_version": PDF_ORACLE_SCHEMA,
    "dpi": 150,
    "min_supported_font_pt": 9.0,
    "crop_tolerance_pt": 0.5,
    "min_word_luminance_range": 32,
    "min_word_ink_fraction": 0.005,
    "max_pages": 500,
    "max_words": 250_000,
    "max_chars": 2_000_000,
    "max_page_pixels": 60_000_000,
    "max_raster_bytes": 256 * 1024 * 1024,
    "assurance": "ordered supported text presence; all extracted word glyph bounds and localized ink only",
}
CONTROL_SOURCE = b"# Invented public measurement\n\nMeasured offset -3.25 mV.\n"
PDF_CONTROL_CODES: dict[str, str | None] = {
    "baseline": None,
    "changed-number": "pdf.content.missing",
    "clipped-text": "pdf.layout.crop",
    "tiny-text": "pdf.layout.font",
    "opaque-overlay": "pdf.visual.invisible",
}


def _budget(deadline: float) -> None:
    if type(deadline) not in {int, float} or not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise TimeoutError("PDF content/geometry observer exhausted its finite deadline")


def _finite_box(value: dict[str, Any]) -> tuple[float, float, float, float]:
    box = tuple(float(value[key]) for key in ("x0", "top", "x1", "bottom"))
    if not all(math.isfinite(number) for number in box) or box[0] >= box[2] or box[1] >= box[3]:
        raise ValueError("actual PDF glyph/word geometry is not finite and positive")
    return box  # type: ignore[return-value]


def _span(tokens: tuple[str, ...], expected: tuple[str, ...], start: int, deadline: float) -> int | None:
    if not expected:
        raise ValueError("native source block has no tokens")
    for index in range(start, len(tokens) - len(expected) + 1):
        if index % 1024 == 0:
            _budget(deadline)
        if tokens[index : index + len(expected)] == expected:
            return index
    return None


def inspect_pdf_content(
    pdf_bytes: bytes, raster_bytes: tuple[bytes, ...], contract: NativeContentContract, *, deadline: float
) -> dict[str, Any]:
    """Observe original parsed glyphs and actual admitted 150-dpi page pixels.

    Parser/tool exceptions are failures of the observer, never scientific or
    visual negative-control success. Source and policy limits remain explicit.
    """
    import pdfplumber
    from PIL import Image

    _budget(deadline)
    if sum(len(item) for item in raster_bytes) > PDF_POLICY["max_raster_bytes"]:
        raise ValueError("PDF localized observer exceeds its raster-byte budget")
    words: list[dict[str, Any]] = []
    page_rows: list[dict[str, Any]] = []
    blockers = list(contract.blockers)
    chars_total = 0
    with pdfplumber.open(BytesIO(pdf_bytes)) as document:
        if (
            not document.pages
            or len(document.pages) > PDF_POLICY["max_pages"]
            or len(raster_bytes) != len(document.pages)
        ):
            raise ValueError("PDF content observer requires a bounded complete page/raster set")
        for page_number, page in enumerate(document.pages, 1):
            _budget(deadline)
            chars_total += len(page.chars)
            if chars_total > PDF_POLICY["max_chars"]:
                raise ValueError("PDF content observer exceeds its glyph budget")
            media = tuple(float(item) for item in page.mediabox)
            crop = tuple(float(item) for item in page.cropbox)
            if any(not math.isfinite(item) for item in (*media, *crop)):
                raise ValueError("PDF page/crop geometry is not finite")
            supported_geometry = page.rotation == 0 and media[:2] == (0.0, 0.0)
            if not supported_geometry:
                blockers.append(f"page {page_number}: rotated/nonzero-origin geometry projection unsupported")
            extracted = page.extract_words(use_text_flow=True, expand_ligatures=False, return_chars=True)
            for word in extracted:
                box = _finite_box(word)
                glyphs = word.get("chars")
                if not isinstance(glyphs, list) or not glyphs:
                    raise ValueError("PDF word observer omitted actual glyph identities")
                sizes = [float(glyph["size"]) for glyph in glyphs]
                if not all(math.isfinite(size) and size > 0 for size in sizes):
                    raise ValueError("PDF glyph font sizes are invalid")
                words.append(
                    {
                        "text": word["text"],
                        "tokens": text_tokens(word["text"]),
                        "page": page_number,
                        "box": box,
                        "glyph_boxes": tuple(_finite_box(glyph) for glyph in glyphs),
                        "min_font_pt": min(sizes),
                        "fonts": sorted({str(glyph["fontname"]) for glyph in glyphs}),
                        "geometry_supported": supported_geometry,
                    }
                )
                if len(words) > PDF_POLICY["max_words"]:
                    raise ValueError("PDF content observer exceeds its word budget")
            page_rows.append(
                {
                    "page": page_number,
                    "media_box_pt": list(media),
                    "crop_box_pt": list(crop),
                    "rotation": page.rotation,
                    "glyphs": len(page.chars),
                }
            )
    flat: list[str] = []
    owners: list[int] = []
    for word_index, word in enumerate(words):
        flat.extend(word["tokens"])
        owners.extend([word_index] * len(word["tokens"]))
    tokens = tuple(flat)
    findings: list[dict[str, Any]] = []
    matches: list[dict[str, Any]] = []
    required_words: set[int] = set()
    cursor = 0
    for block in contract.blocks:
        _budget(deadline)
        index = _span(tokens, block.tokens, cursor, deadline)
        if index is None:
            earlier = _span(tokens, block.tokens, 0, deadline)
            findings.append(
                {"code": "pdf.content.order" if earlier is not None else "pdf.content.missing", "block_id": block.id}
            )
            continue
        end = index + len(block.tokens)
        selected = sorted(set(owners[index:end]))
        required_words.update(selected)
        matches.append({"block_id": block.id, "token_span": [index, end], "word_indices": selected})
        cursor = end
    observed_words: list[dict[str, Any]] = []
    for page_number, raw_image in enumerate(raster_bytes, 1):
        _budget(deadline)
        page_row = page_rows[page_number - 1]
        with Image.open(BytesIO(raw_image)) as image:
            if image.format != "PNG" or image.width * image.height > PDF_POLICY["max_page_pixels"]:
                raise ValueError("PDF localized observer requires bounded actual PNG pixels")
            image.load()
            gray = image.convert("L")
            media = page_row["media_box_pt"]
            if (
                abs(image.width - (media[2] - media[0]) * 150 / 72) > 2
                or abs(image.height - (media[3] - media[1]) * 150 / 72) > 2
            ):
                raise ValueError("PDF localized pixels differ from admitted 150-dpi page geometry")
            for index in range(len(words)):
                word = words[index]
                if word["page"] != page_number:
                    continue
                _budget(deadline)
                row = {
                    "word_index": index,
                    "page": page_number,
                    "box_pt": list(word["box"]),
                    "min_font_pt": word["min_font_pt"],
                    "fonts": word["fonts"],
                }
                if index in required_words and word["min_font_pt"] < PDF_POLICY["min_supported_font_pt"]:
                    findings.append({"code": "pdf.layout.font", "word_index": index})
                if word["geometry_supported"]:
                    crop = page_row["crop_box_pt"]
                    tolerance = PDF_POLICY["crop_tolerance_pt"]
                    if any(
                        box[0] < crop[0] - tolerance
                        or box[1] < crop[1] - tolerance
                        or box[2] > crop[2] + tolerance
                        or box[3] > crop[3] + tolerance
                        for box in word["glyph_boxes"]
                    ):
                        findings.append({"code": "pdf.layout.crop", "word_index": index})
                    else:
                        x0, top, x1, bottom = word["box"]
                        pixels = (
                            max(0, math.floor(x0 * 150 / 72)),
                            max(0, math.floor(top * 150 / 72)),
                            min(image.width, math.ceil(x1 * 150 / 72)),
                            min(image.height, math.ceil(bottom * 150 / 72)),
                        )
                        if pixels[0] >= pixels[2] or pixels[1] >= pixels[3]:
                            raise ValueError("PDF supported word has no actual raster region")
                        region = gray.crop(pixels)
                        low, high = cast(tuple[int, int], region.getextrema())
                        histogram = region.histogram()
                        ink = sum(histogram[: max(0, high - PDF_POLICY["min_word_luminance_range"] + 1)]) / (
                            region.width * region.height
                        )
                        row.update(
                            {"roi_px": list(pixels), "luminance_range": high - low, "ink_fraction": round(ink, 8)}
                        )
                        if (
                            high - low < PDF_POLICY["min_word_luminance_range"]
                            or ink < PDF_POLICY["min_word_ink_fraction"]
                        ):
                            findings.append({"code": "pdf.visual.invisible", "word_index": index})
                observed_words.append(row)
    _budget(deadline)
    return {
        "schema_version": PDF_ORACLE_SCHEMA,
        "pdf_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        "raster_sha256": [hashlib.sha256(item).hexdigest() for item in raster_bytes],
        "contract_digest": contract.digest,
        "policy_digest": canonical_digest(PDF_POLICY),
        "observer_versions": {name: version(name) for name in ("pdfplumber", "pdfminer.six", "Pillow")},
        "pages": page_rows,
        "word_count": len(words),
        "token_count": len(tokens),
        "matches": matches,
        "supported_words": observed_words,
        "observed_glyph_words": len(observed_words),
        "source_required_words": len(required_words),
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }


def pdf_control_contract() -> NativeContentContract:
    return content_contract_from_bytes("invented-control:pdf", (("invented-public-control.md", CONTROL_SOURCE),))


def pdf_control_bytes(name: str) -> bytes:
    """Fixed PDF objects and drawing bytes; no ambient clock or epoch metadata."""
    from pypdf import PdfWriter
    from pypdf.generic import ContentStream, DictionaryObject, NameObject

    if name not in PDF_CONTROL_CODES:
        raise ValueError("unknown actual valid-PDF control")
    writer = PdfWriter()
    writer.metadata = None
    page = writer.add_blank_page(width=288, height=216)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
            NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
    )
    font_size = 5 if name == "tiny-text" else 12
    offset = 220 if name == "clipped-text" else 24
    measurement = "-8.25" if name == "changed-number" else "-3.25"
    # Standard Helvetica glyphs, PDF point coordinates and ordinary fill text.
    # The overpaint follows the actual text, leaving parseable hidden glyphs.
    drawing = (
        "0 g\n"
        "BT /F1 12 Tf 1 0 0 1 24 180 Tm (Invented public measurement) Tj ET\n"
        f"BT /F1 {font_size} Tf 1 0 0 1 {offset} 144 Tm (Measured offset {measurement} mV.) Tj ET\n"
    )
    if name == "opaque-overlay":
        drawing += "q 1 1 1 rg 20 135 240 24 re f Q\n"
    content = ContentStream(None, writer)
    content.set_data(drawing.encode("ascii"))
    page.replace_contents(content)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def require_pdf_control_result(name: str, observation: dict[str, Any]) -> int:
    """An exact semantic/geometry/pixel refusal cannot be replaced by setup errors."""
    if name not in PDF_CONTROL_CODES or observation.get("blockers") != []:
        raise ValueError("actual valid-PDF control has unsupported or unknown obligations")
    codes = {item["code"] for item in observation["findings"]}
    expected = PDF_CONTROL_CODES[name]
    if codes != ({expected} if expected else set()) or observation.get("status") != ("fail" if expected else "pass"):
        raise ValueError(f"actual valid-PDF {name} did not reach its exact intended diagnostic")
    return 1 if expected else 0
