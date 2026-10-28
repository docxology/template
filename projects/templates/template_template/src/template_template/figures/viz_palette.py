"""Shared palette and drawing helpers for architecture figures."""

from __future__ import annotations

import hashlib
import json
from math import ceil
from pathlib import Path
from typing import Any

import matplotlib.colors as mcolors
from matplotlib.backend_bases import RendererBase
from matplotlib.backends.backend_agg import FigureCanvasAgg, RendererAgg
from matplotlib.font_manager import FontProperties
from matplotlib.figure import Figure
from matplotlib.text import Text
from PIL import Image

from ..core.introspection import ModuleInfo, PipelineStage

ARCH_VIZ_COLORS = {
    "infra": "#0072B2",
    "infra_dark": "#004F7F",
    "project": "#D55E00",
    "project_dark": "#A34500",
    "pipeline": "#009E73",
    "accent": "#CC79A7",
    "neutral": "#666666",
    "bg_infra": "#ddeeff",
    "bg_project": "#fff0e0",
    "bg_pipeline": "#e8f5e9",
    "white": "#ffffff",
    "text_dark": "#1a1a1a",
    "text_light": "#555555",
    "shadow": "#cccccc",
    "divider": "#bbbbbb",
}

# Publication-policy constants live here so figures, tests, and manuscript
# metrics all read the same values.  Keeping the render resolution beside the
# palette also removes four independent ``dpi=...`` literals from the figure
# builders.
FONT_FLOOR = 16
FIGURE_DPI = 200

_TAG_COLORS = {
    "core": ARCH_VIZ_COLORS["pipeline"],
    "llm": ARCH_VIZ_COLORS["accent"],
    "bundle": "#E69F00",
    "archival": "#56B4E9",
    "clean": ARCH_VIZ_COLORS["neutral"],
    "tests": "#0072B2",
}


def stage_color(stage: PipelineStage) -> tuple[float, float, float, float]:
    """Pick a fill colour from the first recognised stage tag."""
    for tag in stage.tags:
        if tag in _TAG_COLORS:
            return mcolors.to_rgba(_TAG_COLORS[tag])
    return mcolors.to_rgba(ARCH_VIZ_COLORS["pipeline"])


def short_stage_label(name: str) -> str:
    """Compact label for pipeline boxes."""
    overrides = {
        "Clean Output Directories": "Clean",
        "Environment Setup": "Setup",
        "Infrastructure Tests": "Infra Tests",
        "Project Tests": "Proj Tests",
        "Project Analysis": "Analysis",
        "PDF Rendering": "Render PDF",
        "Output Validation": "Validate",
        "LLM Scientific Review": "LLM Review",
        "LLM Translations": "LLM Trans",
        "Copy Outputs": "Copy Out",
        "Executable Bundle": "Bundle",
        "Archival Publication": "Archive",
    }
    return overrides.get(name, name)


def doc_badge(module: ModuleInfo) -> str:
    """Build a compact 4-letter doc-coverage badge for *module*."""
    parts = [
        "A" if module.has_agents_md else "·",
        "R" if module.has_readme_md else "·",
        "S" if module.has_skill_md else "·",
        "P" if module.has_pai_md else "·",
    ]
    return "".join(parts)


def presentation_renderer(fig: Figure) -> RendererAgg:
    """Select the actual headless raster canvas and return its typed renderer."""
    canvas = fig.canvas
    if not isinstance(canvas, FigureCanvasAgg):
        canvas = FigureCanvasAgg(fig)
    renderer = canvas.get_renderer()
    if not isinstance(renderer, RendererAgg):
        raise TypeError("The presentation canvas did not return its actual Agg renderer")
    return renderer


def save_presentation_panel(fig: Figure, path: Path, alt: str) -> dict[str, object]:
    """Save a panel with conservative measurements from its actual raster draw.

    Never infer the manifest's minimum from a requested fontsize alone. Measure
    every visible text artist at the exact saved DPI, cap its extent by its
    actual font pixel height, and retain the complete measurement evidence.
    """
    fig.set_dpi(FIGURE_DPI)
    presentation_renderer(fig)
    fig.canvas.draw()
    renderer = presentation_renderer(fig)
    canvas = fig.bbox
    measurements: list[dict[str, Any]] = []
    for text in fig.findobj(match=Text):
        if not text.get_visible() or not text.get_text().strip():
            continue
        box = text.get_window_extent(renderer)
        if not (canvas.contains(box.x0, box.y0) and canvas.contains(box.x1, box.y1)):
            raise ValueError(f"Presentation text leaves its raster: {text.get_text()!r}")
        measurements.append(
            {
                "text": text.get_text(),
                "bbox_px": [round(value, 6) for value in (box.x0, box.y0, box.x1, box.y1)],
                "font_pixels": float(text.get_fontsize()) * float(fig.dpi) / 72,
                "minimum_label_px": min(float(box.height), float(text.get_fontsize()) * float(fig.dpi) / 72),
            }
        )
    if not measurements:
        raise ValueError("A presentation panel must have measured visible labels")
    for index, first in enumerate(measurements):
        a = first["bbox_px"]
        for second in measurements[index + 1 :]:
            b = second["bbox_px"]
            if max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3]):
                raise ValueError(f"Presentation labels overlap: {first['text']!r}, {second['text']!r}")
    fig.savefig(path, dpi=FIGURE_DPI, facecolor="white")
    with Image.open(path) as raster:
        width, height = raster.size
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    minimum = min(row["minimum_label_px"] for row in measurements)
    evidence = {
        "schema_version": "1.0",
        "png_sha256": digest,
        "width_px": width,
        "height_px": height,
        "dpi": FIGURE_DPI,
        "minimum_label_px": minimum,
        "text_measurements": measurements,
    }
    path.with_suffix(".labels.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return {"src": "../output/figures/" + path.name, "alt": alt, "sha256": digest, "minimum_label_px": minimum}


def save_presentation_manifest(path: Path, panels: list[dict[str, object]]) -> Path:
    """Write the existing Source slide-manifest schema in intentional order."""
    if not panels:
        raise ValueError("A presentation manifest requires at least one panel")
    path.write_text(json.dumps({"schema_version": "1.0", "panels": panels}, indent=2) + "\n", encoding="utf-8")
    return path


def wrap_presentation_label(text: str, renderer: RendererBase, font: FontProperties, maximum_width_px: float) -> str:
    """Wrap full identifiers by actual glyph widths; preserve every character.

    Long unspaced identifiers use balanced physical-line chunks. Line wrapping
    adds only whitespace; the original spelling remains in the panel alt text.
    """
    lines = []
    current = ""

    def width(value: str) -> float:
        return float(renderer.get_text_width_height_descent(value, font, False)[0])

    for word in text.split():
        if width(word) > maximum_width_px:
            if current:
                lines.append(current)
                current = ""
            count = max(2, ceil(width(word) / maximum_width_px))
            while True:
                length = ceil(len(word) / count)
                parts = [word[index : index + length] for index in range(0, len(word), length)]
                if all(width(part) <= maximum_width_px for part in parts):
                    break
                count += 1
                if count > len(word):
                    raise ValueError("A presentation glyph exceeds the full card width")
            lines.extend(parts[:-1])
            current = parts[-1]
        elif current and width(current + " " + word) > maximum_width_px:
            lines.append(current)
            current = word
        else:
            current = (current + " " + word).strip()
    if current:
        lines.append(current)
    return "\n".join(lines)
