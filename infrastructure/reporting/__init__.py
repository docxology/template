"""Pipeline reporting module for generating consolidated reports.

This module provides utilities for generating comprehensive reports from
pipeline execution, including test results, validation results, performance
metrics, and error summaries.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""
from __future__ import annotations

from infrastructure.reporting.pipeline_reporter import (
    generate_pipeline_report,
    generate_test_report,
    generate_validation_report,
    generate_performance_report,
    generate_error_summary,
    save_pipeline_report,
)
from infrastructure.reporting.test_reporter import (
    parse_pytest_output,
    generate_test_report as generate_test_report_from_results,
    save_test_report,
)
from infrastructure.reporting.error_aggregator import (
    ErrorAggregator,
    ErrorEntry,
    get_error_aggregator,
    reset_error_aggregator,
)
from infrastructure.reporting.output_reporter import (
    generate_output_summary,
    collect_output_statistics,
)

__all__ = [
    'generate_pipeline_report',
    'generate_test_report',
    'generate_validation_report',
    'generate_performance_report',
    'generate_error_summary',
    'save_pipeline_report',
    'parse_pytest_output',
    'generate_test_report_from_results',
    'save_test_report',
    'ErrorAggregator',
    'ErrorEntry',
    'get_error_aggregator',
    'reset_error_aggregator',
    'generate_output_summary',
    'collect_output_statistics',
]

