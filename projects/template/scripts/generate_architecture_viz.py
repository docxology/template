#!/usr/bin/env python3
"""Architecture visualization generator — Thin Orchestrator.

Imports introspection functions from ``src/template/`` to gather real
repository data, then produces publication-quality figures in ``output/figures/``.

Figures generated:
    1. architecture_overview.png — Two-Layer Architecture diagram
    2. pipeline_stages.png — 8-stage pipeline flow
    3. module_dependency.png — Infrastructure module inventory
"""

import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Ensure src/ is importable
PROJECT_DIR = Path(os.environ.get("PROJECT_DIR", Path(__file__).parent.parent))
SRC_DIR = PROJECT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from template import (
    discover_infrastructure_modules,
    count_pipeline_stages,
    discover_projects,
)

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# Repo root
REPO_ROOT = PROJECT_DIR.parent.parent
OUTPUT_DIR = PROJECT_DIR / "output" / "figures"

# Colorblind-safe palette (IBM Design / Wong palette)
COLORS = {
    "infra": "#0072B2",
    "project": "#D55E00",
    "pipeline": "#009E73",
    "accent": "#CC79A7",
    "neutral": "#999999",
    "bg_infra": "#e3f2fd",
    "bg_project": "#fff3e0",
    "bg_pipeline": "#e8f5e9",
    "white": "#ffffff",
}

FONT_FLOOR = 16  # Accessibility: minimum font size


def generate_architecture_overview(modules, projects):
    """Generate the Two-Layer Architecture overview figure.

    Shows infrastructure modules in the upper layer and project workspaces
    in the lower layer, connected by the pipeline arrow.
    """
    fig, ax = plt.subplots(figsize=(14, 9))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Title
    ax.text(50, 97, "The Docxology Template: Two-Layer Architecture",
            ha="center", va="top", fontsize=20, fontweight="bold")

    # --- Infrastructure Layer ---
    ax.add_patch(patches.FancyBboxPatch(
        (5, 55), 90, 35, boxstyle="round,pad=2",
        facecolor=COLORS["bg_infra"], edgecolor=COLORS["infra"],
        linewidth=2.5, alpha=0.7,
    ))
    ax.text(50, 87, "INFRASTRUCTURE LAYER", ha="center", va="center",
            fontsize=FONT_FLOOR + 2, fontweight="bold", color=COLORS["infra"])
    ax.text(50, 82, f"{len(modules)} reusable subpackages · v2.0.0",
            ha="center", va="center", fontsize=FONT_FLOOR - 2,
            color=COLORS["neutral"], style="italic")

    # Module circles
    n_cols = min(len(modules), 5)
    n_rows = (len(modules) + n_cols - 1) // n_cols
    for idx, mod in enumerate(modules):
        row, col = divmod(idx, n_cols)
        cx = 15 + col * 18
        cy = 73 - row * 10
        ax.add_patch(patches.FancyBboxPatch(
            (cx - 7, cy - 3), 14, 6, boxstyle="round,pad=0.5",
            facecolor=COLORS["white"], edgecolor=COLORS["infra"],
            linewidth=1.5,
        ))
        label = mod.name.replace("_", "\n") if len(mod.name) > 8 else mod.name
        ax.text(cx, cy, label, ha="center", va="center",
                fontsize=max(9, FONT_FLOOR - 6), fontweight="medium")

    # --- Pipeline Arrow ---
    ax.annotate("", xy=(50, 20), xytext=(50, 55),
                arrowprops=dict(arrowstyle="-|>", lw=3, color=COLORS["pipeline"],
                                connectionstyle="arc3,rad=0"))
    ax.text(55, 38, "8-Stage\nPipeline", ha="left", va="center",
            fontsize=FONT_FLOOR, fontweight="bold", color=COLORS["pipeline"])

    # --- Project Layer ---
    ax.add_patch(patches.FancyBboxPatch(
        (5, 2), 90, 18, boxstyle="round,pad=2",
        facecolor=COLORS["bg_project"], edgecolor=COLORS["project"],
        linewidth=2.5, alpha=0.7,
    ))
    ax.text(50, 17, "PROJECT LAYER", ha="center", va="center",
            fontsize=FONT_FLOOR + 2, fontweight="bold", color=COLORS["project"])

    # Project boxes
    n_proj = len(projects)
    proj_width = min(25, 80 / max(n_proj, 1))
    start_x = 50 - (n_proj * proj_width) / 2
    for i, proj in enumerate(projects):
        px = start_x + i * proj_width + proj_width / 2
        ax.add_patch(patches.FancyBboxPatch(
            (px - proj_width / 2 + 1, 5), proj_width - 2, 8,
            boxstyle="round,pad=0.3",
            facecolor=COLORS["white"], edgecolor=COLORS["project"],
            linewidth=1.5,
        ))
        ax.text(px, 9, proj.name.replace("_", "\n"),
                ha="center", va="center",
                fontsize=max(9, FONT_FLOOR - 5), fontweight="medium")

    plt.tight_layout()
    path = OUTPUT_DIR / "architecture_overview.png"
    plt.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    logger.info(f"Saved architecture overview to {path}")
    return path


