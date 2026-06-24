"""Citation network analysis using networkx.

Builds directed citation graphs and computes network-level metrics
including PageRank, degree distributions, and community structure.
"""

from __future__ import annotations

import logging

import networkx as nx

from literature.models import Citation, Paper

logger = logging.getLogger(__name__)


def build_citation_graph(papers: list[Paper], citations: list[Citation]) -> nx.DiGraph:
    """Build a directed citation graph from papers and citation links.

    Each paper becomes a node with attributes (title, year, citation_count).
    Each citation becomes a directed edge from source to target.

    Args:
        papers: List of Paper objects to include as nodes.
        citations: List of Citation objects defining directed edges.

    Returns:
        Directed graph with paper nodes and citation edges.
    """
    graph = nx.DiGraph()

    for paper in papers:
        attrs = {}
        if paper.title is not None:
            attrs["title"] = paper.title
        if paper.year is not None:
            attrs["year"] = int(paper.year)
        if paper.citation_count is not None:
            attrs["citation_count"] = int(paper.citation_count)

        graph.add_node(paper.canonical_id, **attrs)

    for citation in citations:
        # Only add edges between nodes that exist in the graph
        if graph.has_node(citation.source_id) and graph.has_node(citation.target_id):
            graph.add_edge(citation.source_id, citation.target_id)

    return graph


# Decimal places to round centrality scores to before serialization. Well below any
# analytically meaningful precision; exists only to absorb last-ULP threaded-BLAS
# floating-point noise so artifacts are byte-reproducible across runs.
_SCORE_PRECISION = 12


def _top_scores(scores: dict[str, float], top_n: int = 10) -> dict[str, float]:
    """Round and rank centrality scores deterministically.

    Rounds each score to ``_SCORE_PRECISION`` decimals and returns the ``top_n``
    nodes ordered by descending score with the node id as a stable tiebreaker, so
    both membership and order are reproducible regardless of FP summation order.
    """
    rounded = {node: round(float(score), _SCORE_PRECISION) for node, score in scores.items()}
    ranked = sorted(rounded.items(), key=lambda kv: (-kv[1], kv[0]))
    return {node: score for node, score in ranked[:top_n]}


def compute_network_metrics(
    graph: nx.DiGraph,
    hits_max_iter: int = 200,
    hits_tol: float = 1e-06,
) -> dict:
    """Compute summary metrics for a citation network.

    Args:
        graph: Directed citation graph.
        hits_max_iter: Maximum iterations for HITS convergence (default: 200).
        hits_tol: Convergence tolerance for HITS algorithm (default: 1e-06).

    Returns:
        Dictionary with keys:
            num_nodes: Number of nodes
            num_edges: Number of edges
            density: Graph density
            avg_in_degree: Average in-degree
            avg_out_degree: Average out-degree
            pagerank: Dict of top-10 nodes by PageRank score
            connected_components: Number of weakly connected components
    """
    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()

    density = nx.density(graph)

    if num_nodes > 0:
        in_degrees = [d for _, d in graph.in_degree()]
        out_degrees = [d for _, d in graph.out_degree()]
        avg_in_degree = sum(in_degrees) / num_nodes
        avg_out_degree = sum(out_degrees) / num_nodes
        max_in_degree = max(in_degrees) if in_degrees else 0
        max_out_degree = max(out_degrees) if out_degrees else 0
    else:
        avg_in_degree = 0.0
        avg_out_degree = 0.0
        max_in_degree = 0
        max_out_degree = 0

    # PageRank and HITS.
    #
    # Centrality scores are computed by iterative matrix-vector products whose
    # floating-point summation order is not associative under threaded BLAS, so raw
    # scores can differ at the last ULP between runs. For byte-reproducible
    # artifacts we (1) round each score to a fixed precision and (2) break ranking
    # ties deterministically by node id, so both the top-10 membership AND its order
    # are stable across runs. The rounding is well below any analytically meaningful
    # precision (~1e-12 on scores of order 1e-1).
    if num_nodes > 0:
        pagerank = _top_scores(nx.pagerank(graph))
        try:
            h, a = nx.hits(graph, max_iter=hits_max_iter, tol=hits_tol)
            hubs = _top_scores(h)
            authorities = _top_scores(a)
        except Exception as e:  # noqa: BLE001 -- safety net: HITS non-convergence must not abort metrics
            logger.error("HITS algorithm failed: %s", e)
            hubs = {}
            authorities = {}
    else:
        pagerank = {}
        hubs, authorities = {}, {}

    # Weakly connected components
    if num_nodes > 0:
        connected_components = nx.number_weakly_connected_components(graph)
    else:
        connected_components = 0

    return {
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "density": density,
        "avg_in_degree": avg_in_degree,
        "avg_out_degree": avg_out_degree,
        "max_in_degree": max_in_degree,
        "max_out_degree": max_out_degree,
        "pagerank": pagerank,
        "hubs": hubs,
        "authorities": authorities,
        "connected_components": connected_components,
    }


