"""Source-only glyph scenes and complete independently rendered ink comparison.

The reference renderer receives original characters, independently decoded font
contours and measured native coordinates. Candidate HTML, CSS, clipping, canvas
or raster never supplies its expected ink. A tool-backed reader must freshly
render the exact returned scene and authenticate its font/runtime consumption.
This module retains the unresolved OS/shaping obligations; it is not a source
approval switch.
"""

from __future__ import annotations

import hashlib
import html
import json
import math
import re
from io import BytesIO
from typing import Any, cast

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_html_glyph_contours import (
    FONT_CONTOUR_SCHEMA,
    contour_paint_bounds,
    map_source_character_runs,
)
from infrastructure.reporting.native_format_html_source_metadata import (
    remaining_seconds,
)

SCENE_SCHEMA = "template-native-html-source-glyph-scene-v1"
GLYPH_REFERENCE_SCRIPT = r"""
addEventListener('load',async()=>{
 const consumed=[];
 for(const entry of globalThis.__native_source_font_buffers||[]){
  const raw=Uint8Array.from(atob(entry.data),c=>c.charCodeAt(0));
  if(raw.byteLength!==entry.bytes)throw Error('Source physical font buffer length changed');
  const digestBytes=new Uint8Array(await crypto.subtle.digest('SHA-256',raw));
  const digest=[...digestBytes].map(x=>x.toString(16).padStart(2,'0')).join('');
  if(digest!==entry.sha256)throw Error('Source physical font buffer bytes changed');
  const face=new FontFace(entry.family,raw.buffer,{weight:entry.weight,style:entry.style});
  await face.load();if(face.status!=='loaded')throw Error('Source physical font buffer failed to load');
  document.fonts.add(face);
  consumed.push({family:entry.family,weight:entry.weight,style:entry.style,sha256:digest,bytes:raw.byteLength});
 }
 await document.fonts.ready;
 const rows=[],nodes=[];
 for(const e of document.querySelectorAll('[data-source-glyph]')){
  const n=e.firstChild,r=document.createRange();r.selectNodeContents(n);
  const target=JSON.parse(e.getAttribute('data-target')),b=r.getBoundingClientRect();
  e.style.left=(target[0]-b.x)+'px';e.style.top=(target[1]-b.y)+'px';
  const q=r.getBoundingClientRect(),baseline=e.querySelector('i').getBoundingClientRect();
  rows.push({source_id:e.getAttribute('data-source-glyph'),text:n.textContent,
    box:[q.x,q.y,q.width,q.height],baseline:[q.x,baseline.y]});nodes.push(n);
 }
 globalThis.__native_glyph_text_nodes=nodes;
 const data={ready:document.readyState,width:innerWidth,height:document.documentElement.scrollHeight,
  text:rows,source_font_buffers:consumed};
 const out=document.createElement('pre');out.id='native-browser-observation';out.hidden=true;
 out.textContent=JSON.stringify(data);document.body.append(out);
});
"""


def platform_font_request(source: dict[str, Any], dom: dict[str, Any], *, deadline: float) -> dict[str, Any]:
    """Bind the actual native single-face observation to original codepoints."""
    remaining_seconds(deadline)
    mapping = map_source_character_runs(source, dom)
    fonts: dict[str, dict[str, Any]] = {}
    blockers = list(mapping["blockers"])
    if source.get("source_style_profile") is not None:
        from infrastructure.reporting.native_format_html_contextual_request import (
            compile_contextual_font_request,
        )

        context_fonts, findings, context_blockers = compile_contextual_font_request(
            source, dom, mapping, deadline=deadline
        )
        request = {
            "schema_version": "template-native-html-platform-font-request-v1",
            "source_digest": source["digest"],
            "fonts": context_fonts,
            "findings": [*mapping["findings"], *findings],
            "blockers": [*blockers, *context_blockers],
        }
        profile = source["source_style_profile"]
        if profile.get("font_provider") == "source-web-font-assets-v1":
            if dom.get("source_font_buffers") != [
                {"schema_version": "template-source-web-font-buffer-v1", **row}
                for row in profile["physical_font_assets"]
            ]:
                raise ValueError("actual candidate FontFace buffers differ from independently admitted Source bodies")
            request["font_provider"] = "source-web-font-assets-v1"
        return request
    for row in mapping["characters"]:
        native_fonts = dom["text"][row["text_index"]].get("platform_fonts")
        if not isinstance(native_fonts, list):
            raise ValueError("genuine native glyph font capture is missing")
        if len(native_fonts) != 1 or native_fonts[0].get("isCustomFont"):
            blockers.append(
                row["source_id"]
                + ": native fallback/multi-face/custom-font consumption needs a shaped source run model"
            )
            continue
        name = native_fonts[0]["postScriptName"]
        item = fonts.setdefault(name, {"postscript_name": name, "characters": "", "source_ids": []})
        if row["character"] not in item["characters"]:
            item["characters"] += row["character"]
        item["source_ids"].append(row["source_id"])
    result = {
        "schema_version": "template-native-html-platform-font-request-v1",
        "source_digest": source["digest"],
        "fonts": list(fonts.values()),
        "findings": mapping["findings"],
        "blockers": blockers,
    }
    remaining_seconds(deadline)
    return result


