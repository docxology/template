"""Tests for core CLI interface."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from infrastructure.core.cli import create_parser, main
from infrastructure.core.cli_handlers import (
    handle_discover_command,
    handle_inventory_command,
)


def _make_project(base: Path, name: str, *, valid: bool = True) -> Path:
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


class TestCreateParser:
    """Test argument parser creation."""

    def test_create_parser(self):
        """Test parser creation."""
        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)

        # Test that all expected subcommands exist
        subcommands = [
            action.dest
            for action in parser._subparsers._actions
            if hasattr(action, "dest") and action.dest == "command"
        ]
        assert len(subcommands) == 1  # Should have command subparser

    def test_pipeline_subcommand(self):
        """Test pipeline subcommand arguments."""
        parser = create_parser()

        # Parse pipeline command
        args = parser.parse_args(["pipeline", "--mode", "live", "--project", "test"])

        assert args.command == "pipeline"
        assert args.mode == "live"
        assert args.project == "test"
        assert args.skip_infra is False
        assert args.resume is False

    def test_multi_project_subcommand(self):
        """Test multi-project subcommand arguments."""
        parser = create_parser()

        args = parser.parse_args(["multi-project", "--mode", "live"])

        assert args.command == "multi-project"
        assert args.mode == "live"
        assert args.projects is None

    def test_inventory_subcommand(self):
        """Test inventory subcommand arguments."""
        parser = create_parser()

        args = parser.parse_args(["inventory", "/tmp/output"])

        assert args.command == "inventory"
        assert args.output_dir == Path("/tmp/output")
        assert args.format == "text"
        assert args.categories is None


# Full-DAG subprocess runs take minutes even with instant stub stages;
# the default 60s class pytest-timeout fires before the inner subprocess
# timeout can. See DEEP_PASS_2026-08-21_ox-alpha-session7.md.
@pytest.mark.timeout(900)
class TestCLISubprocess:
    """Test CLI through real subprocess execution."""

    @pytest.mark.parametrize(
        "mode, expected_steps", [("core", ["infra", "analysis"]), ("live", ["infra", "analysis", "live"])]
    )
    def test_cli_pipeline_real_mode_selection(self, tmp_path: Path, mode: str, expected_steps: list[str]):
        from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline

        scaffold_pipeline(tmp_path, ("templates/demo",))
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "infrastructure.core.cli",
                "pipeline",
                "--mode",
                mode,
                "--project",
                "demo",
                "--repo-root",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert (tmp_path / "process_order.log").read_text().splitlines() == [
            f"templates/demo:{step}" for step in expected_steps
        ]

    @pytest.mark.parametrize("infra_exit, expected_code", [(0, 0), (2, 1)])
    def test_cli_multi_shared_verification_and_project_selection(
        self, tmp_path: Path, infra_exit: int, expected_code: int
    ):
        from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline

        scaffold_pipeline(tmp_path, ("templates/alpha", "templates/beta"), infra_exit=infra_exit)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "infrastructure.core.cli",
                "multi-project",
                "--projects",
                "templates/beta",
                "--repo-root",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == expected_code, result.stderr
        rows = (tmp_path / "process_order.log").read_text().splitlines()
        assert rows == (
            ["templates/beta:infra", "templates/beta:analysis"] if infra_exit == 0 else ["templates/beta:infra"]
        )

    def test_cli_inventory_command(self):
        """Test inventory command execution via CLI."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "output"
            output_dir.mkdir()

            # Inventory scans recognized output categories rather than arbitrary
            # root files, so place the fixture in the PDF category.
            pdf_dir = output_dir / "pdf"
            pdf_dir.mkdir()
            test_file = pdf_dir / "test.pdf"
            test_file.write_bytes(b"fake pdf content")

            # Test CLI execution via subprocess
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "infrastructure.core.cli",
                    "inventory",
                    str(output_dir),
                    "--format",
                    "text",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            assert result.returncode == 0
            combined_output = result.stdout + result.stderr
            assert "test.pdf" in combined_output

    def test_cli_discover_command(self):
        """Test discover command execution via CLI."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir) / "repo"
            repo_root.mkdir()

            # Create projects directory with a test project
            projects_dir = repo_root / "projects"
            projects_dir.mkdir()

            project_dir = projects_dir / "test_project"
            project_dir.mkdir()
            (project_dir / "src").mkdir()
            (project_dir / "tests").mkdir()
            (project_dir / "manuscript").mkdir()

            (project_dir / "src" / "__init__.py").write_text("")
            (project_dir / "tests" / "__init__.py").write_text("")

            # Test CLI execution via subprocess
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "infrastructure.core.cli",
                    "discover",
                    "--repo-root",
                    str(repo_root),
                    "--format",
                    "text",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            assert result.returncode == 0
            assert "Found 1 projects" in result.stdout


@pytest.mark.timeout(60)
class TestMainFunction:
    """Test main CLI function with real subprocess calls."""

    def test_main_help(self):
        """Test main function displays help."""
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.core.cli", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        assert "Core infrastructure CLI" in result.stdout

    def test_main_invalid_command(self):
        """Test main function with invalid command."""
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.core.cli", "invalid_command"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 2  # argparse error code


class TestCreateParserFromCoreCli:
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


class TestMainFunctionFromCoreCli:
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

    def test_discover_empty_repo(self, tmp_path, capsys):
        """Repo with no projects/ directory should still succeed."""
        args = argparse.Namespace(
            repo_root=tmp_path,
            format="text",
        )
        exit_code = handle_discover_command(args)
        assert exit_code == 0


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
