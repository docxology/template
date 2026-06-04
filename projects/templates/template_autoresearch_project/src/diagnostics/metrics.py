"""Metric, calibration, robustness, and training diagnostics."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .intervals import (
    _interval_summary,
    _wilson_interval,
    bootstrap_intervals,
    paired_comparison_report,
)
from src.json_coerce import mapping_list
from .records import (
    _candidate_predictions,
    _candidate_records,
    _evaluated_candidates,
    _record_predictions,
    _record_probabilities,
    prediction_records,
)
from src.ml.task import CandidateResult, MLTaskResult, load_mnist_arrays, load_mnist_task_config


def classification_diagnostics(result: MLTaskResult) -> dict[str, object]:
    """Return class metrics, confidence interval, confusion pairs, and train/test gaps."""
    candidate = result.accepted_candidate
    matrix = np.asarray(candidate.confusion_matrix, dtype=float)
    if matrix.shape != (10, 10):
        raise ValueError("accepted-candidate confusion matrix must be 10 by 10")
    support = matrix.sum(axis=1)
    predicted = matrix.sum(axis=0)
    true_positive = np.diag(matrix)
    precision = np.divide(true_positive, predicted, out=np.zeros_like(true_positive), where=predicted > 0)
    recall = np.divide(true_positive, support, out=np.zeros_like(true_positive), where=support > 0)
    f1 = np.divide(
        2.0 * precision * recall, precision + recall, out=np.zeros_like(precision), where=(precision + recall) > 0
    )
    successes = int(true_positive.sum())
    total = int(matrix.sum())
    ci_low, ci_high = _wilson_interval(successes, total)
    return {
        "schema": "template-autoresearch-classification-diagnostics-v1",
        "accepted_candidate_id": result.accepted_candidate_id,
        "accuracy": round(float(successes / total), 6) if total else 0.0,
        "accuracy_ci_method": "Wilson 95%",
        "accuracy_ci_low": ci_low,
        "accuracy_ci_high": ci_high,
        "macro_precision": round(float(np.mean(precision)), 6),
        "macro_recall": round(float(np.mean(recall)), 6),
        "macro_f1": round(float(np.mean(f1)), 6),
        "train_test_accuracy_gap": _rounded_gap(candidate.train_accuracy, candidate.test_accuracy),
        "train_test_loss_gap": _rounded_gap(candidate.test_loss, candidate.train_loss),
        "per_class": [
            {
                "class_label": int(label),
                "precision": round(float(precision[label]), 6),
                "recall": round(float(recall[label]), 6),
                "f1": round(float(f1[label]), 6),
                "support": int(support[label]),
            }
            for label in range(10)
        ],
        "top_confusion_pairs": _top_confusion_pairs(matrix),
        "generalization": _generalization_rows(result),
    }


def class_balance_report(project_root: Path, result: MLTaskResult) -> dict[str, object]:
    """Return class-count balance for the local train and test splits."""
    config = load_mnist_task_config(project_root, result.task_config.source_path)
    _x_train, y_train, _x_test, y_test = load_mnist_arrays(project_root, config)
    rows: list[dict[str, int | float | str]] = []
    for split, labels in (("train", y_train), ("test", y_test)):
        total = int(labels.size)
        for label in range(10):
            count = int(np.sum(labels == label))
            rows.append(
                {
                    "split": split,
                    "class_label": label,
                    "count": count,
                    "fraction": round(count / total, 6) if total else 0.0,
                }
            )
    return {
        "schema": "template-autoresearch-class-balance-v1",
        "task_id": result.task_config.identifier,
        "dataset_path": result.task_config.dataset_path,
        "provenance_path": result.task_config.provenance_path,
        "train_size": int(y_train.size),
        "test_size": int(y_test.size),
        "rows": rows,
        "claim_boundary": "Class-balance counts describe the local offline fixture used by this run.",
    }


def calibration_report(
    project_root: Path,
    result: MLTaskResult,
    *,
    bin_count: int | None = None,
    records_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return calibration bins and aggregate calibration errors for the accepted candidate."""
    config = load_mnist_task_config(project_root, result.task_config.source_path)
    resolved_bin_count = bin_count or config.diagnostics.calibration_bins
    records_payload = records_payload or prediction_records(project_root, result)
    records = [
        row
        for row in mapping_list(records_payload.get("records"))
        if row.get("candidate_id") == result.accepted_candidate_id
    ]
    if not records:
        raise ValueError("accepted-candidate prediction records are missing")
    confidences = np.asarray([float(row["confidence"]) for row in records], dtype=float)
    correct = np.asarray([bool(row["correct"]) for row in records], dtype=bool)
    bins: list[dict[str, int | float]] = []
    expected_calibration_error = 0.0
    maximum_calibration_error = 0.0
    for index in range(resolved_bin_count):
        lower = index / resolved_bin_count
        upper = (index + 1) / resolved_bin_count
        if index == resolved_bin_count - 1:
            mask = (confidences >= lower) & (confidences <= upper)
        else:
            mask = (confidences >= lower) & (confidences < upper)
        count = int(np.sum(mask))
        bin_accuracy = float(np.mean(correct[mask])) if count else 0.0
        mean_confidence = float(np.mean(confidences[mask])) if count else 0.0
        gap = abs(bin_accuracy - mean_confidence)
        expected_calibration_error += (count / len(records)) * gap
        maximum_calibration_error = max(maximum_calibration_error, gap)
        bins.append(
            {
                "bin_index": index,
                "lower": round(lower, 3),
                "upper": round(upper, 3),
                "count": count,
                "accuracy": round(bin_accuracy, 6),
                "mean_confidence": round(mean_confidence, 6),
                "absolute_gap": round(gap, 6),
            }
        )
    high_confidence_threshold = config.diagnostics.high_confidence_threshold
    high_confidence_errors = int(np.sum((confidences >= high_confidence_threshold) & ~correct))
    return {
        "schema": "template-autoresearch-calibration-report-v1",
        "accepted_candidate_id": result.accepted_candidate_id,
        "source_predictions": "output/data/ml_prediction_records.json",
        "bin_count": resolved_bin_count,
        "expected_calibration_error": round(expected_calibration_error, 6),
        "maximum_calibration_error": round(maximum_calibration_error, 6),
        "high_confidence_threshold": high_confidence_threshold,
        "high_confidence_error_count": high_confidence_errors,
        "bins": bins,
    }


