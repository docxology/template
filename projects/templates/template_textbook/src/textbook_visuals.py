"""Small image post-processing helpers used by figure + diagram renderers."""

from __future__ import annotations

from pathlib import Path


def pad_png_to_square(path: Path) -> Path:
    """Pad a PNG to a square canvas on a white background, in place.

    A no-op-safe helper: if Pillow is unavailable or the file is missing, the
    original path is returned unchanged so figure generation never hard-fails on
    a cosmetic step.
    """
    path = Path(path)
    if not path.exists():
        return path
    try:  # pragma: no cover - exercised only when Pillow is installed
        from PIL import Image
    except ImportError:
        return path

    with Image.open(path) as img:  # pragma: no cover - optional dependency path
        width, height = img.size
        if width == height:
            return path
        side = max(width, height)
        canvas = Image.new("RGBA", (side, side), (255, 255, 255, 255))
        canvas.paste(img, ((side - width) // 2, (side - height) // 2))
        canvas.convert("RGB").save(path)
    return path
