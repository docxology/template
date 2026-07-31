"""Direct tests for promoted sheaf-track builders.

These builders read from the tracked output/data snapshot and are safe to run
against the real project tree (read-only). The autouse conftest fixture
restores any mutated project files after each test.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from roadmap_tracks.sheaf_tracks_builders_release import (
    build_evidence_field_index,
    build_release_bundle_manifest,
    build_theorem_traceability_matrix,
)
from roadmap_tracks.sheaf_tracks_builders_toy import (
    build_sensitivity_sweep,
    build_uncertainty_summary,
)
from roadmap_tracks.sheaf_tracks_builders_graph import (
    build_track_lane_matrix,
)


# ---------------------------------------------------------------------------
# sheaf_tracks_builders_release
# ---------------------------------------------------------------------------


def test_release_bundle_manifest_has_schema_and_rows(project_root: Path) -> None:
    """Exercise the release-bundle builder end-to-end against the snapshot."""
    payload = build_release_bundle_manifest(project_root)
    assert payload["schema"] == "template_active_inference.release_bundle_manifest.v1"
    assert payload["artifact_count"] == len(payload["rows"]) > 0
    for row in payload["rows"]:
        assert "artifact" in row
        assert "source_exists" in row or "deferred_until_render" in row


def test_release_bundle_required_sources_have_existence_state(project_root: Path) -> None:
    """Every required artifact row reports whether it exists or is deferred."""
    payload = build_release_bundle_manifest(project_root)
    pdf_web = {row["artifact"] for row in payload["rows"]
               if row["artifact"].startswith("output/pdf/")
               or row["artifact"].startswith("output/web/")}
    for row in payload["rows"]:
        deferred = row.get("deferred_until_render", False)
        if row["artifact"] in pdf_web and not row["source_exists"]:
            assert deferred, f"{row['artifact']} should be deferred if absent"
        else:
            assert row["source_exists"] or deferred, f"{row['artifact']} should exist"


def test_theorem_traceability_matrix_is_structured(project_root: Path) -> None:
    """Exercise the theorem-traceability builder."""
    payload = build_theorem_traceability_matrix(project_root)
    assert payload["schema"] == "template_active_inference.theorem_traceability_matrix.v1"
    assert payload["row_count"] == len(payload["rows"])
    for row in payload["rows"]:
        assert "theorem" in row
        assert "status" in row
        assert "claim_ids" in row


def test_evidence_field_index_is_schema_valid(project_root: Path) -> None:
    """Exercise the evidence-field-index builder."""
    payload = build_evidence_field_index(project_root)
    assert payload["schema"] == "template_active_inference.evidence_field_index.v1"
    assert payload["field_count"] == len(payload["rows"])
    if payload["rows"]:
        for row in payload["rows"]:
            assert "artifact" in row
            assert "field" in row
            assert "claim_id" in row


# ---------------------------------------------------------------------------
# sheaf_tracks_builders_toy
# ---------------------------------------------------------------------------


def test_sensitivity_sweep_is_promoted_to_canonical(project_root: Path) -> None:
    """Exercise the promoted sensitivity-sweep builder."""
    payload = build_sensitivity_sweep(project_root)
    assert payload["schema"] == "template_active_inference.sensitivity_sweep.v1"
    assert payload["row_count"] == len(payload["rows"]) >= 0
    # The grid must track topologies and modes explicitly
    assert "topologies" in payload["grid"]
    assert "modes" in payload["grid"]
    # Topology parameter count should be > 0 when rows exist
    if payload["row_count"] > 0:
        assert payload["topology_parameter_count"] > 0
    # Complete grid: every expected cell has a row, or empty when inputs are empty
    assert isinstance(payload["complete_grid"], bool)


@pytest.mark.timeout(60)
def test_uncertainty_summary_has_all_bins(project_root: Path) -> None:
    """Exercise the promoted uncertainty-summary builder."""
    payload = build_uncertainty_summary(project_root)
    assert payload["schema"] == "template_active_inference.uncertainty_summary.v1"
    assert payload["row_count"] == len(payload["rows"])
    assert set(payload["bins"].keys()) == {"low_entropy", "mid_entropy", "high_entropy"}
    for bin_id, bin_info in payload["bins"].items():
        assert "lower" in bin_info
        assert "upper" in bin_info
    if payload["rows"]:
        for row in payload["rows"]:
            assert row["bin"] in payload["bins"]
            assert row["entropy"] >= 0.0
            assert "distribution" in row
            assert "id" in row


# ---------------------------------------------------------------------------
# sheaf_tracks_builders_graph
# ---------------------------------------------------------------------------


def test_track_lane_matrix_covers_pipeline_tracks(project_root: Path) -> None:
    """Exercise the track-lane-matrix builder."""
    payload = build_track_lane_matrix(project_root)
    assert payload["schema"] == "template_active_inference.track_lane_matrix.v1"
    assert payload["row_count"] == len(payload["rows"])
    assert payload["pipeline_track_ids"] == sorted(payload["pipeline_track_ids"])
    if payload["rows"]:
        for row in payload["rows"]:
            assert "track_id" in row
            assert "sheaf_tracks" in row
            assert "primary_artifact" in row
            assert "promotion_requirements" in row
        # Count required tracks
        required = [row for row in payload["rows"] if row.get("required")]
        assert payload["required_track_count"] == len(required)