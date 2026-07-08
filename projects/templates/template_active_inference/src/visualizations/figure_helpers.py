"""Shared matplotlib helpers for figure generators."""

from __future__ import annotations

import contextlib
import json
import warnings
from collections.abc import Iterator
from pathlib import Path
from textwrap import fill

from .figure_io import save_figure_png
from .figure_registry import figure_output_path
from .figure_style import FigureStyleConfig, active_style, apply_style, load_figure_style

_TIGHT_LAYOUT_INCOMPATIBLE = "This figure includes Axes that are not compatible with tight_layout"


def save_styled_figure(fig, path: Path, style: FigureStyleConfig) -> Path:
    """Save styled figure to the output path."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", UserWarning)
        fig.tight_layout()
    if any(_TIGHT_LAYOUT_INCOMPATIBLE in str(item.message) for item in caught):
        fig.subplots_adjust(left=0.08, right=0.98, bottom=0.08, top=0.92)
    return save_figure_png(
        fig,
        path,
        dpi=style.dpi,
        facecolor="white",
        transparent=style.transparent,
    )


def style_grid(ax, style: FigureStyleConfig) -> None:
    """Process style grid."""
    if style.grid:
        ax.grid(True, alpha=0.25, color=style.color("grid"), linewidth=style.layout_value("grid_line_width", 0.8))
    ax.spines["left"].set_color(style.color("grid"))
    ax.spines["bottom"].set_color(style.color("grid"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(color=style.color("grid"), labelcolor=style.color("primary"))


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
        fontsize=style.text_size("source_note"),
        color=style.color("primary"),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#ffffff", edgecolor=style.color("grid"), alpha=0.92),
    )


def configure_axis(
    ax,
    style: FigureStyleConfig,
    *,
    title: str,
    xlabel: str | None = None,
    ylabel: str | None = None,
    integer_x: bool = False,
    integer_y: bool = False,
    title_loc: str | None = None,
    title_size: float | None = None,
) -> None:
    """Apply the common publication axis treatment."""
    from matplotlib.ticker import MaxNLocator

    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    effective_title_size = title_size if title_size is not None else style.text_size("title")
    if title_loc is None:
        ax.set_title(title, fontsize=effective_title_size)
    else:
        ax.set_title(title, loc=title_loc, fontsize=effective_title_size)
    if integer_x:
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    if integer_y:
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    style_grid(ax, style)


def text_box(
    ax,
    x: float,
    y: float,
    text: object,
    style: FigureStyleConfig,
    *,
    width: int = 28,
    edge_role: str = "grid",
    facecolor: str = "#ffffff",
    fontsize: float | None = None,
    weight: str | None = None,
    ha: str = "left",
    va: str = "center",
) -> None:
    """Draw a wrapped labeled box in axes/data coordinates."""
    ax.text(
        x,
        y,
        wrap_text(text, width),
        fontsize=fontsize if fontsize is not None else style.text_size("annotation"),
        va=va,
        ha=ha,
        linespacing=1.05,
        weight=weight,
        color=style.color("primary"),
        bbox=dict(boxstyle="round,pad=0.25", facecolor=facecolor, edgecolor=style.color(edge_role)),
    )


def draw_column_headers(
    ax, columns: list[float], headers: list[str], style: FigureStyleConfig, *, y: float = 0.94
) -> None:
    """Draw aligned column headers for flow/table figures."""
    for x, header in zip(columns, headers, strict=True):
        ax.text(x, y, header, weight="bold", color=style.color("primary"), fontsize=style.text_size("header"))


def draw_arrow(ax, start_x: float, end_x: float, y: float, style: FigureStyleConfig) -> None:
    """Draw a compact left-to-right flow arrow."""
    ax.annotate(
        "",
        xy=(end_x, y),
        xytext=(start_x, y),
        arrowprops={
            "arrowstyle": "->",
            "color": style.color("muted"),
            "linewidth": style.layout_value("card_line_width", 1.0),
        },
    )


def load_json_artifact(project_root: Path, relative_path: str) -> dict:
    """Load a JSON artifact by project-relative path."""
    payload = json.loads((project_root.resolve() / relative_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        msg = f"Expected dict JSON artifact at {relative_path}"
        raise TypeError(msg)
    return payload


def add_value_labels(ax, bars, *, fmt: str = "{:.2f}", pad: float = 0.02, fontsize: float | None = None) -> None:
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
            fontsize=fontsize if fontsize is not None else active_style().text_size("annotation"),
        )


@contextlib.contextmanager
def styled_figure(project_root: Path, figure_id: str) -> Iterator[tuple[FigureStyleConfig, Path]]:
    """Load style, resolve output path, and apply matplotlib rc context."""
    root = project_root.resolve()
    style = load_figure_style(root)
    out = figure_output_path(root, figure_id)
    with apply_style(style):
        yield style, out
