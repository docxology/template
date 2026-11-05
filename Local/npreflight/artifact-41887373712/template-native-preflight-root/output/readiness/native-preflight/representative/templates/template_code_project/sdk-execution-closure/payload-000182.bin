"""Revalidate the frozen execution identity at launch, reuse, and completion."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from infrastructure.core.pipeline.execution_environment import effective_environment_identity
from infrastructure.core.pipeline.fingerprints import source_fingerprint
from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus
from infrastructure.core.pipeline.types import PipelineConfig, PipelineStageResult

if TYPE_CHECKING:
    from infrastructure.core.pipeline.plan import ExecutionPlan


def execution_guard_result(
    *,
    config: PipelineConfig,
    plan: ExecutionPlan | None,
    deadline: float,
    stage_num: int = 0,
    stage_name: str = "Execution contract",
    stage_key: str = "execution",
    completion: bool = False,
) -> PipelineStageResult | None:
    """Return a blocking result when custody or the finite run budget changed.

    A completed checkpoint prefix receives the same checks as a child launch.
    Identity failures refuse reuse without deleting the previous checkpoint.
    Environment values are never included in diagnostics.
    """
    source_changed = False
    environment_changed = False
    identity_error = ""
    if plan is not None:
        try:
            source_changed = (
                source_fingerprint(
                    config.repo_root, config.project_dir, definition_path=config.repo_root / plan.provenance
                )
                != plan.source_identity
            )
            environment_changed = (
                effective_environment_identity(config.repo_root, config.project_dir, mode=config.mode)
                != plan.environment_identity
            )
        except (OSError, ValueError) as exc:
            identity_error = f"Execution identity unavailable: {exc}"
    expired = bool(deadline and time.monotonic() >= deadline)
    if not (expired or source_changed or environment_changed or identity_error):
        return None
    phase = (
        "during execution"
        if completion and stage_num
        else "before completion validation"
        if completion
        else "after plan resolution"
    )
    diagnostic = (
        f"Run deadline expired {phase}"
        if expired
        else identity_error
        if identity_error
        else f"Consumed source changed {phase}; start a fresh run"
        if source_changed
        else f"Effective child environment changed {phase}; start a fresh run"
    )
    state = StageStatus.TIMED_OUT if expired else StageStatus.BLOCKED
    return PipelineStageResult(
        stage_num,
        stage_name,
        False,
        0.0,
        124 if expired else 75,
        diagnostic,
        stage_completed=False,
        stage_key=stage_key,
        outcome=StageOutcome(stage_key, state, child_exit_code=None, diagnostic=diagnostic),
    )


__all__ = ["execution_guard_result"]
