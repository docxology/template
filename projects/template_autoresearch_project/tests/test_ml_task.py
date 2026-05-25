"""Tests for the deterministic ML-loop task."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from infrastructure.autoresearch import BudgetPolicy

from src.ml_task import (
    CandidateResult,
    generate_dataset,
    load_candidate_specs,
    run_bounded_ml_task,
    select_accepted_candidate,
)


def test_generate_dataset_is_deterministic() -> None:
    first = generate_dataset(seed=20260525)
    second = generate_dataset(seed=20260525)

    assert all(np.array_equal(left, right) for left, right in zip(first, second))
    x_train, y_train, x_test, y_test = first
    assert x_train.shape == (96, 2)
    assert x_test.shape == (64, 2)
    assert set(y_train) == {-1, 1}
    assert set(y_test) == {-1, 1}


def test_load_candidate_specs_reads_seed_ideas(project_root: Path) -> None:
    specs = load_candidate_specs(project_root)

    assert len(specs) == 4
    assert specs[0].identifier == "exp-linear-alpha-1"
    assert specs[2].feature_map == "quadratic"
    assert specs[2].complexity == 2


def test_run_bounded_ml_task_selects_best_candidate_under_budget(project_root: Path) -> None:
    result = run_bounded_ml_task(project_root, BudgetPolicy(max_iterations=3))

    assert result.candidate_count == 4
    assert result.evaluated_candidate_count == 3
    assert result.budget_exhausted is True
    assert result.llm_calls_used == 0
    assert result.cost_usd_used == 0.0
    assert result.accepted_candidate_id == "exp-quadratic-alpha-0p1"
    assert result.best_accuracy > result.baseline.accuracy
    assert result.benchmark_score == 1.0
    assert {candidate.status for candidate in result.candidates} == {"accepted", "rejected", "deferred"}


def test_select_accepted_candidate_tie_breaks_by_simplicity() -> None:
    complex_candidate = CandidateResult(
        identifier="complex",
        title="Complex",
        feature_map="quadratic",
        alpha=0.1,
        complexity=2,
        status="evaluated",
        lifecycle=("proposed", "evaluated"),
        accuracy=0.75,
        accuracy_delta_vs_baseline=0.25,
    )
    simple_candidate = CandidateResult(
        identifier="simple",
        title="Simple",
        feature_map="linear",
        alpha=1.0,
        complexity=1,
        status="evaluated",
        lifecycle=("proposed", "evaluated"),
        accuracy=0.75,
        accuracy_delta_vs_baseline=0.25,
    )

    assert select_accepted_candidate((complex_candidate, simple_candidate)).identifier == "simple"


def test_run_bounded_ml_task_requires_candidate_budget(project_root: Path) -> None:
    with pytest.raises(ValueError, match="at least one candidate"):
        run_bounded_ml_task(project_root, BudgetPolicy(max_iterations=0))
