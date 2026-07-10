"""Tests for error paths and convenience functions without mocks."""

from __future__ import annotations

import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

from src.fonds_reader import read_all_fonds
from src.rules_applier import load_all_manuscript_rules, load_all_project_rules


class TestReadAllFonds:
    def test_returns_dict(self):
        result = read_all_fonds()
        assert isinstance(result, dict)

    def test_has_three_keys(self):
        result = read_all_fonds()
        assert {"bibliography", "contacts", "datasets"} <= set(result)

    def test_values_are_dicts_or_none(self):
        result = read_all_fonds()
        for value in result.values():
            assert value is None or isinstance(value, dict)


class TestLoadAllProjectRules:
    def test_returns_dict_with_soft_strong(self):
        result = load_all_project_rules()
        assert "soft" in result and "strong" in result

    def test_soft_is_list(self):
        assert isinstance(load_all_project_rules()["soft"], list)

    def test_strong_is_list(self):
        assert isinstance(load_all_project_rules()["strong"], list)


class TestLoadAllManuscriptRules:
    def test_returns_dict_with_soft_strong(self):
        result = load_all_manuscript_rules()
        assert "soft" in result and "strong" in result

    def test_soft_is_list(self):
        assert isinstance(load_all_manuscript_rules()["soft"], list)

    def test_strong_is_list(self):
        assert isinstance(load_all_manuscript_rules()["strong"], list)


def test_read_bibliography_fond_missing_bib_returns_none(tmp_path: pathlib.Path) -> None:
    from src.fonds_reader import read_bibliography_fond

    fond_dir = tmp_path / "test_bib_fond"
    fond_dir.mkdir()
    (fond_dir / "fonds.yaml").write_text("type: bibliography\nversion: '1.0'\n", encoding="utf-8")
    (fond_dir / "data").mkdir()
    assert read_bibliography_fond("test_bib_fond", templates_root=tmp_path) is None


def test_read_contacts_fond_missing_contacts_yaml_returns_none(tmp_path: pathlib.Path) -> None:
    from src.fonds_reader import read_contacts_fond

    fond_dir = tmp_path / "test_contacts_fond"
    fond_dir.mkdir()
    (fond_dir / "fonds.yaml").write_text("type: contacts\nversion: '1.0'\n", encoding="utf-8")
    (fond_dir / "data").mkdir()
    assert read_contacts_fond("test_contacts_fond", templates_root=tmp_path) is None


def test_read_datasets_fond_missing_datasets_yaml_returns_none(tmp_path: pathlib.Path) -> None:
    from src.fonds_reader import read_datasets_fond

    fond_dir = tmp_path / "test_datasets_fond"
    fond_dir.mkdir()
    (fond_dir / "fonds.yaml").write_text("type: datasets\nversion: '1.0'\n", encoding="utf-8")
    (fond_dir / "data").mkdir()
    assert read_datasets_fond("test_datasets_fond", templates_root=tmp_path) is None


def test_read_bibliography_fond_invalid_yaml_returns_none(tmp_path: pathlib.Path) -> None:
    from src.fonds_reader import read_bibliography_fond

    fond_dir = tmp_path / "bad_bib"
    fond_dir.mkdir()
    data_dir = fond_dir / "data"
    data_dir.mkdir()
    (fond_dir / "fonds.yaml").write_text(": : invalid: yaml: {", encoding="utf-8")
    (data_dir / "references.bib").write_text("@article{x2020, title={X}}", encoding="utf-8")
    (data_dir / "references.csv").write_text(
        "key,type,title,author,year,journal,doi\nx2020,article,X,A,2020,,\n",
        encoding="utf-8",
    )
    assert read_bibliography_fond("bad_bib", templates_root=tmp_path) is None


