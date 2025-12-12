"""Visualization utilities for meta-analysis.

Provides plotting functions for temporal, keyword, metadata,
and PCA visualizations with enhanced accessibility features.
"""
from __future__ import annotations

from typing import List, Optional, Dict, Tuple, Any
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# Set style
plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')

# Accessibility constants
FONT_SIZE_LABELS = 14
FONT_SIZE_TITLE = 16
FONT_SIZE_LEGEND = 14  # Increased from 12 for better readability
GRID_ALPHA = 0.3
EDGE_WIDTH = 0.8
MARKER_SIZE = 120

# Colorblind-friendly colormaps
COLORMAP_YEAR = 'plasma'  # Continuous colormap for years
COLORMAP_CATEGORICAL = 'tab10'  # For discrete categories


def plot_publications_by_year(
    years: List[int],
    counts: List[int],
    title: str = "Publications by Year"
) -> plt.Figure:
    """Plot publications by year with enhanced accessibility.
    
    Args:
        years: List of years.
        counts: List of publication counts per year.
        title: Plot title.
        
    Returns:
        Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Use colorblind-friendly colors with better contrast
    ax.bar(years, counts, alpha=0.8, color='#2E86AB', edgecolor='#1B4F72', linewidth=EDGE_WIDTH)
    ax.plot(years, counts, marker='o', color='#A23B72', linewidth=2.5, markersize=8, label='Trend')
    
    ax.set_xlabel('Year', fontsize=FONT_SIZE_LABELS, fontweight='medium')
    ax.set_ylabel('Number of Publications', fontsize=FONT_SIZE_LABELS, fontweight='medium')
    ax.set_title(title, fontsize=FONT_SIZE_TITLE, fontweight='bold', pad=15)
    ax.grid(True, alpha=GRID_ALPHA, linestyle='--')
    
    # Add legend
    ax.legend(loc='best', fontsize=FONT_SIZE_LEGEND, framealpha=0.9)
    
    # Rotate x-axis labels if many years
    if len(years) > 10:
        plt.xticks(rotation=45, ha='right', fontsize=FONT_SIZE_LABELS - 2)
    else:
        plt.xticks(fontsize=FONT_SIZE_LABELS - 2)
    plt.yticks(fontsize=FONT_SIZE_LABELS - 2)
    
    plt.tight_layout()
    return fig


def plot_keyword_frequency(
    keywords: List[str],
    counts: Optional[List[int]] = None,
    frequency_data: Optional[Dict[str, List[Tuple[int, int]]]] = None,
    title: str = "Keyword Frequency",
    show_evolution: bool = False
) -> plt.Figure:
    """Plot keyword frequency with enhanced accessibility.
    
    Args:
        keywords: List of keywords.
        counts: List of keyword counts (for bar chart).
        frequency_data: Dictionary mapping keywords to (year, count) lists (for evolution).
        title: Plot title.
        show_evolution: Whether to show evolution over time.
        
    Returns:
        Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=(16, 9))
    
    if show_evolution and frequency_data:
        # Plot evolution lines with distinct colors and markers
        try:
            cmap = plt.colormaps.get_cmap(COLORMAP_CATEGORICAL)
        except AttributeError:
            cmap = plt.get_cmap(COLORMAP_CATEGORICAL)
        colors = cmap(np.linspace(0, 1, len(keywords)))
        markers = ['o', 's', '^', 'D', 'v', 'p', '*', 'h', 'X', 'P']
        
        for i, keyword in enumerate(keywords):
            if keyword in frequency_data:
                data = frequency_data[keyword]
                years = [d[0] for d in data]
                freqs = [d[1] for d in data]
                marker = markers[i % len(markers)]
                ax.plot(years, freqs, marker=marker, label=keyword, linewidth=2.5, 
                       markersize=8, color=colors[i], alpha=0.8)
        
        ax.set_xlabel('Year', fontsize=FONT_SIZE_LABELS, fontweight='medium')
        ax.set_ylabel('Frequency', fontsize=FONT_SIZE_LABELS, fontweight='medium')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=FONT_SIZE_LEGEND, 
                 framealpha=0.9, title='Keywords', title_fontsize=FONT_SIZE_LEGEND + 1)
    else:
        # Bar chart with color gradient
        if counts is None:
            counts = [1] * len(keywords)
        
        y_pos = np.arange(len(keywords))
        # Use color gradient for better visual distinction
        try:
            cmap = plt.colormaps.get_cmap(COLORMAP_YEAR)
        except AttributeError:
            cmap = plt.get_cmap(COLORMAP_YEAR)
        colors = cmap(np.linspace(0.2, 0.8, len(keywords)))
        bars = ax.barh(y_pos, counts, alpha=0.8, color=colors, edgecolor='#1B4F72', 
                      linewidth=EDGE_WIDTH)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(keywords, fontsize=FONT_SIZE_LABELS - 2)
        ax.set_xlabel('Frequency', fontsize=FONT_SIZE_LABELS, fontweight='medium')
        ax.set_ylabel('Keywords', fontsize=FONT_SIZE_LABELS, fontweight='medium')
        
        # Add value labels on bars
        for i, (bar, count) in enumerate(zip(bars, counts)):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2, 
                   f' {int(count)}', va='center', fontsize=FONT_SIZE_LEGEND - 1)
    
    ax.set_title(title, fontsize=FONT_SIZE_TITLE, fontweight='bold', pad=15)
    ax.grid(True, alpha=GRID_ALPHA, linestyle='--', axis='x' if not show_evolution else 'both')
    
    plt.xticks(fontsize=FONT_SIZE_LABELS - 2)
    plt.yticks(fontsize=FONT_SIZE_LABELS - 2)
    
    plt.tight_layout()
    return fig


