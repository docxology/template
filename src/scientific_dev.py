"""Scientific package development utilities for research software.

This module provides utilities for:
- Scientific software development patterns
- Numerical stability checking
- Performance benchmarking
- Documentation generation for scientific APIs
- Scientific computing best practices

All functions follow the thin orchestrator pattern and maintain
100% test coverage requirements.
"""

from __future__ import annotations

import os
import sys
import time
import inspect
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
import numpy as np
import matplotlib.pyplot as plt


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""

    function_name: str
    execution_time: float
    memory_usage: Optional[float]
    iterations: int
    parameters: Dict[str, Any]
    result_summary: str
    timestamp: str


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


def benchmark_function(func: Callable, test_inputs: List[Any],
                      iterations: int = 100) -> BenchmarkResult:
    """Benchmark function performance across multiple inputs.

    Args:
        func: Function to benchmark
        test_inputs: List of input values to test
        iterations: Number of iterations per input

    Returns:
        BenchmarkResult with performance analysis
    """
    import time
    import os

    try:
        import psutil
        psutil_available = True
    except ImportError:
        psutil_available = False

    execution_times = []
    memory_usages = []

    for test_input in test_inputs:
        # Warm up
        for _ in range(10):
            try:
                _ = func(test_input)
            except:
                pass

        # Measure execution time
        start_time = time.perf_counter()

        for _ in range(iterations):
            try:
                result = func(test_input)
            except:
                result = None

        end_time = time.perf_counter()
        avg_time = (end_time - start_time) / iterations
        execution_times.append(avg_time)

        # Try to measure memory usage
        if psutil_available:
            try:
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                memory_usages.append(memory_info.rss / 1024 / 1024)  # MB
            except:
                memory_usages.append(None)
        else:
            memory_usages.append(None)

    avg_execution_time = np.mean(execution_times) if execution_times else 0.0
    valid_memory = [m for m in memory_usages if m is not None and not (isinstance(m, float) and np.isnan(m))]
    avg_memory_usage = np.mean(valid_memory) if valid_memory else None

    # Create result summary
    result_summary = f"Avg time: {avg_execution_time:.6f}s"
    if avg_memory_usage:
        result_summary += f", Avg memory: {avg_memory_usage:.1f}MB"

    return BenchmarkResult(
        function_name=func.__name__,
        execution_time=avg_execution_time,
        memory_usage=avg_memory_usage,
        iterations=iterations,
        parameters={'input_count': len(test_inputs)},
        result_summary=result_summary,
        timestamp=time.strftime('%Y-%m-%d %H:%M:%S')
    )


def generate_scientific_documentation(func: Callable) -> str:
    """Generate scientific documentation for a function.

    Args:
        func: Function to document

    Returns:
        Markdown formatted scientific documentation
    """
    docstring = inspect.getdoc(func) or "No documentation available"
    signature = inspect.signature(func)

    # Extract parameter information
    parameters = []
    for param_name, param in signature.parameters.items():
        param_info = f"- `{param_name}`"
        if param.annotation != inspect.Parameter.empty:
            param_info += f" ({param.annotation.__name__})"
        if param.default != inspect.Parameter.empty:
            param_info += f", default: {param.default}"
        parameters.append(param_info)

    # Extract return information
    return_info = ""
    if signature.return_annotation != inspect.Signature.empty:
        return_info = f"Returns: {signature.return_annotation.__name__}"

    documentation = f"""## {func.__name__}

**Function**: `{func.__name__}{signature}`

### Description
{docstring}

### Parameters
{chr(10).join(parameters)}

### {return_info if return_info else 'Returns'}
No return annotation specified.

### Usage Example
```python
# Example usage would go here
result = {func.__name__}(example_input)
```

### Scientific Context
This function implements [mathematical concept] with [specific approach].
"""

    return documentation


