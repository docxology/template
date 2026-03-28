"""Tests for blake_bimetalism/src/manuscript.py."""

from __future__ import annotations

import pytest

from projects.blake_bimetalism.src.analysis import MetaStabilityMetrics
from projects.blake_bimetalism.src.manuscript import ManuscriptBuilder


def _default_metrics() -> MetaStabilityMetrics:
    return MetaStabilityMetrics(
        gold_reserves=2_000_000.0,
        silver_reserves=40_000_000.0,
        market_ratio=15.7,
        mint_ratio=15.2,
    )


def test_generate_injection_data_returns_expected_keys() -> None:
    """generate_injection_data() returns the three required keys."""
    builder = ManuscriptBuilder(_default_metrics())
    data = builder.generate_injection_data()

    assert "entropy_gap_value" in data
    assert "visionary_dampening_0_5" in data
    assert "visionary_dampening_1_0" in data


def test_generate_injection_data_entropy_gap_correct() -> None:
    """entropy_gap_value is abs(market_ratio - mint_ratio) rounded to 2dp."""
    builder = ManuscriptBuilder(_default_metrics())
    data = builder.generate_injection_data()

    # |15.7 - 15.2| = 0.5
    assert data["entropy_gap_value"] == pytest.approx(0.5, abs=1e-9)


def test_generate_injection_data_dampening_values_are_floats() -> None:
    """Dampening values are numeric (float or int)."""
    builder = ManuscriptBuilder(_default_metrics())
    data = builder.generate_injection_data()

    assert isinstance(data["visionary_dampening_0_5"], (int, float))
    assert isinstance(data["visionary_dampening_1_0"], (int, float))


def test_generate_injection_data_higher_weight_reduces_gap() -> None:
    """prophetic_weight=1.0 damps the gap more than 0.5."""
    builder = ManuscriptBuilder(_default_metrics())
    data = builder.generate_injection_data()

    # Higher prophetic weight should reduce the visionary inversion gap further
    assert data["visionary_dampening_1_0"] <= data["visionary_dampening_0_5"]


def test_generate_injection_data_rounding() -> None:
    """All returned values are rounded to at most 2 decimal places."""
    metrics = MetaStabilityMetrics(
        gold_reserves=1.0,
        silver_reserves=3.0,
        market_ratio=15.71234,
        mint_ratio=15.0,
    )
    builder = ManuscriptBuilder(metrics)
    data = builder.generate_injection_data()

    for key, val in data.items():
        # rounded to 2dp means the rounded value should match
        assert round(val, 2) == val, f"{key}={val} is not rounded to 2dp"
