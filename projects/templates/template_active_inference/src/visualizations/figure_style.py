"""Configurable matplotlib style for publication figures."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_PALETTE: dict[str, str] = {
    "primary": "#111827",
    "secondary": "#2563eb",
    "accent": "#0f766e",
    "grid": "#d4d4d8",
    "muted": "#64748b",
    "reference": "#52525b",
    "pass": "#0f766e",
    "fail": "#b91c1c",
    "proved": "#dcfce7",
    "sorry": "#fee2e2",
    "panel_bg": "#f8fafc",
    "header_bg": "#e2e8f0",
}


@dataclass(frozen=True)
class FigureStyleConfig:
    dpi: int = 160
    transparent: bool = False
    font_scale: float = 1.0
    grid: bool = True
    palette: Mapping[str, str] = field(default_factory=lambda: dict(_DEFAULT_PALETTE))

    def color(self, role: str, fallback: str = "#111827") -> str:
        return str(self.palette.get(role, fallback))

    def rc_params(self) -> dict[str, Any]:
        base = 10.0 * float(self.font_scale)
        return {
            "font.size": base,
            "axes.titlesize": base * 1.05,
            "axes.labelsize": base,
            "xtick.labelsize": base * 0.9,
            "ytick.labelsize": base * 0.9,
            "legend.fontsize": base * 0.8,
        }


DEFAULT_FIGURE_STYLE = FigureStyleConfig()

_active_style: FigureStyleConfig = DEFAULT_FIGURE_STYLE


def active_style() -> FigureStyleConfig:
    return _active_style


def load_figure_style(project_root: Path) -> FigureStyleConfig:
    path = project_root.resolve() / "figures.yaml"
    if not path.is_file():
        return DEFAULT_FIGURE_STYLE
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    palette = dict(_DEFAULT_PALETTE)
    palette.update(dict(raw.get("palette") or {}))
    return FigureStyleConfig(
        dpi=int(raw.get("dpi", 160)),
        transparent=bool(raw.get("transparent", False)),
        font_scale=float(raw.get("font_scale", 1.0)),
        grid=bool(raw.get("grid", True)),
        palette=palette,
    )


@contextlib.contextmanager
def apply_style(config: FigureStyleConfig) -> Iterator[FigureStyleConfig]:
    global _active_style
    previous = _active_style
    _active_style = config
    import matplotlib.pyplot as plt

    with plt.rc_context(config.rc_params()):
        try:
            yield config
        finally:
            _active_style = previous
