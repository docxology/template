#!/usr/bin/env python3
"""Thin orchestrator: coordinated search vs single-thread baseline.

Runs the coordinated AutoScientists loop and the single-thread baseline on the
same deterministic objective under a *matched* experiment budget, then renders
their champion trajectories plus a machine-readable summary. Because coordinated
teams partition the same sequential budget (rather than adding parallel compute),
this is an honest robustness/efficiency comparison, not a speedup claim — the
summary reports both the reported metric and the noise-free clean metric. All
computation lives in ``src``; this script only orchestrates, plots, and writes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]
for path in (PROJECT_ROOT, PROJECT_ROOT / "src", REPO_ROOT):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from src import (  # noqa: E402
    DeterministicProposer,
    SearchConfig,
    SearchResult,
    SyntheticObjective,
    run_search,
)
from src.figures import write_comparison_figure, write_figure_registry  # noqa: E402

BUDGET = 60


def _build_objective() -> SyntheticObjective:
    return SyntheticObjective(dimensions=4, noise_scale=0.02)


def _run_pair(objective: SyntheticObjective) -> tuple[SearchResult, SearchResult]:
    proposer = DeterministicProposer()
    coordinated = run_search(objective, proposer, SearchConfig(budget=BUDGET))
    baseline = run_search(objective, proposer, SearchConfig.single_thread_baseline(budget=BUDGET))
    return coordinated, baseline


def _summary(objective: SyntheticObjective, coordinated: SearchResult, baseline: SearchResult) -> dict[str, object]:
    return {
        "budget": BUDGET,
        "note": (
            "Coordinated teams partition the same sequential experiment budget as the "
            "baseline, so this is a robustness/efficiency comparison, not a parallel-compute "
            "speedup. Clean metric is the noise-free ground truth."
        ),
        "coordinated": _run_summary(objective, coordinated),
        "baseline": _run_summary(objective, baseline),
        "clean_metric_advantage": (
            objective.clean(coordinated.champion.params) - objective.clean(baseline.champion.params)
        ),
    }


def _run_summary(objective: SyntheticObjective, result: SearchResult) -> dict[str, object]:
    return {
        "reported_metric": result.champion.metric,
        "clean_metric": objective.clean(result.champion.params),
        "confirmed_improvements": result.num_confirmed_improvements,
        "retired_dead_ends": len(result.retired_dead_ends),
        "experiments_used": len(result.trajectory),
        "experiments_to_target": result.experiments_to_target,
        "redundant_experiments": result.redundant_experiments,
    }


def main() -> int:
    """CLI entry point."""
    objective = _build_objective()
    coordinated, baseline = _run_pair(objective)

    figures_dir = PROJECT_ROOT / "output" / "figures"
    data_dir = PROJECT_ROOT / "output" / "data"
    figures_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    figure_path = figures_dir / "search_comparison.png"
    data_path = data_dir / "search_comparison.json"
    write_comparison_figure(coordinated, baseline, figure_path)
    registry_path = write_figure_registry(figures_dir)
    data_path.write_text(json.dumps(_summary(objective, coordinated, baseline), indent=2, sort_keys=True) + "\n")

    print(figure_path)
    print(registry_path)
    print(data_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
