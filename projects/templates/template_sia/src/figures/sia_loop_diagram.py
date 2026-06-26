"""Comprehensive SIA loop topology diagram — publication-quality variant.

Renders the three-agent Meta → Target → Feedback cycle as a polished
box-and-arrow diagram suitable for embedding in a manuscript PDF:

* rounded, shaded node boxes with bold labels and role subtitles,
* curved arrows with arrowheads styled from the PALETTE,
* a generation-counter annotation at the bottom,
* optional "live / fixture" mode badge in the top-right corner,
* white background, Agg backend (headless).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from .figure_registry import FIGURE_SPECS, PALETTE, figure_path

# ── layout constants ───────────────────────────────────────────────────────────
_DPI = 160
_FIG_W, _FIG_H = 7.2, 3.4
_BOX_W, _BOX_H = 1.8, 0.9
_Y_CENTER = 1.8  # vertical midpoint of all boxes
_NODES = [
    (1.0, _Y_CENTER, "Meta", "proposes agent"),
    (4.0, _Y_CENTER, "Target", "runs & records"),
    (7.0, _Y_CENTER, "Feedback", "reads & improves"),
]
_ARROW_Y = _Y_CENTER + _BOX_H / 2  # arrow passes through box midpoint
_INK = PALETTE["ink"]
_BOX_FACE = PALETTE["box_face"]
_BOX_EDGE = PALETTE["box_edge"]
_ARROW_COLOR = PALETTE["arrow"]
_ANNOT = PALETTE["annotation"]


def write_sia_loop_topology(project_root: Path) -> Path:
    """Render a publication-quality Meta → Target → Feedback loop diagram."""
    project_root = project_root.resolve()
    spec = FIGURE_SPECS[1]  # sia_loop_topology
    out = figure_path(project_root, spec)
    out.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(_FIG_W, _FIG_H))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 9.5)
    ax.set_ylim(0, 3.8)
    ax.axis("off")

    # ── draw node boxes ────────────────────────────────────────────────────────
    for x, y, label, subtitle in _NODES:
        patch = FancyBboxPatch(
            (x, y),
            _BOX_W,
            _BOX_H,
            boxstyle="round,pad=0.12",
            linewidth=1.6,
            edgecolor=_BOX_EDGE,
            facecolor=_BOX_FACE,
            zorder=3,
        )
        ax.add_patch(patch)
        ax.text(
            x + _BOX_W / 2,
            y + _BOX_H * 0.62,
            label,
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color=_INK,
            zorder=4,
        )
        ax.text(
            x + _BOX_W / 2,
            y + _BOX_H * 0.25,
            subtitle,
            ha="center",
            va="center",
            fontsize=7.5,
            color=_ANNOT,
            zorder=4,
        )

    # ── draw arrows ────────────────────────────────────────────────────────────
    # WHY: FancyArrowPatch kwargs are passed explicitly rather than via **dict
    # unpacking because mypy's matplotlib stubs cannot narrow the value type of a
    # dict literal, causing spurious arg-type errors on every **-unpack.

    # Meta → Target (forward)
    ax.add_patch(
        FancyArrowPatch(
            (_NODES[0][0] + _BOX_W, _ARROW_Y),
            (_NODES[1][0], _ARROW_Y),
            arrowstyle="-|>",
            mutation_scale=14,
            linewidth=1.6,
            color=_ARROW_COLOR,
            connectionstyle="arc3,rad=0.0",
            zorder=2,
        )
    )
    ax.text(2.9, _ARROW_Y + 0.18, "gen n", ha="center", fontsize=7.5, color=_ANNOT)

    # Target → Feedback (forward)
    ax.add_patch(
        FancyArrowPatch(
            (_NODES[1][0] + _BOX_W, _ARROW_Y),
            (_NODES[2][0], _ARROW_Y),
            arrowstyle="-|>",
            mutation_scale=14,
            linewidth=1.6,
            color=_ARROW_COLOR,
            connectionstyle="arc3,rad=0.0",
            zorder=2,
        )
    )
    ax.text(5.9, _ARROW_Y + 0.18, "results.json", ha="center", fontsize=7.5, color=_ANNOT)

    # Feedback → Meta (return arc below)
    _ret_y = _ARROW_Y - 1.15
    # Draw a bent arrow: down from Feedback, across, up to Meta
    ax.annotate(
        "",
        xy=(_NODES[0][0] + _BOX_W / 2, _Y_CENTER),  # arrive at Meta (bottom)
        xytext=(_NODES[2][0] + _BOX_W / 2, _Y_CENTER),  # start at Feedback (bottom)
        arrowprops=dict(
            arrowstyle="-|>",
            color=_ARROW_COLOR,
            lw=1.6,
            connectionstyle="arc3,rad=-0.42",
            mutation_scale=14,
        ),
        zorder=2,
    )
    ax.text(
        4.7,
        _ret_y + 0.08,
        "improvement.md  →  gen n+1",
        ha="center",
        fontsize=7.5,
        color=_ANNOT,
    )

    # ── generation counter ────────────────────────────────────────────────────
    ax.text(
        4.75,
        0.22,
        "generation  n  →  n+1",
        ha="center",
        fontsize=9,
        color=_ANNOT,
        style="italic",
    )

    # ── title ─────────────────────────────────────────────────────────────────
    ax.set_title(
        "SIA loop topology",
        fontsize=11,
        color=_INK,
        pad=6,
        loc="center",
    )

    fig.tight_layout(pad=0.8)
    fig.savefig(
        out,
        dpi=_DPI,
        metadata={"Software": None, "Creation Time": None, "Date": None},
    )
    plt.close(fig)
    return out


__all__ = ["write_sia_loop_topology"]
