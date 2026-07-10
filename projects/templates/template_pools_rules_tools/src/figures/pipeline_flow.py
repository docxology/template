"""pipeline_flow.py — Figure 8: Pipeline Flow — the three-script orchestration sequence."""

from __future__ import annotations

import pathlib

from ._theme import (
    _MPL_AVAILABLE,
    BG,
    BLUE,
    BLUE_LIGHT,
    NEUTRAL,
    NEUTRAL_LIGHT,
    TEAL,
    TEAL_LIGHT,
    WHITE,
    _resolve_output,
    _save,
    mpatches,
    plt,
)

__all__ = [
    "generate_pipeline_flow",
]


def generate_pipeline_flow(
    output_dir: str | pathlib.Path | None = None,
    filename: str = "pipeline_flow.png",
) -> pathlib.Path | None:
    """Generate a left-to-right flow diagram of the scripts/ orchestration sequence."""
    if not _MPL_AVAILABLE:
        return None

    dest = _resolve_output(output_dir, filename)
    stages = [
        ("01_validate_sources.py", "Validate presence + well-formedness", BLUE_LIGHT),
        ("02_run_integration.py", "run_integration_demo() → JSON summary", TEAL),
        ("03_generate_manuscript.py", "Write manuscript_variables.json", BLUE),
        ("04_validate_strong_rules.py", "Semantic strong-rule evaluation", NEUTRAL_LIGHT),
        ("05_generate_figures.py", "Render 8 figures + cover art", TEAL_LIGHT),
        ("z_generate_manuscript_...py", "Hydrate + inject {{TOKENS}}", BLUE_LIGHT),
        ("PDF render", "4-pass xelatex + bibtex", NEUTRAL),
    ]

    n = len(stages)
    step = 1.85
    box_w = 1.65
    fig, ax = plt.subplots(figsize=(2.0 * n, 3.4), facecolor=BG)
    ax.set_facecolor(WHITE)
    ax.set_xlim(0, n * step)
    ax.set_ylim(0, 2)
    ax.axis("off")

    for i, (name, desc, color) in enumerate(stages):
        cx = step / 2 + i * step
        ax.add_patch(
            mpatches.FancyBboxPatch(
                (cx - box_w / 2, 0.55),
                box_w,
                0.9,
                boxstyle="round,pad=0.06",
                facecolor=color,
                edgecolor="none",
            )
        )
        ax.text(
            cx, 1.15, name, ha="center", va="center", color="white", fontsize=6.6, fontweight="bold"
        )
        ax.text(cx, 0.82, desc, ha="center", va="center", color="white", fontsize=5.8, alpha=0.92)
        if i < n - 1:
            ax.annotate(
                "",
                xy=(cx + step / 2 - 0.05, 1.0),
                xytext=(cx + box_w / 2 + 0.05, 1.0),
                arrowprops={"arrowstyle": "-|>", "color": NEUTRAL, "linewidth": 1.4},
            )

    ax.set_title(
        "Script Pipeline: Six Scripts, Each One Job, Ending in the Combined PDF",
        fontsize=12,
        fontweight="bold",
        color="#0f172a",
        pad=10,
    )
    fig.tight_layout()
    return _save(fig, dest)
