"""Tests for the deterministic AutoResearch loop."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np

from src.config import build_loop_config, load_manuscript_loop_settings
from src.loop import build_claims, run_autoresearch_loop
from src.models import AutoResearchLoopResult


def _run_loop_without_coverage(project: Path, repo: Path) -> AutoResearchLoopResult:
    """Run a secondary smoke loop without tracing every training operation."""
    coverage_module = sys.modules.get("coverage")
    coverage_class = getattr(coverage_module, "Coverage", None)
    current_coverage = coverage_class.current() if coverage_class is not None else None
    if current_coverage is not None:
        current_coverage.stop()
    try:
        return run_autoresearch_loop(project, repo)
    finally:
        if current_coverage is not None:
            current_coverage.start()


def test_run_autoresearch_loop_writes_artifacts_and_valid_readiness(
    project_root: Path,
    autoresearch_loop_result: AutoResearchLoopResult,
) -> None:
    assert autoresearch_loop_result.readiness_valid is True
    assert len(autoresearch_loop_result.stage_results) == 7
    assert autoresearch_loop_result.supported_claim_count == len(autoresearch_loop_result.claims)
    assert all(stage.status == "declared" for stage in autoresearch_loop_result.stage_results)
    assert autoresearch_loop_result.ml_task["accepted_candidate_id"] == "exp-mlp-tanh-64"
    assert autoresearch_loop_result.ml_task["transformer_evaluated"] is True
    for rel_path in autoresearch_loop_result.config.required_artifacts:
        assert (project_root / rel_path).exists()

    readiness = json.loads((project_root / "output" / "reports" / "autoresearch_readiness.json").read_text())
    assert readiness["valid"] is True
    assert readiness["summary"]["errors"] == 0


def test_evidence_registry_report_is_compact_by_default(
    project_root: Path,
    autoresearch_loop_result: AutoResearchLoopResult,
) -> None:
    assert autoresearch_loop_result.readiness_valid is True
    report_path = project_root / "output" / "reports" / "evidence_registry.json"
    full_debug_path = project_root / "output" / "reports" / "evidence_registry_full.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    reports_size = sum(
        path.stat().st_size for path in (project_root / "output" / "reports").rglob("*") if path.is_file()
    )

    assert payload["schema"] == "template-evidence-registry-report-v1"
    assert payload["fact_count"] > len(payload["sample_facts"])
    assert len(payload["sample_facts"]) <= 200
    assert payload["omitted_fact_count"] == payload["fact_count"] - len(payload["sample_facts"])
    assert report_path.stat().st_size < 1024 * 1024
    assert reports_size < 10 * 1024 * 1024
    assert full_debug_path.exists() is False
    assert "output/reports/evidence_registry_full.json" not in autoresearch_loop_result.output_paths


def test_loop_payload_contains_claims_metrics_and_output_paths(
    project_root: Path,
    autoresearch_loop_result: AutoResearchLoopResult,
) -> None:
    assert autoresearch_loop_result.readiness_valid is True
    payload = json.loads((project_root / "output" / "data" / "autoresearch_loop.json").read_text())

    assert payload["metrics"]["stage_count"] == 7
    assert payload["metrics"]["supported_claim_count"] == 6
    assert payload["metrics"]["readiness_valid"] is True
    assert payload["ml_task"]["best_accuracy"] > payload["ml_task"]["baseline_accuracy"]
    assert "output/reports/autoresearch_loop.md" in payload["output_paths"]
    assert "output/data/research_program.json" in payload["output_paths"]
    assert "output/data/idea_ledger.json" in payload["output_paths"]
    assert "output/data/run_ledger.json" in payload["output_paths"]
    assert "output/data/review_decisions.json" in payload["output_paths"]
    assert "output/data/benchmark_scores.json" in payload["output_paths"]
    assert "output/data/mnist_task_config.json" in payload["output_paths"]
    assert "output/data/ml_task_results.json" in payload["output_paths"]
    assert "output/data/ml_candidate_ledger.json" in payload["output_paths"]
    assert "output/data/ml_confusion_matrix.csv" in payload["output_paths"]
    assert "output/data/ml_training_history.csv" in payload["output_paths"]
    assert "output/data/ml_error_examples.json" in payload["output_paths"]
    assert "output/data/ml_prediction_records.json" in payload["output_paths"]
    assert "output/data/ml_classification_diagnostics.json" in payload["output_paths"]
    assert "output/data/ml_candidate_intervals.json" in payload["output_paths"]
    assert "output/data/ml_class_balance.json" in payload["output_paths"]
    assert "output/data/ml_calibration_report.json" in payload["output_paths"]
    assert "output/data/ml_calibration_bin_intervals.json" in payload["output_paths"]
    assert "output/data/ml_robustness_report.json" in payload["output_paths"]
    assert "output/data/ml_probability_diagnostics.json" in payload["output_paths"]
    assert "output/data/ml_bootstrap_intervals.json" in payload["output_paths"]
    assert "output/data/ml_paired_comparison.json" in payload["output_paths"]
    assert "output/data/ml_statistical_summary.json" in payload["output_paths"]
    assert "output/data/ml_candidate_selection_audit.json" in payload["output_paths"]
    assert "output/data/ml_candidate_rank_stability.json" in payload["output_paths"]
    assert "output/data/ml_diagnostic_boundary.json" in payload["output_paths"]
    assert "output/data/autoresearch_phase_ledger.json" in payload["output_paths"]
    assert "output/data/figure_quality_report.json" in payload["output_paths"]
    assert "output/data/autoresearch_security_profile.json" in payload["output_paths"]
    assert "output/data/autoresearch_threat_model.json" in payload["output_paths"]
    assert "output/data/autoresearch_supply_chain_inventory.json" in payload["output_paths"]
    assert "output/data/autoresearch_inventory_export.json" in payload["output_paths"]
    assert "output/data/autoresearch_integrity_attestation.json" in payload["output_paths"]
    assert "output/data/autoresearch_schema_manifest.json" in payload["output_paths"]
    assert "output/data/research_object_manifest.json" in payload["output_paths"]
    assert "output/data/manuscript_variable_provenance.json" in payload["output_paths"]
    assert "output/data/manuscript_figure_blocks.json" in payload["output_paths"]
    assert "output/figures/ml_confusion_matrix.png" in payload["output_paths"]
    assert "output/figures/ml_per_class_accuracy.png" in payload["output_paths"]
    assert "output/figures/ml_learning_curves.png" in payload["output_paths"]
    assert "output/figures/ml_complexity_accuracy.png" in payload["output_paths"]
    assert "output/figures/mnist_error_examples.png" in payload["output_paths"]
    assert "output/figures/ml_calibration_reliability.png" in payload["output_paths"]
    assert "output/figures/ml_classification_metrics_heatmap.png" in payload["output_paths"]
    assert "output/figures/ml_confusion_pairs.png" in payload["output_paths"]
    assert "output/figures/ml_generalization_gap.png" in payload["output_paths"]
    assert "output/figures/ml_robustness_matrix.png" in payload["output_paths"]
    assert "output/figures/ml_probability_margin_distribution.png" in payload["output_paths"]
    assert "output/figures/ml_bootstrap_intervals.png" in payload["output_paths"]
    assert "output/figures/ml_paired_correctness.png" in payload["output_paths"]
    assert "output/figures/ml_selective_accuracy.png" in payload["output_paths"]
    assert "output/figures/ml_probability_quality.png" in payload["output_paths"]
    assert "output/figures/ml_candidate_rank_stability.png" in payload["output_paths"]
    assert "output/figures/autoresearch_candidate_lifecycle.png" in payload["output_paths"]
    assert "output/figures/mnist_class_balance.png" in payload["output_paths"]
    assert "output/figures/mnist_subset_contact_sheet.png" in payload["output_paths"]
    assert "output/figures/autoresearch_closure_flow.png" in payload["output_paths"]
    assert "output/figures/autoresearch_security_control_matrix.png" in payload["output_paths"]
    assert "output/figures/autoresearch_integrity_chain.png" in payload["output_paths"]
    assert "output/reports/autoresearch_security_review.md" in payload["output_paths"]


def test_run_autoresearch_loop_writes_bounded_method_ledgers(
    project_root: Path,
    autoresearch_loop_result: AutoResearchLoopResult,
) -> None:
    research_program = json.loads((project_root / "output" / "data" / "research_program.json").read_text())
    idea_ledger = json.loads((project_root / "output" / "data" / "idea_ledger.json").read_text())
    run_ledger = json.loads((project_root / "output" / "data" / "run_ledger.json").read_text())
    review_decisions = json.loads((project_root / "output" / "data" / "review_decisions.json").read_text())
    benchmark_scores = json.loads((project_root / "output" / "data" / "benchmark_scores.json").read_text())

    assert autoresearch_loop_result.readiness_valid is True
    assert research_program["path"] == "program.md"
    assert research_program["autonomy_level"] == "proposal_only"
    assert research_program["budget_policy"]["max_iterations"] == 4
    assert "projects/template_autoresearch_project/src/" in research_program["edit_allowlist"]
    assert {idea["status"] for idea in idea_ledger["ideas"]} >= {"accepted", "rejected", "deferred"}
    accepted = [idea for idea in idea_ledger["ideas"] if idea["status"] == "accepted"]
    assert accepted and all(idea["evidence_links"] for idea in accepted)
    assert run_ledger["iterations_used"] == 4
    assert run_ledger["llm_calls_used"] == 0
    assert run_ledger["cost_usd_used"] == 0.0
    assert run_ledger["budget_exhausted"] is True
    assert run_ledger["exhaustion_reason"] == "candidate iteration budget reached"
    assert review_decisions["publication_approved"] is False
    assert review_decisions["schema"] == "template-autoresearch-review-decisions-v1"
    assert review_decisions["human_review_source"] == "human_review.yaml"
    assert {row["decision"] for row in review_decisions["decisions"]} == {"deferred"}
    assert {task["id"] for task in benchmark_scores["tasks"]} == {"readiness-smoke", "ml-loop-score"}
    assert all(task["status"] == "graded" for task in benchmark_scores["tasks"])


def test_run_autoresearch_loop_writes_review_packet_and_stage_matrix(
    project_root: Path,
    autoresearch_loop_result: AutoResearchLoopResult,
) -> None:
    expected_paths = {
        "output/data/autoresearch_stage_matrix.csv",
        "output/data/autoresearch_review_packet.json",
        "output/data/research_program.json",
        "output/data/idea_ledger.json",
        "output/data/run_ledger.json",
        "output/data/review_decisions.json",
        "output/data/benchmark_scores.json",
        "output/data/mnist_task_config.json",
        "output/data/ml_task_results.json",
        "output/data/ml_candidate_ledger.json",
        "output/data/ml_confusion_matrix.csv",
        "output/data/ml_training_history.csv",
        "output/data/ml_error_examples.json",
        "output/data/ml_prediction_records.json",
        "output/data/ml_classification_diagnostics.json",
        "output/data/ml_candidate_intervals.json",
        "output/data/ml_class_balance.json",
        "output/data/ml_calibration_report.json",
        "output/data/ml_calibration_bin_intervals.json",
        "output/data/ml_robustness_report.json",
        "output/data/ml_probability_diagnostics.json",
        "output/data/ml_bootstrap_intervals.json",
        "output/data/ml_paired_comparison.json",
        "output/data/ml_statistical_summary.json",
        "output/data/ml_candidate_selection_audit.json",
        "output/data/ml_candidate_rank_stability.json",
        "output/data/ml_diagnostic_boundary.json",
        "output/data/autoresearch_phase_ledger.json",
        "output/data/figure_quality_report.json",
        "output/data/autoresearch_security_profile.json",
        "output/data/autoresearch_threat_model.json",
        "output/data/autoresearch_supply_chain_inventory.json",
        "output/data/autoresearch_inventory_export.json",
        "output/data/autoresearch_integrity_attestation.json",
        "output/data/autoresearch_schema_manifest.json",
        "output/data/research_object_manifest.json",
        "output/data/manuscript_variable_provenance.json",
        "output/data/manuscript_figure_blocks.json",
        "output/reports/autoresearch_review_packet.md",
        "output/reports/autoresearch_summary.md",
        "output/reports/ml_experiment_report.md",
        "output/reports/ml_benchmark_score.json",
        "output/figures/autoresearch_stage_matrix.png",
        "output/figures/ml_candidate_scores.png",
        "output/figures/ml_confusion_matrix.png",
        "output/figures/ml_per_class_accuracy.png",
        "output/figures/ml_learning_curves.png",
        "output/figures/ml_complexity_accuracy.png",
        "output/figures/mnist_error_examples.png",
        "output/figures/ml_calibration_reliability.png",
        "output/figures/ml_classification_metrics_heatmap.png",
        "output/figures/ml_confusion_pairs.png",
        "output/figures/ml_generalization_gap.png",
        "output/figures/ml_robustness_matrix.png",
        "output/figures/ml_probability_margin_distribution.png",
        "output/figures/ml_bootstrap_intervals.png",
        "output/figures/ml_paired_correctness.png",
        "output/figures/ml_selective_accuracy.png",
        "output/figures/ml_probability_quality.png",
        "output/figures/ml_candidate_rank_stability.png",
        "output/figures/autoresearch_candidate_lifecycle.png",
        "output/figures/mnist_class_balance.png",
        "output/figures/mnist_subset_contact_sheet.png",
        "output/figures/autoresearch_closure_flow.png",
        "output/figures/autoresearch_security_control_matrix.png",
        "output/figures/autoresearch_integrity_chain.png",
        "output/figures/figure_registry.json",
        "output/reports/autoresearch_security_review.md",
    }
    assert expected_paths <= set(autoresearch_loop_result.output_paths)

    stage_matrix = (project_root / "output" / "data" / "autoresearch_stage_matrix.csv").read_text(encoding="utf-8")
    assert "stage,status,evidence,suggested_action" in stage_matrix
    assert "readiness,declared" in stage_matrix

    review_packet = json.loads((project_root / "output" / "data" / "autoresearch_review_packet.json").read_text())
    assert review_packet["human_review"]["policy"] == "human_review_required"
    assert review_packet["human_review"]["ready_for_review"] == (
        autoresearch_loop_result.readiness_valid
        and autoresearch_loop_result.supported_claim_count == len(autoresearch_loop_result.claims)
    )
    assert review_packet["human_review"]["publication_approved"] is False
    assert review_packet["schema"] == "template-autoresearch-review-packet-v1"


def test_run_autoresearch_loop_writes_stage_matrix_figure(
    project_root: Path,
    autoresearch_loop_result: AutoResearchLoopResult,
) -> None:
    assert autoresearch_loop_result.readiness_valid is True
    figure_path = project_root / "output" / "figures" / "autoresearch_stage_matrix.png"
    registry_path = project_root / "output" / "figures" / "figure_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    assert figure_path.exists()
    assert figure_path.stat().st_size > 1000
    assert (project_root / "output" / "figures" / "ml_candidate_scores.png").exists()
    assert (project_root / "output" / "figures" / "ml_confusion_matrix.png").exists()
    assert (project_root / "output" / "figures" / "ml_per_class_accuracy.png").exists()
    assert (project_root / "output" / "figures" / "ml_learning_curves.png").exists()
    assert (project_root / "output" / "figures" / "ml_complexity_accuracy.png").exists()
    assert (project_root / "output" / "figures" / "mnist_error_examples.png").exists()
    assert (project_root / "output" / "figures" / "ml_calibration_reliability.png").exists()
    assert (project_root / "output" / "figures" / "ml_classification_metrics_heatmap.png").exists()
    assert (project_root / "output" / "figures" / "ml_confusion_pairs.png").exists()
    assert (project_root / "output" / "figures" / "ml_generalization_gap.png").exists()
    assert (project_root / "output" / "figures" / "ml_robustness_matrix.png").exists()
    assert (project_root / "output" / "figures" / "ml_probability_margin_distribution.png").exists()
    assert (project_root / "output" / "figures" / "ml_bootstrap_intervals.png").exists()
    assert (project_root / "output" / "figures" / "ml_paired_correctness.png").exists()
    assert (project_root / "output" / "figures" / "ml_selective_accuracy.png").exists()
    assert (project_root / "output" / "figures" / "ml_probability_quality.png").exists()
    assert (project_root / "output" / "figures" / "ml_candidate_rank_stability.png").exists()
    assert (project_root / "output" / "figures" / "autoresearch_candidate_lifecycle.png").exists()
    assert (project_root / "output" / "figures" / "mnist_class_balance.png").exists()
    assert (project_root / "output" / "figures" / "mnist_subset_contact_sheet.png").exists()
    assert (project_root / "output" / "figures" / "autoresearch_closure_flow.png").exists()
    assert (project_root / "output" / "figures" / "autoresearch_security_control_matrix.png").exists()
    assert (project_root / "output" / "figures" / "autoresearch_integrity_chain.png").exists()
    assert registry["fig:autoresearch_stage_matrix"]["filename"] == "autoresearch_stage_matrix.png"
    assert registry["fig:ml_candidate_scores"]["filename"] == "ml_candidate_scores.png"
    assert registry["fig:ml_confusion_matrix"]["filename"] == "ml_confusion_matrix.png"
    assert registry["fig:ml_per_class_accuracy"]["filename"] == "ml_per_class_accuracy.png"
    assert registry["fig:ml_learning_curves"]["filename"] == "ml_learning_curves.png"
    assert registry["fig:ml_complexity_accuracy"]["filename"] == "ml_complexity_accuracy.png"
    assert registry["fig:mnist_error_examples"]["filename"] == "mnist_error_examples.png"
    assert registry["fig:ml_calibration_reliability"]["filename"] == "ml_calibration_reliability.png"
    assert registry["fig:ml_classification_metrics_heatmap"]["filename"] == "ml_classification_metrics_heatmap.png"
    assert registry["fig:ml_confusion_pairs"]["filename"] == "ml_confusion_pairs.png"
    assert registry["fig:ml_generalization_gap"]["filename"] == "ml_generalization_gap.png"
    assert registry["fig:ml_robustness_matrix"]["filename"] == "ml_robustness_matrix.png"
    assert registry["fig:ml_probability_margin_distribution"]["filename"] == "ml_probability_margin_distribution.png"
    assert registry["fig:ml_bootstrap_intervals"]["filename"] == "ml_bootstrap_intervals.png"
    assert registry["fig:ml_paired_correctness"]["filename"] == "ml_paired_correctness.png"
    assert registry["fig:ml_selective_accuracy"]["filename"] == "ml_selective_accuracy.png"
    assert registry["fig:ml_probability_quality"]["filename"] == "ml_probability_quality.png"
    assert registry["fig:ml_candidate_rank_stability"]["filename"] == "ml_candidate_rank_stability.png"
    assert registry["fig:autoresearch_candidate_lifecycle"]["filename"] == "autoresearch_candidate_lifecycle.png"
    assert registry["fig:mnist_class_balance"]["filename"] == "mnist_class_balance.png"
    assert registry["fig:mnist_subset_contact_sheet"]["filename"] == "mnist_subset_contact_sheet.png"
    assert registry["fig:autoresearch_closure_flow"]["filename"] == "autoresearch_closure_flow.png"
    assert (
        registry["fig:autoresearch_security_control_matrix"]["filename"] == "autoresearch_security_control_matrix.png"
    )
    assert registry["fig:autoresearch_integrity_chain"]["filename"] == "autoresearch_integrity_chain.png"
    for record in registry.values():
        assert record["metadata"]["source"].startswith(("output/", "data/"))
        assert record["metadata"]["alt_text"]
        assert record["metadata"]["claim_boundary"]


def test_run_derived_visual_diagnostics_match_source_artifacts(
    project_root: Path,
    autoresearch_loop_result: AutoResearchLoopResult,
) -> None:
    assert autoresearch_loop_result.readiness_valid is True
    matrix_path = project_root / "output" / "data" / "ml_confusion_matrix.csv"
    matrix_rows = matrix_path.read_text(encoding="utf-8").splitlines()
    matrix = np.array([[int(value) for value in row.split(",")[1:]] for row in matrix_rows[1:]], dtype=float)
    per_class = np.divide(
        np.diag(matrix),
        matrix.sum(axis=1),
        out=np.zeros(matrix.shape[0], dtype=float),
        where=matrix.sum(axis=1) > 0,
    )
    assert per_class.shape == (10,)
    assert float(per_class.min()) >= 0.0
    assert float(per_class.max()) <= 1.0

    candidate_ledger = json.loads((project_root / "output" / "data" / "ml_candidate_ledger.json").read_text())
    statuses = [candidate["status"] for candidate in candidate_ledger["candidates"]]
    assert statuses.count("accepted") == 1
    assert statuses.count("deferred") == 1
    assert statuses.count("rejected") == 3

    registry = json.loads((project_root / "output" / "figures" / "figure_registry.json").read_text())
    assert registry["fig:ml_per_class_accuracy"]["metadata"]["source"] == "output/data/ml_confusion_matrix.csv"
    assert registry["fig:ml_learning_curves"]["metadata"]["source"] == "output/data/ml_training_history.csv"
    assert registry["fig:ml_complexity_accuracy"]["metadata"]["source"] == "output/data/ml_task_results.json"
    assert registry["fig:mnist_error_examples"]["metadata"]["source"] == "output/data/ml_error_examples.json"
    assert registry["fig:ml_calibration_reliability"]["metadata"]["source"] == "output/data/ml_calibration_report.json"
    assert registry["fig:ml_classification_metrics_heatmap"]["metadata"]["source"] == (
        "output/data/ml_classification_diagnostics.json"
    )
    assert registry["fig:ml_confusion_pairs"]["metadata"]["source"] == (
        "output/data/ml_classification_diagnostics.json"
    )
    assert registry["fig:ml_generalization_gap"]["metadata"]["source"] == (
        "output/data/ml_classification_diagnostics.json"
    )
    assert registry["fig:ml_robustness_matrix"]["metadata"]["source"] == "output/data/ml_robustness_report.json"
    assert registry["fig:ml_probability_margin_distribution"]["metadata"]["source"] == (
        "output/data/ml_probability_diagnostics.json"
    )
    assert registry["fig:ml_bootstrap_intervals"]["metadata"]["source"] == "output/data/ml_bootstrap_intervals.json"
    assert registry["fig:ml_paired_correctness"]["metadata"]["source"] == "output/data/ml_paired_comparison.json"
    assert registry["fig:ml_selective_accuracy"]["metadata"]["source"] == "output/data/ml_statistical_summary.json"
    assert registry["fig:ml_probability_quality"]["metadata"]["source"] == "output/data/ml_statistical_summary.json"
    assert registry["fig:ml_candidate_rank_stability"]["metadata"]["source"] == (
        "output/data/ml_candidate_rank_stability.json"
    )
    assert registry["fig:autoresearch_candidate_lifecycle"]["metadata"]["source"] == (
        "output/data/ml_candidate_ledger.json"
    )
    assert registry["fig:mnist_class_balance"]["metadata"]["source"] == "output/data/ml_class_balance.json"
    assert registry["fig:mnist_subset_contact_sheet"]["metadata"]["source"] == "data/mnist_small.npz"
    assert registry["fig:mnist_subset_contact_sheet"]["metadata"]["source_provenance"] == (
        "data/mnist_small_provenance.json"
    )

    history_rows = (project_root / "output" / "data" / "ml_training_history.csv").read_text().splitlines()
    assert history_rows[0].startswith("candidate_id,model_type,epoch")
    assert len(history_rows) > 1
    error_examples = json.loads((project_root / "output" / "data" / "ml_error_examples.json").read_text())
    assert error_examples["accepted_candidate_id"] == "exp-mlp-tanh-64"
    assert error_examples["examples"]


def test_build_claims_only_supports_existing_files(project_root: Path, repo_root: Path) -> None:
    plan_settings = load_manuscript_loop_settings(project_root)
    from infrastructure.autoresearch import build_autoresearch_plan

    plan = build_autoresearch_plan(repo_root, project_root.name)
    config = build_loop_config(plan, plan_settings)
    missing_path = project_root / "output" / "reports" / "missing_evidence.json"

    claims = build_claims(config, project_root)
    supported_paths = {claim.evidence_path for claim in claims if claim.supported}
    assert "output/reports/missing_evidence.json" not in supported_paths
    assert missing_path.exists() is False


def test_run_autoresearch_loop_on_clean_scaffold(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    project = tmp_path / "template_autoresearch_project"
    source = Path(__file__).resolve().parents[1]
    shutil.copytree(
        source,
        project,
        ignore=shutil.ignore_patterns("output", ".pytest_cache", "__pycache__"),
    )

    result = _run_loop_without_coverage(project, repo_root)

    assert len(result.stage_results) == 7
    assert all(stage.status == "declared" for stage in result.stage_results)
    assert (project / "output" / "data" / "autoresearch_loop.json").exists()
    assert (project / "output" / "data" / "mnist_task_config.json").exists()
    assert (project / "output" / "data" / "ml_task_results.json").exists()
    assert (project / "output" / "data" / "autoresearch_schema_manifest.json").exists()
    assert (project / "output" / "data" / "research_object_manifest.json").exists()
    assert (project / "output" / "data" / "autoresearch_phase_ledger.json").exists()
    assert (project / "output" / "data" / "figure_quality_report.json").exists()
    assert (project / "output" / "data" / "manuscript_variable_provenance.json").exists()
    assert (project / "output" / "reports" / "artifact_manifest.json").exists()
    assert (project / "output" / "reports" / "evidence_registry_full.json").exists() is False


def test_phase_ledger_records_manifest_settlement_without_self_approval(
    project_root: Path,
    autoresearch_loop_result: AutoResearchLoopResult,
) -> None:
    assert autoresearch_loop_result.readiness_valid is True

    ledger = json.loads(
        (project_root / "output" / "data" / "autoresearch_phase_ledger.json").read_text(encoding="utf-8")
    )
    assert ledger["schema"] == "template-autoresearch-phase-ledger-v1"
    assert ledger["project_name"] == "template_autoresearch_project"
    assert ledger["settlement_pass_count"] >= 2
    assert ledger["publication_approved"] is False
    phase_names = [row["phase"] for row in ledger["phases"]]
    assert phase_names[:4] == ["intrinsic_readiness", "core_artifacts", "evidence_registry", "ml_task"]
    assert "extrinsic_readiness" in phase_names
    assert "final_schema_manifest" in phase_names
    assert all(row["artifact_group"] for row in ledger["phases"])
