"""Re-export shim for advanced visualization functions."""

from __future__ import annotations

from template_literature_meta_analysis.visualization.advanced.embeddings import (
    plot_dendrogram,
    plot_pca_embeddings,
    plot_term_heatmap,
)
from template_literature_meta_analysis.visualization.advanced.topics import (
    plot_cooccurrence_matrix,
    plot_topic_term_bars,
)
from template_literature_meta_analysis.visualization.advanced.word_cloud import plot_word_cloud

__all__ = [
    "plot_word_cloud",
    "plot_pca_embeddings",
    "plot_term_heatmap",
    "plot_dendrogram",
    "plot_topic_term_bars",
    "plot_cooccurrence_matrix",
]
