"""Data Generation for Active Inference Meta-Pragmatic Framework.

This module provides synthetic data generation capabilities for demonstrating
Active Inference concepts, including time series data, categorical observations,
and structured datasets for theoretical analysis.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from numpy.typing import NDArray

from infrastructure.core.exceptions import ValidationError
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


class DataGenerator:
    """Data generator for Active Inference demonstrations and testing.

    Provides controlled synthetic data generation for theoretical analysis
    and algorithm validation.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        """Initialize data generator.

        Args:
            seed: Random seed for reproducibility
        """
        self.rng = np.random.RandomState(seed)
        if seed is not None:
            logger.info(f"Initialized data generator with seed: {seed}")
        else:
            logger.info("Initialized data generator without fixed seed")

    def generate_time_series(self, n_points: int = 100,
                           trend: str = "stationary",
                           noise_level: float = 0.1,
                           seasonality: bool = False) -> NDArray:
        """Generate synthetic time series data.

        Args:
            n_points: Number of data points to generate
            trend: Type of trend ('stationary', 'linear', 'exponential', 'sinusoidal')
            noise_level: Standard deviation of additive noise
            seasonality: Whether to include seasonal component

        Returns:
            Generated time series array
        """
        try:
            t = np.arange(n_points, dtype=float)

            # Generate base signal based on trend
            if trend == "stationary":
                signal = np.zeros(n_points)
            elif trend == "linear":
                signal = 0.01 * t
            elif trend == "exponential":
                signal = np.exp(0.01 * t) - 1
            elif trend == "sinusoidal":
                signal = np.sin(0.1 * t)
            else:
                raise ValidationError(f"Unknown trend type: {trend}")

            # Add seasonality if requested
            if seasonality:
                seasonal = 0.5 * np.sin(0.05 * t) + 0.3 * np.sin(0.2 * t)
                signal += seasonal

            # Add noise
            noise = self.rng.normal(0, noise_level, n_points)
            time_series = signal + noise

            logger.debug(f"Generated time series: {n_points} points, trend={trend}")
            return time_series

        except Exception as e:
            logger.error(f"Error generating time series: {e}")
            raise ValidationError(f"Time series generation failed: {e}") from e

    def generate_categorical_observations(self, n_samples: int = 100,
                                        n_categories: int = 3,
                                        distribution: str = "uniform") -> NDArray:
        """Generate categorical observation data.

        Args:
            n_samples: Number of samples to generate
            n_categories: Number of observation categories
            distribution: Distribution type ('uniform', 'skewed', 'bimodal')

        Returns:
            Array of categorical observations (integer indices)
        """
        try:
            if distribution == "uniform":
                probs = np.ones(n_categories) / n_categories
            elif distribution == "skewed":
                # Exponential decay probabilities
                probs = np.exp(-np.arange(n_categories))
                probs = probs / probs.sum()
            elif distribution == "bimodal":
                # Two peaks
                probs = np.array([0.7, 0.1, 0.2])  # Adjust for n_categories
                if n_categories != 3:
                    # Simple extension - normalize to requested categories
                    probs = np.ones(n_categories) / n_categories
                    probs[0] = 0.5  # Make first category more likely
                    probs = probs / probs.sum()
            else:
                raise ValidationError(f"Unknown distribution: {distribution}")

            observations = self.rng.choice(n_categories, size=n_samples, p=probs)

            logger.debug(f"Generated categorical observations: {n_samples} samples, {n_categories} categories")
            return observations

        except Exception as e:
            logger.error(f"Error generating categorical observations: {e}")
            raise ValidationError(f"Categorical observation generation failed: {e}") from e

    def generate_state_sequences(self, n_sequences: int = 10,
                               sequence_length: int = 50,
                               n_states: int = 3,
                               transition_type: str = "markov") -> NDArray:
        """Generate sequences of hidden states.

        Args:
            n_sequences: Number of sequences to generate
            sequence_length: Length of each sequence
            n_states: Number of possible states
            transition_type: Type of transitions ('markov', 'random', 'sticky')

        Returns:
            Array of shape (n_sequences, sequence_length) with state indices
        """
        try:
            sequences = np.zeros((n_sequences, sequence_length), dtype=int)

            for seq_idx in range(n_sequences):
                current_state = self.rng.randint(n_states)

                for t in range(sequence_length):
                    sequences[seq_idx, t] = current_state

                    # Generate next state based on transition type
                    if transition_type == "markov":
                        # Simple Markov chain with self-transition bias
                        if self.rng.random() < 0.7:  # Stay in current state
                            next_state = current_state
                        else:
                            next_state = self.rng.randint(n_states)
                    elif transition_type == "random":
                        next_state = self.rng.randint(n_states)
                    elif transition_type == "sticky":
                        # Strong preference to stay in current state
                        if self.rng.random() < 0.9:
                            next_state = current_state
                        else:
                            next_state = self.rng.randint(n_states)
                    else:
                        raise ValidationError(f"Unknown transition type: {transition_type}")

                    current_state = next_state

            logger.debug(f"Generated state sequences: {n_sequences} sequences, length {sequence_length}")
            return sequences

        except Exception as e:
            logger.error(f"Error generating state sequences: {e}")
            raise ValidationError(f"State sequence generation failed: {e}") from e

    def generate_observation_matrix(self, n_states: int = 3,
                                  n_observations: int = 4,
                                  noise_level: float = 0.1) -> NDArray:
        """Generate observation likelihood matrix A.

        Args:
            n_states: Number of hidden states
            n_observations: Number of possible observations
            noise_level: Amount of noise in the mapping

        Returns:
            Observation likelihood matrix A of shape (n_observations, n_states)
        """
        try:
            # Create base deterministic mapping
            A = np.zeros((n_observations, n_states))

            # Each state has a preferred observation, but with some noise
            for s in range(n_states):
                preferred_obs = s % n_observations  # Cycle through observations
                A[preferred_obs, s] = 1.0 - noise_level

                # Distribute remaining probability
                remaining_prob = noise_level
                other_obs = [i for i in range(n_observations) if i != preferred_obs]

                for obs in other_obs:
                    A[obs, s] = remaining_prob / len(other_obs)

            # Ensure each column sums to 1
            A = A / A.sum(axis=0, keepdims=True)

            logger.debug(f"Generated observation matrix: {n_observations}×{n_states}")
            return A

        except Exception as e:
            logger.error(f"Error generating observation matrix: {e}")
            raise ValidationError(f"Observation matrix generation failed: {e}") from e

    def generate_transition_matrix(self, n_states: int = 3,
                                 n_actions: int = 2,
                                 transition_type: str = "controlled") -> NDArray:
        """Generate state transition matrix B.

        Args:
            n_states: Number of hidden states
            n_actions: Number of possible actions
            transition_type: Type of transitions ('controlled', 'random', 'deterministic')

        Returns:
            Transition matrix B of shape (n_states, n_states, n_actions)
        """
        try:
            B = np.zeros((n_states, n_states, n_actions))

            if transition_type == "controlled":
                # Action 0: stay in current state
                for s in range(n_states):
                    B[s, s, 0] = 1.0

                # Action 1: move to next state (cyclic)
                for s in range(n_states):
                    next_s = (s + 1) % n_states
                    B[next_s, s, 1] = 1.0

            elif transition_type == "random":
                # Uniform random transitions for all actions
                for a in range(n_actions):
                    for s in range(n_states):
                        B[:, s, a] = 1.0 / n_states

            elif transition_type == "deterministic":
                # Each action deterministically changes state
                for a in range(n_actions):
                    for s in range(n_states):
                        target_s = (s + a + 1) % n_states
                        B[target_s, s, a] = 1.0

            else:
                raise ValidationError(f"Unknown transition type: {transition_type}")

            logger.debug(f"Generated transition matrix: {n_states}×{n_states}×{n_actions}")
            return B

        except Exception as e:
            logger.error(f"Error generating transition matrix: {e}")
            raise ValidationError(f"Transition matrix generation failed: {e}") from e

    def generate_preference_vector(self, n_observations: int = 4,
                                 preference_type: str = "simple") -> NDArray:
        """Generate preference vector C.

        Args:
            n_observations: Number of possible observations
            preference_type: Type of preferences ('simple', 'complex', 'neutral')

        Returns:
            Preference vector C of length n_observations
        """
        try:
            if preference_type == "simple":
                # Prefer first observation, avoid last
                C = np.linspace(2.0, -2.0, n_observations)
            elif preference_type == "complex":
                # More complex preference structure
                C = np.array([1.5, -1.0, 0.5, -0.5, 2.0, -2.0][:n_observations])
                if len(C) < n_observations:
                    C = np.pad(C, (0, n_observations - len(C)), constant_values=0.0)
            elif preference_type == "neutral":
                # No strong preferences
                C = np.zeros(n_observations)
            else:
                raise ValidationError(f"Unknown preference type: {preference_type}")

            logger.debug(f"Generated preference vector: {n_observations} observations")
            return C

        except Exception as e:
            logger.error(f"Error generating preference vector: {e}")
            raise ValidationError(f"Preference vector generation failed: {e}") from e

    def create_synthetic_dataset(self, n_samples: int = 1000,
                               n_features: int = 2,
                               n_classes: int = 3,
                               distribution: str = "gaussian") -> Tuple[NDArray, NDArray]:
        """Create synthetic classification dataset.

        Args:
            n_samples: Total number of samples
            n_features: Number of features
            n_classes: Number of classes
            distribution: Data distribution type

        Returns:
            Tuple of (features, labels) arrays
        """
        try:
            if distribution == "gaussian":
                # Generate Gaussian clusters
                features = np.zeros((n_samples, n_features))
                labels = np.zeros(n_samples, dtype=int)

                samples_per_class = n_samples // n_classes

                for c in range(n_classes):
                    start_idx = c * samples_per_class
                    end_idx = (c + 1) * samples_per_class if c < n_classes - 1 else n_samples

                    # Class centers in a circle
                    angle = 2 * np.pi * c / n_classes
                    center = np.array([np.cos(angle), np.sin(angle)]) * 2

                    # Generate samples around center
                    n_class_samples = end_idx - start_idx
                    class_features = self.rng.multivariate_normal(
                        center, np.eye(n_features) * 0.5, n_class_samples
                    )

                    features[start_idx:end_idx] = class_features
                    labels[start_idx:end_idx] = c

            else:
                raise ValidationError(f"Unknown distribution: {distribution}")

            logger.debug(f"Created synthetic dataset: {n_samples} samples, {n_features} features, {n_classes} classes")
            return features, labels

        except Exception as e:
            logger.error(f"Error creating synthetic dataset: {e}")
            raise ValidationError(f"Synthetic dataset creation failed: {e}") from e


