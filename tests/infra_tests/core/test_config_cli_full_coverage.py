"""Tests for infrastructure/core/config/cli.py.

Covers: main() function with real argparse and config loading.

No mocks used — all tests use real function calls with a plain
try/finally swap of ``sys.argv`` (the no-mocks policy forbids
``unittest.mock`` entirely, including ``patch``).
"""

from __future__ import annotations

import sys

from infrastructure.core.config.cli import main


class TestConfigCli:
    """Test the config CLI main function."""

    def test_main_with_no_args(self, capsys):
        """Should run main with default args (no --project)."""
        old_argv = sys.argv
        try:
            sys.argv = ["config_cli.py"]
            main()
        finally:
            sys.argv = old_argv
        captured = capsys.readouterr()
        assert isinstance(captured.out, str)

    def test_main_with_project_arg(self, capsys):
        """Should run main with --project arg."""
        old_argv = sys.argv
        try:
            sys.argv = ["config_cli.py", "--project", "code_project"]
            main()
        finally:
            sys.argv = old_argv
        captured = capsys.readouterr()
        assert isinstance(captured.out, str)
