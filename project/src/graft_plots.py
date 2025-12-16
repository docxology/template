"""Plotting functions for tree grafting visualization.

This module provides visualization functions for success rates, compatibility
matrices, temporal healing, species dendrograms, and technique comparisons.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

from graft_visualization import GraftVisualizationEngine


def plot_success_rates(
    techniques: List[str],
    success_rates: np.ndarray,
    ax: Optional[plt.Axes] = None,
    **kwargs
) -> plt.Axes:
    """Plot success rates by technique.
    
    Args:
        techniques: Technique names
        success_rates: Success rates (0-1)
        ax: Axes to plot on
        **kwargs: Additional arguments
        
    Returns:
        Axes object
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))
    
    bars = ax.bar(techniques, success_rates, **kwargs)
    ax.set_ylabel("Success Rate")
    ax.set_title("Graft Success Rates by Technique")
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar, rate in zip(bars, success_rates):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{rate:.2f}', ha='center', va='bottom')
    
    return ax


def plot_compatibility_matrix(
    compatibility_matrix: np.ndarray,
    species_names: Optional[List[str]] = None,
    ax: Optional[plt.Axes] = None,
    **kwargs
) -> plt.Axes:
    """Plot species compatibility matrix as heatmap.
    
    Args:
        compatibility_matrix: Compatibility matrix
        species_names: Optional species names
        ax: Axes to plot on
        **kwargs: Additional arguments
        
    Returns:
        Axes object
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 8))
    
    im = ax.imshow(compatibility_matrix, cmap='RdYlGn', vmin=0, vmax=1, **kwargs)
    
    # Set labels
    n_species = compatibility_matrix.shape[0]
    if species_names is None:
        species_names = [f"Species {i+1}" for i in range(n_species)]
    
    ax.set_xticks(range(n_species))
    ax.set_yticks(range(n_species))
    ax.set_xticklabels(species_names, rotation=45, ha='right')
    ax.set_yticklabels(species_names)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Compatibility Score")
    
    ax.set_title("Species Compatibility Matrix")
    ax.set_xlabel("Scion Species")
    ax.set_ylabel("Rootstock Species")
    
    return ax


def plot_healing_timeline(
    days: np.ndarray,
    union_strength: np.ndarray,
    ax: Optional[plt.Axes] = None,
    label: Optional[str] = None,
    **kwargs
) -> plt.Axes:
    """Plot graft union strength over time.
    
    Args:
        days: Days since grafting
        union_strength: Union strength values (0-1)
        ax: Axes to plot on
        label: Line label
        **kwargs: Additional arguments
        
    Returns:
        Axes object
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))
    
    ax.plot(days, union_strength, label=label, **kwargs)
    ax.set_xlabel("Days Since Grafting")
    ax.set_ylabel("Union Strength")
    ax.set_title("Graft Union Strength Over Time")
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    
    if label:
        ax.legend()
    
    return ax


def plot_success_by_factor(
    factor_values: np.ndarray,
    success: np.ndarray,
    factor_name: str = "Factor",
    ax: Optional[plt.Axes] = None,
    **kwargs
) -> plt.Axes:
    """Plot success rate as function of a factor.
    
    Args:
        factor_values: Factor values
        success: Success outcomes
        factor_name: Name of factor
        ax: Axes to plot on
        **kwargs: Additional arguments
        
    Returns:
        Axes object
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))
    
    # Bin factor values
    n_bins = 10
    bins = np.linspace(np.min(factor_values), np.max(factor_values), n_bins + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    
    success_rates = []
    for i in range(len(bins) - 1):
        mask = (factor_values >= bins[i]) & (factor_values < bins[i+1])
        if i == len(bins) - 2:  # Include last bin
            mask |= (factor_values == bins[i+1])
        if np.any(mask):
            success_rates.append(np.mean(success[mask]))
        else:
            success_rates.append(0.0)
    
    ax.plot(bin_centers, success_rates, marker='o', **kwargs)
    ax.set_xlabel(factor_name)
    ax.set_ylabel("Success Rate")
    ax.set_title(f"Success Rate vs {factor_name}")
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    
    return ax


def plot_technique_comparison(
    technique_data: Dict[str, Dict[str, np.ndarray]],
    metric: str = "success",
    ax: Optional[plt.Axes] = None,
    **kwargs
) -> plt.Axes:
    """Plot comparison of multiple techniques.
    
    Args:
        technique_data: Dictionary mapping technique names to data
        metric: Metric to compare (success, union_strength, healing_time)
        ax: Axes to plot on
        **kwargs: Additional arguments
        
    Returns:
        Axes object
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    
    techniques = list(technique_data.keys())
    means = []
    stds = []
    
    for tech in techniques:
        data = technique_data[tech].get(metric)
        if data is not None:
            valid_data = data[~np.isnan(data)]
            means.append(np.mean(valid_data))
            stds.append(np.std(valid_data))
        else:
            means.append(0.0)
            stds.append(0.0)
    
    x_pos = np.arange(len(techniques))
    bars = ax.bar(x_pos, means, yerr=stds, capsize=5, **kwargs)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(techniques, rotation=45, ha='right')
    ax.set_ylabel(metric.replace('_', ' ').title())
    ax.set_title(f"Technique Comparison: {metric.replace('_', ' ').title()}")
    ax.grid(True, alpha=0.3, axis='y')
    
    return ax


def plot_survival_curve(
    time: np.ndarray,
    survival: np.ndarray,
    ax: Optional[plt.Axes] = None,
    label: Optional[str] = None,
    **kwargs
) -> plt.Axes:
    """Plot graft survival curve.
    
    Args:
        time: Time points
        survival: Survival probabilities
        ax: Axes to plot on
        label: Line label
        **kwargs: Additional arguments
        
    Returns:
        Axes object
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))
    
    ax.plot(time, survival, label=label, **kwargs)
    ax.set_xlabel("Time (days)")
    ax.set_ylabel("Survival Probability")
    ax.set_title("Graft Survival Curve")
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    
    if label:
        ax.legend()
    
    return ax


def plot_environmental_effects(
    temperature: np.ndarray,
    humidity: np.ndarray,
    success: np.ndarray,
    ax: Optional[plt.Axes] = None,
    **kwargs
) -> plt.Axes:
    """Plot success as function of environmental conditions.
    
    Args:
        temperature: Temperature values
        humidity: Humidity values
        success: Success outcomes
        ax: Axes to plot on
        **kwargs: Additional arguments
        
    Returns:
        Axes object
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))
    
    # Create scatter plot colored by success
    scatter = ax.scatter(temperature, humidity, c=success, cmap='RdYlGn', 
                        vmin=0, vmax=1, alpha=0.6, **kwargs)
    
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("Humidity")
    ax.set_title("Graft Success by Environmental Conditions")
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Success (0=fail, 1=success)")
    
    # Mark optimal region
    ax.axvspan(20, 25, alpha=0.1, color='green', label='Optimal temp range')
    ax.axhspan(0.7, 0.9, alpha=0.1, color='blue', label='Optimal humidity range')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    return ax

