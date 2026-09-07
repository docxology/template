"""Shared helpers for sheaf-track artifact builders."""

from __future__ import annotations

import stat
from pathlib import Path
from typing import Any

from roadmap_tracks.image_content_hash import image_content_sha256, is_image_artifact
from roadmap_tracks.sheaf_tracks_context import _ProvenanceContext, _provenance_context
from roadmap_tracks.sheaf_tracks_io import (
    _analysis_scripts,
    _artifact_maps,
    _claim_ids_by_path,
    _sha256,
)
from roadmap_tracks.sheaf_tracks_registry import (
    HASH_CYCLE_AUTHORITY,
    LEGACY_ARTIFACTS,
    hash_cycle_excluded,
)


def _entropy(values: list[float]) -> float:
    import math

    return float(-sum(value * math.log(value) for value in values if value > 0.0))


def _root_output_dir(project_root: Path) -> Path:
    root = project_root.resolve()
    for parent in root.parents:
        if (parent / "run.sh").is_file() and (parent / "projects").is_dir():
            return parent / "output" / "templates" / root.name
    raise RuntimeError(f"cannot locate verified repository root for copied-output parity: {root}")


def _portable_repo_path(path: Path, project_root: Path) -> str:
    """Represent repository-local paths without embedding a developer home directory."""
    for parent in project_root.resolve().parents:
        if (parent / "run.sh").is_file() and (parent / "projects").is_dir():
            try:
                return f"<repo-root>/{path.resolve().relative_to(parent).as_posix()}"
            except ValueError:
                break
    return "<external-path>"


def _confined_regular_path(base: Path, rel: str) -> Path:
    relative = Path(rel)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise RuntimeError(f"copied-output parity path must be normalized and relative: {rel}")
    cursor = base.resolve()
    for index, part in enumerate(relative.parts):
        cursor /= part
        try:
            metadata = cursor.lstat()
        except FileNotFoundError:
            return cursor
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"copied-output parity path must not contain symlinks: {cursor}")
        if index < len(relative.parts) - 1 and not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError(f"copied-output parity parent is not a directory: {cursor}")
        if index == len(relative.parts) - 1 and not stat.S_ISREG(metadata.st_mode):
            raise RuntimeError(f"copied-output parity target is not a regular file: {cursor}")
    return cursor


def _copied_parity(project_root: Path, rel_paths: list[str]) -> dict[str, Any]:
    root = project_root.resolve()
    copied_root = _root_output_dir(root)
    rows: list[dict[str, Any]] = []
    for rel in rel_paths:
        source = _confined_regular_path(root, rel)
        copied = _confined_regular_path(copied_root, rel.removeprefix("output/"))
        source_hash = _sha256(source)
        copied_hash = _sha256(copied)
        source_exists = source.is_file()
        copied_exists = copied.is_file()
        hash_matches = bool(source_hash) and source_hash == copied_hash
        render_deferred = rel.startswith("output/pdf/") or rel.startswith("output/web/")
        deferred = (source_exists and not hash_matches) or (not source_exists and render_deferred)
        status = (
            "matched"
            if hash_matches
            else "deferred"
            if deferred
            else "missing_copied_output"
            if not copied_exists
            else "mismatch"
        )
        rows.append(
            {
                "artifact": rel,
                "source_exists": source_exists,
                "copied_path": copied.relative_to(copied_root).as_posix(),
                "copied_exists": copied_exists,
                "source_sha256": source_hash,
                "copied_sha256": copied_hash,
                "hash_matches": hash_matches,
                "status": status,
                "comparison_deferred_until_copy": deferred,
                "matches_when_copied": status in {"matched", "deferred"},
            }
        )
    return {
        "copied_root": _portable_repo_path(copied_root, root),
        "copied_root_exists": copied_root.is_dir(),
        "rows": rows,
        "row_count": len(rows),
        "all_required_sources_present": all(row["source_exists"] for row in rows),
        "all_copied_outputs_match": all(row["hash_matches"] for row in rows if row["copied_exists"]),
        "all_copied_outputs_match_or_deferred": all(row["matches_when_copied"] for row in rows),
        "pre_copy_stage": any(row["comparison_deferred_until_copy"] for row in rows),
    }


