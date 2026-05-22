"""Real-data tests for ``infrastructure.core.pipeline.multi_project_parallel``.

These tests verify the contract of :func:`run_projects_in_parallel`:

* parallel speedup vs an equivalent serial run on the same workload,
* per-project log-file isolation (each project's stdout lands only in its
  own ``projects/<name>/output/logs/pipeline.log``),
* failure isolation (one failing project does not block the others).

No mocks are used. The tests build three synthetic projects on
``tmp_path`` and exercise the parallel module's pool-execution helper
``_execute_specs`` with a small, deterministic worker function. The
worker function is module-level (so it pickles for ``ProcessPoolExecutor``
on every supported start method) and reproduces the behaviour the real
pipeline worker relies on:

1. Redirect ``stdout``/``stderr`` to a per-project log file (the same
   isolation strategy used by ``_run_single_project_worker``).
2. Do a small amount of CPU work and a real ``time.sleep`` so the
   wall-clock comparison between parallel and serial is meaningful.
3. Optionally fail to exercise the failure-isolation contract.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Sequence

import pytest

from infrastructure.core.pipeline.multi_project_parallel import (
    ENV_MAX_WORKERS,
    ParallelRunResult,
    _execute_specs,
    _redirect_worker_streams,
    _resolve_max_workers,
    _WorkerSpec,
    run_projects_in_parallel,
)


# ---------------------------------------------------------------------------
# Synthetic project tree
# ---------------------------------------------------------------------------


def _scaffold_project(repo_root: Path, name: str) -> Path:
    """Create the directory layout required by ``ProjectInfo`` discovery.

    Each synthetic project ships ``src/__init__.py``, a smoke test in
    ``tests/test_smoke.py``, and a minimal ``manuscript/config.yaml`` so the
    discovery and worker code paths see a believable project tree.
    """
    project_dir = repo_root / "projects" / name
    (project_dir / "src").mkdir(parents=True)
    (project_dir / "tests").mkdir()
    (project_dir / "manuscript").mkdir()
    (project_dir / "output" / "logs").mkdir(parents=True)

    (project_dir / "src" / "__init__.py").write_text("")
    (project_dir / "tests" / "__init__.py").write_text("")
    (project_dir / "tests" / "test_smoke.py").write_text("def test_smoke() -> None:\n    assert True\n")
    (project_dir / "manuscript" / "config.yaml").write_text(
        f'paper:\n  title: "Synthetic project {name}"\n  version: "0.0.1"\n'
    )
    return project_dir


# ---------------------------------------------------------------------------
# Module-level test workers (must be picklable for ProcessPoolExecutor)
# ---------------------------------------------------------------------------


SLEEP_SECONDS = 2.0  # tuned to dominate process-spawn overhead on macOS spawn


def _sleepy_worker(spec: _WorkerSpec) -> tuple[str, bool, str]:
    """Pretend pipeline worker: redirect output, log, sleep, succeed."""
    log_path = Path(spec.log_file)
    with _redirect_worker_streams(log_path):
        print(f"[{spec.project_name}] start pid={os.getpid()}")
        time.sleep(SLEEP_SECONDS)
        print(f"[{spec.project_name}] done pid={os.getpid()}")
    return (spec.project_name, True, "")


_FAILING_PROJECT_TOKEN = "synthetic_proj_b"


def _maybe_failing_worker(spec: _WorkerSpec) -> tuple[str, bool, str]:
    """Same as ``_sleepy_worker`` but project ``synthetic_proj_b`` fails."""
    log_path = Path(spec.log_file)
    with _redirect_worker_streams(log_path):
        print(f"[{spec.project_name}] start pid={os.getpid()}")
        time.sleep(SLEEP_SECONDS / 3)
        if spec.project_name == _FAILING_PROJECT_TOKEN:
            print(f"[{spec.project_name}] simulated failure")
            return (spec.project_name, False, "synthetic stage failure")
        print(f"[{spec.project_name}] done pid={os.getpid()}")
    return (spec.project_name, True, "")


def _run_serial(specs: Sequence[_WorkerSpec]) -> tuple[float, list[str]]:
    """Sequential reference run for the speedup comparison."""
    start = time.time()
    succeeded: list[str] = []
    for spec in specs:
        name, ok, _ = _sleepy_worker(spec)
        if ok:
            succeeded.append(name)
    return time.time() - start, sorted(succeeded)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def synthetic_repo(tmp_path: Path) -> tuple[Path, list[_WorkerSpec]]:
    """Build three synthetic projects under ``tmp_path``.

    Returns ``(repo_root, specs)``. Specs target the parallel module's
    ``_execute_specs`` helper so tests do not depend on the heavy
    ``PipelineExecutor`` real-pipeline path.
    """
    names = ["synthetic_proj_a", "synthetic_proj_b", "synthetic_proj_c"]
    specs: list[_WorkerSpec] = []
    for name in names:
        project_dir = _scaffold_project(tmp_path, name)
        log_file = project_dir / "output" / "logs" / "pipeline.log"
        specs.append(
            _WorkerSpec(
                project_name=name,
                projects_dir="projects",
                repo_root=str(tmp_path),
                core_only=True,
                skip_llm=True,
                resume=False,
                log_file=str(log_file),
            )
        )
    return tmp_path, specs


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_resolve_max_workers_explicit_argument_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    """Explicit ``max_workers`` argument overrides env var and CPU count."""
    monkeypatch.setenv(ENV_MAX_WORKERS, "16")
    assert _resolve_max_workers(num_projects=5, override=2) == 2


def test_resolve_max_workers_env_var_used_when_no_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """``MULTI_PROJECT_MAX_WORKERS`` is honoured when no explicit override."""
    monkeypatch.setenv(ENV_MAX_WORKERS, "3")
    assert _resolve_max_workers(num_projects=10, override=None) == 3


def test_resolve_max_workers_invalid_env_var_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    """Garbage env values are ignored and the CPU-count default is used."""
    monkeypatch.setenv(ENV_MAX_WORKERS, "not-a-number")
    capped = _resolve_max_workers(num_projects=2, override=None)
    assert 1 <= capped <= 2  # never exceeds num_projects


def test_run_projects_in_parallel_empty_returns_zero_elapsed() -> None:
    """No projects → no work, no error, zero elapsed."""
    result = run_projects_in_parallel([], repo_root=Path("/tmp"))
    assert result == ParallelRunResult(succeeded=[], failed=[], elapsed_seconds=0.0)


def test_parallel_run_succeeds_and_beats_serial(
    synthetic_repo: tuple[Path, list[_WorkerSpec]],
) -> None:
    """Parallel run finishes faster than the sum of per-project sleeps."""
    _, specs = synthetic_repo

    serial_elapsed, serial_succeeded = _run_serial(specs)
    assert serial_succeeded == sorted(s.project_name for s in specs)

    # Re-create logs so the parallel run starts from clean files.
    for spec in specs:
        Path(spec.log_file).unlink(missing_ok=True)

    parallel = _execute_specs(specs, workers=3, worker_fn=_sleepy_worker)

    assert parallel.failed == []
    assert parallel.succeeded == sorted(s.project_name for s in specs)
    # Parallel must be meaningfully faster; allow generous slack for CI.
    assert parallel.elapsed_seconds < serial_elapsed * 0.9, (
        f"parallel={parallel.elapsed_seconds:.2f}s not < 0.9 * serial={serial_elapsed:.2f}s"
    )


def test_parallel_run_isolates_per_project_logs(
    synthetic_repo: tuple[Path, list[_WorkerSpec]],
) -> None:
    """Each project's log file contains only that project's output."""
    _, specs = synthetic_repo
    for spec in specs:
        Path(spec.log_file).unlink(missing_ok=True)

    result = _execute_specs(specs, workers=3, worker_fn=_sleepy_worker)
    assert result.failed == []

    log_contents: dict[str, str] = {}
    for spec in specs:
        log_contents[spec.project_name] = Path(spec.log_file).read_text()

    # Each log mentions its own project name and no other project's name.
    other_names = {spec.project_name for spec in specs}
    for spec in specs:
        own = spec.project_name
        text = log_contents[own]
        assert f"[{own}] start" in text, f"missing own start marker in {own} log"
        assert f"[{own}] done" in text, f"missing own done marker in {own} log"
        for other in other_names - {own}:
            assert f"[{other}]" not in text, f"log for '{own}' contained foreign project marker '[{other}]'"


def test_parallel_run_isolates_failures(
    synthetic_repo: tuple[Path, list[_WorkerSpec]],
) -> None:
    """One failing project still allows the other two to complete."""
    _, specs = synthetic_repo
    for spec in specs:
        Path(spec.log_file).unlink(missing_ok=True)

    result = _execute_specs(specs, workers=3, worker_fn=_maybe_failing_worker)

    assert result.failed == [_FAILING_PROJECT_TOKEN]
    assert result.succeeded == sorted(s.project_name for s in specs if s.project_name != _FAILING_PROJECT_TOKEN)
    # Failing project's log captured the failure marker.
    failing_log = next(s.log_file for s in specs if s.project_name == _FAILING_PROJECT_TOKEN)
    assert "simulated failure" in Path(failing_log).read_text()


def test_redirected_streams_restores_original_fds(tmp_path: Path) -> None:
    """The context manager restores the original FD 1/2 on exit.

    Without restoration, a single worker process could not be re-used for a
    second project — its second-task output would still go to the first
    project's log file.
    """
    log_a = tmp_path / "a.log"
    log_b = tmp_path / "b.log"

    with _redirect_worker_streams(log_a):
        print("python-a")
        os.write(1, b"hello-a\n")
    with _redirect_worker_streams(log_b):
        print("python-b")
        os.write(1, b"hello-b\n")

    assert "hello-a" in log_a.read_text()
    assert "python-a" in log_a.read_text()
    assert "hello-b" in log_b.read_text()
    assert "python-b" in log_b.read_text()
    assert "hello-b" not in log_a.read_text()
    assert "python-b" not in log_a.read_text()
    assert "hello-a" not in log_b.read_text()
    assert "python-a" not in log_b.read_text()
