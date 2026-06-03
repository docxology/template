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


def generate_variables(project_root: Path, *, require_analysis_outputs: bool = True) -> dict[str, Any]:
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
    policy_data = _load_json(root / "output" / "data" / "si_policy_comparison.json")
    posterior_data = _load_json(root / "output" / "data" / "pymdp_policy_posterior_grid.json")
    runtime_data = _load_json(root / "output" / "reports" / "pymdp_runtime_diagnostics.json")
    graph_data = _load_json(root / "output" / "data" / "si_graph_world_summary.json")
    graph_topology_traces = _load_json(root / "output" / "data" / "si_graph_world_topology_traces.json")
    provenance_data = _load_json(root / "output" / "data" / "artifact_provenance.json")
    replay_data = _load_json(root / "output" / "reports" / "reproducibility_replay.json")
    counterexample_data = _load_json(root / "output" / "reports" / "counterexample_matrix.json")
    sensitivity_data = _load_json(root / "output" / "data" / "sensitivity_sweep.json")
    uncertainty_data = _load_json(root / "output" / "data" / "uncertainty_summary.json")
    benchmark_data = _load_json(root / "output" / "data" / "toy_benchmark_matrix.json")
    model_checking_data = _load_json(root / "output" / "reports" / "model_checking_witnesses.json")
    lean_graph_data = _load_json(root / "output" / "reports" / "lean_graph_world_inventory.json")
    interop_data = _load_json(root / "output" / "data" / "interop_roundtrip_report.json")
    adversarial_data = _load_json(root / "output" / "reports" / "adversarial_audit.json")
    semantic_data = _load_json(root / "output" / "data" / "sheaf_gluing_certificate.json")
    dependency_data = _load_json(root / "output" / "data" / "validation_dependency_graph.json")
    stale_data = _load_json(root / "output" / "reports" / "stale_artifact_report.json")
    manuscript_staleness_data = _load_json(root / "output" / "reports" / "manuscript_staleness_report.json")
    figure_source_data = _load_json(root / "output" / "data" / "figure_source_map.json")
    scope_data = _load_json(root / "output" / "reports" / "scope_boundary_audit.json")
    gate_index_data = _load_json(root / "output" / "data" / "validation_gate_index.json")
    section_status_data = _load_json(root / "output" / "data" / "sheaf_section_status_matrix.json")
    render_log_data = _load_json(root / "output" / "reports" / "sheaf_render_log.json")
    claim_audit_data = _load_json(root / "output" / "reports" / "claim_evidence_audit.json")
    token_provenance_data = _load_json(root / "output" / "data" / "manuscript_token_provenance.json")
    cross_symbol_data = _load_json(root / "output" / "data" / "cross_track_symbol_table.json")
    assumption_data = _load_json(root / "output" / "data" / "analytical_assumption_index.json")
    animation_delta_data = _load_json(root / "output" / "data" / "animation_frame_deltas.json")
    replay_matrix_data = _load_json(root / "output" / "reports" / "replay_matrix.json")
    track_scope_data = _load_json(root / "output" / "data" / "track_improvement_scope.json")
    blocked_scope_data = _load_json(root / "output" / "reports" / "blocked_scope_manifest.json")
    evidence_fields_data = _load_json(root / "output" / "data" / "evidence_field_index.json")
    release_bundle_data = _load_json(root / "output" / "reports" / "release_bundle_manifest.json")
    theorem_traceability_data = _load_json(root / "output" / "data" / "theorem_traceability_matrix.json")
    artifact_diffoscope_data = _load_json(root / "output" / "reports" / "artifact_diffoscope.json")
    proof_extraction_data = _load_json(root / "output" / "data" / "proof_extraction_index.json")
    state_space_catalog_data = _load_json(root / "output" / "data" / "state_space_catalog.json")
    causal_ablation_data = _load_json(root / "output" / "data" / "causal_ablation_matrix.json")
    artifact_license_data = _load_json(root / "output" / "reports" / "artifact_license_audit.json")
    release_notes_data = _load_json(root / "output" / "reports" / "release_notes_evidence.json")
    proof_dependency_data = _load_json(root / "output" / "data" / "proof_dependency_graph.json")
    state_transition_data = _load_json(root / "output" / "data" / "state_transition_table.json")
    ablation_sensitivity_data = _load_json(root / "output" / "reports" / "ablation_sensitivity_report.json")
    release_attestation_data = _load_json(root / "output" / "reports" / "release_attestation.json")
    si_stats = stats_data.get("si_tmaze") or {}
    sweep_stats = stats_data.get("sweep") or {}
    policy_summary = policy_data.get("summary") or {}
    policy_goal_by_mode = _policy_goal_counts_by_mode(policy_data)

    mean_entropy = float(si_data.get("mean_belief_entropy", si_stats.get("entropy_mean", 0.0)))
    from manuscript.sheaf.counts import structural_counts

    counts = structural_counts(root)
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
        "invariants_passed": inv_passed,
        "invariants_total": inv_total,
        "si_tmaze_steps": si_data.get("steps", si_stats.get("steps", 0)),
        "si_tmaze_policy_len": si_data.get("policy_len", pymdp_cfg.policy_len),
        "si_tmaze_mean_belief_entropy": mean_entropy,
        "si_tmaze_mean_belief_entropy_formatted": f"{mean_entropy:.4f}",
        "si_goal_reached": int(bool(si_data.get("goal_reached", si_stats.get("goal_reached", False)))),
        "si_action_diversity": si_data.get("action_diversity", si_stats.get("action_diversity", 0)),
        "si_entropy_min": si_stats.get("entropy_min", 0.0),
        "si_entropy_max": si_stats.get("entropy_max", 0.0),
        "sweep_max_residual": sweep_stats.get("max_residual", 0.0),
        "sweep_rmse_mi": sweep_stats.get("rmse_mi", 0.0),
        "pymdp_mode": stats_data.get("pymdp_mode", si_data.get("mode", pymdp_cfg.mode)),
        "pymdp_config_hash": stats_data.get("pymdp_config_hash", si_data.get("config_hash", "")),
        "si_policy_comparison_run_count": policy_summary.get("run_count", 0),
        "si_policy_comparison_goal_reached_count": policy_summary.get("goal_reached_count", 0),
        "si_policy_comparison_state_goal_count": policy_goal_by_mode["state_inference"],
        "si_policy_comparison_policy_goal_count": policy_goal_by_mode["policy_inference"],
        "si_policy_comparison_complete_grid": int(bool(policy_summary.get("complete_grid", False))),
        "si_policy_efe_rows_explained": int(bool(policy_summary.get("all_efe_rows_explained", False))),
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
        "token_provenance_count": token_provenance_data.get("token_count", 0),
        "cross_track_symbol_count": cross_symbol_data.get("symbol_count", 0),
        "cross_track_symbols_consistent": int(bool(cross_symbol_data.get("all_consistent", False))),
        "provenance_bundle_count": provenance_data.get("bundle_count", 0),
        "provenance_bundle_complete": bool(provenance_data.get("all_bundles_complete", False)),
        "replay_matrix_check_count": replay_matrix_data.get("check_count", replay_matrix_data.get("row_count", 0)),
        "replay_matrix_row_count": replay_matrix_data.get("row_count", replay_matrix_data.get("check_count", 0)),
        "replay_matrix_all_replayed": bool(replay_matrix_data.get("all_replayed", False)),
        "replay_matrix_all_matched": bool(replay_matrix_data.get("all_replay_rows_matched", False)),
        "uncertainty_bin_count": uncertainty_data.get("bin_count", 0),
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
        "proof_dependency_edge_count": proof_dependency_data.get("edge_count", 0),
        "proof_dependency_all_resolved": bool(proof_dependency_data.get("all_edges_resolved", False)),
        "state_transition_row_count": state_transition_data.get("row_count", 0),
        "state_transition_all_covered": bool(state_transition_data.get("all_reachable_states_covered", False)),
        "ablation_sensitivity_row_count": ablation_sensitivity_data.get("row_count", 0),
        "ablation_sensitivity_source_backed": bool(ablation_sensitivity_data.get("all_effects_source_backed", False)),
        "release_attestation_row_count": release_attestation_data.get("row_count", 0),
        "release_attestation_all_attested": bool(release_attestation_data.get("all_attested", False)),
        "pipeline_track_count": _pipeline_track_count(root),
        **counts,
    }
