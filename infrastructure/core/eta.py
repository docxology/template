"""ETA (Estimated Time of Arrival) calculation functions.

Pure functions for calculating time estimates during long-running operations.
Split from logging_progress.py to keep each module under 300 LOC.
"""

from __future__ import annotations

from typing import NamedTuple


class ETAEstimate(NamedTuple):
    """Three-point ETA estimate with optimistic, realistic, and pessimistic values.

    All values are in seconds, or None when indeterminate.
    """

    optimistic: float | None
    realistic: float | None
    pessimistic: float | None


def calculate_eta(elapsed_time: float, completed_items: int, total_items: int) -> float | None:
    """Calculate estimated time remaining using linear extrapolation; returns None if indeterminate."""
    if completed_items <= 0 or total_items <= 0:
        return None

    if completed_items >= total_items:
        return 0.0

    avg_time_per_item = elapsed_time / completed_items
    remaining_items = total_items - completed_items
    return avg_time_per_item * remaining_items


def calculate_eta_ema(
    elapsed_time: float,
    completed_items: int,
    total_items: int,
    previous_eta: float | None = None,
    alpha: float = 0.3,
) -> float | None:
    """Calculate ETA using EMA blending; returns seconds remaining or None."""
    if completed_items <= 0 or total_items <= 0:
        return None

    if completed_items >= total_items:
        return 0.0

    # Calculate linear ETA
    linear_eta = calculate_eta(elapsed_time, completed_items, total_items)
    if linear_eta is None:
        return None

    # If no previous ETA, return linear estimate
    if previous_eta is None:
        return linear_eta

    # Apply EMA: new_eta = alpha * linear_eta + (1 - alpha) * previous_eta
    ema_eta = alpha * linear_eta + (1 - alpha) * previous_eta

    # Ensure ETA is non-negative
    return max(0.0, ema_eta)


def calculate_eta_with_confidence(
    elapsed_time: float,
    completed_items: int,
    total_items: int,
    item_durations: list[float | None] = None,
) -> ETAEstimate:
    """Return ETAEstimate(optimistic, realistic, pessimistic) based on min/avg/max item duration."""
    if completed_items <= 0 or total_items <= 0:
        return ETAEstimate(None, None, None)

    if completed_items >= total_items:
        return ETAEstimate(0.0, 0.0, 0.0)

    remaining_items = total_items - completed_items

    if item_durations and len(item_durations) > 0:
        # Use actual item durations for better estimates
        min_duration = min(item_durations)
        avg_duration = sum(item_durations) / len(item_durations)
        max_duration = max(item_durations)

        optimistic = min_duration * remaining_items
        realistic = avg_duration * remaining_items
        pessimistic = max_duration * remaining_items
    else:
        # Fall back to simple linear calculation
        avg_time_per_item = elapsed_time / completed_items
        optimistic = avg_time_per_item * 0.8 * remaining_items  # 20% faster
        realistic = avg_time_per_item * remaining_items
        pessimistic = avg_time_per_item * 1.2 * remaining_items  # 20% slower

    return ETAEstimate(optimistic, realistic, pessimistic)