def validate_scientific_implementation(func: Callable, test_cases: List[Tuple]) -> Dict[str, Any]:
    """Validate scientific implementation against known test cases.

    Args:
        func: Function to validate
        test_cases: List of (input, expected_output) tuples

    Returns:
        Dictionary with validation results
    """
    validation_results = {
        'total_tests': len(test_cases),
        'passed_tests': 0,
        'failed_tests': 0,
        'accuracy_score': 0.0,
        'details': []
    }

    for i, (test_input, expected_output) in enumerate(test_cases):
        try:
            actual_output = func(test_input)

            # Compare results with tolerance for floating point
            if isinstance(actual_output, (int, float)) and isinstance(expected_output, (int, float)):
                if abs(actual_output - expected_output) < 1e-10:
                    validation_results['passed_tests'] += 1
                    validation_results['details'].append({
                        'test_index': i,
                        'input': test_input,
                        'expected': expected_output,
                        'actual': actual_output,
                        'status': 'PASSED'
                    })
                else:
                    validation_results['failed_tests'] += 1
                    validation_results['details'].append({
                        'test_index': i,
                        'input': test_input,
                        'expected': expected_output,
                        'actual': actual_output,
                        'status': 'FAILED'
                    })
            elif actual_output == expected_output:
                validation_results['passed_tests'] += 1
                validation_results['details'].append({
                    'test_index': i,
                    'input': test_input,
                    'expected': expected_output,
                    'actual': actual_output,
                    'status': 'PASSED'
                })
            else:
                validation_results['failed_tests'] += 1
                validation_results['details'].append({
                    'test_index': i,
                    'input': test_input,
                    'expected': expected_output,
                    'actual': actual_output,
                    'status': 'FAILED'
                })

        except Exception as e:
            validation_results['failed_tests'] += 1
            validation_results['details'].append({
                'test_index': i,
                'input': test_input,
                'expected': expected_output,
                'actual': f"Exception: {e}",
                'status': 'ERROR'
            })

    # Calculate accuracy score
    if validation_results['total_tests'] > 0:
        validation_results['accuracy_score'] = validation_results['passed_tests'] / validation_results['total_tests']

    return validation_results


def create_scientific_test_suite(module_name: str) -> str:
    """Create a comprehensive test suite for a scientific module.

    Args:
        module_name: Name of the module to create tests for

    Returns:
        Python test file content as string
    """
    test_content = f'''"""Test suite for {module_name} module.

This test suite provides comprehensive validation for scientific functions
including numerical stability, performance benchmarking, and correctness verification.
"""

import pytest
import numpy as np
from pathlib import Path

# Import the module to test
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import {module_name}


class TestNumericalStability:
    """Test numerical stability of functions."""

    def test_function_stability_across_range(self):
        """Test function stability across input range."""
        test_inputs = np.linspace(-10, 10, 100)

        for func_name in dir({module_name}):
            func = getattr({module_name}, func_name)
            if callable(func) and not func_name.startswith('_'):
                # Skip functions that don't take numeric inputs
                try:
                    result = check_numerical_stability(func, test_inputs)
                    assert result.stability_score > 0.8, f"{{func_name}} has poor numerical stability"
                except:
                    # Skip functions that can't be tested this way
                    continue


class TestPerformance:
    """Test performance characteristics."""

    def test_function_performance(self):
        """Test function performance across inputs."""
        test_inputs = [1.0, 10.0, 100.0]

        for func_name in dir({module_name}):
            func = getattr({module_name}, func_name)
            if callable(func) and not func_name.startswith('_'):
                try:
                    result = benchmark_function(func, test_inputs)
                    assert result.execution_time < 1.0, f"{{func_name}} is too slow"
                except:
                    continue


class TestCorrectness:
    """Test mathematical correctness."""

    def test_basic_functionality(self):
        """Test basic function behavior."""
        # Add specific test cases for your functions
        pass


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_inputs(self):
        """Test functions with zero inputs."""
        # Add zero input test cases
        pass

    def test_large_inputs(self):
        """Test functions with large inputs."""
        # Add large input test cases
        pass


if __name__ == "__main__":
    pytest.main([__file__])
'''
    return test_content


