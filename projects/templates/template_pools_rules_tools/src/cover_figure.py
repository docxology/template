"""Deterministic cover-art renderer for the pools/rules/tools exemplar."""

from __future__ import annotations

import logging
import pathlib

logger = logging.getLogger(__name__)

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt

    _MPL_AVAILABLE = True
except ImportError:
    _MPL_AVAILABLE = False

BLUE = "#1e3a8a"
BLUE_LIGHT = "#3b82f6"
TEAL = "#0f766e"
NEUTRAL_LIGHT = "#94a3b8"


def _default_output_dir() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[1] / "manuscript" / "figures"


def generate_cover_art(
    output_dir: str | pathlib.Path | None = None,
    filename: str = "cover_art.png",
) -> pathlib.Path | None:
    """Generate the deterministic title-page illustration."""
    if not _MPL_AVAILABLE:
        return None

    out_dir = pathlib.Path(output_dir) if output_dir is not None else _default_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / filename

    fig, ax = plt.subplots(figsize=(8.5, 11), facecolor="#0f172a")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor("#0f172a")

    for index, (color, label) in enumerate(
        zip((BLUE, TEAL, BLUE_LIGHT), ("FONDS", "RULES", "TOOLS"), strict=True)
    ):
        y0 = 0.06 + index * 0.09
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
