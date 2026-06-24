"""Bibliometric, temporal, and text-analytics pipelines."""

from __future__ import annotations

from .text_processing import tokenize, remove_stopwords, build_tfidf_matrix
from .topic_modeling import fit_nmf_topics, get_document_topics
from .citation_network import (
    build_citation_graph,
    compute_network_metrics,
    detect_communities,
    build_reference_index,
    resolve_citations,
)
from .temporal_analysis import compute_temporal_metrics, estimate_growth_rate
from .subfield_classifier import classify_paper, classify_corpus

__all__ = [
    "tokenize",
    "remove_stopwords",
    "build_tfidf_matrix",
    "fit_nmf_topics",
    "get_document_topics",
    "build_citation_graph",
    "compute_network_metrics",
    "detect_communities",
    "build_reference_index",
    "resolve_citations",
    "compute_temporal_metrics",
    "estimate_growth_rate",
    "classify_paper",
    "classify_corpus",
]
