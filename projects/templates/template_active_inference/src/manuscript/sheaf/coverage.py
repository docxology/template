"""Coverage matrix for sheaf track bindings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dataclasses import dataclass

from .models import (
    CoverageCell,
    CoverageColor,
    CoverageMatrix,
    CoverageSectionRow,
    CoverageStatus,
    ManifestIssue,
    SheafManifest,
    TrackRegistry,
)


@dataclass(frozen=True)
class SheafCoverageContext:
    manifest: SheafManifest
    registry: TrackRegistry
    matrix: CoverageMatrix


def load_sheaf_coverage_context(
    project_root: Path,
    *,
    manifest_path: Path | None = None,
) -> SheafCoverageContext:
    from manuscript.sheaf.manifest import load_manifest
    from manuscript.sheaf.registry import load_track_registry

    root = project_root.resolve()
    mpath = manifest_path or (root / "manuscript" / "sheaf" / "manifest.yaml")
    manifest = load_manifest(mpath, project_root=root)
    registry = load_track_registry(root / manifest.registry_path)
    matrix = build_coverage_matrix(registry, manifest, root)
    return SheafCoverageContext(manifest=manifest, registry=registry, matrix=matrix)


def classify_cell(
    *,
    track_id: str,
    bound: bool,
    rel_path: str | None,
    file_exists: bool,
) -> tuple[CoverageStatus, CoverageColor]:
    if not bound:
        return "absent", "white"
    if file_exists:
        return "present", "black"
    return "missing", "gray"


def build_coverage_matrix(
    registry: TrackRegistry,
    manifest: SheafManifest,
    project_root: Path,
) -> CoverageMatrix:
    root = project_root.resolve()
    track_ids = tuple(tid for tid, _ in sorted(registry.tracks.items(), key=lambda item: item[1].order))
    rows: list[CoverageSectionRow] = []
    for section in manifest.sections:
        cells: list[CoverageCell] = []
        for track_id in track_ids:
            rel = section.tracks.get(track_id)
            bound = rel is not None
            exists = bool(rel and (root / rel).exists())
            status, color = classify_cell(
                track_id=track_id,
                bound=bound,
                rel_path=rel,
                file_exists=exists,
            )
            cells.append(
                CoverageCell(
                    track_id=track_id,
                    bound=bound,
                    path=rel,
                    status=status,
                    color=color,
                )
            )
        rows.append(
            CoverageSectionRow(
                section_id=section.id,
                title=section.title,
                cells=tuple(cells),
                kind=section.kind,
                imrad=section.imrad,
                depth=section.depth,
                compose=section.compose,
            )
        )
    return CoverageMatrix(track_ids=track_ids, sections=tuple(rows))


def coverage_matrix_to_dict(matrix: CoverageMatrix) -> dict[str, Any]:
    return {
        "tracks": list(matrix.track_ids),
        "sections": [
            {
                "id": row.section_id,
                "title": row.title,
                "kind": row.kind,
                "imrad": row.imrad,
                "depth": row.depth,
                "compose": row.compose,
                "cells": [
                    {
                        "track": cell.track_id,
                        "bound": cell.bound,
                        "path": cell.path,
                        "status": cell.status,
                        "color": cell.color,
                    }
                    for cell in row.cells
                ],
            }
            for row in matrix.sections
        ],
    }


def write_coverage_json(matrix: CoverageMatrix, path: Path) -> Path:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(coverage_matrix_to_dict(matrix), indent=2) + "\n"
    if path.is_file() and path.read_text(encoding="utf-8") == content:
        return path
    path.write_text(content, encoding="utf-8")
    return path


def load_coverage_json(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def validate_coverage_strict(matrix: CoverageMatrix) -> list[ManifestIssue]:
    issues: list[ManifestIssue] = []
    for section_id, track_id in matrix.gray_cells():
        issues.append(
            ManifestIssue(
                "error",
                "coverage_missing",
                f"{section_id}/{track_id}: bound track fragment missing (gray cell)",
            )
        )
    return issues


def gray_cell_count(matrix: CoverageMatrix) -> int:
    return len(matrix.gray_cells())


def gray_cell_count_from_json(data: dict[str, Any]) -> int:
    total = 0
    for section in data.get("sections") or []:
        for cell in section.get("cells") or []:
            if cell.get("color") == "gray":
                total += 1
    return total


def validate_coverage_json_data(
    data: dict[str, Any],
    manifest: SheafManifest,
    registry: TrackRegistry,
) -> list[ManifestIssue]:
    issues: list[ManifestIssue] = []
    tracks = data.get("tracks") or []
    sections = data.get("sections") or []
    if len(tracks) != len(registry.tracks):
        issues.append(
            ManifestIssue(
                "error",
                "coverage_track_count",
                f"coverage JSON lists {len(tracks)} tracks; registry has {len(registry.tracks)}",
            )
        )
    if len(sections) != len(manifest.sections):
        issues.append(
            ManifestIssue(
                "error",
                "coverage_section_count",
                f"coverage JSON lists {len(sections)} sections; manifest has {len(manifest.sections)}",
            )
        )
    gray = gray_cell_count_from_json(data)
    if gray:
        issues.append(
            ManifestIssue(
                "error",
                "coverage_gray_cells",
                f"coverage JSON has {gray} gray cell(s)",
            )
        )
    return issues


def emit_coverage_artifacts(
    project_root: Path,
    *,
    json_path: Path | None = None,
) -> Path:
    """Build matrix from live manifest/registry and write coverage JSON only."""
    ctx = load_sheaf_coverage_context(project_root)
    return write_coverage_json(
        ctx.matrix,
        json_path or project_root.resolve() / "output" / "data" / "sheaf_coverage_matrix.json",
    )
