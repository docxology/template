"""Validation gates for canonical sheaf-track artifacts."""

from __future__ import annotations

from pathlib import Path

from . import sheaf_tracks as _tracks


def validate_sheaf_track_artifacts(project_root: Path, *, validate_saved_certificate: bool = True) -> list[str]:
    """Validate canonical sheaf-track artifacts and their semantic certificate."""
    root = project_root.resolve()
    issues: list[str] = []
    registry = _tracks._registry_tracks(root)
    versioned = sorted(track_id for track_id in registry if _tracks.VERSIONED_TRACK_RE.search(track_id))
    if versioned:
        issues.append(f"versioned live track ids are not allowed: {', '.join(versioned)}")

    missing_tracks = sorted(set(_tracks.CANONICAL_TRACKS) - set(registry))
    if missing_tracks:
        issues.append(f"missing canonical live tracks: {', '.join(missing_tracks)}")
    bound = _tracks._bound_tracks(root)
    unbound = sorted(track_id for track_id in _tracks.CANONICAL_TRACKS if not bound.get(track_id))
    if unbound:
        issues.append(f"canonical live tracks missing manuscript bindings: {', '.join(unbound)}")

    provenance = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["provenance"])
    if provenance.get("schema") != "template_active_inference.artifact_provenance.v1":
        issues.append("artifact_provenance.json schema mismatch")
    if provenance.get("all_records_complete") is not True or provenance.get("all_bundles_complete") is not True:
        issues.append("artifact_provenance.json has incomplete provenance rows or bundles")

    replay = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["replay_matrix"])
    if replay.get("schema") != "template_active_inference.replay_matrix.v1":
        issues.append("replay_matrix.json schema mismatch")
    if replay.get("all_replay_rows_matched") is not True:
        issues.append("replay_matrix.json records a replay mismatch")

    sensitivity = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["sensitivity"])
    if sensitivity.get("schema") != "template_active_inference.sensitivity_sweep.v1":
        issues.append("sensitivity_sweep.json schema mismatch")
    if sensitivity.get("complete_grid") is not True or sensitivity.get("row_count") != sensitivity.get(
        "expected_cells"
    ):
        issues.append("sensitivity_sweep.json grid is incomplete")

    uncertainty = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["uncertainty"])
    if uncertainty.get("schema") != "template_active_inference.uncertainty_summary.v1":
        issues.append("uncertainty_summary.json schema mismatch")
    if uncertainty.get("all_normalized") is not True or uncertainty.get("all_bins_valid") is not True:
        issues.append("uncertainty_summary.json has invalid bins or unnormalized rows")

    counter = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["counterexample"])
    if counter.get("schema") != "template_active_inference.counterexample_matrix.v1":
        issues.append("counterexample_matrix.json schema mismatch")
    if counter.get("all_expected_failures_observed") is not True:
        issues.append("counterexample_matrix.json has expected-failure fixtures passing")

    model = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["model_checking"])
    if model.get("schema") != "template_active_inference.model_checking_witnesses.v1":
        issues.append("model_checking_witnesses.json schema mismatch")
    if model.get("all_exhaustive") is not True or model.get("all_passed") is not True:
        issues.append("model_checking_witnesses.json missed a finite counterexample")

    interop = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["interop"])
    if interop.get("schema") != "template_active_inference.interop_roundtrip_report.v1":
        issues.append("interop_roundtrip_report.json schema mismatch")
    if interop.get("all_lossless") is not True or interop.get("all_shape_diffs_empty") is not True:
        issues.append("interop_roundtrip_report.json is not lossless")

    adversarial = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["adversarial_audit"])
    if adversarial.get("schema") != "template_active_inference.adversarial_audit.v1":
        issues.append("adversarial_audit.json schema mismatch")
    if adversarial.get("all_expected_failures_observed") is not True or adversarial.get("known_bad_rows_passed") != 0:
        issues.append("adversarial_audit.json has known-bad rows passing")

    dependency = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["dependency"])
    if dependency.get("schema") != _tracks.DEPENDENCY_SCHEMA:
        issues.append("validation_dependency_graph.json schema mismatch")
    if dependency.get("all_required_edge_types_present") is not True:
        issues.append("validation_dependency_graph.json lacks required edge types")

    section_status = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["section_status"])
    if section_status.get("schema") != "template_active_inference.sheaf_section_status_matrix.v1":
        issues.append("sheaf_section_status_matrix.json schema mismatch")
    if section_status.get("all_bound_fragments_present") is not True:
        issues.append("sheaf_section_status_matrix.json has missing bound fragments")
    if (
        section_status.get("all_sections_have_status") is not True
        or section_status.get("all_tracks_have_status") is not True
    ):
        issues.append("sheaf_section_status_matrix.json has incomplete status rows")

    render_log = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["render_log"])
    if render_log.get("schema") != "template_active_inference.sheaf_render_log.v1":
        issues.append("sheaf_render_log.json schema mismatch")
    if render_log.get("all_events_ok") is not True:
        issues.append("sheaf_render_log.json has failed render events")

    scope = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["track_improvement_scope"])
    if scope.get("schema") != "template_active_inference.track_improvement_scope.v1":
        issues.append("track_improvement_scope.json schema mismatch")
    if scope.get("all_live_tracks_valid") is not True:
        issues.append("track_improvement_scope.json has incomplete live-track promotion rows")

    blocked = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["blocked_scope_manifest"])
    if blocked.get("schema") != "template_active_inference.blocked_scope_manifest.v1":
        issues.append("blocked_scope_manifest.json schema mismatch")
    if blocked.get("all_blocked") is not True:
        issues.append("blocked_scope_manifest.json does not keep empirical scope blocked")

    evidence = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["evidence_fields"])
    if evidence.get("schema") != "template_active_inference.evidence_field_index.v1":
        issues.append("evidence_field_index.json schema mismatch")
    if evidence.get("all_fields_mapped") is not True:
        issues.append("evidence_field_index.json has unmapped evidence fields")

    release = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["release_bundle"])
    if release.get("schema") != "template_active_inference.release_bundle_manifest.v1":
        issues.append("release_bundle_manifest.json schema mismatch")
    if release.get("all_required_sources_present") is not True:
        issues.append("release_bundle_manifest.json is missing required deliverables")

    theorem = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["theorem_traceability"])
    if theorem.get("schema") != "template_active_inference.theorem_traceability_matrix.v1":
        issues.append("theorem_traceability_matrix.json schema mismatch")
    if theorem.get("all_theorems_linked") is not True:
        issues.append("theorem_traceability_matrix.json has unlinked theorem rows")

    gate_index = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["gate_ergonomics"])
    if gate_index.get("all_indexed") is not True:
        issues.append("validation_gate_index.json has unindexed gates")

    diffoscope = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["artifact_diffoscope"])
    if diffoscope.get("schema") != "template_active_inference.artifact_diffoscope.v1":
        issues.append("artifact_diffoscope.json schema mismatch")
    if diffoscope.get("all_equal") is not True:
        issues.append("artifact_diffoscope.json records artifact drift")

    proof = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["proof_extraction"])
    if proof.get("schema") != "template_active_inference.proof_extraction_index.v1":
        issues.append("proof_extraction_index.json schema mismatch")
    if proof.get("all_extracted") is not True or proof.get("all_constructive") is not True:
        issues.append("proof_extraction_index.json has missing statements or nonconstructive tokens")

    catalog = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["state_space_catalog"])
    if catalog.get("schema") != "template_active_inference.state_space_catalog.v1":
        issues.append("state_space_catalog.json schema mismatch")
    if catalog.get("all_finite") is not True or catalog.get("all_counts_positive") is not True:
        issues.append("state_space_catalog.json has missing finite spaces")

    ablation = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["causal_ablation"])
    if ablation.get("schema") != "template_active_inference.causal_ablation_matrix.v1":
        issues.append("causal_ablation_matrix.json schema mismatch")
    if ablation.get("complete_grid") is not True or ablation.get("all_deterministic") is not True:
        issues.append("causal_ablation_matrix.json has incomplete deterministic rows")

    license_audit = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["artifact_license"])
    if license_audit.get("schema") != "template_active_inference.artifact_license_audit.v1":
        issues.append("artifact_license_audit.json schema mismatch")
    if license_audit.get("all_license_safe") is not True:
        issues.append("artifact_license_audit.json records unsafe artifacts")

    release_notes = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["release_notes"])
    if release_notes.get("schema") != "template_active_inference.release_notes_evidence.v1":
        issues.append("release_notes_evidence.json schema mismatch")
    if release_notes.get("all_notes_source_backed") is not True:
        issues.append("release_notes_evidence.json has unsupported notes")

    restrictions = _tracks._canonical_restrictions(root)
    false_restrictions = sorted(key for key, ok in restrictions.items() if not ok)
    if false_restrictions:
        issues.append(f"canonical semantic restrictions failed: {', '.join(false_restrictions)}")

    if validate_saved_certificate:
        semantic = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["semantic"])
        if semantic.get("schema") != _tracks.SEMANTIC_SCHEMA:
            issues.append("sheaf_gluing_certificate.json schema mismatch")
        if semantic.get("ok") is not True:
            issues.append("sheaf_gluing_certificate.json is not ok")
        saved_restrictions = semantic.get("restrictions") or {}
        for key, expected in restrictions.items():
            if saved_restrictions.get(key) != expected:
                issues.append("sheaf_gluing_certificate.json is stale relative to canonical restrictions")
                break

    if "empirical_adapter" in registry:
        issues.append("empirical_adapter blocked track was promoted live")
    return issues