def generate_time_series(*args, **kwargs) -> Tuple[NDArray, NDArray]:
    """Convenience function for time series generation.

    Returns:
        Tuple of (time_array, values_array)
    """
    generator = DataGenerator()
    values = generator.generate_time_series(*args, **kwargs)
    time = np.arange(len(values))
    return time, values


def generate_synthetic_data(n_samples: int = 100, n_features: int = 2,
                          distribution: str = "normal", seed: int = 42) -> NDArray:
    """Convenience function for synthetic data generation.

    Returns:
        Generated data array
    """
    generator = DataGenerator(seed=seed)

    if distribution == "normal":
        return generator.rng.multivariate_normal(
            np.zeros(n_features), np.eye(n_features), n_samples
        )
    else:
        raise ValidationError(f"Unsupported distribution: {distribution}")


def demonstrate_data_generation() -> Dict[str, Union[str, Dict]]:
    """Demonstrate data generation capabilities.

    Returns:
        Dictionary containing generation demonstrations
    """
    generator = DataGenerator(seed=42)

    # Generate time series
    time, values = generator.generate_time_series(n_points=50, trend="sinusoidal")

    # Generate categorical observations
    observations = generator.generate_categorical_observations(n_samples=30, n_categories=3)

    # Generate state sequences
    sequences = generator.generate_state_sequences(n_sequences=3, sequence_length=10)

    # Generate generative model matrices
    A = generator.generate_observation_matrix(n_states=3, n_observations=4)
    B = generator.generate_transition_matrix(n_states=3, n_actions=2)
    C = generator.generate_preference_vector(n_observations=4)

    demonstration = {
        'time_series': {
            'time': time.tolist()[:10],  # First 10 points
            'values': values.tolist()[:10],
            'trend_type': 'sinusoidal'
        },
        'categorical_observations': {
            'samples': observations.tolist()[:10],
            'categories': 3,
            'distribution': 'uniform'
        },
        'state_sequences': {
            'sequences': sequences.tolist(),
            'n_sequences': 3,
            'sequence_length': 10
        },
        'generative_model_matrices': {
            'A_shape': list(A.shape),
            'B_shape': list(B.shape),
            'C_shape': list(C.shape),
            'A_sample': A[:, :2].tolist(),  # First 2 columns
            'C_values': C.tolist()
        },
        'purpose': """
        These synthetic data generation functions enable controlled testing and
        demonstration of Active Inference algorithms with known ground truth.
        """
    }

    logger.info("Demonstrated data generation capabilities")
    return demonstration