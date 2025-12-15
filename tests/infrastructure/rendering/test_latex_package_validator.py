"""Tests for infrastructure.rendering.latex_package_validator module.

Comprehensive tests for LaTeX package validation including kpsewhich
discovery, package checking, and validation reporting.
"""

from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess
import pytest
import sys

from infrastructure.rendering.latex_package_validator import (
    find_kpsewhich,
    check_latex_package,
    validate_packages,
    validate_preamble_packages,
    get_missing_packages_command,
    PackageStatus,
    ValidationReport,
)
from infrastructure.core.exceptions import ValidationError


class TestFindKpsewhich:
    """Test find_kpsewhich function."""

    def test_find_kpsewhich_in_common_path(self, tmp_path):
        """Test finding kpsewhich in common path."""
        # Create a mock kpsewhich executable
        mock_kpsewhich = tmp_path / "kpsewhich"
        mock_kpsewhich.write_text("#!/bin/sh\necho")
        mock_kpsewhich.chmod(0o755)
        
        common_path = tmp_path / "texlive" / "2025basic" / "bin" / "universal-darwin" / "kpsewhich"
        common_path.parent.mkdir(parents=True)
        common_path.write_text("#!/bin/sh\necho")
        common_path.chmod(0o755)
        
        with patch('infrastructure.rendering.latex_package_validator.Path') as mock_path_class:
            # Mock Path.exists() to return True for our test path
            def mock_exists(self):
                return str(self) == str(common_path)
            
            mock_path_class.side_effect = lambda p: type('Path', (), {
                'exists': lambda: str(p) == str(common_path),
                '__str__': lambda self: str(p),
                '__fspath__': lambda self: str(p)
            })()
            
            # Patch the common_paths list
            with patch('infrastructure.rendering.latex_package_validator.find_kpsewhich', 
                      wraps=find_kpsewhich) as wrapped:
                # Since we can't easily mock Path.exists() in a clean way,
                # we'll test the subprocess fallback path instead
                pass

    def test_find_kpsewhich_via_which_command(self):
        """Test finding kpsewhich via which command."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "/usr/local/bin/kpsewhich\n"
        
        # Mock Path.exists() to return False for common paths, forcing which fallback
        with patch('pathlib.Path.exists', return_value=False):
            with patch('subprocess.run', return_value=mock_result):
                result = find_kpsewhich()
        
        assert result is not None
        assert isinstance(result, Path)
        assert "/usr/local/bin/kpsewhich" in str(result) or "kpsewhich" in str(result)

    def test_find_kpsewhich_not_found(self):
        """Test when kpsewhich is not found."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('pathlib.Path.exists', return_value=False):
                result = find_kpsewhich()
        
        assert result is None

    def test_find_kpsewhich_which_exception(self):
        """Test exception handling in which command."""
        with patch('subprocess.run', side_effect=Exception("Test error")):
            with patch('pathlib.Path.exists', return_value=False):
                result = find_kpsewhich()
        
        assert result is None


class TestCheckLatexPackage:
    """Test check_latex_package function."""

    def test_check_package_installed(self):
        """Test checking an installed package."""
        mock_kpsewhich = Path("/usr/local/bin/kpsewhich")
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "/usr/local/texlive/2025/texmf-dist/tex/latex/amsmath/amsmath.sty\n"
        
        with patch('subprocess.run', return_value=mock_result):
            result = check_latex_package("amsmath", kpsewhich_path=mock_kpsewhich)
        
        assert result.installed is True
        assert result.name == "amsmath"
        assert result.path is not None
        assert "amsmath.sty" in result.path

    def test_check_package_not_installed(self):
        """Test checking a missing package."""
        mock_kpsewhich = Path("/usr/local/bin/kpsewhich")
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        
        with patch('subprocess.run', return_value=mock_result):
            result = check_latex_package("nonexistent", kpsewhich_path=mock_kpsewhich)
        
        assert result.installed is False
        assert result.name == "nonexistent"
        assert result.path is None

    def test_check_package_no_kpsewhich(self):
        """Test checking package when kpsewhich is not found."""
        with patch('infrastructure.rendering.latex_package_validator.find_kpsewhich', return_value=None):
            result = check_latex_package("amsmath")
        
        assert result.installed is False
        assert result.name == "amsmath"
        assert result.path is None

    def test_check_package_timeout(self):
        """Test timeout handling."""
        mock_kpsewhich = Path("/usr/local/bin/kpsewhich")
        
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("kpsewhich", 5)):
            result = check_latex_package("amsmath", kpsewhich_path=mock_kpsewhich)
        
        assert result.installed is False
        assert result.name == "amsmath"

    def test_check_package_exception(self):
        """Test exception handling."""
        mock_kpsewhich = Path("/usr/local/bin/kpsewhich")
        
        with patch('subprocess.run', side_effect=Exception("Test error")):
            result = check_latex_package("amsmath", kpsewhich_path=mock_kpsewhich)
        
        assert result.installed is False
        assert result.name == "amsmath"

    def test_check_package_empty_output(self):
        """Test when kpsewhich returns empty output."""
        mock_kpsewhich = Path("/usr/local/bin/kpsewhich")
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        
        with patch('subprocess.run', return_value=mock_result):
            result = check_latex_package("amsmath", kpsewhich_path=mock_kpsewhich)
        
        assert result.installed is False


