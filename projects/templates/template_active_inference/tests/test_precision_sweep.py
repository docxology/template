"""Tests for the closed-form precision (gamma) sweep over the policy posterior.

Deterministic, no-mocks numerical checks on the canonical finite T-maze model:
posterior normalization, monotone sharpening (entropy down, optimal-set mass up),
the degenerate optimal tie, the entropy floor ln(|optimal set|), byte-determinism,
and the helper edge behaviour.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from simulation.precision_sweep import (
    DEFAULT_GAMMA_GRID_POINTS,
    PrecisionPoint,
    _entropy,
    _softmax,
    gamma_grid,
    posterior_at_gamma,
    sweep_precision,
)
from simulation.tmaze_model import TMazeSpec, build_tmaze_generative_model


def test_softmax_normalizes_and_orders() -> None:
    p = _softmax(np.array([0.0, 2.0]))
    assert abs(float(p.sum()) - 1.0) < 1e-12
    assert p[1] > p[0]


def test_entropy_uniform_and_one_hot() -> None:
    assert abs(_entropy(np.full(4, 0.25)) - math.log(4.0)) < 1e-12
    assert _entropy(np.array([1.0, 0.0, 0.0])) == 0.0


def test_gamma_grid_endpoints_and_count() -> None:
    grid = gamma_grid(16.0, DEFAULT_GAMMA_GRID_POINTS)
    assert len(grid) == DEFAULT_GAMMA_GRID_POINTS
    assert grid[0] == 0.0
    assert abs(grid[-1] - 16.0) < 1e-12
    # Step 0.5 puts gamma == 1.0 and gamma == 3.0 exactly on grid points.
    assert any(abs(g - 1.0) <= 1e-12 for g in grid)
    assert any(abs(g - 3.0) <= 1e-12 for g in grid)


def test_posterior_at_zero_precision_is_uniform() -> None:
    totals = np.array([1.0, 1.0, 3.0, 3.0])
    q = posterior_at_gamma(totals, 0.0)
    assert np.allclose(q, np.full(4, 0.25), atol=1e-12)


def test_posterior_normalized_at_every_gamma() -> None:
    model = build_tmaze_generative_model()
    result = sweep_precision(model)
    # Reconstruct each posterior from the reported entropy is not possible, so
    # recompute from the model and check normalization directly.
    from simulation.efe_decomposition import decompose_all_policies

    totals = np.array([row["total"] for row in decompose_all_policies(model)["rows"]])
    for row in result["rows"]:
        q = posterior_at_gamma(totals, row["gamma"])
        assert abs(float(q.sum()) - 1.0) < 1e-12


def test_precisionpoint_to_dict_roundtrip() -> None:
    pt = PrecisionPoint(gamma=1.0, entropy=0.5, selected_policy=(0, 1), selected_prob=0.4, optimal_set_mass=0.8)
    payload = pt.to_dict()
    assert payload["selected_policy"] == [0, 1]
    assert payload["gamma"] == 1.0
    assert payload["optimal_set_mass"] == 0.8


def test_sweep_structure_and_schema() -> None:
    result = sweep_precision(build_tmaze_generative_model())
    assert result["schema"] == "template_active_inference.precision_sweep.v1"
    assert result["gamma_grid_points"] == DEFAULT_GAMMA_GRID_POINTS
    assert len(result["rows"]) == DEFAULT_GAMMA_GRID_POINTS
    assert result["policy_count"] == 4
    for key in ("gamma", "entropy", "selected_policy", "selected_prob", "optimal_set_mass"):
        assert key in result["rows"][0]


def test_entropy_decreases_with_precision() -> None:
    result = sweep_precision(build_tmaze_generative_model())
    entropies = [row["entropy"] for row in result["rows"]]
    # Strictly: gamma=0 entropy is the largest (ln 4); the sequence is monotone.
    assert result["entropy_monotone_nonincreasing"] is True
    assert abs(entropies[0] - math.log(4.0)) < 1e-9
    assert entropies[-1] < entropies[0]


def test_optimal_set_mass_increases_with_precision() -> None:
    result = sweep_precision(build_tmaze_generative_model())
    masses = [row["optimal_set_mass"] for row in result["rows"]]
    assert result["optimal_mass_monotone_nondecreasing"] is True
    assert abs(masses[0] - 0.5) < 1e-9  # uniform: optimal set is 2 of 4
    assert masses[-1] > 0.999


def test_degenerate_optimal_tie_and_entropy_floor() -> None:
    # The absorbing goal makes the second action irrelevant once reached: two
    # policies tie at the EFE minimum, so the entropy floor is ln 2, not 0.
    result = sweep_precision(build_tmaze_generative_model())
    assert result["optimal_set_size"] == 2
    assert abs(result["entropy_floor"] - math.log(2.0)) < 1e-12
    # The saturating entropy approaches the floor from above.
    assert result["rows"][-1]["entropy"] >= result["entropy_floor"] - 1e-9
    assert abs(result["rows"][-1]["entropy"] - result["entropy_floor"]) < 1e-3


def test_entropy_at_gamma_one_value() -> None:
    result = sweep_precision(build_tmaze_generative_model())
    # Verified against the real model: H[q] at gamma=1 is 1.145819 nats.
    assert abs(result["entropy_at_gamma_one"] - 1.145819) < 1e-5


def test_gamma_deterministic_selection_crossing() -> None:
    result = sweep_precision(build_tmaze_generative_model())
    # Optimal-set mass first crosses 0.99 at gamma=3.0 on the default grid.
    assert result["gamma_deterministic_selection"] == 3.0


def test_gamma_deterministic_none_when_threshold_unreachable() -> None:
    # A threshold above the achievable mass (mass saturates < 1 only in the limit,
    # but is < 1 at every finite gamma) forces the None branch on a short grid.
    result = sweep_precision(
        build_tmaze_generative_model(),
        gamma_max=0.5,
        grid_points=2,
        selection_mass_threshold=0.999999,
    )
    assert result["gamma_deterministic_selection"] is None


def test_selected_policy_is_an_optimal_policy_at_high_precision() -> None:
    result = sweep_precision(build_tmaze_generative_model())
    optimal = {tuple(p) for p in result["optimal_policy_set"]}
    assert tuple(result["rows"][-1]["selected_policy"]) in optimal


def test_sweep_is_byte_deterministic() -> None:
    first = sweep_precision(build_tmaze_generative_model())
    second = sweep_precision(build_tmaze_generative_model())
    assert first == second


def test_deterministic_likelihood_still_sharpens() -> None:
    # A perfectly informative likelihood changes G but the posterior must still
    # sharpen monotonically with precision.
    model = build_tmaze_generative_model(TMazeSpec(likelihood_diag=1.0))
    result = sweep_precision(model)
    assert result["entropy_monotone_nonincreasing"] is True
    assert result["optimal_mass_monotone_nondecreasing"] is True


@pytest.mark.parametrize("diag", [0.6, 0.75, 0.9, 0.99])
def test_monotonicity_robust_across_likelihoods(diag: float) -> None:
    result = sweep_precision(build_tmaze_generative_model(TMazeSpec(likelihood_diag=diag)))
    assert result["entropy_monotone_nonincreasing"] is True
    assert result["optimal_mass_monotone_nondecreasing"] is True
