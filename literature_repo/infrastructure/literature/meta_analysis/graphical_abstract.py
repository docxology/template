"""Graphical abstract generation for meta-analysis.

Creates composite visualizations that combine all meta-analysis plots
into single-page and multi-page graphical abstracts.
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.meta_analysis.aggregator import DataAggregator
from infrastructure.literature.meta_analysis.visualizations import (
    plot_pca_2d,
    plot_pca_3d,
    plot_keyword_frequency,
    plot_metadata_completeness,
    plot_publications_by_year,
    plot_citation_distribution,
    save_plot,
    FONT_SIZE_TITLE,
)

logger = get_logger(__name__)


def create_single_page_abstract(
    aggregator: Optional[DataAggregator] = None,
    keywords: Optional[List[str]] = None,
    output_path: Optional[Path] = None,
    format: str = "png"
) -> Path:
    """Create single-page graphical abstract with all visualizations.
    
    Creates a composite figure with subplots arranged in a grid:
    - PCA 2D (top-left)
    - PCA 3D (top-right)
    - Keyword frequency (middle-left)
    - Metadata completeness (middle-right)
    - Publication timeline (bottom-left)
    - Citation distribution (bottom-right)
    
    Args:
        aggregator: Optional DataAggregator instance.
        keywords: Optional list of search keywords for title.
        output_path: Optional output path.
        format: Output format (png, svg, pdf).
        
    Returns:
        Path to saved plot.
    """
    if aggregator is None:
        aggregator = DataAggregator()
    
    if output_path is None:
        output_path = Path("data/output/graphical_abstract_single_page." + format)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare data
    entries = aggregator.aggregate_library_data()
    temporal_data = aggregator.prepare_temporal_data()
    keyword_data = aggregator.prepare_keyword_data()
    metadata_data = aggregator.prepare_metadata_data()
    corpus = aggregator.prepare_text_corpus()
    
    # Calculate completeness stats
    from infrastructure.literature.meta_analysis.metadata import calculate_completeness_stats
    completeness_stats = calculate_completeness_stats(aggregator)
    
    # Create figure with GridSpec for flexible layout
    fig = plt.figure(figsize=(20, 16))
    gs = GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3, 
                  left=0.05, right=0.95, top=0.93, bottom=0.05)
    
    # Overall title
    title_text = "Meta-Analysis Graphical Abstract"
    if keywords:
        title_text += f"\nKeywords: {', '.join(keywords)}"
    title_text += f"\nTotal Papers: {len(entries)} | Date: {datetime.now().strftime('%Y-%m-%d')}"
    fig.suptitle(title_text, fontsize=FONT_SIZE_TITLE + 2, fontweight='bold', y=0.98)
    
    try:
        # 1. PCA 2D (top-left)
        from infrastructure.literature.meta_analysis.pca import (
            extract_text_features,
            compute_pca,
            cluster_papers,
        )
        feature_matrix, feature_names = extract_text_features(corpus)
        pca_data_2d, pca_model_2d = compute_pca(feature_matrix, n_components=2)
        cluster_labels = cluster_papers(pca_data_2d, n_clusters=5)
        
        ax1 = fig.add_subplot(gs[0, 0])
        fig_pca_2d = plot_pca_2d(
            pca_data_2d, corpus.titles, corpus.years,
            cluster_labels=cluster_labels,
            explained_variance=pca_model_2d.explained_variance_ratio_,
            title="PCA Analysis (2D)"
        )
        # Copy axes content
        ax1_original = fig_pca_2d.axes[0]
        for child in ax1_original.get_children():
            if hasattr(child, 'get_position'):
                pos = child.get_position()
                # Adjust position if needed
        plt.close(fig_pca_2d)
        
        # Recreate in subplot
        scatter = ax1.scatter(
            pca_data_2d[:, 0], pca_data_2d[:, 1],
            c=[y if y else min([y for y in corpus.years if y]) for y in corpus.years],
            cmap='plasma', alpha=0.7, s=80, edgecolors='black', linewidth=0.5
        )
        ax1.set_xlabel(f'PC1 ({pca_model_2d.explained_variance_ratio_[0]*100:.1f}%)', 
                      fontsize=10, fontweight='medium')
        ax1.set_ylabel(f'PC2 ({pca_model_2d.explained_variance_ratio_[1]*100:.1f}%)', 
                      fontsize=10, fontweight='medium')
        ax1.set_title("PCA Analysis (2D)", fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3, linestyle='--')
        
    except Exception as e:
        logger.warning(f"Failed to create PCA 2D subplot: {e}")
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.text(0.5, 0.5, 'PCA 2D\n(Not available)', ha='center', va='center')
        ax1.set_title("PCA Analysis (2D)", fontsize=12, fontweight='bold')
    
    try:
        # 2. PCA 3D (top-right) - simplified 2D projection
        ax2 = fig.add_subplot(gs[0, 1])
        pca_data_3d, pca_model_3d = compute_pca(feature_matrix, n_components=3)
        scatter = ax2.scatter(
            pca_data_3d[:, 0], pca_data_3d[:, 1],
            c=[y if y else min([y for y in corpus.years if y]) for y in corpus.years],
            cmap='plasma', alpha=0.7, s=80, edgecolors='black', linewidth=0.5
        )
        ax2.set_xlabel(f'PC1 ({pca_model_3d.explained_variance_ratio_[0]*100:.1f}%)', 
                      fontsize=10, fontweight='medium')
        ax2.set_ylabel(f'PC2 ({pca_model_3d.explained_variance_ratio_[1]*100:.1f}%)', 
                      fontsize=10, fontweight='medium')
        ax2.set_title("PCA Analysis (3D Projection)", fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3, linestyle='--')
    except Exception as e:
        logger.warning(f"Failed to create PCA 3D subplot: {e}")
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.text(0.5, 0.5, 'PCA 3D\n(Not available)', ha='center', va='center')
        ax2.set_title("PCA Analysis (3D)", fontsize=12, fontweight='bold')
    
    try:
        # 3. Keyword frequency (middle-left)
        ax3 = fig.add_subplot(gs[1, 0])
        top_keywords = sorted(
            keyword_data.keyword_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:15]
        keywords_list = [k for k, _ in top_keywords]
        counts_list = [c for _, c in top_keywords]
        
        y_pos = np.arange(len(keywords_list))
        ax3.barh(y_pos, counts_list, alpha=0.8, color='#2E86AB', edgecolor='#1B4F72', linewidth=0.5)
        ax3.set_yticks(y_pos)
        ax3.set_yticklabels(keywords_list, fontsize=8)
        ax3.set_xlabel('Frequency', fontsize=10, fontweight='medium')
        ax3.set_ylabel('Keywords', fontsize=10, fontweight='medium')
        ax3.set_title("Top Keywords", fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='x', linestyle='--')
    except Exception as e:
        logger.warning(f"Failed to create keyword frequency subplot: {e}")
        ax3 = fig.add_subplot(gs[1, 0])
        ax3.text(0.5, 0.5, 'Keywords\n(Not available)', ha='center', va='center')
        ax3.set_title("Top Keywords", fontsize=12, fontweight='bold')
    
    try:
        # 4. Metadata completeness (middle-right)
        ax4 = fig.add_subplot(gs[1, 1])
        if completeness_stats:
            fields = []
            percentages = []
            for field_key in ['year', 'authors', 'citations', 'doi', 'pdf', 'venue', 'abstract']:
                if field_key in completeness_stats:
                    field_names = {
                        'year': 'Year', 'authors': 'Authors', 'citations': 'Citations',
                        'doi': 'DOI', 'pdf': 'PDF', 'venue': 'Venue', 'abstract': 'Abstract'
                    }
                    fields.append(field_names.get(field_key, field_key.capitalize()))
                    percentages.append(completeness_stats[field_key]['percentage'])
            
            y_pos = np.arange(len(fields))
            colors = ['#2A9D8F' if p >= 80 else '#E9C46A' if p >= 60 else '#F77F00' if p >= 40 else '#E63946' 
                     for p in percentages]
            ax4.barh(y_pos, percentages, alpha=0.8, color=colors, edgecolor='#1B4F72', linewidth=0.5)
            ax4.set_yticks(y_pos)
            ax4.set_yticklabels(fields, fontsize=9)
            ax4.set_xlabel('Completeness (%)', fontsize=10, fontweight='medium')
            ax4.set_ylabel('Metadata Field', fontsize=10, fontweight='medium')
            ax4.set_title("Metadata Completeness", fontsize=12, fontweight='bold')
            ax4.set_xlim(0, 105)
            ax4.grid(True, alpha=0.3, axis='x', linestyle='--')
        else:
            ax4.text(0.5, 0.5, 'Metadata\n(Not available)', ha='center', va='center')
            ax4.set_title("Metadata Completeness", fontsize=12, fontweight='bold')
    except Exception as e:
        logger.warning(f"Failed to create metadata completeness subplot: {e}")
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.text(0.5, 0.5, 'Metadata\n(Not available)', ha='center', va='center')
        ax4.set_title("Metadata Completeness", fontsize=12, fontweight='bold')
    
    try:
        # 5. Publication timeline (bottom-left)
        ax5 = fig.add_subplot(gs[2, 0])
        if temporal_data.years:
            ax5.bar(temporal_data.years, temporal_data.counts, alpha=0.8, 
                   color='#2E86AB', edgecolor='#1B4F72', linewidth=0.5)
            ax5.plot(temporal_data.years, temporal_data.counts, marker='o', 
                    color='#A23B72', linewidth=2, markersize=4)
            ax5.set_xlabel('Year', fontsize=10, fontweight='medium')
            ax5.set_ylabel('Publications', fontsize=10, fontweight='medium')
            ax5.set_title("Publications by Year", fontsize=12, fontweight='bold')
            ax5.grid(True, alpha=0.3, linestyle='--')
            if len(temporal_data.years) > 10:
                plt.setp(ax5.xaxis.get_majorticklabels(), rotation=45, ha='right')
        else:
            ax5.text(0.5, 0.5, 'Timeline\n(Not available)', ha='center', va='center')
            ax5.set_title("Publications by Year", fontsize=12, fontweight='bold')
    except Exception as e:
        logger.warning(f"Failed to create publication timeline subplot: {e}")
        ax5 = fig.add_subplot(gs[2, 0])
        ax5.text(0.5, 0.5, 'Timeline\n(Not available)', ha='center', va='center')
        ax5.set_title("Publications by Year", fontsize=12, fontweight='bold')
    
    try:
        # 6. Citation distribution (bottom-right)
        ax6 = fig.add_subplot(gs[2, 1])
        if metadata_data.citation_counts:
            ax6.hist(metadata_data.citation_counts, bins=30, alpha=0.8, 
                    color='#6A4C93', edgecolor='#1B4F72', linewidth=0.5)
            mean_cit = np.mean(metadata_data.citation_counts)
            median_cit = np.median(metadata_data.citation_counts)
            ax6.axvline(mean_cit, color='#E63946', linestyle='--', linewidth=1.5, 
                       label=f'Mean: {mean_cit:.1f}')
            ax6.axvline(median_cit, color='#2A9D8F', linestyle='--', linewidth=1.5, 
                       label=f'Median: {median_cit:.1f}')
            ax6.set_xlabel('Citation Count', fontsize=10, fontweight='medium')
            ax6.set_ylabel('Frequency', fontsize=10, fontweight='medium')
            ax6.set_title("Citation Distribution", fontsize=12, fontweight='bold')
            ax6.legend(fontsize=8, framealpha=0.9)
            ax6.grid(True, alpha=0.3, axis='y', linestyle='--')
        else:
            ax6.text(0.5, 0.5, 'Citations\n(Not available)', ha='center', va='center')
            ax6.set_title("Citation Distribution", fontsize=12, fontweight='bold')
    except Exception as e:
        logger.warning(f"Failed to create citation distribution subplot: {e}")
        ax6 = fig.add_subplot(gs[2, 1])
        ax6.text(0.5, 0.5, 'Citations\n(Not available)', ha='center', va='center')
        ax6.set_title("Citation Distribution", fontsize=12, fontweight='bold')
    
    return save_plot(fig, output_path)


def create_multi_page_abstract(
    aggregator: Optional[DataAggregator] = None,
    keywords: Optional[List[str]] = None,
    output_path: Optional[Path] = None,
    format: str = "pdf"
) -> Path:
    """Create multi-page graphical abstract PDF.
    
    Creates a PDF with one visualization per page.
    
    Args:
        aggregator: Optional DataAggregator instance.
        keywords: Optional list of search keywords for title.
        output_path: Optional output path.
        format: Output format (pdf recommended).
        
    Returns:
        Path to saved PDF.
    """
    if aggregator is None:
        aggregator = DataAggregator()
    
    if output_path is None:
        output_path = Path("data/output/graphical_abstract_multi_page." + format)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    from matplotlib.backends.backend_pdf import PdfPages
    
    # Prepare data
    entries = aggregator.aggregate_library_data()
    temporal_data = aggregator.prepare_temporal_data()
    keyword_data = aggregator.prepare_keyword_data()
    metadata_data = aggregator.prepare_metadata_data()
    corpus = aggregator.prepare_text_corpus()
    
    from infrastructure.literature.meta_analysis.metadata import calculate_completeness_stats
    completeness_stats = calculate_completeness_stats(aggregator)
    
    with PdfPages(output_path) as pdf:
        # Title page
        fig = plt.figure(figsize=(11, 8.5))
        ax = fig.add_subplot(111)
        ax.axis('off')
        title_text = "Meta-Analysis Graphical Abstract"
        if keywords:
            title_text += f"\n\nKeywords: {', '.join(keywords)}"
        title_text += f"\n\nTotal Papers: {len(entries)}"
        title_text += f"\nDate: {datetime.now().strftime('%Y-%m-%d')}"
        ax.text(0.5, 0.5, title_text, ha='center', va='center',
               fontsize=FONT_SIZE_TITLE + 4, fontweight='bold')
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        
        # Individual visualizations
        try:
            from infrastructure.literature.meta_analysis.pca import (
                create_pca_2d_plot,
                create_pca_3d_plot,
            )
            from infrastructure.literature.meta_analysis.keywords import create_keyword_frequency_plot
            from infrastructure.literature.meta_analysis.metadata import create_metadata_completeness_plot
            from infrastructure.literature.meta_analysis.temporal import create_publication_timeline_plot
            
            if not PIL_AVAILABLE:
                logger.warning("PIL/Pillow not available, skipping multi-page abstract image pages")
                return output_path
            
            # PCA 2D
            pca_2d_path = create_pca_2d_plot(aggregator=aggregator, n_clusters=5, format="png")
            img = Image.open(pca_2d_path)
            pdf_fig = plt.figure(figsize=(11, 8.5))
            plt.imshow(img)
            plt.axis('off')
            pdf.savefig(pdf_fig, bbox_inches='tight')
            plt.close(pdf_fig)
            
            # PCA 3D
            pca_3d_path = create_pca_3d_plot(aggregator=aggregator, n_clusters=5, format="png")
            img = Image.open(pca_3d_path)
            pdf_fig = plt.figure(figsize=(11, 8.5))
            plt.imshow(img)
            plt.axis('off')
            pdf.savefig(pdf_fig, bbox_inches='tight')
            plt.close(pdf_fig)
            
            # Keyword frequency
            keyword_path = create_keyword_frequency_plot(aggregator=aggregator, format="png")
            img = Image.open(keyword_path)
            pdf_fig = plt.figure(figsize=(11, 8.5))
            plt.imshow(img)
            plt.axis('off')
            pdf.savefig(pdf_fig, bbox_inches='tight')
            plt.close(pdf_fig)
            
            # Metadata completeness
            completeness_path = create_metadata_completeness_plot(aggregator=aggregator, format="png")
            img = Image.open(completeness_path)
            pdf_fig = plt.figure(figsize=(11, 8.5))
            plt.imshow(img)
            plt.axis('off')
            pdf.savefig(pdf_fig, bbox_inches='tight')
            plt.close(pdf_fig)
            
            # Publication timeline
            timeline_path = create_publication_timeline_plot(aggregator=aggregator, format="png")
            img = Image.open(timeline_path)
            pdf_fig = plt.figure(figsize=(11, 8.5))
            plt.imshow(img)
            plt.axis('off')
            pdf.savefig(pdf_fig, bbox_inches='tight')
            plt.close(pdf_fig)
            
            # Citation distribution
            citation_path = create_citation_distribution_plot(aggregator=aggregator, format="png")
            img = Image.open(citation_path)
            pdf_fig = plt.figure(figsize=(11, 8.5))
            plt.imshow(img)
            plt.axis('off')
            pdf.savefig(pdf_fig, bbox_inches='tight')
            plt.close(pdf_fig)
            
        except Exception as e:
            logger.warning(f"Failed to add some pages to multi-page abstract: {e}")
            if not PIL_AVAILABLE:
                logger.warning("PIL/Pillow not available, cannot create multi-page abstract from images")
    
    logger.info(f"Created multi-page graphical abstract: {output_path}")
    return output_path


def create_comprehensive_abstract(
    aggregator: Optional[DataAggregator] = None,
    keywords: Optional[List[str]] = None,
    output_path: Optional[Path] = None,
    format: str = "png"
) -> Path:
    """Create comprehensive single-page abstract with all visualizations including loadings.
    
    Similar to create_single_page_abstract but includes PCA loadings visualizations.
    
    Args:
        aggregator: Optional DataAggregator instance.
        keywords: Optional list of search keywords for title.
        output_path: Optional output path.
        format: Output format (png, svg, pdf).
        
    Returns:
        Path to saved plot.
    """
    # For now, use the single-page abstract
    # Can be extended to include loadings visualizations in a larger grid
    return create_single_page_abstract(aggregator, keywords, output_path, format)


