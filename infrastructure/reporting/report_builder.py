"""Summary report generation for the full repository test suite.

This module builds the comprehensive test summary data structure by
aggregating results from infrastructure and project test suites.
"""

from __future__ import annotations

import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Any

from infrastructure.core.config.queries import get_testing_config
from infrastructure.core.logging.utils import get_logger
from infrastructure.project.discovery import discover_projects

from .result_loaders import load_infrastructure_results, load_test_results

logger = get_logger(__name__)


def discover_active_projects(repo_root: Path | None = None) -> list[str]:
    """Discover active projects from the projects/ directory."""
    root = repo_root or Path.cwd()
    return sorted(p.name for p in discover_projects(root))


def _calculate_weighted_coverage(
    results_list: list[dict[str, Any]],
) -> float:
    """Return coverage percentage weighted by lines of code across all suites."""
    total_lines = sum(r.get("total_lines", 0) for r in results_list)
    if total_lines == 0:
        return 0.0
    weighted_sum: float = sum(
        float(r.get("coverage_percent", 0)) * float(r.get("total_lines", 0))
        for r in results_list
    )
    return weighted_sum / float(total_lines)


def _aggregate_counts(results_list: list[dict[str, Any]]) -> dict[str, Any]:
    """Return summed passed/failed/skipped/duration across all suites."""
    total_passed = sum(r.get("passed", 0) for r in results_list)
    total_failed = sum(r.get("failed", 0) for r in results_list)
    total_skipped = sum(r.get("skipped", 0) for r in results_list)
    total_tests = total_passed + total_failed + total_skipped
    total_duration = sum(r.get("duration_seconds", 0) for r in results_list)
    return {
        "total_tests": total_tests,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "total_skipped": total_skipped,
        "pass_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
        "total_duration_seconds": total_duration,
    }


def _is_ollama_available() -> bool:
    """Return True if the ollama package is importable."""
    try:
        return importlib.util.find_spec("ollama") is not None
    except (ImportError, ValueError):  # importlib.util.find_spec may raise for invalid names
        return False


def generate_summary_report(repo_root: Path | None = None) -> dict[str, Any]:
    """Generate comprehensive test summary report."""
    root = repo_root or Path.cwd()
    timestamp = datetime.now().isoformat()
    active_projects = discover_active_projects(root)

    infra_results = load_infrastructure_results(root)
    project_results = {name: load_test_results(name, root) for name in active_projects}

    # InfraResults is a TypedDict (structural subtype of dict[str, Any])
    all_results: list[dict[str, Any]] = [infra_results, *project_results.values()]  # type: ignore[list-item]
    counts = _aggregate_counts(all_results)
    weighted_coverage = _calculate_weighted_coverage(all_results)

    overall_success = all(r.get("exit_code", 1) == 0 for r in all_results)
    infra_coverage = infra_results.get("coverage_percent", 0)
    infra_lines = infra_results.get("total_lines", 0)
    testing_config = get_testing_config(root)

    report: dict[str, Any] = {
        "timestamp": timestamp,
        "test_type": "full_repository_suite",
        "overall_success": overall_success,
        "summary": {
            **counts,
            "weighted_coverage_percent": round(weighted_coverage, 2),
        },
        "infrastructure": {
            "passed": infra_results.get("passed", 0),
            "failed": infra_results.get("failed", 0),
            "skipped": infra_results.get("skipped", 0),
            "warnings": infra_results.get("warnings", 0),
            "coverage_percent": infra_coverage,
            "total_lines": infra_lines,
            "covered_lines": infra_results.get("covered_lines", 0),
            "missing_lines": infra_results.get("missing_lines", 0),
            "duration_seconds": infra_results.get("duration_seconds", 0),
            "exit_code": infra_results.get("exit_code", 1),
            "meets_threshold": infra_coverage >= testing_config.infra_coverage_threshold,
        },
        "projects": {},
        "metadata": {
            "test_run_type": "all_test_types_included",
            "infrastructure_tests_included": True,
            "integration_tests_included": True,
            "slow_tests_included": True,
            "ollama_tests_included": True,
            "ollama_server_available": _is_ollama_available(),
            "test_command": "scripts/01_run_tests.py --include-slow --include-ollama-tests --verbose",  # noqa: E501
            "active_projects": active_projects,
        },
        "files_generated": [
            "test_results_summary.json",
            "test_results_summary.md",
            "coverage_infra.json",
            "htmlcov/index.html (infrastructure)",
        ],
    }

    for project_name, results in project_results.items():
        proj_coverage = results.get("coverage_percent", 0)
        report["projects"][project_name] = {
            "passed": results.get("passed", 0),
            "failed": results.get("failed", 0),
            "skipped": results.get("skipped", 0),
            "warnings": results.get("warnings", 0),
            "coverage_percent": proj_coverage,
            "total_lines": results.get("total_lines", 0),
            "covered_lines": results.get("covered_lines", 0),
            "missing_lines": results.get("missing_lines", 0),
            "duration_seconds": results.get("duration_seconds", 0),
            "exit_code": results.get("exit_code", 1),
            "meets_threshold": proj_coverage >= testing_config.project_coverage_threshold,
        }
        report["files_generated"].append(f"coverage_project.json ({project_name})")
        report["files_generated"].append(f"htmlcov/index.html ({project_name})")

    return report
