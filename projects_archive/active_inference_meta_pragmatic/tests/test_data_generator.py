"""Tests for data_generator.py module.

Comprehensive tests for the DataGenerator class and its methods,
ensuring all synthetic data generation functions work correctly.
"""

import numpy as np
import pytest
from src.data_generator import DataGenerator


class TestDataGenerator:
    """Test DataGenerator class functionality."""

    def test_initialization_no_seed(self):
        """Test DataGenerator initialization without seed."""
        generator = DataGenerator()

        assert generator.rng is not None
        assert isinstance(generator.rng, np.random.RandomState)

    def test_initialization_with_seed(self):
        """Test DataGenerator initialization with seed."""
        seed = 42
        generator = DataGenerator(seed=seed)

        assert generator.rng is not None
        assert isinstance(generator.rng, np.random.RandomState)

    def test_seed_reproducibility(self):
        """Test that same seed produces identical results."""
        seed = 123
        gen1 = DataGenerator(seed=seed)
        gen2 = DataGenerator(seed=seed)

        data1 = gen1.generate_time_series(n_points=10, seed=seed)
        data2 = gen2.generate_time_series(n_points=10, seed=seed)

        np.testing.assert_array_equal(data1, data2)

    def test_generate_time_series_stationary(self):
        """Test time series generation with stationary trend."""
        generator = DataGenerator(seed=42)

        series = generator.generate_time_series(n_points=100, trend="stationary")

        assert len(series) == 100
        assert isinstance(series, np.ndarray)

        # Stationary should have mean close to zero
        assert abs(np.mean(series)) < 0.5  # Allow for noise

    def test_generate_time_series_linear(self):
        """Test time series generation with linear trend."""
        generator = DataGenerator(seed=42)

        series = generator.generate_time_series(n_points=100, trend="linear")

        assert len(series) == 100
        assert isinstance(series, np.ndarray)

        # Linear trend should show increasing values
        assert series[-1] > series[0]

    def test_generate_time_series_exponential(self):
        """Test time series generation with exponential trend."""
        generator = DataGenerator(seed=42)

        series = generator.generate_time_series(n_points=50, trend="exponential")

        assert len(series) == 50
        assert isinstance(series, np.ndarray)

        # Exponential should grow rapidly
        assert series[-1] > series[0]
        assert series[-1] > series[len(series) // 2]  # Some growth

    def test_generate_time_series_sinusoidal(self):
        """Test time series generation with sinusoidal trend."""
        generator = DataGenerator(seed=42)

        series = generator.generate_time_series(n_points=100, trend="sinusoidal")

        assert len(series) == 100
        assert isinstance(series, np.ndarray)

        # Sinusoidal should oscillate around zero
        assert abs(np.mean(series)) < 0.5

    def test_generate_time_series_with_seasonality(self):
        """Test time series generation with seasonality."""
        generator = DataGenerator(seed=42)

        series_seasonal = generator.generate_time_series(
            n_points=100, trend="stationary", seasonality=True
        )

        assert len(series_seasonal) == 100
        assert isinstance(series_seasonal, np.ndarray)

    def test_generate_time_series_invalid_trend(self):
        """Test time series generation with invalid trend type."""
        generator = DataGenerator(seed=42)

        with pytest.raises(Exception):  # ValidationError
            generator.generate_time_series(trend="invalid")

    def test_generate_time_series_custom_noise(self):
        """Test time series generation with custom noise level."""
        generator = DataGenerator(seed=42)

        # Low noise
        series_low = generator.generate_time_series(n_points=100, noise_level=0.01)
        # High noise
        series_high = generator.generate_time_series(n_points=100, noise_level=1.0)

        assert len(series_low) == 100
        assert len(series_high) == 100

        # High noise should have higher variance
        assert np.var(series_high) > np.var(series_low)

    def test_generate_categorical_observations_uniform(self):
        """Test categorical observation generation with uniform distribution."""
        generator = DataGenerator(seed=42)

        observations = generator.generate_categorical_observations(
            n_samples=100, n_categories=3, distribution="uniform"
        )

        assert len(observations) == 100
        assert isinstance(observations, np.ndarray)
        assert all(0 <= obs < 3 for obs in observations)

        # Check approximate uniformity
        unique, counts = np.unique(observations, return_counts=True)
        assert len(unique) <= 3  # May not see all categories in small sample
        assert max(counts) - min(counts) <= 20  # Rough uniformity check

    def test_generate_categorical_observations_skewed(self):
        """Test categorical observation generation with skewed distribution."""
        generator = DataGenerator(seed=42)

        observations = generator.generate_categorical_observations(
            n_samples=1000, n_categories=4, distribution="skewed"
        )

        assert len(observations) == 1000
        assert isinstance(observations, np.ndarray)
        assert all(0 <= obs < 4 for obs in observations)

        # Check that lower indices appear more frequently
        unique, counts = np.unique(observations, return_counts=True)
        if len(counts) > 1:
            assert counts[0] >= counts[-1]  # First category most frequent

    def test_generate_categorical_observations_bimodal(self):
        """Test categorical observation generation with bimodal distribution."""
        generator = DataGenerator(seed=42)

        observations = generator.generate_categorical_observations(
            n_samples=1000, n_categories=3, distribution="bimodal"
        )

        assert len(observations) == 1000
        assert isinstance(observations, np.ndarray)
        assert all(0 <= obs < 3 for obs in observations)

    def test_generate_categorical_observations_invalid_distribution(self):
        """Test categorical observation generation with invalid distribution."""
        generator = DataGenerator(seed=42)

        with pytest.raises(Exception):  # ValidationError
            generator.generate_categorical_observations(distribution="invalid")

    def test_generate_state_sequences_markov(self):
        """Test state sequence generation with Markov transitions."""
        generator = DataGenerator(seed=42)

        sequences = generator.generate_state_sequences(
            n_sequences=5, sequence_length=20, n_states=3, transition_type="markov"
        )

        assert sequences.shape == (5, 20)
        assert isinstance(sequences, np.ndarray)
        assert all(0 <= state < 3 for seq in sequences for state in seq)

    def test_generate_state_sequences_random(self):
        """Test state sequence generation with random transitions."""
        generator = DataGenerator(seed=42)

        sequences = generator.generate_state_sequences(
            n_sequences=3, sequence_length=15, n_states=4, transition_type="random"
        )

        assert sequences.shape == (3, 15)
        assert isinstance(sequences, np.ndarray)
        assert all(0 <= state < 4 for seq in sequences for state in seq)

    def test_generate_state_sequences_sticky(self):
        """Test state sequence generation with sticky transitions."""
        generator = DataGenerator(seed=42)

        sequences = generator.generate_state_sequences(
            n_sequences=2, sequence_length=25, n_states=3, transition_type="sticky"
        )

        assert sequences.shape == (2, 25)
        assert isinstance(sequences, np.ndarray)
        assert all(0 <= state < 3 for seq in sequences for state in seq)

    def test_generate_state_sequences_invalid_transition(self):
        """Test state sequence generation with invalid transition type."""
        generator = DataGenerator(seed=42)

        with pytest.raises(Exception):  # ValidationError
            generator.generate_state_sequences(transition_type="invalid")

    def test_generate_synthetic_dataset(self):
        """Test synthetic dataset generation for classification."""
        generator = DataGenerator(seed=42)

        X, y = generator.generate_synthetic_dataset(
            n_samples=100, n_features=5, n_classes=3
        )

        assert X.shape == (100, 5)
        assert y.shape == (100,)
        assert isinstance(X, np.ndarray)
        assert isinstance(y, np.ndarray)
        assert all(0 <= label < 3 for label in y)

    def test_generate_synthetic_dataset_single_class(self):
        """Test synthetic dataset generation with single class."""
        generator = DataGenerator(seed=42)

        X, y = generator.generate_synthetic_dataset(
            n_samples=50, n_features=2, n_classes=1
        )

        assert X.shape == (50, 2)
        assert y.shape == (50,)
        assert all(label == 0 for label in y)

    def test_generate_synthetic_dataset_edge_cases(self):
        """Test synthetic dataset generation with edge cases."""
        generator = DataGenerator(seed=42)

        # Small dataset
        X, y = generator.generate_synthetic_dataset(
            n_samples=5, n_features=1, n_classes=2
        )
        assert X.shape == (5, 1)
        assert y.shape == (5,)

        # Large feature space
        X, y = generator.generate_synthetic_dataset(
            n_samples=20, n_features=10, n_classes=2
        )
        assert X.shape == (20, 10)
        assert y.shape == (20,)

    def test_all_methods_with_seed_reproducibility(self):
        """Test that all generation methods are reproducible with seed."""
        seed = 999
        gen1 = DataGenerator(seed=seed)
        gen2 = DataGenerator(seed=seed)

        # Time series
        ts1 = gen1.generate_time_series(n_points=20)
        ts2 = gen2.generate_time_series(n_points=20)
        np.testing.assert_array_equal(ts1, ts2)

        # Categorical observations
        cat1 = gen1.generate_categorical_observations(n_samples=15)
        cat2 = gen2.generate_categorical_observations(n_samples=15)
        np.testing.assert_array_equal(cat1, cat2)

        # State sequences
        seq1 = gen1.generate_state_sequences(n_sequences=2, sequence_length=10)
        seq2 = gen2.generate_state_sequences(n_sequences=2, sequence_length=10)
        np.testing.assert_array_equal(seq1, seq2)

        # Synthetic dataset
        X1, y1 = gen1.generate_synthetic_dataset(n_samples=10, n_features=3)
        X2, y2 = gen2.generate_synthetic_dataset(n_samples=10, n_features=3)
        np.testing.assert_array_equal(X1, X2)
        np.testing.assert_array_equal(y1, y2)

    def test_error_handling_comprehensive(self):
        """Test error handling across all methods."""
        generator = DataGenerator(seed=42)

        # Test invalid parameters for each method
        with pytest.raises(Exception):
            generator.generate_time_series(trend="invalid")

        with pytest.raises(Exception):
            generator.generate_categorical_observations(distribution="invalid")

        with pytest.raises(Exception):
            generator.generate_state_sequences(transition_type="invalid")

    def test_output_types_and_shapes(self):
        """Test that all methods return correct types and shapes."""
        generator = DataGenerator(seed=42)

        # Time series
        ts = generator.generate_time_series(n_points=50)
        assert isinstance(ts, np.ndarray)
        assert ts.shape == (50,)
        assert ts.dtype == float

        # Categorical observations
        cat = generator.generate_categorical_observations(n_samples=30, n_categories=4)
        assert isinstance(cat, np.ndarray)
        assert cat.shape == (30,)
        assert cat.dtype == int

        # State sequences
        seq = generator.generate_state_sequences(n_sequences=3, sequence_length=20)
        assert isinstance(seq, np.ndarray)
        assert seq.shape == (3, 20)
        assert seq.dtype == int

        # Synthetic dataset
        X, y = generator.generate_synthetic_dataset(n_samples=25, n_features=4)
        assert isinstance(X, np.ndarray)
        assert isinstance(y, np.ndarray)
        assert X.shape == (25, 4)
        assert y.shape == (25,)
        assert X.dtype == float
        assert y.dtype == int

    def test_generate_observation_matrix_default(self):
        """Test observation matrix generation with default parameters."""
        generator = DataGenerator(seed=42)

        A = generator.generate_observation_matrix()

        assert A.shape == (4, 3)  # Default: 4 observations, 3 states
        assert isinstance(A, np.ndarray)
        # Each column should sum to 1 (probability distribution)
        np.testing.assert_allclose(A.sum(axis=0), 1.0, rtol=1e-6)

    def test_generate_observation_matrix_custom(self):
        """Test observation matrix generation with custom parameters."""
        generator = DataGenerator(seed=42)

        A = generator.generate_observation_matrix(
            n_states=5, n_observations=3, noise_level=0.2
        )

        assert A.shape == (3, 5)
        assert isinstance(A, np.ndarray)
        np.testing.assert_allclose(A.sum(axis=0), 1.0, rtol=1e-6)

    def test_generate_observation_matrix_no_noise(self):
        """Test observation matrix generation with zero noise."""
        generator = DataGenerator(seed=42)

        A = generator.generate_observation_matrix(
            n_states=3, n_observations=3, noise_level=0.0
        )

        assert A.shape == (3, 3)
        # With no noise, should be deterministic
        np.testing.assert_allclose(A.sum(axis=0), 1.0, rtol=1e-6)

    def test_generate_observation_matrix_high_noise(self):
        """Test observation matrix generation with high noise."""
        generator = DataGenerator(seed=42)

        A = generator.generate_observation_matrix(
            n_states=3, n_observations=4, noise_level=0.5
        )

        assert A.shape == (4, 3)
        np.testing.assert_allclose(A.sum(axis=0), 1.0, rtol=1e-6)

    def test_generate_transition_matrix_controlled(self):
        """Test transition matrix generation with controlled transitions."""
        generator = DataGenerator(seed=42)

        B = generator.generate_transition_matrix(
            n_states=3, n_actions=2, transition_type="controlled"
        )

        assert B.shape == (3, 3, 2)
        assert isinstance(B, np.ndarray)
        # Each column should sum to 1
        for a in range(2):
            np.testing.assert_allclose(B[:, :, a].sum(axis=0), 1.0, rtol=1e-6)

    def test_generate_transition_matrix_random(self):
        """Test transition matrix generation with random transitions."""
        generator = DataGenerator(seed=42)

        B = generator.generate_transition_matrix(
            n_states=4, n_actions=3, transition_type="random"
        )

        assert B.shape == (4, 4, 3)
        for a in range(3):
            np.testing.assert_allclose(B[:, :, a].sum(axis=0), 1.0, rtol=1e-6)

    def test_generate_transition_matrix_deterministic(self):
        """Test transition matrix generation with deterministic transitions."""
        generator = DataGenerator(seed=42)

        B = generator.generate_transition_matrix(
            n_states=3, n_actions=2, transition_type="deterministic"
        )

        assert B.shape == (3, 3, 2)
        for a in range(2):
            np.testing.assert_allclose(B[:, :, a].sum(axis=0), 1.0, rtol=1e-6)

    def test_generate_transition_matrix_invalid_type(self):
        """Test transition matrix generation with invalid transition type."""
        generator = DataGenerator(seed=42)

        with pytest.raises(Exception):  # ValidationError
            generator.generate_transition_matrix(transition_type="invalid")

    def test_generate_preference_vector_simple(self):
        """Test preference vector generation with simple preferences."""
        generator = DataGenerator(seed=42)

        C = generator.generate_preference_vector(
            n_observations=4, preference_type="simple"
        )

        assert C.shape == (4,)
        assert isinstance(C, np.ndarray)

    def test_generate_preference_vector_complex(self):
        """Test preference vector generation with complex preferences."""
        generator = DataGenerator(seed=42)

        C = generator.generate_preference_vector(
            n_observations=5, preference_type="complex"
        )

        assert C.shape == (5,)
        assert isinstance(C, np.ndarray)

    def test_generate_preference_vector_neutral(self):
        """Test preference vector generation with neutral preferences."""
        generator = DataGenerator(seed=42)

        C = generator.generate_preference_vector(
            n_observations=3, preference_type="neutral"
        )

        assert C.shape == (3,)
        assert isinstance(C, np.ndarray)

    def test_generate_preference_vector_invalid_type(self):
        """Test preference vector generation with invalid preference type."""
        generator = DataGenerator(seed=42)

        with pytest.raises(Exception):  # ValidationError
            generator.generate_preference_vector(preference_type="invalid")

    def test_generate_categorical_observations_n_categories_not_3(self):
        """Test categorical observations with n_categories != 3 for bimodal."""
        generator = DataGenerator(seed=42)

        observations = generator.generate_categorical_observations(
            n_samples=100, n_categories=5, distribution="bimodal"
        )

        assert len(observations) == 100
        assert all(0 <= obs < 5 for obs in observations)

    def test_generate_synthetic_dataset_invalid_distribution(self):
        """Test synthetic dataset generation with invalid distribution."""
        generator = DataGenerator(seed=42)

        with pytest.raises(Exception):  # ValidationError
            generator.generate_synthetic_dataset(distribution="invalid")

    def test_generate_time_series_convenience_function(self):
        """Test generate_time_series convenience function."""
        from src.data_generator import generate_time_series

        time, values = generate_time_series(n_points=50, seed=42)

        assert len(time) == 50
        assert len(values) == 50
        assert isinstance(time, np.ndarray)
        assert isinstance(values, np.ndarray)
        np.testing.assert_array_equal(time, np.arange(50))

    def test_generate_synthetic_data_convenience_function(self):
        """Test generate_synthetic_data convenience function."""
        from src.data_generator import generate_synthetic_data

        data = generate_synthetic_data(n_samples=100, n_features=3, seed=42)

        assert data.shape == (100, 3)
        assert isinstance(data, np.ndarray)

    def test_generate_synthetic_data_invalid_distribution(self):
        """Test generate_synthetic_data with invalid distribution."""
        from src.data_generator import generate_synthetic_data

        with pytest.raises(Exception):  # ValidationError
            generate_synthetic_data(distribution="invalid")

    def test_demonstrate_data_generation(self):
        """Test demonstrate_data_generation function."""
        from src.data_generator import demonstrate_data_generation

        result = demonstrate_data_generation()

        assert isinstance(result, dict)
        assert "time_series" in result
        assert "categorical_observations" in result
        assert "state_sequences" in result
        assert "generative_model_matrices" in result
        assert "purpose" in result
        # Check that time_series has expected keys
        # Note: demonstrate_data_generation may generate time from values
        assert "values" in result["time_series"] or "time" in result["time_series"]
