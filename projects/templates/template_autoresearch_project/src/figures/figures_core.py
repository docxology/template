"""Shared helpers for AutoResearch figure generation.

Colour, resolution, grid, and save behaviour all resolve from the active
:class:`~src.figure_style.FigureStyleConfig` (see :func:`figure_style.apply_style`).
Figure writers call :func:`save_figure` instead of ``fig.savefig(..., dpi=160)`` and
:func:`styled_grid` instead of an inline ``ax.grid(...)`` so a single style controls
every figure. With the default style these helpers reproduce the historical output
byte-for-byte.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .figure_style import FigureStyleConfig, get_active_style
from src.json_coerce import mapping_list as _mapping_list

# Candidate-status roles resolved from the palette; any other status falls back to
# the muted colour (matching the historical default for unknown statuses).
_STATUS_ROLES = ("baseline", "accepted", "rejected", "evaluated", "deferred")
_MUTED_FALLBACK = "#64748b"


def save_figure(fig: Any, path: Path, *, style: FigureStyleConfig | None = None) -> Path:
    """Save ``fig`` to ``path`` using the active style's dpi/transparency, then close it.

    Replaces the historical ``fig.savefig(path, dpi=160); plt.close(fig)`` pattern.
    At the default style this is byte-identical (dpi 160, opaque background).
    """
    from matplotlib import pyplot as plt

    style = style or get_active_style()
    # Pin metadata so PNG bytes are reproducible across machines, dates, and
    # matplotlib versions: by default the Agg writer stamps a version-dependent
    # "Software" chunk and a wall-clock "Creation Time"/"Date", which silently
    # break byte-identity outside a single-machine, single-version window.
    fig.savefig(
        path,
        dpi=style.dpi,
        transparent=style.transparent,
        metadata={"Software": None, "Creation Time": None, "Date": None},
    )
    plt.close(fig)
    return path


def styled_grid(ax: Any, axis: str, *, style: FigureStyleConfig | None = None) -> None:
    """Draw an axis grid using the active style's grid colour, honouring ``grid`` on/off."""
    style = style or get_active_style()
    if not style.grid:
        return
    ax.grid(axis=axis, color=style.color("grid", "#d4d4d8"), linewidth=0.8)


def palette_color(role: str, fallback: str, *, style: FigureStyleConfig | None = None) -> str:
    """Resolve a palette ``role`` from the active style with an explicit fallback."""
    style = style or get_active_style()
    return style.color(role, fallback)


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _first_label_index(labels: np.ndarray, label: int) -> int:
    matches = np.flatnonzero(labels == label)
    if matches.size == 0:
        raise ValueError(f"label is missing from MNIST subset: {label}")
    return int(matches[0])


def _float_value(value: object) -> float:
    return float(value) if isinstance(value, int | float | str) else 0.0


def _short_candidate_label(value: object) -> str:
    text = str(value)
    if text == "nearest_centroid_baseline":
        return "baseline"
    return text.replace("exp-", "")


def _status_color(status: str) -> str:
    style = get_active_style()
    if status in _STATUS_ROLES:
        return style.color(status, _MUTED_FALLBACK)
    return style.color("muted", _MUTED_FALLBACK)


def _status_marker(status: str) -> str:
    return {"baseline": "s", "accepted": "D"}.get(status, "o")


def _class_balance_count(rows: list[dict[str, Any]], split: str, label: int) -> int:
    for row in rows:
        if row.get("split") == split and int(row.get("class_label", -1)) == label:
            return int(row.get("count", 0))
    return 0


def annotate_imshow_matrix(
    ax: Any,
    matrix: np.ndarray,
    row_labels: list[str] | None,
    col_labels: list[str] | None,
    *,
    vmin: float | None = 0.0,
    vmax: float | None = 1.0,
    cmap: str | None = None,
    cell_text: np.ndarray | list[list[str]] | None = None,
    color_threshold: float | None = None,
    fontsize: float = 8.0,
    style: FigureStyleConfig | None = None,
) -> Any:
    """Render a heatmap with optional axis labels and per-cell annotations."""
    style = style or get_active_style()
    colormap = cmap or style.metrics_colormap
    imshow_kwargs: dict[str, Any] = {"cmap": colormap}
    if vmin is not None:
        imshow_kwargs["vmin"] = vmin
    if vmax is not None:
        imshow_kwargs["vmax"] = vmax
    image = ax.imshow(matrix, **imshow_kwargs)
    if color_threshold is None:
        color_threshold = float(np.max(matrix)) / 2.0 if matrix.size else 0.5
    if col_labels is not None:
        ax.set_xticks(range(len(col_labels)), labels=col_labels)
    if row_labels is not None:
        ax.set_yticks(range(len(row_labels)), labels=row_labels)
    if cell_text is not None:
        text_grid = np.asarray(cell_text, dtype=object)
        for row_index in range(matrix.shape[0]):
            for col_index in range(matrix.shape[1]):
                value = matrix[row_index, col_index]
                label = str(text_grid[row_index, col_index])
                text_color = (
                    "white" if float(value) > color_threshold else palette_color("text_dark", "#111827", style=style)
                )
                ax.text(
                    col_index,
                    row_index,
                    label,
                    ha="center",
                    va="center",
                    fontsize=fontsize,
                    color=text_color,
                )
    return image


