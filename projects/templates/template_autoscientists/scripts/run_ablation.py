#!/usr/bin/env python3
"""Thin orchestrator: per-mechanism ablation of the coordination loop.

Reproduces the paper's "remove one component" study. Starting from the full
coordinated configuration, each mechanism (confirmation, dead-end registry,
effect-size ranking, stagnation reorganization) is switched off in turn and the
resulting final champion metric is compared against the full configuration. All
computation lives in ``src``; this script only orchestrates and writes outputs.
"""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]
for path in (PROJECT_ROOT, PROJECT_ROOT / "src", REPO_ROOT):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from src import DeterministicProposer, SearchConfig, SyntheticObjective, run_search  # noqa: E402
from src.figures import AblationRow, write_ablation_figure, write_efficiency_figure  # noqa: E402

BUDGET = 60

ABLATIONS: tuple[tuple[str, dict[str, bool]], ...] = (
    ("full coordination", {}),
    ("no confirmation", {"use_confirmation": False}),
    ("no dead-end registry", {"use_dead_ends": False}),
    ("no effect-size ranking", {"use_ranking": False}),
    ("no reorganization", {"use_reorganization": False}),
)


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


def main() -> int:
    rows = _run_ablations()

    figures_dir = PROJECT_ROOT / "output" / "figures"
    data_dir = PROJECT_ROOT / "output" / "data"
    figures_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    figure_path = figures_dir / "ablation.png"
    efficiency_path = figures_dir / "ablation_efficiency.png"
    data_path = data_dir / "ablation.json"
    write_ablation_figure(rows, figure_path)
    write_efficiency_figure(rows, efficiency_path)
    data_path.write_text(json.dumps({"budget": BUDGET, "rows": rows}, indent=2, sort_keys=True) + "\n")

    print(figure_path)
    print(efficiency_path)
    print(data_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
