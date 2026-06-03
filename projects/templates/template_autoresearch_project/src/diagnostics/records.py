"""Prediction-record builders for ML diagnostics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from src.json_coerce import mapping_list
from src.ml.task import CandidateResult, MLTaskResult, load_mnist_arrays, load_mnist_task_config


def prediction_records(project_root: Path, result: MLTaskResult) -> dict[str, object]:
    """Return probability-aware prediction records for evaluated candidates."""
    config = load_mnist_task_config(project_root, result.task_config.source_path)
    _x_train, _y_train, _x_test, y_test = load_mnist_arrays(project_root, config)
    rows: list[dict[str, object]] = []
    for candidate in _evaluated_candidates(result):
        probabilities = _candidate_probabilities(candidate, expected_rows=y_test.size)
        predictions = _candidate_predictions(candidate, expected_rows=y_test.size)
        top_two = np.sort(probabilities, axis=1)[:, -2:]
        for index, true_label in enumerate(y_test):
            predicted_label = int(np.argmax(probabilities[index]))
            stored_prediction = int(predictions[index])
            if predicted_label != stored_prediction:
                raise ValueError(f"probability argmax does not match stored prediction for {candidate.identifier}")
            confidence = float(top_two[index, 1])
            margin = float(top_two[index, 1] - top_two[index, 0])
            rows.append(
                {
                    "candidate_id": candidate.identifier,
                    "model_type": candidate.model_type,
                    "sample_index": index,
                    "true_label": int(true_label),
                    "predicted_label": predicted_label,
                    "correct": predicted_label == int(true_label),
                    "confidence": round(confidence, 6),
                    "margin": round(margin, 6),
                    "probabilities": [round(float(value), 10) for value in probabilities[index].tolist()],
                }
            )
    return {
        "schema": "template-autoresearch-prediction-records-v1",
        "task_id": result.task_config.identifier,
        "dataset_path": result.task_config.dataset_path,
        "accepted_candidate_id": result.accepted_candidate_id,
        "evaluated_candidate_count": result.evaluated_candidate_count,
        "test_size": int(y_test.size),
        "class_count": 10,
        "records": rows,
    }


def _evaluated_candidates(result: MLTaskResult) -> tuple[CandidateResult, ...]:
    return tuple(candidate for candidate in result.candidates if candidate.test_accuracy is not None)


def _candidate_probabilities(candidate: CandidateResult, *, expected_rows: int) -> np.ndarray:
    probabilities = np.asarray(candidate.test_probabilities, dtype=float)
    if probabilities.shape != (expected_rows, 10):
        raise ValueError(f"probability rows have unexpected shape for {candidate.identifier}: {probabilities.shape}")
    sums = probabilities.sum(axis=1)
    if not np.allclose(sums, 1.0, atol=1e-6):
        raise ValueError(f"probability rows do not sum to one for {candidate.identifier}")
    return probabilities


def _candidate_predictions(candidate: CandidateResult, *, expected_rows: int) -> np.ndarray:
    predictions = np.asarray(candidate.test_predictions, dtype=np.int64)
    if predictions.shape != (expected_rows,):
        raise ValueError(f"prediction rows have unexpected shape for {candidate.identifier}: {predictions.shape}")
    return predictions


def _candidate_records(records_payload: dict[str, object], candidate_id: str) -> list[dict[str, Any]]:
    return [row for row in mapping_list(records_payload.get("records")) if row.get("candidate_id") == candidate_id]


def _record_probabilities(records: list[dict[str, Any]], *, expected_rows: int) -> np.ndarray:
    probabilities = np.asarray([row.get("probabilities", []) for row in records], dtype=float)
    if probabilities.shape != (expected_rows, 10):
        raise ValueError(f"record probability rows have unexpected shape: {probabilities.shape}")
    return probabilities


def _record_predictions(records: list[dict[str, Any]], *, expected_rows: int) -> np.ndarray:
    predictions = np.asarray([int(row.get("predicted_label", -1)) for row in records], dtype=np.int64)
    if predictions.shape != (expected_rows,):
        raise ValueError(f"record prediction rows have unexpected shape: {predictions.shape}")
    return predictions


__all__ = [
    "prediction_records",
    "_evaluated_candidates",
    "_candidate_probabilities",
    "_candidate_predictions",
    "_candidate_records",
    "_record_probabilities",
    "_record_predictions",
]
