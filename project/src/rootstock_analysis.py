"""Rootstock selection and analysis for tree grafting.

This module provides rootstock selection optimization, vigor analysis,
disease resistance evaluation, and rootstock-scion interaction analysis.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np


class RootstockProfile:
    """Profile of rootstock characteristics."""
    
    def __init__(
        self,
        name: str,
        vigor: float,
        disease_resistance: Dict[str, float],
        climate_adaptation: List[str],
        soil_preference: str = "well_drained"
    ):
        """Initialize rootstock profile.
        
        Args:
            name: Rootstock name/cultivar
            vigor: Vigor level (0-1, where 1 = very vigorous)
            disease_resistance: Dictionary mapping disease names to resistance (0-1)
            climate_adaptation: List of climate zones adapted to
            soil_preference: Soil type preference
        """
        self.name = name
        self.vigor = vigor
        self.disease_resistance = disease_resistance
        self.climate_adaptation = climate_adaptation
        self.soil_preference = soil_preference
    
    def overall_disease_resistance(self) -> float:
        """Calculate overall disease resistance score.
        
        Returns:
            Average disease resistance (0-1)
        """
        if not self.disease_resistance:
            return 0.5  # Default moderate resistance
        
        return float(np.mean(list(self.disease_resistance.values())))


def evaluate_rootstock_suitability(
    rootstock: RootstockProfile,
    scion_requirements: Dict[str, any],
    climate_zone: str,
    soil_type: str
) -> Tuple[float, Dict[str, float]]:
    """Evaluate rootstock suitability for specific conditions.
    
    Args:
        rootstock: Rootstock profile
        scion_requirements: Dictionary with scion requirements
        climate_zone: Climate zone
        soil_type: Soil type
        
    Returns:
        Tuple of (overall_suitability_score, factor_scores)
    """
    factor_scores = {}
    
    # Vigor match
    required_vigor = scion_requirements.get("vigor", 0.5)
    vigor_match = 1.0 - abs(rootstock.vigor - required_vigor)
    factor_scores["vigor_match"] = float(np.clip(vigor_match, 0.0, 1.0))
    
    # Disease resistance
    required_resistance = scion_requirements.get("disease_resistance", 0.5)
    actual_resistance = rootstock.overall_disease_resistance()
    resistance_score = actual_resistance if actual_resistance >= required_resistance else \
                       actual_resistance * 0.7  # Penalty for insufficient resistance
    factor_scores["disease_resistance"] = float(resistance_score)
    
    # Climate adaptation
    climate_match = 1.0 if climate_zone in rootstock.climate_adaptation else 0.5
    factor_scores["climate_adaptation"] = climate_match
    
    # Soil preference
    soil_match = 1.0 if soil_type == rootstock.soil_preference else 0.7
    factor_scores["soil_preference"] = soil_match
    
    # Weighted overall suitability
    weights = {
        "vigor_match": 0.3,
        "disease_resistance": 0.3,
        "climate_adaptation": 0.2,
        "soil_preference": 0.2
    }
    
    overall_score = sum(weights[k] * factor_scores[k] for k in weights.keys())
    
    return float(overall_score), factor_scores


def select_optimal_rootstock(
    rootstock_candidates: List[RootstockProfile],
    scion_requirements: Dict[str, any],
    climate_zone: str,
    soil_type: str
) -> Tuple[RootstockProfile, float, Dict[str, float]]:
    """Select optimal rootstock from candidates.
    
    Args:
        rootstock_candidates: List of candidate rootstocks
        scion_requirements: Scion requirements
        climate_zone: Climate zone
        soil_type: Soil type
        
    Returns:
        Tuple of (best_rootstock, suitability_score, factor_scores)
    """
    best_rootstock = None
    best_score = 0.0
    best_factors = {}
    
    for rootstock in rootstock_candidates:
        score, factors = evaluate_rootstock_suitability(
            rootstock, scion_requirements, climate_zone, soil_type
        )
        
        if score > best_score:
            best_score = score
            best_rootstock = rootstock
            best_factors = factors
    
    return best_rootstock, best_score, best_factors


def analyze_vigor_effects(
    rootstock_vigor: float,
    scion_vigor: float
) -> Dict[str, float]:
    """Analyze effects of vigor mismatch.
    
    Args:
        rootstock_vigor: Rootstock vigor (0-1)
        scion_vigor: Scion vigor (0-1)
        
    Returns:
        Dictionary with vigor analysis
    """
    vigor_ratio = scion_vigor / (rootstock_vigor + 1e-10)
    vigor_difference = abs(rootstock_vigor - scion_vigor)
    
    # Effects of mismatch
    if vigor_ratio > 1.5:
        effect = "scion_overgrowth"
        risk = "high"
    elif vigor_ratio < 0.67:
        effect = "rootstock_overgrowth"
        risk = "high"
    else:
        effect = "balanced"
        risk = "low"
    
    return {
        "vigor_ratio": float(vigor_ratio),
        "vigor_difference": float(vigor_difference),
        "effect": effect,
        "risk_level": risk,
        "recommendation": "match_vigor" if risk == "high" else "acceptable"
    }


def calculate_dwarfing_effect(
    rootstock_vigor: float,
    standard_vigor: float = 1.0
) -> float:
    """Calculate dwarfing effect of rootstock.
    
    Args:
        rootstock_vigor: Rootstock vigor (0-1)
        standard_vigor: Standard/vigorous rootstock vigor (default 1.0)
        
    Returns:
        Dwarfing factor (1.0 = no dwarfing, <1.0 = dwarfing effect)
    """
    dwarfing_factor = rootstock_vigor / (standard_vigor + 1e-10)
    return float(np.clip(dwarfing_factor, 0.0, 1.0))

