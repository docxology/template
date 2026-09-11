"""Matplotlib figure modules for the prose-review workflow.

These modules are re-exported from ``template_prose_project`` for
backwards compatibility; import them from the package root.
"""

from .figures import (
    generate_all_figures,
    plot_citation_density,
    plot_readability_metrics,
    plot_section_word_counts,
)

__all__ = [
    "generate_all_figures",
    "plot_citation_density",
    "plot_readability_metrics",
    "plot_section_word_counts",
]
