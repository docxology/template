"""Test orchestration module.

This module contains the business logic for discovering, executing, and reporting
on the tests for both infrastructure and project suites.
"""

from __future__ import annotations


import os
import re
import shutil
import subprocess
import time
import tomllib
from pathlib import Path
from typing import Literal, TypedDict

import tempfile

from infrastructure.core.logging.utils import get_logger, log_success, log_header, log_substep
from infrastructure.core.logging.constants import BANNER_WIDTH, TABLE_WIDTH
from infrastructure.core.config.queries import get_testing_config
from infrastructure.core.files.coverage_cleanup import clean_coverage_files
from infrastructure.reporting.coverage_reporter import (
    generate_test_report,
    save_test_report_to_files,
    format_coverage_status,
    analyze_coverage_gaps,
    format_failure_suggestions,
)
from infrastructure.core.logging.helpers import format_duration as _format_duration
from infrastructure.core.pytest_marker_exprs import build_pytest_marker_expression
from infrastructure.core.runtime.environment import get_python_command, resolve_test_python
from infrastructure.project.discovery import resolve_project_root
from infrastructure.reporting.coverage_parser import check_cov_datafile_support
from infrastructure.reporting.suite_runner import TestSuiteConfig, run_test_suite

logger = get_logger(__name__)

InfrastructureTestScope = Literal["full", "pipeline-smoke"]

INFRASTRUCTURE_TEST_SCOPES: tuple[InfrastructureTestScope, ...] = ("full", "pipeline-smoke")

PIPELINE_SMOKE_INFRA_TEST_PATHS = (
    Path("tests/infra_tests/git_hook_smoke"),
    Path("tests/infra_tests/core/test_pipeline.py"),
    Path("tests/infra_tests/core/test_pipeline_types.py"),
    Path("tests/infra_tests/core/test_pipeline_control_extensions.py"),
    Path("tests/infra_tests/project/test_domain_profile.py"),
    Path("tests/infra_tests/validation/test_evidence_registry.py"),
    Path("tests/infra_tests/bench/test_template_benchmark_harness.py"),
    Path("tests/infra_tests/test_documentation_index_invariants.py"),
)


def _project_declared_coverage_floor(project_root: Path) -> int | None:
    """Return a project's self-declared coverage floor, if any.

    Rotating research projects (animation/visualization/Lean-adjacent surface
    intentionally not driven to the 90% exemplar floor) pin their own
    sustainable floor via ``[tool.coverage.report] fail_under`` in their
    ``pyproject.toml`` — the rotating-project coverage exception documented in
    CLAUDE.md. The per-project gate honours that declared floor when present so
    it enforces the project's real contract instead of a global value the
    project never claimed to meet. Returns ``None`` when the project declares
    no floor (the global default then applies). This keeps the gate strict — a
    declared floor is still enforced, so a "0/0 lies green" run cannot pass —
    while not forcing research projects to an inappropriate exemplar threshold.
    """
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


class TestSuiteResults(TypedDict, total=False):
    """Structured result dict returned by run_infrastructure_tests / run_project_tests."""

    passed: int
    failed: int
    skipped: int
    total: int
    warnings: int
    exit_code: int
    discovery_count: int
    collection_errors: int
    execution_phases: dict
    test_categories: dict
    coverage_percent: float
    failed_tests: list


_DISCOVERY_PATTERNS = [
    r"(\d+)\s+tests?\s+collected",
    r"collected\s+(\d+)\s+items?",
    r"found\s+(\d+)\s+tests?",
    r"(\d+)\s+tests?\s+found",
    r"=+\s+(\d+)\s+tests?\s+collected",
]


def _resolve_infrastructure_test_paths(repo_root: Path, scope: InfrastructureTestScope) -> list[str]:
    """Return pytest paths for an infrastructure test scope."""
    if scope == "full":
        return [
            str(repo_root / "tests" / "infra_tests"),
            str(repo_root / "tests" / "integration"),
            "--ignore=" + str(repo_root / "tests" / "integration" / "test_module_interoperability.py"),
        ]
    if scope == "pipeline-smoke":
        return [str(repo_root / relative_path) for relative_path in PIPELINE_SMOKE_INFRA_TEST_PATHS]
    raise ValueError(f"Unknown infrastructure test scope: {scope}")


