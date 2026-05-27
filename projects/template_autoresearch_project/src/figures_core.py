"""Shared helpers for AutoResearch figure generation.

Colour, resolution, grid, and save behaviour all resolve from the active
:class:`~src.figure_style.FigureStyleConfig` (see :func:`figure_style.apply_style`).
Figure writers call :func:`save_figure` instead of ``fig.savefig(..., dpi=160)`` and
:func:`styled_grid` instead of an inline ``ax.grid(...)`` so a single style controls
every figure. With the default style these helpers reproduce the historical output
byte-for-byte.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .figure_style import FigureStyleConfig, get_active_style

# Candidate-status roles resolved from the palette; any other status falls back to
# the muted colour (matching the historical default for unknown statuses).
_STATUS_ROLES = ("baseline", "accepted", "rejected", "evaluated", "deferred")
_MUTED_FALLBACK = "#64748b"


def save_figure(fig: Any, path: Path, *, style: FigureStyleConfig | None = None) -> Path:
    """Save ``fig`` to ``path`` using the active style's dpi/transparency, then close it.

    Replaces the historical ``fig.savefig(path, dpi=160); plt.close(fig)`` pattern.
    At the default style this is byte-identical (dpi 160, opaque background).
    """
    from matplotlib import pyplot as plt

    style = style or get_active_style()
    # Pin metadata so PNG bytes are reproducible across machines, dates, and
    # matplotlib versions: by default the Agg writer stamps a version-dependent
    # "Software" chunk and a wall-clock "Creation Time"/"Date", which silently
    # break byte-identity outside a single-machine, single-version window.
    fig.savefig(
        path,
        dpi=style.dpi,
        transparent=style.transparent,
        metadata={"Software": None, "Creation Time": None, "Date": None},
    )
    plt.close(fig)
    return path


def styled_grid(ax: Any, axis: str, *, style: FigureStyleConfig | None = None) -> None:
    """Draw an axis grid using the active style's grid colour, honouring ``grid`` on/off."""
    style = style or get_active_style()
    if not style.grid:
        return
    ax.grid(axis=axis, color=style.color("grid", "#d4d4d8"), linewidth=0.8)


def palette_color(role: str, fallback: str, *, style: FigureStyleConfig | None = None) -> str:
    """Resolve a palette ``role`` from the active style with an explicit fallback."""
    style = style or get_active_style()
    return style.color(role, fallback)


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _first_label_index(labels: np.ndarray, label: int) -> int:
    matches = np.flatnonzero(labels == label)
    if matches.size == 0:
        raise ValueError(f"label is missing from MNIST subset: {label}")
    return int(matches[0])


def _mapping_list(value: object) -> list[dict[str, Any]]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _float_value(value: object) -> float:
    return float(value) if isinstance(value, int | float | str) else 0.0


def _short_candidate_label(value: object) -> str:
    text = str(value)
    if text == "nearest_centroid_baseline":
        return "baseline"
    return text.replace("exp-", "")


def _status_color(status: str) -> str:
    style = get_active_style()
    if status in _STATUS_ROLES:
        return style.color(status, _MUTED_FALLBACK)
    return style.color("muted", _MUTED_FALLBACK)


def _status_marker(status: str) -> str:
    return {"baseline": "s", "accepted": "D"}.get(status, "o")


def _class_balance_count(rows: list[dict[str, Any]], split: str, label: int) -> int:
    for row in rows:
        if row.get("split") == split and int(row.get("class_label", -1)) == label:
            return int(row.get("count", 0))
    return 0
