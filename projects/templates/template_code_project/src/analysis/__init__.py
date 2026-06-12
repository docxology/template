"""Optimization analysis package (re-export barrel)."""

from __future__ import annotations

import logging

from ._infra import (
    INFRASTRUCTURE_AVAILABLE,
    ProgressBar,
    ScriptExecutionError,
    SystemHealthChecker,
    TemplateError,
    benchmark_function,
    check_numerical_stability,
    log_success,
    verify_output_integrity,
)
from ._logging import _setup_fallback_logging, get_logger as _get_logger
from ..project_paths import _DEFAULT_ROOT as project_root
from .pipeline import (
    extract_optimization_metadata,
    generate_citations_from_metadata,
    register_figure,
    run_convergence_experiment,
    run_performance_benchmarking,
    run_stability_analysis,
    save_optimization_results,
    save_publishing_materials,
    save_validation_report,
    validate_generated_outputs,
)
from .scientific_reports import _benchmark_timings, _stability_score_from_runs
from .workflow import main, run_analysis_pipeline

if not INFRASTRUCTURE_AVAILABLE:

    def log_success(message: str, logger: logging.Logger | None = None) -> None:
        return None


__all__ = [
    "INFRASTRUCTURE_AVAILABLE",
    "ProgressBar",
    "ScriptExecutionError",
    "SystemHealthChecker",
    "TemplateError",
    "_benchmark_timings",
    "_get_logger",
    "_setup_fallback_logging",
    "_stability_score_from_runs",
    "benchmark_function",
    "check_numerical_stability",
    "extract_optimization_metadata",
    "generate_citations_from_metadata",
    "log_success",
    "main",
    "project_root",
    "register_figure",
    "run_analysis_pipeline",
    "run_convergence_experiment",
    "run_performance_benchmarking",
    "run_stability_analysis",
    "save_optimization_results",
    "save_publishing_materials",
    "save_validation_report",
    "validate_generated_outputs",
    "verify_output_integrity",
]
