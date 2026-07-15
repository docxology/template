"""Tests for strong_rule_evaluator.py using real rule exemplars and project context."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

from src.rules_applier import load_strong_rules
from src.strong_rule_evaluator import (
    evaluate_strong_rule,
    evaluate_strong_rules,
    load_rule_context_from_project,
)

_PROJECT_DIR = pathlib.Path(__file__).parents[1]


def test_evaluate_strong_rules_passes_for_pools_project() -> None:
    """Regression pin against this project's OWN live tree, not a synthetic fixture.

    load_rule_context_from_project() parses this project's actual
    manuscript/references.bib and real manuscript/*.md section headings, so
    this genuinely exercises reference_schema and section_schema against
    live content. A future manuscript edit (new section, malformed bib entry)
    can legitimately flip this red — that proves the semantic layer still
    runs against real content, it is not a frozen fixture to work around.

    Only `template_project_rules` is pinned green here. See
    `test_evaluate_strong_rules_detects_real_missing_manuscript_sections` for
    why `template_manuscript_rules` genuinely (and correctly) fails today.
    """
    context = load_rule_context_from_project(_PROJECT_DIR)
    result = evaluate_strong_rules("template_project_rules", context)
    assert result["rule_set"] == "template_project_rules"
    assert isinstance(result["evaluations"], list)
    assert result["passed"] is True
    assert result["violation_count"] == 0


def test_evaluate_strong_rules_detects_real_missing_manuscript_sections() -> None:
    """`section_schema` against this project's OWN live manuscript headings.

    Regression guard for a bug where `load_rule_context_from_project()`
    unconditionally injected every `config.yaml` `canonical_sections` entry
    into the detected `manuscript_sections` list. Since `section-schema.yaml`'s
    `required_sections` is drawn from that same canonical list, the injection
    made the "required section missing" check compare the config's canonical
    list against itself — it could never fail no matter what the manuscript
    actually contained.

    This project's manuscript uses domain-specific section names (Pools,
    Rules, Tools, Integration) rather than the canonical Related Work /
    Methods / Results / Discussion / References headings `section-schema.yaml`
    requires, so with the injection removed this rule set genuinely (and
    correctly) fails today. A future manuscript restructuring that adds these
    headings (or their declared aliases) can legitimately flip this green —
    that would prove the semantic layer runs against real content, not a
    frozen fixture to work around.
    """
    context = load_rule_context_from_project(_PROJECT_DIR)
    result = evaluate_strong_rules("template_manuscript_rules", context)
    assert result["rule_set"] == "template_manuscript_rules"
    assert result["passed"] is False

    messages = {v["message"] for ev in result["evaluations"] for v in ev["violations"]}
    for missing in ("Related Work", "Methods", "Results", "Discussion", "References"):
        assert f"required section missing: {missing}" in messages
    # Sections that ARE genuinely present must not be flagged.
    for present in ("Abstract",):
        assert f"required section missing: {present}" not in messages


def test_coverage_threshold_flags_low_coverage() -> None:
    strong = load_strong_rules("template_project_rules")
    coverage_rule = next(entry for entry in strong if entry["filename"] == "coverage-gate.yaml")
    evaluation = evaluate_strong_rule(
        coverage_rule,
        {"coverage": {"infrastructure": 10, "project_src": 10, "public_api": 10}},
    )
    assert evaluation["passed"] is False
    assert len(evaluation["violations"]) >= 1


def test_section_schema_flags_missing_section() -> None:
    strong = load_strong_rules("template_manuscript_rules")
    section_rule = next(entry for entry in strong if entry["filename"] == "section-schema.yaml")
    evaluation = evaluate_strong_rule(section_rule, {"manuscript_sections": ["Abstract"]})
    assert evaluation["passed"] is False
    assert any("required section missing" in v["message"] for v in evaluation["violations"])


def test_module_structure_flags_missing_src(tmp_path: pathlib.Path) -> None:
    strong = load_strong_rules("template_project_rules")
    module_rule = next(entry for entry in strong if entry["filename"] == "module-structure.yaml")
    evaluation = evaluate_strong_rule(module_rule, {"project_root": tmp_path})
    assert evaluation["passed"] is False
    assert any("src/ directory missing" in v["message"] for v in evaluation["violations"])


def test_load_rule_context_includes_manuscript_sections() -> None:
    context = load_rule_context_from_project(_PROJECT_DIR)
    sections = context.get("manuscript_sections")
    assert isinstance(sections, list)
    assert "Abstract" in sections
    assert "Introduction" in sections
    # "References" has no literal `# References` heading in manuscript/*.md
    # (it is generated at render time from references.bib) — it must NOT
    # appear here just because config.yaml's canonical_sections lists it.
    assert "References" not in sections
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
    coverage_rule = next(entry for entry in strong if entry["filename"] == "coverage-gate.yaml")
    broken = {
        "filename": coverage_rule["filename"],
        "schema": {"rule": {"name": "coverage_threshold"}},
    }
    evaluation = evaluate_strong_rule(broken, {"coverage": {"project_src": 99}})
    assert evaluation["passed"] is False


def test_coverage_threshold_flags_missing_context_key() -> None:
    strong = load_strong_rules("template_project_rules")
    coverage_rule = next(entry for entry in strong if entry["filename"] == "coverage-gate.yaml")
    evaluation = evaluate_strong_rule(coverage_rule, {"coverage": {"project_src": 99}})
    assert evaluation["passed"] is False
    assert any("not provided in context" in v["message"] for v in evaluation["violations"])


def test_section_schema_flags_forbidden_heading() -> None:
    strong = load_strong_rules("template_manuscript_rules")
    section_rule = next(entry for entry in strong if entry["filename"] == "section-schema.yaml")
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
    reference_rule = next(entry for entry in strong if entry["filename"] == "reference-schema.yaml")
    evaluation = evaluate_strong_rule(reference_rule, {"references": ["not-a-mapping"]})
    assert evaluation["passed"] is False


def test_load_rule_context_detects_real_heading_matching_a_canonical_section(
    tmp_path: pathlib.Path,
) -> None:
    """A section that is BOTH a real heading AND config's canonical_sections
    entry is detected via the real heading — config.yaml plays no role."""
    project = tmp_path / "demo"
    manuscript = project / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "config.yaml").write_text(
        "project_config:\n  strong_rules:\n    canonical_sections:\n      - Abstract\n",
        encoding="utf-8",
    )
    (manuscript / "01_abstract.md").write_text("# Abstract {#sec:abstract}\n", encoding="utf-8")
    context = load_rule_context_from_project(project)
    assert context["manuscript_sections"] == ["Abstract"]


# ---------------------------------------------------------------------------
# Negative-control fixtures — malformed inputs, real violations, and real
# missing-context degradation. Each proves a real defect gets caught, not
# just that a line executes (TODO.md: "Add negative-control fixtures for
# malformed fonds/rules/tools payloads to exercise the fallback paths").
# ---------------------------------------------------------------------------


def test_evaluate_strong_rule_rejects_non_dict_schema() -> None:
    """An empty or malformed strong-rule YAML file (yaml.safe_load returns None
    or a non-dict) must degrade to a structured violation, not crash."""
    entry = {"filename": "empty.yaml", "schema": None}
    evaluation = evaluate_strong_rule(entry, {})
    assert evaluation["passed"] is False
    assert evaluation["violations"][0]["message"] == "schema missing top-level 'rule' mapping"


def test_load_rule_context_survives_malformed_config_yaml(tmp_path: pathlib.Path) -> None:
    """A hand-edit typo in config.yaml must not crash context loading."""
    project = tmp_path / "demo"
    manuscript = project / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "config.yaml").write_text("strong_rules: [unterminated\n", encoding="utf-8")
    context = load_rule_context_from_project(project)
    assert "coverage" not in context


def test_load_rule_context_ignores_non_dict_config_yaml(tmp_path: pathlib.Path) -> None:
    """Valid YAML that is a list, not a mapping, must not raise on .get()."""
    project = tmp_path / "demo"
    manuscript = project / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "config.yaml").write_text("- one\n- two\n", encoding="utf-8")
    context = load_rule_context_from_project(project)
    assert "coverage" not in context


def test_reference_schema_flags_missing_and_empty_fields() -> None:
    """A malformed BibTeX entry (empty author field, year entirely absent) is
    exactly the kind of real-world reference-schema violation this rule exists
    to catch — the project's own well-formed references.bib never exercises it."""
    strong = load_strong_rules("template_manuscript_rules")
    reference_rule = next(entry for entry in strong if entry["filename"] == "reference-schema.yaml")
    evaluation = evaluate_strong_rule(
        reference_rule,
        {
            "references": [
                {"key": "Smith2021", "authors": "", "title": "T", "type": "article"},
            ]
        },
    )
    assert evaluation["passed"] is False
    messages = [v["message"] for v in evaluation["violations"]]
    assert "reference[0] missing required field 'authors'" in messages
    assert "reference[0] missing required field 'year'" in messages


def test_module_structure_flags_forbidden_secrets_file(tmp_path: pathlib.Path) -> None:
    """module-structure.yaml's own stated rationale is preventing accidental
    credential-file commits — this proves that actually fires."""
    strong = load_strong_rules("template_project_rules")
    module_rule = next(entry for entry in strong if entry["filename"] == "module-structure.yaml")
    src = tmp_path / "src"
    src.mkdir()
    (src / "py.typed").write_text("", encoding="utf-8")
    (src / "__init__.py").write_text("", encoding="utf-8")
    (src / "secrets.py").write_text("", encoding="utf-8")
    evaluation = evaluate_strong_rule(module_rule, {"project_root": tmp_path})
    assert evaluation["passed"] is False
    assert any(
        "forbidden file matched under src/: secrets.py" in v["message"]
        for v in evaluation["violations"]
    )


def test_module_structure_flags_missing_required_src_files(tmp_path: pathlib.Path) -> None:
    """Distinct from the missing-src/-dir-entirely case: src/ exists but lacks
    the required py.typed and __init__.py marker files."""
    strong = load_strong_rules("template_project_rules")
    module_rule = next(entry for entry in strong if entry["filename"] == "module-structure.yaml")
    (tmp_path / "src").mkdir()
    evaluation = evaluate_strong_rule(module_rule, {"project_root": tmp_path})
    assert evaluation["passed"] is False
    messages = [v["message"] for v in evaluation["violations"]]
    assert "required src file missing: src/py.typed" in messages
    assert "required src file missing: src/__init__.py" in messages


def test_coverage_threshold_ignores_non_numeric_rule_minimum() -> None:
    """A malformed threshold value in the rule YAML itself (e.g. an
    accidentally-quoted percentage) is silently skipped, not raised on."""
    entry = {
        "filename": "coverage-gate.yaml",
        "schema": {
            "rule": {
                "name": "coverage_threshold",
                "constraints": {"project_src": "high-priority"},
            }
        },
    }
    evaluation = evaluate_strong_rule(entry, {"coverage": {"project_src": 10}})
    assert evaluation["passed"] is True
    assert evaluation["violations"] == []


def test_coverage_threshold_flags_non_numeric_measured_value() -> None:
    """A caller passing a stringly-typed coverage report is caught rather than
    silently coerced or crashing on float()."""
    strong = load_strong_rules("template_project_rules")
    coverage_rule = next(entry for entry in strong if entry["filename"] == "coverage-gate.yaml")
    evaluation = evaluate_strong_rule(
        coverage_rule,
        {"coverage": {"infrastructure": "60", "project_src": 95, "public_api": 99}},
    )
    assert evaluation["passed"] is False
    assert any(
        "coverage.infrastructure must be numeric, got str" in v["message"]
        for v in evaluation["violations"]
    )


def test_module_structure_flags_max_depth_violation(tmp_path: pathlib.Path) -> None:
    strong = load_strong_rules("template_project_rules")
    module_rule = next(entry for entry in strong if entry["filename"] == "module-structure.yaml")
    src = tmp_path / "src"
    deep = src / "a" / "b" / "c" / "d" / "e"
    deep.mkdir(parents=True)
    (src / "py.typed").write_text("", encoding="utf-8")
    (src / "__init__.py").write_text("", encoding="utf-8")
    (deep / "deep.py").write_text("", encoding="utf-8")
    evaluation = evaluate_strong_rule(module_rule, {"project_root": tmp_path})
    assert evaluation["passed"] is False
    assert any("exceeds max depth 4" in v["message"] for v in evaluation["violations"])


def test_module_structure_flags_synthetic_glob_forbidden_pattern(tmp_path: pathlib.Path) -> None:
    """Exercises the *.ext glob branch of forbidden_patterns, distinct from the
    named-file branch already covered by the secrets.py test above."""
    entry = {
        "filename": "synthetic-module-structure.yaml",
        "schema": {
            "rule": {
                "name": "module_structure",
                "forbidden_patterns": ["**/*.bak"],
            }
        },
    }
    src = tmp_path / "src"
    src.mkdir()
    (src / "leftover.bak").write_text("", encoding="utf-8")
    evaluation = evaluate_strong_rule(entry, {"project_root": tmp_path})
    assert evaluation["passed"] is False
    assert any(
        "forbidden file pattern matched under src/: **/*.bak" in v["message"]
        for v in evaluation["violations"]
    )


