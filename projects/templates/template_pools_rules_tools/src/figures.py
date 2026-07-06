"""figures.py — Matplotlib-based architecture visualisations for the integration demo.

Public API
----------
generate_architecture_overview(output_dir=None, filename="architecture_overview.png")
generate_resource_counts(output_dir=None, filename="resource_counts.png", counts=None, _data=None)
generate_status_dashboard(
    output_dir=None,
    filename="status_dashboard.png",
    statuses=None,
    integration_result=None,
)
all_figures(output_dir=None, integration_result=None) -> dict[str, Path]
generate_all_figures(...)  -- alias for all_figures

All functions return pathlib.Path (or None if matplotlib unavailable).
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_dir(path: pathlib.Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _default_output_dir() -> pathlib.Path:
    here = pathlib.Path(__file__).resolve().parents[1]
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


# ---------------------------------------------------------------------------
# Figure 1: Architecture Overview — three-panel diagram
# ---------------------------------------------------------------------------


def generate_architecture_overview(
    output_dir: str | pathlib.Path | None = None,
    filename: str = "architecture_overview.png",
) -> pathlib.Path | None:
    """Generate a three-panel figure showing fonds → rules → tools architecture."""
    if not _MPL_AVAILABLE:
        return None

    dest = _resolve_output(output_dir, filename)
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), facecolor=BG)
    panel_titles = (
        "Fonds (Data Pools)",
        "Rules (Specifications)",
        "Tools (Entrypoints)",
    )

    for ax, title, entries, color in zip(
        axes,
        panel_titles,
        [
            [("Bibliography", 8), ("Contacts", 5), ("Datasets", 5)],
            [("Project Rules", 4), ("Manuscript Rules", 4)],
            [("Code Executor", 2), ("Validator", 2), ("Skill", 2)],
        ],
        [BLUE, TEAL, BLUE_LIGHT],
        strict=True,
    ):
        ax.set_facecolor(WHITE)
        ax.set_title(title, fontsize=11, fontweight="bold", color=color, pad=12)
        labels_vals = [e[0] for e in entries]
        widths_vals = [e[1] for e in entries]
        y_pos = range(len(labels_vals))
        bars = ax.barh(
            y_pos,
            widths_vals,
            height=0.55,
            color=color,
            edgecolor="white",
            linewidth=0.5,
        )
        for bar, val in zip(bars, widths_vals, strict=True):
            ax.text(
                bar.get_width() + 0.3,
                bar.get_y() + bar.get_height() / 2,
                str(val),
                va="center",
                fontsize=9,
                color=NEUTRAL,
            )
        ax.set_yticks(list(y_pos))
        ax.set_yticklabels(labels_vals, fontsize=9)
        ax.tick_params(axis="x", colors=NEUTRAL, labelsize=8)
        ax.set_xlim(0, max(widths_vals) * 1.5)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.grid(axis="x", color=GRID, linewidth=0.4)

    fig.text(0.5, -0.02, "Resource Counts by Category", ha="center", fontsize=10, color=NEUTRAL)
    fig.suptitle(
        "Research Resource Architecture: Fonds × Rules × Tools",
        fontsize=14,
        fontweight="bold",
        color="#0f172a",
        y=1.02,
    )
    fig.tight_layout(pad=2)
    return _save(fig, dest)


# ---------------------------------------------------------------------------
# Figure 2: Resource Counts — horizontal bar chart
# ---------------------------------------------------------------------------


def generate_resource_counts(
    output_dir: str | pathlib.Path | None = None,
    filename: str = "resource_counts.png",
    counts: dict[str, int] | None = None,
    _data: Any = None,
) -> pathlib.Path | None:
    """Generate a bar chart of resource counts."""
    if not _MPL_AVAILABLE:
        return None

    if counts is None:
        counts = {"Fonds": 3, "Tools": 3, "Rules": 2}

    dest = _resolve_output(output_dir, filename)
    fig, ax = plt.subplots(figsize=(8, 4), facecolor=BG)
    ax.set_facecolor(WHITE)

    names = list(counts.keys())
    vals = list(counts.values())
    colors_list = [BLUE, TEAL, BLUE_LIGHT, NEUTRAL, TEAL_LIGHT][: len(names)]

    bars = ax.bar(names, vals, color=colors_list, edgecolor="white", linewidth=1.2, width=0.55)
    for bar, val in zip(bars, vals, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.15,
            str(val),
            ha="center",
            fontsize=11,
            fontweight="bold",
            color=NEUTRAL,
        )

    ax.set_ylabel("Count", fontsize=10, color=NEUTRAL)
    ax.set_title(
        "Discovered Resources by Category",
        fontsize=13,
        fontweight="bold",
        color="#0f172a",
        pad=12,
    )
    ax.tick_params(colors=NEUTRAL, labelsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=0.4)
    ax.set_ylim(0, max(max(vals) * 1.4, 1) if vals else 5)
    fig.tight_layout()
    return _save(fig, dest)


# ---------------------------------------------------------------------------
# Figure 3: Status Dashboard — component validation status
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Wrapper
# ---------------------------------------------------------------------------


def all_figures(
    output_dir: str | pathlib.Path | None = None,
    integration_result: Any = None,
) -> dict[str, pathlib.Path | None] | None:
    """Generate all three figures and return a dict of {name: path}.

    Returns None if matplotlib is unavailable.
    """
    if not _MPL_AVAILABLE:
        return None

    if output_dir is not None:
        output_dir = pathlib.Path(output_dir)

    arch = generate_architecture_overview(output_dir=output_dir)
    counts = generate_resource_counts(output_dir=output_dir)
    dash = generate_status_dashboard(output_dir=output_dir, integration_result=integration_result)

    return {
        "architecture_overview": arch,
        "resource_counts": counts,
        "status_dashboard": dash,
    }


generate_all_figures = all_figures  # alias for script use
