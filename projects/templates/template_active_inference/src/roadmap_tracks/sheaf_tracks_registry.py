"""Canonical sheaf-track registry constants."""

from __future__ import annotations

import re

SHEAF_TRACK_PRODUCER = "generate_sheaf_tracks.py"
CANONICAL_SCHEMA = "template_active_inference.canonical_sheaf_tracks.v1"
SEMANTIC_SCHEMA = "template_active_inference.semantic_gluing.v2"
DEPENDENCY_SCHEMA = "template_active_inference.validation_dependency_graph.v1"
VERSIONED_TRACK_RE = re.compile(r"(?:^|_)v[2-9]$")

CANONICAL_TRACKS: tuple[str, ...] = (
    "provenance",
    "replay_matrix",
    "sensitivity",
    "uncertainty",
    "counterexample",
    "model_checking",
    "interop",
    "adversarial_audit",
    "evidence_fields",
    "release_bundle",
    "theorem_traceability",
    "gate_ergonomics",
    "scholarship",
    "security_posture",
    "artifact_diffoscope",
    "proof_extraction",
    "state_space_catalog",
    "causal_ablation",
    "artifact_license",
    "release_notes",
)

CANONICAL_ARTIFACTS: dict[str, str] = {
    "provenance": "output/data/artifact_provenance.json",
    "replay_matrix": "output/reports/replay_matrix.json",
    "sensitivity": "output/data/sensitivity_sweep.json",
    "uncertainty": "output/data/uncertainty_summary.json",
    "counterexample": "output/reports/counterexample_matrix.json",
    "model_checking": "output/reports/model_checking_witnesses.json",
    "interop": "output/data/interop_roundtrip_report.json",
    "adversarial_audit": "output/reports/adversarial_audit.json",
    "semantic": "output/data/sheaf_gluing_certificate.json",
    "dependency": "output/data/validation_dependency_graph.json",
    "section_status": "output/data/sheaf_section_status_matrix.json",
    "render_log": "output/reports/sheaf_render_log.json",
    "track_lane_matrix": "output/data/track_lane_matrix.json",
    "artifact_contract_index": "output/data/artifact_contract_index.json",
    "track_improvement_scope": "output/data/track_improvement_scope.json",
    "blocked_scope_manifest": "output/reports/blocked_scope_manifest.json",
    "evidence_fields": "output/data/evidence_field_index.json",
    "release_bundle": "output/reports/release_bundle_manifest.json",
    "theorem_traceability": "output/data/theorem_traceability_matrix.json",
    "gate_ergonomics": "output/data/validation_gate_index.json",
    "scholarship": "output/data/scholarship_source_matrix.json",
    "security_posture": "output/reports/security_posture_audit.json",
    "artifact_diffoscope": "output/reports/artifact_diffoscope.json",
    "proof_extraction": "output/data/proof_extraction_index.json",
    "state_space_catalog": "output/data/state_space_catalog.json",
    "causal_ablation": "output/data/causal_ablation_matrix.json",
    "artifact_license": "output/reports/artifact_license_audit.json",
    "release_notes": "output/reports/release_notes_evidence.json",
    "statistical_visualization_bridge": "output/data/statistical_visualization_bridge.json",
    "proof_dependency_graph": "output/data/proof_dependency_graph.json",
    "state_transition_table": "output/data/state_transition_table.json",
    "ablation_sensitivity_report": "output/reports/ablation_sensitivity_report.json",
    "release_attestation": "output/reports/release_attestation.json",
}

LEGACY_ARTIFACTS: tuple[str, ...] = (
    "output/data/artifact_lineage_v2.json",
    "output/data/artifact_bundle_lineage_v3.json",
    "output/data/sensitivity_sweep_v2.json",
    "output/data/sensitivity_sweep_v3.json",
    "output/data/uncertainty_summary_v2.json",
    "output/data/uncertainty_calibration_v3.json",
    "output/reports/counterexample_matrix_v2.json",
    "output/reports/counterexample_fixture_matrix_v3.json",
    "output/reports/model_checking_witnesses_v2.json",
    "output/reports/model_checking_witnesses_v3.json",
    "output/data/interop_roundtrip_v2.json",
    "output/data/interop_roundtrip_v3.json",
    "output/reports/adversarial_audit_v2.json",
    "output/reports/adversarial_probe_matrix_v3.json",
    "output/reports/replay_matrix_v2.json",
    "output/data/sheaf_gluing_certificate_v3.json",
    "output/data/sheaf_gluing_certificate_v4.json",
    "output/data/sheaf_gluing_certificate_v5.json",
    "output/data/validation_dependency_graph_v2.json",
    "output/data/validation_dependency_graph_v3.json",
    "output/data/validation_dependency_graph_v4.json",
    "output/data/track_improvement_scope_v2.json",
    "output/reports/blocked_scope_manifest_v2.json",
)

REQUIRED_EDGE_TYPES: tuple[str, ...] = (
    "producer_to_track",
    "track_to_artifact",
    "artifact_to_bundle",
    "artifact_to_token",
    "token_to_claim",
    "claim_to_section",
    "validator_to_negative_control",
    "fixture_to_expected_failure",
    "model_to_witness",
    "ontology_to_roundtrip",
    "figure_to_source",
    "scholarship_to_method",
    "scholarship_to_artifact",
    "output_to_copied_output",
)

OPTIONAL_CLAIM_EXEMPT_TRACKS: set[str] = {
    "prose",
    "formalism",
    "simulation",
    "layers",
    "visualization",
    "animation",
    "animation_delta",
    "manuscript_staleness",
}

PIPELINE_TRACK_SHEAF_ALIASES: dict[str, tuple[str, ...]] = {
    "analytical": ("formalism", "simulation", "assumption_index"),
    "visualizations": ("visualization",),
    "manuscript": ("prose", "formalism", "layers"),
}