def build_source_glyph_scene(
    source: dict[str, Any],
    dom: dict[str, Any],
    contours: list[dict[str, Any]],
    *,
    deadline: float,
) -> tuple[dict[str, Any], bytes]:
    """Produce a finite clipping-free scene containing every modeled source glyph.

    Native geometry calibrates placement. Font/style origin, hinting and OS
    consumption are retained obligations until their independent witnesses and
    real controls exist. No unsupported source occurrence is silently omitted.
    """
    remaining_seconds(deadline)
    if source.get("source_style_profile") is not None:
        from infrastructure.reporting.native_format_html_shaped_scene import (
            build_source_shaped_scene,
        )

        return build_source_shaped_scene(
            source,
            dom,
            contours,
            deadline=deadline,
            observer_script=GLYPH_REFERENCE_SCRIPT,
            scene_schema=SCENE_SCHEMA,
        )
    mapping = map_source_character_runs(source, dom)
    catalog: dict[str, dict[str, Any]] = {}
    blockers = list(mapping["blockers"])
    for source_font in contours:
        if source_font.get("schema_version") != FONT_CONTOUR_SCHEMA or source_font.get("digest") != canonical_digest(
            {key: value for key, value in source_font.items() if key != "digest"}
        ):
            raise ValueError("independent admitted-font source contours changed")
        name = source_font["postscript_name"]
        if name in catalog:
            raise ValueError("source font contour face identity is ambiguous")
        catalog[name] = source_font
        blockers.extend(source_font["blockers"])
    width, height = dom["width"], max(900, dom["height"])
    if type(width) is not int or width not in {390, 1280} or type(height) is not int or height > 30000:
        raise ValueError("source glyph reference exceeds existing native viewport bounds")
    faces: dict[str, str] = {}
    spans = []
    glyph_rows = []
    for mapped in mapping["characters"]:
        remaining_seconds(deadline)
        row = dom["text"][mapped["text_index"]]
        actual_fonts = row.get("platform_fonts")
        if not isinstance(actual_fonts, list) or len(actual_fonts) != 1 or actual_fonts[0].get("isCustomFont"):
            blockers.append(mapped["source_id"] + ": unknown physical font/fallback source glyph remains obligated")
            continue
        name = actual_fonts[0]["postScriptName"]
        font = catalog.get(name)
        glyph = (
            next(
                (item for item in font["glyphs"] if item["character"] == mapped["character"]),
                None,
            )
            if font
            else None
        )
        if font is None or glyph is None or not glyph["commands"]:
            blockers.append(mapped["source_id"] + ": no independently admitted complete source outline")
            continue
        style = row.get("glyph_style")
        if not isinstance(style, dict):
            raise ValueError("native source glyph omitted its actual text presentation")
        restrictions = {
            "font_style": "normal",
            "font_stretch": "100%",
            "font_kerning": "none",
            "font_ligatures": "none",
            "font_features": "normal",
            "font_variations": "normal",
            "font_synthesis": "none",
            "letter_spacing": "normal",
            "word_spacing": "0px",
            "text_transform": "none",
            "text_shadow": "none",
            "text_decoration": "none",
            "direction": "ltr",
            "writing_mode": "horizontal-tb",
        }
        if (
            any(style.get(key) != expected for key, expected in restrictions.items())
            or font["italic"]
            or style.get("font_weight") != str(font["weight_class"])
        ):
            blockers.append(
                mapped["source_id"]
                + ": kerning/ligatures/synthetic/complex glyph styling requires an independent shaped outline model"
            )
            continue
        color = style.get("color", "")
        if (
            not re.fullmatch(r"rgb\(\d{1,3}, \d{1,3}, \d{1,3}\)", color)
            or any(int(value) > 255 for value in re.findall(r"\d+", color))
            or not re.fullmatch(r"[A-Za-z0-9_ .-]{1,128}", name)
        ):
            blockers.append(
                mapped["source_id"] + ": source glyph color/font syntax requires a separate exact projection model"
            )
            continue
        boxes = mapped["boxes"]
        px = row.get("font_px")
        if (
            len(boxes) != 1
            or any(type(v) not in {int, float} or not math.isfinite(v) for v in boxes[0])
            or type(px) not in {int, float}
            or not 0 < px <= 128
            or not math.isfinite(px)
        ):
            blockers.append(
                mapped["source_id"] + ": source glyph baseline/wrapping geometry requires a separate run model"
            )
            continue
        if boxes[0][2] <= 0 or boxes[0][3] <= 0:
            blockers.append(mapped["source_id"] + ": source glyph has no independently placeable native extent")
            continue
        alias = faces.setdefault(name, "SourceFont" + str(len(faces)))
        identity = html.escape(mapped["source_id"], quote=True)
        target = html.escape(json.dumps(boxes[0], separators=(",", ":")), quote=True)
        spans.append(
            f'<span data-source-glyph="{identity}" data-target="{target}" '
            f'style="font-family:{alias};font-size:{px}px;font-weight:{font["weight_class"]};color:{color}">'
            f"{html.escape(mapped['character'])}<i></i></span>"
        )
        glyph_rows.append(
            {
                "source_id": mapped["source_id"],
                "character": mapped["character"],
                "box": boxes[0],
                "font_px": px,
                "postscript_name": name,
                "font_sha256": font["font_sha256"],
                "font_contour_digest": font["digest"],
                "glyph_id": glyph["glyph_id"],
                "commands_digest": canonical_digest(glyph["commands"]),
            }
        )
    css_faces = "".join(
        f"@font-face{{font-family:{alias};src:local({json.dumps(name)});"
        f"font-weight:{catalog[name]['weight_class']};font-style:normal}}"
        for name, alias in faces.items()
    )
    page = (
        f'<!doctype html><html><head><meta charset="utf-8"><style>{css_faces}'
        f"html,body{{margin:0;padding:0;background:white;width:{width}px;height:{height}px;overflow:visible}}"
        "[data-source-glyph]{position:absolute;left:0;top:0;white-space:pre;font-style:normal;font-stretch:100%;"
        "font-kerning:none;font-variant-ligatures:none;font-feature-settings:normal;font-variation-settings:normal;"
        "font-synthesis:none;letter-spacing:normal;word-spacing:0px;text-transform:none;text-shadow:none;"
        "text-decoration:none;direction:ltr;writing-mode:horizontal-tb;line-height:normal}"
        "i{display:inline-block;width:0;height:0;padding:0;margin:0;vertical-align:baseline}"
        f"</style></head><body>{''.join(spans)}</body></html>"
    ).encode()
    # These are actual unclosed obligations, never producer approval booleans.
    blockers.extend(
        [
            "complete Chromium/CoreText/dyld font consumption and decoder custody is not yet independently admitted",
            "source-authored font/style and baseline-hinting projection needs an independent original-source witness",
            "full source outline/reference raster calibration and common-clip controls have not yet passed genuinely",
        ]
    )
    base = {
        "schema_version": SCENE_SCHEMA,
        "source_digest": source["digest"],
        "width": width,
        "height": height,
        "scene_sha256": hashlib.sha256(page).hexdigest(),
        "observer_sha256": hashlib.sha256(GLYPH_REFERENCE_SCRIPT.encode()).hexdigest(),
        "glyphs": glyph_rows,
        "source_occurrences": len(mapping["characters"]),
        "findings": mapping["findings"],
        "blockers": blockers,
    }
    result = {**base, "digest": canonical_digest(base)}
    remaining_seconds(deadline)
    return result, page


