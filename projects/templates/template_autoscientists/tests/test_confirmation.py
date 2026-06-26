"""Tests for noise-band confirmation."""

from __future__ import annotations

import pytest

from src.confirmation import confirm_improvement


def test_confirms_when_gain_exceeds_band() -> None:
    # Noiseless evaluator: any positive gain clears a zero-width band.
    result = confirm_improvement(
        evaluate=lambda params, seed: 1.0,
        candidate=(0.0,),
        baseline_metric=0.5,
        seeds=(1, 2, 3),
        noise_scale=0.0,
    )
    assert result.candidate_mean == 1.0
    assert result.delta == 0.5
    assert result.noise_band == 0.0
    assert result.confirmed is True


def test_rejects_gain_within_noise_band() -> None:
    # Mean gain of 0.1 against a band of 2 * 0.3 / sqrt(4) = 0.3.
    result = confirm_improvement(
        evaluate=lambda params, seed: 1.1,
        candidate=(0.0,),
        baseline_metric=1.0,
        seeds=(1, 2, 3, 4),
        noise_scale=0.3,
        sigma=2.0,
    )
    assert result.delta == pytest.approx(0.1)
    assert result.noise_band == pytest.approx(0.3)
    assert result.confirmed is False


def test_band_shrinks_with_more_seeds() -> None:
    band_few = confirm_improvement(lambda p, s: 1.0, (0.0,), 0.0, seeds=(1,), noise_scale=0.4).noise_band
    band_many = confirm_improvement(lambda p, s: 1.0, (0.0,), 0.0, seeds=(1, 2, 3, 4), noise_scale=0.4).noise_band
    assert band_many < band_few


def test_averages_over_seeds() -> None:
    result = confirm_improvement(
        evaluate=lambda params, seed: float(seed),
        candidate=(0.0,),
        baseline_metric=0.0,
        seeds=(2, 4),
        noise_scale=0.0,
    )
    assert result.candidate_mean == 3.0


def test_empty_seeds_rejected() -> None:
    with pytest.raises(ValueError, match="seeds must be non-empty"):
        confirm_improvement(lambda p, s: 1.0, (0.0,), 0.0, seeds=(), noise_scale=0.1)


def test_rejects_gain_exactly_at_band_boundary() -> None:
    """Negative control: delta <= noise_band is NOT sufficient to confirm.

    The accept condition is strictly *greater than* the band.  A delta that
    lands exactly on the boundary should be rejected, not promoted.  We construct
    the case precisely: evaluate always returns a known value, so delta is exact.
    """
    # Use noise_scale=0 so the band is 0.0.  Then delta must be > 0 to confirm.
    # A delta of exactly 0.0 (candidate equals baseline) must be rejected.
    result = confirm_improvement(
        evaluate=lambda params, seed: 1.0,  # mean == baseline, delta == 0
        candidate=(0.0,),
        baseline_metric=1.0,
        seeds=(1, 2, 3),
        noise_scale=0.0,
    )
    assert result.delta == pytest.approx(0.0)
    assert result.noise_band == pytest.approx(0.0)
    assert result.confirmed is False  # delta == band (0 == 0) is not strictly greater


def test_single_seed_band_formula() -> None:
    """Band with one seed equals sigma * noise_scale (standard error = noise_scale / sqrt(1))."""
    result = confirm_improvement(
        evaluate=lambda params, seed: 1.0,
        candidate=(0.0,),
        baseline_metric=0.0,
        seeds=(42,),
        noise_scale=0.5,
        sigma=3.0,
    )
    assert result.noise_band == pytest.approx(1.5)  # 3.0 * 0.5