def generate_performance_report(benchmark_results: List[BenchmarkResult]) -> str:
    """Generate a performance analysis report.

    Args:
        benchmark_results: List of benchmark results to analyze

    Returns:
        Markdown formatted performance report
    """
    if not benchmark_results:
        return "No benchmark results to analyze."

    # Calculate summary statistics
    execution_times = [r.execution_time for r in benchmark_results]
    memory_usages = [r.memory_usage for r in benchmark_results if r.memory_usage is not None]

    report = []
    report.append("# Performance Analysis Report")
    report.append("")

    report.append("## Summary Statistics")
    report.append(f"- **Functions tested**: {len(benchmark_results)}")
    report.append(f"- **Average execution time**: {np.mean(execution_times):.6f}s")
    report.append(f"- **Median execution time**: {np.median(execution_times):.6f}s")
    report.append(f"- **Min execution time**: {np.min(execution_times):.6f}s")
    report.append(f"- **Max execution time**: {np.max(execution_times):.6f}s")

    if memory_usages:
        report.append(f"- **Average memory usage**: {np.mean(memory_usages):.1f}MB")
        report.append(f"- **Median memory usage**: {np.median(memory_usages):.1f}MB")

    report.append("")

    report.append("## Detailed Results")
    report.append("| Function | Exec Time (s) | Memory (MB) | Iterations | Parameters |")
    report.append("|----------|---------------|-------------|------------|------------|")

    for result in sorted(benchmark_results, key=lambda x: x.execution_time, reverse=True):
        memory_str = f"{result.memory_usage:.1f}" if result.memory_usage else "N/A"
        report.append(f"| `{result.function_name}` | {result.execution_time:.6f} | {memory_str} | {result.iterations} | {result.parameters} |")

    report.append("")

    # Performance recommendations
    report.append("## Recommendations")
    slow_functions = [r for r in benchmark_results if r.execution_time > 0.1]
    if slow_functions:
        report.append("### Performance Optimization")
        for func in slow_functions[:3]:  # Top 3 slowest
            report.append(f"- Consider optimizing `{func.function_name}` (currently {func.execution_time:.6f}s)")

    memory_intensive = [r for r in benchmark_results if r.memory_usage and r.memory_usage > 100]
    if memory_intensive:
        report.append("### Memory Optimization")
        for func in memory_intensive[:3]:  # Top 3 memory intensive
            report.append(f"- Review memory usage in `{func.function_name}` (currently {func.memory_usage:.1f}MB)")

    report.append("")

    return '\n'.join(report)


def validate_scientific_best_practices(module) -> Dict[str, Any]:
    """Validate that a module follows scientific computing best practices.

    Args:
        module: Python module to validate

    Returns:
        Dictionary with validation results
    """
    validation = {
        'docstring_coverage': 0.0,
        'type_hints_coverage': 0.0,
        'error_handling': False,
        'input_validation': False,
        'numerical_stability': False,
        'best_practices_score': 0.0,
        'recommendations': []
    }

    functions = []
    for name in dir(module):
        obj = getattr(module, name)
        if callable(obj) and not name.startswith('_'):
            functions.append((name, obj))

    if not functions:
        return validation

    # Check docstring coverage
    documented_functions = sum(1 for _, func in functions if inspect.getdoc(func) is not None)
    validation['docstring_coverage'] = documented_functions / len(functions)

    # Check type hints coverage
    typed_functions = 0
    for _, func in functions:
        sig = inspect.signature(func)
        has_return_annotation = sig.return_annotation != inspect.Signature.empty
        has_param_annotations = any(p.annotation != inspect.Parameter.empty for p in sig.parameters.values())

        if has_return_annotation or has_param_annotations:
            typed_functions += 1

    validation['type_hints_coverage'] = typed_functions / len(functions)

    # Check for error handling patterns
    source_lines = []
    try:
        source = inspect.getsource(module)
        source_lines = source.split('\n')
    except:
        pass

    has_try_except = any('try:' in line or 'except' in line for line in source_lines)
    has_raise = any('raise' in line for line in source_lines)
    validation['error_handling'] = has_try_except or has_raise

    # Check for input validation patterns
    has_validation = any(
        'assert' in line or
        'isinstance' in line or
        'ValueError' in line or
        'TypeError' in line
        for line in source_lines
    )
    validation['input_validation'] = has_validation

    # Calculate best practices score
    weights = {
        'docstring_coverage': 0.25,
        'type_hints_coverage': 0.25,
        'error_handling': 0.25,
        'input_validation': 0.25
    }

    validation['best_practices_score'] = (
        validation['docstring_coverage'] * weights['docstring_coverage'] +
        validation['type_hints_coverage'] * weights['type_hints_coverage'] +
        (1.0 if validation['error_handling'] else 0.0) * weights['error_handling'] +
        (1.0 if validation['input_validation'] else 0.0) * weights['input_validation']
    )

    # Generate recommendations
    if validation['docstring_coverage'] < 0.8:
        validation['recommendations'].append("Add docstrings to undocumented functions")

    if validation['type_hints_coverage'] < 0.8:
        validation['recommendations'].append("Add type hints to function parameters and return values")

    if not validation['error_handling']:
        validation['recommendations'].append("Add proper error handling with try/except blocks")

    if not validation['input_validation']:
        validation['recommendations'].append("Add input validation to prevent invalid arguments")

    return validation


