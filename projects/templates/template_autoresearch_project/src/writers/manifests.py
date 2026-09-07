"""Artifact manifest and schema writers."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from infrastructure.core.pipeline.artifacts import (
    output_inventory_mode_for_project,
    snapshot_current_artifact_manifest,
)

from src.artifact_schemas import schema_manifest_payload
from src.models import AutoResearchLoopResult
from src.phase_ledger import write_phase_ledger
from src.research_object import research_object_manifest_payload

from .io import write_json


def write_artifact_manifest(
    project_root: Path,
    *,
    repo_root: Path,
) -> Path:
    """Snapshot the complete stable output inventory for this lifecycle."""
    project_root = project_root.resolve()
    repo_root = repo_root.resolve()
    output_dir = project_root / "output"
    inventory_mode = output_inventory_mode_for_project(repo_root, project_root)
    snapshot_current_artifact_manifest(output_dir, inventory_mode=inventory_mode)
    return output_dir / "reports" / "artifact_manifest.json"


def write_schema_manifest(project_root: Path, paths: list[Path], *, generated_at: str) -> Path:
    """Write the schema-version manifest; fail the run if any payload is nonconforming."""
    payload = schema_manifest_payload(project_root, paths, generated_at=generated_at)
    if not payload["valid"]:
        nonconforming = payload["nonconforming_schema_artifacts"]
        rows = nonconforming if isinstance(nonconforming, list) else []
        offenders = "; ".join(f"{row.get('path')} ({row.get('violations')})" for row in rows if isinstance(row, dict))
        raise ValueError(f"nonconforming schema artifact(s) — governance gate failed: {offenders}")
    return write_json(
        project_root / "output" / "data" / "autoresearch_schema_manifest.json",
        payload,
    )


def write_research_object_manifest(project_root: Path, paths: list[Path], *, generated_at: str) -> Path:
    """Write the local research-object manifest."""
    return write_json(
        project_root / "output" / "data" / "research_object_manifest.json",
        research_object_manifest_payload(project_root, paths, generated_at=generated_at),
    )


def write_autoresearch_phase_ledger(
    project_root: Path,
    result: AutoResearchLoopResult,
    paths: list[Path],
    *,
    generated_at: str,
    settlement_pass_count: int,
) -> Path:
    """Write the deterministic phase ledger for the loop settlement order."""
    return cast(
        Path,
        write_phase_ledger(
            project_root / "output" / "data" / "autoresearch_phase_ledger.json",
            project_root,
            result,
            paths,
            generated_at=generated_at,
            settlement_pass_count=settlement_pass_count,
        ),
    )
