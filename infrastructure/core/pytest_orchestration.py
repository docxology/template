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
import tomllib
from pathlib import Path
from typing import Any, Literal, TypedDict

from infrastructure.core.logging.utils import get_logger, log_substep, log_success
from infrastructure.core.runtime.environment import get_python_command
from infrastructure.reporting.coverage_parser import check_cov_datafile_support

logger = get_logger(__name__)

InfrastructureTestScope = Literal["full", "pipeline-smoke"]

INFRASTRUCTURE_TEST_SCOPES: tuple[InfrastructureTestScope, ...] = ("full", "pipeline-smoke")

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


def project_declared_coverage_floor(project_root: Path) -> int | None:
    """Return a project's self-declared ``fail_under`` from ``pyproject.toml``, if any."""
    pyproject = project_root / "pyproject.toml"
    if not pyproject.is_file():
        return None
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    declared = data.get("tool", {}).get("coverage", {}).get("report", {}).get("fail_under")
    if isinstance(declared, (int, float)):
        return int(declared)
    return None


def resolve_project_cov_config(project_root: Path) -> Path | None:
    """Return project ``pyproject.toml`` when it declares ``[tool.coverage.run]``."""
    pyproject = project_root / "pyproject.toml"
    if not pyproject.is_file():
        return None
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    if data.get("tool", {}).get("coverage", {}).get("run") is None:
        return None
    return pyproject


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
    """Apply zero-collected and below-threshold coverage guards for project runs."""
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

    cov_pct = test_results.get("coverage_percent")
    if strict and cov_pct is not None and ran_count > 0 and cov_pct < project_threshold:
        logger.error(
            "Project '%s' coverage %.2f%% is below the %.0f%% gate — failing "
            "(suite_runner would otherwise suppress the cov-fail-under exit).",
            project_name,
            cov_pct,
            project_threshold,
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
    "apply_coverage_datafile",
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
]
