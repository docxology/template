"""Metadata visualization and analysis.

Visualizes paper metadata including venues, authors, citations,
and source distributions.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Any
from pathlib import Path

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.meta_analysis.aggregator import (
    DataAggregator,
    MetadataData,
)
from infrastructure.literature.meta_analysis.visualizations import (
    plot_venue_distribution,
    plot_author_contributions,
    plot_citation_distribution,
    plot_metadata_completeness,
    save_plot,
)

logger = get_logger(__name__)


def create_venue_distribution_plot(
    top_n: int = 15,
    output_path: Optional[Path] = None,
    aggregator: Optional[DataAggregator] = None,
    format: str = "png"
) -> Path:
    """Create venue distribution plot.
    
    Args:
        top_n: Number of top venues to show.
        output_path: Optional output path.
        aggregator: Optional DataAggregator instance.
        format: Output format (png, svg, pdf).
        
    Returns:
        Path to saved plot.
    """
    if aggregator is None:
        aggregator = DataAggregator()
    
    metadata = aggregator.prepare_metadata_data()
    
    # Get top N venues
    sorted_venues = sorted(
        metadata.venues.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]
    
    venues = [v for v, _ in sorted_venues]
    counts = [c for _, c in sorted_venues]
    
    if output_path is None:
        output_path = Path("data/output/venue_distribution." + format)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fig = plot_venue_distribution(
        venues=venues,
        counts=counts,
        title=f"Top {top_n} Publication Venues"
    )
    
    return save_plot(fig, output_path)


def create_author_contributions_plot(
    top_n: int = 20,
    output_path: Optional[Path] = None,
    aggregator: Optional[DataAggregator] = None,
    format: str = "png"
) -> Path:
    """Create author contributions plot.
    
    Args:
        top_n: Number of top authors to show.
        output_path: Optional output path.
        aggregator: Optional DataAggregator instance.
        format: Output format (png, svg, pdf).
        
    Returns:
        Path to saved plot.
    """
    if aggregator is None:
        aggregator = DataAggregator()
    
    metadata = aggregator.prepare_metadata_data()
    
    # Get top N authors
    sorted_authors = sorted(
        metadata.authors.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]
    
    authors = [a for a, _ in sorted_authors]
    counts = [c for _, c in sorted_authors]
    
    if output_path is None:
        output_path = Path("data/output/author_contributions." + format)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fig = plot_author_contributions(
        authors=authors,
        counts=counts,
        title=f"Top {top_n} Authors by Publication Count"
    )
    
    return save_plot(fig, output_path)


def create_citation_distribution_plot(
    output_path: Optional[Path] = None,
    aggregator: Optional[DataAggregator] = None,
    format: str = "png"
) -> Path:
    """Create citation distribution plot.
    
    Args:
        output_path: Optional output path.
        aggregator: Optional DataAggregator instance.
        format: Output format (png, svg, pdf).
        
    Returns:
        Path to saved plot.
    """
    if aggregator is None:
        aggregator = DataAggregator()
    
    metadata = aggregator.prepare_metadata_data()
    
    if output_path is None:
        output_path = Path("data/output/citation_distribution." + format)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fig = plot_citation_distribution(
        citation_counts=metadata.citation_counts,
        title="Citation Count Distribution"
    )
    
    return save_plot(fig, output_path)


def calculate_completeness_stats(aggregator: Optional[DataAggregator] = None) -> Dict[str, Dict[str, Any]]:
    """Calculate metadata completeness statistics.
    
    Args:
        aggregator: Optional DataAggregator instance.
        
    Returns:
        Dictionary with completeness statistics for each metadata field.
        Format: {
            'field_name': {
                'total': int,
                'available': int,
                'missing': int,
                'fraction': float,
                'percentage': float
            }
        }
    """
    if aggregator is None:
        aggregator = DataAggregator()
    
    entries = aggregator.aggregate_library_data()
    total = len(entries)
    
    if total == 0:
        return {}
    
    # Count available fields
    stats = {}
    
    # Year
    years_available = sum(1 for e in entries if e.year is not None)
    stats['year'] = {
        'total': total,
        'available': years_available,
        'missing': total - years_available,
        'fraction': years_available / total,
        'percentage': (years_available / total) * 100
    }
    
    # Authors
    authors_available = sum(1 for e in entries if e.authors and len(e.authors) > 0)
    stats['authors'] = {
        'total': total,
        'available': authors_available,
        'missing': total - authors_available,
        'fraction': authors_available / total,
        'percentage': (authors_available / total) * 100
    }
    
    # Citations
    citations_available = sum(1 for e in entries if e.citation_count is not None)
    stats['citations'] = {
        'total': total,
        'available': citations_available,
        'missing': total - citations_available,
        'fraction': citations_available / total,
        'percentage': (citations_available / total) * 100
    }
    
    # DOI
    dois_available = sum(1 for e in entries if e.doi is not None and e.doi != "")
    stats['doi'] = {
        'total': total,
        'available': dois_available,
        'missing': total - dois_available,
        'fraction': dois_available / total,
        'percentage': (dois_available / total) * 100
    }
    
    # PDF
    pdfs_available = sum(1 for e in entries if e.pdf_path is not None and e.pdf_path != "")
    stats['pdf'] = {
        'total': total,
        'available': pdfs_available,
        'missing': total - pdfs_available,
        'fraction': pdfs_available / total,
        'percentage': (pdfs_available / total) * 100
    }
    
    # Venue
    venues_available = sum(1 for e in entries if e.venue is not None and e.venue != "")
    stats['venue'] = {
        'total': total,
        'available': venues_available,
        'missing': total - venues_available,
        'fraction': venues_available / total,
        'percentage': (venues_available / total) * 100
    }
    
    # Abstract
    abstracts_available = sum(1 for e in entries if hasattr(e, 'abstract') and e.abstract and e.abstract.strip() != "")
    stats['abstract'] = {
        'total': total,
        'available': abstracts_available,
        'missing': total - abstracts_available,
        'fraction': abstracts_available / total,
        'percentage': (abstracts_available / total) * 100
    }
    
    return stats


def get_metadata_summary(aggregator: Optional[DataAggregator] = None) -> Dict:
    """Get summary statistics of metadata.
    
    Args:
        aggregator: Optional DataAggregator instance.
        
    Returns:
        Dictionary with summary statistics.
    """
    if aggregator is None:
        aggregator = DataAggregator()
    
    metadata = aggregator.prepare_metadata_data()
    
    return {
        "total_venues": len(metadata.venues),
        "total_authors": len(metadata.authors),
        "total_sources": len(metadata.sources),
        "papers_with_citations": len(metadata.citation_counts),
        "average_citations": (
            sum(metadata.citation_counts) / len(metadata.citation_counts)
            if metadata.citation_counts else 0
        ),
        "max_citations": max(metadata.citation_counts) if metadata.citation_counts else 0,
        "dois_available": metadata.dois_available,
        "pdfs_available": metadata.pdfs_available,
        "top_venue": max(metadata.venues.items(), key=lambda x: x[1])[0] if metadata.venues else None,
        "top_author": max(metadata.authors.items(), key=lambda x: x[1])[0] if metadata.authors else None,
    }


def create_metadata_completeness_plot(
    output_path: Optional[Path] = None,
    aggregator: Optional[DataAggregator] = None,
    format: str = "png"
) -> Path:
    """Create metadata completeness visualization.
    
    Args:
        output_path: Optional output path.
        aggregator: Optional DataAggregator instance.
        format: Output format (png, svg, pdf).
        
    Returns:
        Path to saved plot.
    """
    if aggregator is None:
        aggregator = DataAggregator()
    
    completeness_stats = calculate_completeness_stats(aggregator)
    
    if output_path is None:
        output_path = Path("data/output/metadata_completeness." + format)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fig = plot_metadata_completeness(
        completeness_stats=completeness_stats,
        title="Metadata Completeness"
    )
    
    return save_plot(fig, output_path)


