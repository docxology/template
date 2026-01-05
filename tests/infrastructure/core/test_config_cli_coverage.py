"""Tests for infrastructure/core/config_cli.py.

Tests configuration CLI functionality.
"""

from pathlib import Path
import pytest
import subprocess
import sys
import os


class TestConfigCli:
    """Test config_cli module."""
    
    def test_module_imports(self):
        """Test module imports correctly."""
        from infrastructure.core import config_cli
        assert config_cli is not None
    
    def test_has_main(self):
        """Test module has main function."""
        from infrastructure.core import config_cli
        assert hasattr(config_cli, 'main') or callable(config_cli)
    
    def test_main_execution_help(self):
        """Test main function execution with --help option."""
        # Test real CLI execution with subprocess
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        script_path = repo_root / "infrastructure" / "core" / "config_cli.py"

        if script_path.exists():
            env = os.environ.copy()
            env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

            # Test --help option (should succeed with argparse)
            result = subprocess.run([
                sys.executable, str(script_path), "--help"
            ], capture_output=True, text=True, env=env)

            # Argparse --help returns 0
            assert result.returncode == 0
            assert "usage:" in result.stdout.lower() or "Load manuscript configuration" in result.stdout
    
    def test_main_execution_no_args(self):
        """Test main function execution without arguments."""
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        script_path = repo_root / "infrastructure" / "core" / "config_cli.py"

        if script_path.exists():
            env = os.environ.copy()
            env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

            # Test execution without arguments (should succeed even if no config found)
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=True, text=True, env=env)

            # Should execute without error (may output nothing if no config, but exit code should be 0)
            assert result.returncode == 0
    
    def test_main_execution_with_project(self):
        """Test main function execution with --project argument."""
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        script_path = repo_root / "infrastructure" / "core" / "config_cli.py"

        if script_path.exists():
            env = os.environ.copy()
            env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

            # Test execution with --project argument
            result = subprocess.run([
                sys.executable, str(script_path), "--project", "code_project"
            ], capture_output=True, text=True, env=env)

            # Should execute without error
            assert result.returncode == 0



















