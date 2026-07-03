"""Canonical sheaf-track surface tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from gate_support import (
    ensure_gate_artifacts,
    temporary_json_mutation,
    temporary_text_mutation,
    temporary_yaml_mutation,
)
from track_consolidation_support import (
    VERSIONED_TRACK_RE,
    _load,
    _relative_posix,
    _set_value,
    _write,
)

pytestmark = [pytest.mark.timeout(600)]


def test_sheaf_track_source_commit_times_out_to_unknown(project_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from roadmap_tracks import sheaf_tracks

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

    monkeypatch.setattr("roadmap_tracks.sheaf_tracks_io.subprocess.run", fake_run)

    assert sheaf_tracks._source_commit(project_root) == "unknown"


def test_temporary_json_mutation_restores_after_exception(tmp_path: Path) -> None:
    path = tmp_path / "artifact.json"
    original = {"ok": True, "rows": [{"passed": True}]}
    _write(path, original)

    with pytest.raises(RuntimeError, match="forced failure"):
        with temporary_json_mutation(path, _set_value(("rows", 0, "passed"), False)):
            assert _load(path)["rows"][0]["passed"] is False
            raise RuntimeError("forced failure")

    assert _load(path) == original


def test_text_and_yaml_mutation_helpers_restore_after_exception(tmp_path: Path) -> None:
    text_path = tmp_path / "note.md"
    yaml_path = tmp_path / "config.yaml"
    text_original = "alpha: keep\n"
    yaml_original = "tracks:\n  prose:\n    renderer: markdown\n"
    text_path.write_text(text_original, encoding="utf-8")
    yaml_path.write_text(yaml_original, encoding="utf-8")

    with pytest.raises(RuntimeError, match="text failure"):
        with temporary_text_mutation(text_path, lambda text: text.replace("keep", "break")):
            assert text_path.read_text(encoding="utf-8") == "alpha: break\n"
            raise RuntimeError("text failure")

    with pytest.raises(RuntimeError, match="yaml failure"):
        with temporary_yaml_mutation(
            yaml_path,
            lambda payload: payload["tracks"]["prose"].update({"renderer": "broken"}),
        ):
            assert yaml.safe_load(yaml_path.read_text(encoding="utf-8"))["tracks"]["prose"]["renderer"] == "broken"
            raise RuntimeError("yaml failure")

    assert text_path.read_text(encoding="utf-8") == text_original
    assert yaml_path.read_text(encoding="utf-8") == yaml_original


def test_live_track_surface_uses_canonical_ids(project_root: Path) -> None:
    from gates.artifact_manifest import REQUIRED_OUTPUTS
    from roadmap_tracks.sheaf_tracks import CANONICAL_TRACKS, LEGACY_ARTIFACTS

    registry = yaml.safe_load((project_root / "manuscript" / "sheaf" / "tracks.yaml").read_text())["tracks"]
    manifest = yaml.safe_load((project_root / "manuscript" / "sheaf" / "manifest.yaml").read_text())
    public_tracks = {
        str(row["id"])
        for row in yaml.safe_load((project_root / "tracks.yaml").read_text())["tracks"]
        if isinstance(row, dict) and row.get("id")
    }
    claims = yaml.safe_load((project_root / "data" / "claim_ledger.yaml").read_text()).get("claims") or []
    configured = yaml.safe_load((project_root / "manuscript" / "config.yaml").read_text())["analysis"]["scripts"]

    bound_tracks = {
        str(track_id) for section in manifest["sections"] for track_id in ((section.get("tracks") or {}).keys())
    }
    claim_ids = {str(claim.get("id")) for claim in claims}

    assert set(CANONICAL_TRACKS).issubset(registry)
    assert set(CANONICAL_TRACKS).issubset(public_tracks)
    assert set(CANONICAL_TRACKS).issubset(bound_tracks)
    assert not any(VERSIONED_TRACK_RE.search(track_id) for track_id in registry)
    assert not any(VERSIONED_TRACK_RE.search(track_id) for track_id in public_tracks)
    assert not any(VERSIONED_TRACK_RE.search(track_id) for track_id in bound_tracks)
    assert not any(VERSIONED_TRACK_RE.search(claim_id) for claim_id in claim_ids)
    assert "generate_sheaf_tracks.py" in configured
    assert "generate_v2_sheaf_tracks.py" not in configured
    assert "generate_v3_sheaf_tracks.py" not in configured
    assert not (set(LEGACY_ARTIFACTS) & set(REQUIRED_OUTPUTS))


def test_canonical_sheaf_artifacts_are_written_and_valid(project_root: Path) -> None:
    from roadmap_tracks import validate_sheaf_track_artifacts, write_sheaf_track_artifacts

    ensure_gate_artifacts(project_root)
    paths = write_sheaf_track_artifacts(project_root)

    assert _relative_posix(paths["semantic"], project_root) == "output/data/sheaf_gluing_certificate.json"
    assert _relative_posix(paths["dependency"], project_root) == "output/data/validation_dependency_graph.json"
    assert _relative_posix(paths["evidence_fields"], project_root) == "output/data/evidence_field_index.json"
    assert _relative_posix(paths["release_bundle"], project_root) == "output/reports/release_bundle_manifest.json"
    assert _relative_posix(paths["theorem_traceability"], project_root) == (
        "output/data/theorem_traceability_matrix.json"
    )
    assert _relative_posix(paths["artifact_diffoscope"], project_root) == ("output/reports/artifact_diffoscope.json")
    assert _relative_posix(paths["scholarship"], project_root) == "output/data/scholarship_source_matrix.json"
    assert _relative_posix(paths["proof_extraction"], project_root) == "output/data/proof_extraction_index.json"
    assert _relative_posix(paths["state_space_catalog"], project_root) == "output/data/state_space_catalog.json"
    assert _relative_posix(paths["causal_ablation"], project_root) == "output/data/causal_ablation_matrix.json"
    assert _relative_posix(paths["artifact_license"], project_root) == "output/reports/artifact_license_audit.json"
    assert _relative_posix(paths["release_notes"], project_root) == "output/reports/release_notes_evidence.json"
    assert _relative_posix(paths["proof_dependency_graph"], project_root) == ("output/data/proof_dependency_graph.json")
    assert _relative_posix(paths["state_transition_table"], project_root) == ("output/data/state_transition_table.json")
    assert _relative_posix(paths["ablation_sensitivity_report"], project_root) == (
        "output/reports/ablation_sensitivity_report.json"
    )
    assert _relative_posix(paths["release_attestation"], project_root) == "output/reports/release_attestation.json"
    assert _relative_posix(paths["track_lane_matrix"], project_root) == "output/data/track_lane_matrix.json"
    assert _relative_posix(paths["artifact_contract_index"], project_root) == "output/data/artifact_contract_index.json"
    assert _relative_posix(paths["security_posture"], project_root) == "output/reports/security_posture_audit.json"
    assert _relative_posix(paths["section_status"], project_root) == "output/data/sheaf_section_status_matrix.json"
    assert _relative_posix(paths["render_log"], project_root) == "output/reports/sheaf_render_log.json"
    assert validate_sheaf_track_artifacts(project_root) == []

    semantic = _load(project_root / "output" / "data" / "sheaf_gluing_certificate.json")
    evidence = _load(project_root / "output" / "data" / "evidence_field_index.json")
    claim_audit = _load(project_root / "output" / "reports" / "claim_evidence_audit.json")
    release = _load(project_root / "output" / "reports" / "release_bundle_manifest.json")
    theorem = _load(project_root / "output" / "data" / "theorem_traceability_matrix.json")
    gate_index = _load(project_root / "output" / "data" / "validation_gate_index.json")
    diffoscope = _load(project_root / "output" / "reports" / "artifact_diffoscope.json")
    proof = _load(project_root / "output" / "data" / "proof_extraction_index.json")
    catalog = _load(project_root / "output" / "data" / "state_space_catalog.json")
    ablation = _load(project_root / "output" / "data" / "causal_ablation_matrix.json")
    license_audit = _load(project_root / "output" / "reports" / "artifact_license_audit.json")
    release_notes = _load(project_root / "output" / "reports" / "release_notes_evidence.json")
    scholarship = _load(project_root / "output" / "data" / "scholarship_source_matrix.json")
    proof_dependency = _load(project_root / "output" / "data" / "proof_dependency_graph.json")
    transition_table = _load(project_root / "output" / "data" / "state_transition_table.json")
    ablation_sensitivity = _load(project_root / "output" / "reports" / "ablation_sensitivity_report.json")
    release_attestation = _load(project_root / "output" / "reports" / "release_attestation.json")
    track_lane = _load(project_root / "output" / "data" / "track_lane_matrix.json")
    artifact_contract = _load(project_root / "output" / "data" / "artifact_contract_index.json")
    security_posture = _load(project_root / "output" / "reports" / "security_posture_audit.json")
    section_status = _load(project_root / "output" / "data" / "sheaf_section_status_matrix.json")
    render_log = _load(project_root / "output" / "reports" / "sheaf_render_log.json")
    visualization_quality = _load(project_root / "output" / "reports" / "visualization_quality_audit.json")
    statistical_bridge = _load(project_root / "output" / "data" / "statistical_visualization_bridge.json")

    assert semantic["ok"] is True
    assert semantic["restrictions"]["no_versioned_live_tracks"] is True
    assert semantic["all_proof_obligations_ok"] is True
    assert semantic["proof_obligations"]
    assert all(row["class"] and row["restriction"] and row["ok"] for row in semantic["proof_obligations"])
    dependency = _load(project_root / "output" / "data" / "validation_dependency_graph.json")
    assert dependency["all_field_edges_mapped"] is True
    assert dependency["field_edges"]
    assert evidence["all_fields_mapped"] is True
    assert all(row["jsonpath"] and row["validator"] and row["semantic_restriction"] for row in evidence["rows"])
    assert claim_audit["all_complete"] is True
    assert claim_audit["all_artifacts_resolved"] is True
    assert claim_audit["all_evidence_resolved"] is True
    assert claim_audit["all_evidence_predicates_hold"] is True
    assert claim_audit["incomplete_claim_count"] == 0
    assert all(row["complete"] and row["artifact_exists"] and row["evidence_holds"] for row in claim_audit["rows"])
    assert release["all_required_sources_present"] is True
    assert release["all_copied_outputs_match_or_deferred"] is True
    assert theorem["all_theorems_linked"] is True
    assert all(row["claim_ids"] and row["evidence_fields"] for row in theorem["rows"])
    assert gate_index["all_indexed"] is True
    assert all(
        row["command"] and row["required_inputs"] and row["declared_outputs"] and row["negative_control_id"]
        for row in gate_index["rows"]
    )
    assert diffoscope["all_equal"] is True
    assert proof["all_extracted"] is True
    assert catalog["all_finite"] is True
    assert ablation["complete_grid"] is True
    assert license_audit["all_license_safe"] is True
    assert release_notes["all_notes_source_backed"] is True
    assert scholarship["all_sources_connected"] is True
    assert scholarship["all_citations_present"] is True
    assert scholarship["all_claim_boundaries_scope_guarded"] is True
    assert scholarship["all_rows_rederived"] is True
    assert scholarship["source_locator_kind_count"] >= 1
    assert scholarship["declared_section_citation_overlap_count"] >= 1
    assert scholarship["quantitative_method_role_count"] >= 3
    assert all(
        row["source_locator_kind"] and row["citation_sections"] and row["claim_boundary_scope_guarded"]
        for row in scholarship["rows"]
    )
    assert proof_dependency["all_theorems_have_dependencies"] is True
    assert transition_table["all_reachable_states_covered"] is True
    assert ablation_sensitivity["all_effects_source_backed"] is True
    assert release_attestation["all_attested"] is True
    assert track_lane["schema"] == "template_active_inference.track_lane_matrix.v1"
    assert track_lane["matrix_track_ids_match_tracks_yaml"] is True
    assert track_lane["all_typed_claim_evidence_present"] is True
    assert track_lane["all_semantic_restrictions_declared"] is True
    assert track_lane["all_negative_controls_declared"] is True
    assert track_lane["all_pipeline_tracks_complete"] is True
    assert track_lane["all_required_pipeline_tracks_complete"] is True
    assert all(
        row["sheaf_tracks"]
        and row["manuscript_consumers"]
        and row["claim_ids"]
        and row["semantic_restrictions"]
        and row["negative_control"]
        and all(row["promotion_requirements"].values())
        for row in track_lane["rows"]
    )
    assert artifact_contract["schema"] == "template_active_inference.artifact_contract_index.v1"
    assert artifact_contract["all_artifact_rows_match_semantic_map"] is True
    assert artifact_contract["all_rows_complete"] is True
    assert artifact_contract["all_claim_required_rows_bound"] is True
    assert artifact_contract["all_validators_bound"] is True
    assert artifact_contract["all_negative_controls_bound"] is True
    assert artifact_contract["all_freshness_hashes_current"] is True
    assert artifact_contract["all_copied_parity_complete"] is True
    assert any(row["artifact"] == "output/data/artifact_contract_index.json" for row in artifact_contract["rows"])
    assert security_posture["schema"] == "template_active_inference.security_posture_audit.v1"
    assert security_posture["all_controls_ok"] is True
    assert security_posture["all_secret_patterns_absent"] is True
    assert security_posture["high_risk_gap_count"] == 0
    assert security_posture["secret_finding_count"] == 0
    assert security_posture["deferred_count"] >= 1
    assert section_status["all_bound_fragments_present"] is True
    assert section_status["all_sections_have_status"] is True
    assert section_status["cell_count"] == section_status["section_count"] * section_status["track_count"]
    assert render_log["all_events_ok"] is True
    assert render_log["event_count"] >= 6
    assert visualization_quality["all_quality_ok"] is True
    assert visualization_quality["all_figures_complete"] is True
    assert visualization_quality["all_rendered"] is True
    assert visualization_quality["figure_count"] >= 23
    assert visualization_quality["statistically_backed_count"] >= 6
    assert visualization_quality["all_statistical_sources_present"] is True
    assert visualization_quality["all_visual_roles_present"] is True
    assert visualization_quality["all_evidence_roles_present"] is True
    assert visualization_quality["all_paper_claims_present"] is True
    assert visualization_quality["all_figures_section_bound"] is True
    entropy_row = next(row for row in visualization_quality["rows"] if row["figure_id"] == "si_belief_entropy_curve")
    assert entropy_row["statistically_backed"] is True
    assert "output/data/si_tmaze_trace.json" in entropy_row["statistical_sources"]
    assert entropy_row["visual_role"] == "trend"
    assert entropy_row["evidence_role"] == "statistical"
    assert "belief entropy" in entropy_row["paper_claim"]
    assert "results_si_tmaze" in entropy_row["section_bindings"]
    assert statistical_bridge["schema"] == "template_active_inference.statistical_visualization_bridge.v1"
    assert statistical_bridge["row_count"] == visualization_quality["statistically_backed_count"]
    assert statistical_bridge["all_rows_connected"] is True
    assert statistical_bridge["all_rows_complete"] is True
    assert statistical_bridge["all_complete"] is True
    assert statistical_bridge["all_sheaf_tracks_registered"] is True
    assert statistical_bridge["all_figures_referenced"] is True
    assert statistical_bridge["all_reference_sections_sheaf_bound"] is True
    assert statistical_bridge["all_reference_sections_visualization_bound"] is True
    entropy_bridge = next(row for row in statistical_bridge["rows"] if row["figure_id"] == "si_belief_entropy_curve")
    assert "output/data/si_tmaze_trace.json" in entropy_bridge["statistical_sources"]
    assert "statistical_visualization_bridge" in entropy_bridge["scholarship_method_roles"]
    assert {"simulation", "visualization", "scholarship"} <= set(entropy_bridge["sheaf_tracks"])
    assert "results_si_tmaze" in entropy_bridge["figure_reference_sections"]
    assert "visualization" in entropy_bridge["reference_track_bindings"]["results_si_tmaze"]
    assert entropy_bridge["reference_sections_sheaf_bound"] is True
    assert entropy_bridge["reference_sections_visualization_bound"] is True
    assert entropy_bridge["referenced_in_manuscript"] is True
