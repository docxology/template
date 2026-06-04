"""Diagram of Meta → Target → Feedback loop."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from .figure_registry import FIGURE_SPECS, figure_path


def write_sia_loop_topology(project_root: Path) -> Path:
    """Render a simple loop topology diagram."""
    project_root = project_root.resolve()
    spec = FIGURE_SPECS[1]
    out = figure_path(project_root, spec)
    out.parent.mkdir(parents=True, exist_ok=True)

    fig, axis = plt.subplots(figsize=(6.0, 3.0))
    axis.set_xlim(0, 10)
    axis.set_ylim(0, 4)
    axis.axis("off")

    boxes = [
        (1.0, 1.5, "Meta"),
        (4.0, 1.5, "Target"),
        (7.0, 1.5, "Feedback"),
    ]
    for x, y, label in boxes:
        patch = FancyBboxPatch(
            (x, y),
            2.0,
            1.0,
            boxstyle="round,pad=0.05",
            linewidth=1.2,
            edgecolor="#0f172a",
            facecolor="#ecfdf5",
        )
        axis.add_patch(patch)
        axis.text(x + 1.0, y + 0.5, label, ha="center", va="center", fontsize=11)

    for start, end in ((3.0, 4.0), (6.0, 7.0), (8.0, 2.0)):
        arrow = FancyArrowPatch(
            (start, 2.0),
            (end, 2.0),
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=1.2,
            color="#0f766e",
        )
        axis.add_patch(arrow)

    axis.text(5.0, 0.4, "generation n → n+1", ha="center", fontsize=10, color="#334155")
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


__all__ = ["write_sia_loop_topology"]
