"""dashboard.py — Figure 3: Status Dashboard — component validation status."""

from __future__ import annotations

import pathlib
from typing import Any

from ._theme import (
    _MPL_AVAILABLE,
    BG,
    NEUTRAL,
    STATUS_COLORS,
    STATUS_LABELS,
    WHITE,
    _resolve_output,
    _save,
    mpatches,
    plt,
)

__all__ = [
    "generate_status_dashboard",
]


def generate_status_dashboard(
    output_dir: str | pathlib.Path | None = None,
    filename: str = "status_dashboard.png",
    statuses: dict[str, str] | None = None,
    integration_result: Any = None,
) -> pathlib.Path | None:
    """Generate a status dashboard of component validation results."""
    if not _MPL_AVAILABLE:
        return None

    if statuses is None:
        statuses = {
            "Bibliography Fond": "ok",
            "Contacts Fond": "ok",
            "Datasets Fond": "ok",
            "Project Rules": "ok",
            "Manuscript Rules": "ok",
            "Code Executor": "ok",
            "Validator": "ok",
            "Skill": "ok",
        }
    if integration_result is not None and hasattr(integration_result, "statuses"):
        statuses = integration_result.statuses

    dest = _resolve_output(output_dir, filename)
    n = len(statuses)
    fig_height = max(3, n * 0.45)
    fig, ax = plt.subplots(figsize=(9, fig_height), facecolor=BG)
    ax.set_facecolor(WHITE)

    names = list(statuses.keys())
    colors_strip = [STATUS_COLORS.get(s, NEUTRAL) for s in statuses.values()]
    y_pos = range(n)

    bars = ax.barh(
        y_pos,
        [1] * n,
        height=0.65,
        color=colors_strip,
        edgecolor="white",
        linewidth=0.8,
    )
    for bar, name, st in zip(bars, names, statuses.values(), strict=True):
        label = STATUS_LABELS.get(st, st)
        ax.text(
            0.02,
            bar.get_y() + bar.get_height() / 2,
            name,
            va="center",
            fontsize=9,
            fontweight="bold",
            color="white",
        )
        ax.text(
            0.98,
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            ha="right",
            fontsize=8,
            color="white",
            alpha=0.85,
        )

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels([""] * n)
    ax.set_xlim(0, 1)
    ax.set_title(
        "Component Validation Status",
        fontsize=13,
        fontweight="bold",
        color="#0f172a",
        pad=12,
    )
    ax.tick_params(colors=NEUTRAL, labelsize=8)
    ax.spines[:].set_visible(False)
    ax.set_xticks([])

    # Legend
    legend_patches = [
        mpatches.Patch(color=STATUS_COLORS.get(k, NEUTRAL), label=STATUS_LABELS.get(k, k))
        for k in ["ok", "partial", "missing"]
        if k in statuses.values() or k in STATUS_COLORS
    ]
    if legend_patches:
        ax.legend(handles=legend_patches, loc="lower right", framealpha=0.8, fontsize=8)

    fig.tight_layout()
    return _save(fig, dest)
