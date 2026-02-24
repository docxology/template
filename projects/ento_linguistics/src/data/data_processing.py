"""Data processing utilities for Ento-Linguistic analysis.

This module provides data cleaning, preprocessing, feature extraction,
and validation pipelines supporting the analysis of entomological terminology
in scientific discourse.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

__all__ = [
    "clean_data",
    "normalize_data",
    "standardize_data",
    "detect_outliers",
    "remove_outliers",
    "extract_features",
    "transform_data",
    "create_validation_pipeline",
]


def clean_data(
    data: np.ndarray,
    remove_nan: bool = True,
    remove_inf: bool = True,
    fill_method: Optional[str] = None,
) -> np.ndarray:
    """Clean data by removing or filling invalid values.

    Args:
        data: Input data
        remove_nan: Remove NaN values
        remove_inf: Remove infinite values
        fill_method: Method to fill missing values (mean, median, zero, None)

    Returns:
        Cleaned data
    """
    cleaned = data.copy()

    # Create mask for invalid values
    invalid_mask = np.zeros(cleaned.shape, dtype=bool)

    if remove_nan:
        # Note: ~np.isfinite catches both NaN and Inf values.
        # When remove_nan=True alone, this also removes Inf.
        invalid_mask |= np.isnan(cleaned)
    if remove_inf:
        invalid_mask |= np.isinf(cleaned)

    if fill_method is not None:
        if fill_method == "mean":
            fill_value = np.nanmean(cleaned)
        elif fill_method == "median":
            fill_value = np.nanmedian(cleaned)
        elif fill_method == "zero":
            fill_value = 0.0
        else:
            raise ValueError(f"Unknown fill method: {fill_method}")

        cleaned[invalid_mask] = fill_value
    else:
        # Remove invalid values (flatten first)
        if invalid_mask.any():
            cleaned = cleaned[~invalid_mask.flatten()].reshape(-1, *cleaned.shape[1:])

    return cleaned


def normalize_data(
    data: np.ndarray, method: str = "z_score", axis: Optional[int] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Normalize data using specified method.

    Args:
        data: Input data
        method: Normalization method (z_score, min_max, unit_vector)
        axis: Axis along which to normalize (None for all data)

    Returns:
        Tuple of (normalized_data, normalization_params)
    """
    if method == "z_score":
        # Z-score normalization: (x - mean) / std
        if axis is not None:
            mean = np.mean(data, axis=axis, keepdims=True)
            std = np.std(data, axis=axis, keepdims=True)
        else:
            mean = np.mean(data)
            std = np.std(data)

        normalized = (data - mean) / (std + 1e-10)
        params = {"mean": mean, "std": std, "method": method}

    elif method == "min_max":
        # Min-max normalization: (x - min) / (max - min)
        if axis is not None:
            min_val = np.min(data, axis=axis, keepdims=True)
            max_val = np.max(data, axis=axis, keepdims=True)
        else:
            min_val = np.min(data)
            max_val = np.max(data)

        normalized = (data - min_val) / (max_val - min_val + 1e-10)
        params = {"min": min_val, "max": max_val, "method": method}

    elif method == "unit_vector":
        # Unit vector normalization: x / ||x||
        if axis is not None:
            norm = np.linalg.norm(data, axis=axis, keepdims=True)
        else:
            norm = np.linalg.norm(data)

        normalized = data / (norm + 1e-10)
        params = {"norm": norm, "method": method}

    else:
        raise ValueError(f"Unknown normalization method: {method}")

    return normalized, params


def standardize_data(
    data: np.ndarray, mean: Optional[float] = None, std: Optional[float] = None
) -> Tuple[np.ndarray, Dict[str, float]]:
    """Standardize data to zero mean and unit variance.

    Args:
        data: Input data
        mean: Mean to use (if None, calculate from data)
        std: Standard deviation to use (if None, calculate from data)

    Returns:
        Tuple of (standardized_data, params)
    """
    if mean is None:
        mean = float(np.mean(data))
    if std is None:
        std = float(np.std(data))

    standardized = (data - mean) / (std + 1e-10)

    return standardized, {"mean": mean, "std": std}


