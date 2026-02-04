"""Test suite for infrastructure.scientific.documentation module.

Tests scientific documentation generation utilities including:
- Function documentation from signatures
- API documentation for modules
- Markdown-formatted output
- Parameter and return value extraction

All tests use real functions and modules with no mocks.
"""

import inspect
import sys
from pathlib import Path
from types import ModuleType

import numpy as np
import pytest

from infrastructure.scientific.documentation import (
    generate_api_documentation,
    generate_scientific_documentation,
)


class TestGenerateScientificDocumentation:
    """Test generate_scientific_documentation function."""

    def test_simple_function_documentation(self):
        """Test documentation for simple function."""

        def simple_function(x):
            """A simple function that doubles input."""
            return x * 2

        doc = generate_scientific_documentation(simple_function)

        assert "simple_function" in doc
        assert "A simple function that doubles input" in doc
        assert "## simple_function" in doc

    def test_function_with_type_hints(self):
        """Test documentation includes type hints."""

        def typed_function(x: float, y: int) -> float:
            """Function with type hints."""
            return x + y

        doc = generate_scientific_documentation(typed_function)

        assert "float" in doc
        assert "int" in doc
        assert "Parameters" in doc

    def test_function_with_defaults(self):
        """Test documentation includes default values."""

        def function_with_defaults(x: float, y: int = 10, z: str = "default") -> str:
            """Function with default parameters."""
            return f"{x}, {y}, {z}"

        doc = generate_scientific_documentation(function_with_defaults)

        assert "default:" in doc
        assert "10" in doc
        assert '"default"' in doc or "'default'" in doc

    def test_function_without_docstring(self):
        """Test documentation for function without docstring."""

        def undocumented(x):
            return x + 1

        doc = generate_scientific_documentation(undocumented)

        assert "undocumented" in doc
        assert "No documentation available" in doc

    def test_function_with_args_kwargs(self):
        """Test documentation for function with *args and **kwargs."""

        def variadic_function(x: float, *args, y: int = 5, **kwargs) -> tuple:
            """Function with variadic arguments.

            Args:
                x: First positional argument
                *args: Additional positional arguments
                y: Keyword-only argument
                **kwargs: Additional keyword arguments

            Returns:
                Tuple of all inputs
            """
            return (x, args, y, kwargs)

        doc = generate_scientific_documentation(variadic_function)

        assert "variadic_function" in doc
        assert "args" in doc
        assert "kwargs" in doc

    def test_function_with_detailed_docstring(self):
        """Test documentation extracts detailed docstring."""

        def detailed_function(x: float, y: float) -> float:
            """Calculate the weighted average.

            This function computes a weighted average of two values,
            where the first value has weight 0.7 and the second has
            weight 0.3.

            Args:
                x: First value (weight 0.7)
                y: Second value (weight 0.3)

            Returns:
                Weighted average of x and y

            Raises:
                ValueError: If inputs are not numeric

            Examples:
                >>> detailed_function(10.0, 20.0)
                13.0
            """
            return 0.7 * x + 0.3 * y

        doc = generate_scientific_documentation(detailed_function)

        assert "weighted average" in doc
        assert "Args:" in doc
        assert "Returns:" in doc

    def test_function_no_parameters(self):
        """Test documentation for function with no parameters."""

        def no_params() -> float:
            """Returns constant value."""
            return 42.0

        doc = generate_scientific_documentation(no_params)

        assert "no_params" in doc
        assert "constant value" in doc

    def test_function_many_parameters(self):
        """Test documentation with many parameters."""

        def many_params(a: int, b: int, c: int, d: int, e: int) -> int:
            """Sum of five integers."""
            return a + b + c + d + e

        doc = generate_scientific_documentation(many_params)

        for param in ["a", "b", "c", "d", "e"]:
            assert f"`{param}`" in doc

    def test_documentation_includes_usage_example(self):
        """Test documentation includes usage example section."""

        def example_function(x: int) -> int:
            """Example function."""
            return x

        doc = generate_scientific_documentation(example_function)

        assert "Usage Example" in doc
        assert "```python" in doc
        assert "example_function" in doc

    def test_documentation_includes_scientific_context(self):
        """Test documentation includes scientific context section."""

        def scientific_function(x: float) -> float:
            """Applies scientific transformation."""
            return np.log(x) if x > 0 else 0

        doc = generate_scientific_documentation(scientific_function)

        assert "Scientific Context" in doc

    def test_lambda_function_documentation(self):
        """Test documentation for lambda function."""
        square = lambda x: x * x

        doc = generate_scientific_documentation(square)

        assert "<lambda>" in doc

    def test_class_method_as_function(self):
        """Test documentation for a method extracted as function."""

        class Calculator:
            def add(self, x: float, y: float) -> float:
                """Add two numbers."""
                return x + y

        calc = Calculator()
        doc = generate_scientific_documentation(calc.add)

        assert "add" in doc


