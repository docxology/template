"""Per-generation metric heatmap — publication-quality SIA figure.

Renders a 2-row × N-column heatmap where each column is a generation and the
two rows show:
  * Row 0 — accuracy (normalised 0–1),
  * Row 1 — sample count (normalised to the run maximum).

Cell annotations display the raw value.  The colour scale uses a sequential
blue palette (``PALETTE["accent"]`` family) so it is colourblind-safe and
prints well in greyscale.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ..generation_records import generation_metrics, load_run_summary
from ..loop_config import load_sia_settings
from .figure_registry import FIGURE_SPECS, PALETTE, figure_path

_DPI = 160
_INK = PALETTE["ink"]
_ANNOT = PALETTE["annotation"]
_GRID = PALETTE["grid"]
_CMAP = "Blues"


def write_sia_generation_heatmap(project_root: Path) -> Path:
    """Render a per-generation metric heatmap.

    Produces ``output/figures/sia_generation_heatmap.png``.
    """
    project_root = project_root.resolve()
    settings = load_sia_settings(project_root)
    summary = load_run_summary(project_root, run_id=settings.run_id)
    metrics = generation_metrics(summary)

    spec = FIGURE_SPECS[2]  # sia_generation_heatmap
    out = figure_path(project_root, spec)
    out.parent.mkdir(parents=True, exist_ok=True)

    n_gen = len(metrics)
    if n_gen == 0:
        _write_empty(out)
        return out

    gen_labels = [f"Gen {row['generation']}" for row in metrics]
    acc_vals = [float(row["metric_value"]) if row.get("metric_value") is not None else 0.0 for row in metrics]
    n_vals = [int(row["n_samples"]) if row.get("n_samples") else 0 for row in metrics]

    max_n = max(n_vals) if n_vals else 1

    # matrix: shape (2, n_gen) — row 0: accuracy, row 1: normalised n_samples
    matrix = np.array(
        [acc_vals, [v / max_n for v in n_vals]],
        dtype=float,
    )

    # raw annotation strings
    cell_text = [
        [f"{v:.1%}" for v in acc_vals],
        [str(v) for v in n_vals],
    ]

    row_labels = ["Accuracy", "N samples (norm)"]

    fig_h = max(2.0, 0.7 * 2 + 1.2)
    fig_w = max(4.0, 1.5 * n_gen + 1.6)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.patch.set_facecolor("white")

    im = ax.imshow(matrix, cmap=_CMAP, vmin=0.0, vmax=1.0, aspect="auto")

    # cell annotations
    threshold = 0.55
    for row_i in range(matrix.shape[0]):
        for col_i in range(matrix.shape[1]):
            val = matrix[row_i, col_i]
            text_color = "white" if val > threshold else _INK
            ax.text(
                col_i,
                row_i,
                cell_text[row_i][col_i],
                ha="center",
                va="center",
                fontsize=9.5,
                color=text_color,
                fontweight="semibold",
            )

    # axes labels
    ax.set_xticks(range(n_gen), labels=gen_labels, fontsize=9)
    ax.set_yticks(range(2), labels=row_labels, fontsize=9)
    ax.tick_params(axis="both", length=0)
    ax.set_title("Generation metrics heatmap", fontsize=11, color=_INK, pad=9)

    # colourbar
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=7.5)
    cbar.set_label("normalised value", fontsize=8, color=_ANNOT)

    fig.tight_layout(pad=1.1)
    fig.savefig(
        out,
        dpi=_DPI,
        metadata={"Software": None, "Creation Time": None, "Date": None},
    )
    plt.close(fig)
    return out


def _write_empty(out: Path) -> None:
    """Write a placeholder PNG when no metric data is available."""
    fig, ax = plt.subplots(figsize=(4, 2))
    ax.text(0.5, 0.5, "No metric data", ha="center", va="center", transform=ax.transAxes)
    ax.axis("off")
    fig.savefig(out, dpi=_DPI, metadata={"Software": None, "Creation Time": None, "Date": None})
    plt.close(fig)


__all__ = ["write_sia_generation_heatmap"]
