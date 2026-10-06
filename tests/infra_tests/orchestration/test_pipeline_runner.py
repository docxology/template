"""Runner contracts through real declared stages and child processes."""

from __future__ import annotations

import io
from pathlib import Path

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
