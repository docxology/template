"""Domain-neutral computational backbone — the worked formalisms.

These are the tested, reusable functions a textbook's figures and worked
examples should call (thin-orchestrator rule: scripts never reimplement maths).
They are deliberately generic — logistic growth, saturating response,
exponential decay, a linear model, and descriptive statistics — so any
discipline can reuse them or replace them with subject-specific equivalents.

All functions are pure and deterministic: same inputs -> same outputs.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray


def logistic_growth(t: ArrayLike, *, r: float, carrying_capacity: float, initial: float) -> NDArray[np.float64]:
    r"""Logistic growth $N(t) = K / (1 + ((K - N_0)/N_0)\,e^{-rt})$.

    Args:
        t: Time points.
        r: Intrinsic growth rate (``r > 0``).
        carrying_capacity: Saturation level ``K`` (``K > 0``).
        initial: Initial value ``N_0`` (``0 < N_0 <= K``).

    Returns:
        Population/quantity at each time in ``t``.
    """
    if r <= 0:
        raise ValueError("r must be positive")
    if carrying_capacity <= 0:
        raise ValueError("carrying_capacity must be positive")
    if not 0 < initial <= carrying_capacity:
        raise ValueError("initial must satisfy 0 < initial <= carrying_capacity")
    t_arr = np.asarray(t, dtype=np.float64)
    k = carrying_capacity
    a = (k - initial) / initial
    return k / (1.0 + a * np.exp(-r * t_arr))


def saturating_response(
    x: ArrayLike, *, maximum: float, half_saturation: float, hill: float = 1.0
) -> NDArray[np.float64]:
    r"""Hill / Michaelis-Menten-style saturating response.

    $y = y_{max}\, x^{n} / (k^{n} + x^{n})$ with Hill coefficient ``n``.

    Args:
        x: Non-negative input values.
        maximum: Asymptotic maximum ``y_max`` (``> 0``).
        half_saturation: Input at half-maximal response ``k`` (``> 0``).
        hill: Hill coefficient ``n`` (``> 0``); 1.0 is Michaelis-Menten.
    """
    if maximum <= 0:
        raise ValueError("maximum must be positive")
    if half_saturation <= 0:
        raise ValueError("half_saturation must be positive")
    if hill <= 0:
        raise ValueError("hill must be positive")
    x_arr = np.asarray(x, dtype=np.float64)
    if np.any(x_arr < 0):
        raise ValueError("x must be non-negative")
    xn = np.power(x_arr, hill)
    result = maximum * xn / (np.power(half_saturation, hill) + xn)
    return np.asarray(result, dtype=np.float64)


def exponential_decay(t: ArrayLike, *, initial: float, rate: float) -> NDArray[np.float64]:
    r"""Exponential decay $y = y_0\, e^{-\lambda t}$."""
    if initial < 0:
        raise ValueError("initial must be non-negative")
    if rate < 0:
        raise ValueError("rate must be non-negative")
    t_arr = np.asarray(t, dtype=np.float64)
    return initial * np.exp(-rate * t_arr)


def half_life(rate: float) -> float:
    r"""Half-life $t_{1/2} = \ln 2 / \lambda$ for a decay ``rate`` (``> 0``)."""
    if rate <= 0:
        raise ValueError("rate must be positive")
    return float(np.log(2.0) / rate)


@dataclass(frozen=True)
class LinearFit:
    """Result of an ordinary least-squares line fit."""

    slope: float
    intercept: float
    r_squared: float

    def predict(self, x: ArrayLike) -> NDArray[np.float64]:
        """Evaluate the fitted line at ``x``."""
        return self.slope * np.asarray(x, dtype=np.float64) + self.intercept


def linear_fit(x: ArrayLike, y: ArrayLike) -> LinearFit:
    """Ordinary least-squares fit of ``y = slope * x + intercept``.

    Returns a :class:`LinearFit` carrying slope, intercept, and the coefficient
    of determination ``r_squared``.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)
    if x_arr.shape != y_arr.shape:
        raise ValueError("x and y must have the same shape")
    if x_arr.size < 2:
        raise ValueError("need at least two points")
    slope, intercept = np.polyfit(x_arr, y_arr, 1)
    predicted = slope * x_arr + intercept
    ss_res = float(np.sum((y_arr - predicted) ** 2))
    ss_tot = float(np.sum((y_arr - np.mean(y_arr)) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return LinearFit(slope=float(slope), intercept=float(intercept), r_squared=r_squared)


def descriptive_statistics(values: ArrayLike) -> dict[str, float]:
    """Return mean, standard deviation (population), min, max, and count."""
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        raise ValueError("values must be non-empty")
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "count": float(arr.size),
    }


def normalize_unit_interval(values: ArrayLike) -> NDArray[np.float64]:
    """Min-max scale ``values`` into ``[0, 1]``.

    A constant input maps to all-zeros (degenerate range handled explicitly).
    """
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        raise ValueError("values must be non-empty")
    lo = float(np.min(arr))
    hi = float(np.max(arr))
    if hi == lo:
        return np.zeros_like(arr)
    return (arr - lo) / (hi - lo)


__all__ = [
    "LinearFit",
    "descriptive_statistics",
    "exponential_decay",
    "half_life",
    "linear_fit",
    "logistic_growth",
    "normalize_unit_interval",
    "saturating_response",
]
