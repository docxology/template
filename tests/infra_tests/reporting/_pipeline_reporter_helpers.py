"""Canonical result and stage fixtures for the split pipeline-reporter test modules (formerly test_pipeline_reporter.py)."""

from __future__ import annotations


def _Project(name: str):
    from pathlib import Path
    from infrastructure.project.project_info import ProjectInfo

    return ProjectInfo(name, Path("/tmp") / name, True, True, False, False)


def _Stage(success: bool, duration: float, error_message: str = "", errors=None):
    from infrastructure.core.pipeline.types import PipelineStageResult

    return PipelineStageResult(
        1, "Fixture", success, duration, 0 if success else 1, error_message, stage_completed=success
    )


from tests._support.multi_project import bound_result


def _Result(**values):
    return bound_result(**values)


def _stage_results() -> list[dict[str, object]]:
    return [
        {"name": "setup", "exit_code": 0, "duration": 1.2},
        {"name": "tests", "exit_code": 1, "duration": 2.8},
        {"name": "analysis", "exit_code": 0, "duration": 3.0},
    ]
