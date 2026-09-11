"""The AutoScientists coordination loop and its experiment machinery: the
propose→evaluate→confirm→promote→reorganize loop, matched-budget comparison,
effect-size ranking, the single-mechanism ablation matrix, the dead-end
registry, and stagnation-driven team reorganization."""

from .ablation import (
    ABLATIONS,
    AblationPayload,
    AblationRow,
    DEFAULT_BUDGET,
    build_ablation_payload,
    run_ablations,
)
from .comparison import (
    RunSummary,
    build_comparison_payload,
    build_objective,
    run_comparison,
    summarize_run,
)
from .dead_ends import DeadEnd, DeadEndRegistry
from .ranking import axis_effect_sizes, rank_axes
from .search import SearchConfig, SearchResult, run_search
from .stagnation import StagnationDetector, reorganize_axes

__all__ = [
    "ABLATIONS",
    "AblationPayload",
    "AblationRow",
    "DEFAULT_BUDGET",
    "DeadEnd",
    "DeadEndRegistry",
    "RunSummary",
    "SearchConfig",
    "SearchResult",
    "StagnationDetector",
    "axis_effect_sizes",
    "build_ablation_payload",
    "build_comparison_payload",
    "build_objective",
    "rank_axes",
    "reorganize_axes",
    "run_ablations",
    "run_comparison",
    "run_search",
    "summarize_run",
]
