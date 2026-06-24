"""Tests for analysis.citation_network module.

Validates citation graph construction, network metrics, community
detection, reference index building, and citation resolution
using small hand-built paper/citation datasets.
"""

import logging

import networkx as nx
import pytest

from analysis.citation_network import (
    _top_scores,
    build_citation_graph,
    build_reference_index,
    compute_network_metrics,
    detect_communities,
    resolve_citations,
)
from literature.models import Citation, Paper


class TestTopScores:
    """The deterministic rounding/ranking helper behind reproducible centrality."""

    def test_rounds_and_takes_top_n(self) -> None:
        scores = {"a": 0.30000000000004, "b": 0.2, "c": 0.1, "d": 0.05}
        result = _top_scores(scores, top_n=2)
        assert list(result) == ["a", "b"]
        # rounded to _SCORE_PRECISION (12 dp), absorbing the 1e-14 noise
        assert result["a"] == 0.3

    def test_ties_break_by_node_id_not_fp_order(self) -> None:
        # Two scores equal after rounding must rank by node id, stably, regardless
        # of insertion order — this is what makes the artifact byte-reproducible.
        forward = _top_scores({"zeta": 0.5000000000000004, "alpha": 0.5}, top_n=2)
        reverse = _top_scores({"alpha": 0.5, "zeta": 0.5000000000000004}, top_n=2)
        assert list(forward) == ["alpha", "zeta"]
        assert list(forward) == list(reverse)


# ── Fixtures ──────────────────────────────────────────────────────────


def _make_papers() -> list[Paper]:
    """Create 5 papers with distinct DOIs for testing."""
    return [
        Paper(
            title="Free Energy Principle",
            abstract="Foundational theory paper",
            year=2010,
            doi="10.1000/p1",
            citation_count=500,
        ),
        Paper(
            title="Active Inference Tutorial",
            abstract="An introduction to active inference",
            year=2017,
            doi="10.1000/p2",
            citation_count=200,
        ),
        Paper(
            title="Deep Active Inference",
            abstract="Scaling active inference with deep nets",
            year=2020,
            doi="10.1000/p3",
            citation_count=80,
        ),
        Paper(
            title="Robot Navigation via AIF",
            abstract="Applying active inference to robot navigation",
            year=2021,
            doi="10.1000/p4",
            citation_count=30,
        ),
        Paper(
            title="Active Inference in Psychiatry",
            abstract="Computational psychiatry with active inference",
            year=2022,
            doi="10.1000/p5",
            citation_count=15,
        ),
    ]


def _make_citations(papers: list[Paper]) -> list[Citation]:
    """Create citation links:
    p2 -> p1, p3 -> p1, p3 -> p2, p4 -> p3, p5 -> p1, p5 -> p2
    """
    ids = [p.canonical_id for p in papers]
    return [
        Citation(source_id=ids[1], target_id=ids[0]),  # p2 cites p1
        Citation(source_id=ids[2], target_id=ids[0]),  # p3 cites p1
        Citation(source_id=ids[2], target_id=ids[1]),  # p3 cites p2
        Citation(source_id=ids[3], target_id=ids[2]),  # p4 cites p3
        Citation(source_id=ids[4], target_id=ids[0]),  # p5 cites p1
        Citation(source_id=ids[4], target_id=ids[1]),  # p5 cites p2
    ]


# ── build_citation_graph ─────────────────────────────────────────────


