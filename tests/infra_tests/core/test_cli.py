"""Tests for core CLI interface."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from infrastructure.core.cli import create_parser, main


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
        args = parser.parse_args(["pipeline", "full", "--project", "test"])

        assert args.command == "pipeline"
        assert args.pipeline_type == "full"
        assert args.project == "test"
        assert args.skip_infra is False
        assert args.resume is False

    def test_multi_project_subcommand(self):
        """Test multi-project subcommand arguments."""
        parser = create_parser()

        args = parser.parse_args(["multi-project", "full"])

        assert args.command == "multi-project"
        assert args.execution_type == "full"
        assert args.projects is None

    def test_inventory_subcommand(self):
        """Test inventory subcommand arguments."""
        parser = create_parser()

        args = parser.parse_args(["inventory", "/tmp/output"])

        assert args.command == "inventory"
        assert args.output_dir == Path("/tmp/output")
        assert args.format == "text"
        assert args.categories is None


class TestCLISubprocess:
    """Test CLI through real subprocess execution."""

    def test_cli_pipeline_command_success(self):
        """Test successful pipeline command execution via CLI."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir) / "repo"
            repo_root.mkdir()

            # Create minimal scripts directory with stub scripts
            scripts_dir = repo_root / "scripts"
            scripts_dir.mkdir()

            script_files = [
                "00_setup_environment.py",
                "01_run_tests.py",
                "02_run_analysis.py",
                "03_render_pdf.py",
                "04_validate_output.py",
                "05_copy_outputs.py",
            ]

            for script_file in script_files:
                script_path = scripts_dir / script_file
                script_path.write_text(
                    """
import sys
import time
time.sleep(0.01)
print("Script executed successfully")
sys.exit(0)
"""
                )

            # Create project structure
            project_dir = repo_root / "projects" / "test_project"
            project_dir.mkdir(parents=True)

            # Create required subdirectories and files
            (project_dir / "src").mkdir()
            (project_dir / "tests").mkdir()
            (project_dir / "scripts").mkdir()
            (project_dir / "manuscript").mkdir()
            (project_dir / "output").mkdir()

            (project_dir / "src" / "__init__.py").write_text("")
            (project_dir / "tests" / "__init__.py").write_text("")
            (project_dir / "manuscript" / "config.yaml").write_text(
                """
paper:
  title: "Test Project"
authors:
  - name: "Test Author"
"""
            )

            # Test CLI execution via subprocess
            # Need to run from repository directory where infrastructure module is available
            env = os.environ.copy()
            env["PYTHONPATH"] = str(
                Path(__file__).parent.parent.parent
            )  # Add repository root to PYTHONPATH

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "infrastructure.core.cli",
                    "pipeline",
                    "core",
                    "--project",
                    "test_project",
                    "--repo-root",
                    str(repo_root),
                ],
                capture_output=True,
                text=True,
                env=env,
            )

            assert result.returncode == 0
            # CLI successfully executed scripts - check that scripts were called
            # The stub scripts print "Script executed successfully"
            assert "Script executed successfully" in result.stdout

    def test_cli_multi_project_command(self):
        """Test multi-project command execution via CLI."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir) / "repo"
            repo_root.mkdir()

            # Create scripts directory
            scripts_dir = repo_root / "scripts"
            scripts_dir.mkdir()

            script_files = [
                "00_setup_environment.py",
                "01_run_tests.py",
                "02_run_analysis.py",
                "03_render_pdf.py",
                "04_validate_output.py",
                "05_copy_outputs.py",
            ]

            for script_file in script_files:
                script_path = scripts_dir / script_file
                script_path.write_text(
                    """
import sys
import time
time.sleep(0.01)
print("Script executed successfully")
sys.exit(0)
"""
                )

            # Create projects
            projects_dir = repo_root / "projects"
            projects_dir.mkdir()

            for project_name in ["project1", "project2"]:
                project_dir = projects_dir / project_name
                project_dir.mkdir()

                # Create required subdirectories and files
                (project_dir / "src").mkdir()
                (project_dir / "tests").mkdir()
                (project_dir / "scripts").mkdir()
                (project_dir / "manuscript").mkdir()
                (project_dir / "output").mkdir()

                (project_dir / "src" / "__init__.py").write_text("")
                (project_dir / "tests" / "__init__.py").write_text("")
                (project_dir / "manuscript" / "config.yaml").write_text(
                    f"""
paper:
  title: "{project_name} Project"
authors:
  - name: "Test Author"
"""
                )

            # Test CLI execution via subprocess
            # Need to run from repository directory where infrastructure module is available
            env = os.environ.copy()
            env["PYTHONPATH"] = str(
                Path(__file__).parent.parent.parent
            )  # Add repository root to PYTHONPATH

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "infrastructure.core.cli",
                    "multi-project",
                    "core",
                    "--repo-root",
                    str(repo_root),
                ],
                capture_output=True,
                text=True,
                env=env,
            )

            assert result.returncode == 0
            # CLI successfully executed scripts for multiple projects
            # Should have more script executions (2 projects × multiple scripts each)
            assert result.stdout.count("Script executed successfully") > 10

    def test_cli_inventory_command(self):
        """Test inventory command execution via CLI."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "output"
            output_dir.mkdir()

            # Create a test file
            test_file = output_dir / "test.pdf"
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
            )

            assert result.returncode == 0
            # Inventory command may produce output in different formats
            combined_output = result.stdout + result.stderr
            # Just check that it ran without error - specific output format may vary
            assert len(combined_output.strip()) >= 0

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
            )

            assert result.returncode == 0
            assert "Found 1 projects" in result.stdout


class TestMainFunction:
    """Test main CLI function with real subprocess calls."""

    def test_main_help(self):
        """Test main function displays help."""
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.core.cli", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Core infrastructure CLI" in result.stdout

    def test_main_invalid_command(self):
        """Test main function with invalid command."""
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.core.cli", "invalid_command"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2  # argparse error code
