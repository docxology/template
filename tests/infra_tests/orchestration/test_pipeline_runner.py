"""Runner contracts through real declared stages and child processes."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.orchestration.pipeline_runner import MultiProjectInvocation, PipelineInvocation, PipelineRunner
from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline


def test_default_core_banners_match_executed_plan(tmp_path: Path) -> None:
    scaffold_pipeline(tmp_path)
    runner = PipelineRunner(tmp_path, stream=io.StringIO())
    assert runner.run(PipelineInvocation("demo")) == 0
    transcript = runner.stream.getvalue()
    assert "CORE PIPELINE" in transcript and "Project Analysis" in transcript
    assert "Live Review" not in transcript
    assert (tmp_path / "process_order.log").read_text().splitlines() == ["demo:infra", "demo:analysis"]


def test_explicit_live_mode_executes_live_stage(tmp_path: Path) -> None:
    scaffold_pipeline(tmp_path)
    runner = PipelineRunner(tmp_path, stream=io.StringIO())
    assert runner.run(PipelineInvocation("demo", mode="live")) == 0
    assert "Live Review" in runner.stream.getvalue()
    assert (tmp_path / "projects/demo/output/data/live.json").is_file()


def test_skip_infra_uses_selected_expected_set(tmp_path: Path) -> None:
    scaffold_pipeline(tmp_path)
    runner = PipelineRunner(tmp_path, stream=io.StringIO())
    assert runner.run(PipelineInvocation("demo", skip_infra=True)) == 0
    assert "Infrastructure Tests" not in runner.stream.getvalue()
    assert (tmp_path / "process_order.log").read_text().splitlines() == ["demo:analysis"]


def test_child_exit_two_cannot_report_complete(tmp_path: Path) -> None:
    scaffold_pipeline(tmp_path, ("fail",))
    runner = PipelineRunner(tmp_path, stream=io.StringIO())
    assert runner.run(PipelineInvocation("fail", skip_infra=True)) == 1
    assert "PIPELINE FAILED" in runner.stream.getvalue()


def test_invalid_mode_is_invocation_error(tmp_path: Path) -> None:
    scaffold_pipeline(tmp_path)
    runner = PipelineRunner(tmp_path, stream=io.StringIO())
    assert runner.run(PipelineInvocation("demo", mode="unknown")) == 2
    assert not (tmp_path / "process_order.log").exists()


def test_multi_runs_shared_infrastructure_once(tmp_path: Path) -> None:
    scaffold_pipeline(tmp_path, ("alpha", "beta"))
    runner = PipelineRunner(tmp_path, stream=io.StringIO())
    assert runner.run_multi(MultiProjectInvocation()) == 0
    rows = (tmp_path / "process_order.log").read_text().splitlines()
    assert sum(row.endswith(":infra") for row in rows) == 1
    assert sorted(row for row in rows if row.endswith(":analysis")) == ["alpha:analysis", "beta:analysis"]


def test_failed_shared_infrastructure_prevents_all_projects(tmp_path: Path) -> None:
    scaffold_pipeline(tmp_path, ("alpha", "beta"), infra_exit=2)
    runner = PipelineRunner(tmp_path, stream=io.StringIO())
    assert runner.run_multi(MultiProjectInvocation()) == 1
    assert (tmp_path / "process_order.log").read_text().splitlines() == ["alpha:infra"]


def test_runner_canonicalizes_bare_public_project_before_execution(tmp_path: Path) -> None:
    scaffold_pipeline(tmp_path, ("templates/demo",))
    runner = PipelineRunner(tmp_path, stream=io.StringIO())
    assert runner.run(PipelineInvocation("demo", skip_infra=True)) == 0
    assert (tmp_path / "process_order.log").read_text().splitlines() == ["templates/demo:analysis"]


def test_runner_rejects_traversal_before_creating_logs(tmp_path: Path) -> None:
    scaffold_pipeline(tmp_path)
    runner = PipelineRunner(tmp_path, stream=io.StringIO())
    assert runner.run(PipelineInvocation("../outside")) == 2
    assert not (tmp_path / "outside").exists()
    assert not (tmp_path / "process_order.log").exists()


def test_multi_invalid_mode_is_invocation_error(tmp_path: Path) -> None:
    scaffold_pipeline(tmp_path)
    runner = PipelineRunner(tmp_path, stream=io.StringIO())
    assert runner.run_multi(MultiProjectInvocation(mode="unknown")) == 2
    assert not (tmp_path / "process_order.log").exists()


def _run_real_multi_cli(root: Path, label: str, *options: str) -> subprocess.CompletedProcess[bytes]:
    """Run the actual CLI and retain its original streams beside the owned fixture."""
    environment = dict(os.environ)
    for key in (
        "TEMPLATE_SKIP_LINK_SYNC",
        "TEMPLATE_SKIP_FOND_LINK_SYNC",
        "TEMPLATE_SKIP_RULE_LINK_SYNC",
        "TEMPLATE_SKIP_TOOL_LINK_SYNC",
    ):
        environment[key] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "infrastructure.orchestration",
            "--repo-root",
            str(root),
            "pipeline",
            "--all-projects",
            "--skip-infra",
            *options,
        ],
        cwd=Path(__file__).resolve().parents[3],
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=30,
        check=False,
    )
    directory = root / "cli-observations" / label
    directory.mkdir(parents=True)
    (directory / "stdout").write_bytes(result.stdout)
    (directory / "stderr").write_bytes(result.stderr)
    (directory / "exit.json").write_text(json.dumps({"returncode": result.returncode}) + "\n", encoding="utf-8")
    return result


@pytest.mark.timeout(90)
def test_cli_all_project_resume_preserves_checkpoint_refusal(tmp_path: Path) -> None:
    scaffold_pipeline(tmp_path, ("alpha", "beta"))
    resumed = _run_real_multi_cli(tmp_path, "resume", "--resume")
    assert resumed.returncode == 75, (resumed.stdout.decode(), resumed.stderr.decode())
    assert not (tmp_path / "process_order.log").exists()
    for name in ("alpha", "beta"):
        execution = json.loads((tmp_path / "projects" / name / "output/.pipeline/execution.json").read_bytes())
        assert execution["complete"] is False and execution["exit_code"] == 75
        assert len(execution["outcomes"]) == 1
        outcome = execution["outcomes"][0]
        assert outcome["stage_key"] == "resume" and outcome["status"] == "blocked"
        assert "Resume refused:" in outcome["diagnostic"]

    fresh = _run_real_multi_cli(tmp_path, "fresh")
    assert fresh.returncode == 0, (fresh.stdout.decode(), fresh.stderr.decode())
    assert sorted((tmp_path / "process_order.log").read_text().splitlines()) == ["alpha:analysis", "beta:analysis"]


@pytest.mark.timeout(90)
def test_cli_all_project_incremental_refuses_before_project_execution(tmp_path: Path) -> None:
    scaffold_pipeline(tmp_path, ("alpha", "beta"))
    refused = _run_real_multi_cli(tmp_path, "incremental", "--incremental")
    assert refused.returncode == 2, (refused.stdout.decode(), refused.stderr.decode())
    assert b"--incremental is supported only for a single-project pipeline" in refused.stderr
    assert not (tmp_path / "process_order.log").exists()
    assert not any((tmp_path / "projects").glob("*/output/.pipeline/execution.json"))
