"""Scientific module - Scientific development utilities.

This module contains utilities for scientific computing, numerical stability
checking, performance benchmarking, and research software development.

Modules:
    scientific_dev: Scientific computing best practices and tools
"""

from .scientific_dev import (
    check_numerical_stability,
    benchmark_function,
    generate_scientific_documentation,
    validate_scientific_implementation,
    validate_scientific_best_practices,
)

__all__ = [
    "check_numerical_stability",
    "benchmark_function",
    "generate_scientific_documentation",
    "validate_scientific_implementation",
    "validate_scientific_best_practices",
]

