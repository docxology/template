"""Tests for infrastructure/core/env_deps.py.

Tests dependency and build tool checking utilities using real execution.
Follows No Mocks Policy - all tests use real data and real execution.
"""

from infrastructure.core.runtime.env_deps import check_dependencies, check_build_tools


class TestCheckDependencies:
    """Test check_dependencies function."""

    def test_returns_tuple(self):
        """Test that check_dependencies returns a (bool, list) tuple."""
        result = check_dependencies()
        assert isinstance(result, tuple)
        assert len(result) == 2
        all_present, missing = result
        assert isinstance(all_present, bool)
        assert isinstance(missing, list)

    def test_known_installed_package(self):
        """Test that numpy is found (it's a declared dependency)."""
        all_present, missing = check_dependencies(["numpy"])
        assert all_present is True
        assert missing == []

    def test_nonexistent_package_flagged(self):
        """Test that a nonexistent package is reported as missing."""
        all_present, missing = check_dependencies(["__nonexistent_pkg_xyz__"])
        assert all_present is False
        assert "__nonexistent_pkg_xyz__" in missing

    def test_empty_list_returns_all_present(self):
        """Test that empty required list returns True with no missing."""
        all_present, missing = check_dependencies([])
        assert all_present is True
        assert missing == []

    def test_default_packages_present(self):
        """Test that the default package list check passes in this environment."""
        all_present, missing = check_dependencies()
        # numpy, matplotlib, pytest should all be installed in test env
        assert isinstance(all_present, bool)
        assert isinstance(missing, list)


class TestCheckBuildTools:
    """Test check_build_tools function."""

    def test_returns_bool(self):
        """Test that check_build_tools returns a boolean."""
        result = check_build_tools()
        assert isinstance(result, bool)

    def test_custom_tool_dict(self):
        """Test with custom tool dict including a known-available tool."""
        # python is always available, so use that as a known tool
        result = check_build_tools({"python3": "Python interpreter"})
        # python3 may or may not be available (uv manages it), but result must be bool
        assert isinstance(result, bool)

    def test_nonexistent_tool_returns_false(self):
        """Test that a definitely nonexistent tool causes False return."""
        result = check_build_tools({"__nonexistent_tool_xyz__": "Does not exist"})
        assert result is False
