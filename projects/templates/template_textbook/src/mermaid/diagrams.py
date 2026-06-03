"""Build Mermaid diagram sources from ``diagram_specs.yaml`` and render them."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from textbook_logging import get_logger

from .renderer import MermaidRenderer, RenderResult

logger = get_logger(__name__)

SPECS_PATH = Path(__file__).resolve().parent / "diagram_specs.yaml"


def load_specs(path: Path | None = None) -> list[dict[str, Any]]:
    """Load the diagram specifications list from YAML."""
    specs_path = Path(path) if path is not None else SPECS_PATH
    data = yaml.safe_load(specs_path.read_text(encoding="utf-8"))
    diagrams = data.get("diagrams", []) if isinstance(data, dict) else []
    if not isinstance(diagrams, list):
        raise ValueError("diagram_specs.yaml: 'diagrams' must be a list")
    return diagrams


def build_flowchart(spec: dict[str, Any]) -> str:
    """Render one flowchart spec to Mermaid source text."""
    direction = spec.get("direction", "TD")
    lines = [f"graph {direction}"]
    for node in spec.get("nodes", []):
        lines.append(f'  {node["id"]}["{node["label"]}"]')
    for edge in spec.get("edges", []):
        label = edge.get("label")
        arrow = f"-->|{label}|" if label else "-->"
        lines.append(f"  {edge['from']} {arrow} {edge['to']}")
    return "\n".join(lines) + "\n"


def build_sequence(spec: dict[str, Any]) -> str:
    """Sequence diagram: participants + ordered messages."""
    lines = ["sequenceDiagram"]
    for participant in spec.get("participants", []):
        lines.append(f"  participant {participant}")
    for msg in spec.get("messages", []):
        arrow = "-->>" if msg.get("dashed") else "->>"
        lines.append(f"  {msg['from']} {arrow} {msg['to']}: {msg['text']}")
    return "\n".join(lines) + "\n"


def build_state(spec: dict[str, Any]) -> str:
    """State diagram (v2): transitions with optional [*] start/end."""
    lines = ["stateDiagram-v2"]
    for tr in spec.get("transitions", []):
        label = f": {tr['label']}" if tr.get("label") else ""
        lines.append(f"  {tr['from']} --> {tr['to']}{label}")
    return "\n".join(lines) + "\n"


def build_class(spec: dict[str, Any]) -> str:
    """Class diagram: classes with members, plus relations."""
    lines = ["classDiagram"]
    for cls in spec.get("classes", []):
        lines.append(f"  class {cls['name']} {{")
        for member in cls.get("members", []):
            lines.append(f"    {member}")
        lines.append("  }")
    for rel in spec.get("relations", []):
        arrow = rel.get("arrow", "<|--")
        label = f" : {rel['label']}" if rel.get("label") else ""
        lines.append(f"  {rel['from']} {arrow} {rel['to']}{label}")
    return "\n".join(lines) + "\n"


def build_er(spec: dict[str, Any]) -> str:
    """Entity-relationship diagram: relationships + entity attribute blocks."""
    lines = ["erDiagram"]
    for rel in spec.get("relations", []):
        card = rel.get("cardinality", "||--o{")
        lines.append(f"  {rel['from']} {card} {rel['to']} : {rel.get('label', 'relates')}")
    for entity in spec.get("entities", []):
        lines.append(f"  {entity['name']} {{")
        for attr in entity.get("attributes", []):
            lines.append(f"    {attr['type']} {attr['name']}")
        lines.append("  }")
    return "\n".join(lines) + "\n"


def build_gantt(spec: dict[str, Any]) -> str:
    """Gantt chart: sections of dated tasks."""
    lines = ["gantt", f"  title {spec.get('title', 'Schedule')}", "  dateFormat YYYY-MM-DD"]
    for section in spec.get("sections", []):
        lines.append(f"  section {section['name']}")
        for task in section.get("tasks", []):
            lines.append(f"  {task['name']} :{task['id']}, {task['start']}, {task['duration']}")
    return "\n".join(lines) + "\n"


def build_pie(spec: dict[str, Any]) -> str:
    """Pie chart: labelled slices."""
    lines = [f"pie title {spec.get('title', 'Distribution')}"]
    for slice_ in spec.get("slices", []):
        lines.append(f'  "{slice_["label"]}" : {slice_["value"]}')
    return "\n".join(lines) + "\n"


def build_mindmap(spec: dict[str, Any]) -> str:
    """Mind map: a root with (optionally nested) branches."""
    lines = ["mindmap", f"  root(({spec.get('root', 'Root')}))"]

    def _walk(nodes: list[Any], depth: int) -> None:
        indent = "  " * (depth + 2)
        for node in nodes:
            if isinstance(node, dict):
                lines.append(f"{indent}{node['label']}")
                _walk(node.get("children", []), depth + 1)
            else:
                lines.append(f"{indent}{node}")

    _walk(spec.get("branches", []), 0)
    return "\n".join(lines) + "\n"


def build_timeline(spec: dict[str, Any]) -> str:
    """Timeline: periods, each with one or more events."""
    lines = ["timeline", f"  title {spec.get('title', 'Timeline')}"]
    for entry in spec.get("events", []):
        items = " : ".join(entry.get("items", []))
        lines.append(f"  {entry['period']} : {items}")
    return "\n".join(lines) + "\n"


def build_quadrant(spec: dict[str, Any]) -> str:
    """Quadrant chart: two axes, four labelled quadrants, plotted points."""
    lines = [
        "quadrantChart",
        f"  title {spec.get('title', 'Quadrant')}",
        f"  x-axis {spec.get('x_axis', 'Low --> High')}",
        f"  y-axis {spec.get('y_axis', 'Low --> High')}",
    ]
    for i, label in enumerate(spec.get("quadrants", []), start=1):
        lines.append(f"  quadrant-{i} {label}")
    for point in spec.get("points", []):
        lines.append(f"  {point['label']}: [{point['x']}, {point['y']}]")
    return "\n".join(lines) + "\n"


def build_journey(spec: dict[str, Any]) -> str:
    """User-journey diagram: sections of scored steps."""
    lines = ["journey", f"  title {spec.get('title', 'Journey')}"]
    for section in spec.get("sections", []):
        lines.append(f"  section {section['name']}")
        for step in section.get("steps", []):
            actors = ", ".join(step.get("actors", []))
            lines.append(f"    {step['task']}: {step['score']}: {actors}")
    return "\n".join(lines) + "\n"


_BUILDERS = {
    "flowchart": build_flowchart,
    "sequence": build_sequence,
    "state": build_state,
    "class": build_class,
    "er": build_er,
    "gantt": build_gantt,
    "pie": build_pie,
    "mindmap": build_mindmap,
    "timeline": build_timeline,
    "quadrant": build_quadrant,
    "journey": build_journey,
}


def build_source(spec: dict[str, Any]) -> str:
    """Dispatch a spec to its builder by ``kind``."""
    kind = spec.get("kind", "flowchart")
    builder = _BUILDERS.get(kind)
    if builder is None:
        raise ValueError(f"unknown diagram kind: {kind!r}")
    return builder(spec)


def generate_all_diagrams(output_dir: Path, specs_path: Path | None = None) -> list[RenderResult]:
    """Build and render every diagram in the spec file."""
    renderer = MermaidRenderer(output_dir)
    results: list[RenderResult] = []
    for spec in load_specs(specs_path):
        source = build_source(spec)
        results.append(renderer.render(spec["name"], source))
    logger.info("generated %d diagrams in %s", len(results), output_dir)
    return results


__all__ = [
    "SPECS_PATH",
    "build_class",
    "build_er",
    "build_flowchart",
    "build_gantt",
    "build_journey",
    "build_mindmap",
    "build_pie",
    "build_quadrant",
    "build_sequence",
    "build_source",
    "build_state",
    "build_timeline",
    "generate_all_diagrams",
    "load_specs",
]
