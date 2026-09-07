"""Figure generation for the AutoScientists analysis scripts.

Kept here in Layer-2 ``src/`` so the ``scripts/`` entry points stay thin
orchestrators: they compute via the coordination core and call these helpers to
render and save the paper's figures. No mocks; deterministic; ``MPLBACKEND=Agg``.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

if TYPE_CHECKING:  # pragma: no cover
    from .search import SearchResult

from .ablation import AblationRow


@dataclass(frozen=True)
class FigureSpec:
    """Data container for FigureSpec."""

    label: str
    filename: str
    caption: str
    generated_by: str
    alt_text: str


FIGURE_SPECS: tuple[FigureSpec, ...] = (
    FigureSpec(
        label="fig:comparison",
        filename="search_comparison.png",
        caption="Champion metric trajectory under a matched experiment budget.",
        generated_by="scripts/run_search_comparison.py",
        alt_text=(
            "Line chart of reported champion metrics under one matched sequential budget, with coordinated "
            "teams shown solid and the single-thread baseline dashed; point counts are not wall-clock speed."
        ),
    ),
    FigureSpec(
        label="fig:ablation",
        filename="ablation.png",
        caption="Reported versus clean champion metric by coordination mechanism ablation.",
        generated_by="scripts/run_ablation.py",
        alt_text=(
            "Paired horizontal bars encode reported and noise-free clean final metrics for each coordination "
            "ablation on the synthetic objective; values do not establish general agent performance."
        ),
    ),
    FigureSpec(
        label="fig:ablation_efficiency",
        filename="ablation_efficiency.png",
        caption="Experiment use and redundant re-probes by coordination mechanism ablation.",
        generated_by="scripts/run_ablation.py",
        alt_text=(
            "Paired horizontal bars encode sequential experiments used and redundant re-probes for each "
            "coordination ablation; counts are not parallel throughput or wall-clock timing."
        ),
    ),
)


def figure_specs_for_results(
    coordinated: SearchResult,
    baseline: SearchResult,
    rows: Sequence[AblationRow],
) -> tuple[FigureSpec, ...]:
    """Bind alternate text to the exact result objects rendered in one run."""
    alt_by_label = {
        "fig:comparison": comparison_alt_text(coordinated.trajectory, baseline.trajectory),
        "fig:ablation": ablation_alt_text(rows),
        "fig:ablation_efficiency": efficiency_alt_text(rows),
    }
    return tuple(replace(spec, alt_text=alt_by_label[spec.label]) for spec in FIGURE_SPECS)


def comparison_alt_text(
    coordinated: Sequence[float],
    baseline: Sequence[float],
) -> str:
    """Describe the plotted reported-metric trajectories without stale constants."""
    if not coordinated and not baseline:
        return (
            "Empty champion-metric line chart: neither the coordinated run nor the single-thread baseline "
            "contains trajectory points, so no search comparison can be made."
        )

    def describe(label: str, style: str, values: Sequence[float]) -> str:
        if not values:
            return f"The {style} {label} line contains no points"
        return (
            f"The {style} {label} line contains {len(values)} points, starting at {_metric(values[0])} and "
            f"ending at {_metric(values[-1])}"
        )

    return (
        f"Champion-metric trajectories under a matched sequential experiment budget. "
        f"{describe('coordinated-teams', 'solid', coordinated)}; "
        f"{describe('single-thread baseline', 'dashed', baseline)}. Values are reported noisy champion "
        "metrics; line length can reflect early stopping and does not encode wall-clock speed."
    )


def ablation_alt_text(rows: Sequence[AblationRow]) -> str:
    """Describe reported/clean bars from the actual ablation rows."""
    if not rows:
        return (
            "Empty reported-versus-clean ablation chart: no configuration rows were supplied, so no "
            "mechanism comparison can be made."
        )
    descriptions = [
        f"{row['configuration']}: reported {_metric(row['reported_metric'])}, clean {_metric(row['clean_metric'])}"
        for row in rows
    ]
    largest = max(rows, key=lambda row: abs(row["reported_metric"] - row["clean_metric"]))
    gap = largest["reported_metric"] - largest["clean_metric"]
    return (
        f"Paired horizontal bars compare final reported and clean metrics for {len(rows)} configurations: "
        f"{'; '.join(descriptions)}. The largest absolute reported-minus-clean gap is {_metric(abs(gap))} "
        f"for {largest['configuration']}. These are outcomes on this synthetic objective, not evidence of "
        "general agent performance."
    )


def efficiency_alt_text(rows: Sequence[AblationRow]) -> str:
    """Describe experiment-use/re-probe bars from the actual ablation rows."""
    if not rows:
        return (
            "Empty search-efficiency ablation chart: no configuration rows were supplied, so no experiment "
            "use or redundant re-probes can be compared."
        )
    descriptions = [
        f"{row['configuration']}: {row['experiments_used']} used, {row['redundant_experiments']} redundant"
        for row in rows
    ]
    most_redundant = max(row["redundant_experiments"] for row in rows)
    most_redundant_labels = [row["configuration"] for row in rows if row["redundant_experiments"] == most_redundant]
    return (
        f"Paired horizontal bars compare sequential experiment use and redundant re-probes for {len(rows)} "
        f"configurations: {'; '.join(descriptions)}. The largest redundant count is {most_redundant} for "
        f"{', '.join(most_redundant_labels)}. Counts do not encode parallel throughput or wall-clock timing."
    )


def _metric(value: float) -> str:
    if abs(value) < 5e-13:
        value = 0.0
    return f"{value:.4f}"


def write_figure_registry(
    figures_dir: Path,
    specs: Sequence[FigureSpec] = FIGURE_SPECS,
) -> Path:
    """Write the figure registry to a JSON file."""
    figures_dir.mkdir(parents=True, exist_ok=True)
    path = figures_dir / "figure_registry.json"
    records: list[dict[str, object]] = []
    for spec in specs:
        record = asdict(spec)
        alt_text = str(record.pop("alt_text")).strip()
        if not alt_text:
            raise ValueError(f"figure alt_text must not be empty: {spec.label}")
        record["metadata"] = {"alt_text": alt_text}
        records.append(record)
    payload = {
        "schema_version": "template-autoscientists-figure-registry-v1",
        "figures": records,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


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


__all__ = [
    "AblationRow",
    "FIGURE_SPECS",
    "FigureSpec",
    "build_ablation_figure",
    "build_comparison_figure",
    "build_efficiency_figure",
    "ablation_alt_text",
    "comparison_alt_text",
    "efficiency_alt_text",
    "figure_specs_for_results",
    "write_ablation_figure",
    "write_comparison_figure",
    "write_efficiency_figure",
    "write_figure_registry",
]