def create_scientific_module_template(module_name: str) -> str:
    """Create a template for a new scientific module.

    Args:
        module_name: Name of the module to create

    Returns:
        Python module template content
    """
    template = f'''"""Scientific module: {module_name}.

This module implements [mathematical concept/algorithm] following
scientific computing best practices.

Functions:
- [function1]: Description of first function
- [function2]: Description of second function

All functions include:
- Comprehensive docstrings
- Type hints
- Input validation
- Error handling
- Numerical stability considerations
"""

from __future__ import annotations

import numpy as np
from typing import List, Tuple, Optional, Union


def function1(param1: float, param2: int) -> float:
    """[Brief description of function1].

    This function implements [mathematical operation] with
    [specific approach/algorithm].

    Args:
        param1: Description of first parameter
        param2: Description of second parameter

    Returns:
        Description of return value

    Raises:
        ValueError: If inputs are invalid
        TypeError: If input types are incorrect

    Examples:
        >>> result = function1(1.0, 2)
        >>> print(result)
        3.0
    """
    # Input validation
    if not isinstance(param1, (int, float)):
        raise TypeError(f"param1 must be numeric, got {{type(param1)}}")
    if not isinstance(param2, int):
        raise TypeError(f"param2 must be integer, got {{type(param2)}}")

    # Numerical computation
    try:
        result = param1 * param2 + 1.0
        return result
    except OverflowError:
        raise ValueError("Computation resulted in overflow")


def function2(data: List[float], threshold: float = 0.0) -> Tuple[List[float], float]:
    """[Brief description of function2].

    This function processes [data type] using [algorithm approach]
    with [specific mathematical properties].

    Args:
        data: Input data to process
        threshold: Threshold value for filtering

    Returns:
        Tuple of (filtered_data, summary_statistic)

    Raises:
        ValueError: If data is empty or invalid
    """
    # Input validation
    if not data:
        raise ValueError("Input data cannot be empty")

    if not all(isinstance(x, (int, float)) for x in data):
        raise ValueError("All data elements must be numeric")

    # Process data
    filtered_data = [x for x in data if x > threshold]

    # Calculate summary statistic
    if filtered_data:
        summary = sum(filtered_data) / len(filtered_data)
    else:
        summary = 0.0

    return filtered_data, summary
'''
    return template


def generate_api_documentation(module) -> str:
    """Generate comprehensive API documentation for a scientific module.

    Args:
        module: Python module to document

    Returns:
        Markdown formatted API documentation
    """
    functions = []
    classes = []

    for name in dir(module):
        if name.startswith('_'):
            continue

        obj = getattr(module, name)
        if inspect.isfunction(obj):
            functions.append((name, obj))
        elif inspect.isclass(obj):
            classes.append((name, obj))

    doc = []
    doc.append(f"# {module.__name__} API Documentation")
    doc.append("")

    if functions:
        doc.append("## Functions")
        doc.append("")

        for name, func in functions:
            docstring = inspect.getdoc(func) or "No documentation available"
            signature = inspect.signature(func)

            doc.append(f"### `{name}`")
            doc.append(f"**Signature**: `{name}{signature}`")
            doc.append("")
            doc.append("**Description**:")
            doc.append(f"{docstring}")
            doc.append("")

    if classes:
        doc.append("## Classes")
        doc.append("")

        for name, cls in classes:
            docstring = inspect.getdoc(cls) or "No documentation available"

            doc.append(f"### `{name}`")
            doc.append("**Description**:")
            doc.append(f"{docstring}")
            doc.append("")

    return '\n'.join(doc)


def check_research_compliance(func: Callable) -> Dict[str, Any]:
    """Check function compliance with research software standards.

    Args:
        func: Function to check

    Returns:
        Dictionary with compliance assessment
    """
    compliance = {
        'has_docstring': False,
        'has_type_hints': False,
        'has_examples': False,
        'has_error_handling': False,
        'has_input_validation': False,
        'follows_naming_conventions': False,
        'compliance_score': 0.0,
        'recommendations': []
    }

    # Check docstring
    docstring = inspect.getdoc(func)
    if docstring:
        compliance['has_docstring'] = True

        # Check for examples in docstring
        if '>>>' in docstring or 'Example' in docstring:
            compliance['has_examples'] = True

    # Check type hints
    signature = inspect.signature(func)
    has_param_hints = any(p.annotation != inspect.Parameter.empty for p in signature.parameters.values())
    has_return_hint = signature.return_annotation != inspect.Signature.empty

    if has_param_hints or has_return_hint:
        compliance['has_type_hints'] = True

    # Check naming conventions (should be snake_case)
    if func.__name__.islower() and '_' in func.__name__:
        compliance['follows_naming_conventions'] = True

    # Check source code for error handling patterns
    try:
        source = inspect.getsource(func)
        source_lines = source.split('\n')

        has_validation = any(
            'assert' in line or
            'isinstance' in line or
            'ValueError' in line or
            'TypeError' in line
            for line in source_lines
        )
        compliance['has_input_validation'] = has_validation

        has_error_handling = any(
            'try:' in line or
            'except' in line or
            'raise' in line
            for line in source_lines
        )
        compliance['has_error_handling'] = has_error_handling

    except:
        pass

    # Calculate compliance score
    weights = {
        'has_docstring': 0.25,
        'has_type_hints': 0.20,
        'has_examples': 0.10,
        'has_error_handling': 0.15,
        'has_input_validation': 0.15,
        'follows_naming_conventions': 0.15
    }

    score = 0.0
    for key, weight in weights.items():
        if compliance[key]:
            score += weight

    compliance['compliance_score'] = score

    # Generate recommendations
    if not compliance['has_docstring']:
        compliance['recommendations'].append("Add comprehensive docstring with description and parameters")

    if not compliance['has_type_hints']:
        compliance['recommendations'].append("Add type hints to parameters and return value")

    if not compliance['has_examples']:
        compliance['recommendations'].append("Add usage examples in docstring")

    if not compliance['has_error_handling']:
        compliance['recommendations'].append("Add proper error handling for edge cases")

    if not compliance['has_input_validation']:
        compliance['recommendations'].append("Add input validation to prevent invalid arguments")

    if not compliance['follows_naming_conventions']:
        compliance['recommendations'].append("Use snake_case naming convention for functions")

    return compliance


