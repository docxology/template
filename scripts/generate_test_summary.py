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
from infrastructure.reporting.test_summary_generator import run_test_summary_generation

if __name__ == "__main__":
    exit(run_test_summary_generation())
