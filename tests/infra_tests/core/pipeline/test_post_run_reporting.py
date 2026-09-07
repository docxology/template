#!/usr/bin/env python3
"""Tests for infrastructure.core.pipeline.post_run_reporting."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from infrastructure.core.pipeline.post_run_reporting import write_pipeline_post_run_reports
from infrastructure.core.pipeline.types import PipelineStageResult


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
