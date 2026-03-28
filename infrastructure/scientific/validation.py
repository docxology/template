"""Scientific implementation validation utilities.

Provides comprehensive validation for scientific code:
- Test case validation against expected outputs
- Best practices compliance checking
- Research software standards verification
- Code quality metrics and recommendations
"""

from __future__ import annotations

import inspect
from typing import Any, Callable, TypedDict

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

# Minimum coverage fraction considered acceptable for docstrings and type hints
_COVERAGE_THRESHOLD = 0.8

class _ValidationResults(TypedDict):
    """TypedDict for holding the results of scientific validation."""
    total_tests: int
    passed_tests: int
    failed_tests: int
    accuracy_score: float
    details: list[dict[str, Any]]

def validate_scientific_implementation(func: Callable[..., Any], test_cases: list[tuple[Any, Any]]) -> _ValidationResults:
    """Validate scientific implementation against known test cases."""
    validation_results: _ValidationResults = {
        "total_tests": len(test_cases),
        "passed_tests": 0,
        "failed_tests": 0,
        "accuracy_score": 0.0,
        "details": [],
    }

    for i, (test_input, expected_output) in enumerate(test_cases):
        try:
            actual_output = func(test_input)

            # Compare results with tolerance for floating point
            if isinstance(actual_output, (int, float)) and isinstance(
                expected_output, (int, float)
            ):
                passed = abs(actual_output - expected_output) < 1e-10
            else:
                passed = actual_output == expected_output

            if passed:
                validation_results["passed_tests"] += 1
            else:
                validation_results["failed_tests"] += 1
            validation_results["details"].append(
                {
                    "test_index": i,
                    "input": test_input,
                    "expected": expected_output,
                    "actual": actual_output,
                    "status": "PASSED" if passed else "FAILED",
                }
            )

        except (TypeError, ValueError, RuntimeError) as e:
            validation_results["failed_tests"] += 1
            validation_results["details"].append(
                {
                    "test_index": i,
                    "input": test_input,
                    "expected": expected_output,
                    "actual": f"Exception: {e}",
                    "status": "ERROR",
                }
            )

    if validation_results["total_tests"] > 0:
        validation_results["accuracy_score"] = (
            validation_results["passed_tests"] / validation_results["total_tests"]
        )

    return validation_results


def _type_hints_fraction(functions: list[tuple[str, Any]]) -> float:
    """Return the fraction of functions that have at least one type annotation."""
    typed = 0
    for _, func in functions:
        sig = inspect.signature(func)
        has_return = sig.return_annotation != inspect.Signature.empty
        has_params = any(
            p.annotation != inspect.Parameter.empty for p in sig.parameters.values()
        )
        if has_return or has_params:
            typed += 1
    return typed / len(functions) if functions else 0.0


def _analyze_source_features(module: Any) -> tuple[bool, bool]:
    """Return (has_error_handling, has_input_validation) from module source text."""
    try:
        source_lines = inspect.getsource(module).split("\n")
    except (OSError, TypeError) as e:
        logger.debug(f"Could not get source for module {module}: {e}")
        return False, False

    has_error = any("try:" in line or "except" in line or "raise" in line for line in source_lines)
    has_validation = any(
        "assert" in line or "isinstance" in line or "ValueError" in line or "TypeError" in line
        for line in source_lines
    )
    return has_error, has_validation


def _best_practices_recommendations(validation: dict[str, Any]) -> list[str]:
    """Return actionable recommendations based on validation scores."""
    recs: list[str] = []
    if validation["docstring_coverage"] < _COVERAGE_THRESHOLD:
        recs.append("Add docstrings to undocumented functions")
    if validation["type_hints_coverage"] < _COVERAGE_THRESHOLD:
        recs.append("Add type hints to function parameters and return values")
    if not validation["error_handling"]:
        recs.append("Add proper error handling with try/except blocks")
    if not validation["input_validation"]:
        recs.append("Add input validation to prevent invalid arguments")
    return recs


