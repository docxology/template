"""Test reporting module - Parse test output and generate test reports.

This module provides utilities for parsing pytest output and generating
structured test reports. Part of the infrastructure layer (Layer 1) -
reusable across all projects.

This module re-exports from focused submodules for backwards compatibility.
"""

from __future__ import annotations

# Re-export coverage JSON parsing
from .coverage_json_parser import parse_coverage_json

# Re-export pytest output parsing
from .pytest_output_parser import parse_pytest_output

# Re-export test report generation and persistence
from .test_report_generator import generate_test_report, save_test_report_to_files

# Re-export coverage analysis utilities
from .coverage_analysis import (
    analyze_coverage_gaps,
    format_coverage_status,
    format_failure_suggestions,
)

__all__ = [
    "parse_coverage_json",
    "parse_pytest_output",
    "generate_test_report",
    "save_test_report_to_files",
    "format_coverage_status",
    "analyze_coverage_gaps",
    "format_failure_suggestions",
]
