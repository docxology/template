"""Pipeline reporting module for generating consolidated reports.

Exports report generators for test results, validation, performance
metrics, and error summaries from pipeline execution.
"""

from __future__ import annotations

# Pipeline stage reporters (used during pipeline execution)
from .error_aggregator import (
    ErrorAggregator,
    ErrorEntry,
    get_error_aggregator,
    reset_error_aggregator,
)
from .pipeline_reporter import (
    generate_performance_report,
    generate_pipeline_report,
    generate_validation_report,
    save_error_summary,
    save_pipeline_report,
    save_test_results,
)

# Output & statistics reporters (post-pipeline)
from .output_reporter import (
    collect_output_statistics,
    log_output_summary,
)
from .output_organizer import FileType, OutputOrganizer

# Executive & multi-project reporters (cross-project summaries)
from .executive_reporter import (
    ExecutiveSummary,
    ProjectMetrics,
    collect_project_metrics,
    generate_executive_summary,
    save_executive_summary,
)
from .multi_project_reporter import generate_multi_project_report, generate_multi_project_summary_report

# Test suite summary generator
from .suite_summary_generator import (
    generate_markdown_report,
    generate_summary_report,
    load_infrastructure_results,
    load_test_results,
    run_test_summary_generation,
)


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
