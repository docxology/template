from __future__ import annotations
from pathlib import Path
from typing import Any
from contracts.artifact_contract import EXPERIMENT_PLAN_METRIC_KEYS, PROMOTED_ARTIFACTS
from gates.output_checks_simulation import efe_values_explained
from json_io import read_json


def load_promoted_artifacts(root: Path) -> dict[str, dict]:
    return {name: read_json(root / rel_path) for name, rel_path in PROMOTED_ARTIFACTS.items()}


def add_toy_formal_integration_checks(checks: dict[str, bool], artifacts: dict[str, dict]) -> None:
    sensitivity = artifacts["sensitivity"]
    uncertainty = artifacts["uncertainty"]
    benchmark = artifacts["benchmark"]
    policy_grid = artifacts["policy_grid"]
    efe_terms = artifacts["efe_terms"]
    topology = artifacts["topology"]
    topology_traces = artifacts["topology_traces"]
    graph_invariants = artifacts["graph_invariants"]
    observable = artifacts["observable"]
    model_checking = artifacts["model_checking"]
    interop = artifacts["interop"]
    gnn_roundtrip = artifacts["gnn_roundtrip"]
    gnn_lint = artifacts["gnn_lint"]
    ontology_alias = artifacts["ontology_alias"]
    ontology_profile = artifacts["ontology_profile"]
    lean_theorems = artifacts["lean_theorems"]
    lean_graph = artifacts["lean_graph"]
    producer_completeness = artifacts["producer_completeness"]
    stale_report = artifacts["stale_report"]
    manuscript_staleness = artifacts["manuscript_staleness"]
    cross_symbols = artifacts["cross_symbols"]
    evidence_tables = artifacts["evidence_tables"]
    token_provenance = artifacts["token_provenance"]
    claim_audit = artifacts["claim_audit"]
    gate_index = artifacts["gate_index"]
    section_status = artifacts["section_status"]
    render_log = artifacts["render_log"]
    scope = artifacts["scope"]
    adversarial = artifacts["adversarial"]
    assumptions = artifacts["assumptions"]

    checks["analytical_observable_sweep_schema"] = (
        observable.get("schema") == "template_active_inference.analytical_observable_sweep.v1"
        and float(observable.get("max_abs_residual", 1.0)) <= 1e-12
    )
    checks["analytical_assumption_index_schema"] = (
        assumptions.get("schema") == "template_active_inference.analytical_assumption_index.v1"
        and assumptions.get("all_equations_indexed") is True
    )
    checks["sensitivity_sweep_schema"] = (
        sensitivity.get("schema") == "template_active_inference.sensitivity_sweep.v1"
        and sensitivity.get("complete_grid") is True
    )
    checks["uncertainty_summary_schema"] = (
        uncertainty.get("schema") == "template_active_inference.uncertainty_summary.v1"
        and uncertainty.get("all_normalized") is True
    )
    checks["toy_benchmark_matrix_schema"] = (
        benchmark.get("schema") == "template_active_inference.toy_benchmark_matrix.v1"
        and benchmark.get("all_models_complete") is True
    )
    checks["si_policy_grid_schema"] = policy_grid.get("complete_grid") is True
    checks["si_efe_terms_schema"] = (
        efe_terms.get("schema") == "template_active_inference.si_efe_values.v1"
        and efe_terms.get("all_rows_explained") is True
        and efe_terms.get("all_rows_explained") == efe_values_explained(efe_terms)
    )
    checks["si_graph_world_topology_sweep_schema"] = topology.get("all_summary_trace_agree") is True
    checks["si_graph_world_topology_traces_schema"] = (
        topology_traces.get("schema") == "template_active_inference.si_graph_world_topology_traces.v1"
        and topology_traces.get("all_trace_summary_agree") is True
        and topology_traces.get("topology_count") == topology.get("topology_count")
    )
    checks["graph_world_invariants_schema"] = graph_invariants.get("all_passed") is True
    checks["model_checking_witnesses_schema"] = (
        model_checking.get("schema") == "template_active_inference.model_checking_witnesses.v1"
        and model_checking.get("all_passed") is True
    )
    checks["interop_roundtrip_schema"] = (
        interop.get("schema") == "template_active_inference.interop_roundtrip_report.v1"
        and interop.get("all_lossless") is True
    )
    checks["gnn_roundtrip_schema"] = gnn_roundtrip.get("all_lossless") is True
    checks["gnn_lint_schema"] = gnn_lint.get("all_variables_mapped_once") is True
    checks["ontology_alias_schema"] = ontology_alias.get("no_conflicts") is True
    checks["ontology_profile_schema"] = ontology_profile.get("all_mapped_once") is True
    checks["lean_theorem_inventory_schema"] = lean_theorems.get("all_proved") is True
    checks["lean_graph_world_inventory_schema"] = (
        lean_graph.get("all_topologies_witnessed") is True
        and lean_graph.get("all_policy_witnesses_present") is True
        and int(lean_graph.get("topology_count", 0) or 0) == int(topology.get("topology_count", 0) or 0)
    )
    checks["producer_completeness_schema"] = producer_completeness.get("all_complete") is True
    checks["stale_artifact_report_schema"] = stale_report.get("all_fresh") is True
    checks["manuscript_staleness_report_schema"] = (
        manuscript_staleness.get("schema") == "template_active_inference.manuscript_staleness_report.v1"
        and manuscript_staleness.get("all_fresh") is True
    )
    checks["cross_track_symbol_table_schema"] = (
        cross_symbols.get("all_consistent") is True
        and cross_symbols.get("all_shapes_declared") is True
        and cross_symbols.get("all_dtypes_declared") is True
        and cross_symbols.get("all_ontology_terms_declared") is True
        and cross_symbols.get("all_section_terms_declared") is True
    )
    checks["manuscript_evidence_tables_schema"] = evidence_tables.get("all_source_backed") is True
    checks["manuscript_token_provenance_schema"] = token_provenance.get("all_tokens_mapped") is True
    checks["claim_evidence_audit_schema"] = (
        claim_audit.get("all_claims_typed") is True
        and claim_audit.get("all_complete") is True
        and claim_audit.get("all_artifacts_resolved") is True
        and claim_audit.get("all_evidence_resolved") is True
        and claim_audit.get("all_evidence_predicates_hold") is True
        and int(claim_audit.get("incomplete_claim_count", -1)) == 0
    )
    checks["validation_gate_index_schema"] = gate_index.get("all_indexed") is True
    checks["sheaf_section_status_matrix_schema"] = (
        section_status.get("schema") == "template_active_inference.sheaf_section_status_matrix.v1"
        and section_status.get("all_bound_fragments_present") is True
        and section_status.get("all_sections_have_status") is True
        and section_status.get("all_tracks_have_status") is True
        and int(section_status.get("cell_count", 0) or 0) > 0
    )
    checks["sheaf_render_log_schema"] = (
        render_log.get("schema") == "template_active_inference.sheaf_render_log.v1"
        and render_log.get("all_events_ok") is True
        and int(render_log.get("event_count", 0) or 0) > 0
    )
    checks["scope_boundary_audit_schema"] = (
        scope.get("scope_boundary_status") == "toy_only_pass"
        and scope.get("all_current_claims_toy") is True
        and scope.get("all_required_scope_categories_present") is True
        and scope.get("blocked_manifest_concordant") is True
        and scope.get("all_future_rows_non_live") is True
        and scope.get("all_blocked_contexts_non_live") is True
    )
    checks["adversarial_audit_schema"] = (
        adversarial.get("all_expected_failures_documented") is True
        and adversarial.get("all_expected_failures_observed") is True
        and int(adversarial.get("known_bad_rows_passed", 0) or 0) == 0
    )


