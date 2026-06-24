"""Canonical sheaf-track negative-control tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from gate_support import ensure_gate_artifacts, temporary_json_mutation, temporary_text_mutation, temporary_yaml_mutation
from track_consolidation_support import (
    JsonMutation,
    _break_statistical_bridge_visualization_binding,
    _break_visualization_statistical_row,
    _combine_mutations,
    _drop_last_row,
    _drop_transition_covered_model,
    _load,
    _set_value,
    _write,
)

pytestmark = [pytest.mark.long_running, pytest.mark.timeout(600)]

def test_sheaf_track_writer_looks_up_source_commit_once(
    project_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from roadmap_tracks import sheaf_tracks

    ensure_gate_artifacts(project_root)
    calls = 0

    def fake_source_commit(root: Path) -> str:
        nonlocal calls
        calls += 1
        assert root == project_root.resolve()
        return "test-source-commit"

    monkeypatch.setattr("roadmap_tracks.sheaf_tracks_write._source_commit", fake_source_commit)

    sheaf_tracks.write_sheaf_track_artifacts(project_root, finalize=False)

    assert calls == 1


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
        "track_lane": project_root / "output" / "data" / "track_lane_matrix.json",
        "artifact_contract": project_root / "output" / "data" / "artifact_contract_index.json",
        "security_posture": project_root / "output" / "reports" / "security_posture_audit.json",
        "section_status": project_root / "output" / "data" / "sheaf_section_status_matrix.json",
        "render_log": project_root / "output" / "reports" / "sheaf_render_log.json",
        "visualization_quality": project_root / "output" / "reports" / "visualization_quality_audit.json",
        "statistical_bridge": project_root / "output" / "data" / "statistical_visualization_bridge.json",
        "semantic": project_root / "output" / "data" / "sheaf_gluing_certificate.json",
    }

    def drop_llm_blocked_row(data: dict) -> None:
        data["rows"] = [row for row in data["rows"] if row.get("id") != "llm_generated_evidence"]
        data["blocked_count"] = len(data["rows"])
        data["all_blocked"] = True

    def break_release_attestation(data: dict) -> None:
        row = next(row for row in data["rows"] if not row.get("deferred_until_validation"))
        row["passed"] = False
        data["all_attested"] = True

    cases: tuple[tuple[str, JsonMutation, str], ...] = (
        (
            "replay",
            _combine_mutations(
                _set_value(("rows", 0, "matched"), False), _set_value(("all_replay_rows_matched",), False)
            ),
            "replay mismatch",
        ),
        (
            "sensitivity",
            _combine_mutations(_drop_last_row(update_row_count=True), _set_value(("complete_grid",), False)),
            "grid is incomplete",
        ),
        (
            "uncertainty",
            _combine_mutations(
                _set_value(("rows", 0, "distribution_sum"), 1.5),
                _set_value(("rows", 0, "normalized"), False),
                _set_value(("all_normalized",), False),
            ),
            "unnormalized",
        ),
        (
            "counterexample",
            _combine_mutations(
                _set_value(("rows", 0, "fixture_replay_status"), "passed"),
                _set_value(("all_expected_failures_observed",), False),
            ),
            "fixtures passing",
        ),
        (
            "model",
            _combine_mutations(
                _set_value(("rows", 0, "counterexamples"), ["finite miss"]),
                _set_value(("rows", 0, "passed"), False),
                _set_value(("all_passed",), False),
            ),
            "finite counterexample",
        ),
        (
            "interop",
            _combine_mutations(
                _set_value(("rows", 0, "shape_diff"), ["policy_shape"]),
                _set_value(("all_shape_diffs_empty",), False),
                _set_value(("all_lossless",), False),
            ),
            "not lossless",
        ),
        (
            "adversarial",
            _combine_mutations(
                _set_value(("rows", 0, "known_bad_passed"), True), _set_value(("known_bad_rows_passed",), 1)
            ),
            "known-bad rows passing",
        ),
        (
            "dependency",
            _combine_mutations(
                _set_value(("edge_types",), ["producer_to_track"]),
                _set_value(("all_required_edge_types_present",), False),
            ),
            "lacks required edge types",
        ),
        (
            "dependency",
            _combine_mutations(
                _set_value(("field_edges", 0, "validator"), ""), _set_value(("all_field_edges_mapped",), True)
            ),
            "field-level edges",
        ),
        (
            "scope",
            _combine_mutations(
                _set_value(("promotion_matrix", 0, "promotion_complete"), False),
                _set_value(("all_live_tracks_valid",), False),
            ),
            "promotion rows",
        ),
        ("blocked", _set_value(("all_blocked",), False), "empirical scope blocked"),
        ("blocked", drop_llm_blocked_row, "empirical scope blocked"),
        (
            "evidence",
            _combine_mutations(
                _set_value(("rows", 0, "semantic_restriction"), ""), _set_value(("all_fields_mapped",), False)
            ),
            "unmapped evidence fields",
        ),
        (
            "release",
            _combine_mutations(
                _set_value(("rows", 0, "source_present"), False), _set_value(("all_required_sources_present",), False)
            ),
            "missing required deliverables",
        ),
        (
            "release",
            _combine_mutations(
                _set_value(("copied_output_parity", "rows", 0, "status"), "mismatch"),
                _set_value(("copied_output_parity", "all_copied_outputs_match_or_deferred"), True),
                _set_value(("all_copied_outputs_match_or_deferred",), True),
            ),
            "copied output parity",
        ),
        (
            "theorem",
            _combine_mutations(
                _set_value(("rows", 0, "evidence_fields"), []), _set_value(("all_theorems_linked",), False)
            ),
            "unlinked theorem rows",
        ),
        (
            "gate",
            _combine_mutations(_set_value(("rows", 0, "command"), ""), _set_value(("all_indexed",), False)),
            "unindexed gates",
        ),
        (
            "diffoscope",
            _combine_mutations(_set_value(("rows", 0, "equal"), False), _set_value(("all_equal",), False)),
            "artifact drift",
        ),
        (
            "scholarship",
            _combine_mutations(
                _set_value(("rows", 0, "bib_has_locator"), False),
                _set_value(("rows", 0, "connected"), True),
                _set_value(("all_sources_connected",), True),
            ),
            "disconnected source rows",
        ),
        (
            "proof",
            _combine_mutations(_set_value(("rows", 0, "extracted"), False), _set_value(("all_extracted",), False)),
            "missing statements",
        ),
        (
            "catalog",
            _combine_mutations(_set_value(("rows", 0, "finite"), False), _set_value(("all_finite",), False)),
            "missing finite spaces",
        ),
        (
            "ablation",
            _combine_mutations(_drop_last_row(update_row_count=True), _set_value(("complete_grid",), False)),
            "incomplete deterministic rows",
        ),
        (
            "license",
            _combine_mutations(
                _set_value(("rows", 0, "license_safe"), False), _set_value(("all_license_safe",), False)
            ),
            "unsafe artifacts",
        ),
        (
            "release_notes",
            _combine_mutations(
                _set_value(("rows", 0, "passed"), False), _set_value(("all_notes_source_backed",), False)
            ),
            "unsupported notes",
        ),
        (
            "proof_dependency",
            _combine_mutations(
                _set_value(("rows", 0, "linked"), False), _set_value(("all_theorems_have_dependencies",), True)
            ),
            "unlinked theorem dependencies",
        ),
        ("transition_table", _drop_transition_covered_model, "omits a reachable finite model"),
        (
            "ablation_sensitivity",
            _combine_mutations(
                _set_value(("rows", 0, "source_backed"), False), _set_value(("all_effects_source_backed",), True)
            ),
            "unsupported ablation effects",
        ),
        (
            "release_attestation",
            break_release_attestation,
            "failed gate passed",
        ),
        (
            "track_lane",
            _combine_mutations(
                _set_value(("rows", 0, "producer_configured"), False),
                _set_value(("all_pipeline_tracks_complete",), True),
            ),
            "pipeline-to-sheaf rows",
        ),
        (
            "artifact_contract",
            _combine_mutations(
                _set_value(("rows", 0, "validation_gates"), []),
                _set_value(("all_validators_bound",), True),
            ),
            "artifact contract rows",
        ),
        (
            "security_posture",
            _combine_mutations(
                _set_value(("rows", 0, "evidence_present"), False),
                _set_value(("rows", 0, "control_ok"), True),
                _set_value(("all_evidence_present",), True),
                _set_value(("all_controls_ok",), True),
            ),
            "stale or forged row evidence",
        ),
        (
            "section_status",
            _combine_mutations(
                _set_value(("missing_required_count",), 1), _set_value(("all_bound_fragments_present",), False)
            ),
            "missing bound fragments",
        ),
        (
            "render_log",
            _combine_mutations(_set_value(("events", 0, "status"), "failed"), _set_value(("all_events_ok",), False)),
            "failed render events",
        ),
        (
            "visualization_quality",
            _combine_mutations(_set_value(("rows", 0, "quality_ok"), False), _set_value(("all_quality_ok",), True)),
            "visualization_quality_ok",
        ),
        ("visualization_quality", _break_visualization_statistical_row, "visualization_statistics_bridge_ok"),
        (
            "visualization_quality",
            _combine_mutations(
                _set_value(("rows", 0, "visual_role"), ""), _set_value(("all_visual_roles_present",), True)
            ),
            "visualization_quality_ok",
        ),
        (
            "statistical_bridge",
            _combine_mutations(_set_value(("rows", 0, "connected"), False), _set_value(("all_rows_connected",), True)),
            "statistical_visualization_crosswalk_ok",
        ),
        (
            "statistical_bridge",
            _combine_mutations(
                _set_value(("rows", 0, "referenced_in_manuscript"), False),
                _set_value(("all_figures_referenced",), True),
            ),
            "statistical_visualization_crosswalk_ok",
        ),
        (
            "statistical_bridge",
            _break_statistical_bridge_visualization_binding,
            "statistical_visualization_crosswalk_ok",
        ),
        (
            "semantic",
            _combine_mutations(
                _set_value(("proof_obligations", 0, "ok"), False), _set_value(("all_proof_obligations_ok",), True)
            ),
            "proof obligations",
        ),
        (
            "semantic",
            _set_value(("restrictions", "replay_matrix_all_matched"), False),
            "stale relative to canonical restrictions",
        ),
    )

    for artifact_key, mutate, expected in cases:
        with temporary_json_mutation(paths[artifact_key], mutate):
            assert any(expected in issue for issue in validate_sheaf_track_artifacts(project_root)), artifact_key


def test_canonical_sheaf_row_only_forgeries_are_caught(project_root: Path) -> None:
    """Row-only forgeries (rows contradict a True stored aggregate) must be caught.

    Each mutation here corrupts ONLY a row (or an edge / edge-type list) and leaves the
    stored aggregate boolean True. A trust-the-flag check (read the flag, never recompute
    from the rows) passes every one of these; the hardened checks recompute the aggregate
    from its rows exactly as the generator derives it and require stored == recomputed.
    """
    from roadmap_tracks import validate_sheaf_track_artifacts, write_sheaf_track_artifacts

    ensure_gate_artifacts(project_root)
    write_sheaf_track_artifacts(project_root)
    paths = {
        "provenance": project_root / "output" / "data" / "artifact_provenance.json",
        "dependency": project_root / "output" / "data" / "validation_dependency_graph.json",
        "section_status": project_root / "output" / "data" / "sheaf_section_status_matrix.json",
        "render_log": project_root / "output" / "reports" / "sheaf_render_log.json",
        "scope": project_root / "output" / "data" / "track_improvement_scope.json",
        "release": project_root / "output" / "reports" / "release_bundle_manifest.json",
        "track_lane": project_root / "output" / "data" / "track_lane_matrix.json",
        "artifact_contract": project_root / "output" / "data" / "artifact_contract_index.json",
        "security_posture": project_root / "output" / "reports" / "security_posture_audit.json",
    }
    originals = {path: path.read_text(encoding="utf-8") for path in paths.values()}
    try:
        # provenance: a row contradicts the True all_records_complete aggregate.
        data = _load(paths["provenance"])
        data["rows"][0]["complete"] = False
        data["rows"][0]["cycle_excluded"] = False
        assert data["all_records_complete"] is True
        _write(paths["provenance"], data)
        assert any(
            "incomplete provenance rows or bundles" in issue for issue in validate_sheaf_track_artifacts(project_root)
        )
        paths["provenance"].write_text(originals[paths["provenance"]], encoding="utf-8")

        # provenance: a bundle contradicts the True all_bundles_complete aggregate.
        data = _load(paths["provenance"])
        data["bundles"][0]["complete"] = False
        assert data["all_bundles_complete"] is True
        _write(paths["provenance"], data)
        assert any(
            "incomplete provenance rows or bundles" in issue for issue in validate_sheaf_track_artifacts(project_root)
        )
        paths["provenance"].write_text(originals[paths["provenance"]], encoding="utf-8")

        # dependency: drop a required edge type while leaving the flag True.
        data = _load(paths["dependency"])
        data["edge_types"] = [kind for kind in data["edge_types"] if kind != "producer_to_track"]
        assert data["all_required_edge_types_present"] is True
        _write(paths["dependency"], data)
        assert any("lacks required edge types" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["dependency"].write_text(originals[paths["dependency"]], encoding="utf-8")

        # section_status: stale missing_required_count vs True all_bound_fragments_present.
        data = _load(paths["section_status"])
        data["missing_required_count"] = 1
        assert data["all_bound_fragments_present"] is True
        _write(paths["section_status"], data)
        assert any("missing bound fragments" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["section_status"].write_text(originals[paths["section_status"]], encoding="utf-8")

        # section_status: a section row with a blank status vs True all_sections_have_status.
        data = _load(paths["section_status"])
        data["sections"][0]["status"] = ""
        assert data["all_sections_have_status"] is True
        _write(paths["section_status"], data)
        assert any("incomplete status rows" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["section_status"].write_text(originals[paths["section_status"]], encoding="utf-8")

        # section_status: a track row with a blank status vs True all_tracks_have_status.
        data = _load(paths["section_status"])
        data["tracks"][0]["status"] = ""
        assert data["all_tracks_have_status"] is True
        _write(paths["section_status"], data)
        assert any("incomplete status rows" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["section_status"].write_text(originals[paths["section_status"]], encoding="utf-8")

        # render_log: a failed event row vs True all_events_ok.
        data = _load(paths["render_log"])
        data["events"][0]["status"] = "failed"
        assert data["all_events_ok"] is True
        _write(paths["render_log"], data)
        assert any("failed render events" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["render_log"].write_text(originals[paths["render_log"]], encoding="utf-8")

        # scope: an incomplete promotion row vs True all_live_tracks_valid.
        data = _load(paths["scope"])
        data["promotion_matrix"][0]["promotion_complete"] = False
        assert data["all_live_tracks_valid"] is True
        _write(paths["scope"], data)
        assert any("live-track promotion rows" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["scope"].write_text(originals[paths["scope"]], encoding="utf-8")

        # release_bundle: a missing source row vs True all_required_sources_present.
        data = _load(paths["release"])
        data["rows"][0]["source_exists"] = False
        data["rows"][0]["deferred_until_render"] = False
        assert data["all_required_sources_present"] is True
        _write(paths["release"], data)
        assert any("missing required deliverables" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["release"].write_text(originals[paths["release"]], encoding="utf-8")

        # track_lane_matrix: a row loses its sheaf fragment while aggregate flags stay True.
        data = _load(paths["track_lane"])
        data["rows"][0]["sheaf_tracks"] = []
        data["rows"][0]["sheaf_tracks_registered"] = True
        assert data["all_pipeline_tracks_complete"] is True
        _write(paths["track_lane"], data)
        assert any("pipeline-to-sheaf rows" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["track_lane"].write_text(originals[paths["track_lane"]], encoding="utf-8")

        # track_lane_matrix: a row loses typed claim evidence while aggregate flags stay True.
        data = _load(paths["track_lane"])
        data["rows"][0]["claim_ids"] = []
        data["rows"][0]["has_typed_claim_evidence"] = True
        data["all_typed_claim_evidence_present"] = True
        assert data["all_pipeline_tracks_complete"] is True
        _write(paths["track_lane"], data)
        assert any("pipeline-to-sheaf rows" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["track_lane"].write_text(originals[paths["track_lane"]], encoding="utf-8")

        # artifact_contract_index: a row loses validator binding while aggregate flags stay True.
        data = _load(paths["artifact_contract"])
        data["rows"][0]["validation_gates"] = []
        data["rows"][0]["contract_complete"] = True
        data["all_validators_bound"] = True
        data["all_rows_complete"] = True
        assert data["all_rows_complete"] is True
        _write(paths["artifact_contract"], data)
        assert any("artifact_contract_index.json" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["artifact_contract"].write_text(originals[paths["artifact_contract"]], encoding="utf-8")

        # artifact_contract_index: an orphan row cannot be hidden by True aggregates.
        data = _load(paths["artifact_contract"])
        orphan = dict(data["rows"][0])
        orphan["artifact"] = "output/data/orphan_artifact_contract.json"
        data["rows"].append(orphan)
        data["row_count"] = len(data["rows"])
        data["all_artifact_rows_match_semantic_map"] = True
        _write(paths["artifact_contract"], data)
        assert any("artifact_contract_index.json" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["artifact_contract"].write_text(originals[paths["artifact_contract"]], encoding="utf-8")

        # security_posture: a row loses live evidence while summary booleans stay True.
        data = _load(paths["security_posture"])
        data["rows"][0]["evidence_present"] = False
        data["rows"][0]["control_ok"] = True
        data["all_evidence_present"] = True
        data["all_controls_ok"] = True
        assert data["all_controls_ok"] is True
        _write(paths["security_posture"], data)
        assert any("security_posture_audit.json" in issue for issue in validate_sheaf_track_artifacts(project_root))
        paths["security_posture"].write_text(originals[paths["security_posture"]], encoding="utf-8")
    finally:
        for path, text in originals.items():
            path.write_text(text, encoding="utf-8")
        write_sheaf_track_artifacts(project_root)


def test_canonical_track_contract_negative_controls(project_root: Path) -> None:
    from roadmap_tracks import validate_sheaf_track_source_contract

    ensure_gate_artifacts(project_root)
    config_path = project_root / "manuscript" / "config.yaml"
    manifest_path = project_root / "manuscript" / "sheaf" / "manifest.yaml"
    registry_path = project_root / "manuscript" / "sheaf" / "tracks.yaml"
    ledger_path = project_root / "data" / "claim_ledger.yaml"

    def remove_sheaf_producer(text: str) -> str:
        return text.replace("    - generate_sheaf_tracks.py\n", "")

    def unbind_evidence_fields(manifest_payload: dict) -> None:
        for section in manifest_payload["sections"]:
            (section.get("tracks") or {}).pop("evidence_fields", None)

    def promote_empirical_adapter(registry_payload: dict) -> None:
        registry_payload["tracks"]["empirical_adapter"] = {"order": 999, "renderer": "markdown", "label": "Empirical"}

    def remove_evidence_field_claim(ledger_payload: dict) -> None:
        ledger_payload["claims"] = [
            claim for claim in ledger_payload["claims"] if claim.get("path") != "output/data/evidence_field_index.json"
        ]

    def add_pipeline_track_without_sheaf_fragment(tracks_payload: dict) -> None:
        tracks_payload["tracks"].append(
            {
                "id": "orphan_pipeline",
                "label": "Orphan pipeline track",
                "paths": ["src/analytical"],
                "gate": "validate_outputs",
                "required": True,
            }
        )

    cases = (
        ("producer_coverage_complete", lambda: temporary_text_mutation(config_path, remove_sheaf_producer)),
        ("missing manuscript bindings", lambda: temporary_yaml_mutation(manifest_path, unbind_evidence_fields)),
        ("empirical_adapter blocked", lambda: temporary_yaml_mutation(registry_path, promote_empirical_adapter)),
        (
            "pipeline tracks missing sheaf fragments",
            lambda: temporary_yaml_mutation(project_root / "tracks.yaml", add_pipeline_track_without_sheaf_fragment),
        ),
        (
            "all_canonical_artifacts_have_claims",
            lambda: temporary_yaml_mutation(ledger_path, remove_evidence_field_claim),
        ),
    )
    for expected, context_factory in cases:
        with context_factory():
            assert any(expected in issue for issue in validate_sheaf_track_source_contract(project_root)), expected
