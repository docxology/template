"""Configurable matplotlib style for publication figures."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


_DEFAULT_PALETTE: dict[str, str] = {
    "primary": "#111827",
    "secondary": "#2563eb",
    "accent": "#0f766e",
    "grid": "#d4d4d8",
    "muted": "#64748b",
    "reference": "#52525b",
    "pass": "#0f766e",  # nosec B105
    "fail": "#b91c1c",
    "proved": "#dcfce7",
    "sorry": "#fee2e2",
    "panel_bg": "#f8fafc",
    "header_bg": "#e2e8f0",
}

_DEFAULT_TYPOGRAPHY: dict[str, float] = {
    "title": 13.2,
    "subtitle": 11.4,
    "header": 10.8,
    "axis_label": 10.4,
    "tick": 9.6,
    "legend": 9.2,
    "annotation": 9.0,
    "source_note": 8.8,
    "table_cell": 8.6,
    "matrix_label": 7.8,
    "matrix_label_dense": 6.8,
}

_DEFAULT_LAYOUT: dict[str, float] = {
    "grid_line_width": 0.8,
    "matrix_grid_width": 0.35,
    "line_width": 2.0,
    "marker_size": 4.5,
    "card_line_width": 1.0,
}


@dataclass(frozen=True)
class FigureStyleConfig:
    """Data container for FigureStyleConfig."""

    dpi: int = 160
    transparent: bool = False
    font_scale: float = 1.0
    grid: bool = True
    palette: Mapping[str, str] = field(default_factory=lambda: dict(_DEFAULT_PALETTE))
    typography: Mapping[str, float] = field(default_factory=lambda: dict(_DEFAULT_TYPOGRAPHY))
    layout: Mapping[str, float] = field(default_factory=lambda: dict(_DEFAULT_LAYOUT))

    def color(self, role: str, fallback: str = "#111827") -> str:
        """Process color."""
        return str(self.palette.get(role, fallback))

    def text_size(self, role: str, fallback_role: str = "annotation") -> float:
        """Process text size."""
        fallback = float(self.typography.get(fallback_role, _DEFAULT_TYPOGRAPHY[fallback_role]))
        return float(self.typography.get(role, fallback))

    def layout_value(self, role: str, fallback: float) -> float:
        """Process layout value."""
        return float(self.layout.get(role, fallback))

    def rc_params(self) -> dict[str, Any]:
        """Process rc params."""
        base = 10.0 * float(self.font_scale)
        return {
            "font.size": self.text_size("axis_label") if self.typography else base,
            "axes.titlesize": self.text_size("title") if self.typography else base * 1.18,
            "axes.titleweight": "bold",
            "axes.labelsize": self.text_size("axis_label") if self.typography else base,
            "xtick.labelsize": self.text_size("tick") if self.typography else base * 0.9,
            "ytick.labelsize": self.text_size("tick") if self.typography else base * 0.9,
            "legend.fontsize": self.text_size("legend") if self.typography else base * 0.8,
            "figure.titlesize": self.text_size("title") + 1.0 if self.typography else base * 1.28,
            "figure.titleweight": "bold",
        }


DEFAULT_FIGURE_STYLE = FigureStyleConfig()

_active_style: FigureStyleConfig = DEFAULT_FIGURE_STYLE


def active_style() -> FigureStyleConfig:
    """Process active style."""
    return _active_style


def load_figure_style(project_root: Path) -> FigureStyleConfig:
    """Load figure style from a file."""
    path = project_root.resolve() / "figures.yaml"
    if not path.is_file():
        return DEFAULT_FIGURE_STYLE
    try:
        raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(raw, dict):
            return DEFAULT_FIGURE_STYLE

        palette = dict(_DEFAULT_PALETTE)
        if "palette" in raw and isinstance(raw["palette"], dict):
            palette.update({str(key): str(value) for key, value in raw["palette"].items()})

        typography = dict(_DEFAULT_TYPOGRAPHY)
        if "typography" in raw and isinstance(raw["typography"], dict):
            for key, value in raw["typography"].items():
                parsed = _safe_float(value)
                if parsed is None:
                    return DEFAULT_FIGURE_STYLE
                typography[str(key)] = parsed

        layout = dict(_DEFAULT_LAYOUT)
        if "layout" in raw and isinstance(raw["layout"], dict):
            for key, value in raw["layout"].items():
                parsed = _safe_float(value)
                if parsed is None:
                    return DEFAULT_FIGURE_STYLE
                layout[str(key)] = parsed

        dpi = _safe_int(raw.get("dpi", 160))
        font_scale = _safe_float(raw.get("font_scale", 1.0))
        if dpi is None or font_scale is None:
            return DEFAULT_FIGURE_STYLE

        return FigureStyleConfig(
            dpi=dpi,
            transparent=bool(raw.get("transparent", False)),
            font_scale=font_scale,
            grid=bool(raw.get("grid", True)),
            palette=palette,
            typography=typography,
            layout=layout,
        )
    except (OSError, yaml.YAMLError, ValueError, TypeError):
        return DEFAULT_FIGURE_STYLE


@contextlib.contextmanager
def apply_style(config: FigureStyleConfig) -> Iterator[FigureStyleConfig]:
    """Process apply style."""
    global _active_style
    previous = _active_style
    _active_style = config
    import matplotlib.pyplot as plt

    with plt.rc_context(config.rc_params()):
        try:
            yield config
        finally:
            _active_style = previous
