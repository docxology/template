"""A typed shared pheromone-field substrate, accessed only through a narrow Protocol."""

from template_formal.colony.analysis import AnalysisArtifacts, run_publication_analysis
from template_formal.colony.demo import run_demo_colony, run_statistics_sweep
from template_formal.colony.experiment import (
    ColonyTrialConfig,
    ColonyTrialResult,
    find_sustained_consensus_tick,
    run_colony_trial,
)
from template_formal.colony.nullmodel import NullModelTrialConfig, NullModelTrialResult, run_null_model_trial
from template_formal.colony.pheromone import InMemoryPheromoneField, PheromoneField
from template_formal.colony.stats import (
    ConsensusTickSummary,
    EmptySummaryError,
    cochran_armitage_trend_test,
    consensus_tick_summary,
    convergence_rate,
    fisher_exact_test_two_sided,
    pearson_r,
    wilson_score_interval,
)
from template_formal.colony.sweep import SweepPointResult, run_parameter_sweep
from template_formal.colony.visualization import write_convergence_tick_histogram, write_demo_convergence_figure

__all__ = [
    "ColonyTrialConfig",
    "ColonyTrialResult",
    "AnalysisArtifacts",
    "ConsensusTickSummary",
    "EmptySummaryError",
    "InMemoryPheromoneField",
    "NullModelTrialConfig",
    "NullModelTrialResult",
    "PheromoneField",
    "SweepPointResult",
    "cochran_armitage_trend_test",
    "consensus_tick_summary",
    "convergence_rate",
    "find_sustained_consensus_tick",
    "fisher_exact_test_two_sided",
    "pearson_r",
    "run_colony_trial",
    "run_demo_colony",
    "run_null_model_trial",
    "run_parameter_sweep",
    "run_publication_analysis",
    "run_statistics_sweep",
    "wilson_score_interval",
    "write_convergence_tick_histogram",
    "write_demo_convergence_figure",
]
