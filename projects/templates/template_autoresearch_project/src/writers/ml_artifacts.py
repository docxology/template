"""ML task artifact writers."""

from __future__ import annotations

from pathlib import Path

from src.diagnostics import diagnostic_bundle
from src.figures.figure_quality import write_figure_quality_report
from src.figures.figure_registry import figure_registry_payload
from src.figures.figure_style import apply_style, load_figure_style
from src.ml.task import (
    MLTaskResult,
    write_confusion_matrix_csv,
    write_error_examples_json,
    write_training_history_csv,
)
from src.reports import render_ml_experiment_report

from .figure_artifacts import build_figure_render_context
from .figure_dispatch import render_figure_batch
from .io import write_json, write_text


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
        return [
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
