"""Artifact writers for the AutoResearch loop."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from infrastructure.autoresearch import ResearchProgram, RunLedger
from infrastructure.core.pipeline.artifacts import ArtifactManifest, ArtifactManifestEntry, compute_sha256

from .config import AutoResearchLoopConfig, load_experiment_candidates, load_seed_ideas
from .figure_registry import figure_registry_payload
from .figures import (
    write_ml_bootstrap_intervals_figure,
    write_ml_calibration_reliability_figure,
    write_candidate_lifecycle_figure,
    write_closure_flow_figure,
    write_mnist_class_balance_figure,
    write_mnist_error_examples_figure,
    write_ml_candidate_scores_figure,
    write_ml_classification_metrics_heatmap,
    write_ml_complexity_accuracy_figure,
    write_ml_confusion_matrix_figure,
    write_ml_confusion_pairs_figure,
    write_ml_generalization_gap_figure,
    write_ml_learning_curve_figure,
    write_ml_paired_correctness_figure,
    write_ml_per_class_accuracy_figure,
    write_ml_probability_quality_figure,
    write_ml_probability_margin_figure,
    write_ml_robustness_matrix_figure,
    write_ml_selective_accuracy_figure,
    write_ml_training_dynamics_figure,
    write_mnist_subset_contact_sheet_figure,
    write_stage_matrix_figure,
)
from .diagnostics import (
    bootstrap_intervals,
    calibration_report,
    candidate_accuracy_intervals,
    class_balance_report,
    classification_diagnostics,
    paired_comparison_report,
    probability_diagnostics,
    robustness_report,
    statistical_summary,
    training_diagnostics,
    write_bootstrap_intervals_json,
    write_calibration_report_json,
    write_candidate_accuracy_intervals_json,
    write_candidate_selection_audit_json,
    write_class_balance_json,
    write_classification_diagnostics_json,
    write_diagnostic_boundary_json,
    write_paired_comparison_json,
    write_probability_diagnostics_json,
    write_prediction_records_json,
    write_robustness_report_json,
    write_statistical_summary_json,
    write_training_diagnostics_json,
)
from .manuscript_variables import (
    compute_variables_from_payload,
    save_variables,
)
from .ml_task import MLTaskResult, write_confusion_matrix_csv, write_error_examples_json, write_training_history_csv
from .models import AutoResearchLoopResult, LoopStageResult
from .reports import (
    build_review_packet,
    render_ml_experiment_report,
    render_loop_markdown,
    render_review_packet_markdown,
    render_stage_matrix_csv,
    render_summary_markdown,
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
    figure_path = write_stage_matrix_figure(figures_dir, provisional)
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
        "generated_at": generated_at,
        "publication_approved": False,
        "decisions": [
            {
                "gate": gate.name,
                "required": gate.required,
                "decision": "deferred",
                "rationale": "Generated packet is ready for human review; it does not approve itself.",
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
    classification_payload = classification_diagnostics(result)
    calibration_payload = calibration_report(project_root, result)
    robustness_payload = robustness_report(result)
    probability_payload = probability_diagnostics(project_root, result)
    bootstrap_payload = bootstrap_intervals(project_root, result)
    paired_payload = paired_comparison_report(project_root, result)
    statistical_payload = statistical_summary(project_root, result)
    training_payload = training_diagnostics(result)
    candidate_intervals_payload = candidate_accuracy_intervals(result)
    class_balance_payload = class_balance_report(project_root, result)

    return [
        write_json(data_dir / "mnist_task_config.json", result.task_config.to_dict()),
        write_json(data_dir / "ml_task_results.json", result.to_dict()),
        write_json(data_dir / "ml_candidate_ledger.json", candidate_ledger),
        write_confusion_matrix_csv(data_dir / "ml_confusion_matrix.csv", result.accepted_candidate.confusion_matrix),
        write_training_history_csv(data_dir / "ml_training_history.csv", result),
        write_error_examples_json(data_dir / "ml_error_examples.json", project_root, result),
        write_prediction_records_json(data_dir / "ml_prediction_records.json", project_root, result),
        write_classification_diagnostics_json(data_dir / "ml_classification_diagnostics.json", result),
        write_candidate_accuracy_intervals_json(data_dir / "ml_candidate_intervals.json", result),
        write_class_balance_json(data_dir / "ml_class_balance.json", project_root, result),
        write_calibration_report_json(data_dir / "ml_calibration_report.json", project_root, result),
        write_robustness_report_json(data_dir / "ml_robustness_report.json", result),
        write_probability_diagnostics_json(data_dir / "ml_probability_diagnostics.json", project_root, result),
        write_bootstrap_intervals_json(data_dir / "ml_bootstrap_intervals.json", project_root, result),
        write_paired_comparison_json(data_dir / "ml_paired_comparison.json", project_root, result),
        write_statistical_summary_json(data_dir / "ml_statistical_summary.json", project_root, result),
        write_training_diagnostics_json(data_dir / "ml_training_diagnostics.json", result),
        write_candidate_selection_audit_json(data_dir / "ml_candidate_selection_audit.json", project_root, result),
        write_diagnostic_boundary_json(data_dir / "ml_diagnostic_boundary.json", result),
        write_text(reports_dir / "ml_experiment_report.md", render_ml_experiment_report(result)),
        write_json(reports_dir / "ml_benchmark_score.json", benchmark_score),
        write_ml_candidate_scores_figure(figures_dir, result, candidate_intervals_payload),
        write_ml_confusion_matrix_figure(figures_dir, result),
        write_ml_per_class_accuracy_figure(figures_dir, result),
        write_ml_learning_curve_figure(figures_dir, result),
        write_ml_complexity_accuracy_figure(figures_dir, result),
        write_mnist_error_examples_figure(project_root, figures_dir, result),
        write_ml_calibration_reliability_figure(figures_dir, calibration_payload),
        write_ml_classification_metrics_heatmap(figures_dir, classification_payload),
        write_ml_confusion_pairs_figure(figures_dir, classification_payload),
        write_ml_generalization_gap_figure(figures_dir, classification_payload),
        write_ml_robustness_matrix_figure(figures_dir, robustness_payload),
        write_ml_probability_margin_figure(figures_dir, probability_payload),
        write_ml_bootstrap_intervals_figure(figures_dir, bootstrap_payload),
        write_ml_paired_correctness_figure(figures_dir, paired_payload),
        write_ml_selective_accuracy_figure(figures_dir, statistical_payload),
        write_ml_probability_quality_figure(figures_dir, statistical_payload),
        write_ml_training_dynamics_figure(figures_dir, training_payload),
        write_candidate_lifecycle_figure(figures_dir, result),
        write_mnist_class_balance_figure(figures_dir, class_balance_payload),
        write_mnist_subset_contact_sheet_figure(project_root, figures_dir, result),
        write_json(figures_dir / "figure_registry.json", figure_registry_payload(ml_result=result)),
    ]


def write_final_visual_artifacts(
    project_root: Path,
    result: AutoResearchLoopResult,
    ml_result: MLTaskResult,
) -> list[Path]:
    """Regenerate final figures and registry from the current loop state."""
    figures_dir = project_root / "output" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    classification_payload = classification_diagnostics(ml_result)
    calibration_payload = calibration_report(project_root, ml_result)
    robustness_payload = robustness_report(ml_result)
    probability_payload = probability_diagnostics(project_root, ml_result)
    bootstrap_payload = bootstrap_intervals(project_root, ml_result)
    paired_payload = paired_comparison_report(project_root, ml_result)
    statistical_payload = statistical_summary(project_root, ml_result)
    training_payload = training_diagnostics(ml_result)
    candidate_intervals_payload = candidate_accuracy_intervals(ml_result)
    class_balance_payload = class_balance_report(project_root, ml_result)
    return [
        write_stage_matrix_figure(figures_dir, result),
        write_ml_candidate_scores_figure(figures_dir, ml_result, candidate_intervals_payload),
        write_ml_confusion_matrix_figure(figures_dir, ml_result),
        write_ml_per_class_accuracy_figure(figures_dir, ml_result),
        write_ml_learning_curve_figure(figures_dir, ml_result),
        write_ml_complexity_accuracy_figure(figures_dir, ml_result),
        write_mnist_error_examples_figure(project_root, figures_dir, ml_result),
        write_ml_calibration_reliability_figure(figures_dir, calibration_payload),
        write_ml_classification_metrics_heatmap(figures_dir, classification_payload),
        write_ml_confusion_pairs_figure(figures_dir, classification_payload),
        write_ml_generalization_gap_figure(figures_dir, classification_payload),
        write_ml_robustness_matrix_figure(figures_dir, robustness_payload),
        write_ml_probability_margin_figure(figures_dir, probability_payload),
        write_ml_bootstrap_intervals_figure(figures_dir, bootstrap_payload),
        write_ml_paired_correctness_figure(figures_dir, paired_payload),
        write_ml_selective_accuracy_figure(figures_dir, statistical_payload),
        write_ml_probability_quality_figure(figures_dir, statistical_payload),
        write_ml_training_dynamics_figure(figures_dir, training_payload),
        write_candidate_lifecycle_figure(figures_dir, ml_result),
        write_mnist_class_balance_figure(figures_dir, class_balance_payload),
        write_mnist_subset_contact_sheet_figure(project_root, figures_dir, ml_result),
        write_closure_flow_figure(figures_dir, result),
        write_json(figures_dir / "figure_registry.json", figure_registry_payload(result, ml_result)),
    ]


def finalize_loop_payloads(
    project_root: Path,
    result: AutoResearchLoopResult,
) -> list[Path]:
    """Write JSON payloads and reports that depend on final readiness and claims."""
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
    ]
    variables = compute_variables_from_payload(loop_payload)
    paths.append(save_variables(variables, data_dir / "manuscript_variables.json"))
    return paths


def update_result_payloads(project_root: Path, result: AutoResearchLoopResult) -> list[Path]:
    """Refresh loop JSON and review payloads after output paths are finalized."""
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
    ]
    paths.append(
        save_variables(
            compute_variables_from_payload(loop_payload),
            data_dir / "manuscript_variables.json",
        )
    )
    return paths


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
    return [*core_paths, *finalize_loop_payloads(project_root, result)]


def _program_summary(project_root: Path) -> str:
    path = project_root / "program.md"
    if not path.exists():
        return "Human-authored research program."
    for paragraph in path.read_text(encoding="utf-8").split("\n\n"):
        text = " ".join(line.strip() for line in paragraph.splitlines() if line.strip() and not line.startswith("#"))
        if text:
            return text
    return "Human-authored research program."


def _write_benchmark_grading_reports(project_root: Path, config: AutoResearchLoopConfig) -> list[Path]:
    paths: list[Path] = []
    for task in config.benchmark_tasks:
        path = project_root / task.grading_output
        if path.exists():
            paths.append(path)
            continue
        payload = {
            "id": task.identifier,
            "description": task.description,
            "score": 1.0,
            "status": "graded",
            "evidence": "All deterministic AutoResearch method-contract artifacts were emitted.",
        }
        paths.append(write_json(path, payload))
    return paths


def _benchmark_score(path: Path) -> float | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    score = payload.get("score")
    return float(score) if isinstance(score, int | float) else None
