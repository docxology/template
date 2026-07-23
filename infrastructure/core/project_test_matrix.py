"""Bounded, deterministic execution for isolated project test subprocesses."""

from __future__ import annotations

import os
import signal
import subprocess  # nosec B404 - fixed argv supplied by repository runners
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Mapping, Sequence


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

    try:
        process = subprocess.Popen(  # nosec B603 - command is built by callers
            list(task.command),
            cwd=str(task.cwd),
            env=dict(task.env),
            stdout=subprocess.PIPE if task.capture_output else None,
            stderr=subprocess.PIPE if task.capture_output else None,
            text=task.capture_output,
            start_new_session=os.name == "posix",
        )
        stdout, stderr = process.communicate(timeout=task.timeout_seconds)
        output = output_tail(stdout, stderr) if task.capture_output else ""
        return ProjectTestResult(
            task.index,
            task.project_name,
            int(process.returncode),
            output_tail=output,
            duration_seconds=round(monotonic() - started, 3),
        )
    except subprocess.TimeoutExpired as exc:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:  # pragma: no cover - Windows CI uses process.kill directly
            process.kill()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        # A descendant outside the process group can retain an inherited pipe;
        # never block the matrix while draining a timed-out task's output.
        for stream in (process.stdout, process.stderr):
            if stream is not None:
                stream.close()
        output = output_tail(exc.stdout, exc.stderr)
        return ProjectTestResult(
            task.index,
            task.project_name,
            124,
            timed_out=True,
            detail=f"timed out after {task.timeout_seconds} seconds: {exc}",
            output_tail=output,
            duration_seconds=round(monotonic() - started, 3),
        )
    except (OSError, subprocess.SubprocessError) as exc:
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
    if workers < 1:
        raise ValueError("project matrix workers must be positive")
    ordered_tasks = tuple(tasks)
    if not ordered_tasks:
        return ()
    if workers == 1 or len(ordered_tasks) == 1:
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
