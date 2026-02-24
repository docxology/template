"""Data sub-package for Ento-Linguistic research.

Provides modules for synthetic data generation, data processing/cleaning,
and literature mining.
"""

from .loader import DataLoader
from .data_processing import (
    clean_data,
    normalize_data,
    detect_outliers,
    extract_features,
    transform_data,
    create_validation_pipeline,
)
from .literature_mining import (
    LiteratureCorpus,
    Publication,
    create_entomology_query,
    mine_entomology_literature,
    PubMedMiner,
    ArXivMiner,
)

__all__ = [
    "DataLoader",
    # Analysis modules
    "LiteratureCorpus",
    "Publication",
    "ArXivMiner",
    "PubMedMiner",
    "create_entomology_query",
    "mine_entomology_literature",
    # data_processing
    "clean_data",
    "normalize_data",
    "detect_outliers",
    "extract_features",
    "transform_data",
    "create_validation_pipeline",
]
