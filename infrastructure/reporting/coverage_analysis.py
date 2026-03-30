"""Coverage analysis and failure suggestion utilities.

Provides formatting for coverage status, gap analysis with actionable
suggestions, and failure classification with debug recommendations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

def format_coverage_status(coverage_pct: float, threshold: float) -> str:
    """Format coverage percentage with visual indicators and threshold context."""
    if coverage_pct >= threshold:
        return f"\u2713 {coverage_pct:.1f}% (meets {threshold}% threshold)"
    gap = threshold - coverage_pct
    if coverage_pct >= threshold * 0.9:
        return f"\U0001f7e1 {coverage_pct:.1f}% (close to {threshold}% threshold, {gap:.1f}% gap)"
    elif coverage_pct >= threshold * 0.8:
        return f"\u26a0\ufe0f {coverage_pct:.1f}% (below {threshold}% threshold by {gap:.1f}%)"
    else:
        return f"\u274c {coverage_pct:.1f}% (significantly below {threshold}% threshold by {gap:.1f}%)"


def analyze_coverage_gaps(
    results: dict[str, Any], threshold: float, test_type: str, report: dict[str, Any]
) -> list[str]:
    """Analyze coverage gaps and return actionable improvement suggestions."""
    suggestions = []
    coverage = results.get("coverage_percent", 0)

    if coverage < threshold:
        gap = threshold - coverage
        suggestions.append(f"\U0001f4ca {test_type} coverage is {gap:.1f}% below threshold")

        coverage_details = report.get("coverage_details", {}).get(test_type.lower(), {})
        file_coverage = coverage_details.get("file_coverage", {})

        if file_coverage:
            low_coverage_files = [
                (file_path, data["coverage_percent"])
                for file_path, data in file_coverage.items()
                if data["coverage_percent"] < 50 and data["total_lines"] > 10
            ]
            low_coverage_files.sort(key=lambda x: x[1])

            if low_coverage_files:
                suggestions.append("  \U0001f4c1 Files needing attention:")
                for file_path, file_cov in low_coverage_files[:5]:
                    file_name = Path(file_path).name
                    missing_lines = file_coverage[file_path]["missing_lines"]
                    suggestions.append(
                        f"    \u2022 {file_name}: {file_cov:.1f}% coverage ({missing_lines} uncovered lines)"  # noqa: E501
                    )

            substantial_files = [
                (file_path, data)
                for file_path, data in file_coverage.items()
                if data["total_lines"] > 100 and data["coverage_percent"] < 70
            ]
            substantial_files.sort(key=lambda x: x[1]["total_lines"], reverse=True)

            if substantial_files:
                suggestions.append("  \U0001f4ca High-impact files to prioritize:")
                for file_path, data in substantial_files[:3]:
                    file_name = Path(file_path).name
                    suggestions.append(
                        f"    \u2022 {file_name}: {data['total_lines']} lines, {data['coverage_percent']:.1f}% coverage"  # noqa: E501
                    )
        else:
            suggestions.append(
                "  \u2022 Run with --cov-report=json to enable file-level coverage suggestions"
            )

        suggestions.extend(
            [
                f"  \u2022 Target: Reach {threshold}% coverage minimum",
                "  \u2022 Run: pytest --cov-report=html && open htmlcov/index.html",
            ]
        )

    return suggestions


def format_failure_suggestions(
    failed_tests: list[dict[str, Any]], test_suite: str, project_name: str = ""
) -> list[str]:
    """Return fix suggestions based on failure patterns in failed_tests.

    Classifies failures by error type and returns actionable suggestions.
    General debug commands are parameterized by test_suite ('infrastructure' or 'project').
    """
    suggestions: list[str] = []

    has_import_errors = any("import" in str(f) or "module" in str(f).lower() for f in failed_tests)
    has_assertion_errors = any("assertion" in str(f).lower() for f in failed_tests)
    has_coverage_errors = any(
        "coverage" in str(f).lower()
        or "dataerror" in str(f).lower()
        or "no such table" in str(f).lower()
        for f in failed_tests
    )
    has_timeout_errors = any("timeout" in str(f).lower() for f in failed_tests)

    if has_import_errors:
        if test_suite == "infrastructure":
            suggestions.append(
                "    - Missing dependencies: pip install pytest-httpserver pytest-timeout"
            )
            suggestions.append(
                "    - Import path issues: check PYTHONPATH includes repository root"
            )
        else:
            suggestions.append(
                "    - Missing project dependencies: check pyproject.toml and uv sync"
            )
            suggestions.append("    - Import path issues: verify project src/ directory structure")

    if has_assertion_errors and test_suite != "infrastructure":
        suggestions.append("    - Review test assertions and expected values")
        suggestions.append("    - Check test data generation and reproducibility")

    if has_coverage_errors:
        suggestions.append(
            "    - Coverage database corruption: files automatically cleaned and retried"
        )
        suggestions.append(
            "    - If errors persist: rm -f .coverage* coverage_*.json && rerun tests"
        )
        if test_suite == "infrastructure":
            suggestions.append(
                "    - To skip coverage temporarily: pytest --no-cov tests/infra_tests/"
            )
            suggestions.append(
                "    - Coverage isolation: infrastructure and project tests use separate data files"
            )
        else:
            suggestions.append(
                "    - Coverage isolation: project tests use separate data file (.coverage.project)"
            )

    if has_timeout_errors:
        suggestions.append("    - Timeout issues: increase with --timeout=60 or PYTEST_TIMEOUT=60")
        if test_suite == "infrastructure":
            suggestions.append(
                "    - Identify slow tests: pytest --durations=10 tests/infra_tests/"
            )
            suggestions.append("    - Skip slow tests: pytest -m 'not slow' tests/infra_tests/")
        else:
            suggestions.append(
                f"    - Identify slow tests: pytest --durations=10 projects/{project_name}/tests/"
            )
            suggestions.append(
                f"    - Skip slow tests: pytest -m 'not slow' projects/{project_name}/tests/"
            )

    if test_suite == "infrastructure":
        suggestions.append(
            "    - Run individual failing tests: pytest tests/infra_tests/<test_file> -v"
        )
        suggestions.append(
            "    - Debug with full traceback: pytest tests/infra_tests/<test_file> -s --tb=long"
        )
        suggestions.append(
            "    - Run infrastructure tests only: python3 scripts/01_run_tests.py --infrastructure-only"
        )
        suggestions.append("    - Check test environment: python3 scripts/00_setup_environment.py")
    else:
        suggestions.append(
            f"    - Run individual failing tests: pytest projects/{project_name}/tests/<test_file> -v"
        )
        suggestions.append(
            f"    - Debug with full traceback: pytest projects/{project_name}/tests/<test_file> -s --tb=long"
        )
        suggestions.append(
            f"    - Run project tests only: python3 scripts/01_run_tests.py --project {project_name} --project-only"
        )
        suggestions.append(
            f"    - Check project structure: verify projects/{project_name}/src/ and tests/ exist"
        )

    return suggestions
