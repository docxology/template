"""Publication-ready visualization generation."""

from __future__ import annotations

from .style import VIZ_CONFIG
from .field_overview import plot_field_summary, plot_subfield_distribution
from .citation_plots import plot_citation_network, plot_degree_distribution
from .temporal_plots import plot_growth_curve, plot_subfield_timeline
from .hypothesis_charts import (
    plot_hypothesis_dashboard,
    plot_evidence_timeline,
    plot_assertion_type_breakdown,
    plot_assertion_summary,
)
from .advanced_plots import (
    plot_word_cloud,
    plot_pca_embeddings,
    plot_term_heatmap,
    plot_dendrogram,
    plot_topic_term_bars,
    plot_cooccurrence_matrix,
)

__all__ = [
    "VIZ_CONFIG",
    "plot_field_summary",
    "plot_subfield_distribution",
    "plot_citation_network",
    "plot_degree_distribution",
    "plot_growth_curve",
    "plot_subfield_timeline",
    "plot_hypothesis_dashboard",
    "plot_evidence_timeline",
    "plot_assertion_type_breakdown",
    "plot_assertion_summary",
    "plot_word_cloud",
    "plot_pca_embeddings",
    "plot_term_heatmap",
    "plot_dendrogram",
    "plot_topic_term_bars",
    "plot_cooccurrence_matrix",
]
