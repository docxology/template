"""Specialized dashboard visualizations for executive reporting.

Implementation is split into domain modules; this file re-exports the public
chart functions so existing imports from ``_dashboard_specialized`` keep working.
"""

from __future__ import annotations

from infrastructure.reporting._dashboard_specialized_codebase import (
    generate_codebase_comparison_chart,
    generate_codebase_complexity_chart,
)
from infrastructure.reporting._dashboard_specialized_health import (
    generate_health_comparison_chart,
    generate_health_radar_chart,
)
from infrastructure.reporting._dashboard_specialized_outputs import (
    generate_output_comparison_chart,
    generate_output_distribution_charts,
)
from infrastructure.reporting._dashboard_specialized_pipeline import (
    generate_pipeline_bottlenecks_chart,
    generate_pipeline_efficiency_chart,
)
from infrastructure.reporting._dashboard_specialized_projects import generate_project_breakdowns

__all__ = [
    "generate_codebase_comparison_chart",
    "generate_codebase_complexity_chart",
    "generate_health_comparison_chart",
    "generate_health_radar_chart",
    "generate_output_comparison_chart",
    "generate_output_distribution_charts",
    "generate_pipeline_bottlenecks_chart",
    "generate_pipeline_efficiency_chart",
    "generate_project_breakdowns",
]
