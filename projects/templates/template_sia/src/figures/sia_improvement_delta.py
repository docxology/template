"""Generation-over-generation metric delta chart — publication-quality SIA figure.

Renders a vertical bar chart of Δaccuracy between consecutive SIA generations,
with:
* a zero reference line,
* signed colour coding (positive = teal, negative = rust),
* value annotations above / below each bar,
* a cumulative gain line overlaid on a secondary y-axis.

The figure communicates the *incremental* self-improvement signal at each
refinement step rather than the raw accumulated score.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from ..generation_records import generation_metrics, load_run_summary
from ..loop_config import load_sia_settings
from .figure_registry import FIGURE_SPECS, PALETTE, figure_path

_DPI = 160
_FIG_W, _FIG_H = 5.6, 3.8
_POS_COLOR = PALETTE["positive"]
_NEG_COLOR = PALETTE["negative"]
_CUM_COLOR = PALETTE["accent"]
_ANNOT = PALETTE["annotation"]
_GRID = PALETTE["grid"]
_INK = PALETTE["ink"]
_RULE = PALETTE["rule"]


def write_sia_improvement_delta(project_root: Path) -> Path:
    """Render a generation-over-generation metric delta chart.

    Produces ``output/figures/sia_improvement_delta.png``.
    """
    project_root = project_root.resolve()
    settings = load_sia_settings(project_root)
    summary = load_run_summary(project_root, run_id=settings.run_id)
    metrics = generation_metrics(summary)

    spec = FIGURE_SPECS[3]  # sia_improvement_delta
    out = figure_path(project_root, spec)
    out.parent.mkdir(parents=True, exist_ok=True)

    n_gen = len(metrics)
    if n_gen < 2:
        _write_placeholder(out, "Need ≥ 2 generations for delta chart")
        return out

    values = [float(row["metric_value"]) if row.get("metric_value") is not None else 0.0 for row in metrics]
    gen_labels = [f"Gen {metrics[i]['generation']}→{metrics[i + 1]['generation']}" for i in range(n_gen - 1)]
    deltas = [values[i + 1] - values[i] for i in range(n_gen - 1)]
    cumulative = [sum(deltas[: k + 1]) for k in range(len(deltas))]

    x = np.arange(len(deltas), dtype=float)
    bar_colors = [_POS_COLOR if d >= 0 else _NEG_COLOR for d in deltas]

    fig, ax1 = plt.subplots(figsize=(_FIG_W, _FIG_H))
    fig.patch.set_facecolor("white")
    ax1.set_facecolor("#fafafa")

    # ── bar chart (primary axis) ──────────────────────────────────────────────
    bars = ax1.bar(x, deltas, color=bar_colors, width=0.55, zorder=3, label="Δ accuracy")
    ax1.axhline(0, color=_RULE, linewidth=1.0, linestyle="-", zorder=2)

    # value annotations
    for bar, d in zip(bars, deltas):
        va = "bottom" if d >= 0 else "top"
        ax1.annotate(
            f"{d:+.1%}",
            xy=(bar.get_x() + bar.get_width() / 2, d),
            xytext=(0, 6 if d >= 0 else -6),
            textcoords="offset points",
            ha="center",
            va=va,
            fontsize=8.5,
            color=_ANNOT,
            fontweight="semibold",
        )

    ax1.set_ylabel("Δ accuracy per step", fontsize=10, color=_INK)
    ax1.set_xticks(x, labels=gen_labels, fontsize=9)
    ax1.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0, decimals=0))
    ax1.grid(True, axis="y", color=_GRID, linewidth=0.7, zorder=0)
    ax1.set_axisbelow(True)
    for spine in ("top", "right"):
        ax1.spines[spine].set_visible(False)
    ax1.spines["left"].set_color(_RULE)
    ax1.spines["bottom"].set_color(_RULE)

    # ── cumulative line (secondary axis) ─────────────────────────────────────
    ax2 = ax1.twinx()
    ax2.plot(
        x,
        cumulative,
        marker="D",
        markersize=6,
        linewidth=1.8,
        linestyle="--",
        color=_CUM_COLOR,
        zorder=4,
        label="cumulative Δ",
    )
    ax2.set_ylabel("cumulative Δ accuracy", fontsize=9, color=_CUM_COLOR)
    ax2.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1.0, decimals=0))
    ax2.tick_params(axis="y", labelcolor=_CUM_COLOR, labelsize=8)
    for spine in ("top",):
        ax2.spines[spine].set_visible(False)

    # ── combined legend ───────────────────────────────────────────────────────
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(
        handles1 + handles2,
        labels1 + labels2,
        fontsize=7.5,
        frameon=False,
        loc="upper left",
    )

    ax1.set_title(
        "Generation-over-generation metric delta",
        fontsize=11,
        color=_INK,
        pad=9,
    )
    fig.tight_layout(pad=1.2)
    fig.savefig(
        out,
        dpi=_DPI,
        metadata={"Software": None, "Creation Time": None, "Date": None},
    )
    plt.close(fig)
    return out


def _write_placeholder(out: Path, message: str) -> None:
    fig, ax = plt.subplots(figsize=(4, 2))
    ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes, fontsize=9)
    ax.axis("off")
    fig.savefig(out, dpi=_DPI, metadata={"Software": None, "Creation Time": None, "Date": None})
    plt.close(fig)


__all__ = ["write_sia_improvement_delta"]
