"""Tests for the deterministic MNIST neural-network task."""

from __future__ import annotations

import hashlib
import json
import gzip
import struct
from pathlib import Path

import numpy as np
import pytest
from infrastructure.autoresearch import BudgetPolicy

from src import mnist_fixture
from src.diagnostics import (
    bootstrap_intervals,
    calibration_report,
    candidate_accuracy_intervals,
    class_balance_report,
    classification_diagnostics,
    paired_comparison_report,
    probability_diagnostics,
    prediction_records,
    robustness_report,
    statistical_summary,
    training_diagnostics,
)
from src.ml_task import (
    CandidateResult,
    accepted_error_examples,
    flatten_images,
    load_mnist_arrays,
    load_mnist_task_config,
    run_bounded_ml_task,
    select_accepted_candidate,
    tiny_patch_attention_features,
)


def test_load_mnist_arrays_reads_balanced_local_subset(project_root: Path) -> None:
    config = load_mnist_task_config(project_root)
    x_train, y_train, x_test, y_test = load_mnist_arrays(project_root, config)

    assert x_train.shape == (2000, 28, 28)
    assert x_test.shape == (500, 28, 28)
    assert y_train.shape == (2000,)
    assert y_test.shape == (500,)
    assert set(y_train.tolist()) == set(range(10))
    assert set(y_test.tolist()) == set(range(10))
    assert {int(label): int((y_train == label).sum()) for label in range(10)} == dict.fromkeys(range(10), 200)
    assert {int(label): int((y_test == label).sum()) for label in range(10)} == dict.fromkeys(range(10), 50)
    assert float(x_train.min()) >= 0.0
    assert float(x_train.max()) <= 1.0


def test_mnist_fixture_provenance_matches_local_archive(project_root: Path) -> None:
    fixture_path = project_root / "data" / "mnist_small.npz"
    provenance_path = project_root / "data" / "mnist_small_provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))

    assert provenance["fixture_id"] == "mnist_small"
    assert provenance["train_per_class"] == 200
    assert provenance["test_per_class"] == 50
    assert provenance["npz_sha256"] == hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    assert provenance["x_train_shape"] == [2000, 28, 28]
    assert provenance["x_test_shape"] == [500, 28, 28]


def test_mnist_fixture_helpers_are_offline_and_deterministic(tmp_path: Path) -> None:
    labels = np.repeat(np.arange(10), 5)
    first = mnist_fixture._stratified_indices(labels, per_class=2, seed=7)
    second = mnist_fixture._stratified_indices(labels, per_class=2, seed=7)

    assert np.array_equal(first, second)
    assert {int(label): int((labels[first] == label).sum()) for label in range(10)} == dict.fromkeys(range(10), 2)
    assert {record["filename"] for record in mnist_fixture.SOURCE_FILES.values()} == {
        "train-images-idx3-ubyte.gz",
        "train-labels-idx1-ubyte.gz",
        "t10k-images-idx3-ubyte.gz",
        "t10k-labels-idx1-ubyte.gz",
    }

    invalid_labels = tmp_path / "invalid-labels.gz"
    with gzip.open(invalid_labels, "wb") as handle:
        handle.write(struct.pack(">II", 9999, 0))
    with pytest.raises(ValueError, match="unsupported MNIST label file"):
        mnist_fixture._read_idx_labels(invalid_labels)

    valid_images = tmp_path / "valid-images.gz"
    with gzip.open(valid_images, "wb") as handle:
        handle.write(struct.pack(">IIII", 2051, 2, 28, 28))
        handle.write((bytes(range(256)) * 7)[: 2 * 28 * 28])
    images = mnist_fixture._read_idx_images(valid_images)
    assert images.shape == (2, 28, 28)
    assert images.dtype == np.uint8

    invalid_images = tmp_path / "invalid-images.gz"
    with gzip.open(invalid_images, "wb") as handle:
        handle.write(struct.pack(">IIII", 9999, 1, 28, 28))
    with pytest.raises(ValueError, match="unsupported MNIST image file"):
        mnist_fixture._read_idx_images(invalid_images)

    valid_labels = tmp_path / "valid-labels.gz"
    with gzip.open(valid_labels, "wb") as handle:
        handle.write(struct.pack(">II", 2049, 3))
        handle.write(bytes([1, 2, 3]))
    parsed_labels = mnist_fixture._read_idx_labels(valid_labels)
    assert parsed_labels.dtype == np.int64
    assert parsed_labels.tolist() == [1, 2, 3]

    mismatched_labels = tmp_path / "mismatched-labels.gz"
    with gzip.open(mismatched_labels, "wb") as handle:
        handle.write(struct.pack(">II", 2049, 2))
        handle.write(bytes([1]))
    with pytest.raises(ValueError, match="label count mismatch"):
        mnist_fixture._read_idx_labels(mismatched_labels)

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    bad_source = cache_dir / mnist_fixture.SOURCE_FILES["train_labels"]["filename"]
    bad_source.write_bytes(b"too small")
    with pytest.raises(ValueError, match="unexpected MNIST source size"):
        mnist_fixture._verified_source(cache_dir, "train_labels")


