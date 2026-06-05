"""Figure source-provenance map for canonical sheaf-track gates.

Extracted from ``integration_audit.py`` to keep that module within the
composability line-count budget. ``mapped`` is re-derived from the filesystem
(verifier-first) rather than trusting a hardcoded flag: a figure is mapped only
when it has at least one source and every listed source-code path exists.
``output/**`` artifact paths are deferred (produced later in the pipeline).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _is_deferred_source(rel: str) -> bool:
    """Pipeline-produced artifacts that do not exist at map-build time.

    output/** paths (data, reports, figures) are generated later in the pipeline, so
    requiring them on a clean tree would falsely report unmapped figures. They are
    deferred — their existence is verified by the freshness/stale-artifact validators.
    """
    normalized = rel.replace("\\", "/").lstrip("./")
    return normalized.startswith("output/")


def _source_path_exists(root: Path, rel: str) -> bool:
    """A listed source-code path must resolve to a real file or directory on disk."""
    return (root / rel).exists()


def _figure_sources_mapped(root: Path, figure_sources: list[str]) -> bool:
    """Re-derive `mapped` from the filesystem rather than trusting the hardcoded dict.

    A figure is mapped only when it has at least one source AND every listed
    source-code path (src/**, *.yaml, *.bib, lean/**, gnn/**, manuscript/**, etc.)
    exists. output/** artifact paths are deferred (produced later in the pipeline).
    """
    if not figure_sources:
        return False
    for rel in figure_sources:
        if _is_deferred_source(rel):
            continue
        if not _source_path_exists(root, rel):
            return False
    return True


def build_figure_source_map(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()
    from visualizations.figure_registry import load_figure_registry

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
    for figure_id in sorted(load_figure_registry(root)):
        figure_sources = sources.get(figure_id, [])
        rows.append(
            {
                "figure_id": figure_id,
                "sources": figure_sources,
                "mapped": _figure_sources_mapped(root, figure_sources),
            }
        )
    return {
        "schema": "template_active_inference.figure_source_map.v1",
        "rows": rows,
        "figure_count": len(rows),
        "all_figures_mapped": bool(rows) and all(row["mapped"] for row in rows),
    }
