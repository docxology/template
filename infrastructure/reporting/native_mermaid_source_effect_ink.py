"""Finite original rectangular clip, opaque mask and identity filter profiles.

Containment tests the entire independently derived ink enclosure. Intersections
are refused, never cropped or waived using target pixels. Unsupported effect
definitions remain exact Source identity failures, rather than generic approval.
"""

from __future__ import annotations

from typing import Any

from infrastructure.reporting.native_mermaid_source_marker_ink import source_local_reference
from infrastructure.reporting.native_mermaid_svg_geometry import SvgGeometry, multiply, numbers, point, transform


def _scalar(element: Any, key: str) -> float:
    values = numbers(element.get(key, "0"))
    if len(values) != 1:
        raise ValueError("Source effect region has an unmodeled percentage/length scalar")
    return values[0]


def _rect(element: Any, matrix: tuple[float, ...]) -> list[tuple[float, float]]:
    x, y, width, height = (_scalar(element, key) for key in ("x", "y", "width", "height"))
    if min(width, height) <= 0 or element.get("rx", "0") != "0" or element.get("ry", "0") != "0":
        raise ValueError("Source effect rectangle is empty, rounded or independently unmodeled")
    return [point(matrix, p) for p in ((x, y), (x + width, y), (x + width, y + height), (x, y + height))]


def _contains(polygon: list[tuple[float, float]], box: list[float]) -> bool:
    area = sum(
        left[0] * right[1] - left[1] * right[0] for left, right in zip(polygon, polygon[1:] + polygon[:1], strict=True)
    )
    if area == 0:
        raise ValueError("Source effect clip has a collapsed actual transform")
    sign = 1 if area > 0 else -1
    for x in (box[0], box[2]):
        for y in (box[1], box[3]):
            for left, right in zip(polygon, polygon[1:] + polygon[:1], strict=True):
                if sign * ((right[0] - left[0]) * (y - left[1]) - (right[1] - left[1]) * (x - left[0])) < 0:
                    return False
    return True


def _definition_matrix(svg: SvgGeometry, root: Any, child: Any) -> tuple[float, ...]:
    ancestry = []
    while child is not root:
        ancestry.append(child)
        child = svg.parents[child]
    matrix = transform(root.get("transform", ""))
    for ancestor in reversed(ancestry):
        matrix = multiply(matrix, transform(ancestor.get("transform", "")))
    return matrix


def source_effect_containment(
    svg: SvgGeometry,
    element: Any,
    styles: dict[Any, dict[str, Any]],
    box: list[float],
) -> list[dict[str, Any]]:
    """Interpret each actually applied ancestor effect against whole Source ink."""
    result: list[dict[str, Any]] = []
    host = element
    while host is not None:
        for property_name, expected in (("clipPath", "clipPath"), ("mask", "mask"), ("filter", "filter")):
            value = styles[host].get(property_name)
            if value in {"none", ""}:
                continue
            if not isinstance(value, str):
                raise ValueError("Source effect computed reference is absent or not literal")
            identity = source_local_reference(value)
            definition = svg.ids.get(identity)
            if definition is None or svg.local(definition) != expected:
                raise ValueError("Source effect lacks its exact original definition: " + identity)
            matrix = svg.world(host)
            definition_nodes = list(definition.iter())
            for node in definition_nodes:
                node_style = styles[node]
                if any(node_style.get(key) not in {"none", ""} for key in ("clipPath", "mask", "filter")):
                    raise ValueError("Source effect definition contains an unmodeled nested effect: " + identity)
                if node_style.get("opacity") != "1":
                    raise ValueError("Source effect definition has unmodeled ancestor opacity: " + identity)
                if svg.local(node) in {"g", "rect"} and node_style.get("_actual_visible") is not True:
                    raise ValueError("Source effect definition display/visibility is unmodeled or hidden: " + identity)
            shapes = [child for child in definition_nodes[1:] if svg.local(child) not in {"g", "title", "desc"}]
            if property_name == "filter":
                if definition.get("filterUnits", "objectBoundingBox") != "userSpaceOnUse":
                    raise ValueError(
                        "Source filter object bounding-box region requires independent host bounds: " + identity
                    )
                if not _contains(_rect(definition, matrix), box):
                    raise ValueError("complete Source ink intersects original filter region: " + identity)
                for child in shapes:
                    tag = svg.local(child)
                    if tag == "feColorMatrix":
                        if child.get("type", "matrix") != "matrix" or numbers(child.get("values", "")) != [
                            1,
                            0,
                            0,
                            0,
                            0,
                            0,
                            1,
                            0,
                            0,
                            0,
                            0,
                            0,
                            1,
                            0,
                            0,
                            0,
                            0,
                            0,
                            1,
                            0,
                        ]:
                            raise ValueError(
                                "Source filter changes ink and needs exact independent kernel interpretation: "
                                + identity
                            )
                    elif tag == "feComponentTransfer":
                        if any(c.get("type", "identity") != "identity" for c in child):
                            raise ValueError("Source filter transfer changes ink: " + identity)
                    elif tag not in {"feFuncR", "feFuncG", "feFuncB", "feFuncA"}:
                        raise ValueError("Source filter has an unmodeled consumed primitive: " + identity + ":" + tag)
                    if any(key in child.attrib for key in ("x", "y", "width", "height", "in")):
                        raise ValueError(
                            "Source filter subregion/input requires independent interpretation: " + identity
                        )
            else:
                units = "clipPathUnits" if property_name == "clipPath" else "maskContentUnits"
                if definition.get(units, "userSpaceOnUse") != "userSpaceOnUse":
                    raise ValueError(
                        "Source effect object bounding-box coordinates require exact host bounds: " + identity
                    )
                if not shapes or any(svg.local(child) != "rect" for child in shapes):
                    raise ValueError("Source effect has an unmodeled non-rectangular contour: " + identity)
                regions = []
                for child in shapes:
                    child_style = styles[child]
                    if child_style.get("_actual_visible") is not True:
                        raise ValueError("Source effect rectangle has no actually visible whole region: " + identity)
                    if any(child_style.get(key) not in {"none", ""} for key in ("clipPath", "mask", "filter")):
                        raise ValueError("Source effect definition contains an unmodeled nested effect: " + identity)
                    if property_name == "mask" and (
                        child_style.get("fill")
                        not in {"rgb(255, 255, 255)", "rgba(255, 255, 255, 1)", "white", "#ffffff"}
                        or child_style.get("fillOpacity") != "1"
                        or child_style.get("opacity") != "1"
                        or child_style.get("stroke") != "none"
                    ):
                        raise ValueError(
                            "Source mask is not a whole opaque-white independently modeled region: " + identity
                        )
                    child_matrix = multiply(matrix, _definition_matrix(svg, definition, child))
                    regions.append(_rect(child, child_matrix))
                if not any(_contains(region, box) for region in regions):
                    raise ValueError("complete Source ink intersects original effect clipping: " + identity)
                if property_name == "mask":
                    if definition.get("maskUnits", "objectBoundingBox") != "userSpaceOnUse":
                        raise ValueError(
                            "Source mask default region requires independent host bounding-box bounds: " + identity
                        )
                    if not _contains(_rect(definition, matrix), box):
                        raise ValueError("complete Source ink intersects original mask region: " + identity)
            result.append({"property": property_name, "definition_id": identity, "complete_ink_contained": True})
        host = svg.parents.get(host)
    return result
