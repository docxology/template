"""Pipeline reporting module for generating consolidated reports.

Exports report generators for test results, validation, performance
metrics, and error summaries from pipeline execution.
"""

from __future__ import annotations

from pathlib import Path  # noqa: F401

try:
    from infrastructure.reporting.dashboard_generator import (
        generate_all_dashboards,
        generate_matplotlib_dashboard,
        generate_plotly_dashboard,
    )
except ImportError:
    pass
from infrastructure.reporting.error_aggregator import (
    ErrorAggregator,
    ErrorEntry,
    get_error_aggregator,
    reset_error_aggregator,
)
from infrastructure.reporting.executive_reporter import (
    ExecutiveSummary,
    ProjectMetrics,
    collect_project_metrics,
    generate_executive_summary,
    save_executive_summary,
)
from infrastructure.reporting.output_reporter import (
    collect_output_statistics,
    generate_output_summary,
)
from infrastructure.reporting.pipeline_reporter import (
    generate_error_summary,
    generate_performance_report,
    generate_pipeline_report,
    generate_test_report,
    generate_validation_report,
    save_pipeline_report,
)
from infrastructure.reporting.output_organizer import FileType, OutputOrganizer
from infrastructure.reporting.coverage_reporter import (
    generate_coverage_test_report,
    parse_pytest_output,
    save_test_report,
)
from infrastructure.reporting.multi_project_reporter import generate_multi_project_report


__all__ = [
    "generate_pipeline_report",
    "generate_test_report",
    "generate_validation_report",
    "generate_performance_report",
    "generate_error_summary",
    "save_pipeline_report",
    "parse_pytest_output",
    "generate_coverage_test_report",
    "save_test_report",
    "ErrorAggregator",
    "ErrorEntry",
    "get_error_aggregator",
    "reset_error_aggregator",
    "generate_output_summary",
    "collect_output_statistics",
    "generate_executive_summary",
    "save_executive_summary",
    "collect_project_metrics",
    "ProjectMetrics",
    "ExecutiveSummary",
    "generate_all_dashboards",
    "generate_matplotlib_dashboard",
    "generate_plotly_dashboard",
    "generate_multi_project_report",
    "OutputOrganizer",
    "FileType",
]
