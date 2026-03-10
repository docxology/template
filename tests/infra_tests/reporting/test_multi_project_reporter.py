"""Tests for infrastructure.reporting.multi_project_reporter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from infrastructure.core.multi_project import MultiProjectResult
from infrastructure.core.pipeline import PipelineStageResult
from infrastructure.reporting.multi_project_reporter import (
    _build_summary_dict,
    generate_multi_project_summary_report,
)


@dataclass
class _FakeProject:
    name: str


def _make_stage(name: str, success: bool = True, duration: float = 1.0) -> PipelineStageResult:
    return PipelineStageResult(
        stage_num=1,
        stage_name=name,
        success=success,
        exit_code=0 if success else 1,
        duration=duration,
        error_message="" if success else f"{name} failed",
    )


def test_build_summary_dict_two_projects_all_pass():
    projects = [_FakeProject("alpha"), _FakeProject("beta")]
    alpha_stages = [_make_stage("tests", True, 2.0), _make_stage("render", True, 3.0)]
    beta_stages = [_make_stage("tests", True, 1.5)]
    result = MultiProjectResult(
        project_results={"alpha": alpha_stages, "beta": beta_stages},
        successful_projects=2,
        failed_projects=0,
        total_duration=10.0,
        infra_test_duration=1.0,
    )

    summary = _build_summary_dict(result, projects)

    assert summary["total_projects"] == 2
    assert summary["successful_projects"] == 2
    assert summary["failed_projects"] == 0
    assert summary["total_duration"] == 10.0
    assert summary["projects"]["alpha"]["success"] is True
    assert summary["projects"]["alpha"]["duration"] == pytest.approx(5.0)
    assert summary["projects"]["alpha"]["stages_completed"] == 2
    assert summary["projects"]["alpha"]["errors"] == []
    assert summary["projects"]["beta"]["success"] is True


def test_build_summary_dict_one_failed_project():
    projects = [_FakeProject("x")]
    stages = [_make_stage("tests", False, 0.5)]
    result = MultiProjectResult(
        project_results={"x": stages},
        successful_projects=0,
        failed_projects=1,
        total_duration=5.0,
        infra_test_duration=0.0,
    )

    summary = _build_summary_dict(result, projects)

    assert summary["failed_projects"] == 1
    assert summary["projects"]["x"]["success"] is False
    assert any("tests failed" in e for e in summary["projects"]["x"]["errors"])


def test_build_summary_dict_empty_projects():
    result = MultiProjectResult(
        project_results={},
        successful_projects=0,
        failed_projects=0,
        total_duration=0.0,
        infra_test_duration=0.0,
    )

    summary = _build_summary_dict(result, [])

    assert summary["total_projects"] == 0
    assert summary["projects"] == {}


def test_generate_multi_project_summary_report_writes_files(tmp_path: Path):
    projects = [_FakeProject("proj1"), _FakeProject("proj2")]
    stages = [_make_stage("tests", True, 1.0)]
    result = MultiProjectResult(
        project_results={"proj1": stages, "proj2": stages},
        successful_projects=2,
        failed_projects=0,
        total_duration=5.0,
        infra_test_duration=0.5,
    )

    files = generate_multi_project_summary_report(result, projects, tmp_path)

    assert "json" in files
    assert "markdown" in files
    assert files["json"].exists()
    assert files["markdown"].exists()
    content = files["json"].read_text()
    assert "proj1" in content
    assert "proj2" in content
