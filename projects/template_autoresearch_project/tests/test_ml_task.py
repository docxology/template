"""Tests for the deterministic MNIST neural-network task."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from infrastructure.autoresearch import BudgetPolicy

from src.ml_task import (
    CandidateResult,
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

    assert x_train.shape == (300, 28, 28)
    assert x_test.shape == (100, 28, 28)
    assert y_train.shape == (300,)
    assert y_test.shape == (100,)
    assert set(y_train.tolist()) == set(range(10))
    assert set(y_test.tolist()) == set(range(10))
    assert float(x_train.min()) >= 0.0
    assert float(x_train.max()) <= 1.0


def test_load_mnist_task_config_reads_candidate_search(project_root: Path) -> None:
    config = load_mnist_task_config(project_root)

    assert config.identifier == "mnist_tiny_neural_search"
    assert config.dataset_path == "data/mnist_tiny.npz"
    assert config.max_candidates == 3
    assert len(config.candidates) == 4
    assert config.candidates[0].identifier == "exp-softmax-linear"
    assert config.candidates[2].model_type == "tiny_patch_transformer"


def test_tiny_patch_attention_features_are_deterministic(project_root: Path) -> None:
    config = load_mnist_task_config(project_root)
    x_train, _, _, _ = load_mnist_arrays(project_root, config)
    spec = config.candidates[2]

    first = tiny_patch_attention_features(x_train[:5], spec)
    second = tiny_patch_attention_features(x_train[:5], spec)

    assert np.array_equal(first, second)
    assert first.shape == (5, spec.d_model)


def test_run_bounded_ml_task_selects_best_candidate_under_budget(project_root: Path) -> None:
    result = run_bounded_ml_task(project_root, BudgetPolicy(max_iterations=3))

    assert result.dataset.dataset_name == "MNIST handwritten digit database"
    assert result.candidate_count == 4
    assert result.evaluated_candidate_count == 3
    assert result.budget_exhausted is True
    assert result.llm_calls_used == 0
    assert result.cost_usd_used == 0.0
    assert result.accepted_candidate_id == "exp-mlp-relu-32"
    assert result.best_accuracy > result.baseline.test_accuracy
    assert result.benchmark_score == 1.0
    assert any(candidate.model_type == "tiny_patch_transformer" for candidate in result.candidates)
    assert {candidate.status for candidate in result.candidates} == {"accepted", "rejected", "deferred"}


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
