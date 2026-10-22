"""Complete declared-stage references for article and presentation figures."""

from __future__ import annotations
from math import ceil
from pathlib import Path
from typing import Sequence
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from ..core.introspection import PipelineStage
from .viz_palette import (
    FIGURE_DPI,
    stage_color,
    save_presentation_manifest,
    save_presentation_panel,
    wrap_presentation_label,
    presentation_renderer,
)


def _draw_pipeline_detail(fig: Figure, ax: Axes, selected: Sequence[PipelineStage], *, offset: int, total: int) -> None:
    """Draw one physical9×6.6inch complete stage-detail area without scaling text."""
    ax.set(xlim=(0, 9), ylim=(0, 6.6))
    ax.axis("off")
    ax.text(
        4.5,
        6.5,
        f"Stages {offset + 1}–{offset + len(selected)} of {total}",
        ha="center",
        va="top",
        fontsize=40,
        fontweight="bold",
    )
    for index, stage in enumerate(selected):
        y = 5.2 - index * 1.15
        ax.add_patch(
            patches.Rectangle((0.08, y - 0.53), 8.84, 1.07, facecolor=stage_color(stage), alpha=0.12, edgecolor="none")
        )
        ax.text(0.45, y, str(offset + index + 1), ha="center", va="center", fontsize=40, fontweight="bold")
        name = ax.text(3.5, y, "", ha="center", va="center", fontsize=40, linespacing=1.0)
        name.set_text(
            wrap_presentation_label(stage.name, presentation_renderer(fig), name.get_fontproperties(), 4.8 * fig.dpi)
        )
        name.set_gid("pipeline-stage-name")
        tags = ax.text(7.4, y, "", ha="center", va="center", fontsize=36, linespacing=1.0)
        tags.set_text(
            "\n".join(
                wrap_presentation_label(tag, presentation_renderer(fig), tags.get_fontproperties(), 3.0 * fig.dpi)
                for tag in stage.tags
            )
            or "(none)"
        )
        tags.set_gid("pipeline-stage-tags")


def _pipeline_overview_figure(stages: Sequence[PipelineStage]) -> Figure:
    """Arrange source-drawn detail areas in reading order; grow rows if needed."""
    if not stages:
        raise ValueError("The declared-stage overview requires actual stages")
    count = ceil(len(stages) / 5)
    columns = min(2, count)
    rows = ceil(count / columns)
    width = columns * 9.0 + (columns - 1) * 0.2 + 0.2
    height = rows * 6.6 + (rows - 1) * 0.2 + 0.2
    fig = plt.figure(figsize=(width, height), dpi=FIGURE_DPI, facecolor="white")
    for panel, offset in enumerate(range(0, len(stages), 5)):
        row, column = divmod(panel, columns)
        left = 0.1 + column * 9.2
        bottom = 0.1 + (rows - row - 1) * 6.8
        ax = fig.add_axes((left / width, bottom / height, 9.0 / width, 6.6 / height))
        _draw_pipeline_detail(fig, ax, stages[offset : offset + 5], offset=offset, total=len(stages))
    return fig


def generate_pipeline_stages(stages: Sequence[PipelineStage], output_dir: Path) -> Path:
    """Generate a readable complete declaration overview, not inferred DAG edges."""
    fig = _pipeline_overview_figure(stages)
    path = output_dir / "pipeline_stages.png"
    try:
        save_presentation_panel(fig, path, "Complete YAML stage declarations in reading order; full names and tags.")
    finally:
        plt.close(fig)
    return path


def generate_pipeline_presentation_panels(stages: Sequence[PipelineStage], output_dir: Path) -> Path:
    """Reuse the same actual drawing for complete unabridged slide details."""
    panels = []
    for offset in range(0, len(stages), 5):
        selected = stages[offset : offset + 5]
        fig = plt.figure(figsize=(9.0, 6.6), dpi=FIGURE_DPI, facecolor="white")
        ax = fig.add_axes((0, 0, 1, 1))
        _draw_pipeline_detail(fig, ax, selected, offset=offset, total=len(stages))
        path = output_dir / f"pipeline_stages_panel_{offset // 5 + 1:02d}.png"
        alt = "Declared stages in YAML order; final column lists all tags: " + "; ".join(
            f"{offset + index + 1}: {stage.name} [{', '.join(stage.tags)}]" for index, stage in enumerate(selected)
        )
        try:
            panels.append(save_presentation_panel(fig, path, alt))
        finally:
            plt.close(fig)
    return save_presentation_manifest(output_dir / "pipeline_stages.panels.json", panels)
