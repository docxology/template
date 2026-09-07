"""Compact publication-pairing diagram for transmission bookends."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from PIL import Image, ImageDraw, ImageFont

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

_STEPS = ("Render", "Zenodo", "GitHub", "Re-render")
_WIDTH = 525
_HEIGHT = 300


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Return a portable bitmap font for the compact diagram."""
    try:
        return ImageFont.truetype("Arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _centered_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    *,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str = "#0f172a",
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    draw.text((xy[0] - width / 2, xy[1] - height / 2), text, font=font, fill=fill)


def _draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int]) -> None:
    draw.line([start, end], fill="#334155", width=3)
    x, y = end
    draw.polygon([(x, y), (x - 10, y - 6), (x - 10, y + 6)], fill="#334155")


def write_transmission_diagram(output_path: Path, *, current: Mapping[str, str | None]) -> Path:
    """Write a compact PNG flow diagram for the release pairing pipeline."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doi = str(current.get("doi") or "pending")
    pdf_hash = str(current.get("pdf_sha256") or "pending")
    hash_label = pdf_hash[:12] + "..." if len(pdf_hash) > 12 else pdf_hash

    image = Image.new("RGB", (_WIDTH, _HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    title_font = _font(18)
    label_font = _font(16)
    small_font = _font(13)

    x_positions = [70, 200, 330, 455]
    y_center = 125
    box_w = 98
    box_h = 62
    for index, (label, x_pos) in enumerate(zip(_STEPS, x_positions, strict=True)):
        left = x_pos - box_w // 2
        top = y_center - box_h // 2
        right = x_pos + box_w // 2
        bottom = y_center + box_h // 2
        draw.rounded_rectangle(
            [left, top, right, bottom],
            radius=10,
            outline="#1e3a8a",
            width=2,
            fill="#e0e7ff",
        )
        _centered_text(draw, (x_pos, y_center), label, font=label_font)
        if index < len(_STEPS) - 1:
            _draw_arrow(draw, (right + 6, y_center), (x_positions[index + 1] - box_w // 2 - 8, y_center))

    _centered_text(draw, (_WIDTH / 2, 38), "Publication Pairing", font=title_font)
    _centered_text(draw, (_WIDTH / 2, 226), f"DOI: {doi}", font=small_font)
    _centered_text(draw, (_WIDTH / 2, 254), f"PDF SHA-256: {hash_label}", font=small_font)

    image.save(output_path, format="PNG")
    logger.info("Wrote transmission pairing diagram: %s", output_path)
    return output_path
