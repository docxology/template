"""Tests for infrastructure/core/cli.py.

Covers: main() function dispatch and error handling.

No mocks used — tests use real argparse with sys.argv patching.
"""

from __future__ import annotations

import sys


from infrastructure.core.cli import main, create_parser


class TestCreateParser:
    """Test the CLI argument parser creation."""

    def test_parser_created(self):
        """Parser should be created without errors."""
        parser = create_parser()
        assert parser is not None

    def test_parser_has_subcommands(self):
        """Parser should accept known subcommands."""
        parser = create_parser()
        # Test that parsing a known command doesn't raise
        args = parser.parse_args(["discover", "--repo-root", "/tmp"])
        assert args.command == "discover"


class TestMainFunction:
    """Test the main() CLI entry point."""

    def test_no_command_returns_1(self):
        """Calling main with no command should return 1."""
        old_argv = sys.argv
        try:
            sys.argv = ["infra-cli"]
            result = main()
            assert result == 1
        finally:
            sys.argv = old_argv

    def test_discover_command_runs(self):
        """Calling main with discover command should work."""
        old_argv = sys.argv
        try:
            sys.argv = ["infra-cli", "discover", "--repo-root", "/tmp/nonexistent"]
            result = main()
            assert result == 0  # Discover with no projects returns 0
        finally:
            sys.argv = old_argv