def _parse_test_discovery_timeout(scope: InfrastructureTestScope) -> float:
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


def _log_discovered_tests(
    cmd: list[str],
    repo_root: Path,
    env: dict,
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
        test_count = None
        for pattern in _DISCOVERY_PATTERNS:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                try:
                    test_count = int(match.group(1))
                    break
                except (ValueError, IndexError):
                    logger.debug("Could not parse match group as int, trying next pattern")
                    continue
        if test_count is not None:
            log_success(f"Discovered {test_count} {label} tests", logger)
        else:
            logger.warning("Could not parse test count from %s test discovery", label)
    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        logger.warning("Test discovery failed for %s: %s", label, e)


def run_infrastructure_tests(
    repo_root: Path,
    project_name: str = "project",
    quiet: bool = True,
    include_slow: bool = False,
    include_ollama_tests: bool = False,
    include_bench: bool = False,
    strict: bool = True,
    scope: InfrastructureTestScope = "full",
) -> tuple[int, TestSuiteResults]:
    """Execute infrastructure test suite with coverage."""
    if scope not in INFRASTRUCTURE_TEST_SCOPES:
        raise ValueError(f"Unknown infrastructure test scope: {scope}")
    start_time = time.time()
    project_root = resolve_project_root(repo_root, project_name)

    clean_coverage_files(repo_root)

    testing_config = get_testing_config(repo_root)
    full_scope = scope == "full"
    infra_threshold = testing_config.infra_coverage_threshold if full_scope else 0

    if full_scope:
        log_substep(f"Running infrastructure tests ({infra_threshold}% coverage threshold)...", logger)
    else:
        log_substep("Running pipeline-smoke infrastructure tests (no coverage gate)...", logger)
    if not include_ollama_tests:
        log_substep("(Skipping LLM integration tests - run separately with: pytest -m requires_ollama)", logger)
    logger.info("Infrastructure test scope: %s", scope)
    logger.info("Test path(s): %s", ", ".join(_resolve_infrastructure_test_paths(repo_root, scope)))
    if full_scope:
        logger.info("Coverage target: infrastructure (%s%% minimum)", infra_threshold)
    else:
        logger.info("Coverage target: N/A for pipeline-smoke scope")

    cmd = resolve_test_python(repo_root / ".venv")

    cmd += [
        "-m",
        "pytest",
    ]
    cmd.extend(_resolve_infrastructure_test_paths(repo_root, scope))
    if full_scope:
        cmd.append("--cov=infrastructure")
    infra_marker = build_pytest_marker_expression(
        skip_requires_ollama=not include_ollama_tests,
        skip_slow=not include_slow,
        skip_bench=not include_bench,
    )
    if infra_marker:
        cmd.extend(["-m", infra_marker])

    env = os.environ.copy()
    env.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))
    cov_datafile_supported = check_cov_datafile_support()
    coverage_json_paths: list[Path] = []
    if full_scope:
        if cov_datafile_supported:
            cmd.append("--cov-datafile=.coverage.infra")
        else:
            env["COVERAGE_FILE"] = ".coverage.infra"

        coverage_json_paths = [
            repo_root / "coverage_infra.json",
            repo_root / "coverage.json",
            repo_root / "htmlcov" / "coverage.json",
        ]
        cmd.extend(
            [
                "--cov-report=term-missing",
                "--cov-report=html",
                "--cov-report=json:coverage_infra.json",
                f"--cov-fail-under={infra_threshold}",
            ]
        )
    cmd.append("--tb=short")
    if quiet:
        cmd.extend(["-q"])

    pythonpath_parts = [str(repo_root), str(repo_root / "infrastructure")]
    project_src = project_root / "src"
    if project_src.exists():
        pythonpath_parts.append(str(project_src))
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    if shutil.which("uv"):
        env["PATH"] = f"{os.path.dirname(shutil.which('uv'))}:{env.get('PATH', '')}"

    _log_discovered_tests(
        cmd,
        repo_root,
        env,
        f"infrastructure ({scope})",
        timeout_seconds=_parse_test_discovery_timeout(scope),
    )

    try:
        config = TestSuiteConfig(
            label="Infrastructure",
            cmd=cmd,
            env=env,
            repo_root=repo_root,
            coverage_json_paths=coverage_json_paths,
            coverage_threshold=infra_threshold,
            max_failures_env_var="MAX_INFRA_TEST_FAILURES",
            max_failures_config_key="max_infra_test_failures",
            quiet=quiet,
            spinner_label=f"Running infrastructure tests ({scope})",
            streaming_subprocess=True,
        )
        exit_code, test_results = run_test_suite(config)
        if strict and test_results.get("failed", 0) > 0:
            exit_code = 1
        duration = time.time() - start_time
        logger.info(f"Infrastructure test suite completed in {duration:.1f}s")
        if exit_code == 0:
            log_success("Infrastructure tests passed", logger)
        return exit_code, test_results
    except (OSError, subprocess.SubprocessError, RuntimeError, ValueError) as e:
        duration = time.time() - start_time
        logger.error(f"Failed to run infrastructure tests after {duration:.1f}s: {e}", exc_info=True)
        return 1, {}


