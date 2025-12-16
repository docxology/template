"""Metrics calculation for tree grafting analysis.

This module provides success metrics, compatibility scoring, union strength
metrics, and economic metrics for grafting operations.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

import numpy as np


def calculate_success_rate(
    success: np.ndarray
) -> float:
    """Calculate graft success rate.
    
    Args:
        success: Success outcomes (0/1 array)
        
    Returns:
        Success rate (0-1)
    """
    return float(np.mean(success))


def calculate_take_rate(
    success: np.ndarray,
    days_after_grafting: int = 30
) -> float:
    """Calculate graft take rate (successful grafts after specified days).
    
    Args:
        success: Success outcomes
        days_after_grafting: Days after grafting to assess
        
    Returns:
        Take rate (0-1)
    """
    # For now, use overall success rate
    # In practice, would filter by time
    return float(np.mean(success))


def calculate_union_strength_metrics(
    union_strength: np.ndarray,
    success: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """Calculate union strength metrics.
    
    Args:
        union_strength: Union strength values (0-1)
        success: Success outcomes (optional, for filtering)
        
    Returns:
        Dictionary with union strength metrics
    """
    if success is not None:
        # Only consider successful grafts
        valid_strength = union_strength[success == 1]
    else:
        valid_strength = union_strength[~np.isnan(union_strength)]
    
    if len(valid_strength) == 0:
        return {
            "mean": 0.0,
            "median": 0.0,
            "min": 0.0,
            "max": 0.0,
            "std": 0.0
        }
    
    return {
        "mean": float(np.mean(valid_strength)),
        "median": float(np.median(valid_strength)),
        "min": float(np.min(valid_strength)),
        "max": float(np.max(valid_strength)),
        "std": float(np.std(valid_strength))
    }


def calculate_compatibility_score(
    rootstock_species: np.ndarray,
    scion_species: np.ndarray,
    compatibility_matrix: np.ndarray
) -> np.ndarray:
    """Calculate compatibility scores from compatibility matrix.
    
    Args:
        rootstock_species: Rootstock species indices
        scion_species: Scion species indices
        compatibility_matrix: Species compatibility matrix
        
    Returns:
        Compatibility scores for each pair
    """
    scores = np.zeros(len(rootstock_species))
    
    for i, (root, scion) in enumerate(zip(rootstock_species, scion_species)):
        if (0 <= root < compatibility_matrix.shape[0] and 
            0 <= scion < compatibility_matrix.shape[1]):
            scores[i] = compatibility_matrix[int(root), int(scion)]
    
    return scores


def calculate_growth_rate(
    initial_size: np.ndarray,
    final_size: np.ndarray,
    time_period: float
) -> np.ndarray:
    """Calculate growth rate for grafted plants.
    
    Args:
        initial_size: Initial size measurements
        final_size: Final size measurements
        time_period: Time period in days
        
    Returns:
        Growth rates (size per day)
    """
    growth = final_size - initial_size
    growth_rate = growth / (time_period + 1e-10)
    
    return growth_rate


def calculate_economic_metrics(
    success_rate: float,
    cost_per_graft: float,
    value_per_successful_graft: float,
    n_grafts: int
) -> Dict[str, float]:
    """Calculate economic metrics for grafting operations.
    
    Args:
        success_rate: Graft success rate (0-1)
        cost_per_graft: Cost per graft attempt
        value_per_successful_graft: Value of successful graft
        n_grafts: Number of grafts
        
    Returns:
        Dictionary with economic metrics
    """
    total_cost = n_grafts * cost_per_graft
    n_successful = int(n_grafts * success_rate)
    total_revenue = n_successful * value_per_successful_graft
    net_profit = total_revenue - total_cost
    roi = (net_profit / total_cost) * 100 if total_cost > 0 else 0.0
    break_even_success_rate = cost_per_graft / value_per_successful_graft if value_per_successful_graft > 0 else 0.0
    
    return {
        "total_cost": float(total_cost),
        "total_revenue": float(total_revenue),
        "net_profit": float(net_profit),
        "roi_percent": float(roi),
        "break_even_success_rate": float(break_even_success_rate),
        "n_successful": int(n_successful),
        "n_failed": int(n_grafts - n_successful)
    }


def calculate_quality_index(
    compatibility: np.ndarray,
    technique_quality: np.ndarray,
    environmental_score: np.ndarray
) -> np.ndarray:
    """Calculate overall quality index for grafting operations.
    
    Args:
        compatibility: Compatibility scores
        technique_quality: Technique execution quality
        environmental_score: Environmental conditions score
        
    Returns:
        Quality index values (0-1)
    """
    weights = np.array([0.4, 0.3, 0.3])
    factors = np.column_stack([compatibility, technique_quality, environmental_score])
    
    quality_index = np.dot(factors, weights)
    
    return np.clip(quality_index, 0.0, 1.0)


def calculate_healing_efficiency(
    healing_times: np.ndarray,
    target_time: float = 21.0
) -> Dict[str, float]:
    """Calculate healing efficiency metrics.
    
    Args:
        healing_times: Time to healing (days)
        target_time: Target healing time (days)
        
    Returns:
        Dictionary with efficiency metrics
    """
    valid_times = healing_times[~np.isnan(healing_times)]
    
    if len(valid_times) == 0:
        return {
            "mean_healing_time": 0.0,
            "efficiency_score": 0.0,
            "on_time_percentage": 0.0
        }
    
    mean_time = float(np.mean(valid_times))
    efficiency_score = target_time / (mean_time + 1e-10)
    efficiency_score = min(1.0, efficiency_score)  # Cap at 1.0
    
    on_time = np.sum(valid_times <= target_time)
    on_time_percentage = float(on_time / len(valid_times) * 100)
    
    return {
        "mean_healing_time": mean_time,
        "efficiency_score": float(efficiency_score),
        "on_time_percentage": on_time_percentage
    }


class GraftCustomMetric:
    """Framework for custom grafting metrics."""
    
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


def calculate_all_graft_metrics(
    success: np.ndarray,
    union_strength: Optional[np.ndarray] = None,
    healing_time: Optional[np.ndarray] = None,
    compatibility: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """Calculate all applicable grafting metrics.
    
    Args:
        success: Success outcomes
        union_strength: Union strength values (optional)
        healing_time: Healing times (optional)
        compatibility: Compatibility scores (optional)
        
    Returns:
        Dictionary of all calculated metrics
    """
    metrics = {}
    
    # Success metrics
    metrics["success_rate"] = calculate_success_rate(success)
    metrics["take_rate"] = calculate_take_rate(success)
    
    # Union strength metrics
    if union_strength is not None:
        strength_metrics = calculate_union_strength_metrics(union_strength, success)
        metrics.update({f"union_{k}": v for k, v in strength_metrics.items()})
    
    # Healing efficiency
    if healing_time is not None:
        efficiency = calculate_healing_efficiency(healing_time)
        metrics.update(efficiency)
    
    # Compatibility
    if compatibility is not None:
        metrics["mean_compatibility"] = float(np.mean(compatibility))
        metrics["min_compatibility"] = float(np.min(compatibility))
        metrics["max_compatibility"] = float(np.max(compatibility))
    
    return metrics

