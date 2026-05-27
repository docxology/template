"""Shared matplotlib figure save helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image


def save_figure_png(
    fig,
    path: Path,
    *,
    dpi: int,
    facecolor: str = "white",
    transparent: bool = False,
    bbox_inches: str = "tight",
    normalize_rgb: bool = True,
) -> Path:
    """Save a figure to PNG and optionally normalize to RGB for PDF pipelines."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        path,
        dpi=dpi,
        bbox_inches=bbox_inches,
        facecolor=facecolor,
        transparent=transparent,
    )
    plt.close(fig)
    if normalize_rgb:
        with Image.open(path) as img:
            img.convert("RGB").save(path)
    return path
