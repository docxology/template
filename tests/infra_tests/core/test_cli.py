"""Tests for core CLI interface."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from infrastructure.core.cli import main
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
            # This disposable non-Git fixture owns its deterministic epoch.
            env={**os.environ, "SOURCE_DATE_EPOCH": "0"},
            timeout=30,
        )
        assert result.returncode == 0, (result.stdout, result.stderr)
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
            env={**os.environ, "SOURCE_DATE_EPOCH": "0"},
            # Guardian startup, the shared gate and one project child run in turn;
            # this bounds only the test's wait (CI lanes pass --timeout=120).
            timeout=110,
        )
        if result.returncode != expected_code:
            # Pytest clips assertion tuple repr; retain the real child diagnostics.
            sys.stdout.write(result.stdout)
            sys.stderr.write(result.stderr)
        assert result.returncode == expected_code, (result.stdout, result.stderr)
        rows = (tmp_path / "process_order.log").read_text().splitlines()
        assert rows == (
            ["templates/beta:infra", "templates/beta:analysis"] if infra_exit == 0 else ["templates/beta:infra"]
        )

    @pytest.mark.parametrize("mutation_stage", ["shared", "project"])
    def test_cli_frozen_source_refusal_retains_complete_diagnostics(self, tmp_path: Path, mutation_stage: str) -> None:
        from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline

        scaffold_pipeline(tmp_path, ("templates/alpha", "templates/beta"))
        marker = b"\n# Actual frozen Source control.\n"
        if mutation_stage == "project":
            target = tmp_path / "projects/templates/beta/src/__init__.py"
            script = tmp_path / "scripts/stage.py"
            script.write_text(
                script.read_text()
                + "\nif step == 'analysis':\n"
                + "    target = Path('projects') / project / 'src' / '__init__.py'\n"
                + f"    target.write_bytes(target.read_bytes() + {marker!r})\n"
            )
        else:
            target = tmp_path / "scripts/pipeline/stage_01_test.py"
            body = target.read_text()
            assert body.count("sys.exit(0)\n") == 1
            target.write_text(
                body.replace(
                    "sys.exit(0)\n",
                    "target = Path(__file__)\n"
                    + f"target.write_bytes(target.read_bytes() + {marker!r})\n"
                    + "sys.exit(0)\n",
                )
            )
        original = target.read_bytes()
        environment = {**os.environ, "SOURCE_DATE_EPOCH": "0"}
        observation = (
            "import json,sys\nfrom pathlib import Path\n"
            "from infrastructure.core.pipeline.fingerprints import canonical_digest,source_fingerprint_components\n"
            "root=Path(sys.argv[1]).resolve()\n"
            "components=source_fingerprint_components(root,root/'projects/templates/beta',"
            "definition_path=root/'infrastructure/core/pipeline/pipeline.yaml')\n"
            "print(json.dumps({'role':'Independent adjacent-process observation; only an exact total match "
            "binds it to the original CLI identity; no substituted admission',"
            "'total':canonical_digest(components),"
            "'component_digests':{key:canonical_digest(components[key]) for key in ('source','python','tools')},"
            "'components':components},sort_keys=True))\n"
        )

        def observe_source(label: str) -> None:
            directory = tmp_path / "cli-observations" / label
            directory.mkdir(parents=True)
            command = [sys.executable, "-B", "-c", observation, str(tmp_path)]
            try:
                observed = subprocess.run(command, env=environment, capture_output=True, timeout=2)
            except subprocess.TimeoutExpired as error:
                (directory / "stdout").write_bytes(error.stdout or b"")
                (directory / "stderr").write_bytes(error.stderr or b"")
                (directory / "timeout.json").write_text(
                    json.dumps({"command": error.cmd, "timeout": error.timeout}) + "\n"
                )
            else:
                (directory / "stdout").write_bytes(observed.stdout)
                (directory / "stderr").write_bytes(observed.stderr)
                (directory / "exit.json").write_text(json.dumps({"returncode": observed.returncode}) + "\n")

        observe_source("source-before")
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
            env=environment,
            timeout=110,
        )
        directory = tmp_path / "cli-observations" / "refusal"
        directory.mkdir(parents=True)
        (directory / "stdout").write_text(result.stdout)
        (directory / "stderr").write_text(result.stderr)
        (directory / "exit.json").write_text(json.dumps({"returncode": result.returncode}) + "\n")
        observe_source("source-after")
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        assert result.returncode == 75
        assert target.read_bytes() == original + marker
        assert (tmp_path / "process_order.log").read_text().splitlines() == (
            ["templates/beta:infra", "templates/beta:analysis"]
            if mutation_stage == "project"
            else ["templates/beta:infra"]
        )
        encoded = next(
            line.split("fingerprint_diagnostics=", 1)[1]
            for line in result.stdout.splitlines()
            if "fingerprint_diagnostics=" in line
        )
        diagnostic, _ = json.JSONDecoder().raw_decode(encoded)
        assert diagnostic["expected_total"] != diagnostic["observed_total"]
        digests = [
            diagnostic["expected_total"],
            diagnostic["observed_total"],
            *(diagnostic["components"][name] for name in ("source", "python", "tools")),
        ]
        assert all(len(digest) == 64 and set(digest) <= set("0123456789abcdef") for digest in digests)

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

    def test_main_invalid_command(self):
        """Test main function with invalid command."""
        result = subprocess.run(
            [sys.executable, "-m", "infrastructure.core.cli", "invalid_command"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 2  # argparse error code


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

    def test_discover_command_runs(self, tmp_path: Path):
        """Missing repositories return empty discovery without an error."""
        missing = tmp_path / "missing"
        old_argv = sys.argv
        try:
            sys.argv = ["infra-cli", "discover", "--repo-root", str(missing)]
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
