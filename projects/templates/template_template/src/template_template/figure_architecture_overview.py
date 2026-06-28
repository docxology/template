"""Two-layer architecture overview figure."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib.patches as patches
import matplotlib.pyplot as plt

from .introspection import ModuleInfo, ProjectAnalysis
from .viz_palette import ARCH_VIZ_COLORS, FONT_FLOOR, doc_badge


def generate_architecture_overview(
    modules: Sequence[ModuleInfo],
    projects: Sequence[ProjectAnalysis],
    output_dir: Path,
    version: str = "v2.0.0",
) -> Path:
    """Generate the Two-Layer Architecture overview figure."""
    fig, ax = plt.subplots(figsize=(18, 12))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.text(
        50,
        99,
        "Two-Layer Architecture",
        ha="center",
        va="top",
        fontsize=28,
        fontweight="bold",
        color=ARCH_VIZ_COLORS["text_dark"],
    )
    ax.text(
        50,
        95.5,
        "Layer 1: Infrastructure  (generic · reusable · cross-project)",
        ha="center",
        va="top",
        fontsize=FONT_FLOOR,
        color=ARCH_VIZ_COLORS["infra"],
        fontweight="semibold",
    )
    ax.text(
        50,
        92,
        "Layer 2: Projects  (domain-specific · customizable · isolated)",
        ha="center",
        va="top",
        fontsize=FONT_FLOOR,
        color=ARCH_VIZ_COLORS["project"],
        fontweight="semibold",
    )

    infra_y = 44
    infra_h = 45
    ax.add_patch(
        patches.FancyBboxPatch(
            (2, infra_y),
            96,
            infra_h,
            boxstyle="round,pad=1.5",
            facecolor=ARCH_VIZ_COLORS["bg_infra"],
            edgecolor=ARCH_VIZ_COLORS["infra"],
            linewidth=3,
            alpha=0.90,
        )
    )
    ax.text(
        50,
        infra_y + infra_h - 2,
        "INFRASTRUCTURE LAYER",
        ha="center",
        va="center",
        fontsize=FONT_FLOOR + 4,
        fontweight="bold",
        color=ARCH_VIZ_COLORS["infra"],
    )
    ax.text(
        50,
        infra_y + infra_h - 6,
        f"{len(modules)} reusable subpackages  ·  {version}",
        ha="center",
        va="center",
        fontsize=FONT_FLOOR,
        color=ARCH_VIZ_COLORS["neutral"],
        style="italic",
    )

    n_cols = 6
    col_width = 15.5
    n_mods = len(modules)
    xs_start = 50 - (min(n_mods, n_cols) * col_width / 2)
    box_h = 9.5
    row_gap = 11.5

    for idx, module in enumerate(modules):
        row, col = divmod(idx, n_cols)
        cx = xs_start + col * col_width + col_width / 2
        cy = (infra_y + infra_h - 12) - row * row_gap

        ax.add_patch(
            patches.FancyBboxPatch(
                (cx - 7.2 + 0.4, cy - box_h / 2 - 0.3),
                14.4,
                box_h,
                boxstyle="round,pad=0.6",
                facecolor=ARCH_VIZ_COLORS["shadow"],
                edgecolor="none",
                alpha=0.35,
                zorder=1,
            )
        )
        ax.add_patch(
            patches.FancyBboxPatch(
                (cx - 7.2, cy - box_h / 2),
                14.4,
                box_h,
                boxstyle="round,pad=0.6",
                facecolor=ARCH_VIZ_COLORS["white"],
                edgecolor=ARCH_VIZ_COLORS["infra"],
                linewidth=2.2,
                zorder=2,
            )
        )
        label = module.name.replace("_", "\n") if len(module.name) > 10 else module.name
        ax.text(
            cx,
            cy + 1.2,
            label,
            ha="center",
            va="center",
            fontsize=FONT_FLOOR - 2,
            fontweight="bold",
            color=ARCH_VIZ_COLORS["text_dark"],
            zorder=3,
            linespacing=1.1,
        )
        ax.text(
            cx,
            cy - 2.5,
            f"{module.python_file_count} py",
            ha="center",
            va="center",
            fontsize=FONT_FLOOR - 4,
            fontweight="semibold",
            color=ARCH_VIZ_COLORS["infra_dark"],
            zorder=3,
        )
        badge = doc_badge(module)
        ax.text(
            cx + 6,
            cy + box_h / 2 - 1.8,
            badge,
            ha="right",
            va="center",
            fontsize=8,
            fontfamily="monospace",
            color=ARCH_VIZ_COLORS["neutral"],
            zorder=3,
            alpha=0.7,
        )

    arrow_x = 50
    arrow_top = infra_y - 0.5
    arrow_bot = 25
    ax.annotate(
        "",
        xy=(arrow_x, arrow_bot),
        xytext=(arrow_x, arrow_top),
        arrowprops=dict(
            arrowstyle="-|>",
            lw=5,
            color=ARCH_VIZ_COLORS["pipeline"],
            connectionstyle="arc3,rad=0",
        ),
    )
    ax.text(
        arrow_x + 5,
        (arrow_top + arrow_bot) / 2,
        f"YAML DAG\n{len(modules)} modules",
        ha="left",
        va="center",
        fontsize=FONT_FLOOR + 2,
        fontweight="bold",
        color=ARCH_VIZ_COLORS["pipeline"],
        linespacing=1.4,
    )

    # Documentation-badge legend (left of the DAG arrow): decode the [ARSP]
    # four-slot badge printed on every infrastructure module box.
    legend_x = 8
    legend_y = arrow_bot + 1
    ax.add_patch(
        patches.FancyBboxPatch(
            (legend_x - 1.5, legend_y - 1),
            34,
            13,
            boxstyle="round,pad=0.5",
            facecolor=ARCH_VIZ_COLORS["white"],
            edgecolor=ARCH_VIZ_COLORS["divider"],
            linewidth=1.5,
            alpha=0.95,
            zorder=4,
        )
    )
    ax.text(
        legend_x,
        legend_y + 10,
        "Doc badge",
        ha="left",
        va="center",
        fontsize=FONT_FLOOR - 4,
        fontweight="bold",
        color=ARCH_VIZ_COLORS["text_dark"],
        zorder=5,
    )
    for row, (glyph, meaning) in enumerate(
        [
            ("A", "AGENTS.md"),
            ("R", "README.md"),
            ("S", "SKILL.md"),
            ("P", "PAI.md  ( ·  = absent )"),
        ]
    ):
        ax.text(
            legend_x,
            legend_y + 7.5 - row * 2.4,
            f"{glyph}  ·  {meaning}",
            ha="left",
            va="center",
            fontsize=FONT_FLOOR - 6,
            fontfamily="monospace",
            color=ARCH_VIZ_COLORS["neutral"],
            zorder=5,
        )

    proj_y = 2
    proj_h = 22
    ax.add_patch(
        patches.FancyBboxPatch(
            (2, proj_y),
            96,
            proj_h,
            boxstyle="round,pad=1.5",
            facecolor=ARCH_VIZ_COLORS["bg_project"],
            edgecolor=ARCH_VIZ_COLORS["project"],
            linewidth=3,
            alpha=0.90,
        )
    )
    ax.text(
        50,
        proj_y + proj_h - 1.5,
        "PROJECT LAYER",
        ha="center",
        va="center",
        fontsize=FONT_FLOOR + 4,
        fontweight="bold",
        color=ARCH_VIZ_COLORS["project"],
    )

    n_proj = len(projects)
    proj_width = min(28, 86 / max(n_proj, 1))
    start_px = 50 - (n_proj * proj_width) / 2
    for i, project in enumerate(projects):
        px = start_px + i * proj_width + proj_width / 2
        ax.add_patch(
            patches.FancyBboxPatch(
                (px - proj_width / 2 + 1.2, proj_y + 2.5),
                proj_width - 2,
                12.5,
                boxstyle="round,pad=0.5",
                facecolor=ARCH_VIZ_COLORS["shadow"],
                edgecolor="none",
                alpha=0.3,
                zorder=1,
            )
        )
        ax.add_patch(
            patches.FancyBboxPatch(
                (px - proj_width / 2 + 0.8, proj_y + 3),
                proj_width - 1.6,
                12.5,
                boxstyle="round,pad=0.5",
                facecolor=ARCH_VIZ_COLORS["white"],
                edgecolor=ARCH_VIZ_COLORS["project"],
                linewidth=2,
                zorder=2,
            )
        )
        proj_label = project.name.replace("_", "\n")
        ax.text(
            px,
            proj_y + 9.5,
            proj_label,
            ha="center",
            va="center",
            fontsize=FONT_FLOOR - 2,
            fontweight="semibold",
            color=ARCH_VIZ_COLORS["text_dark"],
            zorder=3,
            linespacing=1.15,
        )
        ax.text(
            px,
            proj_y + 4.8,
            f"{project.chapter_count} ch · {project.test_file_count} tests",
            ha="center",
            va="center",
            fontsize=FONT_FLOOR - 5,
            fontweight="normal",
            color=ARCH_VIZ_COLORS["text_light"],
            zorder=3,
        )

    plt.tight_layout(pad=0.3)
    path = output_dir / "architecture_overview.png"
    plt.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    return path
