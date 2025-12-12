"""Temporal analysis of publications.

Analyzes publication trends over time, including papers per year,
publication rate changes, and temporal filtering.
"""
from __future__ import annotations

from typing import List, Optional, Tuple
from pathlib import Path

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.meta_analysis.aggregator import (
    DataAggregator,
    TemporalData,
)
from infrastructure.literature.meta_analysis.visualizations import (
    plot_publications_by_year,
    save_plot,
)

logger = get_logger(__name__)


def get_publication_trends(
    aggregator: Optional[DataAggregator] = None
) -> TemporalData:
    """Get publication trends data.
    
    Args:
        aggregator: Optional DataAggregator instance.
        
    Returns:
        TemporalData with publication trends.
    """
    if aggregator is None:
        aggregator = DataAggregator()
    
    return aggregator.prepare_temporal_data()


def filter_by_year_range(
    entries: List,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None
) -> List:
    """Filter entries by year range.
    
    Args:
        entries: List of library entries.
        start_year: Optional start year (inclusive).
        end_year: Optional end year (inclusive).
        
    Returns:
        Filtered list of entries.
    """
    filtered = []
    
    for entry in entries:
        if entry.year is None:
            continue
        
        if start_year is not None and entry.year < start_year:
            continue
        
        if end_year is not None and entry.year > end_year:
            continue
        
        filtered.append(entry)
    
    return filtered


def analyze_publication_rate(temporal_data: TemporalData) -> dict:
    """Analyze publication rate changes.
    
    Args:
        temporal_data: Temporal data from aggregator.
        
    Returns:
        Dictionary with rate analysis statistics.
    """
    if len(temporal_data.years) < 2:
        return {
            "average_per_year": temporal_data.total_papers,
            "growth_rate": 0.0,
            "peak_year": temporal_data.years[0] if temporal_data.years else None,
        }
    
    # Calculate average
    avg_per_year = temporal_data.total_papers / len(temporal_data.years)
    
    # Calculate growth rate (simple linear regression slope)
    n = len(temporal_data.years)
    sum_x = sum(temporal_data.years)
    sum_y = sum(temporal_data.counts)
    sum_xy = sum(y * x for x, y in zip(temporal_data.years, temporal_data.counts))
    sum_x2 = sum(x * x for x in temporal_data.years)
    
    if n * sum_x2 - sum_x * sum_x != 0:
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
    else:
        slope = 0.0
    
    # Find peak year
    peak_idx = temporal_data.counts.index(max(temporal_data.counts))
    peak_year = temporal_data.years[peak_idx]
    
    return {
        "average_per_year": avg_per_year,
        "growth_rate": slope,
        "peak_year": peak_year,
        "peak_count": temporal_data.counts[peak_idx],
        "total_years": len(temporal_data.years),
        "year_range": temporal_data.year_range,
    }


def create_publication_timeline_plot(
    output_path: Optional[Path] = None,
    aggregator: Optional[DataAggregator] = None,
    format: str = "png"
) -> Path:
    """Create publication timeline plot.
    
    Args:
        output_path: Optional output path (defaults to data/output/).
        aggregator: Optional DataAggregator instance.
        format: Output format (png, svg, pdf).
        
    Returns:
        Path to saved plot.
    """
    if aggregator is None:
        aggregator = DataAggregator()
    
    temporal_data = aggregator.prepare_temporal_data()
    
    if output_path is None:
        output_path = Path("data/output/publications_by_year." + format)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fig = plot_publications_by_year(
        years=temporal_data.years,
        counts=temporal_data.counts,
        title="Publications by Year"
    )
    
    return save_plot(fig, output_path)


