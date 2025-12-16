"""Statistical analysis for tree grafting experiments.

This module provides descriptive statistics, hypothesis testing,
correlation analysis, and survival curve analysis for grafting data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np


@dataclass
class GraftDescriptiveStats:
    """Descriptive statistics for grafting data."""
    mean: float
    std: float
    median: float
    min: float
    max: float
    q25: float
    q75: float
    count: int
    success_rate: Optional[float] = None
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        result = {
            "mean": self.mean,
            "std": self.std,
            "median": self.median,
            "min": self.min,
            "max": self.max,
            "q25": self.q25,
            "q75": self.q75,
            "count": self.count
        }
        if self.success_rate is not None:
            result["success_rate"] = self.success_rate
        return result


def calculate_graft_statistics(
    success: np.ndarray,
    union_strength: Optional[np.ndarray] = None,
    healing_time: Optional[np.ndarray] = None
) -> Dict[str, GraftDescriptiveStats]:
    """Calculate descriptive statistics for grafting outcomes.
    
    Args:
        success: Success outcomes (0/1 array)
        union_strength: Union strength values (optional)
        healing_time: Healing time in days (optional)
        
    Returns:
        Dictionary of statistics for each metric
    """
    stats = {}
    
    # Success rate
    success_rate = float(np.mean(success))
    stats["success"] = GraftDescriptiveStats(
        mean=success_rate,
        std=0.0,
        median=1.0 if success_rate > 0.5 else 0.0,
        min=0.0,
        max=1.0,
        q25=0.0,
        q75=1.0,
        count=int(len(success)),
        success_rate=success_rate
    )
    
    # Union strength (only for successful grafts)
    if union_strength is not None:
        valid_strength = union_strength[~np.isnan(union_strength)]
        if len(valid_strength) > 0:
            stats["union_strength"] = GraftDescriptiveStats(
                mean=float(np.mean(valid_strength)),
                std=float(np.std(valid_strength)),
                median=float(np.median(valid_strength)),
                min=float(np.min(valid_strength)),
                max=float(np.max(valid_strength)),
                q25=float(np.percentile(valid_strength, 25)),
                q75=float(np.percentile(valid_strength, 75)),
                count=int(len(valid_strength))
            )
    
    # Healing time
    if healing_time is not None:
        valid_time = healing_time[~np.isnan(healing_time)]
        if len(valid_time) > 0:
            stats["healing_time"] = GraftDescriptiveStats(
                mean=float(np.mean(valid_time)),
                std=float(np.std(valid_time)),
                median=float(np.median(valid_time)),
                min=float(np.min(valid_time)),
                max=float(np.max(valid_time)),
                q25=float(np.percentile(valid_time, 25)),
                q75=float(np.percentile(valid_time, 75)),
                count=int(len(valid_time))
            )
    
    return stats


def compare_technique_success(
    success_group1: np.ndarray,
    success_group2: np.ndarray
) -> Dict[str, float]:
    """Compare success rates between two techniques using statistical test.
    
    Args:
        success_group1: Success outcomes for group 1
        success_group2: Success outcomes for group 2
        
    Returns:
        Dictionary with test results
    """
    n1, n2 = len(success_group1), len(success_group2)
    p1 = np.mean(success_group1)
    p2 = np.mean(success_group2)
    
    # Two-proportion z-test
    p_pooled = (np.sum(success_group1) + np.sum(success_group2)) / (n1 + n2)
    se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
    
    z_stat = (p1 - p2) / (se + 1e-10)
    
    # Approximate p-value (two-sided)
    p_value = 2 * (1 - 0.5 * (1 + np.sign(z_stat) * (1 - np.exp(-0.717 * abs(z_stat) - 0.416 * z_stat**2))))
    p_value = max(0.0, min(1.0, p_value))
    
    return {
        "z_statistic": float(z_stat),
        "p_value": float(p_value),
        "success_rate_1": float(p1),
        "success_rate_2": float(p2),
        "difference": float(p1 - p2)
    }


def calculate_success_correlation(
    success: np.ndarray,
    factor: np.ndarray
) -> Dict[str, float]:
    """Calculate correlation between success and a factor.
    
    Args:
        success: Success outcomes
        factor: Factor values (e.g., compatibility, temperature)
        
    Returns:
        Dictionary with correlation statistics
    """
    # Point-biserial correlation (success is binary)
    mean_success = np.mean(success)
    mean_factor_success = np.mean(factor[success == 1])
    mean_factor_fail = np.mean(factor[success == 0])
    
    std_factor = np.std(factor)
    
    if std_factor > 1e-10:
        correlation = (mean_factor_success - mean_factor_fail) / std_factor * \
                     np.sqrt(mean_success * (1 - mean_success))
    else:
        correlation = 0.0
    
    # Approximate significance
    n = len(success)
    t_stat = correlation * np.sqrt((n - 2) / (1 - correlation**2 + 1e-10))
    p_value = 0.05  # Placeholder - would use proper t-distribution
    
    return {
        "correlation": float(correlation),
        "p_value": float(p_value),
        "mean_factor_success": float(mean_factor_success),
        "mean_factor_fail": float(mean_factor_fail)
    }


def analyze_survival_curve(
    healing_times: np.ndarray,
    success: np.ndarray
) -> Dict[str, np.ndarray]:
    """Analyze graft survival/healing curve.
    
    Args:
        healing_times: Time to healing (or failure)
        success: Success outcomes
        
    Returns:
        Dictionary with survival curve data
    """
    # Sort by time
    sorted_indices = np.argsort(healing_times)
    sorted_times = healing_times[sorted_indices]
    sorted_success = success[sorted_indices]
    
    # Calculate cumulative survival
    n_total = len(healing_times)
    survival = np.ones(n_total)
    
    for i in range(1, n_total):
        if sorted_success[i-1] == 0:  # Failure
            survival[i] = survival[i-1] * (n_total - i) / (n_total - i + 1)
        else:
            survival[i] = survival[i-1]
    
    return {
        "time": sorted_times,
        "survival": survival,
        "success": sorted_success
    }


def calculate_confidence_interval_success_rate(
    success: np.ndarray,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """Calculate confidence interval for success rate.
    
    Args:
        success: Success outcomes
        confidence: Confidence level (0.95 for 95%)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    n = len(success)
    p = np.mean(success)
    
    # Normal approximation for binomial
    z_value = 1.96 if confidence == 0.95 else 2.576 if confidence == 0.99 else 1.645
    
    se = np.sqrt(p * (1 - p) / n)
    margin = z_value * se
    
    lower = max(0.0, p - margin)
    upper = min(1.0, p + margin)
    
    return (float(lower), float(upper))


