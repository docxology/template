"""Deterministic AutoResearch exemplar project."""

from .config import (
    AutoResearchLoopConfig,
    ManuscriptLoopSettings,
    ResearchQuestion,
    build_loop_config,
    load_loop_config,
    load_manuscript_loop_settings,
)
from .loop import run_autoresearch_loop
from .manuscript_variables import compute_variables, save_variables
from .ml_task import MLTaskResult, run_bounded_ml_task
from .models import AutoResearchClaim, AutoResearchLoopResult, LoopStageResult

__all__ = [
    "AutoResearchClaim",
    "AutoResearchLoopConfig",
    "AutoResearchLoopResult",
    "LoopStageResult",
    "ManuscriptLoopSettings",
    "MLTaskResult",
    "ResearchQuestion",
    "build_loop_config",
    "compute_variables",
    "load_loop_config",
    "load_manuscript_loop_settings",
    "run_bounded_ml_task",
    "run_autoresearch_loop",
    "save_variables",
]
