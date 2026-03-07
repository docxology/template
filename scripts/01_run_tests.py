#!/usr/bin/env python3
"""Test suite orchestrator script.

This thin orchestrator runs the complete test suite for the project:
1. Runs infrastructure tests with 60%+ coverage
2. Runs project tests with 90%+ coverage
3. Reports test results
4. Validates test infrastructure

Stage 01 of the pipeline orchestration.

Note: For separate infrastructure/project test runs, use ./run.sh which
provides an interactive menu with options 1 (infrastructure) and 2 (project).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, log_success, log_header, log_substep, log_live_resource_usage
from infrastructure.core.config_loader import get_testing_config
from infrastructure.core.file_operations import clean_coverage_files
from infrastructure.reporting.coverage_reporter import (
    generate_test_report,
    save_test_report as save_test_report_to_files,
    format_coverage_status,
    analyze_coverage_gaps,
    format_failure_suggestions,
)
from infrastructure.core.logging_helpers import format_duration as _format_duration
from infrastructure.core.environment import get_python_command, check_uv_available
from infrastructure.reporting.coverage_parser import check_cov_datafile_support
from infrastructure.reporting.test_runner import TestSuiteConfig, run_test_suite


# Set up logger for this module
logger = get_logger(__name__)

_DISCOVERY_PATTERNS = [
    r"(\d+)\s+tests?\s+collected",
    r"collected\s+(\d+)\s+items?",
    r"found\s+(\d+)\s+tests?",
    r"(\d+)\s+tests?\s+found",
]


def _discover_tests(cmd: list[str], repo_root: Path, env: dict, label: str) -> None:
    """Run pytest --collect-only and log the discovered test count."""
    discovery_cmd = cmd.copy()
    discovery_cmd.insert(-1, "--collect-only")
    log_substep(f"Discovering {label} tests...")
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
                    continue
        if test_count is not None:
            log_success(f"Discovered {test_count} {label} tests")
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
) -> tuple[int, dict]:
    """Execute infrastructure test suite with coverage."""
    import shutil

    start_time = time.time()
    project_root = repo_root / "projects" / project_name

    clean_coverage_files(repo_root)

    testing_config = get_testing_config(repo_root)
    infra_threshold = testing_config.infra_coverage_threshold

    log_substep(f"Running infrastructure tests ({infra_threshold}% coverage threshold)...")
    if not include_ollama_tests:
        log_substep(
            "(Skipping LLM integration tests - run separately with: pytest -m requires_ollama)"
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

    _discover_tests(cmd, repo_root, env, "infrastructure")

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
    repo_root: Path, project_name: str = "project", quiet: bool = True, include_slow: bool = False
) -> tuple[int, dict]:
    """Execute project test suite with coverage."""
    import shutil

    start_time = time.time()
    project_root = repo_root / "projects" / project_name

    clean_coverage_files(repo_root)

    testing_config = get_testing_config(repo_root)
    project_threshold = testing_config.project_coverage_threshold

    log_substep(
        f"Running project tests for '{project_name}' ({project_threshold}% coverage threshold)..."
    )
    logger.info(f"Test path: {project_root / 'tests'}")
    logger.info(f"Coverage target: projects/{project_name}/src ({project_threshold}% minimum)")

    project_cov_config = project_root / "pyproject.toml"
    # Point coverage to the project's pyproject.toml so all subprocess coverage trackers
    # (spawned by integration tests) use the same branch=true setting. Without this,
    # subprocesses fall back to branch=false and combine() crashes with DataError.
    if check_uv_available():
        cmd = get_python_command() + [
            "-m", "pytest",
            f"projects/{project_name}/tests",
            f"--cov=projects/{project_name}/src",
            f"--cov-config={project_cov_config}",
        ]
    else:
        cmd = [sys.executable, "-m", "pytest",
               f"projects/{project_name}/tests",
               f"--cov=projects/{project_name}/src",
               f"--cov-config={project_cov_config}"]

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

    _discover_tests(cmd, repo_root, env, f"project '{project_name}'")

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
                    f"       {failure['error_type']}: {failure['error_message'][:60]}{'...' if len(failure['error_message']) > 60 else ''}"  # noqa: E501
                )
        if len(failed_tests) > 5:
            logger.info(f"    ... and {len(failed_tests) - 5} more failures")

    logger.info("")
    logger.info("  🔧 Quick Fix Suggestions:")
    suite_key = "infrastructure" if suite_name == "Infrastructure" else "project"
    for suggestion in format_failure_suggestions(failed_tests, suite_key, project_name):
        logger.info(suggestion)


def report_results(
    infra_exit: int,
    project_exit: int,
    infra_results: dict,
    project_results: dict,
    report: dict,
    project_name: str = "project",
) -> None:
    """Report comprehensive test execution results with detailed breakdowns.

    Args:
        infra_exit: Infrastructure test exit code
        project_exit: Project test exit code
        infra_results: Infrastructure test results
        project_results: Project test results
        report: Complete test report with detailed metrics
        project_name: Name of the project (for debug command suggestions)
    """

    log_header("Test Execution Summary", logger)

    # Check for collection errors
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

    # Infrastructure summary
    logger.info("")  # Add spacing
    # Check if infrastructure tests were actually run
    infra_was_run = infra_results.get("total", 0) > 0 or infra_exit != 0

    if not infra_was_run:
        # Infrastructure tests were skipped
        logger.info("Infrastructure Results:")
        logger.info("  ⏭ Skipped (not run in this execution)")
        logger.info("  📊 Coverage: N/A (tests not executed)")
    elif infra_exit == 0:
        passed = infra_results.get("passed", 0)
        failed = infra_results.get("failed", 0)
        skipped = infra_results.get("skipped", 0)
        coverage = infra_results.get("coverage_percent", 0)

        logger.info("Infrastructure Results:")
        logger.info(f"  ✓ Passed: {passed}")
        if skipped > 0:
            logger.info(f"  ⚠ Skipped: {skipped}")
        warnings = infra_results.get("warnings", 0)
        if warnings > 0:
            logger.info(f"  ⚠ Warnings: {warnings}")
        logger.info(f"  📊 Coverage: {format_coverage_status(coverage, 60.0)}")

        # Show coverage improvement suggestions if below threshold
        if coverage < 60.0:
            suggestions = analyze_coverage_gaps(infra_results, 60.0, "Infrastructure", report)
            for suggestion in suggestions:
                logger.info(f"    {suggestion}")

        # Show execution phases if available
        phases = infra_results.get("execution_phases", {})
        if phases:
            total_exec_time = sum(phases.values())
            logger.info(f"  ⏱ Duration: {_format_duration(total_exec_time)}")
    else:
        _report_suite_failure("Infrastructure", infra_results)

    # Project summary
    logger.info("")  # Add spacing
    if project_exit == 0:
        passed = project_results.get("passed", 0)
        failed = project_results.get("failed", 0)
        skipped = project_results.get("skipped", 0)
        coverage = project_results.get("coverage_percent", 0)

        logger.info("Project Results:")
        logger.info(f"  ✓ Passed: {passed}")
        if skipped > 0:
            logger.info(f"  ⚠ Skipped: {skipped}")
        warnings = project_results.get("warnings", 0)
        if warnings > 0:
            logger.info(f"  ⚠ Warnings: {warnings}")
        logger.info(f"  📊 Coverage: {format_coverage_status(coverage, 90.0)}")

        # Show coverage improvement suggestions if below threshold
        if coverage < 90.0:
            suggestions = analyze_coverage_gaps(project_results, 90.0, "Project", report)
            for suggestion in suggestions:
                logger.info(f"    {suggestion}")

        # Show execution phases if available
        phases = project_results.get("execution_phases", {})
        if phases:
            total_exec_time = sum(phases.values())
            logger.info(f"  ⏱ Duration: {_format_duration(total_exec_time)}")
    else:
        _report_suite_failure("Project", project_results, project_name)

    # Overall summary
    logger.info("")  # Add spacing
    logger.info("=" * 64)

    infra_passed = infra_results.get("passed", 0)
    infra_total = infra_results.get("total", 0)
    infra_coverage = infra_results.get("coverage_percent", 0)

    project_passed = project_results.get("passed", 0)
    project_total = project_results.get("total", 0)
    project_coverage = project_results.get("coverage_percent", 0)

    total_passed = infra_passed + project_passed
    total_tests = infra_total + project_total

    # Determine overall success based on project tests (infrastructure is optional)
    overall_success = project_exit == 0

    if overall_success:
        # Report infrastructure status separately
        if not infra_was_run:
            logger.info(
                "Infrastructure: ⏭ SKIPPED (intentionally skipped - use --infra-only to run infrastructure tests)"  # noqa: E501
            )
        elif infra_exit == 0:
            logger.info(
                "Infrastructure: ✓ PASSED "
                f"({infra_passed}/{infra_total} tests, {infra_coverage:.1f}% coverage)"
            )
        else:
            infra_failed = infra_results.get("failed", 0)
            logger.info(
                f"Infrastructure: ⚠ WARNING ({infra_failed} test(s) failed, but continuing)"
            )

        logger.info(
            f"Project:       ✓ PASSED "
            f"({project_passed}/{project_total} tests, {project_coverage:.1f}% coverage)"
        )
        logger.info("-" * 64)
        logger.info(f"Total:         ✓ PASSED ({total_passed}/{total_tests} tests)")
        if infra_was_run:
            logger.info(
                f"Coverage:      Infrastructure: {infra_coverage:.1f}% | Project: {project_coverage:.1f}%"  # noqa: E501
            )
        else:
            logger.info(f"Coverage:      Infrastructure: N/A | Project: {project_coverage:.1f}%")

        # Calculate total duration
        infra_duration = sum(infra_results.get("execution_phases", {}).values())
        project_duration = sum(project_results.get("execution_phases", {}).values())
        total_duration = infra_duration + project_duration
        if total_duration > 0:
            logger.info(f"Duration:      {_format_duration(total_duration)}")

        logger.info("=" * 64)
        log_success("All tests passed - ready for analysis", logger)
    else:
        # Project tests failed - this is fatal
        if infra_exit == 0:
            logger.info(
                "Infrastructure: ✓ PASSED "
                f"({infra_passed}/{infra_total} tests, {infra_coverage:.1f}% coverage)"
            )
        else:
            infra_failed = infra_results.get("failed", 0)
            logger.info(f"Infrastructure: ✗ FAILED ({infra_failed} test(s) failed)")

        logger.info(f"Project:       ✗ FAILED ({project_results.get('failed', 0)} test(s) failed)")
        logger.info("-" * 64)
        logger.info("Total:         ✗ FAILED (project tests failed)")
        logger.error("Project tests failed - pipeline cannot continue until tests pass")
        logger.info("Fix the failing tests shown above and re-run the pipeline")
        logger.info(
            "Run 'pytest projects/{project_name}/tests/ -v' for detailed failure information"
        )


def main() -> int:
    """Execute test suite orchestration.

    Runs both infrastructure and project tests in sequence.
    Infrastructure test failures are reported but don't fail the pipeline.

    Returns:
        Exit code (0=project tests passed, 1=project tests failed)
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run test suite")
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress individual test names (default: verbose mode)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show individual test names (deprecated/default)",
    )
    parser.add_argument(
        "--project",
        default="project",
        help="Project name in projects/ directory (default: project)",
    )
    parser.add_argument(
        "--include-slow",
        action="store_true",
        help="Include slow tests (normally skipped for faster execution)",
    )
    parser.add_argument(
        "--infra-only",
        action="store_true",
        help="Run only infrastructure tests (skip project tests)",
    )
    parser.add_argument(
        "--project-only",
        action="store_true",
        help="Run only project tests (skip infrastructure tests)",
    )
    parser.add_argument(
        "--include-ollama-tests",
        action="store_true",
        help="Include Ollama-dependent tests (requires Ollama server running)",
    )
    args = parser.parse_args()

    # Validate mutually exclusive flags
    if args.infra_only and args.project_only:
        parser.error("--infra-only and --project-only cannot be used together")

    quiet = args.quiet

    # Determine execution mode based on flags
    run_infra = not args.project_only  # Run infra unless --project-only specified
    run_project = not args.infra_only  # Run project unless --infra-only specified

    log_header(f"STAGE 01: Run Tests (Project: {args.project})", logger)

    # Log resource usage at start
    log_live_resource_usage("Test stage start", logger)

    repo_root = Path(__file__).parent.parent

    # Initialize result variables
    infra_exit, infra_results = 0, {}
    project_exit, project_results = 0, {}

    # Phase 1: Infrastructure Tests (run unless --project-only specified)
    if run_infra:
        phase_title = "Infrastructure Tests" if run_project else "Infrastructure Tests (Only)"
        log_header(f"Phase 1/{1 + int(run_project)}: {phase_title}")

        # Run infrastructure tests first (but don't fail the whole pipeline if they fail)
        infra_exit, infra_results = run_infrastructure_tests(
            repo_root,
            args.project,
            quiet=quiet,
            include_slow=args.include_slow,
            include_ollama_tests=args.include_ollama_tests,
        )

    # Phase 2: Project Tests (run unless --infra-only specified)
    if run_project:
        phase_num = 2 if run_infra else 1
        total_phases = 1 + int(run_infra)
        phase_title = (
            f"Project Tests ({args.project})"
            if run_infra
            else f"Project Tests ({args.project}) (Only)"
        )
        log_header(f"Phase {phase_num}/{total_phases}: {phase_title}")

        # Run project tests (even if infrastructure tests fail, for complete reporting)
        project_exit, project_results = run_project_tests(
            repo_root, args.project, quiet=quiet, include_slow=args.include_slow
        )

    # Generate and save test report with detailed coverage information
    if run_project:  # Only generate report if project tests were run (for output directory)
        report = generate_test_report(
            infra_results, project_results, repo_root, include_coverage_details=True
        )
        output_dir = repo_root / "projects" / args.project / "output" / "reports"
        save_test_report_to_files(report, output_dir)

        # Report combined results with detailed breakdowns
        report_results(
            infra_exit,
            project_exit,
            infra_results,
            project_results,
            report,
            project_name=args.project,
        )
    elif run_infra:  # Only infrastructure tests were run
        # For infra-only mode, create a minimal report
        log_header("Infrastructure Test Results", logger)
        if infra_exit == 0:
            log_success("Infrastructure tests passed", logger)
        else:
            logger.error("Infrastructure tests failed - this may affect build quality")
            logger.info(
                "Infrastructure test failures don't block the pipeline but should be addressed"
            )
            # Show detailed failure information
            failed_tests = infra_results.get("failed_tests", [])
            if failed_tests:
                logger.info("")
                logger.info("📋 Failed Tests:")
                for i, failure in enumerate(failed_tests[:5], 1):
                    logger.info(f"    {i}. {failure['test']}")
                    if failure["error_type"] != "Unknown":
                        logger.info(
                            f"       {failure['error_type']}: {failure['error_message'][:60]}{'...' if len(failure['error_message']) > 60 else ''}"  # noqa: E501
                        )
                if len(failed_tests) > 5:
                    logger.info(f"    ... and {len(failed_tests) - 5} more failures")

    # Log resource usage at end
    log_live_resource_usage("Test stage end", logger)

    # Return exit code based on execution mode
    if run_project and run_infra:
        # Both tests run - return failure only if project tests failed (infrastructure tests are optional)  # noqa: E501
        return 1 if project_exit != 0 else 0
    elif run_project:
        # Project tests only
        return project_exit
    elif run_infra:
        # Infrastructure tests only
        return infra_exit
    else:
        # Should not happen due to argument validation
        return 0


if __name__ == "__main__":
    exit(main())