def test_load_rule_context_does_not_inject_canonical_section_without_real_heading(
    tmp_path: pathlib.Path,
) -> None:
    """Regression guard for the vacuous section-schema gate.

    `config.yaml` naming a canonical section ("Appendix") must NOT cause it
    to appear in `manuscript_sections` unless a real `# Appendix` heading
    exists — otherwise `section-schema.yaml`'s `required_sections` (drawn
    from this same canonical list) would compare the config's list against
    itself and could never detect a genuinely missing section.
    """
    project = tmp_path / "demo"
    manuscript = project / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "config.yaml").write_text(
        "strong_rules:\n  canonical_sections:\n    - Abstract\n    - Appendix\n",
        encoding="utf-8",
    )
    (manuscript / "01_abstract.md").write_text("# Abstract\n", encoding="utf-8")
    context = load_rule_context_from_project(project)
    assert context["manuscript_sections"] == ["Abstract"]
    assert "Appendix" not in context["manuscript_sections"]


def test_load_rule_context_handles_missing_manuscript_dir(tmp_path: pathlib.Path) -> None:
    context = load_rule_context_from_project(tmp_path)
    assert context["manuscript_sections"] == []
    assert context["references"] == []
    assert "coverage" not in context


def test_load_rule_context_skips_non_heading_md_file(tmp_path: pathlib.Path) -> None:
    project = tmp_path / "demo"
    manuscript = project / "manuscript"
    manuscript.mkdir(parents=True)
    (manuscript / "01_abstract.md").write_text("# Abstract\n", encoding="utf-8")
    (manuscript / "00_notes.md").write_text("Just some notes, no heading.\n", encoding="utf-8")
    context = load_rule_context_from_project(project)
    assert "Abstract" in context["manuscript_sections"]
    assert "Just some notes, no heading." not in context["manuscript_sections"]


