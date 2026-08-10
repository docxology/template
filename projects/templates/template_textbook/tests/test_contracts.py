"""Tests for configuration, quantitative, diagram, and visual contracts."""

from __future__ import annotations

import hashlib
from pathlib import Path

from mermaid import diagrams
from textbook.config import load_config
from textbook.contracts import (
    compare_config_shapes,
    numeric_fact_receipt,
    validate_diagram_inventory,
    validate_numeric_facts,
)
from visualization import plots


PROJECT = Path(__file__).resolve().parent.parent
MANUSCRIPT = PROJECT / "manuscript"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_live_and_example_config_shapes_are_lockstep():
    live = load_config(MANUSCRIPT / "config.yaml")
    example = load_config(MANUSCRIPT / "config.yaml.example")
    assert compare_config_shapes(live, example) == ()


def test_config_shape_detects_dropped_nested_key():
    live = {"units": [{"id": "p", "chapters": [{"file": "a.md"}]}]}
    example = {"units": [{"id": "p", "chapters": [{"file": "a.md"}], "intro_file": "unit_intro.md"}]}
    differences = compare_config_shapes(live, example)
    assert "$.units[0].intro_file: missing from live config" in differences


def test_numeric_fact_registry_is_source_bound():
    registry = PROJECT / "data" / "numeric_facts.yaml"
    assert validate_numeric_facts(registry, project_root=PROJECT) == ()
    receipt = numeric_fact_receipt(registry, project_root=PROJECT)
    assert receipt["status"] == "pass"
    assert receipt["fact_count"] >= 8


def test_numeric_fact_registry_rejects_changed_source(tmp_path):
    source = tmp_path / "source.md"
    source.write_text("value = 2\n", encoding="utf-8")
    registry = tmp_path / "numeric_facts.yaml"
    registry.write_text(
        "schema_version: template-textbook-numeric-facts-v1\n"
        "facts:\n"
        "  - fact_id: changed\n"
        "    source: source.md\n"
        "    needle: 'value = 1'\n"
        "    value: 1\n"
        "    status: bound\n"
        "    rationale: test\n",
        encoding="utf-8",
    )
    issues = validate_numeric_facts(registry, project_root=tmp_path)
    assert any("registered source snippet is absent" in issue for issue in issues)


def test_diagram_inventory_rejects_stale_output(tmp_path):
    specs = diagrams.load_specs()
    for spec in specs:
        (tmp_path / f"{spec['name']}.mmd").write_text("graph TD\n", encoding="utf-8")
    (tmp_path / "obsolete.mmd").write_text("graph TD\n", encoding="utf-8")
    issues = validate_diagram_inventory(specs, tmp_path)
    assert "stale generated diagram: obsolete" in issues


def test_diagram_inventory_accepts_png_or_mmd_per_spec(tmp_path):
    specs = diagrams.load_specs()[:2]
    (tmp_path / "concept_map.png").write_bytes(b"png fixture")
    (tmp_path / "process_flow.mmd").write_text("graph LR\n", encoding="utf-8")
    assert validate_diagram_inventory(specs, tmp_path) == ()


def test_cover_art_and_mermaid_sources_are_deterministic(tmp_path):
    first = plots.cover_art(tmp_path / "one", subtitle="A scaffold")
    second = plots.cover_art(tmp_path / "two", subtitle="A scaffold")
    assert _sha256(first) == _sha256(second)
    specs = diagrams.load_specs()
    sources = [diagrams.build_source(spec) for spec in specs]
    assert sources == [diagrams.build_source(spec) for spec in specs]
