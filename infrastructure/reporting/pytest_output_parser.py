"""Parse pytest stdout/stderr into structured test metrics.

Extracts test counts, coverage percentages, timing phases, and
test categories from pytest console output.
"""

from __future__ import annotations

import re
from typing import Any


def parse_pytest_output(stdout: str, stderr: str, exit_code: int) -> dict[str, Any]:
    """Parse pytest stdout/stderr and exit_code into structured test metrics."""
    results: dict[str, Any] = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "total": 0,
        "warnings": 0,
        "exit_code": exit_code,
        "discovery_count": 0,
        "collection_errors": 0,
        "execution_phases": {},
        "test_categories": {},
    }

    # Parse summary line (e.g., "1747 passed, 2 skipped, 41 deselected in 37.59s")
    # This handles both verbose and quiet modes
    summary_pattern = r"(\d+)\s+passed|(\d+)\s+failed|(\d+)\s+skipped|(\d+)\s+deselected"
    for match in re.finditer(summary_pattern, stdout):
        if match.group(1):  # passed
            results["passed"] = int(match.group(1))
        elif match.group(2):  # failed
            results["failed"] = int(match.group(2))
        elif match.group(3):  # skipped
            results["skipped"] = int(match.group(3))

    # If no summary line found, check for collection errors vs test failures
    if results["passed"] == 0 and results["failed"] == 0 and results["skipped"] == 0:
        # Check for collection errors FIRST
        collection_error_match = re.search(r"collected\s+\d+\s+items?\s*/\s*(\d+)\s+error", stdout)

        if collection_error_match:
            # Collection error - don't treat as test failures
            error_count = int(collection_error_match.group(1))
            results["collection_errors"] = error_count
            results["failed"] = 0  # Collection errors are not test failures
            results["total"] = 0  # No tests actually ran
            # Store discovery count separately
            discovery_match = re.search(r"(\d+)\s+tests?\s+collected", stdout)
            if discovery_match:
                results["discovery_count"] = int(discovery_match.group(1))
        else:
            # No collection error - infer from discovery count
            discovery_match = re.search(r"collected\s+(\d+)\s+items?", stdout)
            if discovery_match:
                discovery_count = int(discovery_match.group(1))
                if exit_code == 0:
                    # All tests passed if exit code is 0
                    results["passed"] = discovery_count
                    results["total"] = discovery_count
                else:
                    # Non-zero exit with no summary suggests test failures
                    # But we don't know exact count - mark as indeterminate
                    results["failed"] = 1  # At least 1 failed, exact count unknown
                    results["total"] = discovery_count
            # Also check if stdout contains test result indicators
            elif "..." in stdout or "[100%]" in stdout:
                # Count dots and percentage indicators as rough test count
                dot_count = stdout.count(".")
                if dot_count > 0 and exit_code == 0:
                    results["passed"] = dot_count
                    results["total"] = dot_count

    # Only compute total from parsed counts when the fallback branch didn't set it explicitly
    if results["total"] == 0:
        results["total"] = results["passed"] + results["failed"] + results["skipped"]

    # Parse discovery count from collection output (e.g., "collected 187 items")
    # Only update if not already set by the collection-error branch above
    if results["discovery_count"] == 0:
        discovery_match = re.search(r"collected\s+(\d+)\s+items?", stdout)
        if discovery_match:
            results["discovery_count"] = int(discovery_match.group(1))

    # Parse execution timing phases
    # Look for patterns like "test session starts", "collecting", etc.
    timing_patterns = {
        "setup": r"test session starts.*?in\s+([\d.]+)s",
        "collection": r"collecting.*?in\s+([\d.]+)s",
        "execution": r"(\d+)\s+passed.*?in\s+([\d.]+)s",
    }

    for phase, pattern in timing_patterns.items():
        match = re.search(pattern, stdout, re.DOTALL)
        if match:
            if phase == "execution" and len(match.groups()) > 1:
                results["execution_phases"][phase] = float(match.group(2))
            elif phase != "execution":
                results["execution_phases"][phase] = float(match.group(1))

    # Parse test categories by markers (slow, integration, requires_ollama, etc.)
    # Look for markers in the output
    marker_indicators = ["slow", "integration", "requires_ollama"]
    for marker in marker_indicators:
        # Count occurrences of marker-related output
        marker_count = stdout.count(f"::{marker}") + stdout.count(f" - {marker}")
        if marker_count > 0:
            results["test_categories"][marker] = marker_count

    # Count warnings
    results["warnings"] = stdout.count(" warning") + stderr.count(" warning")

    # Parse coverage if present (works in both verbose and quiet modes)
    # Look for TOTAL line first, then fall back to any percentage
    total_match = re.search(r"TOTAL\s+.*?\s+(\d+\.\d+)%", stdout)
    if total_match:
        results["coverage_percent"] = float(total_match.group(1))
    else:
        # Fallback to any percentage (for smaller test runs)
        coverage_match = re.search(r"(\d+\.\d+)%", stdout)
        if coverage_match:
            results["coverage_percent"] = float(coverage_match.group(1))

    return results
