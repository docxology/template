"""Scientific package development utilities for research software.

This module provides utilities for scientific software development with
a modular architecture for focused functionality.

Modules:
- stability: Numerical stability checking
- benchmarking: Performance benchmarking
- documentation: Scientific documentation generation
- validation: Implementation validation and best practices
- templates: Module and workflow templates

All functions follow the thin orchestrator pattern and maintain
comprehensive test coverage requirements.
"""

# Import benchmarking functions
from infrastructure.scientific.benchmarking import (
    BenchmarkResult, benchmark_function, generate_performance_report)
# Import documentation functions
from infrastructure.scientific.documentation import (
    generate_api_documentation, generate_scientific_documentation)
# Import stability functions
# Import data classes
from infrastructure.scientific.stability import (StabilityTest,
                                                 check_numerical_stability)
# Import template functions
from infrastructure.scientific.templates import (
    create_scientific_module_template, create_scientific_test_suite,
    create_scientific_workflow_template)
# Import validation functions
from infrastructure.scientific.validation import (
    check_research_compliance, validate_scientific_best_practices,
    validate_scientific_implementation)

__all__ = [
    # Data classes
    "StabilityTest",
    "BenchmarkResult",
    # Stability
    "check_numerical_stability",
    # Benchmarking
    "benchmark_function",
    "generate_performance_report",
    # Documentation
    "generate_scientific_documentation",
    "generate_api_documentation",
    # Validation
    "validate_scientific_implementation",
    "validate_scientific_best_practices",
    "check_research_compliance",
    # Templates
    "create_scientific_module_template",
    "create_scientific_test_suite",
    "create_scientific_workflow_template",
]
