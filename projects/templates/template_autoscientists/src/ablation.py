"""Deterministic ablation study for the coordination mechanisms.

This module owns the experiment definition and derived measurements.  The
corresponding script is intentionally limited to file-system orchestration and
figure writing.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TypedDict

from .agents import DeterministicProposer
from .objective import SyntheticObjective
from .search import SearchConfig, run_search

DEFAULT_BUDGET = 60

ABLATIONS: tuple[tuple[str, dict[str, bool]], ...] = (
    ("full coordination", {}),
    ("no confirmation", {"use_confirmation": False}),
    ("no dead-end registry", {"use_dead_ends": False}),
    ("no effect-size ranking", {"use_ranking": False}),
    ("no reorganization", {"use_reorganization": False}),
)


class AblationRow(TypedDict):
    """One ablation configuration's measured outcomes."""

    configuration: str
    reported_metric: float
    clean_metric: float
    noise_inflation: float
    confirmed_improvements: int
    experiments_used: int
    experiments_to_target: int | None
    redundant_experiments: int


class AblationPayload(TypedDict):
    """Machine-readable ablation report."""

    budget: int
    noise_inflation_ratio_without_confirmation: float
    rows: list[AblationRow]


def run_ablations(*, budget: int = DEFAULT_BUDGET) -> list[AblationRow]:
    """Run the full configuration and each single-mechanism ablation."""
    objective = SyntheticObjective(dimensions=4, noise_scale=0.02)
    proposer = DeterministicProposer()
    base = SearchConfig(budget=budget)

    rows: list[AblationRow] = []
    for label, overrides in ABLATIONS:
        config = base
        if "use_confirmation" in overrides:
            config = replace(config, use_confirmation=overrides["use_confirmation"])
        if "use_dead_ends" in overrides:
            config = replace(config, use_dead_ends=overrides["use_dead_ends"])
        if "use_ranking" in overrides:
            config = replace(config, use_ranking=overrides["use_ranking"])
        if "use_reorganization" in overrides:
            config = replace(config, use_reorganization=overrides["use_reorganization"])
        result = run_search(objective, proposer, config)
        reported = result.champion.metric
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


def build_ablation_payload(rows: list[AblationRow], *, budget: int = DEFAULT_BUDGET) -> AblationPayload:
    """Add the manuscript's derived noise-inflation ratio to measured rows."""
    by_label = {row["configuration"]: row for row in rows}
    full = by_label["full coordination"]["noise_inflation"]
    without_confirmation = by_label["no confirmation"]["noise_inflation"]
    if full == 0:
        raise ValueError("full-coordination noise inflation is zero; ratio is undefined")
    return {
        "budget": budget,
        "noise_inflation_ratio_without_confirmation": without_confirmation / full,
        "rows": rows,
    }
