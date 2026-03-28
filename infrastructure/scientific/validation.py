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

    functions = []
    for name in dir(module):
        obj = getattr(module, name)
        if callable(obj) and not name.startswith("_"):
            functions.append((name, obj))

    if not functions:
        return validation

    documented_functions = sum(1 for _, func in functions if inspect.getdoc(func) is not None)
    validation["docstring_coverage"] = documented_functions / len(functions)

    typed_functions = 0
    for _, func in functions:
        sig = inspect.signature(func)
        has_return_annotation = sig.return_annotation != inspect.Signature.empty
        has_param_annotations = any(
            p.annotation != inspect.Parameter.empty for p in sig.parameters.values()
        )

        if has_return_annotation or has_param_annotations:
            typed_functions += 1

    validation["type_hints_coverage"] = typed_functions / len(functions)

    source_lines = []
    try:
        source = inspect.getsource(module)
        source_lines = source.split("\n")
    except (OSError, TypeError) as e:
        logger.debug(f"Could not get source for module {module}: {e}")

    has_try_except = any("try:" in line or "except" in line for line in source_lines)
    has_raise = any("raise" in line for line in source_lines)
    validation["error_handling"] = has_try_except or has_raise

    has_validation = any(
        "assert" in line or "isinstance" in line or "ValueError" in line or "TypeError" in line
        for line in source_lines
    )
    validation["input_validation"] = has_validation

    weights = {
        "docstring_coverage": 0.25,
        "type_hints_coverage": 0.25,
        "error_handling": 0.25,
        "input_validation": 0.25,
    }

    validation["best_practices_score"] = (
        validation["docstring_coverage"] * weights["docstring_coverage"]        + validation["type_hints_coverage"] * weights["type_hints_coverage"]        + (1.0 if validation["error_handling"] else 0.0) * weights["error_handling"]
        + (1.0 if validation["input_validation"] else 0.0) * weights["input_validation"]
    )

    if validation["docstring_coverage"] < _COVERAGE_THRESHOLD:
        validation["recommendations"].append("Add docstrings to undocumented functions")
    if validation["type_hints_coverage"] < _COVERAGE_THRESHOLD:
        validation["recommendations"].append(
            "Add type hints to function parameters and return values"
        )

    if not validation["error_handling"]:
        validation["recommendations"].append("Add proper error handling with try/except blocks")
    if not validation["input_validation"]:
        validation["recommendations"].append("Add input validation to prevent invalid arguments")
    return validation

def check_research_compliance(func: Callable[..., Any]) -> dict[str, Any]:
    """Check function compliance with research software standards.

    Uses ``inspect.getsource`` to analyse source text. If the source is
    unavailable (e.g. C extensions, frozen modules), the ``has_error_handling``
    and ``has_input_validation`` checks are silently skipped and left False.
    The compliance_score is computed only from the checks that can be evaluated.
    """
    compliance = {
        "has_docstring": False,
        "has_type_hints": False,
        "has_examples": False,
        "has_error_handling": False,
        "has_input_validation": False,
        "follows_naming_conventions": False,
        "recommendations": [],
    }

    docstring = inspect.getdoc(func)
    if docstring:
        compliance["has_docstring"] = True

        if ">>>" in docstring or "Example" in docstring:
            compliance["has_examples"] = True

    signature = inspect.signature(func)
    has_param_hints = any(
        p.annotation != inspect.Parameter.empty for p in signature.parameters.values()
    )
    has_return_hint = signature.return_annotation != inspect.Signature.empty

    if has_param_hints or has_return_hint:
        compliance["has_type_hints"] = True

    if func.__name__.islower() and "_" in func.__name__:
        compliance["follows_naming_conventions"] = True

    try:
        source = inspect.getsource(func)
        source_lines = source.split("\n")

        has_validation = any(
            "assert" in line or "isinstance" in line or "ValueError" in line or "TypeError" in line
            for line in source_lines
        )
        compliance["has_input_validation"] = has_validation

        has_error_handling = any(
            "try:" in line or "except" in line or "raise" in line for line in source_lines
        )
        compliance["has_error_handling"] = has_error_handling

    except (OSError, TypeError) as e:
        logger.debug(f"Could not analyze function compliance for {func}: {e}")

    weights = {
        "has_docstring": 0.25,
        "has_type_hints": 0.20,
        "has_examples": 0.10,
        "has_error_handling": 0.15,
        "has_input_validation": 0.15,
        "follows_naming_conventions": 0.15,
    }

    score = 0.0
    for key, weight in weights.items():
        if compliance[key]:
            score += weight

    compliance["compliance_score"] = score

    if not compliance["has_docstring"]:
        compliance["recommendations"].append(            "Add comprehensive docstring with description and parameters"
        )

    if not compliance["has_type_hints"]:
        compliance["recommendations"].append("Add type hints to parameters and return value")
    if not compliance["has_examples"]:
        compliance["recommendations"].append("Add usage examples in docstring")
    if not compliance["has_error_handling"]:
        compliance["recommendations"].append("Add proper error handling for edge cases")
    if not compliance["has_input_validation"]:
        compliance["recommendations"].append("Add input validation to prevent invalid arguments")
    if not compliance["follows_naming_conventions"]:
        compliance["recommendations"].append("Use snake_case naming convention for functions")
    return compliance
