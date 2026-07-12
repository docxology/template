"""Pipeline stage flow diagram figure."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib.patches as patches
import matplotlib.pyplot as plt

from .introspection import PipelineStage
from .viz_palette import ARCH_VIZ_COLORS, FIGURE_DPI, FONT_FLOOR, short_stage_label, stage_color


def generate_pipeline_stages(stages: Sequence[PipelineStage], output_dir: Path) -> Path:
    """Generate the pipeline stage flow diagram from YAML-declared stages."""
    fig, ax = plt.subplots(figsize=(22, 5.5))
    n = len(stages)
    box_w = 0.92 / max(n, 1)
    box_h = 0.62
    box_y = 0.18

    for i, stage in enumerate(stages):
        x = 0.04 + i * box_w + box_w * 0.04
        w = box_w * 0.92
        fill = stage_color(stage)

        shadow = patches.FancyBboxPatch(
            (x + 0.003, box_y - 0.015),
            w,
            box_h,
            boxstyle="round,pad=0.018",
            facecolor="#00000015",
            edgecolor="none",
            transform=ax.transAxes,
            zorder=0,
        )
        ax.add_patch(shadow)

        rect = patches.FancyBboxPatch(
            (x, box_y),
            w,
            box_h,
            boxstyle="round,pad=0.018",
            facecolor=fill,
            edgecolor="white",
            linewidth=2.5,
            alpha=0.92,
            transform=ax.transAxes,
        )
        ax.add_patch(rect)

        ax.text(
            x + w / 2,
            box_y + box_h - 0.12,
            f"{i + 1:02d}",
            ha="center",
            va="center",
            fontsize=FONT_FLOOR,
            fontweight="bold",
            color="white",
            transform=ax.transAxes,
        )

        name = short_stage_label(stage.name)
        if len(name) > 14:
            words = name.split()
            mid = len(words) // 2
            name = " ".join(words[:mid]) + "\n" + " ".join(words[mid:])
        ax.text(
            x + w / 2,
            box_y + box_h / 2 - 0.02,
            name,
            ha="center",
            va="center",
            fontsize=max(FONT_FLOOR - 4, 11),
            fontweight="semibold",
            color="white",
            transform=ax.transAxes,
            linespacing=1.2,
        )

        tag_text = ", ".join(stage.tags) if stage.tags else ""
        if tag_text:
            ax.text(
                x + w / 2,
                box_y + 0.08,
                tag_text,
                ha="center",
                va="center",
                fontsize=max(FONT_FLOOR - 6, 9),
                color="#ffffffbb",
                transform=ax.transAxes,
                style="italic",
            )

        if i < n - 1:
            arr_x = x + w + box_w * 0.01
            ax.text(
                arr_x + box_w * 0.01,
                box_y + box_h / 2,
                "▸",
                ha="center",
                va="center",
                fontsize=FONT_FLOOR + 2,
                color=ARCH_VIZ_COLORS["pipeline"],
                fontweight="bold",
                transform=ax.transAxes,
            )

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title(
        f"Pipeline DAG ({n} declared stages)",
        fontsize=22,
        fontweight="bold",
        pad=12,
        color=ARCH_VIZ_COLORS["text_dark"],
    )

    plt.tight_layout(pad=0.3)
    path = output_dir / "pipeline_stages.png"
    plt.savefig(path, dpi=FIGURE_DPI, bbox_inches="tight", facecolor="white")
    plt.close()
    return path
