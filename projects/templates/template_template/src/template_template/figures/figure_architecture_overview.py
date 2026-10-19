"""Two-layer architecture overview with a complete, readable project roster."""

from __future__ import annotations

from math import ceil
from pathlib import Path
from textwrap import fill
from typing import Sequence

import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ..core.introspection import ModuleInfo, ProjectAnalysis
from .viz_palette import ARCH_VIZ_COLORS, FIGURE_DPI, FONT_FLOOR, doc_badge


def _architecture_figure(
    modules: Sequence[ModuleInfo], projects: Sequence[ProjectAnalysis], version: str
) -> tuple[Figure, Axes]:
    """Lay out every discovered item in bounded cards at fixed readable sizes.

    Rows grow with the roster rather than narrowing all projects into one row.
    Coordinates are physical inches, so more rows never shrink existing text.
    """
    columns = 5
    row_height = 0.82
    module_rows = ceil(len(modules) / columns)
    project_rows = ceil(len(projects) / columns)
    width = 12.0
    height = 2.8 + row_height * (module_rows + project_rows)
    fig = plt.figure(figsize=(width, height), facecolor="white")
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set(xlim=(0, width), ylim=(0, height))
    ax.axis("off")
    ax.text(
        width / 2,
        height - 0.16,
        "Two-Layer Architecture",
        ha="center",
        va="top",
        fontsize=24,
        fontweight="bold",
        color=ARCH_VIZ_COLORS["text_dark"],
    )

    def panel(top: float, rows: int, title: str, subtitle: str, color: str, background: str) -> float:
        bottom = top - 0.82 - rows * row_height
        ax.add_patch(
            patches.FancyBboxPatch(
                (0.2, bottom),
                width - 0.4,
                top - bottom,
                boxstyle="round,pad=0.03",
                linewidth=1.5,
                edgecolor=color,
                facecolor=background,
                zorder=0,
            )
        )
        ax.text(
            width / 2,
            top - 0.14,
            title,
            ha="center",
            va="top",
            fontsize=FONT_FLOOR,
            fontweight="bold",
            color=color,
        )
        ax.text(
            width / 2,
            top - 0.49,
            subtitle,
            ha="center",
            va="top",
            fontsize=12,
            color=ARCH_VIZ_COLORS["neutral"],
        )
        return bottom

    infra_top = height - 0.7
    infra_bottom = panel(
        infra_top,
        module_rows,
        "Layer 1 · Infrastructure · generic and reusable",
        f"{len(modules)} directories · {version} · badges: A AGENTS · R README · S SKILL · P PAI · absent = ·",
        ARCH_VIZ_COLORS["infra"],
        ARCH_VIZ_COLORS["bg_infra"],
    )
    project_top = infra_bottom - 0.42
    panel(
        project_top,
        project_rows,
        "Layer 2 · Projects · isolated domain logic",
        f"{len(projects)} projects · template_ prefix omitted from card labels · ch = manuscript chapters",
        ARCH_VIZ_COLORS["project"],
        ARCH_VIZ_COLORS["bg_project"],
    )
    ax.annotate(
        "",
        xy=(width / 2, project_top + 0.03),
        xytext=(width / 2, infra_bottom - 0.03),
        arrowprops={"arrowstyle": "-|>", "color": ARCH_VIZ_COLORS["pipeline"], "lw": 2},
    )

    card_width = (width - 0.8) / columns

    def card(index: int, top: float, label: str, detail: str, color: str, badge: str = "") -> None:
        row, column = divmod(index, columns)
        left = 0.4 + column * card_width
        bottom = top - 0.78 - (row + 1) * row_height
        box = patches.FancyBboxPatch(
            (left + 0.04, bottom + 0.08),
            card_width - 0.08,
            row_height - 0.12,
            boxstyle="round,pad=0.02",
            facecolor="white",
            edgecolor=color,
            linewidth=1,
        )
        box.set_gid("architecture-card")
        ax.add_patch(box)
        center = left + card_width / 2
        name = ax.text(
            center,
            bottom + 0.53,
            fill(label.replace("_", " "), width=17),
            ha="center",
            va="center",
            fontsize=FONT_FLOOR,
            fontweight="semibold",
            color=ARCH_VIZ_COLORS["text_dark"],
            linespacing=1.05,
        )
        name.set_gid("architecture-card-label")
        metric = ax.text(
            center,
            bottom + 0.20,
            detail,
            ha="center",
            va="center",
            fontsize=12,
            color=color,
        )
        metric.set_gid("architecture-card-detail")
        if badge:
            metric.set_text(detail + " · " + badge)

    for index, module in enumerate(modules):
        card(
            index,
            infra_top,
            module.name,
            f"{module.python_file_count} py",
            ARCH_VIZ_COLORS["infra_dark"],
            f"[{doc_badge(module)}]",
        )
    for index, project in enumerate(projects):
        card(
            index,
            project_top,
            project.name.removeprefix("template_"),
            f"{project.chapter_count} ch · {project.test_file_count} test files",
            ARCH_VIZ_COLORS["project"],
        )
    return fig, ax


def generate_architecture_overview(
    modules: Sequence[ModuleInfo],
    projects: Sequence[ProjectAnalysis],
    output_dir: Path,
    version: str = "v2.0.0",
) -> Path:
    """Generate a two-layer overview without dropping or overlapping projects."""
    fig, _ = _architecture_figure(modules, projects, version)
    path = output_dir / "architecture_overview.png"
    try:
        fig.savefig(path, dpi=FIGURE_DPI, facecolor="white")
    finally:
        plt.close(fig)
    return path
