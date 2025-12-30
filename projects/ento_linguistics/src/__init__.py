"""Scientific layer - Project-specific algorithms and analysis.

This package contains domain-specific functionality for the research project,
including simulations, statistical analysis, data processing, visualization,
and other scientific computations.

Modules:
    example: Basic mathematical operations (template example)
    simulation: Core simulation framework with reproducibility
    statistics: Statistical analysis functions
    data_generator: Synthetic data generation
    data_processing: Data preprocessing and cleaning
    metrics: Performance and quality metrics
    parameters: Parameter set management and validation
    performance: Convergence and scalability analysis
    plots: Publication-quality plot implementations
    reporting: Automated report generation
    validation: Result validation framework
    visualization: Visualization engine with styling
"""

__version__ = "1.0.0"
__layer__ = "scientific"

# Import core classes for convenient access
from .example import add_numbers, calculate_average
from .simulation import SimpleSimulation, SimulationBase
from .visualization import VisualizationEngine
from .statistics import calculate_descriptive_stats

__all__ = [
    "example",
    "simulation",
    "statistics",
    "data_generator",
    "data_processing",
    "metrics",
    "parameters",
    "performance",
    "plots",
    "reporting",
    "validation",
    "visualization",
]

