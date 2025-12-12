"""PCA loadings analysis and export.

Extracts and analyzes PCA loadings (word contributions to principal components)
and exports them in multiple formats for interpretation.
"""
from __future__ import annotations

import json
import csv
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import numpy as np

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.meta_analysis.aggregator import (
    DataAggregator,
    TextCorpus,
)
from infrastructure.literature.meta_analysis.pca import (
    extract_text_features,
    compute_pca,
)

logger = get_logger(__name__)

try:
    from sklearn.decomposition import PCA
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. PCA loadings functionality will be limited.")


def extract_pca_loadings(
    corpus: TextCorpus,
    n_components: int = 5,
    max_features: int = 1000,
    min_df: int = 2,
    max_df: float = 0.95
) -> Tuple[np.ndarray, np.ndarray, List[str], PCA]:
    """Extract PCA loadings from text corpus.
    
    Args:
        corpus: Text corpus from aggregator.
        n_components: Number of principal components to extract.
        max_features: Maximum number of TF-IDF features.
        min_df: Minimum document frequency.
        max_df: Maximum document frequency.
        
    Returns:
        Tuple of (loadings_matrix, transformed_data, feature_names, pca_model).
        loadings_matrix: (n_features, n_components) array of loadings.
        transformed_data: (n_samples, n_components) PCA-transformed data.
        feature_names: List of feature (word) names.
        pca_model: Fitted PCA model.
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn is required for PCA loadings extraction")
    
    # Extract features
    feature_matrix, feature_names = extract_text_features(
        corpus, max_features=max_features, min_df=min_df, max_df=max_df
    )
    
    # Compute PCA
    transformed_data, pca_model = compute_pca(feature_matrix, n_components=n_components)
    
    # Extract loadings (components_ is already transposed: n_components x n_features)
    # We want n_features x n_components for easier interpretation
    loadings_matrix = pca_model.components_.T
    
    return loadings_matrix, transformed_data, feature_names, pca_model


def get_top_words_per_component(
    loadings_matrix: np.ndarray,
    feature_names: List[str],
    n_components: int,
    top_n: int = 20
) -> Dict[int, List[Tuple[str, float]]]:
    """Get top N words (by absolute loading) for each component.
    
    Args:
        loadings_matrix: (n_features, n_components) loadings matrix.
        feature_names: List of feature names.
        n_components: Number of components.
        top_n: Number of top words per component.
        
    Returns:
        Dictionary mapping component index to list of (word, loading) tuples.
    """
    top_words = {}
    
    for comp_idx in range(n_components):
        # Get loadings for this component
        component_loadings = loadings_matrix[:, comp_idx]
        
        # Get absolute values and sort
        abs_loadings = np.abs(component_loadings)
        top_indices = np.argsort(abs_loadings)[::-1][:top_n]
        
        # Extract top words with their loadings
        top_words[comp_idx] = [
            (feature_names[idx], float(component_loadings[idx]))
            for idx in top_indices
        ]
    
    return top_words


def export_loadings_csv(
    loadings_matrix: np.ndarray,
    feature_names: List[str],
    n_components: int,
    output_path: Path
) -> Path:
    """Export PCA loadings to CSV format.
    
    Args:
        loadings_matrix: (n_features, n_components) loadings matrix.
        feature_names: List of feature names.
        n_components: Number of components.
        output_path: Output file path.
        
    Returns:
        Path to saved CSV file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header row
        header = ['Word'] + [f'PC{i+1}' for i in range(n_components)]
        writer.writerow(header)
        
        # Data rows
        for word_idx, word in enumerate(feature_names):
            row = [word] + [
                f'{loadings_matrix[word_idx, comp_idx]:.6f}'
                for comp_idx in range(n_components)
            ]
            writer.writerow(row)
    
    logger.info(f"Exported PCA loadings to CSV: {output_path}")
    return output_path


