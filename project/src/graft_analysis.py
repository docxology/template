"""Analysis functions for tree grafting outcomes.

This module provides analysis of grafting outcomes, temporal patterns,
comparative technique analysis, and factor analysis.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class GraftOutcomeMetrics:
    """Metrics for grafting outcome analysis."""
    success_rate: float
    mean_union_strength: float
    mean_healing_time: float
    n_trials: int
    n_successful: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success_rate": self.success_rate,
            "mean_union_strength": self.mean_union_strength,
            "mean_healing_time": self.mean_healing_time,
            "n_trials": self.n_trials,
            "n_successful": self.n_successful
        }


def analyze_graft_outcomes(
    success: np.ndarray,
    union_strength: Optional[np.ndarray] = None,
    healing_time: Optional[np.ndarray] = None
) -> GraftOutcomeMetrics:
    """Analyze overall grafting outcomes.
    
    Args:
        success: Success outcomes
        union_strength: Union strength values (optional)
        healing_time: Healing times (optional)
        
    Returns:
        GraftOutcomeMetrics object
    """
    success_rate = float(np.mean(success))
    n_trials = len(success)
    n_successful = int(np.sum(success))
    
    mean_union_strength = 0.0
    if union_strength is not None:
        valid_strength = union_strength[success == 1]
        if len(valid_strength) > 0:
            mean_union_strength = float(np.mean(valid_strength))
    
    mean_healing_time = 0.0
    if healing_time is not None:
        valid_time = healing_time[success == 1]
        if len(valid_time) > 0:
            mean_healing_time = float(np.mean(valid_time))
    
    return GraftOutcomeMetrics(
        success_rate=success_rate,
        mean_union_strength=mean_union_strength,
        mean_healing_time=mean_healing_time,
        n_trials=n_trials,
        n_successful=n_successful
    )


def analyze_temporal_patterns(
    success: np.ndarray,
    dates: Optional[np.ndarray] = None,
    months: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """Analyze temporal patterns in grafting success.
    
    Args:
        success: Success outcomes
        dates: Date array (optional)
        months: Month numbers (1-12, optional)
        
    Returns:
        Dictionary with temporal analysis results
    """
    results = {}
    
    if months is not None:
        # Analyze by month
        monthly_success = {}
        for month in range(1, 13):
            month_mask = months == month
            if np.any(month_mask):
                monthly_success[month] = float(np.mean(success[month_mask]))
        
        results["monthly_success_rates"] = monthly_success
        
        # Find best month
        if monthly_success:
            best_month = max(monthly_success, key=monthly_success.get)
            results["best_month"] = int(best_month)
            results["best_month_success_rate"] = monthly_success[best_month]
    
    return results


def compare_techniques(
    technique_groups: Dict[str, np.ndarray]
) -> Dict[str, Any]:
    """Compare grafting techniques.
    
    Args:
        technique_groups: Dictionary mapping technique names to success arrays
        
    Returns:
        Dictionary with comparison results
    """
    comparison = {}
    
    # Calculate success rates for each technique
    technique_success_rates = {
        name: float(np.mean(success)) 
        for name, success in technique_groups.items()
    }
    
    comparison["technique_success_rates"] = technique_success_rates
    
    # Find best technique
    if technique_success_rates:
        best_technique = max(technique_success_rates, key=technique_success_rates.get)
        comparison["best_technique"] = best_technique
        comparison["best_technique_success_rate"] = technique_success_rates[best_technique]
    
    # Statistical comparison
    if len(technique_groups) >= 2:
        groups_list = list(technique_groups.values())
        from graft_statistics import anova_technique_comparison
        anova_results = anova_technique_comparison(groups_list)
        comparison["anova"] = anova_results
    
    return comparison


def analyze_factor_importance(
    success: np.ndarray,
    factors: Dict[str, np.ndarray]
) -> Dict[str, float]:
    """Analyze importance of different factors on success.
    
    Args:
        success: Success outcomes
        factors: Dictionary mapping factor names to factor values
        
    Returns:
        Dictionary with factor importance scores
    """
    importance = {}
    
    for factor_name, factor_values in factors.items():
        # Calculate correlation with success
        from graft_statistics import calculate_success_correlation
        correlation = calculate_success_correlation(success, factor_values)
        importance[factor_name] = abs(correlation["correlation"])
    
    # Normalize to sum to 1.0
    total_importance = sum(importance.values())
    if total_importance > 0:
        importance = {k: v / total_importance for k, v in importance.items()}
    
    return importance


def analyze_species_compatibility_patterns(
    compatibility_matrix: np.ndarray,
    species_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Analyze patterns in species compatibility matrix.
    
    Args:
        compatibility_matrix: Compatibility matrix
        species_names: Optional species names
        
    Returns:
        Dictionary with compatibility analysis
    """
    n_species = compatibility_matrix.shape[0]
    
    # Average compatibility for each species
    avg_compatibility = np.mean(compatibility_matrix, axis=1)
    
    # Most compatible species pairs
    # Exclude self-compatibility (diagonal)
    matrix_copy = compatibility_matrix.copy()
    np.fill_diagonal(matrix_copy, 0.0)
    
    # Find top pairs
    flat_indices = np.argsort(matrix_copy.flatten())[::-1]
    top_pairs = []
    for idx in flat_indices[:10]:  # Top 10
        i, j = np.unravel_index(idx, matrix_copy.shape)
        if i != j:  # Skip diagonal
            top_pairs.append({
                "species_1": int(i) if species_names is None else species_names[i],
                "species_2": int(j) if species_names is None else species_names[j],
                "compatibility": float(matrix_copy[i, j])
            })
    
    return {
        "n_species": int(n_species),
        "average_compatibility": float(np.mean(compatibility_matrix)),
        "avg_compatibility_per_species": [float(x) for x in avg_compatibility],
        "most_compatible_pairs": top_pairs
    }


def analyze_environmental_effects(
    success: np.ndarray,
    temperature: np.ndarray,
    humidity: np.ndarray
) -> Dict[str, Any]:
    """Analyze effects of environmental conditions on success.
    
    Args:
        success: Success outcomes
        temperature: Temperature values
        humidity: Humidity values
        
    Returns:
        Dictionary with environmental analysis
    """
    # Optimal ranges
    optimal_temp_range = (20.0, 25.0)
    optimal_humidity_range = (0.7, 0.9)
    
    # Classify conditions
    temp_optimal = (temperature >= optimal_temp_range[0]) & (temperature <= optimal_temp_range[1])
    humidity_optimal = (humidity >= optimal_humidity_range[0]) & (humidity <= optimal_humidity_range[1])
    both_optimal = temp_optimal & humidity_optimal
    
    # Calculate success rates
    success_optimal = float(np.mean(success[both_optimal])) if np.any(both_optimal) else 0.0
    success_suboptimal = float(np.mean(success[~both_optimal])) if np.any(~both_optimal) else 0.0
    
    # Correlation analysis
    from graft_statistics import calculate_success_correlation
    temp_corr = calculate_success_correlation(success, temperature)
    humidity_corr = calculate_success_correlation(success, humidity)
    
    return {
        "success_rate_optimal_conditions": success_optimal,
        "success_rate_suboptimal_conditions": success_suboptimal,
        "temperature_correlation": temp_corr["correlation"],
        "humidity_correlation": humidity_corr["correlation"],
        "optimal_temperature_range": optimal_temp_range,
        "optimal_humidity_range": optimal_humidity_range
    }

