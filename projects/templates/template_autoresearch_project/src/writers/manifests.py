"""Artifact manifest and schema writers."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from infrastructure.core.pipeline.artifacts import ArtifactManifest, ArtifactManifestEntry, compute_sha256

from src.artifact_schemas import schema_manifest_payload
from src.models import AutoResearchLoopResult
from src.phase_ledger import write_phase_ledger
from src.research_object import research_object_manifest_payload

from .constants import ALWAYS_MANIFEST_EXCLUSIONS, VOLATILE_LOOP_STATE_ARTIFACTS
from .io import relative_path, write_json


def write_artifact_manifest(
    project_root: Path,
    paths: list[Path],
    *,
    exclude_volatile: bool = False,
) -> Path:
    """Write the artifact manifest for declared loop outputs."""
    manifest_path = (project_root / "output" / "reports" / "artifact_manifest.json").resolve()
    entries = []
    for index, path in enumerate(
        sorted(
            {
                path.resolve()
                for path in paths
                if path.exists()
                and path.resolve() != manifest_path
                and relative_path(project_root, path) not in ALWAYS_MANIFEST_EXCLUSIONS
                and (not exclude_volatile or relative_path(project_root, path) not in VOLATILE_LOOP_STATE_ARTIFACTS)
            }
        ),
        start=1,
    ):
        entries.append(
            ArtifactManifestEntry(
                path=relative_path(project_root, path),
                size_bytes=path.stat().st_size,
                sha256=compute_sha256(path),
                stage_num=index,
                stage_name="AutoResearch loop",
                contract_match=True,
            )
        )
    manifest = ArtifactManifest(entries=tuple(entries), issues=())
    return write_json(manifest_path, manifest.to_dict())


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