def add_visualization_checks(checks: dict[str, bool], artifacts: dict[str, dict]) -> None:
    figure_source = artifacts["figure_source"]
    figure_hash = artifacts["figure_hash"]
    visualization_quality = artifacts["visualization_quality"]
    statistical_bridge = artifacts["statistical_bridge"]

    checks["figure_source_map_schema"] = (
        figure_source.get("all_figures_mapped") is True
        and figure_source.get("all_figures_have_claim_lanes") is True
        and figure_source.get("all_claim_lanes_valid") is True
    )
    checks["figure_hash_manifest_schema"] = figure_hash.get("all_hashes_present") is True
    checks["visualization_quality_audit_schema"] = (
        visualization_quality.get("schema") == "template_active_inference.visualization_quality_audit.v1"
        and visualization_quality.get("all_figures_complete") is True
        and visualization_quality.get("all_quality_ok") is True
        and visualization_quality.get("all_sources_mapped") is True
        and visualization_quality.get("all_rendered") is True
        and visualization_quality.get("all_accessibility_text_ok") is True
        and visualization_quality.get("all_hashes_present") is True
        and visualization_quality.get("all_visual_roles_present") is True
        and visualization_quality.get("all_evidence_roles_present") is True
        and visualization_quality.get("all_paper_claims_present") is True
        and visualization_quality.get("all_figures_section_bound") is True
        and visualization_quality.get("all_figures_have_claim_lanes") is True
        and visualization_quality.get("all_claim_lanes_valid") is True
        and visualization_quality.get("all_style_tokens_ok") is True
        and visualization_quality.get("all_auxiliary_outputs_classified") is True
        and visualization_quality.get("all_auxiliary_outputs_rendered") is True
        and int(visualization_quality.get("statistically_backed_count", 0) or 0) >= 6
        and visualization_quality.get("all_statistical_sources_present") is True
    )
    checks["statistical_visualization_bridge_schema"] = (
        statistical_bridge.get("schema") == "template_active_inference.statistical_visualization_bridge.v1"
        and int(statistical_bridge.get("row_count", 0) or 0) >= 6
        and statistical_bridge.get("all_rows_connected") is True
        and statistical_bridge.get("all_rows_complete") is True
        and statistical_bridge.get("all_complete") is True
        and statistical_bridge.get("all_statistical_sources_present") is True
        and statistical_bridge.get("all_figures_referenced") is True
        and statistical_bridge.get("all_reference_sections_sheaf_bound") is True
        and statistical_bridge.get("all_reference_sections_visualization_bound") is True
        and statistical_bridge.get("all_sheaf_tracks_registered") is True
        and "statistical_visualization_bridge" in set(statistical_bridge.get("scholarship_method_roles") or [])
    )


