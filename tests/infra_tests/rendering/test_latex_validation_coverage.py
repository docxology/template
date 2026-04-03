"""Tests for infrastructure.rendering.latex_validation — coverage for pure-logic parts."""

from infrastructure.rendering.latex_validation import (
    ValidationReport,
    get_missing_packages_command,
)
from infrastructure.rendering.latex_discovery import PackageStatus


class TestValidationReport:
    def test_str_all_available(self):
        report = ValidationReport(
            required_packages=[PackageStatus("amsmath", True, "/path/amsmath.sty")],
            optional_packages=[],
            missing_required=[],
            missing_optional=[],
            all_required_available=True,
        )
        s = str(report)
        assert "All required packages available" in s

    def test_str_missing_required(self):
        report = ValidationReport(
            required_packages=[PackageStatus("foo", False, None)],
            optional_packages=[],
            missing_required=["foo"],
            missing_optional=[],
            all_required_available=False,
        )
        s = str(report)
        assert "Missing" in s
        assert "foo" in s
        assert "tlmgr install" in s

    def test_str_missing_optional(self):
        report = ValidationReport(
            required_packages=[],
            optional_packages=[PackageStatus("bar", False, None)],
            missing_required=[],
            missing_optional=["bar"],
            all_required_available=True,
        )
        s = str(report)
        assert "optional" in s.lower()
        assert "bar" in s

    def test_str_both_missing(self):
        report = ValidationReport(
            required_packages=[PackageStatus("foo", False, None)],
            optional_packages=[PackageStatus("bar", False, None)],
            missing_required=["foo"],
            missing_optional=["bar"],
            all_required_available=False,
        )
        s = str(report)
        assert "foo" in s
        assert "bar" in s
        assert "tlmgr install foo bar" in s


class TestGetMissingPackagesCommand:
    def test_empty(self):
        assert get_missing_packages_command([]) == ""

    def test_single_package(self):
        result = get_missing_packages_command(["multirow"])
        assert result == "sudo tlmgr install multirow"

    def test_multiple_packages(self):
        result = get_missing_packages_command(["multirow", "cleveref", "doi"])
        assert "multirow" in result
        assert "cleveref" in result
        assert "doi" in result
        assert result.startswith("sudo tlmgr install")
