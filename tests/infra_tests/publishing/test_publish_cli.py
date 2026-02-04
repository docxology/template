"""Comprehensive tests for infrastructure/publishing/publish_cli.py.

Tests the wrapper CLI script for publishing releases.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.publishing import publish_cli


class TestPublishCliMain:
    """Test suite for publish_cli main function."""

    def test_main_basic_publish_argument_parsing(self, tmp_path):
        """Test basic argument parsing without actual publishing."""
        # Create real PDF file
        pdf_dir = tmp_path / "output" / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "test.pdf").write_bytes(b"%PDF-1.4\n%EOF")

        # Test that the CLI script can be executed with proper arguments
        # (We can't make real GitHub API calls, so we test argument validation)
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        script_path = repo_root / "infrastructure" / "publishing" / "publish_cli.py"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

        # Test that script runs and shows help (validates argument parsing)
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env=env,
        )

        # Should show help without error
        assert result.returncode == 0
        assert "--token" in result.stdout
        assert "--repo" in result.stdout

    def test_main_missing_required_args(self):
        """Test with missing required arguments."""
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        script_path = repo_root / "infrastructure" / "publishing" / "publish_cli.py"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root) + os.pathsep + env.get("PYTHONPATH", "")

        # Run without required arguments - should fail
        result = subprocess.run(
            [sys.executable, str(script_path)], capture_output=True, text=True, env=env
        )

        # Should exit with error due to missing required arguments
        assert result.returncode != 0
        assert (
            "required" in result.stderr.lower() or "required" in result.stdout.lower()
        )


class TestPublishCliModule:
    """Test module structure."""

    def test_has_main_function(self):
        """Test that module has main function."""
        assert hasattr(publish_cli, "main")
        assert callable(publish_cli.main)

    def test_imports_publishing(self):
        """Test that publishing module is imported."""
        assert hasattr(publish_cli, "publishing")
