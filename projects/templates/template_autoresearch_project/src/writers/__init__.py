"""Artifact writers for the AutoResearch loop."""

from __future__ import annotations

from .benchmark import (
    _BENCHMARK_CORE_ARTIFACTS,
    _GradingSettings,
    _benchmark_score,
    _grade_absent_benchmark,
    _load_grading_settings,
    _ml_accuracy_improved,
    _write_benchmark_grading_reports,
)
from .figure_artifacts import (
    build_figure_render_context,
    write_final_visual_artifacts,
    write_loop_bound_figures,
)
from .figure_dispatch import (
    FIGURE_DISPATCH,
    FigureDispatchEntry,
    FigureRenderContext,
    render_all_figures,
    render_figure_batch,
    render_security_figures,
)
from .io import relative_path, write_json, write_text
from .loop_artifacts import write_core_loop_artifacts, write_method_contract_artifacts
from .manifests import (
    write_artifact_manifest,
    write_autoresearch_phase_ledger,
    write_research_object_manifest,
    write_schema_manifest,
)
from .ml_artifacts import write_ml_task_artifacts
from .payloads import (
    finalize_loop_payloads,
    refresh_loop_payloads,
    update_result_payloads,
    write_loop_payloads,
)

__all__ = [
    "FIGURE_DISPATCH",
    "FigureDispatchEntry",
    "FigureRenderContext",
    "_BENCHMARK_CORE_ARTIFACTS",
    "_GradingSettings",
    "_benchmark_score",
    "_grade_absent_benchmark",
    "_load_grading_settings",
    "_ml_accuracy_improved",
    "_write_benchmark_grading_reports",
    "build_figure_render_context",
    "finalize_loop_payloads",
    "refresh_loop_payloads",
    "relative_path",
    "render_all_figures",
    "render_figure_batch",
    "render_security_figures",
    "update_result_payloads",
    "write_artifact_manifest",
    "write_autoresearch_phase_ledger",
    "write_core_loop_artifacts",
    "write_final_visual_artifacts",
    "write_json",
    "write_loop_bound_figures",
    "write_loop_payloads",
    "write_method_contract_artifacts",
    "write_ml_task_artifacts",
    "write_research_object_manifest",
    "write_schema_manifest",
    "write_text",
]
