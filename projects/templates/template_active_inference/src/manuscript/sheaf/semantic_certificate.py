"""Semantic gluing certificate builder and writer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from manuscript.variables import generate_variables
from ontology.bindings import validate_all_gnn_ontology

from manuscript.sheaf.coverage import gray_cell_count, load_sheaf_coverage_context
from manuscript.sheaf.semantic_evidence import (
    _canonical_restriction_snapshot,
    _claim_records,
    _section_records,
    _semantic_artifact_sources,
    _semantic_payloads,
    _semantic_shared_symbols,
    _semantic_track_rows,
    build_evidence_crosswalk,
    build_validation_dependency_graph,
)
from manuscript.sheaf.semantic_issues import semantic_gluing_issues
from manuscript.sheaf.semantic_maps import SEMANTIC_SCHEMA
from manuscript.sheaf.semantic_refresh import _refresh_hydrated_manuscript
from manuscript.sheaf.semantic_restrictions import (
    _animation_frame_count,
    _graph_world_restrictions,
    _lean_status,
    _policy_comparison_restrictions,
    _policy_posterior_restrictions,
    _proof_obligation_rows,
    _pymdp_hash_restrictions,
    _restriction_lane_assignments,
    _restriction_lane_summaries,
    _runtime_diagnostics_restrictions,
)


def build_semantic_gluing_certificate(project_root: Path) -> dict[str, Any]:
    """Build a JSON-serializable semantic certificate from live project state."""
    root = project_root.resolve()
    ctx = load_sheaf_coverage_context(root)
    issues = semantic_gluing_issues(root)
    variables = generate_variables(root, require_analysis_outputs=False)
    dependency_graph = build_validation_dependency_graph(root)
    policy = _policy_comparison_restrictions(root)
    posterior = _policy_posterior_restrictions(root)
    runtime = _runtime_diagnostics_restrictions(root)
    graph_world = _graph_world_restrictions(root)
    pymdp_hash = _pymdp_hash_restrictions(root)
    lean = _lean_status(root)
    payloads = _semantic_payloads(root)
    sensitivity = payloads["sensitivity"]
    uncertainty = payloads["uncertainty"]
    benchmark = payloads["benchmark"]
    model_checking = payloads["model_checking"]
    interop = payloads["interop"]
    adversarial = payloads["adversarial"]
    stale = payloads["stale"]
    manuscript_staleness = payloads["manuscript_staleness"]
    tokens = payloads["tokens"]
    figures = payloads["figures"]
    scope = payloads["scope"]
    provenance = payloads["provenance"]
    assumptions = payloads["assumptions"]
    animation_deltas = payloads["animation_deltas"]
    release_bundle = payloads["release_bundle"]
    evidence_fields = payloads["evidence_fields"]
    theorem_traceability = payloads["theorem_traceability"]
    gate_index = payloads["gate_index"]
    section_status = payloads["section_status"]
    render_log = payloads["render_log"]
    track_lane = payloads["track_lane"]
    track_scope = payloads["track_scope"]
    blocked_scope = payloads["blocked_scope"]
    replay_matrix = payloads["replay_matrix"]
    proof_dependency = payloads["proof_dependency"]
    transition_table = payloads["transition_table"]
    ablation_sensitivity = payloads["ablation_sensitivity"]
    release_attestation = payloads["release_attestation"]
    security_posture = payloads["security_posture"]
    canonical_restrictions = _canonical_restriction_snapshot(root)
    from validation_spine import validate_validation_spine

    proof_obligations = _proof_obligation_rows(canonical_restrictions)
    restrictions = {
        "coverage_missing": gray_cell_count(ctx.matrix),
        "section_count": len(ctx.manifest.sections),
        "track_count": len(ctx.registry.tracks),
        "claim_count": len(_claim_records(root)),
        "policy_comparison_run_count": policy["run_count"],
        "policy_comparison_modes": policy["modes"],
        "policy_comparison_horizons": policy["horizons"],
        "policy_comparison_goal_reached_count": policy["goal_reached_count"],
        "policy_comparison_complete_grid": policy["complete_grid"],
        "policy_comparison_efe_rows_explained": policy["all_efe_rows_explained"],
        "policy_posterior_row_count": posterior["row_count"],
        "policy_posterior_available_row_count": posterior["available_row_count"],
        "policy_posterior_normalized": posterior["all_available_posteriors_normalized"],
        "pymdp_runtime_ok": runtime["ok"],
        "pymdp_runtime_phase_rows_ok": runtime["phase_rows_ok"],
        "pymdp_runtime_known_warning_count": runtime["known_warning_count"],
        "pymdp_runtime_unexpected_warning_count": runtime["unexpected_warning_count"],
        "graph_world_steps_match": graph_world["steps_match"],
        "graph_world_goal_reached": graph_world["goal_reached"],
        "animation_frame_count": _animation_frame_count(root),
        "animation_deltas_all_nonzero": animation_deltas.get("all_nonzero") is True,
        "animation_delta_count": int(animation_deltas.get("delta_count", 0) or 0),
        "pymdp_mode_match": pymdp_hash["mode_match"],
        "pymdp_config_hash_match": pymdp_hash["config_hash_match"],
        "artifact_provenance_seed_config_complete": provenance.get("all_seeded") is True
        and provenance.get("all_config_digests") is True,
        "lean_all_proved": lean["all_proved"],
        "lean_proved_count": lean["proved_count"],
        "gnn_ontology_ok": not validate_all_gnn_ontology(root),
        "configured_artifact_producers_ok": not dependency_graph["issues"],
        "validation_spine_ok": not validate_validation_spine(root),
        "sensitivity_complete_grid": sensitivity.get("complete_grid") is True,
        "analytical_assumptions_indexed": assumptions.get("all_equations_indexed") is True,
        "analytical_assumption_count": int(assumptions.get("row_count", 0) or 0),
        "sensitivity_cell_count": int(sensitivity.get("row_count", 0) or 0),
        "uncertainty_all_normalized": uncertainty.get("all_normalized") is True,
        "uncertainty_row_count": int(uncertainty.get("row_count", 0) or 0),
        "benchmark_all_models_complete": benchmark.get("all_models_complete") is True,
        "benchmark_model_count": len(benchmark.get("models") or []),
        "model_checking_all_passed": model_checking.get("all_passed") is True,
        "model_checking_witness_count": int(model_checking.get("witness_count", 0) or 0),
        "interop_all_lossless": interop.get("all_lossless") is True,
        "interop_check_count": int(interop.get("check_count", 0) or 0),
        "adversarial_expected_failures_documented": adversarial.get("all_expected_failures_documented") is True,
        "adversarial_known_bad_passed": int(adversarial.get("known_bad_rows_passed", 0) or 0),
        "dependency_edge_types_ok": dependency_graph.get("all_required_edge_types_present") is True,
        "dependency_edge_type_count": len(dependency_graph.get("edge_types") or []),
        "stale_artifacts_all_fresh": stale.get("all_fresh") is True,
        "manuscript_staleness_all_fresh": manuscript_staleness.get("all_fresh") is True,
        "manuscript_staleness_row_count": int(manuscript_staleness.get("row_count", 0) or 0),
        "token_provenance_complete": tokens.get("all_tokens_mapped") is True,
        "figure_source_coverage": figures.get("all_figures_mapped") is True,
        "scope_boundary_toy_only": scope.get("all_current_claims_toy") is True,
        "provenance_bundle_complete": provenance.get("all_bundles_complete") is True,
        "provenance_bundle_count": int(provenance.get("bundle_count", 0) or 0),
        "replay_matrix_all_matched": replay_matrix.get("all_replay_rows_matched") is True,
        "replay_matrix_row_count": int(replay_matrix.get("row_count", replay_matrix.get("check_count", 0)) or 0),
        "track_improvement_scope_complete": track_scope.get("all_live_tracks_valid") is True,
        "track_improvement_row_count": int(track_scope.get("improvement_row_count", 0) or 0),
        "blocked_empirical_adapter": blocked_scope.get("all_blocked") is True,
        "evidence_fields_mapped": evidence_fields.get("all_fields_mapped") is True,
        "evidence_field_count": int(evidence_fields.get("field_count", 0) or 0),
        "release_bundle_sources_present": release_bundle.get("all_required_sources_present") is True,
        "release_bundle_artifact_count": int(release_bundle.get("artifact_count", 0) or 0),
        "theorem_traceability_linked": theorem_traceability.get("all_theorems_linked") is True,
        "theorem_traceability_row_count": int(theorem_traceability.get("row_count", 0) or 0),
        "gate_ergonomics_indexed": gate_index.get("all_indexed") is True,
        "validation_gate_index_count": int(gate_index.get("gate_count", 0) or 0),
        "section_status_all_bound_present": section_status.get("all_bound_fragments_present") is True,
        "section_status_all_sections_have_status": section_status.get("all_sections_have_status") is True,
        "section_status_all_tracks_have_status": section_status.get("all_tracks_have_status") is True,
        "section_status_cell_count": int(section_status.get("cell_count", 0) or 0),
        "section_status_fully_sheafed_count": int(section_status.get("fully_sheafed_section_count", 0) or 0),
        "sheaf_render_log_all_events_ok": render_log.get("all_events_ok") is True,
        "sheaf_render_log_event_count": int(render_log.get("event_count", 0) or 0),
        "track_lane_matrix_complete": track_lane.get("all_pipeline_tracks_complete") is True,
        "track_lane_matrix_row_count": int(track_lane.get("row_count", 0) or 0),
        "proof_dependency_graph_resolved": proof_dependency.get("all_theorems_have_dependencies") is True
        and proof_dependency.get("all_edges_resolved") is True,
        "proof_dependency_edge_count": int(proof_dependency.get("edge_count", 0) or 0),
        "state_transition_table_complete": transition_table.get("all_transitions_deterministic") is True
        and transition_table.get("all_reachable_states_covered") is True,
        "state_transition_row_count": int(transition_table.get("row_count", 0) or 0),
        "ablation_sensitivity_source_backed": ablation_sensitivity.get("all_effects_source_backed") is True,
        "ablation_sensitivity_row_count": int(ablation_sensitivity.get("row_count", 0) or 0),
        "release_attestation_complete": release_attestation.get("all_attested") is True,
        "release_attestation_row_count": int(release_attestation.get("row_count", 0) or 0),
        "security_posture_controls_ok": security_posture.get("all_controls_ok") is True,
        "security_posture_control_count": int(security_posture.get("control_count", 0) or 0),
        "security_posture_high_risk_gap_count": int(security_posture.get("high_risk_gap_count", 0) or 0),
        "security_posture_secret_finding_count": int(security_posture.get("secret_finding_count", 0) or 0),
        "security_posture_secret_patterns_absent": security_posture.get("all_secret_patterns_absent") is True,
        "no_versioned_live_tracks": not any(tid.endswith(("_v2", "_v3", "_v4", "_v5")) for tid in ctx.registry.tracks),
        **canonical_restrictions,
    }
    restriction_lanes = _restriction_lane_assignments(restrictions)
    lane_summaries = _restriction_lane_summaries(restrictions, restriction_lanes)
    return {
        "schema": SEMANTIC_SCHEMA,
        "ok": not issues,
        "issues": issues,
        "restriction_classes": sorted({row["class"] for row in proof_obligations}),
        "restriction_lanes": restriction_lanes,
        "lane_summaries": lane_summaries,
        "all_lane_summaries_ok": bool(lane_summaries) and all(row["all_ok"] for row in lane_summaries.values()),
        "proof_obligations": proof_obligations,
        "all_proof_obligations_ok": bool(proof_obligations) and all(row["ok"] for row in proof_obligations),
        "tracks": _semantic_track_rows(ctx),
        "sections": _section_records(root),
        "shared_symbols": _semantic_shared_symbols(root),
        "artifact_sources": _semantic_artifact_sources(root),
        "restrictions": restrictions,
        "artifact_graph": dependency_graph["artifacts"],
        "evidence_crosswalk": build_evidence_crosswalk(root),
        "claims": _claim_records(root),
        "manuscript_variables": variables,
    }


def write_semantic_gluing_certificate(
    project_root: Path,
    *,
    output_path: Path | None = None,
) -> Path:
    """Write semantic gluing certificate to the output path."""
    root = project_root.resolve()
    path = output_path or root / "output" / "data" / "sheaf_gluing_certificate.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        _refresh_hydrated_manuscript(root)
        from manuscript.sheaf.status import write_sheaf_status_outputs

        write_sheaf_status_outputs(root)
    payload = build_semantic_gluing_certificate(root)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if output_path is None:
        _refresh_hydrated_manuscript(root)
        from manuscript.sheaf.status import write_sheaf_status_outputs

        write_sheaf_status_outputs(root)
        payload = build_semantic_gluing_certificate(root)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
