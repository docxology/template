"""Test result loading utilities for infrastructure and project test suites.

This module provides functions to load test results from JSON files
produced by the test runner and coverage tools.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict, cast

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


class InfraResults(TypedDict):
    """Infrastructure test result fields with consistent shape across all loaders."""

    passed: int
    failed: int
    skipped: int
    warnings: int
    coverage_percent: float
    total_lines: int
    covered_lines: int
    missing_lines: int
    duration_seconds: float
    exit_code: int


_EMPTY_INFRA_RESULTS: InfraResults = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "warnings": 0,
    "coverage_percent": 0.0,
    "total_lines": 0,
    "covered_lines": 0,
    "missing_lines": 0,
    "duration_seconds": 0.0,
    "exit_code": 0,
}


def load_test_results(
    project_name: str,
    repo_root: Path | None = None,
    project_dir: Path | None = None,
) -> dict[str, Any]:
    """Load test results from a project's output directory; returns {} if not found.

    Args:
        project_name: Name of the project.
        repo_root: Repository root (default: cwd).
        project_dir: Absolute path to the project directory. When provided,
            overrides ``repo_root / 'projects' / project_name``.

    Note:
        OSError and json.JSONDecodeError are caught and logged as warnings;
        returns ``{}`` rather than raising.
    """
    root = repo_root or Path.cwd()
    _base = project_dir if project_dir is not None else root / "projects" / project_name
    results_file = _base / "output" / "reports" / "test_results.json"

    if results_file.exists():
        try:
            with open(results_file, "r") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load results from {results_file}: {e}")
            return {}
        # Extract project results from the nested structure
        if "project" in data:
            return data["project"]
        return data
    else:
        logger.warning(f"Test results file not found: {results_file}")
        return {}


def load_infrastructure_results(repo_root: Path | None = None) -> InfraResults:
    """Load infrastructure test results from root coverage files."""
    root = repo_root or Path.cwd()
    base: InfraResults = cast(InfraResults, dict(_EMPTY_INFRA_RESULTS))

    infra_results_file = root / "infrastructure_validation_report.json"
    if infra_results_file.exists():
        try:
            with open(infra_results_file, "r") as f:
                data = json.load(f)
            test_results = data.get("test_results", {})
            infra_data = test_results.get("infrastructure", {})
            if infra_data:
                total = infra_data.get("total_tests", 0)
                passed = infra_data.get("passed", 0)
                skipped = infra_data.get("skipped", 0)
                return {
                    **base,
                    "passed": passed,
                    "failed": max(0, total - passed - skipped),
                    "skipped": skipped,
                    "warnings": infra_data.get("warnings", 0),
                    "coverage_percent": infra_data.get("coverage_percent", 0.0),
                    "duration_seconds": infra_data.get("duration_seconds", 0.0),
                    "exit_code": 0 if infra_data.get("status") == "PASSED" else 1,
                }
        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not load infrastructure results from validation report: {e}")

    for coverage_path in (root / "coverage_infra.json", root / "htmlcov" / "coverage.json"):
        if coverage_path.exists():
            try:
                with open(coverage_path, "r") as f:
                    coverage_data = json.load(f)
                totals = coverage_data.get("totals", {})
                return {
                    **base,
                    "coverage_percent": totals.get("percent_covered", 0.0),
                    "total_lines": totals.get("num_statements", 0),
                    "covered_lines": totals.get("covered_lines", 0),
                    "missing_lines": totals.get("missing_lines", 0),
                }
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Could not load infrastructure coverage from {coverage_path}: {e}")

    logger.warning("No infrastructure test results found")
    return base
