"""Independent original-source graph witnesses for all five Mermaid families.

Source is compiled independently; XML labels, node shapes, endpoint coordinates,
message order, class members and actual marker primitives are decoded here.
Native paint/fonts/process custody and genuine controls are additional gates.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from typing import Any

from infrastructure.reporting.native_format_pdf_mermaid_source import (
    compile_original_mermaid_source,
)
from infrastructure.reporting.native_mermaid_svg_geometry import (
    SvgGeometry,
    boundary_distance,
    numbers,
    path_geometry,
    point,
)

SCHEMA = "template-native-mermaid-independent-svg-topology-v1"


def _plain(value: str) -> str:
    return " ".join(value.split())


def _texts(svg: SvgGeometry, group: Any) -> list[str]:
    def text(element: Any) -> str:
        result = element.text or ""
        for child in element:
            result += " " if svg.local(child) == "br" else text(child)
            result += child.tail or ""
        return result

    return [
        _plain(text(element))
        for element in group.iter()
        if svg.local(element) in {"text", "p", "foreignObject"}
        and not (
            svg.local(element) == "foreignObject"
            and any(svg.local(child) in {"text", "p"} for child in element.iter() if child is not element)
        )
        and _plain(text(element))
    ]


def _marker(svg: SvgGeometry, edge: Any, end: str) -> dict[str, Any]:
    reference = edge.get(f"marker-{end}", "")
    match = re.fullmatch(r"url\(\s*[\"']?#([^\s\"')]+)[\"']?\s*\)", reference)
    marker = svg.ids.get(match[1]) if match else None
    if marker is None or svg.local(marker) != "marker":
        raise ValueError("source arrow/cardinality omitted its actual local marker")
    orient = marker.get("orient")
    if orient not in {"auto", "auto-start-reverse"}:
        orientation = numbers(orient or "0")
        if len(orientation) != 1:
            raise ValueError("source marker orientation syntax differs")
    paths = [path_geometry(element.get("d", "")) for element in marker.iter() if svg.local(element) == "path"]
    circles = [
        [numbers(element.get(key, "0"))[0] for key in ("cx", "cy", "r")]
        for element in marker.iter()
        if svg.local(element) == "circle"
    ]
    if not paths and not circles:
        raise ValueError("source marker has no independent graphic primitive")
    refx = numbers(marker.get("refX", "0"))[0]
    xs = [p[0] for path in paths for p in path["endpoints"]]
    width = numbers(marker.get("markerWidth", "0"))[0]
    height = numbers(marker.get("markerHeight", "0"))[0]
    if min(width, height) <= 0 or max(width, height) > 1000:
        raise ValueError("source marker has invalid finite dimensions")
    return {
        "id": marker.get("id"),
        "orientation": orient,
        "paths": paths,
        "circles": circles,
        "attachment_margin": max([abs(x - refx) for x in xs] + [0]) + 4,
    }


def _arrow(marker: dict[str, Any]) -> bool:
    """Recognize a real right-pointing arrowhead/barb, including concave barbs."""
    if marker["orientation"] not in {"auto", "auto-start-reverse"} or marker["circles"] or len(marker["paths"]) != 1:
        return False
    points = marker["paths"][0]["endpoints"]
    if len(points) > 1 and points[0] == points[-1]:
        points = points[:-1]
    if not 3 <= len(points) <= 5:
        return False
    xmax = max(p[0] for p in points)
    tips = [p for p in points if p[0] == xmax]
    return len(tips) == 1 and min(p[1] for p in points) < tips[0][1] < max(p[1] for p in points)


def _cardinality(marker: dict[str, Any]) -> str:
    """Decode bars, optional-circle and crowfoot curves, not their DOM names."""
    paths = marker["paths"]
    if marker["orientation"] != "auto":
        return "unsupported"
    segments = [segment for path in paths for segment in path["segments"]]
    bars = [(a, b) for a, b in segments if a[0] == b[0] and a[1] != b[1]]
    curved = sum(command[0] == "Q" for path in paths for command in path["commands"])
    circles = marker["circles"]
    if len(circles) > 1 or any(circle[2] <= 0 for circle in circles):
        return "unsupported"
    if curved == 0 and len(bars) == 2 and not circles and len(segments) == 2:
        return "one"
    if curved == 0 and len(bars) == 1 and len(circles) == 1 and len(segments) == 1:
        return "optional-one"
    if curved == 2 and len(bars) == 1 and not circles:
        return "one-or-more"
    if curved == 2 and len(bars) == 0 and len(circles) == 1:
        return "zero-or-more"
    return "unsupported"


def _member_display(source: str) -> str:
    """Keep visibility/name/type/parameters; only explicit method colon syntax changes."""
    source = re.sub(r"([A-Za-z_][A-Za-z0-9_]*)~([^~]+)~", r"\1<\2>", source)
    if "~" in source[1:]:
        raise ValueError("original class generic nesting requires independent interpretation")
    method = re.fullmatch(r"([+#~-])([^()]*)\(([^()]*)\)\s+([^$*]+)", source)
    return _plain(f"{method[1]}{method[2]}({method[3]}) : {method[4]}") if method else _plain(source)


def inspect_original_mermaid_svg(source: bytes, data: bytes) -> dict[str, Any]:
    """Crosscheck independently compiled source against actual bounded SVG graph."""
    graph = compile_original_mermaid_source(source)
    svg = SvgGeometry(data)
    findings = []
    witnesses = []
    blockers = []
    frames = {}
    groups = {}

    def finding(code: str, **details: Any) -> None:
        findings.append({"code": "mermaid.source." + code, **details})

    family = graph["family"]
    try:
        for node in graph["nodes"]:
            identity = node["identity"]
            if family == "sequenceDiagram":
                candidates = [
                    e for e in svg.elements if e.get("data-et") == "participant" and e.get("data-id") == identity
                ]
                candidates = sorted(candidates, key=lambda e: svg.frame(e)["box"][1])[:1]
            else:
                prefix = {
                    "flowchart": "flowchart",
                    "classDiagram": "classId",
                    "stateDiagram-v2": "state",
                    "erDiagram": "entity",
                }[family]
                candidates = [
                    e
                    for e in svg.elements
                    if svg.local(e) == "g"
                    and re.search(rf"(?:^|-){prefix}-{re.escape(identity)}-\d+$", e.get("id", ""))
                ]
            if len(candidates) != 1:
                finding("node", identity=identity, count=len(candidates))
                continue
            group = candidates[0]
            frame = svg.frame(group)
            texts = _texts(svg, group)
            if _plain(node["label"]) not in texts:
                finding("label", identity=identity, label=node["label"])
            shape = node["shape"]
            if shape in {"diamond", "hexagon"}:
                primitive = [svg.shape(e) for e in group.iter() if svg.local(e) == "polygon"]
                sizes = [len(s["points"]) for s in primitive if s]
                if (4 if shape == "diamond" else 6) not in sizes:
                    finding("shape", identity=identity, shape=shape)
            elif shape in {"rectangle", "class", "entity", "participant"} and frame["primitive"] not in {
                "rect",
                "path",
            }:
                finding("shape", identity=identity, shape=shape)
            members = node.get("members", [])
            expected = Counter(_member_display(member) for member in members)
            actual = Counter(text for text in texts if text.startswith(("+", "#", "~", "-")))
            if expected and expected != actual:
                finding(
                    "member",
                    identity=identity,
                    expected=dict(expected),
                    observed=dict(actual),
                )
            for key, value in node.get("style", {}).items():
                choices = [e.get(key, "") for e in group.iter()]
                choices.extend(
                    match[1].strip().removesuffix("!important").strip().lower()
                    for e in group.iter()
                    for match in re.finditer(rf"(?:^|;)\s*{re.escape(key)}\s*:\s*([^;]+)", e.get("style", ""))
                )
                if value not in choices:
                    finding("style", identity=identity, property=key, value=value)
            x, y, w, h = svg.viewbox
            box = frame["box"]
            if box[0] < x - 1 or box[1] < y - 1 or box[2] > x + w + 1 or box[3] > y + h + 1:
                finding("clipped_node", identity=identity, box=box)
            frames[identity] = frame
            groups[identity] = group
            witnesses.append(
                {
                    "kind": "node",
                    "source_identity": identity,
                    "svg_id": group.get("id"),
                    "frame": frame,
                    "labels": texts,
                    "members": dict(expected),
                }
            )
        if family == "stateDiagram-v2":
            for endpoint, token in (("$start", "start"), ("$end", "end")):
                if not any(edge["from"] == endpoint or edge["to"] == endpoint for edge in graph["edges"]):
                    continue
                candidates = [
                    e
                    for e in svg.elements
                    if svg.local(e) == "g" and re.search(rf"^state-.*_{token}-\d+$", e.get("id", ""))
                ]
                if len(candidates) != 1:
                    finding("state_endpoint", endpoint=endpoint, count=len(candidates))
                    continue
                frames[endpoint] = svg.frame(candidates[0])
                groups[endpoint] = candidates[0]
                circles = [e for e in candidates[0].iter() if svg.local(e) == "circle"]
                if not circles or (endpoint == "$end" and len(circles) < 2):
                    finding("state_endpoint", endpoint=endpoint)
        if family == "sequenceDiagram":
            _sequence(svg, graph, frames, finding, witnesses)
        else:
            prefix = {
                "flowchart": "flowchart",
                "classDiagram": "classId",
                "stateDiagram-v2": "state",
                "erDiagram": "entity",
            }[family]
            actual_groups = [
                e
                for e in svg.elements
                if svg.local(e) == "g" and re.search(rf"(?:^|-){prefix}-.+-\d+$", e.get("id", ""))
            ]
            if len(actual_groups) != len(groups):
                finding("node_count", expected=len(groups), observed=len(actual_groups))
            _graph_edges(svg, graph, frames, groups, finding, witnesses)
        if graph["direction"]:
            order = {node["identity"]: index for index, node in enumerate(graph["nodes"])}
            for ordinal, edge in enumerate(graph["edges"]):
                left, right = edge["from"], edge["to"]
                if left not in frames or right not in frames or order[left] >= order[right]:
                    continue
                a, b = frames[left]["box"], frames[right]["box"]
                axis = 0 if graph["direction"] in {"LR", "RL"} else 1
                delta = (b[axis] + b[axis + 2] - a[axis] - a[axis + 2]) / 2
                sign = -1 if graph["direction"] in {"RL", "BT"} else 1
                if delta * sign <= 0:
                    finding("direction", ordinal=ordinal, direction=graph["direction"])
                witnesses.append(
                    {
                        "kind": "direction",
                        "ordinal": ordinal,
                        "direction": graph["direction"],
                        "source_axis_delta": delta,
                    }
                )
    except (ValueError, KeyError, IndexError, TypeError) as error:
        blockers.append(f"{family} actual SVG geometry: {error}")
    return {
        "schema_version": SCHEMA,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "svg_sha256": hashlib.sha256(data).hexdigest(),
        "source_graph": graph,
        "status": "failed" if findings else "blocked" if blockers else "pass",
        "findings": findings,
        "blockers": blockers,
        "witnesses": witnesses,
        "assurance": (
            "independent source/SVG graph geometry; native paint/font/process custody and genuine controls required"
        ),
    }


def _graph_edges(
    svg: SvgGeometry,
    graph: dict[str, Any],
    frames: dict,
    groups: dict,
    finding: Any,
    witnesses: list,
) -> None:
    candidates = []
    for element in svg.elements:
        if svg.local(element) != "path" or not (element.get("marker-end") or element.get("marker-start")):
            continue
        ancestor = element
        definition = False
        while ancestor is not None:
            if svg.local(ancestor) in {"defs", "marker"}:
                definition = True
                break
            ancestor = svg.parents.get(ancestor)
        if not definition:
            candidates.append(element)
    if len(candidates) != len(graph["edges"]):
        finding("edge_count", expected=len(graph["edges"]), observed=len(candidates))
    consumed = set()
    for ordinal, edge in enumerate(graph["edges"]):
        start, end = edge["from"], edge["to"]
        if start not in frames or end not in frames:
            continue
        matches = []
        for index, element in enumerate(candidates):
            if index in consumed:
                continue
            geometry = svg.edge_points(element)
            start_marker = _marker(svg, element, "start") if element.get("marker-start") else None
            end_marker = _marker(svg, element, "end") if element.get("marker-end") else None
            start_margin = start_marker["attachment_margin"] if start_marker else 4
            end_margin = end_marker["attachment_margin"] if end_marker else 4
            # Margins derive from the actual marker's refX/tip extent. They are
            # source-unit attachment geometry, never a relaxed pixel tolerance.
            starts = {name: boundary_distance(frame, geometry["start"]) for name, frame in frames.items()}
            ends = {name: boundary_distance(frame, geometry["end"]) for name, frame in frames.items()}
            if (
                min(starts, key=lambda name: starts[name]) == start
                and min(ends, key=lambda name: ends[name]) == end
                and starts[start] <= start_margin
                and ends[end] <= end_margin
            ):
                matches.append((index, element, geometry, start_marker, end_marker))
        if len(matches) != 1:
            finding("edge", ordinal=ordinal, source_edge=edge, count=len(matches))
            continue
        index, element, geometry, start_marker, end_marker = matches[0]
        consumed.add(index)
        if graph["family"] == "erDiagram":
            cards = {
                "||": "one",
                "o|": "optional-one",
                "|o": "optional-one",
                "o{": "zero-or-more",
                "}o": "zero-or-more",
                "|{": "one-or-more",
                "}|": "one-or-more",
            }
            if not start_marker or _cardinality(start_marker) != cards[edge["from_cardinality"]]:
                finding("cardinality", ordinal=ordinal, end="from")
            if not end_marker or _cardinality(end_marker) != cards[edge["to_cardinality"]]:
                finding("cardinality", ordinal=ordinal, end="to")
        elif not end_marker or not _arrow(end_marker):
            finding("arrow", ordinal=ordinal)
        label = edge["label"]
        if label:
            identity = element.get("data-id", element.get("id", ""))
            labels = [e for e in svg.elements if e.get("data-id") == identity and e is not element]
            if not any(_plain(label) in _texts(svg, e) for e in labels):
                finding("edge_label", ordinal=ordinal, label=label)
        cardinal = edge.get("to_cardinality", "") if graph["family"] == "classDiagram" else ""
        terminal_witness = None
        if cardinal:
            terminals = [e for e in svg.elements if "edgeTerminals" in e.get("class", "").split()]
            bound = []
            for terminal in terminals:
                if _texts(svg, terminal) != [cardinal]:
                    continue
                anchor = point(svg.world(terminal), (0.0, 0.0))
                endpoint_distances = [math.dist(anchor, svg.edge_points(item)["end"]) for item in candidates]
                closest = min(endpoint_distances)
                # Original Mermaid positions terminal text near its edge end.
                # Require a unique physical binding; a global '*' cannot stand
                # in for any other relationship's cardinality.
                if endpoint_distances[index] != closest or endpoint_distances.count(closest) != 1:
                    continue
                # Mermaid 12 calcTerminalLabelPosition uses a 25 + 10
                # path distance, half that displacement, 10 + 10/2 normal
                # offset and a (-5,-5) translation at the end. The triangle
                # inequality bounds attachment independently of label text.
                source_geometry_bound = (25 + 10) / 2 + (10 + 10 / 2) + math.sqrt(50)
                if closest > source_geometry_bound:
                    continue
                bound.append({"anchor": anchor, "distance": closest, "cardinality": cardinal})
            if len(bound) != 1:
                finding("class_cardinality", ordinal=ordinal, cardinality=cardinal)
            else:
                terminal_witness = bound[0]
        witnesses.append(
            {
                "kind": "edge",
                "ordinal": ordinal,
                "source_edge": edge,
                "svg_id": element.get("data-id", element.get("id")),
                "geometry": geometry,
                "start_marker": start_marker,
                "end_marker": end_marker,
                "class_terminal": terminal_witness,
            }
        )


def _sequence(svg: SvgGeometry, graph: dict[str, Any], frames: dict, finding: Any, witnesses: list) -> None:
    lines = [e for e in svg.elements if e.get("data-et") == "message"]
    if len(lines) != len(graph["edges"]):
        finding("edge_count", expected=len(graph["edges"]), observed=len(lines))
    previous = -math.inf
    texts = [e for e in svg.elements if "messageText" in e.get("class", "").split()]
    for ordinal, (edge, line) in enumerate(zip(graph["edges"], lines)):
        geometry = svg.edge_points(line)
        marker = _marker(svg, line, "end")
        if line.get("data-from") != edge["from"] or line.get("data-to") != edge["to"]:
            finding("edge", ordinal=ordinal, source_edge=edge)
        for key, endpoint in (("from", "start"), ("to", "end")):
            frame = frames.get(edge[key])
            if not frame:
                continue
            center = (frame["box"][0] + frame["box"][2]) / 2
            if abs(geometry[endpoint][0] - center) > marker["attachment_margin"]:
                finding("message_endpoint", ordinal=ordinal, end=key)
        y = geometry["start"][1]
        if y <= previous or geometry["end"][1] != y:
            finding("message_order", ordinal=ordinal)
        previous = y
        dashed = bool(re.search(r"stroke-dasharray\s*:\s*[\d.]+", line.get("style", "")))
        if dashed != (edge["arrow"] == "-->>") or not _arrow(marker):
            finding("arrow", ordinal=ordinal)
        if ordinal >= len(texts) or _plain(edge["label"]) not in _texts(svg, texts[ordinal]):
            finding("edge_label", ordinal=ordinal, label=edge["label"])
        witnesses.append(
            {
                "kind": "message",
                "ordinal": ordinal,
                "source_edge": edge,
                "geometry": geometry,
                "marker": marker,
            }
        )
