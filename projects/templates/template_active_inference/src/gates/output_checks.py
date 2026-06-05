"""Pipeline output artifact validation."""

from __future__ import annotations

import json
from pathlib import Path

from gates.artifact_manifest import REQUIRED_OUTPUTS

# Matches the tests/test_figures.py::_assert_png lower bound. A 0-byte or blank
# PNG has the empty-file sha (e3b0c4...) yet still satisfies Path.exists(); a
# size floor plus a PIL decode of width/height closes that fail-open hole.
_MIN_FIGURE_BYTES = 5_000


def _figures_nonblank(root: Path) -> bool:
    """Return True only if every required figure PNG is non-trivially sized and decodable."""
    from PIL import Image

    png_rels = [rel for rel in REQUIRED_OUTPUTS if rel.startswith("output/figures/") and rel.endswith(".png")]
    if not png_rels:
        return False
    for rel in png_rels:
        path = root / rel
        if not path.is_file():
            return False
        if path.stat().st_size < _MIN_FIGURE_BYTES:
            return False
        try:
            with Image.open(path) as img:
                width, height = img.size
        except (OSError, ValueError):
            return False
        if width <= 0 or height <= 0:
            return False
    return True


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _pymdp_logging_expected(root: Path) -> bool:
    from simulation.pymdp_config import load_pymdp_config
    from simulation.si_runner import pymdp_available

    if not pymdp_available():
        return False
    cfg = load_pymdp_config(root)
    return bool(cfg.logging.enabled)


def _efe_values_explained(payload: dict) -> bool:
    rows = payload.get("rows") or []
    return bool(rows) and all(
        (row.get("terms_available") and bool((row.get("terms") or {}).get("values")))
        or (not row.get("terms_available") and bool(row.get("fallback_reason")))
        for row in rows
    )


