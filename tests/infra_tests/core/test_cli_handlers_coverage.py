"""Tests for infrastructure.core.cli_handlers — handle_discover and handle_inventory."""

import argparse
import json
from pathlib import Path

from infrastructure.core.cli_handlers import (
    handle_discover_command,
    handle_inventory_command,
)


def _make_project(base: Path, name: str, *, valid: bool = True):
    """Create a minimal project structure under base/projects/name."""
    proj = base / "projects" / name
    if valid:
        (proj / "src").mkdir(parents=True)
        (proj / "src" / "__init__.py").write_text("")
        (proj / "tests").mkdir(parents=True, exist_ok=True)
        (proj / "tests" / "__init__.py").write_text("")
    (proj / "manuscript").mkdir(parents=True, exist_ok=True)
    (proj / "manuscript" / "config.yaml").write_text(f"paper:\n  title: {name}\n")
    return proj


class TestHandleDiscoverCommand:
    def test_text_format_with_projects(self, tmp_path, capsys):
        _make_project(tmp_path, "alpha")
        _make_project(tmp_path, "beta")

        args = argparse.Namespace(
            repo_root=tmp_path,
            format="text",
        )
        exit_code = handle_discover_command(args)
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "alpha" in out
        assert "beta" in out

    def test_json_format(self, tmp_path, capsys):
        _make_project(tmp_path, "gamma")

        args = argparse.Namespace(
            repo_root=tmp_path,
            format="json",
        )
        exit_code = handle_discover_command(args)
        assert exit_code == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert isinstance(data, list)
        assert any(p["name"] == "gamma" for p in data)

    def test_no_projects_text(self, tmp_path, capsys):
        # Empty projects dir
        (tmp_path / "projects").mkdir()

        args = argparse.Namespace(
            repo_root=tmp_path,
            format="text",
        )
        exit_code = handle_discover_command(args)
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "No valid projects" in out or "Found 0" in out

    def test_json_format_empty(self, tmp_path, capsys):
        (tmp_path / "projects").mkdir()

        args = argparse.Namespace(
            repo_root=tmp_path,
            format="json",
        )
        exit_code = handle_discover_command(args)
        assert exit_code == 0
        data = json.loads(capsys.readouterr().out)
        assert data == []


class TestHandleInventoryCommand:
    def test_empty_output_dir(self, tmp_path, capsys):
        out_dir = tmp_path / "output"
        out_dir.mkdir()

        args = argparse.Namespace(
            output_dir=out_dir,
            categories=None,
            format="text",
        )
        exit_code = handle_inventory_command(args)
        assert exit_code == 0

    def test_with_files(self, tmp_path, capsys):
        out_dir = tmp_path / "output"
        pdf_dir = out_dir / "pdf"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "paper.pdf").write_bytes(b"%PDF content here")

        args = argparse.Namespace(
            output_dir=out_dir,
            categories=None,
            format="text",
        )
        exit_code = handle_inventory_command(args)
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "paper.pdf" in out

    def test_json_format(self, tmp_path, capsys):
        out_dir = tmp_path / "output"
        data_dir = out_dir / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "results.json").write_text('{"key": "value"}')

        args = argparse.Namespace(
            output_dir=out_dir,
            categories=None,
            format="json",
        )
        exit_code = handle_inventory_command(args)
        assert exit_code == 0

    def test_nonexistent_dir(self, tmp_path, capsys):
        args = argparse.Namespace(
            output_dir=tmp_path / "nonexistent",
            categories=None,
            format="text",
        )
        exit_code = handle_inventory_command(args)
        assert exit_code == 0  # Returns 0 with "No files found"
