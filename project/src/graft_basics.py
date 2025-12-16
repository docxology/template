"""Core grafting concepts and basic calculations.

This module provides fundamental grafting operations including compatibility
checks, basic calculations, and core grafting concepts.
"""
from typing import Dict, List, Optional, Tuple


def check_cambium_alignment(
    rootstock_diameter: float,
    scion_diameter: float,
    tolerance: float = 0.1
) -> Tuple[bool, float]:
    """Check if rootstock and scion diameters are compatible for cambium alignment.
    
    Cambium alignment is critical for successful graft union formation. The
    diameters should be similar to ensure proper contact between cambial layers.
    
    Args:
        rootstock_diameter: Rootstock stem diameter (mm)
        scion_diameter: Scion stem diameter (mm)
        tolerance: Maximum relative difference allowed (default 0.1 = 10%)
        
    Returns:
        Tuple of (is_compatible, diameter_ratio)
    """
    if rootstock_diameter <= 0 or scion_diameter <= 0:
        return False, 0.0
    
    ratio = scion_diameter / rootstock_diameter
    max_ratio = 1.0 + tolerance
    min_ratio = 1.0 - tolerance
    
    is_compatible = min_ratio <= ratio <= max_ratio
    
    return is_compatible, ratio


def calculate_graft_angle(
    rootstock_diameter: float,
    scion_diameter: float,
    technique: str = "whip"
) -> float:
    """Calculate optimal cut angle for grafting technique.
    
    Different grafting techniques require different cut angles for optimal
    cambium contact and union formation.
    
    Args:
        rootstock_diameter: Rootstock diameter (mm)
        scion_diameter: Scion diameter (mm)
        technique: Grafting technique (whip, cleft, bark, approach)
        
    Returns:
        Optimal cut angle in degrees
    """
    if technique == "whip" or technique == "whip_and_tongue":
        # Whip grafting: 30-45 degree angle for long sloping cut
        return 35.0
    elif technique == "cleft":
        # Cleft grafting: 30-45 degree angle for wedge cut
        return 40.0
    elif technique == "bark":
        # Bark grafting: 20-30 degree angle for insertion
        return 25.0
    elif technique == "approach":
        # Approach grafting: 30-40 degree angle for matching cuts
        return 35.0
    else:
        # Default angle
        return 30.0


def estimate_callus_formation_time(
    temperature: float,
    humidity: float,
    species_compatibility: float = 0.8
) -> float:
    """Estimate callus formation time based on environmental conditions.
    
    Callus formation is the first stage of graft union healing. Time depends
    on temperature, humidity, and species compatibility.
    
    Args:
        temperature: Ambient temperature (Celsius)
        humidity: Relative humidity (0-1 or percentage)
        species_compatibility: Compatibility score (0-1, higher = more compatible)
        
    Returns:
        Estimated callus formation time in days
    """
    # Normalize humidity to 0-1 if given as percentage
    if humidity > 1.0:
        humidity = humidity / 100.0
    
    # Optimal temperature range: 20-25°C
    optimal_temp = 22.5
    temp_factor = 1.0
    
    if 15 <= temperature <= 30:
        # Within acceptable range
        temp_deviation = abs(temperature - optimal_temp)
        temp_factor = 1.0 + (temp_deviation / 10.0) * 0.5
    elif temperature < 15:
        # Too cold - slows formation
        temp_factor = 1.0 + (15 - temperature) / 5.0
    else:
        # Too hot - slows formation
        temp_factor = 1.0 + (temperature - 30) / 5.0
    
    # Humidity factor (optimal: 0.7-0.9)
    optimal_humidity = 0.8
    humidity_factor = 1.0 + abs(humidity - optimal_humidity) * 2.0
    
    # Base time: 7-14 days for compatible species
    base_time = 10.0 / species_compatibility
    
    # Apply environmental factors
    estimated_time = base_time * temp_factor * humidity_factor
    
    return max(3.0, min(30.0, estimated_time))  # Clamp to reasonable range


def calculate_union_strength(
    days_since_grafting: float,
    compatibility_score: float,
    technique_quality: float = 0.8
) -> float:
    """Calculate estimated graft union strength.
    
    Union strength increases over time as vascular connections form and
    callus tissue matures. Strength depends on compatibility and technique quality.
    
    Args:
        days_since_grafting: Days since grafting was performed
        compatibility_score: Species compatibility (0-1)
        technique_quality: Quality of grafting technique execution (0-1)
        
    Returns:
        Estimated union strength (0-1, where 1.0 = fully established)
    """
    # Union strength follows sigmoidal growth curve
    # Initial slow growth, rapid increase, then plateau
    
    # Time constant depends on compatibility
    time_constant = 30.0 / (compatibility_score + 0.1)
    
    # Sigmoid function: strength = 1 / (1 + exp(-k*(t - t0)))
    # Simplified: strength = 1 - exp(-t/tau)
    tau = time_constant * (2.0 - technique_quality)
    
    strength = 1.0 - (1.0 - compatibility_score * technique_quality) * \
               (1.0 - (1.0 - 1.0 / (1.0 + days_since_grafting / tau)))
    
    return max(0.0, min(1.0, strength))


