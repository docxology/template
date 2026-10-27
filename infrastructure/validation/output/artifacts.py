"""Artifact manifest helpers for the output validation pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.core.pipeline.artifacts import (
    STABLE_OUTPUT_INVENTORY_MODE,
    ArtifactManifest,
    OutputInventoryMode,
    artifact_manifest_from_payload,
    validate_artifact_manifest,
)


def read_artifact_manifest(path: Path) -> ArtifactManifest:
    """Read an artifact manifest JSON file into the shared manifest model."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return artifact_manifest_from_payload(payload)


def current_project_manifest_if_valid(
    output_dir: Path,
    project_root: Path,
    *,
    expected_inventory_mode: OutputInventoryMode = STABLE_OUTPUT_INVENTORY_MODE,
) -> ArtifactManifest | None:
    """Return the project-authored manifest when it is present and current."""
    manifest_path = output_dir / "reports" / "artifact_manifest.json"
    if not manifest_path.exists():
        return None
    try:
        manifest = read_artifact_manifest(manifest_path)
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    output_categories = ("pdf", "web", "slides", "figures", "data")
    if not manifest.entries and any((output_dir / name).exists() for name in output_categories):
        return None
    if validate_artifact_manifest(
        manifest,
        project_dir=project_root,
        expected_inventory_mode=expected_inventory_mode,
    ).valid:
        return manifest
    return None
