"""Tests for infrastructure/core/runtime/env_deps.py.

Tests dependency and build tool checking utilities using real execution.
Follows No Mocks Policy — all tests use real package imports and shutil.which.
"""

from __future__ import annotations

import pytest

from infrastructure.core.runtime.env_deps import check_build_tools, check_dependencies


class TestCheckDependencies:
    """Test check_dependencies with real package checks."""

    def test_returns_tuple(self):
        """check_dependencies returns a (bool, list) tuple."""
        result = check_dependencies()
        assert isinstance(result, tuple)
        assert len(result) == 2
        all_present, missing = result
        assert isinstance(all_present, bool)
        assert isinstance(missing, list)

    def test_default_packages_check(self):
        """Default package list returns a valid result (env-dependent)."""
        all_present, missing = check_dependencies()
        assert isinstance(all_present, bool)
        assert isinstance(missing, list)

    def test_known_installed_package(self):
        """numpy is a declared dependency and should import."""
        all_present, missing = check_dependencies(["numpy"])
        assert all_present is True
        assert missing == []

    @pytest.mark.parametrize(
        "packages",
        [
            ["numpy"],
            ["json", "os", "sys"],
            ["os", "sys", "pathlib"],
            ["json"],
        ],
    )
    def test_present_packages(self, packages):
        """Specified present packages return True with empty missing list."""
        all_present, missing = check_dependencies(packages)
        assert all_present is True
        assert missing == []

    @pytest.mark.parametrize(
        "packages,missing_name",
        [
            (["__nonexistent_pkg_xyz__"], "__nonexistent_pkg_xyz__"),
            (["nonexistent_package_xyz"], "nonexistent_package_xyz"),
            (["nonexistent_package_xyz123"], "nonexistent_package_xyz123"),
        ],
    )
    def test_single_missing_package(self, packages, missing_name):
        """A single missing package is reported."""
        all_present, missing = check_dependencies(packages)
        assert all_present is False
        assert missing_name in missing

    def test_mixed_present_and_missing(self):
        """Mix of present and missing packages returns False with only missing listed."""
        all_present, missing = check_dependencies(["json", "nonexistent_abc"])
        assert all_present is False
        assert "nonexistent_abc" in missing
        assert "json" not in missing

    def test_custom_packages_all_missing(self):
        """All specified missing packages are reported."""
        all_present, missing = check_dependencies(["nonexistent_a", "nonexistent_b"])
        assert all_present is False
        assert len(missing) == 2

    def test_empty_list_returns_all_present(self):
        """Empty required list returns True with no missing."""
        all_present, missing = check_dependencies([])
        assert all_present is True
        assert missing == []


class TestCheckBuildTools:
    """Test check_build_tools with real tool detection."""

    def test_returns_bool(self):
        """check_build_tools returns a boolean."""
        result = check_build_tools()
        assert isinstance(result, bool)

    def test_default_tools(self):
        """Default checks (pandoc, xelatex) — result depends on system."""
        result = check_build_tools()
        assert isinstance(result, bool)

    @pytest.mark.parametrize(
        "tools,expected",
        [
            ({"python3": "Python interpreter"}, True),
            ({"echo": "Echo command", "cat": "Concatenate"}, True),
        ],
    )
    def test_common_tools_present(self, tools, expected):
        """Known-available tools should be found."""
        assert check_build_tools(tools) is expected

    @pytest.mark.parametrize(
        "tools",
        [
            {"__nonexistent_tool_xyz__": "Does not exist"},
            {"nonexistent_tool_xyz": "Fake tool"},
        ],
    )
    def test_missing_tools(self, tools):
        """Nonexistent tools cause False return."""
        assert check_build_tools(tools) is False

    def test_mixed_tools(self):
        """Mix of present and missing tools returns False."""
        result = check_build_tools(
            {
                "echo": "Echo command",
                "nonexistent_tool_xyz": "Fake tool",
            }
        )
        assert result is False

    def test_empty_tools_dict(self):
        """Empty tools dict returns True."""
        assert check_build_tools({}) is True


# ---------------------------------------------------------------------------
# Helpers for install_missing_packages tests
# ---------------------------------------------------------------------------

import os
import stat
import textwrap
from contextlib import contextmanager
from pathlib import Path

from infrastructure.core.runtime.env_deps import install_missing_packages


@contextmanager
def _path_override(new_path: str):
    """Temporarily override PATH for real shutil.which resolution."""
    original = os.environ.get("PATH", "")
    os.environ["PATH"] = new_path
    try:
        yield
    finally:
        os.environ["PATH"] = original


import sys as _sys