def plot_keyword_cooccurrence(
    cooccurrence_matrix: np.ndarray,
    keywords: List[str],
    title: str = "Keyword Co-occurrence"
) -> plt.Figure:
    """Plot keyword co-occurrence heatmap.
    
    Args:
        cooccurrence_matrix: Matrix of co-occurrence counts.
        keywords: List of keywords.
        title: Plot title.
        
    Returns:
        Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=(12, 10))
    
    im = ax.imshow(cooccurrence_matrix, cmap='YlOrRd', aspect='auto')
    
    ax.set_xticks(np.arange(len(keywords)))
    ax.set_yticks(np.arange(len(keywords)))
    ax.set_xticklabels(keywords, rotation=45, ha='right')
    ax.set_yticklabels(keywords)
    
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Add colorbar
    plt.colorbar(im, ax=ax, label='Co-occurrence Count')
    
    plt.tight_layout()
    return fig


def plot_venue_distribution(
    venues: List[str],
    counts: List[int],
    title: str = "Venue Distribution"
) -> plt.Figure:
    """Plot venue distribution with enhanced accessibility.
    
    Args:
        venues: List of venue names.
        counts: List of publication counts per venue.
        title: Plot title.
        
    Returns:
        Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=(14, 9))
    
    y_pos = np.arange(len(venues))
    # Use color gradient for better visual distinction
    try:
        cmap = plt.colormaps.get_cmap(COLORMAP_YEAR)
    except AttributeError:
        cmap = plt.get_cmap(COLORMAP_YEAR)
    colors = cmap(np.linspace(0.2, 0.8, len(venues)))
    bars = ax.barh(y_pos, counts, alpha=0.8, color=colors, edgecolor='#1B4F72', 
                  linewidth=EDGE_WIDTH)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(venues, fontsize=FONT_SIZE_LABELS - 2)
    ax.set_xlabel('Number of Publications', fontsize=FONT_SIZE_LABELS, fontweight='medium')
    ax.set_ylabel('Venues', fontsize=FONT_SIZE_LABELS, fontweight='medium')
    ax.set_title(title, fontsize=FONT_SIZE_TITLE, fontweight='bold', pad=15)
    ax.grid(True, alpha=GRID_ALPHA, axis='x', linestyle='--')
    
    # Add value labels on bars
    for bar, count in zip(bars, counts):
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height()/2, 
               f' {int(count)}', va='center', fontsize=FONT_SIZE_LEGEND - 1)
    
    plt.xticks(fontsize=FONT_SIZE_LABELS - 2)
    plt.yticks(fontsize=FONT_SIZE_LABELS - 2)
    
    plt.tight_layout()
    return fig


def plot_author_contributions(
    authors: List[str],
    counts: List[int],
    title: str = "Author Contributions"
) -> plt.Figure:
    """Plot author contributions with enhanced accessibility.
    
    Args:
        authors: List of author names.
        counts: List of publication counts per author.
        title: Plot title.
        
    Returns:
        Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=(14, 9))
    
    y_pos = np.arange(len(authors))
    # Use colorblind-friendly green gradient
    try:
        cmap = plt.colormaps.get_cmap('viridis')
    except AttributeError:
        cmap = plt.get_cmap('viridis')
    colors = cmap(np.linspace(0.3, 0.9, len(authors)))
    bars = ax.barh(y_pos, counts, alpha=0.8, color=colors, edgecolor='#1B4F72', 
                  linewidth=EDGE_WIDTH)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(authors, fontsize=FONT_SIZE_LABELS - 2)
    ax.set_xlabel('Number of Publications', fontsize=FONT_SIZE_LABELS, fontweight='medium')
    ax.set_ylabel('Authors', fontsize=FONT_SIZE_LABELS, fontweight='medium')
    ax.set_title(title, fontsize=FONT_SIZE_TITLE, fontweight='bold', pad=15)
    ax.grid(True, alpha=GRID_ALPHA, axis='x', linestyle='--')
    
    # Add value labels on bars
    for bar, count in zip(bars, counts):
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height()/2, 
               f' {int(count)}', va='center', fontsize=FONT_SIZE_LEGEND - 1)
    
    plt.xticks(fontsize=FONT_SIZE_LABELS - 2)
    plt.yticks(fontsize=FONT_SIZE_LABELS - 2)
    
    plt.tight_layout()
    return fig


def plot_citation_distribution(
    citation_counts: List[int],
    title: str = "Citation Distribution"
) -> plt.Figure:
    """Plot citation distribution histogram with enhanced accessibility.
    
    Args:
        citation_counts: List of citation counts.
        title: Plot title.
        
    Returns:
        Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Use colorblind-friendly color
    n, bins, patches = ax.hist(citation_counts, bins=50, alpha=0.8, 
                               color='#6A4C93', edgecolor='#1B4F72', linewidth=EDGE_WIDTH)
    
    # Color gradient for histogram bars
    try:
        cmap = plt.colormaps.get_cmap(COLORMAP_YEAR)
    except AttributeError:
        cmap = plt.get_cmap(COLORMAP_YEAR)
    colors = cmap(np.linspace(0.3, 0.9, len(patches)))
    for patch, color in zip(patches, colors):
        patch.set_facecolor(color)
    
    ax.set_xlabel('Citation Count', fontsize=FONT_SIZE_LABELS, fontweight='medium')
    ax.set_ylabel('Frequency', fontsize=FONT_SIZE_LABELS, fontweight='medium')
    ax.set_title(title, fontsize=FONT_SIZE_TITLE, fontweight='bold', pad=15)
    ax.grid(True, alpha=GRID_ALPHA, axis='y', linestyle='--')
    
    # Add statistics with better visibility
    mean_citations = np.mean(citation_counts)
    median_citations = np.median(citation_counts)
    std_citations = np.std(citation_counts)
    
    ax.axvline(mean_citations, color='#E63946', linestyle='--', linewidth=2.5, 
              label=f'Mean: {mean_citations:.1f}', alpha=0.9)
    ax.axvline(median_citations, color='#2A9D8F', linestyle='--', linewidth=2.5, 
              label=f'Median: {median_citations:.1f}', alpha=0.9)
    ax.axvline(mean_citations + std_citations, color='#F77F00', linestyle=':', linewidth=2, 
              label=f'Mean + 1σ: {mean_citations + std_citations:.1f}', alpha=0.7)
    ax.axvline(mean_citations - std_citations, color='#F77F00', linestyle=':', linewidth=2, 
              label=f'Mean - 1σ: {mean_citations - std_citations:.1f}', alpha=0.7)
    
    ax.legend(loc='best', fontsize=FONT_SIZE_LEGEND, framealpha=0.9, 
             title='Statistics', title_fontsize=FONT_SIZE_LEGEND + 1)
    
    plt.xticks(fontsize=FONT_SIZE_LABELS - 2)
    plt.yticks(fontsize=FONT_SIZE_LABELS - 2)
    
    plt.tight_layout()
    return fig


