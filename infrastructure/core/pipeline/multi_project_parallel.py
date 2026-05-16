"""Bounded-parallel multi-project pipeline orchestration.

This module mirrors :mod:`infrastructure.core.pipeline.multi_project` but executes
each project's pipeline in a **separate worker process** via
:class:`concurrent.futures.ProcessPoolExecutor`. The serial path in
``multi_project.py`` remains the default for ``execute_multi_project.py``;
this module is opt-in via the ``--parallel`` CLI flag.

Design constraints
------------------
* **Per-project log isolation.** Each worker redirects its OS-level
  ``stdout`` and ``stderr`` file descriptors to
  ``projects/<name>/output/logs/pipeline.log`` *before* importing or
  instantiating any pipeline component. This means:

  - The parent process never receives interleaved stage output from
    multiple projects.
  - Subprocesses spawned by individual stages (pytest, latex, etc.)
    inherit the redirected FDs, so their output also lands in the
    project-local log file.

* **Bounded parallelism.** ``max_workers`` defaults to
  ``min(len(projects), os.cpu_count() or 1)``. The
  ``MULTI_PROJECT_MAX_WORKERS`` environment variable, when set to a
  positive integer, overrides the default.

* **Failure isolation.** A worker exception is captured into
  :class:`ParallelRunResult.failed`; remaining projects continue
  to completion.

* **Thin orchestrator.** All real work is delegated to
  :class:`infrastructure.core.pipeline.executor.PipelineExecutor`, the
  same executor that drives the serial path.
"""

import os
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Sequence

from infrastructure.core.logging.utils import get_logger

if TYPE_CHECKING:
    from infrastructure.project.project_info import ProjectInfo

logger = get_logger(__name__)

ENV_MAX_WORKERS = "MULTI_PROJECT_MAX_WORKERS"


@dataclass(frozen=True)
class ParallelRunResult:
    """Outcome of :func:`run_projects_in_parallel`.

    Attributes:
        succeeded: Qualified project names that completed every stage cleanly.
        failed: Qualified project names where at least one stage failed or the
            worker raised an exception.
        elapsed_seconds: Wall-clock duration of the parallel run.
    """

    succeeded: list[str]
    failed: list[str]
    elapsed_seconds: float


@dataclass(frozen=True)
class _WorkerSpec:
    """Picklable inputs for a single worker invocation.

    Kept separate from :class:`infrastructure.project.project_info.ProjectInfo`
    so workers do not need to re-resolve project metadata or carry mutable
    state across the process boundary.
    """

    project_name: str
    projects_dir: str
    repo_root: str
    core_only: bool
    skip_llm: bool
    resume: bool
    log_file: str


def _projects_dir_for(repo_root: Path, project_path: Path) -> str:
    """Return the repo-relative top-level pool for ``project_path``."""
    try:
        rel = project_path.resolve().relative_to(repo_root.resolve()).parts
    except ValueError:
        return "projects"
    return rel[0] if rel else "projects"


