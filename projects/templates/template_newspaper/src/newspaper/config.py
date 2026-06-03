"""Typed, strict access to the newspaper render configuration.

Render knobs live in the ``render:`` block of ``content/edition.yaml`` so an
edition's *content* and its *production settings* travel together. The loader is
**strict**: an unknown key under ``render`` raises ``ValueError`` quoting both
the offending key and the allowed set. This is the same single-source-of-truth
validator contract the sibling ``template_prose_project`` uses, and the tests
assert on substrings of these messages.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .geometry import INCH, PageGeometry

_KNOWN_RENDER_KEYS: frozenset[str] = frozenset(
    {
        "output_basename",
        "page",
        "columns_default",
        "gutter_inches",
        "rail_inches",
        "figures_dir",
        "draft_grid",
        "spot_color",
        "spot_hex",
    }
)

#: Supported trim sizes, in inches (width, height). Tabloid is the default
#: large-format community-newspaper trim.
_PAGE_SIZES: dict[str, tuple[float, float]] = {
    "tabloid": (11.0, 17.0),
    "broadsheet": (12.0, 22.5),
    "berliner": (12.4, 18.5),
    "letter": (8.5, 11.0),
}


@dataclass(frozen=True)
class NewspaperConfig:
    """Production settings for one render."""

    output_basename: str = "the-triplicate"
    page: str = "tabloid"
    columns_default: int = 5
    gutter_inches: float = 0.16
    rail_inches: float = 1.55
    figures_dir: str = "output/figures"
    draft_grid: bool = False
    spot_color: bool = False
    spot_hex: str = "#9E1B32"  # classic newspaper-flag red; used when spot_color is on

    def __post_init__(self) -> None:
        if self.page not in _PAGE_SIZES:
            raise ValueError(f"unknown page size {self.page!r}; allowed: {sorted(_PAGE_SIZES)}")
        if self.columns_default < 1:
            raise ValueError(f"columns_default must be >= 1, got {self.columns_default}")
        if self.gutter_inches < 0:
            raise ValueError(f"gutter_inches must be >= 0, got {self.gutter_inches}")
        if self.rail_inches <= 0:
            raise ValueError(f"rail_inches must be > 0, got {self.rail_inches}")
        if not self.output_basename:
            raise ValueError("output_basename must be non-empty")

    def geometry(self) -> PageGeometry:
        """Build the :class:`PageGeometry` for the configured trim size."""
        w_in, h_in = _PAGE_SIZES[self.page]
        return PageGeometry(width=w_in * INCH, height=h_in * INCH)

    @property
    def gutter_points(self) -> float:
        return self.gutter_inches * INCH

    @property
    def rail_points(self) -> float:
        return self.rail_inches * INCH

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NewspaperConfig":
        render = data.get("render") or {}
        if not isinstance(render, dict):
            raise ValueError("'render' section must be a mapping")
        unknown = sorted(set(render) - _KNOWN_RENDER_KEYS)
        if unknown:
            raise ValueError(f"Unknown render key(s) in config: {unknown}. Allowed: {sorted(_KNOWN_RENDER_KEYS)}")
        return cls(
            output_basename=str(render.get("output_basename", "the-triplicate")),
            page=str(render.get("page", "tabloid")),
            columns_default=int(render.get("columns_default", 5)),
            gutter_inches=float(render.get("gutter_inches", 0.16)),
            rail_inches=float(render.get("rail_inches", 1.55)),
            figures_dir=str(render.get("figures_dir", "output/figures")),
            draft_grid=bool(render.get("draft_grid", False)),
            spot_color=bool(render.get("spot_color", False)),
            spot_hex=str(render.get("spot_hex", "#9E1B32")),
        )

    def spot(self) -> object | None:
        """The spot Color when ``spot_color`` is enabled, else ``None``."""
        if not self.spot_color:
            return None
        from reportlab.lib.colors import HexColor

        try:
            color: object = HexColor(self.spot_hex)
            return color
        except Exception:
            return None


def load_newspaper_config(content_dir: Path | str) -> NewspaperConfig:
    """Load :class:`NewspaperConfig` from ``content/edition.yaml``'s render block."""
    path = Path(content_dir) / "edition.yaml"
    if not path.exists():
        raise FileNotFoundError(f"edition manifest not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a YAML mapping at the top level")
    return NewspaperConfig.from_dict(data)


__all__ = ["NewspaperConfig", "load_newspaper_config"]