def test_section_schema_ignores_non_forbidden_heading() -> None:
    """The forbidden-heading branch's negative case: a real heading that is
    NOT in the forbidden set must not produce a violation."""
    entry = {
        "filename": "synthetic-section-schema.yaml",
        "schema": {
            "rule": {
                "name": "section_schema",
                "forbidden_sections": ["TODO"],
            }
        },
    }
    evaluation = evaluate_strong_rule(entry, {"forbidden_sections_found": ["Some Other Heading"]})
    assert evaluation["passed"] is True
    assert evaluation["violations"] == []


def test_evaluate_strong_rule_module_structure_missing_project_root() -> None:
    strong = load_strong_rules("template_project_rules")
    module_rule = next(entry for entry in strong if entry["filename"] == "module-structure.yaml")
    evaluation = evaluate_strong_rule(module_rule, {})
    assert evaluation["passed"] is True
    assert evaluation["violations"] == []


@pytest.mark.parametrize("filename", ["coverage-gate.yaml", "reference-schema.yaml"])
def test_missing_context_key_vacuous_pass(filename: str) -> None:
    """coverage_threshold and reference_schema both degrade to a vacuous pass
    when their required context key is absent entirely (as opposed to present
    but empty) — distinct from section_schema, whose vacuous-pass path is
    already covered elsewhere."""
    rule_set = (
        "template_project_rules"
        if filename == "coverage-gate.yaml"
        else "template_manuscript_rules"
    )
    strong = load_strong_rules(rule_set)
    rule = next(entry for entry in strong if entry["filename"] == filename)
    evaluation = evaluate_strong_rule(rule, {})
    assert evaluation["passed"] is True
    assert evaluation["violations"] == []


