"""Tests for infrastructure.core.eta module.

Tests ETA calculation functions using real numerical examples (No Mocks Policy).
"""

from __future__ import annotations

import pytest

from infrastructure.core.eta import (
    ETAEstimate,
    calculate_eta,
    calculate_eta_ema,
    calculate_eta_with_confidence,
)


class TestCalculateEta:
    """Tests for calculate_eta linear extrapolation."""

    def test_basic_linear_eta(self):
        """10 items at 1s each, 5 done → 5s remaining."""
        result = calculate_eta(elapsed_time=5.0, completed_items=5, total_items=10)
        assert result == pytest.approx(5.0)

    def test_halfway_point(self):
        """Half done in 30s → 30s remaining."""
        result = calculate_eta(elapsed_time=30.0, completed_items=50, total_items=100)
        assert result == pytest.approx(30.0)

    def test_nearly_complete(self):
        """99 of 100 done in 99s → 1s remaining."""
        result = calculate_eta(elapsed_time=99.0, completed_items=99, total_items=100)
        assert result == pytest.approx(1.0)

    def test_all_items_complete(self):
        """All items complete → 0.0 remaining."""
        result = calculate_eta(elapsed_time=10.0, completed_items=10, total_items=10)
        assert result == 0.0

    def test_zero_completed_returns_none(self):
        """No items completed → indeterminate."""
        result = calculate_eta(elapsed_time=5.0, completed_items=0, total_items=10)
        assert result is None

    def test_zero_total_returns_none(self):
        """Zero total items → indeterminate."""
        result = calculate_eta(elapsed_time=5.0, completed_items=5, total_items=0)
        assert result is None

    def test_one_item_of_many(self):
        """1 of 100 done in 2s → 198s remaining."""
        result = calculate_eta(elapsed_time=2.0, completed_items=1, total_items=100)
        assert result == pytest.approx(198.0)

    def test_over_complete_returns_zero(self):
        """More completed than total → 0.0."""
        result = calculate_eta(elapsed_time=10.0, completed_items=15, total_items=10)
        assert result == 0.0


class TestCalculateEtaEma:
    """Tests for calculate_eta_ema exponential moving average."""

    def test_no_previous_eta_returns_linear(self):
        """Without prior ETA, result equals linear ETA."""
        linear = calculate_eta(elapsed_time=10.0, completed_items=5, total_items=10)
        ema = calculate_eta_ema(
            elapsed_time=10.0, completed_items=5, total_items=10, previous_eta=None
        )
        assert ema == pytest.approx(linear)

    def test_ema_blending(self):
        """EMA blends linear and previous: alpha*linear + (1-alpha)*previous."""
        linear = calculate_eta(elapsed_time=10.0, completed_items=5, total_items=10)  # 10.0
        previous = 20.0
        alpha = 0.3
        expected = alpha * linear + (1 - alpha) * previous  # 0.3*10 + 0.7*20 = 17.0
        result = calculate_eta_ema(
            elapsed_time=10.0, completed_items=5, total_items=10,
            previous_eta=previous, alpha=alpha,
        )
        assert result == pytest.approx(expected)

    def test_non_negative_result(self):
        """Result must be non-negative even with aggressive previous ETA."""
        result = calculate_eta_ema(
            elapsed_time=0.001, completed_items=99, total_items=100,
            previous_eta=-100.0, alpha=1.0,
        )
        assert result >= 0.0

    def test_all_complete_returns_zero(self):
        """All complete → 0.0."""
        result = calculate_eta_ema(
            elapsed_time=10.0, completed_items=10, total_items=10, previous_eta=5.0
        )
        assert result == 0.0

    def test_zero_completed_returns_none(self):
        """No items done → indeterminate."""
        result = calculate_eta_ema(
            elapsed_time=10.0, completed_items=0, total_items=10, previous_eta=5.0
        )
        assert result is None


class TestCalculateEtaWithConfidence:
    """Tests for calculate_eta_with_confidence three-point estimation."""

    def test_returns_named_tuple(self):
        """Result is ETAEstimate namedtuple."""
        result = calculate_eta_with_confidence(10.0, 5, 10)
        assert isinstance(result, ETAEstimate)

    def test_all_complete_returns_zeros(self):
        """All items complete → (0.0, 0.0, 0.0)."""
        result = calculate_eta_with_confidence(10.0, 10, 10)
        assert result == ETAEstimate(0.0, 0.0, 0.0)

    def test_zero_completed_returns_none_triple(self):
        """No items done → (None, None, None)."""
        result = calculate_eta_with_confidence(10.0, 0, 10)
        assert result == ETAEstimate(None, None, None)

    def test_with_item_durations(self):
        """With durations, uses min/avg/max for optimistic/realistic/pessimistic."""
        durations = [1.0, 2.0, 3.0]  # min=1, avg=2, max=3
        result = calculate_eta_with_confidence(
            elapsed_time=6.0, completed_items=3, total_items=8,
            item_durations=durations,
        )
        remaining = 5
        assert result.optimistic == pytest.approx(1.0 * remaining)
        assert result.realistic == pytest.approx(2.0 * remaining)
        assert result.pessimistic == pytest.approx(3.0 * remaining)

    def test_without_durations_uses_linear_fallback(self):
        """Without durations, fallback uses avg_per_item with ±20% spread."""
        result = calculate_eta_with_confidence(
            elapsed_time=10.0, completed_items=5, total_items=10,
        )
        avg_per_item = 2.0  # 10s / 5 items
        remaining = 5
        assert result.optimistic == pytest.approx(avg_per_item * 0.8 * remaining)
        assert result.realistic == pytest.approx(avg_per_item * remaining)
        assert result.pessimistic == pytest.approx(avg_per_item * 1.2 * remaining)

    def test_ordering_optimistic_le_realistic_le_pessimistic(self):
        """Optimistic ≤ realistic ≤ pessimistic."""
        result = calculate_eta_with_confidence(20.0, 4, 10)
        assert result.optimistic <= result.realistic <= result.pessimistic

    def test_single_duration(self):
        """Single item duration → all three estimates equal."""
        result = calculate_eta_with_confidence(
            elapsed_time=5.0, completed_items=1, total_items=6,
            item_durations=[5.0],
        )
        assert result.optimistic == result.realistic == result.pessimistic
