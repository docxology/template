"""Backwards-compatible re-export shim for specialized dashboard charts.

Historical location for nine chart generators that were consolidated into a
single 1354-LOC module. They now live in thematic sibling modules:

- ``_dashboard_health``    — health radar, health comparison, per-project breakdowns
- ``_dashboard_pipeline``  — pipeline efficiency, pipeline bottlenecks
- ``_dashboard_outputs``   — output distribution, output comparison
- ``_dashboard_codebase``  — codebase complexity, codebase comparison

Prefer importing from the thematic sibling directly. This shim exists only so
that callers that historically used::

    from infrastructure.reporting._dashboard_specialized import generate_health_radar_chart

continue to work unchanged.
"""

from __future__ import annotations

from infrastructure.reporting._dashboard_codebase import (
    generate_codebase_comparison_chart,
    generate_codebase_complexity_chart,
)
from infrastructure.reporting._dashboard_health import (
    generate_health_comparison_chart,
    generate_health_radar_chart,
    generate_project_breakdowns,
)
from infrastructure.reporting._dashboard_outputs import (
    generate_output_comparison_chart,
    generate_output_distribution_charts,
)
from infrastructure.reporting._dashboard_pipeline import (
    generate_pipeline_bottlenecks_chart,
    generate_pipeline_efficiency_chart,
)

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
