"""Evidence crosswalk, dependency graph, and semantic certificate inputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from json_io import load_json as _load_json
from ontology.bindings import (
    BERNOULLI_EXPECTED_TERMS,
    SI_EXPECTED_TERMS,
)

from manuscript.sheaf.coverage import load_sheaf_coverage_context
from manuscript.sheaf.semantic_maps import ARTIFACT_GATES, ARTIFACT_PRODUCERS
from manuscript.sheaf.semantic_restrictions import _configured_analysis_scripts, _gnn_symbols


def _section_records(project_root: Path) -> list[dict[str, Any]]:
    ctx = load_sheaf_coverage_context(project_root)
    records: list[dict[str, Any]] = []
    by_id = {section.id: section for section in ctx.manifest.sections}
    for row in ctx.matrix.sections:
        section = by_id[row.section_id]
        records.append(
            {
                "id": section.id,
                "title": section.title,
                "imrad": section.imrad,
                "kind": section.kind,
                "compose": section.compose,
                "tracks": {
                    cell.track_id: {
                        "status": cell.status,
                        "path": cell.path,
                    }
                    for cell in row.cells
                    if cell.bound
                },
            }
        )
    return records


def _claim_records(root: Path) -> list[dict[str, Any]]:
    path = root / "data" / "claim_ledger.yaml"
    if not path.is_file():
        return []
    ledger = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    records: list[dict[str, Any]] = []
    for claim in ledger.get("claims") or []:
        records.append(
            {
                "id": claim.get("id"),
                "statement": claim.get("statement"),
                "path": claim.get("path"),
                "section": claim.get("section"),
                "tracks": claim.get("tracks") or [],
                "evidence": claim.get("evidence") or {},
            }
        )
    return records


def build_evidence_crosswalk(project_root: Path) -> dict[str, Any]:
    """Build a claim-to-artifact crosswalk from the typed claim ledger."""
    root = project_root.resolve()
    claims = []
    for claim in _claim_records(root):
        rel = str(claim.get("path") or "")
        artifact = root / rel
        claims.append(
            {
                **claim,
                "artifact_exists": artifact.exists(),
                "producer": ARTIFACT_PRODUCERS.get(rel, "manual"),
                "validation_gates": list(ARTIFACT_GATES.get(rel, ("validate_outputs",))),
            }
        )
    return {
        "schema": "template_active_inference.evidence_crosswalk.v1",
        "claim_count": len(claims),
        "claims": claims,
    }


def build_validation_dependency_graph(project_root: Path) -> dict[str, Any]:
    """Build script → artifact → manuscript/gate dependency records."""
    from roadmap_tracks.sheaf_tracks import build_validation_dependency_graph as build_canonical_dependency_graph

    return dict(build_canonical_dependency_graph(project_root))


def validate_configured_artifact_producers(
    project_root: Path,
    *,
    configured_scripts: list[str] | None = None,
) -> list[str]:
    """Fail when required generated artifacts lack configured analysis producers."""
    root = project_root.resolve()
    configured = configured_scripts if configured_scripts is not None else _configured_analysis_scripts(root)
    issues: list[str] = []
    for rel, producer in sorted(ARTIFACT_PRODUCERS.items()):
        if producer not in configured:
            qualifier = " exists without" if (root / rel).exists() else " lacks"
            issues.append(f"required artifact {rel}{qualifier} configured producer {producer}")
    return issues


SEMANTIC_ARTIFACT_SOURCE_PATHS: dict[str, str] = {
    "coverage_matrix": "output/data/sheaf_coverage_matrix.json",
    "si_summary": "output/data/si_tmaze_summary.json",
    "analysis_statistics": "output/data/analysis_statistics.json",
    "claim_ledger": "data/claim_ledger.yaml",
    "evidence_crosswalk": "output/data/sheaf_evidence_crosswalk.json",
    "dependency_graph": "output/data/validation_dependency_graph.json",
    "analytical_assumption_index": "output/data/analytical_assumption_index.json",
    "animation_frame_deltas": "output/data/animation_frame_deltas.json",
    "manuscript_staleness": "output/reports/manuscript_staleness_report.json",
    "track_lane_matrix": "output/data/track_lane_matrix.json",
    "track_improvement_scope": "output/data/track_improvement_scope.json",
    "evidence_field_index": "output/data/evidence_field_index.json",
    "release_bundle": "output/reports/release_bundle_manifest.json",
    "theorem_traceability": "output/data/theorem_traceability_matrix.json",
    "section_status_matrix": "output/data/sheaf_section_status_matrix.json",
    "sheaf_render_log": "output/reports/sheaf_render_log.json",
    "proof_dependency_graph": "output/data/proof_dependency_graph.json",
    "state_transition_table": "output/data/state_transition_table.json",
    "ablation_sensitivity_report": "output/reports/ablation_sensitivity_report.json",
    "release_attestation": "output/reports/release_attestation.json",
    "security_posture": "output/reports/security_posture_audit.json",
}

SEMANTIC_PAYLOAD_PATHS: dict[str, str] = {
    "sensitivity": "output/data/sensitivity_sweep.json",
    "uncertainty": "output/data/uncertainty_summary.json",
    "benchmark": "output/data/toy_benchmark_matrix.json",
    "model_checking": "output/reports/model_checking_witnesses.json",
    "interop": "output/data/interop_roundtrip_report.json",
    "adversarial": "output/reports/adversarial_audit.json",
    "stale": "output/reports/stale_artifact_report.json",
    "manuscript_staleness": "output/reports/manuscript_staleness_report.json",
    "tokens": "output/data/manuscript_token_provenance.json",
    "figures": "output/data/figure_source_map.json",
    "scope": "output/reports/scope_boundary_audit.json",
    "provenance": "output/data/artifact_provenance.json",
    "assumptions": "output/data/analytical_assumption_index.json",
    "animation_deltas": "output/data/animation_frame_deltas.json",
    "release_bundle": "output/reports/release_bundle_manifest.json",
    "evidence_fields": "output/data/evidence_field_index.json",
    "theorem_traceability": "output/data/theorem_traceability_matrix.json",
    "gate_index": "output/data/validation_gate_index.json",
    "section_status": "output/data/sheaf_section_status_matrix.json",
    "render_log": "output/reports/sheaf_render_log.json",
    "track_lane": "output/data/track_lane_matrix.json",
    "artifact_contract": "output/data/artifact_contract_index.json",
    "track_scope": "output/data/track_improvement_scope.json",
    "blocked_scope": "output/reports/blocked_scope_manifest.json",
    "replay_matrix": "output/reports/replay_matrix.json",
    "proof_dependency": "output/data/proof_dependency_graph.json",
    "transition_table": "output/data/state_transition_table.json",
    "ablation_sensitivity": "output/reports/ablation_sensitivity_report.json",
    "release_attestation": "output/reports/release_attestation.json",
    "security_posture": "output/reports/security_posture_audit.json",
}


def _semantic_artifact_sources(root: Path) -> dict[str, dict[str, Any]]:
    return {key: {"path": rel, "exists": (root / rel).exists()} for key, rel in SEMANTIC_ARTIFACT_SOURCE_PATHS.items()}


def _semantic_payloads(root: Path) -> dict[str, dict[str, Any]]:
    return {key: _load_json(root / rel) for key, rel in SEMANTIC_PAYLOAD_PATHS.items()}


def _semantic_track_rows(ctx: Any) -> list[dict[str, Any]]:
    return [
        {
            "id": tid,
            "renderer": spec.renderer,
            "optional": spec.optional,
            "order": spec.order,
            "paper_role": spec.paper_role,
            "paper_use": spec.paper_use,
        }
        for tid, spec in sorted(ctx.registry.tracks.items(), key=lambda item: item[1].order)
    ]


def _semantic_shared_symbols(root: Path) -> dict[str, dict[str, str | None]]:
    bernoulli_symbols = _gnn_symbols(root, "gnn/bernoulli_toy.gnn.md")
    si_symbols = _gnn_symbols(root, "gnn/si_tmaze.gnn.md")
    return {
        "bernoulli": {var: bernoulli_symbols.get(var) for var in BERNOULLI_EXPECTED_TERMS},
        "si_tmaze": {var: si_symbols.get(var) for var in SI_EXPECTED_TERMS},
    }


def _canonical_restriction_snapshot(root: Path) -> dict[str, bool]:
    try:
        from roadmap_tracks.sheaf_tracks import _canonical_restrictions

        return dict(_canonical_restrictions(root))
    except (ImportError, OSError, ValueError, KeyError, TypeError):
        return {}