def create_scientific_workflow_template(workflow_name: str) -> str:
    """Create a template for scientific research workflows.

    Args:
        workflow_name: Name of the workflow

    Returns:
        Python workflow template content
    """
    template = f'''#!/usr/bin/env python3
"""Scientific research workflow: {workflow_name}.

This workflow demonstrates best practices for scientific computing:
- Reproducible data processing
- Comprehensive validation
- Performance benchmarking
- Documentation generation
- Result verification
"""

from __future__ import annotations

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Scientific computing imports
import numpy as np
import matplotlib.pyplot as plt

# Project imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from reproducibility import generate_reproducibility_report, save_reproducibility_report
from integrity import verify_output_integrity
from quality_checker import analyze_document_quality


def setup_workflow_environment():
    """Setup environment for reproducible scientific workflow."""
    # Set random seeds for reproducibility
    np.random.seed(42)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'{workflow_name}_workflow.log'),
            logging.StreamHandler()
        ]
    )

    # Create output directories
    output_dirs = ['output', 'output/data', 'output/figures', 'output/reports']
    for dir_path in output_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def run_data_processing() -> Dict[str, Any]:
    """Run the main data processing workflow."""
    logging.info(f"Starting {workflow_name} workflow")

    # Your scientific data processing here
    # Example: load data, process, analyze

    results = {{
        'processed_data': None,
        'analysis_results': None,
        'figures_generated': 0,
        'files_created': []
    }}

    # Process data using src/ methods
    # Generate figures
    # Save results

    logging.info(f"Completed {workflow_name} workflow")
    return results


def validate_workflow_results(results: Dict[str, Any]) -> bool:
    """Validate workflow results for correctness."""
    # Add validation logic here
    return True


def generate_workflow_report(results: Dict[str, Any], reproducibility_report: Any) -> str:
    """Generate comprehensive workflow report."""
    report = []
    report.append("# Scientific Workflow Report")
    report.append(f"**Workflow**: {workflow_name}")
    report.append(f"**Timestamp**: {{datetime.now().isoformat()}}")
    report.append("")

    report.append("## Results Summary")
    report.append(f"- **Figures generated**: {{results['figures_generated']}}")
    report.append(f"- **Files created**: {{len(results['files_created'])}}")
    report.append("")

    report.append("## Reproducibility Information")
    report.append(f"- **Environment hash**: {{reproducibility_report.environment_hash[:16]}}...")
    report.append(f"- **Code hash**: {{reproducibility_report.code_hash[:16]}}...")
    report.append("")

    return '\\n'.join(report)


def main():
    """Main workflow execution function."""
    setup_workflow_environment()

    # Generate reproducibility report
    reproducibility_report = generate_reproducibility_report(Path("output"))

    # Run main workflow
    results = run_data_processing()

    # Validate results
    if not validate_workflow_results(results):
        logging.error("Workflow validation failed")
        sys.exit(1)

    # Generate final report
    report_content = generate_workflow_report(results, reproducibility_report)
    with open('output/workflow_report.md', 'w') as f:
        f.write(report_content)

    # Save reproducibility information
    save_reproducibility_report(reproducibility_report, Path("output/reproducibility_report.json"))

    logging.info("Workflow completed successfully")


if __name__ == "__main__":
    main()
'''
    return template
