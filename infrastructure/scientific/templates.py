"""Scientific code templates and test suite generation.

Provides templates for new scientific modules and workflows:
- Module templates with best practices
- Test suite templates
- Workflow templates for reproducible research
"""
from __future__ import annotations


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
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Scientific computing imports
import numpy as np
import matplotlib.pyplot as plt

# Project imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from infrastructure.core.logging_utils import get_logger
from reproducibility import generate_reproducibility_report, save_reproducibility_report
from integrity import verify_output_integrity
from quality_checker import analyze_document_quality

# Set up logger using unified logging system
logger = get_logger(__name__)


def setup_workflow_environment():
    """Setup environment for reproducible scientific workflow."""
    # Set random seeds for reproducibility
    np.random.seed(42)

    # Logging is configured via unified system (get_logger above)
    # For file logging, use get_logger with log_file parameter if needed

    # Create output directories
    output_dirs = ['output', 'output/data', 'output/figures', 'output/reports']
    for dir_path in output_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def run_data_processing() -> Dict[str, Any]:
    """Run the main data processing workflow."""
    logger.info(f"Starting {workflow_name} workflow")

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

    logger.info(f"Completed {workflow_name} workflow")
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
        logger.error("Workflow validation failed")
        sys.exit(1)

    # Generate final report
    report_content = generate_workflow_report(results, reproducibility_report)
    with open('output/workflow_report.md', 'w') as f:
        f.write(report_content)

    # Save reproducibility information
    save_reproducibility_report(reproducibility_report, Path("output/reproducibility_report.json"))

    logger.info("Workflow completed successfully")


if __name__ == "__main__":
    main()
'''
    return template

