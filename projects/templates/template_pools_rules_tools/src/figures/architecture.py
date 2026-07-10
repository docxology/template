"""architecture.py — Figure 1: Architecture Overview — three-panel diagram."""

from __future__ import annotations

import pathlib

from ._theme import (
    _MPL_AVAILABLE,
    BG,
    BLUE,
    BLUE_LIGHT,
    GRID,
    NEUTRAL,
    TEAL,
    WHITE,
    _resolve_output,
    _save,
    plt,
)

__all__ = [
    "generate_architecture_overview",
]


def generate_architecture_overview(
    output_dir: str | pathlib.Path | None = None,
    filename: str = "architecture_overview.png",
) -> pathlib.Path | None:
    """Generate a three-panel figure showing fonds → rules → tools architecture."""
    if not _MPL_AVAILABLE:
        return None

    dest = _resolve_output(output_dir, filename)
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), facecolor=BG)
    panel_titles = (
        "Fonds (Data Pools)",
        "Rules (Specifications)",
        "Tools (Entrypoints)",
    )

    for ax, title, entries, color in zip(
        axes,
        panel_titles,
        [
            [("Bibliography", 8), ("Contacts", 5), ("Datasets", 5)],
            [("Project Rules", 4), ("Manuscript Rules", 4)],
            [("Code Executor", 2), ("Validator", 2), ("Skill", 2)],
        ],
        [BLUE, TEAL, BLUE_LIGHT],
        strict=True,
    ):
        ax.set_facecolor(WHITE)
        ax.set_title(title, fontsize=11, fontweight="bold", color=color, pad=12)
        labels_vals = [e[0] for e in entries]
        widths_vals = [e[1] for e in entries]
        y_pos = range(len(labels_vals))
        bars = ax.barh(
            y_pos,
            widths_vals,
            height=0.55,
            color=color,
            edgecolor="white",
            linewidth=0.5,
        )
        for bar, val in zip(bars, widths_vals, strict=True):
            ax.text(
                bar.get_width() + 0.3,
                bar.get_y() + bar.get_height() / 2,
                str(val),
                va="center",
                fontsize=9,
                color=NEUTRAL,
            )
        ax.set_yticks(list(y_pos))
        ax.set_yticklabels(labels_vals, fontsize=9)
        ax.tick_params(axis="x", colors=NEUTRAL, labelsize=8)
        ax.set_xlim(0, max(widths_vals) * 1.5)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.grid(axis="x", color=GRID, linewidth=0.4)

    fig.text(0.5, -0.02, "Resource Counts by Category", ha="center", fontsize=10, color=NEUTRAL)
    fig.suptitle(
        "Research Resource Architecture: Fonds × Rules × Tools",
        fontsize=14,
        fontweight="bold",
        color="#0f172a",
        y=1.02,
    )
    fig.tight_layout(pad=2)
    return _save(fig, dest)