def check_seasonal_timing(
    month: int,
    species_type: str = "temperate",
    hemisphere: str = "northern"
) -> Tuple[bool, str]:
    """Check if current month is suitable for grafting.
    
    Grafting timing is critical for success. Different species and regions
    have optimal grafting windows.
    
    Args:
        month: Month number (1-12)
        species_type: Species type (temperate, tropical, subtropical)
        hemisphere: Hemisphere (northern, southern)
        
    Returns:
        Tuple of (is_suitable, reason)
    """
    # Adjust month for southern hemisphere (6 month offset)
    if hemisphere == "southern":
        month = ((month + 5) % 12) + 1
    
    if species_type == "temperate":
        # Temperate species: late winter to early spring (Feb-Apr in northern)
        if month in [2, 3, 4]:
            return True, "Optimal grafting season"
        elif month in [1, 5]:
            return True, "Acceptable grafting season"
        elif month in [11, 12]:
            return False, "Too early - dormancy not complete"
        else:
            return False, "Too late - active growth period"
    
    elif species_type == "tropical":
        # Tropical species: can graft year-round, but avoid extreme weather
        if month in [6, 7, 8, 9]:
            return True, "Optimal season (moderate weather)"
        else:
            return True, "Acceptable season"
    
    elif species_type == "subtropical":
        # Subtropical: late fall to early spring
        if month in [11, 12, 1, 2, 3]:
            return True, "Optimal grafting season"
        elif month in [10, 4]:
            return True, "Acceptable grafting season"
        else:
            return False, "Outside optimal season"
    
    else:
        return True, "Unknown species type - assume acceptable"


def calculate_scion_length(
    rootstock_diameter: float,
    technique: str = "whip",
    bud_count: int = 3
) -> float:
    """Calculate optimal scion length for grafting.
    
    Scion length depends on rootstock size, technique, and desired bud count.
    
    Args:
        rootstock_diameter: Rootstock diameter (mm)
        technique: Grafting technique
        bud_count: Number of buds desired on scion
        
    Returns:
        Optimal scion length (cm)
    """
    # Base length per bud (cm)
    length_per_bud = 2.5
    
    # Technique-specific adjustments
    if technique == "whip" or technique == "whip_and_tongue":
        base_length = bud_count * length_per_bud + 2.0  # Extra for cut
    elif technique == "cleft":
        base_length = bud_count * length_per_bud + 3.0  # Longer for wedge
    elif technique == "bark":
        base_length = bud_count * length_per_bud + 2.5
    elif technique == "bud":
        base_length = 1.0  # Single bud only
    else:
        base_length = bud_count * length_per_bud + 2.0
    
    # Adjust for rootstock size (larger rootstock can support longer scion)
    size_factor = 1.0 + (rootstock_diameter - 10.0) / 50.0
    size_factor = max(0.8, min(1.5, size_factor))
    
    optimal_length = base_length * size_factor
    
    # For bud grafting, allow shorter scions (minimum 1 cm)
    # For other techniques, minimum 5 cm
    min_length = 1.0 if technique == "bud" else 5.0
    
    return max(min_length, min(30.0, optimal_length))  # Clamp to reasonable range


def estimate_success_probability(
    compatibility_score: float,
    technique_quality: float,
    environmental_score: float,
    timing_score: float
) -> float:
    """Estimate overall graft success probability.
    
    Combines multiple factors to estimate likelihood of successful graft union.
    
    Args:
        compatibility_score: Species compatibility (0-1)
        technique_quality: Grafting technique execution quality (0-1)
        environmental_score: Environmental conditions score (0-1)
        timing_score: Seasonal timing appropriateness (0-1)
        
    Returns:
        Estimated success probability (0-1)
    """
    # Weighted combination of factors
    weights = {
        "compatibility": 0.4,
        "technique": 0.3,
        "environment": 0.2,
        "timing": 0.1
    }
    
    success_prob = (
        weights["compatibility"] * compatibility_score +
        weights["technique"] * technique_quality +
        weights["environment"] * environmental_score +
        weights["timing"] * timing_score
    )
    
    return max(0.0, min(1.0, success_prob))