class _RedirectedStreams:
    """Context manager that redirects FD 1/2 to ``log_file`` and restores them.

    Uses :func:`os.dup2` on the underlying file descriptors so any subprocess
    (pytest, pdflatex, ollama, etc.) inherits the same redirection. The
    *original* stdout/stderr FDs are duplicated before the redirect and
    restored on ``__exit__`` so a single worker process can be re-used for
    multiple projects without leaking the previous project's log file.
    """

    def __init__(self, log_file: Path) -> None:
        self._log_file = log_file
        self._saved_stdout: int | None = None
        self._saved_stderr: int | None = None

    def __enter__(self) -> "_RedirectedStreams":
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        # Flush any pending Python-level buffered output before swapping FDs.
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except (OSError, ValueError):
            pass

        self._saved_stdout = os.dup(1)
        self._saved_stderr = os.dup(2)

        fd = os.open(str(self._log_file), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.dup2(fd, 1)
            os.dup2(fd, 2)
        finally:
            os.close(fd)
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except (OSError, ValueError):
            pass
        if self._saved_stdout is not None:
            os.dup2(self._saved_stdout, 1)
            os.close(self._saved_stdout)
            self._saved_stdout = None
        if self._saved_stderr is not None:
            os.dup2(self._saved_stderr, 2)
            os.close(self._saved_stderr)
            self._saved_stderr = None


def _redirect_worker_streams(log_file: Path) -> _RedirectedStreams:
    """Return a context manager that pins this process's stdout/stderr to ``log_file``.

    Use as ``with _redirect_worker_streams(path): ...``. Subprocesses
    spawned inside the ``with`` block inherit the redirection.
    """
    return _RedirectedStreams(log_file)


def _run_single_project_worker(spec: _WorkerSpec) -> tuple[str, bool, str]:
    """Worker entry point: execute one project's pipeline.

    Runs in a child :class:`ProcessPoolExecutor` worker. Must be a module-level
    function so it is picklable on every supported start method.

    Args:
        spec: All inputs needed to construct a :class:`PipelineConfig` and
            invoke :class:`PipelineExecutor`.

    Returns:
        ``(project_name, success, error_message)`` tuple. ``success`` is
        ``True`` only when every stage of the pipeline reported success.
        ``error_message`` is empty on success.
    """
    log_path = Path(spec.log_file)
    with _redirect_worker_streams(log_path):
        # Imports happen inside the worker so each child gets a fresh
        # module state; this avoids a parent-side import cache leaking
        # partially configured loggers into the children.
        from infrastructure.core.pipeline.executor import PipelineExecutor
        from infrastructure.core.pipeline.types import PipelineConfig

        try:
            config = PipelineConfig(
                project_name=spec.project_name,
                repo_root=Path(spec.repo_root),
                projects_dir=spec.projects_dir,
                skip_infra=True,  # Infra tests run once at the orchestrator level.
                skip_llm=spec.skip_llm or spec.core_only,
                resume=spec.resume,
                total_stages=8 if (spec.core_only or spec.skip_llm) else 10,
            )
            executor = PipelineExecutor(config)
            method = executor.execute_core_pipeline if spec.core_only else executor.execute_full_pipeline
            results = method()
            success = bool(results) and all(r.success for r in results)
            return (spec.project_name, success, "" if success else "one or more stages failed")
        except Exception as exc:  # noqa: BLE001 — worker boundary
            # Surface a compact traceback in the per-project log file.
            traceback.print_exc()
            return (spec.project_name, False, f"{type(exc).__name__}: {exc}")


def _resolve_max_workers(num_projects: int, override: int | None) -> int:
    """Compute the bounded worker count.

    Precedence: explicit ``override`` argument → ``MULTI_PROJECT_MAX_WORKERS``
    env var → ``min(num_projects, os.cpu_count() or 1)``. The result is
    always at least ``1`` and never exceeds ``num_projects``.
    """
    if override is not None and override > 0:
        return min(override, max(num_projects, 1))

    env_value = os.environ.get(ENV_MAX_WORKERS, "").strip()
    if env_value:
        try:
            parsed = int(env_value)
            if parsed > 0:
                return min(parsed, max(num_projects, 1))
        except ValueError:
            logger.warning(
                "Ignoring non-integer %s=%r; falling back to default.",
                ENV_MAX_WORKERS,
                env_value,
            )

    cpu = os.cpu_count() or 1
    return max(1, min(num_projects, cpu))


def _spec_for(
    project: "ProjectInfo | str",
    repo_root: Path,
    core_only: bool,
    skip_llm: bool,
    resume: bool,
) -> _WorkerSpec:
    """Build a :class:`_WorkerSpec` from either a ``ProjectInfo`` or a name."""
    if isinstance(project, str):
        project_name = project
        projects_dir = "projects"
        project_path = repo_root / projects_dir / project_name
    else:
        project_name = project.qualified_name
        projects_dir = _projects_dir_for(repo_root, project.path)
        project_path = project.path

    log_file = project_path / "output" / "logs" / "pipeline.log"
    return _WorkerSpec(
        project_name=project_name,
        projects_dir=projects_dir,
        repo_root=str(repo_root),
        core_only=core_only,
        skip_llm=skip_llm,
        resume=resume,
        log_file=str(log_file),
    )


def run_projects_in_parallel(
    projects: Sequence["ProjectInfo | str"],
    *,
    repo_root: Path,
    max_workers: int | None = None,
    core_only: bool = False,
    skip_llm: bool = False,
    resume: bool = False,
) -> ParallelRunResult:
    """Run each project's pipeline in a worker process.

    Args:
        projects: Discovered projects (or qualified names). Order is preserved
            in the returned ``succeeded``/``failed`` lists by sorting.
        repo_root: Absolute path to the repository root.
        max_workers: Optional override for the worker pool size. When ``None``,
            defaults to ``min(len(projects), os.cpu_count() or 1)``. The
            ``MULTI_PROJECT_MAX_WORKERS`` env var overrides the default but is
            itself overridden by an explicit ``max_workers`` argument.
        core_only: Forward ``--core-only`` to each worker (skip LLM stages).
        skip_llm: Skip the LLM stages even when ``core_only`` is False.
        resume: Forward ``--resume`` to each worker.

    Returns:
        :class:`ParallelRunResult` with successful/failed project names and
        wall-clock elapsed seconds.
    """
    if not projects:
        logger.warning("run_projects_in_parallel called with no projects")
        return ParallelRunResult(succeeded=[], failed=[], elapsed_seconds=0.0)

    workers = _resolve_max_workers(len(projects), max_workers)
    logger.info(
        "Parallel multi-project run: %d project(s), %d worker(s), core_only=%s, skip_llm=%s",
        len(projects),
        workers,
        core_only,
        skip_llm,
    )

    specs = [_spec_for(p, repo_root, core_only=core_only, skip_llm=skip_llm, resume=resume) for p in projects]
    return _execute_specs(specs, workers=workers, worker_fn=_run_single_project_worker)


def _execute_specs(
    specs: Sequence[_WorkerSpec],
    *,
    workers: int,
    worker_fn: "Callable[[_WorkerSpec], tuple[str, bool, str]]",
) -> ParallelRunResult:
    """Submit ``specs`` to a pool and aggregate results.

    Factored out of :func:`run_projects_in_parallel` so tests can substitute
    a deterministic, lightweight ``worker_fn`` without spinning up a real
    pipeline executor.
    """
    succeeded: list[str] = []
    failed: list[str] = []

    start = time.time()
    # Worker processes save and restore FD 1/2 around each task (see
    # ``_redirect_worker_streams``) so re-using a worker for a second
    # project does not leak the previous project's log redirection.
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(worker_fn, spec): spec.project_name for spec in specs}
        for future in as_completed(futures):
            project_name = futures[future]
            try:
                name, success, err = future.result()
            except Exception as exc:  # noqa: BLE001 — boundary catch
                logger.error("Worker for project '%s' raised: %s", project_name, exc, exc_info=True)
                failed.append(project_name)
                continue
            if success:
                logger.info("✅ Parallel project '%s' completed successfully", name)
                succeeded.append(name)
            else:
                logger.error("❌ Parallel project '%s' failed: %s", name, err)
                failed.append(name)
    elapsed = time.time() - start

    succeeded.sort()
    failed.sort()
    logger.info(
        "Parallel multi-project run finished in %.2fs (succeeded=%d, failed=%d)",
        elapsed,
        len(succeeded),
        len(failed),
    )
    return ParallelRunResult(succeeded=succeeded, failed=failed, elapsed_seconds=elapsed)


__all__ = [
    "ENV_MAX_WORKERS",
    "ParallelRunResult",
    "run_projects_in_parallel",
]
