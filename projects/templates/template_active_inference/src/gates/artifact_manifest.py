"""Canonical required output artifact paths for gate validation."""

from __future__ import annotations

REQUIRED_OUTPUTS: tuple[str, ...] = (
    "output/data/parameter_sweep.csv",
    "output/data/si_tmaze_summary.json",
    "output/data/si_tmaze_trace.json",
    "output/data/analysis_statistics.json",
    "output/figures/ising_mi_curve.png",
    "output/figures/free_energy_curve.png",
    "output/figures/si_tmaze_actions.png",
    "output/figures/si_belief_entropy_curve.png",
    "output/figures/si_obs_action_trace.png",
    "output/figures/sheaf_layers_overview.png",
    "output/figures/sheaf_coverage_heatmap.png",
    "output/figures/invariant_dashboard.png",
    "output/figures/tmaze_schematic.png",
    "output/figures/multi_track_architecture.png",
    "output/figures/lean_boundary_status.png",
    "output/figures/gnn_ontology_concordance.png",
    "output/figures/figure_registry.json",
    "output/data/sheaf_coverage_matrix.json",
    "output/reports/invariants.json",
    "output/reports/si_invariants.json",
    "output/reports/si_tmaze_run_report.json",
)

REQUIRED_OUTPUT_CHECK_KEYS: tuple[str, ...] = (
    "output/data/parameter_sweep.csv",
    "output/data/analysis_statistics.json",
    "output/data/sheaf_coverage_matrix.json",
    "output/data/si_tmaze_summary.json",
    "output/figures/ising_mi_curve.png",
    "output/figures/sheaf_coverage_heatmap.png",
    "output/figures/sheaf_layers_overview.png",
    "output/figures/invariant_dashboard.png",
    "output/figures/figure_registry.json",
    "output/reports/si_invariants.json",
    "output/reports/si_tmaze_run_report.json",
)
