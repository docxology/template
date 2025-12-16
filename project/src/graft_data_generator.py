"""Data generation for tree grafting experiments and analysis.

This module provides synthetic grafting experiment data generation including
success/failure scenarios, species compatibility matrices, and environmental data.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def generate_graft_trial_data(
    n_trials: int,
    n_species: int = 10,
    success_rate: float = 0.75,
    seed: Optional[int] = None
) -> Dict[str, np.ndarray]:
    """Generate synthetic grafting trial data.
    
    Creates realistic grafting experiment data with success/failure outcomes,
    environmental conditions, and species compatibility information.
    
    Args:
        n_trials: Number of grafting trials
        n_species: Number of species pairs
        success_rate: Overall success rate (0-1)
        seed: Random seed
        
    Returns:
        Dictionary with trial data arrays
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Generate species pairs
    rootstock_species = np.random.randint(0, n_species, size=n_trials)
    scion_species = np.random.randint(0, n_species, size=n_trials)
    
    # Generate compatibility scores (higher = more compatible)
    compatibility = np.random.beta(3, 1, size=n_trials)  # Skewed toward higher values
    
    # Generate environmental conditions
    temperature = np.random.normal(22.0, 3.0, size=n_trials)
    humidity = np.random.beta(8, 2, size=n_trials)  # Skewed toward 0.8
    
    # Generate technique quality
    technique_quality = np.random.beta(4, 1, size=n_trials)
    
    # Calculate success probability
    success_prob = (
        0.4 * compatibility +
        0.2 * np.clip((temperature - 15) / 15, 0, 1) +
        0.2 * humidity +
        0.2 * technique_quality
    )
    
    # Generate success outcomes
    success = (np.random.random(n_trials) < success_prob).astype(int)
    
    # Generate union strength (only for successful grafts)
    union_strength = np.zeros(n_trials)
    successful_mask = success == 1
    union_strength[successful_mask] = np.random.beta(5, 2, size=np.sum(successful_mask))
    
    # Generate healing time (days)
    healing_time = np.zeros(n_trials)
    healing_time[successful_mask] = np.random.lognormal(
        np.log(21.0), 0.3, size=np.sum(successful_mask)
    )
    healing_time[~successful_mask] = np.nan
    
    return {
        "rootstock_species": rootstock_species,
        "scion_species": scion_species,
        "compatibility": compatibility,
        "temperature": temperature,
        "humidity": humidity,
        "technique_quality": technique_quality,
        "success": success,
        "union_strength": union_strength,
        "healing_time": healing_time
    }


def generate_compatibility_matrix(
    n_species: int = 20,
    phylogenetic_structure: bool = True,
    seed: Optional[int] = None
) -> np.ndarray:
    """Generate species compatibility matrix.
    
    Creates a compatibility matrix where values represent graft success
    probability between species pairs. Can include phylogenetic structure
    where closely related species are more compatible.
    
    Args:
        n_species: Number of species
        phylogenetic_structure: Whether to include phylogenetic clustering
        seed: Random seed
        
    Returns:
        n_species x n_species compatibility matrix (0-1)
    """
    if seed is not None:
        np.random.seed(seed)
    
    if phylogenetic_structure:
        # Create phylogenetic distance matrix
        # Closely related species have higher compatibility
        positions = np.random.rand(n_species, 2)  # 2D phylogenetic space
        
        # Calculate distances
        distances = np.zeros((n_species, n_species))
        for i in range(n_species):
            for j in range(n_species):
                distances[i, j] = np.linalg.norm(positions[i] - positions[j])
        
        # Convert distances to compatibility (closer = more compatible)
        max_dist = np.max(distances)
        compatibility = 1.0 - (distances / max_dist) * 0.7  # 0.3 to 1.0 range
        
        # Add some noise
        noise = np.random.normal(0, 0.1, size=(n_species, n_species))
        compatibility = np.clip(compatibility + noise, 0.0, 1.0)
        
        # Make symmetric
        compatibility = (compatibility + compatibility.T) / 2
        
        # Self-compatibility is always 1.0
        np.fill_diagonal(compatibility, 1.0)
    else:
        # Random compatibility matrix
        compatibility = np.random.beta(3, 1, size=(n_species, n_species))
        compatibility = (compatibility + compatibility.T) / 2
        np.fill_diagonal(compatibility, 1.0)
    
    return compatibility


