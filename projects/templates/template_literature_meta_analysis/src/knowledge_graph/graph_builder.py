"""Knowledge graph builder with rdflib primary and networkx fallback.

Provides the ``KnowledgeGraph`` class that wraps either an ``rdflib.Graph``
(preferred) or a ``networkx.DiGraph`` (fallback) to store the five core
triple patterns of the literature meta-analysis:

    Paper  --aif:asserts-->      Assertion
    Paper  --aif:cites-->        Paper
    Paper  --aif:belongsTo-->    Subfield
    Assertion --aif:supports-->  Hypothesis
    Assertion --aif:contradicts--> Hypothesis
"""

from __future__ import annotations

import logging
from typing import Optional

import networkx as nx

import knowledge_graph.schema as _schema
from knowledge_graph.nanopublication import Assertion
from knowledge_graph.schema import (
    AIF_NAMESPACE,
    ASSERTION_TYPES,
    SUBFIELD_URIS,
)
from literature.models import Paper

logger = logging.getLogger(__name__)

try:
    import rdflib
    from rdflib import Graph as RDFGraph, URIRef, Literal, Namespace

    RDFLIB_AVAILABLE = True
except ImportError:  # pragma: no cover
    RDFLIB_AVAILABLE = False


def _paper_uri(paper_id: str) -> str:
    """Build a URI for a paper node.

    Args:
        paper_id: Canonical paper identifier.

    Returns:
        Full URI string.
    """
    safe_id = paper_id.replace(":", "_").replace("/", "_")
    return f"{AIF_NAMESPACE}paper/{safe_id}"


def _assertion_uri(assertion_id: str) -> str:
    """Build a URI for an assertion node.

    Args:
        assertion_id: Unique assertion identifier.

    Returns:
        Full URI string.
    """
    safe_id = assertion_id.replace(":", "_").replace("/", "_")
    return f"{AIF_NAMESPACE}assertion/{safe_id}"


