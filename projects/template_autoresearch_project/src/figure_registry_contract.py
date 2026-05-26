"""Registry-level figure caption and method contracts."""

from __future__ import annotations

from typing import Any

FIGURE_VALIDATION_NOTE = (
    "Registry metadata records the generation method, source artifact, and claim boundary for validation."
)


def finalize_figure_registry(records: dict[str, dict[str, object]]) -> dict[str, dict[str, object]]:
    """Add method and validation metadata to figure registry records."""
    for label, record in records.items():
        method = figure_method(label)
        record["caption"] = caption_with_contract(str(record.get("caption", "")), method)
        metadata = _metadata(record)
        metadata["method"] = method
        metadata["validated_by"] = (
            "Stage 04 output validation, figure registry validation, and AutoResearch readiness validation."
        )
        record["metadata"] = metadata
    return records


def caption_with_contract(caption: str, method: str) -> str:
    """Attach the method sentence and common figure-validation phrase to a caption."""
    if FIGURE_VALIDATION_NOTE in caption:
        return caption
    return f"{caption} Generation method: {method} {FIGURE_VALIDATION_NOTE}"


def figure_method(label: str) -> str:
    """Return the concise generation method for a figure label."""
    return _FIGURE_METHODS.get(label, "Registered deterministic figure generated from local artifacts.")


def _metadata(record: dict[str, object]) -> dict[str, Any]:
    metadata = record.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


_FIGURE_METHODS = {
    "fig:autoresearch_stage_matrix": "Horizontal count summary from final loop metrics.",
    "fig:ml_candidate_scores": "Lollipop accuracy comparison with Wilson interval error bars and direct labels.",
    "fig:ml_confusion_matrix": "Row-normalized heatmap with cell counts and row percentages.",
    "fig:autoresearch_closure_flow": "File-backed process-flow diagram from final loop state.",
    "fig:ml_per_class_accuracy": "Per-class accuracy bars computed from the confusion matrix diagonal.",
    "fig:ml_learning_curves": "Epoch-level held-out accuracy lines with accepted best-epoch marker.",
    "fig:ml_complexity_accuracy": "Log-parameter scatter plot against held-out accuracy.",
    "fig:mnist_error_examples": "Deterministic grid of the first accepted-candidate misclassifications.",
    "fig:ml_calibration_reliability": "Reliability curve with confidence-bin support histogram.",
    "fig:ml_classification_metrics_heatmap": "Per-class precision, recall, and F1 heatmap.",
    "fig:ml_confusion_pairs": "Ranked off-diagonal confusion-pair bars with true-class error rates.",
    "fig:ml_generalization_gap": "Grouped train/test accuracy and loss bars by evaluated candidate.",
    "fig:ml_robustness_matrix": "Candidate-by-transform accuracy heatmap for deterministic perturbations.",
    "fig:ml_probability_margin_distribution": "Confidence and margin histograms split by correctness.",
    "fig:ml_bootstrap_intervals": "Horizontal percentile-bootstrap interval plot.",
    "fig:ml_paired_correctness": "Matched accepted-versus-baseline correctness heatmap.",
    "fig:ml_selective_accuracy": "Confidence-threshold coverage and selective-accuracy line chart.",
    "fig:ml_probability_quality": "Brier score and negative-log-likelihood bar comparison.",
    "fig:ml_training_dynamics": "Final and best-epoch accuracy bars plus train-test gap bars.",
    "fig:autoresearch_candidate_lifecycle": "Candidate lifecycle status-count bar chart.",
    "fig:mnist_subset_contact_sheet": "Class-balanced contact sheet from fixed local MNIST arrays.",
    "fig:mnist_class_balance": "Grouped train/test class-count bars from the local MNIST fixture.",
    "fig:autoresearch_security_control_matrix": "Structured control matrix from local threat-model controls.",
    "fig:autoresearch_integrity_chain": "Local checksum attestation chain with checked, missing, and mismatch counts.",
}
