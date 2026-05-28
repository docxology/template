"""Publication-quality matplotlib styling for template_code_project figures."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt

VIZ_CONFIG: dict[str, Any] = {
    "colors": {
        "primary": "#0072B2",
        "secondary": "#D55E00",
        "tertiary": "#009E73",
        "quaternary": "#CC79A7",
        "neutral": "#999999",
        "success": "#009E73",
        "warning": "#F0E442",
        "error": "#D55E00",
    },
    "palette": ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#F0E442", "#56B4E9"],
    "fonts": {
        "title": 16,
        "subtitle": 14,
        "axis_label": 14,
        "tick_label": 12,
        "legend": 12,
        "annotation": 11,
    },
    "figure": {
        "dpi": 300,
        "facecolor": "white",
        "figsize_single": (10, 7),
        "figsize_double": (14, 6),
        "figsize_quad": (14, 11),
    },
    "lines": {
        "linewidth": 2.5,
        "markersize": 8,
        "markeredgewidth": 2,
    },
    "grid": {
        "alpha": 0.4,
        "linestyle": "-",
        "linewidth": 0.5,
    },
    "legend": {
        "framealpha": 0.95,
        "edgecolor": "#666666",
        "fancybox": True,
    },
    "markers": ["o", "s", "^", "D", "v", "p"],
}


def apply_visualization_style() -> None:
    """Apply global matplotlib style for publication-quality, accessible figures."""
    plt.rcParams.update(
        {
            "figure.dpi": VIZ_CONFIG["figure"]["dpi"],
            "figure.facecolor": VIZ_CONFIG["figure"]["facecolor"],
            "figure.edgecolor": "none",
            "font.size": VIZ_CONFIG["fonts"]["tick_label"],
            "axes.titlesize": VIZ_CONFIG["fonts"]["title"],
            "axes.labelsize": VIZ_CONFIG["fonts"]["axis_label"],
            "xtick.labelsize": VIZ_CONFIG["fonts"]["tick_label"],
            "ytick.labelsize": VIZ_CONFIG["fonts"]["tick_label"],
            "legend.fontsize": VIZ_CONFIG["fonts"]["legend"],
            "axes.titleweight": "bold",
            "axes.labelweight": "medium",
            "lines.linewidth": VIZ_CONFIG["lines"]["linewidth"],
            "lines.markersize": VIZ_CONFIG["lines"]["markersize"],
            "axes.grid": True,
            "grid.alpha": VIZ_CONFIG["grid"]["alpha"],
            "grid.linestyle": VIZ_CONFIG["grid"]["linestyle"],
            "grid.linewidth": VIZ_CONFIG["grid"]["linewidth"],
            "legend.framealpha": VIZ_CONFIG["legend"]["framealpha"],
            "legend.edgecolor": VIZ_CONFIG["legend"]["edgecolor"],
            "legend.fancybox": VIZ_CONFIG["legend"]["fancybox"],
            "axes.spines.top": False,
            "axes.spines.right": False,
            "savefig.dpi": VIZ_CONFIG["figure"]["dpi"],
            "savefig.bbox": "tight",
            "savefig.facecolor": VIZ_CONFIG["figure"]["facecolor"],
            "savefig.edgecolor": "none",
        }
    )


def agency_category(alpha: float) -> tuple[str, str]:
    """Classify step size α into agency category for H=I quadratic."""
    if alpha < 0.3:
        return "Conservative", "#2196F3"
    if alpha <= 1.0:
        return "Near-optimal", "#4CAF50"
    if alpha < 2.0:
        return "Aggressive", "#FF9800"
    return "Divergent", "#F44336"


__all__ = ["VIZ_CONFIG", "agency_category", "apply_visualization_style"]
