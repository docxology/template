"""Pipeline report data model and report generation.

Contains the PipelineReport dataclass and the generate_pipeline_report function
that constructs reports from stage results.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, NotRequired, TypedDict

from infrastructure.core.runtime.checkpoint import StageResult
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus

logger = get_logger(__name__)


class _StageResultDict(TypedDict):
    """Dict representation of a pipeline stage result passed to generate_pipeline_report."""

    name: str
    exit_code: int
    duration: float
    error_message: NotRequired[str]
    timestamp: NotRequired[str]
    stage_key: NotRequired[str]
    outcome: NotRequired[dict[str, Any]]
    input_digest: NotRequired[str]
    output_digest: NotRequired[str]


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


def stage_is_complete(stage: StageResult) -> bool:
    """Classify rendered stage evidence without treating a child code as approval."""
    if not stage.completed:
        return False
    evidence = stage.context.get("outcome")
    if evidence is None:
        # Historical saved reports used the display label ``passed``.
        return stage.status in {"succeeded", "passed"} and stage.exit_code == 0
    try:
        fields = dict(evidence)
        fields["status"] = StageStatus(fields["status"])
        fields["attempt_exit_codes"] = tuple(fields.get("attempt_exit_codes", ()))
        outcome = StageOutcome(**fields)
    except (TypeError, ValueError, KeyError):
        return False
    return (
        stage.status == outcome.status.value
        and outcome.complete
        and report_stage_binding_valid(stage.context.get("stage_key"), stage.exit_code, outcome)
    )


def report_stage_binding_valid(stage_key: object, code: object, outcome: StageOutcome) -> bool:
    """Bind a displayed execution result to its identity and typed state."""
    if stage_key != outcome.stage_key or type(code) is not int:
        return False
    expected = {
        StageStatus.SUCCEEDED: 0,
        StageStatus.CACHED: 0,
        StageStatus.SKIPPED: 2,
        StageStatus.PAUSED: 75,
        StageStatus.BLOCKED: 75,
        StageStatus.REJECTED: 1,
        StageStatus.ABORTED: 1,
        StageStatus.TIMED_OUT: 124,
        StageStatus.INTERRUPTED: 130,
    }
    if outcome.status is StageStatus.FAILED:
        return code == 1 or (outcome.child_exit_code not in {None, 0} and code == outcome.child_exit_code)
    return code == expected[outcome.status]


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
            path resolution. Pass this when the project lives in a typed
            subfolder such as ``projects/working/``.
        Other keyword args pass through to PipelineReport fields.
    """
    stages = []
    for result in stage_results:
        evidence = result.get("outcome")
        if evidence is not None:
            outcome_fields = dict(evidence)
            outcome_fields["status"] = StageStatus(outcome_fields["status"])
            outcome_fields["attempt_exit_codes"] = tuple(outcome_fields.get("attempt_exit_codes", ()))
            outcome = StageOutcome(**outcome_fields)
            if not report_stage_binding_valid(
                result.get("stage_key", outcome.stage_key), result.get("exit_code", 1), outcome
            ):
                raise ValueError("Report stage identity or execution exit code contradicts its typed outcome")
        else:
            code = result.get("exit_code", 1)
            outcome = StageOutcome(
                result.get("stage_key", result.get("name", "unknown")),
                StageStatus.SUCCEEDED if code == 0 else StageStatus.FAILED,
                code,
                result.get("error_message", ""),
            )
        context = {
            "outcome": outcome.to_dict(),
            "stage_key": outcome.stage_key,
            "input_digest": result.get("input_digest", ""),
            "output_digest": result.get("output_digest", ""),
        }
        stages.append(
            StageResult(
                name=result.get("name", "unknown"),
                exit_code=result.get("exit_code", 1),
                duration=result.get("duration", 0.0),
                status=outcome.status.value,
                completed=outcome.complete,
                context=context,
            )
        )

    # Enrich a copy of output_statistics with log file info (avoid mutating caller's dict)
    if project_name and output_statistics is not None:
        # Use explicit project_dir if given; fall back to default projects/ location.
        _log_base = project_dir if project_dir is not None else repo_root / "projects" / project_name
        log_file = _log_base / "output" / "logs" / "pipeline.log"
        output_statistics = {
            **output_statistics,
            "log_file": {
                "exists": log_file.exists(),
                "size": log_file.stat().st_size if log_file.exists() else 0,
                "path": _release_safe_log_path(log_file, _log_base),
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


def _release_safe_log_path(log_file: Path, project_dir: Path) -> str:
    """Serialize project log paths without leaking the local checkout root."""
    try:
        return str(log_file.relative_to(project_dir))
    except ValueError:
        return log_file.name
