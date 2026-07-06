"""test_property_based.py — Property-based tests using Hypothesis.

Validates that all public src/ functions satisfy robustness properties:
  - never raise on absent/empty/garbage paths
  - always return the declared type
  - load_soft_rules always returns a list
  - integration demo never raises
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

try:
    from hypothesis import assume, given, settings
    from hypothesis import strategies as st

    _HYPOTHESIS_AVAILABLE = True
except ImportError:
    _HYPOTHESIS_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _HYPOTHESIS_AVAILABLE,
    reason="hypothesis not installed — skipping property-based tests",
)

if _HYPOTHESIS_AVAILABLE:
    from src.fonds_reader import (
        read_bibliography_fond,
        read_contacts_fond,
        read_datasets_fond,
        read_all_fonds,
    )
    from src.rules_applier import (
        load_soft_rules,
        load_strong_rules,
        validate_against_rules,
        load_all_project_rules,
        load_all_manuscript_rules,
    )
    from src.tools_invoker import (
        discover_tools,
        get_tool_entrypoints,
        validate_tool_scripts_exist,
    )
    from src.integration import run_integration_demo


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Names that look like real rule/fond/tool set names — alphanumeric + underscores
_name_st = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"),
    min_size=1,
    max_size=40,
)

# Completely arbitrary strings (may contain path separators, unicode, etc.)
_arbitrary_st = st.text(min_size=0, max_size=80)


# ---------------------------------------------------------------------------
# Property: fonds functions never raise for any fond_name input
# ---------------------------------------------------------------------------


@given(fond_name=_name_st)
@settings(max_examples=30, deadline=5000)
def test_read_bibliography_fond_never_raises(fond_name: str):
    """read_bibliography_fond must return None or a dict — never raise."""
    result = read_bibliography_fond(fond_name=fond_name)
    assert result is None or isinstance(result, dict)


@given(fond_name=_name_st)
@settings(max_examples=30, deadline=5000)
def test_read_contacts_fond_never_raises(fond_name: str):
    result = read_contacts_fond(fond_name=fond_name)
    assert result is None or isinstance(result, dict)


@given(fond_name=_name_st)
@settings(max_examples=30, deadline=5000)
def test_read_datasets_fond_never_raises(fond_name: str):
    result = read_datasets_fond(fond_name=fond_name)
    assert result is None or isinstance(result, dict)


# ---------------------------------------------------------------------------
# Property: bibliography fond returns None or TypedDict-compatible shape
# ---------------------------------------------------------------------------


@given(fond_name=_name_st)
@settings(max_examples=25, deadline=5000)
def test_bibliography_fond_shape_when_not_none(fond_name: str):
    """When read_bibliography_fond returns a dict, it must have the required keys."""
    result = read_bibliography_fond(fond_name=fond_name)
    if result is not None:
        assert "manifest" in result
        assert "bib_text" in result
        assert "csv_rows" in result
        assert isinstance(result["bib_text"], str)
        assert isinstance(result["csv_rows"], list)


@given(fond_name=_name_st)
@settings(max_examples=25, deadline=5000)
def test_contacts_fond_shape_when_not_none(fond_name: str):
    result = read_contacts_fond(fond_name=fond_name)
    if result is not None:
        assert "manifest" in result
        assert "contacts" in result
        assert isinstance(result["contacts"], list)


@given(fond_name=_name_st)
@settings(max_examples=25, deadline=5000)
def test_datasets_fond_shape_when_not_none(fond_name: str):
    result = read_datasets_fond(fond_name=fond_name)
    if result is not None:
        assert "manifest" in result
        assert "datasets" in result
        assert isinstance(result["datasets"], list)


# ---------------------------------------------------------------------------
# Property: load_soft_rules always returns list (never None, never raises)
# ---------------------------------------------------------------------------


@given(rule_set_name=_name_st)
@settings(max_examples=30, deadline=5000)
def test_load_soft_rules_always_returns_list(rule_set_name: str):
    result = load_soft_rules(rule_set_name)
    assert isinstance(result, list)


@given(rule_set_name=_name_st)
@settings(max_examples=30, deadline=5000)
def test_load_strong_rules_always_returns_list(rule_set_name: str):
    result = load_strong_rules(rule_set_name)
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Property: load_soft_rules entries always have filename + content keys
# ---------------------------------------------------------------------------


@given(rule_set_name=_name_st)
@settings(max_examples=25, deadline=5000)
def test_load_soft_rules_entries_have_required_keys(rule_set_name: str):
    result = load_soft_rules(rule_set_name)
    for entry in result:
        assert "filename" in entry, f"Missing 'filename' in entry: {entry}"
        assert "content" in entry, f"Missing 'content' in entry: {entry}"
        assert isinstance(entry["filename"], str)
        assert isinstance(entry["content"], str)


@given(rule_set_name=_name_st)
@settings(max_examples=25, deadline=5000)
def test_load_strong_rules_entries_have_required_keys(rule_set_name: str):
    result = load_strong_rules(rule_set_name)
    for entry in result:
        assert "filename" in entry
        assert "schema" in entry
        assert isinstance(entry["filename"], str)


# ---------------------------------------------------------------------------
# Property: validate_against_rules always returns expected keys
# ---------------------------------------------------------------------------


@given(rule_set_name=_name_st)
@settings(max_examples=25, deadline=5000)
def test_validate_against_rules_never_raises(rule_set_name: str):
    result = validate_against_rules(rule_set_name)
    assert isinstance(result, dict)
    required_keys = {
        "rule_set",
        "manifest",
        "soft_rules_count",
        "strong_rules_count",
        "status",
        "warnings",
    }
    assert required_keys <= set(result.keys()), (
        f"Missing keys: {required_keys - set(result.keys())}"
    )


@given(rule_set_name=_name_st)
@settings(max_examples=25, deadline=5000)
def test_validate_against_rules_status_is_valid_string(rule_set_name: str):
    result = validate_against_rules(rule_set_name)
    assert result["status"] in {"ok", "partial", "missing"}


@given(rule_set_name=_name_st)
@settings(max_examples=25, deadline=5000)
def test_validate_against_rules_counts_are_non_negative(rule_set_name: str):
    result = validate_against_rules(rule_set_name)
    assert result["soft_rules_count"] >= 0
    assert result["strong_rules_count"] >= 0


# ---------------------------------------------------------------------------
# Property: tools_invoker functions never raise for arbitrary tool names
# ---------------------------------------------------------------------------


@given(tool_name=_name_st)
@settings(max_examples=25, deadline=5000)
def test_get_tool_entrypoints_always_returns_list(tool_name: str):
    result = get_tool_entrypoints(tool_name)
    assert isinstance(result, list)


@given(tool_name=_name_st)
@settings(max_examples=25, deadline=5000)
def test_validate_tool_scripts_exist_always_returns_dict(tool_name: str):
    result = validate_tool_scripts_exist(tool_name)
    assert isinstance(result, dict)
    assert "tool" in result
    assert "entrypoints" in result
    assert "missing" in result
    assert "valid" in result
    assert isinstance(result["valid"], bool)


# ---------------------------------------------------------------------------
# Property: read_all_fonds always returns dict with three keys
# ---------------------------------------------------------------------------


def test_read_all_fonds_always_returns_three_keys():
    """read_all_fonds is not parameterised, but always returns exactly three keys."""
    result = read_all_fonds()
    assert isinstance(result, dict)
    assert set(result.keys()) == {"bibliography", "contacts", "datasets"}


# ---------------------------------------------------------------------------
# Property: load_all_project_rules / load_all_manuscript_rules return correct shape
# ---------------------------------------------------------------------------


def test_load_all_project_rules_returns_soft_and_strong():
    result = load_all_project_rules()
    assert isinstance(result, dict)
    assert "soft" in result
    assert "strong" in result
    assert isinstance(result["soft"], list)
    assert isinstance(result["strong"], list)


def test_load_all_manuscript_rules_returns_soft_and_strong():
    result = load_all_manuscript_rules()
    assert isinstance(result, dict)
    assert "soft" in result
    assert "strong" in result
    assert isinstance(result["soft"], list)
    assert isinstance(result["strong"], list)


# ---------------------------------------------------------------------------
# Property: integration demo never raises (single call — covers end-to-end)
# ---------------------------------------------------------------------------


def test_integration_demo_never_raises():
    """run_integration_demo must return a structured dict without raising."""
    result = run_integration_demo()
    assert isinstance(result, dict)
    assert "fonds" in result
    assert "rules" in result
    assert "tools" in result
    assert "summary" in result


def test_integration_demo_summary_shape():
    result = run_integration_demo()
    summary = result["summary"]
    required = {
        "fonds_loaded",
        "rules_sets_ok",
        "rules_sets_total",
        "tools_discovered",
        "tools_valid",
    }
    assert required <= set(summary.keys()), (
        f"Missing summary keys: {required - set(summary.keys())}"
    )
    assert summary["fonds_loaded"] >= 0
    assert summary["rules_sets_total"] >= 0
    assert summary["tools_discovered"] >= 0


def test_integration_demo_fonds_has_expected_sub_keys():
    result = run_integration_demo()
    fonds = result["fonds"]
    assert "bibliography" in fonds
    assert "contacts" in fonds
    assert "datasets" in fonds


def test_integration_demo_rules_have_status_keys():
    result = run_integration_demo()
    for rule_set_name, rule_result in result["rules"].items():
        assert "status" in rule_result, f"{rule_set_name}: 'status' key missing"
        assert rule_result["status"] in {"ok", "partial", "missing"}, (
            f"{rule_set_name}: unexpected status {rule_result['status']!r}"
        )
