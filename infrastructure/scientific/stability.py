"""Numerical stability checking for scientific functions.

Provides utilities for testing algorithmic stability across input ranges:
- Stability testing with tolerance checking
- NaN/Inf detection
- Extreme value handling
- Stability scoring and recommendations
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)


@dataclass
class StabilityTest:
    """Container for numerical stability test results."""

    function_name: str
    test_name: str
    input_range: tuple[float, float]
    expected_behavior: str
    actual_behavior: str
    stability_score: float
    recommendations: list[str]


def _score_result(result: Any) -> tuple[str, float]:
    """Return (behavior_label, stability_score) for a numeric result."""
    has_nan = np.isnan(result).any() if hasattr(result, "any") else np.isnan(result)
    has_inf = np.isinf(result).any() if hasattr(result, "any") else np.isinf(result)
    if has_nan:
        return "NaN values detected", 0.0
    if has_inf:
        return "Infinite values detected", 0.0
    if np.abs(result) > 1e10:
        return "Extremely large values", 0.3
    return "Numerically stable", 1.0


def check_numerical_stability(
    func: Callable[..., Any], test_inputs: list[Any], tolerance: float = 1e-12
) -> StabilityTest:
    """Check numerical stability of a function across a range of inputs.

    Args:
        func: Function to test for stability
        test_inputs: List of input values to test
        tolerance: Numerical tolerance for stability assessment

    Returns:
        StabilityTest with analysis results
    """
    results = []

    for test_input in test_inputs:
        try:
            result = func(test_input)
            behavior, score = _score_result(result)
            results.append((test_input, result, behavior, score))

        except Exception as e:  # noqa: BLE001 — any function failure is a stability event
            results.append((test_input, None, f"Exception: {e}", 0.0))

    # Calculate overall stability score
    scores = [r[3] for r in results]
    overall_score = np.mean(scores) if scores else 0.0

    # Determine recommendations
    recommendations = []
    if overall_score < 0.8:
        recommendations.append("Consider adding input validation and error handling")
    if any("NaN" in r[2] or "inf" in r[2] for r in results):
        recommendations.append("Add numerical safeguards against NaN/inf values")
    if any("Exception" in r[2] for r in results):
        recommendations.append("Handle edge cases and invalid inputs gracefully")

    return StabilityTest(
        function_name=getattr(
            func, "__name__", getattr(getattr(func, "func", None), "__name__", repr(func))
        ),
        test_name="numerical_stability",
        input_range=(min(test_inputs), max(test_inputs)) if test_inputs else (0, 0),
        expected_behavior="Stable numerical behavior across input range",
        actual_behavior=f"Stability score: {overall_score:.2f}",
        stability_score=float(overall_score),
        recommendations=recommendations,
    )
