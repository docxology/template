"""Sheaf coverage and layer-stack figure entrypoints."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from visualizations.figure_io import save_figure_png
from visualizations.figure_style import apply_style, load_figure_style
from visualizations.figures_sheaf_draw import (
    draw_coverage_heatmap,
    draw_track_layers_panel,
    layers_overview_figure_height,
)
from visualizations.figures_sheaf_payload import HeatmapPayload, coverage_heatmap_payload

__all__ = [
    "HeatmapPayload",
    "coverage_heatmap_payload",
    "draw_coverage_heatmap",
    "draw_track_layers_panel",
    "figure_sheaf_coverage_heatmap",
    "figure_sheaf_layers_overview",
    "layers_overview_figure_height",
]


def figure_sheaf_layers_overview(project_root: Path) -> Path | None:
    root = project_root.resolve()
    payload = coverage_heatmap_payload(root)
    if payload is None:
        return None
    style = load_figure_style(root)
    out = root / "output" / "figures" / "sheaf_layers_overview.png"
    n_rows = len(payload.y_labels)
    heatmap_height = layers_overview_figure_height(n_rows, payload.cfg.heatmap.row_height)
    dpi = max(style.dpi, payload.cfg.heatmap.dpi)
    with apply_style(style):
        fig, axes = plt.subplots(
            1,
            2,
            figsize=(13.5, heatmap_height),
            gridspec_kw={"width_ratios": [1.05, 1.65], "wspace": 0.28},
        )
        layer_ax, heatmap_ax = axes
        if not draw_track_layers_panel(layer_ax, root):
            plt.close(fig)
            return None
        draw_coverage_heatmap(
            heatmap_ax,
            payload,
            root,
            title="IMRAD binding matrix",
            boundary_width=1.0,
            label_fontsize=7,
        )
        fig.suptitle("Sheaf fragment layers and IMRAD bindings", fontsize=11, y=0.98)
        fig.subplots_adjust(left=0.06, right=0.98, top=0.92, wspace=0.28)
        save_figure_png(fig, out, dpi=dpi)
    return out


def figure_sheaf_coverage_heatmap(
    project_root: Path,
    *,
    output_path: Path | None = None,
) -> Path | None:
    """Render B/W/G sheaf coverage matrix with IMRAD row grouping."""
    root = project_root.resolve()
    payload = coverage_heatmap_payload(root)
    if payload is None:
        return None
    cfg = payload.cfg
    style = load_figure_style(root)
    n_rows = len(payload.y_labels)
    n_cols = len(payload.track_ids)
    row_height = cfg.heatmap.row_height
    fig_height = max(4.5, n_rows * row_height + 2.0)
    fig_width = max(7.5, n_cols * 0.85 + 2.8)
    out = output_path or root / "output" / "figures" / "sheaf_coverage_heatmap.png"
    dpi = max(style.dpi, cfg.heatmap.dpi)
    with apply_style(style):
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        draw_coverage_heatmap(
            ax,
            payload,
            root,
            title=cfg.report.title,
            show_legend=True,
            show_row_pct=True,
            boundary_width=1.2,
        )
        fig.tight_layout()
        save_figure_png(fig, out, dpi=dpi)
    return out
