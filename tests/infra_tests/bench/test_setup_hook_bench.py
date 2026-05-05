"""Performance benchmarks for :mod:`infrastructure.project.setup_hook`.

Four real-filesystem, real-subprocess benches:

* **Bench A** — ``find_setup_hook`` on a project with **no** hook (path miss).
* **Bench B** — ``find_setup_hook`` on a project with a ``setup_hook.py``
  (path hit).
* **Bench C** — ``run_project_setup_hook`` on a project with no hook
  (no-op fast path; should be near-instant).
* **Bench D** — ``run_project_setup_hook`` invoking a trivial Python hook
  that exits 0 (real subprocess; dominated by interpreter startup).

All benches are marked ``@pytest.mark.bench`` and use the
``benchmark`` fixture from ``pytest-benchmark``. No mocks, no patches.

Run with::

    uv run pytest tests/infra_tests/bench/test_setup_hook_bench.py \
        -m bench --benchmark-only --benchmark-min-rounds=3 --timeout=180
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.project.setup_hook import (
    find_setup_hook,
    run_project_setup_hook,
)


def _make_project_no_hook(root: Path) -> Path:
    """Build a minimal ``projects/<name>`` tree with no hook."""
    project = root / "noop_project"
    (project / "scripts").mkdir(parents=True)
    return project


def _make_project_with_py_hook(root: Path) -> Path:
    """Build a minimal ``projects/<name>`` tree with a trivial Python hook."""
    project = root / "hook_project"
    scripts = project / "scripts"
    scripts.mkdir(parents=True)
    hook = scripts / "setup_hook.py"
    hook.write_text(
        "#!/usr/bin/env python3\n"
        '"""Trivial no-op setup hook used by the bench suite."""\n'
        "import sys\n"
        "sys.exit(0)\n",
        encoding="utf-8",
    )
    return project


@pytest.mark.bench
def test_bench_find_setup_hook_no_hook(benchmark: object, tmp_path: Path) -> None:
    """Bench A: ``find_setup_hook`` on a hook-less project (path miss)."""
    project = _make_project_no_hook(tmp_path)

    def call() -> Path | None:
        return find_setup_hook(project)

    result = benchmark(call)  # type: ignore[operator]
    assert result is None


@pytest.mark.bench
def test_bench_find_setup_hook_with_hook(benchmark: object, tmp_path: Path) -> None:
    """Bench B: ``find_setup_hook`` on a project with a Python hook (path hit)."""
    project = _make_project_with_py_hook(tmp_path)

    def call() -> Path | None:
        return find_setup_hook(project)

    result = benchmark(call)  # type: ignore[operator]
    assert result is not None
    assert result.name == "setup_hook.py"


@pytest.mark.bench
def test_bench_run_project_setup_hook_noop(benchmark: object, tmp_path: Path) -> None:
    """Bench C: ``run_project_setup_hook`` no-op fast path (no hook present)."""
    project = _make_project_no_hook(tmp_path)

    def call() -> bool:
        return run_project_setup_hook(project)

    ok = benchmark(call)  # type: ignore[operator]
    assert ok is True


@pytest.mark.bench
def test_bench_run_project_setup_hook_trivial(benchmark: object, tmp_path: Path) -> None:
    """Bench D: ``run_project_setup_hook`` actually launching a trivial hook.

    This bench is dominated by Python interpreter startup time (real
    ``subprocess.run``); it gives a realistic ceiling for what one
    project-setup-hook invocation costs at pipeline startup.
    """
    project = _make_project_with_py_hook(tmp_path)

    # Use fewer rounds — each round forks a real Python interpreter.
    def call() -> bool:
        return run_project_setup_hook(project)

    ok = benchmark.pedantic(call, rounds=3, iterations=1, warmup_rounds=1)  # type: ignore[attr-defined]
    assert ok is True
