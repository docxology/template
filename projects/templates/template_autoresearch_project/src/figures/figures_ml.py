"""Compatibility re-exports for ML and MNIST figure writers."""

from __future__ import annotations

from .figures_ml_calibration import (
    write_ml_calibration_reliability_figure,
    write_ml_probability_margin_figure,
    write_ml_probability_quality_figure,
    write_ml_selective_accuracy_figure,
)
from .figures_ml_candidates import (
    write_ml_candidate_rank_stability_figure,
    write_ml_candidate_scores_figure,
    write_ml_complexity_accuracy_figure,
    write_ml_learning_curve_figure,
    write_ml_training_dynamics_figure,
)
from .figures_ml_matrices import (
    write_ml_bootstrap_intervals_figure,
    write_ml_classification_metrics_heatmap,
    write_ml_confusion_matrix_figure,
    write_ml_confusion_pairs_figure,
    write_ml_generalization_gap_figure,
    write_ml_paired_correctness_figure,
    write_ml_per_class_accuracy_figure,
    write_ml_robustness_matrix_figure,
)
from .figures_ml_mnist import (
    write_mnist_class_balance_figure,
    write_mnist_error_examples_figure,
    write_mnist_subset_contact_sheet_figure,
)

__all__ = [
    "write_ml_candidate_scores_figure",
    "write_ml_confusion_matrix_figure",
    "write_ml_learning_curve_figure",
    "write_ml_complexity_accuracy_figure",
    "write_ml_per_class_accuracy_figure",
    "write_mnist_subset_contact_sheet_figure",
    "write_mnist_class_balance_figure",
    "write_mnist_error_examples_figure",
    "write_ml_calibration_reliability_figure",
    "write_ml_classification_metrics_heatmap",
    "write_ml_confusion_pairs_figure",
    "write_ml_generalization_gap_figure",
    "write_ml_robustness_matrix_figure",
    "write_ml_probability_margin_figure",
    "write_ml_bootstrap_intervals_figure",
    "write_ml_paired_correctness_figure",
    "write_ml_selective_accuracy_figure",
    "write_ml_probability_quality_figure",
    "write_ml_candidate_rank_stability_figure",
    "write_ml_training_dynamics_figure",
]
