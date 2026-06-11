"""Row-only forgery negative controls for the 2026-06-10 hardening pass.

Each case corrupts ONLY per-row ground truth (or the rows' relationship to a
count) while leaving the stored aggregate boolean True. A trust-the-flag
validator passes every one of these; the hardened validators recompute the
aggregate from rows exactly as the builders derive it and require
stored == recomputed, so each mutation must surface an issue.

Complements test_track_consolidation.py::test_canonical_sheaf_row_only_forgeries_are_caught
(sheaf-track surfaces) and test_roadmap_promotion.py (integration-audit surfaces).
"""

from __future__ import annotations

import json
from pathlib import Path

from gate_support import ensure_gate_artifacts, temporary_json_mutation


def _assert_forgery_caught(path: Path, mutate, validator, expected_issue: str, project_root: Path) -> None:
    assert path.is_file(), f"missing artifact {path}"
    baseline = validator(project_root)
    assert all(expected_issue not in issue for issue in baseline), (
        f"{path.name}: expected a clean baseline before mutation, got {baseline}"
    )
    with temporary_json_mutation(path, mutate):
        issues = validator(project_root)
        assert any(expected_issue in issue for issue in issues), (
            f"{path.name}: row-only forgery not caught (issues={issues})"
        )


def test_validation_spine_provenance_record_forgeries_are_caught(project_root: Path) -> None:
    from validation_spine import validate_artifact_provenance

    ensure_gate_artifacts(project_root)
    path = project_root / "output" / "data" / "artifact_provenance.json"

    def forge_unhashed_record(data: dict) -> None:
        rel = next(iter(data["artifacts"]))
        data["artifacts"][rel]["sha256"] = ""
        data["artifacts"][rel]["exists"] = False
        data["all_hashed"] = True

    def forge_unseeded_record(data: dict) -> None:
        rel = next(iter(data["artifacts"]))
        data["artifacts"][rel]["deterministic_seed"] = None
        data["all_seeded"] = True

    def forge_uncommitted_record(data: dict) -> None:
        rel = next(iter(data["artifacts"]))
        data["artifacts"][rel]["source_commit"] = ""
        data["all_source_commits"] = True

    _assert_forgery_caught(path, forge_unhashed_record, validate_artifact_provenance, "all_hashed", project_root)
    _assert_forgery_caught(path, forge_unseeded_record, validate_artifact_provenance, "all_seeded", project_root)
    _assert_forgery_caught(
        path, forge_uncommitted_record, validate_artifact_provenance, "all_source_commits", project_root
    )


def test_toy_sweep_row_only_forgeries_are_caught(project_root: Path) -> None:
    from roadmap_tracks import validate_toy_sweep_artifacts

    ensure_gate_artifacts(project_root)
    data_dir = project_root / "output" / "data"

    def forge_unnormalized_row(data: dict) -> None:
        data["rows"][0]["normalized"] = False
        data["all_normalized"] = True

    def forge_incomplete_model_row(data: dict) -> None:
        data["rows"][0]["gate_passed"] = False
        data["all_models_complete"] = True

    def forge_infinite_catalog_row(data: dict) -> None:
        data["rows"][0]["finite"] = False
        data["all_finite"] = True

    def forge_dropped_grid_row(data: dict) -> None:
        data["rows"] = data["rows"][1:]
        data["complete_grid"] = True
        data["row_count"] = data["expected_cells"]

    def forge_disagreeing_topology_row(data: dict) -> None:
        data["rows"][0]["summary_trace_agreement"] = False
        data["all_summary_trace_agree"] = True

    def forge_unindexed_assumption_row(data: dict) -> None:
        data["rows"][0]["status"] = "draft"
        data["all_equations_indexed"] = True

    cases = (
        (data_dir / "uncertainty_summary.json", forge_unnormalized_row, "unnormalized rows"),
        (data_dir / "toy_benchmark_matrix.json", forge_incomplete_model_row, "incomplete model rows"),
        (data_dir / "state_space_catalog.json", forge_infinite_catalog_row, "non-finite state spaces"),
        (data_dir / "sensitivity_sweep.json", forge_dropped_grid_row, "grid is incomplete"),
        (data_dir / "si_graph_world_topology_sweep.json", forge_disagreeing_topology_row, "summary/trace mismatch"),
        (data_dir / "analytical_assumption_index.json", forge_unindexed_assumption_row, "unindexed equations"),
    )
    for path, mutate, expected in cases:
        _assert_forgery_caught(path, mutate, validate_toy_sweep_artifacts, expected, project_root)


def test_animation_static_frame_forgery_is_caught(project_root: Path) -> None:
    from visualizations.animation import validate_animation_frame_deltas

    ensure_gate_artifacts(project_root)
    path = project_root / "output" / "data" / "animation_frame_deltas.json"

    def forge_static_delta_row(data: dict) -> None:
        data["rows"][0]["nonzero"] = False
        data["all_nonzero"] = True

    _assert_forgery_caught(
        path, forge_static_delta_row, validate_animation_frame_deltas, "static adjacent frames", project_root
    )


def test_semantic_certificate_obligation_forgery_is_caught(project_root: Path) -> None:
    from manuscript.sheaf.semantic import validate_semantic_gluing

    ensure_gate_artifacts(project_root)
    path = project_root / "output" / "data" / "sheaf_gluing_certificate.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload.get("proof_obligations"), "certificate must carry proof obligations for this control"

    def forge_failing_obligation(data: dict) -> None:
        data["proof_obligations"][0]["ok"] = False
        data["ok"] = True

    _assert_forgery_caught(
        path,
        forge_failing_obligation,
        validate_semantic_gluing,
        "ok disagrees with proof obligations",
        project_root,
    )


def test_staleness_row_forgeries_are_caught(project_root: Path) -> None:
    from roadmap_tracks import validate_integration_audit_artifacts, write_integration_audit_artifacts

    ensure_gate_artifacts(project_root)
    write_integration_audit_artifacts(project_root)

    def forge_stale_row(data: dict) -> None:
        data["rows"][0]["fresh"] = False
        data["all_fresh"] = True

    _assert_forgery_caught(
        project_root / "output" / "reports" / "stale_artifact_report.json",
        forge_stale_row,
        validate_integration_audit_artifacts,
        "stale_artifact_report.json records stale artifacts",
        project_root,
    )
    _assert_forgery_caught(
        project_root / "output" / "reports" / "manuscript_staleness_report.json",
        forge_stale_row,
        validate_integration_audit_artifacts,
        "records stale manuscript tokens",
        project_root,
    )
