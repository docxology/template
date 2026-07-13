"""Deterministic figure rendering for the registered-report exemplar.

Plotting logic lives here (importable and tested) rather than in ``scripts/``,
so the analysis script stays a thin orchestrator. Every figure is a pure
function of the frozen registration and the seeded demonstration study; nothing
is drawn from external state. Matplotlib is forced onto the headless ``Agg``
backend on import so the module is safe to call from tests and pipelines.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

from registered_report.demo_study import (  # noqa: E402
    analysis_plan_stages,
    deviation_timeline,
    generate_demo_dataset,
    hypothesis_outcome_map,
    permutation_null_distribution,
    run_permutation_test,
)
from registered_report.protocol import build_deviation_ledger  # noqa: E402

__all__ = [
    "FIGURE_REGISTRY_SCHEMA",
    "REGISTERED_REPORT_FIGURE_SPECS",
    "RegisteredReportFigureSpec",
    "plot_analysis_dag",
    "plot_deviation_timeline",
    "plot_hypothesis_map",
    "plot_permutation_result",
    "render_all_figures",
]


@dataclass(frozen=True)
class RegisteredReportFigureSpec:
    """Provenance metadata for one registered-report figure."""

    label: str
    filename: str
    caption: str
    generated_by: str


FIGURE_REGISTRY_SCHEMA = "template-registered-report-figure-registry-v1"
REGISTERED_REPORT_FIGURE_SPECS: tuple[RegisteredReportFigureSpec, ...] = (
    RegisteredReportFigureSpec(
        label="fig:hypothesis_map",
        filename="hypothesis_map.png",
        caption="Registered hypothesis-to-outcome-to-analysis mapping.",
        generated_by="registered_report.figures.plot_hypothesis_map",
    ),
    RegisteredReportFigureSpec(
        label="fig:analysis_dag",
        filename="analysis_dag.png",
        caption="Registered analysis workflow and pre-results lock boundary.",
        generated_by="registered_report.figures.plot_analysis_dag",
    ),
    RegisteredReportFigureSpec(
        label="fig:deviation_timeline",
        filename="deviation_timeline.png",
        caption="Timeline of registered decisions and documented deviations.",
        generated_by="registered_report.figures.plot_deviation_timeline",
    ),
    RegisteredReportFigureSpec(
        label="fig:permutation_result",
        filename="permutation_result.png",
        caption="Seeded permutation null distribution and observed registered statistic.",
        generated_by="registered_report.figures.plot_permutation_result",
    ),
)
_SPEC_BY_LABEL = {spec.label: spec for spec in REGISTERED_REPORT_FIGURE_SPECS}

_OK = "#2f855a"
_WARN = "#c05621"
_ERROR = "#c53030"
_LOCKED = "#2b6cb0"
_OPEN = "#805ad5"
_INK = "#1a202c"
_SEVERITY_COLORS = {"ok": _OK, "warning": _WARN, "error": _ERROR}

# The exploratory endpoint and model change the exemplar reports as documented
# deviations (mirrors scripts/generate_review_artifacts.py).
_EXECUTED_WITH_DEVIATIONS = {
    "outcomes": ["primary_score", "secondary_score"],
    "primary_model": "linear_model",
}
_DEVIATIONS = [
    {"kind": "outcome", "target": "secondary_score", "rationale": "exploratory robustness endpoint"},
    {"kind": "model", "target": "linear_model", "rationale": "robustness sensitivity"},
]


def _box(ax: Any, x: float, y: float, w: float, h: float, text: str, color: str, fontsize: float = 8.5) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.01,rounding_size=0.02",
            linewidth=1.4,
            edgecolor=color,
            facecolor=color + "22",
        )
    )
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize, color=_INK)


def _arrow(ax: Any, start: tuple[float, float], end: tuple[float, float]) -> None:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=12, linewidth=1.2, color=_INK))


def plot_hypothesis_map(registration: dict[str, Any], path: Path) -> Path:
    """Render the hypothesis-to-outcome-to-analysis mapping diagram."""
    edges = hypothesis_outcome_map(registration)
    fig, ax = plt.subplots(figsize=(9.2, 1.9 + 1.7 * len(edges)))
    columns = ("Hypothesis", "Outcome", "Measure", "Analysis")
    xs = (0.02, 0.27, 0.52, 0.77)
    width = 0.20
    for x, title in zip(xs, columns):
        ax.text(x + width / 2, 0.95, title, ha="center", va="center", fontsize=11, fontweight="bold", color=_INK)
    row_span = 0.78 / max(len(edges), 1)
    box_h = min(row_span * 0.82, 0.5)
    for index, edge in enumerate(edges):
        y = 0.80 - (index + 1) * row_span + (row_span - box_h) / 2
        cells = (
            f"{edge.hypothesis_id}\n" + textwrap.fill(edge.claim, 22),
            textwrap.fill(edge.outcome, 16),
            textwrap.fill(edge.measure, 16),
            textwrap.fill(edge.analysis, 16),
        )
        colors = (_LOCKED, _OK, _OPEN, _WARN)
        cy = y + box_h / 2
        for x, cell, color in zip(xs, cells, colors):
            _box(ax, x, y, width, box_h, cell, color)
        for x, nx in zip(xs[:-1], xs[1:]):
            _arrow(ax, (x + width, cy), (nx, cy))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("Registered hypothesis to outcome to analysis mapping", fontsize=12, color=_INK)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_analysis_dag(path: Path) -> Path:
    """Render the registered-report workflow DAG with the results-lock boundary."""
    stages = analysis_plan_stages()
    fig, ax = plt.subplots(figsize=(11.0, 3.0))
    n = len(stages)
    width = 0.128
    box_h = 0.32
    gap = (1.0 - width * n) / (n + 1)
    centers = []
    for stage in stages:
        x = gap + stage.index * (width + gap)
        color = _LOCKED if stage.locks_before_results else _OPEN
        label = f"{stage.index + 1}. " + textwrap.fill(stage.label, 13)
        _box(ax, x, 0.42, width, box_h, label, color, fontsize=8.0)
        centers.append((x, x + width, 0.42 + box_h / 2))
    for (_, right, y), (left, _, _) in zip(centers[:-1], centers[1:]):
        _arrow(ax, (right, y), (left, y))
    locked = [s for s in stages if s.locks_before_results]
    boundary_x = gap + len(locked) * (width + gap) - gap / 2
    ax.axvline(boundary_x, ymin=0.15, ymax=0.85, color=_ERROR, linestyle="--", linewidth=1.4)
    ax.text(boundary_x, 0.86, "results revealed", ha="center", va="bottom", fontsize=9, color=_ERROR)
    ax.text(0.02, 0.18, "Locked before results", color=_LOCKED, fontsize=9, fontweight="bold")
    ax.text(0.62, 0.18, "Interpreted after results", color=_OPEN, fontsize=9, fontweight="bold")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("Registered-report analysis workflow (pre-registration lock boundary)", fontsize=11, color=_INK)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_deviation_timeline(registration: dict[str, Any], path: Path) -> Path:
    """Render the preregistration-versus-executed deviation timeline."""
    ledger = build_deviation_ledger(registration, _EXECUTED_WITH_DEVIATIONS, _DEVIATIONS)
    events = deviation_timeline(ledger)
    fig, ax = plt.subplots(figsize=(8.6, 2.4 + 0.5 * len(events)))
    ax.axhline(0.5, color="#a0aec0", linewidth=1.0, zorder=0)
    n = len(events)
    for event in events:
        x = (event.order + 1) / (n + 1)
        color = _SEVERITY_COLORS.get(event.severity, _INK)
        ax.scatter([x], [0.5], s=260, color=color, zorder=3, edgecolor=_INK, linewidth=0.8)
        status = "registered" if event.registered else ("documented deviation" if event.documented else "undocumented")
        label = f"{event.kind}: {event.target}\n{status} ({event.severity})"
        va = "bottom" if event.order % 2 == 0 else "top"
        y_text = 0.62 if event.order % 2 == 0 else 0.38
        ax.annotate(
            label,
            xy=(x, 0.5),
            xytext=(x, y_text),
            ha="center",
            va=va,
            fontsize=8.5,
            color=_INK,
            arrowprops={"arrowstyle": "-", "color": "#a0aec0"},
        )
    handles = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=10, label=name)
        for name, c in (("registered (ok)", _OK), ("documented deviation", _WARN), ("undocumented (error)", _ERROR))
    ]
    ax.legend(handles=handles, loc="lower center", ncol=3, fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.04))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("Preregistration-versus-executed deviation ledger timeline", fontsize=11, color=_INK)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_permutation_result(summary: dict[str, Any], path: Path) -> Path:
    """Render the seeded permutation null distribution and observed difference."""
    seed = int(summary["seed"])
    dataset = generate_demo_dataset(seed=seed, n_per_group=int(summary["n_control"]), effect=float(summary["effect"]))
    result = run_permutation_test(dataset, seed=seed, n_permutations=int(summary["n_permutations"]))
    null = permutation_null_distribution(dataset, seed=seed, n_permutations=int(summary["n_permutations"]))
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    ax.hist(null, bins=40, color=_LOCKED + "55", edgecolor=_LOCKED, linewidth=0.6, label="permutation null")
    ax.axvline(
        result.observed_difference,
        color=_ERROR,
        linewidth=2.0,
        label=f"observed diff = {result.observed_difference:.3f}",
    )
    ax.axvline(-result.observed_difference, color=_ERROR, linewidth=1.0, linestyle=":")
    ax.set_xlabel("treatment - control mean difference (demonstration data)")
    ax.set_ylabel("permutation count")
    ax.set_title("Registered permutation test on deterministic demonstration data", fontsize=11, color=_INK)
    annotation = (
        f"n = {summary['n_control']} per group\n"
        f"permutations = {summary['n_permutations']}\n"
        f"|diff| >= observed: {summary['n_at_least_as_extreme']}\n"
        f"two-sided p = {result.p_value:.4f}\n"
        f"alpha = {summary['alpha']}"
    )
    ax.text(
        0.02,
        0.97,
        annotation,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        color=_INK,
        bbox={"boxstyle": "round", "facecolor": "white", "edgecolor": _INK, "alpha": 0.9},
    )
    ax.legend(loc="upper right", fontsize=9, frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def render_all_figures(
    registration: dict[str, Any],
    summary: dict[str, Any],
    figures_dir: Path,
) -> dict[str, Path]:
    """Render the four exemplar figures into ``figures_dir``.

    Args:
        registration: A frozen registration mapping.
        summary: The executed-analysis summary from
            :func:`registered_report.demo_study.run_registered_analysis`.
        figures_dir: Destination directory (created if absent).

    Returns:
        Mapping of figure key to written PNG path.
    """
    figures_dir.mkdir(parents=True, exist_ok=True)
    return {
        "hypothesis_map": plot_hypothesis_map(
            registration,
            figures_dir / _SPEC_BY_LABEL["fig:hypothesis_map"].filename,
        ),
        "analysis_dag": plot_analysis_dag(figures_dir / _SPEC_BY_LABEL["fig:analysis_dag"].filename),
        "deviation_timeline": plot_deviation_timeline(
            registration,
            figures_dir / _SPEC_BY_LABEL["fig:deviation_timeline"].filename,
        ),
        "permutation_result": plot_permutation_result(
            summary,
            figures_dir / _SPEC_BY_LABEL["fig:permutation_result"].filename,
        ),
    }
