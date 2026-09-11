"""Manuscript-lane modules for the autopoiesis exemplar: the source-level
readiness contract, manuscript figure writers, manuscript variable
generation, and the @@KEY@@-templated file bodies for generated children.

These modules are re-exported from ``template_autopoiesis`` for backwards
compatibility; import them from the package root.
"""

from .emit_templates import (
    TEMPLATE_PATHS,
    apply_template,
    emit_all,
    emit_file,
)
from .manuscript_contract import (
    PREAMBLE_END,
    PREAMBLE_START,
    REQUIRED_MANUSCRIPT_FILES,
    REQUIRED_SPEC_PHASES,
    validate_phase10_contract,
)
from .manuscript_figures import (
    FIGURE_REGISTRY_SCHEMA,
    MANUSCRIPT_FIGURE_SPECS,
    ManuscriptFigureSpec,
    fig_coverage_by_module,
    fig_domain_coverage,
    fig_product_space_annotation,
    fig_stacked_product,
    generate_manuscript_figures,
)
from .manuscript_variables import (
    generate_variables,
    measure_test_summary,
    save_variables,
)

__all__ = [
    "FIGURE_REGISTRY_SCHEMA",
    "MANUSCRIPT_FIGURE_SPECS",
    "PREAMBLE_END",
    "PREAMBLE_START",
    "TEMPLATE_PATHS",
    "ManuscriptFigureSpec",
    "REQUIRED_MANUSCRIPT_FILES",
    "REQUIRED_SPEC_PHASES",
    "apply_template",
    "emit_all",
    "emit_file",
    "fig_coverage_by_module",
    "fig_domain_coverage",
    "fig_product_space_annotation",
    "fig_stacked_product",
    "generate_manuscript_figures",
    "generate_variables",
    "measure_test_summary",
    "save_variables",
    "validate_phase10_contract",
]
