"""Tests for infrastructure/core/runtime/env_deps.py.

Covers: check_dependencies, check_build_tools, and build tool detection.

No mocks used — tests use real package imports and real shutil.which calls.
"""

from __future__ import annotations


from infrastructure.core.runtime.env_deps import (
    check_dependencies,
    check_build_tools,
)


class TestCheckDependencies:
    """Test check_dependencies with real package checks."""

    def test_default_packages_present(self):
        """Default required packages (numpy, matplotlib, pytest) should be present."""
        all_present, missing = check_dependencies()
        assert all_present is True
        assert len(missing) == 0

    def test_custom_packages_all_present(self):
        """Should return True when all specified packages exist."""
        all_present, missing = check_dependencies(["os", "sys", "pathlib"])
        assert all_present is True
        assert missing == []

    def test_custom_packages_some_missing(self):
        """Should detect missing packages."""
        all_present, missing = check_dependencies(["os", "nonexistent_package_xyz123"])
        assert all_present is False
        assert "nonexistent_package_xyz123" in missing

    def test_custom_packages_all_missing(self):
        """Should report all packages as missing."""
        all_present, missing = check_dependencies(["nonexistent_a", "nonexistent_b"])
        assert all_present is False
        assert len(missing) == 2

    def test_empty_package_list(self):
        """Empty package list should return True with no missing."""
        all_present, missing = check_dependencies([])
        assert all_present is True
        assert missing == []

    def test_single_present_package(self):
        """Single present package should return True."""
        all_present, missing = check_dependencies(["json"])
        assert all_present is True


class TestCheckBuildTools:
    """Test check_build_tools with real tool detection."""

    def test_default_tools(self):
        """Test default tool check (pandoc, xelatex) - result depends on system."""
        result = check_build_tools()
        assert isinstance(result, bool)

    def test_common_tools_present(self):
        """Tools like 'python3' or 'echo' should be found on any system."""
        result = check_build_tools({"echo": "Echo command", "cat": "Concatenate"})
        assert result is True

    def test_missing_tools(self):
        """Nonexistent tools should not be found."""
        result = check_build_tools({"nonexistent_tool_xyz": "Fake tool"})
        assert result is False

    def test_mixed_tools(self):
        """Mix of present and missing tools should return False."""
        result = check_build_tools({
            "echo": "Echo command",
            "nonexistent_tool_xyz": "Fake tool",
        })
        assert result is False

    def test_empty_tools_dict(self):
        """Empty tools dict should return True."""
        result = check_build_tools({})
        assert result is True
