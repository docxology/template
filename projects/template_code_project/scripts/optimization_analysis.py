#!/usr/bin/env python3
"""Compatibility wrapper for the code-project optimization analysis."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for _path in (PROJECT_ROOT, PROJECT_ROOT / "src", PROJECT_ROOT.parent.parent):
    path_text = str(_path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

from src.analysis import (  # noqa: E402,F401
    INFRASTRUCTURE_AVAILABLE,
    extract_optimization_metadata,
    generate_citations_from_metadata,
    main,
    register_figure,
    run_convergence_experiment,
    run_performance_benchmarking,
    run_stability_analysis,
    save_optimization_results,
    save_publishing_materials,
    save_validation_report,
    validate_generated_outputs,
)
from src.figures import (  # noqa: E402,F401
    VIZ_CONFIG,
    apply_visualization_style,
    generate_benchmark_visualization,
    generate_complexity_visualization,
    generate_convergence_plot,
    generate_convergence_rate_plot,
    generate_stability_visualization,
    generate_step_size_sensitivity_plot,
)

__all__ = [
    "INFRASTRUCTURE_AVAILABLE",
    "VIZ_CONFIG",
    "apply_visualization_style",
    "extract_optimization_metadata",
    "generate_benchmark_visualization",
    "generate_citations_from_metadata",
    "generate_complexity_visualization",
    "generate_convergence_plot",
    "generate_convergence_rate_plot",
    "generate_stability_visualization",
    "generate_step_size_sensitivity_plot",
    "main",
    "register_figure",
    "run_convergence_experiment",
    "run_performance_benchmarking",
    "run_stability_analysis",
    "save_optimization_results",
    "save_publishing_materials",
    "save_validation_report",
    "validate_generated_outputs",
]


if __name__ == "__main__":
    main()
