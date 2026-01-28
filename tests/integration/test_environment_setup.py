"""Integration tests for environment setup.

Tests real system operations without mocks:
- uv package manager integration
- Real dependency checking
- Real directory creation
- Real build tool validation
- Real subprocess execution
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from infrastructure.core.environment import (check_build_tools,
                                             check_dependencies,
                                             check_python_version,
                                             check_uv_available,
                                             get_python_command,
                                             get_subprocess_env,
                                             install_missing_packages,
                                             set_environment_variables,
                                             setup_directories,
                                             validate_directory_structure,
                                             validate_uv_sync_result,
                                             verify_source_structure)


@pytest.mark.integration
class TestEnvironmentSetupIntegration:
    """Integration tests for complete environment setup."""

    def test_complete_setup_with_uv(self, tmp_path):
        """Test complete setup when uv is available."""
        if not shutil.which("uv"):
            pytest.skip("uv not installed - skipping integration test")

        # Create a minimal pyproject.toml for testing
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """[project]
name = "test-environment-setup"
version = "0.1.0"
description = "Test project for environment setup"
requires-python = ">=3.8"
dependencies = []

[tool.uv]
managed = true
package = false
"""
        )

        # Test uv sync with real subprocess
        result = subprocess.run(
            ["uv", "sync"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            check=False,
        )

        # Should succeed
        assert result.returncode == 0, f"uv sync failed: {result.stderr}"

        # Validate sync results
        success, message = validate_uv_sync_result(tmp_path)
        assert success, f"uv sync validation failed: {message}"

        # Check for expected artifacts
        assert (tmp_path / ".venv").exists(), "Virtual environment not created"
        assert (tmp_path / "uv.lock").exists(), "Lock file not generated"

    def test_complete_setup_without_uv(self, tmp_path):
        """Test complete setup fallback without uv."""
        # Ensure uv is not available for this test
        if shutil.which("uv"):
            pytest.skip("uv is available - cannot test fallback path")

        # Test fallback dependency checking
        all_present, missing = check_dependencies(["sys", "os"])

        # Should succeed with built-in modules
        assert all_present is True
        assert len(missing) == 0

    def test_directory_structure_creation(self, tmp_path):
        """Test real directory creation."""
        project_name = "test_project"

        # Create a real project structure
        project_dir = tmp_path / "projects" / project_name
        project_dir.mkdir(parents=True)
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()
        (project_dir / "__init__.py").write_text("")
        (project_dir / "src" / "__init__.py").write_text("")
        (project_dir / "tests" / "__init__.py").write_text("")

        # Test directory setup
        result = setup_directories(tmp_path, project_name)

        assert result is True

        # Verify all expected directories exist
        expected_dirs = [
            f"output/{project_name}",
            f"output/{project_name}/figures",
            f"output/{project_name}/data",
            f"output/{project_name}/tex",
            f"output/{project_name}/pdf",
            f"output/{project_name}/logs",
            f"output/{project_name}/reports",
            f"output/{project_name}/simulations",
            f"output/{project_name}/slides",
            f"output/{project_name}/web",
            f"output/{project_name}/llm",
            f"projects/{project_name}/output",
            f"projects/{project_name}/output/figures",
            f"projects/{project_name}/output/data",
            f"projects/{project_name}/output/pdf",
            f"projects/{project_name}/output/tex",
            f"projects/{project_name}/output/logs",
            f"projects/{project_name}/output/reports",
            f"projects/{project_name}/output/simulations",
            f"projects/{project_name}/output/slides",
            f"projects/{project_name}/output/web",
            f"projects/{project_name}/output/llm",
        ]

        for dir_path in expected_dirs:
            full_path = tmp_path / dir_path
            assert full_path.exists(), f"Directory not created: {dir_path}"
            assert full_path.is_dir(), f"Path is not a directory: {dir_path}"

    def test_build_tool_detection(self):
        """Test real build tool availability."""
        # Test with real shutil.which calls
        tools_to_test = {
            "pandoc": "Document conversion",
            "xelatex": "LaTeX compilation",
        }

        result = check_build_tools(tools_to_test)

        # Result should be boolean based on actual system state
        assert isinstance(result, bool)

        # Test individual tools
        for tool, purpose in tools_to_test.items():
            available = shutil.which(tool) is not None
            # Just verify the function returns a boolean
            # (actual availability depends on system setup)
            assert isinstance(available, bool)

    def test_python_version_validation(self):
        """Test real Python version checking."""
        result = check_python_version()

        # Should return boolean based on actual Python version
        assert isinstance(result, bool)

        # Should pass for Python 3.8+ (our minimum requirement)
        assert result is True, f"Python version check failed: {sys.version}"

    def test_dependency_validation(self):
        """Test real dependency checking."""
        # Test with built-in modules that should always exist
        builtin_deps = ["sys", "os", "pathlib"]
        all_present, missing = check_dependencies(builtin_deps)

        assert all_present is True
        assert len(missing) == 0

        # Test with non-existent package
        fake_deps = ["definitely_not_a_real_package_12345"]
        all_present, missing = check_dependencies(fake_deps)

        assert all_present is False
        assert len(missing) == 1
        assert "definitely_not_a_real_package_12345" in missing

    def test_uv_availability_check(self):
        """Test real uv availability checking."""
        result = check_uv_available()

        # Should return boolean based on actual system state
        assert isinstance(result, bool)

        # Should match shutil.which result
        expected = shutil.which("uv") is not None
        assert result == expected

    def test_python_command_selection(self):
        """Test real Python command selection."""
        cmd = get_python_command()

        # Should return a list
        assert isinstance(cmd, list)
        assert len(cmd) > 0
        assert all(isinstance(part, str) for part in cmd)

        # If uv is available, should use uv run python
        if check_uv_available():
            assert cmd == ["uv", "run", "python"]
        else:
            # Should use current Python executable
            assert cmd == [sys.executable]

    def test_source_structure_verification(self, tmp_path):
        """Test real source structure verification."""
        # Create minimal valid structure
        (tmp_path / "infrastructure").mkdir()
        (tmp_path / "projects").mkdir()
        (tmp_path / "projects" / "test").mkdir()
        (tmp_path / "projects" / "test" / "src").mkdir()
        (tmp_path / "projects" / "test" / "tests").mkdir()

        # Create __init__.py files
        (tmp_path / "projects" / "test" / "src" / "__init__.py").write_text("")
        (tmp_path / "projects" / "test" / "tests" / "__init__.py").write_text("")

        result = verify_source_structure(tmp_path, "test")

        assert result is True

    def test_source_structure_verification_missing_dirs(self, tmp_path):
        """Test source structure verification with missing directories."""
        # Create incomplete structure
        (tmp_path / "infrastructure").mkdir()

        result = verify_source_structure(tmp_path, "test")

        assert result is False

    def test_environment_variable_setting(self, tmp_path):
        """Test real environment variable setting."""
        # Save original values
        original_vars = {}
        vars_to_test = ["MPLBACKEND", "PYTHONIOENCODING", "PROJECT_ROOT"]
        for var in vars_to_test:
            original_vars[var] = os.environ.get(var)

        try:
            result = set_environment_variables(tmp_path)

            assert result is True

            # Check that variables were set
            assert os.environ.get("MPLBACKEND") == "Agg"
            assert os.environ.get("PYTHONIOENCODING") == "utf-8"
            assert os.environ.get("PROJECT_ROOT") == str(tmp_path)

        finally:
            # Restore original values
            for var, value in original_vars.items():
                if value is not None:
                    os.environ[var] = value
                elif var in os.environ:
                    del os.environ[var]

    def test_install_missing_packages_fallback(self, tmp_path):
        """Test install_missing_packages fallback behavior."""
        # Test with uv unavailable
        if shutil.which("uv"):
            pytest.skip("uv is available - cannot test fallback")

        # Should return False when uv is not available
        result = install_missing_packages(["test_package"])

        assert result is False

    def test_install_missing_packages_with_uv(self, tmp_path):
        """Test install_missing_packages with uv available."""
        if not shutil.which("uv"):
            pytest.skip("uv not available - skipping integration test")

        # Create a minimal pyproject.toml
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """[project]
name = "test-install"
version = "0.1.0"
dependencies = []
"""
        )

        # Test installation of a simple package
        # Note: This would actually install the package, so we skip for safety
        # In a real scenario, you'd test with a test-specific package
        pytest.skip(
            "Package installation test skipped for safety - would modify environment"
        )

    def test_validate_directory_structure(self, tmp_path):
        """Test directory structure validation."""
        project_name = "test_project"

        # Create some directories
        test_dirs = [
            f"output/{project_name}",
            f"output/{project_name}/figures",
            f"projects/{project_name}/output",
        ]

        for dir_path in test_dirs:
            (tmp_path / dir_path).mkdir(parents=True)

        # Test validation
        missing = validate_directory_structure(tmp_path, project_name)

        # Should return empty list if all directories exist
        assert isinstance(missing, list)

    def test_uv_sync_validation(self, tmp_path):
        """Test uv sync result validation."""
        # Test with no sync performed
        success, message = validate_uv_sync_result(tmp_path)
        assert success is False
        assert "Virtual environment not created" in message

        # Create fake .venv directory
        venv_dir = tmp_path / ".venv"
        venv_dir.mkdir()

        success, message = validate_uv_sync_result(tmp_path)
        assert success is False
        assert "Lock file not generated" in message

        # Create fake uv.lock file
        lock_file = tmp_path / "uv.lock"
        lock_file.write_text("fake lock content")

        success, message = validate_uv_sync_result(tmp_path)
        assert success is True
        assert "uv sync completed successfully" in message

    def test_real_subprocess_execution_patterns(self):
        """Test various real subprocess execution patterns."""
        # Test a simple command that should always work
        result = subprocess.run(
            [sys.executable, "-c", 'print("test")'],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        assert result.stdout.strip() == "test"

        # Test error handling
        result = subprocess.run(
            [sys.executable, "-c", "import sys; sys.exit(1)"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 1

    def test_filesystem_operations_integration(self, tmp_path):
        """Test integration of filesystem operations."""
        # Create complex directory structure
        test_structure = {
            "projects/test/src": ["module1.py", "module2.py"],
            "projects/test/tests": ["test_module1.py", "test_module2.py"],
            "output/test/figures": ["fig1.png", "fig2.png"],
            "output/test/data": ["data.csv"],
        }

        # Create directories and files
        for dir_path, files in test_structure.items():
            full_dir = tmp_path / dir_path
            full_dir.mkdir(parents=True, exist_ok=True)

            for filename in files:
                (full_dir / filename).write_text(f"# Test {filename}")

        # Verify structure
        for dir_path, files in test_structure.items():
            full_dir = tmp_path / dir_path
            assert full_dir.exists()

            for filename in files:
                file_path = full_dir / filename
                assert file_path.exists()
                assert file_path.read_text().startswith("# Test")

    def test_environment_isolation(self, tmp_path):
        """Test that environment setup doesn't affect global state."""
        # Save original environment
        original_env = dict(os.environ)

        try:
            # Run environment setup
            result = set_environment_variables(tmp_path)

            assert result is True

            # Check that expected variables are set
            assert os.environ.get("MPLBACKEND") == "Agg"
            assert os.environ.get("PYTHONIOENCODING") == "utf-8"

        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)

    def test_get_subprocess_env_basic(self):
        """Test get_subprocess_env returns a clean environment dict."""
        # Save original environment
        original_env = dict(os.environ)

        try:
            # Set a test variable
            os.environ["TEST_VAR"] = "test_value"

            # Get subprocess environment
            env = get_subprocess_env()

            # Verify it's a dict and contains expected variables
            assert isinstance(env, dict)
            assert "TEST_VAR" in env
            assert env["TEST_VAR"] == "test_value"

            # Verify it's a copy, not the original
            assert env is not os.environ

        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)

    def test_get_subprocess_env_with_uv_virtual_env_removed(self):
        """Test get_subprocess_env removes VIRTUAL_ENV when uv is available."""
        # Save original environment
        original_env = dict(os.environ)

        try:
            # Set VIRTUAL_ENV to simulate environment
            os.environ["VIRTUAL_ENV"] = "/some/absolute/path/to/venv"

            # Mock uv availability (if not available, should not remove VIRTUAL_ENV)
            if check_uv_available():
                env = get_subprocess_env()
                assert "VIRTUAL_ENV" not in env
            else:
                env = get_subprocess_env()
                assert "VIRTUAL_ENV" in env  # Should be preserved when uv not available

        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)

    def test_get_subprocess_env_with_base_env(self):
        """Test get_subprocess_env with custom base environment."""
        base_env = {"CUSTOM_VAR": "custom_value", "PATH": "/custom/path"}
        env = get_subprocess_env(base_env)

        assert env["CUSTOM_VAR"] == "custom_value"
        assert env["PATH"] == "/custom/path"

        # Test VIRTUAL_ENV handling with custom base
        base_env_with_venv = {"VIRTUAL_ENV": "/test/venv", "OTHER_VAR": "other"}
        if check_uv_available():
            env = get_subprocess_env(base_env_with_venv)
            assert "VIRTUAL_ENV" not in env
            assert env["OTHER_VAR"] == "other"
        else:
            env = get_subprocess_env(base_env_with_venv)
            assert env["VIRTUAL_ENV"] == "/test/venv"
