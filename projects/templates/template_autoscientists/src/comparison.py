"""Matched-budget coordinated-search comparison.

The experiment definition and summary construction live here so scripts remain
thin and tests exercise exactly the same implementation used to make outputs.
"""

from __future__ import annotations

from typing import TypedDict

from .agents import DeterministicProposer
from .objective import SyntheticObjective
from .search import SearchConfig, SearchResult, run_search

DEFAULT_BUDGET = 60


class RunSummary(TypedDict):
    """Reported, ground-truth, and efficiency outcomes for one search."""

    reported_metric: float
    clean_metric: float
    confirmed_improvements: int
    retired_dead_ends: int
    experiments_used: int
    experiments_to_target: int | None
    redundant_experiments: int


def build_objective() -> SyntheticObjective:
    """Build the deterministic objective shared by the paper experiments."""
    return SyntheticObjective(dimensions=4, noise_scale=0.02)


def run_comparison(objective: SyntheticObjective, *, budget: int = DEFAULT_BUDGET) -> tuple[SearchResult, SearchResult]:
    """Run coordinated and single-thread searches under the same budget."""
    proposer = DeterministicProposer()
    coordinated = run_search(objective, proposer, SearchConfig(budget=budget))
    baseline = run_search(objective, proposer, SearchConfig.single_thread_baseline(budget=budget))
    return coordinated, baseline


def summarize_run(objective: SyntheticObjective, result: SearchResult) -> RunSummary:
    """Summarize one run without conflating reported and clean metrics."""
    return {
        "reported_metric": result.champion.metric,
        "clean_metric": objective.clean(result.champion.params),
        "confirmed_improvements": result.num_confirmed_improvements,
        "retired_dead_ends": len(result.retired_dead_ends),
        "experiments_used": len(result.trajectory),
        "experiments_to_target": result.experiments_to_target,
        "redundant_experiments": result.redundant_experiments,
    }


def build_comparison_payload(
    objective: SyntheticObjective,
    coordinated: SearchResult,
    baseline: SearchResult,
    *,
    budget: int = DEFAULT_BUDGET,
) -> dict[str, object]:
    """Build the persisted comparison report from real search results."""
    return {
        "budget": budget,
        "note": (
            "Coordinated teams partition the same sequential experiment budget as the "
            "baseline, so this is a robustness/efficiency comparison, not a parallel-compute "
            "speedup. Clean metric is the noise-free ground truth."
        ),
        "coordinated": summarize_run(objective, coordinated),
        "baseline": summarize_run(objective, baseline),
        "clean_metric_advantage": (
            objective.clean(coordinated.champion.params) - objective.clean(baseline.champion.params)
        ),
    }
