"""test_tools_invoker.py — Tests for tools_invoker.py using real tool exemplars.

Tests skip gracefully when tool directories are absent.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

from src.tools_invoker import (
    get_tools_root,
    discover_tools,
    get_tool_entrypoints,
    validate_tool_scripts_exist,
)

# ---------------------------------------------------------------------------
# Path guards
# ---------------------------------------------------------------------------

_TOOLS_TEMPLATES = get_tools_root()
_CODE_EXECUTOR_DIR = _TOOLS_TEMPLATES / "template_code_executor"
_CODE_EXECUTOR_MANIFEST = _CODE_EXECUTOR_DIR / "tools.yaml"
_VALIDATOR_DIR = _TOOLS_TEMPLATES / "template_validator"
_VALIDATOR_MANIFEST = _VALIDATOR_DIR / "tools.yaml"


# ---------------------------------------------------------------------------
# discover_tools
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _TOOLS_TEMPLATES.is_dir(),
    reason="tools/templates/ not present",
)
class TestDiscoverTools:
    def test_returns_list(self):
        result = discover_tools()
        assert isinstance(result, list)

    def test_nonempty(self):
        result = discover_tools()
        assert len(result) > 0

    def test_each_entry_has_name_path_manifest(self):
        result = discover_tools()
        for tool in result:
            assert "name" in tool
            assert "path" in tool
            assert "manifest" in tool

    def test_known_tools_discovered(self):
        result = discover_tools()
        names = [t["name"] for t in result]
        assert "template_code_executor" in names
        assert "template_validator" in names

    def test_manifests_are_dicts_or_none(self):
        result = discover_tools()
        for tool in result:
            assert tool["manifest"] is None or isinstance(tool["manifest"], dict)


# ---------------------------------------------------------------------------
# get_tool_entrypoints
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _CODE_EXECUTOR_MANIFEST.exists(),
    reason="template_code_executor/tools.yaml not present",
)
class TestGetToolEntrypoints:
    def test_returns_list(self):
        result = get_tool_entrypoints("template_code_executor")
        assert isinstance(result, list)

    def test_nonempty(self):
        result = get_tool_entrypoints("template_code_executor")
        assert len(result) > 0

    def test_entrypoints_are_strings(self):
        result = get_tool_entrypoints("template_code_executor")
        for ep in result:
            assert isinstance(ep, str)

    def test_run_sh_present(self):
        result = get_tool_entrypoints("template_code_executor")
        assert "scripts/run.sh" in result

    def test_validate_sh_present(self):
        result = get_tool_entrypoints("template_code_executor")
        assert "scripts/validate.sh" in result


def test_get_tool_entrypoints_missing_returns_empty():
    result = get_tool_entrypoints("__nonexistent_tool__")
    assert result == []


# ---------------------------------------------------------------------------
# validate_tool_scripts_exist
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _CODE_EXECUTOR_MANIFEST.exists(),
    reason="template_code_executor/tools.yaml not present",
)
class TestValidateToolScriptsExistCodeExecutor:
    def test_returns_dict(self):
        result = validate_tool_scripts_exist("template_code_executor")
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        result = validate_tool_scripts_exist("template_code_executor")
        assert "tool" in result
        assert "entrypoints" in result
        assert "missing" in result
        assert "valid" in result

    def test_tool_name_matches(self):
        result = validate_tool_scripts_exist("template_code_executor")
        assert result["tool"] == "template_code_executor"

    def test_valid_is_bool(self):
        result = validate_tool_scripts_exist("template_code_executor")
        assert isinstance(result["valid"], bool)

    def test_no_missing_scripts(self):
        result = validate_tool_scripts_exist("template_code_executor")
        assert result["missing"] == [], (
            f"Missing scripts in template_code_executor: {result['missing']}"
        )

    def test_is_valid(self):
        result = validate_tool_scripts_exist("template_code_executor")
        assert result["valid"] is True


@pytest.mark.skipif(
    not _VALIDATOR_MANIFEST.exists(),
    reason="template_validator/tools.yaml not present",
)
class TestValidateToolScriptsExistValidator:
    def test_no_missing_scripts(self):
        result = validate_tool_scripts_exist("template_validator")
        assert result["missing"] == [], (
            f"Missing scripts in template_validator: {result['missing']}"
        )

    def test_is_valid(self):
        result = validate_tool_scripts_exist("template_validator")
        assert result["valid"] is True


def test_validate_missing_tool_returns_empty_valid():
    result = validate_tool_scripts_exist("__nonexistent_tool__")
    assert result["tool"] == "__nonexistent_tool__"
    assert result["entrypoints"] == []
    assert result["missing"] == []
    assert result["valid"] is True  # no entrypoints → nothing missing
