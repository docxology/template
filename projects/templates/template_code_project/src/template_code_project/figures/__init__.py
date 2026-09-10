"""Figure generators for the template_code_project exemplar (re-export barrel)."""

from __future__ import annotations

from ..project_paths import _DEFAULT_ROOT as project_root
from ..viz_config import VIZ_CONFIG, agency_category, apply_visualization_style
from .convergence import generate_convergence_plot, generate_convergence_rate_plot
from .scientific import (
    generate_benchmark_visualization,
    generate_complexity_visualization,
    generate_stability_visualization,
)
from .sensitivity import generate_step_size_sensitivity_plot

# Backward-compatible alias used by legacy imports/tests.
_agency_category = agency_category

__all__ = [
    "VIZ_CONFIG",
    "_agency_category",
    "apply_visualization_style",
    "generate_benchmark_visualization",
    "generate_complexity_visualization",
    "generate_convergence_plot",
    "generate_convergence_rate_plot",
    "generate_stability_visualization",
    "generate_step_size_sensitivity_plot",
    "project_root",
]
