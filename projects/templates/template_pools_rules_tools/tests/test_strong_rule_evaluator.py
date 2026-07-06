"""Tests for strong_rule_evaluator.py using real rule exemplars and project context."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

from src.strong_rule_evaluator import (
    evaluate_strong_rule,
    evaluate_strong_rules,
    load_rule_context_from_project,
)
from src.rules_applier import load_strong_rules

_PROJECT_DIR = pathlib.Path(__file__).parents[1]
_RULE_SETS = ["template_project_rules", "template_manuscript_rules"]


@pytest.mark.parametrize("rule_set", _RULE_SETS)
def test_evaluate_strong_rules_passes_for_pools_project(rule_set: str) -> None:
    context = load_rule_context_from_project(_PROJECT_DIR)
    result = evaluate_strong_rules(rule_set, context)
    assert result["rule_set"] == rule_set
    assert isinstance(result["evaluations"], list)
    assert result["passed"] is True
    assert result["violation_count"] == 0


def test_coverage_threshold_flags_low_coverage(tmp_path: pathlib.Path) -> None:
    strong = load_strong_rules("template_project_rules")
    coverage_rule = next(
        entry for entry in strong if entry["filename"] == "coverage-gate.yaml"
    )
    evaluation = evaluate_strong_rule(
        coverage_rule,
        {"coverage": {"infrastructure": 10, "project_src": 10, "public_api": 10}},
    )
    assert evaluation["passed"] is False
    assert len(evaluation["violations"]) >= 1


def test_section_schema_flags_missing_section() -> None:
    strong = load_strong_rules("template_manuscript_rules")
    section_rule = next(
        entry for entry in strong if entry["filename"] == "section-schema.yaml"
    )
    evaluation = evaluate_strong_rule(section_rule, {"manuscript_sections": ["Abstract"]})
    assert evaluation["passed"] is False
    assert any("required section missing" in v["message"] for v in evaluation["violations"])


def test_module_structure_flags_missing_src(tmp_path: pathlib.Path) -> None:
    strong = load_strong_rules("template_project_rules")
    module_rule = next(
        entry for entry in strong if entry["filename"] == "module-structure.yaml"
    )
    evaluation = evaluate_strong_rule(module_rule, {"project_root": tmp_path})
    assert evaluation["passed"] is False
    assert any("src/ directory missing" in v["message"] for v in evaluation["violations"])


def test_load_rule_context_includes_manuscript_sections() -> None:
    context = load_rule_context_from_project(_PROJECT_DIR)
    sections = context.get("manuscript_sections")
    assert isinstance(sections, list)
    assert "Abstract" in sections
    assert "References" in sections
    coverage = context.get("coverage")
    assert isinstance(coverage, dict)
    references = context.get("references")
    assert isinstance(references, list)
    assert references
    assert references[0].get("key")
    assert references[0].get("authors")


def test_evaluate_strong_rule_rejects_schema_without_rule_block() -> None:
    entry = {"filename": "broken.yaml", "schema": {"not_rule": True}}
    evaluation = evaluate_strong_rule(entry, {})
    assert evaluation["passed"] is False
    assert evaluation["violations"][0]["message"] == "schema missing top-level 'rule' mapping"


def test_coverage_threshold_requires_constraints_mapping() -> None:
    strong = load_strong_rules("template_project_rules")
    coverage_rule = next(
        entry for entry in strong if entry["filename"] == "coverage-gate.yaml"
    )
    broken = {"filename": coverage_rule["filename"], "schema": {"rule": {"name": "coverage_threshold"}}}
    evaluation = evaluate_strong_rule(broken, {"coverage": {"project_src": 99}})
    assert evaluation["passed"] is False


def test_coverage_threshold_flags_missing_context_key() -> None:
    strong = load_strong_rules("template_project_rules")
    coverage_rule = next(
        entry for entry in strong if entry["filename"] == "coverage-gate.yaml"
    )
    evaluation = evaluate_strong_rule(coverage_rule, {"coverage": {"project_src": 99}})
    assert evaluation["passed"] is False
    assert any("not provided in context" in v["message"] for v in evaluation["violations"])


def test_section_schema_flags_forbidden_heading() -> None:
    strong = load_strong_rules("template_manuscript_rules")
    section_rule = next(
        entry for entry in strong if entry["filename"] == "section-schema.yaml"
    )
    evaluation = evaluate_strong_rule(
        section_rule,
        {
            "manuscript_sections": ["Abstract", "Introduction"],
            "forbidden_sections_found": ["TODO"],
        },
    )
    assert evaluation["passed"] is False
    assert any("forbidden section present" in v["message"] for v in evaluation["violations"])


def test_reference_schema_flags_non_mapping_entry() -> None:
    strong = load_strong_rules("template_manuscript_rules")
    reference_rule = next(
        entry for entry in strong if entry["filename"] == "reference-schema.yaml"
    )
    evaluation = evaluate_strong_rule(reference_rule, {"references": ["not-a-mapping"]})
    assert evaluation["passed"] is False


def test_load_rule_context_reads_canonical_sections_from_config(tmp_path: pathlib.Path) -> None:
    project = tmp_path / "demo"
    manuscript = project / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "config.yaml").write_text(
        "strong_rules:\n  canonical_sections:\n    - Abstract\n",
        encoding="utf-8",
    )
    (manuscript / "01_abstract.md").write_text("# Abstract {#sec:abstract}\n", encoding="utf-8")
    context = load_rule_context_from_project(project)
    assert context["manuscript_sections"] == ["Abstract"]