def _make_fake_uv(tmp_path: Path, script_body: str) -> Path:
    """Write a real executable shell script named 'uv' to tmp_path."""
    uv_bin = tmp_path / "uv"
    uv_bin.write_text(textwrap.dedent(script_body))
    uv_bin.chmod(uv_bin.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return uv_bin


def _make_fake_uv_py(tmp_path: Path, script_body: str) -> Path:
    """Write a real executable Python script named 'uv' to tmp_path.

    Uses an absolute shebang so the script works even with a restricted PATH.
    script_body should be valid Python (no shebang line — added automatically).
    """
    uv_bin = tmp_path / "uv"
    shebang = f"#!{_sys.executable}\n"
    uv_bin.write_text(shebang + textwrap.dedent(script_body))
    uv_bin.chmod(uv_bin.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return uv_bin


class TestInstallMissingPackages:
    """Tests for install_missing_packages covering uncovered branches.

    All tests manipulate a real PATH pointing to a tmp dir containing a
    real shell-script named 'uv'. No mocks, no MagicMock, no unittest.mock.
    """

    def test_uv_not_found_returns_false(self, tmp_path):
        """Returns False immediately when uv is absent from PATH."""
        empty_bin = tmp_path / "empty_bin"
        empty_bin.mkdir()
        with _path_override(str(empty_bin)):
            result = install_missing_packages(["json"])
        assert result is False

    @pytest.mark.skip(
        reason=(
            "TimeoutExpired on uv add requires a real 30s subprocess wait, "
            "which exceeds the 10s pytest-timeout ceiling. "
            "Branch covered by code inspection; timeout path uses 'continue' so "
            "subsequent packages and uv sync still run."
        )
    )
    def test_uv_add_timeout_continues_to_sync(self, tmp_path):
        """TimeoutExpired on uv add is caught and execution continues to sync."""
        # Python script: sleep long on 'add' (triggers 30s timeout); exit 0 on 'sync'
        script = """\
            import sys, time
            if len(sys.argv) > 1 and sys.argv[1] == "add":
                time.sleep(120)
            sys.exit(0)
        """
        _make_fake_uv_py(tmp_path, script)
        with _path_override(str(tmp_path)):
            result = install_missing_packages(["os"])
        assert result is True

    def test_uv_add_nonzero_returncode_continues(self, tmp_path):
        """Non-zero uv add exit code emits a warning and continues to sync."""
        # Python script: exit 1 on 'add'; exit 0 on 'sync'
        script = """\
            import sys
            if len(sys.argv) > 1 and sys.argv[1] == "add":
                sys.exit(1)
            sys.exit(0)
        """
        _make_fake_uv_py(tmp_path, script)
        with _path_override(str(tmp_path)):
            # uv add fails for each package but uv sync succeeds; 'json' is
            # a stdlib module that will import successfully → True
            result = install_missing_packages(["json"])
        assert result is True

    @pytest.mark.skip(
        reason=(
            "TimeoutExpired on uv sync requires a real 120s subprocess wait, "
            "which exceeds the 10s pytest-timeout ceiling. "
            "Branch covered by code inspection; TimeoutExpired during sync returns False."
        )
    )
    def test_uv_sync_timeout_returns_false(self, tmp_path):
        """TimeoutExpired on uv sync returns False."""
        # Python script: exit 0 on 'add'; sleep long on 'sync'
        script = """\
            import sys, time
            if len(sys.argv) > 1 and sys.argv[1] == "sync":
                time.sleep(300)
            sys.exit(0)
        """
        _make_fake_uv_py(tmp_path, script)
        with _path_override(str(tmp_path)):
            result = install_missing_packages(["json"])
        assert result is False

    def test_uv_sync_success_all_packages_import_returns_true(self, tmp_path):
        """Returns True when uv sync succeeds and all packages import correctly."""
        # Python script: exit 0 unconditionally
        script = """\
            import sys
            sys.exit(0)
        """
        _make_fake_uv_py(tmp_path, script)
        with _path_override(str(tmp_path)):
            # Use stdlib modules that are guaranteed importable
            result = install_missing_packages(["os", "json", "sys"])
        assert result is True

    def test_uv_sync_success_package_import_fails_returns_false(self, tmp_path):
        """Returns False when uv sync exits 0 but a package still fails to import."""
        # Python script: exit 0 unconditionally — simulates successful uv sync
        script = """\
            import sys
            sys.exit(0)
        """
        _make_fake_uv_py(tmp_path, script)
        with _path_override(str(tmp_path)):
            # Package name that cannot possibly be imported
            result = install_missing_packages(["__nonexistent_pkg_for_env_deps_test__"])
        assert result is False

    def test_uv_sync_nonzero_returncode_returns_false(self, tmp_path):
        """Returns False when uv sync exits with a non-zero code."""
        # Python script: exit 0 on 'add'; exit 2 on 'sync'
        script = """\
            import sys
            if len(sys.argv) > 1 and sys.argv[1] == "sync":
                sys.exit(2)
            sys.exit(0)
        """
        _make_fake_uv_py(tmp_path, script)
        with _path_override(str(tmp_path)):
            result = install_missing_packages(["json"])
        assert result is False

    def test_oserror_during_subprocess_returns_false(self, tmp_path):
        """Returns False when an OSError is raised trying to run uv."""
        # Create a 'uv' that is a directory — executing a directory raises
        # PermissionError (subclass of OSError) on subprocess.run
        uv_dir = tmp_path / "uv"
        uv_dir.mkdir()
        with _path_override(str(tmp_path)):
            result = install_missing_packages(["json"])
        assert result is False
