"""Semantic gluing output writers and saved-certificate validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from manuscript.sheaf.semantic_certificate import build_semantic_gluing_certificate
from manuscript.sheaf.semantic_evidence import build_evidence_crosswalk, build_validation_dependency_graph
from manuscript.sheaf.semantic_issues import semantic_gluing_issues
from manuscript.sheaf.semantic_maps import SEMANTIC_RESTRICTION_LANES, SEMANTIC_SCHEMA
from manuscript.sheaf.semantic_refresh import (
    _refresh_animation_outputs,
    _refresh_artifact_contract_outputs,
    _refresh_hydrated_manuscript,
)
from manuscript.sheaf.semantic_restrictions import _load_json, _restriction_lane_summaries


def write_semantic_gluing_outputs(project_root: Path, *, settle: bool = True) -> dict[str, Path]:
    """Write semantic certificate, evidence crosswalk, and dependency graph outputs."""
    root = project_root.resolve()
    if settle:
        from roadmap_tracks.fixed_point import run_semantic_fixed_point

        paths = cast(dict[str, Path], run_semantic_fixed_point(root, require_analysis_outputs=False))
        if "dependency_graph" not in paths and "dependency" in paths:
            paths["dependency_graph"] = paths["dependency"]
        return paths
    data_dir = root / "output" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    crosswalk_path = data_dir / "sheaf_evidence_crosswalk.json"
    dependency_path = data_dir / "validation_dependency_graph.json"
    certificate_path = data_dir / "sheaf_gluing_certificate.json"

    _refresh_animation_outputs(root)
    _refresh_hydrated_manuscript(root)
    from manuscript.sheaf.status import write_sheaf_status_outputs

    status_paths = write_sheaf_status_outputs(root)
    crosswalk_path.write_text(
        json.dumps(build_evidence_crosswalk(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    dependency_path.write_text(
        json.dumps(build_validation_dependency_graph(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    certificate_path.write_text(
        json.dumps(build_semantic_gluing_certificate(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _refresh_animation_outputs(root)
    _refresh_hydrated_manuscript(root)
    status_paths = write_sheaf_status_outputs(root)
    certificate_path.write_text(
        json.dumps(build_semantic_gluing_certificate(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _refresh_animation_outputs(root)
    _refresh_artifact_contract_outputs(root)
    certificate_path.write_text(
        json.dumps(build_semantic_gluing_certificate(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _refresh_artifact_contract_outputs(root)
    certificate_path.write_text(
        json.dumps(build_semantic_gluing_certificate(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "certificate": certificate_path,
        "crosswalk": crosswalk_path,
        "dependency_graph": dependency_path,
        **status_paths,
    }


def _stable_artifact_graph(payload: dict[str, Any]) -> dict[str, Any]:
    graph = payload.get("artifact_graph") or {}
    stable: dict[str, Any] = {}
    for rel, record in graph.items():
        if isinstance(record, dict):
            stable[rel] = {
                key: record.get(key)
                for key in ("producer", "produced_by_configured_analysis", "consumers", "validation_gates", "claim_ids")
            }
    return stable


def _stable_certificate_fields(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": payload.get("schema"),
        "tracks": payload.get("tracks"),
        "sections": payload.get("sections"),
        "shared_symbols": payload.get("shared_symbols"),
        "restrictions": payload.get("restrictions"),
        "restriction_lanes": payload.get("restriction_lanes"),
        "lane_summaries": payload.get("lane_summaries"),
        "artifact_graph": _stable_artifact_graph(payload),
    }


def _semantic_lane_summary_issues(payload: dict[str, Any]) -> list[str]:
    restrictions = payload.get("restrictions") or {}
    lanes = payload.get("restriction_lanes") or {}
    summaries = payload.get("lane_summaries") or {}
    issues: list[str] = []
    if set(lanes) != set(restrictions):
        issues.append("saved sheaf_gluing_certificate.json has incomplete restriction lane assignments")
        return issues
    if any(lane not in SEMANTIC_RESTRICTION_LANES for lane in lanes.values()):
        issues.append("saved sheaf_gluing_certificate.json has unknown restriction lanes")
        return issues
    expected = _restriction_lane_summaries(restrictions, lanes)
    if summaries != expected:
        issues.append("saved sheaf_gluing_certificate.json lane summaries disagree with restrictions")
    all_ok = bool(expected) and all(row["all_ok"] for row in expected.values())
    if payload.get("all_lane_summaries_ok") != all_ok:
        issues.append("saved sheaf_gluing_certificate.json all_lane_summaries_ok disagrees with lane summaries")
    return issues


def validate_semantic_gluing(project_root: Path) -> list[str]:
    """Validate the live semantic certificate and its generated artifact."""
    root = project_root.resolve()
    path = root / "output" / "data" / "sheaf_gluing_certificate.json"
    if not path.is_file():
        missing: list[str] = semantic_gluing_issues(root)
        missing.append("missing output/data/sheaf_gluing_certificate.json")
        return missing
    saved = _load_json(path)
    saved_issues: list[str] = []
    if saved.get("schema") != SEMANTIC_SCHEMA:
        saved_issues.append(f"saved sheaf_gluing_certificate.json schema is not {SEMANTIC_SCHEMA}")
    if saved.get("ok") is not True:
        saved_issues.append("saved sheaf_gluing_certificate.json is not ok")
    # Cross-check the saved aggregate against the saved per-obligation rows
    # (PR#23 class): a forged ok=true over a failing proof obligation fails closed.
    saved_obligations = saved.get("proof_obligations") or []
    obligations_ok = bool(saved_obligations) and all(
        row.get("class") and row.get("restriction") and row.get("ok") is True for row in saved_obligations
    )
    if saved.get("ok") is True and not obligations_ok:
        saved_issues.append("saved sheaf_gluing_certificate.json ok disagrees with proof obligations")
    saved_issues.extend(_semantic_lane_summary_issues(saved))
    if saved.get("restrictions", {}).get("coverage_missing") != 0:
        saved_issues.append("saved sheaf_gluing_certificate.json records missing coverage")
    issues: list[str] = semantic_gluing_issues(root)
    issues.extend(saved_issues)
    live = build_semantic_gluing_certificate(root)
    if _stable_certificate_fields(saved) != _stable_certificate_fields(live):
        issues.append("saved sheaf_gluing_certificate.json is stale relative to live semantic fields")
    return issues
