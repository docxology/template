"""Deterministic figure generation for the AutoScientists analysis scripts:
build/write pairs for the comparison, ablation, and efficiency charts, plus
the ``FIGURE_SPECS`` registry scripts call into."""

from .figures import (
    FIGURE_SPECS,
    FigureSpec,
    ablation_alt_text,
    build_ablation_figure,
    build_comparison_figure,
    build_efficiency_figure,
    comparison_alt_text,
    efficiency_alt_text,
    figure_specs_for_results,
    write_ablation_figure,
    write_comparison_figure,
    write_efficiency_figure,
    write_figure_registry,
)

__all__ = [
    "FIGURE_SPECS",
    "FigureSpec",
    "ablation_alt_text",
    "build_ablation_figure",
    "build_comparison_figure",
    "build_efficiency_figure",
    "comparison_alt_text",
    "efficiency_alt_text",
    "figure_specs_for_results",
    "write_ablation_figure",
    "write_comparison_figure",
    "write_efficiency_figure",
    "write_figure_registry",
]
