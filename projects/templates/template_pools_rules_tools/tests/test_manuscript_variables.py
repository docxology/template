"""test_manuscript_variables.py — Tests for the manuscript_variables module.

Exercises generate_variables() against the real repo fonds/rules/tools
resources (same fixtures test_integration.py relies on) — no mocks.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

from src.figure_support import (
    COVER_FIGURE_FILENAMES,
    INTEGRATION_FIGURE_SPECS,
    IntegrationFigureSpec,
)
from src.manuscript_variables import generate_variables


class TestGenerateVariables:
    def test_returns_dict(self):
        result = generate_variables()
        assert isinstance(result, dict)

    def test_all_values_are_strings(self):
        result = generate_variables()
        for key, value in result.items():
            assert isinstance(value, str), f"{key}: expected str, got {type(value)}"

    def test_expected_keys_present(self):
        result = generate_variables()
        expected = {
            "FONDS_LOADED",
            "FONDS_EXPECTED",
            "RULES_SETS_OK",
            "RULES_SETS_TOTAL",
            "TOOLS_DISCOVERED",
            "TOOLS_VALID",
            "BIB_ENTRIES",
            "CONTACTS_COUNT",
            "DATASETS_COUNT",
            "STRONG_RULES_PROJECT",
            "STRONG_RULES_MANUSCRIPT",
            "CONTENT_FIGURES",
            "COVER_FIGURES",
            "TOTAL_FIGURES",
            "SRC_MODULES",
            "TEST_FILES",
            "ORCHESTRATION_SCRIPTS",
            "TOOL_NAMES",
        }
        assert expected.issubset(result.keys())

    def test_uppercase_keys_only(self):
        """Every key must match the {{UPPERCASE_KEY}} injection token pattern."""
        result = generate_variables()
        for key in result:
            assert key[0].isascii() and key[0].isupper(), f"key {key!r} must start uppercase"
            assert key == key.upper(), f"key {key!r} must be fully uppercase"

    def test_numeric_fields_are_numeric_strings(self):
        result = generate_variables()
        assert result["FONDS_LOADED"].isdigit()
        assert result["FONDS_EXPECTED"].isdigit()
        assert result["TOOLS_DISCOVERED"].isdigit()
        assert result["CONTENT_FIGURES"].isdigit()
        assert result["COVER_FIGURES"].isdigit()
        assert result["TOTAL_FIGURES"].isdigit()
        assert result["SRC_MODULES"].isdigit()
        assert result["TEST_FILES"].isdigit()
        assert result["ORCHESTRATION_SCRIPTS"].isdigit()

    def test_figure_counts_match_declared_content_and_cover_contracts(self):
        result = generate_variables()

        assert result["CONTENT_FIGURES"] == str(len(INTEGRATION_FIGURE_SPECS))
        assert result["COVER_FIGURES"] == str(len(COVER_FIGURE_FILENAMES))
        assert result["TOTAL_FIGURES"] == str(
            len(INTEGRATION_FIGURE_SPECS) + len(COVER_FIGURE_FILENAMES)
        )

    def test_figure_counts_move_when_declared_contract_moves(self):
        """Negative control: figure claims must not be frozen numeric literals."""
        extra_content = IntegrationFigureSpec(
            label="fig:contract-negative-control",
            filename="contract_negative_control.png",
            caption="Negative-control content figure.",
            generated_by="tests.test_manuscript_variables",
            alt_text="A negative-control figure used only to test count derivation.",
        )
        changed_content_contract = (*INTEGRATION_FIGURE_SPECS, extra_content)
        changed_cover_contract = (*COVER_FIGURE_FILENAMES, "alternate_cover.png")

        result = generate_variables(
            content_figure_specs=changed_content_contract,
            cover_figure_filenames=changed_cover_contract,
        )

        assert result["CONTENT_FIGURES"] == str(len(changed_content_contract))
        assert result["COVER_FIGURES"] == str(len(changed_cover_contract))
        assert result["TOTAL_FIGURES"] == str(
            len(changed_content_contract) + len(changed_cover_contract)
        )
        assert result["TOTAL_FIGURES"] != str(
            len(INTEGRATION_FIGURE_SPECS) + len(COVER_FIGURE_FILENAMES)
        )

    def test_filesystem_counts_move_with_real_temp_tree(self, tmp_path: pathlib.Path):
        """Negative control: project inventory claims must follow actual files."""
        for directory in ("src", "tests", "scripts"):
            (tmp_path / directory).mkdir()
        for relative in (
            "src/__init__.py",
            "src/reader.py",
            "tests/test_reader.py",
            "tests/helper.py",
            "scripts/__init__.py",
            "scripts/01_run.py",
        ):
            (tmp_path / relative).write_text("# real temporary file\n", encoding="utf-8")

        baseline = generate_variables(project_root=tmp_path)
        assert baseline["SRC_MODULES"] == "1"
        assert baseline["TEST_FILES"] == "1"
        assert baseline["ORCHESTRATION_SCRIPTS"] == "1"

        for relative in ("src/analysis.py", "tests/test_analysis.py", "scripts/02_analyze.py"):
            (tmp_path / relative).write_text("# added negative-control file\n", encoding="utf-8")

        changed = generate_variables(project_root=tmp_path)
        assert changed["SRC_MODULES"] == "2"
        assert changed["TEST_FILES"] == "2"
        assert changed["ORCHESTRATION_SCRIPTS"] == "2"

    def test_reflects_changed_integration_result(self):
        """Negative control: tokens must track their source, not be hard-coded.

        Injects run_integration_demo's return value and asserts the derived
        token actually moves. A generator that ignored its input and emitted
        a constant would pass every other test in this file but fail this one.
        """
        import src.manuscript_variables as mv

        real_result = mv.run_integration_demo()
        fake_result = {
            "fonds": {**real_result["fonds"], "negative_control": {}},
            "rules": real_result["rules"],
            "tools": real_result["tools"],
            "summary": {**real_result["summary"], "fonds_loaded": 999, "bib_entries": 777},
        }
        result = generate_variables(integration_runner=lambda: fake_result)
        assert result["FONDS_LOADED"] == "999"
        assert result["BIB_ENTRIES"] == "777"
        assert result["FONDS_EXPECTED"] == str(len(fake_result["fonds"]))
        assert result["FONDS_LOADED"] != str(real_result["summary"]["fonds_loaded"])
