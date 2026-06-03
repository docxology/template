"""Semantic gluing certificate for the multi-track manuscript sheaf."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gnn.parser import parse_gnn_file
from manuscript.variables import generate_variables
from ontology.bindings import (
    BERNOULLI_EXPECTED_TERMS,
    BERNOULLI_SYMBOL_MAP,
    SI_EXPECTED_TERMS,
    SI_SYMBOL_MAP,
    load_section_ontology,
    validate_all_gnn_ontology,
)

from .coverage import gray_cell_count, load_sheaf_coverage_context

SEMANTIC_SCHEMA = "template_active_inference.semantic_gluing.v2"

ARTIFACT_PRODUCERS: dict[str, str] = {
    "output/data/parameter_sweep.csv": "run_analytical_sweep.py",
    "output/data/si_tmaze_summary.json": "simulate_si_tmaze.py",
    "output/data/si_tmaze_trace.json": "simulate_si_tmaze.py",
    "output/data/si_policy_comparison.json": "simulate_si_tmaze.py",
    "output/data/pymdp_policy_posterior_grid.json": "simulate_si_tmaze.py",
    "output/reports/pymdp_runtime_diagnostics.json": "simulate_si_tmaze.py",
    "output/data/si_graph_world_summary.json": "simulate_si_graph_world.py",
    "output/data/si_graph_world_trace.json": "simulate_si_graph_world.py",
    "output/data/analysis_statistics.json": "compute_statistics.py",
    "output/data/sheaf_coverage_matrix.json": "generate_figures.py",
    "output/data/manuscript_variables.json": "z_generate_manuscript_variables.py",
    "output/data/sheaf_evidence_crosswalk.json": "generate_sheaf_tracks.py",
    "output/data/validation_dependency_graph.json": "generate_sheaf_tracks.py",
    "output/data/sheaf_gluing_certificate.json": "generate_sheaf_tracks.py",
    "output/data/sheaf_section_status_matrix.json": "generate_sheaf_tracks.py",
    "output/reports/sheaf_render_log.json": "generate_sheaf_tracks.py",
    "output/data/artifact_provenance.json": "generate_sheaf_tracks.py",
    "output/figures/semantic_gluing_graph.png": "generate_figures.py",
    "output/figures/si_belief_trajectory.gif": "render_animation.py",
    "output/data/animation_frame_deltas.json": "render_animation.py",
    "output/figures/sheaf_layers_overview.png": "generate_figures.py",
    "output/figures/sheaf_coverage_heatmap.png": "generate_figures.py",
    "output/figures/figure_registry.json": "generate_figures.py",
    "output/reports/invariants.json": "run_analytical_sweep.py",
    "output/reports/si_invariants.json": "simulate_si_tmaze.py",
    "output/reports/si_tmaze_run_report.json": "simulate_si_tmaze.py",
    "output/reports/reproducibility_replay.json": "generate_validation_spine.py",
    "output/reports/counterexample_matrix.json": "generate_sheaf_tracks.py",
    "output/data/analytical_assumption_index.json": "generate_toy_sweep_tracks.py",
    "output/data/analytical_observable_sweep.json": "generate_toy_sweep_tracks.py",
    "output/data/sensitivity_sweep.json": "generate_sheaf_tracks.py",
    "output/data/uncertainty_summary.json": "generate_sheaf_tracks.py",
    "output/data/toy_benchmark_matrix.json": "generate_toy_sweep_tracks.py",
    "output/data/si_policy_grid.json": "generate_toy_sweep_tracks.py",
    "output/data/si_efe_terms.json": "generate_toy_sweep_tracks.py",
    "output/data/si_graph_world_topology_sweep.json": "generate_toy_sweep_tracks.py",
    "output/data/si_graph_world_topology_traces.json": "generate_toy_sweep_tracks.py",
    "output/reports/graph_world_invariants.json": "generate_toy_sweep_tracks.py",
    "output/reports/model_checking_witnesses.json": "generate_sheaf_tracks.py",
    "output/data/interop_roundtrip_report.json": "generate_sheaf_tracks.py",
    "output/data/gnn_roundtrip_report.json": "generate_formal_interop_tracks.py",
    "output/reports/gnn_lint_report.json": "generate_formal_interop_tracks.py",
    "output/data/ontology_alias_index.json": "generate_formal_interop_tracks.py",
    "output/data/ontology_profile_matrix.json": "generate_formal_interop_tracks.py",
    "output/reports/lean_theorem_inventory.json": "generate_formal_interop_tracks.py",
    "output/reports/lean_graph_world_inventory.json": "generate_formal_interop_tracks.py",
    "output/reports/producer_completeness.json": "generate_integration_audit.py",
    "output/reports/stale_artifact_report.json": "generate_integration_audit.py",
    "output/data/cross_track_symbol_table.json": "generate_integration_audit.py",
    "output/data/manuscript_evidence_tables.json": "generate_integration_audit.py",
    "output/data/manuscript_token_provenance.json": "generate_integration_audit.py",
    "output/reports/claim_evidence_audit.json": "generate_integration_audit.py",
    "output/data/validation_gate_index.json": "generate_integration_audit.py",
    "output/data/figure_source_map.json": "generate_integration_audit.py",
    "output/reports/figure_hash_manifest.json": "generate_integration_audit.py",
    "output/reports/scope_boundary_audit.json": "generate_integration_audit.py",
    "output/reports/adversarial_audit.json": "generate_sheaf_tracks.py",
    "output/reports/manuscript_staleness_report.json": "z_generate_manuscript_variables.py",
    "output/reports/replay_matrix.json": "generate_sheaf_tracks.py",
    "output/data/track_improvement_scope.json": "generate_sheaf_tracks.py",
    "output/reports/blocked_scope_manifest.json": "generate_sheaf_tracks.py",
    "output/data/evidence_field_index.json": "generate_sheaf_tracks.py",
    "output/reports/release_bundle_manifest.json": "generate_sheaf_tracks.py",
    "output/data/theorem_traceability_matrix.json": "generate_sheaf_tracks.py",
    "output/reports/artifact_diffoscope.json": "generate_integration_audit.py",
    "output/data/proof_extraction_index.json": "generate_formal_interop_tracks.py",
    "output/data/state_space_catalog.json": "generate_toy_sweep_tracks.py",
    "output/data/causal_ablation_matrix.json": "generate_toy_sweep_tracks.py",
    "output/reports/artifact_license_audit.json": "generate_integration_audit.py",
    "output/reports/release_notes_evidence.json": "generate_integration_audit.py",
}

ARTIFACT_CONSUMERS: dict[str, tuple[str, ...]] = {
    "output/data/parameter_sweep.csv": ("methods_analytical", "results_mi_sweep"),
    "output/data/si_tmaze_summary.json": ("methods_pymdp", "results_si_tmaze"),
    "output/data/si_tmaze_trace.json": ("methods_pymdp", "results_si_tmaze"),
    "output/data/si_policy_comparison.json": ("methods_pymdp", "results_si_tmaze"),
    "output/data/pymdp_policy_posterior_grid.json": ("methods_pymdp", "appendix_full_sheaf"),
    "output/reports/pymdp_runtime_diagnostics.json": ("methods_pymdp", "appendix_full_sheaf"),
    "output/data/si_graph_world_summary.json": ("methods_pymdp", "results_si_tmaze"),
    "output/data/si_graph_world_trace.json": ("methods_pymdp", "results_si_tmaze", "appendix_full_sheaf"),
    "output/data/analysis_statistics.json": ("results_si_tmaze", "results_invariants"),
    "output/data/sheaf_coverage_matrix.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/data/manuscript_variables.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/data/sheaf_gluing_certificate.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/data/sheaf_evidence_crosswalk.json": ("methods_sheaf",),
    "output/data/validation_dependency_graph.json": ("methods_sheaf",),
    "output/data/sheaf_section_status_matrix.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/reports/sheaf_render_log.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/data/artifact_provenance.json": ("methods_sheaf",),
    "output/reports/counterexample_matrix.json": ("methods_sheaf",),
    "output/reports/replay_matrix.json": ("results_invariants", "appendix_full_sheaf"),
    "output/data/analytical_assumption_index.json": ("methods_analytical", "appendix_full_sheaf"),
    "output/data/sensitivity_sweep.json": ("results_invariants", "appendix_full_sheaf"),
    "output/data/uncertainty_summary.json": ("results_invariants", "appendix_full_sheaf"),
    "output/data/toy_benchmark_matrix.json": ("results_invariants", "appendix_full_sheaf"),
    "output/data/si_policy_grid.json": ("results_invariants", "appendix_full_sheaf"),
    "output/data/si_efe_terms.json": ("results_invariants", "appendix_full_sheaf"),
    "output/data/analytical_observable_sweep.json": ("results_invariants", "appendix_full_sheaf"),
    "output/data/si_graph_world_topology_sweep.json": ("results_invariants", "appendix_full_sheaf"),
    "output/data/si_graph_world_topology_traces.json": ("results_invariants", "appendix_full_sheaf"),
    "output/reports/graph_world_invariants.json": ("results_invariants", "appendix_full_sheaf"),
    "output/reports/model_checking_witnesses.json": ("methods_lean", "appendix_full_sheaf"),
    "output/data/interop_roundtrip_report.json": ("methods_pymdp", "appendix_full_sheaf"),
    "output/data/gnn_roundtrip_report.json": ("methods_pymdp", "appendix_full_sheaf"),
    "output/reports/gnn_lint_report.json": ("methods_pymdp", "appendix_full_sheaf"),
    "output/data/ontology_alias_index.json": ("methods_pymdp", "appendix_full_sheaf"),
    "output/data/ontology_profile_matrix.json": ("methods_pymdp", "appendix_full_sheaf"),
    "output/reports/lean_theorem_inventory.json": ("methods_lean", "appendix_full_sheaf"),
    "output/reports/lean_graph_world_inventory.json": ("methods_lean", "appendix_full_sheaf"),
    "output/reports/producer_completeness.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/reports/stale_artifact_report.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/data/cross_track_symbol_table.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/data/manuscript_evidence_tables.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/data/manuscript_token_provenance.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/reports/claim_evidence_audit.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/data/validation_gate_index.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/data/figure_source_map.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/reports/figure_hash_manifest.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/reports/scope_boundary_audit.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/reports/adversarial_audit.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/reports/manuscript_staleness_report.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/data/track_improvement_scope.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/reports/blocked_scope_manifest.json": ("methods_sheaf", "discussion_outlook", "appendix_full_sheaf"),
    "output/data/evidence_field_index.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/reports/release_bundle_manifest.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/data/theorem_traceability_matrix.json": ("methods_lean", "appendix_full_sheaf"),
    "output/reports/artifact_diffoscope.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/data/proof_extraction_index.json": ("methods_lean", "appendix_full_sheaf"),
    "output/data/state_space_catalog.json": ("results_invariants", "appendix_full_sheaf"),
    "output/data/causal_ablation_matrix.json": ("results_invariants", "appendix_full_sheaf"),
    "output/reports/artifact_license_audit.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/reports/release_notes_evidence.json": ("discussion_outlook", "appendix_full_sheaf"),
    "output/reports/reproducibility_replay.json": ("results_invariants",),
    "output/figures/semantic_gluing_graph.png": ("methods_sheaf",),
    "output/figures/si_belief_trajectory.gif": ("appendix_full_sheaf",),
    "output/data/animation_frame_deltas.json": ("appendix_full_sheaf",),
    "output/figures/sheaf_layers_overview.png": ("methods_sheaf",),
    "output/figures/sheaf_coverage_heatmap.png": ("appendix_full_sheaf",),
    "output/figures/figure_registry.json": ("methods_sheaf", "appendix_full_sheaf"),
    "output/reports/invariants.json": ("results_invariants",),
    "output/reports/si_invariants.json": ("results_si_tmaze",),
    "output/reports/si_tmaze_run_report.json": ("results_si_tmaze",),
}

ARTIFACT_GATES: dict[str, tuple[str, ...]] = {
    "output/data/parameter_sweep.csv": ("validate_outputs",),
    "output/data/si_tmaze_summary.json": ("validate_outputs",),
    "output/data/si_tmaze_trace.json": ("validate_outputs",),
    "output/data/analysis_statistics.json": ("validate_outputs",),
    "output/data/sheaf_coverage_matrix.json": ("validate_outputs", "validate_manuscript"),
    "output/data/manuscript_variables.json": ("validate_manuscript",),
    "output/data/sheaf_gluing_certificate.json": ("validate_manuscript", "validate_outputs"),
    "output/data/sheaf_evidence_crosswalk.json": ("validate_manuscript", "validate_outputs"),
    "output/data/validation_dependency_graph.json": ("validate_manuscript", "validate_outputs"),
    "output/data/sheaf_section_status_matrix.json": ("validate_manuscript", "validate_outputs"),
    "output/reports/sheaf_render_log.json": ("validate_manuscript", "validate_outputs"),
    "output/data/artifact_provenance.json": ("validate_manuscript", "validate_outputs"),
    "output/reports/replay_matrix.json": ("validate_outputs", "validate_manuscript"),
    "output/data/si_policy_comparison.json": ("validate_outputs",),
    "output/data/pymdp_policy_posterior_grid.json": ("validate_outputs", "validate_manuscript"),
    "output/reports/pymdp_runtime_diagnostics.json": ("validate_outputs", "validate_manuscript"),
    "output/data/si_graph_world_summary.json": ("validate_outputs",),
    "output/data/si_graph_world_trace.json": ("validate_outputs",),
    "output/figures/si_belief_trajectory.gif": ("validate_outputs",),
    "output/figures/semantic_gluing_graph.png": ("validate_outputs", "figure_registry"),
    "output/reports/reproducibility_replay.json": ("validate_outputs",),
    "output/reports/counterexample_matrix.json": ("validate_outputs", "validate_manuscript"),
    "output/data/analytical_assumption_index.json": ("validate_outputs", "validate_manuscript"),
    "output/data/analytical_observable_sweep.json": ("validate_outputs",),
    "output/data/sensitivity_sweep.json": ("validate_outputs",),
    "output/data/uncertainty_summary.json": ("validate_outputs",),
    "output/data/toy_benchmark_matrix.json": ("validate_outputs",),
    "output/data/si_policy_grid.json": ("validate_outputs",),
    "output/data/si_efe_terms.json": ("validate_outputs",),
    "output/data/si_graph_world_topology_sweep.json": ("validate_outputs",),
    "output/data/si_graph_world_topology_traces.json": ("validate_outputs",),
    "output/reports/graph_world_invariants.json": ("validate_outputs",),
    "output/reports/model_checking_witnesses.json": ("validate_outputs",),
    "output/data/interop_roundtrip_report.json": ("validate_outputs",),
    "output/data/gnn_roundtrip_report.json": ("validate_outputs",),
    "output/reports/gnn_lint_report.json": ("validate_outputs",),
    "output/data/ontology_alias_index.json": ("validate_outputs",),
    "output/data/ontology_profile_matrix.json": ("validate_outputs",),
    "output/reports/lean_theorem_inventory.json": ("validate_outputs",),
    "output/reports/lean_graph_world_inventory.json": ("validate_outputs",),
    "output/reports/producer_completeness.json": ("validate_outputs", "validate_manuscript"),
    "output/reports/stale_artifact_report.json": ("validate_outputs", "validate_manuscript"),
    "output/data/cross_track_symbol_table.json": ("validate_outputs", "validate_manuscript"),
    "output/data/manuscript_evidence_tables.json": ("validate_outputs", "validate_manuscript"),
    "output/data/manuscript_token_provenance.json": ("validate_outputs", "validate_manuscript"),
    "output/reports/claim_evidence_audit.json": ("validate_outputs", "validate_manuscript"),
    "output/data/validation_gate_index.json": ("validate_outputs", "validate_manuscript"),
    "output/data/figure_source_map.json": ("validate_outputs", "validate_manuscript"),
    "output/reports/figure_hash_manifest.json": ("validate_outputs", "validate_manuscript"),
    "output/reports/scope_boundary_audit.json": ("validate_outputs", "validate_manuscript"),
    "output/reports/adversarial_audit.json": ("validate_outputs", "validate_manuscript"),
    "output/reports/manuscript_staleness_report.json": ("validate_outputs", "validate_manuscript"),
    "output/data/animation_frame_deltas.json": ("validate_outputs", "validate_manuscript"),
    "output/figures/sheaf_layers_overview.png": ("validate_outputs", "figure_registry"),
    "output/figures/sheaf_coverage_heatmap.png": ("validate_outputs", "figure_registry"),
    "output/figures/figure_registry.json": ("validate_outputs",),
    "output/reports/invariants.json": ("validate_outputs",),
    "output/reports/si_invariants.json": ("validate_outputs",),
    "output/reports/si_tmaze_run_report.json": ("validate_outputs",),
    "output/data/track_improvement_scope.json": ("validate_outputs", "validate_manuscript"),
    "output/reports/blocked_scope_manifest.json": ("validate_outputs", "validate_manuscript"),
    "output/data/evidence_field_index.json": ("validate_outputs", "validate_manuscript"),
    "output/reports/release_bundle_manifest.json": ("validate_outputs", "validate_manuscript"),
    "output/data/theorem_traceability_matrix.json": ("validate_outputs", "validate_manuscript"),
    "output/reports/artifact_diffoscope.json": ("validate_outputs", "validate_manuscript"),
    "output/data/proof_extraction_index.json": ("validate_outputs", "validate_manuscript"),
    "output/data/state_space_catalog.json": ("validate_outputs", "validate_manuscript"),
    "output/data/causal_ablation_matrix.json": ("validate_outputs", "validate_manuscript"),
    "output/reports/artifact_license_audit.json": ("validate_outputs", "validate_manuscript"),
    "output/reports/release_notes_evidence.json": ("validate_outputs", "validate_manuscript"),
}


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _configured_analysis_scripts(root: Path) -> list[str]:
    import yaml

    config_path = root / "manuscript" / "config.yaml"
    if not config_path.is_file():
        return []
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    analysis = data.get("analysis") or {}
    scripts = analysis.get("scripts") or []
    return [str(script) for script in scripts]


def _claims_by_path(root: Path) -> dict[str, list[str]]:
    claims: dict[str, list[str]] = {}
    for claim in _claim_records(root):
        path = claim.get("path")
        claim_id = claim.get("id")
        if path and claim_id:
            claims.setdefault(str(path), []).append(str(claim_id))
    return claims


def _animation_frame_count(root: Path) -> int:
    gif_path = root / "output" / "figures" / "si_belief_trajectory.gif"
    if not gif_path.is_file():
        return 0
    try:
        from PIL import Image, ImageSequence

        with Image.open(gif_path) as image:
            return sum(1 for _ in ImageSequence.Iterator(image))
    except (ImportError, OSError, ValueError, EOFError):
        return 0


def _lean_status(root: Path) -> dict[str, Any]:
    try:
        from visualizations.lean_boundary import load_lean_boundary_rows

        rows = load_lean_boundary_rows(root)
    except (ImportError, OSError, ValueError):
        return {"module_count": 0, "proved_count": 0, "all_proved": False, "names": []}
    return {
        "module_count": len(rows),
        "proved_count": sum(1 for row in rows if row.status == "proved"),
        "all_proved": bool(rows) and all(row.status == "proved" for row in rows),
        "names": sorted(row.name for row in rows),
    }


def _policy_comparison_restrictions(root: Path) -> dict[str, Any]:
    path = root / "output" / "data" / "si_policy_comparison.json"
    data = _load_json(path)
    runs = data.get("runs") or []
    return {
        "run_count": int((data.get("summary") or {}).get("run_count", len(runs)) or 0),
        "modes": sorted({str(row.get("mode")) for row in runs if row.get("mode")}),
        "horizons": sorted({int(row.get("horizon")) for row in runs if row.get("horizon") is not None}),
        "goal_reached_count": sum(1 for row in runs if row.get("goal_reached") is True),
        "complete_grid": (data.get("summary") or {}).get("complete_grid") is True,
        "all_efe_rows_explained": (data.get("summary") or {}).get("all_efe_rows_explained") is True,
    }


def _policy_posterior_restrictions(root: Path) -> dict[str, Any]:
    data = _load_json(root / "output" / "data" / "pymdp_policy_posterior_grid.json")
    return {
        "row_count": int(data.get("row_count", 0) or 0),
        "available_row_count": int(data.get("available_row_count", 0) or 0),
        "all_available_posteriors_normalized": data.get("all_available_posteriors_normalized") is True,
        "all_unavailable_rows_explained": data.get("all_unavailable_rows_explained") is True,
    }


def _runtime_diagnostics_restrictions(root: Path) -> dict[str, Any]:
    data = _load_json(root / "output" / "reports" / "pymdp_runtime_diagnostics.json")
    return {
        "ok": data.get("ok") is True,
        "construction_count": int(data.get("construction_count", 0) or 0),
        "known_warning_count": int(data.get("known_warning_count", 0) or 0),
        "unexpected_warning_count": int(data.get("unexpected_warning_count", 0) or 0),
    }


def _graph_world_restrictions(root: Path) -> dict[str, Any]:
    summary = _load_json(root / "output" / "data" / "si_graph_world_summary.json")
    trace = _load_json(root / "output" / "data" / "si_graph_world_trace.json")
    trace_steps = trace.get("steps") or []
    summary_steps = int(summary.get("steps", 0) or 0)
    return {
        "steps": summary_steps,
        "trace_steps": len(trace_steps),
        "steps_match": summary_steps == len(trace_steps) and summary_steps > 0,
        "goal_reached": summary.get("goal_reached") is True,
    }


def _pymdp_hash_restrictions(root: Path) -> dict[str, Any]:
    summary = _load_json(root / "output" / "data" / "si_tmaze_summary.json")
    stats = _load_json(root / "output" / "data" / "analysis_statistics.json")
    return {
        "mode_match": not summary or not stats or summary.get("mode") == stats.get("pymdp_mode"),
        "config_hash_match": not summary or not stats or summary.get("config_hash") == stats.get("pymdp_config_hash"),
    }


def _gnn_symbols(root: Path, rel_path: str) -> dict[str, str]:
    path = root / rel_path
    if not path.is_file():
        return {}
    return dict(parse_gnn_file(path).ontology)


def _section_ontology_symbols(root: Path, rel_path: str) -> dict[str, str]:
    symbols = load_section_ontology(root / rel_path)
    return {str(key): str(value) for key, value in symbols.items()}


def _expected_symbol_gaps(
    *,
    label: str,
    gnn_symbols: dict[str, str],
    section_symbols: dict[str, str],
    symbol_map: dict[str, str],
    expected_terms: dict[str, str],
) -> list[str]:
    gaps: list[str] = []
    for _, variable in symbol_map.items():
        expected = expected_terms.get(variable)
        if expected is None:
            continue
        gnn_term = gnn_symbols.get(variable)
        section_term = section_symbols.get(variable)
        if gnn_term != expected:
            gaps.append(f"{label}: GNN variable {variable!r} annotated {gnn_term!r}, expected {expected!r}")
        if section_term != expected:
            gaps.append(
                f"{label}: section ontology variable {variable!r} annotated {section_term!r}, expected {expected!r}"
            )
    return gaps


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


def build_semantic_gluing_certificate(project_root: Path) -> dict[str, Any]:
    """Build a JSON-serializable semantic certificate from live project state."""
    root = project_root.resolve()
    ctx = load_sheaf_coverage_context(root)
    issues = semantic_gluing_issues(root)
    variables = generate_variables(root, require_analysis_outputs=False)
    bernoulli_symbols = _gnn_symbols(root, "gnn/bernoulli_toy.gnn.md")
    si_symbols = _gnn_symbols(root, "gnn/si_tmaze.gnn.md")
    dependency_graph = build_validation_dependency_graph(root)
    policy = _policy_comparison_restrictions(root)
    posterior = _policy_posterior_restrictions(root)
    runtime = _runtime_diagnostics_restrictions(root)
    graph_world = _graph_world_restrictions(root)
    pymdp_hash = _pymdp_hash_restrictions(root)
    lean = _lean_status(root)
    sensitivity = _load_json(root / "output" / "data" / "sensitivity_sweep.json")
    uncertainty = _load_json(root / "output" / "data" / "uncertainty_summary.json")
    benchmark = _load_json(root / "output" / "data" / "toy_benchmark_matrix.json")
    model_checking = _load_json(root / "output" / "reports" / "model_checking_witnesses.json")
    interop = _load_json(root / "output" / "data" / "interop_roundtrip_report.json")
    adversarial = _load_json(root / "output" / "reports" / "adversarial_audit.json")
    stale = _load_json(root / "output" / "reports" / "stale_artifact_report.json")
    manuscript_staleness = _load_json(root / "output" / "reports" / "manuscript_staleness_report.json")
    tokens = _load_json(root / "output" / "data" / "manuscript_token_provenance.json")
    figures = _load_json(root / "output" / "data" / "figure_source_map.json")
    scope = _load_json(root / "output" / "reports" / "scope_boundary_audit.json")
    provenance = _load_json(root / "output" / "data" / "artifact_provenance.json")
    assumptions = _load_json(root / "output" / "data" / "analytical_assumption_index.json")
    animation_deltas = _load_json(root / "output" / "data" / "animation_frame_deltas.json")
    release_bundle = _load_json(root / "output" / "reports" / "release_bundle_manifest.json")
    evidence_fields = _load_json(root / "output" / "data" / "evidence_field_index.json")
    theorem_traceability = _load_json(root / "output" / "data" / "theorem_traceability_matrix.json")
    gate_index = _load_json(root / "output" / "data" / "validation_gate_index.json")
    section_status = _load_json(root / "output" / "data" / "sheaf_section_status_matrix.json")
    render_log = _load_json(root / "output" / "reports" / "sheaf_render_log.json")
    track_scope = _load_json(root / "output" / "data" / "track_improvement_scope.json")
    blocked_scope = _load_json(root / "output" / "reports" / "blocked_scope_manifest.json")
    replay_matrix = _load_json(root / "output" / "reports" / "replay_matrix.json")
    try:
        from roadmap_tracks.sheaf_tracks import _canonical_restrictions

        canonical_restrictions = _canonical_restrictions(root)
    except (ImportError, OSError, ValueError, KeyError, TypeError):
        canonical_restrictions = {}
    from validation_spine import validate_validation_spine

    return {
        "schema": SEMANTIC_SCHEMA,
        "ok": not issues,
        "issues": issues,
        "tracks": [
            {
                "id": tid,
                "renderer": spec.renderer,
                "optional": spec.optional,
                "order": spec.order,
            }
            for tid, spec in sorted(ctx.registry.tracks.items(), key=lambda item: item[1].order)
        ],
        "sections": _section_records(root),
        "shared_symbols": {
            "bernoulli": {var: bernoulli_symbols.get(var) for var in BERNOULLI_EXPECTED_TERMS},
            "si_tmaze": {var: si_symbols.get(var) for var in SI_EXPECTED_TERMS},
        },
        "artifact_sources": {
            "coverage_matrix": {
                "path": "output/data/sheaf_coverage_matrix.json",
                "exists": (root / "output" / "data" / "sheaf_coverage_matrix.json").exists(),
            },
            "si_summary": {
                "path": "output/data/si_tmaze_summary.json",
                "exists": (root / "output" / "data" / "si_tmaze_summary.json").exists(),
            },
            "analysis_statistics": {
                "path": "output/data/analysis_statistics.json",
                "exists": (root / "output" / "data" / "analysis_statistics.json").exists(),
            },
            "claim_ledger": {
                "path": "data/claim_ledger.yaml",
                "exists": (root / "data" / "claim_ledger.yaml").exists(),
            },
            "evidence_crosswalk": {
                "path": "output/data/sheaf_evidence_crosswalk.json",
                "exists": (root / "output" / "data" / "sheaf_evidence_crosswalk.json").exists(),
            },
            "dependency_graph": {
                "path": "output/data/validation_dependency_graph.json",
                "exists": (root / "output" / "data" / "validation_dependency_graph.json").exists(),
            },
            "analytical_assumption_index": {
                "path": "output/data/analytical_assumption_index.json",
                "exists": (root / "output" / "data" / "analytical_assumption_index.json").exists(),
            },
            "animation_frame_deltas": {
                "path": "output/data/animation_frame_deltas.json",
                "exists": (root / "output" / "data" / "animation_frame_deltas.json").exists(),
            },
            "manuscript_staleness": {
                "path": "output/reports/manuscript_staleness_report.json",
                "exists": (root / "output" / "reports" / "manuscript_staleness_report.json").exists(),
            },
            "track_improvement_scope": {
                "path": "output/data/track_improvement_scope.json",
                "exists": (root / "output" / "data" / "track_improvement_scope.json").exists(),
            },
            "evidence_field_index": {
                "path": "output/data/evidence_field_index.json",
                "exists": (root / "output" / "data" / "evidence_field_index.json").exists(),
            },
            "release_bundle": {
                "path": "output/reports/release_bundle_manifest.json",
                "exists": (root / "output" / "reports" / "release_bundle_manifest.json").exists(),
            },
            "theorem_traceability": {
                "path": "output/data/theorem_traceability_matrix.json",
                "exists": (root / "output" / "data" / "theorem_traceability_matrix.json").exists(),
            },
            "section_status_matrix": {
                "path": "output/data/sheaf_section_status_matrix.json",
                "exists": (root / "output" / "data" / "sheaf_section_status_matrix.json").exists(),
            },
            "sheaf_render_log": {
                "path": "output/reports/sheaf_render_log.json",
                "exists": (root / "output" / "reports" / "sheaf_render_log.json").exists(),
            },
        },
        "restrictions": {
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
            "no_versioned_live_tracks": not any(
                tid.endswith(("_v2", "_v3", "_v4", "_v5")) for tid in ctx.registry.tracks
            ),
            **canonical_restrictions,
        },
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
    """Refresh composed and hydrated manuscript artifacts for semantic checks."""
    from manuscript.hydrate import write_resolved_manuscript
    from manuscript.variables import generate_variables
    from roadmap_tracks.integration_audit import write_manuscript_staleness_report

    from .compose import compose_all_sections

    variables_path = root / "output" / "data" / "manuscript_variables.json"
    variables_path.parent.mkdir(parents=True, exist_ok=True)
    compose_all_sections(root)
    variables = generate_variables(root, require_analysis_outputs=False)
    variables_path.write_text(json.dumps(variables, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_resolved_manuscript(root, variables)
    write_manuscript_staleness_report(root)


def write_semantic_gluing_outputs(project_root: Path) -> dict[str, Path]:
    """Write semantic certificate, evidence crosswalk, and dependency graph outputs."""
    root = project_root.resolve()
    data_dir = root / "output" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    crosswalk_path = data_dir / "sheaf_evidence_crosswalk.json"
    dependency_path = data_dir / "validation_dependency_graph.json"
    certificate_path = data_dir / "sheaf_gluing_certificate.json"

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
    _refresh_hydrated_manuscript(root)
    status_paths = write_sheaf_status_outputs(root)
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
        "artifact_graph": _stable_artifact_graph(payload),
    }


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
    if saved.get("restrictions", {}).get("coverage_missing") != 0:
        saved_issues.append("saved sheaf_gluing_certificate.json records missing coverage")
    issues = semantic_gluing_issues(root)
    issues.extend(saved_issues)
    live = build_semantic_gluing_certificate(root)
    if _stable_certificate_fields(saved) != _stable_certificate_fields(live):
        issues.append("saved sheaf_gluing_certificate.json is stale relative to live semantic fields")
    return issues
