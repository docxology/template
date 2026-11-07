"""Field encoding and typed decoding for source-bound pipeline workers."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any

from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus
from infrastructure.core.pipeline.types import PipelineConfig, PipelineStageResult

WORKER_SCHEMA = "template-multi-project-worker/2"

_CONFIG_FIELDS = (
    "project_name",
    "repo_root",
    "projects_dir",
    "clean",
    "skip_infra",
    "resume",
    "shared_infrastructure",
    "mode",
    "run_timeout_seconds",
    "pipeline_path",
)
_STAGE_RESULT_FIELDS = frozenset(field.name for field in fields(PipelineStageResult))
_STAGE_OUTCOME_FIELDS = frozenset(field.name for field in fields(StageOutcome))


def config_to_payload(config: PipelineConfig) -> dict[str, Any]:
    """Encode the exact config fields sent with a frozen execution plan."""
    payload = {name: getattr(config, name) for name in _CONFIG_FIELDS}
    payload["repo_root"] = str(config.repo_root)
    payload["pipeline_path"] = str(config.pipeline_path) if config.pipeline_path is not None else None
    return payload


def config_from_payload(payload: Any) -> PipelineConfig:
    """Admit the same field set used by the sender and restore config types."""
    if not isinstance(payload, dict) or set(payload) != set(_CONFIG_FIELDS):
        raise ValueError("Worker configuration requires the exact current storage role fields")
    config = dict(payload)
    config["repo_root"] = Path(config["repo_root"])
    config["pipeline_path"] = Path(config["pipeline_path"]) if config["pipeline_path"] is not None else None
    return PipelineConfig(**config)


def stage_results_to_payload(results: Iterable[PipelineStageResult]) -> list[dict[str, Any]]:
    """Encode full stage rows, including fields omitted from standalone outcomes."""
    return [asdict(row) for row in results]


def stage_result_from_payload(raw: dict[str, Any]) -> PipelineStageResult:
    """Restore types after the enclosing receipt or record has admitted the row."""
    row = dict(raw)
    outcome = dict(row["outcome"])
    outcome["status"] = StageStatus(outcome["status"])
    outcome["attempt_exit_codes"] = tuple(outcome["attempt_exit_codes"])
    row["outcome"] = StageOutcome(**outcome)
    row["lessons"] = tuple(row["lessons"])
    return PipelineStageResult(**row)


def results_from_payload(rows: Any) -> list[PipelineStageResult]:
    """Refuse malformed or contradictory stage evidence at the worker boundary."""
    if not isinstance(rows, list):
        raise ValueError("Worker stage results must be a list")
    result = []
    for raw in rows:
        if not isinstance(raw, dict) or set(raw) != _STAGE_RESULT_FIELDS or not isinstance(raw["outcome"], dict):
            raise ValueError("Worker must return complete typed stage evidence")
        for name in ("success", "hitl_pause", "stage_completed"):
            if type(raw[name]) is not bool:
                raise ValueError("Worker stage flags must be exact booleans")
        if (
            type(raw["stage_num"]) is not int
            or raw["stage_num"] < 0
            or type(raw["exit_code"]) is not int
            or isinstance(raw["duration"], bool)
            or not isinstance(raw["duration"], (int, float))
            or not math.isfinite(raw["duration"])
            or raw["duration"] < 0
        ):
            raise ValueError("Worker stage numeric evidence is invalid")
        if any(
            not isinstance(raw[name], str)
            for name in ("stage_name", "error_message", "exception_type", "stage_key", "input_digest", "output_digest")
        ):
            raise ValueError("Worker stage text evidence must be strings")
        if not isinstance(raw["lessons"], list) or any(not isinstance(item, str) for item in raw["lessons"]):
            raise ValueError("Worker stage lessons must be a string list")
        outcome = raw["outcome"]
        if set(outcome) != _STAGE_OUTCOME_FIELDS:
            raise ValueError("Worker stage outcome requires exact evidence fields")
        if any(not isinstance(outcome[name], str) for name in ("stage_key", "diagnostic", "reason", "status")):
            raise ValueError("Worker outcome text evidence must be strings")
        if not isinstance(outcome["attempt_exit_codes"], list):
            raise ValueError("Worker attempt codes must be a list")
        row = stage_result_from_payload(raw)
        assert row.outcome is not None
        if row.stage_key != row.outcome.stage_key or row.success != row.outcome.complete:
            raise ValueError("Worker stage and outcome identities or completion differ")
        result.append(row)
    return result
