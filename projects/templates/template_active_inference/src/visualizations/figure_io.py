"""Shared matplotlib figure save helpers."""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import matplotlib.pyplot as plt
from PIL import Image


def _normalize_rgb_extrema(raw: Any) -> tuple[tuple[int, int], ...]:
    if not raw:
        return ()
    if isinstance(raw[0], tuple):
        return tuple((int(low), int(high)) for low, high in raw)
    low, high = raw
    return ((int(low), int(high)),)


def image_render_metrics(path: Path) -> dict[str, object]:
    """Return deterministic live PNG metrics used by render validators."""
    if not path.is_file():
        return {
            "exists": False,
            "width_px": 0,
            "height_px": 0,
            "mode": "",
            "size_bytes": 0,
            "aspect_ratio": 0.0,
            "nonblank": False,
        }
    channels: tuple[tuple[int, int], ...] = ()
    try:
        with Image.open(path) as image:
            width, height = image.size
            mode = image.mode
            channels = _normalize_rgb_extrema(image.convert("RGB").getextrema())
    except (OSError, ValueError, EOFError, SyntaxError):
        width, height, mode = 0, 0, ""
    aspect_ratio = float(width / height) if height else 0.0
    nonblank = any(low != high for low, high in channels)
    return {
        "exists": path.is_file(),
        "width_px": int(width),
        "height_px": int(height),
        "mode": mode,
        "size_bytes": path.stat().st_size if path.is_file() else 0,
        "aspect_ratio": aspect_ratio,
        "nonblank": nonblank,
    }


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
