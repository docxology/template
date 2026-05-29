"""Infrastructure module inventory bar chart figure."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt

from .introspection import ModuleInfo
from .viz_palette import ARCH_VIZ_COLORS, FONT_FLOOR, doc_badge


def generate_module_inventory(modules: Sequence[ModuleInfo], output_dir: Path) -> Path:
    """Generate an infrastructure module inventory horizontal bar chart."""
    sorted_modules = sorted(modules, key=lambda m: m.python_file_count, reverse=True)
    names = [m.name for m in sorted_modules]
    counts = [m.python_file_count for m in sorted_modules]
    n = len(names)

    max_count = max(counts) if counts else 1
    fig, ax = plt.subplots(figsize=(14, max(7, n * 0.72)))

    cmap = plt.get_cmap("Blues")
    norm_vals = [c / max_count if max_count else 0 for c in counts]
    bar_colors = [cmap(0.35 + 0.55 * v) for v in norm_vals]

    bars = ax.barh(
        range(n),
        counts,
        color=bar_colors,
        alpha=0.90,
        height=0.68,
        edgecolor="white",
        linewidth=1.0,
    )

    for i, (bar, module) in enumerate(zip(bars, sorted_modules)):
        width = bar.get_width()
        ax.text(
            width + 0.5,
            i,
            str(module.python_file_count),
            ha="left",
            va="center",
            fontsize=FONT_FLOOR - 1,
            fontweight="bold",
            color=ARCH_VIZ_COLORS["text_dark"],
        )
        badge = doc_badge(module)
        ax.text(
            width + 3.5,
            i,
            f"[{badge}]",
            ha="left",
            va="center",
            fontsize=FONT_FLOOR - 5,
            fontfamily="monospace",
            color=ARCH_VIZ_COLORS["neutral"],
        )

    ax.set_yticks(range(n))
    ax.set_yticklabels(names, fontsize=FONT_FLOOR - 1)
    ax.set_xlabel(
        "Python Source Files",
        fontsize=FONT_FLOOR,
        fontweight="bold",
        color=ARCH_VIZ_COLORS["text_dark"],
    )
    ax.set_title(
        "Infrastructure Module Inventory",
        fontsize=22,
        fontweight="bold",
        pad=16,
        color=ARCH_VIZ_COLORS["text_dark"],
    )
    ax.invert_yaxis()
    ax.set_xlim(0, max_count * 1.35 if counts else 1)
    ax.grid(True, alpha=0.20, axis="x", linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    total = sum(counts)
    ax.text(
        0.98,
        0.02,
        f"Total: {total} Python files  ·  Badge: A=AGENTS  R=README  S=SKILL  P=PAI",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=FONT_FLOOR - 5,
        style="italic",
        color=ARCH_VIZ_COLORS["text_light"],
    )

    plt.tight_layout(pad=1.2)
    path = output_dir / "module_inventory.png"
    plt.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    return path
