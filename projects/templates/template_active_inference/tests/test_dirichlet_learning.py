"""Tests for the deterministic Dirichlet likelihood-learning track.

No-mocks, fixed generative model. Covers monotone KL decrease toward zero,
column-normalisation of the learned likelihood, steps-to-converge semantics,
byte-determinism, and the helper/guard edge cases for full coverage.
"""

from __future__ import annotations

import numpy as np
import pytest

from simulation.dirichlet_learning import (
    CONVERGENCE_KL_ATOL,
    DEFAULT_NUM_STEPS,
    DirichletLearningResult,
    _kl_columns,
    expected_likelihood,
    learn_likelihood,
    summarize_learning,
)
from simulation.tmaze_model import TMazeSpec, build_tmaze_generative_model


def test_expected_likelihood_columns_sum_to_one() -> None:
    pa = np.array([[1.0, 4.0], [3.0, 2.0]])
    ea = expected_likelihood(pa)
    assert np.allclose(ea.sum(axis=0), np.ones(2), atol=1e-12)
    # Column 0: [1, 3] / 4 = [0.25, 0.75].
    assert abs(float(ea[0, 0]) - 0.25) < 1e-12
    assert abs(float(ea[1, 0]) - 0.75) < 1e-12


def test_kl_columns_zero_when_identical_and_positive_otherwise() -> None:
    a = np.array([[0.9, 0.1], [0.1, 0.9]])
    assert abs(_kl_columns(a, a)) < 1e-12
    learned = np.array([[0.5, 0.5], [0.5, 0.5]])
    assert _kl_columns(a, learned) > 0.0


def test_kl_columns_ignores_true_zero_entries() -> None:
    # A perfectly informative true column has a zero entry; 0 * log 0 == 0, so the
    # divergence stays finite even though learned[that entry] is small.
    true_a = np.array([[1.0, 0.0], [0.0, 1.0]])
    learned = np.array([[0.8, 0.2], [0.2, 0.8]])
    value = _kl_columns(true_a, learned)
    assert np.isfinite(value)
    assert value > 0.0


def test_learn_likelihood_kl_monotone_decreasing_to_near_zero() -> None:
    result = learn_likelihood(build_tmaze_generative_model())
    assert result.is_monotone_decreasing
    # Strictly decreasing for the first several steps (real convergence, not flat).
    assert result.kl_trajectory[0] > result.kl_trajectory[1]
    assert result.kl_trajectory[1] > result.kl_trajectory[2]
    # Final KL is small and below the prior KL by orders of magnitude.
    assert result.final_kl < CONVERGENCE_KL_ATOL
    assert result.final_kl < result.initial_kl / 100.0


def test_learn_likelihood_expected_a_columns_normalised() -> None:
    result = learn_likelihood(build_tmaze_generative_model())
    for column in result.expected_a:
        assert abs(sum(column) - 1.0) < 1e-12
    # Learned A approaches the true A (0.9 on the diagonal) but is not yet exact.
    assert result.expected_a[0][0] > 0.8
    assert result.expected_a[1][1] > 0.8


def test_steps_to_converge_matches_threshold_crossing() -> None:
    result = learn_likelihood(build_tmaze_generative_model())
    k = result.steps_to_converge
    assert 0 < k < len(result.kl_trajectory)
    assert result.kl_trajectory[k] < CONVERGENCE_KL_ATOL
    assert result.kl_trajectory[k - 1] >= CONVERGENCE_KL_ATOL


def test_steps_to_converge_reports_horizon_when_never_reached() -> None:
    # A single coarse step from the prior never crosses the threshold.
    result = learn_likelihood(build_tmaze_generative_model(), num_steps=1)
    assert result.steps_to_converge == 1  # == len(kl_trajectory): not converged


def test_higher_count_scale_converges_at_least_as_fast() -> None:
    slow = learn_likelihood(build_tmaze_generative_model(), count_scale=5.0)
    fast = learn_likelihood(build_tmaze_generative_model(), count_scale=50.0)
    assert fast.final_kl < slow.final_kl


def test_summarize_learning_schema_and_fields() -> None:
    summary = summarize_learning(build_tmaze_generative_model())
    assert summary["schema"] == "template_active_inference.dirichlet_learning.v1"
    assert summary["num_steps"] == DEFAULT_NUM_STEPS
    assert summary["num_states"] == 2
    assert summary["num_obs"] == 2
    assert summary["is_monotone_decreasing"] is True
    assert len(summary["kl_trajectory"]) == DEFAULT_NUM_STEPS
    assert summary["final_kl"] == summary["kl_trajectory"][-1]
    assert summary["initial_kl"] == summary["kl_trajectory"][0]
    assert all(abs(sum(col) - 1.0) < 1e-12 for col in summary["expected_a"])


def test_summarize_is_byte_deterministic() -> None:
    first = summarize_learning(build_tmaze_generative_model())
    second = summarize_learning(build_tmaze_generative_model())
    assert first == second


def test_sharper_likelihood_is_harder_but_still_converges() -> None:
    # A near-deterministic true A has lower-entropy columns and a larger initial
    # KL from the flat prior, so it is *harder* to learn: at the default count
    # budget its final KL sits just above the convergence threshold. It is still
    # monotonically decreasing, and a larger count budget drives it below atol --
    # convergence to the true model genuinely holds, it just takes more evidence.
    sharp = learn_likelihood(build_tmaze_generative_model(TMazeSpec(likelihood_diag=0.99)))
    default = learn_likelihood(build_tmaze_generative_model())
    assert sharp.is_monotone_decreasing
    assert sharp.initial_kl > default.initial_kl  # lower-entropy true A is farther from prior
    assert sharp.final_kl > default.final_kl  # harder to learn at the same count budget
    sharp_more = learn_likelihood(build_tmaze_generative_model(TMazeSpec(likelihood_diag=0.99)), count_scale=50.0)
    assert sharp_more.final_kl < CONVERGENCE_KL_ATOL  # more evidence -> converges


def test_to_dict_round_trips_through_dataclass() -> None:
    result = learn_likelihood(build_tmaze_generative_model())
    payload = result.to_dict()
    # Reconstruct and confirm derived properties agree.
    rebuilt = DirichletLearningResult(
        kl_trajectory=tuple(payload["kl_trajectory"]),
        expected_a=tuple(tuple(c) for c in payload["expected_a"]),
        num_states=payload["num_states"],
        num_obs=payload["num_obs"],
        count_scale=payload["count_scale"],
        prior_concentration=payload["prior_concentration"],
    )
    assert rebuilt.final_kl == result.final_kl
    assert rebuilt.steps_to_converge == result.steps_to_converge


@pytest.mark.parametrize("bad", [0, -3])
def test_invalid_num_steps_rejected(bad: int) -> None:
    with pytest.raises(ValueError, match="num_steps"):
        learn_likelihood(build_tmaze_generative_model(), num_steps=bad)


def test_invalid_scale_and_prior_rejected() -> None:
    model = build_tmaze_generative_model()
    with pytest.raises(ValueError, match="count_scale"):
        learn_likelihood(model, count_scale=0.0)
    with pytest.raises(ValueError, match="prior_concentration"):
        learn_likelihood(model, prior_concentration=-1.0)


def test_true_likelihood_accepts_bare_array() -> None:
    model = dict(build_tmaze_generative_model())
    model["A"] = np.asarray(model["A"][0])  # un-wrap the list
    result = learn_likelihood(model)
    assert result.is_monotone_decreasing
