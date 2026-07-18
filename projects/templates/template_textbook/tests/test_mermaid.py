"""Tests for Mermaid diagram building and rendering (with .mmd fallback)."""

from __future__ import annotations

import os
import subprocess

import pytest

from mermaid import diagrams
from mermaid.renderer import MermaidRenderer, RenderResult, _run_mmdc, mmdc_available


def test_load_specs_from_default_file():
    specs = diagrams.load_specs()
    names = {s["name"] for s in specs}
    assert {"concept_map", "process_flow", "part_hierarchy"} <= names


def test_build_flowchart_with_and_without_edge_label():
    spec = {
        "kind": "flowchart",
        "direction": "LR",
        "nodes": [{"id": "A", "label": "Start"}, {"id": "B", "label": "End"}],
        "edges": [{"from": "A", "to": "B", "label": "go"}, {"from": "B", "to": "A"}],
    }
    source = diagrams.build_flowchart(spec)
    assert source.startswith("graph LR")
    assert 'A["Start"]' in source
    assert "A -->|go| B" in source
    assert "B --> A" in source


def test_build_source_dispatch_and_unknown_kind():
    spec = diagrams.load_specs()[0]
    assert diagrams.build_source(spec).startswith("graph")
    with pytest.raises(ValueError):
        diagrams.build_source({"kind": "nope"})


def test_load_specs_rejects_bad_shape(tmp_path):
    bad = tmp_path / "specs.yaml"
    bad.write_text("diagrams: {}\n", encoding="utf-8")
    with pytest.raises(ValueError):
        diagrams.load_specs(bad)


def test_renderer_writes_mmd_fallback_when_no_mmdc(tmp_path):
    renderer = MermaidRenderer(tmp_path)
    result = renderer.render("demo", "graph TD\n  A --> B\n")
    assert isinstance(result, RenderResult)
    if not mmdc_available():
        assert result.rendered_png is False
        assert result.path.suffix == ".mmd"
        assert result.path.read_text(encoding="utf-8").startswith("graph TD")


def test_generate_all_diagrams(tmp_path):
    results = diagrams.generate_all_diagrams(tmp_path)
    specs = diagrams.load_specs()
    assert len(results) == len(specs) >= 13
    for result in results:
        assert result.path.exists()


def test_every_spec_kind_has_a_builder_and_builds():
    for spec in diagrams.load_specs():
        source = diagrams.build_source(spec)
        assert isinstance(source, str) and source.strip()


def test_build_sequence():
    src = diagrams.build_sequence(
        {
            "participants": ["A", "B"],
            "messages": [
                {"from": "A", "to": "B", "text": "hi"},
                {"from": "B", "to": "A", "text": "bye", "dashed": True},
            ],
        }
    )
    assert src.startswith("sequenceDiagram")
    assert "participant A" in src
    assert "A ->> B: hi" in src
    assert "B -->> A: bye" in src


def test_build_state():
    src = diagrams.build_state(
        {"transitions": [{"from": "[*]", "to": "S"}, {"from": "S", "to": "[*]", "label": "done"}]}
    )
    assert src.startswith("stateDiagram-v2")
    assert "[*] --> S" in src
    assert "S --> [*]: done" in src


def test_build_class():
    src = diagrams.build_class(
        {
            "classes": [{"name": "Foo", "members": ["+int x", "+go()"]}],
            "relations": [{"from": "Foo", "to": "Bar", "arrow": "-->", "label": "uses"}],
        }
    )
    assert "classDiagram" in src
    assert "class Foo {" in src
    assert "+int x" in src
    assert "Foo --> Bar : uses" in src


def test_build_er():
    src = diagrams.build_er(
        {
            "relations": [{"from": "A", "to": "B", "cardinality": "||--o{", "label": "has"}],
            "entities": [{"name": "A", "attributes": [{"type": "string", "name": "id"}]}],
        }
    )
    assert src.startswith("erDiagram")
    assert "A ||--o{ B : has" in src
    assert "string id" in src


def test_build_gantt_pie():
    gantt = diagrams.build_gantt(
        {
            "title": "Sched",
            "sections": [{"name": "S", "tasks": [{"name": "T", "id": "t1", "start": "2026-01-01", "duration": "3d"}]}],
        }
    )
    assert gantt.startswith("gantt")
    assert "title Sched" in gantt
    assert "T :t1, 2026-01-01, 3d" in gantt
    pie = diagrams.build_pie({"title": "P", "slices": [{"label": "X", "value": 70}]})
    assert pie.startswith("pie title P")
    assert '"X" : 70' in pie


def test_build_mindmap_nested():
    src = diagrams.build_mindmap(
        {"root": "R", "branches": [{"label": "B1", "children": ["leaf", {"label": "B2", "children": ["deep"]}]}]}
    )
    assert src.startswith("mindmap")
    assert "root((R))" in src
    assert "B1" in src and "leaf" in src and "deep" in src


