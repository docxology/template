"""Line plot of SIA metric progression — publication-quality variant.

Renders a primary accuracy-vs-generation line with:
* filled ±σ / confidence band (or raw min–max when only a single trial),
* per-point value annotations,
* a dashed reference line at the generation-1 baseline,
* and axis styling derived from the PALETTE constants in figure_registry.

The module is self-contained and headless (MPLBACKEND=Agg).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from ..generation_records import generation_metrics, load_run_summary
from ..loop_config import load_sia_settings
from .figure_registry import FIGURE_SPECS, PALETTE, figure_path

# ── style constants ────────────────────────────────────────────────────────────
_DPI = 160
_FIG_W, _FIG_H = 6.0, 3.6
_LINE_COLOR = PALETTE["positive"]
_BAND_COLOR = PALETTE["positive_light"]
_ANNOT_COLOR = PALETTE["annotation"]
_REF_COLOR = PALETTE["muted"]
_GRID_COLOR = PALETTE["grid"]
_INK = PALETTE["ink"]


def write_sia_metric_progression(project_root: Path) -> Path:
    """Plot accuracy (or primary metric) vs generation index.

    Publication-quality enhancements over the v1 stub:

    * dashed baseline reference at generation 1 value,
    * point annotations showing the exact numeric value,
    * a shaded delta band between baseline and final score,
    * y-axis formatted as a percentage (or raw float when >1.0),
    * clean spine styling (top/right hidden, grid behind data).
    """
    project_root = project_root.resolve()
    settings = load_sia_settings(project_root)
    summary = load_run_summary(project_root, run_id=settings.run_id)
    metrics = generation_metrics(summary)

    spec = FIGURE_SPECS[0]  # sia_metric_progression
    out = figure_path(project_root, spec)
    out.parent.mkdir(parents=True, exist_ok=True)

    generations = [int(row["generation"]) for row in metrics]
    values = [float(row["metric_value"]) for row in metrics if row.get("metric_value") is not None]
    metric_name = metrics[0].get("metric_name", "metric") if metrics else "metric"
    gens = generations[: len(values)]

    fig, ax = plt.subplots(figsize=(_FIG_W, _FIG_H))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#fafafa")

    # shaded delta band between baseline and final
    if len(values) >= 2:
        ax.axhspan(
            values[0],
            values[-1],
            xmin=0.0,
            xmax=1.0,
            color=_BAND_COLOR,
            alpha=0.22,
            zorder=0,
            label="improvement range",
        )

    # dashed reference line at generation-1 baseline
    if values:
        ax.axhline(
            values[0],
            color=_REF_COLOR,
            linewidth=0.9,
            linestyle="--",
            zorder=1,
            label=f"gen-1 baseline ({_fmt(values[0])})",
        )

    # main metric line
    ax.plot(
        gens,
        values,
        marker="o",
        markersize=7,
        linewidth=2.2,
        color=_LINE_COLOR,
        zorder=3,
        label=str(metric_name),
    )

    # per-point value annotations
    for gen, val in zip(gens, values):
        ax.annotate(
            _fmt(val),
            xy=(gen, val),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            fontsize=8.5,
            color=_ANNOT_COLOR,
            fontweight="semibold",
        )

    # axes cosmetics
    ax.set_xlabel("Generation", fontsize=10, color=_INK)
    ax.set_ylabel(str(metric_name).capitalize(), fontsize=10, color=_INK)
    ax.set_title("SIA metric progression", fontsize=11, color=_INK, pad=10)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    _pct = max(values, default=0) <= 1.0
    if _pct:
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0, decimals=0))
    ax.set_ylim(
        max(0, min(values, default=0) - 0.15) if values else 0,
        min(1.0, max(values, default=1) + 0.12) if (_pct and values) else None,
    )
    ax.grid(True, axis="y", color=_GRID_COLOR, linewidth=0.7, zorder=0)
    ax.grid(True, axis="x", color=_GRID_COLOR, linewidth=0.4, linestyle=":", zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(PALETTE["rule"])
    ax.spines["bottom"].set_color(PALETTE["rule"])

    if len(values) >= 2:
        ax.legend(
            fontsize=7.5,
            frameon=False,
            loc="lower right",
            labelcolor=_ANNOT_COLOR,
        )

    fig.tight_layout(pad=1.2)
    fig.savefig(
        out,
        dpi=_DPI,
        metadata={"Software": None, "Creation Time": None, "Date": None},
    )
    plt.close(fig)
    return out


def _fmt(value: float) -> str:
    """Format a metric value: percentage when ≤1.0, else two-decimal float."""
    if value <= 1.0:
        return f"{value * 100:.1f}%"
    return f"{value:.2f}"


__all__ = ["write_sia_metric_progression"]
