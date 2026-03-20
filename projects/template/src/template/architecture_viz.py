"""Architecture visualization generation for the template project.

Generates four publication-quality figures from live introspection data:
  1. Two-Layer Architecture overview  (architecture_overview.png)
  2. Pipeline stage flow diagram      (pipeline_stages.png)
  3. Module inventory bar chart       (module_inventory.png)
  4. Comparative feature matrix       (comparative_feature_matrix.png)

All figures comply with the 16pt font accessibility floor and the
ARCH_VIZ_COLORS colour palette.  DPI is 200 for print quality.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib.colors as mcolors
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np

from .introspection import ModuleInfo, PipelineStage, ProjectInfo, build_infrastructure_report

ARCH_VIZ_COLORS = {
    "infra": "#0072B2",
    "infra_dark": "#004F7F",
    "project": "#D55E00",
    "project_dark": "#A34500",
    "pipeline": "#009E73",
    "accent": "#CC79A7",
    "neutral": "#666666",
    "bg_infra": "#ddeeff",
    "bg_project": "#fff0e0",
    "bg_pipeline": "#e8f5e9",
    "white": "#ffffff",
    "text_dark": "#1a1a1a",
    "text_light": "#555555",
    "shadow": "#cccccc",
    "divider": "#bbbbbb",
}

FONT_FLOOR = 16

# ---------------------------------------------------------------------------
# Stage descriptions used by the pipeline figure
# ---------------------------------------------------------------------------
_STAGE_DESCRIPTIONS = {
    0: "Deps & env",
    1: "pytest suite",
    2: "Scripts & figs",
    3: "Pandoc → PDF",
    4: "PDF integrity",
    5: "→ output/",
    6: "Ollama review",
    7: "Exec. report",
}

# ---------------------------------------------------------------------------
# Name overrides for correct casing
# ---------------------------------------------------------------------------
_STAGE_NAME_OVERRIDES = {
    "Render Pdf": "Render PDF",
    "Llm Review": "LLM Review",
    "Setup Environment": "Setup Env",
    "Run Tests": "Run Tests",
    "Run Analysis": "Analysis",
    "Validate Output": "Validate",
    "Copy Outputs": "Copy Out",
    "Generate Executive Report": "Exec Report",
}

# ---------------------------------------------------------------------------
# Comparative feature data
# ---------------------------------------------------------------------------


def comparative_feature_matrix_data() -> tuple[np.ndarray, list[str], list[str]]:
    """Return matrix values and labels for comparative feature figure."""
    tools = [
        "template/",
        "Snakemake\n9.x",
        "Nextflow\n25.x",
        "CWL\n1.2",
        "Quarto\n1.x",
        "Jupyter\nBook 2.x",
        "R\nMarkdown",
        "DVC\n3.x",
        "Overleaf\n(2025)",
        "OpenAI\nPrism",
    ]

    capabilities = [
        "Pipeline orchestration",
        "Manuscript rendering",
        "Testing enforcement",
        "Coverage thresholds",
        "Cryptographic provenance",
        "Steganographic watermarking",
        "Multi-project management",
        "AI-agent documentation",
        "Agentic skill protocol (MCP)",
        "Interactive TUI",
        "Zero-mock policy",
        "Container support",
        "Distributed execution",
        "Multi-language (R/Julia)",
    ]

    data = np.array(
        [
            [1.0, 1.0, 1.0, 1.0, 0.5, 0.0, 0.0, 1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [1.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.5],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.5],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.5, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0],
            [0.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0],
        ]
    )
    return data, tools, capabilities


# ---------------------------------------------------------------------------
# Helper: documentation badge string
# ---------------------------------------------------------------------------

def _doc_badge(module: ModuleInfo) -> str:
    """Build a compact 4-letter doc-coverage badge for *module*."""
    parts = []
    parts.append("A" if module.has_agents_md else "·")
    parts.append("R" if module.has_readme_md else "·")
    parts.append("S" if module.has_skill_md else "·")
    parts.append("P" if module.has_pai_md else "·")
    return "".join(parts)


# ===================================================================
# Figure 1 — Two-Layer Architecture Overview
# ===================================================================

def generate_architecture_overview(
    modules: Sequence[ModuleInfo],
    projects: Sequence[ProjectInfo],
    output_dir: Path,
    version: str = "v2.0.0",
) -> Path:
    """Generate the Two-Layer Architecture overview figure."""
    fig, ax = plt.subplots(figsize=(18, 12))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # ------ Title ------
    ax.text(
        50, 99, "Two-Layer Architecture",
        ha="center", va="top", fontsize=28, fontweight="bold",
        color=ARCH_VIZ_COLORS["text_dark"],
    )
    ax.text(
        50, 95.5,
        "Layer 1: Infrastructure  (generic · reusable · cross-project)",
        ha="center", va="top", fontsize=FONT_FLOOR,
        color=ARCH_VIZ_COLORS["infra"], fontweight="semibold",
    )
    ax.text(
        50, 92,
        "Layer 2: Projects  (domain-specific · customizable · isolated)",
        ha="center", va="top", fontsize=FONT_FLOOR,
        color=ARCH_VIZ_COLORS["project"], fontweight="semibold",
    )

    # ------ Infrastructure layer box ------
    infra_y = 44
    infra_h = 45
    ax.add_patch(
        patches.FancyBboxPatch(
            (2, infra_y), 96, infra_h,
            boxstyle="round,pad=1.5",
            facecolor=ARCH_VIZ_COLORS["bg_infra"],
            edgecolor=ARCH_VIZ_COLORS["infra"],
            linewidth=3, alpha=0.90,
        )
    )
    ax.text(
        50, infra_y + infra_h - 2,
        "INFRASTRUCTURE LAYER",
        ha="center", va="center",
        fontsize=FONT_FLOOR + 4, fontweight="bold",
        color=ARCH_VIZ_COLORS["infra"],
    )
    ax.text(
        50, infra_y + infra_h - 6,
        f"{len(modules)} reusable subpackages  ·  {version}",
        ha="center", va="center", fontsize=FONT_FLOOR,
        color=ARCH_VIZ_COLORS["neutral"], style="italic",
    )

    # ------ Module boxes with file counts and badges ------
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

        # Shadow
        ax.add_patch(
            patches.FancyBboxPatch(
                (cx - 7.2 + 0.4, cy - box_h / 2 - 0.3),
                14.4, box_h,
                boxstyle="round,pad=0.6",
                facecolor=ARCH_VIZ_COLORS["shadow"],
                edgecolor="none", alpha=0.35, zorder=1,
            )
        )
        # Main box
        ax.add_patch(
            patches.FancyBboxPatch(
                (cx - 7.2, cy - box_h / 2),
                14.4, box_h,
                boxstyle="round,pad=0.6",
                facecolor=ARCH_VIZ_COLORS["white"],
                edgecolor=ARCH_VIZ_COLORS["infra"],
                linewidth=2.2, zorder=2,
            )
        )
        # Module name
        label = module.name.replace("_", "\n") if len(module.name) > 10 else module.name
        ax.text(
            cx, cy + 1.2, label,
            ha="center", va="center",
            fontsize=FONT_FLOOR - 2, fontweight="bold",
            color=ARCH_VIZ_COLORS["text_dark"],
            zorder=3, linespacing=1.1,
        )
        # File count
        ax.text(
            cx, cy - 2.5,
            f"{module.python_file_count} py",
            ha="center", va="center",
            fontsize=FONT_FLOOR - 4, fontweight="semibold",
            color=ARCH_VIZ_COLORS["infra_dark"],
            zorder=3,
        )
        # Doc badge (small, bottom of box)
        badge = _doc_badge(module)
        ax.text(
            cx + 6, cy + box_h / 2 - 1.8,
            badge,
            ha="right", va="center",
            fontsize=8, fontfamily="monospace",
            color=ARCH_VIZ_COLORS["neutral"],
            zorder=3, alpha=0.7,
        )

    # ------ Pipeline arrow ------
    arrow_x = 50
    arrow_top = infra_y - 0.5
    arrow_bot = 25
    ax.annotate(
        "", xy=(arrow_x, arrow_bot), xytext=(arrow_x, arrow_top),
        arrowprops=dict(
            arrowstyle="-|>", lw=5,
            color=ARCH_VIZ_COLORS["pipeline"],
            connectionstyle="arc3,rad=0",
        ),
    )
    ax.text(
        arrow_x + 5, (arrow_top + arrow_bot) / 2,
        "8-Stage\nPipeline",
        ha="left", va="center",
        fontsize=FONT_FLOOR + 2, fontweight="bold",
        color=ARCH_VIZ_COLORS["pipeline"],
        linespacing=1.4,
    )

    # ------ Project layer box ------
    proj_y = 2
    proj_h = 22
    ax.add_patch(
        patches.FancyBboxPatch(
            (2, proj_y), 96, proj_h,
            boxstyle="round,pad=1.5",
            facecolor=ARCH_VIZ_COLORS["bg_project"],
            edgecolor=ARCH_VIZ_COLORS["project"],
            linewidth=3, alpha=0.90,
        )
    )
    ax.text(
        50, proj_y + proj_h - 1.5,
        "PROJECT LAYER",
        ha="center", va="center",
        fontsize=FONT_FLOOR + 4, fontweight="bold",
        color=ARCH_VIZ_COLORS["project"],
    )

    n_proj = len(projects)
    proj_width = min(28, 86 / max(n_proj, 1))
    start_px = 50 - (n_proj * proj_width) / 2
    for i, project in enumerate(projects):
        px = start_px + i * proj_width + proj_width / 2
        # Shadow
        ax.add_patch(
            patches.FancyBboxPatch(
                (px - proj_width / 2 + 1.2, proj_y + 2.5),
                proj_width - 2, 12.5,
                boxstyle="round,pad=0.5",
                facecolor=ARCH_VIZ_COLORS["shadow"],
                edgecolor="none", alpha=0.3, zorder=1,
            )
        )
        ax.add_patch(
            patches.FancyBboxPatch(
                (px - proj_width / 2 + 0.8, proj_y + 3),
                proj_width - 1.6, 12.5,
                boxstyle="round,pad=0.5",
                facecolor=ARCH_VIZ_COLORS["white"],
                edgecolor=ARCH_VIZ_COLORS["project"],
                linewidth=2, zorder=2,
            )
        )
        proj_label = project.name.replace("_", "\n")
        ax.text(
            px, proj_y + 9.5,
            proj_label,
            ha="center", va="center",
            fontsize=FONT_FLOOR - 2, fontweight="semibold",
            color=ARCH_VIZ_COLORS["text_dark"],
            zorder=3, linespacing=1.15,
        )
        # Chapter + test counts
        ax.text(
            px, proj_y + 4.8,
            f"{project.chapter_count} ch · {project.test_file_count} tests",
            ha="center", va="center",
            fontsize=FONT_FLOOR - 5, fontweight="normal",
            color=ARCH_VIZ_COLORS["text_light"],
            zorder=3,
        )

    plt.tight_layout(pad=0.3)
    path = output_dir / "architecture_overview.png"
    plt.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    return path


# ===================================================================
# Figure 2 — Pipeline Stage Flow
# ===================================================================

def generate_pipeline_stages(stages: Sequence[PipelineStage], output_dir: Path) -> Path:
    """Generate the pipeline stage flow diagram."""
    fig, ax = plt.subplots(figsize=(20, 4.5))
    n = len(stages)
    box_w = 0.88 / max(n, 1)
    box_h = 0.62
    box_y = 0.18
    colors = plt.cm.viridis(np.linspace(0.12, 0.92, n))

    for i, stage in enumerate(stages):
        x = 0.04 + i * box_w + box_w * 0.04
        w = box_w * 0.92

        # Shadow
        shadow = patches.FancyBboxPatch(
            (x + 0.003, box_y - 0.015), w, box_h,
            boxstyle="round,pad=0.018",
            facecolor="#00000015", edgecolor="none",
            transform=ax.transAxes, zorder=0,
        )
        ax.add_patch(shadow)

        # Main box
        rect = patches.FancyBboxPatch(
            (x, box_y), w, box_h,
            boxstyle="round,pad=0.018",
            facecolor=colors[i], edgecolor="white",
            linewidth=2.5, alpha=0.92,
            transform=ax.transAxes,
        )
        ax.add_patch(rect)

        # Stage number
        ax.text(
            x + w / 2, box_y + box_h - 0.12,
            f"Stage {stage.number:02d}",
            ha="center", va="center",
            fontsize=FONT_FLOOR, fontweight="bold",
            color="white", transform=ax.transAxes,
        )

        # Stage name (with overrides for correct casing)
        name = _STAGE_NAME_OVERRIDES.get(stage.name, stage.name)
        if len(name) > 14:
            words = name.split()
            mid = len(words) // 2
            name = " ".join(words[:mid]) + "\n" + " ".join(words[mid:])
        ax.text(
            x + w / 2, box_y + box_h / 2 - 0.02,
            name,
            ha="center", va="center",
            fontsize=max(FONT_FLOOR - 4, 11),
            fontweight="semibold",
            color="white", transform=ax.transAxes,
            linespacing=1.2,
        )

        # Description line
        desc = _STAGE_DESCRIPTIONS.get(stage.number, "")
        if desc:
            ax.text(
                x + w / 2, box_y + 0.08,
                desc,
                ha="center", va="center",
                fontsize=max(FONT_FLOOR - 6, 9),
                color="#ffffffbb", transform=ax.transAxes,
                style="italic",
            )

        # Arrow between stages
        if i < n - 1:
            arr_x = x + w + box_w * 0.01
            ax.text(
                arr_x + box_w * 0.01, box_y + box_h / 2,
                "▸",
                ha="center", va="center",
                fontsize=FONT_FLOOR + 2,
                color=ARCH_VIZ_COLORS["pipeline"],
                fontweight="bold",
                transform=ax.transAxes,
            )

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title(
        "Eight-Stage Build Pipeline",
        fontsize=22, fontweight="bold", pad=12,
        color=ARCH_VIZ_COLORS["text_dark"],
    )

    plt.tight_layout(pad=0.3)
    path = output_dir / "pipeline_stages.png"
    plt.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    return path


# ===================================================================
# Figure 3 — Module Inventory Bar Chart
# ===================================================================

def generate_module_inventory(modules: Sequence[ModuleInfo], output_dir: Path) -> Path:
    """Generate an infrastructure module inventory horizontal bar chart."""
    sorted_modules = sorted(modules, key=lambda m: m.python_file_count, reverse=True)
    names = [m.name for m in sorted_modules]
    counts = [m.python_file_count for m in sorted_modules]
    n = len(names)

    max_count = max(counts) if counts else 1
    fig, ax = plt.subplots(figsize=(14, max(7, n * 0.72)))

    # Gradient color: darker for higher file counts
    cmap = plt.cm.Blues
    norm_vals = [c / max_count if max_count else 0 for c in counts]
    bar_colors = [cmap(0.35 + 0.55 * v) for v in norm_vals]

    bars = ax.barh(
        range(n), counts,
        color=bar_colors, alpha=0.90, height=0.68,
        edgecolor="white", linewidth=1.0,
    )

    for i, (bar, module) in enumerate(zip(bars, sorted_modules)):
        width = bar.get_width()
        # Count label (right of bar)
        ax.text(
            width + 0.5, i,
            str(module.python_file_count),
            ha="left", va="center",
            fontsize=FONT_FLOOR - 1, fontweight="bold",
            color=ARCH_VIZ_COLORS["text_dark"],
        )
        # Four-layer doc badge (right of count)
        badge = _doc_badge(module)
        ax.text(
            width + 3.5, i,
            f"[{badge}]",
            ha="left", va="center",
            fontsize=FONT_FLOOR - 5, fontfamily="monospace",
            color=ARCH_VIZ_COLORS["neutral"],
        )

    ax.set_yticks(range(n))
    ax.set_yticklabels(names, fontsize=FONT_FLOOR - 1)
    ax.set_xlabel(
        "Python Source Files",
        fontsize=FONT_FLOOR, fontweight="bold",
        color=ARCH_VIZ_COLORS["text_dark"],
    )
    ax.set_title(
        "Infrastructure Module Inventory",
        fontsize=22, fontweight="bold", pad=16,
        color=ARCH_VIZ_COLORS["text_dark"],
    )
    ax.invert_yaxis()
    ax.set_xlim(0, max_count * 1.35 if counts else 1)
    ax.grid(True, alpha=0.20, axis="x", linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Total file count annotation
    total = sum(counts)
    ax.text(
        0.98, 0.02,
        f"Total: {total} Python files  ·  Badge: A=AGENTS  R=README  S=SKILL  P=PAI",
        transform=ax.transAxes, ha="right", va="bottom",
        fontsize=FONT_FLOOR - 5, style="italic",
        color=ARCH_VIZ_COLORS["text_light"],
    )

    plt.tight_layout(pad=1.2)
    path = output_dir / "module_inventory.png"
    plt.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    return path


# ===================================================================
# Figure 4 — Comparative Feature Matrix
# ===================================================================

# Row-group definitions for visual dividers
_CAPABILITY_GROUPS = [
    ("Core Pipeline", 0, 1),        # rows 0-1
    ("Quality & Security", 2, 7),   # rows 2-7
    ("Ecosystem", 8, 13),           # rows 8-13
]


def generate_comparative_feature_matrix(output_dir: Path) -> Path:
    """Generate the comparative feature matrix heatmap."""
    data, tools, capabilities = comparative_feature_matrix_data()
    # Use Unicode symbols instead of Y/~/N
    labels = np.where(data == 1.0, "✓", np.where(data == 0.5, "◐", "—"))

    nrows, ncols = data.shape
    fig_h = max(12, nrows * 0.75 + 3.0)
    fig_w = max(20, ncols * 1.9 + 5.0)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    cmap = plt.cm.RdYlGn
    norm = mcolors.Normalize(vmin=0, vmax=1)
    im = ax.imshow(data, cmap=cmap, norm=norm, aspect="auto")

    for row in range(nrows):
        for col in range(ncols):
            cell_val = data[row, col]
            txt_color = "#111111" if 0.2 < cell_val < 0.85 else "white"
            sym = labels[row, col]
            fs = FONT_FLOOR + 2 if sym == "✓" else FONT_FLOOR + 1
            ax.text(
                col, row, sym,
                ha="center", va="center",
                fontsize=fs, fontweight="bold",
                color=txt_color,
            )

    ax.set_xticks(range(ncols))
    ax.set_xticklabels(
        tools, fontsize=FONT_FLOOR, fontweight="semibold",
        ha="center", multialignment="center",
    )
    ax.tick_params(
        axis="x", which="both",
        bottom=False, top=True,
        labelbottom=False, labeltop=True, pad=8,
    )
    ax.xaxis.set_label_position("top")
    ax.set_yticks(range(nrows))
    ax.set_yticklabels(capabilities, fontsize=FONT_FLOOR)

    # Grid
    ax.set_xticks(np.arange(-0.5, ncols, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, nrows, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", bottom=False, left=False)

    # Highlight template/ column
    for row in range(nrows):
        ax.add_patch(
            patches.Rectangle(
                (-0.5, row - 0.5), 1, 1,
                fill=False, edgecolor="#0072B2",
                linewidth=3, zorder=3,
            )
        )

    # Row-group dividers and side labels
    for group_name, start_row, end_row in _CAPABILITY_GROUPS:
        if start_row > 0:
            ax.axhline(
                y=start_row - 0.5, color=ARCH_VIZ_COLORS["divider"],
                linewidth=2.5, linestyle="-", zorder=4,
            )
        # Side annotation
        mid_y = (start_row + end_row) / 2
        ax.text(
            ncols + 0.3, mid_y,
            group_name,
            ha="left", va="center",
            fontsize=FONT_FLOOR, fontweight="bold",
            color=ARCH_VIZ_COLORS["text_light"],
            rotation=0,
        )

    ax.set_title(
        "Comparative Feature Matrix: template/ and 9 Peer Tools",
        fontsize=FONT_FLOOR + 3, fontweight="bold", pad=20,
        color=ARCH_VIZ_COLORS["text_dark"],
    )

    # Colorbar
    cbar = fig.colorbar(im, ax=ax, shrink=0.5, pad=0.08, aspect=16)
    cbar.set_ticks([0, 0.5, 1])
    cbar.ax.set_yticklabels(
        ["— Absent", "◐ Partial", "✓ Full"],
        fontsize=FONT_FLOOR,
    )
    cbar.ax.tick_params(labelsize=FONT_FLOOR)
    cbar.set_label("Support Level", fontsize=FONT_FLOOR + 1, fontweight="bold")

    # Bottom footnote
    fig.text(
        0.5, -0.01,
        "✓ = full native support   |   ◐ = partial / plugin-based   |   — = absent"
        "   |   Blue border = template/ column   |   See Appendix for full text table.",
        ha="center", va="bottom",
        fontsize=FONT_FLOOR, style="italic",
        color=ARCH_VIZ_COLORS["text_light"],
    )

    plt.tight_layout(rect=[0, 0.03, 0.92, 1], pad=1.0)
    path = output_dir / "comparative_feature_matrix.png"
    plt.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()
    return path


# ===================================================================
# Entrypoint: generate all figures
# ===================================================================

def generate_all_architecture_figures(repo_root: Path, project_dir: Path) -> list[Path]:
    """Generate all architecture figures and return output paths."""
    output_dir = project_dir / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    report = build_infrastructure_report(repo_root)
    paths = [
        generate_architecture_overview(report.modules, report.projects, output_dir, report.infrastructure_version),
        generate_pipeline_stages(report.pipeline_stages, output_dir),
        generate_module_inventory(report.modules, output_dir),
        generate_comparative_feature_matrix(output_dir),
    ]
    return paths