def calibration_bin_intervals(
    project_root: Path,
    result: MLTaskResult,
    *,
    calibration: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return Wilson intervals for calibration-bin empirical accuracies."""
    payload = calibration or calibration_report(project_root, result)
    rows: list[dict[str, int | float]] = []
    for row in mapping_list(payload.get("bins")):
        count = int(row.get("count", 0))
        accuracy = _float_value(row.get("accuracy"))
        successes = int(round(accuracy * count)) if count else 0
        ci_low, ci_high = _wilson_interval(successes, count)
        rows.append(
            {
                "bin_index": int(row.get("bin_index", 0)),
                "lower": _float_value(row.get("lower")),
                "upper": _float_value(row.get("upper")),
                "count": count,
                "successes": successes,
                "accuracy": round(float(accuracy), 6) if count else 0.0,
                "mean_confidence": _float_value(row.get("mean_confidence")),
                "ci_low": ci_low,
                "ci_high": ci_high,
                "empty_bin": count == 0,
            }
        )
    return {
        "schema": "template-autoresearch-calibration-bin-intervals-v1",
        "accepted_candidate_id": result.accepted_candidate_id,
        "source_calibration": "output/data/ml_calibration_report.json",
        "method": "Wilson 95% binomial interval for empirical bin accuracy",
        "bins": rows,
        "claim_boundary": "Intervals describe calibration-bin uncertainty on the fixed local test split.",
    }


def robustness_report(result: MLTaskResult) -> dict[str, object]:
    """Return deterministic no-retrain perturbation metrics for evaluated candidates."""
    rows: list[dict[str, object]] = []
    for candidate in _evaluated_candidates(result):
        rows.extend(dict(row) for row in candidate.robustness_metrics)
    transforms = list(dict.fromkeys(str(row.get("transform", "")) for row in rows if row.get("transform")))
    accepted_rows = [row for row in rows if row.get("candidate_id") == result.accepted_candidate_id]
    accepted_min_accuracy = min((_float_value(row.get("accuracy")) for row in accepted_rows), default=0.0)
    return {
        "schema": "template-autoresearch-robustness-report-v1",
        "accepted_candidate_id": result.accepted_candidate_id,
        "transforms": transforms,
        "rows": rows,
        "accepted_min_accuracy": round(accepted_min_accuracy, 6),
        "claim_boundary": "Deterministic no-retrain smoke test on the fixed local subset.",
    }


def probability_diagnostics(
    project_root: Path,
    result: MLTaskResult,
    *,
    records_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return accepted-candidate confidence, margin, and entropy diagnostics."""
    config = load_mnist_task_config(project_root, result.task_config.source_path)
    records_payload = records_payload or prediction_records(project_root, result)
    records = [
        row
        for row in mapping_list(records_payload.get("records"))
        if row.get("candidate_id") == result.accepted_candidate_id
    ]
    probabilities = np.asarray([row["probabilities"] for row in records], dtype=float)
    confidence = np.asarray([float(row["confidence"]) for row in records], dtype=float)
    margin = np.asarray([float(row["margin"]) for row in records], dtype=float)
    correct = np.asarray([bool(row["correct"]) for row in records], dtype=bool)
    entropy = -np.sum(probabilities * np.log(np.clip(probabilities, 1e-12, 1.0)), axis=1)
    low_margin_threshold = config.diagnostics.low_margin_threshold
    return {
        "schema": "template-autoresearch-probability-diagnostics-v1",
        "accepted_candidate_id": result.accepted_candidate_id,
        "source_predictions": "output/data/ml_prediction_records.json",
        "sample_count": len(records),
        "low_margin_threshold": low_margin_threshold,
        "low_margin_count": int(np.sum(margin < low_margin_threshold)),
        "mean_confidence": round(float(np.mean(confidence)), 6),
        "mean_correct_confidence": _masked_mean(confidence, correct),
        "mean_error_confidence": _masked_mean(confidence, ~correct),
        "mean_margin": round(float(np.mean(margin)), 6),
        "mean_correct_margin": _masked_mean(margin, correct),
        "mean_error_margin": _masked_mean(margin, ~correct),
        "mean_entropy": round(float(np.mean(entropy)), 6),
        "confidence_histogram": _histogram_payload(confidence, correct),
        "margin_histogram": _histogram_payload(margin, correct),
    }


def statistical_summary(
    project_root: Path,
    result: MLTaskResult,
    *,
    resamples: int | None = None,
    records_payload: dict[str, object] | None = None,
    classification: dict[str, object] | None = None,
    calibration: dict[str, object] | None = None,
    bootstrap: dict[str, object] | None = None,
    paired: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return run-level probabilistic and paired statistical summary diagnostics."""
    config = load_mnist_task_config(project_root, result.task_config.source_path)
    _x_train, _y_train, _x_test, y_test = load_mnist_arrays(project_root, config)
    records_payload = records_payload or prediction_records(project_root, result)
    accepted_records = _candidate_records(records_payload, result.accepted_candidate_id)
    accepted_probabilities = _record_probabilities(accepted_records, expected_rows=y_test.size)
    accepted_predictions = _candidate_predictions(result.accepted_candidate, expected_rows=y_test.size)
    classification = classification or classification_diagnostics(result)
    calibration = calibration or calibration_report(project_root, result, records_payload=records_payload)
    bootstrap = bootstrap or bootstrap_intervals(project_root, result, resamples=resamples)
    paired = paired or paired_comparison_report(project_root, result)
    quality_rows = [
        _probability_quality_row(records_payload, candidate.identifier, y_test)
        for candidate in _evaluated_candidates(result)
    ]
    return {
        "schema": "template-autoresearch-statistical-summary-v1",
        "accepted_candidate_id": result.accepted_candidate_id,
        "source_predictions": "output/data/ml_prediction_records.json",
        "diagnostic_config": config.diagnostics.to_dict(),
        "accuracy": round(float(np.mean(accepted_predictions == y_test)), 6),
        "balanced_accuracy": classification.get("macro_recall", 0.0),
        "macro_f1": classification.get("macro_f1", 0.0),
        "cohen_kappa": _cohen_kappa(np.asarray(result.accepted_candidate.confusion_matrix, dtype=float)),
        "negative_log_likelihood": _negative_log_likelihood(accepted_probabilities, y_test),
        "brier_score": _brier_score(accepted_probabilities, y_test),
        "top2_accuracy": _top_k_accuracy(accepted_probabilities, y_test, k=2),
        "expected_calibration_error": calibration.get("expected_calibration_error", 0.0),
        "accuracy_ci_low": classification.get("accuracy_ci_low", 0.0),
        "accuracy_ci_high": classification.get("accuracy_ci_high", 0.0),
        "bootstrap_accuracy_ci": _interval_summary(bootstrap, "accuracy"),
        "bootstrap_macro_f1_ci": _interval_summary(bootstrap, "macro_f1"),
        "rank_stability_source": "output/data/ml_candidate_rank_stability.json",
        "calibration_bin_intervals_source": "output/data/ml_calibration_bin_intervals.json",
        "exact_mcnemar_p": paired.get("exact_mcnemar_p", 1.0),
        "coverage_curve": _coverage_curve(
            accepted_probabilities,
            accepted_predictions,
            y_test,
            config.diagnostics.coverage_thresholds,
        ),
        "candidate_probability_quality": quality_rows,
        "claim_boundary": "All statistical diagnostics describe the fixed local test split and configured candidates.",
    }


def training_diagnostics(result: MLTaskResult) -> dict[str, object]:
    """Return configured-training dynamics for evaluated candidates."""
    rows = [_training_row(candidate) for candidate in _evaluated_candidates(result)]
    accepted_row = next(
        (row for row in rows if row["candidate_id"] == result.accepted_candidate_id),
        {},
    )
    accepted_training = _accepted_training_config(result.accepted_candidate)
    return {
        "schema": "template-autoresearch-training-diagnostics-v1",
        "accepted_candidate_id": result.accepted_candidate_id,
        "source_history": "output/data/ml_training_history.csv",
        "training_policy": {
            "batch_size": accepted_training.get("batch_size", 0),
            "epochs": accepted_training.get("epochs", result.accepted_candidate.epochs),
            "learning_rate": accepted_training.get("learning_rate", 0.0),
            "learning_rate_decay": accepted_training.get("learning_rate_decay", 1.0),
            "gradient_clip_norm": accepted_training.get("gradient_clip_norm", 0.0),
            "l2": accepted_training.get("l2", 0.0),
        },
        "accepted": accepted_row,
        "rows": rows,
        "claim_boundary": "Training diagnostics describe the configured deterministic run, not convergence in general.",
    }


def _training_row(candidate: CandidateResult) -> dict[str, str | int | float]:
    history = list(candidate.training_history)
    if not history:
        return {
            "candidate_id": candidate.identifier,
            "model_type": candidate.model_type,
            "status": candidate.status,
            "epochs": candidate.epochs,
            "best_epoch": 0,
            "best_test_accuracy": 0.0,
            "final_test_accuracy": 0.0,
            "final_train_accuracy": 0.0,
            "final_test_loss": 0.0,
            "final_train_loss": 0.0,
            "loss_reduction": 0.0,
            "train_test_accuracy_gap": 0.0,
            "final_learning_rate": 0.0,
            "test_accuracy_stability_last5": 0.0,
        }
    best = sorted(
        history,
        key=lambda row: (-_float_value(row.get("test_accuracy")), int(row.get("epoch", 0))),
    )[0]
    final = history[-1]
    last_window = history[-min(5, len(history)) :]
    last_test = [_float_value(row.get("test_accuracy")) for row in last_window]
    return {
        "candidate_id": candidate.identifier,
        "model_type": candidate.model_type,
        "status": candidate.status,
        "epochs": candidate.epochs,
        "best_epoch": int(best.get("epoch", 0)),
        "best_test_accuracy": round(_float_value(best.get("test_accuracy")), 6),
        "final_test_accuracy": round(_float_value(final.get("test_accuracy")), 6),
        "final_train_accuracy": round(_float_value(final.get("train_accuracy")), 6),
        "final_test_loss": round(_float_value(final.get("test_loss")), 6),
        "final_train_loss": round(_float_value(final.get("train_loss")), 6),
        "loss_reduction": round(_float_value(history[0].get("train_loss")) - _float_value(final.get("train_loss")), 6),
        "train_test_accuracy_gap": round(
            _float_value(final.get("train_accuracy")) - _float_value(final.get("test_accuracy")),
            6,
        ),
        "final_learning_rate": round(_float_value(final.get("learning_rate")), 8),
        "test_accuracy_stability_last5": round(max(last_test) - min(last_test), 6) if last_test else 0.0,
    }


def _accepted_training_config(candidate: CandidateResult) -> dict[str, object]:
    raw = candidate.config.get("training") if isinstance(candidate.config, dict) else {}
    return raw if isinstance(raw, dict) else {}


def _probability_quality_row(
    records_payload: dict[str, object],
    candidate_id: str,
    y_true: np.ndarray,
) -> dict[str, str | float]:
    records = _candidate_records(records_payload, candidate_id)
    probabilities = _record_probabilities(records, expected_rows=y_true.size)
    predictions = _record_predictions(records, expected_rows=y_true.size)
    confidence = np.max(probabilities, axis=1)
    return {
        "candidate_id": candidate_id,
        "accuracy": round(float(np.mean(predictions == y_true)), 6),
        "top2_accuracy": _top_k_accuracy(probabilities, y_true, k=2),
        "negative_log_likelihood": _negative_log_likelihood(probabilities, y_true),
        "brier_score": _brier_score(probabilities, y_true),
        "mean_confidence": round(float(np.mean(confidence)), 6),
    }


def _rounded_gap(first: float | None, second: float | None) -> float:
    if first is None or second is None:
        return 0.0
    return round(float(first - second), 6)


def _top_confusion_pairs(matrix: np.ndarray, *, limit: int = 10) -> list[dict[str, int | float]]:
    rows: list[dict[str, int | float]] = []
    support = matrix.sum(axis=1)
    for true_label in range(matrix.shape[0]):
        for predicted_label in range(matrix.shape[1]):
            if true_label == predicted_label:
                continue
            count = int(matrix[true_label, predicted_label])
            if count == 0:
                continue
            rate = float(count / support[true_label]) if support[true_label] else 0.0
            rows.append(
                {
                    "true_label": true_label,
                    "predicted_label": predicted_label,
                    "count": count,
                    "true_class_error_rate": round(rate, 6),
                }
            )
    rows.sort(key=lambda row: (-int(row["count"]), int(row["true_label"]), int(row["predicted_label"])))
    return rows[:limit]


def _generalization_rows(result: MLTaskResult) -> list[dict[str, str | int | float]]:
    rows: list[dict[str, str | int | float]] = []
    for candidate in _evaluated_candidates(result):
        rows.append(
            {
                "candidate_id": candidate.identifier,
                "model_type": candidate.model_type,
                "status": candidate.status,
                "train_accuracy": float(candidate.train_accuracy or 0.0),
                "test_accuracy": float(candidate.test_accuracy or 0.0),
                "accuracy_gap": _rounded_gap(candidate.train_accuracy, candidate.test_accuracy),
                "train_loss": float(candidate.train_loss or 0.0),
                "test_loss": float(candidate.test_loss or 0.0),
                "loss_gap": _rounded_gap(candidate.test_loss, candidate.train_loss),
                "parameter_count": candidate.parameter_count,
            }
        )
    return rows


def _masked_mean(values: np.ndarray, mask: np.ndarray) -> float:
    if not np.any(mask):
        return 0.0
    return round(float(np.mean(values[mask])), 6)


def _histogram_payload(values: np.ndarray, correct: np.ndarray, *, bin_count: int = 10) -> list[dict[str, int | float]]:
    bins: list[dict[str, int | float]] = []
    edges = np.linspace(0.0, 1.0, bin_count + 1)
    for index in range(bin_count):
        lower = float(edges[index])
        upper = float(edges[index + 1])
        if index == bin_count - 1:
            mask = (values >= lower) & (values <= upper)
        else:
            mask = (values >= lower) & (values < upper)
        bins.append(
            {
                "bin_index": index,
                "lower": round(lower, 3),
                "upper": round(upper, 3),
                "correct_count": int(np.sum(mask & correct)),
                "error_count": int(np.sum(mask & ~correct)),
            }
        )
    return bins


def _negative_log_likelihood(probabilities: np.ndarray, y_true: np.ndarray) -> float:
    selected = probabilities[np.arange(y_true.size), y_true]
    return round(float(-np.mean(np.log(np.clip(selected, 1e-12, 1.0)))), 6)


def _brier_score(probabilities: np.ndarray, y_true: np.ndarray) -> float:
    one_hot = np.eye(probabilities.shape[1], dtype=float)[y_true]
    return round(float(np.mean(np.sum((probabilities - one_hot) ** 2, axis=1))), 6)


def _top_k_accuracy(probabilities: np.ndarray, y_true: np.ndarray, *, k: int) -> float:
    top_k = np.argsort(probabilities, axis=1)[:, -k:]
    return round(float(np.mean([label in row for label, row in zip(y_true, top_k, strict=True)])), 6)


def _cohen_kappa(matrix: np.ndarray) -> float:
    total = float(matrix.sum())
    if total == 0.0:
        return 0.0
    observed = float(np.trace(matrix) / total)
    expected = float(np.sum(matrix.sum(axis=0) * matrix.sum(axis=1)) / (total * total))
    if expected >= 1.0:
        return 0.0
    return round((observed - expected) / (1.0 - expected), 6)


def _coverage_curve(
    probabilities: np.ndarray,
    predictions: np.ndarray,
    y_true: np.ndarray,
    thresholds: tuple[float, ...],
) -> list[dict[str, int | float]]:
    confidence = np.max(probabilities, axis=1)
    correct = predictions == y_true
    rows: list[dict[str, int | float]] = []
    for threshold in thresholds:
        mask = confidence >= threshold
        retained = int(np.sum(mask))
        coverage = retained / y_true.size if y_true.size else 0.0
        selective_accuracy = float(np.mean(correct[mask])) if retained else 0.0
        rows.append(
            {
                "threshold": round(float(threshold), 3),
                "retained_count": retained,
                "coverage": round(float(coverage), 6),
                "selective_accuracy": round(selective_accuracy, 6),
                "error_count": int(np.sum(mask & ~correct)),
            }
        )
    return rows


def _float_value(value: object) -> float:
    return float(value) if isinstance(value, int | float | str) else 0.0


__all__ = [
    "classification_diagnostics",
    "class_balance_report",
    "calibration_report",
    "calibration_bin_intervals",
    "robustness_report",
    "probability_diagnostics",
    "statistical_summary",
    "training_diagnostics",
    "_training_row",
    "_accepted_training_config",
    "_probability_quality_row",
    "_rounded_gap",
    "_top_confusion_pairs",
    "_generalization_rows",
    "_masked_mean",
    "_histogram_payload",
    "_negative_log_likelihood",
    "_brier_score",
    "_top_k_accuracy",
    "_cohen_kappa",
    "_coverage_curve",
    "_float_value",
]
