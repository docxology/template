"""Canonical typed evidence for pure aggregate-reporting fixtures."""

from __future__ import annotations

from typing import Any

from infrastructure.core.pipeline.multi_project import MultiProjectResult
from infrastructure.core.pipeline.outcomes import RunResult, outcome_for_result
from infrastructure.core.pipeline.types import PipelineStageResult


def bound_result(**values: Any) -> MultiProjectResult:
    """Bind explicitly declared fixture stage keys and retain malformed display cases."""
    rows = values.get("project_results", {})
    runs = {}
    if isinstance(rows, dict):
        for name, stages in rows.items():
            if not isinstance(stages, list) or any(not isinstance(stage, PipelineStageResult) for stage in stages):
                continue
            for index, stage in enumerate(stages, 1):
                if not stage.stage_key:
                    stage.stage_key = f"fixture_{index}"
                stage.outcome = outcome_for_result(stage)
            runs[name] = RunResult.from_results(stages, tuple(stage.stage_key for stage in stages))
    return MultiProjectResult(
        **values, expected_projects=tuple(rows) if isinstance(rows, dict) else (), run_results=runs
    )
