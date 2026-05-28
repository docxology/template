"""Shared matplotlib helpers for figure generators."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from pathlib import Path

from .figure_io import save_figure_png
from .figure_registry import figure_output_path
from .figure_style import FigureStyleConfig, apply_style, load_figure_style


def save_styled_figure(fig, path: Path, style: FigureStyleConfig) -> Path:
    fig.tight_layout()
    return save_figure_png(
        fig,
        path,
        dpi=style.dpi,
        facecolor="white",
        transparent=style.transparent,
    )


def style_grid(ax, style: FigureStyleConfig) -> None:
    if style.grid:
        ax.grid(True, alpha=0.35, color=style.color("grid"))


@contextlib.contextmanager
def styled_figure(project_root: Path, figure_id: str) -> Iterator[tuple[FigureStyleConfig, Path]]:
    """Load style, resolve output path, and apply matplotlib rc context."""
    root = project_root.resolve()
    style = load_figure_style(root)
    out = figure_output_path(root, figure_id)
    with apply_style(style):
        yield style, out