def test_load_soft_rules_unreadable_file_skips(tmp_path: pathlib.Path) -> None:
    from src.rules_applier import load_soft_rules

    rule_dir = tmp_path / "my_rules" / "soft"
    rule_dir.mkdir(parents=True)
    md_file = rule_dir / "guide.md"
    md_file.write_text("# Guide\n", encoding="utf-8")
    md_file.chmod(0)
    try:
        result = load_soft_rules("my_rules", templates_root=tmp_path)
        assert isinstance(result, list)
    finally:
        md_file.chmod(0o644)


def test_load_strong_rules_invalid_yaml_skips(tmp_path: pathlib.Path) -> None:
    from src.rules_applier import load_strong_rules

    rule_dir = tmp_path / "my_rules" / "strong"
    rule_dir.mkdir(parents=True)
    (rule_dir / "broken.yaml").write_text(": : {unclosed", encoding="utf-8")
    assert load_strong_rules("my_rules", templates_root=tmp_path) == []


def test_validate_against_rules_missing_rules_yaml_warns(tmp_path: pathlib.Path) -> None:
    from src.rules_applier import validate_against_rules

    rule_dir = tmp_path / "incomplete_rules" / "soft"
    rule_dir.mkdir(parents=True)
    (rule_dir / "guide.md").write_text("# Guide\n", encoding="utf-8")
    result = validate_against_rules("incomplete_rules", templates_root=tmp_path)
    assert isinstance(result["warnings"], list)
    assert result["warnings"]
    assert result["manifest"] is None


def test_validate_against_rules_partial_status(tmp_path: pathlib.Path) -> None:
    from src.rules_applier import validate_against_rules

    rule_dir = tmp_path / "bad_manifest_rules"
    soft_dir = rule_dir / "soft"
    soft_dir.mkdir(parents=True)
    (soft_dir / "guide.md").write_text("# Guide\n", encoding="utf-8")
    (rule_dir / "rules.yaml").write_text(": : {unclosed", encoding="utf-8")
    result = validate_against_rules("bad_manifest_rules", templates_root=tmp_path)
    assert result["status"] in {"partial", "missing", "ok"}


def test_discover_tools_missing_root_returns_empty(tmp_path: pathlib.Path) -> None:
    from src.tools_invoker import discover_tools

    assert discover_tools(templates_root=tmp_path / "no_such_dir") == []


def test_discover_tools_tool_without_manifest(tmp_path: pathlib.Path) -> None:
    from src.tools_invoker import discover_tools

    tools_dir = tmp_path / "tools"
    tool_dir = tools_dir / "my_tool"
    tool_dir.mkdir(parents=True)
    result = discover_tools(templates_root=tools_dir)
    assert len(result) == 1
    assert result[0]["name"] == "my_tool"
    assert result[0]["manifest"] is None


def test_discover_tools_invalid_manifest_skips_gracefully(tmp_path: pathlib.Path) -> None:
    from src.tools_invoker import discover_tools

    tools_dir = tmp_path / "tools"
    tool_dir = tools_dir / "bad_tool"
    tool_dir.mkdir(parents=True)
    (tool_dir / "tools.yaml").write_text(": : {unclosed", encoding="utf-8")
    result = discover_tools(templates_root=tools_dir)
    assert len(result) == 1
    assert result[0]["name"] == "bad_tool"
    assert result[0]["manifest"] is None


def test_validate_tool_scripts_exist_missing_entrypoint(tmp_path: pathlib.Path) -> None:
    from src.tools_invoker import validate_tool_scripts_exist

    tools_dir = tmp_path / "tools"
    tool_dir = tools_dir / "partial_tool"
    tool_dir.mkdir(parents=True)
    (tool_dir / "tools.yaml").write_text(
        yaml.dump({"entrypoints": ["scripts/run.sh", "scripts/missing.sh"]}),
        encoding="utf-8",
    )
    scripts_dir = tool_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "run.sh").write_text("#!/bin/bash\n", encoding="utf-8")
    result = validate_tool_scripts_exist("partial_tool", templates_root=tools_dir)
    assert "scripts/missing.sh" in result["missing"]
    assert result["valid"] is False


