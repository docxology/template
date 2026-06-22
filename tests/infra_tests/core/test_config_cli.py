"""Tests for infrastructure/core/config/cli.py.

Tests configuration CLI functionality via subprocess and direct main() calls.
No mocks — subprocess and sys.argv try/finally only.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from contextlib import redirect_stdout
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
            assert "usage:" in result.stdout.lower() or "Load manuscript configuration" in result.stdout

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

    def test_main_schema_flag_emits_json(self):
        """``main(["--schema"])`` returns 0 and prints a valid JSON schema."""
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            rc = main(["--schema"])
        assert rc == 0
        payload = json.loads(buffer.getvalue())
        assert "prog" in payload or "options" in payload
        flags = {flag for opt in payload.get("options", []) for flag in opt.get("flags", [])}
        # Additive guarantee: pre-existing flags are still present in the schema.
        assert "--project" in flags
        assert "--schema-json" in flags

    def test_schema_flag_via_module(self):
        """``python -m infrastructure.core.config --schema`` exits 0 with JSON."""
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.core.config", "--schema"],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(repo_root),
            timeout=30,
        )
        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert "options" in payload
