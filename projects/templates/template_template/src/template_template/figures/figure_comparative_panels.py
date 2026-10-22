"""Complete, measured slide details for the canonical comparative matrix."""

from __future__ import annotations
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from .figure_comparative_matrix import comparative_feature_matrix_data
from .viz_palette import (
    FIGURE_DPI,
    save_presentation_manifest,
    save_presentation_panel,
    wrap_presentation_label,
    presentation_renderer,
)


def generate_comparative_presentation_panels(output_dir: Path) -> Path:
    """Keep all140 cells, with an explicit tool key and complete capability labels."""
    data, tools, capabilities = comparative_feature_matrix_data()
    panels = []
    fig = plt.figure(figsize=(8.5, 6.0), dpi=FIGURE_DPI, facecolor="white")
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set(xlim=(0, 8.5), ylim=(0, 6.0))
    ax.axis("off")
    ax.text(4.25, 5.9, "Tool key · A–J", ha="center", va="top", fontsize=34, fontweight="bold")
    for index, tool in enumerate(tools):
        column, row = divmod(index, 5)
        label = ax.text(
            2.15 + column * 4.15, 4.95 - row * 0.9875, "", ha="center", va="center", fontsize=34, linespacing=1.0
        )
        label.set_text(
            wrap_presentation_label(
                chr(65 + index) + " " + tool.replace("\n", " "),
                presentation_renderer(fig),
                label.get_fontproperties(),
                3.8 * fig.dpi,
            )
        )
    ax.text(4.25, 0.26, "✓ full · ◐ partial · — absent", ha="center", va="center", fontsize=34)
    try:
        panels.append(
            save_presentation_panel(
                fig,
                output_dir / "comparative_tool_key.png",
                "Tool key in source order: "
                + "; ".join(chr(65 + index) + " " + tool.replace("\n", " ") for index, tool in enumerate(tools)),
            )
        )
    finally:
        plt.close(fig)
    offset = 0
    while offset < len(capabilities):
        fig = plt.figure(figsize=(8.5, 6.2), dpi=FIGURE_DPI, facecolor="white")
        ax = fig.add_axes((0, 0, 1, 1))
        ax.set(xlim=(0, 8.5), ylim=(0, 6.2))
        ax.axis("off")
        prototype = ax.text(0, 0, "", fontsize=34)
        selected: list[tuple[int, str, int]] = []
        line_count = 0
        for row in range(offset, min(offset + 3, len(capabilities))):
            wrapped = wrap_presentation_label(
                capabilities[row], presentation_renderer(fig), prototype.get_fontproperties(), 3.0 * fig.dpi
            )
            lines = len(wrapped.splitlines())
            if selected and line_count + lines > 9:
                break
            selected.append((row, wrapped, lines))
            line_count += lines
        prototype.remove()
        ax.text(
            4.25,
            6.1,
            f"Capabilities {offset + 1}–{selected[-1][0] + 1} · tools A–J",
            ha="center",
            va="top",
            fontsize=34,
            fontweight="bold",
        )
        for column in range(len(tools)):
            ax.text(
                3.5 + column * 0.5, 5.33, chr(65 + column), ha="center", va="center", fontsize=34, fontweight="bold"
            )
        top = 5.04
        cmap = plt.get_cmap("RdYlGn")
        for row, wrapped, lines in selected:
            height = max(0.58, 0.47 * lines + 0.1)
            y = top - height / 2
            ax.text(1.65, y, wrapped, ha="center", va="center", fontsize=34, linespacing=1.0)
            for column in range(len(tools)):
                value = float(data[row, column])
                symbol = "✓" if value == 1 else "◐" if value == 0.5 else "—"
                ax.add_patch(
                    Rectangle(
                        (3.25 + column * 0.5, top - height), 0.5, height, facecolor=cmap(value), edgecolor="white"
                    )
                )
                ax.text(
                    3.5 + column * 0.5,
                    y,
                    symbol,
                    ha="center",
                    va="center",
                    fontsize=34,
                    color="#111111" if value == 0.5 else "white",
                )
            top -= height
        ax.text(4.25, 0.25, "✓ full · ◐ partial · — absent", ha="center", va="center", fontsize=34)
        path = output_dir / f"comparative_cells_{offset + 1:02d}_{selected[-1][0] + 1:02d}.png"
        alt = "Full matrix rows; A–J follow the preceding complete tool key: " + "; ".join(
            capabilities[row]
            + ": "
            + ", ".join(f"{chr(65 + column)}={float(data[row, column]):g}" for column in range(len(tools)))
            for row, _, _ in selected
        )
        try:
            panels.append(save_presentation_panel(fig, path, alt))
        finally:
            plt.close(fig)
        offset = selected[-1][0] + 1
    return save_presentation_manifest(output_dir / "comparative_feature_matrix.panels.json", panels)