def validate_scientific_best_practices(module: Any) -> dict[str, Any]:
    """Validate that a module follows scientific computing best practices."""
    validation: dict[str, Any] = {
        "docstring_coverage": 0.0,
        "type_hints_coverage": 0.0,
        "error_handling": False,
        "input_validation": False,
        "numerical_stability": False,
        "best_practices_score": 0.0,
        "recommendations": [],
    }

    functions = [
        (name, getattr(module, name))
        for name in dir(module)
        if callable(getattr(module, name)) and not name.startswith("_")
    ]

    if not functions:
        return validation

    validation["docstring_coverage"] = sum(
        1 for _, func in functions if inspect.getdoc(func) is not None
    ) / len(functions)
    validation["type_hints_coverage"] = _type_hints_fraction(functions)
    validation["error_handling"], validation["input_validation"] = _analyze_source_features(module)

    validation["best_practices_score"] = 0.25 * (
        validation["docstring_coverage"]
        + validation["type_hints_coverage"]
        + (1.0 if validation["error_handling"] else 0.0)
        + (1.0 if validation["input_validation"] else 0.0)
    )
    validation["recommendations"] = _best_practices_recommendations(validation)
    return validation

def _compliance_docstring_features(func: Callable[..., Any]) -> tuple[bool, bool]:
    """Return (has_docstring, has_examples) for *func*."""
    docstring = inspect.getdoc(func)
    if not docstring:
        return False, False
    has_examples = ">>>" in docstring or "Example" in docstring
    return True, has_examples


def _compliance_signature_features(func: Callable[..., Any]) -> tuple[bool, bool]:
    """Return (has_type_hints, follows_naming_conventions) for *func*."""
    sig = inspect.signature(func)
    has_hints = (
        any(p.annotation != inspect.Parameter.empty for p in sig.parameters.values())
        or sig.return_annotation != inspect.Signature.empty
    )
    follows_naming = func.__name__.islower() and "_" in func.__name__
    return has_hints, follows_naming


def _compliance_source_features(func: Callable[..., Any]) -> tuple[bool, bool]:
    """Return (has_error_handling, has_input_validation) from *func* source.

    Returns (False, False) when source is unavailable (C extensions, frozen modules).
    """
    try:
        source_lines = inspect.getsource(func).split("\n")
    except (OSError, TypeError) as e:
        logger.debug(f"Could not analyze function compliance for {func}: {e}")
        return False, False

    has_error = any("try:" in line or "except" in line or "raise" in line for line in source_lines)
    has_validation = any(
        "assert" in line or "isinstance" in line or "ValueError" in line or "TypeError" in line
        for line in source_lines
    )
    return has_error, has_validation


_COMPLIANCE_WEIGHTS: dict[str, float] = {
    "has_docstring": 0.25,
    "has_type_hints": 0.20,
    "has_examples": 0.10,
    "has_error_handling": 0.15,
    "has_input_validation": 0.15,
    "follows_naming_conventions": 0.15,
}


def _compliance_score(compliance: dict[str, Any]) -> float:
    """Compute weighted compliance score from boolean feature flags."""
    return sum(
        weight for key, weight in _COMPLIANCE_WEIGHTS.items() if compliance.get(key)
    )


def _compliance_recommendations(compliance: dict[str, Any]) -> list[str]:
    """Return actionable recommendations for non-passing compliance checks."""
    recs: list[str] = []
    if not compliance["has_docstring"]:
        recs.append("Add comprehensive docstring with description and parameters")
    if not compliance["has_type_hints"]:
        recs.append("Add type hints to parameters and return value")
    if not compliance["has_examples"]:
        recs.append("Add usage examples in docstring")
    if not compliance["has_error_handling"]:
        recs.append("Add proper error handling for edge cases")
    if not compliance["has_input_validation"]:
        recs.append("Add input validation to prevent invalid arguments")
    if not compliance["follows_naming_conventions"]:
        recs.append("Use snake_case naming convention for functions")
    return recs


def check_research_compliance(func: Callable[..., Any]) -> dict[str, Any]:
    """Check function compliance with research software standards.

    Uses ``inspect.getsource`` to analyse source text. If the source is
    unavailable (e.g. C extensions, frozen modules), the ``has_error_handling``
    and ``has_input_validation`` checks are silently skipped and left False.
    The compliance_score is computed only from the checks that can be evaluated.
    """
    has_docstring, has_examples = _compliance_docstring_features(func)
    has_type_hints, follows_naming = _compliance_signature_features(func)
    has_error_handling, has_input_validation = _compliance_source_features(func)

    compliance: dict[str, Any] = {
        "has_docstring": has_docstring,
        "has_type_hints": has_type_hints,
        "has_examples": has_examples,
        "has_error_handling": has_error_handling,
        "has_input_validation": has_input_validation,
        "follows_naming_conventions": follows_naming,
        "recommendations": [],
    }
    compliance["compliance_score"] = _compliance_score(compliance)
    compliance["recommendations"] = _compliance_recommendations(compliance)
    return compliance
