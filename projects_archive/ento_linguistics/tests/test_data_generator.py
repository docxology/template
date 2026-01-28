"""Comprehensive tests for src/data_generator.py to ensure 100% coverage."""

import numpy as np
import pytest
from data_generator import (generate_classification_dataset,
                            generate_correlated_data, generate_synthetic_data,
                            generate_time_series, inject_noise, validate_data)


class TestGenerateSyntheticData:
    """Test synthetic data generation."""

    def test_normal_distribution(self):
        """Test normal distribution generation."""
        data = generate_synthetic_data(100, distribution="normal", seed=42)
        assert data.shape == (100, 1)
        assert np.all(np.isfinite(data))

    def test_uniform_distribution(self):
        """Test uniform distribution generation."""
        data = generate_synthetic_data(
            100, distribution="uniform", low=0, high=10, seed=42
        )
        assert data.shape == (100, 1)
        assert np.all(data >= 0)
        assert np.all(data <= 10)

    def test_exponential_distribution(self):
        """Test exponential distribution generation."""
        data = generate_synthetic_data(
            100, distribution="exponential", scale=1.0, seed=42
        )
        assert data.shape == (100, 1)
        assert np.all(data >= 0)

    def test_poisson_distribution(self):
        """Test Poisson distribution generation."""
        data = generate_synthetic_data(100, distribution="poisson", lam=2.0, seed=42)
        assert data.shape == (100, 1)
        assert np.all(data >= 0)

    def test_beta_distribution(self):
        """Test beta distribution generation."""
        data = generate_synthetic_data(100, distribution="beta", a=2.0, b=2.0, seed=42)
        assert data.shape == (100, 1)
        assert np.all(data >= 0)
        assert np.all(data <= 1)

    def test_multiple_features(self):
        """Test generating data with multiple features."""
        data = generate_synthetic_data(100, n_features=3, seed=42)
        assert data.shape == (100, 3)

    def test_without_seed(self):
        """Test generating data without seed."""
        data = generate_synthetic_data(100, distribution="normal", seed=None)
        assert data.shape == (100, 1)

    def test_invalid_distribution(self):
        """Test invalid distribution raises error."""
        with pytest.raises(ValueError):
            generate_synthetic_data(100, distribution="invalid", seed=42)


class TestGenerateTimeSeries:
    """Test time series generation."""

    def test_linear_trend(self):
        """Test linear trend generation."""
        time, values = generate_time_series(100, trend="linear", seed=42)
        assert len(time) == 100
        assert len(values) == 100

    def test_quadratic_trend(self):
        """Test quadratic trend generation."""
        time, values = generate_time_series(
            100, trend="quadratic", a=0.1, b=1.0, c=0.0, seed=42
        )
        assert len(time) == 100
        assert len(values) == 100

    def test_sinusoidal_trend(self):
        """Test sinusoidal trend generation."""
        time, values = generate_time_series(100, trend="sinusoidal", seed=42)
        assert len(time) == 100
        assert len(values) == 100

    def test_exponential_trend(self):
        """Test exponential trend generation."""
        time, values = generate_time_series(100, trend="exponential", seed=42)
        assert len(time) == 100
        assert len(values) == 100

    def test_time_series_without_seed(self):
        """Test time series generation without seed."""
        time, values = generate_time_series(100, trend="linear", seed=None)
        assert len(time) == 100
        assert len(values) == 100

    def test_invalid_trend(self):
        """Test invalid trend raises error."""
        with pytest.raises(ValueError):
            generate_time_series(100, trend="invalid", seed=42)


class TestGenerateCorrelatedData:
    """Test correlated data generation."""

    def test_basic_generation(self):
        """Test basic correlated data generation."""
        data = generate_correlated_data(100, 3, seed=42)
        assert data.shape == (100, 3)

    def test_with_correlation_matrix(self):
        """Test with provided correlation matrix."""
        corr_matrix = np.array([[1.0, 0.5], [0.5, 1.0]])
        data = generate_correlated_data(100, 2, correlation_matrix=corr_matrix, seed=42)
        assert data.shape == (100, 2)

    def test_correlated_data_without_seed(self):
        """Test correlated data generation without seed."""
        data = generate_correlated_data(100, 3, seed=None)
        assert data.shape == (100, 3)


