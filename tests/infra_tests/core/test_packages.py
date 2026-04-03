"""Tests for infrastructure.core.runtime._packages."""

import os

from infrastructure.core.runtime._packages import (
    check_build_tools,
    set_environment_variables,
    validate_uv_sync_result,
)


class TestSetEnvironmentVariables:
    def test_sets_variables(self, tmp_path):
        result = set_environment_variables(tmp_path)
        assert result is True
        assert os.environ.get("MPLBACKEND") == "Agg"
        assert os.environ.get("PYTHONIOENCODING") == "utf-8"
        assert os.environ.get("PROJECT_ROOT") == str(tmp_path)

    def test_sets_cache_dirs(self, tmp_path):
        # Remove if previously set so setdefault works
        os.environ.pop("MPLCONFIGDIR", None)
        os.environ.pop("UV_CACHE_DIR", None)
        result = set_environment_variables(tmp_path)
        assert result is True
        assert "MPLCONFIGDIR" in os.environ
        assert "UV_CACHE_DIR" in os.environ


class TestValidateUvSyncResult:
    def test_no_venv(self, tmp_path):
        ok, msg = validate_uv_sync_result(tmp_path)
        assert ok is False
        assert "Virtual environment" in msg

    def test_no_lock_file(self, tmp_path):
        (tmp_path / ".venv").mkdir()
        ok, msg = validate_uv_sync_result(tmp_path)
        assert ok is False
        assert "Lock file" in msg

    def test_success(self, tmp_path):
        (tmp_path / ".venv").mkdir()
        (tmp_path / "uv.lock").write_text("lock content")
        ok, msg = validate_uv_sync_result(tmp_path)
        assert ok is True
        assert "successfully" in msg


class TestCheckBuildTools:
    def test_all_found(self):
        # python and ls should be on PATH
        result = check_build_tools({"python3": "Python interpreter"})
        assert result is True

    def test_missing_tool(self):
        result = check_build_tools({"nonexistent_tool_xyz_12345": "Fake tool"})
        assert result is False

    def test_empty_tools(self):
        result = check_build_tools({})
        assert result is True

    def test_mixed(self):
        result = check_build_tools({
            "python3": "Python",
            "nonexistent_xyz_99": "Missing",
        })
        assert result is False
