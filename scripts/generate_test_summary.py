#!/usr/bin/env python3
"""Generate comprehensive test summary report for the full repository test suite.

This script aggregates test results from infrastructure and active project
tests to create a comprehensive summary report.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add infrastructure to path for config loading
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, log_header, log_success
from infrastructure.reporting.suite_summary_generator import run_test_summary_generation

logger = get_logger(__name__)


def main() -> int:
    """Generate test summary report."""
    log_header("Generate Test Summary Report", logger)
    exit_code = run_test_summary_generation()
    if exit_code == 0:
        log_success("Test summary report generated successfully", logger)
    else:
        logger.error("Test summary generation failed")
    return exit_code


if __name__ == "__main__":
    exit(main())
