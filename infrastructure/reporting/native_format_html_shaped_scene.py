"""Complete Source contextual runs rendered from exact physical font buffers.

Positions are native observations; text/style/cluster IDs/outlines/font bytes
come from independently compiled Source and a genuine physical shaper probe.
Source layout, browser defaults and OS calibration obligations remain separate.
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
import math
import re
from io import BytesIO
from typing import Any, cast

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_html_glyph_contours import (
    map_source_character_runs,
)
from infrastructure.reporting.native_format_html_source_metadata import (
    remaining_seconds,
)


def _color(value: str | None) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}|white|black", value):
        raise ValueError("Source contextual scene needs an exact authored finite color")
    return value


def build_source_shaped_scene(
    source: dict[str, Any],
    dom: dict[str, Any],
    contours: list[dict[str, Any]],
    *,
    deadline: float,
    observer_script: str,
    scene_schema: str,
) -> tuple[dict[str, Any], bytes]:
    """Reference words retain true ligatures/kerning/combining and exact bytes."""
    remaining_seconds(deadline)
    mapping = map_source_character_runs(source, dom)
    profile = source["source_style_profile"]
    mapped_by_run: dict[str, list[dict[str, Any]]] = {}
    for mapped in mapping["characters"]:
        mapped_by_run.setdefault(mapped["source_run_id"], []).append(mapped)
    source_runs = {run["source_id"]: run for run in source["runs"]}
    width, height = dom["width"], max(900, dom["height"])
    if width not in {390, 1280} or type(height) is not int or not 0 < height <= 30000:
        raise ValueError("Source contextual scene exceeds the original finite viewport")
    glyphs = []
    spans = []
    faces = []
    complete_outlines = []
    blockers = list(mapping["blockers"])
    for font_index, font in enumerate(contours):
        remaining_seconds(deadline)
        if font.get("digest") != canonical_digest({key: value for key, value in font.items() if key != "digest"}):
            raise ValueError("Source contextual scene received changed complete font contours")
        shaped_runs = font.get("shaped_runs", [])
        if not shaped_runs:
            continue
        complete_outlines.append(
            {
                "postscript_name": font["postscript_name"],
                "glyphs": font["shaped_outlines"],
            }
        )
        raw = base64.b64decode(font["font_data_base64"], validate=True)
        if len(raw) > 32 * 1024 * 1024 or hashlib.sha256(raw).hexdigest() != font["font_sha256"]:
            raise ValueError("Source contextual reference exact font buffer changed")
        if raw.startswith(b"ttcf"):
            blockers.append(
                font["postscript_name"]
                + ": reference FontFace collection selection needs exact exported face-byte custody"
            )
            continue
        alias = "SourceFont" + str(font_index)
        faces.append(
            {
                "family": alias,
                "weight": str(font["weight_class"]),
                "style": "italic" if font["italic"] else "normal",
                "sha256": font["font_sha256"],
                "bytes": len(raw),
                "data": font["font_data_base64"],
            }
        )
        for shaped in shaped_runs:
            remaining_seconds(deadline)
            original = source_runs[shaped["source_run_id"]]
            style = original["source_style"]
            if (
                style["expected_postscript_name"] != font["postscript_name"]
                or style["font_weight"] != str(font["weight_class"])
                or (style["font_style"] == "italic") != font["italic"]
            ):
                raise ValueError("independent physical Source font differs from original authored style")
            rows = [
                row
                for row in mapped_by_run.get(shaped["source_run_id"], [])
                if shaped["source_start"] <= row["source_character_offset"] < shaped["source_end"]
            ]
            if not rows or any(len(row["boxes"]) != 1 for row in rows):
                blockers.append(shaped["source_id"] + ": Source contextual line lacks complete unique placement")
                continue
            boxes = [row["boxes"][0] for row in rows]
            left, top = min(box[0] for box in boxes), min(box[1] for box in boxes)
            right, bottom = (
                max(box[0] + box[2] for box in boxes),
                max(box[1] + box[3] for box in boxes),
            )
            box = [left, top, right - left, bottom - top]
            px = style.get("independent_font_px")
            if px is None:
                blockers.append(shaped["source_id"] + ": independent Source writer/UA font size is unavailable")
                continue
            if (
                type(px) not in {int, float}
                or not math.isfinite(px)
                or not 0 < px <= 128
                or any(not math.isfinite(value) for value in box)
            ):
                raise ValueError("Source contextual line exceeds its original finite font/geometry bound")
            target = html.escape(json.dumps(box, separators=(",", ":")), quote=True)
            identity = html.escape(shaped["source_id"], quote=True)
            background = style["authored_background"]
            spans.append(
                f'<span data-source-glyph="{identity}" data-target="{target}" '
                f'style="font-family:{alias};font-size:{px}px;font-weight:{style["font_weight"]};'
                f"font-style:{style['font_style']};color:{_color(style['authored_color'])};"
                f'background:{_color(background)}">{html.escape(shaped["text"])}<i></i></span>'
            )
            glyphs.append(
                {
                    "source_id": shaped["source_id"],
                    "character": shaped["text"],
                    "box": box,
                    "font_px": px,
                    "postscript_name": font["postscript_name"],
                    "font_sha256": font["font_sha256"],
                    "font_contour_digest": font["digest"],
                    "shaped_run": shaped,
                    "source_style": style,
                    "reference_font_family": alias,
                }
            )
            glyphs[-1]["source_background"] = _color(background)
    body_color = _color(profile["authored_rules"]["body"].get("background-color"))
    body = (
        f'<!doctype html><html><head><meta charset="utf-8"><style>'
        f"html,body{{margin:0;padding:0;width:{width}px;height:{height}px;background:{body_color};overflow:visible}}"
        "[data-source-glyph]{position:absolute;left:0;top:0;white-space:pre;font-kerning:normal;"
        "font-variant-ligatures:normal;font-synthesis:none;letter-spacing:normal;word-spacing:0px;"
        "text-transform:none;text-shadow:none;direction:ltr;writing-mode:horizontal-tb;line-height:normal}"
        "i{display:inline-block;width:0;height:0;padding:0;margin:0;vertical-align:baseline}"
        f"</style><script>globalThis.__native_source_font_buffers={json.dumps(faces, separators=(',', ':'))};"
        f"</script></head><body>{''.join(spans)}</body></html>"
    ).encode()
    blockers.extend(
        [
            "actual Chromium UA-default size and contextual shaper/hinting equivalence need genuine calibration",
            "complete consumed browser/font decoder and dyld dependency custody remains unclosed",
        ]
    )
    base = {
        "schema_version": scene_schema,
        "projection": "source-contextual-lines-v1",
        "source_digest": source["digest"],
        "width": width,
        "height": height,
        "scene_sha256": hashlib.sha256(body).hexdigest(),
        "observer_sha256": hashlib.sha256(observer_script.encode()).hexdigest(),
        "glyphs": glyphs,
        "source_occurrences": len(mapping["characters"]),
        "font_buffers": [{key: value for key, value in face.items() if key != "data"} for face in faces],
        "complete_outlines": complete_outlines,
        "findings": mapping["findings"],
        "blockers": blockers,
    }
    return {**base, "digest": canonical_digest(base)}, body


def inspect_source_shaped_ink(
    scene: dict[str, Any],
    reference_dom: dict[str, Any],
    reference_png: bytes,
    candidate_png: bytes,
    *,
    deadline: float,
) -> dict[str, Any]:
    """Compare complete independently shaped outline regions, never bbox contrast."""
    from PIL import Image

    remaining_seconds(deadline)
    if scene["digest"] != canonical_digest({key: value for key, value in scene.items() if key != "digest"}):
        raise ValueError("Source contextual scene changed")
    actual_buffers = reference_dom.get("source_font_buffers")
    if actual_buffers != scene["font_buffers"]:
        raise ValueError(
            "actual Source reference FontFace(ArrayBuffer) consumption differs from exact physical font bytes"
        )
    rows = reference_dom.get("text")
    if (
        reference_dom.get("ready") != "complete"
        or reference_dom.get("width") != scene["width"]
        or not isinstance(rows, list)
        or len(rows) != len(scene["glyphs"])
    ):
        raise ValueError("actual Source contextual reference omitted complete original line occurrences")
    if max(len(reference_png), len(candidate_png)) > 64 * 1024 * 1024:
        raise ValueError("Source contextual raster exceeds its original finite byte bound")
    findings = list(scene["findings"])
    blockers = list(scene["blockers"])
    observations = []
    with (
        Image.open(BytesIO(reference_png)) as reference,
        Image.open(BytesIO(candidate_png)) as candidate,
    ):
        if reference.size != candidate.size or reference.size != (
            scene["width"],
            scene["height"],
        ):
            raise ValueError("actual Source contextual native viewport changed")
        expected_pixels, actual_pixels = (
            reference.convert("RGB"),
            candidate.convert("RGB"),
        )
        for source, actual in zip(scene["glyphs"], rows, strict=True):
            remaining_seconds(deadline)
            if actual["source_id"] != source["source_id"] or actual["text"] != source["character"]:
                raise ValueError("actual Source contextual native reference reordered original text")
            native_fonts = actual.get("platform_fonts", [])
            if len(native_fonts) != 1 or native_fonts[0]["postScriptName"] != source["postscript_name"]:
                raise ValueError("actual Source contextual reference selected a different physical font")
            if any(abs(a - b) > 1 / 64 for a, b in zip(actual["box"], source["box"], strict=True)):
                findings.append(
                    {
                        "code": "html.glyph.source-contextual-advance",
                        "source_id": source["source_id"],
                    }
                )
            shaped = source["shaped_run"]
            source_outlines = next(
                row["glyphs"]
                for row in scene["complete_outlines"]
                if row["postscript_name"] == source["postscript_name"]
            )
            outlines = {row["glyph_id"]: row for row in source_outlines}
            pen_x = pen_y = 0
            regions = []
            scale = source["font_px"] / shaped["units_per_em"]
            for glyph in shaped["glyphs"]:
                outline = outlines[glyph["glyph_id"]]
                bounds = outline["bounds_units"]
                if bounds:
                    x0, y0, x1, y1 = bounds
                    x = actual["baseline"][0] + (pen_x + glyph["x_offset_units"]) * scale
                    y = actual["baseline"][1] - (pen_y + glyph["y_offset_units"]) * scale
                    regions.append(
                        (
                            math.floor(x + x0 * scale) - 2,
                            math.floor(y - y1 * scale) - 2,
                            math.ceil(x + x1 * scale) + 2,
                            math.ceil(y - y0 * scale) + 2,
                        )
                    )
                pen_x += glyph["x_advance_units"]
                pen_y += glyph["y_advance_units"]
            color = source["source_background"]
            if color.startswith("#"):
                background_rgb = tuple(int(color[index : index + 2], 16) for index in (1, 3, 5))
            else:
                background_rgb = (255, 255, 255) if color == "white" else (0, 0, 0)
            changed = compared = ink = 0
            for left, top, right, bottom in regions:
                if left < 0 or top < 0 or right > reference.width or bottom > reference.height:
                    findings.append(
                        {
                            "code": "html.glyph.source-contextual-outline-crop",
                            "source_id": source["source_id"],
                        }
                    )
                    continue
                for y in range(top, bottom):
                    remaining_seconds(deadline)
                    for x in range(left, right):
                        expected = cast(tuple[int, int, int], expected_pixels.getpixel((x, y)))
                        observed = cast(tuple[int, int, int], actual_pixels.getpixel((x, y)))
                        compared += 1
                        ink += expected != background_rgb
                        changed += max(abs(a - b) for a, b in zip(expected, observed, strict=True)) > 2
            if not regions or not ink:
                findings.append(
                    {
                        "code": "html.glyph.source-contextual-no-outline",
                        "source_id": source["source_id"],
                    }
                )
            if changed:
                findings.append(
                    {
                        "code": "html.glyph.source-contextual-ink",
                        "source_id": source["source_id"],
                    }
                )
            observations.append(
                {
                    "source_id": source["source_id"],
                    "font_sha256": source["font_sha256"],
                    "complete_shaped_outlines_digest": canonical_digest(source_outlines),
                    "pixels_compared": compared,
                    "source_reference_ink_pixels": ink,
                    "pixels_over_error_2": changed,
                }
            )
    base = {
        "scene_digest": scene["digest"],
        "glyphs": observations,
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }
    return {**base, "digest": canonical_digest(base)}
