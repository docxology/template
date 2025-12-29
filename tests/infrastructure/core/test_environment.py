"""Tests for infrastructure.core.environment module.

Comprehensive tests for environment setup and validation utilities.
"""

import os
import subprocess
import sys
from pathlib import Path
import pytest
import tempfile
from unittest.mock import patch, MagicMock

from infrastructure.core.environment import (
    check_python_version,
    check_dependencies,
    install_missing_packages,
    check_build_tools,
    setup_directories,
    verify_source_structure,
    set_environment_variables,
    check_uv_available,
    get_python_command,
)


class TestCheckPythonVersion:
    """Test check_python_version function."""

    def test_check_python_version_current(self):
        """Test checking current Python version."""
        result = check_python_version()
        
        # Should pass for Python 3.8+
        assert result is True

    @patch('sys.version_info')
    def test_check_python_version_38(self, mock_version_info):
        """Test with Python 3.8."""
        mock_version_info.major = 3
        mock_version_info.minor = 8
        mock_version_info.micro = 0
        
        result = check_python_version()
        
        assert result is True

    @patch('sys.version_info')
    def test_check_python_version_37(self, mock_version_info):
        """Test with Python 3.7 (should fail)."""
        mock_version_info.major = 3
        mock_version_info.minor = 7
        mock_version_info.micro = 0
        
        result = check_python_version()
        
        assert result is False

    @patch('sys.version_info')
    def test_check_python_version_2(self, mock_version_info):
        """Test with Python 2 (should fail)."""
        mock_version_info.major = 2
        mock_version_info.minor = 7
        mock_version_info.micro = 0
        
        result = check_python_version()
        
        assert result is False


class TestCheckDependencies:
    """Test check_dependencies function."""

    def test_check_dependencies_default(self):
        """Test checking default dependencies."""
        all_present, missing = check_dependencies()
        
        # Should check for numpy, matplotlib, pytest, requests
        # At least some should be present in test environment
        assert isinstance(all_present, bool)
        assert isinstance(missing, list)

    def test_check_dependencies_custom_list(self):
        """Test checking custom dependency list."""
        # Use packages that should exist
        custom_packages = ['sys', 'os', 'pathlib']
        
        all_present, missing = check_dependencies(custom_packages)
        
        # These are built-in modules, should all be present
        assert all_present is True
        assert len(missing) == 0

    def test_check_dependencies_missing_packages(self):
        """Test checking with non-existent packages."""
        fake_packages = ['nonexistent_package_xyz_123', 'another_fake_package_456']
        
        all_present, missing = check_dependencies(fake_packages)
        
        assert all_present is False
        assert len(missing) == 2
        assert all(pkg in missing for pkg in fake_packages)

    def test_check_dependencies_mixed(self):
        """Test checking with mix of existing and missing packages."""
        mixed_packages = ['sys', 'nonexistent_package_xyz_789']
        
        all_present, missing = check_dependencies(mixed_packages)
        
        assert all_present is False
        assert 'nonexistent_package_xyz_789' in missing
        assert 'sys' not in missing


class TestInstallMissingPackages:
    """Test install_missing_packages function."""

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_install_missing_packages_with_uv(self, mock_run, mock_which):
        """Test installing packages when uv is available."""
        mock_which.return_value = '/usr/bin/uv'
        mock_run.return_value = MagicMock(returncode=0)
        
        # Mock __import__ to simulate successful installation
        with patch('builtins.__import__', return_value=MagicMock()):
            result = install_missing_packages(['test_package'])
        
        # Should attempt installation
        assert mock_run.called
        assert 'uv' in str(mock_run.call_args)

    @patch('shutil.which')
    def test_install_missing_packages_without_uv(self, mock_which):
        """Test installing packages when uv is not available."""
        mock_which.return_value = None
        
        result = install_missing_packages(['test_package'])
        
        assert result is False

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_install_missing_packages_failure(self, mock_run, mock_which):
        """Test handling installation failure."""
        mock_which.return_value = '/usr/bin/uv'
        mock_run.return_value = MagicMock(returncode=1)
        
        result = install_missing_packages(['test_package'])
        
        assert result is False


