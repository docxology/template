"""Registry-driven figure dispatch for the AutoResearch loop."""

from __future__ import annotations

from src.figures.figure_specs import (
    FIGURE_DISPATCH,
    FigureDispatchEntry,
    FigureRenderContext,
    render_all_figures,
    render_figure_batch,
    render_security_figures,
)

__all__ = [
    "FIGURE_DISPATCH",
    "FigureDispatchEntry",
    "FigureRenderContext",
    "render_all_figures",
    "render_figure_batch",
    "render_security_figures",
]