def test_section_schema_skips_malformed_required_section_entries() -> None:
    """A required_sections entry that is not a dict, or lacks a string name,
    must be skipped rather than raising — a rule-authoring mistake, not a
    manuscript defect, so it should not crash the evaluator."""
    entry = {
        "filename": "synthetic-section-schema.yaml",
        "schema": {
            "rule": {
                "name": "section_schema",
                "required_sections": ["not-a-dict", {"name": 42}, {"name": "Abstract"}],
            }
        },
    }
    evaluation = evaluate_strong_rule(entry, {"manuscript_sections": ["Abstract"]})
    assert evaluation["passed"] is True
    assert evaluation["violations"] == []


def test_reference_schema_required_fields_non_string_entry_skipped() -> None:
    """A non-string entry in required_fields (a rule-authoring mistake) must be
    skipped rather than raising when compared against a real reference record."""
    entry = {
        "filename": "synthetic-reference-schema.yaml",
        "schema": {
            "rule": {
                "name": "reference_schema",
                "required_fields": ["key", 42],
            }
        },
    }
    evaluation = evaluate_strong_rule(entry, {"references": [{"key": "Smith2021"}]})
    assert evaluation["passed"] is True
    assert not any("42" in v["message"] for v in evaluation["violations"])


# ---------------------------------------------------------------------------
# manifest_freshness — a fifth evaluator (dispatch + logic implemented and
# unit-tested against synthetic rule dicts). Deliberately NOT wired to a real
# strong-rule YAML file: that would require writing into the shared
# rules/templates/*/strong/ tree, which this project's own read-only
# invariant reserves for a separate, explicit decision. See
# manuscript/07_conclusion.md.
# ---------------------------------------------------------------------------