def plot_pca_2d(
    pca_data: np.ndarray,
    titles: List[str],
    years: List[Optional[int]],
    cluster_labels: Optional[np.ndarray] = None,
    explained_variance: Optional[np.ndarray] = None,
    title: str = "PCA Analysis (2D)"
) -> plt.Figure:
    """Plot 2D PCA visualization with continuous year coloring and cluster shapes.
    
    Uses continuous colormap for years and distinct marker shapes for clusters.
    Enhanced with accessibility features and comprehensive legends.
    
    Args:
        pca_data: 2D PCA-transformed data.
        titles: List of paper titles.
        years: List of publication years.
        cluster_labels: Optional cluster labels for marker shapes.
        explained_variance: Explained variance ratio for each component.
        title: Plot title.
        
    Returns:
        Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=(16, 12))  # Increased for better legend spacing
    
    # Prepare year data for continuous coloring
    years_array = None
    if years and any(y is not None for y in years):
        valid_years = [y for y in years if y is not None]
        if valid_years:
            min_year = min(valid_years)
            years_array = np.array([y if y is not None else min_year for y in years])
    
    # Marker shapes for clusters (colorblind-friendly)
    marker_map = ['o', 's', '^', 'D', 'v', 'p', '*', 'h', 'X', 'P', '<', '>']
    
    if cluster_labels is not None and years_array is not None:
        # Dual encoding: color by year (continuous), shape by cluster
        unique_clusters = np.unique(cluster_labels)
        
        for cluster_id in unique_clusters:
            mask = cluster_labels == cluster_id
            marker = marker_map[cluster_id % len(marker_map)]
            
            scatter = ax.scatter(
                pca_data[mask, 0],
                pca_data[mask, 1],
                c=years_array[mask],
                cmap=COLORMAP_YEAR,
                marker=marker,
                alpha=0.7,
                s=MARKER_SIZE,
                edgecolors='black',
                linewidth=EDGE_WIDTH,
                label=f'Cluster {int(cluster_id)}',
                vmin=years_array.min(),
                vmax=years_array.max()
            )
        
        # Add colorbar for year (positioned on right side)
        cbar = plt.colorbar(scatter, ax=ax, label='Publication Year', pad=0.08)
        cbar.ax.tick_params(labelsize=FONT_SIZE_LEGEND - 1)
        cbar.set_label('Publication Year', fontsize=FONT_SIZE_LEGEND, fontweight='medium')
        
        # Add legend for clusters (positioned at bottom-left to avoid overlap with colorbar)
        n_clusters = len(unique_clusters)
        ncol = 2 if n_clusters > 5 else 1  # Use 2 columns if many clusters
        ax.legend(loc='lower left', fontsize=FONT_SIZE_LEGEND, framealpha=0.9, 
                 title='Cluster Type', title_fontsize=FONT_SIZE_LEGEND + 1,
                 ncol=ncol, bbox_to_anchor=(0.0, 0.0), borderaxespad=0.5)
        
    elif cluster_labels is not None:
        # Only cluster coloring (no year data)
        unique_clusters = np.unique(cluster_labels)
        try:
            cmap = plt.colormaps.get_cmap(COLORMAP_CATEGORICAL)
        except AttributeError:
            cmap = plt.get_cmap(COLORMAP_CATEGORICAL)
        colors = cmap(np.linspace(0, 1, len(unique_clusters)))
        
        for i, cluster_id in enumerate(unique_clusters):
            mask = cluster_labels == cluster_id
            marker = marker_map[cluster_id % len(marker_map)]
            
            ax.scatter(
                pca_data[mask, 0],
                pca_data[mask, 1],
                c=[colors[i]],
                marker=marker,
                alpha=0.7,
                s=MARKER_SIZE,
                edgecolors='black',
                linewidth=EDGE_WIDTH,
                label=f'Cluster {int(cluster_id)}'
            )
        
        ax.legend(loc='best', fontsize=FONT_SIZE_LEGEND, framealpha=0.9, 
                 title='Cluster Type', title_fontsize=FONT_SIZE_LEGEND + 1)
        
    elif years_array is not None:
        # Only year coloring (continuous)
        scatter = ax.scatter(
            pca_data[:, 0],
            pca_data[:, 1],
            c=years_array,
            cmap=COLORMAP_YEAR,
            alpha=0.7,
            s=MARKER_SIZE,
            edgecolors='black',
            linewidth=EDGE_WIDTH
        )
        cbar = plt.colorbar(scatter, ax=ax, label='Publication Year', pad=0.08)
        cbar.ax.tick_params(labelsize=FONT_SIZE_LEGEND - 1)
        cbar.set_label('Publication Year', fontsize=FONT_SIZE_LEGEND, fontweight='medium')
    else:
        # Default: single color
        ax.scatter(
            pca_data[:, 0],
            pca_data[:, 1],
            alpha=0.7,
            s=MARKER_SIZE,
            color='#2E86AB',
            edgecolors='black',
            linewidth=EDGE_WIDTH
        )
    
    # Enhanced axis labels with variance explained
    xlabel = f'PC1 ({explained_variance[0]*100:.1f}% variance)' if explained_variance is not None else 'PC1'
    ylabel = f'PC2 ({explained_variance[1]*100:.1f}% variance)' if explained_variance is not None else 'PC2'
    
    ax.set_xlabel(xlabel, fontsize=FONT_SIZE_LABELS, fontweight='medium')
    ax.set_ylabel(ylabel, fontsize=FONT_SIZE_LABELS, fontweight='medium')
    ax.set_title(title, fontsize=FONT_SIZE_TITLE, fontweight='bold', pad=15)
    ax.grid(True, alpha=GRID_ALPHA, linestyle='--')
    
    plt.xticks(fontsize=FONT_SIZE_LABELS - 2)
    plt.yticks(fontsize=FONT_SIZE_LABELS - 2)
    
    plt.tight_layout()
    return fig


def plot_pca_3d(
    pca_data: np.ndarray,
    titles: List[str],
    years: List[Optional[int]],
    cluster_labels: Optional[np.ndarray] = None,
    explained_variance: Optional[np.ndarray] = None,
    title: str = "PCA Analysis (3D)"
) -> plt.Figure:
    """Plot 3D PCA visualization with continuous year coloring and cluster shapes.
    
    Uses continuous colormap for years and distinct marker shapes for clusters.
    Enhanced with accessibility features and comprehensive legends.
    
    Args:
        pca_data: 3D PCA-transformed data.
        titles: List of paper titles.
        years: List of publication years.
        cluster_labels: Optional cluster labels for marker shapes.
        explained_variance: Explained variance ratio for each component.
        title: Plot title.
        
    Returns:
        Matplotlib figure.
    """
    from mpl_toolkits.mplot3d import Axes3D
    
    fig = plt.figure(figsize=(16, 12))
    ax = fig.add_subplot(111, projection='3d')
    
    # Prepare year data for continuous coloring
    years_array = None
    if years and any(y is not None for y in years):
        valid_years = [y for y in years if y is not None]
        if valid_years:
            min_year = min(valid_years)
            years_array = np.array([y if y is not None else min_year for y in years])
    
    # Marker shapes for clusters (colorblind-friendly)
    marker_map = ['o', 's', '^', 'D', 'v', 'p', '*', 'h', 'X', 'P', '<', '>']
    
    if cluster_labels is not None and years_array is not None:
        # Dual encoding: color by year (continuous), shape by cluster
        unique_clusters = np.unique(cluster_labels)
        
        for cluster_id in unique_clusters:
            mask = cluster_labels == cluster_id
            marker = marker_map[cluster_id % len(marker_map)]
            
            scatter = ax.scatter(
                pca_data[mask, 0],
                pca_data[mask, 1],
                pca_data[mask, 2],
                c=years_array[mask],
                cmap=COLORMAP_YEAR,
                marker=marker,
                alpha=0.7,
                s=MARKER_SIZE,
                edgecolors='black',
                linewidth=EDGE_WIDTH,
                label=f'Cluster {int(cluster_id)}',
                vmin=years_array.min(),
                vmax=years_array.max()
            )
        
        # Add colorbar for year
        cbar = plt.colorbar(scatter, ax=ax, label='Publication Year', shrink=0.6, pad=0.1)
        cbar.ax.tick_params(labelsize=FONT_SIZE_LEGEND - 1)
        cbar.set_label('Publication Year', fontsize=FONT_SIZE_LEGEND, fontweight='medium')
        
        # Add legend for clusters
        ax.legend(loc='upper left', fontsize=FONT_SIZE_LEGEND, framealpha=0.9, 
                 title='Cluster Type', title_fontsize=FONT_SIZE_LEGEND + 1)
        
    elif cluster_labels is not None:
        # Only cluster coloring (no year data)
        unique_clusters = np.unique(cluster_labels)
        try:
            cmap = plt.colormaps.get_cmap(COLORMAP_CATEGORICAL)
        except AttributeError:
            cmap = plt.get_cmap(COLORMAP_CATEGORICAL)
        colors = cmap(np.linspace(0, 1, len(unique_clusters)))
        
        for i, cluster_id in enumerate(unique_clusters):
            mask = cluster_labels == cluster_id
            marker = marker_map[cluster_id % len(marker_map)]
            
            ax.scatter(
                pca_data[mask, 0],
                pca_data[mask, 1],
                pca_data[mask, 2],
                c=[colors[i]],
                marker=marker,
                alpha=0.7,
                s=MARKER_SIZE,
                edgecolors='black',
                linewidth=EDGE_WIDTH,
                label=f'Cluster {int(cluster_id)}'
            )
        
        ax.legend(loc='upper left', fontsize=FONT_SIZE_LEGEND, framealpha=0.9, 
                 title='Cluster Type', title_fontsize=FONT_SIZE_LEGEND + 1)
        
    elif years_array is not None:
        # Only year coloring (continuous)
        scatter = ax.scatter(
            pca_data[:, 0],
            pca_data[:, 1],
            pca_data[:, 2],
            c=years_array,
            cmap=COLORMAP_YEAR,
            alpha=0.7,
            s=MARKER_SIZE,
            edgecolors='black',
            linewidth=EDGE_WIDTH
        )
        cbar = plt.colorbar(scatter, ax=ax, label='Publication Year', shrink=0.6, pad=0.1)
        cbar.ax.tick_params(labelsize=FONT_SIZE_LEGEND - 1)
        cbar.set_label('Publication Year', fontsize=FONT_SIZE_LEGEND, fontweight='medium')
    else:
        # Default: single color
        ax.scatter(
            pca_data[:, 0],
            pca_data[:, 1],
            pca_data[:, 2],
            alpha=0.7,
            s=MARKER_SIZE,
            color='#2E86AB',
            edgecolors='black',
            linewidth=EDGE_WIDTH
        )
    
    # Enhanced axis labels with variance explained
    xlabel = f'PC1 ({explained_variance[0]*100:.1f}%)' if explained_variance is not None else 'PC1'
    ylabel = f'PC2 ({explained_variance[1]*100:.1f}%)' if explained_variance is not None else 'PC2'
    zlabel = f'PC3 ({explained_variance[2]*100:.1f}%)' if explained_variance is not None else 'PC3'
    
    ax.set_xlabel(xlabel, fontsize=FONT_SIZE_LABELS, fontweight='medium', labelpad=10)
    ax.set_ylabel(ylabel, fontsize=FONT_SIZE_LABELS, fontweight='medium', labelpad=10)
    ax.set_zlabel(zlabel, fontsize=FONT_SIZE_LABELS, fontweight='medium', labelpad=10)
    ax.set_title(title, fontsize=FONT_SIZE_TITLE, fontweight='bold', pad=20)
    
    # Improve tick labels
    ax.tick_params(labelsize=FONT_SIZE_LABELS - 2)
    
    plt.tight_layout()
    return fig


def plot_pca_loadings_heatmap(
    loadings_matrix: np.ndarray,
    feature_names: List[str],
    n_components: int,
    top_n_words: int = 50,
    title: str = "PCA Loadings Heatmap"
) -> plt.Figure:
    """Plot PCA loadings as heatmap (words × components).
    
    Shows the loading values for top words across all components.
    
    Args:
        loadings_matrix: (n_features, n_components) loadings matrix.
        feature_names: List of feature (word) names.
        n_components: Number of principal components.
        top_n_words: Number of top words to display (by absolute loading).
        title: Plot title.
        
    Returns:
        Matplotlib figure.
    """
    # Calculate overall importance (sum of absolute loadings)
    importance_scores = np.sum(np.abs(loadings_matrix), axis=1)
    top_indices = np.argsort(importance_scores)[::-1][:top_n_words]
    
    # Extract top words and their loadings
    top_words = [feature_names[i] for i in top_indices]
    top_loadings = loadings_matrix[top_indices, :]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(max(12, n_components * 2), max(10, top_n_words * 0.3)))
    
    # Create heatmap
    im = ax.imshow(top_loadings, cmap='RdBu_r', aspect='auto', 
                   vmin=-np.abs(top_loadings).max(), vmax=np.abs(top_loadings).max())
    
    # Set ticks and labels
    ax.set_xticks(np.arange(n_components))
    ax.set_xticklabels([f'PC{i+1}' for i in range(n_components)], fontsize=FONT_SIZE_LABELS - 1)
    ax.set_yticks(np.arange(len(top_words)))
    ax.set_yticklabels(top_words, fontsize=FONT_SIZE_LABELS - 3)
    
    # Labels and title
    ax.set_xlabel('Principal Component', fontsize=FONT_SIZE_LABELS, fontweight='medium')
    ax.set_ylabel('Words', fontsize=FONT_SIZE_LABELS, fontweight='medium')
    ax.set_title(title, fontsize=FONT_SIZE_TITLE, fontweight='bold', pad=15)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, label='Loading Value', pad=0.02)
    cbar.ax.tick_params(labelsize=FONT_SIZE_LEGEND - 1)
    cbar.set_label('Loading Value', fontsize=FONT_SIZE_LEGEND, fontweight='medium')
    
    plt.tight_layout()
    return fig


def plot_pca_loadings_barplot(
    top_words: Dict[int, List[Tuple[str, float]]],
    explained_variance: np.ndarray,
    n_components: int = 5,
    top_n_words: int = 15,
    title: str = "Top Words per Principal Component"
) -> plt.Figure:
    """Plot bar charts for top words per component.
    
    Creates subplots showing top contributing words for each component.
    
    Args:
        top_words: Dictionary mapping component index to list of (word, loading) tuples.
        explained_variance: Explained variance ratio for each component.
        n_components: Number of components to plot.
        top_n_words: Number of top words per component to show.
        title: Overall plot title.
        
    Returns:
        Matplotlib figure.
    """
    # Determine grid layout
    n_cols = min(3, n_components)
    n_rows = (n_components + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(6 * n_cols, 5 * n_rows))
    if n_components == 1:
        axes = [axes]
    else:
        axes = axes.flatten() if n_components > 1 else [axes]
    
    for comp_idx in range(n_components):
        ax = axes[comp_idx]
        
        if comp_idx in top_words and top_words[comp_idx]:
            words_data = top_words[comp_idx][:top_n_words]
            words = [w for w, _ in words_data]
            loadings = [l for _, l in words_data]
            
            # Color bars by loading sign
            colors = ['#2A9D8F' if l > 0 else '#E63946' for l in loadings]
            
            y_pos = np.arange(len(words))
            bars = ax.barh(y_pos, loadings, alpha=0.8, color=colors, 
                          edgecolor='#1B4F72', linewidth=EDGE_WIDTH)
            
            # Add value labels
            for i, (bar, loading) in enumerate(zip(bars, loadings)):
                width = bar.get_width()
                ax.text(width if loading > 0 else width, bar.get_y() + bar.get_height()/2,
                       f' {loading:.3f}', va='center', 
                       fontsize=FONT_SIZE_LEGEND - 2, fontweight='medium')
            
            ax.set_yticks(y_pos)
            ax.set_yticklabels(words, fontsize=FONT_SIZE_LABELS - 3)
            ax.set_xlabel('Loading', fontsize=FONT_SIZE_LABELS - 1, fontweight='medium')
            
            var_explained = explained_variance[comp_idx] * 100
            ax.set_title(f'PC{comp_idx+1} ({var_explained:.1f}% variance)', 
                        fontsize=FONT_SIZE_LABELS, fontweight='bold')
            ax.axvline(0, color='black', linestyle='-', linewidth=1, alpha=0.3)
            ax.grid(True, alpha=GRID_ALPHA, axis='x', linestyle='--')
        else:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center',
                   fontsize=FONT_SIZE_LABELS)
            ax.set_title(f'PC{comp_idx+1}', fontsize=FONT_SIZE_LABELS, fontweight='bold')
    
    # Hide unused subplots
    for idx in range(n_components, len(axes)):
        axes[idx].axis('off')
    
    fig.suptitle(title, fontsize=FONT_SIZE_TITLE, fontweight='bold', y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    return fig


def plot_pca_biplot(
    pca_data: np.ndarray,
    loadings_matrix: np.ndarray,
    feature_names: List[str],
    titles: List[str],
    years: List[Optional[int]],
    cluster_labels: Optional[np.ndarray] = None,
    explained_variance: Optional[np.ndarray] = None,
    top_n_words: int = 20,
    scale_factor: float = 3.0,
    title: str = "PCA Biplot (Papers and Word Vectors)"
) -> plt.Figure:
    """Plot biplot showing both papers (points) and word vectors (arrows).
    
    Papers are shown as points, word vectors as arrows indicating
    the direction and strength of word contributions to the principal components.
    
    Args:
        pca_data: 2D PCA-transformed data for papers.
        loadings_matrix: (n_features, n_components) loadings matrix.
        feature_names: List of feature (word) names.
        titles: List of paper titles.
        years: List of publication years.
        cluster_labels: Optional cluster labels for coloring papers.
        explained_variance: Explained variance ratio for each component.
        top_n_words: Number of top words to display as vectors.
        scale_factor: Scaling factor for word vectors (larger = longer arrows).
        title: Plot title.
        
    Returns:
        Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Calculate overall importance for word selection
    importance_scores = np.sum(np.abs(loadings_matrix), axis=1)
    top_indices = np.argsort(importance_scores)[::-1][:top_n_words]
    top_words = [feature_names[i] for i in top_indices]
    top_loadings = loadings_matrix[top_indices, :2]  # Only first 2 components
    
    # Prepare year data for paper coloring
    years_array = None
    if years and any(y is not None for y in years):
        valid_years = [y for y in years if y is not None]
        if valid_years:
            min_year = min(valid_years)
            years_array = np.array([y if y is not None else min_year for y in years])
    
    # Plot papers
    marker_map = ['o', 's', '^', 'D', 'v', 'p', '*', 'h', 'X', 'P', '<', '>']
    
    if cluster_labels is not None and years_array is not None:
        unique_clusters = np.unique(cluster_labels)
        for cluster_id in unique_clusters:
            mask = cluster_labels == cluster_id
            marker = marker_map[cluster_id % len(marker_map)]
            scatter = ax.scatter(
                pca_data[mask, 0], pca_data[mask, 1],
                c=years_array[mask], cmap=COLORMAP_YEAR,
                marker=marker, alpha=0.6, s=MARKER_SIZE * 0.8,
                edgecolors='black', linewidth=EDGE_WIDTH,
                label=f'Cluster {int(cluster_id)}',
                vmin=years_array.min(), vmax=years_array.max()
            )
        cbar = plt.colorbar(scatter, ax=ax, label='Publication Year', pad=0.08)
        cbar.ax.tick_params(labelsize=FONT_SIZE_LEGEND - 1)
        cbar.set_label('Publication Year', fontsize=FONT_SIZE_LEGEND, fontweight='medium')
        ax.legend(loc='lower left', fontsize=FONT_SIZE_LEGEND, framealpha=0.9,
                 title='Cluster Type', title_fontsize=FONT_SIZE_LEGEND + 1, ncol=2)
    elif years_array is not None:
        scatter = ax.scatter(
            pca_data[:, 0], pca_data[:, 1],
            c=years_array, cmap=COLORMAP_YEAR,
            alpha=0.6, s=MARKER_SIZE * 0.8,
            edgecolors='black', linewidth=EDGE_WIDTH
        )
        cbar = plt.colorbar(scatter, ax=ax, label='Publication Year', pad=0.08)
        cbar.ax.tick_params(labelsize=FONT_SIZE_LEGEND - 1)
        cbar.set_label('Publication Year', fontsize=FONT_SIZE_LEGEND, fontweight='medium')
    else:
        ax.scatter(
            pca_data[:, 0], pca_data[:, 1],
            alpha=0.6, s=MARKER_SIZE * 0.8,
            color='#2E86AB', edgecolors='black', linewidth=EDGE_WIDTH
        )
    
    # Plot word vectors as arrows
    for i, (word, loading) in enumerate(zip(top_words, top_loadings)):
        # Scale the vector
        arrow_length = np.linalg.norm(loading) * scale_factor
        if arrow_length > 0:
            ax.arrow(0, 0, loading[0] * scale_factor, loading[1] * scale_factor,
                    head_width=0.02, head_length=0.02, fc='red', ec='red', alpha=0.7, linewidth=1.5)
            # Add word label
            ax.text(loading[0] * scale_factor * 1.1, loading[1] * scale_factor * 1.1,
                   word, fontsize=FONT_SIZE_LABELS - 4, alpha=0.8, fontweight='medium',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7, edgecolor='none'))
    
    # Axis labels
    xlabel = f'PC1 ({explained_variance[0]*100:.1f}% variance)' if explained_variance is not None else 'PC1'
    ylabel = f'PC2 ({explained_variance[1]*100:.1f}% variance)' if explained_variance is not None else 'PC2'
    
    ax.set_xlabel(xlabel, fontsize=FONT_SIZE_LABELS, fontweight='medium')
    ax.set_ylabel(ylabel, fontsize=FONT_SIZE_LABELS, fontweight='medium')
    ax.set_title(title, fontsize=FONT_SIZE_TITLE, fontweight='bold', pad=15)
    ax.grid(True, alpha=GRID_ALPHA, linestyle='--')
    ax.axhline(0, color='black', linestyle='-', linewidth=0.5, alpha=0.3)
    ax.axvline(0, color='black', linestyle='-', linewidth=0.5, alpha=0.3)
    
    plt.xticks(fontsize=FONT_SIZE_LABELS - 2)
    plt.yticks(fontsize=FONT_SIZE_LABELS - 2)
    
    plt.tight_layout()
    return fig


