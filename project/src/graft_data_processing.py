"""Data processing for tree grafting experiments.

This module provides data cleaning, preprocessing, feature extraction,
and validation for grafting trial data.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np


def clean_graft_data(
    data: Dict[str, np.ndarray],
    remove_failed: bool = False,
    fill_missing: Optional[str] = None
) -> Dict[str, np.ndarray]:
    """Clean grafting trial data.
    
    Args:
        data: Input data dictionary
        remove_failed: Remove failed grafts from dataset
        fill_missing: Method to fill missing values (mean, median, zero, None)
        
    Returns:
        Cleaned data dictionary
    """
    cleaned = {}
    
    # Get array length
    n_samples = len(next(iter(data.values())))
    
    # Create mask for valid samples
    valid_mask = np.ones(n_samples, dtype=bool)
    
    # Remove failed grafts if requested
    if remove_failed and "success" in data:
        valid_mask &= (data["success"] == 1)
    
    # Process each array
    for key, values in data.items():
        if isinstance(values, np.ndarray):
            cleaned_values = values[valid_mask].copy()
            
            # Handle missing values
            if fill_missing is not None:
                nan_mask = np.isnan(cleaned_values)
                if np.any(nan_mask):
                    if fill_missing == "mean":
                        fill_value = np.nanmean(cleaned_values)
                    elif fill_missing == "median":
                        fill_value = np.nanmedian(cleaned_values)
                    elif fill_missing == "zero":
                        fill_value = 0.0
                    else:
                        raise ValueError(f"Unknown fill method: {fill_missing}")
                    
                    cleaned_values[nan_mask] = fill_value
            
            cleaned[key] = cleaned_values
        else:
            cleaned[key] = values
    
    return cleaned


def normalize_graft_parameters(
    data: Dict[str, np.ndarray],
    method: str = "z_score"
) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
    """Normalize grafting parameter data.
    
    Args:
        data: Input data dictionary
        method: Normalization method (z_score, min_max)
        
    Returns:
        Tuple of (normalized_data, normalization_params)
    """
    normalized = {}
    params = {}
    
    # Parameters to normalize
    normalize_keys = ["temperature", "humidity", "compatibility", "technique_quality"]
    
    for key in normalize_keys:
        if key in data:
            values = data[key]
            valid_values = values[~np.isnan(values)]
            
            if method == "z_score":
                mean = np.mean(valid_values)
                std = np.std(valid_values)
                normalized[key] = (values - mean) / (std + 1e-10)
                params[key] = {"mean": float(mean), "std": float(std)}
            
            elif method == "min_max":
                min_val = np.min(valid_values)
                max_val = np.max(valid_values)
                normalized[key] = (values - min_val) / (max_val - min_val + 1e-10)
                params[key] = {"min": float(min_val), "max": float(max_val)}
            
            else:
                raise ValueError(f"Unknown normalization method: {method}")
        else:
            normalized[key] = data.get(key)
    
    # Copy non-normalized keys
    for key, values in data.items():
        if key not in normalize_keys:
            normalized[key] = values
    
    return normalized, params


def extract_graft_features(
    data: Dict[str, np.ndarray]
) -> Dict[str, np.ndarray]:
    """Extract features from grafting data.
    
    Args:
        data: Input data dictionary
        
    Returns:
        Dictionary of extracted features
    """
    features = {}
    
    # Diameter ratio
    if "rootstock_diameter" in data and "scion_diameter" in data:
        features["diameter_ratio"] = (
            data["scion_diameter"] / (data["rootstock_diameter"] + 1e-10)
        )
    
    # Environmental score
    if "temperature" in data and "humidity" in data:
        # Optimal temperature: 20-25°C, optimal humidity: 0.7-0.9
        temp_score = 1.0 - np.abs(data["temperature"] - 22.5) / 15.0
        temp_score = np.clip(temp_score, 0.0, 1.0)
        
        humidity_score = 1.0 - np.abs(data["humidity"] - 0.8) / 0.3
        humidity_score = np.clip(humidity_score, 0.0, 1.0)
        
        features["environmental_score"] = (temp_score + humidity_score) / 2.0
    
    # Overall quality score
    quality_factors = []
    if "compatibility" in data:
        quality_factors.append(data["compatibility"])
    if "technique_quality" in data:
        quality_factors.append(data["technique_quality"])
    if "environmental_score" in features:
        quality_factors.append(features["environmental_score"])
    
    if quality_factors:
        features["overall_quality"] = np.mean(quality_factors, axis=0)
    
    return features


def detect_outlier_trials(
    data: Dict[str, np.ndarray],
    method: str = "iqr",
    threshold: float = 1.5
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Detect outlier grafting trials.
    
    Args:
        data: Input data dictionary
        method: Detection method (iqr, z_score)
        threshold: Threshold for outlier detection
        
    Returns:
        Tuple of (outlier_mask, detection_info)
    """
    n_samples = len(next(iter(data.values())))
    outlier_scores = np.zeros(n_samples)
    
    # Check numeric columns
    numeric_keys = ["temperature", "humidity", "compatibility", "technique_quality"]
    
    for key in numeric_keys:
        if key in data:
            values = data[key]
            valid_values = values[~np.isnan(values)]
            
            if method == "iqr":
                q25 = np.percentile(valid_values, 25)
                q75 = np.percentile(valid_values, 75)
                iqr = q75 - q25
                
                lower_bound = q25 - threshold * iqr
                upper_bound = q75 + threshold * iqr
                
                outliers = (values < lower_bound) | (values > upper_bound)
                outlier_scores += outliers.astype(float)
            
            elif method == "z_score":
                mean = np.mean(valid_values)
                std = np.std(valid_values)
                
                z_scores = np.abs((values - mean) / (std + 1e-10))
                outliers = z_scores > threshold
                outlier_scores += outliers.astype(float)
    
    # Mark as outlier if flagged in multiple dimensions
    outlier_mask = outlier_scores >= 2.0
    
    info = {
        "method": method,
        "threshold": threshold,
        "outlier_count": int(np.sum(outlier_mask)),
        "outlier_percentage": float(100 * np.sum(outlier_mask) / n_samples)
    }
    
    return outlier_mask, info


