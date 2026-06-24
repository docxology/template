"""Re-export shim for advanced visualization functions."""

from __future__ import annotations

from visualization.advanced.embeddings import (
    plot_dendrogram,
    plot_pca_embeddings,
    plot_term_heatmap,
)
from visualization.advanced.topics import plot_cooccurrence_matrix, plot_topic_term_bars
from visualization.advanced.word_cloud import plot_word_cloud

__all__ = [
    "plot_word_cloud",
    "plot_pca_embeddings",
    "plot_term_heatmap",
    "plot_dendrogram",
    "plot_topic_term_bars",
    "plot_cooccurrence_matrix",
]
