"""Library statistics and display utilities.

Provides functions to get and display comprehensive library statistics
for menu interfaces and reporting.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.library.index import LibraryIndex
from infrastructure.literature.core.config import LiteratureConfig

logger = get_logger(__name__)


def get_library_statistics(config: Optional[LiteratureConfig] = None) -> Dict[str, Any]:
    """Get comprehensive library statistics.
    
    Args:
        config: Optional literature config (uses default if not provided).
        
    Returns:
        Dictionary with comprehensive library statistics.
    """
    if config is None:
        from infrastructure.literature.config import LiteratureConfig
        config = LiteratureConfig.from_env()
    
    library_index = LibraryIndex(config)
    stats = library_index.get_stats()
    
    return stats


def format_library_stats_display(stats: Dict[str, Any]) -> str:
    """Format library statistics for display in menu.
    
    Args:
        stats: Statistics dictionary from get_library_statistics().
        
    Returns:
        Formatted string for display.
    """
    lines = []
    lines.append("Current Library Status:")
    
    total = stats.get("total_entries", 0)
    pdfs = stats.get("downloaded_pdfs", 0)
    summaries = stats.get("summaries_generated", 0)
    pdf_pct = stats.get("pdf_percentage", 0.0)
    summary_pct = stats.get("summary_percentage", 0.0)
    size_mb = stats.get("pdf_size_mb", 0.0)
    
    lines.append(f"  • Total papers: {total}")
    lines.append(f"  • PDFs downloaded: {pdfs} ({pdf_pct:.0f}%)")
    lines.append(f"  • Summaries generated: {summaries} ({summary_pct:.0f}%)")
    if size_mb > 0:
        lines.append(f"  • Library size: {size_mb} MB")
    
    # Source distribution
    sources = stats.get("sources", {})
    if sources:
        top_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)[:3]
        source_str = ", ".join(f"{k}: {v}" for k, v in top_sources)
        lines.append(f"  • Top sources: {source_str}")
    
    # Year range
    oldest = stats.get("oldest_year")
    newest = stats.get("newest_year")
    if oldest and newest:
        lines.append(f"  • Year range: {oldest}-{newest}")
    
    return "\n".join(lines)

