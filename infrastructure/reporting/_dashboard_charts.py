"""Dashboard chart coordinator — re-exports chart families."""

from infrastructure.reporting._dashboard_constants import COLORS
from infrastructure.reporting._dashboard_charts_health import (
    create_coverage_chart,
    create_test_count_chart,
    draw_coverage_on_axes,
    draw_test_count_on_axes,
)
from infrastructure.reporting._dashboard_charts_outputs import (
    create_manuscript_complexity_chart,
    create_manuscript_size_chart,
    create_output_distribution_chart,
    create_summary_table,
    draw_executive_summary_on_axes,
    draw_manuscript_complexity_scatter_on_axes,
    draw_output_distribution_on_axes,
    generate_matplotlib_dashboard,
)
from infrastructure.reporting._dashboard_charts_pipeline import (
    create_performance_timeline_chart,
    create_pipeline_duration_chart,
    draw_pipeline_duration_on_axes,
)

__all__ = [
    "COLORS",
    "create_coverage_chart",
    "create_manuscript_complexity_chart",
    "create_manuscript_size_chart",
    "create_output_distribution_chart",
    "create_performance_timeline_chart",
    "create_pipeline_duration_chart",
    "create_summary_table",
    "create_test_count_chart",
    "draw_coverage_on_axes",
    "draw_executive_summary_on_axes",
    "draw_manuscript_complexity_scatter_on_axes",
    "draw_output_distribution_on_axes",
    "draw_pipeline_duration_on_axes",
    "draw_test_count_on_axes",
    "generate_matplotlib_dashboard",
]
