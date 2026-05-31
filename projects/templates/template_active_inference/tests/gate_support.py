"""Shared artifact bootstrap for gate validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from analysis import run_analysis, write_analysis_statistics
from manuscript.variables import generate_variables
from manuscript.hydrate import write_resolved_manuscript
from manuscript.sheaf import compose_all_sections
from manuscript.sheaf.semantic import write_semantic_gluing_outputs
from orchestration.coverage_pipeline import ensure_coverage_artifacts
from simulation.graph_world import write_graph_world_artifacts
from simulation.si_artifacts import write_policy_comparison
from simulation.si_runner import pymdp_available, run_and_persist
from validation_spine import write_validation_spine_artifacts
from visualizations.animation import write_belief_trajectory_gif
from visualizations.figures import generate_all_figures


def ensure_gate_artifacts(project_root: Path) -> None:
    """Rebuild analysis, simulation, sheaf, and figure outputs for gate checks."""
    run_analysis(project_root)
    if pymdp_available():
        run_and_persist(project_root)
        write_policy_comparison(project_root)
    else:
        pytest.skip("pymdp not installed")
    write_graph_world_artifacts(project_root)
    write_analysis_statistics(project_root)
    compose_all_sections(project_root)
    ensure_coverage_artifacts(project_root, write_page=True, render_heatmap=True, force=True)
    generate_all_figures(project_root)
    write_belief_trajectory_gif(project_root)
    write_validation_spine_artifacts(project_root)
    variables = generate_variables(project_root, require_analysis_outputs=False)
    out = project_root / "output" / "data" / "manuscript_variables.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    import json

    out.write_text(json.dumps(variables, indent=2), encoding="utf-8")
    write_semantic_gluing_outputs(project_root)
    write_resolved_manuscript(project_root, variables)
