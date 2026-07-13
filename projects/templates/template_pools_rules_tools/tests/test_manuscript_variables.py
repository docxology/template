"""test_manuscript_variables.py — Tests for the manuscript_variables module.

Exercises generate_variables() against the real repo fonds/rules/tools
resources (same fixtures test_integration.py relies on) — no mocks.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

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
            "RULES_SETS_OK",
            "RULES_SETS_TOTAL",
            "TOOLS_DISCOVERED",
            "TOOLS_VALID",
            "BIB_ENTRIES",
            "CONTACTS_COUNT",
            "DATASETS_COUNT",
            "STRONG_RULES_PROJECT",
            "STRONG_RULES_MANUSCRIPT",
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
        assert result["TOOLS_DISCOVERED"].isdigit()

    def test_reflects_changed_integration_result(self):
        """Negative control: tokens must track their source, not be hard-coded.

        Injects run_integration_demo's return value and asserts the derived
        token actually moves. A generator that ignored its input and emitted
        a constant would pass every other test in this file but fail this one.
        """
        import src.manuscript_variables as mv

        real_result = mv.run_integration_demo()
        fake_result = {
            "fonds": real_result["fonds"],
            "rules": real_result["rules"],
            "tools": real_result["tools"],
            "summary": {**real_result["summary"], "fonds_loaded": 999, "bib_entries": 777},
        }
        result = generate_variables(integration_runner=lambda: fake_result)
        assert result["FONDS_LOADED"] == "999"
        assert result["BIB_ENTRIES"] == "777"
        assert result["FONDS_LOADED"] != str(real_result["summary"]["fonds_loaded"])