def run_project_tests(
    repo_root: Path,
    project_name: str = "project",
    quiet: bool = True,
    include_slow: bool = False,
    include_bench: bool = False,
    strict: bool = True,
) -> tuple[int, TestSuiteResults]:
    """Execute project test suite with coverage."""
    start_time = time.time()
    project_root = resolve_project_root(repo_root, project_name)

    clean_coverage_files(repo_root)

    testing_config = get_testing_config(repo_root)
    _declared_floor = _project_declared_coverage_floor(project_root)
    project_threshold = _declared_floor if _declared_floor is not None else testing_config.project_coverage_threshold

    log_substep(f"Running project tests for '{project_name}' ({project_threshold}% coverage threshold)...", logger)
    logger.info(f"Test path: {project_root / 'tests'}")
    logger.info(f"Coverage target: {project_root / 'src'} ({project_threshold}% minimum)")

    cmd = resolve_test_python(project_root / ".venv")
    # A per-project ``.venv`` can have a valid interpreter symlink yet lack
    # pytest/pytest-cov (e.g. ``uv venv`` was run but ``uv sync`` was not).
    # Running ``<that python> -m pytest`` then collects zero tests, which the
    # suite scorer would otherwise normalise to a green "0/0 PASSED". Verify
    # the resolved interpreter can import pytest; if not, fall back LOUDLY to
    # the workspace interpreter (which has the dev deps) so the documented
    # per-project command actually runs the suite instead of lying green.
    try:
        _pytest_probe = subprocess.run(  # nosec B603
            [*cmd, "-c", "import pytest"],
            capture_output=True,
            check=False,
            timeout=30,
        )
        if _pytest_probe.returncode != 0:
            logger.warning(
                "Resolved interpreter %s cannot import pytest (project venv "
                "%s/.venv is missing test deps — run `uv sync`). Falling back "
                "to the workspace interpreter %s so the project suite actually runs.",
                cmd,
                project_root,
                get_python_command(),
            )
            cmd = get_python_command()
    except (OSError, subprocess.SubprocessError) as _probe_err:
        logger.warning("pytest-availability probe failed (%s); using %s", _probe_err, get_python_command())
        cmd = get_python_command()

    cmd += [
        "-m",
        "pytest",
        str(project_root / "tests"),
        f"--cov={project_root / 'src'}",
        # No per-project --cov-config: the project pyproject's
        # source=["src"]/omit=["src/analysis.py"] are project-relative and do
        # NOT resolve when pytest runs from repo-root, which silently mis-scoped
        # coverage (48.7% instead of the canonical 99.04%). Omitting it makes
        # coverage use the repo-root pyproject — identical to the documented
        # direct command and CI's run_per_project_pytest path.
    ]

    env = os.environ.copy()
    env.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib"))
    # Project root before repo root so ``import scripts.*`` resolves to
    # ``projects/<name>/scripts/``, not the template's top-level ``scripts/``.
    pythonpath_parts = [str(project_root), str(repo_root)]
    # Include project src/ so subpackage imports resolve when running from repo root
    project_src = project_root / "src"
    if project_src.exists():
        pythonpath_parts.append(str(project_src))
    if env.get("PYTHONPATH"):
        pythonpath_parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    # Keep subprocess coverage on the repo-root config too (CI's
    # run_per_project_pytest does not set COVERAGE_PROCESS_START); pointing it
    # at the project pyproject would re-introduce the project-relative-path
    # mis-scoping fixed above.
    env.pop("COVERAGE_PROCESS_START", None)

    cov_datafile_supported = check_cov_datafile_support()
    if cov_datafile_supported:
        cmd.append("--cov-datafile=.coverage.project")
    else:
        env["COVERAGE_FILE"] = ".coverage.project"

    cmd.extend(
        [
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=json:coverage_project.json",
            f"--cov-fail-under={project_threshold}",
            "--tb=short",
        ]
    )
    project_marker = build_pytest_marker_expression(
        skip_requires_ollama=False,
        skip_slow=not include_slow,
        skip_bench=not include_bench,
    )
    if project_marker:
        cmd.extend(["-m", project_marker])
    if quiet:
        cmd.extend(["-q"])
    if shutil.which("uv"):
        env["PATH"] = f"{os.path.dirname(shutil.which('uv'))}:{env.get('PATH', '')}"

    _log_discovered_tests(cmd, repo_root, env, f"project '{project_name}'")

    try:
        config = TestSuiteConfig(
            label="Project",
            cmd=cmd,
            env=env,
            repo_root=repo_root,
            coverage_json_paths=[
                repo_root / "coverage_project.json",
                repo_root / "coverage.json",
                repo_root / "htmlcov" / "coverage.json",
            ],
            coverage_threshold=project_threshold,
            max_failures_env_var="MAX_PROJECT_TEST_FAILURES",
            max_failures_config_key="max_project_test_failures",
            quiet=quiet,
            spinner_label=f"Running project tests for '{project_name}'",
            streaming_subprocess=True,
        )
        exit_code, test_results = run_test_suite(config)
        if strict and test_results.get("failed", 0) > 0:
            exit_code = 1
        # Zero-collected guard: if the project ships test files but the run
        # executed none, the suite never actually validated anything. The
        # scorer can otherwise report "Project: ✓ PASSED (0/0 tests, 0.0%
        # coverage)" and exit 0 — a coverage/test gate that lies green. A
        # project with discoverable tests that collected zero is always a
        # hard failure, regardless of strict tolerance.
        tests_dir = project_root / "tests"
        has_test_files = (
            tests_dir.is_dir()
            and any(tests_dir.rglob("test_*.py"))
            or (tests_dir.is_dir() and any(tests_dir.rglob("*_test.py")))
        )
        ran_count = test_results.get("total", 0) or test_results.get("passed", 0)
        if has_test_files and ran_count == 0:
            logger.error(
                "Project '%s' has test files under %s but the run collected/ran "
                "0 tests — refusing to score this as PASSED. The project "
                "interpreter is likely missing pytest/pytest-cov (run `uv sync`).",
                project_name,
                tests_dir,
            )
            exit_code = 1
            test_results["exit_code"] = 1
        # Coverage-threshold enforcement: a project run measurably below the
        # gate must FAIL even when no test failed. suite_runner suppresses
        # pytest's --cov-fail-under non-zero exit when failed==0, so without
        # this a below-threshold run would still be scored PASSED — a coverage
        # gate that lies. Safe now that coverage is measured against the
        # repo-root config (matches the canonical 99.04% for the exemplar).
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
        duration = time.time() - start_time
        logger.info(f"Project test suite completed in {duration:.1f}s")
        if exit_code == 0:
            log_success("Project tests passed", logger)
        return exit_code, test_results
    except (OSError, subprocess.SubprocessError, RuntimeError, ValueError) as e:
        duration = time.time() - start_time
        logger.error(f"Failed to run project tests after {duration:.1f}s: {e}", exc_info=True)
        return 1, {}


