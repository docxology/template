"""Pipeline report data model and report generation.

Contains the PipelineReport dataclass and the generate_pipeline_report function
that constructs reports from stage results.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, NotRequired, TypedDict

from infrastructure.core.runtime.checkpoint import StageResult
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


class _StageResultDict(TypedDict):
    """Dict representation of a pipeline stage result passed to generate_pipeline_report."""

    name: str
    exit_code: int
    duration: float
    error_message: NotRequired[str]
    timestamp: NotRequired[str]


@dataclass
class PipelineReport:
    """Complete pipeline execution report."""

    timestamp: str
    total_duration: float
    stages: list[StageResult]
    test_results: dict[str, Any] | None = None
    validation_results: dict[str, Any] | None = None
    performance_metrics: dict[str, Any] | None = None
    error_summary: dict[str, Any] | None = None
    output_statistics: dict[str, Any] | None = None


def generate_pipeline_report(
    stage_results: list[_StageResultDict],
    total_duration: float,
    repo_root: Path,
    *,
    test_results: dict[str, Any] | None = None,
    validation_results: dict[str, Any] | None = None,
    performance_metrics: dict[str, Any] | None = None,
    error_summary: dict[str, Any] | None = None,
    output_statistics: dict[str, Any] | None = None,
    project_name: str | None = None,
    project_dir: Path | None = None,
) -> PipelineReport:
    """Generate consolidated pipeline report from stage results and optional extras.

    The five optional ``dict[str, Any]`` keyword arguments (``test_results``,
    ``validation_results``, ``performance_metrics``, ``error_summary``,
    ``output_statistics``) are intentionally typed as loose dicts.  Each is a
    heterogeneous metrics blob produced by a different pipeline stage; the schemas
    differ per project and are not fixed at the infrastructure level.  Callers that
    need a fixed schema should define their own TypedDict and cast before passing.

    Args:
        stage_results: List of stage result dicts.
        total_duration: Total pipeline duration in seconds.
        repo_root: Repository root directory.
        project_name: Name of the project (for log-file enrichment).
        project_dir: Absolute path to the project directory. When given,
            overrides ``repo_root / 'projects' / project_name`` for log-file
            path resolution. Pass this when the project lives in a
            non-default directory such as ``projects_in_progress/``.
        Other keyword args pass through to PipelineReport fields.
    """
    stages = []
    for result in stage_results:
        status = "passed" if result.get("exit_code", 1) == 0 else "failed"
        stages.append(
            StageResult(
                name=result.get("name", "unknown"),
                exit_code=result.get("exit_code", 1),
                duration=result.get("duration", 0.0),
                status=status,
            )
        )

    # Enrich a copy of output_statistics with log file info (avoid mutating caller's dict)
    if project_name and output_statistics is not None:
        # Use explicit project_dir if given; fall back to default projects/ location.
        _log_base = (
            project_dir if project_dir is not None else repo_root / "projects" / project_name
        )
        log_file = _log_base / "output" / "logs" / "pipeline.log"
        output_statistics = {
            **output_statistics,
            "log_file": {
                "exists": log_file.exists(),
                "size": log_file.stat().st_size if log_file.exists() else 0,
                "path": str(log_file),
            },
        }

    return PipelineReport(
        timestamp=datetime.now().isoformat(),
        total_duration=total_duration,
        stages=stages,
        test_results=test_results,
        validation_results=validation_results,
        performance_metrics=performance_metrics,
        error_summary=error_summary,
        output_statistics=output_statistics,
    )
