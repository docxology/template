"""Contract tests for the public AutoResearch exemplar project."""

from __future__ import annotations

from pathlib import Path

from infrastructure.autoresearch import build_autoresearch_plan
from infrastructure.project.discovery import discover_projects
from infrastructure.project.git_guards import ALLOWED_PROJECT_DIRS
from infrastructure.project.public_scope import public_project_names


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_template_autoresearch_project_is_public_and_discoverable() -> None:
    repo_root = _repo_root()
    project_names = {project.qualified_name for project in discover_projects(repo_root)}

    assert "template_autoresearch_project" in project_names
    assert "template_autoresearch_project" in public_project_names(repo_root)
    assert "projects/template_autoresearch_project/" in ALLOWED_PROJECT_DIRS


def test_template_autoresearch_project_declares_exact_stage_gates() -> None:
    repo_root = _repo_root()
    plan = build_autoresearch_plan(repo_root, "template_autoresearch_project")
    stage_names = {stage.name for stage in plan.stages}

    assert plan.config.strict is True
    assert set(plan.stage_gates) <= stage_names
    assert {"Project Tests", "Project Analysis", "Output Validation"}.issubset(set(plan.stage_gates))
    assert "output/data/autoresearch_loop.json" in plan.required_artifacts
    assert "output/data/manuscript_variable_provenance.json" in plan.required_artifacts
    assert "output/data/manuscript_figure_blocks.json" in plan.required_artifacts
    assert "output/figures/ml_confusion_matrix.png" in plan.required_artifacts
    assert "output/figures/ml_per_class_accuracy.png" in plan.required_artifacts
    assert "output/figures/ml_learning_curves.png" in plan.required_artifacts
    assert "output/figures/ml_complexity_accuracy.png" in plan.required_artifacts
    assert "output/figures/mnist_error_examples.png" in plan.required_artifacts
    assert "output/figures/ml_calibration_reliability.png" in plan.required_artifacts
    assert "output/figures/ml_classification_metrics_heatmap.png" in plan.required_artifacts
    assert "output/figures/ml_confusion_pairs.png" in plan.required_artifacts
    assert "output/figures/ml_generalization_gap.png" in plan.required_artifacts
    assert "output/figures/ml_robustness_matrix.png" in plan.required_artifacts
    assert "output/data/ml_candidate_intervals.json" in plan.required_artifacts
    assert "output/data/ml_class_balance.json" in plan.required_artifacts
    assert "output/data/ml_probability_diagnostics.json" in plan.required_artifacts
    assert "output/data/ml_bootstrap_intervals.json" in plan.required_artifacts
    assert "output/data/ml_paired_comparison.json" in plan.required_artifacts
    assert "output/data/ml_statistical_summary.json" in plan.required_artifacts
    assert "output/data/ml_training_diagnostics.json" in plan.required_artifacts
    assert "output/data/ml_candidate_selection_audit.json" in plan.required_artifacts
    assert "output/data/ml_diagnostic_boundary.json" in plan.required_artifacts
    assert "output/data/autoresearch_security_profile.json" in plan.required_artifacts
    assert "output/data/autoresearch_threat_model.json" in plan.required_artifacts
    assert "output/data/autoresearch_supply_chain_inventory.json" in plan.required_artifacts
    assert "output/data/autoresearch_integrity_attestation.json" in plan.required_artifacts
    assert "output/figures/ml_probability_margin_distribution.png" in plan.required_artifacts
    assert "output/figures/ml_bootstrap_intervals.png" in plan.required_artifacts
    assert "output/figures/ml_paired_correctness.png" in plan.required_artifacts
    assert "output/figures/ml_selective_accuracy.png" in plan.required_artifacts
    assert "output/figures/ml_probability_quality.png" in plan.required_artifacts
    assert "output/figures/ml_training_dynamics.png" in plan.required_artifacts
    assert "output/figures/autoresearch_candidate_lifecycle.png" in plan.required_artifacts
    assert "output/figures/mnist_class_balance.png" in plan.required_artifacts
    assert "output/figures/mnist_subset_contact_sheet.png" in plan.required_artifacts
    assert "output/figures/autoresearch_closure_flow.png" in plan.required_artifacts
    assert "output/figures/autoresearch_security_control_matrix.png" in plan.required_artifacts
    assert "output/figures/autoresearch_integrity_chain.png" in plan.required_artifacts
    assert "output/reports/autoresearch_security_review.md" in plan.required_artifacts
    assert plan.config.security_profile.enabled is True
    assert plan.config.security_profile.external_signing is False


def test_template_autoresearch_project_has_project_docs_contract() -> None:
    project_root = _repo_root() / "projects" / "template_autoresearch_project"
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
    assert "output/data/ml_robustness_report.json" in outputs
    assert "output/data/ml_probability_diagnostics.json" in outputs
    assert "output/data/ml_bootstrap_intervals.json" in outputs
    assert "output/data/ml_paired_comparison.json" in outputs
    assert "output/data/ml_statistical_summary.json" in outputs
    assert "output/data/ml_training_diagnostics.json" in outputs
    assert "output/data/ml_candidate_selection_audit.json" in outputs
    assert "output/data/ml_diagnostic_boundary.json" in outputs
    assert "output/data/autoresearch_security_profile.json" in outputs
    assert "output/data/autoresearch_threat_model.json" in outputs
    assert "output/data/autoresearch_supply_chain_inventory.json" in outputs
    assert "output/data/autoresearch_integrity_attestation.json" in outputs
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
    assert "output/data/ml_robustness_report.json" in project_readme
    assert "output/data/ml_probability_diagnostics.json" in project_readme
    assert "output/data/ml_bootstrap_intervals.json" in project_readme
    assert "output/data/ml_paired_comparison.json" in project_readme
    assert "output/data/ml_statistical_summary.json" in project_readme
    assert "output/data/ml_training_diagnostics.json" in project_readme
    assert "output/data/ml_candidate_selection_audit.json" in project_readme
    assert "output/data/ml_diagnostic_boundary.json" in project_readme
    assert "output/data/autoresearch_security_profile.json" in project_readme
    assert "output/data/autoresearch_threat_model.json" in project_readme
    assert "output/data/autoresearch_supply_chain_inventory.json" in project_readme
    assert "output/data/autoresearch_integrity_attestation.json" in project_readme
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
    project_root = _repo_root() / "projects" / "template_autoresearch_project"

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