class TestBuildCitationGraph:
    """Tests for build_citation_graph."""

    def test_node_count(self):
        """Graph has one node per paper."""
        papers = _make_papers()
        citations = _make_citations(papers)
        graph = build_citation_graph(papers, citations)
        assert graph.number_of_nodes() == 5

    def test_edge_count(self):
        """Graph has one edge per citation."""
        papers = _make_papers()
        citations = _make_citations(papers)
        graph = build_citation_graph(papers, citations)
        assert graph.number_of_edges() == 6

    def test_node_attributes(self):
        """Nodes carry title, year, and citation_count attributes."""
        papers = _make_papers()
        citations = _make_citations(papers)
        graph = build_citation_graph(papers, citations)

        p1_id = papers[0].canonical_id
        attrs = graph.nodes[p1_id]
        assert attrs["title"] == "Free Energy Principle"
        assert attrs["year"] == 2010
        assert attrs["citation_count"] == 500

    def test_edge_direction(self):
        """Edges point from citing paper to cited paper."""
        papers = _make_papers()
        citations = _make_citations(papers)
        graph = build_citation_graph(papers, citations)

        p2_id = papers[1].canonical_id
        p1_id = papers[0].canonical_id
        assert graph.has_edge(p2_id, p1_id)
        assert not graph.has_edge(p1_id, p2_id)

    def test_unknown_citation_targets_ignored(self):
        """Citations referencing unknown papers do not create dangling edges."""
        papers = _make_papers()[:2]
        citations = [
            Citation(
                source_id=papers[1].canonical_id,
                target_id=papers[0].canonical_id,
            ),
            Citation(
                source_id=papers[1].canonical_id,
                target_id="doi:10.9999/nonexistent",
            ),
        ]
        graph = build_citation_graph(papers, citations)
        assert graph.number_of_nodes() == 2
        assert graph.number_of_edges() == 1

    def test_empty_papers(self):
        """Empty paper list produces empty graph."""
        graph = build_citation_graph([], [])
        assert graph.number_of_nodes() == 0
        assert graph.number_of_edges() == 0

    def test_no_citations(self):
        """Papers with no citations produce nodes but no edges."""
        papers = _make_papers()
        graph = build_citation_graph(papers, [])
        assert graph.number_of_nodes() == 5
        assert graph.number_of_edges() == 0


# ── compute_network_metrics ──────────────────────────────────────────


class TestComputeNetworkMetrics:
    """Tests for compute_network_metrics."""

    def test_basic_metrics(self):
        """Verify node/edge counts and density."""
        papers = _make_papers()
        citations = _make_citations(papers)
        graph = build_citation_graph(papers, citations)
        metrics = compute_network_metrics(graph)

        assert metrics["num_nodes"] == 5
        assert metrics["num_edges"] == 6
        assert metrics["density"] == pytest.approx(nx.density(graph), abs=1e-6)

    def test_degree_averages(self):
        """Average in-degree and out-degree equal edges/nodes."""
        papers = _make_papers()
        citations = _make_citations(papers)
        graph = build_citation_graph(papers, citations)
        metrics = compute_network_metrics(graph)

        expected_avg = 6 / 5
        assert metrics["avg_in_degree"] == pytest.approx(expected_avg, abs=1e-6)
        assert metrics["avg_out_degree"] == pytest.approx(expected_avg, abs=1e-6)

    def test_pagerank_returns_top_nodes(self):
        """PageRank dict has at most 10 entries and sums to <= 1."""
        papers = _make_papers()
        citations = _make_citations(papers)
        graph = build_citation_graph(papers, citations)
        metrics = compute_network_metrics(graph)

        pr = metrics["pagerank"]
        assert len(pr) <= 10
        assert sum(pr.values()) <= 1.0 + 1e-6

        # p1 should have highest PageRank (most cited)
        p1_id = papers[0].canonical_id
        assert p1_id in pr
        max_node = max(pr, key=pr.get)
        assert max_node == p1_id

    def test_connected_components(self):
        """Verify weakly connected component count."""
        papers = _make_papers()
        citations = _make_citations(papers)
        graph = build_citation_graph(papers, citations)
        metrics = compute_network_metrics(graph)
        assert metrics["connected_components"] == 1

    def test_disconnected_graph(self):
        """Two isolated clusters produce 2 connected components."""
        papers = _make_papers()
        # Only connect p1-p2 and p4-p5 (leaving p3 isolated with p4)
        ids = [p.canonical_id for p in papers]
        citations = [
            Citation(source_id=ids[1], target_id=ids[0]),
            Citation(source_id=ids[3], target_id=ids[4]),
        ]
        graph = build_citation_graph(papers, citations)
        metrics = compute_network_metrics(graph)
        # p1-p2 cluster, p4-p5 cluster, p3 isolated = 3 components
        assert metrics["connected_components"] == 3

    def test_empty_graph(self):
        """Empty graph returns zero metrics."""
        graph = nx.DiGraph()
        metrics = compute_network_metrics(graph)
        assert metrics["num_nodes"] == 0
        assert metrics["num_edges"] == 0
        assert metrics["density"] == 0.0
        assert metrics["avg_in_degree"] == 0.0
        assert metrics["pagerank"] == {}
        assert metrics["connected_components"] == 0


