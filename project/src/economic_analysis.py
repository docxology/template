"""Economic analysis for tree grafting operations.

This module provides cost-benefit analysis, productivity modeling,
market value projections, and economic optimization for grafting operations.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np


def calculate_grafting_costs(
    n_grafts: int,
    labor_cost_per_graft: float,
    material_cost_per_graft: float,
    overhead_cost: float = 0.0
) -> Dict[str, float]:
    """Calculate total costs for grafting operation.
    
    Args:
        n_grafts: Number of grafts to perform
        labor_cost_per_graft: Labor cost per graft
        material_cost_per_graft: Material cost per graft
        overhead_cost: Fixed overhead costs
        
    Returns:
        Dictionary with cost breakdown
    """
    total_labor = n_grafts * labor_cost_per_graft
    total_materials = n_grafts * material_cost_per_graft
    total_variable = total_labor + total_materials
    total_cost = total_variable + overhead_cost
    
    cost_per_graft = total_cost / n_grafts if n_grafts > 0 else 0.0
    
    return {
        "total_labor_cost": float(total_labor),
        "total_material_cost": float(total_materials),
        "total_variable_cost": float(total_variable),
        "overhead_cost": float(overhead_cost),
        "total_cost": float(total_cost),
        "cost_per_graft": float(cost_per_graft),
        "n_grafts": int(n_grafts)
    }


def calculate_grafting_revenue(
    n_successful: int,
    value_per_successful_graft: float,
    time_to_market: float = 365.0
) -> Dict[str, float]:
    """Calculate revenue from successful grafts.
    
    Args:
        n_successful: Number of successful grafts
        value_per_successful_graft: Market value per successful graft
        time_to_market: Time to market in days (default 1 year)
        
    Returns:
        Dictionary with revenue information
    """
    total_revenue = n_successful * value_per_successful_graft
    
    # Annualized revenue (if time_to_market < 365)
    if time_to_market > 0:
        annualized_revenue = total_revenue * (365.0 / time_to_market)
    else:
        annualized_revenue = total_revenue
    
    return {
        "total_revenue": float(total_revenue),
        "annualized_revenue": float(annualized_revenue),
        "value_per_graft": float(value_per_successful_graft),
        "n_successful": int(n_successful),
        "time_to_market_days": float(time_to_market)
    }


def calculate_profitability(
    total_cost: float,
    total_revenue: float,
    n_grafts: int
) -> Dict[str, float]:
    """Calculate profitability metrics.
    
    Args:
        total_cost: Total costs
        total_revenue: Total revenue
        n_grafts: Number of grafts
        
    Returns:
        Dictionary with profitability metrics
    """
    net_profit = total_revenue - total_cost
    roi = (net_profit / total_cost * 100) if total_cost > 0 else 0.0
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0.0
    profit_per_graft = net_profit / n_grafts if n_grafts > 0 else 0.0
    
    return {
        "net_profit": float(net_profit),
        "roi_percent": float(roi),
        "profit_margin_percent": float(profit_margin),
        "profit_per_graft": float(profit_per_graft),
        "is_profitable": net_profit > 0
    }


def calculate_break_even_analysis(
    cost_per_graft: float,
    value_per_successful_graft: float
) -> Dict[str, float]:
    """Calculate break-even success rate.
    
    Args:
        cost_per_graft: Cost per graft attempt
        value_per_successful_graft: Value of successful graft
        
    Returns:
        Dictionary with break-even analysis
    """
    if value_per_successful_graft <= 0:
        break_even_rate = 1.0  # Impossible
        is_feasible = False
    else:
        break_even_rate = cost_per_graft / value_per_successful_graft
        is_feasible = break_even_rate <= 1.0
    
    return {
        "break_even_success_rate": float(np.clip(break_even_rate, 0.0, 1.0)),
        "cost_per_graft": float(cost_per_graft),
        "value_per_successful_graft": float(value_per_successful_graft),
        "is_feasible": is_feasible
    }


def optimize_grafting_operation(
    success_rate: float,
    cost_per_graft: float,
    value_per_successful_graft: float,
    max_grafts: int = 1000,
    budget: Optional[float] = None
) -> Dict[str, any]:
    """Optimize grafting operation parameters.
    
    Args:
        success_rate: Expected success rate (0-1)
        cost_per_graft: Cost per graft
        value_per_successful_graft: Value per successful graft
        max_grafts: Maximum number of grafts possible
        budget: Optional budget constraint
        
    Returns:
        Dictionary with optimization results
    """
    # Calculate optimal number of grafts
    if budget is not None:
        optimal_n_grafts = int(budget / cost_per_graft)
        optimal_n_grafts = min(optimal_n_grafts, max_grafts)
    else:
        # Calculate based on profitability
        expected_profit_per_graft = success_rate * value_per_successful_graft - cost_per_graft
        if expected_profit_per_graft > 0:
            optimal_n_grafts = max_grafts
        else:
            optimal_n_grafts = 0
    
    # Calculate expected outcomes
    expected_successful = int(optimal_n_grafts * success_rate)
    costs = calculate_grafting_costs(optimal_n_grafts, cost_per_graft, 0.0)
    revenue = calculate_grafting_revenue(expected_successful, value_per_successful_graft)
    profitability = calculate_profitability(
        costs["total_cost"], revenue["total_revenue"], optimal_n_grafts
    )
    
    return {
        "optimal_n_grafts": int(optimal_n_grafts),
        "expected_successful": int(expected_successful),
        "expected_costs": costs,
        "expected_revenue": revenue,
        "expected_profitability": profitability,
        "recommendation": "proceed" if profitability["is_profitable"] else "reconsider"
    }


def calculate_productivity_metrics(
    n_grafts_per_day: float,
    success_rate: float,
    days_per_year: float = 250.0
) -> Dict[str, float]:
    """Calculate productivity metrics.
    
    Args:
        n_grafts_per_day: Number of grafts per day
        success_rate: Success rate
        days_per_year: Working days per year
        
    Returns:
        Dictionary with productivity metrics
    """
    n_grafts_per_year = n_grafts_per_day * days_per_year
    n_successful_per_year = n_grafts_per_year * success_rate
    
    return {
        "grafts_per_day": float(n_grafts_per_day),
        "grafts_per_year": float(n_grafts_per_year),
        "successful_per_year": float(n_successful_per_year),
        "working_days": float(days_per_year),
        "efficiency": float(success_rate)  # Overall efficiency
    }

