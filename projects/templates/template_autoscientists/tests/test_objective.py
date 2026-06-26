"""Tests for the deterministic synthetic objective."""

from __future__ import annotations

import math

import pytest

from src.objective import SyntheticObjective, _seed_noise


def test_clean_peaks_at_optimum() -> None:
    obj = SyntheticObjective(dimensions=3)
    assert obj.clean(obj.optimum) == 0.0
    worse = obj.clean((1.0, 0.0, 0.0))
    assert worse < 0.0


def test_clean_is_symmetric_about_optimum() -> None:
    obj = SyntheticObjective(dimensions=2, ripple=0.0)
    left = obj.clean((-0.7, 0.3))
    right = obj.clean((0.7, -0.3))
    assert left == pytest.approx(right)


def test_ripple_creates_deceptive_structure() -> None:
    rippled = SyntheticObjective(dimensions=1, ripple=0.15)
    smooth = SyntheticObjective(dimensions=1, ripple=0.0)
    # At a half-period the cosine term is -1, so the ripple subtracts its
    # maximum penalty: the rippled landscape dips below the smooth quadratic,
    # which is what creates the deceptive local structure.
    assert rippled.clean((0.5,)) < smooth.clean((0.5,))
    # At a full period the cosine returns to 1 and the two landscapes agree.
    assert rippled.clean((1.0,)) == pytest.approx(smooth.clean((1.0,)))


def test_evaluate_is_deterministic_per_seed() -> None:
    obj = SyntheticObjective()
    params = (0.5, -0.3, 0.1, 0.0)
    assert obj.evaluate(params, 7) == obj.evaluate(params, 7)


def test_evaluate_varies_across_seeds() -> None:
    obj = SyntheticObjective()
    params = (0.5, -0.3, 0.1, 0.0)
    assert obj.evaluate(params, 1) != obj.evaluate(params, 2)


def test_evaluate_noise_is_bounded_by_scale() -> None:
    obj = SyntheticObjective(noise_scale=0.05)
    params = (0.2, 0.2, 0.2, 0.2)
    clean = obj.clean(params)
    for seed in range(50):
        assert abs(obj.evaluate(params, seed) - clean) <= 0.05 + 1e-9


def test_seed_noise_is_zero_centred_label() -> None:
    # The helper maps to [-scale, scale).
    values = [_seed_noise((0.0,), seed, 1.0) for seed in range(200)]
    assert min(values) >= -1.0
    assert max(values) < 1.0
    assert math.isclose(sum(values) / len(values), 0.0, abs_tol=0.15)


def test_start_params_offset_from_optimum() -> None:
    obj = SyntheticObjective(dimensions=4)
    start = obj.start_params()
    assert start == (1.5, 1.5, 1.5, 1.5)
    assert obj.clean(start) < obj.clean(obj.optimum)


def test_invalid_dimensions_rejected() -> None:
    with pytest.raises(ValueError, match="dimensions must be >= 1"):
        SyntheticObjective(dimensions=0)


def test_optimum_length_must_match_dimensions() -> None:
    with pytest.raises(ValueError, match="optimum length must equal dimensions"):
        SyntheticObjective(dimensions=3, optimum=(0.0, 0.0))


def test_clean_rejects_wrong_length_params() -> None:
    obj = SyntheticObjective(dimensions=2)
    with pytest.raises(ValueError, match="params length must equal dimensions"):
        obj.clean((0.0, 0.0, 0.0))


def test_objective_1d_minimal_case() -> None:
    """1-D minimal case: start=1.5, optimum=0, descent should improve."""
    obj = SyntheticObjective(dimensions=1, noise_scale=0.0, ripple=0.0)
    start = obj.start_params()
    assert start == (1.5,)
    # Clean value at optimum is 0.0; at start it is worse.
    assert obj.clean(start) < obj.clean(obj.optimum)
    assert obj.clean(obj.optimum) == 0.0


def test_custom_optimum_is_peak() -> None:
    """Objective with a non-origin optimum peaks there, not at origin."""
    obj = SyntheticObjective(dimensions=2, optimum=(3.0, -2.0), ripple=0.0, noise_scale=0.0)
    assert obj.clean((3.0, -2.0)) == pytest.approx(0.0)
    assert obj.clean((0.0, 0.0)) < 0.0


def test_evaluate_close_to_clean_over_many_seeds() -> None:
    """Over a wide sample of seeds the noisy evaluations stay near the clean value."""
    obj = SyntheticObjective(noise_scale=0.02, ripple=0.0)
    params = (0.5, 0.5, 0.5, 0.5)
    clean = obj.clean(params)
    samples = [obj.evaluate(params, s) for s in range(100)]
    assert all(abs(v - clean) <= 0.02 + 1e-9 for v in samples)
