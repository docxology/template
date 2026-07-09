"""Matplotlib chart-drawing logic for `scripts/16_generate_charts.py`.

Moved out of the script (which grew past the thin-orchestrator line/function
threshold `infrastructure.project.drift.orchestrator` enforces) — the actual
plotting parameters (colors, layout, annotations, thresholds drawn) are this
project's own domain logic, same rationale as `render_orchestration.py`
holding the actual render call sequence instead of the script that invokes it.

Every function takes already-fetched data (never re-derives it from the
filesystem itself) and a `DeckTheme`, so the visual language always matches
the rendered slides. `matplotlib`/`pyplot` are passed in rather than imported
at module scope, matching the lazy-import pattern the calling script already
uses (`matplotlib.use("Agg")` must run before `pyplot` is first imported).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.rendering.slide_deck import DeckTheme


def render_coverage_bar_chart(plt: Any, theme: DeckTheme, rows: list[tuple[str, int, float]], output_path: Path) -> int:
    """Horizontal bar chart of per-exemplar coverage %. Returns the row count."""
    names = [name for name, _, _ in rows]
    coverages = [coverage for _, _, coverage in rows]
    bar_colors = [theme.highlight_1 if cov >= 90.0 else theme.black for cov in coverages]

    fig_height = max(4.0, 0.32 * len(names))
    fig, ax = plt.subplots(figsize=(11, fig_height))
    fig.patch.set_facecolor(theme.white)
    ax.set_facecolor(theme.white)

    y_pos = range(len(names))
    ax.barh(y_pos, coverages, color=bar_colors, edgecolor=theme.black, linewidth=0.6)
    ax.axvline(90.0, color=theme.black, linestyle="--", linewidth=1.0, alpha=0.6)
    ax.text(90.3, len(names) - 0.5, "90% project floor", fontsize=9, color=theme.black, va="top")

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(names, fontsize=8, color=theme.black)
    ax.invert_yaxis()
    ax.set_xlim(0, 105)
    ax.set_xlabel("Measured test coverage (%)", fontsize=10, color=theme.black)
    ax.set_title(
        "Per-exemplar coverage — every public template, measured live",
        fontsize=12,
        color=theme.black,
        loc="left",
    )
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.tick_params(colors=theme.black)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return len(names)


def render_test_count_vs_coverage_scatter(
    plt: Any, theme: DeckTheme, rows: list[tuple[str, int, float]], output_path: Path
) -> int:
    """Scatter of test count vs. coverage %, one point per exemplar. Returns the row count."""
    fig, ax = plt.subplots(figsize=(9, 6.5))
    fig.patch.set_facecolor(theme.white)
    ax.set_facecolor(theme.white)

    for name, test_count, coverage in rows:
        is_this_deck = name == "template_pitch_deck"
        ax.scatter(
            test_count,
            coverage,
            s=140 if is_this_deck else 70,
            color=theme.highlight_1 if is_this_deck else theme.black,
            edgecolor=theme.black,
            linewidth=0.8,
            alpha=1.0 if is_this_deck else 0.55,
            zorder=3 if is_this_deck else 2,
        )
        if is_this_deck:
            ax.annotate(
                name,
                (test_count, coverage),
                textcoords="offset points",
                xytext=(8, -4),
                fontsize=10,
                color=theme.highlight_1,
                fontweight="bold",
            )

    ax.axhline(90.0, color=theme.black, linestyle="--", linewidth=1.0, alpha=0.5)
    ax.set_xlabel("Test count", fontsize=10, color=theme.black)
    ax.set_ylabel("Measured test coverage (%)", fontsize=10, color=theme.black)
    ax.set_title(
        "More tests isn't traded off against coverage — every exemplar, measured live",
        fontsize=12,
        color=theme.black,
        loc="left",
    )
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.tick_params(colors=theme.black)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return len(rows)


def render_infra_subpackage_donut(plt: Any, theme: DeckTheme, rows: list[tuple[str, int]], output_path: Path) -> int:
    """Donut chart of infrastructure/ subpackage sizes. Returns the subpackage row count."""
    top_n = 7
    top_rows = rows[:top_n]
    other_count = sum(count for _, count in rows[top_n:])
    labels = [name for name, _ in top_rows] + (["other subpackages"] if other_count else [])
    values = [count for _, count in top_rows] + ([other_count] if other_count else [])

    palette = [theme.highlight_1, theme.highlight_2, theme.highlight_3, theme.black]
    colors = [palette[i % len(palette)] for i in range(len(values))]
    # Vary opacity across repeats of the same 3-4 base colors so adjacent
    # wedges stay visually distinguishable even in a monochrome theme.
    alphas = [1.0 - 0.15 * (i // len(palette)) for i in range(len(values))]

    fig, ax = plt.subplots(figsize=(8, 8))
    fig.patch.set_facecolor(theme.white)

    wedges, _texts, _autotexts = ax.pie(
        values,
        labels=labels,
        autopct=lambda pct: f"{pct:.0f}%" if pct >= 4 else "",
        pctdistance=0.8,
        colors=colors,
        wedgeprops={"width": 0.42, "edgecolor": theme.white, "linewidth": 2},
        textprops={"color": theme.black, "fontsize": 9},
        startangle=90,
    )
    for wedge, alpha in zip(wedges, alphas, strict=False):
        wedge.set_alpha(alpha)

    total = sum(values)
    ax.set_title(
        f"infrastructure/ — {total} Python files across {len(rows)} importable subpackages",
        fontsize=12,
        color=theme.black,
        loc="left",
    )

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return len(rows)


__all__ = [
    "render_coverage_bar_chart",
    "render_test_count_vs_coverage_scatter",
    "render_infra_subpackage_donut",
]