class KnowledgeGraph:
    """Knowledge graph for the literature corpus.

    Uses ``rdflib`` when available, falls back to ``networkx.DiGraph``.
    The graph stores five kinds of triples encoding papers, assertions,
    citations, subfield membership, and hypothesis relationships.

    Args:
        use_rdflib: Explicitly choose backend. ``None`` auto-detects.
    """

    def __init__(self, use_rdflib: Optional[bool] = None) -> None:
        """Initialize the knowledge graph.

        Args:
            use_rdflib: If ``True`` use rdflib, if ``False`` use networkx,
                if ``None`` auto-detect rdflib availability.
        """
        if use_rdflib is None:
            use_rdflib = RDFLIB_AVAILABLE
        self._use_rdflib: bool = use_rdflib

        if self._use_rdflib:
            self._rdf_graph: RDFGraph = rdflib.Graph()
            self._aif = Namespace(AIF_NAMESPACE)
            self._rdf_graph.bind("aif", self._aif)
        else:
            self._nx_graph: nx.DiGraph = nx.DiGraph()

        # Auxiliary index for fast lookups (used by both backends)
        self._paper_ids: set[str] = set()
        self._assertion_map: dict[str, Assertion] = {}  # assertion_id -> Assertion

    # ------------------------------------------------------------------ #
    # Mutation
    # ------------------------------------------------------------------ #

    def add_paper(self, paper: Paper) -> None:
        """Add a paper node to the graph.

        Args:
            paper: Paper dataclass instance.
        """
        pid = paper.canonical_id
        self._paper_ids.add(pid)

        if self._use_rdflib:
            subj = URIRef(_paper_uri(pid))
            self._rdf_graph.add((subj, URIRef(f"{AIF_NAMESPACE}type"), URIRef(f"{AIF_NAMESPACE}Paper")))
            self._rdf_graph.add((subj, URIRef(f"{AIF_NAMESPACE}title"), Literal(paper.title)))
        else:
            self._nx_graph.add_node(_paper_uri(pid), node_type="Paper", title=paper.title, paper_id=pid)

    def add_assertion(self, assertion: Assertion) -> None:
        """Add an assertion and its relationships to the graph.

        Creates three triples:
            Paper --asserts--> Assertion
            Assertion --supports|contradicts--> Hypothesis  (if applicable)

        Args:
            assertion: Assertion dataclass instance.
        """
        self._assertion_map[assertion.assertion_id] = assertion

        p_uri = _paper_uri(assertion.paper_id)
        a_uri = _assertion_uri(assertion.assertion_id)
        asserts_pred = ASSERTION_TYPES["asserts"]

        # Determine hypothesis-relationship predicate
        rel_pred: Optional[str] = None
        h_uri: Optional[str] = None
        if assertion.assertion_type == "supports":
            rel_pred = ASSERTION_TYPES["supports"]
        elif assertion.assertion_type == "contradicts":
            rel_pred = ASSERTION_TYPES["contradicts"]

        if assertion.hypothesis_id in _schema.HYPOTHESIS_CATEGORIES:
            h_uri = _schema.HYPOTHESIS_CATEGORIES[assertion.hypothesis_id]
        else:
            logger.warning(
                "Unknown hypothesis_id %r — no hypothesis link created for assertion %s",
                assertion.hypothesis_id,
                assertion.assertion_id,
            )

        if self._use_rdflib:
            self._rdf_graph.add((URIRef(p_uri), URIRef(asserts_pred), URIRef(a_uri)))
            self._rdf_graph.add(
                (
                    URIRef(a_uri),
                    URIRef(f"{AIF_NAMESPACE}type"),
                    URIRef(f"{AIF_NAMESPACE}Assertion"),
                )
            )
            self._rdf_graph.add((URIRef(a_uri), URIRef(f"{AIF_NAMESPACE}claim"), Literal(assertion.claim)))
            if rel_pred and h_uri:
                self._rdf_graph.add((URIRef(a_uri), URIRef(rel_pred), URIRef(h_uri)))
        else:
            self._nx_graph.add_node(
                a_uri,
                node_type="Assertion",
                assertion_id=assertion.assertion_id,
                claim=assertion.claim,
            )
            self._nx_graph.add_edge(p_uri, a_uri, predicate="asserts")
            if rel_pred and h_uri:
                self._nx_graph.add_node(h_uri, node_type="Hypothesis")
                self._nx_graph.add_edge(
                    a_uri,
                    h_uri,
                    predicate=assertion.assertion_type,
                )

    def add_citation(self, source_id: str, target_id: str) -> None:
        """Add a citation edge between two papers.

        Args:
            source_id: Canonical ID of the citing paper.
            target_id: Canonical ID of the cited paper.
        """
        s_uri = _paper_uri(source_id)
        t_uri = _paper_uri(target_id)
        cites_pred = ASSERTION_TYPES["cites"]

        if self._use_rdflib:
            self._rdf_graph.add((URIRef(s_uri), URIRef(cites_pred), URIRef(t_uri)))
        else:
            self._nx_graph.add_edge(s_uri, t_uri, predicate="cites")

    def add_subfield(self, paper_id: str, subfield: str) -> None:
        """Assign a paper to a subfield.

        Args:
            paper_id: Canonical paper ID.
            subfield: Key from ``SUBFIELD_URIS``.
        """
        p_uri = _paper_uri(paper_id)
        belongs_pred = ASSERTION_TYPES["belongsTo"]
        sf_uri = SUBFIELD_URIS.get(subfield, f"{AIF_NAMESPACE}subfield/{subfield}")

        if self._use_rdflib:
            self._rdf_graph.add((URIRef(p_uri), URIRef(belongs_pred), URIRef(sf_uri)))
        else:
            self._nx_graph.add_node(sf_uri, node_type="Subfield")
            self._nx_graph.add_edge(p_uri, sf_uri, predicate="belongsTo")

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #

    @property
    def num_triples(self) -> int:
        """Return the total number of triples (edges) in the graph.

        Returns:
            Integer count of triples.
        """
        if self._use_rdflib:
            return len(self._rdf_graph)
        return int(self._nx_graph.number_of_edges())

    def get_papers(self) -> list[str]:
        """Return all paper IDs that have been added.

        Returns:
            List of canonical paper ID strings.
        """
        return sorted(self._paper_ids)

    def get_assertions_for_paper(self, paper_id: str) -> list[str]:
        """Return assertion IDs linked to a given paper.

        Args:
            paper_id: Canonical paper ID.

        Returns:
            List of assertion ID strings.
        """
        p_uri = _paper_uri(paper_id)
        asserts_pred = ASSERTION_TYPES["asserts"]

        result: list[str] = []
        if self._use_rdflib:
            for _, _, obj in self._rdf_graph.triples((URIRef(p_uri), URIRef(asserts_pred), None)):
                # Reverse-lookup assertion_id from the assertion map
                a_uri_str = str(obj)
                for aid, aobj in self._assertion_map.items():
                    if _assertion_uri(aid) == a_uri_str:
                        result.append(aid)
        else:
            if p_uri in self._nx_graph:
                for _, target, data in self._nx_graph.edges(p_uri, data=True):
                    if data.get("predicate") == "asserts":
                        node_data = self._nx_graph.nodes.get(target, {})
                        aid = node_data.get("assertion_id")
                        if aid:
                            result.append(aid)
        return sorted(result)

    def get_papers_for_hypothesis(self, hypothesis_id: str) -> list[str]:
        """Return paper IDs that have assertions related to a hypothesis.

        Args:
            hypothesis_id: Key from ``HYPOTHESIS_CATEGORIES``.

        Returns:
            List of canonical paper ID strings.
        """
        paper_ids: set[str] = set()
        for aid, assertion in self._assertion_map.items():
            if assertion.hypothesis_id == hypothesis_id:
                paper_ids.add(assertion.paper_id)
        return sorted(paper_ids)

    # ------------------------------------------------------------------ #
    # Export
    # ------------------------------------------------------------------ #

    def to_networkx(self) -> nx.DiGraph:
        """Export the graph as a networkx DiGraph.

        If the backend is already networkx, returns a copy.
        If rdflib, converts all triples to networkx edges.

        Returns:
            A ``networkx.DiGraph`` representing the knowledge graph.
        """
        if not self._use_rdflib:
            return self._nx_graph.copy()

        g = nx.DiGraph()
        for s, p, o in self._rdf_graph:
            s_str = str(s)
            p_str = str(p)
            o_str = str(o)
            g.add_edge(s_str, o_str, predicate=p_str)
        return g
