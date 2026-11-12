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
        from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
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
            "import base64,hashlib,json,os,stat,sys\n"
            "from pathlib import Path\n"
            "from infrastructure.core.pipeline.fingerprints import canonical_digest,source_fingerprint_components\n"
            "from infrastructure.core.pipeline.fingerprint_files import anchored_parent,observation\n"
            "root=Path(sys.argv[1]).resolve()\n"
            "components=source_fingerprint_components(root,root/'projects/templates/beta',definition_path=root/'infrastructure/core/pipeline/pipeline.yaml')\n"
            "runtime=components['tools'].get('analysis_runtime',{})\n"
            "sdk_records={}\n"
            "for key,expected in (runtime.get('installation_metadata',{}) if isinstance(runtime,dict) else {}).items():\n"
            "    index,relative=key.split('/',1)\n"
            "    declared=Path(relative)\n"
            "    if declared.name!='RECORD' or not declared.parent.name.startswith('research_project_template-'):\n"
            "        continue\n"
            "    target=Path(runtime['site_roots'][int(index)])/relative\n"
            "    entry={'component_sha256':expected}\n"
            "    try:\n"
            "        with anchored_parent(target) as parent:\n"
            "            if parent is None:\n"
            "                raise FileNotFoundError('observed metadata ancestor unavailable')\n"
            "            descriptor=os.open(target.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)\n"
            "            try:\n"
            "                before=os.fstat(descriptor)\n"
            "                if not stat.S_ISREG(before.st_mode) or before.st_size>1024*1024:\n"
            "                    raise ValueError('observed metadata is not a bounded regular file')\n"
            "                chunks=[]\n"
            "                size=0\n"
            "                while chunk:=os.read(descriptor,1024*1024+1-size):\n"
            "                    size+=len(chunk)\n"
            "                    if size>1024*1024:\n"
            "                        raise ValueError('observed metadata exceeded original capture bound')\n"
            "                    chunks.append(chunk)\n"
            "                raw=b''.join(chunks)\n"
            "                stable=observation(before)==observation(os.fstat(descriptor))==observation(os.stat(target.name,dir_fd=parent,follow_symlinks=False))\n"
            "            finally:\n"
            "                os.close(descriptor)\n"
            "        digest=hashlib.sha256(raw).hexdigest()\n"
            "        entry.update(sha256=digest,bytes=len(raw),base64=base64.b64encode(raw).decode('ascii'),nlink=before.st_nlink,stable=stable,bound_to_components=stable and digest==expected)\n"
            "    except (OSError,ValueError) as error:\n"
            "        entry['capture_error']=type(error).__name__\n"
            "    sdk_records[key]=entry\n"
            "print(json.dumps({'role':'Independent adjacent-process observation; only an exact total match binds it to the original CLI identity; raw SDK RECORD is bounded diagnostic DATA, never substituted admission','total':canonical_digest(components),'component_digests':{key:canonical_digest(components[key]) for key in ('source','python','tools')},'components':components,'sdk_record_data':sdk_records},sort_keys=True))\n"
        )

        def observe_source(label: str) -> None:
            directory = tmp_path / "cli-observations" / label
            directory.mkdir(parents=True)
            command = [sys.executable, "-B", "-c", observation, str(tmp_path)]
            observed = run_bounded_subprocess(
                command,
                cwd=Path(__file__).resolve().parents[3],
                env=environment,
                timeout=2,
                guardian_env=build_bounded_env(),
            )
            (directory / "stdout").write_text(observed.stdout, encoding="utf-8")
            (directory / "stderr").write_text(observed.stderr, encoding="utf-8")
            details = {
                "command": command,
                "timeout": 2,
                "returncode": observed.returncode,
                "original_returncode": observed.original_returncode,
                "timed_out": observed.timed_out,
                "custody_refused": observed.custody_refused,
                "command_error": observed.command_error,
                "capture_encoding": "utf-8",
                "capture_errors": "replace",
            }
            (directory / ("timeout.json" if observed.timed_out else "exit.json")).write_text(json.dumps(details) + "\n")
            if observed.pid is not None and (observed.command_error or observed.custody_refused):
                raise RuntimeError(f"Fingerprint observer cleanup refused: {observed.command_error}")

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

    def test_nonexistent_dir(self, tmp_path, capsys):
        args = argparse.Namespace(
            output_dir=tmp_path / "nonexistent",
            categories=None,
            format="text",
        )
        exit_code = handle_inventory_command(args)
        assert exit_code == 0  # Returns 0 with "No files found"