def _deferred_copy_parity(project_root: Path, rel_paths: list[str]) -> dict[str, Any]:
    """Declare the post-copy boundary without reading a prior Stage-5 mirror.

    Semantic settlement runs before rendering and copying.  Reading the ignored
    repository-root delivery mirror here made canonical project evidence depend
    on stale output from a previous pipeline run.  Stage 5 owns live byte-parity;
    this pre-copy record is deliberately structural and machine-independent.
    """
    root = project_root.resolve()
    producers, _, _ = _artifact_maps()
    rows = []
    for rel in rel_paths:
        source = _confined_regular_path(root, rel)
        producer = producers.get(rel, "generate_figures.py" if rel.endswith(".png") else "")
        rows.append(
            {
                "artifact": rel,
                "source_exists": source.is_file(),
                "copied_path": rel.removeprefix("output/"),
                "copied_exists": False,
                "source_sha256": "",
                "copied_sha256": "",
                "hash_matches": False,
                "hash_cycle_excluded": hash_cycle_excluded(rel, producer),
                "hash_authority": HASH_CYCLE_AUTHORITY,
                "status": "deferred",
                "comparison_deferred_until_copy": True,
                "matches_when_copied": True,
            }
        )
    return {
        "copied_root": f"output/templates/{root.name}",
        "copied_root_exists": False,
        "rows": rows,
        "row_count": len(rows),
        "all_required_sources_present": all(row["source_exists"] for row in rows),
        "all_copied_outputs_match": False,
        "all_copied_outputs_match_or_deferred": True,
        "pre_copy_stage": True,
        "parity_authority": "stage_05_copy",
    }


def _remove_legacy_artifacts(root: Path) -> None:
    for rel in LEGACY_ARTIFACTS:
        path = root / rel
        if path.is_file():
            path.unlink()


def _refresh_hydrated_manuscript(root: Path) -> None:
    from manuscript.refresh import ManuscriptRefreshPhase, refresh_manuscript_pipeline

    refresh_manuscript_pipeline(root, require_analysis_outputs=False, phase=ManuscriptRefreshPhase.POST_COMPOSE)


def _canonical_artifact_rows(root: Path, context: _ProvenanceContext | None = None) -> list[dict[str, Any]]:
    producers, consumers, gates = _artifact_maps()
    configured = set(_analysis_scripts(root))
    claims = _claim_ids_by_path(root)
    context = context or _provenance_context(root)
    rows: list[dict[str, Any]] = []
    for rel, producer in sorted(producers.items()):
        path = root / rel
        cycle_excluded = hash_cycle_excluded(rel, producer)
        exists = path.is_file()
        rows.append(
            {
                "artifact": rel,
                "path": rel,
                "producer": producer,
                "exists": exists,
                "size_bytes": 0 if cycle_excluded else path.stat().st_size if exists else 0,
                # Both are recorded on purpose. `sha256` is the raw-byte digest a
                # third party can confirm with `sha256sum` without running this
                # code; `content_sha256` is the compression-invariant digest the
                # diffoscope actually gates on for images. See
                # roadmap_tracks.image_content_hash for why they differ.
                "sha256": "" if cycle_excluded else _sha256(path),
                "content_sha256": (
                    "" if cycle_excluded else image_content_sha256(path) if is_image_artifact(rel) else ""
                ),
                "deterministic_seed": context.deterministic_seed,
                "config_digest": context.config_digest,
                "source_commit": context.source_commit,
                "producer_configured": producer in configured,
                "consumers": list(consumers.get(rel, ())),
                "validation_gates": list(gates.get(rel, ())),
                "claim_ids": sorted(claims.get(rel, [])),
                "hash_checked": not cycle_excluded,
                "cycle_excluded": cycle_excluded,
                "hash_authority": HASH_CYCLE_AUTHORITY if cycle_excluded else "this_record",
                "complete": exists and producer in configured and bool(consumers.get(rel)) and bool(gates.get(rel)),
            }
        )
    return rows
