"""Bounded independent current Mermaid source semantics, never writer parity.

Interpret each original source line into literal nodes, typed class members,
direction, transitions, message order and ER cardinalities. Unknown directives
remain refused. Original mmdc/Node/Chrome/font custody and every native diagram
pixel/occurrence are additional obligations, not supplied by this source parser.
"""

from __future__ import annotations

import hashlib
import html
import re
from typing import Any

SCHEMA = "template-native-pdf-independent-mermaid-source-v1"
IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"
IDENTITY = re.compile(IDENTIFIER + r"\Z")


def _label(value: str) -> str:
    value = value.strip()
    if value.startswith('"'):
        if len(value) < 2 or not value.endswith('"'):
            raise ValueError("Mermaid original quoted label is unterminated")
        value = value[1:-1]
    if re.search(r"<(?!br\s*/?>)[A-Za-z!/]|\{\{|\}\}", value):
        raise ValueError("Mermaid original label contains unsupported markup/variable semantics")
    value = re.sub(r"<br\s*/?>", "\n", value).replace(r"\n", "\n")
    return html.unescape(value)


def compile_original_mermaid_source(source: bytes) -> dict[str, Any]:
    """Interpret the five diagram families actually present in current PDFs."""
    if not source or len(source) > 64 * 1024:
        raise ValueError("original Mermaid source exceeds its finite byte bound")
    text = source.decode("utf-8")
    if re.search(r"(?m)^\s*%%\s*\{", text):
        raise ValueError("original Mermaid init/config directive requires independent source policy admission")
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("%%")]
    if not lines or len(lines) > 2000:
        raise ValueError("original Mermaid source line census is empty/unbounded")
    header = lines.pop(0)
    flow = re.fullmatch(r"(flowchart|graph) (LR|RL|TB|TD|BT)", header)
    if flow:
        family, direction = "flowchart", flow[2]
    elif header in {"classDiagram", "stateDiagram-v2", "sequenceDiagram", "erDiagram"}:
        family, direction = header, None
    else:
        raise ValueError("original Mermaid family/direction requires independent interpretation")
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    styles: dict[str, dict[str, str]] = {}
    assignments: dict[str, str] = {}
    current_class: str | None = None

    def node(identity: str, label: str | None = None, shape: str = "default") -> str:
        if IDENTITY.fullmatch(identity) is None:
            raise ValueError("original Mermaid node identity is not literal")
        old = nodes.get(identity)
        if old is None:
            nodes[identity] = {
                "identity": identity,
                "label": identity if label is None else _label(label),
                "shape": shape,
            }
        elif label is not None:
            actual = _label(label)
            if old["label"] != identity and (old["label"] != actual or old["shape"] != shape):
                raise ValueError("original Mermaid node repeats conflicting semantics")
            old.update(label=actual, shape=shape)
        return identity

    def flow_node(raw: str) -> str:
        raw = raw.strip()
        match = re.fullmatch(rf"({IDENTIFIER})(?:\[(.*)\]|\{{\{{(.*)\}}\}}|\{{(.*)\}})?", raw)
        if match is None:
            raise ValueError("original Mermaid flow node shape requires independent interpretation")
        shape = "default"
        label = None
        for index, candidate in enumerate(match.groups()[1:]):
            if candidate is not None:
                label, shape = candidate, ("rectangle", "hexagon", "diamond")[index]
        return node(match[1], label, shape)

    for index, line in enumerate(lines):
        if len(nodes) > 1000 or len(edges) > 2000:
            raise ValueError("original Mermaid node/edge census exceeds finite bounds")
        if family == "flowchart":
            style = re.fullmatch(rf"classDef ({IDENTIFIER}) (.+)", line)
            assignment = re.fullmatch(rf"class ((?:{IDENTIFIER})(?:,{IDENTIFIER})*) ({IDENTIFIER})", line)
            if style:
                if style[1] in styles:
                    raise ValueError("original Mermaid repeats a style identity")
                fields = {}
                for field in style[2].split(","):
                    key, separator, value = field.partition(":")
                    if (
                        not separator
                        or key not in {"fill", "stroke", "color"}
                        or re.fullmatch(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?", value) is None
                        or key in fields
                    ):
                        raise ValueError("original Mermaid style property requires independent interpretation")
                    fields[key] = value.lower()
                styles[style[1]] = fields
            elif assignment:
                for identity in assignment[1].split(","):
                    if identity in assignments:
                        raise ValueError("original Mermaid repeats a node style assignment")
                    assignments[identity] = assignment[2]
            else:
                edge = re.fullmatch(r"(.+?)\s+-->\s*(?:\|([^|]+)\|\s*)?(.+)", line)
                labeled = re.fullmatch(r"(.+?)\s+--\s+([^<>|]+?)\s+-->\s*(.+)", line)
                if labeled:
                    left, right, label = flow_node(labeled[1]), flow_node(labeled[3]), labeled[2]
                elif edge:
                    left, right, label = flow_node(edge[1]), flow_node(edge[3]), edge[2]
                else:
                    flow_node(line)
                    continue
                edges.append({"from": left, "to": right, "arrow": "-->", "label": _label(label or "")})
        elif family == "classDiagram":
            if current_class is not None:
                if line == "}":
                    current_class = None
                elif re.fullmatch(r"\+[A-Za-z0-9_|~()., ]+", line):
                    nodes[current_class]["members"].append(line)
                else:
                    raise ValueError("original Mermaid class member requires independent interpretation")
                continue
            declaration = re.fullmatch(rf"class ({IDENTIFIER}) \{{", line)
            edge = re.fullmatch(rf'({IDENTIFIER}) --> (?:("\*") )?({IDENTIFIER})(?: : (.+))?', line)
            if declaration:
                current_class = node(declaration[1], shape="class")
                if "members" in nodes[current_class]:
                    raise ValueError("original Mermaid repeats a class body")
                nodes[current_class]["members"] = []
            elif edge:
                edges.append(
                    {
                        "from": node(edge[1]),
                        "to": node(edge[3]),
                        "arrow": "-->",
                        "to_cardinality": "*" if edge[2] else "",
                        "label": _label(edge[4] or ""),
                    }
                )
            else:
                raise ValueError("original Mermaid class directive requires independent interpretation")
        elif family == "stateDiagram-v2":
            description = re.fullmatch(rf"state ({IDENTIFIER}): (.+)", line)
            transition = re.fullmatch(rf"({IDENTIFIER}|\[\*\]) --> ({IDENTIFIER}|\[\*\])(?:\s*:\s*(.+))?", line)
            if description:
                node(description[1], description[2], "state")
            elif transition:
                left = "$start" if transition[1] == "[*]" else node(transition[1], shape="state")
                right = "$end" if transition[2] == "[*]" else node(transition[2], shape="state")
                edges.append({"from": left, "to": right, "arrow": "-->", "label": _label(transition[3] or "")})
            else:
                raise ValueError("original Mermaid state directive requires independent interpretation")
        elif family == "sequenceDiagram":
            participant = re.fullmatch(rf"participant ({IDENTIFIER})", line)
            message = re.fullmatch(rf"({IDENTIFIER})\s*(-->>|->>)\s*({IDENTIFIER})\s*:\s*(.+)", line)
            if participant:
                if participant[1] in nodes:
                    raise ValueError("original Mermaid repeats a participant declaration")
                node(participant[1], shape="participant")
            elif message:
                if message[1] not in nodes or message[3] not in nodes:
                    raise ValueError("original Mermaid message lacks a declared participant")
                edges.append(
                    {
                        "from": message[1],
                        "to": message[3],
                        "arrow": message[2],
                        "label": _label(message[4]),
                        "source_order": index,
                    }
                )
            else:
                raise ValueError("original Mermaid sequence directive requires independent interpretation")
        else:
            relationship = re.fullmatch(
                rf"({IDENTIFIER}) (\|\||o\||\|o|o\{{|\}}o|\|\{{|\}}\|)--"
                rf"(\|\||o\||\|o|o\{{|\}}o|\|\{{|\}}\|) ({IDENTIFIER}) : (.+)",
                line,
            )
            if relationship is None:
                raise ValueError("original Mermaid ER cardinality requires independent interpretation")
            edges.append(
                {
                    "from": node(relationship[1], shape="entity"),
                    "to": node(relationship[4], shape="entity"),
                    "arrow": "--",
                    "from_cardinality": relationship[2],
                    "to_cardinality": relationship[3],
                    "label": _label(relationship[5]),
                }
            )
    if len(nodes) > 1000 or len(edges) > 2000:
        raise ValueError("original Mermaid final node/edge census exceeds finite bounds")
    if current_class is not None or not nodes or not edges:
        raise ValueError("original Mermaid graph body is incomplete")
    if any(identity not in nodes or style not in styles for identity, style in assignments.items()):
        raise ValueError("original Mermaid style assignment invents a node/class")
    for identity, style_identity in assignments.items():
        nodes[identity]["style"] = styles[style_identity]
    return {
        "schema_version": SCHEMA,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "source_bytes": len(source),
        "family": family,
        "direction": direction,
        "nodes": list(nodes.values()),
        "edges": edges,
        "class_styles": styles,
    }
