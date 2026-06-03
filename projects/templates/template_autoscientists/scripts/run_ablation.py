#!/usr/bin/env python3
"""Thin orchestrator: per-mechanism ablation of the coordination loop.

Reproduces the paper's "remove one component" study. Starting from the full
coordinated configuration, each mechanism (confirmation, dead-end registry,
effect-size ranking, stagnation reorganization) is switched off in turn and the
resulting final champion metric is compared against the full configuration. All
computation lives in ``src``; this script only orchestrates, plots, and writes
outputs.
"""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import TypedDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]
for path in (PROJECT_ROOT, PROJECT_ROOT / "src", REPO_ROOT):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src import DeterministicProposer, SearchConfig, SyntheticObjective, run_search  # noqa: E402

BUDGET = 60

ABLATIONS: tuple[tuple[str, dict[str, bool]], ...] = (
    ("full coordination", {}),
    ("no confirmation", {"use_confirmation": False}),
    ("no dead-end registry", {"use_dead_ends": False}),
    ("no effect-size ranking", {"use_ranking": False}),
    ("no reorganization", {"use_reorganization": False}),
)


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


def _run_ablations() -> list[AblationRow]:
    objective = SyntheticObjective(dimensions=4, noise_scale=0.02)
    proposer = DeterministicProposer()
    base = SearchConfig(budget=BUDGET)

    rows: list[AblationRow] = []
    for label, overrides in ABLATIONS:
        config = replace(base, **overrides) if overrides else base
        result = run_search(objective, proposer, config)
        reported = result.champion.metric
        # Clean is the noise-free ground truth. A large reported-minus-clean gap
        # means the configuration accepted a noise-inflated champion.
        clean = objective.clean(result.champion.params)
        rows.append(
            {
                "configuration": label,
                "reported_metric": reported,
                "clean_metric": clean,
                "noise_inflation": reported - clean,
                "confirmed_improvements": result.num_confirmed_improvements,
                "experiments_used": len(result.trajectory),
                "experiments_to_target": result.experiments_to_target,
                "redundant_experiments": result.redundant_experiments,
            }
        )
    return rows


def _write_figure(rows: list[AblationRow], path: Path) -> None:
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
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _write_efficiency_figure(rows: list[AblationRow], path: Path) -> None:
    """The honest efficiency axis: experiments spent and redundant re-probes.

    The dead-end registry's value shows up here, not in the final metric: with
    it on, the registry-consulting proposer never re-probes a retired direction
    and halts once directions are exhausted; with it off the same search burns
    the whole budget on re-exploration it could have skipped.
    """
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
        "Ablation: search efficiency and hygiene\n(the dead-end registry cuts redundant re-exploration to zero — same clean answer)"
    )
    ax.legend(loc="lower right")
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> int:
    rows = _run_ablations()

    figures_dir = PROJECT_ROOT / "output" / "figures"
    data_dir = PROJECT_ROOT / "output" / "data"
    figures_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    figure_path = figures_dir / "ablation.png"
    efficiency_path = figures_dir / "ablation_efficiency.png"
    data_path = data_dir / "ablation.json"
    _write_figure(rows, figure_path)
    _write_efficiency_figure(rows, efficiency_path)
    data_path.write_text(json.dumps({"budget": BUDGET, "rows": rows}, indent=2, sort_keys=True) + "\n")

    print(figure_path)
    print(efficiency_path)
    print(data_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
