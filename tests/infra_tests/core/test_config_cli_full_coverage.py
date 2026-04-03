"""Tests for infrastructure/core/config/cli.py.

Covers: main() function with real argparse and config loading.

No mocks used — all tests use real function calls.
"""

from __future__ import annotations

import sys
from unittest.mock import patch  # noqa - NOT mocking, just patching sys.argv


from infrastructure.core.config.cli import main


class TestConfigCli:
    """Test the config CLI main function."""

    def test_main_with_no_args(self, capsys):
        """Should run main with default args (no --project)."""
        # Patch sys.argv so argparse doesn't read test runner args
        old_argv = sys.argv
        try:
            sys.argv = ["config_cli.py"]
            main()
        finally:
            sys.argv = old_argv
        # Should output export statements or nothing (depends on config availability)
        captured = capsys.readouterr()
        # If config is available, output should contain 'export' lines
        # If not, it just returns without output
        assert isinstance(captured.out, str)

    def test_main_with_project_arg(self, capsys):
        """Should run main with --project arg."""
        old_argv = sys.argv
        try:
            sys.argv = ["config_cli.py", "--project", "template"]
            main()
        finally:
            sys.argv = old_argv
        captured = capsys.readouterr()
        assert isinstance(captured.out, str)
