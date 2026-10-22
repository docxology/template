"""Infrastructure module inventory bar chart figure."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt

from ..core.introspection import ModuleInfo
from .viz_palette import (
    ARCH_VIZ_COLORS,
    FIGURE_DPI,
    FONT_FLOOR,
    doc_badge,
    save_presentation_manifest,
    save_presentation_panel,
)


def _module_inventory_figure(modules: Sequence[ModuleInfo]) -> tuple[plt.Figure, plt.Axes]:
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
        annotation = ax.text(
            width + 0.5,
            i,
            f"{module.python_file_count} [{doc_badge(module)}]",
            ha="left",
            va="center",
            fontsize=FONT_FLOOR + 2,
            fontweight="bold",
            color=ARCH_VIZ_COLORS["text_dark"],
        )
        annotation.set_gid("module-count-badge")

    ax.set_yticks(range(n))
    ax.set_yticklabels(names, fontsize=FONT_FLOOR + 2)
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
    ax.set_xticks(sorted({0, max_count // 2, max_count}))
    ax.tick_params(axis="x", labelsize=FONT_FLOOR + 2)
    ax.grid(True, alpha=0.20, axis="x", linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    total = sum(counts)
    fig.text(
        0.5,
        0.012,
        f"Total: {total} Python files · A=AGENTS R=README S=SKILL P=PAI",
        ha="center",
        va="bottom",
        fontsize=FONT_FLOOR + 2,
        color=ARCH_VIZ_COLORS["text_light"],
    )

    fig.tight_layout(pad=1.2, rect=(0, 0.045, 1, 1))
    return fig, ax


def generate_module_inventory(modules: Sequence[ModuleInfo], output_dir: Path) -> Path:
    """Generate a readable complete inventory with one count/badge per bar."""
    fig, _ = _module_inventory_figure(modules)
    path = output_dir / "module_inventory.png"
    try:
        save_presentation_panel(
            fig, path, "All infrastructure modules, largest first, with complete counts and badges."
        )
    finally:
        plt.close(fig)
    return path


def _module_inventory_panel_figure(
    modules: Sequence[ModuleInfo],
    *,
    maximum: int,
    first: int,
    total: int,
) -> tuple[plt.Figure, plt.Axes]:
    """Render six complete bars with the same global scale and documentation badges."""
    if not 1 <= len(modules) <= 6:
        raise ValueError("Inventory presentation panels require one to six bars")
    fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=FIGURE_DPI, facecolor="white")
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set(xlim=(0, 8.5), ylim=(0, 5.5))
    ax.axis("off")
    ax.text(
        4.25,
        5.4,
        f"Modules {first}–{first + len(modules) - 1} of {total}",
        ha="center",
        va="top",
        fontsize=34,
        fontweight="bold",
    )
    cmap = plt.get_cmap("Blues")
    for index, module in enumerate(modules):
        y = 4.55 - index * 0.52
        width = 1.25 * module.python_file_count / max(maximum, 1)
        ax.barh(
            y,
            width,
            left=4.25,
            color=cmap(0.35 + 0.55 * module.python_file_count / max(maximum, 1)),
            height=0.35,
            alpha=0.90,
        )
        ax.text(0.12, y, module.name, ha="left", va="center", fontsize=34)
        ax.text(5.65, y, str(module.python_file_count), ha="left", va="center", fontsize=34, fontweight="bold")
        ax.text(6.75, y, f"[{doc_badge(module)}]", ha="left", va="center", fontsize=34)
    ax.text(4.25, 1.27, "Python files · A AGENTS", ha="center", va="center", fontsize=34)
    ax.text(4.25, 0.77, "R README · S SKILL · P PAI", ha="center", va="center", fontsize=34)
    ax.text(4.25, 0.27, "· = absent", ha="center", va="center", fontsize=34)
    return fig, ax


def generate_module_inventory_presentation_panels(modules: Sequence[ModuleInfo], output_dir: Path) -> Path:
    """Preserve all largest-first inventory bars in source-bound slide panels."""
    ordered = sorted(modules, key=lambda module: module.python_file_count, reverse=True)
    maximum = max((module.python_file_count for module in ordered), default=1)
    panels = []
    for offset in range(0, len(ordered), 6):
        selected = ordered[offset : offset + 6]
        fig, _ = _module_inventory_panel_figure(selected, maximum=maximum, first=offset + 1, total=len(ordered))
        path = output_dir / f"module_inventory_panel_{offset // 6 + 1:02d}.png"
        alt = "Infrastructure inventory, largest first: " + "; ".join(
            f"{module.name}: {module.python_file_count} Python files, [{doc_badge(module)}]" for module in selected
        )
        try:
            panels.append(save_presentation_panel(fig, path, alt))
        finally:
            plt.close(fig)
    return save_presentation_manifest(output_dir / "module_inventory.panels.json", panels)
