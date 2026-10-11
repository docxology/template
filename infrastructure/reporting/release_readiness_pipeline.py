"""Validate fresh completion against the actual source-owned execution plan."""

from __future__ import annotations

from pathlib import Path
import math
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.core.pipeline.outcomes import RunResult, StageOutcome, StageStatus
from infrastructure.core.pipeline.plan import compile_execution_plan
from infrastructure.core.pipeline.types import PipelineConfig


def validate_pipeline(scope: str, details: dict[str, Any], root: Path) -> None:
    """An arbitrary successful subset cannot stand in for the full core plan.

    This acceptance requires fresh succeeded outcomes. Valid cache/checkpoint
    reuse is a runtime capability, but does not establish fresh release testing.
    """
    if details.get("mode") != "core" or not isinstance(details.get("run_id"), str) or not details["run_id"]:
        raise ValueError("pipeline acceptance must identify a fresh core run")
    selection = details.get("selection")
    if (
        not isinstance(selection, dict)
        or set(selection) != {"skip_clean", "skip_infra"}
        or any(type(value) is not bool for value in selection.values())
    ):
        raise ValueError("pipeline selection must explicitly declare cleanup/shared verification")
    # The root runtime gate owns shared infrastructure verification. Project
    # workers can omit it only through this explicit compiled selection.
    config = PipelineConfig(
        scope, root, mode="core", clean=not selection["skip_clean"], skip_infra=selection["skip_infra"]
    )
    recorded = details.get("plan")
    if not isinstance(recorded, dict):
        raise ValueError("pipeline execution plan is missing")
    timeout = recorded.get("run_timeout_seconds")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("pipeline budget is invalid")
    config.run_timeout_seconds = timeout
    plan = compile_execution_plan(config)
    if canonical_digest(recorded) != plan.digest or details.get("plan_digest") != plan.digest:
        raise ValueError("pipeline plan differs from the current complete source contract")
    if details.get("expected_stage_keys") != list(plan.expected_stage_keys):
        raise ValueError("pipeline expected stages differ from the actual compiled plan")
    rows = details.get("outcomes")
    if not isinstance(rows, list):
        raise ValueError("pipeline outcomes must be a list")
    outcomes: list[StageOutcome] = []
    for row in rows:
        if not isinstance(row, dict) or row.get("status") != StageStatus.SUCCEEDED.value:
            raise ValueError("required release stages must have fresh succeeded outcomes")
        codes = row.get("attempt_exit_codes", [])
        if not isinstance(codes, list):
            raise ValueError("attempt evidence must be an array")
        outcomes.append(
            StageOutcome(
                row.get("stage_key", ""),
                StageStatus.SUCCEEDED,
                row.get("child_exit_code", -1),
                attempt_count=row.get("attempt_count", 1),
                attempt_exit_codes=tuple(codes),
            )
        )
    result = RunResult(plan.expected_stage_keys, tuple(outcomes))
    if not result.complete or result.exit_code != 0:
        raise ValueError("pipeline did not complete every expected stage exactly once in order")
