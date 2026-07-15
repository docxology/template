"""Query helper functions for the literature knowledge graph.

Provides high-level query functions that operate on a ``KnowledgeGraph``
instance, abstracting away the backend (rdflib vs. networkx).
"""

from __future__ import annotations

from knowledge_graph.graph_builder import KnowledgeGraph
from knowledge_graph.schema import ASSERTION_TYPES

try:
    from rdflib import URIRef
except ImportError:  # pragma: no cover
    pass


def query_papers_by_hypothesis(kg: KnowledgeGraph, hypothesis_id: str) -> list[str]:
    """Return paper IDs that have assertions related to a hypothesis.

    Delegates to the KnowledgeGraph's own index-based lookup for
    consistent results across both backends.

    Args:
        kg: The knowledge graph to query.
        hypothesis_id: Key from ``HYPOTHESIS_CATEGORIES``.

    Returns:
        Sorted list of canonical paper ID strings.
    """
    return list(kg.get_papers_for_hypothesis(hypothesis_id))


def query_assertions_for_paper(kg: KnowledgeGraph, paper_id: str) -> list[str]:
    """Return assertion IDs for a given paper.

    Args:
        kg: The knowledge graph to query.
        paper_id: Canonical paper ID.

    Returns:
        Sorted list of assertion ID strings.
    """
    return list(kg.get_assertions_for_paper(paper_id))


def query_supporting_papers(kg: KnowledgeGraph, hypothesis_id: str) -> list[str]:
    """Return paper IDs with supporting assertions for a hypothesis.

    Only papers whose assertions have ``assertion_type == "supports"``
    for the given hypothesis are returned.

    Args:
        kg: The knowledge graph to query.
        hypothesis_id: Key from ``HYPOTHESIS_CATEGORIES``.

    Returns:
        Sorted list of canonical paper ID strings.
    """
    paper_ids: set[str] = set()
    for aid, assertion in kg._assertion_map.items():
        if assertion.hypothesis_id == hypothesis_id and assertion.assertion_type == "supports":
            paper_ids.add(assertion.paper_id)
    return sorted(paper_ids)


def query_contradicting_papers(kg: KnowledgeGraph, hypothesis_id: str) -> list[str]:
    """Return paper IDs with contradicting assertions for a hypothesis.

    Only papers whose assertions have ``assertion_type == "contradicts"``
    for the given hypothesis are returned.

    Args:
        kg: The knowledge graph to query.
        hypothesis_id: Key from ``HYPOTHESIS_CATEGORIES``.

    Returns:
        Sorted list of canonical paper ID strings.
    """
    paper_ids: set[str] = set()
    for aid, assertion in kg._assertion_map.items():
        if assertion.hypothesis_id == hypothesis_id and assertion.assertion_type == "contradicts":
            paper_ids.add(assertion.paper_id)
    return sorted(paper_ids)


def count_triples_by_type(kg: KnowledgeGraph) -> dict[str, int]:
    """Count triples grouped by assertion type predicate.

    Counts edges whose predicate matches one of the five core
    ``ASSERTION_TYPES`` (asserts, cites, belongsTo, supports, contradicts).

    Args:
        kg: The knowledge graph to query.

    Returns:
        Dictionary mapping predicate name to count.
    """
    counts: dict[str, int] = {name: 0 for name in ASSERTION_TYPES}

    if kg._use_rdflib:
        for pred_name, pred_uri in ASSERTION_TYPES.items():
            for _ in kg._rdf_graph.triples((None, URIRef(pred_uri), None)):
                counts[pred_name] += 1
    else:
        for u, v, data in kg._nx_graph.edges(data=True):
            pred = data.get("predicate", "")
            if pred in counts:
                counts[pred] += 1

    return counts