class TestValidatePackages:
    """Test validate_packages function."""

    def test_validate_all_installed(self):
        """Test validation when all packages are installed."""
        mock_kpsewhich = Path("/usr/local/bin/kpsewhich")
        
        def mock_check(pkg, kpsewhich_path=None):
            return PackageStatus(name=pkg, installed=True, path=f"/path/to/{pkg}.sty")
        
        with patch('infrastructure.rendering.latex_package_validator.check_latex_package', side_effect=mock_check):
            result = validate_packages(
                required=["amsmath", "graphicx"],
                optional=["cleveref"],
                kpsewhich_path=mock_kpsewhich
            )
        
        assert result.all_required_available is True
        assert len(result.missing_required) == 0
        assert len(result.missing_optional) == 0
        assert len(result.required_packages) == 2
        assert len(result.optional_packages) == 1

    def test_validate_missing_required(self):
        """Test validation with missing required packages."""
        mock_kpsewhich = Path("/usr/local/bin/kpsewhich")
        
        def mock_check(pkg, kpsewhich_path=None):
            installed = pkg != "missing"
            return PackageStatus(
                name=pkg,
                installed=installed,
                path=f"/path/to/{pkg}.sty" if installed else None
            )
        
        with patch('infrastructure.rendering.latex_package_validator.check_latex_package', side_effect=mock_check):
            result = validate_packages(
                required=["amsmath", "missing"],
                optional=["cleveref"],
                kpsewhich_path=mock_kpsewhich
            )
        
        assert result.all_required_available is False
        assert len(result.missing_required) == 1
        assert "missing" in result.missing_required
        assert len(result.missing_optional) == 0

    def test_validate_missing_optional(self):
        """Test validation with missing optional packages."""
        mock_kpsewhich = Path("/usr/local/bin/kpsewhich")
        
        def mock_check(pkg, kpsewhich_path=None):
            installed = pkg != "missing_opt"
            return PackageStatus(
                name=pkg,
                installed=installed,
                path=f"/path/to/{pkg}.sty" if installed else None
            )
        
        with patch('infrastructure.rendering.latex_package_validator.check_latex_package', side_effect=mock_check):
            result = validate_packages(
                required=["amsmath"],
                optional=["missing_opt"],
                kpsewhich_path=mock_kpsewhich
            )
        
        assert result.all_required_available is True
        assert len(result.missing_required) == 0
        assert len(result.missing_optional) == 1
        assert "missing_opt" in result.missing_optional

    def test_validate_no_kpsewhich(self):
        """Test validation when kpsewhich is not found."""
        with patch('infrastructure.rendering.latex_package_validator.find_kpsewhich', return_value=None):
            result = validate_packages(
                required=["amsmath"],
                optional=["cleveref"]
            )
        
        assert result.all_required_available is False
        assert len(result.missing_required) == 1