def detect_outliers(
    data: np.ndarray, method: str = "iqr", threshold: float = 1.5
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Detect outliers in data.

    Args:
        data: Input data
        method: Detection method (iqr, z_score, isolation_forest)
        threshold: Threshold for outlier detection

    Returns:
        Tuple of (outlier_mask, detection_info)
    """
    data_flat = data.flatten()
    outlier_mask = np.zeros(len(data_flat), dtype=bool)

    if method == "iqr":
        # Interquartile range method
        q25 = np.percentile(data_flat, 25)
        q75 = np.percentile(data_flat, 75)
        iqr = q75 - q25

        lower_bound = q25 - threshold * iqr
        upper_bound = q75 + threshold * iqr

        outlier_mask = (data_flat < lower_bound) | (data_flat > upper_bound)

        info = {
            "method": method,
            "threshold": threshold,
            "lower_bound": float(lower_bound),
            "upper_bound": float(upper_bound),
            "q25": float(q25),
            "q75": float(q75),
            "iqr": float(iqr),
        }

    elif method == "z_score":
        # Z-score method
        mean = np.mean(data_flat)
        std = np.std(data_flat)

        z_scores = np.abs((data_flat - mean) / (std + 1e-10))
        outlier_mask = z_scores > threshold

        info = {
            "method": method,
            "threshold": threshold,
            "mean": float(mean),
            "std": float(std),
        }

    else:
        raise ValueError(f"Unknown outlier detection method: {method}")

    # Reshape mask to match original data shape
    outlier_mask = outlier_mask.reshape(data.shape)

    return outlier_mask, info


def remove_outliers(
    data: np.ndarray, method: str = "iqr", threshold: float = 1.5
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Remove outliers from data.

    Args:
        data: Input data
        method: Detection method
        threshold: Threshold for outlier detection

    Returns:
        Tuple of (cleaned_data, removal_info)
    """
    outlier_mask, detection_info = detect_outliers(data, method, threshold)

    # Remove outliers (flatten, filter, reshape if possible)
    cleaned = data[~outlier_mask]

    info = {
        **detection_info,
        "outliers_removed": int(np.sum(outlier_mask)),
        "outlier_percentage": float(100 * np.sum(outlier_mask) / outlier_mask.size),
    }

    return cleaned, info


def extract_features(
    data: np.ndarray, feature_types: List[str]
) -> Dict[str, np.ndarray]:
    """Extract features from data.

    Args:
        data: Input data
        feature_types: List of feature types to extract

    Returns:
        Dictionary mapping feature names to feature arrays
    """
    features = {}

    for feature_type in feature_types:
        if feature_type == "mean":
            features["mean"] = (
                np.mean(data, axis=-1) if data.ndim > 1 else np.array([np.mean(data)])
            )
        elif feature_type == "std":
            features["std"] = (
                np.std(data, axis=-1) if data.ndim > 1 else np.array([np.std(data)])
            )
        elif feature_type == "min":
            features["min"] = (
                np.min(data, axis=-1) if data.ndim > 1 else np.array([np.min(data)])
            )
        elif feature_type == "max":
            features["max"] = (
                np.max(data, axis=-1) if data.ndim > 1 else np.array([np.max(data)])
            )
        elif feature_type == "range":
            features["range"] = (
                np.max(data, axis=-1) - np.min(data, axis=-1)
                if data.ndim > 1
                else np.array([np.max(data) - np.min(data)])
            )
        else:
            raise ValueError(f"Unknown feature type: {feature_type}")

    return features


def transform_data(data: np.ndarray, transform: Union[str, Callable]) -> np.ndarray:
    """Apply transformation to data.

    Args:
        data: Input data
        transform: Transformation name or function

    Returns:
        Transformed data
    """
    if isinstance(transform, str):
        if transform == "log":
            return np.log(data + 1e-10)
        elif transform == "sqrt":
            return np.sqrt(np.maximum(data, 0.0))
        elif transform == "square":
            return data**2
        elif transform == "exp":
            return np.exp(np.clip(data, None, 700))
        else:
            raise ValueError(f"Unknown transform: {transform}")
    else:
        # Callable transform
        return transform(data)


def create_validation_pipeline(steps: List[Tuple[str, Dict[str, Any]]]) -> Callable:
    """Create a data validation pipeline.

    Args:
        steps: List of (function_name, kwargs) tuples

    Returns:
        Pipeline function
    """

    def pipeline(data: np.ndarray) -> Tuple[bool, List[str]]:
        """Run validation pipeline.

        Args:
            data: Input data

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        for step_name, step_kwargs in steps:
            try:
                if step_name == "check_finite":
                    if not np.all(np.isfinite(data)):
                        errors.append("Data contains non-finite values")

                elif step_name == "check_shape":
                    expected_shape = step_kwargs.get("shape")
                    if expected_shape and data.shape != expected_shape:
                        errors.append(
                            f"Expected shape {expected_shape}, got {data.shape}"
                        )

                elif step_name == "check_range":
                    min_val = step_kwargs.get("min")
                    max_val = step_kwargs.get("max")
                    if min_val is not None and np.any(data < min_val):
                        errors.append(f"Data below minimum {min_val}")
                    if max_val is not None and np.any(data > max_val):
                        errors.append(f"Data above maximum {max_val}")

                elif step_name == "check_outliers":
                    method = step_kwargs.get("method", "iqr")
                    threshold = step_kwargs.get("threshold", 1.5)
                    outlier_mask, _ = detect_outliers(data, method, threshold)
                    outlier_pct = 100 * np.sum(outlier_mask) / outlier_mask.size
                    max_outliers = step_kwargs.get("max_outlier_percentage", 5.0)
                    if outlier_pct > max_outliers:
                        errors.append(f"Too many outliers: {outlier_pct:.2f}%")

            except Exception as e:
                errors.append(f"Validation step '{step_name}' failed: {e}")

        return len(errors) == 0, errors

    return pipeline