class TestCheckBuildTools:
    """Test check_build_tools function."""

    @patch('shutil.which')
    def test_check_build_tools_default(self, mock_which):
        """Test checking default build tools."""
        # Mock some tools as available
        def which_side_effect(tool):
            return f'/usr/bin/{tool}' if tool in ['pandoc'] else None
        
        mock_which.side_effect = which_side_effect
        
        result = check_build_tools()
        
        # Should return False if xelatex not found
        assert isinstance(result, bool)

    @patch('shutil.which')
    def test_check_build_tools_all_available(self, mock_which):
        """Test when all tools are available."""
        def which_side_effect(tool):
            return f'/usr/bin/{tool}'
        
        mock_which.side_effect = which_side_effect
        
        result = check_build_tools()
        
        assert result is True

    @patch('shutil.which')
    def test_check_build_tools_custom_list(self, mock_which):
        """Test checking custom build tools."""
        custom_tools = {
            'custom_tool': 'Custom tool description'
        }
        
        mock_which.return_value = '/usr/bin/custom_tool'
        
        result = check_build_tools(custom_tools)
        
        assert result is True
        mock_which.assert_called_with('custom_tool')


class TestSetupDirectories:
    """Test setup_directories function."""

    def test_setup_directories_default(self, tmp_path):
        """Test setting up default directories for multi-project."""
        # Create a fake project directory
        project_root = tmp_path / "projects" / "testproject"
        project_root.mkdir(parents=True)

        result = setup_directories(tmp_path, "testproject")

        assert result is True

        # Check default directories were created
        expected_dirs = [
            'output/testproject',
            'output/testproject/figures',
            'output/testproject/data',
            'output/testproject/tex',
            'output/testproject/pdf',
            'output/testproject/logs',
            'output/testproject/reports',
            'output/testproject/simulations',
            'output/testproject/slides',
            'output/testproject/web',
            'output/testproject/llm',
            'projects/testproject/output',
            'projects/testproject/output/figures',
            'projects/testproject/output/data',
            'projects/testproject/output/pdf',
            'projects/testproject/output/tex',
            'projects/testproject/output/logs',
            'projects/testproject/output/reports',
            'projects/testproject/output/simulations',
            'projects/testproject/output/slides',
            'projects/testproject/output/web',
            'projects/testproject/output/llm',
        ]

        for directory in expected_dirs:
            assert (tmp_path / directory).exists()
            assert (tmp_path / directory).is_dir()

    def test_setup_directories_custom(self, tmp_path):
        """Test setting up custom directories for multi-project."""
        # Create a fake project directory
        project_root = tmp_path / "projects" / "testproject"
        project_root.mkdir(parents=True)

        custom_dirs = ['custom1', 'custom2/subdir', 'custom3/nested/deep']

        result = setup_directories(tmp_path, "testproject", custom_dirs)

        assert result is True

        for directory in custom_dirs:
            assert (tmp_path / directory).exists()
            assert (tmp_path / directory).is_dir()

    def test_setup_directories_existing(self, tmp_path):
        """Test setting up directories that already exist."""
        # Create some directories first
        (tmp_path / "output").mkdir()
        (tmp_path / "output" / "figures").mkdir()
        
        result = setup_directories(tmp_path)
        
        # Should still succeed (exist_ok=True)
        assert result is True
        assert (tmp_path / "output").exists()
        assert (tmp_path / "output" / "figures").exists()

    def test_setup_directories_empty_list(self, tmp_path):
        """Test with empty directory list."""
        result = setup_directories(tmp_path, "", directories=[])
        
        assert result is True


