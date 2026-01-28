"""Test suite for infrastructure.scientific.validation module.

Tests scientific validation utilities including:
- Test case validation against expected outputs
- Best practices compliance checking
- Research software standards verification
- Code quality metrics and recommendations

All tests use real functions and modules with no mocks.
"""

import inspect
from pathlib import Path

import numpy as np
import pytest

from infrastructure.scientific.validation import (
    check_research_compliance,
    validate_scientific_best_practices,
    validate_scientific_implementation,
)


class TestValidateScientificImplementation:
    """Test validate_scientific_implementation function."""

    def test_all_tests_pass(self):
        """Test validation when all test cases pass."""

        def multiply(x):
            return x * 2

        test_cases = [(1, 2), (2, 4), (5, 10), (0, 0)]
        result = validate_scientific_implementation(multiply, test_cases)

        assert result["total_tests"] == 4
        assert result["passed_tests"] == 4
        assert result["failed_tests"] == 0
        assert result["accuracy_score"] == 1.0

    def test_all_tests_fail(self):
        """Test validation when all test cases fail."""

        def wrong_multiply(x):
            return x * 3  # Wrong implementation

        test_cases = [(1, 2), (2, 4), (5, 10)]
        result = validate_scientific_implementation(wrong_multiply, test_cases)

        assert result["passed_tests"] == 0
        assert result["failed_tests"] == 3
        assert result["accuracy_score"] == 0.0

    def test_partial_pass(self):
        """Test validation with partial pass rate."""

        def conditional(x):
            return x * 2 if x < 5 else x * 3

        test_cases = [(1, 2), (2, 4), (5, 10), (10, 20)]  # Last two will fail
        result = validate_scientific_implementation(conditional, test_cases)

        assert result["passed_tests"] == 2
        assert result["failed_tests"] == 2
        assert result["accuracy_score"] == 0.5

    def test_floating_point_tolerance(self):
        """Test floating point comparison with tolerance."""

        def divide(x):
            return x / 3.0

        # Results that are approximately equal
        test_cases = [(3.0, 1.0), (6.0, 2.0), (9.0, 3.0)]
        result = validate_scientific_implementation(divide, test_cases)

        assert result["accuracy_score"] == 1.0

    def test_floating_point_tolerance_edge(self):
        """Test floating point at edge of tolerance."""

        def precise_calc(x):
            return x + 1e-11  # Very small difference

        test_cases = [(1.0, 1.0)]  # Difference is 1e-11, less than 1e-10 tolerance
        result = validate_scientific_implementation(precise_calc, test_cases)

        assert result["passed_tests"] == 1

    def test_string_output_equality(self):
        """Test validation with string outputs."""

        def format_string(x):
            return f"result_{x}"

        test_cases = [(1, "result_1"), (2, "result_2"), ("test", "result_test")]
        result = validate_scientific_implementation(format_string, test_cases)

        assert result["accuracy_score"] == 1.0

    def test_string_output_failure(self):
        """Test validation with failing string outputs."""

        def wrong_format(x):
            return f"wrong_{x}"

        test_cases = [(1, "result_1"), (2, "result_2")]
        result = validate_scientific_implementation(wrong_format, test_cases)

        assert result["accuracy_score"] == 0.0

    def test_list_output_equality(self):
        """Test validation with list outputs."""

        def to_list(x):
            return [x, x * 2]

        test_cases = [(1, [1, 2]), (2, [2, 4])]
        result = validate_scientific_implementation(to_list, test_cases)

        assert result["accuracy_score"] == 1.0

    def test_exception_handling(self):
        """Test validation handles exceptions gracefully."""

        def may_fail(x):
            if x == 0:
                raise ValueError("Cannot process zero")
            return x * 2

        test_cases = [(0, 0), (1, 2), (2, 4)]
        result = validate_scientific_implementation(may_fail, test_cases)

        assert result["failed_tests"] >= 1
        # Check details contain error status
        error_cases = [d for d in result["details"] if d["status"] == "ERROR"]
        assert len(error_cases) >= 1

    def test_empty_test_cases(self):
        """Test validation with empty test cases."""

        def dummy(x):
            return x

        result = validate_scientific_implementation(dummy, [])

        assert result["total_tests"] == 0
        assert result["accuracy_score"] == 0.0

    def test_details_structure(self):
        """Test details are properly structured."""

        def identity(x):
            return x

        test_cases = [(1, 1), (2, 2)]
        result = validate_scientific_implementation(identity, test_cases)

        assert len(result["details"]) == 2
        for detail in result["details"]:
            assert "test_index" in detail
            assert "input" in detail
            assert "expected" in detail
            assert "actual" in detail
            assert "status" in detail
            assert detail["status"] in ["PASSED", "FAILED", "ERROR"]

    def test_numpy_array_output(self):
        """Test validation with numpy array outputs."""

        def to_array(x):
            return np.array([x, x + 1])

        # NumPy arrays use __eq__ which returns an array, so equality check differs
        test_cases = [(1, np.array([1, 2]))]
        result = validate_scientific_implementation(to_array, test_cases)

        # This tests the non-numeric comparison path
        assert "details" in result

    def test_mixed_numeric_types(self):
        """Test validation with mixed int/float types."""

        def process(x):
            return float(x) * 2.0

        test_cases = [(1, 2.0), (2, 4.0), (0.5, 1.0)]
        result = validate_scientific_implementation(process, test_cases)

        assert result["accuracy_score"] == 1.0


