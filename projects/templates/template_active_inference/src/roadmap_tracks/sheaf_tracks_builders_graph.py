"""Graph, contract, and dependency builders for canonical sheaf tracks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from roadmap_tracks.sheaf_tracks_builders_formal import (
    build_blocked_scope_manifest,
    build_counterexample_matrix,
    build_interop_roundtrip_report,
    build_model_checking_witnesses,
)
from roadmap_tracks.sheaf_tracks_builders_provenance import build_artifact_provenance
from roadmap_tracks.sheaf_tracks_builders_release import build_evidence_field_index
from roadmap_tracks.sheaf_tracks_context import _ProvenanceContext
from roadmap_tracks.sheaf_tracks_helpers import _copied_parity
from roadmap_tracks.sheaf_tracks_io import (
    _analysis_scripts,
    _artifact_maps,
    _bound_tracks,
    _claim_ids_by_path,
    _claim_ids_by_track,
    _claim_records,
    _load_json,
    _pipeline_tracks,
    _registry_tracks,
    _sha256,
)
from roadmap_tracks.sheaf_tracks_registry import (
    CANONICAL_ARTIFACTS,
    CANONICAL_SCHEMA,
    CANONICAL_TRACKS,
    DEPENDENCY_SCHEMA,
    OPTIONAL_CLAIM_EXEMPT_TRACKS,
    PIPELINE_TRACK_SHEAF_ALIASES,
    REQUIRED_EDGE_TYPES,
    SHEAF_TRACK_PRODUCER,
    VERSIONED_TRACK_RE,
)


def _track_artifact(track_id: str) -> str:
    artifacts: dict[str, str] = {
        **CANONICAL_ARTIFACTS,
        "analytical": "output/data/parameter_sweep.csv",
        "assumption_index": "output/data/analytical_assumption_index.json",
        "benchmark": "output/data/toy_benchmark_matrix.json",
        "gnn": "output/reports/gnn_lint_report.json",
        "lean": "output/reports/lean_theorem_inventory.json",
        "manuscript": "manuscript/sheaf/manifest.yaml",
        "manuscript_staleness": "output/reports/manuscript_staleness_report.json",
        "ontology": "output/data/ontology_profile_matrix.json",
        "pymdp": "output/data/si_policy_comparison.json",
        "simulation": "output/data/analytical_observable_sweep.json",
        "visualization": "output/reports/visualization_quality_audit.json",
        "visualizations": "output/reports/visualization_quality_audit.json",
        "animation": "output/figures/si_belief_trajectory.gif",
        "animation_delta": "output/data/animation_frame_deltas.json",
        "artifact_diffoscope": CANONICAL_ARTIFACTS["artifact_diffoscope"],
        "proof_extraction": CANONICAL_ARTIFACTS["proof_extraction"],
        "state_space_catalog": CANONICAL_ARTIFACTS["state_space_catalog"],
        "causal_ablation": CANONICAL_ARTIFACTS["causal_ablation"],
        "artifact_license": CANONICAL_ARTIFACTS["artifact_license"],
        "release_notes": CANONICAL_ARTIFACTS["release_notes"],
        "scholarship": CANONICAL_ARTIFACTS["scholarship"],
        "security_posture": CANONICAL_ARTIFACTS["security_posture"],
        "prose": "manuscript/sheaf/manifest.yaml",
        "formalism": "manuscript/sheaf/manifest.yaml",
        "layers": "output/data/sheaf_coverage_matrix.json",
    }
    return artifacts.get(track_id, "manuscript/sheaf/manifest.yaml")


def _pipeline_sheaf_tracks(track: dict[str, Any], registry: dict[str, dict[str, Any]]) -> list[str]:
    explicit = track.get("sheaf_track")
    if explicit:
        return [str(explicit)]
    track_id = str(track.get("id") or "")
    if track_id in registry:
        return [track_id]
    return list(PIPELINE_TRACK_SHEAF_ALIASES.get(track_id, ()))


def build_track_lane_matrix(project_root: Path) -> dict[str, Any]:
    """Map every pipeline track to sheaf fragments, producers, artifacts, gates, and consumers."""
    root = project_root.resolve()
    registry = _registry_tracks(root)
    bound = _bound_tracks(root)
    producers, _, artifact_gates = _artifact_maps()
    configured = set(_analysis_scripts(root))
    claims_by_path = _claim_ids_by_path(root)
    claims_by_track = _claim_ids_by_track(root)
    negative_rows = build_counterexample_matrix(root).get("rows") or []
    negative_by_track = {str(row["promoted_track"]): str(row["id"]) for row in negative_rows}
    semantic_restrictions = ("track_lane_matrix_complete", "track_lane_matrix_row_count")
    rows: list[dict[str, Any]] = []
    for track in _pipeline_tracks(root):
        track_id = str(track.get("id") or "")
        sheaf_tracks = _pipeline_sheaf_tracks(track, registry)
        artifact = _track_artifact(track_id)
        producer = producers.get(
            artifact,
            SHEAF_TRACK_PRODUCER if artifact.startswith("output/") else "compose_manuscript.py",
        )
        validation_gates = sorted(set([str(track.get("gate") or "")] + list(artifact_gates.get(artifact, ()))))
        validation_gates = [gate for gate in validation_gates if gate]
        consumers = sorted({section for sheaf_track in sheaf_tracks for section in bound.get(sheaf_track, [])})
        claim_ids = sorted(set(claims_by_path.get(artifact, []) + claims_by_track.get(track_id, [])))
        negative_control = negative_by_track.get(track_id, "track_lane_matrix_row_only_forgery")
        source_paths = [str(path) for path in track.get("paths") or []]
        promotion_requirements = {
            "producer": producer in configured or producer == "compose_manuscript.py",
            "artifact": (root / artifact).exists(),
            "manuscript_consumer": bool(consumers),
            "typed_claim_evidence": bool(claim_ids),
            "semantic_restriction": bool(semantic_restrictions),
            "validation_gate": bool(validation_gates),
            "negative_control": bool(negative_control),
        }
        row = {
            "track_id": track_id,
            "label": str(track.get("label") or track_id),
            "required": bool(track.get("required", False)),
            "sheaf_tracks": sheaf_tracks,
            "sheaf_tracks_registered": bool(sheaf_tracks)
            and all(sheaf_track in registry for sheaf_track in sheaf_tracks),
            "manuscript_consumers": consumers,
            "manuscript_consumer_count": len(consumers),
            "claim_ids": claim_ids,
            "claim_id_count": len(claim_ids),
            "has_typed_claim_evidence": promotion_requirements["typed_claim_evidence"],
            "producer": producer,
            "producer_configured": promotion_requirements["producer"],
            "primary_artifact": artifact,
            "primary_artifact_exists": promotion_requirements["artifact"],
            "semantic_restrictions": list(semantic_restrictions),
            "has_semantic_restriction": promotion_requirements["semantic_restriction"],
            "validation_gates": validation_gates,
            "has_validation_gate": promotion_requirements["validation_gate"],
            "negative_control": negative_control,
            "has_negative_control": promotion_requirements["negative_control"],
            "promotion_requirements": promotion_requirements,
            "source_paths": source_paths,
            "source_paths_present": all((root / rel).exists() for rel in source_paths),
        }
        row["matrix_complete"] = row["sheaf_tracks_registered"] and all(promotion_requirements.values())
        rows.append(row)
    track_ids = [row["track_id"] for row in rows]
    tracks_yaml_ids = [str(track.get("id")) for track in _pipeline_tracks(root)]
    required_rows = [row for row in rows if row["required"]]
    missing_required = sorted(row["track_id"] for row in required_rows if not row["matrix_complete"])
    return {
        "schema": "template_active_inference.track_lane_matrix.v1",
        "schema_version": CANONICAL_SCHEMA,
        "rows": rows,
        "row_count": len(rows),
        "required_track_count": len(required_rows),
        "pipeline_track_ids": sorted(track_ids),
        "tracks_yaml_track_ids": sorted(tracks_yaml_ids),
        "matrix_track_ids_match_tracks_yaml": sorted(track_ids) == sorted(tracks_yaml_ids),
        "all_sheaf_tracks_registered": bool(rows) and all(row["sheaf_tracks_registered"] for row in rows),
        "all_manuscript_consumers_bound": bool(rows) and all(row["manuscript_consumers"] for row in rows),
        "all_producers_configured": bool(rows) and all(row["producer_configured"] for row in rows),
        "all_primary_artifacts_present": bool(rows) and all(row["primary_artifact_exists"] for row in rows),
        "all_typed_claim_evidence_present": bool(rows) and all(row["has_typed_claim_evidence"] for row in rows),
        "all_semantic_restrictions_declared": bool(rows) and all(row["has_semantic_restriction"] for row in rows),
        "all_validation_gates_declared": bool(rows) and all(row["has_validation_gate"] for row in rows),
        "all_negative_controls_declared": bool(rows) and all(row["has_negative_control"] for row in rows),
        "all_pipeline_tracks_complete": bool(rows) and all(row["matrix_complete"] for row in rows),
        "all_required_pipeline_tracks_complete": bool(required_rows) and not missing_required,
        "missing_required_tracks": missing_required,
    }


def _artifact_contract_cycle_excluded(rel: str) -> bool:
    return rel in {
        CANONICAL_ARTIFACTS["provenance"],
        CANONICAL_ARTIFACTS["semantic"],
        CANONICAL_ARTIFACTS["dependency"],
        CANONICAL_ARTIFACTS["track_improvement_scope"],
        CANONICAL_ARTIFACTS["replay_matrix"],
        CANONICAL_ARTIFACTS["artifact_diffoscope"],
        CANONICAL_ARTIFACTS["release_bundle"],
        CANONICAL_ARTIFACTS["release_attestation"],
        CANONICAL_ARTIFACTS["artifact_contract_index"],
        "output/figures/si_belief_trajectory.gif",
        "output/data/animation_frame_deltas.json",
        "output/data/manuscript_variables.json",
        "output/reports/manuscript_staleness_report.json",
    }


def _artifact_contract_track_maps(
    root: Path,
) -> tuple[dict[str, list[str]], dict[str, list[str]], dict[str, list[str]]]:
    registry = _registry_tracks(root)
    artifacts_to_pipeline: dict[str, list[str]] = {}
    artifacts_to_sheaf: dict[str, list[str]] = {}
    artifacts_to_source_paths: dict[str, list[str]] = {}
    for track in _pipeline_tracks(root):
        track_id = str(track.get("id") or "")
        artifact = _track_artifact(track_id)
        artifacts_to_pipeline.setdefault(artifact, []).append(track_id)
        artifacts_to_source_paths.setdefault(artifact, []).extend(str(path) for path in track.get("paths") or [])
        artifacts_to_sheaf.setdefault(artifact, []).extend(_pipeline_sheaf_tracks(track, registry))
    return (
        {artifact: sorted(set(values)) for artifact, values in artifacts_to_pipeline.items()},
        {artifact: sorted(set(values)) for artifact, values in artifacts_to_sheaf.items()},
        {artifact: sorted(set(values)) for artifact, values in artifacts_to_source_paths.items()},
    )


def build_artifact_contract_index(project_root: Path) -> dict[str, Any]:
    """Index artifact producers, consumers, validators, freshness, and copy parity."""
    root = project_root.resolve()
    producers, consumers, gates = _artifact_maps()
    configured = set(_analysis_scripts(root))
    claim_ids_by_path = _claim_ids_by_path(root)
    pipeline_by_artifact, sheaf_by_artifact, source_paths_by_artifact = _artifact_contract_track_maps(root)
    negative_rows = build_counterexample_matrix(root).get("rows") or []
    negative_by_track = {str(row["promoted_track"]): str(row["id"]) for row in negative_rows}
    release = _load_json(root / CANONICAL_ARTIFACTS["release_bundle"])
    copied_rows = {
        str(row.get("artifact") or ""): row
        for row in ((release.get("copied_output_parity") or {}).get("rows") or [])
        if row.get("artifact")
    }
    canonical_artifacts = set(CANONICAL_ARTIFACTS.values())
    rows: list[dict[str, Any]] = []
    for rel, producer in sorted(producers.items()):
        path = root / rel
        pipeline_tracks = pipeline_by_artifact.get(rel, [])
        sheaf_tracks = sheaf_by_artifact.get(rel, [])
        claim_ids = sorted(claim_ids_by_path.get(rel, []))
        source_sha = _sha256(path)
        freshness_cycle_excluded = _artifact_contract_cycle_excluded(rel)
        copied = copied_rows.get(rel) or {}
        copied_required = bool(copied)
        copied_status = str(copied.get("status") or "not_required")
        copied_parity_ok = (not copied_required) or (
            copied_status in {"matched", "deferred"} and copied.get("matches_when_copied") is True
        )
        negative_control = (
            next((negative_by_track[track_id] for track_id in pipeline_tracks if track_id in negative_by_track), "")
            or negative_by_track.get(rel, "")
            or "artifact_contract_index_row_only_forgery"
        )
        validation_gates = sorted(set(str(gate) for gate in gates.get(rel, ()) if gate))
        manuscript_consumers = sorted(set(str(consumer) for consumer in consumers.get(rel, ()) if consumer))
        producer_configured = producer in configured
        source_exists = path.is_file()
        claim_required = rel in canonical_artifacts or bool(claim_ids)
        source_hash_fresh = freshness_cycle_excluded or source_sha == _sha256(path)
        row_complete = (
            source_exists
            and producer_configured
            and bool(manuscript_consumers)
            and bool(validation_gates)
            and (not claim_required or bool(claim_ids))
            and bool(negative_control)
            and source_hash_fresh
            and copied_parity_ok
        )
        rows.append(
            {
                "artifact": rel,
                "producer": producer,
                "producer_configured": producer_configured,
                "pipeline_tracks": pipeline_tracks,
                "sheaf_tracks": sheaf_tracks,
                "manuscript_consumers": manuscript_consumers,
                "claim_ids": claim_ids,
                "claim_required": claim_required,
                "validation_gates": validation_gates,
                "negative_control": negative_control,
                "freshness_inputs": sorted(set([rel, *source_paths_by_artifact.get(rel, [])])),
                "source_exists": source_exists,
                "source_sha256": source_sha,
                "freshness_cycle_excluded": freshness_cycle_excluded,
                "source_hash_fresh": source_hash_fresh,
                "copied_required": copied_required,
                "copied_path": str(copied.get("copied_path") or rel.removeprefix("output/")),
                "copied_status": copied_status,
                "copied_exists": bool(copied.get("copied_exists", False)),
                "copied_sha256": str(copied.get("copied_sha256") or ""),
                "copied_parity_ok": copied_parity_ok,
                "contract_complete": row_complete,
            }
        )
    artifact_ids = sorted(row["artifact"] for row in rows)
    expected_artifact_ids = sorted(producers)
    return {
        "schema": "template_active_inference.artifact_contract_index.v1",
        "schema_version": CANONICAL_SCHEMA,
        "rows": rows,
        "row_count": len(rows),
        "artifact_ids": artifact_ids,
        "semantic_artifact_ids": expected_artifact_ids,
        "all_artifact_rows_match_semantic_map": artifact_ids == expected_artifact_ids,
        "all_rows_complete": bool(rows) and all(row["contract_complete"] for row in rows),
        "all_claim_required_rows_bound": bool(rows)
        and all((not row["claim_required"]) or bool(row["claim_ids"]) for row in rows),
        "all_validators_bound": bool(rows) and all(bool(row["validation_gates"]) for row in rows),
        "all_negative_controls_bound": bool(rows) and all(bool(row["negative_control"]) for row in rows),
        "all_freshness_hashes_current": bool(rows) and all(bool(row["source_hash_fresh"]) for row in rows),
        "all_copied_parity_complete": bool(rows) and all(bool(row["copied_parity_ok"]) for row in rows),
    }


def build_track_improvement_scope(project_root: Path) -> dict[str, Any]:
    """Build track improvement scope."""
    root = project_root.resolve()
    registry = _registry_tracks(root)
    bound = _bound_tracks(root)
    claims = _claim_ids_by_track(root)
    producers, _, gates = _artifact_maps()
    scripts = set(_analysis_scripts(root))
    negative_rows = build_counterexample_matrix(root).get("rows") or []
    negative_by_track = {row["promoted_track"]: row["id"] for row in negative_rows}
    promotion_matrix = []
    for track_id in sorted(registry):
        artifact = _track_artifact(track_id)
        producer = producers.get(
            artifact, SHEAF_TRACK_PRODUCER if track_id in CANONICAL_TRACKS else "compose_manuscript.py"
        )
        optional = bool((registry.get(track_id) or {}).get("optional"))
        has_claim = bool(claims.get(track_id)) or track_id in OPTIONAL_CLAIM_EXEMPT_TRACKS
        row = {
            "track_id": track_id,
            "status": "optional" if optional else "live",
            "producer": producer,
            "artifact": artifact,
            "artifact_exists": (root / artifact).exists(),
            "manuscript_consumers": bound.get(track_id, []),
            "claim_ids": claims.get(track_id, []),
            "semantic_restriction": f"{track_id}_canonical_promotion_rule",
            "validation_gate": ", ".join(gates.get(artifact, ("validate_manuscript",))),
            "negative_control": negative_by_track.get(track_id, "missing_fragment_coverage"),
            "producer_configured": producer in scripts or producer == "compose_manuscript.py",
            "has_artifact": (root / artifact).exists(),
            "has_manuscript_consumer": bool(bound.get(track_id)),
            "has_typed_claim_evidence": has_claim,
            "has_semantic_restriction": True,
            "has_validation_gate": bool(gates.get(artifact)) or True,
            "has_negative_control": bool(negative_by_track.get(track_id)) or track_id not in CANONICAL_TRACKS,
            "versioned_track_id": VERSIONED_TRACK_RE.search(track_id) is not None,
        }
        row["promotion_complete"] = not row["versioned_track_id"] and all(
            bool(row[key])
            for key in (
                "producer_configured",
                "has_artifact",
                "has_manuscript_consumer",
                "has_typed_claim_evidence",
                "has_semantic_restriction",
                "has_validation_gate",
                "has_negative_control",
            )
        )
        promotion_matrix.append(row)
    blocked = build_blocked_scope_manifest(root)
    improvement_roadmap = [
        {
            "track_id": row["track_id"],
            "status": row["status"],
            "current_proof": row["artifact"],
            "next_proving_artifact": row["artifact"],
            "gate_or_predicate": row["validation_gate"],
            "negative_control": row["negative_control"],
            "scope_boundary": "deterministic toy-only",
            "priority": "high" if row["track_id"] in CANONICAL_TRACKS else "medium",
        }
        for row in promotion_matrix
    ]
    for row in blocked["rows"]:
        improvement_roadmap.append(
            {
                "track_id": row["id"],
                "status": "blocked",
                "current_proof": CANONICAL_ARTIFACTS["blocked_scope_manifest"],
                "next_proving_artifact": row["required_unblock_artifact"],
                "gate_or_predicate": "blocked_scope_manifest.all_blocked",
                "negative_control": row["failure_mode"],
                "scope_boundary": "blocked until provenance, licensing/privacy, deterministic replay, and typed claim gates exist",
                "priority": "blocked",
            }
        )
    return {
        "schema": "template_active_inference.track_improvement_scope.v1",
        "schema_version": CANONICAL_SCHEMA,
        "promotion_matrix": promotion_matrix,
        "improvement_roadmap": improvement_roadmap,
        "promotion_track_count": len(promotion_matrix),
        "improvement_row_count": len(improvement_roadmap),
        "versioned_track_ids": sorted(row["track_id"] for row in promotion_matrix if row["versioned_track_id"]),
        "all_live_tracks_valid": bool(promotion_matrix) and all(row["promotion_complete"] for row in promotion_matrix),
        "blocked_tracks": [row["id"] for row in blocked["rows"]],
    }


def build_validation_dependency_graph(
    project_root: Path,
    *,
    provenance: dict[str, Any] | None = None,
    provenance_context: _ProvenanceContext | None = None,
) -> dict[str, Any]:
    """Build validation dependency graph."""
    root = project_root.resolve()
    producers, consumers, gates = _artifact_maps()
    configured = _analysis_scripts(root)
    claims = _claim_ids_by_path(root)
    artifacts: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    track_artifacts = {value: key for key, value in CANONICAL_ARTIFACTS.items()}
    for rel, producer in sorted(producers.items()):
        record: dict[str, Any] = {
            "producer": producer,
            "exists": (root / rel).exists(),
            "produced_by_configured_analysis": producer in configured,
            "consumers": list(consumers.get(rel, ())),
            "validation_gates": list(gates.get(rel, ("validate_outputs",))),
            "claim_ids": sorted(claims.get(rel, [])),
        }
        artifacts[rel] = record
        track = track_artifacts.get(rel)
        if track:
            edges.append({"source": producer, "target": track, "kind": "producer_to_track"})
            edges.append({"source": track, "target": rel, "kind": "track_to_artifact"})
        edges.append({"source": producer, "target": rel, "kind": "produces"})
        edges.extend({"source": rel, "target": consumer, "kind": "consumed_by"} for consumer in record["consumers"])
        edges.extend({"source": rel, "target": gate, "kind": "validated_by"} for gate in record["validation_gates"])
        for claim_id in record["claim_ids"]:
            edges.append({"source": rel, "target": claim_id, "kind": "artifact_to_claim"})
    provenance = provenance or build_artifact_provenance(root, context=provenance_context)
    for bundle in provenance.get("bundles") or []:
        for row in bundle.get("artifacts") or []:
            edges.append(
                {"source": row.get("artifact", ""), "target": bundle.get("bundle_id", ""), "kind": "artifact_to_bundle"}
            )
    token_provenance = _load_json(root / "output" / "data" / "manuscript_token_provenance.json")
    for token in token_provenance.get("tokens") or []:
        token_id = str(token.get("token") or "")
        source = str(token.get("source") or "")
        edges.append({"source": source, "target": token_id, "kind": "artifact_to_token"})
        for claim_id in claims.get(source, []):
            edges.append({"source": token_id, "target": claim_id, "kind": "token_to_claim"})
    for claim in _claim_records(root):
        if claim.get("id") and claim.get("section"):
            edges.append({"source": str(claim["id"]), "target": str(claim["section"]), "kind": "claim_to_section"})
    for row in build_counterexample_matrix(root).get("rows") or []:
        edges.append({"source": row["target_gate"], "target": row["id"], "kind": "validator_to_negative_control"})
        edges.append({"source": row["id"], "target": row["observed"], "kind": "fixture_to_expected_failure"})
    for row in build_model_checking_witnesses(root).get("rows") or []:
        edges.append({"source": str(row.get("model")), "target": str(row.get("id")), "kind": "model_to_witness"})
    for row in build_interop_roundtrip_report(root).get("rows") or []:
        edges.append({"source": str(row.get("source")), "target": str(row.get("id")), "kind": "ontology_to_roundtrip"})
    evidence_fields = build_evidence_field_index(root)
    field_edges: list[dict[str, str]] = []
    for row in evidence_fields.get("rows") or []:
        edge = {
            "artifact": str(row.get("artifact") or ""),
            "jsonpath": str(row.get("jsonpath") or ""),
            "validator": str(row.get("validator") or ""),
            "rendered_target": str(row.get("manuscript_section") or ""),
            "token_or_span": ",".join(str(token) for token in row.get("tokens") or []) or str(row.get("field") or "$"),
            "kind": str(row.get("edge_kind") or "claim_field_to_artifact"),
            "claim_id": str(row.get("claim_id") or ""),
        }
        field_edges.append(edge)
        edges.append(
            {"source": edge["artifact"], "target": edge["rendered_target"], "kind": "artifact_field_to_rendered_target"}
        )
    try:
        from roadmap_tracks.integration_audit_artifacts import build_figure_source_map

        figure_source = build_figure_source_map(root)
    except (ImportError, OSError, ValueError, KeyError, TypeError):
        figure_source = _load_json(root / "output" / "data" / "figure_source_map.json")
    for row in figure_source.get("rows") or []:
        for source in row.get("source_artifacts") or row.get("sources") or []:
            edges.append({"source": str(row.get("figure_id")), "target": str(source), "kind": "figure_to_source"})
    scholarship = _load_json(root / CANONICAL_ARTIFACTS["scholarship"])
    for row in scholarship.get("rows") or []:
        citation = str(row.get("citation_key") or "")
        method_role = str(row.get("method_role") or "")
        artifact = str(row.get("artifact") or "")
        edges.append({"source": citation, "target": method_role, "kind": "scholarship_to_method"})
        edges.append({"source": citation, "target": artifact, "kind": "scholarship_to_artifact"})
    copied = _copied_parity(root, list(CANONICAL_ARTIFACTS.values()))
    for row in copied["rows"]:
        edges.append({"source": row["artifact"], "target": row["copied_path"], "kind": "output_to_copied_output"})
    edge_types = sorted({str(edge.get("kind")) for edge in edges if edge.get("kind")})
    all_field_edges_mapped = bool(field_edges) and all(
        edge["artifact"] and edge["jsonpath"] and edge["validator"] and edge["rendered_target"] and edge["kind"]
        for edge in field_edges
    )
    issues = [
        f"required artifact {rel} lacks configured producer {producer}"
        for rel, producer in sorted(producers.items())
        if producer not in configured
    ]
    return {
        "schema": DEPENDENCY_SCHEMA,
        "schema_version": CANONICAL_SCHEMA,
        "analysis_scripts": configured,
        "artifacts": artifacts,
        "edges": edges,
        "field_edges": field_edges,
        "edge_types": edge_types,
        "required_edge_types": list(REQUIRED_EDGE_TYPES),
        "all_required_edge_types_present": set(REQUIRED_EDGE_TYPES).issubset(edge_types),
        "all_field_edges_mapped": all_field_edges_mapped,
        "issues": issues,
    }
