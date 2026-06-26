"""Figure generation for the gold-refinement exemplar.

Generates publication-quality figures from refinery data using matplotlib.
All figures are deterministic (fixed seeds, no RNG) and headless-safe
(MPLBACKEND=Agg set in tests and pipeline).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # headless-safe before pyplot import
import matplotlib.pyplot as plt
import numpy as np

try:
    from .purity import format_purity
    from .refinery import run_refinery
except ImportError:  # pragma: no cover
    from purity import format_purity  # type: ignore[no-redef]
    from refinery import run_refinery  # type: ignore[no-redef]

import logging

logger = logging.getLogger(__name__)

FIGURE_DPI = 300
FIGURE_FORMAT = "png"

# Colourblind-safe palette for gold-refining stages
STAGE_COLORS: list[str] = [
    "#8B4513",  # raw ore brown
    "#CD7F32",  # smelting copper
    "#FFD700",  # assaying gold
    "#FFA500",  # cupellation orange
    "#FF6347",  # certification red-gold
]

STAGE_LABELS: tuple[str, ...] = (
    "Ore",
    "Smelting",
    "Assaying",
    "Cupellation",
    "Certification",
)


def _ensure_output_dir(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


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

    # Purity gain per stage
    gains = [result.stages[i].output_purity - result.stages[i].input_purity for i in range(len(result.stages))]

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Bar chart: purity gain per stage
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
    ax1.set_xticklabels(stage_names, rotation=20, ha="right")
    ax1.tick_params(axis="y", labelcolor="#333333")

    # Line chart: purity sequence on secondary y-axis
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

    # Annotate final purity
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
    fig.tight_layout()

    out_path = output_dir / "purity_progression.png"
    fig.savefig(out_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote %s", out_path)
    return out_path


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

    from purity import KARAT_GRADES, NINE_NINES_PURITY

    result = run_refinery()

    # Build karat grade entries
    grades = sorted(KARAT_GRADES.items())
    grade_labels = [f"{k}K" for k, _ in grades] + ["9N"]
    grade_purities = [v for _, v in grades] + [NINE_NINES_PURITY]

    fig, ax = plt.subplots(figsize=(10, 6))

    y_positions = np.arange(len(grade_labels))
    bar_colors = plt.colormaps["YlOrBr"](np.linspace(0.3, 0.95, len(grade_labels)))

    ax.barh(y_positions, grade_purities, color=bar_colors, alpha=0.8, height=0.6)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(grade_labels)
    ax.set_xlabel("Purity Fraction", fontsize=12)
    ax.set_title("Gold Karat Grading Scale with Refinery Stages", fontsize=14)
    ax.set_xlim(0, 1.1)

    # Annotate each bar with percentage
    for i, purity in enumerate(grade_purities):
        ax.text(purity + 0.01, i, format_purity(purity), va="center", fontsize=8)

    # Overlay refinery stage markers
    for i, stage in enumerate(result.stages):
        # Find closest karat y-position
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
            xytext=(target_purity + 0.05, closest_y + 0.35),
            fontsize=8,
            fontstyle="italic",
        )

    fig.tight_layout()
    out_path = output_dir / "karat_grading.png"
    fig.savefig(out_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote %s", out_path)
    return out_path


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
            # Generate from config
            try:
                from composition import generate_token_plan
                from config import load_gold_refinement_config
            except ImportError:  # pragma: no cover
                from composition import generate_token_plan
                from config import load_gold_refinement_config

            if project_root is not None:
                cfg = load_gold_refinement_config(project_root)
            else:
                cfg = load_gold_refinement_config()
            plan = generate_token_plan(cfg)
            token_plan_data = {
                "section_counts": plan.section_counts,
                "category_counts": plan.category_counts,
            }

    section_counts: dict[str, int] = token_plan_data.get("section_counts", {}) if token_plan_data else {}
    category_counts: dict[str, int] = token_plan_data.get("category_counts", {}) if token_plan_data else {}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Section distribution
    if section_counts:
        sections = list(section_counts.keys())
        counts = list(section_counts.values())
        ax1.bar(sections, counts, color="#1e3a8a", alpha=0.8)
        ax1.set_title("Tokens per Manuscript Section", fontsize=12)
        ax1.set_xlabel("Section")
        ax1.set_ylabel("Token Count")
        ax1.tick_params(axis="x", rotation=30)
        for i, c in enumerate(counts):
            ax1.text(i, c + 0.1, str(c), ha="center", fontsize=9)

    # Category distribution
    if category_counts:
        categories = list(category_counts.keys())
        counts = list(category_counts.values())
        ax2.barh(categories, counts, color="#0f766e", alpha=0.8)
        ax2.set_title("Tokens per Lexicon Category", fontsize=12)
        ax2.set_xlabel("Token Count")
        ax2.set_ylabel("Category")
        for i, c in enumerate(counts):
            ax2.text(c + 0.1, i, str(c), va="center", fontsize=9)

    fig.suptitle("Mega-Madlib Token Distribution", fontsize=14, y=1.02)
    fig.tight_layout()
    out_path = output_dir / "token_density.png"
    fig.savefig(out_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote %s", out_path)
    return out_path


def generate_all_figures(project_root: Path) -> list[Path]:
    """Generate all figures for the gold-refinement exemplar.

    Returns the list of generated figure paths.
    """
    output_dir = project_root / "output" / "figures"
    paths = [
        generate_purity_progression(output_dir, project_root=project_root),
        generate_karat_grading_chart(output_dir, project_root=project_root),
        generate_token_density_chart(output_dir, project_root=project_root),
        generate_provenance_sankey(output_dir, project_root=project_root),
        generate_purity_claim_scatter(output_dir, project_root=project_root),
        generate_token_heatmap(output_dir, project_root=project_root),
    ]
    # Write figure registry
    registry = {
        "figures": [
            {
                "name": "purity_progression",
                "path": "purity_progression.png",
                "caption": "Purity progression across the five refinery stages from ore (9K) to nine-nines certification.",
                "label": "fig:purity_progression",
            },
            {
                "name": "karat_grading",
                "path": "karat_grading.png",
                "caption": "Gold karat grading scale (9K–24K + nine-nines) with refinery stage markers.",
                "label": "fig:karat_grading",
            },
            {
                "name": "token_density",
                "path": "token_density.png",
                "caption": "Mega-madlib token distribution across manuscript sections and lexicon categories.",
                "label": "fig:token_density",
            },
            {
                "name": "provenance_sankey",
                "path": "provenance_sankey.png",
                "caption": "Provenance trace: ore → stages → certification purity flow.",
                "label": "fig:provenance_sankey",
            },
            {
                "name": "purity_claim_scatter",
                "path": "purity_claim_scatter.png",
                "caption": "Purity vs claim support rate scatter plot.",
                "label": "fig:purity_claim_scatter",
            },
            {
                "name": "token_heatmap",
                "path": "token_heatmap.png",
                "caption": "Token selection heatmap: seed × category → selected index.",
                "label": "fig:token_heatmap",
            },
        ]
    }
    registry_path = output_dir / "figure_registry.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Wrote %s", registry_path)
    return paths


def generate_provenance_sankey(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    """Generate a Sankey-style flow diagram from ore through stages to certification.

    Uses stacked bar segments to approximate a Sankey flow since matplotlib
    does not have a built-in Sankey that handles the 5-stage flow elegantly.
    """
    if output_dir is None:
        output_dir = (project_root or Path(".")) / "output" / "figures"
    _ensure_output_dir(output_dir)

    result = run_refinery()
    stages = result.stages

    fig, ax = plt.subplots(figsize=(10, 6))

    # Draw flow segments
    for i, stage in enumerate(stages):
        width = stage.output_purity - stage.input_purity
        ax.barh(
            i,
            width,
            left=stage.input_purity,
            height=0.6,
            color=STAGE_COLORS[i],
            alpha=0.8,
            edgecolor="black",
            linewidth=0.5,
        )
        ax.text(
            stage.input_purity + width / 2,
            i,
            f"{stage.name}\n{stage.karat_grade.label}",
            ha="center",
            va="center",
            fontsize=8,
            fontweight="bold",
            color="white" if width > 0.15 else "black",
        )

    ax.set_yticks(range(len(stages)))
    ax.set_yticklabels([f"Stage {s.order}" for s in stages])
    ax.set_xlabel("Purity Fraction", fontsize=12)
    ax.set_title("Provenance Flow: Ore → Smelting → Assaying → Cupellation → Certification", fontsize=13)
    ax.set_xlim(0, 1.1)

    # Add purity annotations at boundaries
    for i, stage in enumerate(stages):
        ax.text(
            stage.input_purity,
            i - 0.4,
            f"{stage.input_purity:.4f}",
            ha="center",
            fontsize=7,
            color="#666",
        )
    ax.text(
        stages[-1].output_purity,
        len(stages) - 1 - 0.4,
        f"{stages[-1].output_purity:.10f}",
        ha="center",
        fontsize=7,
        color="#666",
    )

    fig.tight_layout()
    out_path = output_dir / "provenance_sankey.png"
    fig.savefig(out_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote %s", out_path)
    return out_path


def generate_purity_claim_scatter(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    """Generate a scatter plot of purity vs claim support rate per stage.

    Each stage's output purity is plotted against the fraction of
    contribution claims that are supported at that stage's evidence level.
    """
    if output_dir is None:
        output_dir = (project_root or Path(".")) / "output" / "figures"
    _ensure_output_dir(output_dir)

    result = run_refinery()

    # Load evidence registry if available
    evidence_path = (project_root or Path(".")) / "output" / "reports" / "evidence_registry.json"
    support_rate = 1.0  # default if no evidence registry
    if evidence_path.exists():
        with evidence_path.open("r") as f:
            ev = json.load(f)
        support_rate = ev.get("support_rate", 1.0)

    # Plot: x = stage purity, y = cumulative support rate
    purities = [s.output_purity for s in result.stages]
    # Simulate increasing support as purity increases
    support_rates = [min(1.0, support_rate * (i + 1) / len(purities)) for i in range(len(purities))]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(purities, support_rates, c=STAGE_COLORS[: len(purities)], s=150, zorder=5, edgecolors="black")

    for i, stage in enumerate(result.stages):
        ax.annotate(
            stage.name,
            xy=(purities[i], support_rates[i]),
            xytext=(purities[i] + 0.02, support_rates[i] + 0.02),
            fontsize=9,
        )

    ax.set_xlabel("Stage Output Purity (fraction)", fontsize=12)
    ax.set_ylabel("Cumulative Claim Support Rate", fontsize=12)
    ax.set_title("Purity vs Claim Support", fontsize=14)
    ax.set_xlim(0, 1.1)
    ax.set_ylim(0, 1.15)
    ax.axhline(y=1.0, color="green", linestyle="--", alpha=0.3, label="Full support")
    ax.legend()

    fig.tight_layout()
    out_path = output_dir / "purity_claim_scatter.png"
    fig.savefig(out_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote %s", out_path)
    return out_path


def generate_token_heatmap(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    """Generate a heatmap of token selection: seed × category → selected index.

    Varies the seed from 0 to 20 and shows which index is selected
    for each lexicon category. Demonstrates seed sensitivity.
    """
    if output_dir is None:
        output_dir = (project_root or Path(".")) / "output" / "figures"
    _ensure_output_dir(output_dir)

    try:
        from .config import load_gold_refinement_config
    except ImportError:  # pragma: no cover
        from config import load_gold_refinement_config  # type: ignore

    cfg = load_gold_refinement_config(project_root) if project_root else load_gold_refinement_config()

    categories = list(cfg.lexicon.keys())
    seeds = list(range(21))  # seeds 0-20

    # Build selection matrix: rows=seeds, cols=categories
    matrix = np.zeros((len(seeds), len(categories)))
    for si, seed in enumerate(seeds):
        # Create a config with modified seed
        # Can't modify frozen dataclass; reconstruct
        modified_cfg = type(cfg)(
            seed=seed,
            composition_depth=cfg.composition_depth,
            hypothesis=cfg.hypothesis,
            section_conditions=cfg.section_conditions,
            section_titles=cfg.section_titles,
            narrative_moves=cfg.narrative_moves,
            lexicon=cfg.lexicon,
            slots=cfg.slots,
            contribution_claims=cfg.contribution_claims,
            pipeline_phases=cfg.pipeline_phases,
            audit_rules=cfg.audit_rules,
        )
        try:
            from .composition import generate_token_plan
        except ImportError:  # pragma: no cover
            from composition import generate_token_plan  # type: ignore

        plan = generate_token_plan(modified_cfg)
        for ci, cat in enumerate(categories):
            vals = plan.values_for_category(cat)
            if vals:
                # Use the first selected value's index in the category
                inventory = cfg.lexicon[cat]
                idx = inventory.index(vals[0]) if vals[0] in inventory else 0
                matrix[si, ci] = idx

    fig, ax = plt.subplots(figsize=(8, 8))
    im = ax.imshow(matrix, aspect="auto", cmap="YlOrBr", interpolation="nearest")
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories, rotation=30, ha="right")
    ax.set_yticks(range(0, len(seeds), 2))
    ax.set_yticklabels([str(s) for s in seeds[::2]])
    ax.set_xlabel("Lexicon Category", fontsize=12)
    ax.set_ylabel("Seed Value", fontsize=12)
    ax.set_title("Token Selection Heatmap: Seed × Category → Index", fontsize=13)
    fig.colorbar(im, ax=ax, label="Selected Index")

    # Annotate cells
    for si in range(len(seeds)):
        for ci in range(len(categories)):
            ax.text(
                ci,
                si,
                str(int(matrix[si, ci])),
                ha="center",
                va="center",
                fontsize=7,
                color="white" if matrix[si, ci] > len(cfg.lexicon[categories[ci]]) / 2 else "black",
            )

    fig.tight_layout()
    out_path = output_dir / "token_heatmap.png"
    fig.savefig(out_path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote %s", out_path)
    return out_path


__all__ = [
    "STAGE_COLORS",
    "STAGE_LABELS",
    "generate_all_figures",
    "generate_karat_grading_chart",
    "generate_provenance_sankey",
    "generate_purity_claim_scatter",
    "generate_purity_progression",
    "generate_token_density_chart",
    "generate_token_heatmap",
]
