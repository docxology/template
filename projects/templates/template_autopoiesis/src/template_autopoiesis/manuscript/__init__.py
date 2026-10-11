"""Manuscript-lane modules for the autopoiesis exemplar: the source-level
readiness contract, manuscript figure writers, manuscript variable
generation, and the @@KEY@@-templated file bodies for generated children.

Import public symbols from their defining modules for explicit source custody.
"""

from importlib import import_module
from typing import Any

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


_FIGURE_EXPORTS = frozenset(
    {
        "FIGURE_REGISTRY_SCHEMA",
        "MANUSCRIPT_FIGURE_SPECS",
        "ManuscriptFigureSpec",
        "fig_coverage_by_module",
        "fig_domain_coverage",
        "fig_product_space_annotation",
        "fig_stacked_product",
        "generate_manuscript_figures",
    }
)


def __getattr__(name: str) -> Any:
    """Load plotting only when its actual public figure API is requested."""
    if name not in _FIGURE_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(".manuscript_figures", __name__), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
