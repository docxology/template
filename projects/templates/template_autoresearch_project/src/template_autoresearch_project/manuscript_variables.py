"""Render-time manuscript variables for the AutoResearch exemplar."""

from __future__ import annotations

from .manuscript.manuscript_tokens_core import (
    compute_variables,
    compute_variables_and_provenance,
    compute_variables_from_payload,
    save_variable_provenance,
    save_variables,
    validate_manuscript_source_values,
    write_manuscript_hydration_artifacts,
)
from .manuscript.manuscript_tokens_figures import save_figure_blocks
from .manuscript.manuscript_tokens_ml import compute_ml_variables

__all__ = [
    "compute_ml_variables",
    "compute_variables",
    "compute_variables_and_provenance",
    "compute_variables_from_payload",
    "save_figure_blocks",
    "save_variable_provenance",
    "save_variables",
    "validate_manuscript_source_values",
    "write_manuscript_hydration_artifacts",
]