# ── detect_communities ───────────────────────────────────────────────


class TestDetectCommunities:
    """Tests for detect_communities."""

    def test_community_assignment(self):
        """Every node gets assigned to a community."""
        papers = _make_papers()
        citations = _make_citations(papers)
        graph = build_citation_graph(papers, citations)
        communities = detect_communities(graph)

        for paper in papers:
            assert paper.canonical_id in communities

    def test_community_ids_are_integers(self):
        """Community IDs are integers starting from 0."""
        papers = _make_papers()
        citations = _make_citations(papers)
        graph = build_citation_graph(papers, citations)
        communities = detect_communities(graph)

        ids = set(communities.values())
        assert all(isinstance(c, int) for c in ids)
        assert min(ids) == 0

    def test_single_node_returns_empty(self):
        """Graph with < 2 nodes returns empty dict."""
        paper = Paper(title="Solo Paper", doi="10.1000/solo")
        graph = build_citation_graph([paper], [])
        communities = detect_communities(graph)
        assert communities == {}

    def test_empty_graph_returns_empty(self):
        """Empty graph returns empty dict."""
        graph = nx.DiGraph()
        communities = detect_communities(graph)
        assert communities == {}

    def test_two_clusters(self):
        """Two separate clusters should produce at least 2 communities."""
        # Cluster A: p1, p2 connected
        # Cluster B: p3, p4 connected
        papers = [
            Paper(title="A1", doi="10.1/a1"),
            Paper(title="A2", doi="10.1/a2"),
            Paper(title="B1", doi="10.1/b1"),
            Paper(title="B2", doi="10.1/b2"),
        ]
        citations = [
            Citation(
                source_id=papers[0].canonical_id,
                target_id=papers[1].canonical_id,
            ),
            Citation(
                source_id=papers[2].canonical_id,
                target_id=papers[3].canonical_id,
            ),
        ]
        graph = build_citation_graph(papers, citations)
        communities = detect_communities(graph)

        # Papers in cluster A should share a community
        assert communities[papers[0].canonical_id] == communities[papers[1].canonical_id]
        # Papers in cluster B should share a community
        assert communities[papers[2].canonical_id] == communities[papers[3].canonical_id]
        # The two clusters should be different communities
        assert communities[papers[0].canonical_id] != communities[papers[2].canonical_id]


# ── build_citation_graph optional attributes ─────────────────────────


class TestBuildCitationGraphOptionalAttrs:
    """Tests for papers with None title/year/citation_count."""

    def test_minimal_paper_has_no_optional_attrs(self):
        """Paper with only title has no year or optional numeric attrs."""
        paper = Paper(title="Minimal", doi="10.1000/minimal")
        graph = build_citation_graph([paper], [])
        attrs = graph.nodes[paper.canonical_id]
        assert attrs["title"] == "Minimal"
        assert "year" not in attrs
        # citation_count always present (defaults to 0)
        assert attrs["citation_count"] == 0

    def test_none_year_excluded_from_attrs(self):
        """Paper with year=None does not add year attr to node."""
        paper = Paper(title="Test", abstract="", doi="10.1000/none_year")
        graph = build_citation_graph([paper], [])
        attrs = graph.nodes[paper.canonical_id]
        assert "title" in attrs
        assert "year" not in attrs

    def test_all_attrs_present_when_set(self):
        """Paper with all fields populated has all attrs on node."""
        paper = Paper(title="Full", year=2020, doi="10.1000/full", citation_count=42)
        graph = build_citation_graph([paper], [])
        attrs = graph.nodes[paper.canonical_id]
        assert attrs["title"] == "Full"
        assert attrs["year"] == 2020
        assert attrs["citation_count"] == 42


