"""Architecture figure generation for the template meta-project: the
per-figure builders, the shared palette and publication constants, and the
``generate_all_architecture_figures`` orchestration entry point."""

from .architecture_viz import (
    comparative_feature_matrix_data,
    generate_all_architecture_figures,
    generate_architecture_overview,
    generate_comparative_feature_matrix,
    generate_module_inventory,
    generate_pipeline_stages,
)

__all__ = [
    "comparative_feature_matrix_data",
    "generate_all_architecture_figures",
    "generate_architecture_overview",
    "generate_comparative_feature_matrix",
    "generate_module_inventory",
    "generate_pipeline_stages",
]
