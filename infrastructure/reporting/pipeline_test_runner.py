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
from pathlib import Path
from typing import TypedDict

from infrastructure.core.logging.utils import get_logger, log_success, log_header, log_substep
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
from infrastructure.core.runtime.environment import get_python_command
from infrastructure.reporting.coverage_parser import check_cov_datafile_support
from infrastructure.reporting.suite_runner import TestSuiteConfig, run_test_suite

logger = get_logger(__name__)


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


def _log_discovered_tests(cmd: list[str], repo_root: Path, env: dict, label: str) -> None:
    """Run pytest --collect-only and log the discovered test count."""
    discovery_cmd = cmd.copy()
    discovery_cmd.append("--collect-only")
    log_substep(f"Discovering {label} tests...", logger)
    try:
        result = subprocess.run(
            discovery_cmd, cwd=str(repo_root), env=env,
            capture_output=True, text=True, timeout=30,
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
    strict: bool = True,
) -> tuple[int, TestSuiteResults]:
    """Execute infrastructure test suite with coverage."""
    start_time = time.time()
    project_root = repo_root / "projects" / project_name

    clean_coverage_files(repo_root)

    testing_config = get_testing_config(repo_root)
    infra_threshold = testing_config.infra_coverage_threshold

    log_substep(f"Running infrastructure tests ({infra_threshold}% coverage threshold)...", logger)
    if not include_ollama_tests:
        log_substep(
            "(Skipping LLM integration tests - run separately with: pytest -m requires_ollama)", logger
        )
    logger.info(f"Test path: {repo_root / 'tests' / 'infra_tests'}")
    logger.info("Coverage target: infrastructure (60% minimum)")

    cmd = get_python_command() + [
        "-m",
        "pytest",
        str(repo_root / "tests" / "infra_tests"),
        str(repo_root / "tests" / "integration"),
        "--ignore=" + str(repo_root / "tests" / "integration" / "test_module_interoperability.py"),
        "--cov=infrastructure",
    ]
    if not include_ollama_tests:
        cmd.extend(["-m", "not requires_ollama"])

    env = os.environ.copy()
    cov_datafile_supported = check_cov_datafile_support()
    if cov_datafile_supported:
        cmd.append("--cov-datafile=.coverage.infra")
    else:
        env["COVERAGE_FILE"] = ".coverage.infra"

    cmd.extend([
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=json:coverage_infra.json",
        f"--cov-fail-under={infra_threshold}",
        "--tb=short",
    ])
    if not include_slow:
        cmd.extend(["-m", "not slow"])
    if quiet:
        cmd.extend(["-q"])

    pythonpath_parts = [str(repo_root), str(repo_root / "infrastructure")]
    project_src = project_root / "src"
    if project_src.exists():
        pythonpath_parts.append(str(project_src))
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    if shutil.which("uv"):
        env["PATH"] = f"{os.path.dirname(shutil.which('uv'))}:{env.get('PATH', '')}"

    _log_discovered_tests(cmd, repo_root, env, "infrastructure")

    try:
        config = TestSuiteConfig(
            label="Infrastructure",
            cmd=cmd,
            env=env,
            repo_root=repo_root,
            coverage_json_paths=[
                repo_root / "coverage_infra.json",
                repo_root / "coverage.json",
                repo_root / "htmlcov" / "coverage.json",
            ],
            coverage_threshold=infra_threshold,
            max_failures_env_var="MAX_INFRA_TEST_FAILURES",
            max_failures_config_key="max_infra_test_failures",
            quiet=quiet,
            spinner_label="Running infrastructure tests",
        )
        exit_code, test_results = run_test_suite(config)
        if strict and test_results.get("failed", 0) > 0:
            exit_code = 1
        duration = time.time() - start_time
        logger.info(f"Infrastructure test suite completed in {duration:.1f}s")
        if exit_code == 0:
            log_success("Infrastructure tests passed", logger)
        return exit_code, test_results
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Failed to run infrastructure tests after {duration:.1f}s: {e}", exc_info=True)
        return 1, {}


def run_project_tests(
    repo_root: Path,
    project_name: str = "project",
    quiet: bool = True,
    include_slow: bool = False,
    strict: bool = True,
) -> tuple[int, dict]:
    """Execute project test suite with coverage."""
    start_time = time.time()
    project_root = repo_root / "projects" / project_name

    clean_coverage_files(repo_root)

    testing_config = get_testing_config(repo_root)
    project_threshold = testing_config.project_coverage_threshold

    log_substep(
        f"Running project tests for '{project_name}' ({project_threshold}% coverage threshold)...", logger
    )
    logger.info(f"Test path: {project_root / 'tests'}")
    logger.info(f"Coverage target: projects/{project_name}/src ({project_threshold}% minimum)")

    project_cov_config = project_root / "pyproject.toml"
    cmd = get_python_command() + [
        "-m", "pytest",
        f"projects/{project_name}/tests",
        f"--cov=projects/{project_name}/src",
        f"--cov-config={project_cov_config}",
    ]

    env = os.environ.copy()
    pythonpath_parts = [str(repo_root), str(project_root)]
    if env.get("PYTHONPATH"):
        pythonpath_parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    if project_cov_config.exists():
        env["COVERAGE_PROCESS_START"] = str(project_cov_config)
    else:
        env.pop("COVERAGE_PROCESS_START", None)

    cov_datafile_supported = check_cov_datafile_support()
    if cov_datafile_supported:
        cmd.append("--cov-datafile=.coverage.project")
    else:
        env["COVERAGE_FILE"] = ".coverage.project"

    cmd.extend([
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=json:coverage_project.json",
        f"--cov-fail-under={project_threshold}",
        "--tb=short",
    ])
    if not include_slow:
        cmd.extend(["-m", "not slow"])
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
        )
        exit_code, test_results = run_test_suite(config)
        if strict and test_results.get("failed", 0) > 0:
            exit_code = 1
        duration = time.time() - start_time
        logger.info(f"Project test suite completed in {duration:.1f}s")
        if exit_code == 0:
            log_success("Project tests passed", logger)
        return exit_code, test_results
    except Exception as e:
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
    logger.info("=" * 64)

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
        logger.info("-" * 64)
        logger.info(f"Total:         ✓ PASSED ({total_passed}/{total_tests} tests)")
        if infra_was_run:
            logger.info(
                f"Coverage:      Infrastructure: {infra_coverage:.1f}% | Project: {project_coverage:.1f}%"
            )
        else:
            logger.info(f"Coverage:      Infrastructure: N/A | Project: {project_coverage:.1f}%")

        infra_duration = sum(infra_results.get("execution_phases", {}).values())
        project_duration = sum(project_results.get("execution_phases", {}).values())
        total_duration = infra_duration + project_duration
        if total_duration > 0:
            logger.info(f"Duration:      {_format_duration(total_duration)}")

        logger.info("=" * 64)
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
        logger.info("-" * 64)
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
            repo_root, project_name, quiet, include_slow, include_ollama_tests, strict
        )

    if run_project:
        phase_num = 2 if run_infra else 1
        phase_title = (
            f"Project Tests ({project_name})" if run_infra else f"Project Tests ({project_name}) (Only)"
        )
        log_header(f"Phase {phase_num}/{total_phases}: {phase_title}", logger)
        project_exit, project_results = run_project_tests(
            repo_root, project_name, quiet, include_slow, strict
        )

    if run_project:
        report = generate_test_report(
            infra_results, project_results, repo_root, include_coverage_details=True
        )
        output_dir = repo_root / "projects" / project_name / "output" / "reports"
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
