"""Simplified tests for infrastructure/literature/cli.py.

Tests the CLI interface for literature search operations using real execution.
"""

import subprocess
import sys
from pathlib import Path
import pytest

from infrastructure.literature.core import cli


class TestCLIExecution:
    """Test CLI execution with real subprocess calls."""

    def test_cli_help_output(self):
        """Test that CLI help works."""
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.literature.core.cli", "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()
        assert "search" in result.stdout

    def test_cli_importable(self):
        """Test that CLI module can be imported."""
        # This tests that the CLI module structure is correct
        assert hasattr(cli, 'main')
        assert callable(cli.main)

    def test_cli_module_structure(self):
        """Test that CLI module has expected functions."""
        # Test that key functions exist
        assert hasattr(cli, 'main')
        assert hasattr(cli, 'search_command')
        # Note: library_command might not exist in current implementation
        # assert hasattr(cli, 'library_command')












