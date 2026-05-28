"""Artifact writers for the AutoResearch loop."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infrastructure.autoresearch import ResearchProgram, RunLedger
from infrastructure.core.pipeline.artifacts import ArtifactManifest, ArtifactManifestEntry, compute_sha256

from . import figures_process
from .artifact_schemas import schema_manifest_payload
from .config import AutoResearchLoopConfig, load_experiment_candidates, load_seed_ideas
from .diagnostics import diagnostic_bundle
from .figure_quality import write_figure_quality_report
from .figure_registry import figure_registry_payload
from .figure_style import apply_style, load_figure_style
from .manuscript_variables import compute_variables_from_payload, save_variables
from .ml_task import MLTaskResult, write_confusion_matrix_csv, write_error_examples_json, write_training_history_csv
from .models import AutoResearchLoopResult, LoopStageResult
from .phase_ledger import write_phase_ledger
from .reports import (
    build_review_packet,
    render_ml_experiment_report,
    render_loop_markdown,
    render_review_packet_markdown,
    render_stage_matrix_csv,
    render_summary_markdown,
)
from .research_object import research_object_manifest_payload
from .writers_benchmark import (
    _BENCHMARK_CORE_ARTIFACTS,
    _GradingSettings,
    _benchmark_score,
    _grade_absent_benchmark,
    _load_grading_settings,
    _ml_accuracy_improved,
    _write_benchmark_grading_reports,
)
from .writers_figure_dispatch import (
    FigureDispatchEntry,
    FigureRenderContext,
    FIGURE_DISPATCH,
    render_all_figures,
    render_figure_batch,
)

_ALWAYS_MANIFEST_EXCLUSIONS = frozenset(
    {
        "output/figures/autoresearch_stage_matrix.png",
        "output/figures/figure_registry.json",
        "output/reports/autoresearch_loop.md",
        "output/reports/autoresearch_readiness.json",
        "output/reports/autoresearch_readiness.md",
        "output/reports/evidence_registry.json",
    }
)
_VOLATILE_LOOP_STATE_ARTIFACTS = frozenset(
    {
        "output/data/autoresearch_loop.json",
        "output/data/autoresearch_review_packet.json",
        "output/data/manuscript_variables.json",
        "output/figures/autoresearch_stage_matrix.png",
        "output/reports/autoresearch_loop.json",
        "output/reports/autoresearch_loop.md",
        "output/reports/autoresearch_review_packet.md",
        "output/reports/autoresearch_summary.md",
    }
)

__all__ = [
    "FIGURE_DISPATCH",
    "FigureDispatchEntry",
    "FigureRenderContext",
    "_BENCHMARK_CORE_ARTIFACTS",
    "_GradingSettings",
    "_grade_absent_benchmark",
    "_load_grading_settings",
    "_ml_accuracy_improved",
    "build_figure_render_context",
    "finalize_loop_payloads",
    "refresh_loop_payloads",
    "relative_path",
    "render_all_figures",
    "render_figure_batch",
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


def write_json(path: Path, payload: object) -> Path:
    """Write JSON payload to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_text(path: Path, text: str) -> Path:
    """Write text payload to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def build_figure_render_context(
    project_root: Path,
    ml_result: MLTaskResult,
    *,
    loop_result: AutoResearchLoopResult | None = None,
    diagnostics: dict[str, Any] | None = None,
) -> FigureRenderContext:
    """Build figure render context, computing diagnostics at most once per ML result."""
    figures_dir = project_root / "output" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    resolved = diagnostics if diagnostics is not None else diagnostic_bundle(project_root, ml_result)
    return FigureRenderContext(
        project_root=project_root,
        figures_dir=figures_dir,
        loop_result=loop_result,
        ml_result=ml_result,
        diagnostics=resolved,
    )


def relative_path(project_root: Path, path: Path) -> str:
    """Return a project-relative path string when possible."""
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def write_artifact_manifest(
    project_root: Path,
    paths: list[Path],
    *,
    exclude_volatile: bool = False,
) -> Path:
    """Write the artifact manifest for declared loop outputs."""
    manifest_path = (project_root / "output" / "reports" / "artifact_manifest.json").resolve()
    entries = []
    for index, path in enumerate(
        sorted(
            {
                path.resolve()
                for path in paths
                if path.exists()
                and path.resolve() != manifest_path
                and relative_path(project_root, path) not in _ALWAYS_MANIFEST_EXCLUSIONS
                and (not exclude_volatile or relative_path(project_root, path) not in _VOLATILE_LOOP_STATE_ARTIFACTS)
            }
        ),
        start=1,
    ):
        entries.append(
            ArtifactManifestEntry(
                path=relative_path(project_root, path),
                size_bytes=path.stat().st_size,
                sha256=compute_sha256(path),
                stage_num=index,
                stage_name="AutoResearch loop",
                contract_match=True,
            )
        )
    manifest = ArtifactManifest(entries=tuple(entries), issues=())
    return write_json(manifest_path, manifest.to_dict())


def write_core_loop_artifacts(
    project_root: Path,
    plan_payload: dict[str, Any],
    config: AutoResearchLoopConfig,
    stage_results: tuple[LoopStageResult, ...],
    generated_at: str,
    project_name: str,
) -> list[Path]:
    """Write plan, loop markdown, figure, and stage matrix before readiness is known."""
    output = project_root / "output"
    data_dir = output / "data"
    reports_dir = output / "reports"
    figures_dir = output / "figures"
    for directory in (data_dir, reports_dir, figures_dir):
        directory.mkdir(parents=True, exist_ok=True)

    provisional = AutoResearchLoopResult(
        project_name=project_name,
        generated_at=generated_at,
        config=config,
        stage_results=stage_results,
        claims=(),
        readiness_valid=False,
        output_paths=(),
    )
    style = load_figure_style(project_root)
    with apply_style(style):
        figure_path = figures_process.write_stage_matrix_figure(figures_dir, provisional)
    return [
        write_json(data_dir / "autoresearch_plan.json", plan_payload),
        write_text(reports_dir / "autoresearch_loop.md", render_loop_markdown(provisional)),
        write_text(data_dir / "autoresearch_stage_matrix.csv", render_stage_matrix_csv(provisional)),
        figure_path,
        write_json(figures_dir / "figure_registry.json", figure_registry_payload(provisional)),
    ]


def write_method_contract_artifacts(
    project_root: Path,
    config: AutoResearchLoopConfig,
    *,
    generated_at: str,
    ml_result: MLTaskResult | None = None,
) -> list[Path]:
    """Write bounded-loop method artifacts used by readiness validation."""
    output = project_root / "output"
    data_dir = output / "data"
    reports_dir = output / "reports"
    data_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    program = ResearchProgram(
        path="program.md",
        summary=_program_summary(project_root),
        autonomy_level=config.autonomy_level,
        budget_policy=config.budget_policy,
        edit_allowlist=config.edit_allowlist,
    )
    ideas = load_seed_ideas(project_root)
    candidates = load_experiment_candidates(project_root)
    iterations_used = (
        ml_result.evaluated_candidate_count if ml_result is not None else config.budget_policy.max_iterations
    )
    budget_exhausted = bool(ml_result.budget_exhausted) if ml_result is not None else True
    run_ledger = RunLedger(
        budget_policy=config.budget_policy,
        iterations_used=iterations_used,
        wall_clock_minutes_used=0,
        llm_calls_used=0,
        cost_usd_used=0.0,
        budget_exhausted=budget_exhausted,
        exhaustion_reason="candidate iteration budget reached"
        if budget_exhausted
        else "candidate loop completed within budget",
    )
    review_decisions = {
        "schema": "template-autoresearch-review-decisions-v1",
        "generated_at": generated_at,
        "publication_approved": config.human_review.publication_approved,
        "human_review_source": config.human_review.source_path,
        "human_review_source_exists": config.human_review.source_exists,
        "decisions": [
            {
                "gate": gate.name,
                "required": gate.required,
                "decision": config.human_review.decisions.get(gate.name, "deferred"),
                "rationale": "Decision is read from human_review.yaml when present; generated readiness is not approval.",
            }
            for gate in config.review_gates
        ],
    }
    benchmark_report_paths = _write_benchmark_grading_reports(project_root, config)
    benchmark_scores = {
        "generated_at": generated_at,
        "tasks": [
            {
                "id": task.identifier,
                "description": task.description,
                "grading_output_path": task.grading_output,
                "status": "graded" if (project_root / task.grading_output).exists() else "missing",
                "score": _benchmark_score(project_root / task.grading_output),
            }
            for task in config.benchmark_tasks
        ],
        "task_count": len(config.benchmark_tasks),
    }

    paths = [
        write_json(data_dir / "research_program.json", program.to_dict()),
        write_json(
            data_dir / "idea_ledger.json",
            {
                "generated_at": generated_at,
                "ideas": [idea.to_dict() for idea in ideas],
                "candidates": [candidate.to_dict() for candidate in candidates],
            },
        ),
        write_json(data_dir / "run_ledger.json", run_ledger.to_dict()),
        write_json(data_dir / "review_decisions.json", review_decisions),
        write_json(data_dir / "benchmark_scores.json", benchmark_scores),
    ]
    paths.extend(benchmark_report_paths)
    return paths


def write_ml_task_artifacts(project_root: Path, result: MLTaskResult, *, generated_at: str) -> list[Path]:
    """Write deterministic ML task artifacts."""
    output = project_root / "output"
    data_dir = output / "data"
    reports_dir = output / "reports"
    figures_dir = output / "figures"
    for directory in (data_dir, reports_dir, figures_dir):
        directory.mkdir(parents=True, exist_ok=True)

    candidate_ledger = {
        "generated_at": generated_at,
        "objective": {
            "metric": result.task_config.metric_name,
            "direction": result.task_config.metric_direction,
        },
        "budget": {
            "candidate_count": result.candidate_count,
            "evaluated_candidate_count": result.evaluated_candidate_count,
            "budget_exhausted": result.budget_exhausted,
            "llm_calls_used": result.llm_calls_used,
            "cost_usd_used": result.cost_usd_used,
        },
        "baseline": result.baseline.to_dict(),
        "accepted_candidate_id": result.accepted_candidate_id,
        "candidates": [candidate.to_dict() for candidate in result.candidates],
    }
    benchmark_score = {
        "id": "ml-loop-score",
        "description": "Grade bounded ML-loop metric improvement, budget compliance, and offline execution.",
        "score": result.benchmark_score,
        "status": "graded",
        "evidence": {
            "results": "output/data/ml_task_results.json",
            "candidate_ledger": "output/data/ml_candidate_ledger.json",
            "accepted_candidate_id": result.accepted_candidate_id,
            "accuracy_delta": round(result.accuracy_delta, 6),
        },
    }
    diagnostics = diagnostic_bundle(project_root, result)
    registry_payload = figure_registry_payload(ml_result=result)
    figure_ctx = build_figure_render_context(project_root, result, diagnostics=diagnostics)

    style = load_figure_style(project_root)
    with apply_style(style):
        artifacts = [
            write_json(data_dir / "figure_style.json", {"generated_at": generated_at, **style.to_dict()}),
            write_json(data_dir / "mnist_task_config.json", result.task_config.to_dict()),
            write_json(data_dir / "ml_task_results.json", result.to_dict()),
            write_json(data_dir / "ml_candidate_ledger.json", candidate_ledger),
            write_confusion_matrix_csv(
                data_dir / "ml_confusion_matrix.csv", result.accepted_candidate.confusion_matrix
            ),
            write_training_history_csv(data_dir / "ml_training_history.csv", result),
            write_error_examples_json(data_dir / "ml_error_examples.json", project_root, result),
            write_json(data_dir / "ml_prediction_records.json", diagnostics["prediction_records"]),
            write_json(data_dir / "ml_classification_diagnostics.json", diagnostics["classification_diagnostics"]),
            write_json(data_dir / "ml_candidate_intervals.json", diagnostics["candidate_intervals"]),
            write_json(data_dir / "ml_class_balance.json", diagnostics["class_balance"]),
            write_json(data_dir / "ml_calibration_report.json", diagnostics["calibration_report"]),
            write_json(data_dir / "ml_calibration_bin_intervals.json", diagnostics["calibration_bin_intervals"]),
            write_json(data_dir / "ml_robustness_report.json", diagnostics["robustness_report"]),
            write_json(data_dir / "ml_probability_diagnostics.json", diagnostics["probability_diagnostics"]),
            write_json(data_dir / "ml_bootstrap_intervals.json", diagnostics["bootstrap_intervals"]),
            write_json(data_dir / "ml_paired_comparison.json", diagnostics["paired_comparison"]),
            write_json(data_dir / "ml_statistical_summary.json", diagnostics["statistical_summary"]),
            write_json(data_dir / "ml_training_diagnostics.json", diagnostics["training_diagnostics"]),
            write_json(data_dir / "ml_candidate_rank_stability.json", diagnostics["candidate_rank_stability"]),
            write_json(data_dir / "ml_candidate_selection_audit.json", diagnostics["candidate_selection_audit"]),
            write_json(data_dir / "ml_diagnostic_boundary.json", diagnostics["diagnostic_boundary"]),
            write_text(reports_dir / "ml_experiment_report.md", render_ml_experiment_report(result)),
            write_json(reports_dir / "ml_benchmark_score.json", benchmark_score),
            *render_figure_batch(figure_ctx, include_loop_only=False),
            write_json(figures_dir / "figure_registry.json", registry_payload),
            write_figure_quality_report(
                data_dir / "figure_quality_report.json",
                project_root,
                registry_payload,
                generated_at=generated_at,
            ),
        ]
    return artifacts


def write_loop_bound_figures(
    project_root: Path,
    result: AutoResearchLoopResult,
    ml_result: MLTaskResult,
    *,
    diagnostics: dict[str, Any] | None = None,
) -> list[Path]:
    """Render loop-state figures that depend on claims and readiness payloads."""
    figure_ctx = build_figure_render_context(project_root, ml_result, loop_result=result, diagnostics=diagnostics)
    style = load_figure_style(project_root)
    with apply_style(style):
        return render_figure_batch(figure_ctx, include_loop_only=True)


def write_final_visual_artifacts(
    project_root: Path,
    result: AutoResearchLoopResult,
    ml_result: MLTaskResult,
    *,
    diagnostics: dict[str, Any] | None = None,
) -> list[Path]:
    """Refresh all figures, registry metadata, and figure-quality validation."""
    data_dir = project_root / "output" / "data"
    figures_dir = project_root / "output" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    resolved = diagnostics if diagnostics is not None else diagnostic_bundle(project_root, ml_result)
    registry_payload = figure_registry_payload(result, ml_result)
    figure_ctx = build_figure_render_context(project_root, ml_result, loop_result=result, diagnostics=resolved)
    style = load_figure_style(project_root)
    with apply_style(style):
        artifacts = [
            write_json(
                data_dir / "figure_style.json",
                {"generated_at": result.generated_at, **style.to_dict()},
            ),
            *render_all_figures(
                figure_ctx,
                include_security=result.config.security_profile.enabled,
            ),
            write_json(figures_dir / "figure_registry.json", registry_payload),
            write_figure_quality_report(
                data_dir / "figure_quality_report.json",
                project_root,
                registry_payload,
                generated_at=result.generated_at,
                require_all_registered=True,
            ),
        ]
    return artifacts


def refresh_loop_payloads(project_root: Path, result: AutoResearchLoopResult) -> list[Path]:
    """Write or refresh loop JSON, review payloads, and manuscript variables."""
    output = project_root / "output"
    data_dir = output / "data"
    reports_dir = output / "reports"
    loop_payload = result.to_dict()
    paths = [
        write_json(data_dir / "autoresearch_loop.json", loop_payload),
        write_json(data_dir / "autoresearch_claims.json", [claim.to_dict() for claim in result.claims]),
        write_json(data_dir / "autoresearch_review_packet.json", build_review_packet(result)),
        write_json(reports_dir / "autoresearch_loop.json", loop_payload),
        write_text(reports_dir / "autoresearch_loop.md", render_loop_markdown(result)),
        write_text(reports_dir / "autoresearch_review_packet.md", render_review_packet_markdown(result)),
        write_text(reports_dir / "autoresearch_summary.md", render_summary_markdown(result)),
        save_variables(compute_variables_from_payload(loop_payload), data_dir / "manuscript_variables.json"),
    ]
    return paths


def finalize_loop_payloads(project_root: Path, result: AutoResearchLoopResult) -> list[Path]:
    """Compatibility alias for ``refresh_loop_payloads``."""
    return refresh_loop_payloads(project_root, result)


def update_result_payloads(project_root: Path, result: AutoResearchLoopResult) -> list[Path]:
    """Compatibility alias for ``refresh_loop_payloads``."""
    return refresh_loop_payloads(project_root, result)


def write_schema_manifest(project_root: Path, paths: list[Path], *, generated_at: str) -> Path:
    """Write the schema-version manifest; fail the run if any payload is nonconforming.

    This makes schema conformance a HARD production gate (not just an emitted field):
    a governance payload that carries a contracted schema tag but violates its
    field/type contract aborts the loop loudly rather than being written as green.
    """
    payload = schema_manifest_payload(project_root, paths, generated_at=generated_at)
    if not payload["valid"]:
        nonconforming = payload["nonconforming_schema_artifacts"]
        rows = nonconforming if isinstance(nonconforming, list) else []
        offenders = "; ".join(f"{row.get('path')} ({row.get('violations')})" for row in rows if isinstance(row, dict))
        raise ValueError(f"nonconforming schema artifact(s) — governance gate failed: {offenders}")
    return write_json(
        project_root / "output" / "data" / "autoresearch_schema_manifest.json",
        payload,
    )


def write_research_object_manifest(project_root: Path, paths: list[Path], *, generated_at: str) -> Path:
    """Write the local research-object manifest."""
    return write_json(
        project_root / "output" / "data" / "research_object_manifest.json",
        research_object_manifest_payload(project_root, paths, generated_at=generated_at),
    )


def write_autoresearch_phase_ledger(
    project_root: Path,
    result: AutoResearchLoopResult,
    paths: list[Path],
    *,
    generated_at: str,
    settlement_pass_count: int,
) -> Path:
    """Write the deterministic phase ledger for the loop settlement order."""
    return write_phase_ledger(
        project_root / "output" / "data" / "autoresearch_phase_ledger.json",
        project_root,
        result,
        paths,
        generated_at=generated_at,
        settlement_pass_count=settlement_pass_count,
    )


def write_loop_payloads(
    project_root: Path,
    plan_payload: dict[str, Any],
    config: AutoResearchLoopConfig,
    stage_results: tuple[LoopStageResult, ...],
    result: AutoResearchLoopResult,
) -> list[Path]:
    """Write all loop outputs once using core and finalize phases."""
    core_paths = write_core_loop_artifacts(
        project_root,
        plan_payload,
        config,
        stage_results,
        result.generated_at,
        result.project_name,
    )
    return [*core_paths, *refresh_loop_payloads(project_root, result)]


def _program_summary(project_root: Path) -> str:
    path = project_root / "program.md"
    if not path.exists():
        return "Human-authored research program."
    for paragraph in path.read_text(encoding="utf-8").split("\n\n"):
        text = " ".join(line.strip() for line in paragraph.splitlines() if line.strip() and not line.startswith("#"))
        if text:
            return text
    return "Human-authored research program."