def horizontal_bar_panel(
    ax: Any,
    labels: list[str],
    values: list[float],
    *,
    annotations: list[str] | None = None,
    color: str | None = None,
    invert_y: bool = True,
    style: FigureStyleConfig | None = None,
) -> Any:
    """Draw a horizontal bar chart with optional value annotations."""
    style = style or get_active_style()
    bar_color = color or palette_color("negative", "#7c2d12", style=style)
    bars = ax.barh(labels, values, color=bar_color)
    if invert_y:
        ax.invert_yaxis()
    if annotations:
        for bar, annotation in zip(bars, annotations, strict=True):
            ax.text(
                bar.get_width() + 0.05,
                bar.get_y() + bar.get_height() / 2.0,
                annotation,
                va="center",
                fontsize=8,
            )
    return bars


def dual_vertical_bars(
    fig: Any,
    rows: list[dict[str, Any]],
    metric_pairs: tuple[
        tuple[tuple[str, str, str], tuple[str, str, str]],
        tuple[tuple[str, str, str], tuple[str, str, str]],
    ],
    *,
    label_key: str = "candidate_id",
    label_formatter: Any | None = None,
    sharex: bool = True,
) -> tuple[Any, Any]:
    """Create two stacked subplots with paired vertical bar groups per row."""
    format_label = label_formatter or (lambda value: str(value))
    labels = [format_label(row.get(label_key, "candidate")) for row in rows]
    x_positions = np.arange(len(rows), dtype=float)
    width = 0.34
    axes = fig.subplots(2, 1, sharex=sharex)
    for axis, (left_spec, right_spec) in zip(axes, metric_pairs, strict=True):
        left_key, left_role, left_fallback = left_spec
        right_key, right_role, right_fallback = right_spec
        axis.bar(
            x_positions - width / 2.0,
            [float(row.get(left_key, 0.0)) for row in rows],
            width,
            color=palette_color(left_role, left_fallback),
            label="train" if "train" in left_key else left_key.replace("_", " "),
        )
        axis.bar(
            x_positions + width / 2.0,
            [float(row.get(right_key, 0.0)) for row in rows],
            width,
            color=palette_color(right_role, right_fallback),
            label="test" if "test" in right_key else right_key.replace("_", " "),
        )
        styled_grid(axis, "y")
        axis.set_axisbelow(True)
        axis.legend(loc="lower right" if axis is axes[0] else "upper right", frameon=False, fontsize=8)
        for spine in axis.spines.values():
            spine.set_visible(False)
    axes[-1].set_xticks(x_positions, labels=labels, rotation=18, ha="right")
    return axes[0], axes[1]


def grouped_vertical_bars(
    ax: Any,
    x_positions: np.ndarray,
    series: list[tuple[list[float], str, str, str | None]],
    *,
    width: float = 0.38,
    annotate: bool = False,
    style: FigureStyleConfig | None = None,
) -> list[Any]:
    """Draw side-by-side vertical bar groups for multiple series at each x position."""
    style = style or get_active_style()
    bar_groups: list[Any] = []
    for index, (values, role, fallback, label) in enumerate(series):
        positions = x_positions + ((index - (len(series) - 1) / 2.0) * width)
        bar_kwargs: dict[str, Any] = {"width": width, "color": palette_color(role, fallback, style=style)}
        if label is not None:
            bar_kwargs["label"] = label
        bars = ax.bar(positions, values, **bar_kwargs)
        bar_groups.append(bars)
        if annotate:
            for bar in bars:
                height = int(bar.get_height())
                ax.text(bar.get_x() + bar.get_width() / 2.0, height + 3, str(height), ha="center", fontsize=7.5)
    return bar_groups


def hide_spines(ax: Any) -> None:
    """Hide all axis spines (common figure finish)."""
    for spine in ax.spines.values():
        spine.set_visible(False)


__all__ = [
    "_float_value",
    "_mapping_list",
    "_short_candidate_label",
    "annotate_imshow_matrix",
    "dual_vertical_bars",
    "grouped_vertical_bars",
    "hide_spines",
    "horizontal_bar_panel",
    "palette_color",
    "save_figure",
    "styled_grid",
]
