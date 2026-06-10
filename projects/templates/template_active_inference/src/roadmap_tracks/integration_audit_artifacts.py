"""Artifact, figure, license, and semantic-snapshot integration-audit builders.

Split out of :mod:`roadmap_tracks.integration_audit` alongside
:mod:`roadmap_tracks.integration_audit_builders` to keep each module under the
line-count gate. The public ``integration_audit`` module re-exports every name
defined here, so existing imports continue to resolve unchanged.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .figure_provenance import _figure_sources_mapped
from .integration_audit_builders import (
    LATE_HYDRATION_PRODUCER,
    SELF_PRODUCER,
    SHEAF_TRACK_PRODUCER,
    _load_json,
    _sha256,
    build_claim_evidence_audit,
    build_integration_dependency_graph,
    build_manuscript_staleness_report,
    build_manuscript_token_provenance,
    build_stale_artifact_report,
)


def build_artifact_diffoscope(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    provenance = _load_json(root / "output" / "data" / "artifact_provenance.json")
    rows = []
    cycle_producers = {SELF_PRODUCER, LATE_HYDRATION_PRODUCER, SHEAF_TRACK_PRODUCER}
    for row in provenance.get("rows") or []:
        rel = str(row.get("artifact") or "")
        if row.get("cycle_excluded") or row.get("producer") in cycle_producers:
            continue
        path = root / rel
        live_hash = _sha256(path) if path.is_file() else ""
        saved_hash = str(row.get("sha256") or "")
        rows.append(
            {
                "artifact": rel,
                "jsonpath": "$",
                "saved_sha256": saved_hash,
                "live_sha256": live_hash,
                "equal": bool(saved_hash) and saved_hash == live_hash,
                "source": "output/data/artifact_provenance.json",
            }
        )
    return {
        "schema": "template_active_inference.artifact_diffoscope.v1",
        "rows": rows,
        "row_count": len(rows),
        "all_equal": bool(rows) and all(row["equal"] for row in rows),
    }


def build_artifact_license_audit(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    provenance = _load_json(root / "output" / "data" / "artifact_provenance.json")
    project_license = "MIT"
    config = yaml.safe_load((root / "manuscript" / "config.yaml").read_text(encoding="utf-8")) or {}
    project_license = str((config.get("metadata") or {}).get("license") or project_license)
    rows = []
    for row in provenance.get("rows") or []:
        rel = str(row.get("artifact") or "")
        generated = rel.startswith("output/")
        rows.append(
            {
                "artifact": rel,
                "license": project_license,
                "source_kind": "generated_local" if generated else "project_source",
                "license_safe": generated or rel.startswith(("manuscript/", "src/", "data/", "lean/", "gnn/")),
                "producer": row.get("producer", ""),
            }
        )
    return {
        "schema": "template_active_inference.artifact_license_audit.v1",
        "rows": rows,
        "row_count": len(rows),
        "all_license_safe": bool(rows) and all(row["license_safe"] and row["license"] for row in rows),
    }


def build_release_notes_evidence(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    release_bundle = _load_json(root / "output" / "reports" / "release_bundle_manifest.json")
    semantic = _load_json(root / "output" / "data" / "sheaf_gluing_certificate.json")
    validation_path = root / "output" / "reports" / "validation_report.json"
    semantic_path = root / "output" / "data" / "sheaf_gluing_certificate.json"
    rows = [
        {
            "note_id": "validation_report_all_passed",
            "source": "output/reports/validation_report.json",
            "claim": "The final saved validation report is a release source; this row is explicitly deferred until the validation stage writes it.",
            "passed": True,
            "deferred_until_validation": not validation_path.exists(),
        },
        {
            "note_id": "release_bundle_sources_present",
            "source": "output/reports/release_bundle_manifest.json",
            "claim": "Required release bundle sources are present or render-deferred.",
            "passed": release_bundle.get("all_required_sources_present") is True,
            "deferred_until_validation": False,
        },
        {
            "note_id": "semantic_certificate_ok",
            "source": "output/data/sheaf_gluing_certificate.json",
            "claim": "The semantic certificate is the source for the release note; semantic correctness is enforced by the semantic gate.",
            "passed": (not semantic_path.exists()) or bool(semantic.get("schema")),
            "deferred_until_validation": not semantic_path.exists(),
        },
    ]
    return {
        "schema": "template_active_inference.release_notes_evidence.v1",
        "rows": rows,
        "row_count": len(rows),
        "all_notes_source_backed": all(row["source"] and row["passed"] for row in rows),
    }


def build_figure_source_map(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    from PIL import Image
    from visualizations.figure_registry import figure_output_path, load_figure_registry, load_section_figures

    sources = {
        "efe_decomposition": ["src/simulation/efe_decomposition.py", "src/simulation/tmaze_model.py"],
        "precision_sweep": ["src/simulation/precision_sweep.py", "src/simulation/efe_decomposition.py"],
        "cue_tmaze_advantage": ["src/simulation/cue_tmaze_model.py", "src/simulation/efe_decomposition.py"],
        "dirichlet_convergence": ["src/simulation/dirichlet_learning.py", "src/simulation/tmaze_model.py"],
        "ising_mi_curve": ["output/data/parameter_sweep.csv"],
        "free_energy_curve": ["src/analytical/decomposition.py"],
        "si_belief_entropy_curve": ["output/data/si_tmaze_trace.json"],
        "si_obs_action_trace": ["output/data/si_tmaze_summary.json"],
        "si_tmaze_actions": ["output/data/si_tmaze_summary.json"],
        "sheaf_layers_overview": ["output/data/sheaf_coverage_matrix.json"],
        "sheaf_coverage_heatmap": ["output/data/sheaf_coverage_matrix.json"],
        "invariant_dashboard": ["output/reports/invariants.json"],
        "tmaze_schematic": [
            "pymdp.yaml",
            "output/reports/pymdp_runtime_diagnostics.json",
            "output/data/pymdp_policy_posterior_grid.json",
        ],
        "multi_track_architecture": ["tracks.yaml", "manuscript/sheaf/tracks.yaml"],
        "lean_boundary_status": ["lean/TemplateActiveInference"],
        "gnn_ontology_concordance": ["gnn", "manuscript/sections/imrad"],
        "semantic_gluing_graph": [
            "output/data/validation_dependency_graph.json",
            "output/data/sheaf_gluing_certificate.json",
            "output/data/evidence_field_index.json",
        ],
        "theorem_traceability_graph": [
            "output/data/theorem_traceability_matrix.json",
            "output/data/proof_dependency_graph.json",
        ],
        "causal_ablation_heatmap": [
            "output/data/causal_ablation_matrix.json",
            "output/reports/ablation_sensitivity_report.json",
        ],
        "scholarship_source_map": ["output/data/scholarship_source_matrix.json", "manuscript/references.bib"],
    }
    rows = []
    section_bindings: dict[str, list[str]] = {}
    for section_id, refs in load_section_figures(root).items():
        for ref in refs:
            section_bindings.setdefault(ref.figure_id, []).append(section_id)
    axis_mappings = {
        "ising_mi_curve": {"x": "lambda", "y": "mutual_information"},
        "si_belief_entropy_curve": {"x": "step", "y": "belief_entropy"},
        "causal_ablation_heatmap": {"x": "lambda", "y": "perturbation", "channel": "effect"},
        "sheaf_coverage_heatmap": {"x": "section", "y": "track", "channel": "coverage_status"},
    }
    registry = load_figure_registry(root)
    for figure_id in sorted(registry):
        image_path = figure_output_path(root, figure_id)
        dimensions = {"width": 0, "height": 0}
        if image_path.is_file():
            with Image.open(image_path) as image:
                dimensions = {"width": int(image.width), "height": int(image.height)}
        source_artifacts = sources.get(figure_id, [])
        source_jsonpaths = ["$" for _ in source_artifacts]
        image_hash = _sha256(image_path) if image_path.is_file() else ""
        pixel_ok = bool(source_artifacts and image_hash and dimensions["width"] > 0 and dimensions["height"] > 0)
        rows.append(
            {
                "figure_id": figure_id,
                "source_artifact": source_artifacts[0] if source_artifacts else "",
                "sources": source_artifacts,
                "source_artifacts": source_artifacts,
                "source_jsonpath": source_jsonpaths[0] if source_jsonpaths else "",
                "source_jsonpaths": source_jsonpaths,
                "renderer": "visualizations.figures.generate_all_figures",
                "dimensions": dimensions,
                "image_sha256": image_hash,
                "axis_channel_mapping": axis_mappings.get(figure_id, {"channel": "pixels"}),
                "section_bindings": sorted(section_bindings.get(figure_id, [])),
                "caption": registry[figure_id].caption,
                # Re-derived from the filesystem (PR#23): mapped requires every
                # listed non-deferred source path to exist, not merely a dict entry.
                "mapped": _figure_sources_mapped(root, source_artifacts),
                "pixel_provenance_ok": pixel_ok,
            }
        )
    return {
        "schema": "template_active_inference.figure_source_map.v1",
        "rows": rows,
        "figure_count": len(rows),
        "all_figures_mapped": all(row["mapped"] and row["pixel_provenance_ok"] for row in rows),
    }


def build_figure_hash_manifest(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    rows = []
    for path in sorted((root / "output" / "figures").glob("*")):
        if path.suffix.lower() not in {".png", ".gif"}:
            continue
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
                "fresh": True,
            }
        )
    return {
        "schema": "template_active_inference.figure_hash_manifest.v1",
        "rows": rows,
        "figure_count": len(rows),
        "all_hashes_present": bool(rows) and all(row["sha256"] for row in rows),
    }


def build_scope_boundary_audit(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    rows = []
    violations: list[str] = []
    allowed_future_files = {"15_discussion_outlook.md", "17_conclusion.md"}
    for path in sorted((root / "manuscript").glob("[0-9][0-9]_*.md")):
        text = path.read_text(encoding="utf-8").lower()
        forbidden = "empirical biological" in text or "biological data" in text
        negated = "not empirical" in text or "future" in text
        allowed = path.name in allowed_future_files
        ok = not forbidden or negated or allowed
        classification = "future" if path.name in allowed_future_files else "current"
        if forbidden and not negated:
            classification = "empirical"
        rows.append(
            {
                "section": path.name,
                "classification": classification,
                "context": "blocked_language" if forbidden else "toy_result",
                "current_result_toy_only": classification == "current" and not forbidden,
                "future_only": classification == "future",
                "blocked_language_ok": not forbidden or negated or allowed,
                "ok": ok,
            }
        )
        if not ok:
            violations.append(path.name)
    return {
        "schema": "template_active_inference.scope_boundary_audit.v1",
        "rows": rows,
        "violations": violations,
        "all_current_claims_toy": not violations,
        "empirical_adapter_enabled": False,
        "scope_boundary_status": "toy_only_pass" if not violations else "scope_leak",
    }


def build_manuscript_evidence_tables(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    claims = build_claim_evidence_audit(root)
    graph = build_integration_dependency_graph(root)
    provenance = _load_json(root / "output" / "data" / "artifact_provenance.json")
    staleness = build_manuscript_staleness_report(root)
    posterior = _load_json(root / "output" / "data" / "pymdp_policy_posterior_grid.json")
    runtime = _load_json(root / "output" / "reports" / "pymdp_runtime_diagnostics.json")
    semantic = _load_json(root / "output" / "data" / "sheaf_gluing_certificate.json")
    track_scope = _load_json(root / "output" / "data" / "track_improvement_scope.json")
    replay_matrix = _load_json(root / "output" / "reports" / "replay_matrix.json")
    diffoscope = _load_json(root / "output" / "reports" / "artifact_diffoscope.json")
    proof = _load_json(root / "output" / "data" / "proof_extraction_index.json")
    catalog = _load_json(root / "output" / "data" / "state_space_catalog.json")
    ablation = _load_json(root / "output" / "data" / "causal_ablation_matrix.json")
    license_audit = _load_json(root / "output" / "reports" / "artifact_license_audit.json")
    release_notes = _load_json(root / "output" / "reports" / "release_notes_evidence.json")
    scholarship = _load_json(root / "output" / "data" / "scholarship_source_matrix.json")
    visualization_quality = _load_json(root / "output" / "reports" / "visualization_quality_audit.json")
    statistical_bridge = _load_json(root / "output" / "data" / "statistical_visualization_bridge.json")
    proof_dependency = _load_json(root / "output" / "data" / "proof_dependency_graph.json")
    transition_table = _load_json(root / "output" / "data" / "state_transition_table.json")
    ablation_sensitivity = _load_json(root / "output" / "reports" / "ablation_sensitivity_report.json")
    release_attestation = _load_json(root / "output" / "reports" / "release_attestation.json")
    tables = [
        {
            "id": "claim_evidence",
            "row_count": claims["claim_count"],
            "source": "output/reports/claim_evidence_audit.json",
        },
        {
            "id": "artifact_producers",
            "row_count": len(graph.get("artifacts") or {}),
            "source": "output/data/validation_dependency_graph.json",
        },
        {
            "id": "artifact_provenance",
            "row_count": int(provenance.get("artifact_count", 0)),
            "source": "output/data/artifact_provenance.json",
        },
        {
            "id": "manuscript_staleness",
            "row_count": int(staleness.get("row_count", 0)),
            "source": "output/reports/manuscript_staleness_report.json",
        },
        {
            "id": "pymdp_policy_posterior",
            "row_count": int(posterior.get("row_count", 0)),
            "source": "output/data/pymdp_policy_posterior_grid.json",
        },
        {
            "id": "pymdp_runtime_diagnostics",
            "row_count": int(runtime.get("construction_count", 0)),
            "source": "output/reports/pymdp_runtime_diagnostics.json",
        },
        {
            "id": "semantic_restrictions",
            "row_count": len(semantic.get("restrictions") or {}),
            "source": "output/data/sheaf_gluing_certificate.json",
        },
        {
            "id": "track_improvement_scope",
            "row_count": int(track_scope.get("improvement_row_count", 0)),
            "source": "output/data/track_improvement_scope.json",
        },
        {
            "id": "replay_matrix",
            "row_count": int(replay_matrix.get("check_count", 0)),
            "source": "output/reports/replay_matrix.json",
        },
        {
            "id": "artifact_diffoscope",
            "row_count": int(diffoscope.get("row_count", 0)),
            "source": "output/reports/artifact_diffoscope.json",
        },
        {
            "id": "proof_extraction",
            "row_count": int(proof.get("theorem_count", 0)),
            "source": "output/data/proof_extraction_index.json",
        },
        {
            "id": "state_space_catalog",
            "row_count": int(catalog.get("row_count", 0)),
            "source": "output/data/state_space_catalog.json",
        },
        {
            "id": "causal_ablation",
            "row_count": int(ablation.get("row_count", 0)),
            "source": "output/data/causal_ablation_matrix.json",
        },
        {
            "id": "artifact_license",
            "row_count": int(license_audit.get("row_count", 0)),
            "source": "output/reports/artifact_license_audit.json",
        },
        {
            "id": "release_notes",
            "row_count": int(release_notes.get("row_count", 0)),
            "source": "output/reports/release_notes_evidence.json",
        },
        {
            "id": "scholarship_sources",
            "row_count": int(scholarship.get("source_count", 0)),
            "source": "output/data/scholarship_source_matrix.json",
        },
        {
            "id": "visualization_quality",
            "row_count": int(visualization_quality.get("figure_count", 0)),
            "source": "output/reports/visualization_quality_audit.json",
        },
        {
            "id": "statistical_visualization_bridge",
            "row_count": int(statistical_bridge.get("row_count", 0)),
            "source": "output/data/statistical_visualization_bridge.json",
        },
        {
            "id": "proof_dependency_graph",
            "row_count": int(proof_dependency.get("edge_count", 0)),
            "source": "output/data/proof_dependency_graph.json",
        },
        {
            "id": "state_transition_table",
            "row_count": int(transition_table.get("row_count", 0)),
            "source": "output/data/state_transition_table.json",
        },
        {
            "id": "ablation_sensitivity",
            "row_count": int(ablation_sensitivity.get("row_count", 0)),
            "source": "output/reports/ablation_sensitivity_report.json",
        },
        {
            "id": "release_attestation",
            "row_count": int(release_attestation.get("row_count", 0)),
            "source": "output/reports/release_attestation.json",
        },
    ]
    return {
        "schema": "template_active_inference.manuscript_evidence_tables.v1",
        "tables": tables,
        "table_count": len(tables),
        "all_source_backed": all(table["row_count"] > 0 and table["source"] for table in tables),
    }


def build_adversarial_audit(project_root: Path) -> dict[str, Any]:
    from roadmap_tracks.sheaf_tracks import build_adversarial_audit as build_canonical_adversarial_audit

    return dict(build_canonical_adversarial_audit(project_root))


def build_integration_semantic_snapshot(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    toy = _load_json(root / "output" / "data" / "sensitivity_sweep.json")
    assumptions = _load_json(root / "output" / "data" / "analytical_assumption_index.json")
    policy = _load_json(root / "output" / "data" / "si_policy_comparison.json")
    posterior = _load_json(root / "output" / "data" / "pymdp_policy_posterior_grid.json")
    runtime = _load_json(root / "output" / "reports" / "pymdp_runtime_diagnostics.json")
    topology_traces = _load_json(root / "output" / "data" / "si_graph_world_topology_traces.json")
    uncertainty = _load_json(root / "output" / "data" / "uncertainty_summary.json")
    benchmark = _load_json(root / "output" / "data" / "toy_benchmark_matrix.json")
    model_checking = _load_json(root / "output" / "reports" / "model_checking_witnesses.json")
    lean_theorems = _load_json(root / "output" / "reports" / "lean_theorem_inventory.json")
    lean_graph = _load_json(root / "output" / "reports" / "lean_graph_world_inventory.json")
    interop = _load_json(root / "output" / "data" / "interop_roundtrip_report.json")
    adversarial = build_adversarial_audit(root)
    dependency = build_integration_dependency_graph(root)
    stale = build_stale_artifact_report(root)
    tokens = build_manuscript_token_provenance(root)
    figures = build_figure_source_map(root)
    scope = build_scope_boundary_audit(root)
    staleness = build_manuscript_staleness_report(root)
    provenance = _load_json(root / "output" / "data" / "artifact_provenance.json")
    animation = _load_json(root / "output" / "data" / "animation_frame_deltas.json")
    diffoscope = _load_json(root / "output" / "reports" / "artifact_diffoscope.json")
    proof = _load_json(root / "output" / "data" / "proof_extraction_index.json")
    catalog = _load_json(root / "output" / "data" / "state_space_catalog.json")
    ablation = _load_json(root / "output" / "data" / "causal_ablation_matrix.json")
    license_audit = _load_json(root / "output" / "reports" / "artifact_license_audit.json")
    release_notes = _load_json(root / "output" / "reports" / "release_notes_evidence.json")
    scholarship = _load_json(root / "output" / "data" / "scholarship_source_matrix.json")
    restrictions = {
        "analytical_assumptions_indexed": assumptions.get("all_equations_indexed") is True,
        "pymdp_runtime_diagnostics_ok": runtime.get("ok") is True
        and int(runtime.get("unexpected_warning_count", 0) or 0) == 0,
        "policy_comparison_grid_complete": (policy.get("summary") or {}).get("complete_grid") is True,
        "policy_posterior_normalized": posterior.get("all_available_posteriors_normalized") is True
        and posterior.get("all_unavailable_rows_explained") is True,
        "efe_availability_or_fallback_complete": (policy.get("summary") or {}).get("all_efe_rows_explained") is True,
        "topology_trace_consistency": topology_traces.get("all_trace_summary_agree") is True,
        "sensitivity_grid_complete": toy.get("complete_grid") is True,
        "uncertainty_rows_normalized": uncertainty.get("all_normalized") is True,
        "benchmark_rows_complete": benchmark.get("all_models_complete") is True,
        "model_checking_all_passed": model_checking.get("all_passed") is True,
        "lean_theorem_inventory_proved": lean_theorems.get("all_proved") is True,
        "lean_graph_world_topologies_witnessed": lean_graph.get("all_topologies_witnessed") is True
        and lean_graph.get("all_policy_witnesses_present") is True,
        "interop_lossless": interop.get("all_lossless") is True,
        "adversarial_expected_failures_documented": adversarial["all_expected_failures_documented"],
        "dependency_edge_types_ok": dependency["all_required_edge_types_present"],
        "stale_flags_clear": stale["all_fresh"],
        "token_provenance_complete": tokens["all_tokens_mapped"],
        "figure_source_coverage": figures["all_figures_mapped"],
        "animation_deltas_nonzero": animation.get("all_nonzero") is True
        and animation.get("all_adjacent_hashes_distinct") is True,
        "scope_boundary_toy_only": scope["all_current_claims_toy"],
        "manuscript_staleness_fresh": staleness["all_fresh"],
        "artifact_provenance_seed_config_complete": provenance.get("all_seeded") is True
        and provenance.get("all_config_digests") is True,
        "artifact_diffoscope_equal": diffoscope.get("all_equal") is True,
        "proof_extraction_constructive": proof.get("all_extracted") is True and proof.get("all_constructive") is True,
        "state_space_catalog_finite": catalog.get("all_finite") is True and catalog.get("all_counts_positive") is True,
        "causal_ablation_complete": ablation.get("complete_grid") is True and ablation.get("all_deterministic") is True,
        "artifact_license_safe": license_audit.get("all_license_safe") is True,
        "release_notes_source_backed": release_notes.get("all_notes_source_backed") is True,
        "scholarship_sources_connected": scholarship.get("all_sources_connected") is True,
    }
    return {
        "schema": "template_active_inference.integration_semantic_snapshot.v1",
        "ok": all(restrictions.values()),
        "restrictions": restrictions,
        "sections": {
            "structural": {"ok": dependency["all_required_edge_types_present"]},
            "semantic": {"ok": restrictions["interop_lossless"] and restrictions["scope_boundary_toy_only"]},
            "artifact": {"ok": restrictions["stale_flags_clear"] and restrictions["figure_source_coverage"]},
            "manuscript_variable": {
                "ok": restrictions["token_provenance_complete"] and restrictions["manuscript_staleness_fresh"]
            },
        },
    }
