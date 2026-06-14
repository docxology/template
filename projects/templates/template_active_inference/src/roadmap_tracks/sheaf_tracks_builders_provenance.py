"""Provenance and replay-matrix builders for canonical sheaf tracks."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from roadmap_tracks.sheaf_tracks_context import _ProvenanceContext, _provenance_context
from roadmap_tracks.sheaf_tracks_helpers import _canonical_artifact_rows
from roadmap_tracks.sheaf_tracks_io import (
    _analysis_scripts,
    _artifact_maps,
    _load_json,
    _sha256,
)
from roadmap_tracks.sheaf_tracks_registry import CANONICAL_ARTIFACTS, CANONICAL_SCHEMA


def build_artifact_provenance(project_root: Path, *, context: _ProvenanceContext | None = None) -> dict[str, Any]:
    """Build canonical artifact, field-provenance, and bundle provenance rows."""
    root = project_root.resolve()
    rows = _canonical_artifact_rows(root, context or _provenance_context(root))
    field_rows = [
        {
            "artifact": row["artifact"],
            "jsonpath": "$",
            "source_commit": row["source_commit"],
            "config_digest": row["config_digest"],
            "seed": row["deterministic_seed"],
            "producer": row["producer"],
            "input_artifact_lineage": row["consumers"],
            "artifact_hash": row["sha256"],
            "complete": bool(
                row["source_commit"]
                and row["config_digest"]
                and isinstance(row["deterministic_seed"], int)
                and row["producer"]
                and (row["sha256"] or row["cycle_excluded"])
            ),
        }
        for row in rows
    ]
    artifacts = {
        row["artifact"]: {
            "path": row["artifact"],
            "producer": row["producer"],
            "exists": row["exists"],
            "size_bytes": row["size_bytes"],
            "sha256": row["sha256"],
            "deterministic_seed": row["deterministic_seed"],
            "config_digest": row["config_digest"],
            "source_commit": row["source_commit"],
        }
        for row in rows
    }
    coverage = {producer: producer in _analysis_scripts(root) for producer in sorted({row["producer"] for row in rows})}
    bundles = _artifact_bundles(root, rows)
    return {
        "schema": "template_active_inference.artifact_provenance.v1",
        "schema_version": CANONICAL_SCHEMA,
        "configured_analysis_scripts": _analysis_scripts(root),
        "producer_coverage": coverage,
        "artifacts": artifacts,
        "rows": rows,
        "field_provenance_rows": field_rows,
        "artifact_count": len(rows),
        "field_provenance_count": len(field_rows),
        "bundles": bundles,
        "bundle_count": len(bundles),
        "all_bundles_complete": all(bundle["complete"] for bundle in bundles),
        "all_records_complete": all(row["complete"] or row["cycle_excluded"] for row in rows),
        "all_field_provenance_complete": bool(field_rows) and all(row["complete"] for row in field_rows),
        "all_hashed": all((row["exists"] and row["sha256"]) or row["cycle_excluded"] for row in rows),
        "all_seeded": all(isinstance(row.get("deterministic_seed"), int) for row in rows),
        "all_config_digests": all(bool(row.get("config_digest")) for row in rows),
        "all_source_commits": all(bool(row.get("source_commit")) for row in rows),
        "all_producers_configured": all(coverage.values()),
        "cycle_hash_exclusions": sorted(row["artifact"] for row in rows if row["cycle_excluded"]),
    }


def _artifact_bundles(root: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_artifact = {row["artifact"]: row for row in rows}
    groups = {
        "core_data": (
            "output/data/parameter_sweep.csv",
            "output/data/si_policy_comparison.json",
            "output/data/pymdp_policy_posterior_grid.json",
            "output/data/si_graph_world_topology_traces.json",
        ),
        "semantic_audit": (
            CANONICAL_ARTIFACTS["semantic"],
            CANONICAL_ARTIFACTS["dependency"],
            CANONICAL_ARTIFACTS["section_status"],
            CANONICAL_ARTIFACTS["render_log"],
            CANONICAL_ARTIFACTS["track_lane_matrix"],
            CANONICAL_ARTIFACTS["evidence_fields"],
            CANONICAL_ARTIFACTS["theorem_traceability"],
            CANONICAL_ARTIFACTS["release_bundle"],
            CANONICAL_ARTIFACTS["artifact_diffoscope"],
            CANONICAL_ARTIFACTS["artifact_license"],
            CANONICAL_ARTIFACTS["release_notes"],
            CANONICAL_ARTIFACTS["scholarship"],
            CANONICAL_ARTIFACTS["security_posture"],
            CANONICAL_ARTIFACTS["proof_dependency_graph"],
            CANONICAL_ARTIFACTS["release_attestation"],
        ),
        "formal_interop": (
            CANONICAL_ARTIFACTS["model_checking"],
            CANONICAL_ARTIFACTS["interop"],
            CANONICAL_ARTIFACTS["proof_extraction"],
            CANONICAL_ARTIFACTS["proof_dependency_graph"],
            "output/reports/lean_theorem_inventory.json",
            "output/reports/gnn_lint_report.json",
        ),
        "finite_toy_scope": (
            CANONICAL_ARTIFACTS["state_space_catalog"],
            CANONICAL_ARTIFACTS["causal_ablation"],
            CANONICAL_ARTIFACTS["state_transition_table"],
            CANONICAL_ARTIFACTS["ablation_sensitivity_report"],
            CANONICAL_ARTIFACTS["sensitivity"],
            CANONICAL_ARTIFACTS["uncertainty"],
        ),
        "rendered_outputs": (
            "output/figures/semantic_gluing_graph.png",
            "output/figures/track_lane_promotion_map.png",
            "output/figures/theorem_traceability_graph.png",
            "output/figures/causal_ablation_heatmap.png",
            "output/figures/scholarship_source_map.png",
            "output/figures/security_posture_map.png",
            "output/reports/visualization_quality_audit.json",
            CANONICAL_ARTIFACTS["statistical_visualization_bridge"],
            "output/figures/si_belief_trajectory.gif",
            "output/data/animation_frame_deltas.json",
            "output/reports/figure_hash_manifest.json",
        ),
    }
    bundles = []
    for bundle_id, artifacts in groups.items():
        bundle_rows = []
        digest_parts = []
        missing = []
        for rel in artifacts:
            row = by_artifact.get(rel, {"artifact": rel, "exists": (root / rel).is_file(), "producer": ""})
            digest = _sha256(root / rel)
            if not (root / rel).is_file():
                missing.append(rel)
            digest_parts.append(f"{rel}:{digest}")
            bundle_rows.append(
                {"artifact": rel, "exists": (root / rel).is_file(), "sha256": digest, "producer": row["producer"]}
            )
        bundles.append(
            {
                "bundle_id": bundle_id,
                "artifacts": bundle_rows,
                "artifact_count": len(bundle_rows),
                "missing": missing,
                "bundle_hash": hashlib.sha256("\n".join(digest_parts).encode("utf-8")).hexdigest(),
                "complete": not missing and all(row["sha256"] for row in bundle_rows),
            }
        )
    return bundles


def build_replay_matrix(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    scripts = _analysis_scripts(root)
    producers, _, _ = _artifact_maps()
    replay = _load_json(root / "output" / "reports" / "reproducibility_replay.json")
    replay_by_artifact = {row.get("artifact"): row for row in replay.get("checks") or []}
    cycle_excluded = {
        CANONICAL_ARTIFACTS["provenance"],
        CANONICAL_ARTIFACTS["semantic"],
        CANONICAL_ARTIFACTS["dependency"],
        CANONICAL_ARTIFACTS["track_improvement_scope"],
        CANONICAL_ARTIFACTS["replay_matrix"],
        CANONICAL_ARTIFACTS["artifact_diffoscope"],
    }
    rows = []
    for script in scripts:
        outputs = sorted(rel for rel, producer in producers.items() if producer == script)
        if not outputs and script == "compose_manuscript.py":
            outputs = [
                path.relative_to(root).as_posix() for path in sorted((root / "manuscript").glob("[0-9][0-9]_*.md"))
            ]
        method = "subprocess_replay" if any(rel in replay_by_artifact for rel in outputs) else "artifact_fingerprint"
        checked_outputs = [rel for rel in outputs if rel not in cycle_excluded]
        replay_rows = [replay_by_artifact[rel] for rel in outputs if rel in replay_by_artifact]
        matched = (
            all(row.get("passed") is True for row in replay_rows)
            if replay_rows
            else all(_sha256(root / rel) for rel in checked_outputs)
        )
        rows.append(
            {
                "producer_script": script,
                "replay_method": method,
                "artifact_count": len(outputs),
                "artifacts": outputs,
                "cycle_excluded_artifacts": sorted(rel for rel in outputs if rel in cycle_excluded),
                "hash_checked_artifacts": checked_outputs,
                "input_config_hash": _sha256(root / "manuscript" / "config.yaml"),
                "output_hashes": {rel: _sha256(root / rel) for rel in checked_outputs},
                "matched": (bool(outputs) and matched) or (not outputs and script == "compose_manuscript.py"),
            }
        )
    return {
        "schema": "template_active_inference.replay_matrix.v1",
        "schema_version": CANONICAL_SCHEMA,
        "rows": rows,
        "check_count": len(rows),
        "row_count": len(rows),
        "configured_scripts": scripts,
        "all_configured_producers_represented": bool(rows) and {row["producer_script"] for row in rows} == set(scripts),
        "all_replay_rows_matched": bool(rows) and all(row["matched"] for row in rows),
        "all_replayed": bool(rows) and all(row["matched"] for row in rows),
    }
