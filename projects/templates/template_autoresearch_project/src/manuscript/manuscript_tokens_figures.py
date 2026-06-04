"""Figure block generation for manuscript token hydration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.json_coerce import mapping
from .manuscript_tokens_format import string_value

FIGURE_BLOCK_KEYS = frozenset(
    {
        "FIGURE_BLOCK_STAGE_MATRIX",
        "FIGURE_BLOCK_CANDIDATE_SCORES",
        "FIGURE_BLOCK_CONFUSION_MATRIX",
        "FIGURE_BLOCK_PER_CLASS_ACCURACY",
        "FIGURE_BLOCK_LEARNING_CURVES",
        "FIGURE_BLOCK_COMPLEXITY_ACCURACY",
        "FIGURE_BLOCK_ERROR_EXAMPLES",
        "FIGURE_BLOCK_CALIBRATION_RELIABILITY",
        "FIGURE_BLOCK_CLASSIFICATION_METRICS",
        "FIGURE_BLOCK_CONFUSION_PAIRS",
        "FIGURE_BLOCK_GENERALIZATION_GAP",
        "FIGURE_BLOCK_ROBUSTNESS_MATRIX",
        "FIGURE_BLOCK_PROBABILITY_MARGIN",
        "FIGURE_BLOCK_BOOTSTRAP_INTERVALS",
        "FIGURE_BLOCK_PAIRED_CORRECTNESS",
        "FIGURE_BLOCK_SELECTIVE_ACCURACY",
        "FIGURE_BLOCK_PROBABILITY_QUALITY",
        "FIGURE_BLOCK_TRAINING_DYNAMICS",
        "FIGURE_BLOCK_CANDIDATE_RANK_STABILITY",
        "FIGURE_BLOCK_CANDIDATE_LIFECYCLE",
        "FIGURE_BLOCK_DATASET_CLASS_BALANCE",
        "FIGURE_BLOCK_DATASET_CONTACT_SHEET",
        "FIGURE_BLOCK_CLOSURE_FLOW",
        "FIGURE_BLOCK_SECURITY_CONTROL_MATRIX",
        "FIGURE_BLOCK_INTEGRITY_CHAIN",
    }
)

_FIGURE_BLOCK_LABELS = {
    "FIGURE_BLOCK_STAGE_MATRIX": "fig:autoresearch_stage_matrix",
    "FIGURE_BLOCK_CANDIDATE_SCORES": "fig:ml_candidate_scores",
    "FIGURE_BLOCK_CONFUSION_MATRIX": "fig:ml_confusion_matrix",
    "FIGURE_BLOCK_PER_CLASS_ACCURACY": "fig:ml_per_class_accuracy",
    "FIGURE_BLOCK_LEARNING_CURVES": "fig:ml_learning_curves",
    "FIGURE_BLOCK_COMPLEXITY_ACCURACY": "fig:ml_complexity_accuracy",
    "FIGURE_BLOCK_ERROR_EXAMPLES": "fig:mnist_error_examples",
    "FIGURE_BLOCK_CALIBRATION_RELIABILITY": "fig:ml_calibration_reliability",
    "FIGURE_BLOCK_CLASSIFICATION_METRICS": "fig:ml_classification_metrics_heatmap",
    "FIGURE_BLOCK_CONFUSION_PAIRS": "fig:ml_confusion_pairs",
    "FIGURE_BLOCK_GENERALIZATION_GAP": "fig:ml_generalization_gap",
    "FIGURE_BLOCK_ROBUSTNESS_MATRIX": "fig:ml_robustness_matrix",
    "FIGURE_BLOCK_PROBABILITY_MARGIN": "fig:ml_probability_margin_distribution",
    "FIGURE_BLOCK_BOOTSTRAP_INTERVALS": "fig:ml_bootstrap_intervals",
    "FIGURE_BLOCK_PAIRED_CORRECTNESS": "fig:ml_paired_correctness",
    "FIGURE_BLOCK_SELECTIVE_ACCURACY": "fig:ml_selective_accuracy",
    "FIGURE_BLOCK_PROBABILITY_QUALITY": "fig:ml_probability_quality",
    "FIGURE_BLOCK_TRAINING_DYNAMICS": "fig:ml_training_dynamics",
    "FIGURE_BLOCK_CANDIDATE_RANK_STABILITY": "fig:ml_candidate_rank_stability",
    "FIGURE_BLOCK_CANDIDATE_LIFECYCLE": "fig:autoresearch_candidate_lifecycle",
    "FIGURE_BLOCK_DATASET_CLASS_BALANCE": "fig:mnist_class_balance",
    "FIGURE_BLOCK_DATASET_CONTACT_SHEET": "fig:mnist_subset_contact_sheet",
    "FIGURE_BLOCK_CLOSURE_FLOW": "fig:autoresearch_closure_flow",
    "FIGURE_BLOCK_SECURITY_CONTROL_MATRIX": "fig:autoresearch_security_control_matrix",
    "FIGURE_BLOCK_INTEGRITY_CHAIN": "fig:autoresearch_integrity_chain",
}

_FIGURE_REF_LABELS = {
    "FIGURE_REF_STAGE_MATRIX": "fig:autoresearch_stage_matrix",
    "FIGURE_REF_CANDIDATE_SCORES": "fig:ml_candidate_scores",
    "FIGURE_REF_CONFUSION_MATRIX": "fig:ml_confusion_matrix",
    "FIGURE_REF_PER_CLASS_ACCURACY": "fig:ml_per_class_accuracy",
    "FIGURE_REF_LEARNING_CURVES": "fig:ml_learning_curves",
    "FIGURE_REF_COMPLEXITY_ACCURACY": "fig:ml_complexity_accuracy",
    "FIGURE_REF_ERROR_EXAMPLES": "fig:mnist_error_examples",
    "FIGURE_REF_CALIBRATION_RELIABILITY": "fig:ml_calibration_reliability",
    "FIGURE_REF_CLASSIFICATION_METRICS": "fig:ml_classification_metrics_heatmap",
    "FIGURE_REF_CONFUSION_PAIRS": "fig:ml_confusion_pairs",
    "FIGURE_REF_GENERALIZATION_GAP": "fig:ml_generalization_gap",
    "FIGURE_REF_ROBUSTNESS_MATRIX": "fig:ml_robustness_matrix",
    "FIGURE_REF_PROBABILITY_MARGIN": "fig:ml_probability_margin_distribution",
    "FIGURE_REF_BOOTSTRAP_INTERVALS": "fig:ml_bootstrap_intervals",
    "FIGURE_REF_PAIRED_CORRECTNESS": "fig:ml_paired_correctness",
    "FIGURE_REF_SELECTIVE_ACCURACY": "fig:ml_selective_accuracy",
    "FIGURE_REF_PROBABILITY_QUALITY": "fig:ml_probability_quality",
    "FIGURE_REF_TRAINING_DYNAMICS": "fig:ml_training_dynamics",
    "FIGURE_REF_CANDIDATE_RANK_STABILITY": "fig:ml_candidate_rank_stability",
    "FIGURE_REF_CANDIDATE_LIFECYCLE": "fig:autoresearch_candidate_lifecycle",
    "FIGURE_REF_DATASET_CLASS_BALANCE": "fig:mnist_class_balance",
    "FIGURE_REF_DATASET_CONTACT_SHEET": "fig:mnist_subset_contact_sheet",
    "FIGURE_REF_CLOSURE_FLOW": "fig:autoresearch_closure_flow",
    "FIGURE_REF_SECURITY_CONTROL_MATRIX": "fig:autoresearch_security_control_matrix",
    "FIGURE_REF_INTEGRITY_CHAIN": "fig:autoresearch_integrity_chain",
}


def save_figure_blocks(variables: dict[str, str], path: Path) -> Path:
    """Write generated figure blocks as a small JSON sidecar."""
    payload = {key: variables[key] for key in sorted(FIGURE_BLOCK_KEYS) if key in variables}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def figure_block(project_root: Path, registry: dict[str, Any], label: str) -> str:
    record = mapping(registry.get(label))
    filename = string_value(record.get("filename", ""))
    caption = string_value(record.get("caption", ""))
    width = string_value(record.get("width", "0.8\\textwidth"))
    if not filename or not caption:
        raise ValueError(f"figure registry record is incomplete for {label}")
    figure_path = project_root / "output" / "figures" / filename
    if not figure_path.exists():
        raise ValueError(f"registered figure is missing for {label}: {figure_path}")
    return f'![{caption}](../figures/{filename}){{#{label} width="{width}"}}'


def put_figure_blocks(
    project_root: Path,
    variables: dict[str, str],
    provenance: dict[str, dict[str, str]],
    registry: dict[str, Any],
) -> None:
    for token, label in _FIGURE_BLOCK_LABELS.items():
        block = figure_block(project_root, registry, label)
        variables[token] = block
        provenance[token] = {"source": "output/figures/figure_registry.json", "pointer": f"/{label}"}
    for token, label in _FIGURE_REF_LABELS.items():
        variables[token] = f"@{label}"
        provenance[token] = {"source": "output/figures/figure_registry.json", "pointer": f"/{label}/label"}