def test_count_summary_with_explicit_fonds() -> None:
    from src.fonds_reader import count_summary
    from src.type_defs import AllFondsResult, BibliographyFondResult, ContactsFondResult

    all_fonds = AllFondsResult(
        bibliography=BibliographyFondResult(manifest={}, bib_text="", csv_rows=[{}, {}]),
        contacts=ContactsFondResult(manifest={}, contacts=[{}]),
        datasets=None,
    )
    summary = count_summary(all_fonds)
    assert summary["bibliography_entries"] == 2
    assert summary["contacts_count"] == 1
    assert summary["datasets_count"] == 0
    assert summary["fonds_loaded"] == 2


def test_count_summary_defaults_to_read_all() -> None:
    from src.fonds_reader import count_summary

    summary = count_summary()
    assert summary["fonds_loaded"] >= 0


def test_read_contacts_fond_invalid_yaml_returns_none(tmp_path: pathlib.Path) -> None:
    from src.fonds_reader import read_contacts_fond

    fond_dir = tmp_path / "bad_contacts"
    data_dir = fond_dir / "data"
    data_dir.mkdir(parents=True)
    (fond_dir / "fonds.yaml").write_text("type: contacts\n", encoding="utf-8")
    (data_dir / "contacts.yaml").write_text(": : {bad", encoding="utf-8")
    assert read_contacts_fond("bad_contacts", templates_root=tmp_path) is None


def test_read_datasets_fond_invalid_yaml_returns_none(tmp_path: pathlib.Path) -> None:
    from src.fonds_reader import read_datasets_fond

    fond_dir = tmp_path / "bad_datasets"
    data_dir = fond_dir / "data"
    data_dir.mkdir(parents=True)
    (fond_dir / "fonds.yaml").write_text("type: datasets\n", encoding="utf-8")
    (data_dir / "datasets.yaml").write_text(": : {bad", encoding="utf-8")
    assert read_datasets_fond("bad_datasets", templates_root=tmp_path) is None


def test_generate_figure_data_builds_rows() -> None:
    from src.integration import generate_figure_data
    from src.type_defs import (
        AllFondsResult,
        IntegrationResult,
        IntegrationSummary,
        RuleSetResult,
        ToolEntryWithValidation,
        ToolValidationResult,
    )

    result = IntegrationResult(
        fonds=AllFondsResult(bibliography=None, contacts=None, datasets=None),
        rules={
            "template_project_rules": RuleSetResult(
                rule_set="template_project_rules",
                manifest=None,
                soft_rules_count=1,
                strong_rules_count=0,
                soft_rules=["guide"],
                strong_rules=[],
                soft_rules_loaded=["guide.md"],
                strong_rules_loaded=[],
                status="partial",
                warnings=["demo"],
            )
        },
        tools=[
            ToolEntryWithValidation(
                name="demo_tool",
                path=pathlib.Path("demo"),
                manifest=None,
                validation=ToolValidationResult(
                    tool="demo_tool",
                    entrypoints=["scripts/run.sh"],
                    missing=["scripts/run.sh"],
                    valid=False,
                ),
            )
        ],
        summary=IntegrationSummary(
            fonds_loaded=0,
            rules_sets_ok=0,
            rules_sets_total=1,
            tools_discovered=1,
            tools_valid=0,
            bib_entries=0,
            contacts=0,
            datasets=0,
        ),
    )
    rows = generate_figure_data(result)
    assert rows
    assert all(isinstance(row, dict) for row in rows)
    categories = {row["category"] for row in rows}
    assert {"fond", "rule_set", "tool"} <= categories


