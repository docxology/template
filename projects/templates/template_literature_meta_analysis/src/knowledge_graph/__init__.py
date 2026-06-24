"""Knowledge graph and nanopublication ontology."""

from __future__ import annotations

from .schema import AIF_NAMESPACE
from .nanopublication import Assertion, Nanopublication
from .hypothesis import Hypothesis, score_hypothesis
from .graph_builder import KnowledgeGraph
from .llm_extraction import extract_assertions_llm, LLMConfig
from .extraction import extract_assertions
from .query import (
    query_papers_by_hypothesis,
    query_assertions_for_paper,
    query_supporting_papers,
    query_contradicting_papers,
    count_triples_by_type,
)

__all__ = [
    "AIF_NAMESPACE",
    "Assertion",
    "Nanopublication",
    "Hypothesis",
    "score_hypothesis",
    "KnowledgeGraph",
    "extract_assertions_llm",
    "LLMConfig",
    "extract_assertions",
    "query_papers_by_hypothesis",
    "query_assertions_for_paper",
    "query_supporting_papers",
    "query_contradicting_papers",
    "count_triples_by_type",
]