def test_load_mnist_task_config_reads_candidate_search(project_root: Path) -> None:
    config = load_mnist_task_config(project_root)

    assert config.identifier == "mnist_small_neural_search"
    assert config.name == "small MNIST neural-network classification"
    assert config.dataset_path == "data/mnist_small.npz"
    assert config.max_candidates == 4
    assert config.diagnostics.bootstrap_resamples == 1000
    assert config.diagnostics.calibration_bins == 10
    assert config.diagnostics.low_margin_threshold == pytest.approx(0.15)
    assert config.diagnostics.coverage_thresholds == (0.5, 0.6, 0.7, 0.8, 0.9)
    assert config.training_defaults.learning_rate_decay == pytest.approx(0.995)
    assert config.training_defaults.gradient_clip_norm == pytest.approx(5.0)
    assert [transform.identifier for transform in config.robustness_transforms] == [
        "identity",
        "shift_right_1",
        "shift_down_1",
        "low_contrast_0_85",
    ]
    assert len(config.candidates) == 5
    assert config.candidates[0].identifier == "exp-softmax-linear"
    assert config.candidates[2].model_type == "tiny_patch_transformer"
    assert config.candidates[-1].identifier == "exp-mlp-relu-64-deferred"


def test_tiny_patch_attention_features_are_deterministic(project_root: Path) -> None:
    config = load_mnist_task_config(project_root)
    x_train, _, _, _ = load_mnist_arrays(project_root, config)
    spec = config.candidates[2]

    first = tiny_patch_attention_features(x_train[:5], spec)
    second = tiny_patch_attention_features(x_train[:5], spec)

    assert np.array_equal(first, second)
    assert first.shape == (5, spec.d_model)


def test_run_bounded_ml_task_selects_best_candidate_under_budget(project_root: Path) -> None:
    result = run_bounded_ml_task(project_root, BudgetPolicy(max_iterations=4))

    assert result.dataset.dataset_name == "MNIST handwritten digit database"
    assert result.candidate_count == 5
    assert result.evaluated_candidate_count == 4
    assert result.budget_exhausted is True
    assert result.llm_calls_used == 0
    assert result.cost_usd_used == 0.0
    assert result.accepted_candidate_id == "exp-mlp-tanh-64"
    assert result.best_accuracy > result.baseline.test_accuracy
    assert result.benchmark_score == 1.0
    assert result.transformer_evaluated is True
    assert result.model_families == (
        "mlp",
        "nearest_centroid",
        "softmax_regression",
        "tiny_patch_transformer",
    )
    payload = result.to_dict()
    assert payload["configuration_source"] == "mnist_task.yaml"
    assert payload["model_families"] == list(result.model_families)
    assert payload["transformer_evaluated"] is True
    assert result.accepted_candidate.training_history
    assert len(result.accepted_candidate.training_history) == result.accepted_candidate.epochs
    first_rate = result.accepted_candidate.training_history[0]["learning_rate"]
    final_rate = result.accepted_candidate.training_history[-1]["learning_rate"]
    assert first_rate > final_rate
    assert len(result.accepted_candidate.test_predictions) == result.dataset.test_size
    assert len(result.accepted_candidate.test_probabilities) == result.dataset.test_size
    assert {row["transform"] for row in result.accepted_candidate.robustness_metrics} == {
        "identity",
        "shift_right_1",
        "shift_down_1",
        "low_contrast_0_85",
    }
    assert any(candidate.model_type == "tiny_patch_transformer" for candidate in result.candidates)
    assert {candidate.status for candidate in result.candidates} == {"accepted", "rejected", "deferred"}


def test_accepted_error_examples_are_deterministic(project_root: Path) -> None:
    result = run_bounded_ml_task(project_root, BudgetPolicy(max_iterations=4))
    first = accepted_error_examples(project_root, result, limit=5)
    second = accepted_error_examples(project_root, result, limit=5)

    assert first == second
    assert 0 < len(first) <= 5
    assert all(row["true_label"] != row["predicted_label"] for row in first)