def _report_suite_failure(
    suite_name: str,
    results: dict,
    project_name: str = "",
) -> None:
    """Log failure details and fix suggestions for a test suite."""
    failed = results.get("failed", 0)
    skipped = results.get("skipped", 0)
    warnings = results.get("warnings", 0)
    logger.info(f"{suite_name} Results:")
    logger.info(f"  ✗ Failed: {failed} test(s) failed")
    if skipped > 0:
        logger.info(f"  ⚠ Skipped: {skipped}")
    if warnings > 0:
        logger.info(f"  ⚠ Warnings: {warnings}")

    failed_tests = results.get("failed_tests", [])
    if failed_tests:
        logger.info("")
        logger.info("  📋 Failed Tests:")
        for i, failure in enumerate(failed_tests[:5], 1):
            logger.info(f"    {i}. {failure['test']}")
            if failure["error_type"] != "Unknown":
                logger.info(
                    f"       {failure['error_type']}: {failure['error_message'][:60]}{'...' if len(failure['error_message']) > 60 else ''}"
                )
        if len(failed_tests) > 5:
            logger.info(f"    ... and {len(failed_tests) - 5} more failures")

    logger.info("")
    logger.info("  🔧 Quick Fix Suggestions:")
    suite_key = "infrastructure" if suite_name == "Infrastructure" else "project"
    for suggestion in format_failure_suggestions(failed_tests, suite_key, project_name):
        logger.info(suggestion)


