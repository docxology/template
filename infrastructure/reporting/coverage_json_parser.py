"""Parse coverage.json files for detailed per-module coverage data.

Reads the JSON output from pytest-cov and extracts file-level and
overall coverage statistics.
"""

import json
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def _nonnegative_int(value: Any) -> int | None:
    """Return *value* as a non-negative integer, excluding booleans."""
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _coverage_summary(summary: Any) -> tuple[int | None, float | None]:
    """Read the statement count and measured percent from a Coverage.py summary."""
    if not isinstance(summary, dict):
        return None, None
    value = summary.get("percent_covered")
    percent = None
    if isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 100:
        percent = float(value)
    return _nonnegative_int(summary.get("num_statements")), percent


def _read_coverage_json(path: Path) -> dict[str, Any] | None:
    try:
        with path.open(encoding="utf-8") as stream:
            data = json.load(stream)
    except FileNotFoundError:
        logger.debug(f"Coverage JSON file not found: {path}")
        return None
    except (json.JSONDecodeError, OSError, UnicodeError) as error:
        logger.warning(f"Failed to parse coverage JSON file {path}: {error}")
        return None
    if not isinstance(data, dict):
        logger.warning(f"Coverage JSON file must contain an object: {path}")
        return None
    return data


def read_coverage_total(path: Path) -> float | None:
    """Return the measured Coverage.py total, including zero, when available."""
    data = _read_coverage_json(path)
    return _coverage_summary(data.get("totals"))[1] if data is not None else None


def parse_coverage_json(coverage_json_path: Path) -> dict[str, Any] | None:
    """Parse coverage.json file for detailed per-module coverage data.

    Args:
        coverage_json_path: Path to coverage.json file

    Returns:
        Dictionary with detailed coverage information by module, or None if file not found
    """
    coverage_data = _read_coverage_json(coverage_json_path)
    if coverage_data is None:
        return None

    # Extract file-level coverage information
    file_coverage = {}
    for file_path, file_data in coverage_data.get("files", {}).items():
        # Calculate coverage percentage for this file
        executed_lines = len(file_data.get("executed_lines", []))
        missing_lines = len(file_data.get("missing_lines", []))
        excluded_lines = len(file_data.get("excluded_lines", []))

        # Coverage.py excludes ``excluded_lines`` from both
        # ``num_statements`` and the percentage denominator. Prefer its
        # canonical summary (which also reflects branch coverage when
        # enabled), with a line-only fallback for older/minimal JSON.
        total_lines, coverage_percent = _coverage_summary(file_data.get("summary"))
        if total_lines is None:
            total_lines = executed_lines + missing_lines
        if coverage_percent is None:
            coverage_percent = (executed_lines / total_lines) * 100 if total_lines > 0 else 0.0

        file_coverage[file_path] = {
            "coverage_percent": coverage_percent,
            "executed_lines": executed_lines,
            "missing_lines": missing_lines,
            "excluded_lines": excluded_lines,
            "total_lines": total_lines,
        }

    # Calculate overall coverage
    total_executed = sum(int(data["executed_lines"]) for data in file_coverage.values())
    total_missing = sum(int(data["missing_lines"]) for data in file_coverage.values())
    total_excluded = sum(int(data["excluded_lines"]) for data in file_coverage.values())
    official_total_lines, overall_coverage = _coverage_summary(coverage_data.get("totals"))
    overall_total_lines: int = (
        official_total_lines if official_total_lines is not None else total_executed + total_missing
    )
    if overall_coverage is None:
        overall_coverage = (total_executed / overall_total_lines * 100) if overall_total_lines > 0 else 0.0

    return {
        "overall_coverage": overall_coverage,
        "total_executed": total_executed,
        "total_missing": total_missing,
        "total_excluded": total_excluded,
        "total_lines": overall_total_lines,
        "file_coverage": file_coverage,
    }
