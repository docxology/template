"""Figure generation for the AutoScientists analysis scripts.

Kept here in Layer-2 ``src/`` so the ``scripts/`` entry points stay thin
orchestrators: they compute via the coordination core and call these helpers to
render and save the paper's figures. No mocks; deterministic; ``MPLBACKEND=Agg``.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

if TYPE_CHECKING:
    from src import SearchResult


class AblationRow(TypedDict):
    """One ablation configuration's honest metrics."""

    configuration: str
    reported_metric: float
    clean_metric: float
    noise_inflation: float
    confirmed_improvements: int
    experiments_used: int
    experiments_to_target: int | None
    redundant_experiments: int


def _save(fig: "plt.Figure", path: Path) -> None:
    """Finalize and persist a figure deterministically."""
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def build_ablation_figure(rows: list[AblationRow]) -> tuple["plt.Figure", "plt.Axes"]:
    """Build (not save) the reported-vs-clean ablation chart; returns (fig, ax).

    Split from :func:`write_ablation_figure` so tests can assert on the plotted
    content (bar values, labels, legend) instead of only checking that a PNG exists.
    """
    labels = [row["configuration"] for row in rows]
    reported = [row["reported_metric"] for row in rows]
    clean = [row["clean_metric"] for row in rows]
    positions = range(len(rows))
    height = 0.38
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.barh([p + height / 2 for p in positions], reported, height=height, color="#1e3a8a", label="Reported metric")
    ax.barh(
        [p - height / 2 for p in positions], clean, height=height, color="#0f766e", label="Clean (ground-truth) metric"
    )
    ax.set_yticks(list(positions))
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("Final champion metric (higher is better)")
    ax.set_title(
        "Ablation: reported vs clean champion metric\n(a reported>clean gap is noise the mechanism failed to filter)"
    )
    ax.legend(loc="lower right")
    ax.grid(True, axis="x", alpha=0.3)
    return fig, ax


def write_ablation_figure(rows: list[AblationRow], path: Path) -> None:
    """Reported vs clean champion metric per ablation (noise the run failed to filter)."""
    fig, _ = build_ablation_figure(rows)
    _save(fig, path)


def build_efficiency_figure(rows: list[AblationRow]) -> tuple["plt.Figure", "plt.Axes"]:
    """Build (not save) the experiments/redundant-reprobes chart; returns (fig, ax)."""
    labels = [row["configuration"] for row in rows]
    used = [row["experiments_used"] for row in rows]
    redundant = [row["redundant_experiments"] for row in rows]
    positions = range(len(rows))
    height = 0.38
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.barh([p + height / 2 for p in positions], used, height=height, color="#1e3a8a", label="Experiments used")
    ax.barh(
        [p - height / 2 for p in positions],
        redundant,
        height=height,
        color="#b45309",
        label="Redundant re-probes of retired directions",
    )
    ax.set_yticks(list(positions))
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("Experiments (of a 60-experiment budget)")
    ax.set_title(
        "Ablation: search efficiency and hygiene\n"
        "(the dead-end registry cuts redundant re-exploration to zero — same clean answer)"
    )
    ax.legend(loc="lower right")
    ax.grid(True, axis="x", alpha=0.3)
    return fig, ax


def write_efficiency_figure(rows: list[AblationRow], path: Path) -> None:
    """Experiments spent and redundant re-probes (where the dead-end registry pays off)."""
    fig, _ = build_efficiency_figure(rows)
    _save(fig, path)


def build_comparison_figure(coordinated: SearchResult, baseline: SearchResult) -> tuple["plt.Figure", "plt.Axes"]:
    """Build (not save) the champion-trajectory comparison; returns (fig, ax).

    The coordinated curve is drawn solid (default linestyle) and the baseline
    dashed — exactly the convention the @fig:comparison caption states. Splitting
    build from save lets a test pin that convention without mocks.
    """
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    ax.plot(range(1, len(coordinated.trajectory) + 1), coordinated.trajectory, label="Coordinated teams", linewidth=2.0)
    ax.plot(
        range(1, len(baseline.trajectory) + 1),
        baseline.trajectory,
        label="Single-thread baseline",
        linewidth=2.0,
        linestyle="--",
    )
    ax.set_xlabel("Experiment")
    ax.set_ylabel("Champion metric (higher is better)")
    ax.set_title(
        "Champion trajectory under matched experiment budget\n"
        "(coordinated teams partition the same budget as the baseline)"
    )
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    return fig, ax


def write_comparison_figure(coordinated: SearchResult, baseline: SearchResult, path: Path) -> None:
    """Champion trajectories: coordinated teams vs single-thread baseline (matched budget)."""
    fig, _ = build_comparison_figure(coordinated, baseline)
    _save(fig, path)
