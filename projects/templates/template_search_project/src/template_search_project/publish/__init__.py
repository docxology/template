"""Publication-facing modules for the literature workflow: figures,
dashboard, typed configuration, and manuscript variable generation.

These modules are re-exported from ``template_search_project`` for
backwards compatibility; import them from the package root.
"""

from template_search_project.publish.config import (
    DeepSearchConfig,
    EnrichmentConfig,
    LLMConfig,
    ProjectConfig,
    ReportConfig,
    SearchConfig,
    load_project_config,
)
from template_search_project.publish.dashboard import (
    build_dashboard,
    compute_payload,
    filter_papers,
    load_papers,
)
from template_search_project.publish.figures import (
    generate_all_figures,
    load_search_result,
    plot_papers_per_source,
    plot_score_distribution,
    plot_year_histogram,
)
from template_search_project.publish.manuscript_variables import (
    ManuscriptVariables,
    compute_variables,
    substitute_in_text,
    write_variables,
)

__all__ = [
    "DeepSearchConfig",
    "EnrichmentConfig",
    "LLMConfig",
    "ProjectConfig",
    "ReportConfig",
    "SearchConfig",
    "build_dashboard",
    "compute_payload",
    "compute_variables",
    "filter_papers",
    "generate_all_figures",
    "load_papers",
    "load_project_config",
    "load_search_result",
    "ManuscriptVariables",
    "plot_papers_per_source",
    "plot_score_distribution",
    "plot_year_histogram",
    "substitute_in_text",
    "write_variables",
]
