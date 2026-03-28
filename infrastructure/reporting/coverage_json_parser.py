"""Parse coverage.json files for detailed per-module coverage data.

Reads the JSON output from pytest-cov and extracts file-level and
overall coverage statistics.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


def parse_coverage_json(coverage_json_path: Path) -> dict[str, Any] | None:
    """Parse coverage.json file for detailed per-module coverage data.

    Args:
        coverage_json_path: Path to coverage.json file

    Returns:
        Dictionary with detailed coverage information by module, or None if file not found
    """
    if not coverage_json_path.exists():
        logger.debug(f"Coverage JSON file not found: {coverage_json_path}")
        return None

    try:
        with open(coverage_json_path, "r") as f:
            coverage_data = json.load(f)

        # Extract file-level coverage information
        file_coverage = {}
        for file_path, file_data in coverage_data.get("files", {}).items():
            # Calculate coverage percentage for this file
            executed_lines = len(file_data.get("executed_lines", []))
            missing_lines = len(file_data.get("missing_lines", []))
            excluded_lines = len(file_data.get("excluded_lines", []))

            total_lines = executed_lines + missing_lines + excluded_lines
            if total_lines > 0:
                coverage_percent = (executed_lines / total_lines) * 100
            else:
                coverage_percent = 0.0

            file_coverage[file_path] = {
                "coverage_percent": coverage_percent,
                "executed_lines": executed_lines,
                "missing_lines": missing_lines,
                "excluded_lines": excluded_lines,
                "total_lines": total_lines,
            }

        # Calculate overall coverage
        total_executed = sum(data["executed_lines"] for data in file_coverage.values())
        total_missing = sum(data["missing_lines"] for data in file_coverage.values())
        total_excluded = sum(data["excluded_lines"] for data in file_coverage.values())
        total_lines = total_executed + total_missing + total_excluded

        overall_coverage = (total_executed / total_lines * 100) if total_lines > 0 else 0.0

        return {
            "overall_coverage": overall_coverage,
            "total_executed": total_executed,
            "total_missing": total_missing,
            "total_excluded": total_excluded,
            "total_lines": total_lines,
            "file_coverage": file_coverage,
        }

    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to parse coverage JSON file {coverage_json_path}: {e}")
        return None
