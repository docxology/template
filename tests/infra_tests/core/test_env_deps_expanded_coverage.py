"""Tests for infrastructure.core.runtime.env_deps — expanded coverage."""

from infrastructure.core.runtime.env_deps import (
    check_dependencies,
    check_build_tools,
)


class TestCheckDependencies:
    def test_default_packages_all_present(self):
        """Default packages (numpy, matplotlib, pytest) should all be available."""
        all_present, missing = check_dependencies()
        assert all_present is True
        assert missing == []

    def test_custom_packages_present(self):
        all_present, missing = check_dependencies(["json", "os", "sys"])
        assert all_present is True
        assert missing == []

    def test_missing_package(self):
        all_present, missing = check_dependencies(["nonexistent_package_xyz"])
        assert all_present is False
        assert "nonexistent_package_xyz" in missing

    def test_mixed_present_and_missing(self):
        all_present, missing = check_dependencies(["json", "nonexistent_abc"])
        assert all_present is False
        assert "nonexistent_abc" in missing
        assert "json" not in missing

    def test_empty_list(self):
        all_present, missing = check_dependencies([])
        assert all_present is True
        assert missing == []


class TestCheckBuildTools:
    def test_default_tools(self):
        """Default checks pandoc and xelatex -- result depends on system."""
        result = check_build_tools()
        assert isinstance(result, bool)

    def test_custom_tools_present(self):
        result = check_build_tools({"python3": "Python interpreter"})
        assert result is True

    def test_custom_tools_missing(self):
        result = check_build_tools({"nonexistent_tool_xyz": "Does not exist"})
        assert result is False

    def test_mixed_tools(self):
        result = check_build_tools({
            "python3": "Python",
            "nonexistent_tool_abc": "Missing tool",
        })
        assert result is False

    def test_empty_tools(self):
        result = check_build_tools({})
        assert result is True
