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
