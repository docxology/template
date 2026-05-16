"""Tests for :func:`format_multi_project_detailed_report`.

This function renders the rich end-of-run summary shown after option ``d``
of the interactive menu. Tests assert on stable section headings and key
substrings rather than full text — width and layout details may evolve.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.pipeline.multi_project import (
    MultiProjectResult,
    format_multi_project_detailed_report,
)
from infrastructure.core.pipeline.types import PipelineStageResult
from infrastructure.project.project_info import ProjectInfo


def _p(name: str) -> ProjectInfo:
    path = Path("/tmp") / name
    return ProjectInfo(
        name=name,
        path=path,
        has_src=True,
        has_tests=True,
        has_scripts=False,
        has_manuscript=False,
    )


def _ok(num: int, name: str, dur: float = 1.0) -> PipelineStageResult:
    return PipelineStageResult(num, name, True, dur)


def _bad(num: int, name: str, dur: float, msg: str) -> PipelineStageResult:
    return PipelineStageResult(num, name, False, dur, error_message=msg)


def test_detailed_report_all_succeeded() -> None:
    projs = (_p("alpha"), _p("beta"))
    result = MultiProjectResult(
        project_results={
            "alpha": [_ok(1, "Environment Setup"), _ok(2, "Project Tests", 2.0)],
            "beta": [_ok(1, "Environment Setup"), _ok(2, "Project Tests", 3.0)],
        },
        total_duration=7.0,
        successful_projects=2,
        failed_projects=0,
    )
    lines = format_multi_project_detailed_report(projs, result)
    text = "\n".join(lines)
    assert "MULTI-PROJECT EXECUTION SUMMARY" in text
    assert "2 projects" in text and "2 succeeded" in text
    assert "PROJECT STATUS" in text
    assert "STAGE TIMING BREAKDOWN" in text
    assert "ALL 2 PROJECTS PASSED" in text
    assert "FAILURE DETAILS" not in text


def test_detailed_report_mixed_outcomes_shows_failure_section() -> None:
    projs = (_p("alpha"), _p("beta"))
    result = MultiProjectResult(
        project_results={
            "alpha": [_ok(1, "Environment Setup"), _ok(2, "Project Tests")],
            "beta": [
                _ok(1, "Environment Setup"),
                _bad(2, "Project Tests", 5.0, "5 tests failed"),
            ],
        },
        total_duration=8.0,
        successful_projects=1,
        failed_projects=1,
    )
    lines = format_multi_project_detailed_report(projs, result)
    text = "\n".join(lines)
    assert "FAILURE DETAILS" in text
    assert "❌ beta" in text
    assert "Project Tests" in text
    assert "5 tests failed" in text
    assert "1/2 succeeded" in text


def test_detailed_report_renders_stage_breakdown_sorted_by_total_time() -> None:
    projs = (_p("alpha"),)
    result = MultiProjectResult(
        project_results={
            "alpha": [
                _ok(1, "Environment Setup", 5.0),
                _ok(2, "Project Tests", 30.0),
                _ok(3, "PDF Rendering", 10.0),
            ],
        },
        total_duration=45.0,
        successful_projects=1,
        failed_projects=0,
    )
    lines = format_multi_project_detailed_report(projs, result)
    text = "\n".join(lines)
    # Slowest stage (Project Tests) appears before slower-but-not-slowest stages.
    tests_idx = text.index("Project Tests")
    render_idx = text.index("PDF Rendering")
    env_idx = text.index("Environment Setup")
    # Find the indices within the STAGE TIMING BREAKDOWN section.
    stage_section = text.split("STAGE TIMING BREAKDOWN", 1)[1]
    assert stage_section.index("Project Tests") < stage_section.index("PDF Rendering")
    assert stage_section.index("PDF Rendering") < stage_section.index("Environment Setup")
    # Names also still appear elsewhere
    assert tests_idx > 0 and render_idx > 0 and env_idx > 0


def test_detailed_report_includes_next_steps_when_repo_root_provided(tmp_path: Path) -> None:
    projs = (_p("alpha"),)
    result = MultiProjectResult(
        project_results={
            "alpha": [
                _bad(1, "Project Analysis", 0.5, "boom"),
            ],
        },
        total_duration=0.5,
        successful_projects=0,
        failed_projects=1,
    )
    lines = format_multi_project_detailed_report(projs, result, repo_root=tmp_path)
    text = "\n".join(lines)
    assert "NEXT STEPS" in text
    assert "Re-run a failed project" in text
    assert "OUTPUT LOCATIONS" in text


def test_detailed_report_handles_empty_project_list() -> None:
    result = MultiProjectResult(
        project_results={},
        total_duration=0.0,
        successful_projects=0,
        failed_projects=0,
    )
    lines = format_multi_project_detailed_report((), result)
    # Header still rendered, but no projects to enumerate.
    text = "\n".join(lines)
    assert "MULTI-PROJECT EXECUTION SUMMARY" in text
    assert "0 projects" in text