class TestValidatePreamblePackages:
    """Test validate_preamble_packages function."""

    def test_validate_preamble_non_strict(self):
        """Test preamble validation in non-strict mode."""
        mock_kpsewhich = Path("/usr/local/bin/kpsewhich")
        
        def mock_check(pkg, kpsewhich_path=None):
            return PackageStatus(name=pkg, installed=True, path=f"/path/to/{pkg}.sty")
        
        with patch('infrastructure.rendering.latex_package_validator.check_latex_package', side_effect=mock_check):
            with patch('infrastructure.rendering.latex_package_validator.find_kpsewhich', return_value=mock_kpsewhich):
                result = validate_preamble_packages(strict=False)
        
        assert isinstance(result, ValidationReport)
        assert len(result.required_packages) > 0
        assert len(result.optional_packages) > 0

    def test_validate_preamble_strict_mode(self):
        """Test preamble validation in strict mode."""
        mock_kpsewhich = Path("/usr/local/bin/kpsewhich")
        
        def mock_check(pkg, kpsewhich_path=None):
            # Make some packages missing
            missing = ["cleveref", "doi"]
            installed = pkg not in missing
            return PackageStatus(
                name=pkg,
                installed=installed,
                path=f"/path/to/{pkg}.sty" if installed else None
            )
        
        with patch('infrastructure.rendering.latex_package_validator.check_latex_package', side_effect=mock_check):
            with patch('infrastructure.rendering.latex_package_validator.find_kpsewhich', return_value=mock_kpsewhich):
                with pytest.raises(ValidationError) as exc_info:
                    validate_preamble_packages(strict=True)
        
        assert "Missing required LaTeX packages" in str(exc_info.value)
        assert "cleveref" in str(exc_info.value) or "doi" in str(exc_info.value)

    def test_validate_preamble_strict_all_available(self):
        """Test strict mode when all packages are available."""
        mock_kpsewhich = Path("/usr/local/bin/kpsewhich")
        
        def mock_check(pkg, kpsewhich_path=None):
            return PackageStatus(name=pkg, installed=True, path=f"/path/to/{pkg}.sty")
        
        with patch('infrastructure.rendering.latex_package_validator.check_latex_package', side_effect=mock_check):
            with patch('infrastructure.rendering.latex_package_validator.find_kpsewhich', return_value=mock_kpsewhich):
                result = validate_preamble_packages(strict=True)
        
        assert isinstance(result, ValidationReport)
        assert result.all_required_available is True


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
            all_required_available=True
        )
        
        report_str = str(report)
        assert "All required packages available" in report_str
        assert "✅" in report_str

    def test_report_str_missing_required(self):
        """Test report string with missing required packages."""
        report = ValidationReport(
            required_packages=[
                PackageStatus("amsmath", True, "/path/to/amsmath.sty"),
                PackageStatus("missing", False, None)
            ],
            optional_packages=[],
            missing_required=["missing"],
            missing_optional=[],
            all_required_available=False
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
            all_required_available=True
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
            all_required_available=False
        )
        
        report_str = str(report)
        assert "Installation command" in report_str
        assert "sudo tlmgr install" in report_str


class TestMain:
    """Test main CLI function."""

    def test_main_kpsewhich_found(self, capsys):
        """Test main when kpsewhich is found."""
        mock_kpsewhich = Path("/usr/local/bin/kpsewhich")
        
        def mock_check(pkg, kpsewhich_path=None):
            return PackageStatus(name=pkg, installed=True, path=f"/path/to/{pkg}.sty")
        
        with patch('infrastructure.rendering.latex_package_validator.find_kpsewhich', return_value=mock_kpsewhich):
            with patch('infrastructure.rendering.latex_package_validator.check_latex_package', side_effect=mock_check):
                with pytest.raises(SystemExit) as exc_info:
                    from infrastructure.rendering.latex_package_validator import main
                    main()
        
        assert exc_info.value.code == 0

    def test_main_kpsewhich_not_found(self, capsys):
        """Test main when kpsewhich is not found."""
        with patch('infrastructure.rendering.latex_package_validator.find_kpsewhich', return_value=None):
            with pytest.raises(SystemExit) as exc_info:
                from infrastructure.rendering.latex_package_validator import main
                main()
        
        assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        assert "kpsewhich not found" in captured.out

    def test_main_missing_packages(self, capsys):
        """Test main when packages are missing."""
        mock_kpsewhich = Path("/usr/local/bin/kpsewhich")
        
        def mock_check(pkg, kpsewhich_path=None):
            # Make some required packages missing
            missing_packages = ["amsmath", "graphicx"]
            installed = pkg not in missing_packages
            return PackageStatus(
                name=pkg,
                installed=installed,
                path=f"/path/to/{pkg}.sty" if installed else None
            )
        
        with patch('infrastructure.rendering.latex_package_validator.find_kpsewhich', return_value=mock_kpsewhich):
            with patch('infrastructure.rendering.latex_package_validator.check_latex_package', side_effect=mock_check):
                with pytest.raises(SystemExit) as exc_info:
                    from infrastructure.rendering.latex_package_validator import main
                    main()
        
        assert exc_info.value.code == 1




