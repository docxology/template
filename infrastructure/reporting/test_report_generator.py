"""Test report generation and persistence.

Generates structured test reports from infrastructure and project test results,
and saves them in JSON and Markdown formats.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger

from .coverage_json_parser import parse_coverage_json

logger = get_logger(__name__)


def generate_test_report(
    infra_results: dict[str, Any],
    project_results: dict[str, Any],
    repo_root: Path,
    include_coverage_details: bool = True,
) -> dict[str, Any]:
    """Generate structured test report from infrastructure and project test results."""
    report: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "infrastructure": infra_results,
        "project": project_results,
        "summary": {
            "total_passed": infra_results.get("passed", 0) + project_results.get("passed", 0),
            "total_failed": infra_results.get("failed", 0) + project_results.get("failed", 0),
            "total_skipped": infra_results.get("skipped", 0) + project_results.get("skipped", 0),
            "total_tests": infra_results.get("total", 0) + project_results.get("total", 0),
            "all_passed": (
                infra_results.get("exit_code", 0) == 0 and project_results.get("exit_code", 1) == 0
            ),
        },
    }

    # Add coverage summary
    if "coverage_percent" in infra_results:
        report["summary"]["infrastructure_coverage"] = infra_results["coverage_percent"]
    if "coverage_percent" in project_results:
        report["summary"]["project_coverage"] = project_results["coverage_percent"]

    # Add detailed coverage information if requested
    if include_coverage_details:
        coverage_details = {}

        # Try to read infrastructure coverage details
        infra_coverage_json = repo_root / "coverage_infra.json"
        infra_coverage = parse_coverage_json(infra_coverage_json)
        if infra_coverage:
            coverage_details["infrastructure"] = infra_coverage

        # Try to read project coverage details
        project_coverage_json = repo_root / "coverage_project.json"
        project_coverage = parse_coverage_json(project_coverage_json)
        if project_coverage:
            coverage_details["project"] = project_coverage

        if coverage_details:
            report["coverage_details"] = coverage_details

    return report


def save_test_report_to_files(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    """Save test report to JSON and generate Markdown summary.

    Args:
        report: Test report dictionary
        output_dir: Output directory path (will be created if needed)

    Returns:
        Tuple of (json_path, md_path) for the saved files
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON report
    json_path = output_dir / "test_results.json"
    try:
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2)
    except OSError as e:
        logger.error(f"Failed to write test report JSON: {e}")
        raise

    logger.info(f"Test report saved: {json_path}")

    # Generate markdown summary
    md_path = output_dir / "test_results.md"
    try:
        with open(md_path, "w") as f:
            f.write("# Test Results Summary\n\n")
            f.write(f"Generated: {report['timestamp']}\n\n")
            f.write("## Infrastructure Tests\n\n")
            f.write(f"- Passed: {report['infrastructure'].get('passed', 0)}\n")
            f.write(f"- Failed: {report['infrastructure'].get('failed', 0)}\n")
            f.write(f"- Skipped: {report['infrastructure'].get('skipped', 0)}\n")
            if "coverage_percent" in report["infrastructure"]:
                f.write(f"- Coverage: {report['infrastructure']['coverage_percent']:.2f}%\n")
            f.write("\n## Project Tests\n\n")
            f.write(f"- Passed: {report['project'].get('passed', 0)}\n")
            f.write(f"- Failed: {report['project'].get('failed', 0)}\n")
            f.write(f"- Skipped: {report['project'].get('skipped', 0)}\n")
            if "coverage_percent" in report["project"]:
                f.write(f"- Coverage: {report['project']['coverage_percent']:.2f}%\n")
            f.write("\n## Summary\n\n")
            f.write(f"- Total Passed: {report['summary']['total_passed']}\n")
            f.write(f"- Total Failed: {report['summary']['total_failed']}\n")
            f.write(f"- Total Tests: {report['summary']['total_tests']}\n")
            f.write(
                f"- Status: {'✅ PASSED' if report['summary']['all_passed'] else '❌ FAILED'}\n"
            )
    except OSError as e:
        logger.error(f"Failed to write test report markdown: {e}")
        raise

    logger.info(f"Test summary saved: {md_path}")

    return (json_path, md_path)
