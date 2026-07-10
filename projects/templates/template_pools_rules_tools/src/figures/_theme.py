"""_theme.py — shared matplotlib guard, brand palette, and output helpers.

All per-figure builder modules import the availability flag, theme colours,
and save/resolve helpers from here so the guard and palette stay single-source.
"""

from __future__ import annotations

import logging
import pathlib
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Matplotlib availability guard
# ---------------------------------------------------------------------------
try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt

    _MPL_AVAILABLE = True
except ImportError:
    mpatches = None  # type: ignore[assignment]
    plt = None  # type: ignore[assignment]
    _MPL_AVAILABLE = False
    logger.warning("figures: matplotlib not available; all figure functions return None")

# ---------------------------------------------------------------------------
# Theme (matches docxology/template brand)
# ---------------------------------------------------------------------------
BLUE = "#1e3a8a"
BLUE_LIGHT = "#3b82f6"
TEAL = "#0f766e"
TEAL_LIGHT = "#14b8a6"
NEUTRAL = "#64748b"
NEUTRAL_LIGHT = "#94a3b8"
WHITE = "#ffffff"
BG = "#f8fafc"
GRID = "#e2e8f0"

STATUS_COLORS: dict[str, str] = {
    "ok": "#16a34a",
    "partial": "#d97706",
    "missing": "#dc2626",
}

STATUS_LABELS: dict[str, str] = {
    "ok": "Pass",
    "partial": "Partial",
    "missing": "Missing",
}

__all__ = [
    "BG",
    "BLUE",
    "BLUE_LIGHT",
    "GRID",
    "NEUTRAL",
    "NEUTRAL_LIGHT",
    "STATUS_COLORS",
    "STATUS_LABELS",
    "TEAL",
    "TEAL_LIGHT",
    "WHITE",
    "_MPL_AVAILABLE",
    "_default_output_dir",
    "_ensure_dir",
    "_resolve_output",
    "_save",
    "logger",
    "mpatches",
    "plt",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_dir(path: pathlib.Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _default_output_dir() -> pathlib.Path:
    # parents[2]: src/figures/_theme.py -> figures/ -> src/ -> project root.
    here = pathlib.Path(__file__).resolve().parents[2]
    return here / "manuscript" / "figures"


def _resolve_output(
    output_dir: str | pathlib.Path | None,
    filename: str,
) -> pathlib.Path:
    if output_dir is None:
        output_dir = _default_output_dir()
    out_dir = pathlib.Path(output_dir)
    _ensure_dir(out_dir)
    return out_dir / filename


def _save(fig: Any, dest: pathlib.Path) -> pathlib.Path:
    fig.savefig(dest, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    logger.info("figures: saved %s", dest)
    return dest
