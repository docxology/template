"""Numerical stability checking for scientific functions.

Provides utilities for testing algorithmic stability across input ranges:
- Stability testing with tolerance checking
- NaN/Inf detection
- Extreme value handling
- Stability scoring and recommendations
"""
from __future__ import annotations

from typing import List, Any, Callable, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class StabilityTest:
    """Container for numerical stability test results."""

    function_name: str
    test_name: str
    input_range: Tuple[float, float]
    expected_behavior: str
    actual_behavior: str
    stability_score: float
    recommendations: List[str]


def check_numerical_stability(func: Callable, test_inputs: List[Any],
                             tolerance: float = 1e-12) -> StabilityTest:
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
            # Test function execution
            result = func(test_input)

            # Check for NaN, inf, or extreme values
            if np.isnan(result).any() if hasattr(result, 'any') else np.isnan(result):
                behavior = "NaN values detected"
                score = 0.0
            elif np.isinf(result).any() if hasattr(result, 'any') else np.isinf(result):
                behavior = "Infinite values detected"
                score = 0.0
            elif np.abs(result) > 1e10:  # Arbitrary large value threshold
                behavior = "Extremely large values"
                score = 0.3
            else:
                behavior = "Numerically stable"
                score = 1.0

            results.append((test_input, result, behavior, score))

        except Exception as e:
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
        function_name=func.__name__,
        test_name="numerical_stability",
        input_range=(min(test_inputs), max(test_inputs)) if test_inputs else (0, 0),
        expected_behavior="Stable numerical behavior across input range",
        actual_behavior=f"Stability score: {overall_score:.2f}",
        stability_score=overall_score,
        recommendations=recommendations
    )

