"""Canonical pytest subprocess orchestration shared by pipeline and CI runners.

``pipeline_test_runner`` (Stage 01) and ``test_runner.run_per_project_pytest``
(multi-project union gate) both delegate marker expressions, discovery logging,
coverage datafile policy, and project-floor resolution to this module.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any, Literal, Mapping, TypedDict

from infrastructure.core.testing.coverage_policy import check_cov_datafile_support
from infrastructure.core.logging.utils import get_logger, log_substep, log_success
from infrastructure.core.testing.pytest_profiles import (
    DEFAULT_PROJECT_MATRIX_MAX_WORKERS,
    DEFAULT_TEST_PROFILE,
    ENV_PROJECT_MATRIX_WORKERS,
    ENV_XDIST_WORKERS,
    MACOS_COVERAGE_XDIST_MAX_WORKERS,
    TEST_PROFILE_NAMES,
    TEST_PROFILE_REGISTRY,
    XDIST_DISTRIBUTION,
    TestProfileName,
    TestProfileSpec,
    XdistWorkerConfig,
    build_profile_marker_expression,
    parse_project_workers,
    resolve_project_matrix_workers,
    resolve_test_profile,
    resolve_xdist_args,
    resolve_xdist_worker_config,
    test_runner_dependency_specs,
    validate_coverage_parallel,
    validate_project_matrix_concurrency,
)
from infrastructure.core.project_pyproject import (
    project_declared_coverage_floor,
    project_declared_test_command,
    resolve_project_cov_config,
)
from infrastructure.core.runtime._tools import find_uv
from infrastructure.core.testing.project_test_runtime import (
    ProjectTestRuntimeError,
    select_project_test_python,
    build_audited_project_test_command,
)

logger = get_logger(__name__)

InfrastructureTestScope = Literal["full", "pipeline-smoke"]

INFRASTRUCTURE_TEST_SCOPES: tuple[InfrastructureTestScope, ...] = ("full", "pipeline-smoke")
# The test subprocess itself reports its collected count.  A second
# ``--collect-only`` subprocess is useful when diagnosing a surprising
# collection change, but it doubles collection work for every normal pipeline
# run (and is especially costly for the public project matrix).  Keep the
# diagnostic escape hatch explicit and opt-in.
ENV_DISCOVERY_PREFLIGHT = "TEMPLATE_TEST_DISCOVERY_PREFLIGHT"
_TRUE_ENV_VALUES: frozenset[str] = frozenset({"1", "true", "yes", "on"})

PIPELINE_SMOKE_INFRA_TEST_PATHS = (
    Path("tests/infra_tests/git_hook_smoke"),
    Path("tests/infra_tests/core/test_pipeline.py"),
    Path("tests/infra_tests/core/test_pipeline_types.py"),
    Path("tests/infra_tests/core/test_pipeline_control_extensions.py"),
    Path("tests/infra_tests/core/test_pytest_orchestration.py"),
    Path("tests/infra_tests/project/test_domain_profile.py"),
    Path("tests/infra_tests/validation/test_evidence_registry.py"),
    Path("tests/infra_tests/benchmark/test_template_benchmark_harness.py"),
    Path("tests/infra_tests/test_documentation_index_invariants.py"),
)

DISCOVERY_PATTERNS: tuple[str, ...] = (
    r"(\d+)\s+tests?\s+collected",
    r"collected\s+(\d+)\s+items?",
    r"found\s+(\d+)\s+tests?",
    r"(\d+)\s+tests?\s+found",
    r"=+\s+(\d+)\s+tests?\s+collected",
)
_RESULT_STATUS_PATTERN = re.compile(
    r"\b(?P<count>\d+)\s+(?P<status>passed|failed|skipped|xfailed|xpassed|errors?|deselected)\b",
    re.IGNORECASE,
)


class TestSuiteResults(TypedDict, total=False):
    """Structured result dict returned by infrastructure/project test runners."""

    passed: int
    failed: int
    skipped: int
    total: int
    warnings: int
    exit_code: int
    original_exit_code: int | None
    diagnostic: str
    selected_runtime: dict[str, object]
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
        # Fail closed: a manifest entry pointing at a moved/renamed path must
        # error here, not silently collect 0 tests and pass a vacuous gate.
        missing = [str(path) for path in PIPELINE_SMOKE_INFRA_TEST_PATHS if not (repo_root / path).exists()]
        if missing:
            raise FileNotFoundError(
                "pipeline-smoke manifest references missing test paths "
                f"(update PIPELINE_SMOKE_INFRA_TEST_PATHS): {missing}"
            )
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


def discovery_preflight_enabled(*, env: Mapping[str, str] | None = None) -> bool:
    """Return whether the optional collection-only diagnostic should run.

    The real pytest subprocess already records ``discovery_count`` from its
    own output.  This preflight exists for troubleshooting collection or
    command-line issues and is intentionally disabled in ordinary runs so it
    cannot become an invisible second test-suite startup cost.
    """
    values = os.environ if env is None else env
    return values.get(ENV_DISCOVERY_PREFLIGHT, "").strip().lower() in _TRUE_ENV_VALUES


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


def parse_test_summary_count(combined_output: str) -> int | None:
    """Extract the non-vacuous test count from a pytest result summary.

    The normal matrix command uses quiet output, so a second collection-only
    subprocess would waste the most expensive part of the quick-feedback lane.
    Pytest's final summary already reports selected outcomes; summing that
    final summary gives a useful collection/execution count without doubling
    startup and import work. ``None`` means the output was unavailable or did
    not contain a recognizable summary and is therefore not treated as zero.
    """
    candidates = [
        line
        for line in combined_output.splitlines()
        if _RESULT_STATUS_PATTERN.search(line)
        and (" in " in line or line.lstrip().startswith("=") or "short test summary" in line.lower())
    ]
    if not candidates:
        return None
    matches = list(_RESULT_STATUS_PATTERN.finditer(candidates[-1]))
    if not matches:
        return None
    return sum(int(match.group("count")) for match in matches)


def log_discovered_tests(
    cmd: list[str],
    repo_root: Path,
    env: dict[str, str],
    label: str,
    *,
    timeout_seconds: float = 30.0,
) -> None:
    """Run pytest serially with ``--collect-only`` and log its test count.

    Pytest-xdist may schedule collected items even in collection-only mode.
    Discovery is only a pre-flight count, so carrying the execution command's
    ``-n``/``--dist`` options into it can duplicate or even start a large suite
    before the real test run.  A final ``-n 0`` overrides command-line and
    project-level ``addopts`` parallelism; ``--no-cov`` avoids instrumenting a
    throwaway collection pass.
    """
    discovery_cmd = [*cmd, "--collect-only", "-n", "0", "--no-cov"]
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
    uv_path = find_uv()
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
    """Require the nominated existing interpreter; never fall back or install."""
    selected = [str(select_project_test_python(project_root))]
    if cmd != selected:
        raise ProjectTestRuntimeError("Test command differs from the nominated existing project runtime")
    return selected


def normalize_pytest_args_for_project(project_root: Path, pytest_args: list[str]) -> list[str]:
    """Use project-relative positional paths for a project-working-directory invocation."""
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


def build_project_pytest_command(
    project_root: Path, pytest_args: list[str], *, interpreter: Path | None = None
) -> list[str]:
    """Build Python-module argv for one existing prepared project interpreter.

    Execution adapters independently admit its exact runner versions. This
    pure builder never installs dependencies or falls back from a broken venv.
    """
    selected = select_project_test_python(project_root) if interpreter is None else interpreter
    return list(
        build_audited_project_test_command(
            project_root, selected, tuple(normalize_pytest_args_for_project(project_root, pytest_args)), module="pytest"
        )
    )


def build_union_pytest_command(
    repo_root: Path,
    project_root: Path,
    tests_dir: Path,
    *,
    is_first: bool,
    marker_expr: str | None,
    timeout: int,
    parallel: str | int | None = None,
    fail_under: int | None = None,
) -> list[str]:
    """Build argv for one project in a multi-project combined-coverage run.

    When *parallel* (or the ``PYTEST_XDIST_WORKERS`` env var) requests it, the
    per-project pytest invocation is parallelized with pytest-xdist. pytest-cov
    combines per-worker coverage data before that project's isolated datafile
    is written. The runner combines those files only after all project floors
    have been evaluated.
    """
    resolved_root = project_root.resolve()
    src_dir = resolved_root / "src"
    # Use the ABSOLUTE resolved path so that --cov resolves correctly even
    # when the subprocess CWD is the project directory — a repo-relative path
    # (e.g. ``projects/templates/.../src``) resolve to the wrong location and
    # collect 0% coverage.
    if src_dir.is_dir():
        cov_target = str(src_dir)
    else:
        cov_target = str(resolved_root)

    pytest_args: list[str] = [
        str(tests_dir),
        f"--cov={cov_target}",
        "--cov-branch",
        "--cov-report=term-missing",
        f"--timeout={timeout}",
        "--durations=10",
    ]
    if marker_expr:
        pytest_args.extend(["-m", marker_expr])
    if fail_under is not None:
        pytest_args.append(f"--cov-fail-under={fail_under}")
    if not is_first:
        pytest_args.append("--cov-append")
    pytest_args.extend(resolve_xdist_args(parallel))
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
    if strict and exit_code == 0 and project_has_test_files(project_root) and ran_count == 0:
        tests_dir = project_root / "tests"
        logger.error(
            "Project '%s' has test files under %s but the run collected/ran "
            "0 tests — refusing to score this as PASSED. The project "
            "prepared test environment or test selection needs inspection.",
            project_name,
            tests_dir,
        )
        exit_code = 1
        test_results["exit_code"] = 1

    return exit_code, test_results


__all__ = [
    "DEFAULT_PROJECT_MATRIX_MAX_WORKERS",
    "DEFAULT_TEST_PROFILE",
    "DISCOVERY_PATTERNS",
    "ENV_DISCOVERY_PREFLIGHT",
    "ENV_PROJECT_MATRIX_WORKERS",
    "ENV_XDIST_WORKERS",
    "INFRASTRUCTURE_TEST_SCOPES",
    "InfrastructureTestScope",
    "MACOS_COVERAGE_XDIST_MAX_WORKERS",
    "PIPELINE_SMOKE_INFRA_TEST_PATHS",
    "TEST_PROFILE_NAMES",
    "TEST_PROFILE_REGISTRY",
    "TestProfileName",
    "TestProfileSpec",
    "TestSuiteResults",
    "XDIST_DISTRIBUTION",
    "XdistWorkerConfig",
    "apply_coverage_datafile",
    "build_profile_marker_expression",
    "build_project_pytest_command",
    "build_pythonpath",
    "build_union_pytest_command",
    "discovery_preflight_enabled",
    "enforce_project_suite_guards",
    "log_discovered_tests",
    "make_coverage_subprocess_env",
    "parse_discovery_count",
    "parse_project_workers",
    "parse_test_discovery_timeout",
    "parse_test_summary_count",
    "prepend_uv_to_path",
    "project_declared_coverage_floor",
    "project_declared_test_command",
    "project_has_test_files",
    "resolve_coverage_file",
    "resolve_infrastructure_test_paths",
    "resolve_project_cov_config",
    "resolve_project_matrix_workers",
    "resolve_project_test_python",
    "resolve_test_profile",
    "resolve_xdist_args",
    "resolve_xdist_worker_config",
    "test_runner_dependency_specs",
    "validate_coverage_parallel",
    "validate_project_matrix_concurrency",
]
