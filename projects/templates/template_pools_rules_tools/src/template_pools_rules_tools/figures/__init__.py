"""Figure-rendering modules for the pools/rules/tools exemplar: the
figure façade, shared theme/spec support, cover art, the rule-hierarchy
renderer, and manuscript variable hydration.

These modules are re-exported from ``template_pools_rules_tools`` for
backwards compatibility; import them from the package root.
"""

from .cover_figure import generate_cover_art
from .figure_support import (
    COVER_FIGURE_FILENAMES,
    FIGURE_REGISTRY_SCHEMA,
    INTEGRATION_FIGURE_SPECS,
    IntegrationFigureSpec,
)
from .figures import (
    all_figures,
    generate_architecture_overview,
    generate_fond_taxonomy,
    generate_pipeline_flow,
    generate_resilience_layers,
    generate_resource_counts,
    generate_status_dashboard,
    generate_tool_contract,
)
from .manuscript_variables import generate_variables
from .rule_hierarchy_figure import generate_rule_hierarchy

__all__ = [
    "COVER_FIGURE_FILENAMES",
    "FIGURE_REGISTRY_SCHEMA",
    "INTEGRATION_FIGURE_SPECS",
    "IntegrationFigureSpec",
    "all_figures",
    "generate_architecture_overview",
    "generate_cover_art",
    "generate_fond_taxonomy",
    "generate_pipeline_flow",
    "generate_resilience_layers",
    "generate_resource_counts",
    "generate_rule_hierarchy",
    "generate_status_dashboard",
    "generate_tool_contract",
    "generate_variables",
]
