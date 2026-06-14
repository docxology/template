"""Release-bundle and evidence-field builders for canonical sheaf tracks."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from roadmap_tracks.sheaf_tracks_helpers import _copied_parity
from roadmap_tracks.sheaf_tracks_io import (
    _artifact_maps,
    _claim_ids_by_path,
    _claim_records,
    _load_json,
    _load_structured,
    _sha256,
)
from roadmap_tracks.sheaf_tracks_registry import CANONICAL_ARTIFACTS, CANONICAL_SCHEMA


def _field_value(payload: dict[str, Any], field: str) -> Any:
    value: Any = payload
    for part in field.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value


def build_evidence_field_index(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    token_provenance = _load_json(root / "output" / "data" / "manuscript_token_provenance.json")
    tokens_by_source: dict[str, list[str]] = {}
    for row in token_provenance.get("tokens") or []:
        tokens_by_source.setdefault(str(row.get("source") or ""), []).append(str(row.get("token") or ""))
    rows = []
    for claim in _claim_records(root):
        rel = str(claim.get("path") or "")
        evidence = claim.get("evidence") or {}
        field = str(evidence.get("field") or evidence.get("jsonpath") or "")
        payload = _load_structured(root / rel)
        validators = list((_artifact_maps()[2]).get(rel, ("validate_outputs",)))
        jsonpath = f"$.{field}" if field else "$"
        rows.append(
            {
                "claim_id": claim.get("id"),
                "artifact": rel,
                "source_artifact": rel,
                "field": field,
                "jsonpath": jsonpath,
                "field_present": field == "" or _field_value(payload, field) is not None,
                "manuscript_section": claim.get("section", ""),
                "tracks": claim.get("tracks") or [],
                "tokens": sorted(set(tokens_by_source.get(rel, []))),
                "validator": validators[0] if validators else "validate_outputs",
                "validators": validators,
                "semantic_restriction": f"{claim.get('id')}_evidence_field_present",
                "validator_count": len(validators),
                "token_count": len(set(tokens_by_source.get(rel, []))),
                "edge_kind": "claim_field_to_artifact",
            }
        )
    return {
        "schema": "template_active_inference.evidence_field_index.v1",
        "schema_version": CANONICAL_SCHEMA,
        "rows": rows,
        "field_count": len(rows),
        "all_fields_mapped": bool(rows)
        and all(
            row["artifact"]
            and row["source_artifact"]
            and row["field_present"]
            and row["claim_id"]
            and row["jsonpath"]
            and row["validator"]
            and row["semantic_restriction"]
            for row in rows
        ),
    }


def build_release_bundle_manifest(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    required = [
        CANONICAL_ARTIFACTS["semantic"],
        CANONICAL_ARTIFACTS["dependency"],
        CANONICAL_ARTIFACTS["provenance"],
        CANONICAL_ARTIFACTS["replay_matrix"],
        CANONICAL_ARTIFACTS["sensitivity"],
        CANONICAL_ARTIFACTS["uncertainty"],
        CANONICAL_ARTIFACTS["counterexample"],
        CANONICAL_ARTIFACTS["model_checking"],
        CANONICAL_ARTIFACTS["interop"],
        CANONICAL_ARTIFACTS["adversarial_audit"],
        CANONICAL_ARTIFACTS["evidence_fields"],
        CANONICAL_ARTIFACTS["theorem_traceability"],
        CANONICAL_ARTIFACTS["gate_ergonomics"],
        CANONICAL_ARTIFACTS["scholarship"],
        CANONICAL_ARTIFACTS["security_posture"],
        CANONICAL_ARTIFACTS["track_lane_matrix"],
        CANONICAL_ARTIFACTS["artifact_contract_index"],
        "output/figures/si_belief_trajectory.gif",
        "output/figures/semantic_gluing_graph.png",
        "output/figures/track_lane_promotion_map.png",
        "output/figures/artifact_contract_map.png",
        "output/figures/theorem_traceability_graph.png",
        "output/figures/causal_ablation_heatmap.png",
        "output/figures/scholarship_source_map.png",
        "output/reports/visualization_quality_audit.json",
        CANONICAL_ARTIFACTS["statistical_visualization_bridge"],
        "output/pdf/template_active_inference_combined.pdf",
        "output/web/template_active_inference.html",
        CANONICAL_ARTIFACTS["artifact_diffoscope"],
        CANONICAL_ARTIFACTS["proof_extraction"],
        CANONICAL_ARTIFACTS["state_space_catalog"],
        CANONICAL_ARTIFACTS["causal_ablation"],
        CANONICAL_ARTIFACTS["artifact_license"],
        CANONICAL_ARTIFACTS["release_notes"],
        CANONICAL_ARTIFACTS["proof_dependency_graph"],
        CANONICAL_ARTIFACTS["state_transition_table"],
        CANONICAL_ARTIFACTS["ablation_sensitivity_report"],
        CANONICAL_ARTIFACTS["release_attestation"],
    ]
    rows = []
    for rel in required:
        deferred_until_render = rel.startswith("output/pdf/") or rel.startswith("output/web/")
        rows.append(
            {
                "artifact": rel,
                "source_exists": (root / rel).is_file(),
                "source_sha256": _sha256(root / rel),
                "required_deliverable": True,
                "deferred_until_render": deferred_until_render and not (root / rel).is_file(),
            }
        )
    parity = _copied_parity(root, required)
    digest = hashlib.sha256(
        "\n".join(f"{row['artifact']}:{row['source_sha256']}" for row in rows).encode("utf-8")
    ).hexdigest()
    return {
        "schema": "template_active_inference.release_bundle_manifest.v1",
        "schema_version": CANONICAL_SCHEMA,
        "rows": rows,
        "artifact_count": len(rows),
        "bundle_hash": digest,
        "copied_output_parity": parity,
        "all_required_sources_present": all(row["source_exists"] or row["deferred_until_render"] for row in rows),
        "all_copied_outputs_match_or_deferred": parity["all_copied_outputs_match_or_deferred"],
    }


def build_theorem_traceability_matrix(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    lean = _load_json(root / "output" / "reports" / "lean_theorem_inventory.json")
    model = _load_json(root / CANONICAL_ARTIFACTS["model_checking"])
    claims = _claim_ids_by_path(root)
    evidence = _load_json(root / CANONICAL_ARTIFACTS["evidence_fields"])
    evidence_claims = {row.get("claim_id"): row for row in evidence.get("rows") or []}
    evidence_jsonpaths = sorted({str(row.get("jsonpath")) for row in evidence.get("rows") or [] if row.get("jsonpath")})
    model_claim_ids = sorted(claims.get(CANONICAL_ARTIFACTS["model_checking"], [])) or sorted(evidence_claims)[:3]
    theorem_rows = lean.get("theorems") or lean.get("rows") or []
    rows = []
    for idx, theorem in enumerate(theorem_rows):
        rows.append(
            {
                "theorem": theorem.get("name", theorem.get("theorem", f"theorem_{idx}")),
                "status": theorem.get("status", "proved" if lean.get("all_proved") else "unknown"),
                "model_witnesses": [row.get("id", row.get("model")) for row in model.get("rows") or []],
                "finite_models": sorted({str(row.get("model")) for row in model.get("rows") or [] if row.get("model")}),
                "claim_ids": model_claim_ids,
                "evidence_fields": evidence_jsonpaths,
                "source_artifacts": sorted(
                    {str(row.get("artifact")) for row in evidence.get("rows") or [] if row.get("artifact")}
                ),
                "linked": bool(model.get("rows")) and lean.get("all_proved") is True,
            }
        )
    if not rows:
        rows.append(
            {
                "theorem": "lean_boundary_inventory",
                "status": "proved" if lean.get("all_proved") else "unknown",
                "model_witnesses": [row.get("id", row.get("model")) for row in model.get("rows") or []],
                "finite_models": sorted({str(row.get("model")) for row in model.get("rows") or [] if row.get("model")}),
                "claim_ids": model_claim_ids,
                "evidence_fields": evidence_jsonpaths,
                "source_artifacts": sorted(
                    {str(row.get("artifact")) for row in evidence.get("rows") or [] if row.get("artifact")}
                ),
                "linked": bool(model.get("rows")) and lean.get("all_proved") is True,
            }
        )
    return {
        "schema": "template_active_inference.theorem_traceability_matrix.v1",
        "schema_version": CANONICAL_SCHEMA,
        "rows": rows,
        "row_count": len(rows),
        "all_theorems_linked": bool(rows) and all(row["linked"] for row in rows),
    }
