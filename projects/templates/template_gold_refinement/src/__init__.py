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
    generate_all_figures,
    generate_karat_grading_chart,
    generate_provenance_sankey,
    generate_purity_claim_scatter,
    generate_purity_progression,
    generate_token_density_chart,
    generate_token_heatmap,
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
    "generate_all_figures",
    "generate_karat_grading_chart",
    "generate_provenance_sankey",
    "generate_purity_claim_scatter",
    "generate_purity_progression",
    "generate_token_density_chart",
    "generate_token_heatmap",
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
