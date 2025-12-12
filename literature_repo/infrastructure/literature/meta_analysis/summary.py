"""Comprehensive summary report generation for meta-analysis.

Generates text and JSON summaries of literature analysis results,
including temporal trends, keyword analysis, metadata insights, and PCA interpretation.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

import numpy as np

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.meta_analysis.aggregator import (
    DataAggregator,
    TemporalData,
    KeywordData,
    MetadataData,
)
from infrastructure.literature.meta_analysis.pca_loadings import (
    extract_pca_loadings,
    get_top_words_per_component,
)

logger = get_logger(__name__)


def generate_summary_data(
    aggregator: Optional[DataAggregator] = None,
    n_pca_components: int = 5,
    top_n_keywords: int = 20,
    top_n_words_per_component: int = 10
) -> Dict[str, Any]:
    """Generate comprehensive summary data structure.
    
    Args:
        aggregator: Optional DataAggregator instance.
        n_pca_components: Number of PCA components to analyze.
        top_n_keywords: Number of top keywords to include.
        top_n_words_per_component: Number of top words per PCA component.
        
    Returns:
        Dictionary containing all summary data.
    """
    if aggregator is None:
        aggregator = DataAggregator()
    
    # Collect all data
    entries = aggregator.aggregate_library_data()
    temporal_data = aggregator.prepare_temporal_data()
    keyword_data = aggregator.prepare_keyword_data()
    metadata_data = aggregator.prepare_metadata_data()
    
    # PCA analysis (if available)
    pca_summary = None
    try:
        corpus = aggregator.prepare_text_corpus()
        if len(corpus.texts) > 0:
            loadings_matrix, _, feature_names, pca_model = extract_pca_loadings(
                corpus, n_components=n_pca_components
            )
            top_words = get_top_words_per_component(
                loadings_matrix, feature_names, n_pca_components,
                top_n=top_n_words_per_component
            )
            
            pca_summary = {
                'n_components': n_pca_components,
                'total_variance_explained': float(np.sum(pca_model.explained_variance_ratio_)),
                'components': {
                    f'PC{i+1}': {
                        'explained_variance': float(pca_model.explained_variance_ratio_[i]),
                        'top_words': [
                            {'word': word, 'loading': float(loading)}
                            for word, loading in top_words.get(i, [])
                        ]
                    }
                    for i in range(n_pca_components)
                }
            }
    except Exception as e:
        logger.warning(f"PCA analysis skipped in summary: {e}")
    
    # Top keywords
    sorted_keywords = sorted(
        keyword_data.keyword_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n_keywords]
    
    # Top venues
    sorted_venues = sorted(
        metadata_data.venues.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    # Top authors
    sorted_authors = sorted(
        metadata_data.authors.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    # Citation statistics
    citation_stats = {}
    if metadata_data.citation_counts:
        citation_stats = {
            'mean': float(np.mean(metadata_data.citation_counts)),
            'median': float(np.median(metadata_data.citation_counts)),
            'std': float(np.std(metadata_data.citation_counts)),
            'min': int(np.min(metadata_data.citation_counts)),
            'max': int(np.max(metadata_data.citation_counts)),
            'total': int(np.sum(metadata_data.citation_counts))
        }
    
    # Publication rate
    publication_rate = None
    if len(temporal_data.years) > 1:
        years_span = temporal_data.years[-1] - temporal_data.years[0] + 1
        publication_rate = temporal_data.total_papers / years_span if years_span > 0 else 0
    
    # Build summary
    summary = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_papers': len(entries),
            'year_range': {
                'start': temporal_data.year_range[0],
                'end': temporal_data.year_range[1]
            },
            'publication_rate': float(publication_rate) if publication_rate else None
        },
        'temporal': {
            'total_years': len(temporal_data.years),
            'papers_by_year': {
                str(year): count
                for year, count in zip(temporal_data.years, temporal_data.counts)
            },
            'peak_year': {
                'year': int(temporal_data.years[np.argmax(temporal_data.counts)]),
                'count': int(max(temporal_data.counts))
            } if temporal_data.counts else None
        },
        'keywords': {
            'total_unique_keywords': len(keyword_data.keywords),
            'top_keywords': [
                {'keyword': keyword, 'count': count}
                for keyword, count in sorted_keywords
            ]
        },
        'metadata_stats': {
            'venues': {
                'total_unique': len(metadata_data.venues),
                'top_venues': [
                    {'venue': venue, 'count': count}
                    for venue, count in sorted_venues
                ]
            },
            'authors': {
                'total_unique': len(metadata_data.authors),
                'top_authors': [
                    {'author': author, 'count': count}
                    for author, count in sorted_authors
                ]
            },
            'sources': {
                'total_unique': len(metadata_data.sources),
                'source_distribution': {
                    source: count
                    for source, count in metadata_data.sources.items()
                }
            },
            'citations': citation_stats,
            'availability': {
                'dois_available': metadata_data.dois_available,
                'pdfs_available': metadata_data.pdfs_available,
                'doi_coverage': metadata_data.dois_available / len(entries) if entries else 0,
                'pdf_coverage': metadata_data.pdfs_available / len(entries) if entries else 0
            }
        }
    }
    
    # Add PCA summary if available
    if pca_summary:
        summary['pca_analysis'] = pca_summary
    
    return summary


def generate_text_summary(
    summary_data: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """Generate human-readable text summary in Markdown format.
    
    Args:
        summary_data: Summary data from generate_summary_data.
        output_path: Output file path.
        
    Returns:
        Path to saved Markdown file.
    """
    if output_path is None:
        output_path = Path("data/output/meta_analysis_summary.md")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    lines = [
        "# Meta-Analysis Summary Report",
        "",
        f"**Generated**: {summary_data['metadata']['generated_at']}",
        "",
        "---",
        "",
        "## Executive Summary",
        ""
    ]
    
    # Key statistics
    meta = summary_data['metadata']
    lines.extend([
        f"- **Total Papers Analyzed**: {meta['total_papers']}",
        f"- **Year Range**: {meta['year_range']['start']} - {meta['year_range']['end']}",
    ])
    
    if meta['publication_rate']:
        lines.append(f"- **Average Publications per Year**: {meta['publication_rate']:.2f}")
    
    lines.extend(["", "---", "", "## Temporal Trends", ""])
    
    # Temporal analysis
    temporal = summary_data['temporal']
    if temporal['peak_year']:
        lines.extend([
            f"- **Peak Publication Year**: {temporal['peak_year']['year']} ({temporal['peak_year']['count']} papers)",
            "",
            "### Publications by Year",
            "",
            "| Year | Count |",
            "|------|-------|"
        ])
        
        for year, count in sorted(temporal['papers_by_year'].items()):
            lines.append(f"| {year} | {count} |")
    
    lines.extend(["", "---", "", "## Keyword Analysis", ""])
    
    # Keywords
    keywords = summary_data['keywords']
    lines.extend([
        f"- **Total Unique Keywords**: {keywords['total_unique_keywords']}",
        "",
        "### Top Keywords",
        "",
        "| Rank | Keyword | Frequency |",
        "|------|---------|-----------|"
    ])
    
    for rank, kw_data in enumerate(keywords['top_keywords'], 1):
        lines.append(f"| {rank} | {kw_data['keyword']} | {kw_data['count']} |")
    
    lines.extend(["", "---", "", "## Metadata Insights", ""])
    
    # Metadata
    meta_stats = summary_data['metadata_stats']
    
    # Venues
    lines.extend([
        "### Publication Venues",
        "",
        f"- **Total Unique Venues**: {meta_stats['venues']['total_unique']}",
        "",
        "#### Top Venues",
        "",
        "| Rank | Venue | Publications |",
        "|------|-------|--------------|"
    ])
    
    for rank, venue_data in enumerate(meta_stats['venues']['top_venues'], 1):
        lines.append(f"| {rank} | {venue_data['venue']} | {venue_data['count']} |")
    
    # Authors
    lines.extend([
        "",
        "### Authors",
        "",
        f"- **Total Unique Authors**: {meta_stats['authors']['total_unique']}",
        "",
        "#### Top Authors",
        "",
        "| Rank | Author | Publications |",
        "|------|--------|--------------|"
    ])
    
    for rank, author_data in enumerate(meta_stats['authors']['top_authors'], 1):
        lines.append(f"| {rank} | {author_data['author']} | {author_data['count']} |")
    
    # Citations
    if meta_stats['citations']:
        citations = meta_stats['citations']
        lines.extend([
            "",
            "### Citation Statistics",
            "",
            f"- **Mean Citations**: {citations['mean']:.1f}",
            f"- **Median Citations**: {citations['median']:.1f}",
            f"- **Standard Deviation**: {citations['std']:.1f}",
            f"- **Range**: {citations['min']} - {citations['max']}",
            f"- **Total Citations**: {citations['total']:,}"
        ])
    
    # Availability
    availability = meta_stats['availability']
    lines.extend([
        "",
        "### Data Availability",
        "",
        f"- **Papers with DOI**: {availability['dois_available']} ({availability['doi_coverage']*100:.1f}%)",
        f"- **Papers with PDF**: {availability['pdfs_available']} ({availability['pdf_coverage']*100:.1f}%)"
    ])
    
    # PCA Analysis
    if 'pca_analysis' in summary_data:
        lines.extend(["", "---", "", "## PCA Interpretation", ""])
        
        pca = summary_data['pca_analysis']
        lines.extend([
            f"- **Total Variance Explained**: {pca['total_variance_explained']*100:.2f}%",
            "",
            "### Principal Components",
            ""
        ])
        
        for comp_name, comp_data in pca['components'].items():
            var_explained = comp_data['explained_variance'] * 100
            lines.extend([
                f"#### {comp_name}",
                "",
                f"- **Variance Explained**: {var_explained:.2f}%",
                "",
                "**Top Contributing Words**:"
            ])
            
            for word_data in comp_data['top_words'][:5]:
                lines.append(f"- {word_data['word']} (loading: {word_data['loading']:.4f})")
            
            lines.append("")
    
    # Recommendations
    lines.extend([
        "---",
        "",
        "## Key Observations",
        ""
    ])
    
    # Generate insights
    insights = []
    
    if temporal['peak_year']:
        insights.append(
            f"Peak publication activity occurred in {temporal['peak_year']['year']} "
            f"with {temporal['peak_year']['count']} papers."
        )
    
    if meta['publication_rate'] and meta['publication_rate'] > 1:
        insights.append(
            f"Strong publication activity with an average of {meta['publication_rate']:.1f} "
            "papers per year."
        )
    
    if keywords['top_keywords']:
        top_kw = keywords['top_keywords'][0]['keyword']
        insights.append(
            f"Most frequent keyword: '{top_kw}' (appears {keywords['top_keywords'][0]['count']} times)."
        )
    
    if meta_stats['citations']:
        if meta_stats['citations']['mean'] > 50:
            insights.append(
                f"High citation activity with mean of {meta_stats['citations']['mean']:.1f} citations per paper."
            )
    
    if insights:
        for insight in insights:
            lines.append(f"- {insight}")
    else:
        lines.append("- Analysis complete. Review individual sections for detailed insights.")
    
    lines.extend(["", "---", ""])
    
    # Write markdown
    output_path.write_text('\n'.join(lines), encoding='utf-8')
    logger.info(f"Generated text summary: {output_path}")
    return output_path


def export_summary_json(
    summary_data: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """Export summary data to JSON format.
    
    Args:
        summary_data: Summary data from generate_summary_data.
        output_path: Output file path.
        
    Returns:
        Path to saved JSON file.
    """
    if output_path is None:
        output_path = Path("data/output/meta_analysis_summary.json")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Exported summary JSON: {output_path}")
    return output_path


def generate_all_summaries(
    aggregator: Optional[DataAggregator] = None,
    output_dir: Optional[Path] = None,
    n_pca_components: int = 5
) -> Dict[str, Path]:
    """Generate all summary outputs (text and JSON).
    
    Args:
        aggregator: Optional DataAggregator instance.
        output_dir: Output directory (defaults to data/output).
        n_pca_components: Number of PCA components to analyze.
        
    Returns:
        Dictionary mapping format name to output path.
    """
    if output_dir is None:
        output_dir = Path("data/output")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate summary data
    summary_data = generate_summary_data(
        aggregator=aggregator,
        n_pca_components=n_pca_components
    )
    
    # Generate outputs
    outputs = {}
    
    # Text summary
    md_path = generate_text_summary(
        summary_data,
        output_dir / "meta_analysis_summary.md"
    )
    outputs['markdown'] = md_path
    
    # JSON summary
    json_path = export_summary_json(
        summary_data,
        output_dir / "meta_analysis_summary.json"
    )
    outputs['json'] = json_path
    
    return outputs


