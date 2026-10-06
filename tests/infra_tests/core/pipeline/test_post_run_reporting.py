#!/usr/bin/env python3
"""Tests for infrastructure.core.pipeline.post_run_reporting."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import pytest

from infrastructure.core.pipeline.post_run_reporting import write_pipeline_post_run_reports
from infrastructure.core.pipeline.types import PipelineStageResult
from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus
from infrastructure.reporting.pipeline_html import generate_html_report
from infrastructure.reporting.pipeline_markdown import _generate_pipeline_markdown
from infrastructure.reporting.pipeline_report_model import generate_pipeline_report, stage_is_complete


def _result(name: str, *, success: bool = True) -> PipelineStageResult:
    return PipelineStageResult(
        stage_num=1,
        stage_name=name,
        success=success,
        duration=1.0,
        exit_code=0 if success else 1,
    )


def test_write_pipeline_post_run_reports_creates_reports_dir(tmp_path: Path) -> None:
    project = "demo"
    project_root = tmp_path / "projects" / project
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True)
    results = [_result("setup"), _result("tests")]

    write_pipeline_post_run_reports(
        results=results,
        repo_root=tmp_path,
        project_name=project,
        skip_infra=False,
    )

    reports_dir = output_dir / "reports"
    assert reports_dir.is_dir()
    json_reports = list(reports_dir.glob("pipeline_report*.json"))
    assert json_reports, "expected JSON pipeline report from post-run reporting"


def test_post_run_reporting_uses_lifecycle_local_inventory(tmp_path: Path) -> None:
    """Qualified local projects retain stable facts behind packaging ignores."""
    project = "working/demo"
    project_root = tmp_path / "projects" / "working" / "demo"
    output_dir = project_root / "output"
    result_path = output_dir / "data" / "result.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text('{"score": 7}\n', encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".gitignore").write_text(
        "projects/working/demo/output/\n",
        encoding="utf-8",
    )

    write_pipeline_post_run_reports(
        results=[_result("analysis")],
        repo_root=tmp_path,
        project_name=project,
        skip_infra=False,
    )

    report_path = next((output_dir / "reports").glob("pipeline_report*.json"))
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    statistics = payload["output_statistics"]
    assert statistics["inventory_mode"] == "stable-local-output-v1"
    assert statistics["directories"]["data"]["file_count"] == 1


@pytest.mark.parametrize(
    "status",
    [
        StageStatus.PAUSED,
        StageStatus.BLOCKED,
        StageStatus.REJECTED,
        StageStatus.ABORTED,
        StageStatus.FAILED,
        StageStatus.TIMED_OUT,
        StageStatus.INTERRUPTED,
    ],
)
def test_original_child_zero_cannot_render_as_completed(tmp_path: Path, status: StageStatus) -> None:
    outcome = StageOutcome("child", status, 0, "Post-execution contract refused completion", attempt_exit_codes=(0,))
    codes = {
        StageStatus.PAUSED: 75,
        StageStatus.BLOCKED: 75,
        StageStatus.REJECTED: 1,
        StageStatus.ABORTED: 1,
        StageStatus.FAILED: 1,
        StageStatus.TIMED_OUT: 124,
        StageStatus.INTERRUPTED: 130,
    }
    report = generate_pipeline_report(
        [{"name": "Child", "exit_code": codes[status], "duration": 1.0, "outcome": outcome.to_dict()}], 1.0, tmp_path
    )
    stage = report.stages[0]
    assert stage.status == status.value
    assert not stage.completed and not stage_is_complete(stage)
    assert stage.context["outcome"]["attempt_exit_codes"] == (0,)
    assert f"❌ {status.value}" in generate_html_report(report)
    assert f"❌ {status.value}" in _generate_pipeline_markdown(report)


def test_post_run_saved_report_keeps_typed_custody(tmp_path: Path) -> None:
    (tmp_path / "projects/demo/output").mkdir(parents=True)
    result = _result("Child")
    result.stage_key = "child"
    result.input_digest = "a" * 64
    result.output_digest = "b" * 64
    result.outcome = StageOutcome("child", StageStatus.BLOCKED, 0, "Consumed bytes changed", attempt_exit_codes=(0,))
    result.success = False
    result.stage_completed = False
    result.exit_code = 75
    write_pipeline_post_run_reports(results=[result], repo_root=tmp_path, project_name="demo", skip_infra=False)
    report = next((tmp_path / "projects/demo/output/reports").glob("pipeline_report*.json"))
    stage = json.loads(report.read_text())["stages"][0]
    assert stage["status"] == "blocked" and stage["completed"] is False
    assert stage["context"]["outcome"]["child_exit_code"] == 0
    assert stage["context"]["input_digest"] == "a" * 64


@pytest.mark.parametrize("changed", ["identity", "exit_code"])
def test_contradictory_outer_stage_binding_refuses_completion(tmp_path: Path, changed: str) -> None:
    outcome = StageOutcome("child", StageStatus.SUCCEEDED, 0, attempt_exit_codes=(0,))
    result = {
        "name": "Child",
        "stage_key": "wrong" if changed == "identity" else "child",
        "exit_code": 7 if changed == "exit_code" else 0,
        "duration": 1.0,
        "outcome": outcome.to_dict(),
    }
    with pytest.raises(ValueError, match="contradicts"):
        generate_pipeline_report([result], 1.0, tmp_path)
