"""cover.py — Cover Art — deterministic title-page illustration."""

from __future__ import annotations

import pathlib

from ._theme import (
    _MPL_AVAILABLE,
    BLUE,
    BLUE_LIGHT,
    NEUTRAL_LIGHT,
    TEAL,
    _resolve_output,
    logger,
    mpatches,
    plt,
)

__all__ = [
    "generate_cover_art",
]


def generate_cover_art(
    output_dir: str | pathlib.Path | None = None,
    filename: str = "cover_art.png",
) -> pathlib.Path | None:
    """Generate a deterministic cover illustration for the PDF title page.

    Renders the three-layer fonds/rules/tools motif as concentric bands
    behind the paper title, matching the repository's brand palette. Fully
    reproducible from code — no external image-generation dependency.
    """
    if not _MPL_AVAILABLE:
        return None

    dest = _resolve_output(output_dir, filename)
    fig, ax = plt.subplots(figsize=(8.5, 11), facecolor="#0f172a")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor("#0f172a")

    band_colors = [BLUE, TEAL, BLUE_LIGHT]
    band_labels = ["FONDS", "RULES", "TOOLS"]
    for i, (color, label) in enumerate(zip(band_colors, band_labels, strict=True)):
        y0 = 0.06 + i * 0.09
        ax.add_patch(
            mpatches.Rectangle(
                (0.08, y0), 0.84, 0.065, facecolor=color, edgecolor="none", alpha=0.9
            )
        )
        ax.text(
            0.5,
            y0 + 0.0325,
            label,
            ha="center",
            va="center",
            color="white",
            fontsize=13,
            fontweight="bold",
            alpha=0.85,
        )

    ax.plot([0.14, 0.86], [0.42, 0.42], color=NEUTRAL_LIGHT, linewidth=0.8, alpha=0.5)

    ax.text(
        0.5,
        0.62,
        "Pools, Rules,\nand Tools",
        ha="center",
        va="center",
        color="white",
        fontsize=34,
        fontweight="bold",
        linespacing=1.2,
    )
    ax.text(
        0.5,
        0.47,
        "A Template-Integrated Resource Architecture",
        ha="center",
        va="center",
        color=NEUTRAL_LIGHT,
        fontsize=13,
        style="italic",
    )

    ax.text(
        0.5,
        0.03,
        "docxology/template  ·  research template exemplar",
        ha="center",
        va="center",
        color=NEUTRAL_LIGHT,
        fontsize=9,
        alpha=0.8,
    )

    fig.savefig(dest, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    logger.info("figures: saved cover art %s", dest)
    return dest
