"""Chart renderers for the gold-refinement figures.

Houses the bar/line/heatmap chart generators driven by refinery purity and
token-plan data: the purity progression chart, the karat grading chart, and the
token density chart. Each generator writes a deterministic PNG + SVG pair via
the shared :mod:`._common` IO helpers.

All figures are deterministic (fixed seeds, no RNG) and headless-safe
(MPLBACKEND=Agg set in tests and pipeline).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from ._common import (
    STAGE_COLORS,
    STAGE_LABELS,
    _ensure_output_dir,
    _save_figure,
    _style_axes,
    purity_nines_values,
)

try:
    from ..composition import generate_token_plan
    from ..config import load_gold_refinement_config
    from ..purity import KARAT_GRADES, NINE_NINES_PURITY, format_purity
    from ..refinery import run_refinery
except ImportError:  # pragma: no cover - flat-layout fallback
    from composition import generate_token_plan  # type: ignore[no-redef]
    from config import load_gold_refinement_config  # type: ignore[no-redef]
    from purity import KARAT_GRADES, NINE_NINES_PURITY, format_purity  # type: ignore[no-redef]
    from refinery import run_refinery  # type: ignore[no-redef]


def generate_purity_progression(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    """Generate a line+bar chart showing purity progression across refinery stages.

    The x-axis is stage order, the y-axis is purity fraction. A line shows
    the purity sequence (input→output per stage) and bars show the per-stage
    purity gain. The nine-nines threshold is marked.
    """
    if output_dir is None:
        if project_root is not None:
            output_dir = project_root / "output" / "figures"
        else:
            output_dir = Path("output") / "figures"
    _ensure_output_dir(output_dir)

    result = run_refinery()
    purity_seq = list(result.purity_sequence)
    stage_names = [STAGE_LABELS[i] for i in range(len(result.stages))]
    gains = [result.stages[i].output_purity - result.stages[i].input_purity for i in range(len(result.stages))]

    fig = plt.figure(figsize=(11, 7.5))
    grid = fig.add_gridspec(2, 1, height_ratios=(3.2, 1.2), hspace=0.24)
    ax1 = fig.add_subplot(grid[0])
    ax3 = fig.add_subplot(grid[1])

    x_positions = np.arange(len(result.stages))
    bar_width = 0.6
    ax1.bar(
        x_positions,
        gains,
        bar_width,
        color=STAGE_COLORS[: len(result.stages)],
        alpha=0.7,
        label="Purity gain per stage",
    )
    ax1.set_xlabel("Refinery Stage", fontsize=12)
    ax1.set_ylabel("Purity Gain (fraction)", fontsize=12, color="#333333")
    ax1.set_xticks(x_positions)
    ax1.set_xticklabels(stage_names, rotation=15, ha="right")
    ax1.tick_params(axis="y", labelcolor="#333333")
    _style_axes(ax1)

    ax2 = ax1.twinx()
    line_x = np.arange(len(purity_seq))
    ax2.plot(
        line_x,
        purity_seq,
        "ko-",
        linewidth=2,
        markersize=8,
        label="Purity sequence",
    )
    ax2.set_ylabel("Cumulative Purity (fraction)", fontsize=12, color="#333333")
    ax2.set_ylim(-0.05, 1.15)
    ax2.axhline(y=0.999999999, color="r", linestyle="--", alpha=0.5, label="Nine-nines (99.9999999%)")
    ax2.axhline(y=0.999, color="orange", linestyle="--", alpha=0.3, label="24K (99.9%)")

    ax2.annotate(
        f"{format_purity(result.final_purity)}",
        xy=(len(purity_seq) - 1, result.final_purity),
        xytext=(len(purity_seq) - 1.5, result.final_purity + 0.05),
        fontsize=9,
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color="black"),
    )

    ax1.set_title("Gold Refinery: Purity Progression from Ore to Nine-Nines", fontsize=14)
    fig.legend(loc="upper left", bbox_to_anchor=(0.12, 0.95), fontsize=9)

    nines = purity_nines_values(tuple(purity_seq))
    ax3.plot(line_x, nines, color="#7f1d1d", marker="o", linewidth=2.0)
    ax3.fill_between(line_x, nines, color="#fecaca", alpha=0.45)
    ax3.set_xticks(line_x)
    ax3.set_xticklabels(["Input", *stage_names], rotation=15, ha="right")
    ax3.set_ylabel("Nines gained\n$-\\log_{10}(1-p)$", fontsize=10)
    ax3.set_xlabel("Refinery trajectory")
    ax3.set_title("Late-stage purity is visible on a nines transform", fontsize=11)
    for x, score in zip(line_x, nines):
        ax3.text(float(x), score + 0.08, f"{score:.1f}", ha="center", va="bottom", fontsize=8)
    _style_axes(ax3)

    out_path = output_dir / "purity_progression.png"
    return _save_figure(fig, out_path)


def generate_karat_grading_chart(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    """Generate a horizontal bar chart mapping karat grades to purity fractions.

    Shows all standard karat grades (9K–24K) plus the nine-nines threshold,
    with the refinery stages overlaid as markers.
    """
    if output_dir is None:
        if project_root is not None:
            output_dir = project_root / "output" / "figures"
        else:
            output_dir = Path("output") / "figures"
    _ensure_output_dir(output_dir)

    result = run_refinery()

    grades = sorted(KARAT_GRADES.items())
    grade_labels = [f"{k}K" for k, _ in grades] + ["9N"]
    grade_purities = [v for _, v in grades] + [NINE_NINES_PURITY]

    fig, ax = plt.subplots(figsize=(11, 6.2))

    y_positions = np.arange(len(grade_labels))
    bar_colors = plt.colormaps["YlOrBr"](np.linspace(0.3, 0.95, len(grade_labels)))

    ax.barh(y_positions, grade_purities, color=bar_colors, alpha=0.84, height=0.56)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(grade_labels)
    ax.set_xlabel("Purity Fraction", fontsize=12)
    ax.set_title("Gold Karat Grading Scale with Refinery Stages", fontsize=14)
    ax.set_xlim(0, 1.1)
    ax.axvspan(0.999, 1.0, color="#fde68a", alpha=0.26, label="24K band")
    ax.axvline(NINE_NINES_PURITY, color="#991b1b", linestyle="--", linewidth=1.4, label="Nine-nines")

    for i, purity in enumerate(grade_purities):
        ax.text(purity + 0.01, i, format_purity(purity), va="center", fontsize=8)

    for i, stage in enumerate(result.stages):
        target_purity = stage.output_purity
        closest_y = min(y_positions, key=lambda y: abs(grade_purities[y] - target_purity))
        ax.scatter(
            target_purity,
            closest_y + 0.35,
            color=STAGE_COLORS[i],
            s=100,
            zorder=5,
            marker="D",
            edgecolors="black",
            linewidths=0.5,
        )
        ax.annotate(
            stage.name,
            xy=(target_purity, closest_y + 0.35),
            xytext=(min(1.03, target_purity + 0.035), closest_y + 0.35),
            fontsize=8,
            fontstyle="italic",
        )

    ax.legend(loc="lower right", fontsize=8)
    _style_axes(ax, grid_axis="x")
    out_path = output_dir / "karat_grading.png"
    return _save_figure(fig, out_path)


def generate_token_density_chart(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
    token_plan_data: dict[str, Any] | None = None,
) -> Path:
    """Generate a bar chart showing token counts per section and per category.

    Reads token_plan.json if available, otherwise generates the plan.
    """
    if output_dir is None:
        if project_root is not None:
            output_dir = project_root / "output" / "figures"
        else:
            output_dir = Path("output") / "figures"
    _ensure_output_dir(output_dir)

    # Load token plan data
    if token_plan_data is None:
        plan_path = output_dir.parent / "reports" / "token_plan.json"
        if plan_path.exists():
            with plan_path.open("r") as f:
                token_plan_data = json.load(f)
        else:
            cfg = load_gold_refinement_config(project_root) if project_root else load_gold_refinement_config()
            plan = generate_token_plan(cfg)
            token_plan_data = {
                "section_counts": plan.section_counts,
                "category_counts": plan.category_counts,
            }

    section_counts: dict[str, int] = token_plan_data.get("section_counts", {}) if token_plan_data else {}
    category_counts: dict[str, int] = token_plan_data.get("category_counts", {}) if token_plan_data else {}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.4))

    if section_counts:
        section_items = sorted(section_counts.items(), key=lambda item: (-item[1], item[0]))
        sections = [item[0] for item in section_items]
        counts = [item[1] for item in section_items]
        total = sum(counts)
        ax1.bar(sections, counts, color="#1e3a8a", alpha=0.82)
        ax1.set_title("Tokens per Manuscript Section", fontsize=12)
        ax1.set_xlabel("Section")
        ax1.set_ylabel("Token Count")
        ax1.tick_params(axis="x", rotation=30)
        for i, c in enumerate(counts):
            pct = 100 * c / total if total else 0
            ax1.text(i, c + 0.1, f"{c}\n{pct:.0f}%", ha="center", fontsize=8)
        ax1.text(0.98, 0.95, f"Total: {total}", transform=ax1.transAxes, ha="right", va="top", fontsize=9)
        _style_axes(ax1)

    if category_counts:
        category_items = sorted(category_counts.items(), key=lambda item: (item[1], item[0]))
        categories = [item[0] for item in category_items]
        counts = [item[1] for item in category_items]
        total = sum(counts)
        ax2.barh(categories, counts, color="#0f766e", alpha=0.8)
        ax2.set_title("Tokens per Lexicon Category", fontsize=12)
        ax2.set_xlabel("Token Count")
        ax2.set_ylabel("Category")
        for i, c in enumerate(counts):
            pct = 100 * c / total if total else 0
            ax2.text(c + 0.1, i, f"{c} ({pct:.0f}%)", va="center", fontsize=8)
        ax2.text(0.98, 0.04, f"Total: {total}", transform=ax2.transAxes, ha="right", va="bottom", fontsize=9)
        _style_axes(ax2, grid_axis="x")

    fig.suptitle("Mega-Madlib Token Distribution", fontsize=14, y=1.02)
    out_path = output_dir / "token_density.png"
    return _save_figure(fig, out_path)