def validate_outputs(project_root: Path) -> dict[str, bool]:
    root = project_root.resolve()
    required = [root / rel for rel in REQUIRED_OUTPUTS]
    checks = {str(p.relative_to(root)): p.exists() for p in required}

    checks["figures_nonblank"] = _figures_nonblank(root)

    summary_path = root / "output" / "data" / "si_tmaze_summary.json"
    trace_path = root / "output" / "data" / "si_tmaze_trace.json"
    si_inv_path = root / "output" / "reports" / "si_invariants.json"
    si_summary_present = summary_path.exists()
    if si_summary_present and not si_inv_path.exists():
        checks["si_invariants_all_pass"] = False
    elif si_inv_path.exists():
        si_inv = json.loads(si_inv_path.read_text(encoding="utf-8"))
        checks["si_invariants_all_pass"] = bool(si_inv.get("all_pass"))

    inv_path = root / "output" / "reports" / "invariants.json"
    if inv_path.exists():
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
        checks["invariants_all_pass"] = bool(inv.get("all_pass"))
        sim = inv.get("simulation") or {}
        if sim:
            checks["simulation_invariants_all_pass"] = all(sim.values())

    if summary_path.exists() and trace_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        steps = int(summary.get("steps", 0))
        trace_steps = trace.get("steps") or []
        checks["si_trace_present"] = len(trace_steps) == steps and steps >= 1
        checks["si_summary_schema"] = (
            steps >= 1
            and float(summary.get("mean_belief_entropy", -1.0)) >= 0.0
            and "mode" in summary
            and "config" in summary
        )

    comparison_path = root / "output" / "data" / "si_policy_comparison.json"
    if comparison_path.exists():
        comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
        runs = comparison.get("runs") or []
        checks["si_policy_comparison_schema"] = (
            bool(runs)
            and {row.get("mode") for row in runs} == {"state_inference", "policy_inference"}
            and all("horizon" in row and "goal_reached" in row for row in runs)
            and (comparison.get("summary") or {}).get("complete_grid") is True
            and (comparison.get("summary") or {}).get("all_efe_rows_explained") is True
        )
    posterior_path = root / "output" / "data" / "pymdp_policy_posterior_grid.json"
    if posterior_path.exists():
        posterior = json.loads(posterior_path.read_text(encoding="utf-8"))
        rows = posterior.get("rows") or []
        checks["pymdp_policy_posterior_grid_schema"] = (
            posterior.get("schema") == "template_active_inference.pymdp_policy_posterior_grid.v1"
            and bool(rows)
            and posterior.get("all_available_posteriors_normalized") is True
            and posterior.get("all_unavailable_rows_explained") is True
            and all(
                (not row.get("posterior_available")) or abs(float(sum(row.get("q_pi") or [])) - 1.0) <= 1e-9
                for row in rows
            )
        )
    runtime_path = root / "output" / "reports" / "pymdp_runtime_diagnostics.json"
    if runtime_path.exists():
        from simulation.pymdp_runtime import validate_runtime_diagnostics

        runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        checks["pymdp_runtime_diagnostics_schema"] = (
            runtime.get("schema") == "template_active_inference.pymdp_runtime_diagnostics.v1"
            and runtime.get("ok") is True
            and int(runtime.get("unexpected_warning_count", 0) or 0) == 0
            and not validate_runtime_diagnostics(root)
        )

    graph_summary_path = root / "output" / "data" / "si_graph_world_summary.json"
    graph_trace_path = root / "output" / "data" / "si_graph_world_trace.json"
    if graph_summary_path.exists() and graph_trace_path.exists():
        graph_summary = json.loads(graph_summary_path.read_text(encoding="utf-8"))
        graph_trace = json.loads(graph_trace_path.read_text(encoding="utf-8"))
        checks["si_graph_world_schema"] = (
            graph_summary.get("status") == "ok"
            and graph_summary.get("goal_reached") is True
            and len(graph_trace.get("steps") or []) == int(graph_summary.get("steps", 0))
            and "not_implemented" not in json.dumps(graph_summary)
        )

    crosswalk_path = root / "output" / "data" / "sheaf_evidence_crosswalk.json"
    dependency_path = root / "output" / "data" / "validation_dependency_graph.json"
    if crosswalk_path.exists():
        crosswalk = json.loads(crosswalk_path.read_text(encoding="utf-8"))
        checks["sheaf_evidence_crosswalk_schema"] = crosswalk.get(
            "schema"
        ) == "template_active_inference.evidence_crosswalk.v1" and int(crosswalk.get("claim_count", 0)) == len(
            crosswalk.get("claims") or []
        )
    if dependency_path.exists():
        dependency = json.loads(dependency_path.read_text(encoding="utf-8"))
        artifacts = dependency.get("artifacts") or {}
        checks["validation_dependency_graph_schema"] = (
            dependency.get("schema") == "template_active_inference.validation_dependency_graph.v1"
            and not dependency.get("issues")
            and bool(artifacts.get("output/data/sheaf_gluing_certificate.json"))
            and bool(artifacts.get("output/figures/si_belief_trajectory.gif"))
        )

    provenance_path = root / "output" / "data" / "artifact_provenance.json"
    replay_path = root / "output" / "reports" / "reproducibility_replay.json"
    counterexample_path = root / "output" / "reports" / "counterexample_matrix.json"
    if provenance_path.exists():
        from validation_spine import validate_artifact_provenance

        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        checks["artifact_provenance_schema"] = (
            provenance.get("schema") == "template_active_inference.artifact_provenance.v1"
            and provenance.get("all_hashed") is True
            and provenance.get("all_seeded") is True
            and provenance.get("all_config_digests") is True
            and provenance.get("all_source_commits") is True
            and provenance.get("all_producers_configured") is True
            and not validate_artifact_provenance(root)
        )
    if replay_path.exists():
        from validation_spine import validate_reproducibility_replay

        replay = json.loads(replay_path.read_text(encoding="utf-8"))
        checks["reproducibility_replay_schema"] = (
            replay.get("schema") == "template_active_inference.reproducibility_replay.v1"
            and replay.get("all_passed") is True
            and not validate_reproducibility_replay(root)
        )
    if counterexample_path.exists():
        from validation_spine import validate_counterexample_matrix

        counterexamples = json.loads(counterexample_path.read_text(encoding="utf-8"))
        checks["counterexample_matrix_schema"] = (
            counterexamples.get("schema") == "template_active_inference.counterexample_matrix.v1"
            and counterexamples.get("all_expected_failures_documented") is True
            and not validate_counterexample_matrix(root)
        )

    from roadmap_tracks import (
        validate_formal_interop_artifacts,
        validate_integration_audit_artifacts,
        validate_sheaf_track_artifacts,
        validate_toy_sweep_artifacts,
    )

    sensitivity = _read_json(root / "output" / "data" / "sensitivity_sweep.json")
    uncertainty = _read_json(root / "output" / "data" / "uncertainty_summary.json")
    benchmark = _read_json(root / "output" / "data" / "toy_benchmark_matrix.json")
    policy_grid = _read_json(root / "output" / "data" / "si_policy_grid.json")
    efe_terms = _read_json(root / "output" / "data" / "si_efe_terms.json")
    topology = _read_json(root / "output" / "data" / "si_graph_world_topology_sweep.json")
    topology_traces = _read_json(root / "output" / "data" / "si_graph_world_topology_traces.json")
    graph_invariants = _read_json(root / "output" / "reports" / "graph_world_invariants.json")
    observable = _read_json(root / "output" / "data" / "analytical_observable_sweep.json")
    model_checking = _read_json(root / "output" / "reports" / "model_checking_witnesses.json")
    interop = _read_json(root / "output" / "data" / "interop_roundtrip_report.json")
    gnn_roundtrip = _read_json(root / "output" / "data" / "gnn_roundtrip_report.json")
    gnn_lint = _read_json(root / "output" / "reports" / "gnn_lint_report.json")
    ontology_alias = _read_json(root / "output" / "data" / "ontology_alias_index.json")
    ontology_profile = _read_json(root / "output" / "data" / "ontology_profile_matrix.json")
    lean_theorems = _read_json(root / "output" / "reports" / "lean_theorem_inventory.json")
    lean_graph = _read_json(root / "output" / "reports" / "lean_graph_world_inventory.json")
    producer_completeness = _read_json(root / "output" / "reports" / "producer_completeness.json")
    stale_report = _read_json(root / "output" / "reports" / "stale_artifact_report.json")
    manuscript_staleness = _read_json(root / "output" / "reports" / "manuscript_staleness_report.json")
    cross_symbols = _read_json(root / "output" / "data" / "cross_track_symbol_table.json")
    evidence_tables = _read_json(root / "output" / "data" / "manuscript_evidence_tables.json")
    token_provenance = _read_json(root / "output" / "data" / "manuscript_token_provenance.json")
    claim_audit = _read_json(root / "output" / "reports" / "claim_evidence_audit.json")
    gate_index = _read_json(root / "output" / "data" / "validation_gate_index.json")
    section_status = _read_json(root / "output" / "data" / "sheaf_section_status_matrix.json")
    render_log = _read_json(root / "output" / "reports" / "sheaf_render_log.json")
    figure_source = _read_json(root / "output" / "data" / "figure_source_map.json")
    figure_hash = _read_json(root / "output" / "reports" / "figure_hash_manifest.json")
    scope = _read_json(root / "output" / "reports" / "scope_boundary_audit.json")
    adversarial = _read_json(root / "output" / "reports" / "adversarial_audit.json")
    assumptions = _read_json(root / "output" / "data" / "analytical_assumption_index.json")
    animation_deltas = _read_json(root / "output" / "data" / "animation_frame_deltas.json")
    replay_matrix = _read_json(root / "output" / "reports" / "replay_matrix.json")
    track_scope = _read_json(root / "output" / "data" / "track_improvement_scope.json")
    blocked_scope = _read_json(root / "output" / "reports" / "blocked_scope_manifest.json")
    evidence_fields = _read_json(root / "output" / "data" / "evidence_field_index.json")
    release_bundle = _read_json(root / "output" / "reports" / "release_bundle_manifest.json")
    theorem_traceability = _read_json(root / "output" / "data" / "theorem_traceability_matrix.json")
    artifact_diffoscope = _read_json(root / "output" / "reports" / "artifact_diffoscope.json")
    proof_extraction = _read_json(root / "output" / "data" / "proof_extraction_index.json")
    state_space_catalog = _read_json(root / "output" / "data" / "state_space_catalog.json")
    causal_ablation = _read_json(root / "output" / "data" / "causal_ablation_matrix.json")
    artifact_license = _read_json(root / "output" / "reports" / "artifact_license_audit.json")
    release_notes = _read_json(root / "output" / "reports" / "release_notes_evidence.json")
    scholarship = _read_json(root / "output" / "data" / "scholarship_source_matrix.json")
    proof_dependency = _read_json(root / "output" / "data" / "proof_dependency_graph.json")
    transition_table = _read_json(root / "output" / "data" / "state_transition_table.json")
    ablation_sensitivity = _read_json(root / "output" / "reports" / "ablation_sensitivity_report.json")
    release_attestation = _read_json(root / "output" / "reports" / "release_attestation.json")

    checks["analytical_observable_sweep_schema"] = (
        observable.get("schema") == "template_active_inference.analytical_observable_sweep.v1"
        and float(observable.get("max_abs_residual", 1.0)) <= 1e-12
    )
    checks["analytical_assumption_index_schema"] = (
        assumptions.get("schema") == "template_active_inference.analytical_assumption_index.v1"
        and assumptions.get("all_equations_indexed") is True
    )
    checks["sensitivity_sweep_schema"] = (
        sensitivity.get("schema") == "template_active_inference.sensitivity_sweep.v1"
        and sensitivity.get("complete_grid") is True
    )
    checks["uncertainty_summary_schema"] = (
        uncertainty.get("schema") == "template_active_inference.uncertainty_summary.v1"
        and uncertainty.get("all_normalized") is True
    )
    checks["toy_benchmark_matrix_schema"] = (
        benchmark.get("schema") == "template_active_inference.toy_benchmark_matrix.v1"
        and benchmark.get("all_models_complete") is True
    )
    checks["si_policy_grid_schema"] = policy_grid.get("complete_grid") is True
    checks["si_efe_terms_schema"] = (
        efe_terms.get("schema") == "template_active_inference.si_efe_values.v1"
        and efe_terms.get("all_rows_explained") is True
        and efe_terms.get("all_rows_explained") == _efe_values_explained(efe_terms)
    )
    checks["si_graph_world_topology_sweep_schema"] = topology.get("all_summary_trace_agree") is True
    checks["si_graph_world_topology_traces_schema"] = (
        topology_traces.get("schema") == "template_active_inference.si_graph_world_topology_traces.v1"
        and topology_traces.get("all_trace_summary_agree") is True
        and topology_traces.get("topology_count") == topology.get("topology_count")
    )
    checks["graph_world_invariants_schema"] = graph_invariants.get("all_passed") is True
    checks["model_checking_witnesses_schema"] = (
        model_checking.get("schema") == "template_active_inference.model_checking_witnesses.v1"
        and model_checking.get("all_passed") is True
    )
    checks["interop_roundtrip_schema"] = (
        interop.get("schema") == "template_active_inference.interop_roundtrip_report.v1"
        and interop.get("all_lossless") is True
    )
    checks["gnn_roundtrip_schema"] = gnn_roundtrip.get("all_lossless") is True
    checks["gnn_lint_schema"] = gnn_lint.get("all_variables_mapped_once") is True
    checks["ontology_alias_schema"] = ontology_alias.get("no_conflicts") is True
    checks["ontology_profile_schema"] = ontology_profile.get("all_mapped_once") is True
    checks["lean_theorem_inventory_schema"] = lean_theorems.get("all_proved") is True
    checks["lean_graph_world_inventory_schema"] = lean_graph.get("all_topologies_witnessed") is True
    checks["lean_graph_world_inventory_schema"] = (
        checks["lean_graph_world_inventory_schema"]
        and lean_graph.get("all_policy_witnesses_present") is True
        and int(lean_graph.get("topology_count", 0) or 0) == int(topology.get("topology_count", 0) or 0)
    )
    checks["producer_completeness_schema"] = producer_completeness.get("all_complete") is True
    checks["stale_artifact_report_schema"] = stale_report.get("all_fresh") is True
    checks["manuscript_staleness_report_schema"] = (
        manuscript_staleness.get("schema") == "template_active_inference.manuscript_staleness_report.v1"
        and manuscript_staleness.get("all_fresh") is True
    )
    checks["cross_track_symbol_table_schema"] = (
        cross_symbols.get("all_consistent") is True
        and cross_symbols.get("all_shapes_declared") is True
        and cross_symbols.get("all_dtypes_declared") is True
        and cross_symbols.get("all_ontology_terms_declared") is True
        and cross_symbols.get("all_section_terms_declared") is True
    )
    checks["manuscript_evidence_tables_schema"] = evidence_tables.get("all_source_backed") is True
    checks["manuscript_token_provenance_schema"] = token_provenance.get("all_tokens_mapped") is True
    checks["claim_evidence_audit_schema"] = claim_audit.get("all_claims_typed") is True
    checks["validation_gate_index_schema"] = gate_index.get("all_indexed") is True
    checks["sheaf_section_status_matrix_schema"] = (
        section_status.get("schema") == "template_active_inference.sheaf_section_status_matrix.v1"
        and section_status.get("all_bound_fragments_present") is True
        and section_status.get("all_sections_have_status") is True
        and section_status.get("all_tracks_have_status") is True
        and int(section_status.get("cell_count", 0) or 0) > 0
    )
    checks["sheaf_render_log_schema"] = (
        render_log.get("schema") == "template_active_inference.sheaf_render_log.v1"
        and render_log.get("all_events_ok") is True
        and int(render_log.get("event_count", 0) or 0) > 0
    )
    checks["figure_source_map_schema"] = figure_source.get("all_figures_mapped") is True
    checks["figure_hash_manifest_schema"] = figure_hash.get("all_hashes_present") is True
    checks["scope_boundary_audit_schema"] = scope.get("scope_boundary_status") == "toy_only_pass"
    checks["adversarial_audit_schema"] = (
        adversarial.get("all_expected_failures_documented") is True
        and adversarial.get("all_expected_failures_observed") is True
        and int(adversarial.get("known_bad_rows_passed", 0) or 0) == 0
    )
    checks["replay_matrix_schema"] = (
        replay_matrix.get("schema") == "template_active_inference.replay_matrix.v1"
        and replay_matrix.get("all_replay_rows_matched") is True
        and replay_matrix.get("all_configured_producers_represented") is True
    )
    checks["track_improvement_scope_schema"] = (
        track_scope.get("schema") == "template_active_inference.track_improvement_scope.v1"
        and track_scope.get("all_live_tracks_valid") is True
    )
    checks["blocked_scope_manifest_schema"] = (
        blocked_scope.get("schema") == "template_active_inference.blocked_scope_manifest.v1"
        and blocked_scope.get("all_blocked") is True
    )
    checks["evidence_field_index_schema"] = (
        evidence_fields.get("schema") == "template_active_inference.evidence_field_index.v1"
        and evidence_fields.get("all_fields_mapped") is True
    )
    checks["release_bundle_manifest_schema"] = (
        release_bundle.get("schema") == "template_active_inference.release_bundle_manifest.v1"
        and release_bundle.get("all_required_sources_present") is True
        and release_bundle.get("all_copied_outputs_match_or_deferred") is True
    )
    checks["theorem_traceability_matrix_schema"] = (
        theorem_traceability.get("schema") == "template_active_inference.theorem_traceability_matrix.v1"
        and theorem_traceability.get("all_theorems_linked") is True
    )
    checks["artifact_diffoscope_schema"] = (
        artifact_diffoscope.get("schema") == "template_active_inference.artifact_diffoscope.v1"
        and artifact_diffoscope.get("all_equal") is True
    )
    checks["proof_extraction_index_schema"] = (
        proof_extraction.get("schema") == "template_active_inference.proof_extraction_index.v1"
        and proof_extraction.get("all_extracted") is True
        and proof_extraction.get("all_constructive") is True
    )
    checks["state_space_catalog_schema"] = (
        state_space_catalog.get("schema") == "template_active_inference.state_space_catalog.v1"
        and state_space_catalog.get("all_finite") is True
        and state_space_catalog.get("all_counts_positive") is True
    )
    checks["causal_ablation_matrix_schema"] = (
        causal_ablation.get("schema") == "template_active_inference.causal_ablation_matrix.v1"
        and causal_ablation.get("complete_grid") is True
        and causal_ablation.get("all_deterministic") is True
    )
    checks["artifact_license_audit_schema"] = (
        artifact_license.get("schema") == "template_active_inference.artifact_license_audit.v1"
        and artifact_license.get("all_license_safe") is True
    )
    checks["release_notes_evidence_schema"] = (
        release_notes.get("schema") == "template_active_inference.release_notes_evidence.v1"
        and release_notes.get("all_notes_source_backed") is True
    )
    checks["scholarship_source_matrix_schema"] = (
        scholarship.get("schema") == "template_active_inference.scholarship_source_matrix.v1"
        and scholarship.get("all_sources_connected") is True
        and scholarship.get("all_expected_sources_present") is True
    )
    checks["proof_dependency_graph_schema"] = (
        proof_dependency.get("schema") == "template_active_inference.proof_dependency_graph.v1"
        and proof_dependency.get("all_theorems_have_dependencies") is True
        and proof_dependency.get("all_edges_resolved") is True
    )
    checks["state_transition_table_schema"] = (
        transition_table.get("schema") == "template_active_inference.state_transition_table.v1"
        and transition_table.get("all_transitions_deterministic") is True
        and transition_table.get("all_reachable_states_covered") is True
    )
    checks["ablation_sensitivity_report_schema"] = (
        ablation_sensitivity.get("schema") == "template_active_inference.ablation_sensitivity_report.v1"
        and ablation_sensitivity.get("all_effects_source_backed") is True
    )
    checks["release_attestation_schema"] = (
        release_attestation.get("schema") == "template_active_inference.release_attestation.v1"
        and release_attestation.get("all_attested") is True
    )
    from visualizations.animation import validate_animation_frame_deltas

    checks["animation_frame_deltas_schema"] = (
        animation_deltas.get("schema") == "template_active_inference.animation_frame_deltas.v1"
        and animation_deltas.get("all_nonzero") is True
        and not validate_animation_frame_deltas(root)
    )
    checks["toy_sweep_track_schemas"] = not validate_toy_sweep_artifacts(root)
    checks["formal_interop_track_schemas"] = not validate_formal_interop_artifacts(root)
    checks["integration_audit_track_schemas"] = not validate_integration_audit_artifacts(root)
    checks["canonical_sheaf_track_schemas"] = not validate_sheaf_track_artifacts(root)

    log_path = root / "output" / "logs" / "pymdp_runs.jsonl"
    if _pymdp_logging_expected(root):
        checks["si_log_present"] = log_path.exists() and any(
            line.strip() for line in log_path.read_text(encoding="utf-8").splitlines()
        )

    checks["experiment_plan_metrics"] = checks.get("invariants_all_pass", False) and checks.get(
        str(summary_path.relative_to(root)),
        False,
    )
    if si_summary_present:
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "si_invariants_all_pass",
            False,
        )
    if comparison_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "si_policy_comparison_schema",
            False,
        )
    if graph_summary_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "si_graph_world_schema",
            False,
        )
    if crosswalk_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "sheaf_evidence_crosswalk_schema",
            False,
        )
    if dependency_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "validation_dependency_graph_schema",
            False,
        )
    if provenance_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "artifact_provenance_schema",
            False,
        )
    if replay_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "reproducibility_replay_schema",
            False,
        )
    if counterexample_path.exists():
        checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and checks.get(
            "counterexample_matrix_schema",
            False,
        )
    checks["experiment_plan_metrics"] = checks["experiment_plan_metrics"] and all(
        checks.get(key, False)
        for key in (
            "figures_nonblank",
            "toy_sweep_track_schemas",
            "formal_interop_track_schemas",
            "integration_audit_track_schemas",
            "animation_frame_deltas_schema",
            "pymdp_policy_posterior_grid_schema",
            "pymdp_runtime_diagnostics_schema",
            "si_graph_world_topology_traces_schema",
            "canonical_sheaf_track_schemas",
            "sheaf_section_status_matrix_schema",
            "sheaf_render_log_schema",
            "artifact_diffoscope_schema",
            "proof_extraction_index_schema",
            "state_space_catalog_schema",
            "causal_ablation_matrix_schema",
            "artifact_license_audit_schema",
            "release_notes_evidence_schema",
            "scholarship_source_matrix_schema",
            "proof_dependency_graph_schema",
            "state_transition_table_schema",
            "ablation_sensitivity_report_schema",
            "release_attestation_schema",
        )
    )

    return checks
