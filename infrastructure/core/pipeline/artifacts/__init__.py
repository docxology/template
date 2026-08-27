"""Artifact manifests for advisory pipeline reproducibility controls."""

from __future__ import annotations

from infrastructure.core.pipeline.artifacts._inventory import (
    STABLE_LOCAL_OUTPUT_INVENTORY_MODE,
    STABLE_OUTPUT_INVENTORY_MODE,
    OutputInventoryMode,
    StableOutputInventory,
    _git_ignore_matches,
    collect_stable_output_inventory,
    git_ignored_paths,
    parse_output_inventory_mode,
)
from infrastructure.core.pipeline.artifacts._manifest import (
    ArtifactManifest,
    ArtifactManifestEntry,
    ArtifactValidationReport,
    aggregate_artifact_manifests,
    artifact_manifest_entry_from_payload,
    artifact_manifest_from_payload,
    artifact_manifest_inventory_mode,
    collect_current_artifact_manifest,
    compute_sha256,
    declared_output_paths,
    output_inventory_mode_for_project,
    snapshot_current_artifact_manifest,
    validate_artifact_manifest,
    write_stage_artifact_manifest,
)

# Backward-compatible alias for incremental.py and tests.
_declared_output_paths = declared_output_paths

__all__ = [
    "STABLE_LOCAL_OUTPUT_INVENTORY_MODE",
    "STABLE_OUTPUT_INVENTORY_MODE",
    "ArtifactManifest",
    "ArtifactManifestEntry",
    "ArtifactValidationReport",
    "OutputInventoryMode",
    "StableOutputInventory",
    "_declared_output_paths",
    "_git_ignore_matches",
    "aggregate_artifact_manifests",
    "artifact_manifest_entry_from_payload",
    "artifact_manifest_from_payload",
    "artifact_manifest_inventory_mode",
    "collect_current_artifact_manifest",
    "collect_stable_output_inventory",
    "compute_sha256",
    "declared_output_paths",
    "git_ignored_paths",
    "output_inventory_mode_for_project",
    "parse_output_inventory_mode",
    "snapshot_current_artifact_manifest",
    "validate_artifact_manifest",
    "write_stage_artifact_manifest",
]