def test_manifest_freshness_flags_stale_version() -> None:
    entry = {
        "filename": "synthetic-manifest-freshness.yaml",
        "schema": {"rule": {"name": "manifest_freshness"}},
    }
    context = {
        "fond_freshness": [
            {"name": "template_bibliography", "manifest_mtime": 100.0, "latest_data_mtime": 200.0},
        ]
    }
    evaluation = evaluate_strong_rule(entry, context)
    assert evaluation["passed"] is False
    assert (
        "fond 'template_bibliography': data/ changed after fonds.yaml was last modified"
        in evaluation["violations"][0]["message"]
    )


def test_manifest_freshness_passes_when_version_bumped() -> None:
    entry = {
        "filename": "synthetic-manifest-freshness.yaml",
        "schema": {"rule": {"name": "manifest_freshness"}},
    }
    context = {
        "fond_freshness": [
            {"name": "template_bibliography", "manifest_mtime": 300.0, "latest_data_mtime": 200.0},
        ]
    }
    evaluation = evaluate_strong_rule(entry, context)
    assert evaluation["passed"] is True
    assert evaluation["violations"] == []


def test_manifest_freshness_ignores_missing_context() -> None:
    entry = {
        "filename": "synthetic-manifest-freshness.yaml",
        "schema": {"rule": {"name": "manifest_freshness"}},
    }
    evaluation = evaluate_strong_rule(entry, {})
    assert evaluation["passed"] is True
    assert evaluation["violations"] == []


def test_manifest_freshness_skips_malformed_records() -> None:
    entry = {
        "filename": "synthetic-manifest-freshness.yaml",
        "schema": {"rule": {"name": "manifest_freshness"}},
    }
    context = {
        "fond_freshness": [
            "not-a-dict",
            {"name": 42, "manifest_mtime": 1.0, "latest_data_mtime": 2.0},
            {"name": "ok", "manifest_mtime": "not-a-number", "latest_data_mtime": 2.0},
        ]
    }
    evaluation = evaluate_strong_rule(entry, context)
    assert evaluation["passed"] is True
    assert evaluation["violations"] == []


def test_evaluate_strong_rule_unrecognized_rule_name_is_structural_only() -> None:
    """A rule kind with no registered evaluator (e.g. a future kind not yet
    implemented) must degrade to structural-only, never crash the dispatch."""
    entry = {
        "filename": "future.yaml",
        "schema": {"rule": {"name": "future_unimplemented_kind"}},
    }
    evaluation = evaluate_strong_rule(entry, {})
    assert evaluation["passed"] is True
    assert evaluation["violations"] == []
