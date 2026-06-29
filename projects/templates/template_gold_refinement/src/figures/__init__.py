"""Figure generation for the gold-refinement exemplar.

Generates publication-quality figures from refinery data using matplotlib.
All figures are deterministic (fixed seeds, no RNG) and headless-safe
(MPLBACKEND=Agg set in tests and pipeline).

This package replaces the former single-file ``figures.py`` module. It is split
into focused submodules — :mod:`._common` (shared infrastructure, specs, and
helpers), :mod:`.graphs` (directed-graph builders), :mod:`.charts` (bar/line
charts), :mod:`.diagrams` (graph and matrix diagrams), and :mod:`.registry`
(registry, quality report, and the all-figures orchestrator) — while preserving
the exact public API the monolith exported.
"""

from __future__ import annotations

from ._common import (
    FIGURE_SPECS,
    FigureSpec,
    STAGE_COLORS,
    STAGE_LABELS,
    purity_nines_values,
)
from .charts import (
    generate_karat_grading_chart,
    generate_purity_progression,
    generate_token_density_chart,
)
from .diagrams import (
    generate_claim_evidence_assay,
    generate_evidence_tier_ladder,
    generate_formalism_traceability,
    generate_implementation_circuit,
    generate_integrity_gate_matrix,
    generate_integrity_risk_matrix,
    generate_provenance_sankey,
    generate_purity_claim_scatter,
    generate_token_heatmap,
)
from .graphs import (
    build_claim_evidence_topology,
    build_formalism_traceability_graph,
    build_implementation_circuit_graph,
    build_provenance_flow_graph,
)
from .registry import (
    figure_registry_payload,
    generate_all_figures,
    write_figure_quality_report,
    write_figure_registry,
)

__all__ = [
    "FIGURE_SPECS",
    "FigureSpec",
    "STAGE_COLORS",
    "STAGE_LABELS",
    "build_claim_evidence_topology",
    "build_formalism_traceability_graph",
    "build_implementation_circuit_graph",
    "build_provenance_flow_graph",
    "figure_registry_payload",
    "generate_all_figures",
    "generate_claim_evidence_assay",
    "generate_evidence_tier_ladder",
    "generate_formalism_traceability",
    "generate_implementation_circuit",
    "generate_integrity_gate_matrix",
    "generate_integrity_risk_matrix",
    "generate_karat_grading_chart",
    "generate_provenance_sankey",
    "generate_purity_claim_scatter",
    "generate_purity_progression",
    "generate_token_density_chart",
    "generate_token_heatmap",
    "purity_nines_values",
    "write_figure_quality_report",
    "write_figure_registry",
]
