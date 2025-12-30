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
    
    def test_main_execution(self):
        """Test main function execution."""
        # Test real CLI execution with subprocess
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        script_path = repo_root / "infrastructure" / "core" / "config_cli.py"

        if script_path.exists():
            env = os.environ.copy()
            env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

            # Test --help option (should succeed)
            result = subprocess.run([
                sys.executable, str(script_path), "--help"
            ], capture_output=True, text=True, env=env)

            # Should execute without error (help returns 0 or 2)
            assert result.returncode in [0, 2]



















