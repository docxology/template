"""resilience.py — Figure 7: Resilience Layers — three failure modes, three responses."""

from __future__ import annotations

import pathlib

from ._theme import (
    _MPL_AVAILABLE,
    BG,
    BLUE,
    BLUE_LIGHT,
    TEAL,
    WHITE,
    _resolve_output,
    _save,
    mpatches,
    plt,
)

__all__ = [
    "generate_resilience_layers",
]


def generate_resilience_layers(
    output_dir: str | pathlib.Path | None = None,
    filename: str = "resilience_layers.png",
) -> pathlib.Path | None:
    """Generate a three-tier diagram of the integration layer's resilience design."""
    if not _MPL_AVAILABLE:
        return None

    dest = _resolve_output(output_dir, filename)
    layers = [
        (
            "Resource absence",
            "Fond / rule set / tool directory not yet created",
            "Return `None` / empty collection; log warning; continue",
        ),
        (
            "Schema malformation",
            "Manifest present but invalid YAML or missing fields",
            'Catch `yaml.YAMLError`; return degraded `status="partial"`',
        ),
        (
            "Script absence",
            "Tool declares entrypoints that do not exist on disk",
            "`validate_tool_scripts_exist()` reports `missing_scripts`",
        ),
    ]

    row_height = 1.55
    box_height = 1.3
    n = len(layers)
    fig, ax = plt.subplots(figsize=(9.5, 1.9 * n + 0.9), facecolor=BG)
    ax.set_facecolor(WHITE)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, n * row_height + 0.5)
    ax.axis("off")

    colors_list = [BLUE, TEAL, BLUE_LIGHT]
    for i, (title, failure, response) in enumerate(layers):
        y = (n - i - 1) * row_height + 0.5 + box_height / 2
        width = 9.6 - i * 1.2
        x0 = (10 - width) / 2
        ax.add_patch(
            mpatches.FancyBboxPatch(
                (x0, y - box_height / 2),
                width,
                box_height,
                boxstyle="round,pad=0.07",
                facecolor=colors_list[i],
                edgecolor="none",
                alpha=0.92,
            )
        )
        ax.text(
            5,
            y + 0.42,
            f"Level {i + 1}: {title}",
            ha="center",
            va="center",
            color="white",
            fontsize=10,
            fontweight="bold",
        )
        ax.text(
            5, y + 0.06, failure, ha="center", va="center", color="white", fontsize=7.6, alpha=0.9
        )
        ax.text(
            5,
            y - 0.42,
            "→ " + response,
            ha="center",
            va="center",
            color="white",
            fontsize=7.4,
            style="italic",
            alpha=0.85,
        )

    ax.set_title(
        "Three-Level Resilience Design: Fail Informatively, Not Catastrophically",
        fontsize=12,
        fontweight="bold",
        color="#0f172a",
        pad=10,
    )
    fig.tight_layout()
    return _save(fig, dest)