def _report_suite_success(suite_name: str, results: dict, threshold: float, report: dict) -> None:
    """Log success details for a test suite."""
    passed = results.get("passed", 0)
    skipped = results.get("skipped", 0)
    coverage = results.get("coverage_percent", 0)
    warnings = results.get("warnings", 0)
    logger.info(f"{suite_name} Results:")
    logger.info(f"  ✓ Passed: {passed}")
    if skipped > 0:
        logger.info(f"  ⚠ Skipped: {skipped}")
    if warnings > 0:
        logger.info(f"  ⚠ Warnings: {warnings}")
    logger.info(f"  📊 Coverage: {format_coverage_status(coverage, threshold)}")
    if coverage < threshold:
        for suggestion in analyze_coverage_gaps(results, threshold, suite_name, report):
            logger.info(f"    {suggestion}")
    phases = results.get("execution_phases", {})
    if phases:
        logger.info(f"  ⏱ Duration: {_format_duration(sum(phases.values()))}")


def report_results(
    infra_exit: int,
    project_exit: int,
    infra_results: dict,
    project_results: dict,
    report: dict,
    project_name: str = "project",
) -> None:
    """Report comprehensive test execution results with detailed breakdowns."""
    log_header("Test Execution Summary", logger)

    if infra_results.get("collection_errors", 0) > 0:
        logger.info("")
        logger.info(f"⚠️  Collection Errors: {infra_results['collection_errors']}")
        logger.info(f"   Tests discovered: {infra_results.get('discovery_count', 0)}")
        logger.info("   Tests executed: 0 (collection failed)")
        logger.info("")
        logger.info("   Common causes:")
        logger.info("     - Missing test dependencies (pytest-httpserver, etc.)")
        logger.info("     - Syntax errors in test files")
        logger.info("     - Import errors in conftest.py")
        logger.info("")

    logger.info("")
    infra_was_run = infra_results.get("total", 0) > 0 or infra_exit != 0

    if not infra_was_run:
        logger.info("Infrastructure Results:")
        logger.info("  ⏭ Skipped (not run in this execution)")
        logger.info("  📊 Coverage: N/A (tests not executed)")
    elif infra_exit == 0:
        _report_suite_success("Infrastructure", infra_results, 60.0, report)
    else:
        _report_suite_failure("Infrastructure", infra_results)

    logger.info("")
    if project_exit == 0:
        _report_suite_success("Project", project_results, 90.0, report)
    else:
        _report_suite_failure("Project", project_results, project_name)

    logger.info("")
    logger.info("=" * BANNER_WIDTH)

    infra_passed = infra_results.get("passed", 0)
    infra_total = infra_results.get("total", 0)
    infra_coverage = infra_results.get("coverage_percent", 0)

    project_passed = project_results.get("passed", 0)
    project_total = project_results.get("total", 0)
    project_coverage = project_results.get("coverage_percent", 0)

    total_passed = infra_passed + project_passed
    total_tests = infra_total + project_total
    overall_success = project_exit == 0

    if overall_success:
        if not infra_was_run:
            logger.info(
                "Infrastructure: ⏭ SKIPPED (intentionally skipped - use --infra-only to run infrastructure tests)"
            )
        elif infra_exit == 0:
            logger.info(
                f"Infrastructure: ✓ PASSED ({infra_passed}/{infra_total} tests, {infra_coverage:.1f}% coverage)"
            )
        else:
            infra_failed = infra_results.get("failed", 0)
            logger.info(f"Infrastructure: ⚠ WARNING ({infra_failed} test(s) failed, but continuing)")

        logger.info(
            f"Project:       ✓ PASSED ({project_passed}/{project_total} tests, {project_coverage:.1f}% coverage)"
        )
        logger.info("-" * TABLE_WIDTH)
        logger.info(f"Total:         ✓ PASSED ({total_passed}/{total_tests} tests)")
        if infra_was_run:
            logger.info(f"Coverage:      Infrastructure: {infra_coverage:.1f}% | Project: {project_coverage:.1f}%")
        else:
            logger.info(f"Coverage:      Infrastructure: N/A | Project: {project_coverage:.1f}%")

        infra_duration = sum(infra_results.get("execution_phases", {}).values())
        project_duration = sum(project_results.get("execution_phases", {}).values())
        total_duration = infra_duration + project_duration
        if total_duration > 0:
            logger.info(f"Duration:      {_format_duration(total_duration)}")

        logger.info("=" * BANNER_WIDTH)
        log_success("All tests passed - ready for analysis", logger)
    else:
        if infra_exit == 0:
            logger.info(
                f"Infrastructure: ✓ PASSED ({infra_passed}/{infra_total} tests, {infra_coverage:.1f}% coverage)"
            )
        else:
            infra_failed = infra_results.get("failed", 0)
            logger.info(f"Infrastructure: ✗ FAILED ({infra_failed} test(s) failed)")

        logger.info(f"Project:       ✗ FAILED ({project_results.get('failed', 0)} test(s) failed)")
        logger.info("-" * TABLE_WIDTH)
        logger.info("Total:         ✗ FAILED (project tests failed)")
        logger.error("Project tests failed - pipeline cannot continue until tests pass")
        logger.info("Fix the failing tests shown above and re-run the pipeline")
        logger.info(f"Run 'pytest projects/{project_name}/tests/ -v' for detailed failure information")


