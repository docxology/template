"""Shared mock dataclasses and stage fixtures for the split pipeline-reporter test modules (formerly test_pipeline_reporter.py)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class _MockProject:
    name: str


@dataclass
class _MockStageResult:
    success: bool
    duration: float
    error_message: str = ""
    errors: list = field(default_factory=list)


@dataclass
class _MockResult:
    successful_projects: int = 0
    failed_projects: int = 0
    total_duration: float = 0.0
    infra_test_duration: float = 0.0
    project_results: Any = field(default_factory=dict)


def _stage_results() -> list[dict[str, object]]:
    return [
        {"name": "setup", "exit_code": 0, "duration": 1.2},
        {"name": "tests", "exit_code": 1, "duration": 2.8},
        {"name": "analysis", "exit_code": 0, "duration": 3.0},
    ]