def generate_pipeline_stages(stages):
    """Generate the pipeline stage flow diagram.

    Horizontal waterfall showing each numbered stage with its script name.
    """
    fig, ax = plt.subplots(figsize=(16, 6))
    n = len(stages)
    box_w = 0.85 / max(n, 1)
    box_h = 0.55

    colors = plt.cm.viridis(np.linspace(0.2, 0.85, n))

    for i, stage in enumerate(stages):
        x = 0.05 + i * box_w + box_w * 0.05
        w = box_w * 0.9

        rect = patches.FancyBboxPatch(
            (x, 0.25), w, box_h, boxstyle="round,pad=0.02",
            facecolor=colors[i], edgecolor="white", linewidth=2, alpha=0.85,
            transform=ax.transAxes,
        )
        ax.add_patch(rect)

        # Stage number
        ax.text(x + w / 2, 0.68, f"Stage {stage.number:02d}",
                ha="center", va="center", fontsize=FONT_FLOOR - 2,
                fontweight="bold", color="white", transform=ax.transAxes)

        # Stage name (wrap long names)
        name = stage.name.replace(" ", "\n") if len(stage.name) > 12 else stage.name
        ax.text(x + w / 2, 0.48, name,
                ha="center", va="center", fontsize=max(9, FONT_FLOOR - 5),
                color="white", transform=ax.transAxes)

        # Arrow between stages
        if i < n - 1:
            ax.annotate("", xy=(x + w + box_w * 0.05, 0.52),
                        xytext=(x + w, 0.52),
                        arrowprops=dict(arrowstyle="-|>", lw=2, color=COLORS["neutral"]),
                        xycoords=ax.transAxes, textcoords=ax.transAxes)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("Docxology Template: 8-Stage Build Pipeline",
                 fontsize=20, fontweight="bold", pad=20)

    plt.tight_layout()
    path = OUTPUT_DIR / "pipeline_stages.png"
    plt.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    logger.info(f"Saved pipeline stages to {path}")
    return path


def generate_module_inventory(modules):
    """Generate an infrastructure module inventory bar chart.

    Shows Python file count per module with documentation status indicators.
    """
    fig, ax = plt.subplots(figsize=(12, 7))

    names = [m.name for m in modules]
    counts = [m.python_file_count for m in modules]

    bars = ax.barh(range(len(names)), counts, color=COLORS["infra"], alpha=0.85)

    # Annotate each bar
    for i, (bar, mod) in enumerate(zip(bars, modules)):
        # File count label
        ax.text(bar.get_width() + 0.3, i, str(mod.python_file_count),
                ha="left", va="center", fontsize=FONT_FLOOR - 2, fontweight="bold")
        # Documentation indicators (text labels — DejaVu Sans lacks emoji glyphs)
        doc_parts = []
        if mod.has_agents_md:
            doc_parts.append("A")
        if mod.has_readme_md:
            doc_parts.append("R")
        if doc_parts:
            doc_label = "[" + "+".join(doc_parts) + "]"
            ax.text(-0.5, i, doc_label, ha="right", va="center",
                    fontsize=10, fontstyle="italic", color="#555555")

    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=FONT_FLOOR - 2)
    ax.set_xlabel("Python Files", fontsize=FONT_FLOOR, fontweight="medium")
    ax.set_title("Infrastructure Module Inventory",
                 fontsize=20, fontweight="bold", pad=15)
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3, axis="x")

    plt.tight_layout()
    path = OUTPUT_DIR / "module_inventory.png"
    plt.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    logger.info(f"Saved module inventory to {path}")
    return path


def main():
    """Generate all architecture visualizations."""
    logger.info("Starting architecture visualization generation...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Gather real data via introspection
    modules = discover_infrastructure_modules(REPO_ROOT)
    projects = discover_projects(REPO_ROOT)
    stages = count_pipeline_stages(REPO_ROOT / "scripts")

    logger.info(f"Data: {len(modules)} modules, {len(projects)} projects, {len(stages)} stages")

    # Generate figures
    p1 = generate_architecture_overview(modules, projects)
    p2 = generate_pipeline_stages(stages)
    p3 = generate_module_inventory(modules)

    logger.info("Architecture visualization generation complete")
    logger.info(f"  • {p1}")
    logger.info(f"  • {p2}")
    logger.info(f"  • {p3}")


if __name__ == "__main__":
    main()
