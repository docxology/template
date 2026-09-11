"""AutoResearch loop orchestration: typed configuration, task-agnostic
adapter registry, defensive JSON coercion, result models, ordered phase
helpers, phase-ledger payloads, and the top-level deterministic loop.

These modules are re-exported from ``template_autoresearch_project`` for
the public loop surface; import them from the package root or directly
from ``template_autoresearch_project.loop.<module>``.
"""

from .adapters import (
    ADAPTER_RESULT_SCHEMA,
    AdapterResult,
    available_adapters,
    run_quadratic_adapter,
)
from .config import (
    AutoResearchLoopConfig,
    HumanReviewState,
    ManuscriptLoopSettings,
    ResearchQuestion,
    build_loop_config,
    load_experiment_candidates,
    load_human_review,
    load_loop_config,
    load_manuscript_loop_settings,
    load_seed_ideas,
)
from .json_coerce import mapping, mapping_list
from .models import (
    AutoResearchClaim,
    AutoResearchLoopResult,
    LoopStageResult,
)
from .phase_ledger import (
    PHASE_LEDGER_SCHEMA,
    phase_ledger_payload,
    write_phase_ledger,
)
from .loop_phases import (
    LoopRunContext,
    PRE_EXTRINSIC_PHASES,
    append_paths,
    build_loop_context,
    combine_readiness_reports,
    final_output_path_payload,
    only_changed_artifact_manifest_issues,
    resolve_extrinsic_readiness,
    run_final_payload_and_visual_phase,
    run_method_contract_phase,
    run_post_readiness_final_phases,
    run_pre_extrinsic_phases,
    run_pre_readiness_settlement_phase,
    run_pre_readiness_visual_phase,
    run_provisional_payload_phase,
    run_settlement_manifest_phase,
    write_readiness_manifest,
)
from .loop import (
    build_claims,
    build_stage_results,
    run_autoresearch_loop,
)

__all__ = [
    "ADAPTER_RESULT_SCHEMA",
    "AdapterResult",
    "AutoResearchClaim",
    "AutoResearchLoopConfig",
    "AutoResearchLoopResult",
    "LoopRunContext",
    "LoopStageResult",
    "PHASE_LEDGER_SCHEMA",
    "PRE_EXTRINSIC_PHASES",
    "HumanReviewState",
    "ManuscriptLoopSettings",
    "ResearchQuestion",
    "append_paths",
    "available_adapters",
    "build_claims",
    "build_loop_config",
    "build_loop_context",
    "build_stage_results",
    "combine_readiness_reports",
    "final_output_path_payload",
    "load_experiment_candidates",
    "load_human_review",
    "load_loop_config",
    "load_manuscript_loop_settings",
    "load_seed_ideas",
    "mapping",
    "mapping_list",
    "only_changed_artifact_manifest_issues",
    "phase_ledger_payload",
    "resolve_extrinsic_readiness",
    "run_autoresearch_loop",
    "run_final_payload_and_visual_phase",
    "run_method_contract_phase",
    "run_post_readiness_final_phases",
    "run_pre_extrinsic_phases",
    "run_pre_readiness_settlement_phase",
    "run_pre_readiness_visual_phase",
    "run_provisional_payload_phase",
    "run_quadratic_adapter",
    "run_settlement_manifest_phase",
    "write_phase_ledger",
    "write_readiness_manifest",
]
