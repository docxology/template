"""Graft compatibility prediction based on phylogenetic and biological factors.

This module provides compatibility prediction algorithms based on phylogenetic
distance, cambium characteristics, growth rates, and other biological factors.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np


def predict_compatibility_from_phylogeny(
    phylogenetic_distance: float,
    max_distance: float = 1.0
) -> float:
    """Predict compatibility based on phylogenetic distance.
    
    Closely related species are generally more compatible for grafting.
    
    Args:
        phylogenetic_distance: Phylogenetic distance (0-1, where 0 = same species)
        max_distance: Maximum distance for compatibility (default 1.0)
        
    Returns:
        Predicted compatibility score (0-1)
    """
    # Compatibility decreases with phylogenetic distance
    # Use exponential decay: compatibility = exp(-k * distance)
    k = 2.0  # Decay constant
    compatibility = np.exp(-k * phylogenetic_distance / max_distance)
    
    return float(np.clip(compatibility, 0.0, 1.0))


def predict_compatibility_from_cambium(
    rootstock_cambium_thickness: float,
    scion_cambium_thickness: float,
    tolerance: float = 0.2
) -> float:
    """Predict compatibility based on cambium thickness match.
    
    Similar cambium thickness indicates better alignment potential.
    
    Args:
        rootstock_cambium_thickness: Rootstock cambium thickness (mm)
        scion_cambium_thickness: Scion cambium thickness (mm)
        tolerance: Maximum relative difference allowed
        
    Returns:
        Predicted compatibility score (0-1)
    """
    if rootstock_cambium_thickness <= 0 or scion_cambium_thickness <= 0:
        return 0.0
    
    ratio = scion_cambium_thickness / rootstock_cambium_thickness
    deviation = abs(ratio - 1.0)
    
    # Compatibility decreases with deviation
    compatibility = 1.0 - min(1.0, deviation / tolerance)
    
    return float(max(0.0, compatibility))


def predict_compatibility_from_growth_rate(
    rootstock_growth_rate: float,
    scion_growth_rate: float,
    tolerance: float = 0.3
) -> float:
    """Predict compatibility based on growth rate match.
    
    Similar growth rates reduce stress at graft union.
    
    Args:
        rootstock_growth_rate: Rootstock growth rate (cm/year)
        scion_growth_rate: Scion growth rate (cm/year)
        tolerance: Maximum relative difference allowed
        
    Returns:
        Predicted compatibility score (0-1)
    """
    if rootstock_growth_rate <= 0 or scion_growth_rate <= 0:
        return 0.0
    
    ratio = scion_growth_rate / rootstock_growth_rate
    deviation = abs(ratio - 1.0)
    
    compatibility = 1.0 - min(1.0, deviation / tolerance)
    
    return float(max(0.0, compatibility))


def predict_compatibility_combined(
    phylogenetic_distance: float,
    cambium_match: float,
    growth_rate_match: float,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """Predict compatibility using multiple factors.
    
    Args:
        phylogenetic_distance: Phylogenetic distance (0-1)
        cambium_match: Cambium thickness match score (0-1)
        growth_rate_match: Growth rate match score (0-1)
        weights: Optional weights for factors (default: equal weights)
        
    Returns:
        Combined compatibility score (0-1)
    """
    if weights is None:
        weights = {
            "phylogeny": 0.5,
            "cambium": 0.3,
            "growth_rate": 0.2
        }
    
    # Convert phylogenetic distance to compatibility
    phylogeny_compat = predict_compatibility_from_phylogeny(phylogenetic_distance)
    
    # Weighted combination
    compatibility = (
        weights["phylogeny"] * phylogeny_compat +
        weights["cambium"] * cambium_match +
        weights["growth_rate"] * growth_rate_match
    )
    
    return float(np.clip(compatibility, 0.0, 1.0))


def predict_success_probability(
    compatibility: float,
    technique_quality: float,
    environmental_score: float,
    timing_score: float
) -> float:
    """Predict overall graft success probability.
    
    Args:
        compatibility: Species compatibility (0-1)
        technique_quality: Grafting technique quality (0-1)
        environmental_score: Environmental conditions score (0-1)
        timing_score: Seasonal timing score (0-1)
        
    Returns:
        Predicted success probability (0-1)
    """
    weights = {
        "compatibility": 0.4,
        "technique": 0.3,
        "environment": 0.2,
        "timing": 0.1
    }
    
    success_prob = (
        weights["compatibility"] * compatibility +
        weights["technique"] * technique_quality +
        weights["environment"] * environmental_score +
        weights["timing"] * timing_score
    )
    
    return float(np.clip(success_prob, 0.0, 1.0))

