"""Targeted execution through the same resolved contract as complete runs."""

from __future__ import annotations

from pathlib import Path
import time

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.plan import compile_execution_plan
from infrastructure.core.pipeline.types import PipelineConfig

logger = get_logger(__name__)


def execute_single_stage(
    stage: str,
    project_name: str,
    repo_root: Path,
    *,
    pipeline_path: Path | str | None = None,
    mode: str = "core",
    run_timeout_seconds: float = 14400.0,
) -> int:
    """Execute exactly one stage after validating its prerequisite artifacts."""
    try:
        config = PipelineConfig(
            project_name,
            repo_root,
            clean=False,
            mode=mode,
            run_timeout_seconds=run_timeout_seconds,
            pipeline_path=Path(pipeline_path) if pipeline_path else None,
        )
        deadline = time.monotonic() + config.run_timeout_seconds
        plan = compile_execution_plan(config, skip_clean=True, target_stage=stage)
        if time.monotonic() >= deadline:
            raise TimeoutError("Stage deadline expired during plan preflight")
        executor = PipelineExecutor(config)
        results = executor.execute_plan(plan, deadline_monotonic=deadline)
        return executor.run_result(results).exit_code
    except ValueError as exc:
        logger.error("Invalid stage invocation: %s", exc)
        return 2
    except TimeoutError as exc:
        logger.error("Stage lock deadline expired: %s", exc)
        return 124


__all__ = ["execute_single_stage"]