def test_prediction_records_store_probabilities_and_predictions(project_root: Path) -> None:
    result = run_bounded_ml_task(project_root, BudgetPolicy(max_iterations=4))
    payload = prediction_records(project_root, result)
    records = payload["records"]
    assert isinstance(records, list)
    rows = [row for row in records if isinstance(row, dict) and row["candidate_id"] == result.accepted_candidate_id]

    assert len(rows) == result.dataset.test_size
    for row in rows:
        probabilities = np.asarray(row["probabilities"], dtype=float)
        assert probabilities.shape == (10,)
        assert probabilities.sum() == pytest.approx(1.0, abs=1e-6)
        assert int(np.argmax(probabilities)) == row["predicted_label"]
        assert 0.0 <= row["confidence"] <= 1.0
        assert 0.0 <= row["margin"] <= 1.0


def test_classification_calibration_and_robustness_diagnostics_are_bounded(project_root: Path) -> None:
    result = run_bounded_ml_task(project_root, BudgetPolicy(max_iterations=4))
    classification = classification_diagnostics(result)
    candidate_intervals = candidate_accuracy_intervals(result)
    class_balance = class_balance_report(project_root, result)
    calibration = calibration_report(project_root, result)
    robustness = robustness_report(result)

    matrix = np.asarray(result.accepted_candidate.confusion_matrix)
    per_class = classification["per_class"]
    assert isinstance(per_class, list)
    assert len(per_class) == 10
    assert sum(int(row["support"]) for row in per_class if isinstance(row, dict)) == int(matrix.sum())
    assert classification["macro_f1"] == pytest.approx(
        np.mean([float(row["f1"]) for row in per_class if isinstance(row, dict)])
    )
    interval_rows = candidate_intervals["rows"]
    assert isinstance(interval_rows, list)
    assert len(interval_rows) == result.evaluated_candidate_count + 1
    assert all(
        0.0 <= float(row["ci_low"]) <= float(row["accuracy"]) <= float(row["ci_high"]) <= 1.0 for row in interval_rows
    )
    balance_rows = class_balance["rows"]
    assert isinstance(balance_rows, list)
    assert {row["count"] for row in balance_rows if row["split"] == "train"} == {200}
    assert {row["count"] for row in balance_rows if row["split"] == "test"} == {50}
    assert 0.0 <= float(classification["accuracy_ci_low"]) <= float(classification["accuracy_ci_high"]) <= 1.0
    bins = calibration["bins"]
    assert isinstance(bins, list)
    assert len(bins) == 10
    assert 0.0 <= float(calibration["expected_calibration_error"]) <= 1.0
    assert 0.0 <= float(calibration["maximum_calibration_error"]) <= 1.0
    assert int(calibration["high_confidence_error_count"]) >= 0
    expected_rows = result.evaluated_candidate_count * 4
    robustness_rows = robustness["rows"]
    transforms = robustness["transforms"]
    assert isinstance(robustness_rows, list)
    assert isinstance(transforms, list)
    assert len(robustness_rows) == expected_rows
    assert set(transforms) == {"identity", "shift_right_1", "shift_down_1", "low_contrast_0_85"}
    assert 0.0 <= float(robustness["accepted_min_accuracy"]) <= 1.0


