"""Figure source-map and hash-manifest builders for integration audits."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .figure_provenance import _figure_sources_mapped
from .integration_audit_builders import _sha256
from .integration_audit_lanes import claim_lane_summary, figure_claim_lanes, manifest_tracks_by_section


def build_figure_source_map(project_root: Path) -> dict[str, Any]:
    """Map rendered figures to source artifacts, section bindings, and claim lanes."""
    root = project_root.resolve()
    from visualizations.figure_registry import figure_output_path, load_figure_registry, load_section_figures
    from visualizations.figure_io import image_render_metrics

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
        "track_lane_promotion_map": [
            "output/data/track_lane_matrix.json",
            "lean/TemplateActiveInference/PromotionProof.lean",
        ],
        "artifact_contract_map": [
            "output/data/artifact_contract_index.json",
            "output/reports/release_bundle_manifest.json",
            "output/data/artifact_provenance.json",
            "output/reports/security_posture_audit.json",
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
        "security_posture_map": [
            "output/reports/security_posture_audit.json",
            "output/reports/blocked_scope_manifest.json",
        ],
    }
    rows = []
    section_bindings: dict[str, list[str]] = {}
    for section_id, refs in load_section_figures(root).items():
        for ref in refs:
            section_bindings.setdefault(ref.figure_id, []).append(section_id)
    section_tracks = manifest_tracks_by_section(root)
    axis_mappings = {
        "ising_mi_curve": {"x": "lambda", "y": "mutual_information"},
        "si_belief_entropy_curve": {"x": "step", "y": "belief_entropy"},
        "causal_ablation_heatmap": {"x": "lambda", "y": "perturbation", "channel": "effect"},
        "sheaf_coverage_heatmap": {"x": "section", "y": "track", "channel": "coverage_status"},
        "track_lane_promotion_map": {"x": "promotion_requirement", "y": "pipeline_track", "channel": "status"},
        "artifact_contract_map": {"x": "contract_obligation", "y": "artifact", "channel": "status"},
        "security_posture_map": {"x": "security_evidence", "y": "control", "channel": "status"},
    }
    registry = load_figure_registry(root)
    for figure_id in sorted(registry):
        image_path = figure_output_path(root, figure_id)
        metrics = image_render_metrics(image_path)
        dimensions = {"width": int(metrics["width_px"]), "height": int(metrics["height_px"])}
        source_artifacts = sources.get(figure_id, [])
        source_jsonpaths = ["$" for _ in source_artifacts]
        image_hash = _sha256(image_path) if image_path.is_file() else ""
        pixel_ok = bool(
            source_artifacts
            and image_hash
            and dimensions["width"] > 0
            and dimensions["height"] > 0
            and metrics["nonblank"]
        )
        bound_sections = sorted(section_bindings.get(figure_id, []))
        bound_tracks = sorted({track for section_id in bound_sections for track in section_tracks.get(section_id, [])})
        source_claim_lanes = figure_claim_lanes(source_artifacts, (), registry[figure_id].evidence_role)
        section_claim_lanes = figure_claim_lanes([], bound_tracks, "")
        claim_lanes = source_claim_lanes or section_claim_lanes
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
                "section_bindings": bound_sections,
                "section_tracks": bound_tracks,
                "source_claim_lanes": source_claim_lanes,
                "section_claim_lanes": section_claim_lanes,
                "claim_lanes": claim_lanes,
                "claim_lane_count": len(claim_lanes),
                "caption": registry[figure_id].caption,
                "mapped": _figure_sources_mapped(root, source_artifacts),
                "pixel_provenance_ok": pixel_ok,
            }
        )
    lane_summary = claim_lane_summary(rows)
    return {
        "schema": "template_active_inference.figure_source_map.v1",
        "rows": rows,
        "figure_count": len(rows),
        "all_figures_mapped": all(row["mapped"] and row["pixel_provenance_ok"] for row in rows),
        **lane_summary,
    }


def build_figure_hash_manifest(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    rows = []
    for path in sorted((root / "output" / "figures").glob("*")):
        if path.name.startswith("."):
            continue
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


__all__ = ["build_figure_hash_manifest", "build_figure_source_map"]
