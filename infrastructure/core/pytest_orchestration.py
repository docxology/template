"""Canonical pytest subprocess orchestration shared by pipeline and CI runners.

``pipeline_test_runner`` (Stage 01) and ``test_runner.run_per_project_pytest``
(multi-project union gate) both delegate marker expressions, discovery logging,
coverage datafile policy, and project-floor resolution to this module.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Literal, TypedDict

from infrastructure.core.coverage_policy import check_cov_datafile_support
from infrastructure.core.logging.utils import get_logger, log_substep, log_success
from infrastructure.core.project_pyproject import (
    project_declared_coverage_floor,
    project_declares_dev_extra,
    resolve_project_cov_config,
)
from infrastructure.core.runtime.environment import get_python_command, resolve_test_python

logger = get_logger(__name__)

InfrastructureTestScope = Literal["full", "pipeline-smoke"]

INFRASTRUCTURE_TEST_SCOPES: tuple[InfrastructureTestScope, ...] = ("full", "pipeline-smoke")

TEST_RUNNER_BASE_DEPS: tuple[str, ...] = ("pytest", "pytest-cov", "pytest-timeout")

PIPELINE_SMOKE_INFRA_TEST_PATHS = (
    Path("tests/infra_tests/git_hook_smoke"),
    Path("tests/infra_tests/core/test_pipeline.py"),
    Path("tests/infra_tests/core/test_pipeline_types.py"),
    Path("tests/infra_tests/core/test_pipeline_control_extensions.py"),
    Path("tests/infra_tests/core/test_pytest_orchestration.py"),
    Path("tests/infra_tests/project/test_domain_profile.py"),
    Path("tests/infra_tests/validation/test_evidence_registry.py"),
    Path("tests/infra_tests/bench/test_template_benchmark_harness.py"),
    Path("tests/infra_tests/test_documentation_index_invariants.py"),
)

DISCOVERY_PATTERNS: tuple[str, ...] = (
    r"(\d+)\s+tests?\s+collected",
    r"collected\s+(\d+)\s+items?",
    r"found\s+(\d+)\s+tests?",
    r"(\d+)\s+tests?\s+found",
    r"=+\s+(\d+)\s+tests?\s+collected",
)


def test_runner_dependency_specs() -> tuple[str, ...]:
    """Return ``uv --with`` specs for project-level pytest subprocesses.

    The multi-project runner appends every project's traces into one coverage
    SQLite database. Mixing project environments with different ``coverage``
    versions can leave that shared file unreadable by later subprocesses, so
    pin ``coverage`` to the workspace version that launched the orchestrator.
    """
    deps = list(TEST_RUNNER_BASE_DEPS)
    try:
        deps.append(f"coverage=={version('coverage')}")
    except PackageNotFoundError:
        logger.warning("coverage package not found; project test subprocesses will not pin coverage")
    return tuple(deps)


class TestSuiteResults(TypedDict, total=False):
    """Structured result dict returned by infrastructure/project test runners."""

    passed: int
    failed: int
    skipped: int
    total: int
    warnings: int
    exit_code: int
    discovery_count: int
    collection_errors: int
    execution_phases: dict[str, float]
    test_categories: dict[str, int]
    coverage_percent: float
    failed_tests: list[dict[str, str]]


def resolve_infrastructure_test_paths(repo_root: Path, scope: InfrastructureTestScope) -> list[str]:
    """Return pytest path arguments for an infrastructure test scope."""
    if scope == "full":
        return [
            str(repo_root / "tests" / "infra_tests"),
            str(repo_root / "tests" / "integration"),
            "--ignore=" + str(repo_root / "tests" / "integration" / "test_module_interoperability.py"),
        ]
    if scope == "pipeline-smoke":
        return [str(repo_root / relative_path) for relative_path in PIPELINE_SMOKE_INFRA_TEST_PATHS]
    raise ValueError(f"Unknown infrastructure test scope: {scope}")


def parse_test_discovery_timeout(scope: InfrastructureTestScope) -> float:
    """Resolve the collection timeout for pytest discovery logging."""
    raw_timeout = os.environ.get("TEST_DISCOVERY_TIMEOUT_SEC")
    if raw_timeout:
        try:
            timeout = float(raw_timeout)
        except ValueError:
            logger.warning("Ignoring invalid TEST_DISCOVERY_TIMEOUT_SEC=%r", raw_timeout)
        else:
            if timeout > 0:
                return timeout
            logger.warning("Ignoring non-positive TEST_DISCOVERY_TIMEOUT_SEC=%r", raw_timeout)
    return 120.0 if scope == "full" else 30.0


def parse_discovery_count(combined_output: str) -> int | None:
    """Extract a collected-test count from pytest --collect-only output."""
    for pattern in DISCOVERY_PATTERNS:
        match = re.search(pattern, combined_output, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue
    return None


def log_discovered_tests(
    cmd: list[str],
    repo_root: Path,
    env: dict[str, str],
    label: str,
    *,
    timeout_seconds: float = 30.0,
) -> None:
    """Run pytest --collect-only and log the discovered test count."""
    discovery_cmd = cmd.copy()
    discovery_cmd.append("--collect-only")
    log_substep(f"Discovering {label} tests...", logger)
    try:
        result = subprocess.run(  # nosec B603
            discovery_cmd,
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        combined = result.stdout + "\n" + result.stderr
        test_count = parse_discovery_count(combined)
        if test_count is not None:
            log_success(f"Discovered {test_count} {label} tests", logger)
        else:
            logger.warning("Could not parse test count from %s test discovery", label)
    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as exc:
        logger.warning("Test discovery failed for %s: %s", label, exc)


def build_pythonpath(
    repo_root: Path,
    project_root: Path,
    *,
    prepend: list[str] | None = None,
    existing_pythonpath: str | None = None,
) -> str:
    """Build PYTHONPATH for a pytest subprocess."""
    parts: list[str] = list(prepend or [])
    parts.extend([str(repo_root), str(repo_root / "infrastructure")])
    project_src = project_root / "src"
    if project_src.exists():
        parts.append(str(project_src))
    if existing_pythonpath:
        parts.append(existing_pythonpath)
    return os.pathsep.join(parts)


def prepend_uv_to_path(env: dict[str, str]) -> None:
    """Ensure ``uv`` is on PATH when available."""
    uv_path = shutil.which("uv")
    if uv_path:
        env["PATH"] = f"{os.path.dirname(uv_path)}:{env.get('PATH', '')}"


def apply_coverage_datafile(
    cmd: list[str],
    env: dict[str, str],
    datafile_name: str,
    *,
    supported: bool | None = None,
) -> None:
    """Pin coverage output to ``datafile_name`` via CLI flag or COVERAGE_FILE."""
    if supported is None:
        supported = check_cov_datafile_support()
    if supported:
        cmd.append(f"--cov-datafile={datafile_name}")
    else:
        env["COVERAGE_FILE"] = datafile_name


def resolve_coverage_file(coverage_file: str) -> str:
    """Return COVERAGE_FILE value, honouring the environment when set."""
    env_value = os.environ.get("COVERAGE_FILE")
    if env_value:
        return env_value
    return coverage_file


def make_coverage_subprocess_env(coverage_file_value: str, repo_root: Path) -> dict[str, str]:
    """Build subprocess env with COVERAGE_FILE pinned and repo root on PYTHONPATH."""
    env = os.environ.copy()
    env["COVERAGE_FILE"] = coverage_file_value
    existing_pp = env.get("PYTHONPATH", "")
    pp_parts = [str(repo_root)]
    if existing_pp:
        pp_parts.append(existing_pp)
    env["PYTHONPATH"] = os.pathsep.join(pp_parts)
    return env


def resolve_project_test_python(project_root: Path, cmd: list[str]) -> list[str]:
    """Use project venv python when it can import pytest; otherwise workspace interpreter."""
    try:
        probe = subprocess.run(  # nosec B603
            [*cmd, "-c", "import pytest"],
            capture_output=True,
            check=False,
            timeout=30,
        )
        if probe.returncode == 0:
            return cmd
        logger.warning(
            "Resolved interpreter %s cannot import pytest (project venv "
            "%s/.venv is missing test deps — run `uv sync`). Falling back "
            "to the workspace interpreter %s so the project suite actually runs.",
            cmd,
            project_root,
            get_python_command(),
        )
    except (OSError, subprocess.SubprocessError) as probe_err:
        logger.warning("pytest-availability probe failed (%s); using %s", probe_err, get_python_command())
    return get_python_command()


def normalize_pytest_args_for_project(project_root: Path, pytest_args: list[str]) -> list[str]:
    """Rewrite absolute paths under *project_root* to project-relative form for ``uv run --directory``."""
    root = project_root.resolve()
    normalized: list[str] = []
    for arg in pytest_args:
        if not arg.startswith("-"):
            candidate = Path(arg)
            if candidate.is_absolute():
                try:
                    normalized.append(str(candidate.resolve().relative_to(root)))
                    continue
                except ValueError:
                    pass
        normalized.append(arg)
    return normalized


def build_project_pytest_command(project_root: Path, pytest_args: list[str]) -> list[str]:
    """Return argv for a project pytest suite using project-local deps when declared.

    Projects with ``pyproject.toml`` run via ``uv run --directory`` so pinned
    dependencies (for example ``scikit-learn``) resolve from the project tree
    instead of the workspace interpreter.

    Test-runner packages (``pytest``, ``pytest-cov``, ``pytest-timeout``) are
    injected via ``--with`` so they are always available in the project's
    ephemeral env even when the project's own ``pyproject.toml`` does not declare
    them. Without this, projects that only declare scientific deps (numpy /
    matplotlib) would fail with ``--timeout=120 unrecognized argument`` (exit=4)
    because the project venv is created on-demand by ``uv run --directory`` and
    contains only the project's own deps — not the workspace dev group.
    """
    pyproject = project_root / "pyproject.toml"
    uv_path = shutil.which("uv")
    if pyproject.is_file() and uv_path:
        resolved_root = project_root.resolve()
        cmd: list[str] = [uv_path, "run", "--directory", str(resolved_root)]
        # Inject test-runner deps so they are always available regardless of
        # what the project itself declares (thin projects declare only runtime
        # deps; pytest/cov/timeout stay in the workspace dev group).
        for dependency_spec in test_runner_dependency_specs():
            cmd.extend(["--with", dependency_spec])
        if project_declares_dev_extra(resolved_root):
            cmd.extend(["--extra", "dev"])
        cmd.extend(
            [
                "python",
                "-m",
                "pytest",
                *normalize_pytest_args_for_project(resolved_root, pytest_args),
            ]
        )
        return cmd
    interpreter = resolve_project_test_python(project_root, resolve_test_python(project_root / ".venv"))
    return interpreter + ["-m", "pytest", *pytest_args]


def build_union_pytest_command(
    repo_root: Path,
    project_root: Path,
    tests_dir: Path,
    *,
    is_first: bool,
    marker_expr: str | None,
    timeout: int,
) -> list[str]:
    """Build argv for one project in a multi-project combined-coverage run."""
    resolved_root = project_root.resolve()
    src_dir = resolved_root / "src"
    # Use the ABSOLUTE resolved path so that --cov resolves correctly even
    # when pytest runs under ``uv run --directory <project>`` which sets the
    # subprocess CWD to the project directory — making a repo-relative path
    # (e.g. ``projects/templates/.../src``) resolve to the wrong location and
    # collect 0% coverage.
    if src_dir.is_dir():
        cov_target = str(src_dir)
    else:
        cov_target = str(resolved_root)

    pytest_args: list[str] = [
        str(tests_dir),
        f"--cov={cov_target}",
        "--cov-report=term-missing",
        f"--timeout={timeout}",
        "--durations=10",
    ]
    if marker_expr:
        pytest_args.extend(["-m", marker_expr])
    if not is_first:
        pytest_args.append("--cov-append")
    return build_project_pytest_command(resolved_root, pytest_args)


def project_has_test_files(project_root: Path) -> bool:
    """Return True when ``tests/`` contains discoverable test modules."""
    tests_dir = project_root / "tests"
    if not tests_dir.is_dir():
        return False
    return any(tests_dir.rglob("test_*.py")) or any(tests_dir.rglob("*_test.py"))


def enforce_project_suite_guards(
    exit_code: int,
    test_results: dict[str, Any],
    *,
    project_name: str,
    project_root: Path,
    project_threshold: float,
    strict: bool,
) -> tuple[int, dict[str, Any]]:
    """Apply zero-collected guard for project runs.

    Coverage thresholds are enforced by pytest ``--cov-fail-under`` on the
    command line; this guard only catches silent zero-collection failures.
    """
    del project_threshold  # retained for call-site stability; pytest owns coverage gates
    ran_count = test_results.get("total", 0) or test_results.get("passed", 0)
    if strict and project_has_test_files(project_root) and ran_count == 0:
        tests_dir = project_root / "tests"
        logger.error(
            "Project '%s' has test files under %s but the run collected/ran "
            "0 tests — refusing to score this as PASSED. The project "
            "interpreter is likely missing pytest/pytest-cov (run `uv sync`).",
            project_name,
            tests_dir,
        )
        exit_code = 1
        test_results["exit_code"] = 1

    return exit_code, test_results


__all__ = [
    "DISCOVERY_PATTERNS",
    "INFRASTRUCTURE_TEST_SCOPES",
    "InfrastructureTestScope",
    "PIPELINE_SMOKE_INFRA_TEST_PATHS",
    "TestSuiteResults",
    "build_project_pytest_command",
    "build_union_pytest_command",
    "build_pythonpath",
    "enforce_project_suite_guards",
    "log_discovered_tests",
    "make_coverage_subprocess_env",
    "parse_discovery_count",
    "parse_test_discovery_timeout",
    "prepend_uv_to_path",
    "project_declared_coverage_floor",
    "project_has_test_files",
    "resolve_coverage_file",
    "resolve_project_cov_config",
    "resolve_infrastructure_test_paths",
    "resolve_project_test_python",
    "test_runner_dependency_specs",
]
