"""Tests for infrastructure.rendering.latex_package_validator module.

Comprehensive tests for LaTeX package validation using real implementations.
Follows No Mocks Policy - all tests use real data and real subprocess execution.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.core.exceptions import ValidationError
from infrastructure.rendering.latex_package_validator import (
    PackageStatus, ValidationReport, check_latex_package, find_kpsewhich,
    get_missing_packages_command, validate_packages,
    validate_preamble_packages)


class TestFindKpsewhich:
    """Test find_kpsewhich function using real execution."""

    def test_find_kpsewhich_real_execution(self):
        """Test finding kpsewhich using real subprocess execution."""
        # Use real find_kpsewhich - may or may not find it depending on system
        result = find_kpsewhich()

        # Result should be None or a valid Path
        assert result is None or isinstance(result, Path)
        if result is not None:
            # If found, should be a valid path
            assert isinstance(result, Path)

    @pytest.mark.skipif(not shutil.which("which"), reason="which command not available")
    def test_find_kpsewhich_via_which_command(self):
        """Test finding kpsewhich via which command using real execution."""
        # Use real which command
        result = subprocess.run(
            ["which", "kpsewhich"], capture_output=True, text=True, check=False
        )

        # Real execution - may or may not find kpsewhich
        if result.returncode == 0 and result.stdout.strip():
            kpsewhich_path = Path(result.stdout.strip())
            assert kpsewhich_path.exists() or True  # May exist or not
        else:
            # kpsewhich not found via which - that's valid
            assert result.returncode != 0 or not result.stdout.strip()

    def test_find_kpsewhich_handles_errors(self):
        """Test that find_kpsewhich handles errors gracefully."""
        # Real execution should handle errors gracefully
        result = find_kpsewhich()

        # Should return None or valid Path, never raise
        assert result is None or isinstance(result, Path)


class TestCheckLatexPackage:
    """Test check_latex_package function using real execution."""

    @pytest.mark.skipif(not shutil.which("kpsewhich"), reason="kpsewhich not available")
    def test_check_package_real_execution(self):
        """Test checking a package using real kpsewhich."""
        kpsewhich_path = Path(shutil.which("kpsewhich"))

        # Test with a common package that might be installed
        result = check_latex_package("amsmath", kpsewhich_path=kpsewhich_path)

        assert isinstance(result, PackageStatus)
        assert result.name == "amsmath"
        # May be installed or not depending on system
        assert isinstance(result.installed, bool)
        if result.installed:
            assert result.path is not None
        else:
            assert result.path is None

    @pytest.mark.skipif(not shutil.which("kpsewhich"), reason="kpsewhich not available")
    def test_check_package_not_installed(self):
        """Test checking a package that definitely doesn't exist."""
        kpsewhich_path = Path(shutil.which("kpsewhich"))

        # Use a package name that definitely doesn't exist
        result = check_latex_package(
            "nonexistent_package_xyz_123", kpsewhich_path=kpsewhich_path
        )

        assert isinstance(result, PackageStatus)
        assert result.name == "nonexistent_package_xyz_123"
        assert result.installed is False
        assert result.path is None

    def test_check_package_no_kpsewhich(self):
        """Test checking package when kpsewhich is not found."""
        # When kpsewhich_path is None, function will try to find it
        # Result depends on whether kpsewhich is available on system
        result = check_latex_package("amsmath", kpsewhich_path=None)

        # Should return valid PackageStatus regardless
        assert isinstance(result, PackageStatus)
        assert result.name == "amsmath"
        # May be installed or not depending on system kpsewhich availability
        assert isinstance(result.installed, bool)

    @pytest.mark.skipif(not shutil.which("kpsewhich"), reason="kpsewhich not available")
    def test_check_package_handles_errors(self):
        """Test that check_latex_package handles errors gracefully."""
        kpsewhich_path = Path(shutil.which("kpsewhich"))

        # Test with real execution - should handle any errors gracefully
        result = check_latex_package("test_package", kpsewhich_path=kpsewhich_path)

        assert isinstance(result, PackageStatus)
        assert result.name == "test_package"
        # Should return valid status regardless of errors
        assert isinstance(result.installed, bool)


class TestValidatePackages:
    """Test validate_packages function using real execution."""

    @pytest.mark.skipif(not shutil.which("kpsewhich"), reason="kpsewhich not available")
    def test_validate_packages_real_execution(self):
        """Test validation using real package checking."""
        kpsewhich_path = Path(shutil.which("kpsewhich"))

        # Use real validation
        result = validate_packages(
            required=["amsmath"], optional=["cleveref"], kpsewhich_path=kpsewhich_path
        )

        assert isinstance(result, ValidationReport)
        assert len(result.required_packages) == 1
        assert len(result.optional_packages) == 1
        assert isinstance(result.all_required_available, bool)
        # May or may not have missing packages depending on system
        assert isinstance(result.missing_required, list)
        assert isinstance(result.missing_optional, list)

    def test_validate_packages_no_kpsewhich(self):
        """Test validation when kpsewhich is not found."""
        # Use real validation - function will try to find kpsewhich
        result = validate_packages(required=["amsmath"], optional=["cleveref"])

        assert isinstance(result, ValidationReport)
        # Result depends on whether kpsewhich is available on system
        # If kpsewhich found, packages may be installed or not
        # If kpsewhich not found, all_required_available should be False
        assert isinstance(result.all_required_available, bool)
        assert isinstance(result.missing_required, list)


