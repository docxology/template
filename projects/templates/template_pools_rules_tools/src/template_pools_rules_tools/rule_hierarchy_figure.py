"""Rule-hierarchy figure renderer for the pools/rules/tools exemplar."""

from __future__ import annotations

import logging
import pathlib
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt

    _MPL_AVAILABLE = True
except ImportError:
    _MPL_AVAILABLE = False

if TYPE_CHECKING:
    from matplotlib.figure import Figure

BLUE = "#1e3a8a"
TEAL = "#0f766e"
NEUTRAL = "#64748b"
NEUTRAL_LIGHT = "#94a3b8"
BG = "#f8fafc"
WHITE = "#ffffff"
GRID = "#e2e8f0"


def _default_output_dir() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[1] / "manuscript" / "figures"


def _resolve_output(output_dir: str | pathlib.Path | None, filename: str) -> pathlib.Path:
    out_dir = pathlib.Path(output_dir) if output_dir is not None else _default_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / filename


def _save(fig: Figure, dest: pathlib.Path) -> pathlib.Path:
    fig.savefig(dest, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    logger.info("figures: saved %s", dest)
    return dest


def generate_rule_hierarchy(
    output_dir: str | pathlib.Path | None = None,
    filename: str = "rule_hierarchy.png",
) -> pathlib.Path | None:
    """Generate a tree diagram of the two rule sets split into soft/strong branches."""
    if not _MPL_AVAILABLE:
        return None

    dest = _resolve_output(output_dir, filename)
    fig, ax = plt.subplots(figsize=(9, 5.5), facecolor=BG)
    ax.set_facecolor(WHITE)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    root_xy = (5, 5.3)
    ax.add_patch(
        mpatches.FancyBboxPatch(
            (root_xy[0] - 1.4, root_xy[1] - 0.35),
            2.8,
            0.7,
            boxstyle="round,pad=0.08",
            facecolor="#0f172a",
            edgecolor="none",
        )
    )
    ax.text(
        root_xy[0],
        root_xy[1],
        "rules/templates/",
        ha="center",
        va="center",
        color="white",
        fontsize=10,
        fontweight="bold",
    )

    rule_sets = [
        (
            "template_project_rules",
            2.5,
            BLUE,
            ["module-structure.yaml", "coverage-gate.yaml"],
            ["style", "commit-msgs"],
        ),
        (
            "template_manuscript_rules",
            7.5,
            TEAL,
            ["reference-schema.yaml", "section-schema.yaml"],
            ["citation prefs"],
        ),
    ]

    for name, x, color, strong_items, soft_items in rule_sets:
        y = 3.9
        ax.plot([root_xy[0], x], [root_xy[1] - 0.35, y + 0.35], color=GRID, linewidth=1.4, zorder=1)
        ax.add_patch(
            mpatches.FancyBboxPatch(
                (x - 1.5, y - 0.3),
                3.0,
                0.6,
                boxstyle="round,pad=0.06",
                facecolor=color,
                edgecolor="none",
            )
        )
        ax.text(
            x, y, name, ha="center", va="center", color="white", fontsize=8.6, fontweight="bold"
        )

        strong_y = 2.4
        ax.plot([x, x - 1.1], [y - 0.3, strong_y + 0.28], color=GRID, linewidth=1.0, zorder=1)
        ax.add_patch(
            mpatches.FancyBboxPatch(
                (x - 1.1 - 1.15, strong_y - 0.28),
                2.3,
                0.56,
                boxstyle="round,pad=0.05",
                facecolor="white",
                edgecolor=color,
                linewidth=1.2,
            )
        )
        ax.text(
            x - 1.1,
            strong_y,
            "strong/",
            ha="center",
            va="center",
            color=color,
            fontsize=8,
            fontweight="bold",
        )
        for j, item in enumerate(strong_items):
            ax.text(
                x - 1.1,
                strong_y - 0.75 - j * 0.45,
                item,
                ha="center",
                va="center",
                color=NEUTRAL,
                fontsize=7,
            )

        soft_y = 2.4
        ax.plot([x, x + 1.1], [y - 0.3, soft_y + 0.28], color=GRID, linewidth=1.0, zorder=1)
        ax.add_patch(
            mpatches.FancyBboxPatch(
                (x + 1.1 - 1.15, soft_y - 0.28),
                2.3,
                0.56,
                boxstyle="round,pad=0.05",
                facecolor="white",
                edgecolor=NEUTRAL_LIGHT,
                linewidth=1.2,
            )
        )
        ax.text(
            x + 1.1,
            soft_y,
            "soft/",
            ha="center",
            va="center",
            color=NEUTRAL,
            fontsize=8,
            fontweight="bold",
        )
        for j, item in enumerate(soft_items):
            ax.text(
                x + 1.1,
                soft_y - 0.75 - j * 0.45,
                item,
                ha="center",
                va="center",
                color=NEUTRAL,
                fontsize=7,
            )

    ax.set_title(
        "Rule Hierarchy: Two Rule Sets × Soft/Strong Branches",
        fontsize=12,
        fontweight="bold",
        color="#0f172a",
        pad=6,
    )
    fig.tight_layout()
    return _save(fig, dest)
