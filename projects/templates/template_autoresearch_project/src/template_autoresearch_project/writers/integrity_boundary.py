"""Reviewed upstream checksum boundary; all other outputs are derivative references."""

from pathlib import Path

PRIMARY_AUTHORITY = "output/reports/artifact_manifest.json"

# These leaf data/report writers finish before security/catalog/presentation settlement.
# Unknown or inherited outputs are deliberately references, never guessed leaf evidence.
UPSTREAM_OUTPUTS = frozenset(
    "output/data/" + name
    for name in (
        "autoresearch_plan.json", "autoresearch_stage_matrix.csv", "mnist_task_config.json",
        "ml_task_results.json", "ml_candidate_ledger.json", "ml_confusion_matrix.csv",
        "ml_training_history.csv", "ml_error_examples.json", "ml_prediction_records.json",
        "ml_classification_diagnostics.json", "ml_candidate_intervals.json", "ml_class_balance.json",
        "ml_calibration_report.json", "ml_calibration_bin_intervals.json", "ml_robustness_report.json",
        "ml_probability_diagnostics.json", "ml_bootstrap_intervals.json", "ml_paired_comparison.json",
        "ml_statistical_summary.json", "ml_training_diagnostics.json", "ml_candidate_rank_stability.json",
        "ml_candidate_selection_audit.json", "ml_diagnostic_boundary.json", "research_program.json",
        "idea_ledger.json", "run_ledger.json", "review_decisions.json", "benchmark_scores.json",
        "benchmark_boundary.json",
    )
) | frozenset((
    "output/reports/ml_experiment_report.md", "output/reports/ml_benchmark_score.json",
    "output/reports/benchmark_readiness_smoke.json",
))


def is_upstream_output(project_root: Path, path: Path) -> bool:
    """Admit only reviewed, in-project leaf records to secondary checksum claims."""
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix() in UPSTREAM_OUTPUTS
    except ValueError:
        return False


def derivative_reference(relative_path: str) -> dict[str, object]:
    """Name a derivative without claiming its existence, size, emptiness or bytes."""
    return {
        "path": relative_path,
        "record_kind": "derivative_reference",
        "integrity_authority": PRIMARY_AUTHORITY,
    }
