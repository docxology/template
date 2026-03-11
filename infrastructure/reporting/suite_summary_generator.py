"""Test summary generator for the full repository test suite.

This module aggregates test results from infrastructure and active project
tests to create a comprehensive summary report in JSON and Markdown formats.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

from infrastructure.core.config_loader import get_testing_config
from infrastructure.core.logging_utils import get_logger
from infrastructure.project.discovery import discover_projects


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


logger = get_logger(__name__)


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
    """
    root = repo_root or Path.cwd()
    _base = project_dir if project_dir is not None else root / "projects" / project_name
    results_file = _base / "output" / "reports" / "test_results.json"

    if results_file.exists():
        try:
            with open(results_file, "r") as f:
                data = json.load(f)
                # Extract project results from the nested structure
                if "project" in data:
                    return data["project"]  # type: ignore
                else:
                    return data  # type: ignore
        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not load results from {results_file}: {e}")
            return {}
    else:
        logger.warning(f"Test results file not found: {results_file}")
        return {}


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


def load_infrastructure_results(repo_root: Path | None = None) -> InfraResults:
    """Load infrastructure test results from root coverage files."""
    root = repo_root or Path.cwd()
    base: InfraResults = dict(_EMPTY_INFRA_RESULTS)  # type: ignore[assignment]

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


def discover_active_projects(repo_root: Path | None = None) -> list:
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
    weighted_sum = sum(r.get("coverage_percent", 0) * r.get("total_lines", 0) for r in results_list)
    return weighted_sum / total_lines


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
        import importlib

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

    all_results = [infra_results] + list(project_results.values())
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


def generate_markdown_report(data: dict[str, Any]) -> str:
    """Generate human-readable markdown report from test data.

    Args:
        data: Test results dictionary

    Returns:
        Markdown formatted report
    """
    lines = []

    lines.append("# Full Repository Test Suite Results")
    lines.append("")
    lines.append(f"**Date**: {data['timestamp']}")
    lines.append(f"**Test Type**: {data['test_type']}")
    lines.append(f"**Overall Status**: {'PASSED' if data['overall_success'] else 'FAILED'}")
    lines.append("")

    # Summary section
    lines.append("## Summary")
    lines.append("")
    summary = data["summary"]
    lines.append(f"- **Total Tests**: {summary['total_tests']:,}")
    lines.append(f"- **Passed**: {summary['total_passed']:,}")
    lines.append(f"- **Failed**: {summary['total_failed']:,}")
    lines.append(f"- **Skipped**: {summary['total_skipped']:,}")
    lines.append(f"- **Pass Rate**: {summary['pass_rate']:.1f}%")
    lines.append(f"- **Weighted Coverage**: {summary['weighted_coverage_percent']:.1f}%")
    lines.append(f"- **Total Duration**: {summary['total_duration_seconds']:.1f}s")
    lines.append("")

    # Infrastructure results
    lines.append("## Infrastructure Tests")
    lines.append("")
    infra = data["infrastructure"]
    status = "PASSED" if infra["exit_code"] == 0 else "FAILED"
    lines.append(f"**Status**: {status}")
    lines.append(
        f"**Tests**: {infra['passed']:,} passed, {infra['failed']:,} failed, {infra['skipped']:,} skipped"  # noqa: E501
    )
    if infra["warnings"] > 0:
        lines.append(f"**Warnings**: {infra['warnings']:,}")
    lines.append(
        f"**Coverage**: {infra['coverage_percent']:.1f}% ({'meets' if infra['meets_threshold'] else 'below'} 60% threshold)"  # noqa: E501
    )
    lines.append(f"**Lines**: {infra['covered_lines']:,}/{infra['total_lines']:,} covered")
    lines.append(f"**Duration**: {infra['duration_seconds']:.1f}s")
    lines.append("")

    # Project results (dynamic)
    projects = data.get("projects", {})
    for project_name, proj_data in sorted(projects.items()):
        # Format project name for display (convert underscores to spaces, title case)
        display_name = project_name.replace("_", " ").title()
        lines.append(f"## {display_name} Tests")
        lines.append("")
        status = "PASSED" if proj_data["exit_code"] == 0 else "FAILED"
        lines.append(f"**Status**: {status}")
        lines.append(
            f"**Tests**: {proj_data['passed']:,} passed, {proj_data['failed']:,} failed, {proj_data['skipped']:,} skipped"  # noqa: E501
        )
        if proj_data["warnings"] > 0:
            lines.append(f"**Warnings**: {proj_data['warnings']:,}")
        lines.append(
            f"**Coverage**: {proj_data['coverage_percent']:.1f}% ({'meets' if proj_data['meets_threshold'] else 'below'} 90% threshold)"  # noqa: E501
        )
        lines.append(
            f"**Lines**: {proj_data['covered_lines']:,}/{proj_data['total_lines']:,} covered"
        )
        lines.append(f"**Duration**: {proj_data['duration_seconds']:.1f}s")
        lines.append("")

    # Metadata
    lines.append("## Test Configuration")
    lines.append("")
    meta = data["metadata"]
    lines.append(
        f"- **Infrastructure Tests**: {'Included' if meta['infrastructure_tests_included'] else 'Excluded'}"  # noqa: E501
    )
    lines.append(
        f"- **Integration Tests**: {'Included' if meta['integration_tests_included'] else 'Excluded'}"  # noqa: E501
    )
    lines.append(f"- **Slow Tests**: {'Included' if meta['slow_tests_included'] else 'Excluded'}")
    lines.append(
        f"- **Ollama Tests**: {'Included' if meta['ollama_tests_included'] else 'Excluded'}"
    )
    lines.append(
        f"- **Ollama Server**: {'Available' if meta['ollama_server_available'] else 'Unavailable'}"
    )
    if "active_projects" in meta:
        lines.append(f"- **Active Projects**: {', '.join(meta['active_projects'])}")
    lines.append("")

    # Files generated
    lines.append("## Generated Files")
    lines.append("")
    for file in data["files_generated"]:
        lines.append(f"- `{file}`")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*Report generated by `scripts/generate_test_summary.py`*")

    return "\n".join(lines)


