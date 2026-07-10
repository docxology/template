"""taxonomy.py — Figure 4: Fond Taxonomy — schema comparison across the three fond types."""

from __future__ import annotations

import pathlib

from ._theme import (
    _MPL_AVAILABLE,
    BG,
    BLUE,
    BLUE_LIGHT,
    GRID,
    NEUTRAL,
    STATUS_COLORS,
    TEAL,
    WHITE,
    _resolve_output,
    _save,
    plt,
)

__all__ = [
    "generate_fond_taxonomy",
]


def generate_fond_taxonomy(
    output_dir: str | pathlib.Path | None = None,
    filename: str = "fond_taxonomy.png",
) -> pathlib.Path | None:
    """Generate a schema-comparison matrix across the three fond types."""
    if not _MPL_AVAILABLE:
        return None

    dest = _resolve_output(output_dir, filename)

    fonds = ["Bibliography", "Contacts", "Datasets"]
    fields: list[tuple[str, list[object]]] = [
        ("Manifest (`fonds.yaml`)", [True, True, True]),
        ("Required `type` field", [True, True, True]),
        ("Primary key", [True, True, True]),
        ("Source-of-truth format", ["BibTeX", "YAML", "YAML"]),
        ("Secondary mirror", ["CSV", "JSON", "—"]),
        ("Dedup key", ["cite key", "`id`", "`id`"]),
        ("Binary data committed", [False, False, False]),
    ]

    fig, ax = plt.subplots(figsize=(9, 0.62 * (len(fields) + 1) + 1), facecolor=BG)
    ax.set_facecolor(WHITE)
    ax.set_xlim(0, len(fonds) + 1.6)
    ax.set_ylim(0, len(fields) + 1)
    ax.axis("off")

    ax.text(
        0.05,
        len(fields) + 0.5,
        "Field",
        fontsize=10,
        fontweight="bold",
        color="#0f172a",
        va="center",
    )
    for i, name in enumerate(fonds):
        ax.text(
            1.6 + i + 0.5,
            len(fields) + 0.5,
            name,
            fontsize=10,
            fontweight="bold",
            color=[BLUE, TEAL, BLUE_LIGHT][i],
            va="center",
            ha="center",
        )
    ax.plot(
        [0, len(fonds) + 1.6], [len(fields) + 0.05, len(fields) + 0.05], color=GRID, linewidth=1.2
    )

    for row, (label, values) in enumerate(reversed(fields)):
        y = row + 0.5
        ax.text(0.05, y, label, fontsize=9, color="#0f172a", va="center")
        for i, val in enumerate(values):
            cx = 1.6 + i + 0.5
            if isinstance(val, bool):
                color = STATUS_COLORS["ok"] if val else STATUS_COLORS["missing"]
                marker = "✓" if val else "–"
                ax.text(
                    cx,
                    y,
                    marker,
                    fontsize=11,
                    fontweight="bold",
                    color=color,
                    va="center",
                    ha="center",
                )
            else:
                ax.text(cx, y, str(val), fontsize=8.5, color=NEUTRAL, va="center", ha="center")
        if row < len(fields) - 1:
            ax.plot([0, len(fonds) + 1.6], [y - 0.5, y - 0.5], color=GRID, linewidth=0.5)

    ax.set_title(
        "Fond Schema Taxonomy: Bibliography × Contacts × Datasets",
        fontsize=12,
        fontweight="bold",
        color="#0f172a",
        pad=10,
    )
    fig.tight_layout()
    return _save(fig, dest)
