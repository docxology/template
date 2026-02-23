"""Analysis modules for the Active Inference Meta-Pragmatic project.

Contains data generation, statistical analysis, and validation tools.
"""

from .data_generator import (
    DataGenerator,
    demonstrate_data_generation,
    generate_synthetic_data,
    generate_time_series,
)
from .statistical_analysis import (
    StatisticalAnalyzer,
    anova_test,
    calculate_confidence_interval,
    calculate_correlation,
    calculate_descriptive_stats,
    demonstrate_statistical_analysis,
)
from .validation import (
    ValidationFramework,
    demonstrate_validation_framework,
)

__all__ = [
    "DataGenerator",
    "generate_time_series",
    "generate_synthetic_data",
    "demonstrate_data_generation",
    "StatisticalAnalyzer",
    "calculate_descriptive_stats",
    "calculate_correlation",
    "calculate_confidence_interval",
    "anova_test",
    "demonstrate_statistical_analysis",
    "ValidationFramework",
    "demonstrate_validation_framework",
]