class TestGenerateAPIDocumentation:
    """Test generate_api_documentation function."""

    def test_api_documentation_for_real_module(self):
        """Test API documentation for actual scientific module."""
        import infrastructure.scientific.benchmarking as benchmarking_module

        doc = generate_api_documentation(benchmarking_module)

        assert "benchmarking API Documentation" in doc
        assert "## Functions" in doc or "## Classes" in doc

    def test_api_documentation_includes_functions(self):
        """Test API documentation lists module functions."""
        import infrastructure.scientific.stability as stability_module

        doc = generate_api_documentation(stability_module)

        assert "check_numerical_stability" in doc
        assert "**Signature**" in doc

    def test_api_documentation_includes_classes(self):
        """Test API documentation lists module classes."""
        import infrastructure.scientific.benchmarking as benchmarking_module

        doc = generate_api_documentation(benchmarking_module)

        assert "## Classes" in doc
        assert "BenchmarkResult" in doc

    def test_api_documentation_for_custom_module(self, tmp_path):
        """Test API documentation for dynamically created module."""
        # Create a test module file
        module_file = tmp_path / "custom_module.py"
        module_file.write_text('''
"""Custom scientific module for testing."""

def public_function(x: float) -> float:
    """A public function that squares input."""
    return x * x

def another_public(y: int, z: int = 5) -> int:
    """Another public function."""
    return y + z

class PublicClass:
    """A public class for testing."""
    pass

def _private_function(x):
    """This should not appear in docs."""
    return x
''')

        # Import the module dynamically
        import importlib.util
        spec = importlib.util.spec_from_file_location("custom_module", module_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        doc = generate_api_documentation(module)

        assert "custom_module API Documentation" in doc
        assert "public_function" in doc
        assert "another_public" in doc
        assert "PublicClass" in doc
        assert "_private_function" not in doc  # Private should be excluded

    def test_api_documentation_empty_module(self, tmp_path):
        """Test API documentation for module with no public members."""
        module_file = tmp_path / "empty_module.py"
        module_file.write_text('''
"""Empty module with only private members."""

def _private1(x):
    return x

def _private2(x):
    return x * 2
''')

        import importlib.util
        spec = importlib.util.spec_from_file_location("empty_module", module_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        doc = generate_api_documentation(module)

        # Should still have header but no function/class sections with content
        assert "empty_module API Documentation" in doc

    def test_api_documentation_function_descriptions(self, tmp_path):
        """Test API documentation includes function descriptions."""
        module_file = tmp_path / "described_module.py"
        module_file.write_text('''
"""Module with detailed descriptions."""

def calculate_mean(values: list) -> float:
    """Calculate the arithmetic mean of a list of values.

    This function computes the sum of all values and divides
    by the count to get the arithmetic mean.

    Args:
        values: List of numeric values

    Returns:
        The arithmetic mean
    """
    return sum(values) / len(values)
''')

        import importlib.util
        spec = importlib.util.spec_from_file_location("described_module", module_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        doc = generate_api_documentation(module)

        assert "calculate_mean" in doc
        assert "arithmetic mean" in doc
        assert "**Description**" in doc

    def test_api_documentation_class_descriptions(self, tmp_path):
        """Test API documentation includes class descriptions."""
        module_file = tmp_path / "class_module.py"
        module_file.write_text('''
"""Module with classes."""

class DataProcessor:
    """Process scientific data efficiently.

    This class provides methods for processing and analyzing
    scientific datasets with configurable parameters.
    """
    pass

class ResultContainer:
    """Container for computation results."""
    pass
''')

        import importlib.util
        spec = importlib.util.spec_from_file_location("class_module", module_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        doc = generate_api_documentation(module)

        assert "DataProcessor" in doc
        assert "ResultContainer" in doc
        assert "Process scientific data" in doc

    def test_api_documentation_signature_format(self):
        """Test API documentation shows proper signature format."""
        import infrastructure.scientific.validation as validation_module

        doc = generate_api_documentation(validation_module)

        # Should contain signature in backticks
        assert "**Signature**:" in doc
        assert "`" in doc

    def test_api_documentation_multiple_modules(self):
        """Test API documentation works for multiple modules."""
        import infrastructure.scientific.benchmarking as bench
        import infrastructure.scientific.stability as stab
        import infrastructure.scientific.templates as templ

        for module in [bench, stab, templ]:
            doc = generate_api_documentation(module)
            assert "API Documentation" in doc
            assert module.__name__ in doc


class TestDocumentationEdgeCases:
    """Test edge cases in documentation generation."""

    def test_function_with_complex_annotations(self):
        """Test documentation with complex type annotations."""
        from typing import Dict, List, Optional, Tuple, Union

        def complex_types(
            data: List[float],
            mapping: Dict[str, int],
            optional_val: Optional[float] = None,
        ) -> Tuple[List[float], int]:
            """Function with complex type annotations."""
            return (data, len(mapping))

        doc = generate_scientific_documentation(complex_types)

        assert "complex_types" in doc
        assert "data" in doc

    def test_function_with_multiline_docstring(self):
        """Test documentation preserves multiline docstring."""

        def multiline_doc(x: float) -> float:
            """First line of documentation.

            This is a more detailed explanation that spans
            multiple lines and provides additional context
            about what the function does.

            The function performs a simple calculation but
            this docstring is intentionally verbose.
            """
            return x * 2

        doc = generate_scientific_documentation(multiline_doc)

        assert "First line of documentation" in doc
        assert "detailed explanation" in doc

    def test_nested_function_documentation(self):
        """Test documentation for nested function."""

        def outer():
            def inner(x: int) -> int:
                """Inner function docstring."""
                return x + 1
            return inner

        inner_func = outer()
        doc = generate_scientific_documentation(inner_func)

        assert "inner" in doc
        assert "Inner function docstring" in doc


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
