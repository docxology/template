"""Stage 01 test execution summary reporting (logging and human-readable output)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from infrastructure.core.logging.constants import BANNER_WIDTH, TABLE_WIDTH
from infrastructure.core.logging.helpers import format_duration as _format_duration
from infrastructure.core.logging.utils import get_logger, log_header, log_success
from infrastructure.reporting.coverage_reporter import (
    analyze_coverage_gaps,
    format_coverage_status,
    format_failure_suggestions,
)

logger = get_logger(__name__)


def _report_suite_failure(
    suite_name: str,
    results: Mapping[str, Any],
    project_name: str = "",
) -> None:
    """Log failure details and fix suggestions for a test suite."""
    failed = results.get("failed", 0)
    skipped = results.get("skipped", 0)
    warnings = results.get("warnings", 0)
    logger.info("%s Results:", suite_name)
    logger.info("  ✗ Failed: %s test(s) failed", failed)
    if skipped > 0:
        logger.info("  ⚠ Skipped: %s", skipped)
    if warnings > 0:
        logger.info("  ⚠ Warnings: %s", warnings)

    failed_tests = results.get("failed_tests", [])
    if failed_tests:
        logger.info("")
        logger.info("  📋 Failed Tests:")
        for i, failure in enumerate(failed_tests[:5], 1):
            logger.info("    %d. %s", i, failure["test"])
            if failure["error_type"] != "Unknown":
                logger.info(
                    "       %s: %s",
                    failure["error_type"],
                    failure["error_message"][:60] + ("..." if len(failure["error_message"]) > 60 else ""),
                )
        if len(failed_tests) > 5:
            logger.info("    ... and %d more failures", len(failed_tests) - 5)

    logger.info("")
    logger.info("  🔧 Quick Fix Suggestions:")
    suite_key = "infrastructure" if suite_name == "Infrastructure" else "project"
    for suggestion in format_failure_suggestions(failed_tests, suite_key, project_name):
        logger.info(suggestion)


def _report_suite_success(
    suite_name: str,
    results: Mapping[str, Any],
    threshold: float,
    report: dict,
) -> None:
    """Log success details for a test suite."""
    passed = results.get("passed", 0)
    skipped = results.get("skipped", 0)
    coverage = results.get("coverage_percent", 0)
    warnings = results.get("warnings", 0)
    logger.info("%s Results:", suite_name)
    logger.info("  ✓ Passed: %s", passed)
    if skipped > 0:
        logger.info("  ⚠ Skipped: %s", skipped)
    if warnings > 0:
        logger.info("  ⚠ Warnings: %s", warnings)
    logger.info("  📊 Coverage: %s", format_coverage_status(coverage, threshold))
    if coverage < threshold:
        for suggestion in analyze_coverage_gaps(results, threshold, suite_name, report):
            logger.info("    %s", suggestion)
    phases = results.get("execution_phases", {})
    if phases:
        logger.info("  ⏱ Duration: %s", _format_duration(sum(phases.values())))


def report_results(
    infra_exit: int,
    project_exit: int,
    infra_results: Mapping[str, Any],
    project_results: Mapping[str, Any],
    report: dict,
    project_name: str = "project",
) -> None:
    """Report comprehensive test execution results with detailed breakdowns."""
    log_header("Test Execution Summary", logger)

    if infra_results.get("collection_errors", 0) > 0:
        logger.info("")
        logger.info("⚠️  Collection Errors: %s", infra_results["collection_errors"])
        logger.info("   Tests discovered: %s", infra_results.get("discovery_count", 0))
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
                "Infrastructure: ✓ PASSED (%s/%s tests, %.1f%% coverage)",
                infra_passed,
                infra_total,
                infra_coverage,
            )
        else:
            infra_failed = infra_results.get("failed", 0)
            logger.info("Infrastructure: ⚠ WARNING (%s test(s) failed, but continuing)", infra_failed)

        logger.info(
            "Project:       ✓ PASSED (%s/%s tests, %.1f%% coverage)",
            project_passed,
            project_total,
            project_coverage,
        )
        logger.info("-" * TABLE_WIDTH)
        logger.info("Total:         ✓ PASSED (%s/%s tests)", total_passed, total_tests)
        if infra_was_run:
            logger.info("Coverage:      Infrastructure: %.1f%% | Project: %.1f%%", infra_coverage, project_coverage)
        else:
            logger.info("Coverage:      Infrastructure: N/A | Project: %.1f%%", project_coverage)

        infra_duration = sum(infra_results.get("execution_phases", {}).values())
        project_duration = sum(project_results.get("execution_phases", {}).values())
        total_duration = infra_duration + project_duration
        if total_duration > 0:
            logger.info("Duration:      %s", _format_duration(total_duration))

        logger.info("=" * BANNER_WIDTH)
        log_success("All tests passed - ready for analysis", logger)
    else:
        if infra_exit == 0:
            logger.info(
                "Infrastructure: ✓ PASSED (%s/%s tests, %.1f%% coverage)",
                infra_passed,
                infra_total,
                infra_coverage,
            )
        else:
            infra_failed = infra_results.get("failed", 0)
            logger.info("Infrastructure: ✗ FAILED (%s test(s) failed)", infra_failed)

        logger.info("Project:       ✗ FAILED (%s test(s) failed)", project_results.get("failed", 0))
        logger.info("-" * TABLE_WIDTH)
        logger.info("Total:         ✗ FAILED (project tests failed)")
        logger.error("Project tests failed - pipeline cannot continue until tests pass")
        logger.info("Fix the failing tests shown above and re-run the pipeline")
        logger.info("Run 'pytest projects/%s/tests/ -v' for detailed failure information", project_name)


def report_infra_only_results(infra_exit: int, infra_results: Mapping[str, Any]) -> None:
    """Log infrastructure-only pipeline completion (no project test phase)."""
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
                logger.info("    %d. %s", i, failure["test"])
                if failure["error_type"] != "Unknown":
                    logger.info("       %s: %s", failure["error_type"], failure["error_message"][:60])


__all__ = [
    "_report_suite_failure",
    "_report_suite_success",
    "report_infra_only_results",
    "report_results",
]
