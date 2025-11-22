"""Test suite for scientific_dev module.

This test suite provides comprehensive validation for scientific development tools
including numerical stability, performance benchmarking, and best practices.
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
import scientific_dev


class TestNumericalStability:
    """Test numerical stability analysis."""

    def test_check_numerical_stability_stable_function(self):
        """Test stability check on numerically stable function."""
        def stable_function(x):
            return x * 2 + 1

        test_inputs = [0.1, 1.0, 10.0, 100.0, 1000.0]
        stability = scientific_dev.check_numerical_stability(stable_function, test_inputs)

        assert stability.stability_score > 0.8
        assert stability.function_name == "stable_function"
        assert len(stability.recommendations) == 0

    def test_check_numerical_stability_unstable_function(self):
        """Test stability check on numerically unstable function."""
        def unstable_function(x):
            return 1.0 / x if x != 0 else float('inf')

        test_inputs = [0.001, 0.01, 0.1, 0.0, 1.0, 10.0]
        stability = scientific_dev.check_numerical_stability(unstable_function, test_inputs)

        assert stability.stability_score < 1.0


class TestBenchmarking:
    """Test performance benchmarking functionality."""

    def test_benchmark_function_simple(self):
        """Test benchmarking of simple function."""
        def simple_function(x):
            return x ** 2

        test_inputs = [1.0, 2.0, 3.0]
        benchmark = scientific_dev.benchmark_function(simple_function, test_inputs, iterations=10)

        assert benchmark.function_name == "simple_function"
        assert benchmark.execution_time > 0
        assert benchmark.iterations == 10
        assert benchmark.parameters['input_count'] == 3

    def test_benchmark_function_with_memory(self):
        """Test benchmarking with memory usage tracking."""
        def memory_function(x):
            arr = np.zeros(1000)
            return np.sum(arr)

        test_inputs = [1.0, 2.0]
        benchmark = scientific_dev.benchmark_function(memory_function, test_inputs, iterations=5)

        # Memory measurement may not be available in all environments
        if benchmark.memory_usage is not None:
            assert benchmark.memory_usage >= 0  # Should be non-negative if available
        else:
            # If memory measurement is not available, check that other metrics are still working
            assert benchmark.execution_time > 0
            assert benchmark.iterations == 5


class TestScientificDocumentation:
    """Test scientific documentation generation."""

    def test_generate_scientific_documentation(self):
        """Test generation of scientific documentation."""
        def test_function(x: float, y: int = 1) -> float:
            """Test function for documentation generation.

            This function demonstrates the documentation pattern.

            Args:
                x: Input parameter
                y: Optional parameter

            Returns:
                Processed result
            """
            return x * y

        doc = scientific_dev.generate_scientific_documentation(test_function)

        assert "test_function" in doc
        assert "Args:" in doc
        assert "Returns:" in doc
        assert "x: Input parameter" in doc

    def test_generate_scientific_documentation_no_docstring(self):
        """Test documentation generation for function without docstring."""
        def undocumented_function(x):
            return x + 1

        doc = scientific_dev.generate_scientific_documentation(undocumented_function)

        assert "undocumented_function" in doc
        assert "No documentation available" in doc


class TestScientificValidation:
    """Test scientific implementation validation."""

    def test_validate_scientific_implementation_correct(self):
        """Test validation of correct scientific implementation."""
        def correct_function(x):
            return x * 2

        test_cases = [(1, 2), (2, 4), (3, 6)]
        validation = scientific_dev.validate_scientific_implementation(correct_function, test_cases)

        assert validation['accuracy_score'] == 1.0
        assert validation['passed_tests'] == 3
        assert validation['failed_tests'] == 0

    def test_validate_scientific_implementation_incorrect(self):
        """Test validation of incorrect scientific implementation."""
        def incorrect_function(x):
            return x * 3  # Wrong multiplier

        test_cases = [(1, 2), (2, 4), (3, 6)]
        validation = scientific_dev.validate_scientific_implementation(incorrect_function, test_cases)

        assert validation['accuracy_score'] == 0.0
        assert validation['passed_tests'] == 0
        assert validation['failed_tests'] == 3


class TestScientificBestPractices:
    """Test scientific best practices validation."""

    def test_validate_scientific_best_practices_good_module(self, tmp_path):
        """Test validation of module following best practices."""
        # Create a test module file
        module_file = tmp_path / "good_module.py"
        module_file.write_text('''
"""Good scientific module following best practices."""

def well_documented_function(x: float) -> float:
    """Well documented function with type hints.

    Args:
        x: Input parameter

    Returns:
        Processed result
    """
    try:
        return x * 2
    except Exception:
        raise ValueError("Invalid input")
''')

        # Import and validate
        import importlib.util
        spec = importlib.util.spec_from_file_location("good_module", module_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        validation = scientific_dev.validate_scientific_best_practices(module)

        assert validation['docstring_coverage'] == 1.0
        assert validation['type_hints_coverage'] == 1.0
        assert validation['error_handling'] == True
        assert validation['best_practices_score'] > 0.8

    def test_validate_scientific_best_practices_poor_module(self, tmp_path):
        """Test validation of module with poor practices."""
        module_file = tmp_path / "poor_module.py"
        module_file.write_text('''
def undocumented_function(x):
    return x + 1
''')

        import importlib.util
        spec = importlib.util.spec_from_file_location("poor_module", module_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        validation = scientific_dev.validate_scientific_best_practices(module)

        assert validation['docstring_coverage'] == 0.0
        assert validation['type_hints_coverage'] == 0.0
        assert len(validation['recommendations']) > 0


class TestScientificModuleTemplate:
    """Test scientific module template generation."""

    def test_create_scientific_module_template(self):
        """Test creation of scientific module template."""
        module_name = "optimization"

        template = scientific_dev.create_scientific_module_template(module_name)

        assert module_name in template
        assert "from __future__ import annotations" in template
        assert "def function1" in template
        assert "def function2" in template
        assert "Input validation" in template
        assert "Error handling" in template


class TestScientificWorkflowTemplate:
    """Test scientific workflow template generation."""

    def test_create_scientific_workflow_template(self):
        """Test creation of scientific workflow template."""
        workflow_name = "ml_training"

        template = scientific_dev.create_scientific_workflow_template(workflow_name)

        assert workflow_name in template
        assert "scientific research workflow" in template.lower()
        assert "setup_workflow_environment" in template
        assert "reproducibility_report" in template


class TestAPIDocumentation:
    """Test API documentation generation."""

    def test_generate_api_documentation(self):
        """Test generation of API documentation."""
        # Test with a module that has functions
        import scientific_dev

        doc = scientific_dev.generate_api_documentation(scientific_dev)

        assert "scientific_dev" in doc
        assert "## Functions" in doc or "## Classes" in doc


class TestResearchCompliance:
    """Test research compliance checking."""

    def test_check_research_compliance_good_function(self):
        """Test compliance check on well-documented function."""
        def well_documented_function(x: float) -> float:
            """Well documented function.

            Args:
                x: Input parameter

            Returns:
                Result

            Examples:
                >>> result = well_documented_function(5.0)
                10.0
            """
            return x * 2

        compliance = scientific_dev.check_research_compliance(well_documented_function)

        assert compliance['has_docstring'] == True
        assert compliance['has_type_hints'] == True
        assert compliance['has_examples'] == True
        assert compliance['compliance_score'] > 0.6

    def test_check_research_compliance_poor_function(self):
        """Test compliance check on poorly documented function."""
        def poor_function(x):
            return x + 1

        compliance = scientific_dev.check_research_compliance(poor_function)

        assert compliance['has_docstring'] == False
        assert compliance['has_type_hints'] == False
        assert compliance['compliance_score'] < 0.5
        assert len(compliance['recommendations']) > 0


class TestPerformanceReporting:
    """Test performance report generation."""

    def test_generate_performance_report(self):
        """Test generation of performance analysis report."""
        from scientific_dev import BenchmarkResult

        results = [
            BenchmarkResult("func1", 0.001, 10.5, 100, {}, "Fast function", "2024-01-01 10:00:00"),
            BenchmarkResult("func2", 0.010, 25.0, 100, {}, "Slow function", "2024-01-01 10:00:01"),
            BenchmarkResult("func3", 0.005, 15.2, 100, {}, "Medium function", "2024-01-01 10:00:02")
        ]

        report = scientific_dev.generate_performance_report(results)

        assert "Performance Analysis Report" in report
        assert "func1" in report
        assert "func2" in report
        assert "func3" in report
        assert "Average execution time" in report


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_check_numerical_stability_empty_inputs(self):
        """Test stability check with empty input list."""
        def dummy_function(x):
            return x

        stability = scientific_dev.check_numerical_stability(dummy_function, [])

        assert stability.stability_score == 0.0
        assert len(stability.recommendations) > 0

    def test_benchmark_function_exception_handling(self):
        """Test benchmarking with function that raises exceptions."""
        def failing_function(x):
            if x > 0:
                raise ValueError("Test error")
            return x

        test_inputs = [-1.0, 1.0]  # One should fail
        benchmark = scientific_dev.benchmark_function(failing_function, test_inputs, iterations=5)

        # Should still complete despite exceptions
        assert benchmark.function_name == "failing_function"
        assert benchmark.execution_time >= 0


if __name__ == "__main__":
    pytest.main([__file__])