def anova_technique_comparison(
    groups: List[np.ndarray]
) -> Dict[str, float]:
    """Perform ANOVA comparing multiple grafting techniques.
    
    Args:
        groups: List of success rate arrays, one per technique
        
    Returns:
        Dictionary with F-statistic and p-value
    """
    # Convert to success rates
    group_means = [np.mean(g) for g in groups]
    group_sizes = [len(g) for g in groups]
    overall_mean = np.mean(np.concatenate(groups))
    
    # Between-group sum of squares
    ss_between = sum(n * (mean - overall_mean)**2 
                     for n, mean in zip(group_sizes, group_means))
    df_between = len(groups) - 1
    
    # Within-group sum of squares
    ss_within = sum(np.sum((g - mean)**2) 
                    for g, mean in zip(groups, group_means))
    df_within = sum(group_sizes) - len(groups)
    
    # F-statistic
    ms_between = ss_between / df_between if df_between > 0 else 0
    ms_within = ss_within / df_within if df_within > 0 else 0
    f_stat = ms_between / ms_within if ms_within > 0 else 0
    
    # Placeholder p-value
    p_value = 0.05
    
    return {
        "f_statistic": float(f_stat),
        "p_value": float(p_value),
        "df_between": float(df_between),
        "df_within": float(df_within),
        "group_means": [float(m) for m in group_means]
    }

