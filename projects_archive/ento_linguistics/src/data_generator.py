"""Data generation for scientific simulations and testing.

This module provides synthetic data generation with configurable distributions,
realistic dataset creation, noise injection, and data validation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


def generate_synthetic_data(
    n_samples: int,
    n_features: int = 1,
    distribution: str = "normal",
    seed: Optional[int] = None,
    **kwargs,
) -> np.ndarray:
    """Generate synthetic data with specified distribution.

    Args:
        n_samples: Number of samples
        n_features: Number of features
        distribution: Distribution type (normal, uniform, exponential, etc.)
        seed: Random seed
        **kwargs: Distribution-specific parameters

    Returns:
        Array of generated data
    """
    if seed is not None:
        np.random.seed(seed)

    if distribution == "normal":
        mean = kwargs.get("mean", 0.0)
        std = kwargs.get("std", 1.0)
        return np.random.normal(mean, std, size=(n_samples, n_features))

    elif distribution == "uniform":
        low = kwargs.get("low", 0.0)
        high = kwargs.get("high", 1.0)
        return np.random.uniform(low, high, size=(n_samples, n_features))

    elif distribution == "exponential":
        scale = kwargs.get("scale", 1.0)
        return np.random.exponential(scale, size=(n_samples, n_features))

    elif distribution == "poisson":
        lam = kwargs.get("lam", 1.0)
        return np.random.poisson(lam, size=(n_samples, n_features))

    elif distribution == "beta":
        a = kwargs.get("a", 2.0)
        b = kwargs.get("b", 2.0)
        return np.random.beta(a, b, size=(n_samples, n_features))

    else:
        raise ValueError(f"Unknown distribution: {distribution}")


def generate_time_series(
    n_points: int,
    trend: str = "linear",
    noise_level: float = 0.1,
    seed: Optional[int] = None,
    **kwargs,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate time series data.

    Args:
        n_points: Number of time points
        trend: Trend type (linear, quadratic, exponential, sinusoidal)
        noise_level: Standard deviation of noise
        seed: Random seed
        **kwargs: Trend-specific parameters

    Returns:
        Tuple of (time, values) arrays
    """
    if seed is not None:
        np.random.seed(seed)

    time = np.linspace(0, 10, n_points)

    if trend == "linear":
        slope = kwargs.get("slope", 1.0)
        intercept = kwargs.get("intercept", 0.0)
        values = slope * time + intercept
    elif trend == "quadratic":
        a = kwargs.get("a", 0.1)
        b = kwargs.get("b", 1.0)
        c = kwargs.get("c", 0.0)
        values = a * time**2 + b * time + c
    elif trend == "exponential":
        a = kwargs.get("a", 1.0)
        b = kwargs.get("b", 0.5)
        values = a * np.exp(b * time)
    elif trend == "sinusoidal":
        amplitude = kwargs.get("amplitude", 1.0)
        frequency = kwargs.get("frequency", 1.0)
        phase = kwargs.get("phase", 0.0)
        values = amplitude * np.sin(2 * np.pi * frequency * time + phase)
    else:
        raise ValueError(f"Unknown trend: {trend}")

    # Add noise
    noise = np.random.normal(0, noise_level, size=n_points)
    values = values + noise

    return time, values


def generate_correlated_data(
    n_samples: int,
    n_features: int,
    correlation_matrix: Optional[np.ndarray] = None,
    seed: Optional[int] = None,
) -> np.ndarray:
    """Generate correlated multivariate data.

    Args:
        n_samples: Number of samples
        n_features: Number of features
        correlation_matrix: Correlation matrix (if None, generates random)
        seed: Random seed

    Returns:
        Array of correlated data
    """
    if seed is not None:
        np.random.seed(seed)

    if correlation_matrix is None:
        # Generate random positive definite correlation matrix
        A = np.random.rand(n_features, n_features)
        correlation_matrix = np.dot(A, A.T)
        # Normalize to correlation matrix
        stds = np.sqrt(np.diag(correlation_matrix))
        correlation_matrix = correlation_matrix / np.outer(stds, stds)

    # Generate data using Cholesky decomposition
    L = np.linalg.cholesky(correlation_matrix)
    uncorrelated = np.random.randn(n_samples, n_features)
    correlated = uncorrelated @ L.T

    return correlated


def inject_noise(
    data: np.ndarray,
    noise_type: str = "gaussian",
    noise_level: float = 0.1,
    seed: Optional[int] = None,
) -> np.ndarray:
    """Inject noise into data.

    Args:
        data: Input data
        noise_type: Type of noise (gaussian, uniform, salt_pepper)
        noise_level: Noise level/strength
        seed: Random seed

    Returns:
        Data with noise added
    """
    if seed is not None:
        np.random.seed(seed)

    if noise_type == "gaussian":
        noise = np.random.normal(0, noise_level, size=data.shape)
        return data + noise

    elif noise_type == "uniform":
        noise = np.random.uniform(-noise_level, noise_level, size=data.shape)
        return data + noise

    elif noise_type == "salt_pepper":
        # Randomly set some values to min or max
        noisy = data.copy()
        mask = np.random.random(size=data.shape) < noise_level
        salt = np.random.random(size=data.shape) < 0.5
        noisy[mask & salt] = data.max()
        noisy[mask & ~salt] = data.min()
        return noisy

    else:
        raise ValueError(f"Unknown noise type: {noise_type}")


def generate_classification_dataset(
    n_samples: int,
    n_features: int = 2,
    n_classes: int = 2,
    class_separation: float = 1.0,
    seed: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate classification dataset.

    Args:
        n_samples: Number of samples per class
        n_features: Number of features
        n_classes: Number of classes
        class_separation: Separation between class centers
        seed: Random seed

    Returns:
        Tuple of (features, labels)
    """
    if seed is not None:
        np.random.seed(seed)

    X_list = []
    y_list = []

    for class_idx in range(n_classes):
        # Generate class center
        center = np.array([class_separation * class_idx] * n_features)

        # Generate samples around center
        X_class = np.random.normal(center, 0.5, size=(n_samples, n_features))
        y_class = np.full(n_samples, class_idx)

        X_list.append(X_class)
        y_list.append(y_class)

    X = np.vstack(X_list)
    y = np.hstack(y_list)

    # Shuffle
    indices = np.random.permutation(len(X))
    X = X[indices]
    y = y[indices]

    return X, y


def validate_data(
    data: np.ndarray,
    check_finite: bool = True,
    check_shape: Optional[Tuple[int, ...]] = None,
    check_range: Optional[Tuple[float, float]] = None,
) -> Tuple[bool, Optional[str]]:
    """Validate data quality.

    Args:
        data: Data to validate
        check_finite: Check for finite values
        check_shape: Expected shape
        check_range: Expected (min, max) range

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check finite
    if check_finite and not np.all(np.isfinite(data)):
        return False, "Data contains non-finite values"

    # Check shape
    if check_shape is not None and data.shape != check_shape:
        return False, f"Expected shape {check_shape}, got {data.shape}"

    # Check range
    if check_range is not None:
        min_val, max_val = check_range
        if np.any(data < min_val) or np.any(data > max_val):
            return False, f"Data outside range [{min_val}, {max_val}]"

    return True, None
