"""test_tools_invoker.py — Tests for tools_invoker.py using real tool exemplars.

Tests skip gracefully when tool directories are absent.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

from src.tools_invoker import (
    discover_tools,
    get_tool_entrypoints,
    get_tools_root,
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


# ---------------------------------------------------------------------------
# Real subprocess invocation — proves the entrypoints actually run, not just
# that they exist on disk. Deliberately test-only: src/tools_invoker.py's own
# public API stays existence-checking only (invoking arbitrary tool scripts
# from library code would violate this project's own "never raise" graceful-
# degradation contract). Each test is skipif-guarded on its real runtime
# dependency so a missing binary skips cleanly instead of failing CI.
# ---------------------------------------------------------------------------

_CODE_EXECUTOR_RUN_SH = get_tools_root() / "template_code_executor" / "scripts" / "run.sh"
_VALIDATOR_VALIDATE_SH = get_tools_root() / "template_validator" / "scripts" / "validate.sh"

_HAS_TIMEOUT_AND_JQ = (
    shutil.which("timeout") is not None or shutil.which("gtimeout") is not None
) and shutil.which("jq") is not None

try:
    import jsonschema  # noqa: F401

    _HAS_JSONSCHEMA = True
except ImportError:
    _HAS_JSONSCHEMA = False


@pytest.mark.skipif(
    not _CODE_EXECUTOR_RUN_SH.is_file(), reason="template_code_executor/scripts/run.sh not present"
)
@pytest.mark.skipif(
    not _HAS_TIMEOUT_AND_JQ, reason="run.sh requires `timeout` (or `gtimeout`) and `jq` on PATH"
)
class TestInvokeCodeExecutor:
    def test_run_sh_executes_real_python(self):
        payload = json.dumps({"code": "print(2 + 2)", "language": "python", "timeout_s": 5})
        proc = subprocess.run(  # noqa: S603
            ["bash", str(_CODE_EXECUTOR_RUN_SH)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=15,
        )
        result = json.loads(proc.stdout)
        assert result["exit_code"] == 0
        assert "4" in result["stdout"]

    def test_run_sh_reports_nonzero_exit_on_real_failure(self):
        payload = json.dumps({"code": "raise SystemExit(3)", "language": "python", "timeout_s": 5})
        proc = subprocess.run(  # noqa: S603
            ["bash", str(_CODE_EXECUTOR_RUN_SH)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=15,
        )
        result = json.loads(proc.stdout)
        assert result["exit_code"] == 3


@pytest.mark.skipif(
    not _VALIDATOR_VALIDATE_SH.is_file(),
    reason="template_validator/scripts/validate.sh not present",
)
@pytest.mark.skipif(
    not _HAS_JSONSCHEMA, reason="validate.sh's real schema check requires the jsonschema package"
)
class TestInvokeValidator:
    def test_validate_sh_accepts_schema_conformant_document(self):
        payload = json.dumps({"name": "template_pools_rules_tools", "version": "1.0.0"})
        proc = subprocess.run(  # noqa: S603
            ["bash", str(_VALIDATOR_VALIDATE_SH)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert proc.returncode == 0
        assert "VALID" in proc.stdout
        assert (
            "jsonschema not installed" not in proc.stdout
        )  # must be the real schema path, not the fallback

    def test_validate_sh_rejects_document_missing_required_version_field(self):
        # tools/templates/template_validator/scripts/schema.json declares
        # "required": ["name", "version"] — omitting version is a genuine,
        # schema-verified violation, not an assumed one.
        payload = json.dumps({"name": "template_pools_rules_tools"})
        proc = subprocess.run(  # noqa: S603
            ["bash", str(_VALIDATOR_VALIDATE_SH)],
            input=payload,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert proc.returncode == 1
        assert "INVALID" in proc.stdout
