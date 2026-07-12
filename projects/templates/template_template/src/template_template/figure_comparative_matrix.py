"""Comparative feature matrix figure and static benchmark data."""

from __future__ import annotations

from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np

from .viz_palette import ARCH_VIZ_COLORS, FIGURE_DPI, FONT_FLOOR

_CAPABILITY_GROUPS = [
    ("Core Pipeline", 0, 1),
    ("Quality & Security", 2, 7),
    ("Ecosystem", 8, 13),
]


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


def generate_comparative_feature_matrix(output_dir: Path) -> Path:
    """Generate the comparative feature matrix heatmap."""
    data, tools, capabilities = comparative_feature_matrix_data()
    labels = np.where(data == 1.0, "✓", np.where(data == 0.5, "◐", "—"))

    nrows, ncols = data.shape
    fig_h = max(12, nrows * 0.75 + 3.0)
    fig_w = max(20, ncols * 1.9 + 5.0)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    cmap = plt.get_cmap("RdYlGn")
    norm = mcolors.Normalize(vmin=0, vmax=1)
    im = ax.imshow(data, cmap=cmap, norm=norm, aspect="auto")

    for row in range(nrows):
        for col in range(ncols):
            cell_val = data[row, col]
            txt_color = "#111111" if 0.2 < cell_val < 0.85 else "white"
            sym = labels[row, col]
            fs = FONT_FLOOR + 2 if sym == "✓" else FONT_FLOOR + 1
            ax.text(
                col,
                row,
                sym,
                ha="center",
                va="center",
                fontsize=fs,
                fontweight="bold",
                color=txt_color,
            )

    ax.set_xticks(range(ncols))
    ax.set_xticklabels(
        tools,
        fontsize=FONT_FLOOR,
        fontweight="semibold",
        ha="center",
        multialignment="center",
    )
    ax.tick_params(
        axis="x",
        which="both",
        bottom=False,
        top=True,
        labelbottom=False,
        labeltop=True,
        pad=8,
    )
    ax.xaxis.set_label_position("top")
    ax.set_yticks(range(nrows))
    ax.set_yticklabels(capabilities, fontsize=FONT_FLOOR)

    ax.set_xticks(np.arange(-0.5, ncols, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, nrows, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", bottom=False, left=False)

    for row in range(nrows):
        ax.add_patch(
            patches.Rectangle(
                (-0.5, row - 0.5),
                1,
                1,
                fill=False,
                edgecolor="#0072B2",
                linewidth=3,
                zorder=3,
            )
        )

    for group_name, start_row, end_row in _CAPABILITY_GROUPS:
        if start_row > 0:
            ax.axhline(
                y=start_row - 0.5,
                color=ARCH_VIZ_COLORS["divider"],
                linewidth=2.5,
                linestyle="-",
                zorder=4,
            )
        mid_y = (start_row + end_row) / 2
        ax.text(
            ncols + 0.3,
            mid_y,
            group_name,
            ha="left",
            va="center",
            fontsize=FONT_FLOOR,
            fontweight="bold",
            color=ARCH_VIZ_COLORS["text_light"],
            rotation=0,
        )

    ax.set_title(
        "Comparative Feature Matrix: template/ and 9 Peer Tools",
        fontsize=FONT_FLOOR + 3,
        fontweight="bold",
        pad=20,
        color=ARCH_VIZ_COLORS["text_dark"],
    )

    cbar = fig.colorbar(im, ax=ax, shrink=0.5, pad=0.08, aspect=16)
    cbar.set_ticks([0, 0.5, 1])
    cbar.ax.set_yticklabels(
        ["— Absent", "◐ Partial", "✓ Full"],
        fontsize=FONT_FLOOR,
    )
    cbar.ax.tick_params(labelsize=FONT_FLOOR)
    cbar.set_label("Support Level", fontsize=FONT_FLOOR + 1, fontweight="bold")

    fig.text(
        0.5,
        -0.01,
        "✓ = full native support   |   ◐ = partial / plugin-based   |   — = absent"
        "   |   Blue border = template/ column   |   See Appendix for full text table.",
        ha="center",
        va="bottom",
        fontsize=FONT_FLOOR,
        style="italic",
        color=ARCH_VIZ_COLORS["text_light"],
    )

    plt.tight_layout(rect=(0, 0.03, 0.92, 1), pad=1.0)
    path = output_dir / "comparative_feature_matrix.png"
    plt.savefig(path, dpi=FIGURE_DPI, bbox_inches="tight", facecolor="white")
    plt.close()
    return path