class TestVerifySourceStructure:
    """Test verify_source_structure function."""

    def test_verify_source_structure(self, tmp_path):
        """Test verifying source structure for multi-project."""
        # Create required directories for multi-project
        (tmp_path / "infrastructure").mkdir()
        (tmp_path / "projects").mkdir()
        (tmp_path / "projects" / "project").mkdir()
        (tmp_path / "projects" / "project" / "src").mkdir()
        (tmp_path / "projects" / "project" / "tests").mkdir()

        # Create __init__.py files to satisfy Python package requirements
        (tmp_path / "projects" / "project" / "src" / "__init__.py").write_text("")
        (tmp_path / "projects" / "project" / "tests" / "__init__.py").write_text("")

        result = verify_source_structure(tmp_path, "project")

        assert result is True

    def test_verify_source_structure_missing_required(self, tmp_path):
        """Test verifying when required directories are missing for multi-project."""
        # Only create one required directory
        (tmp_path / "infrastructure").mkdir()
        # Don't create projects/project structure

        result = verify_source_structure(tmp_path, "project")

        assert result is False

    def test_verify_source_structure_with_optional(self, tmp_path):
        """Test verifying with optional directories present for multi-project."""
        (tmp_path / "infrastructure").mkdir()
        (tmp_path / "projects").mkdir()
        (tmp_path / "projects" / "project").mkdir()
        (tmp_path / "projects" / "project" / "src").mkdir()
        (tmp_path / "projects" / "project" / "tests").mkdir()
        (tmp_path / "scripts").mkdir()
        (tmp_path / "tests").mkdir()

        # Create required __init__.py files
        (tmp_path / "projects" / "project" / "src" / "__init__.py").write_text("")
        (tmp_path / "projects" / "project" / "tests" / "__init__.py").write_text("")

        result = verify_source_structure(tmp_path, "project")

        assert result is True

    def test_verify_source_structure_missing_all(self, tmp_path):
        """Test verifying when all directories are missing."""
        result = verify_source_structure(tmp_path, "project")
        
        assert result is False


class TestSetEnvironmentVariables:
    """Test set_environment_variables function."""

    def test_set_environment_variables(self, tmp_path):
        """Test setting environment variables."""
        # Save original values
        original_mpl = os.environ.get('MPLBACKEND')
        original_encoding = os.environ.get('PYTHONIOENCODING')
        original_root = os.environ.get('PROJECT_ROOT')
        
        try:
            result = set_environment_variables(tmp_path)
            
            assert result is True
            assert os.environ.get('MPLBACKEND') == 'Agg'
            assert os.environ.get('PYTHONIOENCODING') == 'utf-8'
            assert os.environ.get('PROJECT_ROOT') == str(tmp_path)
        finally:
            # Restore original values
            if original_mpl:
                os.environ['MPLBACKEND'] = original_mpl
            elif 'MPLBACKEND' in os.environ:
                del os.environ['MPLBACKEND']
            
            if original_encoding:
                os.environ['PYTHONIOENCODING'] = original_encoding
            elif 'PYTHONIOENCODING' in os.environ:
                del os.environ['PYTHONIOENCODING']
            
            if original_root:
                os.environ['PROJECT_ROOT'] = original_root
            elif 'PROJECT_ROOT' in os.environ:
                del os.environ['PROJECT_ROOT']

    def test_set_environment_variables_overwrites(self, tmp_path):
        """Test that setting environment variables overwrites existing values."""
        # Set initial values
        os.environ['MPLBACKEND'] = 'TkAgg'
        os.environ['PROJECT_ROOT'] = '/old/path'
        
        try:
            result = set_environment_variables(tmp_path)
            
            assert result is True
            assert os.environ.get('MPLBACKEND') == 'Agg'
            assert os.environ.get('PROJECT_ROOT') == str(tmp_path)
        finally:
            # Clean up
            if 'MPLBACKEND' in os.environ:
                del os.environ['MPLBACKEND']
            if 'PROJECT_ROOT' in os.environ:
                del os.environ['PROJECT_ROOT']


