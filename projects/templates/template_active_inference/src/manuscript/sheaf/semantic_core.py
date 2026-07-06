"""Core semantic gluing builders, validators, and issue aggregation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from manuscript.variables import generate_variables
from ontology.bindings import (
    BERNOULLI_EXPECTED_TERMS,
    BERNOULLI_SYMBOL_MAP,
    SI_EXPECTED_TERMS,
    SI_SYMBOL_MAP,
    validate_all_gnn_ontology,
)

from manuscript.sheaf.coverage import gray_cell_count, load_sheaf_coverage_context
from manuscript.sheaf.semantic_maps import (
    ARTIFACT_GATES,
    ARTIFACT_PRODUCERS,
    SEMANTIC_RESTRICTION_LANES,
    SEMANTIC_SCHEMA,
)
from manuscript.sheaf.semantic_restrictions import (
    _animation_frame_count,
    _configured_analysis_scripts,
    _expected_symbol_gaps,
    _gnn_symbols,
    _graph_world_restrictions,
    _lean_status,
    _load_json,
    _policy_comparison_restrictions,
    _policy_posterior_restrictions,
    _proof_obligation_rows,
    _pymdp_hash_restrictions,
    _restriction_lane_assignments,
    _restriction_lane_summaries,
    _runtime_diagnostics_restrictions,
    _section_ontology_symbols,
)


def semantic_gluing_issues(project_root: Path) -> list[str]:
    """Return semantic cross-track disagreements not covered by structural laws."""
    root = project_root.resolve()
    issues: list[str] = []

    ctx = load_sheaf_coverage_context(root)
    missing = gray_cell_count(ctx.matrix)
    if missing:
        issues.append(f"coverage matrix has {missing} missing bound fragment(s)")

    issues.extend(validate_all_gnn_ontology(root))
    issues.extend(
        _expected_symbol_gaps(
            label="bernoulli_toy",
            gnn_symbols=_gnn_symbols(root, "gnn/bernoulli_toy.gnn.md"),
            section_symbols=_section_ontology_symbols(
                root,
                "manuscript/sections/imrad/methods_analytical/ontology.yaml",
            ),
            symbol_map=BERNOULLI_SYMBOL_MAP,
            expected_terms=BERNOULLI_EXPECTED_TERMS,
        )
    )
    issues.extend(
        _expected_symbol_gaps(
            label="si_tmaze",
            gnn_symbols=_gnn_symbols(root, "gnn/si_tmaze.gnn.md"),
            section_symbols=_section_ontology_symbols(
                root,
                "manuscript/sections/imrad/methods_pymdp/ontology.yaml",
            ),
            symbol_map=SI_SYMBOL_MAP,
            expected_terms=SI_EXPECTED_TERMS,
        )
    )

    variables_path = root / "output" / "data" / "manuscript_variables.json"
    if variables_path.is_file():
        saved = _load_json(variables_path)
        live = generate_variables(root, require_analysis_outputs=False)
        for key in ("sheaf_track_count", "pipeline_track_count", "imrad_manifest_rows"):
            if saved.get(key) != live.get(key):
                issues.append(f"manuscript variable {key!r} is stale: saved={saved.get(key)!r}, live={live.get(key)!r}")

    summary = _load_json(root / "output" / "data" / "si_tmaze_summary.json")
    stats = _load_json(root / "output" / "data" / "analysis_statistics.json")
    if summary and stats:
        if summary.get("mode") != stats.get("pymdp_mode"):
            issues.append(f"pymdp mode mismatch: summary={summary.get('mode')!r}, stats={stats.get('pymdp_mode')!r}")
        if summary.get("config_hash") != stats.get("pymdp_config_hash"):
            issues.append(
                f"pymdp config hash mismatch: summary={summary.get('config_hash')!r}, "
                f"stats={stats.get('pymdp_config_hash')!r}"
            )

    policy = _policy_comparison_restrictions(root)
    if set(policy["modes"]) != {"policy_inference", "state_inference"}:
        issues.append(f"policy comparison mode set invalid: {policy['modes']!r}")
    if policy["run_count"] < 4:
        issues.append(f"policy comparison run count too small: {policy['run_count']!r}")
    if not policy["complete_grid"]:
        issues.append("policy comparison grid is incomplete")
    if not policy["all_efe_rows_explained"]:
        issues.append("policy comparison EFE rows are not explained")

    posterior = _policy_posterior_restrictions(root)
    if posterior["row_count"] < 1:
        issues.append("pymdp policy posterior grid has no rows")
    if not posterior["all_available_posteriors_normalized"]:
        issues.append("pymdp policy posterior grid has unnormalized posterior rows")
    if not posterior["all_unavailable_rows_explained"]:
        issues.append("pymdp policy posterior grid has unexplained unavailable rows")

    runtime = _runtime_diagnostics_restrictions(root)
    if not runtime["ok"]:
        issues.append("pymdp runtime diagnostics are not ok")
    if runtime["unexpected_warning_count"] != 0:
        issues.append("pymdp runtime diagnostics captured unexpected warnings")

    graph_world = _graph_world_restrictions(root)
    if not graph_world["steps_match"]:
        issues.append(
            "graph-world summary/trace mismatch: "
            f"summary steps={graph_world['steps']!r}, trace steps={graph_world['trace_steps']!r}"
        )
    if not graph_world["goal_reached"]:
        issues.append("graph-world summary does not record goal_reached=true")

    frame_count = _animation_frame_count(root)
    if frame_count < 2:
        issues.append(f"animation frame count too small: {frame_count}")
    from visualizations.animation import validate_animation_frame_deltas

    issues.extend(validate_animation_frame_deltas(root))

    lean = _lean_status(root)
    if not lean["all_proved"]:
        issues.append("Lean boundary is not fully proved")

    issues.extend(validate_configured_artifact_producers(root))

    from validation_spine import validate_validation_spine

    issues.extend(validate_validation_spine(root))

    from roadmap_tracks import (
        validate_formal_interop_artifacts,
        validate_integration_audit_artifacts,
        validate_sheaf_track_artifacts,
        validate_toy_sweep_artifacts,
    )

    issues.extend(validate_toy_sweep_artifacts(root))
    issues.extend(validate_formal_interop_artifacts(root))
    issues.extend(validate_integration_audit_artifacts(root))
    issues.extend(validate_sheaf_track_artifacts(root, validate_saved_certificate=False))

    from gates.claim_ledger import validate_typed_claim_evidence

    if not validate_typed_claim_evidence(root, allow_missing_certificate=True):
        issues.append("typed claim evidence failed")

    return issues


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
    import yaml

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


def build_semantic_gluing_certificate(project_root: Path) -> dict[str, Any]:
    """Build a JSON-serializable semantic certificate from live project state."""
    root = project_root.resolve()
    ctx = load_sheaf_coverage_context(root)
    issues = semantic_gluing_issues(root)
    variables = generate_variables(root, require_analysis_outputs=False)
    dependency_graph = build_validation_dependency_graph(root)
    policy = _policy_comparison_restrictions(root)
    posterior = _policy_posterior_restrictions(root)
    runtime = _runtime_diagnostics_restrictions(root)
    graph_world = _graph_world_restrictions(root)
    pymdp_hash = _pymdp_hash_restrictions(root)
    lean = _lean_status(root)
    payloads = _semantic_payloads(root)
    sensitivity = payloads["sensitivity"]
    uncertainty = payloads["uncertainty"]
    benchmark = payloads["benchmark"]
    model_checking = payloads["model_checking"]
    interop = payloads["interop"]
    adversarial = payloads["adversarial"]
    stale = payloads["stale"]
    manuscript_staleness = payloads["manuscript_staleness"]
    tokens = payloads["tokens"]
    figures = payloads["figures"]
    scope = payloads["scope"]
    provenance = payloads["provenance"]
    assumptions = payloads["assumptions"]
    animation_deltas = payloads["animation_deltas"]
    release_bundle = payloads["release_bundle"]
    evidence_fields = payloads["evidence_fields"]
    theorem_traceability = payloads["theorem_traceability"]
    gate_index = payloads["gate_index"]
    section_status = payloads["section_status"]
    render_log = payloads["render_log"]
    track_lane = payloads["track_lane"]
    track_scope = payloads["track_scope"]
    blocked_scope = payloads["blocked_scope"]
    replay_matrix = payloads["replay_matrix"]
    proof_dependency = payloads["proof_dependency"]
    transition_table = payloads["transition_table"]
    ablation_sensitivity = payloads["ablation_sensitivity"]
    release_attestation = payloads["release_attestation"]
    security_posture = payloads["security_posture"]
    canonical_restrictions = _canonical_restriction_snapshot(root)
    from validation_spine import validate_validation_spine

    proof_obligations = _proof_obligation_rows(canonical_restrictions)
    restrictions = {
        "coverage_missing": gray_cell_count(ctx.matrix),
        "section_count": len(ctx.manifest.sections),
        "track_count": len(ctx.registry.tracks),
        "claim_count": len(_claim_records(root)),
        "policy_comparison_run_count": policy["run_count"],
        "policy_comparison_modes": policy["modes"],
        "policy_comparison_horizons": policy["horizons"],
        "policy_comparison_goal_reached_count": policy["goal_reached_count"],
        "policy_comparison_complete_grid": policy["complete_grid"],
        "policy_comparison_efe_rows_explained": policy["all_efe_rows_explained"],
        "policy_posterior_row_count": posterior["row_count"],
        "policy_posterior_available_row_count": posterior["available_row_count"],
        "policy_posterior_normalized": posterior["all_available_posteriors_normalized"],
        "pymdp_runtime_ok": runtime["ok"],
        "pymdp_runtime_phase_rows_ok": runtime["phase_rows_ok"],
        "pymdp_runtime_known_warning_count": runtime["known_warning_count"],
        "pymdp_runtime_unexpected_warning_count": runtime["unexpected_warning_count"],
        "graph_world_steps_match": graph_world["steps_match"],
        "graph_world_goal_reached": graph_world["goal_reached"],
        "animation_frame_count": _animation_frame_count(root),
        "animation_deltas_all_nonzero": animation_deltas.get("all_nonzero") is True,
        "animation_delta_count": int(animation_deltas.get("delta_count", 0) or 0),
        "pymdp_mode_match": pymdp_hash["mode_match"],
        "pymdp_config_hash_match": pymdp_hash["config_hash_match"],
        "artifact_provenance_seed_config_complete": provenance.get("all_seeded") is True
        and provenance.get("all_config_digests") is True,
        "lean_all_proved": lean["all_proved"],
        "lean_proved_count": lean["proved_count"],
        "gnn_ontology_ok": not validate_all_gnn_ontology(root),
        "configured_artifact_producers_ok": not dependency_graph["issues"],
        "validation_spine_ok": not validate_validation_spine(root),
        "sensitivity_complete_grid": sensitivity.get("complete_grid") is True,
        "analytical_assumptions_indexed": assumptions.get("all_equations_indexed") is True,
        "analytical_assumption_count": int(assumptions.get("row_count", 0) or 0),
        "sensitivity_cell_count": int(sensitivity.get("row_count", 0) or 0),
        "uncertainty_all_normalized": uncertainty.get("all_normalized") is True,
        "uncertainty_row_count": int(uncertainty.get("row_count", 0) or 0),
        "benchmark_all_models_complete": benchmark.get("all_models_complete") is True,
        "benchmark_model_count": len(benchmark.get("models") or []),
        "model_checking_all_passed": model_checking.get("all_passed") is True,
        "model_checking_witness_count": int(model_checking.get("witness_count", 0) or 0),
        "interop_all_lossless": interop.get("all_lossless") is True,
        "interop_check_count": int(interop.get("check_count", 0) or 0),
        "adversarial_expected_failures_documented": adversarial.get("all_expected_failures_documented") is True,
        "adversarial_known_bad_passed": int(adversarial.get("known_bad_rows_passed", 0) or 0),
        "dependency_edge_types_ok": dependency_graph.get("all_required_edge_types_present") is True,
        "dependency_edge_type_count": len(dependency_graph.get("edge_types") or []),
        "stale_artifacts_all_fresh": stale.get("all_fresh") is True,
        "manuscript_staleness_all_fresh": manuscript_staleness.get("all_fresh") is True,
        "manuscript_staleness_row_count": int(manuscript_staleness.get("row_count", 0) or 0),
        "token_provenance_complete": tokens.get("all_tokens_mapped") is True,
        "figure_source_coverage": figures.get("all_figures_mapped") is True,
        "scope_boundary_toy_only": scope.get("all_current_claims_toy") is True,
        "provenance_bundle_complete": provenance.get("all_bundles_complete") is True,
        "provenance_bundle_count": int(provenance.get("bundle_count", 0) or 0),
        "replay_matrix_all_matched": replay_matrix.get("all_replay_rows_matched") is True,
        "replay_matrix_row_count": int(replay_matrix.get("row_count", replay_matrix.get("check_count", 0)) or 0),
        "track_improvement_scope_complete": track_scope.get("all_live_tracks_valid") is True,
        "track_improvement_row_count": int(track_scope.get("improvement_row_count", 0) or 0),
        "blocked_empirical_adapter": blocked_scope.get("all_blocked") is True,
        "evidence_fields_mapped": evidence_fields.get("all_fields_mapped") is True,
        "evidence_field_count": int(evidence_fields.get("field_count", 0) or 0),
        "release_bundle_sources_present": release_bundle.get("all_required_sources_present") is True,
        "release_bundle_artifact_count": int(release_bundle.get("artifact_count", 0) or 0),
        "theorem_traceability_linked": theorem_traceability.get("all_theorems_linked") is True,
        "theorem_traceability_row_count": int(theorem_traceability.get("row_count", 0) or 0),
        "gate_ergonomics_indexed": gate_index.get("all_indexed") is True,
        "validation_gate_index_count": int(gate_index.get("gate_count", 0) or 0),
        "section_status_all_bound_present": section_status.get("all_bound_fragments_present") is True,
        "section_status_all_sections_have_status": section_status.get("all_sections_have_status") is True,
        "section_status_all_tracks_have_status": section_status.get("all_tracks_have_status") is True,
        "section_status_cell_count": int(section_status.get("cell_count", 0) or 0),
        "section_status_fully_sheafed_count": int(section_status.get("fully_sheafed_section_count", 0) or 0),
        "sheaf_render_log_all_events_ok": render_log.get("all_events_ok") is True,
        "sheaf_render_log_event_count": int(render_log.get("event_count", 0) or 0),
        "track_lane_matrix_complete": track_lane.get("all_pipeline_tracks_complete") is True,
        "track_lane_matrix_row_count": int(track_lane.get("row_count", 0) or 0),
        "proof_dependency_graph_resolved": proof_dependency.get("all_theorems_have_dependencies") is True
        and proof_dependency.get("all_edges_resolved") is True,
        "proof_dependency_edge_count": int(proof_dependency.get("edge_count", 0) or 0),
        "state_transition_table_complete": transition_table.get("all_transitions_deterministic") is True
        and transition_table.get("all_reachable_states_covered") is True,
        "state_transition_row_count": int(transition_table.get("row_count", 0) or 0),
        "ablation_sensitivity_source_backed": ablation_sensitivity.get("all_effects_source_backed") is True,
        "ablation_sensitivity_row_count": int(ablation_sensitivity.get("row_count", 0) or 0),
        "release_attestation_complete": release_attestation.get("all_attested") is True,
        "release_attestation_row_count": int(release_attestation.get("row_count", 0) or 0),
        "security_posture_controls_ok": security_posture.get("all_controls_ok") is True,
        "security_posture_control_count": int(security_posture.get("control_count", 0) or 0),
        "security_posture_high_risk_gap_count": int(security_posture.get("high_risk_gap_count", 0) or 0),
        "security_posture_secret_finding_count": int(security_posture.get("secret_finding_count", 0) or 0),
        "security_posture_secret_patterns_absent": security_posture.get("all_secret_patterns_absent") is True,
        "no_versioned_live_tracks": not any(tid.endswith(("_v2", "_v3", "_v4", "_v5")) for tid in ctx.registry.tracks),
        **canonical_restrictions,
    }
    restriction_lanes = _restriction_lane_assignments(restrictions)
    lane_summaries = _restriction_lane_summaries(restrictions, restriction_lanes)
    return {
        "schema": SEMANTIC_SCHEMA,
        "ok": not issues,
        "issues": issues,
        "restriction_classes": sorted({row["class"] for row in proof_obligations}),
        "restriction_lanes": restriction_lanes,
        "lane_summaries": lane_summaries,
        "all_lane_summaries_ok": bool(lane_summaries) and all(row["all_ok"] for row in lane_summaries.values()),
        "proof_obligations": proof_obligations,
        "all_proof_obligations_ok": bool(proof_obligations) and all(row["ok"] for row in proof_obligations),
        "tracks": _semantic_track_rows(ctx),
        "sections": _section_records(root),
        "shared_symbols": _semantic_shared_symbols(root),
        "artifact_sources": _semantic_artifact_sources(root),
        "restrictions": restrictions,
        "artifact_graph": dependency_graph["artifacts"],
        "evidence_crosswalk": build_evidence_crosswalk(root),
        "claims": _claim_records(root),
        "manuscript_variables": variables,
    }


def write_semantic_gluing_certificate(
    project_root: Path,
    *,
    output_path: Path | None = None,
) -> Path:
    root = project_root.resolve()
    path = output_path or root / "output" / "data" / "sheaf_gluing_certificate.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        _refresh_hydrated_manuscript(root)
        from manuscript.sheaf.status import write_sheaf_status_outputs

        write_sheaf_status_outputs(root)
    payload = build_semantic_gluing_certificate(root)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if output_path is None:
        _refresh_hydrated_manuscript(root)
        from manuscript.sheaf.status import write_sheaf_status_outputs

        write_sheaf_status_outputs(root)
        payload = build_semantic_gluing_certificate(root)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _refresh_hydrated_manuscript(root: Path) -> None:
    from manuscript.refresh import ManuscriptRefreshPhase, refresh_manuscript_pipeline

    refresh_manuscript_pipeline(root, require_analysis_outputs=False, phase=ManuscriptRefreshPhase.POST_COMPOSE)


def _refresh_artifact_contract_outputs(root: Path) -> None:
    """Refresh contract artifacts that hash semantic outputs after final writes."""
    from roadmap_tracks.integration_audit import write_integration_audit_artifacts
    from roadmap_tracks.sheaf_tracks import CANONICAL_ARTIFACTS, build_artifact_contract_index, build_replay_matrix

    write_integration_audit_artifacts(root)
    replay_path = root / CANONICAL_ARTIFACTS["replay_matrix"]
    replay_path.parent.mkdir(parents=True, exist_ok=True)
    replay_path.write_text(
        json.dumps(build_replay_matrix(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    contract_path = root / CANONICAL_ARTIFACTS["artifact_contract_index"]
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        json.dumps(build_artifact_contract_index(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _refresh_animation_outputs(root: Path) -> None:
    """Refresh deterministic animation artifacts before semantic validation."""
    from visualizations.animation import write_animation_frame_deltas, write_belief_trajectory_gif

    try:
        write_belief_trajectory_gif(root)
        write_animation_frame_deltas(root)
    except FileNotFoundError:
        return


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
        return semantic_gluing_issues(root) + ["missing output/data/sheaf_gluing_certificate.json"]
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
    issues = semantic_gluing_issues(root)
    issues.extend(saved_issues)
    live = build_semantic_gluing_certificate(root)
    if _stable_certificate_fields(saved) != _stable_certificate_fields(live):
        issues.append("saved sheaf_gluing_certificate.json is stale relative to live semantic fields")
    return issues
