"""Intrinsic image fitting shared by native PDF and PPTX content slides."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.utils import ImageReader
from infrastructure.core.exceptions import RenderingError


def fit_slide_figure(path: Path, box: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    """Return an aspect-preserving centered rectangle in bottom-origin points."""
    left, bottom, width, height = box
    image_width, image_height = ImageReader(str(path)).getSize()
    if min(image_width, image_height, width, height) <= 0:
        raise RenderingError("Content figure requires positive intrinsic and destination geometry")
    scale = min(width / image_width, height / image_height)
    fitted_width, fitted_height = image_width * scale, image_height * scale
    return (left + (width - fitted_width) / 2, bottom + (height - fitted_height) / 2, fitted_width, fitted_height)
