"""Tests for loop writer helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import shutil

from infrastructure.autoresearch import BudgetPolicy, ReviewGate

from src.config import AutoResearchLoopConfig, HumanReviewState
from src.ml_task import run_bounded_ml_task
from src.models import AutoResearchLoopResult, LoopStageResult
from src.writers import (
    write_loop_payloads,
    write_method_contract_artifacts,
    write_ml_task_artifacts,
    write_research_object_manifest,
    write_schema_manifest,
)


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
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
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
    review_packet = json.loads((tmp_path / "output/data/autoresearch_review_packet.json").read_text(encoding="utf-8"))
    assert review_packet["schema"] == "template-autoresearch-review-packet-v1"


def test_write_method_contract_artifacts_uses_human_review_state(tmp_path: Path) -> None:
    config = AutoResearchLoopConfig(
        topic="Demo",
        review_policy="human_review_required",
        research_questions=(),
        loop_stages=("readiness",),
        required_artifacts=(),
        quality_checks=(),
        review_gates=(ReviewGate(name="proposal_review", required=True),),
        human_review=HumanReviewState(
            publication_approved=True,
            reviewer="Human Reviewer",
            reviewed_at="2026-05-26",
            decisions={"proposal_review": "approved"},
            source_exists=True,
        ),
    )
    (tmp_path / "program.md").write_text("# Program\n\nHuman-authored research program.", encoding="utf-8")
    (tmp_path / "seed_ideas.yaml").write_text("ideas: []\n", encoding="utf-8")

    paths = write_method_contract_artifacts(tmp_path, config, generated_at="2026-05-26T00:00:00+00:00")

    assert tmp_path / "output/data/review_decisions.json" in paths
    payload = json.loads((tmp_path / "output/data/review_decisions.json").read_text(encoding="utf-8"))
    assert payload["schema"] == "template-autoresearch-review-decisions-v1"
    assert payload["publication_approved"] is True
    assert payload["human_review_source_exists"] is True
    assert payload["decisions"][0]["decision"] == "approved"


def test_refresh_loop_payloads_matches_legacy_aliases(tmp_path: Path) -> None:
    from src.writers import finalize_loop_payloads, refresh_loop_payloads, update_result_payloads

    config = AutoResearchLoopConfig(
        topic="Demo",
        review_policy="human_review_required",
        research_questions=(),
        loop_stages=("plan",),
        required_artifacts=(),
        quality_checks=(),
    )
    result = AutoResearchLoopResult(
        project_name="demo",
        generated_at="2026-05-26T00:00:00+00:00",
        config=config,
        stage_results=(),
        claims=(),
        readiness_valid=False,
        output_paths=(),
    )
    refresh_paths = {path.resolve() for path in refresh_loop_payloads(tmp_path, result)}
    assert refresh_paths == {path.resolve() for path in finalize_loop_payloads(tmp_path, result)}
    assert refresh_paths == {path.resolve() for path in update_result_payloads(tmp_path, result)}


def test_build_figure_render_context_reuses_diagnostics(project_root: Path) -> None:
    from src.diagnostics import diagnostic_bundle
    from src.ml_task import run_bounded_ml_task
    from src.writers import build_figure_render_context

    ml_result = run_bounded_ml_task(project_root, BudgetPolicy(max_iterations=4))
    bundle = diagnostic_bundle(project_root, ml_result)
    ctx = build_figure_render_context(project_root, ml_result, diagnostics=bundle)
    assert ctx.diagnostics is bundle


def test_schema_and_research_object_manifests_are_local(project_root: Path, tmp_path: Path) -> None:
    sample = tmp_path / "output" / "data" / "sample.json"
    sample.parent.mkdir(parents=True)
    sample.write_text('{"schema": "sample-v1", "ok": true}\n', encoding="utf-8")
    review = tmp_path / "output" / "data" / "review_decisions.json"
    review.write_text(
        json.dumps(
            {
                "schema": "template-autoresearch-review-decisions-v1",
                "publication_approved": False,
                "human_review_source": "human_review.yaml",
                "human_review_source_exists": True,
                "decisions": [],
            }
        ),
        encoding="utf-8",
    )
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "source_ledger.yaml").write_text(
        (project_root / "manuscript" / "source_ledger.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    schema_path = write_schema_manifest(tmp_path, [sample, review], generated_at="2026-05-26T00:00:00+00:00")
    object_path = write_research_object_manifest(
        tmp_path,
        [sample, review, schema_path],
        generated_at="2026-05-26T00:00:00+00:00",
    )

    schema_manifest = json.loads(schema_path.read_text(encoding="utf-8"))
    research_object = json.loads(object_path.read_text(encoding="utf-8"))
    assert schema_manifest["schema"] == "template-autoresearch-schema-manifest-v1"
    assert not schema_manifest["missing_schema_artifacts"]
    assert research_object["schema"] == "template-autoresearch-research-object-manifest-v1"
    assert research_object["approval_state"]["publication_approved"] is False
    assert "RO-Crate" in research_object["claim_boundary"]


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
        tmp_path / "output/data/ml_calibration_bin_intervals.json",
        tmp_path / "output/data/ml_robustness_report.json",
        tmp_path / "output/data/ml_probability_diagnostics.json",
        tmp_path / "output/data/ml_bootstrap_intervals.json",
        tmp_path / "output/data/ml_paired_comparison.json",
        tmp_path / "output/data/ml_statistical_summary.json",
        tmp_path / "output/data/ml_training_diagnostics.json",
        tmp_path / "output/data/ml_candidate_rank_stability.json",
        tmp_path / "output/data/ml_candidate_selection_audit.json",
        tmp_path / "output/data/ml_diagnostic_boundary.json",
        tmp_path / "output/data/figure_quality_report.json",
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
        tmp_path / "output/figures/ml_candidate_rank_stability.png",
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
    assert (tmp_path / "output/figures/ml_candidate_rank_stability.png").stat().st_size > 1000
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
    assert registry["fig:ml_candidate_rank_stability"]["metadata"]["source"] == (
        "output/data/ml_candidate_rank_stability.json"
    )
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
    figure_quality = json.loads((tmp_path / "output/data/figure_quality_report.json").read_text(encoding="utf-8"))
    assert figure_quality["schema"] == "template-autoresearch-figure-quality-report-v1"
    assert figure_quality["valid"] is True
    assert figure_quality["unregistered_pngs"] == []
    assert all(row["exists"] and row["source_exists"] for row in figure_quality["figures"])
