"""Ways of knowing analysis layer - Domain-specific algorithms and analysis.

This package contains ways of knowing specific functionality for the research project,
including database operations, analysis algorithms, statistical computations,
and ways-specific metrics.

Modules:
    database: SQLAlchemy ORM for ways database operations
    sql_queries: Raw SQL queries for ways data access
    models: Data models for Way, Room, Question, Example entities
    ways_analysis: Main ways analysis framework and characterization
    house_of_knowledge: House of Knowledge structure analysis
    network_analysis: Network relationships between ways
    ways_statistics: Ways-specific statistical analysis and distributions
    metrics: Ways coverage, completeness, and balance metrics
"""

__version__ = "1.0.0"
__layer__ = "scientific"

# Import core classes for convenient access
from .database import WaysDatabase
from .ways_analysis import WaysAnalyzer, WaysCharacterization
from .ways_statistics import analyze_way_distributions
from .metrics import compute_way_coverage_metrics

__all__ = [
    "database",
    "sql_queries",
    "models",
    "ways_analysis",
    "house_of_knowledge",
    "network_analysis",
    "ways_statistics",
    "metrics",
]

