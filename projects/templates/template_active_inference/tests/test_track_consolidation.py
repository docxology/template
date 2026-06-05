"""Canonical sheaf-track consolidation tests and negative controls."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from gate_support import ensure_gate_artifacts

VERSIONED_TRACK_RE = re.compile(r"(?:^|_)v[2-9]$")
# test_canonical_track_contract_negative_controls regenerates the full sheaf-track
# artifact set 5x (4 negative controls + restore); ~85s locally but ubuntu CI runners
# have been observed ~3.5x slower, breaching a 300s ceiling. 600s gives margin for the
# slowest leg without masking a real hang (the test is correct, just heavy).
pytestmark = pytest.mark.timeout(600)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _relative_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


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
    assert _relative_posix(paths["section_status"], project_root) == "output/data/sheaf_section_status_matrix.json"
    assert _relative_posix(paths["render_log"], project_root) == "output/reports/sheaf_render_log.json"
    assert validate_sheaf_track_artifacts(project_root) == []

    semantic = _load(project_root / "output" / "data" / "sheaf_gluing_certificate.json")
    evidence = _load(project_root / "output" / "data" / "evidence_field_index.json")
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
    section_status = _load(project_root / "output" / "data" / "sheaf_section_status_matrix.json")
    render_log = _load(project_root / "output" / "reports" / "sheaf_render_log.json")

    assert semantic["ok"] is True
    assert semantic["restrictions"]["no_versioned_live_tracks"] is True
    assert evidence["all_fields_mapped"] is True
    assert release["all_required_sources_present"] is True
    assert theorem["all_theorems_linked"] is True
    assert gate_index["all_indexed"] is True
    assert diffoscope["all_equal"] is True
    assert proof["all_extracted"] is True
    assert catalog["all_finite"] is True
    assert ablation["complete_grid"] is True
    assert license_audit["all_license_safe"] is True
    assert release_notes["all_notes_source_backed"] is True
    assert scholarship["all_sources_connected"] is True
    assert proof_dependency["all_theorems_have_dependencies"] is True
    assert transition_table["all_reachable_states_covered"] is True
    assert ablation_sensitivity["all_effects_source_backed"] is True
    assert release_attestation["all_attested"] is True
    assert section_status["all_bound_fragments_present"] is True
    assert section_status["all_sections_have_status"] is True
    assert section_status["cell_count"] == section_status["section_count"] * section_status["track_count"]
    assert render_log["all_events_ok"] is True
    assert render_log["event_count"] >= 6


def test_canonical_sheaf_negative_controls(project_root: Path) -> None:
    from roadmap_tracks import validate_sheaf_track_artifacts, write_sheaf_track_artifacts

    ensure_gate_artifacts(project_root)
    write_sheaf_track_artifacts(project_root)
    paths = {
        "replay": project_root / "output" / "reports" / "replay_matrix.json",
        "sensitivity": project_root / "output" / "data" / "sensitivity_sweep.json",
        "uncertainty": project_root / "output" / "data" / "uncertainty_summary.json",
        "counterexample": project_root / "output" / "reports" / "counterexample_matrix.json",
        "model": project_root / "output" / "reports" / "model_checking_witnesses.json",
        "interop": project_root / "output" / "data" / "interop_roundtrip_report.json",
        "adversarial": project_root / "output" / "reports" / "adversarial_audit.json",
        "dependency": project_root / "output" / "data" / "validation_dependency_graph.json",
        "scope": project_root / "output" / "data" / "track_improvement_scope.json",
        "blocked": project_root / "output" / "reports" / "blocked_scope_manifest.json",
        "evidence": project_root / "output" / "data" / "evidence_field_index.json",
        "release": project_root / "output" / "reports" / "release_bundle_manifest.json",
        "theorem": project_root / "output" / "data" / "theorem_traceability_matrix.json",
        "gate": project_root / "output" / "data" / "validation_gate_index.json",
        "diffoscope": project_root / "output" / "reports" / "artifact_diffoscope.json",
        "scholarship": project_root / "output" / "data" / "scholarship_source_matrix.json",
        "proof": project_root / "output" / "data" / "proof_extraction_index.json",
        "catalog": project_root / "output" / "data" / "state_space_catalog.json",
        "ablation": project_root / "output" / "data" / "causal_ablation_matrix.json",
        "license": project_root / "output" / "reports" / "artifact_license_audit.json",
        "release_notes": project_root / "output" / "reports" / "release_notes_evidence.json",
        "proof_dependency": project_root / "output" / "data" / "proof_dependency_graph.json",
        "transition_table": project_root / "output" / "data" / "state_transition_table.json",
        "ablation_sensitivity": project_root / "output" / "reports" / "ablation_sensitivity_report.json",
        "release_attestation": project_root / "output" / "reports" / "release_attestation.json",
        "section_status": project_root / "output" / "data" / "sheaf_section_status_matrix.json",
        "render_log": project_root / "output" / "reports" / "sheaf_render_log.json",
        "semantic": project_root / "output" / "data" / "sheaf_gluing_certificate.json",
    }
    originals = {path: path.read_text(encoding="utf-8") for path in paths.values()}
    try:
        data = _load(paths["replay"])
        data["rows"][0]["matched"] = False
        data["all_replay_rows_matched"] = False
        _write(paths["replay"], data)
        assert any("replay mismatch" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["replay"].write_text(originals[paths["replay"]], encoding="utf-8")

        data = _load(paths["sensitivity"])
        data["rows"] = data["rows"][:-1]
        data["row_count"] = len(data["rows"])
        data["complete_grid"] = False
        _write(paths["sensitivity"], data)
        assert any("grid is incomplete" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["sensitivity"].write_text(originals[paths["sensitivity"]], encoding="utf-8")

        data = _load(paths["uncertainty"])
        data["rows"][0]["distribution_sum"] = 1.5
        data["rows"][0]["normalized"] = False
        data["all_normalized"] = False
        _write(paths["uncertainty"], data)
        assert any("unnormalized" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["uncertainty"].write_text(originals[paths["uncertainty"]], encoding="utf-8")

        data = _load(paths["counterexample"])
        data["rows"][0]["fixture_replay_status"] = "passed"
        data["all_expected_failures_observed"] = False
        _write(paths["counterexample"], data)
        assert any("fixtures passing" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["counterexample"].write_text(originals[paths["counterexample"]], encoding="utf-8")

        data = _load(paths["model"])
        data["rows"][0]["counterexamples"] = ["finite miss"]
        data["rows"][0]["passed"] = False
        data["all_passed"] = False
        _write(paths["model"], data)
        assert any("finite counterexample" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["model"].write_text(originals[paths["model"]], encoding="utf-8")

        data = _load(paths["interop"])
        data["rows"][0]["shape_diff"] = ["policy_shape"]
        data["all_shape_diffs_empty"] = False
        data["all_lossless"] = False
        _write(paths["interop"], data)
        assert any("not lossless" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["interop"].write_text(originals[paths["interop"]], encoding="utf-8")

        data = _load(paths["adversarial"])
        data["rows"][0]["known_bad_passed"] = True
        data["known_bad_rows_passed"] = 1
        _write(paths["adversarial"], data)
        assert any("known-bad rows passing" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["adversarial"].write_text(originals[paths["adversarial"]], encoding="utf-8")

        data = _load(paths["dependency"])
        data["edge_types"] = ["producer_to_track"]
        data["all_required_edge_types_present"] = False
        _write(paths["dependency"], data)
        assert any("lacks required edge types" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["dependency"].write_text(originals[paths["dependency"]], encoding="utf-8")

        data = _load(paths["scope"])
        data["promotion_matrix"][0]["promotion_complete"] = False
        data["all_live_tracks_valid"] = False
        _write(paths["scope"], data)
        assert any("promotion rows" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["scope"].write_text(originals[paths["scope"]], encoding="utf-8")

        data = _load(paths["blocked"])
        data["all_blocked"] = False
        _write(paths["blocked"], data)
        assert any("empirical scope blocked" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["blocked"].write_text(originals[paths["blocked"]], encoding="utf-8")

        data = _load(paths["evidence"])
        data["rows"][0]["mapped"] = False
        data["all_fields_mapped"] = False
        _write(paths["evidence"], data)
        assert any("unmapped evidence fields" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["evidence"].write_text(originals[paths["evidence"]], encoding="utf-8")

        data = _load(paths["release"])
        data["rows"][0]["source_present"] = False
        data["all_required_sources_present"] = False
        _write(paths["release"], data)
        assert any("missing required deliverables" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["release"].write_text(originals[paths["release"]], encoding="utf-8")

        data = _load(paths["theorem"])
        data["rows"][0]["linked"] = False
        data["all_theorems_linked"] = False
        _write(paths["theorem"], data)
        assert any("unlinked theorem rows" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["theorem"].write_text(originals[paths["theorem"]], encoding="utf-8")

        data = _load(paths["gate"])
        data["rows"][0]["indexed"] = False
        data["all_indexed"] = False
        _write(paths["gate"], data)
        assert any("unindexed gates" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["gate"].write_text(originals[paths["gate"]], encoding="utf-8")

        data = _load(paths["diffoscope"])
        data["rows"][0]["equal"] = False
        data["all_equal"] = False
        _write(paths["diffoscope"], data)
        assert any("artifact drift" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["diffoscope"].write_text(originals[paths["diffoscope"]], encoding="utf-8")

        data = _load(paths["scholarship"])
        data["rows"][0]["bib_has_locator"] = False
        data["rows"][0]["connected"] = True
        data["all_sources_connected"] = True
        _write(paths["scholarship"], data)
        assert any("disconnected source rows" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["scholarship"].write_text(originals[paths["scholarship"]], encoding="utf-8")

        data = _load(paths["proof"])
        data["rows"][0]["extracted"] = False
        data["all_extracted"] = False
        _write(paths["proof"], data)
        assert any("missing statements" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["proof"].write_text(originals[paths["proof"]], encoding="utf-8")

        data = _load(paths["catalog"])
        data["rows"][0]["finite"] = False
        data["all_finite"] = False
        _write(paths["catalog"], data)
        assert any("missing finite spaces" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["catalog"].write_text(originals[paths["catalog"]], encoding="utf-8")

        data = _load(paths["ablation"])
        data["rows"] = data["rows"][:-1]
        data["row_count"] = len(data["rows"])
        data["complete_grid"] = False
        _write(paths["ablation"], data)
        assert any("incomplete deterministic rows" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["ablation"].write_text(originals[paths["ablation"]], encoding="utf-8")

        data = _load(paths["license"])
        data["rows"][0]["license_safe"] = False
        data["all_license_safe"] = False
        _write(paths["license"], data)
        assert any("unsafe artifacts" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["license"].write_text(originals[paths["license"]], encoding="utf-8")

        data = _load(paths["release_notes"])
        data["rows"][0]["passed"] = False
        data["all_notes_source_backed"] = False
        _write(paths["release_notes"], data)
        assert any("unsupported notes" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["release_notes"].write_text(originals[paths["release_notes"]], encoding="utf-8")

        data = _load(paths["proof_dependency"])
        data["rows"][0]["linked"] = False
        data["all_theorems_have_dependencies"] = True
        _write(paths["proof_dependency"], data)
        assert any("unlinked theorem dependencies" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["proof_dependency"].write_text(originals[paths["proof_dependency"]], encoding="utf-8")

        data = _load(paths["transition_table"])
        data["covered_models"] = data["covered_models"][:-1]
        data["all_reachable_states_covered"] = True
        _write(paths["transition_table"], data)
        assert any("omits a reachable finite model" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["transition_table"].write_text(originals[paths["transition_table"]], encoding="utf-8")

        data = _load(paths["ablation_sensitivity"])
        data["rows"][0]["source_backed"] = False
        data["all_effects_source_backed"] = True
        _write(paths["ablation_sensitivity"], data)
        assert any("unsupported ablation effects" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["ablation_sensitivity"].write_text(originals[paths["ablation_sensitivity"]], encoding="utf-8")

        data = _load(paths["release_attestation"])
        data["rows"][1]["passed"] = False
        data["all_attested"] = True
        _write(paths["release_attestation"], data)
        assert any("failed gate passed" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["release_attestation"].write_text(originals[paths["release_attestation"]], encoding="utf-8")

        data = _load(paths["section_status"])
        data["missing_required_count"] = 1
        data["all_bound_fragments_present"] = False
        _write(paths["section_status"], data)
        assert any("missing bound fragments" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["section_status"].write_text(originals[paths["section_status"]], encoding="utf-8")

        data = _load(paths["render_log"])
        data["events"][0]["status"] = "failed"
        data["all_events_ok"] = False
        _write(paths["render_log"], data)
        assert any("failed render events" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["render_log"].write_text(originals[paths["render_log"]], encoding="utf-8")

        data = _load(paths["semantic"])
        data["restrictions"]["replay_matrix_all_matched"] = False
        _write(paths["semantic"], data)
        assert any(
            "stale relative to canonical restrictions" in issue
            for issue in validate_sheaf_track_artifacts(project_root)
        )
    finally:
        for path, text in originals.items():
            path.write_text(text, encoding="utf-8")
        write_sheaf_track_artifacts(project_root)


def test_canonical_track_contract_negative_controls(project_root: Path) -> None:
    from roadmap_tracks import validate_sheaf_track_artifacts, write_sheaf_track_artifacts

    ensure_gate_artifacts(project_root)
    config_path = project_root / "manuscript" / "config.yaml"
    manifest_path = project_root / "manuscript" / "sheaf" / "manifest.yaml"
    registry_path = project_root / "manuscript" / "sheaf" / "tracks.yaml"
    ledger_path = project_root / "data" / "claim_ledger.yaml"
    originals = {
        config_path: config_path.read_text(encoding="utf-8"),
        manifest_path: manifest_path.read_text(encoding="utf-8"),
        registry_path: registry_path.read_text(encoding="utf-8"),
        ledger_path: ledger_path.read_text(encoding="utf-8"),
    }
    try:
        config_path.write_text(
            originals[config_path].replace("    - generate_sheaf_tracks.py\n", ""),
            encoding="utf-8",
        )
        write_sheaf_track_artifacts(project_root)
        assert any("producer_coverage_complete" in issue for issue in validate_sheaf_track_artifacts(project_root))
        config_path.write_text(originals[config_path], encoding="utf-8")

        manifest_payload = yaml.safe_load(originals[manifest_path])
        for section in manifest_payload["sections"]:
            (section.get("tracks") or {}).pop("evidence_fields", None)
        manifest_path.write_text(yaml.safe_dump(manifest_payload, sort_keys=False), encoding="utf-8")
        write_sheaf_track_artifacts(project_root)
        assert any("missing manuscript bindings" in issue for issue in validate_sheaf_track_artifacts(project_root))
        manifest_path.write_text(originals[manifest_path], encoding="utf-8")

        registry_payload = yaml.safe_load(originals[registry_path])
        registry_payload["tracks"]["empirical_adapter"] = {"order": 999, "renderer": "markdown", "label": "Empirical"}
        registry_path.write_text(yaml.safe_dump(registry_payload, sort_keys=False), encoding="utf-8")
        write_sheaf_track_artifacts(project_root)
        assert any("empirical_adapter blocked" in issue for issue in validate_sheaf_track_artifacts(project_root))
        registry_path.write_text(originals[registry_path], encoding="utf-8")

        ledger_payload = yaml.safe_load(originals[ledger_path])
        ledger_payload["claims"] = [
            claim for claim in ledger_payload["claims"] if claim.get("path") != "output/data/evidence_field_index.json"
        ]
        ledger_path.write_text(yaml.safe_dump(ledger_payload, sort_keys=False), encoding="utf-8")
        write_sheaf_track_artifacts(project_root)
        assert any(
            "all_canonical_artifacts_have_claims" in issue for issue in validate_sheaf_track_artifacts(project_root)
        )
    finally:
        for path, text in originals.items():
            path.write_text(text, encoding="utf-8")
        write_sheaf_track_artifacts(project_root)
