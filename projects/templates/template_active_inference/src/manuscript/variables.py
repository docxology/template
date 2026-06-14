"""Manuscript variable generation from measured project outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from analytical.hyperparameters import load_hyperparameters
from analytical.sweep_io import read_parameter_sweep
from gnn.concordance import BERNOULLI_EXPECTED_TERMS
from manuscript.invariant_counts import load_invariant_counts
from simulation.pymdp_config import load_pymdp_config


def _ising_mi_saturation_from_sweep(sweep_rows: list[dict[str, float]]) -> float:
    """Maximum closed-form MI on the measured λ grid (nats)."""
    if not sweep_rows:
        return 0.0
    return max(row["closed_form_mi"] for row in sweep_rows)


def _free_energy_argmin_lambda(hp: Any) -> float:
    """λ minimizing free energy of the entangled posterior vs the mean-field prior.

    Deterministic and model-derived (no sampling): replicates the curve drawn by
    ``figure_free_energy_curve`` so the prose argmin and the figure marker share one
    source of truth. Returns the grid λ at the minimum, rounded to the grid precision.
    """
    import numpy as np

    from analytical.bernoulli_toy import ising_coupling, ising_joint_posterior, symmetric_mean_field_prior
    from analytical.decomposition import free_energy_against_entangled_prior
    from analytical.hyperparameters import lambda_grid

    lambdas = lambda_grid(hp)
    if not lambdas:
        return 0.0
    mf = symmetric_mean_field_prior()
    g0 = [np.zeros(2), np.zeros(2)]
    j = ising_coupling()
    kc = np.zeros((2, 2))
    values = [
        free_energy_against_entangled_prior(ising_joint_posterior(float(lam)), mf, g0, j, kc, gamma=1.0, lam=float(lam))
        for lam in lambdas
    ]
    return round(float(lambdas[int(np.argmin(values))]), 4)


def _policy_goal_counts_by_mode(policy_data: dict[str, Any]) -> dict[str, int]:
    """Goal-reaching run counts split by inference mode from si_policy_comparison runs.

    Makes the "too small for sophisticated inference to win" claim measurable rather
    than asserted: each mode's goal count is read from the deterministic comparison runs.
    """
    counts = {"state_inference": 0, "policy_inference": 0}
    for run in policy_data.get("runs") or []:
        mode = run.get("mode")
        if mode in counts and bool(run.get("goal_reached")):
            counts[mode] += 1
    return counts


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data


def _pipeline_track_count(project_root: Path) -> int:
    """Required pipeline tracks from ``tracks.yaml`` (distinct from ``sheaf_track_count``)."""
    tracks_path = project_root / "tracks.yaml"
    if not tracks_path.is_file():
        return 0
    raw = yaml.safe_load(tracks_path.read_text(encoding="utf-8")) or {}
    tracks = raw.get("tracks") or []
    return sum(1 for track in tracks if track.get("required", True))


def _gnn_spec_version(project_root: Path) -> str:
    path = project_root / "gnn" / "bernoulli_toy.gnn.md"
    if not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    for idx, line in enumerate(lines):
        if line.strip() != "## GNNVersionAndFlags":
            continue
        for follow in lines[idx + 1 :]:
            text = follow.strip()
            if not text:
                continue
            return text
    return ""


def _efe_token_values() -> dict[str, Any]:
    """Manuscript tokens for the closed-form Expected Free Energy decomposition.

    Computed directly from the finite T-maze generative model (deterministic, no
    sampling), so the hydrated numbers are reproducible and back the Results prose.
    """
    from simulation.efe_decomposition import decompose_all_policies
    from simulation.tmaze_model import build_tmaze_generative_model

    result = decompose_all_policies(build_tmaze_generative_model())
    best_policy = result["efe_minimizing_policy"]
    best_row = next(row for row in result["rows"] if row["policy"] == best_policy)
    return {
        "efe_policy_count": int(result["policy_count"]),
        "efe_minimizing_policy": "".join(str(a) for a in best_policy),
        "efe_minimizing_total_formatted": f"{result['efe_minimizing_total']:.4f}",
        "efe_risk_at_min_formatted": f"{best_row['risk']:.4f}",
        "efe_ambiguity_at_min_formatted": f"{best_row['ambiguity']:.4f}",
        "efe_pragmatic_at_min_formatted": f"{best_row['pragmatic_value']:.4f}",
        "efe_epistemic_at_min_formatted": f"{best_row['epistemic_value']:.4f}",
        "efe_max_identity_residual_formatted": f"{result['max_identity_residual']:.1e}",
    }


def _precision_token_values() -> dict[str, Any]:
    """Manuscript tokens for the closed-form precision (gamma) sweep.

    Computed directly from the finite T-maze policy posterior (deterministic, no
    sampling), so the hydrated numbers are reproducible and back the Results prose.
    """
    from simulation.precision_sweep import sweep_precision
    from simulation.tmaze_model import build_tmaze_generative_model

    result = sweep_precision(build_tmaze_generative_model())
    gamma_det = result["gamma_deterministic_selection"]
    return {
        "precision_gamma_grid_points": int(result["gamma_grid_points"]),
        "precision_gamma_max": f"{result['gamma_max']:g}",
        "precision_optimal_set_size": int(result["optimal_set_size"]),
        "precision_entropy_at_gamma_one_formatted": f"{result['entropy_at_gamma_one']:.4f}",
        "precision_entropy_floor_formatted": f"{result['entropy_floor']:.4f}",
        "precision_selection_threshold": f"{result['selection_mass_threshold']:g}",
        "precision_gamma_deterministic": ("never" if gamma_det is None else f"{gamma_det:g}"),
    }


def _cue_tmaze_token_values() -> dict[str, Any]:
    """Manuscript tokens for the cue-then-reward T-maze epistemic-necessity result.

    Computed in closed form from the finite cue generative model (deterministic, no
    sampling), so the hydrated numbers reproduce and back the Results prose.
    """
    from simulation.cue_tmaze_model import cue_advantage_summary

    summary = cue_advantage_summary()
    return {
        "cue_information_gain_formatted": f"{summary['cue_information_gain']:.4f}",
        "cue_behavioral_advantage_formatted": f"{summary['behavioral_advantage']:.4f}",
        "cue_epistemic_reward_formatted": f"{summary['epistemic_reward_log_pref']:.4f}",
        "cue_greedy_reward_formatted": f"{summary['greedy_reward_log_pref']:.4f}",
        "cue_flat_efe_indistinguishable": "identical" if summary["flat_efe_indistinguishable"] else "distinct",
        "cue_num_states": int(summary["num_states"]),
    }


def _dirichlet_token_values() -> dict[str, Any]:
    """Manuscript tokens for the deterministic Dirichlet likelihood-learning run.

    Computed in closed form from the finite T-maze model (no sampling), so the
    hydrated numbers are reproducible and back the Results prose.
    """
    from simulation.dirichlet_learning import summarize_learning
    from simulation.tmaze_model import build_tmaze_generative_model

    summary = summarize_learning(build_tmaze_generative_model())
    return {
        "dirichlet_steps_to_converge": int(summary["steps_to_converge"]),
        "dirichlet_final_kl_formatted": f"{summary['final_kl']:.2e}",
        "dirichlet_initial_kl_formatted": f"{summary['initial_kl']:.4f}",
    }


VARIABLE_ARTIFACTS: dict[str, str] = {
    "policy": "output/data/si_policy_comparison.json",
    "posterior": "output/data/pymdp_policy_posterior_grid.json",
    "runtime": "output/reports/pymdp_runtime_diagnostics.json",
    "graph": "output/data/si_graph_world_summary.json",
    "graph_topology_traces": "output/data/si_graph_world_topology_traces.json",
    "provenance": "output/data/artifact_provenance.json",
    "replay": "output/reports/reproducibility_replay.json",
    "counterexample": "output/reports/counterexample_matrix.json",
    "sensitivity": "output/data/sensitivity_sweep.json",
    "uncertainty": "output/data/uncertainty_summary.json",
    "benchmark": "output/data/toy_benchmark_matrix.json",
    "model_checking": "output/reports/model_checking_witnesses.json",
    "lean_graph": "output/reports/lean_graph_world_inventory.json",
    "interop": "output/data/interop_roundtrip_report.json",
    "adversarial": "output/reports/adversarial_audit.json",
    "semantic": "output/data/sheaf_gluing_certificate.json",
    "dependency": "output/data/validation_dependency_graph.json",
    "stale": "output/reports/stale_artifact_report.json",
    "manuscript_staleness": "output/reports/manuscript_staleness_report.json",
    "figure_source": "output/data/figure_source_map.json",
    "visualization_quality": "output/reports/visualization_quality_audit.json",
    "statistical_bridge": "output/data/statistical_visualization_bridge.json",
    "scope": "output/reports/scope_boundary_audit.json",
    "gate_index": "output/data/validation_gate_index.json",
    "section_status": "output/data/sheaf_section_status_matrix.json",
    "render_log": "output/reports/sheaf_render_log.json",
    "claim_audit": "output/reports/claim_evidence_audit.json",
    "token_provenance": "output/data/manuscript_token_provenance.json",
    "cross_symbol": "output/data/cross_track_symbol_table.json",
    "assumption": "output/data/analytical_assumption_index.json",
    "animation_delta": "output/data/animation_frame_deltas.json",
    "replay_matrix": "output/reports/replay_matrix.json",
    "track_lane": "output/data/track_lane_matrix.json",
    "artifact_contract": "output/data/artifact_contract_index.json",
    "track_scope": "output/data/track_improvement_scope.json",
    "blocked_scope": "output/reports/blocked_scope_manifest.json",
    "evidence_fields": "output/data/evidence_field_index.json",
    "release_bundle": "output/reports/release_bundle_manifest.json",
    "theorem_traceability": "output/data/theorem_traceability_matrix.json",
    "artifact_diffoscope": "output/reports/artifact_diffoscope.json",
    "proof_extraction": "output/data/proof_extraction_index.json",
    "state_space_catalog": "output/data/state_space_catalog.json",
    "causal_ablation": "output/data/causal_ablation_matrix.json",
    "artifact_license": "output/reports/artifact_license_audit.json",
    "release_notes": "output/reports/release_notes_evidence.json",
    "scholarship": "output/data/scholarship_source_matrix.json",
    "security_posture": "output/reports/security_posture_audit.json",
    "proof_dependency": "output/data/proof_dependency_graph.json",
    "state_transition": "output/data/state_transition_table.json",
    "ablation_sensitivity": "output/reports/ablation_sensitivity_report.json",
    "release_attestation": "output/reports/release_attestation.json",
}


def _load_variable_artifacts(root: Path) -> dict[str, dict[str, Any]]:
    """Load optional generated artifacts used by manuscript tokens."""
    return {name: _load_json(root / rel_path) for name, rel_path in VARIABLE_ARTIFACTS.items()}


def _core_token_values(ctx: dict[str, Any]) -> dict[str, Any]:
    """Return project, analytical, invariant, and structural manuscript tokens."""
    root = ctx["root"]
    hp = ctx["hp"]
    pymdp_cfg = ctx["pymdp_cfg"]
    sweep_rows = ctx["sweep_rows"]
    return {
        "project_name": root.name,
        "lambda_grid_points": hp.lambda_grid_points,
        "lambda_max": hp.lambda_max,
        "bernoulli_state_count": hp.bernoulli_state_count,
        "gnn_spec_version": _gnn_spec_version(root),
        "pymdp_horizon": pymdp_cfg.horizon,
        "random_seed": pymdp_cfg.random_seed,
        "param_sweep_grid_points": len(sweep_rows) or hp.lambda_grid_points,
        "ising_mi_saturation": _ising_mi_saturation_from_sweep(sweep_rows),
        "free_energy_argmin_lambda": _free_energy_argmin_lambda(hp),
        "bernoulli_ontology_term_count": len(BERNOULLI_EXPECTED_TERMS),
        "invariants_passed": ctx["inv_passed"],
        "invariants_total": ctx["inv_total"],
        "sweep_max_residual": ctx["sweep_stats"].get("max_residual", 0.0),
        "sweep_rmse_mi": ctx["sweep_stats"].get("rmse_mi", 0.0),
        "pipeline_track_count": _pipeline_track_count(root),
        **ctx["counts"],
    }


def _simulation_token_values(ctx: dict[str, Any]) -> dict[str, Any]:
    """Return SI, PyMDP runtime, posterior, and graph-world manuscript tokens."""
    si_data = ctx["si_data"]
    si_stats = ctx["si_stats"]
    stats_data = ctx["stats_data"]
    pymdp_cfg = ctx["pymdp_cfg"]
    policy_summary = ctx["policy_summary"]
    policy_goal_by_mode = ctx["policy_goal_by_mode"]
    posterior_data = ctx["posterior_data"]
    runtime_data = ctx["runtime_data"]
    graph_data = ctx["graph_data"]
    graph_topology_traces = ctx["graph_topology_traces"]
    mean_entropy = ctx["mean_entropy"]
    return {
        "si_tmaze_steps": si_data.get("steps", si_stats.get("steps", 0)),
        "si_tmaze_policy_len": si_data.get("policy_len", pymdp_cfg.policy_len),
        "si_tmaze_mean_belief_entropy": mean_entropy,
        "si_tmaze_mean_belief_entropy_formatted": f"{mean_entropy:.4f}",
        "si_goal_reached": int(bool(si_data.get("goal_reached", si_stats.get("goal_reached", False)))),
        "si_action_diversity": si_data.get("action_diversity", si_stats.get("action_diversity", 0)),
        "si_action_switch_count": si_stats.get("action_switch_count", 0),
        "si_action_switch_rate_formatted": f"{float(si_stats.get('action_switch_rate', 0.0)):.3f}",
        "si_observation_diversity": si_stats.get("observation_diversity", 0),
        "si_entropy_initial": si_stats.get("entropy_initial", 0.0),
        "si_entropy_terminal": si_stats.get("entropy_terminal", 0.0),
        "si_entropy_drop": si_stats.get("entropy_drop", 0.0),
        "si_entropy_drop_formatted": f"{float(si_stats.get('entropy_drop', 0.0)):.4f}",
        "si_trace_steps_match": bool(si_stats.get("trace_summary_steps_match", False)),
        "si_trace_finite": bool(si_stats.get("finite_trace", False)),
        "si_entropy_min": si_stats.get("entropy_min", 0.0),
        "si_entropy_max": si_stats.get("entropy_max", 0.0),
        "pymdp_mode": stats_data.get("pymdp_mode", si_data.get("mode", pymdp_cfg.mode)),
        "pymdp_config_hash": stats_data.get("pymdp_config_hash", si_data.get("config_hash", "")),
        "si_policy_comparison_run_count": policy_summary.get("run_count", 0),
        "si_policy_comparison_goal_reached_count": policy_summary.get("goal_reached_count", 0),
        "si_policy_comparison_state_goal_count": policy_goal_by_mode["state_inference"],
        "si_policy_comparison_policy_goal_count": policy_goal_by_mode["policy_inference"],
        "si_policy_comparison_complete_grid": int(bool(policy_summary.get("complete_grid", False))),
        "si_policy_efe_rows_explained": int(bool(policy_summary.get("all_efe_rows_explained", False))),
        **_efe_token_values(),
        **_precision_token_values(),
        **_cue_tmaze_token_values(),
        **_dirichlet_token_values(),
        "pymdp_policy_posterior_row_count": posterior_data.get("row_count", 0),
        "pymdp_policy_posterior_available_count": posterior_data.get("available_row_count", 0),
        "pymdp_policy_posteriors_normalized": int(
            bool(posterior_data.get("all_available_posteriors_normalized", False))
        ),
        "pymdp_runtime_known_warning_count": runtime_data.get("known_warning_count", 0),
        "pymdp_runtime_unexpected_warning_count": runtime_data.get("unexpected_warning_count", 0),
        "pymdp_runtime_construction_count": runtime_data.get("construction_count", 0),
        "si_graph_world_steps": graph_data.get("steps", 0),
        "si_graph_world_node_count": graph_data.get("node_count", 0),
        "si_graph_world_goal_reached": int(bool(graph_data.get("goal_reached", False))),
        "si_graph_world_topology_trace_count": graph_topology_traces.get("topology_count", 0),
        "si_graph_world_topology_traces_agree": int(bool(graph_topology_traces.get("all_trace_summary_agree", False))),
    }


def _validation_spine_token_values(ctx: dict[str, Any]) -> dict[str, Any]:
    """Return provenance, replay, and counterexample manuscript tokens."""
    provenance_data = ctx["provenance_data"]
    replay_data = ctx["replay_data"]
    counterexample_data = ctx["counterexample_data"]
    return {
        "validation_spine_artifact_count": provenance_data.get("artifact_count", 0),
        "provenance_seeded_count": sum(
            1
            for row in (provenance_data.get("artifacts") or {}).values()
            if isinstance(row.get("deterministic_seed"), int) and row.get("config_digest")
        ),
        "provenance_all_seeded": bool(provenance_data.get("all_seeded", False)),
        "provenance_all_config_digests": bool(provenance_data.get("all_config_digests", False)),
        "provenance_all_source_commits": bool(provenance_data.get("all_source_commits", False)),
        "reproducibility_check_count": replay_data.get("check_count", 0),
        "reproducibility_all_passed": int(bool(replay_data.get("all_passed", False))),
        "counterexample_count": counterexample_data.get("counterexample_count", 0),
        "counterexample_all_known_bad_fail": int(
            bool(counterexample_data.get("all_expected_failures_observed", False))
        ),
    }


def _toy_formal_token_values(ctx: dict[str, Any]) -> dict[str, Any]:
    """Return promoted toy-sweep, formal-interop, and animation manuscript tokens."""
    sensitivity_data = ctx["sensitivity_data"]
    assumption_data = ctx["assumption_data"]
    uncertainty_data = ctx["uncertainty_data"]
    benchmark_data = ctx["benchmark_data"]
    model_checking_data = ctx["model_checking_data"]
    lean_graph_data = ctx["lean_graph_data"]
    interop_data = ctx["interop_data"]
    adversarial_data = ctx["adversarial_data"]
    animation_delta_data = ctx["animation_delta_data"]
    return {
        "sensitivity_cell_count": sensitivity_data.get("row_count", 0),
        "sensitivity_complete_grid": bool(sensitivity_data.get("complete_grid", False)),
        "analytical_assumption_count": assumption_data.get("row_count", 0),
        "analytical_equation_count": len(assumption_data.get("equation_ids") or []),
        "analytical_assumptions_indexed": bool(assumption_data.get("all_equations_indexed", False)),
        "uncertainty_row_count": uncertainty_data.get("row_count", 0),
        "uncertainty_all_normalized": bool(uncertainty_data.get("all_normalized", False)),
        "benchmark_model_count": len(benchmark_data.get("models") or []),
        "benchmark_all_models_complete": bool(benchmark_data.get("all_models_complete", False)),
        "model_checking_witness_count": model_checking_data.get("witness_count", 0),
        "model_checking_all_passed": bool(model_checking_data.get("all_passed", False)),
        "lean_graph_world_topology_witness_count": sum(
            1 for row in lean_graph_data.get("rows", []) if row.get("kind") == "topology"
        ),
        "lean_graph_world_all_topologies_witnessed": bool(lean_graph_data.get("all_topologies_witnessed", False)),
        "interop_check_count": interop_data.get("check_count", 0),
        "interop_all_lossless": bool(interop_data.get("all_lossless", False)),
        "adversarial_audit_count": adversarial_data.get("audit_count", 0),
        "adversarial_audit_all_documented": bool(adversarial_data.get("all_expected_failures_documented", False)),
        "adversarial_known_bad_passed": adversarial_data.get("known_bad_rows_passed", 0),
        "animation_delta_count": animation_delta_data.get("delta_count", 0),
        "animation_deltas_all_nonzero": bool(animation_delta_data.get("all_nonzero", False)),
    }


def _semantic_visualization_token_values(ctx: dict[str, Any]) -> dict[str, Any]:
    """Return semantic, visualization, staleness, and cross-track manuscript tokens."""
    semantic_data = ctx["semantic_data"]
    dependency_data = ctx["dependency_data"]
    stale_data = ctx["stale_data"]
    manuscript_staleness_data = ctx["manuscript_staleness_data"]
    figure_source_data = ctx["figure_source_data"]
    visualization_quality_data = ctx["visualization_quality_data"]
    statistical_bridge_data = ctx["statistical_bridge_data"]
    scope_data = ctx["scope_data"]
    gate_index_data = ctx["gate_index_data"]
    section_status_data = ctx["section_status_data"]
    render_log_data = ctx["render_log_data"]
    claim_audit_data = ctx["claim_audit_data"]
    token_provenance_data = ctx["token_provenance_data"]
    cross_symbol_data = ctx["cross_symbol_data"]
    return {
        "semantic_restriction_count": len(semantic_data.get("restrictions") or {}),
        "semantic_ok": bool(semantic_data.get("ok", False)),
        "dependency_edge_type_count": len(dependency_data.get("edge_types") or []),
        "dependency_edge_types_ok": bool(dependency_data.get("all_required_edge_types_present", False)),
        "stale_artifact_fresh_count": sum(1 for row in stale_data.get("rows") or [] if row.get("fresh")),
        "stale_artifact_all_fresh": bool(stale_data.get("all_fresh", False)),
        "manuscript_staleness_row_count": manuscript_staleness_data.get("row_count", 0),
        "manuscript_staleness_all_fresh": bool(manuscript_staleness_data.get("all_fresh", False)),
        "figure_source_coverage_count": sum(1 for row in figure_source_data.get("rows") or [] if row.get("mapped")),
        "figure_source_all_mapped": bool(figure_source_data.get("all_figures_mapped", False)),
        "visualization_quality_figure_count": visualization_quality_data.get("figure_count", 0),
        "visualization_quality_rendered_count": visualization_quality_data.get("rendered_count", 0),
        "visualization_quality_source_mapped_count": visualization_quality_data.get("source_mapped_count", 0),
        "visualization_quality_accessibility_count": visualization_quality_data.get("accessibility_text_count", 0),
        "visualization_quality_all_ok": bool(visualization_quality_data.get("all_quality_ok", False)),
        "visualization_intent_metadata_complete": bool(
            visualization_quality_data.get("all_visual_roles_present", False)
            and visualization_quality_data.get("all_evidence_roles_present", False)
        ),
        "visualization_paper_claims_complete": bool(visualization_quality_data.get("all_paper_claims_present", False)),
        "visualization_figures_section_bound": bool(visualization_quality_data.get("all_figures_section_bound", False)),
        "visualization_statistics_backed_count": visualization_quality_data.get("statistically_backed_count", 0),
        "visualization_statistics_bridge_ok": bool(
            visualization_quality_data.get("all_statistical_sources_present", False)
        ),
        "statistical_visualization_bridge_row_count": statistical_bridge_data.get("row_count", 0),
        "statistical_visualization_bridge_source_count": statistical_bridge_data.get("statistical_source_count", 0),
        "statistical_visualization_bridge_all_connected": bool(
            statistical_bridge_data.get("all_rows_connected", False)
        ),
        "statistical_visualization_bridge_all_referenced": bool(
            statistical_bridge_data.get("all_figures_referenced", False)
        ),
        "statistical_visualization_bridge_references_sheaf_bound": bool(
            statistical_bridge_data.get("all_reference_sections_sheaf_bound", False)
        ),
        "statistical_visualization_bridge_references_visualization_bound": bool(
            statistical_bridge_data.get("all_reference_sections_visualization_bound", False)
        ),
        "scope_boundary_status": "toy_only_pass" if scope_data.get("all_current_claims_toy") else "scope_leak",
        "validation_gate_index_count": gate_index_data.get("gate_count", 0),
        "sheaf_section_status_cell_count": section_status_data.get("cell_count", 0),
        "sheaf_section_status_bound_count": section_status_data.get("bound_cell_count", 0),
        "sheaf_section_status_validated_count": section_status_data.get("validated_cell_count", 0),
        "sheaf_section_status_missing_count": section_status_data.get("missing_required_count", 0),
        "sheaf_section_status_fully_sheafed_count": section_status_data.get("fully_sheafed_section_count", 0),
        "sheaf_section_status_composable_count": section_status_data.get("composable_section_count", 0),
        "sheaf_section_status_all_bound_present": bool(section_status_data.get("all_bound_fragments_present", False)),
        "sheaf_render_log_event_count": render_log_data.get("event_count", 0),
        "sheaf_render_log_all_events_ok": bool(render_log_data.get("all_events_ok", False)),
        "claim_evidence_audit_count": claim_audit_data.get("claim_count", 0),
        "claim_evidence_audit_all_complete": bool(claim_audit_data.get("all_complete", False)),
        "claim_evidence_audit_all_artifacts_resolved": bool(claim_audit_data.get("all_artifacts_resolved", False)),
        "claim_evidence_audit_all_predicates_hold": bool(claim_audit_data.get("all_evidence_predicates_hold", False)),
        "token_provenance_count": token_provenance_data.get("token_count", 0),
        "cross_track_symbol_count": cross_symbol_data.get("symbol_count", 0),
        "cross_track_symbols_consistent": int(bool(cross_symbol_data.get("all_consistent", False))),
    }


def _canonical_sheaf_token_values(ctx: dict[str, Any]) -> dict[str, Any]:
    """Return canonical sheaf-track, release, proof, and scholarship tokens."""
    provenance_data = ctx["provenance_data"]
    replay_matrix_data = ctx["replay_matrix_data"]
    uncertainty_data = ctx["uncertainty_data"]
    track_lane_data = ctx["track_lane_data"]
    artifact_contract_data = ctx["artifact_contract_data"]
    track_scope_data = ctx["track_scope_data"]
    blocked_scope_data = ctx["blocked_scope_data"]
    evidence_fields_data = ctx["evidence_fields_data"]
    release_bundle_data = ctx["release_bundle_data"]
    theorem_traceability_data = ctx["theorem_traceability_data"]
    artifact_diffoscope_data = ctx["artifact_diffoscope_data"]
    proof_extraction_data = ctx["proof_extraction_data"]
    state_space_catalog_data = ctx["state_space_catalog_data"]
    causal_ablation_data = ctx["causal_ablation_data"]
    artifact_license_data = ctx["artifact_license_data"]
    release_notes_data = ctx["release_notes_data"]
    scholarship_data = ctx["scholarship_data"]
    security_posture_data = ctx["security_posture_data"]
    proof_dependency_data = ctx["proof_dependency_data"]
    state_transition_data = ctx["state_transition_data"]
    ablation_sensitivity_data = ctx["ablation_sensitivity_data"]
    release_attestation_data = ctx["release_attestation_data"]
    return {
        "provenance_bundle_count": provenance_data.get("bundle_count", 0),
        "provenance_bundle_complete": bool(provenance_data.get("all_bundles_complete", False)),
        "replay_matrix_check_count": replay_matrix_data.get("check_count", replay_matrix_data.get("row_count", 0)),
        "replay_matrix_row_count": replay_matrix_data.get("row_count", replay_matrix_data.get("check_count", 0)),
        "replay_matrix_all_replayed": bool(replay_matrix_data.get("all_replayed", False)),
        "replay_matrix_all_matched": bool(replay_matrix_data.get("all_replay_rows_matched", False)),
        "uncertainty_bin_count": uncertainty_data.get("bin_count", 0),
        "track_lane_matrix_row_count": track_lane_data.get("row_count", 0),
        "track_lane_matrix_complete": bool(track_lane_data.get("all_pipeline_tracks_complete", False)),
        "artifact_contract_row_count": artifact_contract_data.get("row_count", 0),
        "artifact_contract_complete": bool(artifact_contract_data.get("all_rows_complete", False)),
        "artifact_contract_copied_parity_complete": bool(
            artifact_contract_data.get("all_copied_parity_complete", False)
        ),
        "track_improvement_row_count": track_scope_data.get("improvement_row_count", 0),
        "track_improvement_all_live_valid": bool(track_scope_data.get("all_live_tracks_valid", False)),
        "blocked_scope_status": "blocked" if blocked_scope_data.get("all_blocked") else "scope_leak",
        "evidence_field_count": evidence_fields_data.get("field_count", 0),
        "evidence_fields_mapped": bool(evidence_fields_data.get("all_fields_mapped", False)),
        "release_bundle_artifact_count": release_bundle_data.get("artifact_count", 0),
        "release_bundle_sources_present": bool(release_bundle_data.get("all_required_sources_present", False)),
        "theorem_traceability_row_count": theorem_traceability_data.get("row_count", 0),
        "theorem_traceability_linked": bool(theorem_traceability_data.get("all_theorems_linked", False)),
        "artifact_diffoscope_row_count": artifact_diffoscope_data.get("row_count", 0),
        "artifact_diffoscope_all_equal": bool(artifact_diffoscope_data.get("all_equal", False)),
        "proof_extraction_theorem_count": proof_extraction_data.get("theorem_count", 0),
        "proof_extraction_all_constructive": bool(proof_extraction_data.get("all_constructive", False)),
        "state_space_catalog_row_count": state_space_catalog_data.get("row_count", 0),
        "state_space_catalog_all_finite": bool(state_space_catalog_data.get("all_finite", False)),
        "causal_ablation_row_count": causal_ablation_data.get("row_count", 0),
        "causal_ablation_complete_grid": bool(causal_ablation_data.get("complete_grid", False)),
        "artifact_license_row_count": artifact_license_data.get("row_count", 0),
        "artifact_license_all_safe": bool(artifact_license_data.get("all_license_safe", False)),
        "release_notes_row_count": release_notes_data.get("row_count", 0),
        "release_notes_source_backed": bool(release_notes_data.get("all_notes_source_backed", False)),
        "scholarship_source_count": scholarship_data.get("source_count", 0),
        "scholarship_method_role_count": scholarship_data.get("method_role_count", 0),
        "scholarship_source_family_count": scholarship_data.get("source_family_count", 0),
        "scholarship_source_locator_kind_count": scholarship_data.get("source_locator_kind_count", 0),
        "scholarship_declared_section_citation_overlap_count": scholarship_data.get(
            "declared_section_citation_overlap_count", 0
        ),
        "scholarship_primary_source_count": scholarship_data.get("primary_source_count", 0),
        "scholarship_quantitative_method_role_count": scholarship_data.get("quantitative_method_role_count", 0),
        "scholarship_sources_connected": bool(scholarship_data.get("all_sources_connected", False)),
        "scholarship_citations_present": bool(scholarship_data.get("all_citations_present", False)),
        "scholarship_claim_boundaries_scope_guarded": bool(
            scholarship_data.get("all_claim_boundaries_scope_guarded", False)
        ),
        "scholarship_rows_rederived": bool(scholarship_data.get("all_rows_rederived", False)),
        "security_posture_control_count": security_posture_data.get("control_count", 0),
        "security_posture_enforced_count": security_posture_data.get("enforced_count", 0),
        "security_posture_deferred_count": security_posture_data.get("deferred_count", 0),
        "security_posture_all_controls_ok": bool(security_posture_data.get("all_controls_ok", False)),
        "security_posture_all_evidence_present": bool(security_posture_data.get("all_evidence_present", False)),
        "security_posture_secret_finding_count": security_posture_data.get("secret_finding_count", 0),
        "security_posture_high_risk_gap_count": security_posture_data.get("high_risk_gap_count", 0),
        "proof_dependency_edge_count": proof_dependency_data.get("edge_count", 0),
        "proof_dependency_all_resolved": bool(proof_dependency_data.get("all_edges_resolved", False)),
        "state_transition_row_count": state_transition_data.get("row_count", 0),
        "state_transition_all_covered": bool(state_transition_data.get("all_reachable_states_covered", False)),
        "ablation_sensitivity_row_count": ablation_sensitivity_data.get("row_count", 0),
        "ablation_sensitivity_source_backed": bool(ablation_sensitivity_data.get("all_effects_source_backed", False)),
        "release_attestation_row_count": release_attestation_data.get("row_count", 0),
        "release_attestation_all_attested": bool(release_attestation_data.get("all_attested", False)),
    }


VARIABLE_TOKEN_BUILDERS = (
    _core_token_values,
    _simulation_token_values,
    _validation_spine_token_values,
    _toy_formal_token_values,
    _semantic_visualization_token_values,
    _canonical_sheaf_token_values,
)


def generate_variables(project_root: Path, *, require_analysis_outputs: bool = True) -> dict[str, Any]:
    """Generate manuscript tokens from live configuration and output artifacts."""
    root = project_root.resolve()
    hp = load_hyperparameters()
    pymdp_cfg = load_pymdp_config(root)
    sweep_path = root / "output" / "data" / "parameter_sweep.csv"
    si_summary = root / "output" / "data" / "si_tmaze_summary.json"
    stats_path = root / "output" / "data" / "analysis_statistics.json"
    inv_passed, inv_total = load_invariant_counts(root)

    if require_analysis_outputs and not sweep_path.exists():
        raise FileNotFoundError(f"missing analysis artifact: {sweep_path}")

    sweep_rows = read_parameter_sweep(sweep_path)
    si_data = _load_json(si_summary)
    stats_data = _load_json(stats_path)
    artifacts = _load_variable_artifacts(root)
    policy_data = artifacts["policy"]
    posterior_data = artifacts["posterior"]
    runtime_data = artifacts["runtime"]
    graph_data = artifacts["graph"]
    graph_topology_traces = artifacts["graph_topology_traces"]
    provenance_data = artifacts["provenance"]
    replay_data = artifacts["replay"]
    counterexample_data = artifacts["counterexample"]
    sensitivity_data = artifacts["sensitivity"]
    uncertainty_data = artifacts["uncertainty"]
    benchmark_data = artifacts["benchmark"]
    model_checking_data = artifacts["model_checking"]
    lean_graph_data = artifacts["lean_graph"]
    interop_data = artifacts["interop"]
    adversarial_data = artifacts["adversarial"]
    semantic_data = artifacts["semantic"]
    dependency_data = artifacts["dependency"]
    stale_data = artifacts["stale"]
    manuscript_staleness_data = artifacts["manuscript_staleness"]
    figure_source_data = artifacts["figure_source"]
    visualization_quality_data = artifacts["visualization_quality"]
    statistical_bridge_data = artifacts["statistical_bridge"]
    scope_data = artifacts["scope"]
    gate_index_data = artifacts["gate_index"]
    section_status_data = artifacts["section_status"]
    render_log_data = artifacts["render_log"]
    claim_audit_data = artifacts["claim_audit"]
    token_provenance_data = artifacts["token_provenance"]
    cross_symbol_data = artifacts["cross_symbol"]
    assumption_data = artifacts["assumption"]
    animation_delta_data = artifacts["animation_delta"]
    replay_matrix_data = artifacts["replay_matrix"]
    track_lane_data = artifacts["track_lane"]
    artifact_contract_data = artifacts["artifact_contract"]
    track_scope_data = artifacts["track_scope"]
    blocked_scope_data = artifacts["blocked_scope"]
    evidence_fields_data = artifacts["evidence_fields"]
    release_bundle_data = artifacts["release_bundle"]
    theorem_traceability_data = artifacts["theorem_traceability"]
    artifact_diffoscope_data = artifacts["artifact_diffoscope"]
    proof_extraction_data = artifacts["proof_extraction"]
    state_space_catalog_data = artifacts["state_space_catalog"]
    causal_ablation_data = artifacts["causal_ablation"]
    artifact_license_data = artifacts["artifact_license"]
    release_notes_data = artifacts["release_notes"]
    scholarship_data = artifacts["scholarship"]
    security_posture_data = artifacts["security_posture"]
    proof_dependency_data = artifacts["proof_dependency"]
    state_transition_data = artifacts["state_transition"]
    ablation_sensitivity_data = artifacts["ablation_sensitivity"]
    release_attestation_data = artifacts["release_attestation"]
    si_stats = stats_data.get("si_tmaze") or {}
    sweep_stats = stats_data.get("sweep") or {}
    policy_summary = policy_data.get("summary") or {}
    policy_goal_by_mode = _policy_goal_counts_by_mode(policy_data)

    mean_entropy = float(si_data.get("mean_belief_entropy", si_stats.get("entropy_mean", 0.0)))
    from manuscript.sheaf.counts import structural_counts

    counts = structural_counts(root)
    context = locals()
    variables: dict[str, Any] = {}
    for build_tokens in VARIABLE_TOKEN_BUILDERS:
        variables.update(build_tokens(context))
    return variables