def test_build_timeline_quadrant_journey():
    timeline = diagrams.build_timeline({"title": "T", "events": [{"period": "2020", "items": ["a", "b"]}]})
    assert "timeline" in timeline
    assert "2020 : a : b" in timeline
    quadrant = diagrams.build_quadrant(
        {"title": "Q", "quadrants": ["q1", "q2", "q3", "q4"], "points": [{"label": "P", "x": 0.5, "y": 0.5}]}
    )
    assert "quadrantChart" in quadrant
    assert "quadrant-1 q1" in quadrant
    assert "P: [0.5, 0.5]" in quadrant
    journey = diagrams.build_journey(
        {"title": "J", "sections": [{"name": "S", "steps": [{"task": "do", "score": 4, "actors": ["Me"]}]}]}
    )
    assert "journey" in journey
    assert "do: 4: Me" in journey


def test_mmdc_available_returns_bool():
    assert isinstance(mmdc_available(), bool)


def test_build_flowchart_defaults():
    """build_flowchart with no direction falls back to TD."""
    spec = {
        "nodes": [{"id": "X", "label": "X node"}],
        "edges": [],
    }
    src = diagrams.build_flowchart(spec)
    assert src.startswith("graph TD")
    assert 'X["X node"]' in src


def test_build_sequence_empty():
    """build_sequence with no participants or messages is still valid Mermaid."""
    src = diagrams.build_sequence({"participants": [], "messages": []})
    assert src.strip() == "sequenceDiagram"


def test_build_state_no_label_transition():
    """Transitions without a label omit the colon segment."""
    src = diagrams.build_state({"transitions": [{"from": "A", "to": "B"}]})
    assert "A --> B" in src
    assert ":" not in src.split("A --> B")[1].split("\n")[0]


def test_build_class_no_relations():
    """A class diagram with no relations is still valid."""
    src = diagrams.build_class({"classes": [{"name": "MyClass", "members": []}], "relations": []})
    assert "classDiagram" in src
    assert "class MyClass {" in src


def test_build_er_no_attributes():
    """An ER diagram entity with no attributes still opens and closes block."""
    src = diagrams.build_er(
        {
            "relations": [],
            "entities": [{"name": "E", "attributes": []}],
        }
    )
    assert "erDiagram" in src
    assert "E {" in src


def test_build_mindmap_flat_branches():
    """Flat branches (no children) are emitted without recursing."""
    src = diagrams.build_mindmap({"root": "Root", "branches": ["A", "B"]})
    assert "mindmap" in src
    assert "root((Root))" in src
    assert "A" in src and "B" in src


def test_build_gantt_no_sections():
    """Gantt with no sections emits only the header lines."""
    src = diagrams.build_gantt({"title": "Empty", "sections": []})
    assert "gantt" in src
    assert "title Empty" in src
    assert "dateFormat" in src


def test_build_pie_empty():
    """Pie with no slices emits at least the chart header."""
    src = diagrams.build_pie({"title": "Empty", "slices": []})
    assert src.startswith("pie title Empty")


def test_build_timeline_empty():
    src = diagrams.build_timeline({"title": "T", "events": []})
    assert "timeline" in src
    assert "title T" in src


def test_build_quadrant_no_points():
    """Quadrant with no points still emits the chart skeleton."""
    src = diagrams.build_quadrant(
        {
            "title": "Q",
            "quadrants": ["q1", "q2", "q3", "q4"],
            "points": [],
        }
    )
    assert "quadrantChart" in src
    assert "quadrant-4 q4" in src


def test_build_journey_empty():
    src = diagrams.build_journey({"title": "J", "sections": []})
    assert "journey" in src
    assert "title J" in src


def test_all_spec_names_are_unique():
    """No two specs in diagram_specs.yaml share the same name."""
    specs = diagrams.load_specs()
    names = [s["name"] for s in specs]
    assert len(names) == len(set(names)), "duplicate spec names in diagram_specs.yaml"


@pytest.mark.skipif(os.name != "posix", reason="process groups differ on Windows")
def test_mmdc_timeout_reaps_descendant_processes():
    """The Mermaid timeout boundary must clean up browser-like descendants."""
    with pytest.raises(subprocess.TimeoutExpired):
        _run_mmdc(["/bin/sh", "-c", "sleep 30"], timeout=1)


def test_load_specs_with_custom_path(tmp_path):
    """load_specs can read a custom YAML file that has a valid diagrams list."""
    custom = tmp_path / "custom.yaml"
    custom.write_text(
        "diagrams:\n"
        "  - name: test_flow\n"
        "    kind: flowchart\n"
        "    nodes:\n"
        "      - {id: A, label: Start}\n"
        "    edges: []\n",
        encoding="utf-8",
    )
    specs = diagrams.load_specs(custom)
    assert len(specs) == 1
    assert specs[0]["name"] == "test_flow"
    # Verify the loaded spec can be built.
    assert diagrams.build_source(specs[0]).startswith("graph")