class TestInjectNoise:
    """Test noise injection."""

    def test_gaussian_noise(self):
        """Test Gaussian noise injection."""
        signal = np.ones(100)
        noisy = inject_noise(signal, noise_type="gaussian", noise_level=0.1, seed=42)
        assert noisy.shape == signal.shape
        assert not np.allclose(signal, noisy)

    def test_uniform_noise(self):
        """Test uniform noise injection."""
        signal = np.ones(100)
        noisy = inject_noise(signal, noise_type="uniform", noise_level=0.1, seed=42)
        assert noisy.shape == signal.shape

    def test_salt_pepper_noise(self):
        """Test salt and pepper noise injection."""
        signal = np.ones(100)
        noisy = inject_noise(signal, noise_type="salt_pepper", noise_level=0.1, seed=42)
        assert noisy.shape == signal.shape
        # Salt and pepper should set some values to min or max
        assert np.any(noisy == signal.min()) or np.any(noisy == signal.max())

    def test_inject_noise_without_seed(self):
        """Test noise injection without seed."""
        signal = np.ones(100)
        noisy = inject_noise(signal, noise_type="gaussian", noise_level=0.1, seed=None)
        assert noisy.shape == signal.shape

    def test_invalid_noise_type(self):
        """Test invalid noise type raises error."""
        signal = np.ones(100)
        with pytest.raises(ValueError):
            inject_noise(signal, noise_type="invalid", seed=42)


class TestGenerateClassificationDataset:
    """Test classification dataset generation."""

    def test_basic_generation(self):
        """Test basic classification dataset generation."""
        X, y = generate_classification_dataset(50, n_features=2, n_classes=2, seed=42)
        assert X.shape == (100, 2)  # 50 per class * 2 classes
        assert len(y) == 100
        assert len(np.unique(y)) == 2

    def test_classification_dataset_without_seed(self):
        """Test classification dataset generation without seed."""
        X, y = generate_classification_dataset(50, n_features=2, n_classes=2, seed=None)
        assert X.shape == (100, 2)
        assert len(y) == 100
        assert len(np.unique(y)) == 2


class TestValidateData:
    """Test data validation."""

    def test_validate_finite(self):
        """Test finite value validation."""
        data = np.array([1, 2, 3, 4, 5])
        is_valid, msg = validate_data(data, check_finite=True)
        assert is_valid is True

        data_with_nan = np.array([1, 2, np.nan, 4, 5])
        is_valid, msg = validate_data(data_with_nan, check_finite=True)
        assert is_valid is False

    def test_validate_shape(self):
        """Test shape validation."""
        data = np.array([1, 2, 3, 4, 5])
        is_valid, msg = validate_data(data, check_shape=(5,))
        assert is_valid is True

        is_valid, msg = validate_data(data, check_shape=(10,))
        assert is_valid is False

    def test_validate_range(self):
        """Test range validation."""
        data = np.array([1, 2, 3, 4, 5])
        is_valid, msg = validate_data(data, check_range=(0, 10))
        assert is_valid is True

        is_valid, msg = validate_data(data, check_range=(0, 3))
        assert is_valid is False

    def test_validate_all_checks_pass(self):
        """Test validation when all checks pass."""
        data = np.array([1, 2, 3, 4, 5])
        is_valid, msg = validate_data(
            data, check_finite=True, check_shape=(5,), check_range=(0, 10)
        )
        assert is_valid is True
        assert msg is None

    def test_validate_no_checks(self):
        """Test validation with no checks enabled."""
        data = np.array([1, 2, 3, 4, 5])
        is_valid, msg = validate_data(data, check_finite=False)
        assert is_valid is True
        assert msg is None