def plot_pca_word_vectors(
    loadings_matrix: np.ndarray,
    feature_names: List[str],
    explained_variance: np.ndarray,
    top_n_words: int = 30,
    title: str = "Word Vectors in Principal Component Space"
) -> plt.Figure:
    """Plot word vectors in PC space (first 2 components).
    
    Shows word contributions as vectors in the principal component space.
    
    Args:
        loadings_matrix: (n_features, n_components) loadings matrix.
        feature_names: List of feature (word) names.
        explained_variance: Explained variance ratio for each component.
        top_n_words: Number of top words to display.
        title: Plot title.
        
    Returns:
        Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Calculate overall importance
    importance_scores = np.sum(np.abs(loadings_matrix), axis=1)
    top_indices = np.argsort(importance_scores)[::-1][:top_n_words]
    top_words = [feature_names[i] for i in top_indices]
    top_loadings = loadings_matrix[top_indices, :2]  # First 2 components
    
    # Plot vectors as arrows from origin
    for word, loading in zip(top_words, top_loadings):
        arrow_length = np.linalg.norm(loading)
        if arrow_length > 0:
            # Color by quadrant
            if loading[0] >= 0 and loading[1] >= 0:
                color = '#2A9D8F'  # Green (top-right)
            elif loading[0] < 0 and loading[1] >= 0:
                color = '#E63946'  # Red (top-left)
            elif loading[0] >= 0 and loading[1] < 0:
                color = '#F77F00'  # Orange (bottom-right)
            else:
                color = '#6A4C93'  # Purple (bottom-left)
            
            ax.arrow(0, 0, loading[0], loading[1],
                    head_width=0.02, head_length=0.02, fc=color, ec=color,
                    alpha=0.7, linewidth=1.5)
            
            # Add word label
            ax.text(loading[0] * 1.1, loading[1] * 1.1, word,
                   fontsize=FONT_SIZE_LABELS - 4, alpha=0.8, fontweight='medium',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7, edgecolor='none'))
    
    # Axis labels
    xlabel = f'PC1 ({explained_variance[0]*100:.1f}% variance)' if explained_variance is not None else 'PC1'
    ylabel = f'PC2 ({explained_variance[1]*100:.1f}% variance)' if explained_variance is not None else 'PC2'
    
    ax.set_xlabel(xlabel, fontsize=FONT_SIZE_LABELS, fontweight='medium')
    ax.set_ylabel(ylabel, fontsize=FONT_SIZE_LABELS, fontweight='medium')
    ax.set_title(title, fontsize=FONT_SIZE_TITLE, fontweight='bold', pad=15)
    ax.grid(True, alpha=GRID_ALPHA, linestyle='--')
    ax.axhline(0, color='black', linestyle='-', linewidth=0.5, alpha=0.3)
    ax.axvline(0, color='black', linestyle='-', linewidth=0.5, alpha=0.3)
    
    # Set equal aspect ratio
    ax.set_aspect('equal', adjustable='box')
    
    plt.xticks(fontsize=FONT_SIZE_LABELS - 2)
    plt.yticks(fontsize=FONT_SIZE_LABELS - 2)
    
    plt.tight_layout()
    return fig


def plot_metadata_completeness(
    completeness_stats: Dict[str, Dict[str, Any]],
    title: str = "Metadata Completeness"
) -> plt.Figure:
    """Plot metadata completeness as horizontal bar chart.
    
    Shows the fraction of papers with each metadata field available.
    Uses color gradient (green = high completeness, red = low).
    
    Args:
        completeness_stats: Dictionary from calculate_completeness_stats().
        title: Plot title.
        
    Returns:
        Matplotlib figure.
    """
    if not completeness_stats:
        # Create empty plot if no data
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, 'No metadata available', 
                ha='center', va='center', fontsize=FONT_SIZE_LABELS)
        ax.set_title(title, fontsize=FONT_SIZE_TITLE, fontweight='bold', pad=15)
        return fig
    
    # Prepare data
    fields = []
    percentages = []
    available_counts = []
    total_counts = []
    
    # Field display names
    field_names = {
        'year': 'Year',
        'authors': 'Authors',
        'citations': 'Citations',
        'doi': 'DOI',
        'pdf': 'PDF',
        'venue': 'Venue',
        'abstract': 'Abstract'
    }
    
    for field_key in ['year', 'authors', 'citations', 'doi', 'pdf', 'venue', 'abstract']:
        if field_key in completeness_stats:
            stats = completeness_stats[field_key]
            fields.append(field_names.get(field_key, field_key.capitalize()))
            percentages.append(stats['percentage'])
            available_counts.append(stats['available'])
            total_counts.append(stats['total'])
    
    if not fields:
        # Create empty plot if no valid data
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, 'No metadata available', 
                ha='center', va='center', fontsize=FONT_SIZE_LABELS)
        ax.set_title(title, fontsize=FONT_SIZE_TITLE, fontweight='bold', pad=15)
        return fig
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))
    
    y_pos = np.arange(len(fields))
    
    # Color gradient: green (high) to red (low)
    # Create colormap from green to yellow to red
    colors = []
    for pct in percentages:
        if pct >= 80:
            # Green for high completeness
            colors.append('#2A9D8F')
        elif pct >= 60:
            # Yellow-green
            colors.append('#E9C46A')
        elif pct >= 40:
            # Orange
            colors.append('#F77F00')
        else:
            # Red for low completeness
            colors.append('#E63946')
    
    # Create horizontal bars
    bars = ax.barh(y_pos, percentages, alpha=0.8, color=colors, 
                   edgecolor='#1B4F72', linewidth=EDGE_WIDTH)
    
    # Add percentage labels on bars
    for i, (bar, pct, avail, total) in enumerate(zip(bars, percentages, available_counts, total_counts)):
        width = bar.get_width()
        # Position label at end of bar
        ax.text(width, bar.get_y() + bar.get_height()/2, 
               f' {pct:.1f}% ({avail}/{total})', 
               va='center', fontsize=FONT_SIZE_LEGEND - 1, fontweight='medium')
    
    # Set y-axis labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(fields, fontsize=FONT_SIZE_LABELS - 1)
    
    # Labels and title
    ax.set_xlabel('Completeness (%)', fontsize=FONT_SIZE_LABELS, fontweight='medium')
    ax.set_ylabel('Metadata Field', fontsize=FONT_SIZE_LABELS, fontweight='medium')
    ax.set_title(title, fontsize=FONT_SIZE_TITLE, fontweight='bold', pad=15)
    
    # Set x-axis limits (0-100%)
    ax.set_xlim(0, 105)
    
    # Add grid
    ax.grid(True, alpha=GRID_ALPHA, axis='x', linestyle='--')
    
    # Add vertical line at 100%
    ax.axvline(100, color='#1B4F72', linestyle=':', linewidth=1.5, alpha=0.5)
    
    plt.xticks(fontsize=FONT_SIZE_LABELS - 2)
    plt.yticks(fontsize=FONT_SIZE_LABELS - 2)
    
    plt.tight_layout()
    return fig


def save_plot(fig: plt.Figure, output_path: Path) -> Path:
    """Save plot to file.
    
    Args:
        fig: Matplotlib figure.
        output_path: Output file path.
        
    Returns:
        Path to saved file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Saved plot to {output_path}")
    return output_path


