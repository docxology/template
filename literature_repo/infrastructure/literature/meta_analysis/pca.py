"""PCA analysis of extracted texts.

Performs principal component analysis on paper texts to identify
clusters and relationships between papers.
"""
from __future__ import annotations

from typing import List, Optional, Tuple
from pathlib import Path

import numpy as np

from infrastructure.core.logging_utils import get_logger
from infrastructure.literature.meta_analysis.aggregator import (
    DataAggregator,
    TextCorpus,
)
from infrastructure.literature.meta_analysis.visualizations import (
    plot_pca_2d,
    plot_pca_3d,
    save_plot,
)

logger = get_logger(__name__)

try:
    from sklearn.decomposition import PCA
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. PCA functionality will be limited.")


def extract_text_features(
    corpus: TextCorpus,
    max_features: int = 1000,
    min_df: int = 2,
    max_df: float = 0.95
) -> Tuple[np.ndarray, List[str]]:
    """Extract text features using TF-IDF.
    
    Args:
        corpus: Text corpus from aggregator.
        max_features: Maximum number of features.
        min_df: Minimum document frequency.
        max_df: Maximum document frequency.
        
    Returns:
        Tuple of (feature_matrix, feature_names).
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn is required for text feature extraction")
    
    # Combine titles and abstracts for better representation
    texts = [
        f"{title} {abstract}".strip()
        for title, abstract in zip(corpus.titles, corpus.abstracts)
    ]
    
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        min_df=min_df,
        max_df=max_df,
        stop_words='english',
        ngram_range=(1, 2)  # Include unigrams and bigrams
    )
    
    feature_matrix = vectorizer.fit_transform(texts).toarray()
    feature_names = vectorizer.get_feature_names_out().tolist()
    
    return feature_matrix, feature_names


def compute_pca(
    feature_matrix: np.ndarray,
    n_components: int = 2
) -> Tuple[np.ndarray, PCA]:
    """Compute PCA on feature matrix.
    
    Args:
        feature_matrix: Feature matrix from extract_text_features.
        n_components: Number of principal components.
        
    Returns:
        Tuple of (transformed_data, pca_model).
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn is required for PCA")
    
    pca = PCA(n_components=n_components)
    transformed = pca.fit_transform(feature_matrix)
    
    return transformed, pca


def cluster_papers(
    pca_data: np.ndarray,
    n_clusters: int = 5
) -> np.ndarray:
    """Cluster papers using K-means on PCA space.
    
    Args:
        pca_data: PCA-transformed data.
        n_clusters: Number of clusters.
        
    Returns:
        Cluster labels for each paper.
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn is required for clustering")
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(pca_data)
    
    return labels


def create_pca_2d_plot(
    corpus: Optional[TextCorpus] = None,
    output_path: Optional[Path] = None,
    aggregator: Optional[DataAggregator] = None,
    n_components: int = 2,
    n_clusters: Optional[int] = None,
    format: str = "png"
) -> Path:
    """Create 2D PCA visualization.
    
    Args:
        corpus: Optional text corpus (created if not provided).
        output_path: Optional output path.
        aggregator: Optional DataAggregator instance.
        n_components: Number of PCA components (must be 2 for 2D plot).
        n_clusters: Optional number of clusters for coloring.
        format: Output format (png, svg, pdf).
        
    Returns:
        Path to saved plot.
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn is required for PCA visualization")
    
    if aggregator is None:
        aggregator = DataAggregator()
    
    if corpus is None:
        corpus = aggregator.prepare_text_corpus()
    
    # Extract features
    feature_matrix, feature_names = extract_text_features(corpus)
    
    # Compute PCA
    pca_data, pca_model = compute_pca(feature_matrix, n_components=2)
    
    # Optional clustering
    cluster_labels = None
    if n_clusters is not None:
        cluster_labels = cluster_papers(pca_data, n_clusters=n_clusters)
    
    if output_path is None:
        output_path = Path("data/output/pca_2d." + format)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create plot
    fig = plot_pca_2d(
        pca_data=pca_data,
        titles=corpus.titles,
        years=corpus.years,
        cluster_labels=cluster_labels,
        explained_variance=pca_model.explained_variance_ratio_,
        title="PCA Analysis of Papers (2D)"
    )
    
    return save_plot(fig, output_path)


def create_pca_3d_plot(
    corpus: Optional[TextCorpus] = None,
    output_path: Optional[Path] = None,
    aggregator: Optional[DataAggregator] = None,
    n_clusters: Optional[int] = None,
    format: str = "png"
) -> Path:
    """Create 3D PCA visualization.
    
    Args:
        corpus: Optional text corpus (created if not provided).
        output_path: Optional output path.
        aggregator: Optional DataAggregator instance.
        n_clusters: Optional number of clusters for coloring.
        format: Output format (png, svg, pdf).
        
    Returns:
        Path to saved plot.
    """
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn is required for PCA visualization")
    
    if aggregator is None:
        aggregator = DataAggregator()
    
    if corpus is None:
        corpus = aggregator.prepare_text_corpus()
    
    # Extract features
    feature_matrix, feature_names = extract_text_features(corpus)
    
    # Compute PCA
    pca_data, pca_model = compute_pca(feature_matrix, n_components=3)
    
    # Optional clustering
    cluster_labels = None
    if n_clusters is not None:
        cluster_labels = cluster_papers(pca_data, n_clusters=n_clusters)
    
    if output_path is None:
        output_path = Path("data/output/pca_3d." + format)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create plot
    fig = plot_pca_3d(
        pca_data=pca_data,
        titles=corpus.titles,
        years=corpus.years,
        cluster_labels=cluster_labels,
        explained_variance=pca_model.explained_variance_ratio_,
        title="PCA Analysis of Papers (3D)"
    )
    
    return save_plot(fig, output_path)


def export_pca_loadings(
    corpus: Optional[TextCorpus] = None,
    aggregator: Optional[DataAggregator] = None,
    n_components: int = 5,
    top_n_words: int = 20,
    output_dir: Optional[Path] = None
) -> Dict[str, Path]:
    """Export PCA loadings in multiple formats.
    
    Convenience function that wraps pca_loadings.export_all_loadings.
    
    Args:
        corpus: Optional text corpus (created if not provided).
        aggregator: Optional DataAggregator instance.
        n_components: Number of principal components.
        top_n_words: Number of top words per component.
        output_dir: Output directory (defaults to data/output).
        
    Returns:
        Dictionary mapping format name to output path.
    """
    from infrastructure.literature.meta_analysis.pca_loadings import export_all_loadings
    
    return export_all_loadings(
        corpus=corpus,
        aggregator=aggregator,
        n_components=n_components,
        top_n_words=top_n_words,
        output_dir=output_dir
    )