def export_loadings_json(
    loadings_matrix: np.ndarray,
    feature_names: List[str],
    n_components: int,
    top_words: Dict[int, List[Tuple[str, float]]],
    explained_variance: np.ndarray,
    output_path: Path
) -> Path:
    """Export PCA loadings to JSON format with metadata.
    
    Args:
        loadings_matrix: (n_features, n_components) loadings matrix.
        feature_names: List of feature names.
        n_components: Number of components.
        top_words: Dictionary of top words per component.
        explained_variance: Explained variance ratio for each component.
        output_path: Output file path.
        
    Returns:
        Path to saved JSON file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare data structure
    data = {
        'metadata': {
            'n_features': len(feature_names),
            'n_components': n_components,
            'explained_variance': {
                f'PC{i+1}': float(explained_variance[i])
                for i in range(n_components)
            },
            'total_variance_explained': float(np.sum(explained_variance))
        },
        'components': {}
    }
    
    # Add component data
    for comp_idx in range(n_components):
        component_data = {
            'explained_variance': float(explained_variance[comp_idx]),
            'top_words': [
                {'word': word, 'loading': loading}
                for word, loading in top_words.get(comp_idx, [])
            ],
            'all_loadings': {
                feature_names[i]: float(loadings_matrix[i, comp_idx])
                for i in range(len(feature_names))
            }
        }
        data['components'][f'PC{comp_idx+1}'] = component_data
    
    # Write JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Exported PCA loadings to JSON: {output_path}")
    return output_path


def export_loadings_summary_markdown(
    top_words: Dict[int, List[Tuple[str, float]]],
    explained_variance: np.ndarray,
    output_path: Path
) -> Path:
    """Export human-readable PCA loadings summary in Markdown format.
    
    Args:
        top_words: Dictionary of top words per component.
        explained_variance: Explained variance ratio for each component.
        output_path: Output file path.
        
    Returns:
        Path to saved Markdown file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    lines = [
        "# PCA Loadings Summary",
        "",
        "This document provides an interpretation of the Principal Component Analysis (PCA) ",
        "loadings, showing which words contribute most to each principal component.",
        "",
        "## Overview",
        "",
        f"- **Total Components Analyzed**: {len(explained_variance)}",
        f"- **Total Variance Explained**: {np.sum(explained_variance)*100:.2f}%",
        "",
        "## Component Analysis",
        ""
    ]
    
    # Add component details
    for comp_idx in range(len(explained_variance)):
        var_explained = explained_variance[comp_idx] * 100
        lines.extend([
            f"### Principal Component {comp_idx + 1} (PC{comp_idx + 1})",
            "",
            f"- **Variance Explained**: {var_explained:.2f}%",
            "",
            "#### Top Contributing Words",
            "",
            "| Rank | Word | Loading |",
            "|------|------|---------|"
        ])
        
        # Add top words
        if comp_idx in top_words:
            for rank, (word, loading) in enumerate(top_words[comp_idx], 1):
                lines.append(f"| {rank} | {word} | {loading:.4f} |")
        else:
            lines.append("| - | No data available | - |")
        
        lines.extend(["", "#### Interpretation", ""])
        
        # Generate interpretation
        if comp_idx in top_words and top_words[comp_idx]:
            positive_words = [w for w, l in top_words[comp_idx] if l > 0][:5]
            negative_words = [w for w, l in top_words[comp_idx] if l < 0][:5]
            
            if positive_words:
                lines.append(f"**Positive contributors** (high loading): {', '.join(positive_words)}")
            if negative_words:
                lines.append(f"**Negative contributors** (low loading): {', '.join(negative_words)}")
        
        lines.extend(["", "---", ""])
    
    # Add summary
    lines.extend([
        "## Summary",
        "",
        "The loadings indicate which words (features) are most strongly associated with each ",
        "principal component. Positive loadings indicate words that increase with the component, ",
        "while negative loadings indicate words that decrease.",
        "",
        "### Key Insights",
        "",
        "- Components with higher explained variance capture more of the overall variation in the corpus.",
        "- Words with large absolute loadings are the most important for that component.",
        "- Components can be interpreted as themes or topics in the literature.",
        ""
    ])
    
    # Write markdown
    output_path.write_text('\n'.join(lines), encoding='utf-8')
    logger.info(f"Exported PCA loadings summary to Markdown: {output_path}")
    return output_path


