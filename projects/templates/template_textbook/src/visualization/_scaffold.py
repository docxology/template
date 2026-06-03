"""Shared matplotlib scaffold: headless backend, palette, deterministic save."""

from __future__ import annotations

import os

os.environ.setdefault("MPLBACKEND", "Agg")

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from textbook_logging import get_logger

logger = get_logger(__name__)

# Colour-vision-deficiency-aware palette (Wong 2011), kept small and stable.
BLUE = "#0072B2"
ORANGE = "#E69F00"
GREEN = "#009E73"
VERMILLION = "#D55E00"
PURPLE = "#CC79A7"
GRAY = "#999999"
SERIES = (BLUE, ORANGE, GREEN, VERMILLION, PURPLE)

# Fixed DPI for reproducible raster output.
DPI = 150


def new_figure(width: float = 6.0, height: float = 4.0) -> tuple[plt.Figure, plt.Axes]:
    """Return a fresh ``(figure, axes)`` with the template's house style."""
    fig, ax = plt.subplots(figsize=(width, height))
    ax.grid(True, linestyle=":", linewidth=0.6, color=GRAY, alpha=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    return fig, ax


def save_figure(fig: plt.Figure, output_dir: Path, filename: str) -> Path:
    """Save ``fig`` as a PNG under ``output_dir`` and close it. Returns the path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if not filename.endswith(".png"):
        filename = f"{filename}.png"
    out_path = output_dir / filename
    fig.tight_layout()
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    logger.debug("wrote figure %s", out_path)
    return out_path


__all__ = [
    "BLUE",
    "DPI",
    "GRAY",
    "GREEN",
    "ORANGE",
    "PURPLE",
    "SERIES",
    "VERMILLION",
    "new_figure",
    "save_figure",
]
