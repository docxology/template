"""Artifact manifest helpers for the output validation pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from infrastructure.core.pipeline.artifacts import ArtifactManifest, ArtifactManifestEntry, validate_artifact_manifest


def read_artifact_manifest(path: Path) -> ArtifactManifest:
    """Read an artifact manifest JSON file into the shared manifest model."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("artifact manifest must contain a mapping")

    raw_entries = payload.get("entries", [])
    if not isinstance(raw_entries, list):
        raise ValueError("artifact manifest entries must be a list")

    entries: list[ArtifactManifestEntry] = []
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, dict):
            raise ValueError("artifact manifest entry must be a mapping")
        entries.append(
            ArtifactManifestEntry(
                path=str(raw_entry.get("path", "")),
                size_bytes=int(raw_entry.get("size_bytes", 0) or 0),
                sha256=str(raw_entry.get("sha256", "")),
                stage_num=int(raw_entry.get("stage_num", 0) or 0),
                stage_name=str(raw_entry.get("stage_name", "")),
                contract_match=bool(raw_entry.get("contract_match", False)),
                timestamp=str(raw_entry.get("timestamp", "")),
            )
        )

    raw_issues = payload.get("issues", [])
    if not isinstance(raw_issues, list):
        raise ValueError("artifact manifest issues must be a list")

    return ArtifactManifest(entries=tuple(entries), issues=tuple(str(issue) for issue in raw_issues))


def current_project_manifest_if_valid(output_dir: Path, project_root: Path) -> ArtifactManifest | None:
    """Return the project-authored manifest when it is present and current."""
    manifest_path = output_dir / "reports" / "artifact_manifest.json"
    if not manifest_path.exists():
        return None
    try:
        manifest = read_artifact_manifest(manifest_path)
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    if validate_artifact_manifest(manifest, project_dir=project_root).valid:
        return manifest
    return None
