"""Source-defined marker placement, viewport and conservative unclipped ink.

Definition styles come from the real SVG-only original observer. Every marker
instance has its own ordered vertex identity. No native pixel crop or marker
label supplies a transform or authorizes process/font/provider custody.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_mermaid_source_path_ink import marker_vertices, source_path_ink
from infrastructure.reporting.native_mermaid_svg_geometry import (
    IDENTITY,
    SvgGeometry,
    multiply,
    numbers,
    point,
    transform,
)

Ink = Callable[[Any, dict[str, Any], tuple[float, ...]], list[float] | None]


def source_local_reference(value: str) -> str:
    match = re.fullmatch(r"url\(\s*['\"]?([^)'\"\s]+)['\"]?\s*\)", value)
    if match is None:
        raise ValueError("Source marker/effect reference is not a finite original local URL")
    # Preflight admits only literal #references in all original SVG CSS/XML.
    # Browser computed values may make those local URLs absolute. This parser
    # interprets the already observed style; it does not grant its provenance.
    fragment = urlsplit(match[1]).fragment
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.:-]*", fragment):
        raise ValueError("Source marker/effect reference has no exact local identity")
    return fragment


def _scalar(element: Any, name: str, default: str) -> float:
    result = numbers(element.get(name, default))
    if len(result) != 1:
        raise ValueError("Source marker scalar requires its independently modeled length profile")
    return result[0]


def marker_viewport(marker: Any) -> tuple[tuple[float, ...], list[float], tuple[float, float]]:
    width, height = _scalar(marker, "markerWidth", "3"), _scalar(marker, "markerHeight", "3")
    if min(width, height) <= 0:
        raise ValueError("Source marker has a zero/negative viewport")
    box = numbers(marker.get("viewBox", f"0 0 {width} {height}"))
    if len(box) != 4 or min(box[2:]) <= 0:
        raise ValueError("Source marker viewBox is absent or degenerate")
    x, y, w, h = box
    sx, sy = width / w, height / h
    aspect = marker.get("preserveAspectRatio", "xMidYMid meet").split()
    if aspect == ["none"]:
        tx, ty = -x * sx, -y * sy
    elif len(aspect) in {1, 2} and re.fullmatch(r"x(?:Min|Mid|Max)Y(?:Min|Mid|Max)", aspect[0]):
        mode = aspect[1] if len(aspect) == 2 else "meet"
        if mode not in {"meet", "slice"}:
            raise ValueError("Source marker aspect fit is outside the finite declared profile")
        sx = sy = min(sx, sy) if mode == "meet" else max(sx, sy)
        align = {"Min": 0.0, "Mid": 0.5, "Max": 1.0}
        tx = -x * sx + (width - w * sx) * align[aspect[0][1:4]]
        ty = -y * sy + (height - h * sy) * align[aspect[0][5:8]]
    else:
        raise ValueError("Source marker preserveAspectRatio needs independent interpretation")
    view = (sx, 0.0, 0.0, sy, tx, ty)
    ref = point(view, (_scalar(marker, "refX", "0"), _scalar(marker, "refY", "0")))
    return view, [0.0, 0.0, width, height], ref


def _corners(box: list[float], matrix: tuple[float, ...]) -> list[tuple[float, float]]:
    return [point(matrix, (x, y)) for x in (box[0], box[2]) for y in (box[1], box[3])]


def source_marker_ink(
    svg: SvgGeometry,
    host: Any,
    style: dict[str, Any],
    styles: dict[Any, dict[str, Any]],
    ink: Ink,
) -> list[dict[str, Any]]:
    active = {
        key: value
        for key, value in style.items()
        if key in {"markerStart", "markerMid", "markerEnd"} and value not in {"none", ""}
    }
    if not active:
        return []
    local = svg.local(host)
    if local == "path":
        path = host.get("d", "")
    elif local in {"polygon", "polyline"}:
        coordinates = numbers(host.get("points", ""))
        if len(coordinates) < 4 or len(coordinates) % 2:
            raise ValueError("Source marker host points are incomplete")
        path = "M" + " L".join(f"{x} {y}" for x, y in zip(coordinates[::2], coordinates[1::2], strict=True))
        path += " Z" if local == "polygon" else ""
    elif local == "line":
        path = f"M{host.get('x1', '0')} {host.get('y1', '0')}L{host.get('x2', '0')} {host.get('y2', '0')}"
    else:
        raise ValueError("Source marker host shape is outside its independent vertex profile")
    result: list[dict[str, Any]] = []
    for vertex in marker_vertices(source_path_ink(path)):
        reference = active.get(vertex["attachment"])
        if reference is None:
            continue
        marker_id = source_local_reference(reference)
        marker = svg.ids.get(marker_id)
        if marker is None or svg.local(marker) != "marker":
            raise ValueError("Source marker attachment lacks its exact original definition")
        view, viewport, ref = marker_viewport(marker)
        units = marker.get("markerUnits", "strokeWidth")
        if units == "strokeWidth":
            widths = numbers(str(style["strokeWidth"]).removesuffix("px"))
            if len(widths) != 1 or widths[0] < 0 or widths[0] > 1000:
                raise ValueError("Source marker stroke-width units are outside the original finite profile")
            scale = widths[0]
        elif units == "userSpaceOnUse":
            scale = 1.0
        else:
            raise ValueError("Source marker units need independent interpretation")
        if scale == 0:
            continue  # A zero strokeWidth-scaled marker has no rendered area.
        orientation = marker.get("orient", "0")
        if orientation in {"auto", "auto-start-reverse"}:
            angle = vertex["angle"]
            if orientation == "auto-start-reverse" and vertex["attachment"] == "markerStart":
                angle += math.pi
        else:
            values = numbers(orientation.removesuffix("deg"))
            if len(values) != 1:
                raise ValueError("Source marker orientation needs its independently modeled angle profile")
            angle = math.radians(values[0])
        cosine, sine = math.cos(angle), math.sin(angle)
        rotation = (cosine, sine, -sine, cosine, *vertex["position"])
        placement = multiply(svg.world(host), multiply(rotation, (scale, 0.0, 0.0, scale, 0.0, 0.0)))
        origin = multiply(placement, (1.0, 0.0, 0.0, 1.0, -ref[0], -ref[1]))
        marker_rows = []
        for child in list(marker.iter())[1:]:
            tag = svg.local(child)
            if tag in {"title", "desc", "style"}:
                continue
            if tag not in {"g", "path", "rect", "circle", "ellipse", "line", "polyline", "polygon"}:
                raise ValueError("Source marker content has an unmodeled glyph/reference/effect primitive")
            child_style = styles[child]
            if any(child_style.get(key) not in {"none", ""} for key in ("clipPath", "mask", "filter")):
                raise ValueError("Source marker contents retain an independently unmodeled effect")
            if tag == "g":
                continue
            ancestry = []
            current = child
            while current is not marker:
                ancestry.append(current)
                current = svg.parents[current]
            local_matrix: tuple[float, ...] = IDENTITY
            for ancestor in reversed(ancestry):
                local_matrix = multiply(local_matrix, transform(ancestor.get("transform", "")))
            local_to_view = multiply(view, local_matrix)
            envelope = ink(child, child_style, local_to_view)
            if envelope is None:
                continue
            overflow = styles[marker].get("overflow")
            if overflow not in {"visible", "hidden", "clip", "scroll", "auto"}:
                raise ValueError("Source marker viewport overflow has no independently modeled profile")
            if overflow != "visible" and not (
                envelope[0] >= viewport[0]
                and envelope[1] >= viewport[1]
                and envelope[2] <= viewport[2]
                and envelope[3] <= viewport[3]
            ):
                raise ValueError("complete Source marker ink intersects its original marker viewport clipping")
            projected = _corners(envelope, origin)
            world = [
                min(p[0] for p in projected),
                min(p[1] for p in projected),
                max(p[0] for p in projected),
                max(p[1] for p in projected),
            ]
            marker_rows.append({"tag": tag, "id": child.get("id", ""), "source_ink_enclosure": world})
        if marker.get("transform"):
            raise ValueError("Source marker element transform requires independent interpretation")
        result.append(
            {
                "marker_id": marker_id,
                "attachment": vertex["attachment"],
                "vertex_ordinal": vertex["vertex_ordinal"],
                "source_position": list(vertex["position"]),
                "source_orientation_radians": angle,
                "definition_sha256": canonical_digest(dict(marker.attrib)),
                "marker_viewport": viewport,
                "local_view_matrix": list(view),
                "world_placement": list(origin),
                "source_ink": marker_rows,
            }
        )
    return result