# ── build_reference_index ────────────────────────────────────────────


class TestBuildReferenceIndex:
    """Tests for build_reference_index."""

    def test_doi_mapping(self):
        """DOI creates both 'doi:' prefixed and raw entries."""
        paper = Paper(title="P1", doi="10.1000/test")
        index = build_reference_index([paper])
        cid = paper.canonical_id
        assert index["doi:10.1000/test"] == cid
        assert index["10.1000/test"] == cid

    def test_arxiv_mapping(self):
        """arXiv ID creates both 'arxiv:' prefixed and raw entries."""
        paper = Paper(title="P2", arxiv_id="2301.12345")
        index = build_reference_index([paper])
        cid = paper.canonical_id
        assert index["arxiv:2301.12345"] == cid
        assert index["2301.12345"] == cid

    def test_openalex_full_url_mapping(self):
        """OpenAlex ID as full URL creates short-form entries too."""
        paper = Paper(
            title="P3",
            doi="10.1000/oa",
            openalex_id="https://openalex.org/W12345",
        )
        index = build_reference_index([paper])
        cid = paper.canonical_id
        assert index["openalex:https://openalex.org/W12345"] == cid
        assert index["openalex:W12345"] == cid
        assert index["W12345"] == cid

    def test_multiple_papers(self):
        """Index correctly maps IDs from multiple papers."""
        p1 = Paper(title="P1", doi="10.1/a")
        p2 = Paper(title="P2", doi="10.1/b", s2_id="S2_999")
        index = build_reference_index([p1, p2])
        assert index["doi:10.1/a"] == p1.canonical_id
        assert index["s2:S2_999"] == p2.canonical_id


# ── resolve_citations ────────────────────────────────────────────────


class TestResolveCitations:
    """Tests for resolve_citations."""

    def test_direct_match(self):
        """References matching directly in the index produce citations."""
        p1 = Paper(title="A", doi="10.1/a")
        p2 = Paper(title="B", doi="10.1/b", references=["doi:10.1/a"])
        index = build_reference_index([p1, p2])
        citations = resolve_citations([p2], index, logging.getLogger("test"))
        assert len(citations) == 1
        assert citations[0].source_id == p2.canonical_id
        assert citations[0].target_id == p1.canonical_id

    def test_prefix_stripping_match(self):
        """References with prefixes are resolved by stripping the prefix."""
        p1 = Paper(title="A", doi="10.1/a")
        p2 = Paper(title="B", doi="10.1/b", references=["unknown_prefix:10.1/a"])
        index = build_reference_index([p1, p2])
        citations = resolve_citations([p2], index, logging.getLogger("test"))
        assert len(citations) == 1

    def test_self_references_excluded(self):
        """A paper referencing itself does not produce a citation."""
        p1 = Paper(title="A", doi="10.1/a", references=["doi:10.1/a"])
        index = build_reference_index([p1])
        citations = resolve_citations([p1], index, logging.getLogger("test"))
        assert len(citations) == 0

    def test_unresolved_reference_skipped(self):
        """References not in the index are silently skipped."""
        p1 = Paper(title="A", doi="10.1/a", references=["doi:10.999/nope"])
        index = build_reference_index([p1])
        citations = resolve_citations([p1], index, logging.getLogger("test"))
        assert len(citations) == 0