def export_word_importance_rankings(
    loadings_matrix: np.ndarray,
    feature_names: List[str],
    n_components: int,
    output_path: Path
) -> Path:
    """Export word importance rankings across all components.
    
    Args:
        loadings_matrix: (n_features, n_components) loadings matrix.
        feature_names: List of feature names.
        n_components: Number of components.
        output_path: Output file path.
        
    Returns:
        Path to saved CSV file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Calculate overall importance (sum of absolute loadings across components)
    importance_scores = np.sum(np.abs(loadings_matrix), axis=1)
    
    # Sort by importance
    sorted_indices = np.argsort(importance_scores)[::-1]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(['Rank', 'Word', 'Total Importance Score'] + 
                       [f'PC{i+1} Loading' for i in range(n_components)])
        
        # Data rows
        for rank, word_idx in enumerate(sorted_indices, 1):
            row = [
                rank,
                feature_names[word_idx],
                f'{importance_scores[word_idx]:.6f}'
            ] + [
                f'{loadings_matrix[word_idx, comp_idx]:.6f}'
                for comp_idx in range(n_components)
            ]
            writer.writerow(row)
    
    logger.info(f"Exported word importance rankings to CSV: {output_path}")
    return output_path


def export_all_loadings(
    corpus: Optional[TextCorpus] = None,
    aggregator: Optional[DataAggregator] = None,
    n_components: int = 5,
    top_n_words: int = 20,
    output_dir: Optional[Path] = None
) -> Dict[str, Path]:
    """Export all PCA loadings in multiple formats.
    
    Args:
        corpus: Optional text corpus (created if not provided).
        aggregator: Optional DataAggregator instance.
        n_components: Number of principal components.
        top_n_words: Number of top words per component to include.
        output_dir: Output directory (defaults to data/output).
        
    Returns:
        Dictionary mapping format name to output path.
    """
    if aggregator is None:
        aggregator = DataAggregator()
    
    if corpus is None:
        corpus = aggregator.prepare_text_corpus()
    
    if output_dir is None:
        output_dir = Path("data/output")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract loadings
    loadings_matrix, transformed_data, feature_names, pca_model = extract_pca_loadings(
        corpus, n_components=n_components
    )
    
    # Get top words
    top_words = get_top_words_per_component(
        loadings_matrix, feature_names, n_components, top_n=top_n_words
    )
    
    # Export in all formats
    outputs = {}
    
    # CSV format
    csv_path = export_loadings_csv(
        loadings_matrix, feature_names, n_components,
        output_dir / "pca_loadings.csv"
    )
    outputs['csv'] = csv_path
    
    # JSON format
    json_path = export_loadings_json(
        loadings_matrix, feature_names, n_components, top_words,
        pca_model.explained_variance_ratio_,
        output_dir / "pca_loadings.json"
    )
    outputs['json'] = json_path
    
    # Markdown summary
    md_path = export_loadings_summary_markdown(
        top_words, pca_model.explained_variance_ratio_,
        output_dir / "pca_loadings_summary.md"
    )
    outputs['markdown'] = md_path
    
    # Word importance rankings
    rankings_path = export_word_importance_rankings(
        loadings_matrix, feature_names, n_components,
        output_dir / "word_importance_rankings.csv"
    )
    outputs['rankings'] = rankings_path
    
    return outputs


def create_loadings_visualizations(
    corpus: Optional[TextCorpus] = None,
    aggregator: Optional[DataAggregator] = None,
    n_components: int = 5,
    top_n_words: int = 20,
    output_dir: Optional[Path] = None,
    format: str = "png"
) -> Dict[str, Path]:
    """Create all PCA loadings visualizations.
    
    Generates heatmap, barplots, biplot, and word vectors visualizations.
    
    Args:
        corpus: Optional text corpus (created if not provided).
        aggregator: Optional DataAggregator instance.
        n_components: Number of principal components.
        top_n_words: Number of top words per component to include.
        output_dir: Output directory (defaults to data/output).
        format: Output format (png, svg, pdf).
        
    Returns:
        Dictionary mapping visualization name to output path.
    """
    if aggregator is None:
        aggregator = DataAggregator()
    
    if corpus is None:
        corpus = aggregator.prepare_text_corpus()
    
    if output_dir is None:
        output_dir = Path("data/output")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract loadings
    loadings_matrix, transformed_data, feature_names, pca_model = extract_pca_loadings(
        corpus, n_components=n_components
    )
    
    # Get top words
    top_words = get_top_words_per_component(
        loadings_matrix, feature_names, n_components, top_n=top_n_words
    )
    
    outputs = {}
    
    # Import visualization functions
    from infrastructure.literature.meta_analysis.visualizations import (
        plot_pca_loadings_heatmap,
        plot_pca_loadings_barplot,
        plot_pca_biplot,
        plot_pca_word_vectors,
        save_plot,
    )
    
    try:
        # 1. Heatmap
        logger.info("Generating PCA loadings heatmap...")
        fig_heatmap = plot_pca_loadings_heatmap(
            loadings_matrix, feature_names, n_components,
            top_n_words=min(50, len(feature_names)),
            title="PCA Loadings Heatmap (Top Words)"
        )
        heatmap_path = save_plot(fig_heatmap, output_dir / f"pca_loadings_heatmap.{format}")
        outputs['heatmap'] = heatmap_path
        
        # 2. Barplots
        logger.info("Generating PCA loadings barplots...")
        fig_barplots = plot_pca_loadings_barplot(
            top_words, pca_model.explained_variance_ratio_,
            n_components=n_components, top_n_words=top_n_words,
            title="Top Words per Principal Component"
        )
        barplots_path = save_plot(fig_barplots, output_dir / f"pca_loadings_barplots.{format}")
        outputs['barplots'] = barplots_path
        
        # 3. Biplot (requires 2D PCA data)
        if transformed_data.shape[1] >= 2:
            logger.info("Generating PCA biplot...")
            # Compute 2D PCA for biplot
            from infrastructure.literature.meta_analysis.pca import (
                extract_text_features,
                compute_pca,
            )
            feature_matrix_2d, _ = extract_text_features(corpus)
            pca_data_2d, pca_model_2d = compute_pca(feature_matrix_2d, n_components=2)
            
            fig_biplot = plot_pca_biplot(
                pca_data_2d, loadings_matrix, feature_names,
                corpus.titles, corpus.years,
                cluster_labels=None,  # Can add clustering if needed
                explained_variance=pca_model_2d.explained_variance_ratio_,
                top_n_words=top_n_words,
                title="PCA Biplot (Papers and Word Vectors)"
            )
            biplot_path = save_plot(fig_biplot, output_dir / f"pca_biplot.{format}")
            outputs['biplot'] = biplot_path
        
        # 4. Word vectors plot
        logger.info("Generating PCA word vectors plot...")
        fig_vectors = plot_pca_word_vectors(
            loadings_matrix, feature_names,
            pca_model.explained_variance_ratio_,
            top_n_words=min(30, len(feature_names)),
            title="Word Vectors in Principal Component Space"
        )
        vectors_path = save_plot(fig_vectors, output_dir / f"pca_word_vectors.{format}")
        outputs['word_vectors'] = vectors_path
        
    except Exception as e:
        logger.warning(f"Failed to generate some loadings visualizations: {e}")
    
    return outputs


