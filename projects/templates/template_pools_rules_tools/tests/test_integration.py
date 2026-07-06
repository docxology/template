"""test_integration.py — Tests for the full integration demo.

These tests exercise the complete run_integration_demo() pipeline.
Individual resource availability is checked via skipif guards on the
sub-tests that require specific fonds/rules/tools to be present.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

from src.integration import run_integration_demo
from src.fonds_reader import get_fonds_root
from src.rules_applier import get_rules_root
from src.tools_invoker import get_tools_root

# ---------------------------------------------------------------------------
# Path guards
# ---------------------------------------------------------------------------

_FONDS_OK = (
    (get_fonds_root() / "template_bibliography" / "fonds.yaml").exists()
    and (get_fonds_root() / "template_contacts" / "fonds.yaml").exists()
    and (get_fonds_root() / "template_datasets" / "fonds.yaml").exists()
)

_RULES_OK = (get_rules_root() / "template_project_rules" / "rules.yaml").exists() and (
    get_rules_root() / "template_manuscript_rules" / "rules.yaml"
).exists()

_TOOLS_OK = get_tools_root().is_dir()


# ---------------------------------------------------------------------------
# Structural tests (always run — no resource required)
# ---------------------------------------------------------------------------


class TestRunIntegrationDemoStructure:
    def test_returns_dict(self):
        result = run_integration_demo()
        assert isinstance(result, dict)

    def test_has_fonds_key(self):
        result = run_integration_demo()
        assert "fonds" in result

    def test_has_rules_key(self):
        result = run_integration_demo()
        assert "rules" in result

    def test_has_tools_key(self):
        result = run_integration_demo()
        assert "tools" in result

    def test_has_summary_key(self):
        result = run_integration_demo()
        assert "summary" in result

    def test_fonds_has_expected_sub_keys(self):
        result = run_integration_demo()
        assert "bibliography" in result["fonds"]
        assert "contacts" in result["fonds"]
        assert "datasets" in result["fonds"]

    def test_summary_has_count_fields(self):
        result = run_integration_demo()
        summary = result["summary"]
        expected = {
            "fonds_loaded",
            "rules_sets_ok",
            "rules_sets_total",
            "tools_discovered",
            "tools_valid",
            "bib_entries",
            "contacts",
            "datasets",
        }
        assert expected <= set(summary.keys())

    def test_summary_counts_are_non_negative_ints(self):
        result = run_integration_demo()
        summary = result["summary"]
        for key, val in summary.items():
            assert isinstance(val, int), f"summary[{key!r}] is not int: {val!r}"
            assert val >= 0, f"summary[{key!r}] is negative: {val}"


# ---------------------------------------------------------------------------
# Fonds integration
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _FONDS_OK, reason="One or more fond exemplars not present")
class TestIntegrationFonds:
    def test_all_fonds_loaded(self):
        result = run_integration_demo()
        assert result["summary"]["fonds_loaded"] == 3

    def test_bibliography_has_entries(self):
        result = run_integration_demo()
        assert result["summary"]["bib_entries"] > 0

    def test_contacts_has_entries(self):
        result = run_integration_demo()
        assert result["summary"]["contacts"] > 0

    def test_datasets_has_entries(self):
        result = run_integration_demo()
        assert result["summary"]["datasets"] > 0


# ---------------------------------------------------------------------------
# Rules integration
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _RULES_OK, reason="One or more rule sets not present")
class TestIntegrationRules:
    def test_rules_sets_ok(self):
        result = run_integration_demo()
        assert result["summary"]["rules_sets_ok"] == result["summary"]["rules_sets_total"]

    def test_project_rules_in_result(self):
        result = run_integration_demo()
        assert "template_project_rules" in result["rules"]

    def test_manuscript_rules_in_result(self):
        result = run_integration_demo()
        assert "template_manuscript_rules" in result["rules"]


# ---------------------------------------------------------------------------
# Tools integration
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _TOOLS_OK, reason="tools/templates/ not present")
class TestIntegrationTools:
    def test_tools_discovered_positive(self):
        result = run_integration_demo()
        assert result["summary"]["tools_discovered"] > 0

    def test_tools_list_is_list(self):
        result = run_integration_demo()
        assert isinstance(result["tools"], list)

    def test_each_tool_has_validation(self):
        result = run_integration_demo()
        for tool in result["tools"]:
            assert "validation" in tool, f"Tool {tool['name']} missing 'validation' key"
            assert "valid" in tool["validation"]
