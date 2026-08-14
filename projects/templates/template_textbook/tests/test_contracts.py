"""Tests for configuration, quantitative, diagram, and visual contracts.

Kept deterministic and mock-free: every fixture is a real tempfile written via
``yaml.safe_dump`` (so the YAML on disk is always well-formed and the negative
controls exercise the parser paths rather than bypassing them).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from mermaid import diagrams
from textbook.config import load_config
from textbook.contracts import (
    compare_config_shapes,
    load_numeric_facts,
    load_yaml_mapping,
    numeric_fact_receipt,
    validate_diagram_inventory,
    validate_numeric_facts,
)
from visualization import plots


PROJECT = Path(__file__).resolve().parent.parent
MANUSCRIPT = PROJECT / "manuscript"

SCHEMA = "template-textbook-numeric-facts-v1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_facts(path: Path, facts: list[dict], *, schema: str = SCHEMA) -> Path:
    """Write a well-formed numeric-facts registry and return its path."""
    path.write_text(
        yaml.safe_dump({"schema_version": schema, "facts": facts}, sort_keys=False),
        encoding="utf-8",
    )
    return path


def _fact(**overrides: object) -> dict:
    row = {
        "fact_id": "f",
        "source": "source.md",
        "needle": "value = 2",
        "status": "bound",
        "rationale": "test",
    }
    row.update(overrides)
    return row


# --- baseline parity ---------------------------------------------------------


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
    registry = _write_facts(
        tmp_path / "numeric_facts.yaml",
        [_fact(fact_id="changed", needle="value = 1", value=1)],
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


# --- compare_config_shapes: both missing directions + kind edges -----------


def test_config_shape_reports_key_missing_from_example():
    live = {"units": [{"id": "p", "chapters": [{"file": "a.md", "intro_note": "x"}]}]}
    example = {"units": [{"id": "p", "chapters": [{"file": "a.md"}]}]}
    differences = compare_config_shapes(live, example)
    assert "$.units[0].chapters[0].intro_note: missing from example" in differences


def test_config_shape_reports_both_missing_directions():
    differences = compare_config_shapes({"a": 1}, {"b": 2})
    assert any("a: missing from example" in d for d in differences)
    assert any("b: missing from live config" in d for d in differences)


def test_config_shape_detects_list_mapping_shape_mismatch():
    differences = compare_config_shapes({"l": [{"id": "x"}]}, {"l": ["not_a_mapping"]})
    assert any("list item mapping shape differs" in d for d in differences)


def test_config_shape_detects_mapping_list_length_mismatch():
    differences = compare_config_shapes({"l": [{"id": "x"}]}, {"l": [{"id": "x"}, {"id": "y"}]})
    assert any("mapping-list length differs (1 != 2)" in d for d in differences)


def test_config_shape_detects_scalar_kind_mismatch():
    differences = compare_config_shapes({"v": 1}, {"v": "one"})
    assert any("kind differs" in d and "number" in d and "string" in d for d in differences)


def test_config_shape_flags_mapping_vs_list_mismatch():
    differences = compare_config_shapes({"a": [{"b": 1}]}, {"a": {"b": 1}})
    assert any("kind differs (list != dict)" in d for d in differences)


def test_config_shape_treats_float_and_int_as_number():
    assert compare_config_shapes({"v": 1}, {"v": 2.5}) == ()
    assert compare_config_shapes({"v": 1.5}, {"v": 2}) == ()


def test_config_shape_ignores_scalar_list_content():
    live = {"languages": ["en", "fr"]}
    example = {"languages": ["en"]}
    assert compare_config_shapes(live, example) == ()


def test_config_shape_ignores_scalar_values():
    live = {"units": [{"id": "p", "pages": 10}]}
    example = {"units": [{"id": "p", "pages": 22}]}
    assert compare_config_shapes(live, example) == ()


def test_config_shape_bool_vs_number_kind():
    differences = compare_config_shapes({"flag": True}, {"flag": 1})
    assert any("kind differs (bool != number)" in d for d in differences)


# --- load_yaml_mapping / load_numeric_facts error paths --------------------


def test_load_yaml_mapping_rejects_non_mapping(tmp_path):
    path = tmp_path / "not_a_mapping.yaml"
    path.write_text("- one\n- two\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected a YAML mapping"):
        load_yaml_mapping(path)


def test_load_numeric_facts_rejects_unsupported_schema(tmp_path):
    path = _write_facts(tmp_path / "facts.yaml", [], schema="wrong-v0")
    with pytest.raises(ValueError, match="unsupported numeric-facts schema"):
        load_numeric_facts(path)


def test_load_numeric_facts_rejects_non_list_facts(tmp_path):
    path = tmp_path / "facts.yaml"
    path.write_text(yaml.safe_dump({"schema_version": SCHEMA, "facts": "nope"}), encoding="utf-8")
    with pytest.raises(ValueError, match="requires a facts list"):
        load_numeric_facts(path)


def test_load_numeric_facts_rejects_non_mapping_row(tmp_path):
    path = tmp_path / "facts.yaml"
    path.write_text(
        yaml.safe_dump({"schema_version": SCHEMA, "facts": ["just_a_string"]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="rows must be mappings"):
        load_numeric_facts(path)


# --- validate_numeric_facts negative controls -------------------------------


def test_numeric_facts_rejects_empty_registry(tmp_path):
    registry = _write_facts(tmp_path / "numeric_facts.yaml", [])
    issues = validate_numeric_facts(registry, project_root=tmp_path)
    assert "numeric-facts registry must not be empty" in issues


def test_numeric_facts_rejects_empty_and_duplicate_fact_ids(tmp_path):
    source = tmp_path / "source.md"
    source.write_text("value = 2\n", encoding="utf-8")
    registry = _write_facts(
        tmp_path / "numeric_facts.yaml",
        [
            _fact(fact_id=""),
            _fact(fact_id="dup"),
            _fact(fact_id="dup"),
        ],
    )
    issues = validate_numeric_facts(registry, project_root=tmp_path)
    assert "numeric fact has an empty fact_id" in issues
    assert "duplicate numeric fact id: dup" in issues


def test_numeric_facts_rejects_unsupported_status(tmp_path):
    source = tmp_path / "source.md"
    source.write_text("value = 2\n", encoding="utf-8")
    registry = _write_facts(
        tmp_path / "numeric_facts.yaml",
        [_fact(fact_id="x", status="tentative")],
    )
    issues = validate_numeric_facts(registry, project_root=tmp_path)
    assert "x: unsupported status 'tentative'" in issues


def test_numeric_facts_rejects_missing_required_fields(tmp_path):
    registry = _write_facts(
        tmp_path / "numeric_facts.yaml",
        [_fact(fact_id="incomplete", source="", needle="", rationale="")],
    )
    issues = validate_numeric_facts(registry, project_root=tmp_path)
    assert "incomplete: source, needle, and rationale are required" in issues


def test_numeric_facts_rejects_source_escaping_project_root(tmp_path):
    registry = _write_facts(
        tmp_path / "numeric_facts.yaml",
        [_fact(fact_id="escape", source="../outside.md", needle="x")],
    )
    issues = validate_numeric_facts(registry, project_root=tmp_path)
    assert "escape: source escapes project root" in issues


def test_numeric_facts_rejects_missing_source_file(tmp_path):
    registry = _write_facts(
        tmp_path / "numeric_facts.yaml",
        [_fact(fact_id="missing", source="absent.md", needle="x")],
    )
    issues = validate_numeric_facts(registry, project_root=tmp_path)
    assert "missing: missing source absent.md" in issues


def test_numeric_fact_receipt_reports_fail_on_bad_registry(tmp_path):
    registry = _write_facts(
        tmp_path / "numeric_facts.yaml",
        [_fact(fact_id="broken", source="absent.md", needle="x")],
    )
    receipt = numeric_fact_receipt(registry, project_root=tmp_path)
    assert receipt["status"] == "fail"
    assert any("missing source" in issue for issue in receipt["issues"])


# --- validate_diagram_inventory negative controls ---------------------------


def test_diagram_inventory_rejects_unsafe_and_empty_names():
    issues = validate_diagram_inventory([{"name": "a/b", "kind": "flowchart"}])
    assert any("unsafe or empty name" in issue for issue in issues)
    issues = validate_diagram_inventory([{"name": "", "kind": "flowchart"}])
    assert any("unsafe or empty name" in issue for issue in issues)


def test_diagram_inventory_rejects_duplicate_names():
    specs = [{"name": "dup", "kind": "flowchart"}, {"name": "dup", "kind": "sequence"}]
    issues = validate_diagram_inventory(specs)
    assert "duplicate diagram name: dup" in issues


def test_diagram_inventory_requires_kind():
    issues = validate_diagram_inventory([{"name": "no_kind"}])
    assert any("kind is required" in issue and "no_kind" in issue for issue in issues)


def test_diagram_inventory_rejects_empty_inventory():
    issues = validate_diagram_inventory([])
    assert "diagram inventory must not be empty" in issues


def test_diagram_inventory_flags_missing_generated_output(tmp_path):
    specs = [{"name": "produced", "kind": "flowchart"}, {"name": "absent", "kind": "sequence"}]
    (tmp_path / "produced.mmd").write_text("graph TD\n", encoding="utf-8")
    issues = validate_diagram_inventory(specs, tmp_path)
    assert "missing generated diagram: absent" in issues
    assert "missing generated diagram: produced" not in issues
