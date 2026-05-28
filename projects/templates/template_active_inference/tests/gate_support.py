"""Shared artifact bootstrap for gate validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from analysis import run_analysis, write_analysis_statistics
from manuscript.sheaf import compose_all_sections
from orchestration.coverage_pipeline import ensure_coverage_artifacts
from simulation.si_runner import pymdp_available, run_and_persist
from visualizations.figures import generate_all_figures


def ensure_gate_artifacts(project_root: Path) -> None:
    """Rebuild analysis, simulation, sheaf, and figure outputs for gate checks."""
    run_analysis(project_root)
    if pymdp_available():
        run_and_persist(project_root)
    else:
        pytest.skip("pymdp not installed")
    write_analysis_statistics(project_root)
    compose_all_sections(project_root)
    ensure_coverage_artifacts(project_root, write_page=True, render_heatmap=True, force=True)
    generate_all_figures(project_root)
