"""Contract tests for the public AutoResearch exemplar project."""

from __future__ import annotations

from pathlib import Path

from infrastructure.autoresearch import build_autoresearch_plan
from infrastructure.project.discovery import discover_projects
from infrastructure.project.git_guards import ALLOWED_PROJECT_DIRS
from infrastructure.project.public_scope import public_project_names

EXPECTED_ARTIFACTS: frozenset[str] = frozenset({
    "output/data/autoresearch_claims.json",
    "output/data/autoresearch_integrity_attestation.json",
    "output/data/autoresearch_inventory_export.json",
    "output/data/autoresearch_loop.json",
    "output/data/autoresearch_phase_ledger.json",
    "output/data/autoresearch_plan.json",
    "output/data/autoresearch_review_packet.json",
    "output/data/autoresearch_schema_manifest.json",
    "output/data/autoresearch_security_profile.json",
    "output/data/autoresearch_stage_matrix.csv",
    "output/data/autoresearch_supply_chain_inventory.json",
    "output/data/autoresearch_threat_model.json",
    "output/data/benchmark_scores.json",
    "output/data/figure_quality_report.json",
    "output/data/idea_ledger.json",
    "output/data/manuscript_figure_blocks.json",
    "output/data/manuscript_variable_provenance.json",
    "output/data/manuscript_variables.json",
    "output/data/ml_bootstrap_intervals.json",
    "output/data/ml_calibration_bin_intervals.json",
    "output/data/ml_calibration_report.json",
    "output/data/ml_candidate_intervals.json",
    "output/data/ml_candidate_ledger.json",
    "output/data/ml_candidate_rank_stability.json",
    "output/data/ml_candidate_selection_audit.json",
    "output/data/ml_class_balance.json",
    "output/data/ml_classification_diagnostics.json",
    "output/data/ml_confusion_matrix.csv",
    "output/data/ml_diagnostic_boundary.json",
    "output/data/ml_error_examples.json",
    "output/data/ml_paired_comparison.json",
    "output/data/ml_prediction_records.json",
    "output/data/ml_probability_diagnostics.json",
    "output/data/ml_robustness_report.json",
    "output/data/ml_statistical_summary.json",
    "output/data/ml_task_results.json",
    "output/data/ml_training_diagnostics.json",
    "output/data/ml_training_history.csv",
    "output/data/mnist_task_config.json",
    "output/data/research_object_manifest.json",
    "output/data/research_program.json",
    "output/data/review_decisions.json",
    "output/data/run_ledger.json",
    "output/figures/autoresearch_candidate_lifecycle.png",
    "output/figures/autoresearch_closure_flow.png",
    "output/figures/autoresearch_integrity_chain.png",
    "output/figures/autoresearch_security_control_matrix.png",
    "output/figures/autoresearch_stage_matrix.png",
    "output/figures/figure_registry.json",
    "output/figures/ml_bootstrap_intervals.png",
    "output/figures/ml_calibration_reliability.png",
    "output/figures/ml_candidate_rank_stability.png",
    "output/figures/ml_candidate_scores.png",
    "output/figures/ml_classification_metrics_heatmap.png",
    "output/figures/ml_complexity_accuracy.png",
    "output/figures/ml_confusion_matrix.png",
    "output/figures/ml_confusion_pairs.png",
    "output/figures/ml_generalization_gap.png",
    "output/figures/ml_learning_curves.png",
    "output/figures/ml_paired_correctness.png",
    "output/figures/ml_per_class_accuracy.png",
    "output/figures/ml_probability_margin_distribution.png",
    "output/figures/ml_probability_quality.png",
    "output/figures/ml_robustness_matrix.png",
    "output/figures/ml_selective_accuracy.png",
    "output/figures/ml_training_dynamics.png",
    "output/figures/mnist_class_balance.png",
    "output/figures/mnist_error_examples.png",
    "output/figures/mnist_subset_contact_sheet.png",
    "output/reports/artifact_manifest.json",
    "output/reports/autoresearch_loop.json",
    "output/reports/autoresearch_loop.md",
    "output/reports/autoresearch_review_packet.md",
    "output/reports/autoresearch_security_review.md",
    "output/reports/autoresearch_summary.md",
    "output/reports/benchmark_readiness_smoke.json",
    "output/reports/ml_benchmark_score.json",
    "output/reports/ml_experiment_report.md",
})

EXPECTED_STAGE_GATES: frozenset[str] = frozenset({
    "Project Tests",
    "Project Analysis",
    "Output Validation",
    "Copy Outputs",
})


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_template_autoresearch_project_is_public_and_discoverable() -> None:
    repo_root = _repo_root()
    project_names = {project.qualified_name for project in discover_projects(repo_root)}

    assert "templates/template_autoresearch_project" in project_names
    assert "templates/template_autoresearch_project" in public_project_names(repo_root)
    assert "projects/templates/template_autoresearch_project/" in ALLOWED_PROJECT_DIRS


