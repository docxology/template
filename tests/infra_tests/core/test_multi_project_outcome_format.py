"""Tests for :func:`format_multi_project_outcome_lines`."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.pipeline.multi_project import MultiProjectResult, format_multi_project_outcome_lines
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


def test_all_succeeded_lists_names() -> None:
    projs = (_p("alpha"), _p("beta"))
    ok = PipelineStageResult(1, "Environment Setup", True, 0.1)
    result = MultiProjectResult(
        project_results={
            "alpha": [ok],
            "beta": [ok],
        },
        successful_projects=2,
        failed_projects=0,
    )
    lines = format_multi_project_outcome_lines(projs, result)
    assert lines[0] == "Succeeded:"
    assert "  - alpha" in lines
    assert "  - beta" in lines
    assert "Failed:" not in lines


def test_infra_aborted_single_message() -> None:
    projs = (_p("a"), _p("b"))
    result = MultiProjectResult(
        project_results={},
        successful_projects=0,
        failed_projects=2,
    )
    lines = format_multi_project_outcome_lines(projs, result)
    assert len(lines) == 1
    assert "Infrastructure tests failed" in lines[0]


def test_failed_stage_includes_name_and_hint() -> None:
    projs = (_p("good"), _p("bad"))
    ok = PipelineStageResult(1, "Setup", True, 0.1)
    boom = PipelineStageResult(
        2,
        "Run Tests",
        False,
        0.2,
        exit_code=1,
        error_message="assert 1 == 2",
    )
    result = MultiProjectResult(
        project_results={
            "good": [ok],
            "bad": [ok, boom],
        },
        successful_projects=1,
        failed_projects=1,
    )
    lines = format_multi_project_outcome_lines(projs, result)
    assert "Succeeded:" in lines
    assert "  - good" in lines
    idx = lines.index("Failed:")
    assert any("bad" in ln and "Run Tests" in ln and "assert" in ln for ln in lines[idx + 1 :])


def test_truncates_long_error_message() -> None:
    projs = (_p("x"),)
    long_msg = "e" * 200
    bad = PipelineStageResult(
        1,
        "Render PDF",
        False,
        0.0,
        exit_code=1,
        error_message=long_msg,
    )
    result = MultiProjectResult(
        project_results={"x": [bad]},
        successful_projects=0,
        failed_projects=1,
    )
    lines = format_multi_project_outcome_lines(projs, result, hint_max_chars=80)
    failed_line = next(ln for ln in lines if ln.startswith("  - x:"))
    assert "…" in failed_line or len(failed_line) < len(long_msg) + 40


def test_empty_stage_list_maps_to_exception_message() -> None:
    projs = (_p("ghost"),)
    result = MultiProjectResult(
        project_results={"ghost": []},
        successful_projects=0,
        failed_projects=1,
    )
    lines = format_multi_project_outcome_lines(projs, result)
    assert any("before stage results" in ln for ln in lines)


def test_missing_project_key_in_results() -> None:
    projs = (_p("orphan"),)
    result = MultiProjectResult(
        project_results={
            "wrong_name": [PipelineStageResult(1, "Setup", True, 0.0)],
        },
        successful_projects=0,
        failed_projects=1,
    )
    lines = format_multi_project_outcome_lines(projs, result)
    assert any("no pipeline results recorded" in ln for ln in lines)
