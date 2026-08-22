"""Bounded, deterministic execution for isolated project test subprocesses."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Mapping, Sequence

from infrastructure.core.worker_policy import clamp_worker_count
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy
from infrastructure.core.pytest_orchestration import parse_test_summary_count


@dataclass(frozen=True)
class ProjectTestTask:
    """One isolated subprocess in a project test matrix."""

    index: int
    project_name: str
    command: tuple[str, ...]
    cwd: Path
    env: Mapping[str, str]
    timeout_seconds: int
    capture_output: bool = False


@dataclass(frozen=True)
class ProjectTestResult:
    """Stable result returned for one matrix task."""

    index: int
    project_name: str
    returncode: int
    timed_out: bool = False
    detail: str = ""
    output_tail: str = ""
    duration_seconds: float = 0.0
    collection_count: int | None = None


def _run_task(task: ProjectTestTask) -> ProjectTestResult:
    """Run one task and convert process failures into structured results."""
    started = monotonic()

    def output_tail(stdout: str | bytes | None, stderr: str | bytes | None) -> str:
        """Combine stdout and stderr into a bounded diagnostic tail."""

        def as_text(value: str | bytes | None) -> str:
            """Decode bytes to text, returning empty string for None."""
            if value is None:
                return ""
            return value.decode(errors="replace") if isinstance(value, bytes) else value

        return f"{as_text(stdout)}\n{as_text(stderr)}".strip()[-4000:]

    policy = SubprocessPolicy(
        policy_id=f"project-test:{task.project_name}",
        source_path="infrastructure/core/project_test_matrix.py",
        timeout_seconds=task.timeout_seconds,
        capture_output=task.capture_output,
        credential_free=True,
    )
    try:
        result = run_with_policy(task.command, cwd=task.cwd, env=dict(task.env), policy=policy)
        output = output_tail(result.stdout, result.stderr) if task.capture_output else ""
        collection_count = parse_test_summary_count(output) if output else None
        return ProjectTestResult(
            task.index,
            task.project_name,
            124 if result.timed_out else result.returncode,
            timed_out=result.timed_out,
            detail=result.command_error,
            output_tail=output,
            duration_seconds=round(monotonic() - started, 3),
            collection_count=collection_count,
        )
    except (OSError, ValueError) as exc:
        return ProjectTestResult(
            task.index,
            task.project_name,
            1,
            detail=str(exc),
            duration_seconds=round(monotonic() - started, 3),
        )


def run_project_test_matrix(
    tasks: Sequence[ProjectTestTask],
    *,
    workers: int = 1,
) -> tuple[ProjectTestResult, ...]:
    """Run project subprocesses with bounded concurrency and stable ordering.

    Completion order is deliberately discarded. Results are returned in the
    caller's canonical roster order, while a failed or timed-out task never
    prevents independent tasks from finishing.
    """
    ordered_tasks = tuple(tasks)
    if not ordered_tasks:
        return ()
    if workers < 1:
        raise ValueError("project matrix workers must be positive")
    seen_indices: set[int] = set()
    for task in ordered_tasks:
        if task.index in seen_indices:
            raise ValueError(f"duplicate project matrix task index: {task.index}")
        seen_indices.add(task.index)
    workers = clamp_worker_count(workers, len(ordered_tasks))
    if workers == 1:
        return tuple(_run_task(task) for task in ordered_tasks)

    results: dict[int, ProjectTestResult] = {}
    with ThreadPoolExecutor(max_workers=min(workers, len(ordered_tasks))) as executor:
        futures = {executor.submit(_run_task, task): task for task in ordered_tasks}
        for future in as_completed(futures):
            task = futures[future]
            try:
                results[task.index] = future.result()
            except Exception as exc:  # pragma: no cover - defensive executor boundary
                results[task.index] = ProjectTestResult(task.index, task.project_name, 1, detail=str(exc))
    return tuple(results[task.index] for task in ordered_tasks)


__all__ = ["ProjectTestResult", "ProjectTestTask", "run_project_test_matrix"]
