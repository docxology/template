"""Pipeline reporting module for generating consolidated reports.

Concern-based entry points (import directly for clarity):
  - Pipeline execution:   infrastructure.reporting.pipeline_io / pipeline_report_model
  - Output statistics:    infrastructure.reporting.output_statistics
  - Executive summaries:  infrastructure.reporting.executive_reporter
  - Test suite summaries: infrastructure.reporting.markdown_formatter / report_builder
  - Error aggregation:    infrastructure.reporting.error_aggregator

This __init__ re-exports the most commonly used symbols for convenience.
"""

from __future__ import annotations

# Pipeline stage reporters (used during pipeline execution)
from .error_aggregator import (
    ErrorAggregator,
    ErrorEntry,
    get_error_aggregator,
    reset_error_aggregator,
)
from .pipeline_io import (
    generate_performance_report,
    generate_validation_report,
    save_error_summary,
    save_pipeline_report,
    save_test_results,
)
from .pipeline_report_model import generate_pipeline_report

# Output & statistics reporters (post-pipeline)
from .output_organizer import FileType, OutputOrganizer
from .output_statistics import (
    collect_output_statistics,
    log_output_summary,
)

# Executive & multi-project reporters (cross-project summaries)
from .executive_reporter import (
    ExecutiveSummary,
    ProjectMetrics,
    collect_project_metrics,
    generate_executive_summary,
    save_executive_summary,
)
from .multi_project_reporter import generate_multi_project_report, generate_multi_project_summary_report

# Test suite summary
from .markdown_formatter import generate_markdown_report, run_test_summary_generation
from .report_builder import generate_summary_report
from .result_loaders import load_infrastructure_results, load_test_results


# Optional imports: _dashboard_matplotlib requires matplotlib/plotly which may not be installed
try:
    from ._dashboard_matplotlib import (
        generate_all_dashboards,
        generate_matplotlib_dashboard,
        generate_plotly_dashboard,
    )

    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False


__all__ = [
    "generate_pipeline_report",
    "generate_validation_report",
    "save_test_results",
    "generate_performance_report",
    "save_error_summary",
    "save_pipeline_report",
    "ErrorAggregator",
    "ErrorEntry",
    "get_error_aggregator",
    "reset_error_aggregator",
    "log_output_summary",
    "collect_output_statistics",
    "generate_executive_summary",
    "save_executive_summary",
    "collect_project_metrics",
    "ProjectMetrics",
    "ExecutiveSummary",
    "generate_multi_project_report",
    "generate_multi_project_summary_report",
    "OutputOrganizer",
    "FileType",
    "generate_summary_report",
    "generate_markdown_report",
    "load_test_results",
    "load_infrastructure_results",
    "run_test_summary_generation",
    "DASHBOARD_AVAILABLE",
]
