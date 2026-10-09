"""Independent finite original SVG primitive/stroke/marker enclosures.

Only original SVG geometry and its genuine Source-only computed styles are
consumed. No target/native candidate pixels select a font, geometry or margin.
Glyph shaping, effects and whole-document positions stay explicit residuals.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Any

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_mermaid_svg_geometry import SvgGeometry, numbers, point
from infrastructure.reporting.native_mermaid_svg_paint import preflight_original_mermaid_svg

SCHEMA = "template-native-independent-original-svg-ink-enclosures-v1"
PRIMITIVES = {"rect", "circle", "ellipse", "polygon", "polyline", "line", "path"}
REMAINING = (
    "genuine Source-only browser/process/style provenance and complete native loaded-provider custody",
    "independent font-body glyph selection/shaping/outlines and exact complete glyph ink",
    "unsupported SVG effects/arc/stroke profiles and any enclosure intersecting original declared clipping",
    "genuine whole-document source occurrence/native page positions and complete native ink visibility",
)


def _number(value: object) -> float:
    if not isinstance(value, str) or not re.fullmatch(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?(?:px)?", value):
        raise ValueError("original Source SVG computed geometric scalar requires independent interpretation")
    result = float(value.removesuffix("px"))
    if not math.isfinite(result) or abs(result) > 1_000_000:
        raise ValueError("original Source SVG computed geometric scalar exceeds finite bounds")
    return result


def _box(svg: SvgGeometry, element: Any) -> list[float] | None:
    local = svg.local(element)
    matrix = svg.world(element)
    if local == "path":
        path = element.get("d", "")
        if len(path) > 100_000 or re.search(r"[Aa]", path):
            raise ValueError("original Source SVG arc profile needs exact independent elliptical bounds")
        pen = BoundsPen(None)
        parse_path(path, TransformPen(pen, matrix))
        return list(pen.bounds) if pen.bounds is not None else None
    if local in {"polygon", "polyline"}:
        coords = numbers(element.get("points", ""))
        if len(coords) < 4 or len(coords) % 2:
            raise ValueError("original Source SVG point primitive differs")
        points = list(zip(coords[::2], coords[1::2], strict=True))
    elif local == "line":
        points = [
            (float(element.get("x1", "0")), float(element.get("y1", "0"))),
            (float(element.get("x2", "0")), float(element.get("y2", "0"))),
        ]
    else:
        shape = svg.shape(element)
        if shape is None:
            return None
        return list(shape["box"])
    projected = [point(matrix, item) for item in points]
    values = [coordinate for item in projected for coordinate in item]
    if any(not math.isfinite(value) or abs(value) > 1_000_000 for value in values):
        raise ValueError("original Source SVG point primitive exceeds finite coordinates")
    return [
        min(item[0] for item in projected),
        min(item[1] for item in projected),
        max(item[0] for item in projected),
        max(item[1] for item in projected),
    ]


def _enclosure(svg: SvgGeometry, element: Any, style: dict[str, Any]) -> list[float] | None:
    box = _box(svg, element)
    if box is None:
        return None
    if style.get("vectorEffect") not in {"none", ""}:
        raise ValueError("original Source SVG non-scaling stroke requires independent interpretation")
    if style.get("stroke", "none") == "none" or _number(style["strokeOpacity"]) == 0:
        return box if style.get("fill", "none") != "none" and _number(style["fillOpacity"]) > 0 else None
    width = _number(style["strokeWidth"])
    if width < 0 or width > 1000 or style.get("strokeLinecap") not in {"butt", "round", "square"}:
        raise ValueError("original Source SVG stroke width/cap requires independent interpretation")
    join = style.get("strokeLinejoin")
    if join not in {"miter", "round", "bevel"}:
        raise ValueError("original Source SVG stroke join requires independent interpretation")
    miter = _number(style["strokeMiterlimit"]) if join == "miter" else 1.0
    if not 1 <= miter <= 1000:
        raise ValueError("original Source SVG miter expansion is outside finite profile")
    # Conservative containment is sufficient only when the entire envelope is
    # inside every admitted clip. It never approves intersections or guesses a
    # smaller actual stroke from raster pixels. Curve geometry uses exact pen
    # extrema; affine expansion uses a finite matrix norm upper bound.
    a, b, c, d, _, _ = svg.world(element)
    scale_bound = math.sqrt(a * a + b * b + c * c + d * d)
    radius = width * max(miter, math.sqrt(2) if style["strokeLinecap"] == "square" else 1) * scale_bound / 2
    return [box[0] - radius, box[1] - radius, box[2] + radius, box[3] + radius]


def inspect_original_svg_ink_enclosures(svg_bytes: bytes, dom: dict[str, Any]) -> dict[str, Any]:
    """Recompute finite source envelopes; never grant remaining glyph/effect gates."""
    preflight_original_mermaid_svg(svg_bytes)
    svg = SvgGeometry(svg_bytes)
    elements = svg.elements[1:]
    rows = dom.get("rows")
    if not isinstance(rows, list) or len(rows) != len(elements) or len(rows) > 20_000:
        raise ValueError("actual original Source computed-style/XML element census differs")
    styles = {}
    for index, (element, row) in enumerate(zip(elements, rows, strict=True)):
        if row.get("index") != index or row.get("tag") != svg.local(element) or row.get("id") != element.get("id", ""):
            raise ValueError("actual original Source computed-style row identity differs from original XML")
        attrs = row.get("attributes")
        if not isinstance(attrs, dict) or any(
            attrs.get(key) != value for key, value in element.attrib.items() if "}" not in key
        ):
            raise ValueError("actual original Source computed-style row altered source XML attributes")
        style = row.get("style")
        if not isinstance(style, dict):
            raise ValueError("actual original Source computed styles are absent")
        styles[element] = style
    x, y, width, height = svg.viewbox
    viewport = [x, y, x + width, y + height]
    primitive_rows = []
    effects = []
    markers = []
    glyphs = []
    blockers = []
    root_style = dom.get("root_style")
    root_attributes = dom.get("root_attributes")
    if (
        not isinstance(root_style, dict)
        or not isinstance(root_attributes, dict)
        or {key: value for key, value in root_attributes.items() if key not in {"xmlns", "xmlns:xlink"}}
        != dict(svg.root.attrib)
    ):
        raise ValueError("actual original Source root computed-style/XML attributes differ")
    for effect in ("clipPath", "mask", "filter"):
        if root_style.get(effect) not in {"none", ""}:
            effects.append({"index": "root", "property": effect, "value": root_style.get(effect)})
    for index, element in enumerate(elements):
        local = svg.local(element)
        style = styles[element]
        if local in {"text", "tspan", "foreignObject"}:
            glyphs.append({"index": index, "tag": local, "id": element.get("id", "")})
        for effect in ("clipPath", "mask", "filter"):
            if style.get(effect) not in {"none", ""}:
                effects.append({"index": index, "property": effect, "value": style.get(effect)})
        if local not in PRIMITIVES:
            continue
        ancestor = element
        definition = False
        while ancestor is not None:
            if svg.local(ancestor) in {"defs", "marker", "clipPath", "mask", "filter"}:
                definition = True
                break
            ancestor = svg.parents.get(ancestor)
        if definition:
            continue
        try:
            envelope = _enclosure(svg, element, style)
        except ValueError as error:
            blockers.append({"index": index, "reason": str(error)})
            continue
        if envelope is None:
            continue
        contained = all(
            (
                envelope[0] >= viewport[0],
                envelope[1] >= viewport[1],
                envelope[2] <= viewport[2],
                envelope[3] <= viewport[3],
            )
        )
        primitive_rows.append(
            {
                "index": index,
                "tag": local,
                "id": element.get("id", ""),
                "source_ink_enclosure": envelope,
                "inside_original_viewbox": contained,
            }
        )
        if not contained:
            blockers.append(
                {"index": index, "reason": "independent primitive/stroke envelope intersects original root clipping"}
            )
        for marker_kind in ("marker-start", "marker-mid", "marker-end"):
            reference = element.get(marker_kind)
            if reference:
                match = re.fullmatch(r"url\(\s*['\"]?#([^)'\"\s]+)['\"]?\s*\)", reference)
                marker = svg.ids.get(match[1]) if match else None
                if marker is None or svg.local(marker) != "marker":
                    raise ValueError("original Source marker reference omits its exact local source definition")
                markers.append(
                    {
                        "index": index,
                        "attachment": marker_kind,
                        "marker_id": marker.get("id"),
                        "viewbox": marker.get("viewBox"),
                        "width": marker.get("markerWidth"),
                        "height": marker.get("markerHeight"),
                        "orientation": marker.get("orient"),
                        "definition_sha256": canonical_digest(dict(marker.attrib)),
                    }
                )
    if glyphs:
        blockers.append({"reason": "complete Source glyph outlines/shaping require genuine admitted font-body metrics"})
    if effects:
        blockers.append({"reason": "Source clip/mask/filter effects need independent finite interpretation"})
    if markers:
        blockers.append(
            {"reason": "complete Source marker ink/viewport/attachment needs independent marker clip interpretation"}
        )
    result = {
        "schema_version": SCHEMA,
        "svg_sha256": hashlib.sha256(svg_bytes).hexdigest(),
        "status": "blocked" if blockers else "finite-primitive-enclosures-observed",
        "full_source_ink_approval": False,
        "source_viewbox": viewport,
        "primitives": primitive_rows,
        "glyph_owners": glyphs,
        "effects": effects,
        "markers": markers,
        "blockers": blockers,
        "remaining_admission": list(REMAINING),
    }
    return {**result, "content_digest": canonical_digest(result)}
