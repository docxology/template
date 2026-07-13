"""Source-owned publication analysis for the formal colony exemplar."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from template_formal.colony.demo import run_demo_colony, run_statistics_sweep
from template_formal.colony.stats import convergence_rate, wilson_score_interval
from template_formal.colony.visualization import (
    write_convergence_tick_histogram,
    write_demo_convergence_figure,
)

SWEEP_NUM_TRIALS = 40
SWEEP_SEED_BASE = 9000
SWEEP_CONFIG_KWARGS: dict[str, object] = {
    "num_agents": 8,
    "locations": ("north", "south"),
    "num_ticks": 30,
    "preference_mean_range": (8.0, 12.0),
    "preference_variance": 1.0,
    "sensing_noise_std": 0.5,
    "deposit_amount": 1.0,
    "decay": 0.46,
}


@dataclass(frozen=True)
class AnalysisArtifacts:
    """Complete artifact set produced by one publication-analysis run."""

    demo_summary: Path
    demo_databases: tuple[Path, ...]
    demo_figure: Path
    sweep_summary: Path
    sweep_figure: Path
    figure_registry: Path

    @property
    def paths(self) -> tuple[Path, ...]:
        """Return every reviewer-facing artifact in stable print order."""
        return (
            self.demo_summary,
            *self.demo_databases,
            self.demo_figure,
            self.sweep_summary,
            self.sweep_figure,
            self.figure_registry,
        )


def run_publication_analysis(project_root: Path) -> AnalysisArtifacts:
    """Run the real demo and sweep, then write all required publication artifacts."""
    output_dir = project_root / "output" / "data"
    figures_dir = project_root / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = run_demo_colony(output_dir)
    summary_path = output_dir / "colony_demo_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    demo_figure = write_demo_convergence_figure(
        summary,
        figures_dir,
        num_agents=summary["num_agents"],
        num_ticks=summary["num_ticks"],
    )
    if demo_figure is None:
        raise RuntimeError("required demo convergence figure was not generated")

    sweep_results = run_statistics_sweep(
        output_dir / "stats_sweep",
        num_trials=SWEEP_NUM_TRIALS,
        seed_base=SWEEP_SEED_BASE,
        config_kwargs=SWEEP_CONFIG_KWARGS,
    )
    outcomes = [result.converged for result in sweep_results]
    successes = sum(outcomes)
    lower, upper = wilson_score_interval(successes, len(sweep_results), confidence=0.95)
    sweep_summary = {
        "num_trials": SWEEP_NUM_TRIALS,
        "seed_base": SWEEP_SEED_BASE,
        "config": SWEEP_CONFIG_KWARGS,
        "successes": successes,
        "convergence_rate": convergence_rate(outcomes),
        "wilson_95_lower": lower,
        "wilson_95_upper": upper,
        "consensus_ticks": [result.consensus_tick for result in sweep_results],
    }
    sweep_summary_path = output_dir / "colony_statistics_sweep_summary.json"
    sweep_summary_path.write_text(json.dumps(sweep_summary, indent=2, sort_keys=True), encoding="utf-8")

    sweep_figure = write_convergence_tick_histogram(sweep_results, figures_dir)
    if sweep_figure is None:
        raise RuntimeError("required convergence-tick distribution figure was not generated")

    registry = {
        "fig:demo-convergence": {
            "label": "fig:demo-convergence",
            "filename": demo_figure.name,
            "caption": (
                "Deterministic demo colony: pheromone concentration and winner "
                "share over 5 ticks (guaranteed by construction, not emergence)."
            ),
            "section": "Colony convergence",
            "generated_by": "template_formal.colony.visualization.write_demo_convergence_figure",
        },
        "fig:convergence-tick-distribution": {
            "label": "fig:convergence-tick-distribution",
            "filename": sweep_figure.name,
            "caption": (
                f"Consensus-tick distribution across {SWEEP_NUM_TRIALS} heterogeneous, "
                "noisy trials -- the earned statistical result."
            ),
            "section": "Colony convergence",
            "generated_by": "template_formal.colony.visualization.write_convergence_tick_histogram",
        },
    }
    figures_dir.mkdir(parents=True, exist_ok=True)
    registry_path = figures_dir / "figure_registry.json"
    registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True), encoding="utf-8")

    return AnalysisArtifacts(
        demo_summary=summary_path,
        demo_databases=tuple(Path(path) for path in summary["agent_db_paths"]),
        demo_figure=demo_figure,
        sweep_summary=sweep_summary_path,
        sweep_figure=sweep_figure,
        figure_registry=registry_path,
    )


__all__ = [
    "AnalysisArtifacts",
    "SWEEP_CONFIG_KWARGS",
    "SWEEP_NUM_TRIALS",
    "SWEEP_SEED_BASE",
    "run_publication_analysis",
]