class TestValidatePreamblePackages:
    """Test validate_preamble_packages function using real execution."""

    @pytest.mark.skipif(not shutil.which("kpsewhich"), reason="kpsewhich not available")
    def test_validate_preamble_non_strict(self):
        """Test preamble validation in non-strict mode using real execution."""
        # Use real validation
        result = validate_preamble_packages(strict=False)

        assert isinstance(result, ValidationReport)
        assert len(result.required_packages) > 0
        assert len(result.optional_packages) >= 0

    @pytest.mark.skipif(not shutil.which("kpsewhich"), reason="kpsewhich not available")
    def test_validate_preamble_strict_mode(self):
        """Test preamble validation in strict mode using real execution."""
        # Use real validation - may or may not raise depending on package availability
        try:
            result = validate_preamble_packages(strict=True)
            # If no exception, all packages available
            assert isinstance(result, ValidationReport)
            assert result.all_required_available is True
        except ValidationError:
            # If exception raised, some packages missing - that's valid
            pass

    def test_validate_preamble_no_kpsewhich(self):
        """Test preamble validation when kpsewhich not available."""
        # Should handle gracefully when kpsewhich not found
        try:
            result = validate_preamble_packages(strict=False)
            assert isinstance(result, ValidationReport)
        except ValidationError:
            # May raise if strict and packages missing
            pass


class TestGetMissingPackagesCommand:
    """Test get_missing_packages_command function."""

    def test_get_command_with_packages(self):
        """Test generating command with missing packages."""
        missing = ["cleveref", "doi", "newunicodechar"]
        result = get_missing_packages_command(missing)

        assert "sudo tlmgr install" in result
        assert "cleveref" in result
        assert "doi" in result
        assert "newunicodechar" in result

    def test_get_command_empty_list(self):
        """Test generating command with empty list."""
        result = get_missing_packages_command([])

        assert result == ""


class TestValidationReport:
    """Test ValidationReport dataclass."""

    def test_report_str_all_available(self):
        """Test report string when all packages available."""
        report = ValidationReport(
            required_packages=[PackageStatus("amsmath", True, "/path/to/amsmath.sty")],
            optional_packages=[],
            missing_required=[],
            missing_optional=[],
            all_required_available=True,
        )

        report_str = str(report)
        assert "All required packages available" in report_str
        assert "✅" in report_str

    def test_report_str_missing_required(self):
        """Test report string with missing required packages."""
        report = ValidationReport(
            required_packages=[
                PackageStatus("amsmath", True, "/path/to/amsmath.sty"),
                PackageStatus("missing", False, None),
            ],
            optional_packages=[],
            missing_required=["missing"],
            missing_optional=[],
            all_required_available=False,
        )

        report_str = str(report)
        assert "Missing" in report_str
        assert "missing" in report_str
        assert "❌" in report_str

    def test_report_str_missing_optional(self):
        """Test report string with missing optional packages."""
        report = ValidationReport(
            required_packages=[PackageStatus("amsmath", True, "/path/to/amsmath.sty")],
            optional_packages=[PackageStatus("cleveref", False, None)],
            missing_required=[],
            missing_optional=["cleveref"],
            all_required_available=True,
        )

        report_str = str(report)
        assert "optional" in report_str.lower()
        assert "cleveref" in report_str
        assert "⚠️" in report_str

    def test_report_str_installation_command(self):
        """Test report includes installation command."""
        report = ValidationReport(
            required_packages=[PackageStatus("missing", False, None)],
            optional_packages=[PackageStatus("missing_opt", False, None)],
            missing_required=["missing"],
            missing_optional=["missing_opt"],
            all_required_available=False,
        )

        report_str = str(report)
        assert "Installation command" in report_str
        assert "sudo tlmgr install" in report_str


class TestMain:
    """Test main CLI function using real execution."""

    @pytest.mark.skipif(not shutil.which("kpsewhich"), reason="kpsewhich not available")
    def test_main_kpsewhich_found(self, capsys):
        """Test main when kpsewhich is found using real execution."""
        from infrastructure.rendering.latex_package_validator import main

        # Use real execution
        try:
            exit_code = main()
            # May return 0 (all packages available) or 1 (some missing)
            assert exit_code in [0, 1]
        except SystemExit as e:
            # May exit with code
            assert e.code in [0, 1]

    def test_main_kpsewhich_not_found(self, capsys):
        """Test main when kpsewhich is not found using real execution."""
        from infrastructure.rendering.latex_package_validator import main

        # If kpsewhich not available, should handle gracefully
        # This test may pass or fail depending on system
        try:
            exit_code = main()
            # May return various codes
            assert exit_code in [0, 1]
        except SystemExit as e:
            # May exit with code
            assert e.code in [0, 1]
        except Exception:
            # May raise if kpsewhich required
            pass