def add_canonical_sheaf_checks(checks: dict[str, bool], artifacts: dict[str, dict]) -> None:
    replay_matrix = artifacts["replay_matrix"]
    track_lane_matrix = artifacts["track_lane_matrix"]
    artifact_contract_index = artifacts["artifact_contract_index"]
    track_scope = artifacts["track_scope"]
    blocked_scope = artifacts["blocked_scope"]
    evidence_fields = artifacts["evidence_fields"]
    release_bundle = artifacts["release_bundle"]
    theorem_traceability = artifacts["theorem_traceability"]
    artifact_diffoscope = artifacts["artifact_diffoscope"]
    proof_extraction = artifacts["proof_extraction"]
    state_space_catalog = artifacts["state_space_catalog"]
    causal_ablation = artifacts["causal_ablation"]
    artifact_license = artifacts["artifact_license"]
    release_notes = artifacts["release_notes"]
    scholarship = artifacts["scholarship"]
    security_posture = artifacts["security_posture"]
    proof_dependency = artifacts["proof_dependency"]
    transition_table = artifacts["transition_table"]
    ablation_sensitivity = artifacts["ablation_sensitivity"]
    release_attestation = artifacts["release_attestation"]

    checks["replay_matrix_schema"] = (
        replay_matrix.get("schema") == "template_active_inference.replay_matrix.v1"
        and replay_matrix.get("all_replay_rows_matched") is True
        and replay_matrix.get("all_configured_producers_represented") is True
    )
    checks["track_lane_matrix_schema"] = (
        track_lane_matrix.get("schema") == "template_active_inference.track_lane_matrix.v1"
        and track_lane_matrix.get("matrix_track_ids_match_tracks_yaml") is True
        and track_lane_matrix.get("all_typed_claim_evidence_present") is True
        and track_lane_matrix.get("all_semantic_restrictions_declared") is True
        and track_lane_matrix.get("all_negative_controls_declared") is True
        and track_lane_matrix.get("all_pipeline_tracks_complete") is True
        and track_lane_matrix.get("all_required_pipeline_tracks_complete") is True
    )
    checks["artifact_contract_index_schema"] = (
        artifact_contract_index.get("schema") == "template_active_inference.artifact_contract_index.v1"
        and artifact_contract_index.get("all_artifact_rows_match_semantic_map") is True
        and artifact_contract_index.get("all_rows_complete") is True
        and artifact_contract_index.get("all_claim_required_rows_bound") is True
        and artifact_contract_index.get("all_validators_bound") is True
        and artifact_contract_index.get("all_negative_controls_bound") is True
        and artifact_contract_index.get("all_freshness_hashes_current") is True
        and artifact_contract_index.get("all_copied_parity_complete") is True
    )
    checks["track_improvement_scope_schema"] = (
        track_scope.get("schema") == "template_active_inference.track_improvement_scope.v1"
        and track_scope.get("all_live_tracks_valid") is True
    )
    checks["blocked_scope_manifest_schema"] = (
        blocked_scope.get("schema") == "template_active_inference.blocked_scope_manifest.v1"
        and blocked_scope.get("all_blocked") is True
    )
    checks["evidence_field_index_schema"] = (
        evidence_fields.get("schema") == "template_active_inference.evidence_field_index.v1"
        and evidence_fields.get("all_fields_mapped") is True
    )
    checks["release_bundle_manifest_schema"] = (
        release_bundle.get("schema") == "template_active_inference.release_bundle_manifest.v1"
        and release_bundle.get("all_required_sources_present") is True
        and release_bundle.get("all_copied_outputs_match_or_deferred") is True
    )
    checks["theorem_traceability_matrix_schema"] = (
        theorem_traceability.get("schema") == "template_active_inference.theorem_traceability_matrix.v1"
        and theorem_traceability.get("all_theorems_linked") is True
    )
    checks["artifact_diffoscope_schema"] = (
        artifact_diffoscope.get("schema") == "template_active_inference.artifact_diffoscope.v1"
        and artifact_diffoscope.get("all_equal") is True
    )
    checks["proof_extraction_index_schema"] = (
        proof_extraction.get("schema") == "template_active_inference.proof_extraction_index.v1"
        and proof_extraction.get("all_extracted") is True
        and proof_extraction.get("all_constructive") is True
    )
    checks["state_space_catalog_schema"] = (
        state_space_catalog.get("schema") == "template_active_inference.state_space_catalog.v1"
        and state_space_catalog.get("all_finite") is True
        and state_space_catalog.get("all_counts_positive") is True
    )
    checks["causal_ablation_matrix_schema"] = (
        causal_ablation.get("schema") == "template_active_inference.causal_ablation_matrix.v1"
        and causal_ablation.get("complete_grid") is True
        and causal_ablation.get("all_deterministic") is True
    )
    checks["artifact_license_audit_schema"] = (
        artifact_license.get("schema") == "template_active_inference.artifact_license_audit.v1"
        and artifact_license.get("all_license_safe") is True
    )
    checks["release_notes_evidence_schema"] = (
        release_notes.get("schema") == "template_active_inference.release_notes_evidence.v1"
        and release_notes.get("all_notes_source_backed") is True
    )
    checks["scholarship_source_matrix_schema"] = (
        scholarship.get("schema") == "template_active_inference.scholarship_source_matrix.v1"
        and scholarship.get("all_sources_connected") is True
        and scholarship.get("all_expected_sources_present") is True
        and scholarship.get("all_citations_present") is True
        and scholarship.get("all_claim_boundaries_scope_guarded") is True
        and scholarship.get("all_rows_rederived") is True
    )
    checks["security_posture_audit_schema"] = (
        security_posture.get("schema") == "template_active_inference.security_posture_audit.v1"
        and security_posture.get("all_controls_ok") is True
        and security_posture.get("all_evidence_present") is True
        and security_posture.get("all_validators_bound") is True
        and security_posture.get("all_negative_controls_declared") is True
        and security_posture.get("all_deferred_controls_scoped") is True
        and security_posture.get("all_secret_patterns_absent") is True
        and int(security_posture.get("secret_finding_count", 1) or 0) == 0
        and int(security_posture.get("high_risk_gap_count", 1) or 0) == 0
    )
    checks["proof_dependency_graph_schema"] = (
        proof_dependency.get("schema") == "template_active_inference.proof_dependency_graph.v1"
        and proof_dependency.get("all_theorems_have_dependencies") is True
        and proof_dependency.get("all_edges_resolved") is True
    )
    checks["state_transition_table_schema"] = (
        transition_table.get("schema") == "template_active_inference.state_transition_table.v1"
        and transition_table.get("all_transitions_deterministic") is True
        and transition_table.get("all_reachable_states_covered") is True
    )
    checks["ablation_sensitivity_report_schema"] = (
        ablation_sensitivity.get("schema") == "template_active_inference.ablation_sensitivity_report.v1"
        and ablation_sensitivity.get("all_effects_source_backed") is True
    )
    checks["release_attestation_schema"] = (
        release_attestation.get("schema") == "template_active_inference.release_attestation.v1"
        and release_attestation.get("all_attested") is True
    )


