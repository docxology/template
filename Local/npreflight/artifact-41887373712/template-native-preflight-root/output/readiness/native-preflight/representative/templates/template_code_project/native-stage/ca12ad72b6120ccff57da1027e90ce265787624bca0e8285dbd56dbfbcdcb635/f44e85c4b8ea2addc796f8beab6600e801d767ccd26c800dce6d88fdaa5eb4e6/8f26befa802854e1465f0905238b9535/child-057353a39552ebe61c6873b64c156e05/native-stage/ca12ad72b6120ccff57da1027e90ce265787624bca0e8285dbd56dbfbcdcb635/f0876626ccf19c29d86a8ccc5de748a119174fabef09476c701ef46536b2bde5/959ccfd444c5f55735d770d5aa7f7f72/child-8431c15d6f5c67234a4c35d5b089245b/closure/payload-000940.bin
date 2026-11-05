"""Scientific package development utilities for research software.

This module provides utilities for scientific software development with
a modular architecture for focused functionality.

Modules:
- stability: Numerical stability checking
- benchmarking: Performance benchmarking
- confirmation: Independent improvement confirmation (confirm_improvement)

All functions follow the thin orchestrator pattern and maintain
comprehensive test coverage requirements.

Exemplar-support tier: this is a Layer-1 module by location, but it is
imported only by its scientific exemplar(s), not reached generically across
infrastructure — see AGENTS.md.
"""

# Import benchmarking functions
from infrastructure.scientific.benchmarking import (
    BenchmarkResult,
    benchmark_function,
    format_benchmark_report,
)

# Import confirmation functions
from infrastructure.scientific.confirmation import Confirmation, confirm_improvement

# Import stability functions
# Import data classes
from infrastructure.scientific.stability import StabilityTest, check_numerical_stability

__all__ = [
    # Data classes
    "StabilityTest",
    "BenchmarkResult",
    "Confirmation",
    # Stability
    "check_numerical_stability",
    # Confirmation
    "confirm_improvement",
    # Benchmarking
    "benchmark_function",
    "format_benchmark_report",
]