class TestUvIntegration:
    """Test uv package manager integration and fallback behavior."""

    def test_check_uv_available_success(self):
        """Test check_uv_available when uv is installed and working."""
        result = check_uv_available()

        # Result depends on actual system state - just verify it's boolean
        assert isinstance(result, bool)

        # If uv is available, verify it actually works
        if result:
            cmd_result = subprocess.run(['uv', '--version'], capture_output=True)
            assert cmd_result.returncode == 0

    def test_check_uv_available_not_found(self):
        """Test check_uv_available when uv is not installed."""
        # Create isolated environment without uv in PATH
        # This simulates uv not being installed
        isolated_env = os.environ.copy()
        isolated_env['PATH'] = '/usr/bin:/bin'  # Minimal PATH

        # Calculate repo root from test file location
        repo_root = Path(__file__).parent.parent.parent.parent

        result = subprocess.run(
            [sys.executable, '-c', f'''
import os
import subprocess
import sys

# Add infrastructure to path
sys.path.insert(0, "{repo_root}")

from infrastructure.core.environment import check_uv_available

# Set minimal PATH that won't contain uv
os.environ['PATH'] = '/usr/bin:/bin'

# This will trigger FileNotFoundError
result = check_uv_available()
print("True" if result else "False")
            '''],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert result.stdout.strip() == "False"

    def test_check_uv_available_error(self):
        """Test check_uv_available handles errors gracefully."""
        # Test that the function always returns a boolean, even in edge cases
        result = check_uv_available()
        assert isinstance(result, bool)

        # The function should handle any subprocess errors gracefully
        # and return False rather than raising exceptions
        # (This is tested by the subprocess_error test)

    def test_check_uv_available_subprocess_error(self):
        """Test check_uv_available when subprocess raises an error."""
        # Create isolated environment without uv in PATH
        # This will trigger FileNotFoundError which is caught and returns False
        isolated_env = os.environ.copy()
        isolated_env['PATH'] = '/usr/bin:/bin'  # Minimal PATH without uv

        # Run the check in a subprocess with modified environment
        # This creates a real scenario where 'uv' command is not found
        # Calculate repo root from test file location
        repo_root = Path(__file__).parent.parent.parent.parent

        result = subprocess.run(
            [sys.executable, '-c', f'''
import os
import subprocess
import sys

# Add infrastructure to path
sys.path.insert(0, "{repo_root}")

from infrastructure.core.environment import check_uv_available

# Set minimal PATH that won't contain uv
os.environ['PATH'] = '/usr/bin:/bin'

# This will trigger FileNotFoundError since uv is not in PATH
result = check_uv_available()
print("True" if result else "False")
            '''],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert result.stdout.strip() == "False"

    @patch('infrastructure.core.environment.check_uv_available')
    def test_get_python_command_with_uv(self, mock_check_uv):
        """Test get_python_command returns uv command when uv is available."""
        mock_check_uv.return_value = True
        
        cmd = get_python_command()
        
        assert cmd == ['uv', 'run', 'python']
        mock_check_uv.assert_called_once()

    @patch('infrastructure.core.environment.check_uv_available')
    def test_get_python_command_without_uv(self, mock_check_uv):
        """Test get_python_command returns python3 when uv is not available."""
        mock_check_uv.return_value = False
        
        cmd = get_python_command()
        
        # Should return sys.executable (current Python interpreter)
        assert cmd == [sys.executable]
        mock_check_uv.assert_called_once()

    @patch('infrastructure.core.environment.check_uv_available')
    def test_get_python_command_consistency(self, mock_check_uv):
        """Test get_python_command returns consistent results."""
        mock_check_uv.return_value = True
        
        cmd1 = get_python_command()
        cmd2 = get_python_command()
        
        assert cmd1 == cmd2
        assert cmd1 == ['uv', 'run', 'python']

    @patch('infrastructure.core.environment.check_uv_available')
    def test_get_python_command_list_format(self, mock_check_uv):
        """Test get_python_command returns list for subprocess usage."""
        for uv_available in [True, False]:
            mock_check_uv.return_value = uv_available
            
            cmd = get_python_command()
            
            # Must be a list for subprocess.run()
            assert isinstance(cmd, list)
            assert len(cmd) > 0
            assert all(isinstance(part, str) for part in cmd)

