"""Tests for environment setup and validation utilities.

Tests environment validation functions using real data only.
No mocks - uses actual system state and temp directories.
"""

import os


from infrastructure.core.environment import (
    check_dependencies,
    check_python_version,
    get_subprocess_env,
    setup_directories,
    validate_directory_structure,
    validate_uv_sync_result,
)


class TestCheckPythonVersion:
    """Tests for check_python_version function."""

    def test_python_version_check_succeeds(self):
        """Test that Python version check succeeds on current system."""
        # We're running on Python 3.8+, so this should pass
        result = check_python_version()

        assert result is True

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

class TestDependencyValidation:
    """Tests for dependency validation scenarios."""

    def test_check_standard_library(self):
        """Test checking standard library modules."""
        packages = ["os", "sys", "pathlib", "json"]
        all_present, missing = check_dependencies(packages)

        assert all_present is True
        assert missing == []


class TestEnvironmentState:
    """Tests for environment state queries."""

    def test_import_system_working(self):
        """Test the import system is working correctly."""
        # Test that we can import and the module has expected attributes
        import infrastructure.core.environment as env_module

        assert hasattr(env_module, "check_python_version")
        assert hasattr(env_module, "check_dependencies")
        assert callable(env_module.check_python_version)
        assert callable(env_module.check_dependencies)


class TestSetupDirectories:
    """Tests for setup_directories and validate_directory_structure."""

    def test_setup_directories_creates_structure(self, tmp_path):
        """Test that setup_directories creates all expected directories."""
        result = setup_directories(tmp_path, "test_project")

        assert result is True
        assert (tmp_path / "output" / "test_project").is_dir()
        assert (tmp_path / "output" / "test_project" / "figures").is_dir()
        assert (tmp_path / "projects" / "test_project" / "output").is_dir()

    def test_setup_directories_idempotent(self, tmp_path):
        """Test that running setup twice does not fail."""
        first = setup_directories(tmp_path, "idempotent_project")
        second = setup_directories(tmp_path, "idempotent_project")

        assert first is True
        assert second is True

    def test_setup_directories_custom_list(self, tmp_path):
        """Test setup_directories with a custom directory list."""
        custom_dirs = ["custom/a", "custom/b/c"]
        result = setup_directories(tmp_path, "unused", directories=custom_dirs)

        assert result is True
        assert (tmp_path / "custom" / "a").is_dir()
        assert (tmp_path / "custom" / "b" / "c").is_dir()

    def test_validate_directory_structure_all_present(self, tmp_path):
        """Test validate_directory_structure returns empty list when all dirs exist."""
        setup_directories(tmp_path, "valid_project")
        missing = validate_directory_structure(tmp_path, "valid_project")

        assert missing == []

    def test_validate_directory_structure_reports_missing(self, tmp_path):
        """Test validate_directory_structure reports missing directories."""
        # Don't create any directories — all should be missing
        missing = validate_directory_structure(tmp_path, "missing_project")

        assert len(missing) > 0
        assert all(isinstance(m, str) for m in missing)

    def test_validate_directory_structure_partial(self, tmp_path):
        """Test validate when some but not all directories exist."""
        (tmp_path / "output" / "partial_proj").mkdir(parents=True)
        missing = validate_directory_structure(tmp_path, "partial_proj")

        # Some subdirs will still be missing
        assert len(missing) > 0


class TestGetSubprocessEnv:
    """Tests for get_subprocess_env."""

    def test_returns_dict(self):
        """Test that get_subprocess_env returns a dict."""
        env = get_subprocess_env()
        assert isinstance(env, dict)

    def test_inherits_parent_env(self):
        """Test that returned env inherits variables from os.environ."""
        os.environ["TEST_SUBPROCESS_VAR_99"] = "hello"
        try:
            env = get_subprocess_env()
            assert env.get("TEST_SUBPROCESS_VAR_99") == "hello"
        finally:
            del os.environ["TEST_SUBPROCESS_VAR_99"]

    def test_custom_base_env(self):
        """Test with a custom base env dict."""
        base = {"MY_VAR": "my_value", "PATH": "/usr/bin"}
        env = get_subprocess_env(base)
        assert env["MY_VAR"] == "my_value"

    def test_returns_copy_not_reference(self):
        """Test that modifying the returned dict does not affect os.environ."""
        env = get_subprocess_env()
        env["__TEST_ISOLATION__"] = "should_not_propagate"
        assert "__TEST_ISOLATION__" not in os.environ


class TestValidateUvSyncResult:
    """Tests for validate_uv_sync_result."""

    def test_returns_false_when_no_venv(self, tmp_path):
        """Test returns failure when .venv is absent."""
        (tmp_path / "uv.lock").write_text("placeholder")
        ok, msg = validate_uv_sync_result(tmp_path)

        assert ok is False
        assert isinstance(msg, str)

    def test_returns_false_when_no_lock_file(self, tmp_path):
        """Test returns failure when uv.lock is absent."""
        (tmp_path / ".venv").mkdir()
        ok, msg = validate_uv_sync_result(tmp_path)

        assert ok is False
        assert isinstance(msg, str)

    def test_returns_true_when_both_present(self, tmp_path):
        """Test returns success when both .venv dir and uv.lock exist."""
        (tmp_path / ".venv").mkdir()
        (tmp_path / "uv.lock").write_text("placeholder")
        ok, msg = validate_uv_sync_result(tmp_path)

        assert ok is True
        assert isinstance(msg, str)