def inspect_source_glyph_ink(
    scene: dict[str, Any],
    contours: list[dict[str, Any]],
    reference_dom: dict[str, Any],
    reference_png: bytes,
    candidate_png: bytes,
    *,
    deadline: float,
) -> dict[str, Any]:
    """Compare every independently rendered source-ink pixel, including strokes.

    This is conditional component evidence. Caller first authenticates the
    source-only scene's genuine original tool outcome, runtime/font byte
    consumption and independent reader re-render. Source blockers survive.
    """
    from PIL import Image

    if scene.get("projection") == "source-contextual-lines-v1":
        from infrastructure.reporting.native_format_html_shaped_scene import (
            inspect_source_shaped_ink,
        )

        return inspect_source_shaped_ink(scene, reference_dom, reference_png, candidate_png, deadline=deadline)

    remaining_seconds(deadline)
    if scene.get("schema_version") != SCENE_SCHEMA or scene.get("digest") != canonical_digest(
        {key: value for key, value in scene.items() if key != "digest"}
    ):
        raise ValueError("source glyph scene witness changed")
    catalog = {font["postscript_name"]: font for font in contours}
    if len(catalog) != len(contours) or any(
        font.get("digest") != canonical_digest({key: value for key, value in font.items() if key != "digest"})
        for font in contours
    ):
        raise ValueError("independent source glyph contour catalog changed")
    rows = reference_dom.get("text")
    if (
        reference_dom.get("ready") != "complete"
        or reference_dom.get("width") != scene["width"]
        or not isinstance(rows, list)
        or len(rows) != len(scene["glyphs"])
    ):
        raise ValueError("actual source-only glyph reference omitted complete occurrences")
    if len(reference_png) > 64 * 1024 * 1024 or len(candidate_png) > 64 * 1024 * 1024:
        raise ValueError("glyph reference/candidate raster exceeds the existing byte bound")
    findings = list(scene["findings"])
    observations = []
    uncovered = 0
    blockers = list(scene["blockers"])
    with (
        Image.open(BytesIO(reference_png)) as reference,
        Image.open(BytesIO(candidate_png)) as candidate,
    ):
        if reference.size != candidate.size or reference.size != (
            scene["width"],
            scene["height"],
        ):
            raise ValueError("independent glyph raster viewport geometry changed")
        expected_pixels, actual_pixels = (
            reference.convert("RGB"),
            candidate.convert("RGB"),
        )
        coverage = Image.new("1", reference.size, 0)
        for source, actual in zip(scene["glyphs"], rows, strict=True):
            remaining_seconds(deadline)
            if actual.get("source_id") != source["source_id"] or actual.get("text") != source["character"]:
                raise ValueError("source-only glyph reference reordered/replaced a source occurrence")
            fonts = actual.get("platform_fonts")
            if (
                not isinstance(fonts, list)
                or len(fonts) != 1
                or fonts[0].get("postScriptName") != source["postscript_name"]
            ):
                raise ValueError("source-only reference consumed a different actual font face")
            box = actual["box"]
            if (
                len(box) != 4
                or any(type(v) not in {int, float} or not math.isfinite(v) for v in box)
                or any(abs(v - w) > 1 / 64 for v, w in zip(box, source["box"], strict=True))
            ):
                blockers.append(source["source_id"] + ": independent glyph baseline/native advance geometry differs")
                continue
            font = catalog[source["postscript_name"]]
            if font["digest"] != source["font_contour_digest"] or font["font_sha256"] != source["font_sha256"]:
                raise ValueError("source-only glyph face bytes changed")
            glyph = next(item for item in font["glyphs"] if item["character"] == source["character"])
            if (
                glyph["glyph_id"] != source["glyph_id"]
                or canonical_digest(glyph["commands"]) != source["commands_digest"]
            ):
                raise ValueError("complete source glyph outline changed")
            x, y, width, height = contour_paint_bounds(glyph, font, source["font_px"], actual["baseline"])
            # Complete outline extent, including negative bearings/descenders;
            # two fixed pixels admit native hinting at its contour boundary.
            left, top, right, bottom = (
                math.floor(x) - 2,
                math.floor(y) - 2,
                math.ceil(x + width) + 2,
                math.ceil(y + height) + 2,
            )
            if left < 0 or top < 0 or right > reference.width or bottom > reference.height:
                findings.append(
                    {
                        "code": "html.glyph.outline-crop",
                        "source_id": source["source_id"],
                    }
                )
                continue
            coverage.paste(1, (left, top, right, bottom))
            ink, changed, maximum = 0, 0, 0
            expected_bytes = bytearray()
            for yy in range(top, bottom):
                remaining_seconds(deadline)
                for xx in range(left, right):
                    pixel = cast(tuple[int, int, int], expected_pixels.getpixel((xx, yy)))
                    if pixel == (255, 255, 255):
                        continue
                    ink += 1
                    expected_bytes.extend(pixel)
                    observed = cast(tuple[int, int, int], actual_pixels.getpixel((xx, yy)))
                    error = max(abs(a - b) for a, b in zip(pixel, observed, strict=True))
                    maximum = max(maximum, error)
                    changed += error > 2
            if not ink:
                findings.append(
                    {
                        "code": "html.glyph.reference-no-ink",
                        "source_id": source["source_id"],
                    }
                )
            if changed:
                findings.append({"code": "html.glyph.outline-ink", "source_id": source["source_id"]})
            observations.append(
                {
                    "source_id": source["source_id"],
                    "font_sha256": source["font_sha256"],
                    "complete_commands_digest": source["commands_digest"],
                    "source_contour_region_px": [left, top, right - left, bottom - top],
                    "source_reference_ink_pixels": ink,
                    "pixels_over_error_2": changed,
                    "maximum_channel_error": maximum,
                    "expected_ink_sha256": hashlib.sha256(expected_bytes).hexdigest(),
                }
            )
        # A contour bbox alone cannot close full-ink coverage. Every source-only
        # reference ink pixel outside the union of complete mapped contours is
        # an unmodeled hinting/placement obligation and a failed reference proof.
        for yy in range(reference.height):
            remaining_seconds(deadline)
            for xx in range(reference.width):
                if not coverage.getpixel((xx, yy)) and expected_pixels.getpixel((xx, yy)) != (255, 255, 255):
                    uncovered += 1
        if uncovered:
            findings.append({"code": "html.glyph.reference-contour-coverage"})
            blockers.append("source-only glyph raster has ink outside independently mapped complete source contours")
    result = {
        "scene_digest": scene["digest"],
        "glyphs": observations,
        "reference_contour_uncovered_ink_pixels": uncovered,
        "findings": findings,
        "blockers": blockers,
        "status": "fail" if findings else "blocked" if blockers else "pass",
    }
    result = {**result, "digest": canonical_digest(result)}
    remaining_seconds(deadline)
    return result


def replay_source_glyph_ink(
    source: dict[str, Any],
    native_dom: dict[str, Any],
    independently_decoded_contours: list[dict[str, Any]],
    independent_reference_dom: dict[str, Any],
    independent_reference_png: bytes,
    candidate_png: bytes,
    raw: dict[str, Any],
    *,
    deadline: float,
) -> dict[str, Any]:
    """Use reader-local source fonts/reference render; never producer pixels."""
    scene, _ = build_source_glyph_scene(source, native_dom, independently_decoded_contours, deadline=deadline)
    result = inspect_source_glyph_ink(
        scene,
        independently_decoded_contours,
        independent_reference_dom,
        independent_reference_png,
        candidate_png,
        deadline=deadline,
    )
    if result != raw:
        raise ValueError("independent source glyph outline/ink replay differs")
    remaining_seconds(deadline)
    return result
