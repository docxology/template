#!/usr/bin/env python3
"""Tests for infrastructure.core.pipeline.post_run_reporting."""

from __future__ import annotations

from pathlib import Path

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
