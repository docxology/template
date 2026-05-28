"""Process and readiness figure writers for the AutoResearch exemplar."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from .figures_core import palette_color, save_figure, styled_grid
from .ml_task import MLTaskResult
from .models import AutoResearchLoopResult


def write_stage_matrix_figure(figures_dir: Path, result: AutoResearchLoopResult) -> Path:
    """Write the stage matrix bar chart."""
    from matplotlib import pyplot as plt

    path = figures_dir / "autoresearch_stage_matrix.png"
    labels = ("stages", "claims", "artifacts")
    values = (
        len(result.stage_results),
        result.supported_claim_count,
        len(result.config.required_artifacts),
    )
    colors = (
        palette_color("accent", "#2563eb"),
        palette_color("positive", "#0f766e"),
        palette_color("negative", "#7c2d12"),
    )
    fig, ax = plt.subplots(figsize=(7.0, 2.6))
    ax.barh(labels, values, color=colors)
    ax.set_title("AutoResearch readiness matrix")
    ax.set_xlabel("count")
    ax.set_xlim(0, max(values) + 1)
    for index, value in enumerate(values):
        ax.text(value + 0.1, index, str(value), va="center", fontsize=10)
    ax.text(
        0.99,
        0.06,
        "validated run state" if result.readiness_valid else "pre-readiness state",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        color=palette_color("annotation", "#475569"),
    )
    styled_grid(ax, "x")
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    return save_figure(fig, path)


def write_candidate_lifecycle_figure(figures_dir: Path, result: MLTaskResult) -> Path:
    """Write candidate lifecycle counts from the candidate ledger state."""
    from matplotlib import pyplot as plt

    path = figures_dir / "autoresearch_candidate_lifecycle.png"
    ordered_statuses = ("proposed", "evaluated", "accepted", "rejected", "deferred")
    lifecycle_counts: Counter[str] = Counter()
    for candidate in result.candidates:
        lifecycle_counts.update(candidate.lifecycle)
        if candidate.status not in candidate.lifecycle:
            lifecycle_counts[candidate.status] += 1
    values = [lifecycle_counts[status] for status in ordered_statuses]
    colors = (
        palette_color("baseline", "#52525b"),
        palette_color("accent", "#2563eb"),
        palette_color("positive", "#0f766e"),
        palette_color("negative", "#7c2d12"),
        palette_color("warning", "#a16207"),
    )
    fig, ax = plt.subplots(figsize=(7.4, 3.0))
    bars = ax.bar(ordered_statuses, values, color=colors)
    ax.set_title("Candidate lifecycle ledger")
    ax.set_ylabel("candidate records")
    ax.set_ylim(0, max(values) + 1)
    styled_grid(ax, "y")
    ax.set_axisbelow(True)
    for bar, value in zip(bars, values, strict=True):
        ax.text(bar.get_x() + bar.get_width() / 2.0, value + 0.06, str(value), ha="center", fontsize=9)
    ax.text(
        0.99,
        0.05,
        f"budget evaluated {result.evaluated_candidate_count} of {result.candidate_count}",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        color=palette_color("annotation", "#475569"),
    )
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    return save_figure(fig, path)


def write_closure_flow_figure(figures_dir: Path, result: AutoResearchLoopResult) -> Path:
    """Write the file-backed research-process closure diagram."""
    from matplotlib import pyplot as plt

    path = figures_dir / "autoresearch_closure_flow.png"
    nodes = (
        ("Program", "program.md"),
        ("Proposals", "idea ledger"),
        ("Evaluation", f"{result.ml_task.get('evaluated_candidate_count', 'N/A')} candidates"),
        ("Ledgers", "run + artifacts"),
        ("Claims", f"{result.supported_claim_count} supported"),
        ("Manuscript", "variables + figures"),
        ("Readiness", "passed" if result.readiness_valid else "pending"),
        ("Review", "human deferred"),
    )
    box_face = palette_color("box_face", "#f8fafc")
    box_edge = palette_color("box_edge", "#334155")
    arrow_color = palette_color("arrow", "#475569")
    fig, ax = plt.subplots(figsize=(10.4, 2.8))
    ax.set_axis_off()
    y = 0.5
    x_positions = [index / (len(nodes) - 1) for index in range(len(nodes))]
    for index, ((title, detail), x_pos) in enumerate(zip(nodes, x_positions, strict=True)):
        ax.text(
            x_pos,
            y,
            f"{title}\n{detail}",
            ha="center",
            va="center",
            fontsize=9,
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": box_face,
                "edgecolor": box_edge,
                "linewidth": 1.0,
            },
        )
        if index < len(nodes) - 1:
            ax.annotate(
                "",
                xy=(x_positions[index + 1] - 0.055, y),
                xytext=(x_pos + 0.055, y),
                arrowprops={"arrowstyle": "->", "color": arrow_color, "linewidth": 1.2},
            )
    ax.set_title("File-backed AutoResearch closure", fontsize=12, pad=18)
    fig.tight_layout()
    return save_figure(fig, path)


__all__ = [
    "write_stage_matrix_figure",
    "write_candidate_lifecycle_figure",
    "write_closure_flow_figure",
]
