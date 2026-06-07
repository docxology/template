"""Shared matplotlib helpers for figure generators."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from pathlib import Path
from textwrap import fill

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
        ax.grid(True, alpha=0.25, color=style.color("grid"), linewidth=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def wrap_text(text: object, width: int = 22) -> str:
    """Wrap labels for compact figure panels."""
    return fill(str(text), width=width, break_long_words=False, break_on_hyphens=False)


def add_note(
    ax,
    text: str,
    style: FigureStyleConfig,
    *,
    x: float = 0.02,
    y: float = 0.96,
    width: int = 46,
) -> None:
    """Add a small source/claim note in axes coordinates."""
    ax.text(
        x,
        y,
        wrap_text(text, width),
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=8,
        color=style.color("primary"),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#ffffff", edgecolor=style.color("grid"), alpha=0.92),
    )


def add_value_labels(ax, bars, *, fmt: str = "{:.2f}", pad: float = 0.02, fontsize: float = 8.0) -> None:
    """Label vertical bars without changing axes limits too aggressively."""
    ylim = ax.get_ylim()
    span = max(ylim[1] - ylim[0], 1e-9)
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + span * pad,
            fmt.format(height),
            ha="center",
            va="bottom",
            fontsize=fontsize,
        )


@contextlib.contextmanager
def styled_figure(project_root: Path, figure_id: str) -> Iterator[tuple[FigureStyleConfig, Path]]:
    """Load style, resolve output path, and apply matplotlib rc context."""
    root = project_root.resolve()
    style = load_figure_style(root)
    out = figure_output_path(root, figure_id)
    with apply_style(style):
        yield style, out
