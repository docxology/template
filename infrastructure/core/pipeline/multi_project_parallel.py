"""Finite multi-project scheduling with fresh subprocesses and frozen parent plans."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

from infrastructure.core.pipeline.execution_session import compose_run_deadline
from infrastructure.core.pipeline.multi_project_runtime import (
    execute_frozen_specs,
    freeze_project_plans,
    freeze_shared_plan,
    validate_budget,
)
from infrastructure.core.pipeline.multi_project_support import (
    SharedInfrastructureResult,
    aggregate_project_exit_code,
    run_shared_infrastructure,
)
from infrastructure.core.pipeline.outcomes import RunResult
from infrastructure.core.pipeline.types import PipelineStageResult
from infrastructure.core.worker_policy import ENV_MULTI_PROJECT_WORKERS, resolve_bounded_workers

if TYPE_CHECKING:
    from infrastructure.project.project_info import ProjectInfo


@dataclass(frozen=True)
class ParallelRunResult:
    """Exact project completion from isolated, supervised execution plans."""

    succeeded: list[str]
    failed: list[str]
    elapsed_seconds: float
    expected_projects: tuple[str, ...] = ()
    run_results: dict[str, RunResult] = field(default_factory=dict)
    shared_infrastructure_exit_code: int = 0
    project_results: dict[str, list[PipelineStageResult]] = field(default_factory=dict)
    infra_test_duration: float = 0.0
    shared_infrastructure_result: SharedInfrastructureResult | None = None

    @property
    def exit_code(self) -> int:
        return aggregate_project_exit_code(
            self.expected_projects,
            self.run_results,
            self.shared_infrastructure_exit_code,
            project_results=self.project_results,
            shared_result=self.shared_infrastructure_result,
        )


def _resolve_max_workers(num_projects: int, override: int | None) -> int:
    """Apply explicit count, environment policy, then the bounded CPU default."""
    if override is not None:
        if type(override) is not int or override <= 0:
            raise ValueError("multi-project worker count must be a positive integer")
        return min(override, max(num_projects, 1))
    return resolve_bounded_workers(env_name=ENV_MULTI_PROJECT_WORKERS, item_count=num_projects, invalid="fallback")


def run_projects_in_parallel(
    projects: Sequence[ProjectInfo | str],
    *,
    repo_root: Path,
    max_workers: int | None = None,
    mode: str = "core",
    run_infra_tests: bool = True,
    resume: bool = False,
    run_timeout_seconds: float = 14400.0,
    deadline_monotonic: float | None = None,
) -> ParallelRunResult:
    """Freeze plans before shared verification; queue and all workers share one deadline.

    Each invocation starts a fresh bytecode prefix and process; workers are never
    reused across project identities. Finite descendant cleanup may exceed an
    expired work deadline, and that run remains timed out.
    """
    started = time.monotonic()
    validate_budget(run_timeout_seconds)
    deadline = compose_run_deadline(run_timeout_seconds, deadline_monotonic)
    workers = _resolve_max_workers(len(projects), max_workers)
    specs = freeze_project_plans(projects, repo_root, mode=mode, resume=resume, timeout=run_timeout_seconds)
    expected = tuple(spec.plan.project for spec in specs)
    shared = freeze_shared_plan(specs) if run_infra_tests and specs else None
    shared_started = time.monotonic()
    shared_result = run_shared_infrastructure(shared, deadline=deadline) if shared is not None else None
    shared_exit = shared_result.exit_code if shared_result is not None else 0
    infra_duration = time.monotonic() - shared_started if shared is not None else 0.0
    if shared_exit:
        return ParallelRunResult(
            [],
            sorted(expected),
            time.monotonic() - started,
            expected,
            {},
            shared_exit,
            infra_test_duration=infra_duration,
            shared_infrastructure_result=shared_result,
        )
    rows, runs = execute_frozen_specs(specs, workers=workers, deadline=deadline)
    return ParallelRunResult(
        sorted(name for name, run in runs.items() if run.complete),
        sorted(name for name, run in runs.items() if not run.complete),
        time.monotonic() - started,
        expected,
        runs,
        project_results=rows,
        infra_test_duration=infra_duration,
        shared_infrastructure_result=shared_result,
    )


__all__ = ["ENV_MULTI_PROJECT_WORKERS", "ParallelRunResult", "run_projects_in_parallel"]