def test_template_autoresearch_project_declares_exact_stage_gates() -> None:
    repo_root = _repo_root()
    plan = build_autoresearch_plan(repo_root, "templates/template_autoresearch_project")

    assert plan.config.strict is True
    assert set(plan.stage_gates) == EXPECTED_STAGE_GATES
    assert set(plan.required_artifacts) == EXPECTED_ARTIFACTS
    assert plan.config.security_profile.enabled is True
    assert plan.config.security_profile.external_signing is False


def test_template_autoresearch_project_has_project_docs_contract() -> None:
    project_root = _repo_root() / "projects" / "templates" / "template_autoresearch_project"
    docs_dir = project_root / "docs"
    required_docs = {
        "README.md",
        "AGENTS.md",
        "configuration.md",
        "outputs.md",
        "runbook.md",
    }

    assert docs_dir.is_dir()
    for filename in required_docs:
        path = docs_dir / filename
        assert path.is_file(), filename
        text = path.read_text(encoding="utf-8")
        assert "template_autoresearch_project" in text
        assert "{{" not in text
        assert "}}" not in text

    readme = (docs_dir / "README.md").read_text(encoding="utf-8")
    assert "./run.sh --pipeline --project template_autoresearch_project" in readme
    outputs = (docs_dir / "outputs.md").read_text(encoding="utf-8")
    assert "output/reports/autoresearch_review_packet.md" in outputs
    assert "output/data/autoresearch_stage_matrix.csv" in outputs
    assert "output/data/research_program.json" in outputs
    assert "output/data/idea_ledger.json" in outputs
    assert "output/data/run_ledger.json" in outputs
    assert "output/data/review_decisions.json" in outputs
    assert "output/data/benchmark_scores.json" in outputs
    assert "output/data/mnist_task_config.json" in outputs
    assert "output/data/ml_task_results.json" in outputs
    assert "output/data/ml_candidate_ledger.json" in outputs
    assert "output/data/ml_confusion_matrix.csv" in outputs
    assert "output/data/ml_training_history.csv" in outputs
    assert "output/data/ml_error_examples.json" in outputs
    assert "output/data/ml_prediction_records.json" in outputs
    assert "output/data/ml_candidate_intervals.json" in outputs
    assert "output/data/ml_class_balance.json" in outputs
    assert "output/data/ml_classification_diagnostics.json" in outputs
    assert "output/data/ml_calibration_report.json" in outputs
    assert "output/data/ml_calibration_bin_intervals.json" in outputs
    assert "output/data/ml_robustness_report.json" in outputs
    assert "output/data/ml_probability_diagnostics.json" in outputs
    assert "output/data/ml_bootstrap_intervals.json" in outputs
    assert "output/data/ml_paired_comparison.json" in outputs
    assert "output/data/ml_statistical_summary.json" in outputs
    assert "output/data/ml_training_diagnostics.json" in outputs
    assert "output/data/ml_candidate_rank_stability.json" in outputs
    assert "output/data/ml_candidate_selection_audit.json" in outputs
    assert "output/data/ml_diagnostic_boundary.json" in outputs
    assert "output/data/autoresearch_phase_ledger.json" in outputs
    assert "output/data/figure_quality_report.json" in outputs
    assert "output/data/autoresearch_security_profile.json" in outputs
    assert "output/data/autoresearch_threat_model.json" in outputs
    assert "output/data/autoresearch_supply_chain_inventory.json" in outputs
    assert "output/data/autoresearch_inventory_export.json" in outputs
    assert "output/data/autoresearch_integrity_attestation.json" in outputs
    assert "output/data/autoresearch_schema_manifest.json" in outputs
    assert "output/data/research_object_manifest.json" in outputs
    assert "output/data/manuscript_variable_provenance.json" in outputs
    assert "output/data/manuscript_figure_blocks.json" in outputs
    assert "output/figures/ml_confusion_matrix.png" in outputs
    assert "output/figures/ml_per_class_accuracy.png" in outputs
    assert "output/figures/ml_learning_curves.png" in outputs
    assert "output/figures/ml_complexity_accuracy.png" in outputs
    assert "output/figures/mnist_error_examples.png" in outputs
    assert "output/figures/ml_calibration_reliability.png" in outputs
    assert "output/figures/ml_classification_metrics_heatmap.png" in outputs
    assert "output/figures/ml_confusion_pairs.png" in outputs
    assert "output/figures/ml_generalization_gap.png" in outputs
    assert "output/figures/ml_robustness_matrix.png" in outputs
    assert "output/figures/ml_probability_margin_distribution.png" in outputs
    assert "output/figures/ml_bootstrap_intervals.png" in outputs
    assert "output/figures/ml_paired_correctness.png" in outputs
    assert "output/figures/ml_selective_accuracy.png" in outputs
    assert "output/figures/ml_probability_quality.png" in outputs
    assert "output/figures/ml_training_dynamics.png" in outputs
    assert "output/figures/ml_candidate_rank_stability.png" in outputs
    assert "output/figures/autoresearch_candidate_lifecycle.png" in outputs
    assert "output/figures/mnist_class_balance.png" in outputs
    assert "output/figures/mnist_subset_contact_sheet.png" in outputs
    assert "output/figures/autoresearch_closure_flow.png" in outputs
    assert "output/figures/autoresearch_security_control_matrix.png" in outputs
    assert "output/figures/autoresearch_integrity_chain.png" in outputs
    assert "output/reports/ml_experiment_report.md" in outputs
    assert "output/reports/ml_benchmark_score.json" in outputs
    assert "output/reports/autoresearch_security_review.md" in outputs

    project_readme = (project_root / "README.md").read_text(encoding="utf-8")
    assert "output/data/manuscript_variable_provenance.json" in project_readme
    assert "output/data/manuscript_figure_blocks.json" in project_readme
    assert "output/data/ml_prediction_records.json" in project_readme
    assert "output/data/ml_candidate_intervals.json" in project_readme
    assert "output/data/ml_class_balance.json" in project_readme
    assert "output/data/ml_classification_diagnostics.json" in project_readme
    assert "output/data/ml_calibration_report.json" in project_readme
    assert "output/data/ml_calibration_bin_intervals.json" in project_readme
    assert "output/data/ml_robustness_report.json" in project_readme
    assert "output/data/ml_probability_diagnostics.json" in project_readme
    assert "output/data/ml_bootstrap_intervals.json" in project_readme
    assert "output/data/ml_paired_comparison.json" in project_readme
    assert "output/data/ml_statistical_summary.json" in project_readme
    assert "output/data/ml_training_diagnostics.json" in project_readme
    assert "output/data/ml_candidate_rank_stability.json" in project_readme
    assert "output/data/ml_candidate_selection_audit.json" in project_readme
    assert "output/data/ml_diagnostic_boundary.json" in project_readme
    assert "output/data/autoresearch_phase_ledger.json" in project_readme
    assert "output/data/figure_quality_report.json" in project_readme
    assert "output/data/autoresearch_security_profile.json" in project_readme
    assert "output/data/autoresearch_threat_model.json" in project_readme
    assert "output/data/autoresearch_supply_chain_inventory.json" in project_readme
    assert "output/data/autoresearch_inventory_export.json" in project_readme
    assert "output/data/autoresearch_integrity_attestation.json" in project_readme
    assert "output/data/autoresearch_schema_manifest.json" in project_readme
    assert "output/data/research_object_manifest.json" in project_readme
    assert "output/figures/autoresearch_closure_flow.png" in project_readme
    assert "output/figures/ml_confusion_matrix.png" in project_readme
    assert "output/figures/ml_per_class_accuracy.png" in project_readme
    assert "output/figures/ml_learning_curves.png" in project_readme
    assert "output/figures/ml_complexity_accuracy.png" in project_readme
    assert "output/figures/mnist_error_examples.png" in project_readme
    assert "output/figures/ml_calibration_reliability.png" in project_readme
    assert "output/figures/ml_classification_metrics_heatmap.png" in project_readme
    assert "output/figures/ml_confusion_pairs.png" in project_readme
    assert "output/figures/ml_generalization_gap.png" in project_readme
    assert "output/figures/ml_robustness_matrix.png" in project_readme
    assert "output/figures/ml_probability_margin_distribution.png" in project_readme
    assert "output/figures/ml_bootstrap_intervals.png" in project_readme
    assert "output/figures/ml_paired_correctness.png" in project_readme
    assert "output/figures/ml_selective_accuracy.png" in project_readme
    assert "output/figures/ml_probability_quality.png" in project_readme
    assert "output/figures/ml_training_dynamics.png" in project_readme
    assert "output/figures/ml_candidate_rank_stability.png" in project_readme
    assert "output/figures/autoresearch_candidate_lifecycle.png" in project_readme
    assert "output/figures/mnist_class_balance.png" in project_readme
    assert "output/figures/mnist_subset_contact_sheet.png" in project_readme
    assert "output/figures/autoresearch_security_control_matrix.png" in project_readme
    assert "output/figures/autoresearch_integrity_chain.png" in project_readme
    assert "output/reports/autoresearch_security_review.md" in project_readme

    agent_notes = (project_root / "AGENTS.md").read_text(encoding="utf-8")
    assert "write_final_visual_artifacts()" in agent_notes
    assert "write_manuscript_hydration_artifacts()" in agent_notes
    assert "strict tokenization" in agent_notes


def test_template_autoresearch_project_declares_program_and_seed_ideas() -> None:
    project_root = _repo_root() / "projects" / "templates" / "template_autoresearch_project"

    program = project_root / "program.md"
    seed_ideas = project_root / "seed_ideas.yaml"
    mnist_task = project_root / "mnist_task.yaml"

    assert program.is_file()
    assert "human-authored research program" in program.read_text(encoding="utf-8")
    assert seed_ideas.is_file()
    assert "accepted" in seed_ideas.read_text(encoding="utf-8")
    assert "idea-ml-loop" in seed_ideas.read_text(encoding="utf-8")
    assert mnist_task.is_file()
    assert "tiny_patch_transformer" in mnist_task.read_text(encoding="utf-8")
