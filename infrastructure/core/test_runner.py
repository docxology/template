"""Per-project pytest runner with combined coverage gate.

Two ``projects/<name>/tests/conftest.py`` files cannot live in the same
``pytest`` process: pytest registers conftest plugins by directory-derived
name, so a second conftest with the same basename collides with the first
("plugin already registered"). The historical workaround in
``.github/workflows/ci.yml`` was an open-coded bash loop that invoked
``pytest`` once per ``projects/<name>/tests/`` directory, accumulating
coverage with ``--cov-append`` and gating the combined coverage with
``coverage report --fail-under=<N>`` at the end.

This module lifts that loop into a single Python entry point so CI and
local runs share one implementation:

    from infrastructure.core.test_runner import run_per_project_pytest
    exit_code = run_per_project_pytest(repo_root)

The runner:

* discovers ``projects/<name>/tests/`` directories via
  :func:`infrastructure.project.discovery.discover_projects` (or accepts
  an explicit list),
* skips projects listed in ``skip_projects`` (default: ``("fep_lean",)``,
  which has its own dedicated CI job),
* invokes a real ``pytest`` subprocess **per project** so conftest
  plugins never collide,
* uses ``--cov=projects/<name>/src`` per project and ``--cov-append``
  for every project after the first,
* honours ``COVERAGE_FILE`` from the environment (or sets it from
  ``coverage_file``) so all per-project runs write to the same combined
  coverage data file,
* runs ``coverage report --fail-under=<fail_under>`` at the end and
  returns ``0`` only when **every** per-project pytest exited cleanly
  **and** the combined coverage gate passes.

The runner is a thin orchestrator: business logic (fail-under threshold,
skip list, marker expression) is configurable, and all subprocess work
happens via real ``subprocess.run`` calls — no mocking.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404
from pathlib import Path
from typing import Sequence

from infrastructure.core.logging.utils import (
    get_logger,
    log_header,
    log_substep,
    log_success,
)
from infrastructure.core.runtime._python_env import get_python_command
from infrastructure.core.pytest_marker_exprs import build_pytest_marker_expression
from infrastructure.project.discovery import discover_projects

logger = get_logger(__name__)

DEFAULT_SKIP_PROJECTS: tuple[str, ...] = ("fep_lean",)
DEFAULT_COVERAGE_FILE: str = ".coverage.project"
DEFAULT_FAIL_UNDER: int = 90
_DEFAULT_MARKER = build_pytest_marker_expression(
    skip_requires_ollama=True,
    skip_slow=True,
    skip_bench=True,
)
if _DEFAULT_MARKER is None:  # pragma: no cover - defensive
    raise RuntimeError("default pytest marker expression must not be empty")
DEFAULT_MARKER_EXPR: str = _DEFAULT_MARKER
DEFAULT_TIMEOUT: int = 120


def _discover_project_test_dirs(
    repo_root: Path,
    projects: Sequence[str] | None,
    skip_projects: Sequence[str],
) -> list[tuple[str, Path]]:
    """Return ``(project_name, tests_dir)`` pairs for every runnable project.

    When ``projects`` is ``None`` the list is built from
    :func:`discover_projects`; otherwise the explicit list is used and any
    name lacking a ``projects/<name>/tests/`` directory is silently dropped
    after a warning is logged.
    """
    pairs: list[tuple[str, Path]] = []
    skip_set = set(skip_projects)

    if projects is None:
        for info in discover_projects(repo_root):
            tests_dir = info.path / "tests"
            if not tests_dir.is_dir():
                continue
            if info.name in skip_set:
                logger.info("Skipping project '%s' (in skip_projects)", info.name)
                continue
            pairs.append((info.name, tests_dir))
    else:
        for name in projects:
            tests_dir = repo_root / "projects" / name / "tests"
            if not tests_dir.is_dir():
                logger.warning(
                    "Project '%s' has no tests directory at %s; skipping",
                    name,
                    tests_dir,
                )
                continue
            if name in skip_set:
                logger.info("Skipping project '%s' (in skip_projects)", name)
                continue
            pairs.append((name, tests_dir))

    return pairs


def _build_pytest_cmd(
    project_name: str,
    tests_dir: Path,
    *,
    repo_root: Path,
    is_first: bool,
    marker_expr: str | None,
    timeout: int,
) -> list[str]:
    """Build the per-project ``pytest`` command line.

    The first project in the loop runs without ``--cov-append`` so it can
    initialize a fresh coverage data file; every subsequent project adds
    ``--cov-append`` so traces accumulate.
    """
    src_dir = repo_root / "projects" / project_name / "src"
    cov_target = f"projects/{project_name}/src" if src_dir.is_dir() else f"projects/{project_name}"

    cmd = get_python_command() + [
        "-m",
        "pytest",
        str(tests_dir),
        f"--cov={cov_target}",
        "--cov-report=term-missing",
        f"--timeout={timeout}",
        "--durations=10",
    ]
    if marker_expr:
        cmd.extend(["-m", marker_expr])
    if not is_first:
        cmd.append("--cov-append")
    return cmd


def _resolve_coverage_file(coverage_file: str) -> str:
    """Return the COVERAGE_FILE value, honouring the env var when set."""
    env_value = os.environ.get("COVERAGE_FILE")
    if env_value:
        return env_value
    return coverage_file


def _make_subprocess_env(coverage_file_value: str, repo_root: Path) -> dict[str, str]:
    """Build a subprocess env with COVERAGE_FILE pinned and PYTHONPATH set."""
    env = os.environ.copy()
    env["COVERAGE_FILE"] = coverage_file_value
    existing_pp = env.get("PYTHONPATH", "")
    pp_parts = [str(repo_root)]
    if existing_pp:
        pp_parts.append(existing_pp)
    env["PYTHONPATH"] = os.pathsep.join(pp_parts)
    return env


def _run_pytest_for_project(
    cmd: list[str],
    repo_root: Path,
    env: dict[str, str],
    project_name: str,
) -> int:
    """Execute pytest for one project and return its exit code."""
    log_substep(f"Running pytest for project '{project_name}'", logger)
    logger.info("    cmd: %s", " ".join(cmd))
    try:
        completed = subprocess.run(  # nosec B603
            cmd,
            cwd=str(repo_root),
            env=env,
            check=False,
        )
        return int(completed.returncode)
    except (OSError, subprocess.SubprocessError) as exc:
        logger.error("pytest invocation failed for '%s': %s", project_name, exc)
        return 1


def _run_combined_coverage_gate(
    repo_root: Path,
    env: dict[str, str],
    fail_under: int,
) -> int:
    """Run ``coverage report --fail-under=<N>`` and return its exit code."""
    log_substep(f"Running combined coverage gate (--fail-under={fail_under})", logger)
    coverage_exe = shutil.which("coverage")
    if coverage_exe:
        cmd = [coverage_exe, "report", f"--fail-under={fail_under}"]
    else:
        cmd = get_python_command() + ["-m", "coverage", "report", f"--fail-under={fail_under}"]
    try:
        completed = subprocess.run(  # nosec B603
            cmd,
            cwd=str(repo_root),
            env=env,
            check=False,
        )
        return int(completed.returncode)
    except (OSError, subprocess.SubprocessError) as exc:
        logger.error("coverage gate invocation failed: %s", exc)
        return 1


def run_per_project_pytest(
    repo_root: Path,
    *,
    projects: Sequence[str] | None = None,
    skip_projects: Sequence[str] = DEFAULT_SKIP_PROJECTS,
    coverage_file: str = DEFAULT_COVERAGE_FILE,
    fail_under: int = DEFAULT_FAIL_UNDER,
    marker_expr: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> int:
    """Run pytest once per project and gate combined coverage.

    Args:
        repo_root: Repository root directory containing ``projects/``.
        projects: Optional explicit project names to run. When ``None`` the
            project list is derived from
            :func:`infrastructure.project.discovery.discover_projects`.
        skip_projects: Project names to skip even if discovered. Defaults
            to ``("fep_lean",)`` because that project has its own
            dedicated CI job (lake build + Open Gauss).
        coverage_file: Path to the combined coverage data file. Used only
            when the ``COVERAGE_FILE`` environment variable is unset.
            Default: ``".coverage.project"``.
        fail_under: Minimum combined coverage percentage required by the
            final ``coverage report`` gate.
        marker_expr: ``pytest -m`` expression. ``None`` uses
            :data:`DEFAULT_MARKER_EXPR` (``not requires_ollama and not slow and
            not bench``). Pass ``""`` to omit ``-m`` (collect all markers).
        timeout: Per-test ``--timeout`` value forwarded to pytest.

    Returns:
        ``0`` only when **every** per-project pytest exited cleanly **and**
        the combined coverage gate passes. ``1`` otherwise.
    """
    log_header("Per-project pytest runner", logger)

    pairs = _discover_project_test_dirs(repo_root, projects, skip_projects)
    if not pairs:
        logger.warning("No runnable projects with a tests/ directory were found.")
        return 0

    resolved_markers = DEFAULT_MARKER_EXPR if marker_expr is None else marker_expr or None

    coverage_file_value = _resolve_coverage_file(coverage_file)
    # Reset combined coverage data file before the first project runs.
    cf_path = Path(coverage_file_value)
    if not cf_path.is_absolute():
        cf_path = repo_root / cf_path
    if cf_path.exists():
        try:
            cf_path.unlink()
            logger.debug("Removed stale coverage file: %s", cf_path)
        except OSError as exc:  # pragma: no cover - filesystem oddity
            logger.warning("Could not remove stale coverage file %s: %s", cf_path, exc)

    env = _make_subprocess_env(str(cf_path), repo_root)

    logger.info("Will run %d project(s):", len(pairs))
    for name, tests_dir in pairs:
        logger.info("  - %s (%s)", name, tests_dir)

    overall_exit = 0
    for index, (project_name, tests_dir) in enumerate(pairs):
        cmd = _build_pytest_cmd(
            project_name,
            tests_dir,
            repo_root=repo_root,
            is_first=(index == 0),
            marker_expr=resolved_markers,
            timeout=timeout,
        )
        rc = _run_pytest_for_project(cmd, repo_root, env, project_name)
        if rc == 0:
            log_success(f"Project '{project_name}' tests passed", logger)
        else:
            logger.error("Project '%s' tests failed (exit=%d)", project_name, rc)
            overall_exit = rc or overall_exit or 1

    cov_rc = _run_combined_coverage_gate(repo_root, env, fail_under)
    if cov_rc == 0:
        log_success(f"Combined coverage gate passed (>= {fail_under}%)", logger)
    else:
        logger.error("Combined coverage gate failed (exit=%d)", cov_rc)
        overall_exit = overall_exit or cov_rc or 1

    return 0 if overall_exit == 0 else 1


__all__ = [
    "DEFAULT_COVERAGE_FILE",
    "DEFAULT_FAIL_UNDER",
    "DEFAULT_MARKER_EXPR",
    "DEFAULT_SKIP_PROJECTS",
    "DEFAULT_TIMEOUT",
    "run_per_project_pytest",
]
