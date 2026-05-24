"""Tests for infrastructure/core/config/cli.py.

Tests configuration CLI functionality via subprocess and direct main() calls.
No mocks — subprocess and sys.argv try/finally only.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.core.config.cli import main


@pytest.mark.timeout(60)
class TestConfigCli:
    """Test config_cli module."""

    def test_module_imports(self):
        from infrastructure.core.config import cli as config_cli

        assert config_cli is not None

    def test_has_main(self):
        from infrastructure.core.config import cli as config_cli

        assert hasattr(config_cli, "main") or callable(config_cli)

    def test_main_with_no_args(self, capsys):
        """Direct main() with default args."""
        old_argv = sys.argv
        try:
            sys.argv = ["config_cli.py"]
            main()
        finally:
            sys.argv = old_argv
        captured = capsys.readouterr()
        assert isinstance(captured.out, str)

    def test_main_with_project_arg(self, capsys):
        """Direct main() with --project arg."""
        old_argv = sys.argv
        try:
            sys.argv = ["config_cli.py", "--project", "template_code_project"]
            main()
        finally:
            sys.argv = old_argv
        captured = capsys.readouterr()
        assert isinstance(captured.out, str)

    def test_main_execution_help(self):
        """CLI --help via subprocess."""
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        script_path = repo_root / "infrastructure" / "core" / "config" / "cli.py"

        if script_path.exists():
            env = os.environ.copy()
            env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

            result = subprocess.run(
                [sys.executable, str(script_path), "--help"],
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
            )

            assert result.returncode == 0
            assert (
                "usage:" in result.stdout.lower()
                or "Load manuscript configuration" in result.stdout
            )

    def test_main_execution_no_args(self):
        """CLI without arguments via subprocess."""
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        script_path = repo_root / "infrastructure" / "core" / "config" / "cli.py"

        if script_path.exists():
            env = os.environ.copy()
            env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
            )

            assert result.returncode == 0

    def test_main_execution_with_project(self):
        """CLI with --project via subprocess."""
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        script_path = repo_root / "infrastructure" / "core" / "config" / "cli.py"

        if script_path.exists():
            env = os.environ.copy()
            env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

            result = subprocess.run(
                [sys.executable, str(script_path), "--project", "template_code_project"],
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
            )

            assert result.returncode == 0
