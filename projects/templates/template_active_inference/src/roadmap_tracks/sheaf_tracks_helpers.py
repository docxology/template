"""Shared helpers for sheaf-track artifact builders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from roadmap_tracks.sheaf_tracks_context import _ProvenanceContext, _provenance_context
from roadmap_tracks.sheaf_tracks_io import (
    _analysis_scripts,
    _artifact_maps,
    _claim_ids_by_path,
    _sha256,
)
from roadmap_tracks.sheaf_tracks_registry import CANONICAL_ARTIFACTS, LEGACY_ARTIFACTS


def _entropy(values: list[float]) -> float:
    import math

    return float(-sum(value * math.log(value) for value in values if value > 0.0))


def _root_output_dir(project_root: Path) -> Path:
    root = project_root.resolve()
    for parent in root.parents:
        if (parent / "run.sh").is_file() and (parent / "projects").is_dir():
            return parent / "output" / "templates" / root.name
    return root.parents[2] / "output" / "templates" / root.name


def _copied_parity(project_root: Path, rel_paths: list[str]) -> dict[str, Any]:
    root = project_root.resolve()
    copied_root = _root_output_dir(root)
    rows: list[dict[str, Any]] = []
    for rel in rel_paths:
        source = root / rel
        copied = copied_root / rel.removeprefix("output/")
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
        "copied_root": copied_root.as_posix(),
        "copied_root_exists": copied_root.is_dir(),
        "rows": rows,
        "row_count": len(rows),
        "all_required_sources_present": all(row["source_exists"] for row in rows),
        "all_copied_outputs_match": all(row["hash_matches"] for row in rows if row["copied_exists"]),
        "all_copied_outputs_match_or_deferred": all(row["matches_when_copied"] for row in rows),
        "pre_copy_stage": any(row["comparison_deferred_until_copy"] for row in rows),
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
        cycle_excluded = rel in {
            CANONICAL_ARTIFACTS["provenance"],
            CANONICAL_ARTIFACTS["semantic"],
            CANONICAL_ARTIFACTS["dependency"],
            CANONICAL_ARTIFACTS["track_improvement_scope"],
            CANONICAL_ARTIFACTS["replay_matrix"],
            CANONICAL_ARTIFACTS["artifact_diffoscope"],
            CANONICAL_ARTIFACTS["artifact_contract_index"],
            "output/figures/si_belief_trajectory.gif",
            "output/data/animation_frame_deltas.json",
        }
        rows.append(
            {
                "artifact": rel,
                "path": rel,
                "producer": producer,
                "exists": path.is_file(),
                "size_bytes": path.stat().st_size if path.is_file() else 0,
                "sha256": _sha256(path),
                "deterministic_seed": context.deterministic_seed,
                "config_digest": context.config_digest,
                "source_commit": context.source_commit,
                "producer_configured": producer in configured,
                "consumers": list(consumers.get(rel, ())),
                "validation_gates": list(gates.get(rel, ())),
                "claim_ids": sorted(claims.get(rel, [])),
                "hash_checked": not cycle_excluded,
                "cycle_excluded": cycle_excluded,
                "complete": path.is_file()
                and producer in configured
                and bool(consumers.get(rel))
                and bool(gates.get(rel)),
            }
        )
    return rows
