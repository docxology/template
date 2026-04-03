"""Tests for infrastructure/core/cli_handlers.py.

Covers: handle_inventory_command, handle_discover_command using real
project structures and real argparse Namespace objects.

No mocks used — all tests use real data and real function calls.
"""

from __future__ import annotations

import argparse


from infrastructure.core.cli_handlers import (
    handle_inventory_command,
    handle_discover_command,
)


class TestHandleInventoryCommand:
    """Test handle_inventory_command with real file structures."""

    def _make_args(self, output_dir, fmt="text", categories=None) -> argparse.Namespace:
        """Create real argparse Namespace."""
        return argparse.Namespace(
            output_dir=output_dir,
            format=fmt,
            categories=categories or [],
        )

    def test_empty_output_dir(self, tmp_path):
        """Should return 0 when output dir has no files."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        args = self._make_args(output_dir)
        assert handle_inventory_command(args) == 0

    def test_nonexistent_output_dir(self, tmp_path):
        """Should handle nonexistent output dir."""
        output_dir = tmp_path / "nonexistent"
        args = self._make_args(output_dir)
        # May return 0 (empty) or 1 (error) depending on implementation
        result = handle_inventory_command(args)
        assert result in (0, 1)


class TestHandleDiscoverCommand:
    """Test handle_discover_command with real project structures."""

    def _make_args(self, repo_root, fmt="text") -> argparse.Namespace:
        """Create real argparse Namespace."""
        return argparse.Namespace(
            repo_root=repo_root,
            format=fmt,
        )

    def test_discover_text_format(self, tmp_path):
        """Should discover projects in text format."""
        # Create a valid project structure
        project = tmp_path / "projects" / "testproject"
        (project / "src").mkdir(parents=True)
        (project / "tests").mkdir(parents=True)
        (project / "src" / "__init__.py").write_text("")
        (project / "tests" / "__init__.py").write_text("")

        args = self._make_args(tmp_path, fmt="text")
        result = handle_discover_command(args)
        assert result == 0

    def test_discover_json_format(self, tmp_path):
        """Should discover projects in JSON format."""
        project = tmp_path / "projects" / "testproject"
        (project / "src").mkdir(parents=True)
        (project / "tests").mkdir(parents=True)
        (project / "src" / "__init__.py").write_text("")
        (project / "tests" / "__init__.py").write_text("")

        args = self._make_args(tmp_path, fmt="json")
        result = handle_discover_command(args)
        assert result == 0

    def test_discover_no_projects(self, tmp_path):
        """Should handle repo with no projects."""
        (tmp_path / "projects").mkdir(parents=True)
        args = self._make_args(tmp_path, fmt="text")
        result = handle_discover_command(args)
        assert result == 0

    def test_discover_empty_repo(self, tmp_path):
        """Should handle empty repo (no projects dir)."""
        args = self._make_args(tmp_path, fmt="text")
        result = handle_discover_command(args)
        assert result == 0
