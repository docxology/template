"""Metrics calculation for scientific computing.

This module provides performance metrics, convergence metrics,
quality metrics, statistical metrics, and a custom metric framework.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np


def calculate_accuracy(
    predictions: np.ndarray,
    targets: np.ndarray
) -> float:
    """Calculate accuracy for classification.
    
    Args:
        predictions: Predicted labels
        targets: True labels
        
    Returns:
        Accuracy (0-1)
    """
    if len(predictions) != len(targets):
        raise ValueError("predictions and targets must have same length")
    
    correct = np.sum(predictions == targets)
    return float(correct / len(predictions))


def calculate_precision_recall_f1(
    predictions: np.ndarray,
    targets: np.ndarray,
    positive_class: int = 1
) -> Dict[str, float]:
    """Calculate precision, recall, and F1 score.
    
    Args:
        predictions: Predicted labels
        targets: True labels
        positive_class: Label for positive class
        
    Returns:
        Dictionary with precision, recall, and f1
    """
    if len(predictions) != len(targets):
        raise ValueError("predictions and targets must have same length")
    
    true_positives = np.sum((predictions == positive_class) & (targets == positive_class))
    false_positives = np.sum((predictions == positive_class) & (targets != positive_class))
    false_negatives = np.sum((predictions != positive_class) & (targets == positive_class))
    
    precision = true_positives / (true_positives + false_positives + 1e-10)
    recall = true_positives / (true_positives + false_negatives + 1e-10)
    f1 = 2 * (precision * recall) / (precision + recall + 1e-10)
    
    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1)
    }


def calculate_convergence_metrics(
    values: np.ndarray,
    target: Optional[float] = None
) -> Dict[str, float]:
    """Calculate convergence metrics.
    
    Args:
        values: Sequence of values
        target: Target value (if known)
        
    Returns:
        Dictionary with convergence metrics
    """
    from performance import analyze_convergence
    
    convergence = analyze_convergence(values, target)
    
    # Calculate residuals
    if target is not None:
        residuals = np.abs(values - target)
    else:
        # Use relative change
        residuals = np.abs(np.diff(values))
        residuals = np.concatenate([[residuals[0]], residuals])
    
    return {
        "final_error": convergence.error,
        "convergence_rate": convergence.convergence_rate or 0.0,
        "iterations_to_convergence": convergence.iterations_to_convergence or len(values),
        "is_converged": convergence.is_converged,
        "mean_residual": float(np.mean(residuals)),
        "max_residual": float(np.max(residuals)),
        "final_residual": float(residuals[-1])
    }


def calculate_snr(
    signal: np.ndarray,
    noise: Optional[np.ndarray] = None
) -> float:
    """Calculate Signal-to-Noise Ratio (SNR).
    
    Args:
        signal: Signal values
        noise: Noise values (if None, estimates from signal)
        
    Returns:
        SNR in dB
    """
    signal_power = np.mean(signal ** 2)
    
    if noise is not None:
        noise_power = np.mean(noise ** 2)
    else:
        # Estimate noise as high-frequency component
        if len(signal) > 1:
            noise_estimate = np.std(np.diff(signal))
            noise_power = noise_estimate ** 2
        else:
            noise_power = 1e-10
    
    snr_linear = signal_power / (noise_power + 1e-10)
    snr_db = 10 * np.log10(snr_linear + 1e-10)
    
    return float(snr_db)


def calculate_psnr(
    original: np.ndarray,
    reconstructed: np.ndarray,
    max_value: Optional[float] = None
) -> float:
    """Calculate Peak Signal-to-Noise Ratio (PSNR).
    
    Args:
        original: Original signal
        reconstructed: Reconstructed signal
        max_value: Maximum possible value (if None, uses max of original)
        
    Returns:
        PSNR in dB
    """
    if max_value is None:
        max_value = np.max(original)
    
    mse = np.mean((original - reconstructed) ** 2)
    psnr = 10 * np.log10((max_value ** 2) / (mse + 1e-10))
    
    return float(psnr)


def calculate_ssim(
    image1: np.ndarray,
    image2: np.ndarray,
    window_size: int = 11
) -> float:
    """Calculate Structural Similarity Index (SSIM).
    
    Simplified implementation - for full SSIM use scipy or skimage.
    
    Args:
        image1: First image
        image2: Second image
        window_size: Window size for local SSIM
        
    Returns:
        SSIM value (0-1)
    """
    # Simplified SSIM calculation
    mu1 = np.mean(image1)
    mu2 = np.mean(image2)
    
    sigma1_sq = np.var(image1)
    sigma2_sq = np.var(image2)
    sigma12 = np.mean((image1 - mu1) * (image2 - mu2))
    
    c1 = 0.01 ** 2
    c2 = 0.03 ** 2
    
    ssim = ((2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)) / (
        (mu1 ** 2 + mu2 ** 2 + c1) * (sigma1_sq + sigma2_sq + c2) + 1e-10
    )
    
    return float(ssim)


def calculate_effect_size(
    group1: np.ndarray,
    group2: np.ndarray
) -> Dict[str, float]:
    """Calculate effect size (Cohen's d).
    
    Args:
        group1: First group
        group2: Second group
        
    Returns:
        Dictionary with effect size and interpretation
    """
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    
    # Pooled standard deviation
    n1, n2 = len(group1), len(group2)
    pooled_std = np.sqrt(((n1 - 1) * std1 ** 2 + (n2 - 1) * std2 ** 2) / (n1 + n2 - 2))
    
    # Cohen's d
    cohens_d = (mean1 - mean2) / (pooled_std + 1e-10)
    
    # Interpretation
    abs_d = abs(cohens_d)
    if abs_d < 0.2:
        interpretation = "negligible"
    elif abs_d < 0.5:
        interpretation = "small"
    elif abs_d < 0.8:
        interpretation = "medium"
    else:
        interpretation = "large"
    
    return {
        "cohens_d": float(cohens_d),
        "interpretation": interpretation,
        "mean1": float(mean1),
        "mean2": float(mean2),
        "pooled_std": float(pooled_std)
    }


def calculate_p_value_approximation(
    statistic: float,
    distribution: str = "normal"
) -> float:
    """Approximate p-value from test statistic.
    
    Simplified approximation - for accurate p-values use scipy.stats.
    
    Args:
        statistic: Test statistic value
        distribution: Distribution type (normal, t, chi2)
        
    Returns:
        Approximate p-value
    """
    # Simplified p-value calculation
    # In practice, use proper statistical distributions
    abs_stat = abs(statistic)
    
    if distribution == "normal":
        # Normal distribution approximation
        if abs_stat > 3:
            p_value = 0.001
        elif abs_stat > 2:
            p_value = 0.05
        else:
            p_value = 0.1
    else:
        # Default approximation
        p_value = 0.05
    
    return float(p_value)


class CustomMetric:
    """Framework for custom metrics."""
    
    def __init__(self, name: str, metric_function: Callable):
        """Initialize custom metric.
        
        Args:
            name: Metric name
            metric_function: Function that calculates the metric
        """
        self.name = name
        self.metric_function = metric_function
    
    def calculate(self, *args, **kwargs) -> float:
        """Calculate the metric.
        
        Args:
            *args: Positional arguments for metric function
            **kwargs: Keyword arguments for metric function
            
        Returns:
            Metric value
        """
        return float(self.metric_function(*args, **kwargs))


def calculate_all_metrics(
    predictions: Optional[np.ndarray] = None,
    targets: Optional[np.ndarray] = None,
    values: Optional[np.ndarray] = None,
    signal: Optional[np.ndarray] = None,
    noise: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """Calculate all applicable metrics.
    
    Args:
        predictions: Predicted values (for classification metrics)
        targets: True values (for classification metrics)
        values: Sequence values (for convergence metrics)
        signal: Signal values (for SNR)
        noise: Noise values (for SNR)
        
    Returns:
        Dictionary of all calculated metrics
    """
    metrics = {}
    
    # Classification metrics
    if predictions is not None and targets is not None:
        metrics["accuracy"] = calculate_accuracy(predictions, targets)
        prf = calculate_precision_recall_f1(predictions, targets)
        metrics.update(prf)
    
    # Convergence metrics
    if values is not None:
        conv_metrics = calculate_convergence_metrics(values)
        metrics.update({f"convergence_{k}": v for k, v in conv_metrics.items()})
    
    # Signal quality metrics
    if signal is not None:
        metrics["snr"] = calculate_snr(signal, noise)
    
    return metrics

