"""Finite independent Mermaid source grammar and bounded SVG interpretation.

This grammar covers the actual configured fences. It never accepts arbitrary
Mermaid statements, metadata-only edges, or an unsupported SVG topology.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from defusedxml.ElementTree import fromstring

_ID = r"[A-Za-z][A-Za-z0-9_]*"
_NODE = rf"({_ID})(?:\[([^\[\]\n]+)\]|\{{([^{{}}\n]+)\}})?"


def mermaid_source_semantics(source: str) -> dict[str, Any]:
    """Preserve every admitted node, member, endpoint, arrow and edge label."""
    if len(source.encode()) > 64 * 1024:
        raise ValueError("Office Mermaid DSL exceeds its finite source budget")
    lines = [line.strip() for line in source.splitlines() if line.strip()]
    if not lines or len(lines) > 1000:
        raise ValueError("Office Mermaid DSL has invalid bounded line count")
    first, *body = lines
    nodes: dict[str, dict[str, Any]] = {}
    edges = []
    members = []

    def node(identifier: str, label: str | None = None, shape: str = "rect") -> None:
        value = {"id": identifier, "label": label or identifier, "shape": shape}
        if identifier in nodes and label and nodes[identifier] != value:
            raise ValueError("Office Mermaid source redeclares a node with changed semantics")
        if identifier not in nodes or label:
            nodes[identifier] = value

    def edge(start: str, end: str, arrow: str, label: str = "") -> None:
        edges.append({"start": start, "end": end, "arrow": arrow, "label": label})

    flow = re.fullmatch(r"(?:flowchart|graph) (LR|TD)", first)
    if flow:
        kind, direction = "flowchart", flow[1]
        pattern = re.compile(rf"{_NODE}\s+-->\s*(?:\|([^|\n]+)\|\s*)?{_NODE}")
        for line in body:
            match = pattern.fullmatch(line)
            if not match:
                raise ValueError("Office Mermaid flowchart contains an unsupported statement")
            start, rectangular, diamond, label, end, end_rect, end_diamond = match.groups()
            node(start, rectangular or diamond, "diamond" if diamond else "rect")
            node(end, end_rect or end_diamond, "diamond" if end_diamond else "rect")
            edge(start, end, "-->", label or "")
    elif first == "sequenceDiagram":
        kind, direction = "sequence", "LR"
        for line in body:
            participant = re.fullmatch(rf"participant ({_ID})", line)
            message = re.fullmatch(rf"({_ID})\s+(->>|-->>)\s+({_ID}):\s*(.+)", line)
            if participant:
                node(participant[1], shape="participant")
            elif message:
                if message[1] not in nodes or message[3] not in nodes:
                    raise ValueError("Office Mermaid sequence message has no declared participant")
                edge(message[1], message[3], message[2], message[4])
            else:
                raise ValueError("Office Mermaid sequence contains an unsupported statement")
    elif first == "stateDiagram-v2":
        kind, direction = "state", "TD"
        for line in body:
            match = re.fullmatch(rf"({_ID}|\[\*\])\s+-->\s+({_ID}|\[\*\])(?::\s*(.+))?", line)
            if not match:
                raise ValueError("Office Mermaid state diagram contains an unsupported statement")
            start = "__start__" if match[1] == "[*]" else match[1]
            end = "__end__" if match[2] == "[*]" else match[2]
            node(start, shape="start" if start == "__start__" else "state")
            node(end, shape="end" if end == "__end__" else "state")
            edge(start, end, "-->", match[3] or "")
    elif first == "classDiagram":
        kind, direction, current = "class", "TD", None
        for line in body:
            declaration = re.fullmatch(rf"class ({_ID}) \{{", line)
            relation = re.fullmatch(rf"({_ID}) --> ({_ID})\s*:\s*(.+)", line)
            if declaration and current is None:
                current = declaration[1]
                node(current, shape="class")
            elif line == "}" and current is not None:
                current = None
            elif current is not None and re.fullmatch(r"\+(?:str [A-Za-z_]+|[A-Za-z_]+\(\) str)", line):
                members.append({"class": current, "declaration": line})
            elif relation and current is None:
                node(relation[1], shape="class")
                node(relation[2], shape="class")
                edge(relation[1], relation[2], "-->", relation[3])
            else:
                raise ValueError("Office Mermaid class diagram contains an unsupported statement")
        if current is not None:
            raise ValueError("Office Mermaid class body has no closing brace")
    elif first == "erDiagram":
        kind, direction = "er", "TD"
        for line in body:
            match = re.fullmatch(rf"({_ID}) (\|\|--o\{{|\|\|--\|\|) ({_ID})\s*:\s*(.+)", line)
            if not match:
                raise ValueError("Office Mermaid ER diagram contains an unsupported relationship")
            node(match[1], shape="entity")
            node(match[3], shape="entity")
            edge(match[1], match[3], match[2], match[4])
    else:
        raise ValueError("Office Mermaid source diagram kind is unsupported")
    if not nodes or not edges:
        raise ValueError("Office Mermaid source omitted nodes or relationships")
    return {
        "schema_version": "template-native-office-mermaid-semantics-v1",
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "kind": kind,
        "direction": direction,
        "nodes": list(nodes.values()),
        "edges": edges,
        "members": members,
    }


def inspect_mermaid_svg_source(source: str, svg: bytes) -> dict[str, Any]:
    """Bind source labels and flowchart endpoint paths to actual SVG elements.

    Remaining diagram kinds have explicit topology blockers. SVG semantics
    alone never establish raster ink, visibility, marker orientation or layout.
    """
    semantics = mermaid_source_semantics(source)
    if len(svg) > 8 * 1024 * 1024:
        raise ValueError("Office Mermaid SVG exceeds its finite byte budget")
    tree = fromstring(svg)
    elements = list(tree.iter())
    if tree.tag != "{http://www.w3.org/2000/svg}svg" or len(elements) > 100_000:
        raise ValueError("Office Mermaid SVG has invalid bounded structure")
    for element in elements:
        local = element.tag.rsplit("}", 1)[-1]
        if local in {"script", "iframe", "object", "embed", "image", "img", "video", "audio", "a"}:
            raise ValueError("Office Mermaid SVG contains an unsupported active/external element")
        for key, value in element.attrib.items():
            if key.rsplit("}", 1)[-1].lower().startswith("on"):
                raise ValueError("Office Mermaid SVG contains an active event attribute")
            if key.rsplit("}", 1)[-1] == "href" and not value.startswith("#"):
                raise ValueError("Office Mermaid SVG contains an external reference")
            if any(not item.strip(" \t\r\n\"'").startswith("#") for item in re.findall(r"url\(([^)]+)\)", value)):
                raise ValueError("Office Mermaid SVG contains an external URL")
        if local == "style":
            stylesheet = element.text or ""
            if re.search(r"@import", stylesheet, re.I) or any(
                not item.strip(" \t\r\n\"'").startswith("#") for item in re.findall(r"url\(([^)]+)\)", stylesheet, re.I)
            ):
                raise ValueError("Office Mermaid SVG stylesheet contains an external resource")
    labels = [
        " ".join("".join(element.itertext()).split())
        for element in elements
        if element.tag.rsplit("}", 1)[-1] in {"text", "foreignObject"}
    ]
    expected = [node["label"] for node in semantics["nodes"] if node["shape"] not in {"start", "end"}]
    expected.extend(edge["label"] for edge in semantics["edges"] if edge["label"])
    findings = [{"code": "office.mermaid.source_label", "label": label} for label in expected if label not in labels]
    blockers = []
    paths = []
    if semantics["kind"] == "flowchart":
        for edge in semantics["edges"]:
            matches = [
                element
                for element in elements
                if element.tag.rsplit("}", 1)[-1] == "path"
                and (
                    {f"LS-{edge['start']}", f"LE-{edge['end']}"} <= set(element.get("class", "").split())
                    or re.fullmatch(
                        rf"L_{re.escape(edge['start'])}_{re.escape(edge['end'])}_\d+",
                        element.get("data-id", element.get("id", "")),
                    )
                )
            ]
            if len(matches) != 1 or not matches[0].get("d") or not matches[0].get("marker-end"):
                findings.append({"code": "office.mermaid.source_edge", "edge": edge})
            else:
                paths.append({"edge": edge, "d": matches[0].get("d"), "marker_end": matches[0].get("marker-end")})
        blockers.append(
            "flowchart marker orientation, node/path geometry and actual decoded ink require native controls"
        )
    else:
        blockers.append(
            f"{semantics['kind']} SVG endpoint/cardinality/member topology requires independent interpretation"
        )
    if semantics["members"]:
        blockers.append("class member types, visibility and method signatures require independent SVG binding")
    return {
        "schema_version": "template-native-office-mermaid-svg-source-v1",
        "status": "failed" if findings else "blocked" if blockers else "observed",
        "svg_sha256": hashlib.sha256(svg).hexdigest(),
        "source_semantics": semantics,
        "labels": labels,
        "endpoint_paths": paths,
        "findings": findings,
        "blockers": blockers,
    }
