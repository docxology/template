"""Tests for noise-band confirmation in infrastructure.scientific."""

from __future__ import annotations

import pytest

from infrastructure.scientific import Confirmation, confirm_improvement


def test_confirms_when_gain_exceeds_band() -> None:
    result = confirm_improvement(
        evaluate=lambda params, seed: 1.0,
        candidate=(0.0,),
        baseline_metric=0.5,
        seeds=(1, 2, 3),
        noise_scale=0.0,
    )
    assert isinstance(result, Confirmation)
    assert result.candidate_mean == 1.0
    assert result.delta == 0.5
    assert result.noise_band == 0.0
    assert result.confirmed is True


def test_rejects_gain_within_noise_band() -> None:
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


def test_averages_candidate_over_seeds() -> None:
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
