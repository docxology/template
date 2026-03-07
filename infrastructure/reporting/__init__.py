"""Pipeline reporting module for generating consolidated reports.

Exports report generators for test results, validation, performance
metrics, and error summaries from pipeline execution.
"""

from __future__ import annotations

from pathlib import Path  # noqa: F401

try:
    from .dashboard_generator import (
        generate_all_dashboards,
        generate_matplotlib_dashboard,
        generate_plotly_dashboard,
    )
except ImportError as _dashboard_err:
    import warnings

    warnings.warn(
        f"dashboard_generator unavailable (plotly not installed): {_dashboard_err}",
        ImportWarning,
        stacklevel=2,
    )
    generate_all_dashboards = None  # type: ignore[assignment]
    generate_matplotlib_dashboard = None  # type: ignore[assignment]
    generate_plotly_dashboard = None  # type: ignore[assignment]
from .error_aggregator import (
    ErrorAggregator,
    ErrorEntry,
    get_error_aggregator,
    reset_error_aggregator,
)
from .executive_reporter import (
    ExecutiveSummary,
    ProjectMetrics,
    collect_project_metrics,
    generate_executive_summary,
    save_executive_summary,
)
from .output_reporter import (
    collect_output_statistics,
    generate_output_summary,
)
from .pipeline_reporter import (
    generate_error_summary,
    generate_performance_report,
    generate_pipeline_report,
    generate_validation_report,
    save_pipeline_report,
    save_test_results,
)
from .output_organizer import FileType, OutputOrganizer
from .multi_project_reporter import generate_multi_project_report
from .suite_summary_generator import (
    generate_markdown_report,
    generate_summary_report,
    load_infrastructure_results,
    load_test_results,
    run_test_summary_generation,
)


__all__ = [
    "generate_pipeline_report",
    "generate_validation_report",
    "save_test_results",
    "generate_performance_report",
    "generate_error_summary",
    "save_pipeline_report",
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
    "generate_summary_report",
    "generate_markdown_report",
    "load_test_results",
    "load_infrastructure_results",
    "run_test_summary_generation",
]
