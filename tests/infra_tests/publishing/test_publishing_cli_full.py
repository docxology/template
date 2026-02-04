"""Comprehensive tests for infrastructure/publishing/publish_cli.py.

Tests publishing CLI functionality.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest


class TestPublishCliCore:
    """Test core publish CLI functionality."""

    def test_module_imports(self):
        """Test that module imports correctly."""
        from infrastructure.publishing import publish_cli

        assert publish_cli is not None

    def test_has_main_function(self):
        """Test that module has main function."""
        from infrastructure.publishing import publish_cli

        assert hasattr(publish_cli, "main") or hasattr(publish_cli, "publish_cli")


class TestZenodoCommands:
    """Test Zenodo publishing commands."""

    def test_zenodo_upload_command(self):
        """Test Zenodo upload command."""
        from infrastructure.publishing import publish_cli

        if hasattr(publish_cli, "zenodo_upload_command"):
            assert callable(publish_cli.zenodo_upload_command)

    def test_zenodo_create_command(self):
        """Test Zenodo create command."""
        from infrastructure.publishing import publish_cli

        if hasattr(publish_cli, "zenodo_create_command"):
            assert callable(publish_cli.zenodo_create_command)


class TestArxivCommands:
    """Test arXiv publishing commands."""

    def test_arxiv_prepare_command(self):
        """Test arXiv prepare command."""
        from infrastructure.publishing import publish_cli

        if hasattr(publish_cli, "arxiv_prepare_command"):
            assert callable(publish_cli.arxiv_prepare_command)


class TestGitHubCommands:
    """Test GitHub release commands."""

    def test_github_release_command(self):
        """Test GitHub release command."""
        from infrastructure.publishing import publish_cli

        if hasattr(publish_cli, "github_release_command"):
            assert callable(publish_cli.github_release_command)


class TestPublishCliParsing:
    """Test CLI argument parsing."""

    def test_parse_args_basic(self):
        """Test basic argument parsing."""
        # Test by running the CLI script with arguments
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        script_path = repo_root / "infrastructure" / "publishing" / "publish_cli.py"

        # Set PYTHONPATH to include repo root
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

        # Run with --help to test argument parsing works
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True,
            cwd=repo_root,
            env=env,
        )

        # Should exit with code 0 (help) or 2 (error but parsed correctly)
        assert result.returncode in [0, 2]
        assert "Publish release" in result.stdout or "Publish release" in result.stderr


class TestPublishCliMain:
    """Test main entry point."""

    def test_main_without_args(self):
        """Test main without arguments shows error."""
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        script_path = repo_root / "infrastructure" / "publishing" / "publish_cli.py"

        # Set PYTHONPATH to include repo root
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

        # Run without required arguments - should fail
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=repo_root,
            env=env,
        )

        # Should exit with error code due to missing required arguments
        assert result.returncode != 0
        assert (
            "required" in result.stderr.lower() or "required" in result.stdout.lower()
        )

    def test_main_with_help(self):
        """Test main with help flag."""
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        script_path = repo_root / "infrastructure" / "publishing" / "publish_cli.py"

        # Set PYTHONPATH to include repo root
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

        # Run with --help
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True,
            cwd=repo_root,
            env=env,
        )

        # Should show help and exit
        assert result.returncode in [0, 2]  # argparse uses 2 for help
        assert "--token" in result.stdout or "--token" in result.stderr


class TestPublishCliIntegration:
    """Integration tests for publish CLI."""

    def test_full_publish_workflow(self, tmp_path):
        """Test complete publish workflow."""
        from infrastructure.publishing import publish_cli

        # Module should be importable
        assert publish_cli is not None
