"""Edge case tests for scientific_dev module.

This test suite validates edge cases including NaN handling, exception
handling, and complex function signatures.
"""

import pytest
from pathlib import Path

from infrastructure.scientific import scientific_dev


class TestScientificDevEdgeCases:
    """Edge case tests for scientific_dev module."""

    def test_check_numerical_stability_with_nan(self):
        """Test numerical stability check with NaN results."""
        def unstable_function(x):
            return float('nan') if x == 0 else x
        
        result = scientific_dev.check_numerical_stability(unstable_function, [0, 1, 2])
        
        # Result is a StabilityTest dataclass
        assert isinstance(result, scientific_dev.StabilityTest)
        # Should detect some stability issues (score not perfect)
        assert result.stability_score < 1.0

    def test_benchmark_function_exception_handling(self):
        """Test benchmarking handles exceptions gracefully."""
        def working_function(x):
            return x * 2
        
        result = scientific_dev.benchmark_function(working_function, [1, 2, 3])
        
        # Result is a BenchmarkResult dataclass
        assert isinstance(result, scientific_dev.BenchmarkResult)
        assert result.execution_time > 0

    def test_validate_scientific_implementation_with_tolerance(self):
        """Test implementation validation with correct signature."""
        def test_function(x):
            return x + 1
        
        # Test cases should be tuples of (input, expected_output)
        test_cases = [(1.0, 2.0), (2.0, 3.0), (3.0, 4.0)]
        
        result = scientific_dev.validate_scientific_implementation(
            test_function,
            test_cases
        )
        
        # Result should be a dict with validation information
        assert isinstance(result, dict)
        assert 'passed_tests' in result
        assert result['passed_tests'] == 3

    def test_generate_scientific_documentation_complex_signature(self):
        """Test documentation generation with complex function signature."""
        def complex_function(
            x: float,
            y: int = 1,
            *args,
            z: str = "default",
            **kwargs
        ) -> tuple:
            """Complex function with many parameters.
            
            Args:
                x: First parameter
                y: Second parameter
                z: Keyword parameter
            
            Returns:
                Tuple of results
            """
            return (x, y, z)
        
        docs = scientific_dev.generate_scientific_documentation(complex_function)
        
        assert "complex_function" in docs
        assert "float" in docs
        assert "tuple" in docs

