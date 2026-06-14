"""Compatibility tests for integration-audit module splitting."""

from __future__ import annotations

from roadmap_tracks import integration_audit
from roadmap_tracks import integration_audit_artifacts
from roadmap_tracks import integration_audit_figures
from roadmap_tracks import integration_audit_lanes


def test_integration_audit_figure_builders_keep_public_facade() -> None:
    assert integration_audit.build_figure_source_map is integration_audit_figures.build_figure_source_map
    assert integration_audit_artifacts.build_figure_source_map is integration_audit_figures.build_figure_source_map
    assert integration_audit.build_figure_hash_manifest is integration_audit_figures.build_figure_hash_manifest
    assert (
        integration_audit_artifacts.build_figure_hash_manifest
        is integration_audit_figures.build_figure_hash_manifest
    )


def test_integration_audit_lane_vocabulary_keeps_public_facade() -> None:
    assert integration_audit.ALLOWED_CLAIM_LANES is integration_audit_lanes.ALLOWED_CLAIM_LANES
    assert integration_audit_artifacts.ALLOWED_CLAIM_LANES is integration_audit_lanes.ALLOWED_CLAIM_LANES
    assert integration_audit_artifacts.allowed_claim_lanes is integration_audit_lanes.allowed_claim_lanes
