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


def test_success_flag_without_completed_contract_is_not_reported_as_succeeded() -> None:
    """A row marked successful but lacking contract completion stays unproven."""
    projs = (_p("alpha"),)
    result = MultiProjectResult(
        project_results={"alpha": [PipelineStageResult(1, "Environment Setup", True, 0.1)]},
        successful_projects=1,
        failed_projects=0,
    )
    lines = format_multi_project_outcome_lines(projs, result)
    assert "Succeeded:" not in lines and "Failed:" in lines