def test_probability_bootstrap_and_paired_diagnostics_are_deterministic(project_root: Path) -> None:
    result = run_bounded_ml_task(project_root, BudgetPolicy(max_iterations=4))
    probability = probability_diagnostics(project_root, result)
    bootstrap = bootstrap_intervals(project_root, result, resamples=100)
    paired = paired_comparison_report(project_root, result)
    statistical = statistical_summary(project_root, result)

    assert probability["accepted_candidate_id"] == result.accepted_candidate_id
    assert int(probability["sample_count"]) == result.dataset.test_size
    assert 0.0 <= float(probability["mean_error_confidence"]) <= 1.0
    assert 0.0 <= float(probability["mean_correct_confidence"]) <= 1.0
    assert int(probability["low_margin_count"]) >= 0
    assert len(probability["confidence_histogram"]) == 10
    assert len(probability["margin_histogram"]) == 10
    intervals = bootstrap["intervals"]
    assert isinstance(intervals, list)
    assert {row["metric"] for row in intervals if isinstance(row, dict)} == {"accuracy", "macro_f1"}
    assert all(
        0.0 <= float(row["ci_low"]) <= float(row["ci_high"]) <= 1.0 for row in intervals if isinstance(row, dict)
    )
    assert paired["accepted_candidate_id"] == result.accepted_candidate_id
    assert (
        int(paired["both_correct"])
        + int(paired["accepted_only_correct"])
        + int(paired["baseline_only_correct"])
        + int(paired["both_wrong"])
    ) == result.dataset.test_size
    assert 0.0 <= float(paired["exact_mcnemar_p"]) <= 1.0
    assert float(paired["net_accuracy_gain"]) == pytest.approx(result.accuracy_delta)
    assert statistical["accepted_candidate_id"] == result.accepted_candidate_id
    assert 0.0 <= float(statistical["brier_score"]) <= 2.0
    assert float(statistical["negative_log_likelihood"]) >= 0.0
    assert 0.0 <= float(statistical["top2_accuracy"]) <= 1.0
    assert -1.0 <= float(statistical["cohen_kappa"]) <= 1.0
    coverage_curve = statistical["coverage_curve"]
    quality_rows = statistical["candidate_probability_quality"]
    assert isinstance(coverage_curve, list)
    assert [row["threshold"] for row in coverage_curve if isinstance(row, dict)] == [0.5, 0.6, 0.7, 0.8, 0.9]
    assert all(0.0 <= float(row["coverage"]) <= 1.0 for row in coverage_curve if isinstance(row, dict))
    assert isinstance(quality_rows, list)
    assert len(quality_rows) == result.evaluated_candidate_count


def test_training_diagnostics_match_epoch_history(project_root: Path) -> None:
    result = run_bounded_ml_task(project_root, BudgetPolicy(max_iterations=4))
    payload = training_diagnostics(result)
    rows = payload["rows"]
    policy = payload["training_policy"]
    accepted = payload["accepted"]

    assert isinstance(rows, list)
    assert isinstance(policy, dict)
    assert isinstance(accepted, dict)
    accepted_config = result.accepted_candidate.config["training"]
    assert isinstance(accepted_config, dict)
    assert policy["learning_rate_decay"] == pytest.approx(accepted_config["learning_rate_decay"])
    assert policy["gradient_clip_norm"] == pytest.approx(accepted_config["gradient_clip_norm"])
    assert len(rows) == result.evaluated_candidate_count
    for candidate in result.candidates:
        if not candidate.training_history:
            continue
        row = next(row for row in rows if isinstance(row, dict) and row["candidate_id"] == candidate.identifier)
        best_history = max(
            candidate.training_history,
            key=lambda history_row: (float(history_row["test_accuracy"]), -int(history_row["epoch"])),
        )
        final_history = candidate.training_history[-1]
        assert row["best_epoch"] == best_history["epoch"]
        assert row["best_test_accuracy"] == pytest.approx(best_history["test_accuracy"])
        assert row["final_test_accuracy"] == pytest.approx(final_history["test_accuracy"])
        assert row["final_learning_rate"] == pytest.approx(final_history["learning_rate"])
        assert float(row["test_accuracy_stability_last5"]) >= 0.0
    assert accepted["candidate_id"] == result.accepted_candidate_id


def test_select_accepted_candidate_tie_breaks_by_parameter_count() -> None:
    large_candidate = CandidateResult(
        identifier="large",
        title="Large",
        model_type="mlp",
        status="evaluated",
        lifecycle=("proposed", "evaluated"),
        test_accuracy=0.75,
        train_accuracy=0.8,
        test_loss=0.5,
        train_loss=0.4,
        parameter_count=100,
        epochs=1,
        seed=1,
        accuracy_delta_vs_baseline=0.25,
        config={},
    )
    small_candidate = CandidateResult(
        identifier="small",
        title="Small",
        model_type="softmax_regression",
        status="evaluated",
        lifecycle=("proposed", "evaluated"),
        test_accuracy=0.75,
        train_accuracy=0.8,
        test_loss=0.5,
        train_loss=0.4,
        parameter_count=10,
        epochs=1,
        seed=1,
        accuracy_delta_vs_baseline=0.25,
        config={},
    )

    assert select_accepted_candidate((large_candidate, small_candidate)).identifier == "small"


def test_run_bounded_ml_task_requires_candidate_budget(project_root: Path) -> None:
    with pytest.raises(ValueError, match="at least one candidate"):
        run_bounded_ml_task(project_root, BudgetPolicy(max_iterations=0))


def test_flatten_images_preserves_row_count(project_root: Path) -> None:
    config = load_mnist_task_config(project_root)
    x_train, _, _, _ = load_mnist_arrays(project_root, config)

    assert flatten_images(x_train[:3]).shape == (3, 784)