class TestValidateScientificBestPractices:
    """Test validate_scientific_best_practices function."""

    def test_well_documented_module(self, tmp_path):
        """Test validation of well-documented module."""
        module_file = tmp_path / "good_module.py"
        module_file.write_text('''
"""Well documented module."""

def documented_function(x: float, y: int = 5) -> float:
    """Process input values.

    Args:
        x: First value
        y: Second value

    Returns:
        Processed result
    """
    try:
        if not isinstance(x, (int, float)):
            raise TypeError("x must be numeric")
        return x + y
    except Exception as e:
        raise ValueError(f"Processing failed: {e}")
''')

        import importlib.util
        spec = importlib.util.spec_from_file_location("good_module", module_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        result = validate_scientific_best_practices(module)

        assert result["docstring_coverage"] == 1.0
        assert result["type_hints_coverage"] == 1.0
        assert result["error_handling"] is True
        assert result["input_validation"] is True
        assert result["best_practices_score"] == 1.0

    def test_poorly_documented_module(self, tmp_path):
        """Test validation of poorly documented module."""
        module_file = tmp_path / "poor_module.py"
        module_file.write_text('''
def undocumented(x):
    return x + 1

def another_undocumented(y):
    return y * 2
''')

        import importlib.util
        spec = importlib.util.spec_from_file_location("poor_module", module_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        result = validate_scientific_best_practices(module)

        assert result["docstring_coverage"] == 0.0
        assert result["type_hints_coverage"] == 0.0
        assert result["error_handling"] is False
        assert result["input_validation"] is False
        assert len(result["recommendations"]) >= 2

    def test_partial_documentation(self, tmp_path):
        """Test validation of partially documented module."""
        module_file = tmp_path / "partial_module.py"
        module_file.write_text('''
def documented(x: float) -> float:
    """This function is documented."""
    return x * 2

def undocumented(x):
    return x + 1
''')

        import importlib.util
        spec = importlib.util.spec_from_file_location("partial_module", module_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        result = validate_scientific_best_practices(module)

        assert result["docstring_coverage"] == 0.5
        assert result["type_hints_coverage"] == 0.5

    def test_module_with_error_handling(self, tmp_path):
        """Test detection of error handling patterns."""
        module_file = tmp_path / "error_module.py"
        module_file.write_text('''
def with_try_except(x):
    try:
        return x / x
    except ZeroDivisionError:
        return 0

def with_raise(x):
    if x < 0:
        raise ValueError("Negative input")
    return x
''')

        import importlib.util
        spec = importlib.util.spec_from_file_location("error_module", module_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        result = validate_scientific_best_practices(module)

        assert result["error_handling"] is True

    def test_module_with_input_validation(self, tmp_path):
        """Test detection of input validation patterns."""
        module_file = tmp_path / "validation_module.py"
        module_file.write_text('''
def with_isinstance(x):
    if not isinstance(x, (int, float)):
        raise TypeError("x must be numeric")
    return x

def with_assert(x):
    assert x > 0, "x must be positive"
    return x
''')

        import importlib.util
        spec = importlib.util.spec_from_file_location("validation_module", module_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        result = validate_scientific_best_practices(module)

        assert result["input_validation"] is True

    def test_empty_module(self, tmp_path):
        """Test validation of module with no public functions."""
        module_file = tmp_path / "empty_module.py"
        module_file.write_text('''
"""Empty module."""

def _private_function(x):
    return x

_PRIVATE_VAR = 42
''')

        import importlib.util
        spec = importlib.util.spec_from_file_location("empty_module", module_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        result = validate_scientific_best_practices(module)

        assert result["docstring_coverage"] == 0.0

    def test_recommendations_generation(self, tmp_path):
        """Test recommendations are generated appropriately."""
        module_file = tmp_path / "needs_work.py"
        module_file.write_text('''
def no_docs(x):
    return x

def no_types(y):
    return y * 2
''')

        import importlib.util
        spec = importlib.util.spec_from_file_location("needs_work", module_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        result = validate_scientific_best_practices(module)

        assert "Add docstrings" in str(result["recommendations"])
        assert "Add type hints" in str(result["recommendations"])
        assert "error handling" in str(result["recommendations"]).lower()
        assert "input validation" in str(result["recommendations"]).lower()

    def test_best_practices_score_calculation(self, tmp_path):
        """Test best practices score is calculated correctly."""
        module_file = tmp_path / "scored_module.py"
        module_file.write_text('''
def typed_func(x: int) -> int:
    """Documented and typed."""
    return x * 2
''')

        import importlib.util
        spec = importlib.util.spec_from_file_location("scored_module", module_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        result = validate_scientific_best_practices(module)

        # Score = 0.25 * docstring + 0.25 * type_hints + 0.25 * error + 0.25 * validation
        # = 0.25 * 1.0 + 0.25 * 1.0 + 0.25 * 0 + 0.25 * 0 = 0.5
        assert result["best_practices_score"] == 0.5



class TestCheckResearchCompliance:
    """Test check_research_compliance function."""

    def test_fully_compliant_function(self):
        """Test compliance check on fully compliant function."""

        def compliant_function(x: float, y: int = 5) -> float:
            """Calculate weighted sum.

            This function computes a weighted sum of two values.

            Args:
                x: First value (weight 1.0)
                y: Second value (weight 0.5)

            Returns:
                Weighted sum

            Examples:
                >>> compliant_function(10.0, 4)
                12.0
            """
            try:
                if not isinstance(x, (int, float)):
                    raise TypeError("x must be numeric")
                return x + 0.5 * y
            except Exception:
                raise ValueError("Calculation failed")

        result = check_research_compliance(compliant_function)

        assert result["has_docstring"] is True
        assert result["has_type_hints"] is True
        assert result["has_examples"] is True
        assert result["has_error_handling"] is True
        assert result["has_input_validation"] is True
        assert result["follows_naming_conventions"] is True
        assert result["compliance_score"] == 1.0

    def test_non_compliant_function(self):
        """Test compliance check on non-compliant function."""

        def BadFunction(x):
            return x + 1

        result = check_research_compliance(BadFunction)

        assert result["has_docstring"] is False
        assert result["has_type_hints"] is False
        assert result["has_examples"] is False
        assert result["follows_naming_conventions"] is False
        assert result["compliance_score"] < 0.5

    def test_partial_compliance(self):
        """Test compliance check on partially compliant function."""

        def partial_function(x: float) -> float:
            """A documented function with types."""
            return x * 2

        result = check_research_compliance(partial_function)

        assert result["has_docstring"] is True
        assert result["has_type_hints"] is True
        assert result["has_examples"] is False
        assert result["has_error_handling"] is False

    def test_naming_conventions(self):
        """Test naming convention checking."""

        def snake_case_function(x: int) -> int:
            """Follows snake_case."""
            return x

        def CamelCase(x):
            return x

        def nounderscores(x):
            return x

        snake_result = check_research_compliance(snake_case_function)
        camel_result = check_research_compliance(CamelCase)
        no_under_result = check_research_compliance(nounderscores)

        assert snake_result["follows_naming_conventions"] is True
        assert camel_result["follows_naming_conventions"] is False
        assert no_under_result["follows_naming_conventions"] is False

    def test_example_detection(self):
        """Test detection of examples in docstring."""

        def with_doctest(x):
            """Function with doctest example.

            >>> with_doctest(5)
            10
            """
            return x * 2

        def with_example_section(x):
            """Function with Example section.

            Example:
                result = with_example_section(5)
            """
            return x * 2

        doctest_result = check_research_compliance(with_doctest)
        example_result = check_research_compliance(with_example_section)

        assert doctest_result["has_examples"] is True
        assert example_result["has_examples"] is True

    def test_recommendations_for_non_compliant(self):
        """Test recommendations are generated for non-compliant functions."""

        def poor_function(x):
            return x

        result = check_research_compliance(poor_function)

        assert len(result["recommendations"]) > 0
        # Should recommend adding docstring
        assert any("docstring" in rec.lower() for rec in result["recommendations"])
        # Should recommend adding type hints
        assert any("type hint" in rec.lower() for rec in result["recommendations"])

    def test_compliance_score_weights(self):
        """Test compliance score is calculated with correct weights."""
        # Weights: docstring=0.25, types=0.20, examples=0.10,
        #          error_handling=0.15, input_validation=0.15, naming=0.15

        def just_docstring(x):
            """Has only docstring."""
            return x

        result = check_research_compliance(just_docstring)

        # Should have docstring weight contribution
        assert result["has_docstring"] is True
        assert result["compliance_score"] >= 0.25

    def test_source_inspection_failure(self):
        """Test compliance check handles source inspection failure."""
        # Built-in functions don't have inspectable source
        result = check_research_compliance(len)

        # Should still return a valid result
        assert "compliance_score" in result
        assert isinstance(result["compliance_score"], (int, float))

    def test_return_annotation_only(self):
        """Test function with only return annotation."""

        def return_only(x) -> int:
            return x

        result = check_research_compliance(return_only)

        assert result["has_type_hints"] is True

    def test_param_annotation_only(self):
        """Test function with only parameter annotations."""

        def param_only(x: int):
            return x

        result = check_research_compliance(param_only)

        assert result["has_type_hints"] is True


class TestValidationIntegration:
    """Integration tests for validation functionality."""

    def test_validate_real_scientific_module(self):
        """Test validation of actual infrastructure module."""
        import infrastructure.scientific.stability as stability_module

        result = validate_scientific_best_practices(stability_module)

        # Real module should have some good practices
        # Note: coverage depends on module implementation
        assert result["docstring_coverage"] > 0.0
        assert "best_practices_score" in result
        assert isinstance(result["best_practices_score"], float)

    def test_compliance_on_real_function(self):
        """Test compliance check on actual infrastructure function."""
        from infrastructure.scientific.stability import check_numerical_stability

        result = check_research_compliance(check_numerical_stability)

        # Real function should be fairly compliant
        assert result["has_docstring"] is True
        assert result["has_type_hints"] is True

    def test_implementation_validation_with_numpy(self):
        """Test implementation validation with numpy computations."""

        def matrix_norm(arr):
            return np.linalg.norm(arr)

        test_cases = [
            (np.array([3, 4]), 5.0),
            (np.array([1, 0]), 1.0),
            (np.array([0, 0]), 0.0),
        ]

        result = validate_scientific_implementation(matrix_norm, test_cases)

        assert result["accuracy_score"] == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
