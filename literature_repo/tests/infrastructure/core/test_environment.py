"""Tests for infrastructure.core.environment module.

Comprehensive tests for environment setup and validation utilities.
"""

import os
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
        """Test setting up default directories."""
        result = setup_directories(tmp_path)
        
        assert result is True
        
        # Check default directories were created
        default_dirs = [
            'output',
            'output/figures',
            'output/data',
            'output/tex',
            'output/pdf',
            'output/logs',
            'project/output',
            'project/output/logs',
        ]
        
        for directory in default_dirs:
            assert (tmp_path / directory).exists()
            assert (tmp_path / directory).is_dir()

    def test_setup_directories_custom(self, tmp_path):
        """Test setting up custom directories."""
        custom_dirs = ['custom1', 'custom2/subdir', 'custom3/nested/deep']
        
        result = setup_directories(tmp_path, custom_dirs)
        
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
        result = setup_directories(tmp_path, [])
        
        assert result is True


class TestVerifySourceStructure:
    """Test verify_source_structure function."""

    def test_verify_source_structure_complete(self, tmp_path):
        """Test verifying complete source structure."""
        # Create required directories
        (tmp_path / "infrastructure").mkdir()
        (tmp_path / "project").mkdir()
        
        result = verify_source_structure(tmp_path)
        
        assert result is True

    def test_verify_source_structure_missing_required(self, tmp_path):
        """Test verifying when required directories are missing."""
        # Only create one required directory
        (tmp_path / "infrastructure").mkdir()
        # Don't create project/
        
        result = verify_source_structure(tmp_path)
        
        assert result is False

    def test_verify_source_structure_with_optional(self, tmp_path):
        """Test verifying with optional directories present."""
        (tmp_path / "infrastructure").mkdir()
        (tmp_path / "project").mkdir()
        (tmp_path / "scripts").mkdir()
        (tmp_path / "tests").mkdir()
        
        result = verify_source_structure(tmp_path)
        
        assert result is True

    def test_verify_source_structure_missing_all(self, tmp_path):
        """Test verifying when all directories are missing."""
        result = verify_source_structure(tmp_path)
        
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

