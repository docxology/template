"""Keyword and term evolution analysis.

Analyzes keyword frequency over time, co-occurrence patterns,
and emerging trends in research literature.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.meta_analysis.aggregator import (
    DataAggregator,
    KeywordData,
)
from infrastructure.literature.meta_analysis.visualizations import (
    plot_keyword_frequency,
    plot_keyword_cooccurrence,
    save_plot,
)

logger = get_logger(__name__)


def extract_keywords_over_time(
    aggregator: Optional[DataAggregator] = None,
    min_frequency: int = 2
) -> KeywordData:
    """Extract keywords and their evolution over time.
    
    Args:
        aggregator: Optional DataAggregator instance.
        min_frequency: Minimum keyword frequency to include.
        
    Returns:
        KeywordData with keyword information.
    """
    if aggregator is None:
        aggregator = DataAggregator()
    
    keyword_data = aggregator.prepare_keyword_data()
    
    # Filter by minimum frequency
    filtered_keywords = {
        k: v for k, v in keyword_data.keyword_counts.items()
        if v >= min_frequency
    }
    
    # Update keyword_data with filtered keywords
    keyword_data.keyword_counts = filtered_keywords
    keyword_data.keywords = list(filtered_keywords.keys())
    
    return keyword_data


def detect_emerging_keywords(
    keyword_data: KeywordData,
    recent_years: int = 3,
    growth_threshold: float = 1.5
) -> List[Tuple[str, float]]:
    """Detect emerging keywords with increasing frequency.
    
    Args:
        keyword_data: Keyword data from aggregator.
        recent_years: Number of recent years to analyze.
        growth_threshold: Minimum growth ratio to consider emerging.
        
    Returns:
        List of (keyword, growth_ratio) tuples sorted by growth.
    """
    emerging = []
    
    # Get recent years
    all_years = sorted(set(
        year for years in keyword_data.keywords_by_year.values()
        for year in [y for y in keyword_data.keywords_by_year.keys()]
    ))
    
    if len(all_years) < recent_years:
        return []
    
    recent_years_list = sorted(all_years)[-recent_years:]
    earlier_years_list = sorted(all_years)[:-recent_years] if len(all_years) > recent_years else []
    
    for keyword in keyword_data.keywords:
        # Count in recent years
        recent_count = sum(
            keyword_data.keywords_by_year.get(year, []).count(keyword)
            for year in recent_years_list
        )
        
        # Count in earlier years
        if earlier_years_list:
            earlier_count = sum(
                keyword_data.keywords_by_year.get(year, []).count(keyword)
                for year in earlier_years_list
            )
            
            # Calculate growth ratio
            if earlier_count > 0:
                growth_ratio = recent_count / earlier_count
            else:
                growth_ratio = float('inf') if recent_count > 0 else 0.0
        else:
            growth_ratio = float('inf') if recent_count > 0 else 0.0
        
        if growth_ratio >= growth_threshold:
            emerging.append((keyword, growth_ratio))
    
    # Sort by growth ratio (descending)
    emerging.sort(key=lambda x: x[1], reverse=True)
    
    return emerging


def create_keyword_frequency_plot(
    keyword_data: KeywordData,
    top_n: int = 20,
    output_path: Optional[Path] = None,
    format: str = "png"
) -> Path:
    """Create keyword frequency plot.
    
    Args:
        keyword_data: Keyword data from aggregator.
        top_n: Number of top keywords to plot.
        output_path: Optional output path.
        format: Output format (png, svg, pdf).
        
    Returns:
        Path to saved plot.
    """
    # Get top N keywords
    sorted_keywords = sorted(
        keyword_data.keyword_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]
    
    keywords = [k for k, _ in sorted_keywords]
    counts = [c for _, c in sorted_keywords]
    
    if output_path is None:
        output_path = Path("data/output/keyword_frequency." + format)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fig = plot_keyword_frequency(
        keywords=keywords,
        counts=counts,
        title=f"Top {top_n} Keywords"
    )
    
    return save_plot(fig, output_path)


def create_keyword_evolution_plot(
    keyword_data: KeywordData,
    keywords: List[str],
    output_path: Optional[Path] = None,
    format: str = "png"
) -> Path:
    """Create keyword evolution over time plot.
    
    Args:
        keyword_data: Keyword data from aggregator.
        keywords: List of keywords to plot.
        output_path: Optional output path.
        format: Output format (png, svg, pdf).
        
    Returns:
        Path to saved plot.
    """
    if output_path is None:
        output_path = Path("data/output/keyword_evolution." + format)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare data for plotting
    plot_data = {}
    for keyword in keywords:
        if keyword in keyword_data.keyword_frequency_over_time:
            plot_data[keyword] = keyword_data.keyword_frequency_over_time[keyword]
    
    fig = plot_keyword_frequency(
        keywords=list(plot_data.keys()),
        frequency_data=plot_data,
        title="Keyword Evolution Over Time",
        show_evolution=True
    )
    
    return save_plot(fig, output_path)


