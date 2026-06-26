"""Gold Refinement exemplar — metallurgical manuscript composition.

Maps gold-refining stages (ore → smelting → assaying → cupellation →
certification) onto scientific manuscript purity with mega-madlib token
injection. The refinery is a load-bearing pipeline: each stage maps to
a real template-infrastructure operation.
"""

from .composition import TokenChoice, TokenPlan, generate_token_plan
from .config import (
    GoldRefinementConfig,
    GoldRefinementConfigError,
    SlotSpec,
    load_gold_refinement_config,
)
from .dashboard import build_dashboard_html, write_dashboard
from .evidence import (
    EvidenceEntry,
    EvidenceRegistry,
    build_evidence_registry,
    check_claim_ledger_alignment,
    write_evidence_registry,
)
from .figures import (
    FIGURE_SPECS,
    FigureSpec,
    build_claim_evidence_topology,
    build_formalism_traceability_graph,
    build_implementation_circuit_graph,
    build_provenance_flow_graph,
    figure_registry_payload,
    generate_all_figures,
    generate_claim_evidence_assay,
    generate_evidence_tier_ladder,
    generate_formalism_traceability,
    generate_implementation_circuit,
    generate_integrity_gate_matrix,
    generate_integrity_risk_matrix,
    generate_karat_grading_chart,
    generate_provenance_sankey,
    generate_purity_claim_scatter,
    generate_purity_progression,
    generate_token_density_chart,
    generate_token_heatmap,
    purity_nines_values,
    write_figure_quality_report,
    write_figure_registry,
)
from .formalisms import (
    FORMALISMS,
    Formalism,
    equation_labels,
    formalism_count,
    formalism_equation_blocks,
    formalism_records,
    formalism_table_rows,
    formalism_traceability_rows,
)
from .integrity import (
    EvidenceTier,
    IntegrityDimension,
    build_evidence_tiers,
    build_integrity_dimensions,
    evidence_tier_records,
    evidence_tier_table_rows,
    integrity_dimension_table_rows,
    integrity_owner_table_rows,
    integrity_records,
    integrity_summary_line,
)
from .purity import (
    KARAT_GRADES,
    NINE_NINES_PURITY,
    KaratGrade,
    format_purity,
    karat_for_purity,
    purity_to_nines,
)
from .refinery import (
    CANONICAL_STAGES,
    RefinementStage,
    RefineryResult,
    run_refinery,
    stage_by_name,
    stage_by_order,
)
from .assay import (
    AssayReport,
    ClaimRecord,
    assay_claims,
    compute_assay_purity,
)

__all__ = [
    # Refinery
    "CANONICAL_STAGES",
    "RefinementStage",
    "RefineryResult",
    "run_refinery",
    "stage_by_name",
    "stage_by_order",
    # Purity
    "KARAT_GRADES",
    "NINE_NINES_PURITY",
    "KaratGrade",
    "format_purity",
    "karat_for_purity",
    "purity_to_nines",
    # Config
    "GoldRefinementConfig",
    "GoldRefinementConfigError",
    "SlotSpec",
    "load_gold_refinement_config",
    # Composition
    "TokenChoice",
    "TokenPlan",
    "generate_token_plan",
    # Assay
    "AssayReport",
    "ClaimRecord",
    "assay_claims",
    "compute_assay_purity",
    # Figures
    "FIGURE_SPECS",
    "FigureSpec",
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
    "FORMALISMS",
    "Formalism",
    "equation_labels",
    "formalism_count",
    "formalism_equation_blocks",
    "formalism_records",
    "formalism_table_rows",
    "formalism_traceability_rows",
    "EvidenceTier",
    "IntegrityDimension",
    "build_evidence_tiers",
    "build_integrity_dimensions",
    "evidence_tier_records",
    "evidence_tier_table_rows",
    "integrity_dimension_table_rows",
    "integrity_owner_table_rows",
    "integrity_records",
    "integrity_summary_line",
    # Evidence
    "EvidenceEntry",
    "EvidenceRegistry",
    "build_evidence_registry",
    "check_claim_ledger_alignment",
    "write_evidence_registry",
    # Dashboard
    "build_dashboard_html",
    "write_dashboard",
]
