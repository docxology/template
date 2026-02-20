"""Tests for src/data/data_generator.py functionality.

Covers both generate_synthetic_data and generate_time_series with all
distribution/trend types, edge cases, and reproducibility.
"""

from __future__ import annotations

import numpy as np
import pytest
from data.data_generator import generate_synthetic_data, generate_time_series


class TestGenerateSyntheticData:
    """Test generate_synthetic_data function."""

    def test_default_parameters(self) -> None:
        """Test generation with default parameters."""
        data = generate_synthetic_data()
        assert isinstance(data, np.ndarray)
        assert data.shape == (100,)

    def test_normal_distribution(self) -> None:
        """Test normal distribution generation."""
        data = generate_synthetic_data(
            n_samples=1000, distribution="normal", mean=5.0, std=2.0, seed=42
        )
        assert data.shape == (1000,)
        assert abs(data.mean() - 5.0) < 0.5
        assert abs(data.std() - 2.0) < 0.5

    def test_uniform_distribution(self) -> None:
        """Test uniform distribution generation."""
        data = generate_synthetic_data(
            n_samples=500, distribution="uniform", mean=3.0, std=1.0, seed=42
        )
        assert data.shape == (500,)
        assert data.min() >= 2.0  # mean - std
        assert data.max() <= 4.0  # mean + std

    def test_exponential_distribution(self) -> None:
        """Test exponential distribution generation."""
        data = generate_synthetic_data(
            n_samples=500, distribution="exponential", std=2.0, seed=42
        )
        assert data.shape == (500,)
        assert data.min() >= 0  # Exponential is non-negative

    def test_unknown_distribution_raises(self) -> None:
        """Test that unknown distribution raises ValueError."""
        with pytest.raises(ValueError, match="Unknown distribution"):
            generate_synthetic_data(distribution="gamma")

    def test_multi_feature(self) -> None:
        """Test multi-feature data generation."""
        data = generate_synthetic_data(n_samples=50, n_features=5, seed=42)
        assert data.shape == (50, 5)

    def test_single_feature_flattened(self) -> None:
        """Test single feature returns flattened array."""
        data = generate_synthetic_data(n_samples=50, n_features=1, seed=42)
        assert data.ndim == 1
        assert data.shape == (50,)

    def test_reproducibility(self) -> None:
        """Test that same seed produces same data."""
        data1 = generate_synthetic_data(seed=123)
        data2 = generate_synthetic_data(seed=123)
        np.testing.assert_array_equal(data1, data2)

    def test_different_seeds_differ(self) -> None:
        """Test that different seeds produce different data."""
        data1 = generate_synthetic_data(seed=1)
        data2 = generate_synthetic_data(seed=2)
        assert not np.array_equal(data1, data2)


class TestGenerateTimeSeries:
    """Test generate_time_series function."""

    def test_default_parameters(self) -> None:
        """Test generation with default parameters."""
        time, values = generate_time_series()
        assert isinstance(time, np.ndarray)
        assert isinstance(values, np.ndarray)
        assert len(time) == 100
        assert len(values) == 100

    def test_linear_trend(self) -> None:
        """Test linear trend generation."""
        time, values = generate_time_series(
            n_points=50, trend="linear", noise_level=0.0, seed=42
        )
        assert len(time) == 50
        # With no noise, values should follow linear trend exactly
        expected = time * 0.5 + 2.0
        # Allow small float tolerance
        np.testing.assert_allclose(values, expected, atol=0.01)

    def test_sinusoidal_trend(self) -> None:
        """Test sinusoidal trend generation."""
        time, values = generate_time_series(
            n_points=50, trend="sinusoidal", noise_level=0.0, seed=42
        )
        assert len(time) == 50
        expected = np.sin(time) * 2.0 + 3.0
        np.testing.assert_allclose(values, expected, atol=0.01)

    def test_exponential_trend(self) -> None:
        """Test exponential trend generation."""
        time, values = generate_time_series(
            n_points=50, trend="exponential", noise_level=0.0, seed=42
        )
        assert len(time) == 50
        expected = np.exp(time * 0.2)
        np.testing.assert_allclose(values, expected, atol=0.01)

    def test_unknown_trend_raises(self) -> None:
        """Test that unknown trend raises ValueError."""
        with pytest.raises(ValueError, match="Unknown trend"):
            generate_time_series(trend="polynomial")

    def test_noise_level(self) -> None:
        """Test that noise level affects output variability."""
        _, values_low = generate_time_series(noise_level=0.01, seed=42)
        _, values_high = generate_time_series(noise_level=1.0, seed=42)
        # High noise should produce more variance around the trend
        assert np.std(values_high) > np.std(values_low)

    def test_reproducibility(self) -> None:
        """Test that same seed produces same time series."""
        t1, v1 = generate_time_series(seed=99)
        t2, v2 = generate_time_series(seed=99)
        np.testing.assert_array_equal(t1, t2)
        np.testing.assert_array_equal(v1, v2)
