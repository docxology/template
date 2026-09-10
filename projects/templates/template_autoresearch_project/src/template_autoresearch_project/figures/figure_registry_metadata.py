"""Per-label manuscript registry metadata (filename comes from figure_specs dispatch)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FigureRecordSpec:
    """Static registry fields excluding filename, figure_id, caption, and label."""

    caption_field: str
    section: str
    width: str
    placement: str
    generated_by: str
    metadata: dict[str, Any]


FIGURE_RECORD_SPECS: dict[str, FigureRecordSpec] = {
    "fig:autoresearch_stage_matrix": FigureRecordSpec(
        caption_field="stage_caption",
        section="Results",
        width="0.8\\textwidth",
        placement="h",
        generated_by="src.figures.write_stage_matrix_figure",
        metadata={
            "source": "output/data/autoresearch_loop.json",
            "alt_text": "Horizontal bar chart showing configured stages, supported claims, and required artifacts.",
            "claim_boundary": "Readiness artifacts summarize local validation only; publication approval is human.",
        },
    ),
    "fig:ml_candidate_scores": FigureRecordSpec(
        caption_field="score_caption",
        section="Results",
        width="0.8\\textwidth",
        placement="h",
        generated_by="src.figures.write_ml_candidate_scores_figure",
        metadata={
            "source": "output/data/ml_candidate_intervals.json",
            "source_results": "output/data/ml_task_results.json",
            "alt_text": "Lollipop chart comparing baseline and evaluated candidate accuracies with Wilson interval error bars.",
            "claim_boundary": "Scores apply only to the fixed local subset and configured candidates.",
        },
    ),
    "fig:ml_confusion_matrix": FigureRecordSpec(
        caption_field="confusion_caption",
        section="Results",
        width="0.72\\textwidth",
        placement="h",
        generated_by="src.figures.write_ml_confusion_matrix_figure",
        metadata={
            "source": "output/data/ml_confusion_matrix.csv",
            "alt_text": "Ten-by-ten confusion matrix for the accepted candidate on the local test split.",
            "claim_boundary": "Confusion counts diagnose this run only and do not imply full-dataset generalization.",
        },
    ),
    "fig:autoresearch_closure_flow": FigureRecordSpec(
        caption_field="closure_caption",
        section="Results",
        width="0.95\\textwidth",
        placement="h",
        generated_by="src.figures.write_closure_flow_figure",
        metadata={
            "source": "output/data/autoresearch_loop.json",
            "alt_text": "Flow diagram linking program, proposals, evaluation, ledgers, claims, manuscript, readiness, and review.",
            "claim_boundary": "The workflow is file-backed and inspectable but not self-approving.",
        },
    ),
    "fig:ml_per_class_accuracy": FigureRecordSpec(
        caption_field="per_class_caption",
        section="Results",
        width="0.78\\textwidth",
        placement="h",
        generated_by="src.figures.write_ml_per_class_accuracy_figure",
        metadata={
            "source": "output/data/ml_confusion_matrix.csv",
            "alt_text": "Bar chart of accepted-candidate accuracy for each true digit class.",
            "claim_boundary": "Per-class values diagnose this local split only and do not certify robustness.",
        },
    ),
    "fig:ml_learning_curves": FigureRecordSpec(
        caption_field="learning_curve_caption",
        section="Results",
        width="0.82\\textwidth",
        placement="h",
        generated_by="src.figures.write_ml_learning_curve_figure",
        metadata={
            "source": "output/data/ml_training_history.csv",
            "alt_text": "Line chart of held-out accuracy by epoch for each evaluated candidate.",
            "claim_boundary": "Learning curves diagnose configured training only, not convergence in general.",
        },
    ),
    "fig:ml_complexity_accuracy": FigureRecordSpec(
        caption_field="complexity_caption",
        section="Results",
        width="0.78\\textwidth",
        placement="h",
        generated_by="src.figures.write_ml_complexity_accuracy_figure",
        metadata={
            "source": "output/data/ml_task_results.json",
            "alt_text": "Scatter plot comparing parameter count and held-out accuracy.",
            "claim_boundary": "The plot compares this bounded candidate set and does not infer a scaling law.",
        },
    ),
    "fig:mnist_error_examples": FigureRecordSpec(
        caption_field="error_caption",
        section="Results",
        width="0.82\\textwidth",
        placement="h",
        generated_by="src.figures.write_mnist_error_examples_figure",
        metadata={
            "source": "output/data/ml_error_examples.json",
            "source_images": "data/mnist_small.npz",
            "alt_text": "Grid of accepted-candidate misclassified test examples with true and predicted labels.",
            "claim_boundary": "Examples are qualitative diagnostics for this run, not an error taxonomy.",
        },
    ),
    "fig:ml_calibration_reliability": FigureRecordSpec(
        caption_field="calibration_caption",
        section="Results",
        width="0.82\\textwidth",
        placement="h",
        generated_by="src.figures.write_ml_calibration_reliability_figure",
        metadata={
            "source": "output/data/ml_calibration_report.json",
            "alt_text": "Reliability curve with accepted-candidate confidence-bin counts.",
            "claim_boundary": "Calibration values describe the fixed local split only.",
        },
    ),
    "fig:ml_classification_metrics_heatmap": FigureRecordSpec(
        caption_field="class_metrics_caption",
        section="Results",
        width="0.76\\textwidth",
        placement="h",
        generated_by="src.figures.write_ml_classification_metrics_heatmap",
        metadata={
            "source": "output/data/ml_classification_diagnostics.json",
            "alt_text": "Heatmap of per-class precision, recall, and F1 for the accepted candidate.",
            "claim_boundary": "Class metrics diagnose this run only and are not full-dataset estimates.",
        },
    ),
    "fig:ml_confusion_pairs": FigureRecordSpec(
        caption_field="confusion_pairs_caption",
        section="Results",
        width="0.82\\textwidth",
        placement="h",
        generated_by="src.figures.write_ml_confusion_pairs_figure",
        metadata={
            "source": "output/data/ml_classification_diagnostics.json",
            "alt_text": "Horizontal bar chart of the most frequent non-diagonal confusion pairs.",
            "claim_boundary": "Pair counts identify local error cases and are not a general taxonomy.",
        },
    ),
    "fig:ml_generalization_gap": FigureRecordSpec(
        caption_field="generalization_caption",
        section="Results",
        width="0.82\\textwidth",
        placement="h",
        generated_by="src.figures.write_ml_generalization_gap_figure",
        metadata={
            "source": "output/data/ml_classification_diagnostics.json",
            "alt_text": "Grouped bars comparing train and test accuracy and loss by candidate.",
            "claim_boundary": "Gaps are local bounded-loop diagnostics, not convergence guarantees.",
        },
    ),
    "fig:ml_robustness_matrix": FigureRecordSpec(
        caption_field="robustness_caption",
        section="Results",
        width="0.84\\textwidth",
        placement="h",
        generated_by="src.figures.write_ml_robustness_matrix_figure",
        metadata={
            "source": "output/data/ml_robustness_report.json",
            "alt_text": "Heatmap of candidate accuracy under identity, shift, and low-contrast transforms.",
            "claim_boundary": "Deterministic perturbations are a smoke test and do not certify robustness.",
        },
    ),
    "fig:ml_probability_margin_distribution": FigureRecordSpec(
        caption_field="probability_caption",
        section="Results",
        width="0.82\\textwidth",
        placement="h",
        generated_by="src.figures.write_ml_probability_margin_figure",
        metadata={
            "source": "output/data/ml_probability_diagnostics.json",
            "source_predictions": "output/data/ml_prediction_records.json",
            "alt_text": "Two histograms of accepted-candidate confidence and prediction margin by correctness.",
            "claim_boundary": "Distributions are descriptive diagnostics for the fixed local test split.",
        },
    ),
    "fig:ml_bootstrap_intervals": FigureRecordSpec(
        caption_field="bootstrap_caption",
        section="Results",
        width="0.78\\textwidth",
        placement="h",
        generated_by="src.figures.write_ml_bootstrap_intervals_figure",
        metadata={
            "source": "output/data/ml_bootstrap_intervals.json",
            "alt_text": "Horizontal interval chart for accepted-candidate accuracy and macro F1.",
            "claim_boundary": "Bootstrap intervals summarize local test-set resampling only.",
        },
    ),
    "fig:ml_paired_correctness": FigureRecordSpec(
        caption_field="paired_caption",
        section="Results",
        width="0.66\\textwidth",
        placement="h",
        generated_by="src.figures.write_ml_paired_correctness_figure",
        metadata={
            "source": "output/data/ml_paired_comparison.json",
            "alt_text": "Two-by-two heatmap of baseline and accepted-candidate correctness on matched examples.",
            "claim_boundary": "Matched comparison is limited to the fixed local test split.",
        },
    ),
    "fig:ml_selective_accuracy": FigureRecordSpec(
        caption_field="selective_caption",
        section="Results",
        width="0.76\\textwidth",
        placement="h",
        generated_by="src.figures.write_ml_selective_accuracy_figure",
        metadata={
            "source": "output/data/ml_statistical_summary.json",
            "alt_text": "Line chart comparing coverage, selective accuracy, and overall accuracy by confidence threshold.",
            "claim_boundary": "Selective accuracy describes thresholded predictions on the fixed local split only.",
        },
    ),
    "fig:ml_probability_quality": FigureRecordSpec(
        caption_field="probability_quality_caption",
        section="Results",
        width="0.82\\textwidth",
        placement="h",
        generated_by="src.figures.write_ml_probability_quality_figure",
        metadata={
            "source": "output/data/ml_statistical_summary.json",
            "alt_text": "Paired horizontal bar charts of Brier score and negative log likelihood with the accepted candidate highlighted.",
            "claim_boundary": "Probability-quality metrics compare the configured evaluated candidates only.",
        },
    ),
    "fig:ml_training_dynamics": FigureRecordSpec(
        caption_field="training_dynamics_caption",
        section="Results",
        width="0.84\\textwidth",
        placement="h",
        generated_by="src.figures.write_ml_training_dynamics_figure",
        metadata={
            "source": "output/data/ml_training_diagnostics.json",
            "source_history": "output/data/ml_training_history.csv",
            "alt_text": "Two-panel chart showing final versus best held-out accuracy and train-test accuracy gaps by candidate.",
            "claim_boundary": "Training dynamics diagnose this configured deterministic run only.",
        },
    ),
    "fig:ml_candidate_rank_stability": FigureRecordSpec(
        caption_field="rank_stability_caption",
        section="Results",
        width="0.82\\textwidth",
        placement="h",
        generated_by="src.figures.write_ml_candidate_rank_stability_figure",
        metadata={
            "source": "output/data/ml_candidate_rank_stability.json",
            "source_results": "output/data/ml_task_results.json",
            "alt_text": "Two-panel chart of candidate top-rank frequency and mean rank under deterministic bootstrap resampling.",
            "claim_boundary": "Rank stability describes local resampling behavior, not model-selection certainty.",
        },
    ),
    "fig:autoresearch_candidate_lifecycle": FigureRecordSpec(
        caption_field="lifecycle_caption",
        section="Results",
        width="0.78\\textwidth",
        placement="h",
        generated_by="src.figures.write_candidate_lifecycle_figure",
        metadata={
            "source": "output/data/ml_candidate_ledger.json",
            "alt_text": "Bar chart of proposed, evaluated, accepted, rejected, and deferred candidate counts.",
            "claim_boundary": "Lifecycle counts describe bounded orchestration, not autonomous approval.",
        },
    ),
    "fig:mnist_class_balance": FigureRecordSpec(
        caption_field="class_balance_caption",
        section="Methodology",
        width="0.78\\textwidth",
        placement="h",
        generated_by="src.figures.write_mnist_class_balance_figure",
        metadata={
            "source": "output/data/ml_class_balance.json",
            "source_fixture": "data/mnist_small.npz",
            "source_provenance": "data/mnist_small_provenance.json",
            "alt_text": "Grouped bar chart showing train and test example counts for each digit class.",
            "claim_boundary": "Class counts describe the local fixed fixture and are not population statistics.",
        },
    ),
    "fig:mnist_subset_contact_sheet": FigureRecordSpec(
        caption_field="contact_sheet_caption",
        section="Methodology",
        width="0.78\\textwidth",
        placement="h",
        generated_by="src.figures.write_mnist_subset_contact_sheet_figure",
        metadata={
            "source": "data/mnist_small.npz",
            "source_provenance": "data/mnist_small_provenance.json",
            "alt_text": "Two-row grid with one local handwritten digit example for each class zero through nine.",
            "claim_boundary": "The sheet illustrates the local fixed subset and is not a statistical sample claim.",
        },
    ),
    "fig:autoresearch_security_control_matrix": FigureRecordSpec(
        caption_field="security_control_caption",
        section="Methodology",
        width="0.84\\textwidth",
        placement="h",
        generated_by="src.figures.write_security_control_matrix_figure",
        metadata={
            "source": "output/data/autoresearch_threat_model.json",
            "alt_text": "Matrix of local security controls mapped to framework-inspired evidence surfaces and status.",
            "claim_boundary": "Controls are local research-artifact safeguards, not production security certification.",
        },
    ),
    "fig:autoresearch_integrity_chain": FigureRecordSpec(
        caption_field="integrity_chain_caption",
        section="Results",
        width="0.84\\textwidth",
        placement="h",
        generated_by="src.figures.write_security_integrity_chain_figure",
        metadata={
            "source": "output/data/autoresearch_integrity_attestation.json",
            "source_inventory": "output/data/autoresearch_supply_chain_inventory.json",
            "alt_text": "Process-chain diagram and bar chart summarizing checked, missing, and mismatched local artifact records.",
            "claim_boundary": "Integrity checks are local SHA-256 observations and are not externally signed provenance.",
        },
    ),
}

__all__ = ["FIGURE_RECORD_SPECS", "FigureRecordSpec"]