def _format_console_summary(report_data: dict[str, Any]) -> str:
    """Format a console-friendly summary string from report data."""
    summary = report_data["summary"]
    infra = report_data["infrastructure"]
    projects = report_data.get("projects", {})
    lines = [
        "",
        "=" * 80,
        "FULL REPOSITORY TEST SUITE SUMMARY",
        "=" * 80,
        f"Overall Status: {'PASSED' if report_data['overall_success'] else 'FAILED'}",
        f"Total Tests: {summary['total_tests']:,} ({summary['pass_rate']:.1f}% pass rate)",
        f"Total Duration: {summary['total_duration_seconds']:.1f}s",
        f"Weighted Coverage: {summary['weighted_coverage_percent']:.1f}%",
        "",
        "Suite Breakdown:",
        f"  Infrastructure:          {infra['passed']:,} passed ({infra['coverage_percent']:.1f}% coverage)",  # noqa: E501
    ]
    for project_name, proj_data in sorted(projects.items()):
        display_name = project_name[:20] + "..." if len(project_name) > 23 else project_name
        lines.append(
            f"  {display_name:<24} {proj_data['passed']:,} passed ({proj_data['coverage_percent']:.1f}% coverage)"  # noqa: E501
        )
    lines.append("=" * 80)
    return "\n".join(lines)


def run_test_summary_generation() -> int:
    """Main entry point for generating test summary reports."""
    print("Generating comprehensive test summary reports...")

    # Generate the summary data
    report_data = generate_summary_report()

    # Save JSON report
    json_file = Path("test_results_summary.json")
    try:
        with open(json_file, "w") as f:
            json.dump(report_data, f, indent=2)
        print(f"✅ JSON report saved: {json_file}")
    except OSError as e:
        logger.error(f"Failed to write JSON report to {json_file}: {e}")
        raise

    # Generate and save markdown report
    markdown_content = generate_markdown_report(report_data)
    md_file = Path("test_results_summary.md")
    try:
        with open(md_file, "w") as f:
            f.write(markdown_content)
        print(f"✅ Markdown report saved: {md_file}")
    except OSError as e:
        logger.error(f"Failed to write markdown report to {md_file}: {e}")
        raise

    print(_format_console_summary(report_data))

    return 0
