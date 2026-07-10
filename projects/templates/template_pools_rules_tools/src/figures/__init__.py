"""figures — Matplotlib-based architecture visualisations for the integration demo.

Split into one module per figure builder, sharing the matplotlib guard and
brand palette in ``_theme``.

Public API
----------
generate_architecture_overview(output_dir=None, filename="architecture_overview.png")
generate_resource_counts(output_dir=None, filename="resource_counts.png", counts=None, _data=None)
generate_status_dashboard(
    output_dir=None,
    filename="status_dashboard.png",
    statuses=None,
    integration_result=None,
)
generate_fond_taxonomy(output_dir=None, filename="fond_taxonomy.png")
generate_rule_hierarchy(output_dir=None, filename="rule_hierarchy.png")
generate_tool_contract(output_dir=None, filename="tool_contract.png")
generate_resilience_layers(output_dir=None, filename="resilience_layers.png")
generate_pipeline_flow(output_dir=None, filename="pipeline_flow.png")
generate_cover_art(output_dir=None, filename="cover_art.png")
all_figures(output_dir=None, integration_result=None) -> dict[str, Path]
generate_all_figures(...)  -- alias for all_figures

All functions return pathlib.Path (or None if matplotlib unavailable).
"""

from __future__ import annotations

from .aggregate import all_figures, generate_all_figures
from .architecture import generate_architecture_overview
from .contract import generate_tool_contract
from .counts import generate_resource_counts
from .cover import generate_cover_art
from .dashboard import generate_status_dashboard
from .hierarchy import generate_rule_hierarchy
from .pipeline_flow import generate_pipeline_flow
from .resilience import generate_resilience_layers
from .taxonomy import generate_fond_taxonomy

__all__ = [
    "all_figures",
    "generate_all_figures",
    "generate_architecture_overview",
    "generate_cover_art",
    "generate_fond_taxonomy",
    "generate_pipeline_flow",
    "generate_resilience_layers",
    "generate_resource_counts",
    "generate_rule_hierarchy",
    "generate_status_dashboard",
    "generate_tool_contract",
]
