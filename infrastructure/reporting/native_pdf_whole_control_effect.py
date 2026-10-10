"""Actual native effects of complete Source-selected whole-PDF controls.

These deterministic facts are DATA. The caller separately authenticates the
complete Source-selected requirement, original native raster executions, SDK
ownership, original OS outcome and independent current predicate replay. This
helper cannot admit a caller-selected subset or qualify a control by itself.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from io import BytesIO
from typing import Any

SCHEMA = "template-native-whole-pdf-control-effect-v1"
_MAX_BYTES = 64 * 1024 * 1024
_MAX_RASTERS = 256 * 1024 * 1024
_MAX_PIXELS = 60_000_000
_MAX_OBJECTS = 4_000_000
_SCALE = 150 / 72
_TEXT_OPERATORS = frozenset(
    (
        b"BT",
        b"ET",
        b"Tc",
        b"Tw",
        b"Tz",
        b"TL",
        b"Tf",
        b"Tr",
        b"Ts",
        b"Td",
        b"TD",
        b"Tm",
        b"T*",
        b"Tj",
        b"TJ",
        b"'",
        b'"',
    )
)


def _budget(deadline: float) -> None:
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError("whole PDF native effect requires its original finite deadline")
    if time.monotonic() >= deadline:
        raise TimeoutError("whole PDF native effect exhausted its original deadline")


def _number(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("whole PDF native effect geometry is not finite numeric data")
    return float(value)


def _box(value: Any) -> tuple[float, float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError("whole PDF native effect requires a complete actual box")
    x0, top, x1, bottom = map(_number, value)
    if x0 >= x1 or top >= bottom:
        raise ValueError("whole PDF native effect box has no positive area")
    return x0, top, x1, bottom


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _operand(value: Any, depth: int = 0) -> Any:
    if depth > 8:
        raise ValueError("whole PDF native text operand nesting exceeds its bound")
    if isinstance(value, str):
        return ["string", str(value)]
    if isinstance(value, bytes):
        return ["bytes", value.hex()]
    if isinstance(value, (list, tuple)):
        if len(value) > _MAX_OBJECTS:
            raise ValueError("whole PDF native text operand exceeds its complete object bound")
        return ["array", [_operand(item, depth + 1) for item in value]]
    return ["number", _number(value)]


def _control(control: dict[str, Any]) -> str:
    if type(control) is not dict or set(control) != {
        "identity",
        "mutation",
        "target",
        "intended_diagnostic",
        "unsupported",
        "source_category",
        "source_identity",
    }:
        raise ValueError("whole PDF native effect requires the exact Source-selected control row")
    identity = control["identity"]
    mutation = control["mutation"]
    if (
        not isinstance(identity, str)
        or not identity
        or not isinstance(mutation, str)
        or control["unsupported"] is not None
    ):
        raise ValueError("whole PDF native effect refuses a missing or unsupported Source control")
    if mutation == "baseline":
        if (
            identity != "baseline"
            or control["target"] is not None
            or control["intended_diagnostic"] is not None
            or control["source_category"] is not None
            or control["source_identity"] is not None
        ):
            raise ValueError("whole PDF native effect baseline differs from its Source declaration")
    elif mutation == "page-rotation":
        target = control["target"]
        if (
            type(target) is not dict
            or set(target) != {"page"}
            or type(target["page"]) is not int
            or identity != f"page:{target['page']}:rotation"
            or control["intended_diagnostic"] != "pdf.reference.layout"
            or control["source_category"] is not None
            or control["source_identity"] is not None
        ):
            raise ValueError("whole PDF native effect rotation differs from its Source declaration")
    elif mutation == "occurrence-white-paint":
        category, source_identity = control["source_category"], control["source_identity"]
        if (
            not isinstance(category, str)
            or category not in {"text", "note", "occurrence", "table-cell"}
            or not isinstance(source_identity, str)
            or not source_identity
            or identity != category + ":" + source_identity + ":paint"
            or control["intended_diagnostic"] != "pdf.reference.pixels"
            or type(control["target"]) is not list
            or not 1 <= len(control["target"]) <= 250_000
        ):
            raise ValueError("whole PDF native effect requires every admitted Source occurrence target")
    else:
        raise ValueError("whole PDF native effect refuses an unknown Source mutation")
    return mutation


def inspect_whole_pdf_native_effect(
    original_pdf: bytes,
    mutant_pdf: bytes,
    original_rasters: tuple[bytes, ...],
    mutant_rasters: tuple[bytes, ...],
    control: dict[str, Any],
    *,
    deadline: float,
) -> dict[str, Any]:
    """Observe actual complete native mutation effects, refusing setup/no-op.

    All supplied rasters must already be bound to genuine original native tool
    execution for the exact PDFs. This callable observes bytes and all targets;
    it neither invents that authority nor declares a native predicate outcome.
    """
    import pdfplumber
    from PIL import Image, ImageChops
    from pypdf import PdfReader

    from infrastructure.reporting.native_pdf_stream_bounds import preflight_pdf_streams

    def _text_program(page: Any, deadline: float) -> tuple[str, int, int]:
        content = page.get_contents()
        if content is None:
            raise ValueError("whole PDF native control page has no original content program")
        operations = content.operations
        if not operations or len(operations) > _MAX_OBJECTS:
            raise ValueError("whole PDF native control page content exceeds its original finite bound")
        digest = hashlib.sha256()
        count = text_objects = 0
        depth = 0
        for ordinal, (operands, operator) in enumerate(operations):
            if ordinal % 1024 == 0:
                _budget(deadline)
            if operator not in _TEXT_OPERATORS:
                continue
            if operator == b"BT":
                if depth:
                    raise ValueError("whole PDF native text program has nested text objects")
                depth = 1
                text_objects += 1
            elif operator == b"ET":
                if not depth:
                    raise ValueError("whole PDF native text program has an unmatched text-object end")
                depth = 0
            digest.update(json.dumps([operator.decode("ascii"), _operand(operands)], separators=(",", ":")).encode())
            digest.update(b"\n")
            count += 1
        if depth:
            raise ValueError("whole PDF native text program omitted its text-object end")
        return digest.hexdigest(), count, text_objects

    def _text_census(page: Any, deadline: float) -> tuple[str, dict[str, int]]:
        digest = hashlib.sha256()
        counts: dict[str, int] = {}
        total = 0
        for kind, objects in sorted(page.objects.items()):
            if kind != "char" and not kind.startswith("text"):
                continue
            counts[kind] = len(objects)
            total += len(objects)
            if total > _MAX_OBJECTS:
                raise ValueError("whole PDF native complete text census exceeds its finite bound")
            for ordinal, obj in enumerate(objects):
                if ordinal % 1024 == 0:
                    _budget(deadline)
                text = obj.get("text")
                if not isinstance(text, str) or "(cid:" in text:
                    raise ValueError("whole PDF native text identity is missing or unresolved")
                row: dict[str, Any] = {"kind": kind, "text": text}
                for key in ("x0", "x1", "y0", "y1", "top", "bottom", "width", "height", "doctop"):
                    row[key] = _number(obj[key])
                if row["x0"] > row["x1"] or row["top"] > row["bottom"]:
                    raise ValueError("whole PDF native text geometry has inverted bounds")
                if kind == "char":
                    font = obj.get("fontname")
                    matrix = obj.get("matrix")
                    if (
                        not isinstance(font, str)
                        or not font
                        or not isinstance(matrix, (list, tuple))
                        or len(matrix) != 6
                    ):
                        raise ValueError("whole PDF native glyph omitted its original font or transform")
                    row.update(fontname=font, size=_number(obj["size"]), adv=_number(obj["adv"]))
                    if row["size"] <= 0 or type(obj.get("upright")) is not bool:
                        raise ValueError("whole PDF native glyph has invalid size or orientation")
                    row.update(upright=obj["upright"], matrix=list(map(_number, matrix)))
                digest.update(json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())
                digest.update(b"\n")
        return digest.hexdigest(), counts

    def _geometry(page: Any) -> dict[str, Any]:
        width, height = _number(page.width), _number(page.height)
        if width <= 0 or height <= 0 or math.ceil(width * _SCALE) * math.ceil(height * _SCALE) > _MAX_PIXELS:
            raise ValueError("whole PDF native page has empty or excessive physical geometry")
        rotation = page.rotation
        if type(rotation) is not int or rotation not in (0, 90, 180, 270):
            raise ValueError("whole PDF native page rotation is not an admitted quarter turn")
        return {
            "width_pt": width,
            "height_pt": height,
            "media_box_pt": list(_box(page.mediabox)),
            "crop_box_pt": list(_box(page.cropbox)),
            "rotation": rotation,
        }

    _budget(deadline)
    mutation = _control(control)
    if any(type(raw) is not bytes or not raw or len(raw) > _MAX_BYTES for raw in (original_pdf, mutant_pdf)):
        raise ValueError("whole PDF native effect requires two bounded nonempty exact PDF byte strings")
    if (
        type(original_rasters) is not tuple
        or type(mutant_rasters) is not tuple
        or not 1 <= len(original_rasters) <= 500
        or len(original_rasters) != len(mutant_rasters)
        or any(type(raw) is not bytes or not raw for raw in (*original_rasters, *mutant_rasters))
        or sum(map(len, (*original_rasters, *mutant_rasters))) > _MAX_RASTERS
    ):
        raise ValueError("whole PDF native effect requires every bounded nonempty original and mutant page raster")
    if mutation == "baseline" and mutant_pdf != original_pdf:
        raise ValueError("whole PDF native baseline changed the exact original PDF bytes")
    if mutation != "baseline" and mutant_pdf == original_pdf:
        raise ValueError("whole PDF native mutation changed no actual PDF bytes")
    for raw in (original_pdf, mutant_pdf):
        preflight_pdf_streams(raw, deadline=deadline, max_bytes=_MAX_BYTES, max_objects=_MAX_OBJECTS)
    original_reader = PdfReader(BytesIO(original_pdf), strict=True)
    mutant_reader = PdfReader(BytesIO(mutant_pdf), strict=True)
    pages: list[dict[str, Any]] = []
    targets: list[dict[str, Any]] = []
    total_objects = total_operations = 0
    with (
        pdfplumber.open(BytesIO(original_pdf), laparams={}) as original,
        pdfplumber.open(BytesIO(mutant_pdf), laparams={}) as mutant,
    ):
        count = len(original.pages)
        if not 1 <= count <= 500 or any(
            size != count
            for size in (len(mutant.pages), len(original_reader.pages), len(mutant_reader.pages), len(original_rasters))
        ):
            raise ValueError("whole PDF native effect omitted an actual original or mutant page")
        selected_page = control["target"]["page"] if mutation == "page-rotation" else None
        if selected_page is not None and not 1 <= selected_page <= count:
            raise ValueError("whole PDF native rotation target is outside the complete page roster")
        by_page: dict[int, list[tuple[int, tuple[float, float, float, float]]]] = {}
        if mutation == "occurrence-white-paint":
            for ordinal, target in enumerate(control["target"], 1):
                _budget(deadline)
                if (
                    type(target) is not dict
                    or set(target) != {"page", "box_pt"}
                    or type(target["page"]) is not int
                    or not 1 <= target["page"] <= count
                ):
                    raise ValueError("whole PDF native occurrence target has no admitted original page")
                by_page.setdefault(target["page"], []).append((ordinal, _box(target["box_pt"])))
        for number, (page, changed) in enumerate(zip(original.pages, mutant.pages, strict=True), 1):
            _budget(deadline)
            geometry, changed_geometry = _geometry(page), _geometry(changed)
            for parsed, native in (
                (original_reader.pages[number - 1], page),
                (mutant_reader.pages[number - 1], changed),
            ):
                if _number(parsed.user_unit) != 1 or parsed.rotation % 360 != native.rotation:
                    raise ValueError("whole PDF native page parsers disagree on original rotation or physical units")
            expected_rotation = (page.rotation + (180 if number == selected_page else 0)) % 360
            if changed.rotation != expected_rotation or {k: v for k, v in geometry.items() if k != "rotation"} != {
                k: v for k, v in changed_geometry.items() if k != "rotation"
            }:
                raise ValueError("whole PDF native mutation changed unexpected complete page geometry")
            original_program = _text_program(original_reader.pages[number - 1], deadline)
            mutant_program = _text_program(mutant_reader.pages[number - 1], deadline)
            if original_program != mutant_program:
                raise ValueError("whole PDF native mutation changed an original text object or text program")
            original_census, original_counts = _text_census(page, deadline)
            mutant_census, mutant_counts = _text_census(changed, deadline)
            total_objects += sum(original_counts.values()) + sum(mutant_counts.values())
            total_operations += original_program[1] + mutant_program[1]
            if max(total_objects, total_operations) > _MAX_OBJECTS:
                raise ValueError("whole PDF native complete text census exceeds its aggregate finite bound")
            if original_counts != mutant_counts or number != selected_page and original_census != mutant_census:
                raise ValueError("whole PDF native mutation removed or changed original glyph/text census or geometry")
            with (
                Image.open(BytesIO(original_rasters[number - 1])) as original_image,
                Image.open(BytesIO(mutant_rasters[number - 1])) as mutant_image,
            ):
                for image, native in ((original_image, page), (mutant_image, changed)):
                    if (
                        image.format != "PNG"
                        or image.mode not in ("L", "RGB")
                        or image.info.get("transparency") is not None
                        or getattr(image, "n_frames", 1) != 1
                        or not 0 < image.width * image.height <= _MAX_PIXELS
                        or abs(image.width - native.width * _SCALE) > 2
                        or abs(image.height - native.height * _SCALE) > 2
                    ):
                        raise ValueError(
                            "whole PDF native effect requires complete opaque bounded 150dpi PNG page pixels"
                        )
                if original_image.size != mutant_image.size:
                    raise ValueError("whole PDF native mutation changed actual page pixel dimensions")
                with original_image.convert("RGB") as pixels, mutant_image.convert("RGB") as changed_pixels:
                    for pixel_image in (pixels, changed_pixels):
                        if not any(
                            isinstance(channel, tuple) and len(channel) == 2 and channel[0] != channel[1]
                            for channel in pixel_image.getextrema()
                        ):
                            raise ValueError("whole PDF native control page is blank or uniformly colored")
                    with ImageChops.difference(pixels, changed_pixels) as difference:
                        with (
                            difference.getchannel("R") as red,
                            difference.getchannel("G") as green,
                            difference.getchannel("B") as blue,
                            ImageChops.lighter(red, green) as red_green,
                            ImageChops.lighter(red_green, blue) as mask,
                        ):
                            changed_count = mask.width * mask.height - mask.histogram()[0]
                            if (number == selected_page or number in by_page) and not changed_count:
                                raise ValueError("whole PDF native target page changed no actual decoded pixels")
                            if number != selected_page and number not in by_page and changed_count:
                                raise ValueError("whole PDF native mutation changed an unselected original page")
                            for ordinal, box in by_page.get(number, []):
                                _budget(deadline)
                                x0, top, x1, bottom = box
                                if (
                                    page.rotation != 0
                                    or geometry["media_box_pt"][:2] != [0.0, 0.0]
                                    or not (0 <= x0 < x1 <= page.width and 0 <= top < bottom <= page.height)
                                ):
                                    raise ValueError(
                                        "whole PDF native occurrence target is outside admitted page geometry"
                                    )
                                roi = (
                                    math.floor(x0 * _SCALE),
                                    math.floor(top * _SCALE),
                                    min(mask.width, math.ceil(x1 * _SCALE)),
                                    min(mask.height, math.ceil(bottom * _SCALE)),
                                )
                                if roi[0] >= roi[2] or roi[1] >= roi[3]:
                                    raise ValueError("whole PDF native occurrence target has no actual raster region")
                                with mask.crop(roi) as region:
                                    target_changed = region.width * region.height - region.histogram()[0]
                                if not target_changed:
                                    raise ValueError("whole PDF native Source occurrence mutation is a pixel no-op")
                                targets.append(
                                    {
                                        "target_ordinal": ordinal,
                                        "page": number,
                                        "box_pt": list(box),
                                        "roi_px": list(roi),
                                        "changed_pixels": target_changed,
                                    }
                                )
                    pages.append(
                        {
                            "page": number,
                            "original_geometry": geometry,
                            "mutant_geometry": changed_geometry,
                            "original_text_census_sha256": original_census,
                            "mutant_text_census_sha256": mutant_census,
                            "text_object_counts": original_counts,
                            "text_program_sha256": original_program[0],
                            "text_operation_count": original_program[1],
                            "text_object_count": original_program[2],
                            "pixel_dimensions": list(pixels.size),
                            "original_pixels_sha256": hashlib.sha256(pixels.tobytes()).hexdigest(),
                            "mutant_pixels_sha256": hashlib.sha256(changed_pixels.tobytes()).hexdigest(),
                            "original_raster_sha256": hashlib.sha256(original_rasters[number - 1]).hexdigest(),
                            "mutant_raster_sha256": hashlib.sha256(mutant_rasters[number - 1]).hexdigest(),
                            "changed_pixels": changed_count,
                        }
                    )
            page.close()
            changed.close()
    targets.sort(key=lambda row: row["target_ordinal"])
    if mutation == "occurrence-white-paint" and len(targets) != len(control["target"]):
        raise ValueError("whole PDF native effect omitted an admitted Source occurrence target")
    _budget(deadline)
    return {
        "schema_version": SCHEMA,
        "control_identity": control["identity"],
        "source_category": control["source_category"],
        "source_identity": control["source_identity"],
        "control_digest": _digest(control),
        "mutation": mutation,
        "original_pdf_sha256": hashlib.sha256(original_pdf).hexdigest(),
        "mutant_pdf_sha256": hashlib.sha256(mutant_pdf).hexdigest(),
        "ordered_pages": list(range(1, len(pages) + 1)),
        "pages": pages,
        "targets": targets,
        "assurance": (
            "actual complete byte, text, geometry and decoded-pixel effect data; "
            "no execution authority or native predicate outcome"
        ),
    }
