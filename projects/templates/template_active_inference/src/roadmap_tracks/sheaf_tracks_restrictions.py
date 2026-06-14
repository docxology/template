"""Canonical restriction snapshot for semantic gluing gates."""

from __future__ import annotations

import re
from pathlib import Path

from roadmap_tracks.sheaf_tracks_io import (
    _bound_tracks,
    _bridge_reference_section_status,
    _claim_ids_by_path,
    _load_json,
    _registry_tracks,
)
from roadmap_tracks.sheaf_tracks_registry import CANONICAL_ARTIFACTS, CANONICAL_TRACKS, VERSIONED_TRACK_RE


def _canonical_restrictions(root: Path) -> dict[str, bool]:
    registry = _registry_tracks(root)
    bound = _bound_tracks(root)
    provenance = _load_json(root / CANONICAL_ARTIFACTS["provenance"])
    replay = _load_json(root / CANONICAL_ARTIFACTS["replay_matrix"])
    sensitivity = _load_json(root / CANONICAL_ARTIFACTS["sensitivity"])
    uncertainty = _load_json(root / CANONICAL_ARTIFACTS["uncertainty"])
    counter = _load_json(root / CANONICAL_ARTIFACTS["counterexample"])
    model = _load_json(root / CANONICAL_ARTIFACTS["model_checking"])
    interop = _load_json(root / CANONICAL_ARTIFACTS["interop"])
    adversarial = _load_json(root / CANONICAL_ARTIFACTS["adversarial_audit"])
    dependency = _load_json(root / CANONICAL_ARTIFACTS["dependency"])
    track_lane = _load_json(root / CANONICAL_ARTIFACTS["track_lane_matrix"])
    artifact_contract = _load_json(root / CANONICAL_ARTIFACTS["artifact_contract_index"])
    scope = _load_json(root / CANONICAL_ARTIFACTS["track_improvement_scope"])
    section_status = _load_json(root / CANONICAL_ARTIFACTS["section_status"])
    render_log = _load_json(root / CANONICAL_ARTIFACTS["render_log"])
    blocked = _load_json(root / CANONICAL_ARTIFACTS["blocked_scope_manifest"])
    evidence = _load_json(root / CANONICAL_ARTIFACTS["evidence_fields"])
    release = _load_json(root / CANONICAL_ARTIFACTS["release_bundle"])
    theorem = _load_json(root / CANONICAL_ARTIFACTS["theorem_traceability"])
    gate_index = _load_json(root / CANONICAL_ARTIFACTS["gate_ergonomics"])
    diffoscope = _load_json(root / CANONICAL_ARTIFACTS["artifact_diffoscope"])
    proof = _load_json(root / CANONICAL_ARTIFACTS["proof_extraction"])
    catalog = _load_json(root / CANONICAL_ARTIFACTS["state_space_catalog"])
    ablation = _load_json(root / CANONICAL_ARTIFACTS["causal_ablation"])
    license_audit = _load_json(root / CANONICAL_ARTIFACTS["artifact_license"])
    release_notes = _load_json(root / CANONICAL_ARTIFACTS["release_notes"])
    scholarship = _load_json(root / CANONICAL_ARTIFACTS["scholarship"])
    security_posture = _load_json(root / CANONICAL_ARTIFACTS["security_posture"])
    visualization_quality = _load_json(root / "output" / "reports" / "visualization_quality_audit.json")
    statistical_bridge = _load_json(root / CANONICAL_ARTIFACTS["statistical_visualization_bridge"])
    proof_dependency = _load_json(root / CANONICAL_ARTIFACTS["proof_dependency_graph"])
    transition = _load_json(root / CANONICAL_ARTIFACTS["state_transition_table"])
    ablation_sensitivity = _load_json(root / CANONICAL_ARTIFACTS["ablation_sensitivity_report"])
    release_attestation = _load_json(root / CANONICAL_ARTIFACTS["release_attestation"])
    claims_by_path = _claim_ids_by_path(root)
    visualization_rows = visualization_quality.get("rows") or []
    visualization_rows_ok = bool(visualization_rows) and all(row.get("quality_ok") for row in visualization_rows)
    from roadmap_tracks.visualization_audit import (
        ALLOWED_EVIDENCE_ROLES,
        ALLOWED_VISUAL_ROLES,
        MIN_PAPER_CLAIM_WORDS,
    )

    visualization_visual_roles_ok = bool(visualization_rows) and all(
        row.get("visual_role") in ALLOWED_VISUAL_ROLES and row.get("visual_role_ok") is True
        for row in visualization_rows
    )
    visualization_evidence_roles_ok = bool(visualization_rows) and all(
        row.get("evidence_role") in ALLOWED_EVIDENCE_ROLES and row.get("evidence_role_ok") is True
        for row in visualization_rows
    )
    visualization_claim_rows_ok = bool(visualization_rows) and all(
        len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", str(row.get("paper_claim", "")))) >= MIN_PAPER_CLAIM_WORDS
        and row.get("paper_claim_ok") is True
        for row in visualization_rows
    )
    visualization_section_rows_ok = bool(visualization_rows) and all(
        bool(row.get("section_bindings")) and row.get("section_bound") is True for row in visualization_rows
    )
    visualization_intent_ok = (
        visualization_quality.get("all_visual_roles_present") is True
        and visualization_quality.get("all_evidence_roles_present") is True
        and visualization_visual_roles_ok
        and visualization_evidence_roles_ok
    )
    visualization_claims_ok = (
        visualization_quality.get("all_paper_claims_present") is True and visualization_claim_rows_ok
    )
    visualization_sections_ok = (
        visualization_quality.get("all_figures_section_bound") is True and visualization_section_rows_ok
    )
    statistical_visualization_rows = [row for row in visualization_rows if row.get("statistical_sources")]
    statistically_backed_count = sum(1 for row in statistical_visualization_rows if row.get("statistically_backed"))
    statistical_visualizations_ok = (
        len(statistical_visualization_rows) >= 6
        and visualization_quality.get("statistically_backed_count") == statistically_backed_count
        and visualization_quality.get("all_statistical_sources_present") is True
        and all(
            row.get("statistical_sources_present") and row.get("statistically_backed")
            for row in statistical_visualization_rows
        )
    )
    statistical_bridge_rows = statistical_bridge.get("rows") or []
    statistical_bridge_reference_status = [_bridge_reference_section_status(row) for row in statistical_bridge_rows]
    statistical_bridge_references_sheaf_bound = bool(statistical_bridge_rows) and all(
        row.get("reference_sections_sheaf_bound") is True and status[0]
        for row, status in zip(statistical_bridge_rows, statistical_bridge_reference_status, strict=True)
    )
    statistical_bridge_references_visualization_bound = bool(statistical_bridge_rows) and all(
        row.get("reference_sections_visualization_bound") is True and status[1]
        for row, status in zip(statistical_bridge_rows, statistical_bridge_reference_status, strict=True)
    )
    statistical_bridge_rows_connected = bool(statistical_bridge_rows) and all(
        row.get("connected")
        and row.get("statistical_sources_present")
        and row.get("sheaf_tracks_registered")
        and row.get("referenced_in_manuscript")
        and row.get("reference_sections_sheaf_bound")
        and row.get("reference_sections_visualization_bound")
        for row in statistical_bridge_rows
    )
    statistical_crosswalk_ok = (
        statistical_bridge.get("schema") == "template_active_inference.statistical_visualization_bridge.v1"
        and statistical_bridge.get("row_count") == statistically_backed_count
        and statistical_bridge.get("all_rows_connected") is True
        and statistical_bridge_rows_connected
        and statistical_bridge.get("all_statistical_sources_present") is True
        and statistical_bridge.get("all_figures_referenced") is True
        and statistical_bridge.get("all_reference_sections_sheaf_bound") is True
        and statistical_bridge_references_sheaf_bound
        and statistical_bridge.get("all_reference_sections_visualization_bound") is True
        and statistical_bridge_references_visualization_bound
        and statistical_bridge.get("all_sheaf_tracks_registered") is True
        and "statistical_visualization_bridge" in set(statistical_bridge.get("scholarship_method_roles") or [])
    )
    return {
        "no_versioned_live_tracks": not any(VERSIONED_TRACK_RE.search(track_id) for track_id in registry),
        "all_canonical_tracks_registered": set(CANONICAL_TRACKS).issubset(registry),
        "all_canonical_tracks_bound": all(bound.get(track_id) for track_id in CANONICAL_TRACKS),
        "artifact_provenance_complete": provenance.get("all_records_complete") is True
        and provenance.get("all_bundles_complete") is True,
        "artifact_field_provenance_complete": provenance.get("all_field_provenance_complete") is True,
        "producer_coverage_complete": provenance.get("all_producers_configured") is True,
        "replay_matrix_all_matched": replay.get("all_replay_rows_matched") is True
        and replay.get("all_configured_producers_represented") is True,
        "sensitivity_complete_grid": sensitivity.get("complete_grid") is True
        and sensitivity.get("all_finite_bounds_ok") is True,
        "uncertainty_normalized": uncertainty.get("all_normalized") is True
        and uncertainty.get("all_bins_valid") is True,
        "counterexamples_fail_as_expected": counter.get("all_expected_failures_observed") is True,
        "model_checking_exhaustive": model.get("all_exhaustive") is True and model.get("all_passed") is True,
        "interop_lossless": interop.get("all_lossless") is True and interop.get("all_shape_diffs_empty") is True,
        "adversarial_expected_failures": adversarial.get("all_expected_failures_observed") is True
        and int(adversarial.get("known_bad_rows_passed", 1) or 0) == 0,
        "dependency_edge_types_complete": dependency.get("all_required_edge_types_present") is True,
        "dependency_field_edges_mapped": dependency.get("all_field_edges_mapped") is True,
        "track_lane_matrix_complete": track_lane.get("all_pipeline_tracks_complete") is True
        and track_lane.get("matrix_track_ids_match_tracks_yaml") is True,
        "artifact_contract_index_complete": artifact_contract.get("all_rows_complete") is True
        and artifact_contract.get("all_artifact_rows_match_semantic_map") is True
        and artifact_contract.get("all_claim_required_rows_bound") is True
        and artifact_contract.get("all_validators_bound") is True
        and artifact_contract.get("all_negative_controls_bound") is True
        and artifact_contract.get("all_freshness_hashes_current") is True,
        "artifact_contract_copied_parity_complete": artifact_contract.get("all_copied_parity_complete") is True,
        "section_status_all_bound_present": section_status.get("all_bound_fragments_present") is True,
        "section_status_all_rows_indexed": section_status.get("all_sections_have_status") is True
        and section_status.get("all_tracks_have_status") is True,
        "sheaf_render_log_all_events_ok": render_log.get("all_events_ok") is True,
        "track_scope_complete": scope.get("all_live_tracks_valid") is True,
        "blocked_empirical_scope": blocked.get("all_blocked") is True and "empirical_adapter" not in registry,
        "evidence_fields_mapped": evidence.get("all_fields_mapped") is True,
        "release_bundle_sources_present": release.get("all_required_sources_present") is True,
        "release_bundle_parity_ok": release.get("all_copied_outputs_match_or_deferred") is True,
        "theorem_traceability_linked": theorem.get("all_theorems_linked") is True,
        "gate_ergonomics_indexed": gate_index.get("all_indexed") is True,
        "artifact_diffoscope_equal": diffoscope.get("all_equal") is True,
        "proof_extraction_constructive": proof.get("all_extracted") is True and proof.get("all_constructive") is True,
        "state_spaces_finite": catalog.get("all_finite") is True and catalog.get("all_counts_positive") is True,
        "causal_ablation_complete": ablation.get("complete_grid") is True and ablation.get("all_deterministic") is True,
        "artifact_license_safe": license_audit.get("all_license_safe") is True,
        "release_notes_source_backed": release_notes.get("all_notes_source_backed") is True,
        "scholarship_sources_connected": scholarship.get("all_sources_connected") is True
        and scholarship.get("all_expected_sources_present") is True,
        "security_posture_controls_ok": security_posture.get("all_controls_ok") is True
        and security_posture.get("all_evidence_present") is True,
        "security_posture_secret_patterns_absent": security_posture.get("all_secret_patterns_absent") is True,
        "security_posture_no_high_risk_gaps": int(security_posture.get("high_risk_gap_count", 1) or 0) == 0,
        "visualization_quality_ok": visualization_quality.get("all_quality_ok") is True
        and visualization_rows_ok
        and visualization_quality.get("all_sources_mapped") is True
        and visualization_quality.get("all_rendered") is True
        and visualization_quality.get("all_style_tokens_ok") is True
        and visualization_quality.get("all_auxiliary_outputs_classified") is True
        and visualization_quality.get("all_auxiliary_outputs_rendered") is True
        and visualization_intent_ok
        and visualization_claims_ok
        and visualization_sections_ok,
        "visualization_intent_metadata_complete": visualization_intent_ok,
        "visualization_paper_claims_complete": visualization_claims_ok,
        "visualization_figures_section_bound": visualization_sections_ok,
        "visualization_statistics_bridge_ok": statistical_visualizations_ok,
        "statistical_visualization_crosswalk_ok": statistical_crosswalk_ok,
        "statistical_visualization_figures_referenced": statistical_bridge.get("all_figures_referenced") is True,
        "statistical_visualization_reference_sections_sheaf_bound": (
            statistical_bridge.get("all_reference_sections_sheaf_bound") is True
            and statistical_bridge_references_sheaf_bound
        ),
        "statistical_visualization_reference_sections_visualization_bound": (
            statistical_bridge.get("all_reference_sections_visualization_bound") is True
            and statistical_bridge_references_visualization_bound
        ),
        "proof_dependency_graph_resolved": proof_dependency.get("all_theorems_have_dependencies") is True
        and proof_dependency.get("all_edges_resolved") is True,
        "state_transition_table_complete": transition.get("all_transitions_deterministic") is True
        and transition.get("all_reachable_states_covered") is True,
        "ablation_sensitivity_source_backed": ablation_sensitivity.get("all_effects_source_backed") is True,
        "release_attestation_complete": release_attestation.get("all_attested") is True,
        "all_canonical_artifacts_have_claims": all(claims_by_path.get(rel) for rel in CANONICAL_ARTIFACTS.values()),
    }
