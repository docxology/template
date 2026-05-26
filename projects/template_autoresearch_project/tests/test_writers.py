"""Tests for loop writer helpers."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
import shutil

from infrastructure.autoresearch import BudgetPolicy

from src.config import AutoResearchLoopConfig
from src.ml_task import run_bounded_ml_task
from src.models import AutoResearchLoopResult, LoopStageResult
from src.writers import write_loop_payloads, write_ml_task_artifacts


def test_write_loop_payloads_writes_core_and_finalize_artifacts(tmp_path: Path) -> None:
    config = AutoResearchLoopConfig(
        topic="Demo",
        review_policy="human_review_required",
        research_questions=(),
        loop_stages=("plan", "readiness"),
        required_artifacts=(),
        quality_checks=(),
    )
    stage_results = (
        LoopStageResult(
            name="plan",
            status="declared",
            evidence="Declared one stage.",
            suggested_action="review",
        ),
        LoopStageResult(
            name="readiness",
            status="declared",
            evidence="Scheduled checks.",
            suggested_action="review",
        ),
    )
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")
    result = AutoResearchLoopResult(
        project_name="demo",
        generated_at=generated_at,
        config=config,
        stage_results=stage_results,
        claims=(),
        readiness_valid=False,
        output_paths=(),
    )

    paths = write_loop_payloads(
        tmp_path,
        {"project_name": "demo", "stages": []},
        config,
        stage_results,
        result,
    )

    expected = {
        tmp_path / "output/data/autoresearch_plan.json",
        tmp_path / "output/data/autoresearch_loop.json",
        tmp_path / "output/data/autoresearch_claims.json",
        tmp_path / "output/data/autoresearch_stage_matrix.csv",
        tmp_path / "output/data/autoresearch_review_packet.json",
        tmp_path / "output/data/manuscript_variables.json",
        tmp_path / "output/reports/autoresearch_loop.json",
        tmp_path / "output/reports/autoresearch_loop.md",
        tmp_path / "output/reports/autoresearch_review_packet.md",
        tmp_path / "output/reports/autoresearch_summary.md",
        tmp_path / "output/figures/autoresearch_stage_matrix.png",
        tmp_path / "output/figures/figure_registry.json",
    }
    assert expected <= {path.resolve() for path in paths}
    loop_payload = (tmp_path / "output/data/autoresearch_loop.json").read_text(encoding="utf-8")
    assert '"readiness_valid": false' in loop_payload


def test_write_ml_task_artifacts_writes_results_report_and_figure(project_root: Path, tmp_path: Path) -> None:
    result = run_bounded_ml_task(project_root, BudgetPolicy(max_iterations=4))
    shutil.copy(project_root / "mnist_task.yaml", tmp_path / "mnist_task.yaml")
    shutil.copytree(project_root / "data", tmp_path / "data")

    paths = write_ml_task_artifacts(tmp_path, result, generated_at="2026-05-25T00:00:00+00:00")

    expected = {
        tmp_path / "output/data/mnist_task_config.json",
        tmp_path / "output/data/ml_task_results.json",
        tmp_path / "output/data/ml_candidate_ledger.json",
        tmp_path / "output/data/ml_confusion_matrix.csv",
        tmp_path / "output/data/ml_training_history.csv",
        tmp_path / "output/data/ml_error_examples.json",
        tmp_path / "output/data/ml_prediction_records.json",
        tmp_path / "output/data/ml_classification_diagnostics.json",
        tmp_path / "output/data/ml_candidate_intervals.json",
        tmp_path / "output/data/ml_class_balance.json",
        tmp_path / "output/data/ml_calibration_report.json",
        tmp_path / "output/data/ml_robustness_report.json",
        tmp_path / "output/data/ml_probability_diagnostics.json",
        tmp_path / "output/data/ml_bootstrap_intervals.json",
        tmp_path / "output/data/ml_paired_comparison.json",
        tmp_path / "output/data/ml_statistical_summary.json",
        tmp_path / "output/data/ml_training_diagnostics.json",
        tmp_path / "output/data/ml_candidate_selection_audit.json",
        tmp_path / "output/data/ml_diagnostic_boundary.json",
        tmp_path / "output/reports/ml_experiment_report.md",
        tmp_path / "output/reports/ml_benchmark_score.json",
        tmp_path / "output/figures/ml_candidate_scores.png",
        tmp_path / "output/figures/ml_confusion_matrix.png",
        tmp_path / "output/figures/ml_per_class_accuracy.png",
        tmp_path / "output/figures/ml_learning_curves.png",
        tmp_path / "output/figures/ml_complexity_accuracy.png",
        tmp_path / "output/figures/mnist_error_examples.png",
        tmp_path / "output/figures/ml_calibration_reliability.png",
        tmp_path / "output/figures/ml_classification_metrics_heatmap.png",
        tmp_path / "output/figures/ml_confusion_pairs.png",
        tmp_path / "output/figures/ml_generalization_gap.png",
        tmp_path / "output/figures/ml_robustness_matrix.png",
        tmp_path / "output/figures/ml_probability_margin_distribution.png",
        tmp_path / "output/figures/ml_bootstrap_intervals.png",
        tmp_path / "output/figures/ml_paired_correctness.png",
        tmp_path / "output/figures/ml_selective_accuracy.png",
        tmp_path / "output/figures/ml_probability_quality.png",
        tmp_path / "output/figures/ml_training_dynamics.png",
        tmp_path / "output/figures/autoresearch_candidate_lifecycle.png",
        tmp_path / "output/figures/mnist_class_balance.png",
        tmp_path / "output/figures/mnist_subset_contact_sheet.png",
        tmp_path / "output/figures/figure_registry.json",
    }
    assert expected <= {path.resolve() for path in paths}
    assert (tmp_path / "output/figures/ml_candidate_scores.png").stat().st_size > 1000
    assert (tmp_path / "output/figures/ml_confusion_matrix.png").stat().st_size > 1000
    assert (tmp_path / "output/figures/ml_per_class_accuracy.png").stat().st_size > 1000
    assert (tmp_path / "output/figures/ml_learning_curves.png").stat().st_size > 1000
    assert (tmp_path / "output/figures/ml_complexity_accuracy.png").stat().st_size > 1000
    assert (tmp_path / "output/figures/mnist_error_examples.png").stat().st_size > 1000
    assert (tmp_path / "output/figures/ml_calibration_reliability.png").stat().st_size > 1000
    assert (tmp_path / "output/figures/ml_classification_metrics_heatmap.png").stat().st_size > 1000
    assert (tmp_path / "output/figures/ml_confusion_pairs.png").stat().st_size > 1000
    assert (tmp_path / "output/figures/ml_generalization_gap.png").stat().st_size > 1000
    assert (tmp_path / "output/figures/ml_robustness_matrix.png").stat().st_size > 1000
    assert (tmp_path / "output/figures/ml_probability_margin_distribution.png").stat().st_size > 1000
    assert (tmp_path / "output/figures/ml_bootstrap_intervals.png").stat().st_size > 1000
    assert (tmp_path / "output/figures/ml_paired_correctness.png").stat().st_size > 1000
    assert (tmp_path / "output/figures/ml_selective_accuracy.png").stat().st_size > 1000
    assert (tmp_path / "output/figures/ml_probability_quality.png").stat().st_size > 1000
    assert (tmp_path / "output/figures/ml_training_dynamics.png").stat().st_size > 1000
    assert (tmp_path / "output/figures/autoresearch_candidate_lifecycle.png").stat().st_size > 1000
    assert (tmp_path / "output/figures/mnist_class_balance.png").stat().st_size > 1000
    assert (tmp_path / "output/figures/mnist_subset_contact_sheet.png").stat().st_size > 1000
    registry = json.loads((tmp_path / "output/figures/figure_registry.json").read_text(encoding="utf-8"))
    for record in registry.values():
        metadata = record["metadata"]
        assert metadata["method"] in record["caption"]
        assert "generation method" in record["caption"]
        assert "method" in metadata
        assert "validated_by" in metadata
        assert metadata["source"]
        assert metadata["claim_boundary"]
    assert registry["fig:ml_calibration_reliability"]["metadata"]["source"] == "output/data/ml_calibration_report.json"
    assert (
        registry["fig:ml_classification_metrics_heatmap"]["metadata"]["source"]
        == "output/data/ml_classification_diagnostics.json"
    )
    assert registry["fig:ml_confusion_pairs"]["metadata"]["source"] == "output/data/ml_classification_diagnostics.json"
    assert (
        registry["fig:ml_generalization_gap"]["metadata"]["source"] == "output/data/ml_classification_diagnostics.json"
    )
    assert registry["fig:ml_robustness_matrix"]["metadata"]["source"] == "output/data/ml_robustness_report.json"
    assert (
        registry["fig:ml_probability_margin_distribution"]["metadata"]["source"]
        == "output/data/ml_probability_diagnostics.json"
    )
    assert registry["fig:ml_bootstrap_intervals"]["metadata"]["source"] == "output/data/ml_bootstrap_intervals.json"
    assert registry["fig:ml_paired_correctness"]["metadata"]["source"] == "output/data/ml_paired_comparison.json"
    assert registry["fig:ml_selective_accuracy"]["metadata"]["source"] == "output/data/ml_statistical_summary.json"
    assert registry["fig:ml_probability_quality"]["metadata"]["source"] == "output/data/ml_statistical_summary.json"
    assert registry["fig:ml_training_dynamics"]["metadata"]["source"] == "output/data/ml_training_diagnostics.json"
    assert registry["fig:ml_candidate_scores"]["metadata"]["source"] == "output/data/ml_candidate_intervals.json"
    assert registry["fig:mnist_class_balance"]["metadata"]["source"] == "output/data/ml_class_balance.json"
    assert (
        registry["fig:autoresearch_security_control_matrix"]["metadata"]["source"]
        == "output/data/autoresearch_threat_model.json"
    )
    assert (
        registry["fig:autoresearch_integrity_chain"]["metadata"]["source"]
        == "output/data/autoresearch_integrity_attestation.json"
    )
