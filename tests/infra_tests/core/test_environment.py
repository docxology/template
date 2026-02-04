"""Tests for environment setup and validation utilities.

Tests environment validation functions using real data only.
No mocks - uses actual system state and temp directories.
"""

import os
import sys
from pathlib import Path

import pytest

from infrastructure.core.environment import (check_dependencies,
                                             check_python_version)


class TestCheckPythonVersion:
    """Tests for check_python_version function."""

    def test_python_version_check_succeeds(self):
        """Test that Python version check succeeds on current system."""
        # We're running on Python 3.8+, so this should pass
        result = check_python_version()

        assert result is True

    def test_version_info_is_valid(self):
        """Test that sys.version_info contains expected components."""
        version = sys.version_info

        assert version.major >= 3
        assert version.minor >= 0
        assert version.micro >= 0


class TestCheckDependencies:
    """Tests for check_dependencies function."""

    def test_check_default_dependencies(self):
        """Test checking default required packages."""
        all_present, missing = check_dependencies()

        # Core packages should be present in test environment
        # numpy, matplotlib, pytest, requests are required
        assert isinstance(all_present, bool)
        assert isinstance(missing, list)

    def test_check_specific_packages_present(self):
        """Test checking packages known to be present."""
        # These packages are definitely installed in test environment
        packages = ["pytest", "pathlib"]
        all_present, missing = check_dependencies(packages)

        # pytest is definitely present since we're running tests with it
        assert "pytest" not in missing

    def test_check_nonexistent_package(self):
        """Test checking a package that doesn't exist."""
        packages = ["nonexistent_package_12345_xyz"]
        all_present, missing = check_dependencies(packages)

        assert all_present is False
        assert "nonexistent_package_12345_xyz" in missing

    def test_check_mixed_packages(self):
        """Test checking mix of present and missing packages."""
        packages = ["pytest", "completely_fake_package_999"]
        all_present, missing = check_dependencies(packages)

        assert all_present is False
        assert "completely_fake_package_999" in missing
        assert "pytest" not in missing

    def test_check_empty_list(self):
        """Test checking empty package list."""
        all_present, missing = check_dependencies([])

        assert all_present is True
        assert missing == []

    def test_returns_tuple(self):
        """Test that function returns proper tuple type."""
        result = check_dependencies(["pytest"])

        assert isinstance(result, tuple)
        assert len(result) == 2


class TestEnvironmentSetupIntegration:
    """Integration tests for environment setup."""

    def test_full_environment_check(self):
        """Test running multiple environment checks together."""
        # Check Python version
        python_ok = check_python_version()
        assert python_ok is True

        # Check core packages
        deps_ok, missing = check_dependencies(["pytest"])
        assert deps_ok is True

    def test_environment_variables_accessible(self):
        """Test that environment variables can be accessed."""
        # Set a test variable
        os.environ["TEST_ENV_VAR_12345"] = "test_value"

        try:
            assert os.environ.get("TEST_ENV_VAR_12345") == "test_value"
        finally:
            # Clean up
            del os.environ["TEST_ENV_VAR_12345"]

    def test_path_operations(self, tmp_path):
        """Test path operations work correctly."""
        # Create test directory structure
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        output_dir = test_dir / "output"
        output_dir.mkdir()

        assert test_dir.exists()
        assert output_dir.exists()
        assert test_dir.is_dir()

    def test_current_working_directory(self):
        """Test current working directory is accessible."""
        cwd = Path.cwd()

        assert cwd.exists()
        assert cwd.is_dir()

    def test_home_directory_accessible(self):
        """Test home directory is accessible."""
        home = Path.home()

        assert home.exists()
        assert home.is_dir()


class TestDependencyValidation:
    """Tests for dependency validation scenarios."""

    def test_numpy_importable(self):
        """Test that numpy can be imported."""
        try:
            import numpy

            can_import = True
        except ImportError:
            can_import = False

        # This test documents the current state
        # numpy should be installed in the test environment
        assert can_import is True

    def test_pytest_importable(self):
        """Test that pytest can be imported."""
        import pytest as _pytest

        assert _pytest is not None

    def test_pathlib_importable(self):
        """Test that pathlib can be imported."""
        from pathlib import Path as _Path

        assert _Path is not None

    def test_check_standard_library(self):
        """Test checking standard library modules."""
        packages = ["os", "sys", "pathlib", "json"]
        all_present, missing = check_dependencies(packages)

        assert all_present is True
        assert missing == []


class TestEnvironmentState:
    """Tests for environment state queries."""

    def test_python_executable_exists(self):
        """Test Python executable path is valid."""
        python_path = sys.executable

        assert python_path is not None
        assert Path(python_path).exists()

    def test_platform_info_available(self):
        """Test platform information is available."""
        platform = sys.platform

        assert platform in ["linux", "darwin", "win32", "cygwin"]

    def test_version_components(self):
        """Test Python version has all components."""
        v = sys.version_info

        assert hasattr(v, "major")
        assert hasattr(v, "minor")
        assert hasattr(v, "micro")
        assert hasattr(v, "releaselevel")

    def test_import_system_working(self):
        """Test the import system is working correctly."""
        # Test that we can import and the module has expected attributes
        import infrastructure.core.environment as env_module

        assert hasattr(env_module, "check_python_version")
        assert hasattr(env_module, "check_dependencies")
        assert callable(env_module.check_python_version)
        assert callable(env_module.check_dependencies)
