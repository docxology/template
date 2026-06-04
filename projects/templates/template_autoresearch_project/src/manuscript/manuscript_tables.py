"""Manuscript table builders for the AutoResearch exemplar."""

from __future__ import annotations

from . import manuscript_tables_builders as builders
from src.artifact_loader import LoopArtifacts


def build_table_specs(artifacts: LoopArtifacts) -> dict[str, tuple[str, str, str]]:
    """Build manuscript table variables and provenance pointers."""
    registry = artifacts.figure_registry
    candidate_ledger = artifacts.candidate_ledger
    review_decisions = artifacts.review_decisions
    benchmark_scores = artifacts.benchmark_scores
    artifact_manifest = artifacts.artifact_manifest
    classification = artifacts.classification_diagnostics
    candidate_intervals = artifacts.candidate_intervals
    class_balance = artifacts.class_balance
    calibration = artifacts.calibration_report
    calibration_intervals = artifacts.calibration_bin_intervals
    robustness = artifacts.robustness_report
    probability = artifacts.probability_diagnostics
    bootstrap = artifacts.bootstrap_intervals
    paired = artifacts.paired_comparison
    statistical = artifacts.statistical_summary
    training = artifacts.training_diagnostics
    rank_stability = artifacts.candidate_rank_stability
    candidate_selection = artifacts.candidate_selection_audit
    diagnostic_boundary = artifacts.diagnostic_boundary
    phase_ledger = artifacts.phase_ledger
    figure_quality = artifacts.figure_quality
    security_profile = artifacts.security_profile
    security_threat_model = artifacts.security_threat_model
    security_inventory = artifacts.security_inventory
    security_attestation = artifacts.security_attestation

    table_specs = {
        "FIGURE_METHOD_TABLE": (
            builders.figure_method_table(registry),
            "output/figures/figure_registry.json",
            "/",
        ),
        "ML_CANDIDATE_LEDGER_TABLE": (
            builders.candidate_ledger_table(candidate_ledger),
            "output/data/ml_candidate_ledger.json",
            "/candidates",
        ),
        "AUTORESEARCH_ARTIFACT_TABLE": (
            builders.artifact_manifest_table(artifact_manifest),
            "output/reports/artifact_manifest.json",
            "/entries",
        ),
        "REVIEW_GATE_TABLE": (
            builders.review_gate_table(review_decisions),
            "output/data/review_decisions.json",
            "/decisions",
        ),
        "BENCHMARK_SCORE_TABLE": (
            builders.benchmark_score_table(benchmark_scores),
            "output/data/benchmark_scores.json",
            "/tasks",
        ),
        "CLASSIFICATION_DIAGNOSTICS_TABLE": (
            builders.classification_diagnostics_table(classification),
            "output/data/ml_classification_diagnostics.json",
            "/per_class",
        ),
        "CANDIDATE_INTERVAL_TABLE": (
            builders.candidate_interval_table(candidate_intervals),
            "output/data/ml_candidate_intervals.json",
            "/rows",
        ),
        "CLASS_BALANCE_TABLE": (
            builders.class_balance_table(class_balance),
            "output/data/ml_class_balance.json",
            "/rows",
        ),
        "CALIBRATION_BIN_TABLE": (
            builders.calibration_bin_table(calibration),
            "output/data/ml_calibration_report.json",
            "/bins",
        ),
        "CALIBRATION_BIN_INTERVAL_TABLE": (
            builders.calibration_bin_interval_table(calibration_intervals),
            "output/data/ml_calibration_bin_intervals.json",
            "/bins",
        ),
        "CONFUSION_PAIR_TABLE": (
            builders.confusion_pair_table(classification),
            "output/data/ml_classification_diagnostics.json",
            "/top_confusion_pairs",
        ),
        "ROBUSTNESS_SCORE_TABLE": (
            builders.robustness_score_table(robustness),
            "output/data/ml_robustness_report.json",
            "/rows",
        ),
        "PROBABILITY_DIAGNOSTICS_TABLE": (
            builders.probability_diagnostics_table(probability),
            "output/data/ml_probability_diagnostics.json",
            "/",
        ),
        "BOOTSTRAP_INTERVAL_TABLE": (
            builders.bootstrap_interval_table(bootstrap),
            "output/data/ml_bootstrap_intervals.json",
            "/intervals",
        ),
        "PAIRED_COMPARISON_TABLE": (
            builders.paired_comparison_table(paired),
            "output/data/ml_paired_comparison.json",
            "/",
        ),
        "STATISTICAL_SUMMARY_TABLE": (
            builders.statistical_summary_table(statistical),
            "output/data/ml_statistical_summary.json",
            "/",
        ),
        "SELECTIVE_ACCURACY_TABLE": (
            builders.selective_accuracy_table(statistical),
            "output/data/ml_statistical_summary.json",
            "/coverage_curve",
        ),
        "PROBABILITY_QUALITY_TABLE": (
            builders.probability_quality_table(statistical),
            "output/data/ml_statistical_summary.json",
            "/candidate_probability_quality",
        ),
        "TRAINING_DIAGNOSTICS_TABLE": (
            builders.training_diagnostics_table(training),
            "output/data/ml_training_diagnostics.json",
            "/rows",
        ),
        "CANDIDATE_RANK_STABILITY_TABLE": (
            builders.candidate_rank_stability_table(rank_stability),
            "output/data/ml_candidate_rank_stability.json",
            "/rank_frequencies",
        ),
        "CANDIDATE_SELECTION_AUDIT_TABLE": (
            builders.candidate_selection_audit_table(candidate_selection),
            "output/data/ml_candidate_selection_audit.json",
            "/rows",
        ),
        "DIAGNOSTIC_BOUNDARY_TABLE": (
            builders.diagnostic_boundary_table(diagnostic_boundary),
            "output/data/ml_diagnostic_boundary.json",
            "/rows",
        ),
        "PHASE_LEDGER_TABLE": (
            builders.phase_ledger_table(phase_ledger),
            "output/data/autoresearch_phase_ledger.json",
            "/phases",
        ),
        "FIGURE_QUALITY_TABLE": (
            builders.figure_quality_table(figure_quality),
            "output/data/figure_quality_report.json",
            "/figures",
        ),
        "SECURITY_ARTIFACT_TABLE": (
            builders.security_artifact_table(security_profile, security_inventory, security_attestation),
            "output/data/autoresearch_supply_chain_inventory.json",
            "/",
        ),
        "SECURITY_THREAT_MODEL_TABLE": (
            builders.security_threat_model_table(security_threat_model),
            "output/data/autoresearch_threat_model.json",
            "/threats",
        ),
        "SECURITY_INTEGRITY_TABLE": (
            builders.security_integrity_table(security_attestation),
            "output/data/autoresearch_integrity_attestation.json",
            "/",
        ),
    }
    return table_specs


def variable_provenance_table(provenance: dict[str, dict[str, str]]) -> str:
    """Build the manuscript variable provenance table."""
    return builders.variable_provenance_table(provenance)


__all__ = ["build_table_specs", "variable_provenance_table"]
