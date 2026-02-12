"""Ento-Linguistic Research — Source Package.

This package implements the computational framework for Ento-Linguistic analysis,
studying how entomological metaphors permeate and shape scientific discourse.

Domain-Specific Modules:
    analysis.term_extraction: Terminology extraction from scientific corpora
    analysis.discourse_analysis: Framing and discourse pattern analysis
    analysis.domain_analysis: Cross-domain ento-linguistic comparison
    analysis.conceptual_mapping: Conceptual mapping and relationship modeling
    analysis.text_analysis: Natural language processing for scientific texts
    analysis.statistics: Statistical hypothesis testing and descriptive stats

Visualization Modules:
    visualization.concept_visualization: Network visualization of concept relationships
    visualization.statistical_visualization: Statistical result visualization
    visualization.plots: Publication-quality plot types
    visualization.visualization: Visualization engine with consistent styling

Data Modules:
    data.literature_mining: Corpus-based literature mining and analysis
    data.data_generator: Synthetic data generation for testing
    data.data_processing: Data preprocessing and cleaning pipelines

Infrastructure Modules:
    core.validation: Result validation and quality assurance
    core.metrics: Quality and performance metrics
    core.parameters: Parameter management for reproducible analyses
    core.example: Basic utility functions
    pipeline.simulation: Simulation framework for sensitivity analysis
    pipeline.reporting: Automated report generation

All submodules are imported lazily — use explicit imports to avoid
loading unnecessary dependencies:

    from src.analysis.term_extraction import TerminologyExtractor
    from src.visualization.concept_visualization import ConceptVisualizer
"""

__version__ = "1.0.0"
__layer__ = "scientific"

__all__ = [
    # Subpackages
    "analysis",
    "visualization",
    "data",
    "core",
    "pipeline",
]
