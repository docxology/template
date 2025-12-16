"""Optimal timing calculations for tree grafting.

This module provides seasonal window calculations, climate zone adjustments,
and optimal timing recommendations for different species and regions.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np


def calculate_optimal_grafting_window(
    species_type: str,
    hemisphere: str = "northern",
    climate_zone: str = "temperate"
) -> Tuple[int, int]:
    """Calculate optimal grafting window (start and end months).
    
    Args:
        species_type: Species type (temperate, tropical, subtropical)
        hemisphere: Hemisphere (northern, southern)
        climate_zone: Climate zone
        
    Returns:
        Tuple of (start_month, end_month) where months are 1-12
    """
    if species_type == "temperate":
        if hemisphere == "northern":
            return (2, 4)  # Late winter to early spring
        else:
            return (8, 10)  # Late winter in southern hemisphere
    elif species_type == "tropical":
        # Can graft year-round, but optimal in moderate seasons
        return (6, 9)  # Mid-year moderate weather
    elif species_type == "subtropical":
        if hemisphere == "northern":
            return (11, 3)  # Late fall to early spring
        else:
            return (5, 9)  # Late fall to early spring in southern
    else:
        # Default: spring
        return (3, 5)


def get_seasonal_suitability(
    month: int,
    species_type: str,
    hemisphere: str = "northern"
) -> Tuple[bool, str]:
    """Get seasonal suitability for grafting.
    
    Args:
        month: Month number (1-12)
        species_type: Species type
        hemisphere: Hemisphere
        
    Returns:
        Tuple of (is_suitable, reason)
    """
    start_month, end_month = calculate_optimal_grafting_window(
        species_type, hemisphere
    )
    
    # Handle year-spanning windows (e.g., Nov-Mar)
    if start_month > end_month:
        is_suitable = (month >= start_month) or (month <= end_month)
    else:
        is_suitable = start_month <= month <= end_month
    
    if is_suitable:
        reason = "Within optimal grafting window"
    else:
        reason = f"Outside optimal window ({start_month}-{end_month})"
    
    return is_suitable, reason


def calculate_temperature_suitability(
    temperature: float,
    species_type: str = "temperate"
) -> float:
    """Calculate temperature suitability score.
    
    Args:
        temperature: Temperature in Celsius
        species_type: Species type
        
    Returns:
        Suitability score (0-1)
    """
    if species_type == "temperate":
        optimal_range = (18, 25)
        acceptable_range = (10, 30)
    elif species_type == "tropical":
        optimal_range = (22, 28)
        acceptable_range = (18, 35)
    elif species_type == "subtropical":
        optimal_range = (15, 25)
        acceptable_range = (8, 32)
    else:
        optimal_range = (20, 25)
        acceptable_range = (10, 30)
    
    if optimal_range[0] <= temperature <= optimal_range[1]:
        return 1.0
    elif acceptable_range[0] <= temperature <= acceptable_range[1]:
        # Linear decrease outside optimal range
        if temperature < optimal_range[0]:
            return 1.0 - (optimal_range[0] - temperature) / (optimal_range[0] - acceptable_range[0])
        else:
            return 1.0 - (temperature - optimal_range[1]) / (acceptable_range[1] - optimal_range[1])
    else:
        return 0.0


def generate_grafting_calendar(
    species_type: str,
    hemisphere: str = "northern",
    climate_zone: str = "temperate"
) -> Dict[int, Dict[str, any]]:
    """Generate grafting calendar for the year.
    
    Args:
        species_type: Species type
        hemisphere: Hemisphere
        climate_zone: Climate zone
        
    Returns:
        Dictionary mapping month (1-12) to calendar information
    """
    calendar = {}
    start_month, end_month = calculate_optimal_grafting_window(
        species_type, hemisphere, climate_zone
    )
    
    for month in range(1, 13):
        is_suitable, reason = get_seasonal_suitability(month, species_type, hemisphere)
        
        # Estimate average temperature (simplified)
        if hemisphere == "northern":
            # Northern hemisphere seasonal pattern
            if month in [12, 1, 2]:
                avg_temp = 5.0
            elif month in [3, 4, 5]:
                avg_temp = 15.0
            elif month in [6, 7, 8]:
                avg_temp = 25.0
            else:
                avg_temp = 15.0
        else:
            # Southern hemisphere (6 month offset)
            offset_month = ((month + 5) % 12) + 1
            if offset_month in [12, 1, 2]:
                avg_temp = 5.0
            elif offset_month in [3, 4, 5]:
                avg_temp = 15.0
            elif offset_month in [6, 7, 8]:
                avg_temp = 25.0
            else:
                avg_temp = 15.0
        
        temp_suitability = calculate_temperature_suitability(avg_temp, species_type)
        
        calendar[month] = {
            "is_suitable": is_suitable,
            "reason": reason,
            "estimated_temperature": avg_temp,
            "temperature_suitability": float(temp_suitability),
            "overall_suitability": float(temp_suitability * (1.0 if is_suitable else 0.5))
        }
    
    return calendar


def adjust_for_climate_zone(
    base_window: Tuple[int, int],
    climate_zone: str
) -> Tuple[int, int]:
    """Adjust grafting window for specific climate zone.
    
    Args:
        base_window: Base window (start_month, end_month)
        climate_zone: Climate zone (tropical, subtropical, temperate, cold)
        
    Returns:
        Adjusted window (start_month, end_month)
    """
    start, end = base_window
    
    if climate_zone == "tropical":
        # Extend window, can graft more months
        return (max(1, start - 1), min(12, end + 2))
    elif climate_zone == "cold":
        # Narrow window, later start
        return (min(12, start + 1), min(12, end + 1))
    elif climate_zone == "subtropical":
        # Slight extension
        return (max(1, start - 1), min(12, end + 1))
    else:
        # Temperate: no adjustment
        return base_window

