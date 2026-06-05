"""Validation gates for canonical sheaf-track artifacts."""

from __future__ import annotations

from pathlib import Path

from . import sheaf_tracks as _tracks
from .supplemental import validate_supplemental_artifacts


def _all_rows(payload: dict, field: str) -> bool:
    rows = payload.get("rows") or []
    return bool(rows) and all(row.get(field) for row in rows)


def _all_rows_absent(payload: dict, field: str) -> bool:
    rows = payload.get("rows") or []
    return bool(rows) and all(not row.get(field) for row in rows)


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
    replay_rows_matched = _all_rows(replay, "matched")
    if (
        replay.get("all_replay_rows_matched") is not True
        or replay.get("all_replay_rows_matched") != replay_rows_matched
    ):
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
    uncertainty_normalized = _all_rows(uncertainty, "normalized")
    valid_bins = set((uncertainty.get("bins") or {}).keys())
    uncertainty_bins_valid = bool(uncertainty.get("rows")) and all(
        row.get("bin") in valid_bins for row in uncertainty.get("rows") or []
    )
    if (
        uncertainty.get("all_normalized") is not True
        or uncertainty.get("all_normalized") != uncertainty_normalized
        or uncertainty.get("all_bins_valid") is not True
        or uncertainty.get("all_bins_valid") != uncertainty_bins_valid
    ):
        issues.append("uncertainty_summary.json has invalid bins or unnormalized rows")

    counter = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["counterexample"])
    if counter.get("schema") != "template_active_inference.counterexample_matrix.v1":
        issues.append("counterexample_matrix.json schema mismatch")
    counter_observed = bool(counter.get("rows")) and all(
        row.get("fixture_replay_status") == "expected_failure_observed" for row in counter.get("rows") or []
    )
    if (
        counter.get("all_expected_failures_observed") is not True
        or counter.get("all_expected_failures_observed") != counter_observed
    ):
        issues.append("counterexample_matrix.json has expected-failure fixtures passing")

    model = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["model_checking"])
    if model.get("schema") != "template_active_inference.model_checking_witnesses.v1":
        issues.append("model_checking_witnesses.json schema mismatch")
    model_exhaustive = _all_rows(model, "exhaustive")
    model_passed = bool(model.get("rows")) and all(
        row.get("passed") and not row.get("counterexamples") for row in model.get("rows") or []
    )
    if (
        model.get("all_exhaustive") is not True
        or model.get("all_exhaustive") != model_exhaustive
        or model.get("all_passed") is not True
        or model.get("all_passed") != model_passed
    ):
        issues.append("model_checking_witnesses.json missed a finite counterexample")

    interop = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["interop"])
    if interop.get("schema") != "template_active_inference.interop_roundtrip_report.v1":
        issues.append("interop_roundtrip_report.json schema mismatch")
    interop_lossless = _all_rows(interop, "lossless")
    interop_shapes_empty = _all_rows_absent(interop, "shape_diff")
    if (
        interop.get("all_lossless") is not True
        or interop.get("all_lossless") != interop_lossless
        or interop.get("all_shape_diffs_empty") is not True
        or interop.get("all_shape_diffs_empty") != interop_shapes_empty
    ):
        issues.append("interop_roundtrip_report.json is not lossless")

    adversarial = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["adversarial_audit"])
    if adversarial.get("schema") != "template_active_inference.adversarial_audit.v1":
        issues.append("adversarial_audit.json schema mismatch")
    adversarial_observed = bool(adversarial.get("rows")) and all(
        row.get("expected_failure") and row.get("observed") == "expected_failure"
        for row in adversarial.get("rows") or []
    )
    known_bad_passed = sum(1 for row in adversarial.get("rows") or [] if row.get("known_bad_passed"))
    if (
        adversarial.get("all_expected_failures_observed") is not True
        or adversarial.get("all_expected_failures_observed") != adversarial_observed
        or adversarial.get("known_bad_rows_passed") != known_bad_passed
        or known_bad_passed != 0
    ):
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
    blocked_rows_ok = bool(blocked.get("rows")) and all(
        row.get("status") == "blocked"
        and row.get("no_live_registry_entry")
        and row.get("no_configured_producer")
        and row.get("no_empirical_result_artifact")
        for row in blocked.get("rows") or []
    )
    if blocked.get("all_blocked") is not True or blocked.get("all_blocked") != blocked_rows_ok:
        issues.append("blocked_scope_manifest.json does not keep empirical scope blocked")

    evidence = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["evidence_fields"])
    if evidence.get("schema") != "template_active_inference.evidence_field_index.v1":
        issues.append("evidence_field_index.json schema mismatch")
    evidence_fields_mapped = bool(evidence.get("rows")) and all(
        row.get("artifact") and row.get("field_present") and row.get("claim_id") for row in evidence.get("rows") or []
    )
    if evidence.get("all_fields_mapped") is not True or evidence.get("all_fields_mapped") != evidence_fields_mapped:
        issues.append("evidence_field_index.json has unmapped evidence fields")

    release = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["release_bundle"])
    if release.get("schema") != "template_active_inference.release_bundle_manifest.v1":
        issues.append("release_bundle_manifest.json schema mismatch")
    if release.get("all_required_sources_present") is not True:
        issues.append("release_bundle_manifest.json is missing required deliverables")

    theorem = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["theorem_traceability"])
    if theorem.get("schema") != "template_active_inference.theorem_traceability_matrix.v1":
        issues.append("theorem_traceability_matrix.json schema mismatch")
    theorem_linked = _all_rows(theorem, "linked")
    if theorem.get("all_theorems_linked") is not True or theorem.get("all_theorems_linked") != theorem_linked:
        issues.append("theorem_traceability_matrix.json has unlinked theorem rows")

    gate_index = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["gate_ergonomics"])
    gate_indexed = _all_rows(gate_index, "indexed")
    if gate_index.get("all_indexed") is not True or gate_index.get("all_indexed") != gate_indexed:
        issues.append("validation_gate_index.json has unindexed gates")

    diffoscope = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["artifact_diffoscope"])
    if diffoscope.get("schema") != "template_active_inference.artifact_diffoscope.v1":
        issues.append("artifact_diffoscope.json schema mismatch")
    diffoscope_equal = _all_rows(diffoscope, "equal")
    if diffoscope.get("all_equal") is not True or diffoscope.get("all_equal") != diffoscope_equal:
        issues.append("artifact_diffoscope.json records artifact drift")

    proof = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["proof_extraction"])
    if proof.get("schema") != "template_active_inference.proof_extraction_index.v1":
        issues.append("proof_extraction_index.json schema mismatch")
    proof_extracted = _all_rows(proof, "extracted")
    proof_constructive = bool(proof.get("rows")) and all(
        not row.get("forbidden_tokens") for row in proof.get("rows") or []
    )
    if (
        proof.get("all_extracted") is not True
        or proof.get("all_extracted") != proof_extracted
        or proof.get("all_constructive") is not True
        or proof.get("all_constructive") != proof_constructive
    ):
        issues.append("proof_extraction_index.json has missing statements or nonconstructive tokens")

    catalog = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["state_space_catalog"])
    if catalog.get("schema") != "template_active_inference.state_space_catalog.v1":
        issues.append("state_space_catalog.json schema mismatch")
    catalog_finite = _all_rows(catalog, "finite")
    catalog_counts_positive = bool(catalog.get("rows")) and all(
        int(row.get("state_count", 0) or 0) > 0 and int(row.get("policy_count", 0) or 0) >= 1
        for row in catalog.get("rows") or []
    )
    if (
        catalog.get("all_finite") is not True
        or catalog.get("all_finite") != catalog_finite
        or catalog.get("all_counts_positive") is not True
        or catalog.get("all_counts_positive") != catalog_counts_positive
    ):
        issues.append("state_space_catalog.json has missing finite spaces")

    ablation = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["causal_ablation"])
    if ablation.get("schema") != "template_active_inference.causal_ablation_matrix.v1":
        issues.append("causal_ablation_matrix.json schema mismatch")
    ablation_deterministic = _all_rows(ablation, "deterministic")
    ablation_complete = len(ablation.get("rows") or []) == int(ablation.get("expected_cells", -1) or -1)
    if (
        ablation.get("complete_grid") is not True
        or ablation.get("complete_grid") != ablation_complete
        or ablation.get("all_deterministic") is not True
        or ablation.get("all_deterministic") != ablation_deterministic
    ):
        issues.append("causal_ablation_matrix.json has incomplete deterministic rows")

    license_audit = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["artifact_license"])
    if license_audit.get("schema") != "template_active_inference.artifact_license_audit.v1":
        issues.append("artifact_license_audit.json schema mismatch")
    license_safe = bool(license_audit.get("rows")) and all(
        row.get("license_safe") and row.get("license") for row in license_audit.get("rows") or []
    )
    if license_audit.get("all_license_safe") is not True or license_audit.get("all_license_safe") != license_safe:
        issues.append("artifact_license_audit.json records unsafe artifacts")

    release_notes = _tracks._load_json(root / _tracks.CANONICAL_ARTIFACTS["release_notes"])
    if release_notes.get("schema") != "template_active_inference.release_notes_evidence.v1":
        issues.append("release_notes_evidence.json schema mismatch")
    notes_backed = bool(release_notes.get("rows")) and all(
        row.get("source") and row.get("passed") for row in release_notes.get("rows") or []
    )
    if (
        release_notes.get("all_notes_source_backed") is not True
        or release_notes.get("all_notes_source_backed") != notes_backed
    ):
        issues.append("release_notes_evidence.json has unsupported notes")

    from .scholarship import validate_scholarship_source_matrix

    issues.extend(validate_scholarship_source_matrix(root))

    issues.extend(validate_supplemental_artifacts(root))

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