def create_graft_validation_pipeline(
    steps: List[Tuple[str, Dict[str, Any]]]
) -> Callable:
    """Create a grafting data validation pipeline.
    
    Args:
        steps: List of (function_name, kwargs) tuples
        
    Returns:
        Pipeline function
    """
    def pipeline(data: Dict[str, np.ndarray]) -> Tuple[bool, List[str]]:
        """Run validation pipeline.
        
        Args:
            data: Input data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        for step_name, step_kwargs in steps:
            try:
                if step_name == "check_finite":
                    for key, values in data.items():
                        if isinstance(values, np.ndarray):
                            valid = values[~np.isnan(values)]
                            if len(valid) > 0 and not np.all(np.isfinite(valid)):
                                errors.append(f"Non-finite values in {key}")
                
                elif step_name == "check_ranges":
                    ranges = step_kwargs.get("ranges", {})
                    for key, (min_val, max_val) in ranges.items():
                        if key in data:
                            values = data[key]
                            valid = values[~np.isnan(values)]
                            if len(valid) > 0:
                                if np.any(valid < min_val) or np.any(valid > max_val):
                                    errors.append(f"{key} outside range [{min_val}, {max_val}]")
                
                elif step_name == "check_outliers":
                    method = step_kwargs.get("method", "iqr")
                    threshold = step_kwargs.get("threshold", 1.5)
                    outlier_mask, info = detect_outlier_trials(data, method, threshold)
                    max_outliers = step_kwargs.get("max_outlier_percentage", 10.0)
                    if info["outlier_percentage"] > max_outliers:
                        errors.append(f"Too many outliers: {info['outlier_percentage']:.2f}%")
                
            except Exception as e:
                errors.append(f"Validation step '{step_name}' failed: {e}")
        
        return len(errors) == 0, errors
    
    return pipeline

