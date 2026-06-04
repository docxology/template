"""Shared matplotlib figure save helpers."""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

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
    raw_path = path
    if normalize_rgb:
        with NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.stem}.",
            suffix=path.suffix,
            delete=False,
        ) as tmp:
            raw_path = Path(tmp.name)
    fig.savefig(
        raw_path,
        dpi=dpi,
        bbox_inches=bbox_inches,
        facecolor=facecolor,
        transparent=transparent,
    )
    plt.close(fig)
    if normalize_rgb:
        try:
            with Image.open(raw_path) as img:
                rgb = img.convert("RGB")
                rgb.save(path, format="PNG")
        finally:
            raw_path.unlink(missing_ok=True)
    return path
