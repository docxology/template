"""Section-track status and render-log artifacts for the manuscript sheaf."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

from manuscript.sheaf.coverage import load_sheaf_coverage_context

STATUS_MATRIX_SCHEMA = "template_active_inference.sheaf_section_status_matrix.v1"
RENDER_LOG_SCHEMA = "template_active_inference.sheaf_render_log.v1"


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _claim_indexes(root: Path) -> tuple[dict[str, list[str]], dict[str, list[str]], dict[tuple[str, str], list[str]]]:
    ledger = _load_yaml(root / "data" / "claim_ledger.yaml")
    by_track: dict[str, list[str]] = defaultdict(list)
    by_path: dict[str, list[str]] = defaultdict(list)
    by_section_track: dict[tuple[str, str], list[str]] = defaultdict(list)
    for claim in ledger.get("claims") or []:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("id") or "")
        if not claim_id:
            continue
        rel = claim.get("path")
        if rel:
            by_path[str(rel)].append(claim_id)
        section = str(claim.get("section") or "")
        for track in claim.get("tracks") or []:
            track_id = str(track)
            by_track[track_id].append(claim_id)
            if section:
                by_section_track[(section, track_id)].append(claim_id)
    return (
        {key: sorted(set(value)) for key, value in by_track.items()},
        {key: sorted(set(value)) for key, value in by_path.items()},
        {key: sorted(set(value)) for key, value in by_section_track.items()},
    )


def _artifact_indexes(root: Path) -> tuple[dict[str, str], dict[str, list[str]], dict[str, list[str]]]:
    try:
        from manuscript.sheaf.semantic import ARTIFACT_CONSUMERS, ARTIFACT_GATES, ARTIFACT_PRODUCERS
    except ImportError:
        return {}, {}, {}
    producers = dict(ARTIFACT_PRODUCERS)
    by_section: dict[str, list[str]] = defaultdict(list)
    by_gate: dict[str, list[str]] = defaultdict(list)
    for rel, consumers in ARTIFACT_CONSUMERS.items():
        for section_id in consumers:
            by_section[str(section_id)].append(rel)
    for rel, gates in ARTIFACT_GATES.items():
        for gate in gates:
            by_gate[str(gate)].append(rel)
    return (
        producers,
        {key: sorted(value) for key, value in by_section.items()},
        {key: sorted(value) for key, value in by_gate.items()},
    )


def build_sheaf_section_status_matrix(project_root: Path) -> dict[str, Any]:
    """Build one explicit status row for every section x registered-track cell."""
    root = project_root.resolve()
    ctx = load_sheaf_coverage_context(root)
    claim_by_track, claim_by_path, claim_by_section_track = _claim_indexes(root)
    _, artifacts_by_section, _ = _artifact_indexes(root)
    try:
        from roadmap_tracks.sheaf_tracks import CANONICAL_ARTIFACTS
    except ImportError:
        CANONICAL_ARTIFACTS = {}

    rows: list[dict[str, Any]] = []
    section_summaries: list[dict[str, Any]] = []
    track_counters: dict[str, Counter[str]] = {track_id: Counter() for track_id in ctx.matrix.track_ids}
    section_by_id = {section.id: section for section in ctx.manifest.sections}
    status_counts: Counter[str] = Counter()
    missing_required_count = 0

    for section_row in ctx.matrix.sections:
        section = section_by_id[section_row.section_id]
        section_counts: Counter[str] = Counter()
        for cell in section_row.cells:
            spec = ctx.registry.tracks[cell.track_id]
            fragment_claims = claim_by_path.get(cell.path or "", [])
            track_claims = claim_by_track.get(cell.track_id, [])
            section_track_claims = claim_by_section_track.get((section.id, cell.track_id), [])
            canonical_artifact = CANONICAL_ARTIFACTS.get(cell.track_id, "")
            canonical_exists = bool(canonical_artifact and (root / canonical_artifact).is_file())
            status = cell.status
            has_claim_evidence = bool(fragment_claims or section_track_claims or track_claims)
            if cell.bound and cell.status == "present" and has_claim_evidence:
                status = "validated"
            if cell.bound and cell.status == "missing" and not spec.optional:
                missing_required_count += 1
            row = {
                "section_id": section.id,
                "section_title": section.title,
                "imrad": section.imrad,
                "section_kind": section.kind,
                "compose": section.should_compose(),
                "track_id": cell.track_id,
                "track_label": spec.label,
                "renderer": spec.renderer,
                "optional": spec.optional,
                "bound": cell.bound,
                "fragment_path": cell.path,
                "fragment_exists": bool(cell.path and (root / cell.path).is_file()),
                "coverage_status": cell.status,
                "status": status,
                "canonical_artifact": canonical_artifact,
                "canonical_artifact_exists": canonical_exists,
                "section_artifacts": artifacts_by_section.get(section.id, []),
                "claim_ids": sorted(set(fragment_claims + section_track_claims + track_claims)),
                "has_claim_evidence": has_claim_evidence,
                "validated": status == "validated",
            }
            rows.append(row)
            section_counts[cell.status] += 1
            track_counters[cell.track_id][cell.status] += 1
            status_counts[status] += 1

        bound_count = section_counts["present"] + section_counts["missing"]
        section_status = "group" if section.kind == "group" else "fully_sheafed"
        if section.kind != "group" and section_counts["missing"]:
            section_status = "missing_bound_fragments"
        elif section.kind != "group" and bound_count == 0:
            section_status = "unbound"
        section_summaries.append(
            {
                "section_id": section.id,
                "title": section.title,
                "imrad": section.imrad,
                "kind": section.kind,
                "compose": section.should_compose(),
                "bound_count": bound_count,
                "present_count": section_counts["present"],
                "missing_count": section_counts["missing"],
                "absent_count": section_counts["absent"],
                "status": section_status,
            }
        )

    track_summaries = []
    for track_id in ctx.matrix.track_ids:
        spec = ctx.registry.tracks[track_id]
        counts = track_counters[track_id]
        bound_count = counts["present"] + counts["missing"]
        track_summaries.append(
            {
                "track_id": track_id,
                "label": spec.label,
                "renderer": spec.renderer,
                "optional": spec.optional,
                "bound_section_count": bound_count,
                "present_section_count": counts["present"],
                "missing_section_count": counts["missing"],
                "absent_section_count": counts["absent"],
                "claim_count": len(claim_by_track.get(track_id, [])),
                "status": "complete" if counts["missing"] == 0 else "missing_fragments",
            }
        )

    composable = [row for row in section_summaries if row["compose"]]
    return {
        "schema": STATUS_MATRIX_SCHEMA,
        "sections": section_summaries,
        "tracks": track_summaries,
        "cells": rows,
        "section_count": len(section_summaries),
        "track_count": len(track_summaries),
        "cell_count": len(rows),
        "bound_cell_count": sum(1 for row in rows if row["bound"]),
        "present_cell_count": sum(1 for row in rows if row["coverage_status"] == "present"),
        "absent_cell_count": sum(1 for row in rows if row["coverage_status"] == "absent"),
        "missing_cell_count": sum(1 for row in rows if row["coverage_status"] == "missing"),
        "validated_cell_count": sum(1 for row in rows if row["validated"]),
        "status_counts": dict(sorted(status_counts.items())),
        "fully_sheafed_section_count": sum(1 for row in composable if row["status"] == "fully_sheafed"),
        "composable_section_count": len(composable),
        "missing_required_count": missing_required_count,
        "all_bound_fragments_present": missing_required_count == 0,
        "all_sections_have_status": bool(section_summaries) and all(bool(row["status"]) for row in section_summaries),
        "all_tracks_have_status": bool(track_summaries) and all(bool(row["status"]) for row in track_summaries),
    }


def build_sheaf_render_log(project_root: Path) -> dict[str, Any]:
    """Build a deterministic render/log summary for the sheaf manuscript layer."""
    root = project_root.resolve()
    matrix = build_sheaf_section_status_matrix(root)
    producers, _, artifacts_by_gate = _artifact_indexes(root)
    manuscript_outputs = sorted(
        path.relative_to(root).as_posix() for path in (root / "manuscript").glob("[0-9][0-9]_*.md")
    )
    events = [
        {
            "event_id": "registry_loaded",
            "component": "sheaf.registry",
            "input": "manuscript/sheaf/tracks.yaml",
            "output": "registered_tracks",
            "status": "ok" if matrix["track_count"] > 0 else "failed",
            "detail": f"{matrix['track_count']} tracks",
        },
        {
            "event_id": "manifest_loaded",
            "component": "sheaf.manifest",
            "input": "manuscript/sheaf/manifest.yaml",
            "output": "manifest_sections",
            "status": "ok" if matrix["section_count"] > 0 else "failed",
            "detail": f"{matrix['section_count']} sections",
        },
        {
            "event_id": "coverage_matrix_built",
            "component": "sheaf.coverage",
            "input": "registry+manifest",
            "output": "output/data/sheaf_coverage_matrix.json",
            "status": "ok" if matrix["missing_cell_count"] == 0 else "failed",
            "detail": f"{matrix['present_cell_count']} present cells",
        },
        {
            "event_id": "section_status_matrix_built",
            "component": "sheaf.status",
            "input": "registry+manifest+claim_ledger",
            "output": "output/data/sheaf_section_status_matrix.json",
            "status": "ok" if matrix["all_bound_fragments_present"] else "failed",
            "detail": f"{matrix['cell_count']} section-track cells",
        },
        {
            "event_id": "layers_renderer_bound",
            "component": "sheaf.layers_report",
            "input": "output/data/sheaf_section_status_matrix.json",
            "output": "manuscript/08_methods_sheaf.md",
            "status": "ok" if (root / "manuscript" / "08_methods_sheaf.md").is_file() else "failed",
            "detail": "methods sheaf layer tables",
        },
        {
            "event_id": "semantic_artifacts_indexed",
            "component": "sheaf.semantic",
            "input": "artifact producers",
            "output": "output/data/validation_dependency_graph.json",
            "status": "ok" if producers else "failed",
            "detail": f"{len(producers)} artifact producer rows",
        },
        {
            "event_id": "validation_gates_indexed",
            "component": "gates",
            "input": "artifact gate map",
            "output": "output/data/validation_gate_index.json",
            "status": "ok" if artifacts_by_gate else "failed",
            "detail": f"{len(artifacts_by_gate)} gate groups",
        },
        {
            "event_id": "manuscript_sections_composed",
            "component": "sheaf.compose",
            "input": "manifest fragments",
            "output": "manuscript/*.md",
            "status": "ok" if manuscript_outputs else "failed",
            "detail": f"{len(manuscript_outputs)} composed markdown files",
        },
    ]
    return {
        "schema": RENDER_LOG_SCHEMA,
        "events": events,
        "event_count": len(events),
        "rendered_section_count": len(manuscript_outputs),
        "artifact_producer_count": len(producers),
        "all_events_ok": all(event["status"] == "ok" for event in events),
        "section_status_matrix": "output/data/sheaf_section_status_matrix.json",
    }


def validate_sheaf_status_outputs(project_root: Path) -> list[str]:
    root = project_root.resolve()
    issues: list[str] = []
    status_path = root / "output" / "data" / "sheaf_section_status_matrix.json"
    render_log_path = root / "output" / "reports" / "sheaf_render_log.json"
    if not status_path.is_file():
        issues.append("missing output/data/sheaf_section_status_matrix.json")
    else:
        status = json.loads(status_path.read_text(encoding="utf-8"))
        if status.get("schema") != STATUS_MATRIX_SCHEMA:
            issues.append("sheaf_section_status_matrix.json schema mismatch")
        if status.get("all_bound_fragments_present") is not True:
            issues.append("sheaf_section_status_matrix.json has missing bound fragments")
        if status.get("all_sections_have_status") is not True or status.get("all_tracks_have_status") is not True:
            issues.append("sheaf_section_status_matrix.json has incomplete status rows")
    if not render_log_path.is_file():
        issues.append("missing output/reports/sheaf_render_log.json")
    else:
        render_log = json.loads(render_log_path.read_text(encoding="utf-8"))
        if render_log.get("schema") != RENDER_LOG_SCHEMA:
            issues.append("sheaf_render_log.json schema mismatch")
        if render_log.get("all_events_ok") is not True:
            issues.append("sheaf_render_log.json has failed render events")
    return issues


def write_sheaf_status_outputs(project_root: Path) -> dict[str, Path]:
    root = project_root.resolve()
    status_path = root / "output" / "data" / "sheaf_section_status_matrix.json"
    render_log_path = root / "output" / "reports" / "sheaf_render_log.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    render_log_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(
        json.dumps(build_sheaf_section_status_matrix(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    render_log_path.write_text(
        json.dumps(build_sheaf_render_log(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"section_status": status_path, "render_log": render_log_path}