def generate_environmental_data(
    n_samples: int,
    season: str = "spring",
    seed: Optional[int] = None
) -> Dict[str, np.ndarray]:
    """Generate environmental condition data.
    
    Creates realistic environmental data for grafting operations including
    temperature, humidity, and seasonal variations.
    
    Args:
        n_samples: Number of samples
        season: Season (spring, summer, fall, winter)
        seed: Random seed
        
    Returns:
        Dictionary with environmental data
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Seasonal temperature patterns
    season_temps = {
        "spring": (18.0, 4.0),
        "summer": (25.0, 3.0),
        "fall": (15.0, 4.0),
        "winter": (8.0, 3.0)
    }
    
    temp_mean, temp_std = season_temps.get(season, (20.0, 3.0))
    temperature = np.random.normal(temp_mean, temp_std, size=n_samples)
    
    # Humidity (higher in spring/summer)
    if season in ["spring", "summer"]:
        humidity = np.random.beta(9, 2, size=n_samples)  # Mean ~0.82
    else:
        humidity = np.random.beta(6, 3, size=n_samples)  # Mean ~0.67
    
    # Light intensity (hours of daylight)
    season_light = {
        "spring": (12.0, 1.0),
        "summer": (14.0, 0.5),
        "fall": (11.0, 1.0),
        "winter": (9.0, 1.0)
    }
    
    light_mean, light_std = season_light.get(season, (12.0, 1.0))
    light_hours = np.random.normal(light_mean, light_std, size=n_samples)
    light_hours = np.clip(light_hours, 8.0, 16.0)
    
    # Rainfall (mm per day)
    if season in ["spring", "fall"]:
        rainfall = np.random.exponential(2.0, size=n_samples)
    elif season == "summer":
        rainfall = np.random.exponential(1.0, size=n_samples)
    else:
        rainfall = np.random.exponential(1.5, size=n_samples)
    
    return {
        "temperature": temperature,
        "humidity": humidity,
        "light_hours": light_hours,
        "rainfall": rainfall,
        "season": np.full(n_samples, season)
    }


def generate_success_scenarios(
    n_scenarios: int,
    base_success_rate: float = 0.7,
    seed: Optional[int] = None
) -> Dict[str, np.ndarray]:
    """Generate different grafting success scenarios.
    
    Creates scenarios with varying success rates to simulate different
    conditions, techniques, or species combinations.
    
    Args:
        n_scenarios: Number of scenarios
        base_success_rate: Base success rate
        seed: Random seed
        
    Returns:
        Dictionary with scenario data
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Generate scenario parameters
    scenario_success_rates = np.random.beta(
        base_success_rate * 10, (1 - base_success_rate) * 10, size=n_scenarios
    )
    
    # Generate number of trials per scenario
    trials_per_scenario = np.random.poisson(50, size=n_scenarios)
    trials_per_scenario = np.maximum(trials_per_scenario, 10)  # Minimum 10 trials
    
    # Generate success outcomes for each scenario
    all_success = []
    scenario_ids = []
    
    for i, (success_rate, n_trials) in enumerate(zip(scenario_success_rates, trials_per_scenario)):
        successes = np.random.binomial(1, success_rate, size=n_trials)
        all_success.extend(successes)
        scenario_ids.extend([i] * n_trials)
    
    return {
        "scenario_id": np.array(scenario_ids),
        "success": np.array(all_success),
        "scenario_success_rates": scenario_success_rates,
        "trials_per_scenario": trials_per_scenario
    }


def validate_graft_data(
    data: Dict[str, np.ndarray],
    check_finite: bool = True,
    check_ranges: bool = True
) -> Tuple[bool, Optional[str]]:
    """Validate grafting data quality.
    
    Args:
        data: Data dictionary
        check_finite: Check for finite values
        check_ranges: Check value ranges
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check finite values
    if check_finite:
        for key, values in data.items():
            if isinstance(values, np.ndarray):
                if not np.all(np.isfinite(values[~np.isnan(values)])):
                    return False, f"Non-finite values in {key}"
    
    # Check ranges
    if check_ranges:
        range_checks = {
            "compatibility": (0.0, 1.0),
            "humidity": (0.0, 1.0),
            "technique_quality": (0.0, 1.0),
            "union_strength": (0.0, 1.0),
            "success": (0, 1),
            "temperature": (-10.0, 50.0)
        }
        
        for key, (min_val, max_val) in range_checks.items():
            if key in data:
                values = data[key]
                valid_values = values[~np.isnan(values)]
                if len(valid_values) > 0:
                    if np.any(valid_values < min_val) or np.any(valid_values > max_val):
                        return False, f"{key} outside range [{min_val}, {max_val}]"
    
    return True, None

