"""Active Inference Meta-Pragmatic Framework.

This package implements theoretical concepts for understanding Active Inference
as a meta-(pragmatic/epistemic) method, including the 2x2 matrix framework
of Data/Meta-Data x Cognitive/Meta-Cognitive processing.

Subpackages:
- core: Active Inference, Free Energy Principle, Generative Models
- framework: Quadrant Framework, Meta-Cognition, Modeler Perspective, Cognitive Security
- analysis: Data Generation, Statistical Analysis, Validation
- visualization: Publication-quality plotting and figure generation
- utils: Logging, exceptions, figure management, markdown integration
"""

__version__ = "1.0.0"
__author__ = "Daniel Friedman"
__description__ = "Active Inference as a Meta-(Pragmatic/Epistemic) Method"

from .core import (
    ActiveInferenceFramework,
    FreeEnergyPrinciple,
    GenerativeModel,
    create_simple_generative_model,
    define_what_is_a_thing,
    demonstrate_active_inference_concepts,
    demonstrate_fep_concepts,
    demonstrate_generative_model_concepts,
)
from .framework import (
    CognitiveSecurityAnalyzer,
    MetaCognitiveSystem,
    ModelerPerspective,
    QuadrantFramework,
    demonstrate_meta_cognitive_processes,
    demonstrate_modeler_perspective,
    demonstrate_quadrant_framework,
    demonstrate_thinking_about_thinking,
)
from .analysis import (
    DataGenerator,
    StatisticalAnalyzer,
    ValidationFramework,
    anova_test,
    calculate_confidence_interval,
    calculate_correlation,
    calculate_descriptive_stats,
    demonstrate_data_generation,
    demonstrate_statistical_analysis,
    demonstrate_validation_framework,
    generate_synthetic_data,
    generate_time_series,
)
from .visualization import VisualizationEngine

__all__ = [
    # Core
    "ActiveInferenceFramework",
    "demonstrate_active_inference_concepts",
    "FreeEnergyPrinciple",
    "define_what_is_a_thing",
    "demonstrate_fep_concepts",
    "GenerativeModel",
    "create_simple_generative_model",
    "demonstrate_generative_model_concepts",
    # Framework
    "QuadrantFramework",
    "demonstrate_quadrant_framework",
    "MetaCognitiveSystem",
    "demonstrate_meta_cognitive_processes",
    "demonstrate_thinking_about_thinking",
    "ModelerPerspective",
    "demonstrate_modeler_perspective",
    "CognitiveSecurityAnalyzer",
    # Analysis
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
    # Visualization
    "VisualizationEngine",
]
