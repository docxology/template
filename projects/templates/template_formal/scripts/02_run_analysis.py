#!/usr/bin/env python3
"""Thin orchestrator for a demo ant-robot colony run plus a statistics sweep.

All business logic lives in ``src/template_formal``: this script only wires
up real on-disk paths, calls :mod:`template_formal.colony.demo` /
:mod:`template_formal.colony.visualization`, writes small JSON summaries and
the figure registry, and prints the output paths it produced (for manifest
collection, mirroring `template_code_project/scripts/optimization_analysis.py`).

Two independent real runs, not one:

1. **Deterministic demo colony**: three identical agents, five ticks, no
   seeded variation -- the "guaranteed by construction" mechanism
   demonstration @sec:results-discussion already scopes honestly as "not
   emergence."
2. **Statistics sweep**: a modest N=40 batch of real, seeded,
   heterogeneous-preference/noisy-sensing trials via
   :func:`template_formal.colony.demo.run_statistics_sweep` -- the same real
   harness `tests/colony/test_colony_convergence_statistics.py` uses at
   N=150, just small enough to stay fast in a demo script.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for _path in (PROJECT_ROOT, PROJECT_ROOT / "src", PROJECT_ROOT.parents[2]):
    path_text = str(_path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

from template_formal.colony.demo import run_demo_colony, run_statistics_sweep  # noqa: E402
from template_formal.colony.stats import convergence_rate, wilson_score_interval  # noqa: E402
from template_formal.colony.visualization import (  # noqa: E402
    write_convergence_tick_histogram,
    write_demo_convergence_figure,
)

# Statistics-sweep configuration. Deliberately the same real-world regime as
# `tests/colony/test_colony_convergence_statistics.py`'s calibrated N=150
# config (8 heterogeneous agents, sensing noise, decay=0.46) so this demo's
# figure is a real, honest (if smaller and noisier) echo of that test's
# claim -- not an unrelated toy configuration. N=40 (not N=150) keeps this
# script's own wall-clock cost low (~2-3s locally, versus ~9s at N=150).
_SWEEP_NUM_TRIALS = 40
_SWEEP_SEED_BASE = 9000
_SWEEP_CONFIG_KWARGS: dict[str, object] = {
    "num_agents": 8,
    "locations": ("north", "south"),
    "num_ticks": 30,
    "preference_mean_range": (8.0, 12.0),
    "preference_variance": 1.0,
    "sensing_noise_std": 0.5,
    "deposit_amount": 1.0,
    "decay": 0.46,
}


def main() -> int:
    output_dir = PROJECT_ROOT / "output" / "data"
    figures_dir = PROJECT_ROOT / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Deterministic demo colony.
    summary = run_demo_colony(output_dir)

    summary_path = output_dir / "colony_demo_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print(str(summary_path))
    for db_path in summary["agent_db_paths"]:  # type: ignore[union-attr]
        print(db_path)

    demo_figure_path = write_demo_convergence_figure(
        summary,
        figures_dir,
        num_agents=summary["num_agents"],
        num_ticks=summary["num_ticks"],  # type: ignore[arg-type]
    )
    if demo_figure_path is None:
        raise RuntimeError("required demo convergence figure was not generated")
    print(str(demo_figure_path))

    # 2. Real statistics sweep: a modest N=40 heterogeneous/noisy batch.
    sweep_db_dir = output_dir / "stats_sweep"
    sweep_results = run_statistics_sweep(
        sweep_db_dir, num_trials=_SWEEP_NUM_TRIALS, seed_base=_SWEEP_SEED_BASE, config_kwargs=_SWEEP_CONFIG_KWARGS
    )
    outcomes = [result.converged for result in sweep_results]
    successes = sum(1 for outcome in outcomes if outcome)
    rate = convergence_rate(outcomes)
    lower, upper = wilson_score_interval(successes, len(sweep_results), confidence=0.95)

    sweep_summary = {
        "num_trials": _SWEEP_NUM_TRIALS,
        "seed_base": _SWEEP_SEED_BASE,
        "config": _SWEEP_CONFIG_KWARGS,
        "successes": successes,
        "convergence_rate": rate,
        "wilson_95_lower": lower,
        "wilson_95_upper": upper,
        "consensus_ticks": [result.consensus_tick for result in sweep_results],
    }
    sweep_summary_path = output_dir / "colony_statistics_sweep_summary.json"
    sweep_summary_path.write_text(json.dumps(sweep_summary, indent=2, sort_keys=True), encoding="utf-8")
    print(str(sweep_summary_path))

    histogram_path = write_convergence_tick_histogram(sweep_results, figures_dir)
    if histogram_path is None:
        raise RuntimeError("required convergence-tick distribution figure was not generated")
    print(str(histogram_path))

    # Figure registry: infrastructure.validation's figure_validator checks every
    # {#fig:...} label referenced in manuscript/*.md against this file. Written
    # here (not hand-maintained) so it always reflects what this script actually
    # generated -- an unregistered or stale entry would mean the script and the
    # manuscript have drifted apart.
    registry: dict[str, dict[str, object]] = {
        "fig:demo-convergence": {
            "label": "fig:demo-convergence",
            "filename": demo_figure_path.name,
            "caption": (
                "Deterministic demo colony: pheromone concentration and winner "
                "share over 5 ticks (guaranteed by construction, not emergence)."
            ),
            "section": "Colony convergence",
            "generated_by": "template_formal.colony.visualization.write_demo_convergence_figure",
        },
        "fig:convergence-tick-distribution": {
            "label": "fig:convergence-tick-distribution",
            "filename": histogram_path.name,
            "caption": (
                f"Consensus-tick distribution across {_SWEEP_NUM_TRIALS} heterogeneous, "
                "noisy trials -- the earned statistical result."
            ),
            "section": "Colony convergence",
            "generated_by": "template_formal.colony.visualization.write_convergence_tick_histogram",
        },
    }
    figures_dir.mkdir(parents=True, exist_ok=True)
    registry_path = figures_dir / "figure_registry.json"
    registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True), encoding="utf-8")
    print(str(registry_path))

    return 0


if __name__ == "__main__":
    sys.exit(main())
