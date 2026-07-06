"""test_rules_applier.py — Tests for rules_applier.py using real rule exemplars.

Tests skip gracefully when rule directories are absent.
Includes edge-case tests for empty directories, malformed YAML, deeply nested
structures, and the load_all_project_rules / load_all_manuscript_rules helpers.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

from src.rules_applier import (
    get_rules_root,
    load_all_manuscript_rules,
    load_all_project_rules,
    load_soft_rules,
    load_strong_rules,
    validate_against_rules,
)

# ---------------------------------------------------------------------------
# Path guards
# ---------------------------------------------------------------------------

_PROJECT_RULES_DIR = get_rules_root() / "template_project_rules"
_PROJECT_SOFT = _PROJECT_RULES_DIR / "soft"
_PROJECT_STRONG = _PROJECT_RULES_DIR / "strong"

_MANUSCRIPT_RULES_DIR = get_rules_root() / "template_manuscript_rules"
_MANUSCRIPT_SOFT = _MANUSCRIPT_RULES_DIR / "soft"
_MANUSCRIPT_STRONG = _MANUSCRIPT_RULES_DIR / "strong"


# ---------------------------------------------------------------------------
# load_soft_rules
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _PROJECT_SOFT.is_dir(),
    reason="template_project_rules/soft/ not present",
)
class TestLoadSoftRulesProject:
    def test_returns_list(self):
        result = load_soft_rules("template_project_rules")
        assert isinstance(result, list)

    def test_nonempty(self):
        result = load_soft_rules("template_project_rules")
        assert len(result) > 0

    def test_each_entry_has_filename_and_content(self):
        result = load_soft_rules("template_project_rules")
        for entry in result:
            assert "filename" in entry
            assert "content" in entry
            assert isinstance(entry["content"], str)
            assert len(entry["content"]) > 0

    def test_filenames_are_md(self):
        result = load_soft_rules("template_project_rules")
        for entry in result:
            assert entry["filename"].endswith(".md"), entry["filename"]


@pytest.mark.skipif(
    not _MANUSCRIPT_SOFT.is_dir(),
    reason="template_manuscript_rules/soft/ not present",
)
class TestLoadSoftRulesManuscript:
    def test_returns_nonempty_list(self):
        result = load_soft_rules("template_manuscript_rules")
        assert len(result) > 0


def test_load_soft_rules_missing_returns_empty():
    result = load_soft_rules("__nonexistent_rule_set__")
    assert result == []


# ---------------------------------------------------------------------------
# load_strong_rules
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _PROJECT_STRONG.is_dir(),
    reason="template_project_rules/strong/ not present",
)
class TestLoadStrongRulesProject:
    def test_returns_list(self):
        result = load_strong_rules("template_project_rules")
        assert isinstance(result, list)

    def test_nonempty(self):
        result = load_strong_rules("template_project_rules")
        assert len(result) > 0

    def test_each_entry_has_schema(self):
        result = load_strong_rules("template_project_rules")
        for entry in result:
            assert "filename" in entry
            assert "schema" in entry
            assert isinstance(entry["schema"], dict)

    def test_schema_has_rule_key(self):
        result = load_strong_rules("template_project_rules")
        for entry in result:
            assert "rule" in entry["schema"], (
                f"Strong rule {entry['filename']} has no 'rule' top-level key"
            )

    def test_rule_has_name_and_kind(self):
        result = load_strong_rules("template_project_rules")
        for entry in result:
            rule = entry["schema"]["rule"]
            assert "name" in rule, f"{entry['filename']}: rule.name missing"
            assert "kind" in rule, f"{entry['filename']}: rule.kind missing"
            assert rule["kind"] == "strong"

    def test_coverage_gate_yaml_present(self):
        result = load_strong_rules("template_project_rules")
        filenames = [r["filename"] for r in result]
        assert "coverage-gate.yaml" in filenames

    def test_module_structure_yaml_present(self):
        result = load_strong_rules("template_project_rules")
        filenames = [r["filename"] for r in result]
        assert "module-structure.yaml" in filenames


@pytest.mark.skipif(
    not _MANUSCRIPT_STRONG.is_dir(),
    reason="template_manuscript_rules/strong/ not present",
)
class TestLoadStrongRulesManuscript:
    def test_returns_nonempty_list(self):
        result = load_strong_rules("template_manuscript_rules")
        assert len(result) > 0

    def test_reference_schema_present(self):
        result = load_strong_rules("template_manuscript_rules")
        filenames = [r["filename"] for r in result]
        assert "reference-schema.yaml" in filenames


def test_load_strong_rules_missing_returns_empty():
    result = load_strong_rules("__nonexistent_rule_set__")
    assert result == []


# ---------------------------------------------------------------------------
# validate_against_rules
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _PROJECT_RULES_DIR.is_dir(),
    reason="template_project_rules/ not present",
)
class TestValidateAgainstRulesProject:
    def test_returns_dict(self):
        result = validate_against_rules("template_project_rules")
        assert isinstance(result, dict)

    def test_status_ok(self):
        result = validate_against_rules("template_project_rules")
        assert result["status"] == "ok", f"Unexpected status: {result}"

    def test_soft_and_strong_counts_positive(self):
        result = validate_against_rules("template_project_rules")
        assert result["soft_rules_count"] > 0
        assert result["strong_rules_count"] > 0

    def test_manifest_present(self):
        result = validate_against_rules("template_project_rules")
        assert result["manifest"] is not None
        assert result["manifest"]["type"] == "project"

    def test_no_warnings_for_valid_rule_set(self):
        result = validate_against_rules("template_project_rules")
        assert result["warnings"] == []


def test_validate_missing_rule_set_returns_missing_status():
    result = validate_against_rules("__nonexistent_rule_set__")
    assert result["status"] == "missing"
    assert result["soft_rules_count"] == 0
    assert result["strong_rules_count"] == 0


# ---------------------------------------------------------------------------
# Edge cases: empty strong/ directory
# ---------------------------------------------------------------------------


class TestEmptyStrongDirectory:
    """strong/ exists but contains no YAML files → empty list, no exception."""

    def test_empty_strong_dir_returns_empty_list(self, tmp_path: pathlib.Path):
        # Simulate a rule-set that has a strong/ dir with no YAML files
        # We do this by monkey-patching the rules root temporarily.
        import src.rules_applier as ra

        rule_set = "test_empty_strong"
        strong_dir = tmp_path / rule_set / "strong"
        strong_dir.mkdir(parents=True)
        # Add a non-YAML file to ensure glob("*.yaml") correctly returns nothing
        (strong_dir / "README.md").write_text("# not a yaml rule\n")

        original_root = ra._rules_root  # noqa: SLF001
        ra._rules_root = lambda: tmp_path  # type: ignore[assignment]
        try:
            result = load_strong_rules(rule_set)
            assert isinstance(result, list)
            assert result == [], f"Expected empty list, got: {result}"
        finally:
            ra._rules_root = original_root  # type: ignore[assignment]

    def test_empty_soft_dir_returns_empty_list(self, tmp_path: pathlib.Path):
        import src.rules_applier as ra

        rule_set = "test_empty_soft"
        soft_dir = tmp_path / rule_set / "soft"
        soft_dir.mkdir(parents=True)
        # Add a .yaml file to ensure only .md files are picked up
        (soft_dir / "not_markdown.yaml").write_text("rule: foo\n")

        original_root = ra._rules_root  # noqa: SLF001
        ra._rules_root = lambda: tmp_path  # type: ignore[assignment]
        try:
            result = load_soft_rules(rule_set)
            assert isinstance(result, list)
            assert result == [], f"Expected empty list, got: {result}"
        finally:
            ra._rules_root = original_root  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Edge cases: malformed YAML files
# ---------------------------------------------------------------------------


class TestMalformedYAML:
    """Malformed YAML strong rules should be skipped with a warning, not raise."""

    def test_malformed_yaml_is_skipped(self, tmp_path: pathlib.Path):
        import src.rules_applier as ra

        rule_set = "test_malformed"
        strong_dir = tmp_path / rule_set / "strong"
        strong_dir.mkdir(parents=True)
        # Write invalid YAML (unclosed brace)
        (strong_dir / "bad.yaml").write_text("rule: {name: foo, broken: \n")
        # Write a valid YAML rule alongside
        (strong_dir / "good.yaml").write_text("rule:\n  name: valid_rule\n  kind: strong\n")

        original_root = ra._rules_root  # noqa: SLF001
        ra._rules_root = lambda: tmp_path  # type: ignore[assignment]
        try:
            result = load_strong_rules(rule_set)
            # Only the valid rule should appear
            filenames = [r["filename"] for r in result]
            assert "good.yaml" in filenames
            assert "bad.yaml" not in filenames
        finally:
            ra._rules_root = original_root  # type: ignore[assignment]

    def test_all_malformed_yaml_returns_empty_list(self, tmp_path: pathlib.Path):
        import src.rules_applier as ra

        rule_set = "test_all_malformed"
        strong_dir = tmp_path / rule_set / "strong"
        strong_dir.mkdir(parents=True)
        (strong_dir / "bad1.yaml").write_text(": :invalid: yaml: {\n")
        (strong_dir / "bad2.yaml").write_text("{{also bad}}\n")

        original_root = ra._rules_root  # noqa: SLF001
        ra._rules_root = lambda: tmp_path  # type: ignore[assignment]
        try:
            result = load_strong_rules(rule_set)
            assert isinstance(result, list)
            assert result == []
        finally:
            ra._rules_root = original_root  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Edge cases: deeply nested rule structures
# ---------------------------------------------------------------------------


class TestDeeplyNestedRuleStructures:
    """load_strong_rules must handle YAML with arbitrary nesting depth."""

    def test_deeply_nested_schema_is_loaded(self, tmp_path: pathlib.Path):
        import src.rules_applier as ra

        rule_set = "test_nested"
        strong_dir = tmp_path / rule_set / "strong"
        strong_dir.mkdir(parents=True)
        nested_yaml = (
            "rule:\n"
            "  name: deep_rule\n"
            "  kind: strong\n"
            "  constraints:\n"
            "    level1:\n"
            "      level2:\n"
            "        level3:\n"
            "          level4:\n"
            "            value: 42\n"
            "            nested_list:\n"
            "              - a\n"
            "              - b\n"
            "              - c\n"
        )
        (strong_dir / "nested.yaml").write_text(nested_yaml)

        original_root = ra._rules_root  # noqa: SLF001
        ra._rules_root = lambda: tmp_path  # type: ignore[assignment]
        try:
            result = load_strong_rules(rule_set)
            assert len(result) == 1
            schema = result[0]["schema"]
            assert schema["rule"]["name"] == "deep_rule"
            # Verify deep access
            deep = schema["rule"]["constraints"]["level1"]["level2"]["level3"]["level4"]
            assert deep["value"] == 42
            assert deep["nested_list"] == ["a", "b", "c"]
        finally:
            ra._rules_root = original_root  # type: ignore[assignment]

    def test_soft_rule_with_large_content_is_loaded(self, tmp_path: pathlib.Path):
        import src.rules_applier as ra

        rule_set = "test_large_soft"
        soft_dir = tmp_path / rule_set / "soft"
        soft_dir.mkdir(parents=True)
        # Simulate a soft rule with many sections
        large_content = "\n".join(
            [f"## Section {i}\n\nContent for section {i}.\n" for i in range(50)]
        )
        (soft_dir / "large_rule.md").write_text(large_content)

        original_root = ra._rules_root  # noqa: SLF001
        ra._rules_root = lambda: tmp_path  # type: ignore[assignment]
        try:
            result = load_soft_rules(rule_set)
            assert len(result) == 1
            assert len(result[0]["content"]) > 100
        finally:
            ra._rules_root = original_root  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# load_all_project_rules and load_all_manuscript_rules signatures
# ---------------------------------------------------------------------------


class TestLoadAllProjectRules:
    def test_returns_dict(self):
        result = load_all_project_rules()
        assert isinstance(result, dict)

    def test_has_soft_and_strong_keys(self):
        result = load_all_project_rules()
        assert "soft" in result, "Expected 'soft' key in load_all_project_rules()"
        assert "strong" in result, "Expected 'strong' key in load_all_project_rules()"

    def test_soft_is_list(self):
        result = load_all_project_rules()
        assert isinstance(result["soft"], list)

    def test_strong_is_list(self):
        result = load_all_project_rules()
        assert isinstance(result["strong"], list)

    def test_no_extra_unexpected_keys(self):
        result = load_all_project_rules()
        assert set(result.keys()) == {"soft", "strong"}


class TestLoadAllManuscriptRules:
    def test_returns_dict(self):
        result = load_all_manuscript_rules()
        assert isinstance(result, dict)

    def test_has_soft_and_strong_keys(self):
        result = load_all_manuscript_rules()
        assert "soft" in result
        assert "strong" in result

    def test_soft_is_list(self):
        result = load_all_manuscript_rules()
        assert isinstance(result["soft"], list)

    def test_strong_is_list(self):
        result = load_all_manuscript_rules()
        assert isinstance(result["strong"], list)

    def test_no_extra_unexpected_keys(self):
        result = load_all_manuscript_rules()
        assert set(result.keys()) == {"soft", "strong"}

    def test_never_raises_when_manuscript_rules_absent(self, tmp_path: pathlib.Path):
        """Even when the manuscript rules dir is completely absent, no exception."""
        import src.rules_applier as ra

        original_root = ra._rules_root  # noqa: SLF001
        ra._rules_root = lambda: tmp_path  # type: ignore[assignment]
        try:
            result = load_all_manuscript_rules()
            assert isinstance(result, dict)
            assert result["soft"] == []
            assert result["strong"] == []
        finally:
            ra._rules_root = original_root  # type: ignore[assignment]