def detect_communities(graph: nx.DiGraph) -> dict[str, int]:
    """Detect communities using greedy modularity on the undirected projection.

    Args:
        graph: Directed citation graph.

    Returns:
        Dictionary mapping node_id to community_id (integer).
        Returns empty dict if graph has fewer than 2 nodes.
    """
    if graph.number_of_nodes() < 2:
        return {}

    undirected = graph.to_undirected()

    # Remove isolated nodes for community detection, add them back after
    communities = nx.community.greedy_modularity_communities(undirected)

    node_to_community: dict[str, int] = {}
    for community_id, community in enumerate(communities):
        for node in community:
            node_to_community[node] = community_id

    n_communities = len(set(node_to_community.values()))
    logger.info(
        "Community detection: %d communities from %d nodes",
        n_communities,
        graph.number_of_nodes(),
    )
    return node_to_community


def build_reference_index(papers: list[Paper]) -> dict[str, str]:
    """Build a lookup index mapping raw identifiers to corpus canonical IDs.

    Creates mappings from DOI, arXiv ID, S2 ID, and OpenAlex ID to the
    canonical_id of papers in the corpus. This enables cross-matching
    references that use source-specific identifier formats.

    Args:
        papers: List of Paper objects in the corpus.

    Returns:
        Dictionary mapping raw identifier strings to canonical IDs.
    """
    index: dict[str, str] = {}
    for paper in papers:
        cid = paper.canonical_id
        # Map all known IDs to canonical_id
        if paper.doi:
            index[f"doi:{paper.doi}"] = cid
            index[paper.doi] = cid
        if paper.arxiv_id:
            index[f"arxiv:{paper.arxiv_id}"] = cid
            index[paper.arxiv_id] = cid
        if paper.s2_id:
            index[f"s2:{paper.s2_id}"] = cid
            index[paper.s2_id] = cid
        if paper.openalex_id:
            index[f"openalex:{paper.openalex_id}"] = cid
            # OpenAlex IDs sometimes appear as full URLs
            if paper.openalex_id.startswith("https://openalex.org/"):
                short_id = paper.openalex_id.replace("https://openalex.org/", "")
                index[f"openalex:{short_id}"] = cid
                index[short_id] = cid
            index[paper.openalex_id] = cid
    logger.info(
        "Reference index built: %d entries from %d papers",
        len(index),
        len(papers),
    )
    return index


def resolve_citations(
    papers: list[Paper],
    ref_index: dict[str, str],
    logger: logging.Logger,
) -> list[Citation]:
    """Resolve paper references to Citation objects using the reference index.

    For each paper's references, attempts to match against known corpus
    identifiers via the reference index. Logs match statistics.

    Args:
        papers: List of papers with references.
        ref_index: Lookup index from build_reference_index.
        logger: Logger for statistics output.

    Returns:
        List of Citation objects with resolved source and target IDs.
    """
    citations: list[Citation] = []
    total_refs = 0
    matched_refs = 0

    for paper in papers:
        for ref_id in paper.references:
            total_refs += 1
            # Try direct match
            resolved = ref_index.get(ref_id)
            if resolved is None:
                # Try stripping prefix (e.g., "openalex:W123" -> "W123")
                if ":" in ref_id:
                    raw = ref_id.split(":", 1)[1]
                    resolved = ref_index.get(raw)

            if resolved and resolved != paper.canonical_id:
                citations.append(Citation(source_id=paper.canonical_id, target_id=resolved))
                matched_refs += 1

    logger.info(
        "Reference normalization: %d/%d refs resolved to corpus papers (%.1f%%)",
        matched_refs,
        total_refs,
        (matched_refs / total_refs * 100) if total_refs > 0 else 0,
    )
    return citations
