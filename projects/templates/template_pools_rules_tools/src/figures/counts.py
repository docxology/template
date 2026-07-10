"""counts.py — Figure 2: Resource Counts — horizontal bar chart."""

from __future__ import annotations

import pathlib
from typing import Any

from ._theme import (
    _MPL_AVAILABLE,
    BG,
    BLUE,
    BLUE_LIGHT,
    GRID,
    NEUTRAL,
    TEAL,
    TEAL_LIGHT,
    WHITE,
    _resolve_output,
    _save,
    plt,
)

__all__ = [
    "generate_resource_counts",
]


def generate_resource_counts(
    output_dir: str | pathlib.Path | None = None,
    filename: str = "resource_counts.png",
    counts: dict[str, int] | None = None,
    _data: Any = None,
) -> pathlib.Path | None:
    """Generate a bar chart of resource counts."""
    if not _MPL_AVAILABLE:
        return None

    if counts is None:
        counts = {"Fonds": 3, "Tools": 3, "Rules": 2}

    dest = _resolve_output(output_dir, filename)
    fig, ax = plt.subplots(figsize=(8, 4), facecolor=BG)
    ax.set_facecolor(WHITE)

    names = list(counts.keys())
    vals = list(counts.values())
    colors_list = [BLUE, TEAL, BLUE_LIGHT, NEUTRAL, TEAL_LIGHT][: len(names)]

    bars = ax.bar(names, vals, color=colors_list, edgecolor="white", linewidth=1.2, width=0.55)
    for bar, val in zip(bars, vals, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.15,
            str(val),
            ha="center",
            fontsize=11,
            fontweight="bold",
            color=NEUTRAL,
        )

    ax.set_ylabel("Count", fontsize=10, color=NEUTRAL)
    ax.set_title(
        "Discovered Resources by Category",
        fontsize=13,
        fontweight="bold",
        color="#0f172a",
        pad=12,
    )
    ax.tick_params(colors=NEUTRAL, labelsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=0.4)
    ax.set_ylim(0, max(max(vals) * 1.4, 1) if vals else 5)
    fig.tight_layout()
    return _save(fig, dest)
