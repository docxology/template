"""Composable analysis pipeline steps (orchestration lives in scripts/optimization_analysis.py)."""

from __future__ import annotations

from .experiments import run_convergence_experiment, save_optimization_results
from .publishing import (
    extract_optimization_metadata,
    generate_citations_from_metadata,
    save_publishing_materials,
)
from .scientific_reports import (
    register_figure,
    run_performance_benchmarking,
    run_stability_analysis,
    save_validation_report,
    validate_generated_outputs,
)

__all__ = [
    "extract_optimization_metadata",
    "generate_citations_from_metadata",
    "register_figure",
    "run_convergence_experiment",
    "run_performance_benchmarking",
    "run_stability_analysis",
    "save_optimization_results",
    "save_publishing_materials",
    "save_validation_report",
    "validate_generated_outputs",
]