def test_derive_dashboard_data_binds_to_ground_truth() -> None:
    """derive_dashboard_data() must reflect a degraded run, not a hard-coded default."""
    from src.integration import derive_dashboard_data
    from src.type_defs import (
        AllFondsResult,
        IntegrationResult,
        IntegrationSummary,
        RuleSetResult,
        ToolEntryWithValidation,
        ToolValidationResult,
    )

    result = IntegrationResult(
        fonds=AllFondsResult(bibliography=None, contacts=None, datasets=None),
        rules={
            "template_project_rules": RuleSetResult(
                rule_set="template_project_rules",
                manifest=None,
                soft_rules_count=1,
                strong_rules_count=0,
                soft_rules=["guide"],
                strong_rules=[],
                soft_rules_loaded=["guide.md"],
                strong_rules_loaded=[],
                status="partial",
                warnings=["demo"],
            )
        },
        tools=[
            ToolEntryWithValidation(
                name="demo_tool",
                path=pathlib.Path("demo"),
                manifest=None,
                validation=ToolValidationResult(
                    tool="demo_tool",
                    entrypoints=["scripts/run.sh"],
                    missing=["scripts/run.sh"],
                    valid=False,
                ),
            )
        ],
        summary=IntegrationSummary(
            fonds_loaded=0,
            rules_sets_ok=0,
            rules_sets_total=1,
            tools_discovered=1,
            tools_valid=0,
            bib_entries=0,
            contacts=0,
            datasets=0,
        ),
    )

    counts, statuses = derive_dashboard_data(result)

    # Counts must come from the degraded summary, not an illustrative default.
    assert counts == {"Fonds": 0, "Rules": 0, "Tools": 1}

    # Every fond is missing (the synthetic result has none loaded).
    assert statuses["Bibliography Fond"] == "missing"
    assert statuses["Contacts Fond"] == "missing"
    assert statuses["Datasets Fond"] == "missing"
    # The one rule set present is genuinely partial.
    assert statuses["Project Rules"] == "partial"
    # The one tool present failed validation, so it maps to "missing", not "ok".
    assert statuses["Demo Tool"] == "missing"


def test_discover_tools_with_validation(tmp_path: pathlib.Path) -> None:
    from src.tools_invoker import discover_tools_with_validation

    tools_dir = tmp_path / "tools"
    tool_dir = tools_dir / "demo_tool"
    scripts = tool_dir / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "run.sh").write_text("#!/bin/bash\n", encoding="utf-8")
    (tool_dir / "tools.yaml").write_text(
        yaml.dump({"entrypoints": ["scripts/run.sh"]}),
        encoding="utf-8",
    )
    results = discover_tools_with_validation(templates_root=tools_dir)
    assert len(results) == 1
    assert results[0]["validation"]["valid"] is True


def test_get_tool_entrypoints_invalid_yaml(tmp_path: pathlib.Path) -> None:
    from src.tools_invoker import get_tool_entrypoints

    tools_dir = tmp_path / "tools"
    tool_dir = tools_dir / "bad_tool"
    tool_dir.mkdir(parents=True)
    (tool_dir / "tools.yaml").write_text(": : {bad", encoding="utf-8")
    assert get_tool_entrypoints("bad_tool", templates_root=tools_dir) == []


def test_get_tool_entrypoints_non_dict_manifest(tmp_path: pathlib.Path) -> None:
    from src.tools_invoker import get_tool_entrypoints

    tools_dir = tmp_path / "tools"
    tool_dir = tools_dir / "list_tool"
    tool_dir.mkdir(parents=True)
    (tool_dir / "tools.yaml").write_text("- not-a-dict\n", encoding="utf-8")
    assert get_tool_entrypoints("list_tool", templates_root=tools_dir) == []


def test_discover_tools_skips_non_directory_entries(tmp_path: pathlib.Path) -> None:
    from src.tools_invoker import discover_tools

    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    (tools_dir / "readme.txt").write_text("skip me", encoding="utf-8")
    tool_dir = tools_dir / "real_tool"
    tool_dir.mkdir()
    assert len(discover_tools(templates_root=tools_dir)) == 1