def execute_test_pipeline(
    project_name: str,
    repo_root: Path,
    run_infra: bool,
    run_project: bool,
    quiet: bool,
    include_slow: bool,
    include_ollama_tests: bool,
    strict: bool,
    infra_scope: InfrastructureTestScope = "full",
) -> int:
    """Run full test orchestration.

    Returns:
        Exit code (0=success, 1=failure)
    """
    infra_exit, infra_results = 0, {}
    project_exit, project_results = 0, {}
    total_phases = int(run_infra) + int(run_project)

    if run_infra:
        phase_title = "Infrastructure Tests" if run_project else "Infrastructure Tests (Only)"
        log_header(f"Phase 1/{total_phases}: {phase_title}", logger)
        infra_exit, infra_results = run_infrastructure_tests(
            repo_root,
            project_name,
            quiet,
            include_slow,
            include_ollama_tests,
            strict=strict,
            scope=infra_scope,
        )

    if run_project:
        phase_num = 2 if run_infra else 1
        phase_title = f"Project Tests ({project_name})" if run_infra else f"Project Tests ({project_name}) (Only)"
        log_header(f"Phase {phase_num}/{total_phases}: {phase_title}", logger)
        project_exit, project_results = run_project_tests(
            repo_root,
            project_name,
            quiet,
            include_slow,
            strict=strict,
        )

    if run_project:
        report = generate_test_report(infra_results, project_results, repo_root, include_coverage_details=True)
        output_dir = resolve_project_root(repo_root, project_name) / "output" / "reports"
        save_test_report_to_files(report, output_dir)
        report_results(infra_exit, project_exit, infra_results, project_results, report, project_name)
    elif run_infra:
        log_header("Infrastructure Test Results", logger)
        if infra_exit == 0:
            log_success("Infrastructure tests passed", logger)
        else:
            logger.error("Infrastructure tests failed - this may affect build quality")
            logger.info("Infrastructure test failures don't block the pipeline but should be addressed")
            failed_tests = infra_results.get("failed_tests", [])
            if failed_tests:
                logger.info("")
                logger.info("📋 Failed Tests:")
                for i, failure in enumerate(failed_tests[:5], 1):
                    logger.info(f"    {i}. {failure['test']}")
                    if failure["error_type"] != "Unknown":
                        logger.info(f"       {failure['error_type']}: {failure['error_message'][:60]}")

    if run_project and run_infra:
        return 1 if (infra_exit != 0 or project_exit != 0) else 0
    elif run_project:
        return project_exit
    elif run_infra:
        return infra_exit
    return 0
