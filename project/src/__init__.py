"""Tree grafting toolkit - Project-specific algorithms and analysis.

This package contains domain-specific functionality for tree grafting research,
including compatibility prediction, biological simulation, statistical analysis,
data processing, visualization, and other grafting-related computations.

Modules:
    graft_basics: Core grafting concepts and basic calculations
    biological_simulation: Biological process simulation framework
    graft_statistics: Statistical analysis functions
    graft_data_generator: Synthetic grafting data generation
    graft_data_processing: Data preprocessing and cleaning
    graft_metrics: Success and quality metrics
    graft_parameters: Parameter set management and validation
    graft_analysis: Outcome and factor analysis
    graft_plots: Publication-quality plot implementations
    graft_reporting: Automated report generation
    graft_validation: Result validation framework
    graft_visualization: Visualization engine with styling
    compatibility_prediction: Graft compatibility prediction
    species_database: Species compatibility database
    technique_library: Grafting technique encyclopedia
    rootstock_analysis: Rootstock selection and analysis
    seasonal_planning: Optimal timing calculations
    economic_analysis: Cost-benefit analysis
"""

__version__ = "1.0.0"
__layer__ = "scientific"

# Import core classes for convenient access
from .graft_basics import (
    check_cambium_alignment,
    calculate_graft_angle,
    estimate_callus_formation_time,
    calculate_union_strength,
    estimate_success_probability
)
from .biological_simulation import CambiumIntegrationSimulation, GraftSimulationBase
from .graft_visualization import GraftVisualizationEngine
from .graft_statistics import calculate_graft_statistics

__all__ = [
    "graft_basics",
    "biological_simulation",
    "graft_statistics",
    "graft_data_generator",
    "graft_data_processing",
    "graft_metrics",
    "graft_parameters",
    "graft_analysis",
    "graft_plots",
    "graft_reporting",
    "graft_validation",
    "graft_visualization",
    "compatibility_prediction",
    "species_database",
    "technique_library",
    "rootstock_analysis",
    "seasonal_planning",
    "economic_analysis",
]