def add_track_validator_checks(root: Path, checks: dict[str, bool], animation_deltas: dict) -> None:
    from roadmap_tracks import (
        validate_formal_interop_artifacts,
        validate_integration_audit_artifacts,
        validate_sheaf_track_artifacts,
        validate_toy_sweep_artifacts,
    )
    from visualizations.animation import validate_animation_frame_deltas

    checks["animation_frame_deltas_schema"] = (
        animation_deltas.get("schema") == "template_active_inference.animation_frame_deltas.v1"
        and animation_deltas.get("all_nonzero") is True
        and not validate_animation_frame_deltas(root)
    )
    checks["toy_sweep_track_schemas"] = not validate_toy_sweep_artifacts(root)
    checks["formal_interop_track_schemas"] = not validate_formal_interop_artifacts(root)
    checks["integration_audit_track_schemas"] = not validate_integration_audit_artifacts(root)
    checks["canonical_sheaf_track_schemas"] = not validate_sheaf_track_artifacts(root)


def set_experiment_plan_metrics(
    root: Path,
    checks: dict[str, bool],
    simulation_context: dict[str, Any],
    spine_context: dict[str, Path],
) -> None:
    summary_path = simulation_context["summary_path"]
    checks["experiment_plan_metrics"] = checks.get("invariants_all_pass", False) and checks.get(
        str(summary_path.relative_to(root)),
        False,
    )
    if simulation_context["si_summary_present"]:
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "si_invariants_all_pass",
            False,
        )
    if simulation_context["comparison_path"].exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "si_policy_comparison_schema",
            False,
        )
    if simulation_context["graph_summary_path"].exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "si_graph_world_schema",
            False,
        )
    if spine_context["crosswalk_path"].exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "sheaf_evidence_crosswalk_schema",
            False,
        )
    if spine_context["dependency_path"].exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "validation_dependency_graph_schema",
            False,
        )
    if spine_context["provenance_path"].exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "artifact_provenance_schema",
            False,
        )
    if spine_context["replay_path"].exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "reproducibility_replay_schema",
            False,
        )
    if spine_context["counterexample_path"].exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "counterexample_matrix_schema",
            False,
        )
    checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and all(
        checks.get(key, False) for key in EXPERIMENT_PLAN_METRIC_KEYS
    )
