"""Synthetic data generation for Ento-Linguistic analysis.

This module provides functions for generating synthetic datasets and time series
for testing, simulation, and benchmarking of terminology extraction and
discourse analysis models.
"""

import numpy as np
from typing import Tuple, List, Optional, Union

__all__ = [
    "generate_synthetic_data",
    "generate_time_series",
]


def generate_synthetic_data(
    n_samples: int = 100,
    n_features: int = 1,
    distribution: str = "normal",
    mean: float = 0.0,
    std: float = 1.0,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate synthetic data for testing and simulation.

    Args:
        n_samples: Number of samples to generate
        n_features: Number of features per sample
        distribution: Type of distribution ('normal', 'uniform', 'exponential')
        mean: Mean of the distribution (for normal)
        std: Standard deviation (for normal)
        seed: Random seed for reproducibility

    Returns:
        Numpy array of shape (n_samples, n_features) or (n_samples,) if n_features=1
    """
    rng = np.random.default_rng(seed)

    if distribution == "normal":
        data = rng.normal(mean, std, (n_samples, n_features))
    elif distribution == "uniform":
        data = rng.uniform(mean - std, mean + std, (n_samples, n_features))
    elif distribution == "exponential":
        data = rng.exponential(scale=std, size=(n_samples, n_features))
    else:
        raise ValueError(f"Unknown distribution: {distribution}")

    if n_features == 1:
        return data.flatten()
    return data

def generate_time_series(
    n_points: int = 100,
    trend: str = "linear",
    noise_level: float = 0.1,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic time series data.

    Args:
        n_points: Number of time points
        trend: Type of trend ('linear', 'sinusoidal', 'exponential')
        noise_level: Standard deviation of added Gaussian noise
        seed: Random seed for reproducibility

    Returns:
        Tuple of (time_points, values)
    """
    rng = np.random.default_rng(seed)

    time = np.linspace(0, 10, n_points)

    if trend == "linear":
        values = time * 0.5 + 2.0
    elif trend == "sinusoidal":
        values = np.sin(time) * 2.0 + 3.0
    elif trend == "exponential":
        values = np.exp(time * 0.2)
    else:
        raise ValueError(f"Unknown trend: {trend}")

    # Add noise
    noise = rng.normal(0, noise_level, n_points)
    values += noise

    return time, values
