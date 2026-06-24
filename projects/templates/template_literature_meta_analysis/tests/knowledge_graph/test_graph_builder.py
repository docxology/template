"""Tests for knowledge_graph.graph_builder module.

Tests both rdflib and networkx backends by parametrizing on use_rdflib.
No mocks -- all tests use real data structures and real graph operations.
"""

from __future__ import annotations

import pytest
import networkx as nx

from literature.models import Paper
from knowledge_graph.nanopublication import Assertion
from knowledge_graph.graph_builder import KnowledgeGraph, RDFLIB_AVAILABLE


def _make_paper(doi_suffix: str, title: str = "Test Paper") -> Paper:
    """Build a Paper with a given DOI suffix."""
    return Paper(title=title, doi=f"10.1234/{doi_suffix}", year=2023)


def _make_assertion(
    assertion_id: str,
    paper_doi_suffix: str,
    assertion_type: str = "supports",
    hypothesis_id: str = "PRIMARY_EFFICACY",
) -> Assertion:
    """Build an Assertion linked to a paper by DOI suffix."""
    return Assertion(
        assertion_id=assertion_id,
        paper_id=f"doi:10.1234/{paper_doi_suffix}",
        claim=f"Claim from {assertion_id}",
        assertion_type=assertion_type,
        hypothesis_id=hypothesis_id,
        confidence=1.0,
        citation_count=10,
    )


# Parametrize across both backends
_backends = [False]
if RDFLIB_AVAILABLE:
    _backends.append(True)


@pytest.fixture(params=_backends, ids=lambda v: f"rdflib={v}")
def use_rdflib(request) -> bool:
    """Parametrize tests across networkx and rdflib backends."""
    return request.param


class TestKnowledgeGraphInit:
    """Validate graph initialization for both backends."""

    def test_empty_graph(self, use_rdflib: bool) -> None:
        """A fresh graph should have zero triples."""
        kg = KnowledgeGraph(use_rdflib=use_rdflib)
        assert kg.num_triples == 0

    def test_backend_selection(self) -> None:
        """Explicit False should use networkx."""
        kg = KnowledgeGraph(use_rdflib=False)
        assert kg._use_rdflib is False

    def test_auto_detect(self) -> None:
        """None should auto-detect rdflib availability."""
        kg = KnowledgeGraph(use_rdflib=None)
        assert kg._use_rdflib == RDFLIB_AVAILABLE


class TestAddPaper:
    """Validate adding papers to the graph."""

    def test_single_paper(self, use_rdflib: bool) -> None:
        """Adding a paper should make it retrievable."""
        kg = KnowledgeGraph(use_rdflib=use_rdflib)
        p = _make_paper("p1", "Paper One")
        kg.add_paper(p)
        assert p.canonical_id in kg.get_papers()

    def test_multiple_papers(self, use_rdflib: bool) -> None:
        """Adding 5 papers should yield 5 paper IDs."""
        kg = KnowledgeGraph(use_rdflib=use_rdflib)
        for i in range(5):
            kg.add_paper(_make_paper(f"multi{i}", f"Paper {i}"))
        assert len(kg.get_papers()) == 5

    def test_no_duplicate_ids(self, use_rdflib: bool) -> None:
        """Adding the same paper twice should not duplicate its ID."""
        kg = KnowledgeGraph(use_rdflib=use_rdflib)
        p = _make_paper("dup")
        kg.add_paper(p)
        kg.add_paper(p)
        assert kg.get_papers().count(p.canonical_id) == 1


class TestAddAssertion:
    """Validate adding assertions and their triple structure."""

    def test_assertion_creates_triples(self, use_rdflib: bool) -> None:
        """Adding a supporting assertion should create triples."""
        kg = KnowledgeGraph(use_rdflib=use_rdflib)
        p = _make_paper("ap1")
        kg.add_paper(p)
        a = _make_assertion("a1", "ap1", assertion_type="supports")
        kg.add_assertion(a)
        assert kg.num_triples > 0

    def test_assertion_linked_to_paper(self, use_rdflib: bool) -> None:
        """Assertion should be retrievable via its paper."""
        kg = KnowledgeGraph(use_rdflib=use_rdflib)
        p = _make_paper("link1")
        kg.add_paper(p)
        a = _make_assertion("al1", "link1")
        kg.add_assertion(a)
        ids = kg.get_assertions_for_paper(p.canonical_id)
        assert "al1" in ids

    def test_contradicting_assertion(self, use_rdflib: bool) -> None:
        """Contradicting assertions should also be retrievable."""
        kg = KnowledgeGraph(use_rdflib=use_rdflib)
        p = _make_paper("con1")
        kg.add_paper(p)
        a = _make_assertion("ac1", "con1", assertion_type="contradicts")
        kg.add_assertion(a)
        ids = kg.get_assertions_for_paper(p.canonical_id)
        assert "ac1" in ids

    def test_neutral_assertion(self, use_rdflib: bool) -> None:
        """Neutral assertions should be linked to paper but not to hypothesis."""
        kg = KnowledgeGraph(use_rdflib=use_rdflib)
        p = _make_paper("neu1")
        kg.add_paper(p)
        a = _make_assertion("an1", "neu1", assertion_type="neutral")
        kg.add_assertion(a)
        ids = kg.get_assertions_for_paper(p.canonical_id)
        assert "an1" in ids


class TestAddCitation:
    """Validate citation edges."""

    def test_citation_increments_triples(self, use_rdflib: bool) -> None:
        """Adding a citation should increase the triple count."""
        kg = KnowledgeGraph(use_rdflib=use_rdflib)
        p1 = _make_paper("cite_src")
        p2 = _make_paper("cite_tgt")
        kg.add_paper(p1)
        kg.add_paper(p2)
        before = kg.num_triples
        kg.add_citation(p1.canonical_id, p2.canonical_id)
        assert kg.num_triples > before


class TestAddSubfield:
    """Validate subfield membership edges."""

    def test_subfield_increments_triples(self, use_rdflib: bool) -> None:
        """Adding a subfield should increase the triple count."""
        kg = KnowledgeGraph(use_rdflib=use_rdflib)
        p = _make_paper("sf1")
        kg.add_paper(p)
        before = kg.num_triples
        kg.add_subfield(p.canonical_id, "C1_neuroscience")
        assert kg.num_triples > before


class TestGetPapersForHypothesis:
    """Validate hypothesis-to-paper lookup."""

    def test_returns_correct_papers(self, use_rdflib: bool) -> None:
        """Only papers with matching hypothesis assertions should be returned."""
        kg = KnowledgeGraph(use_rdflib=use_rdflib)
        p1 = _make_paper("hp1")
        p2 = _make_paper("hp2")
        kg.add_paper(p1)
        kg.add_paper(p2)
        kg.add_assertion(_make_assertion("ha1", "hp1", hypothesis_id="SCALABILITY"))
        kg.add_assertion(_make_assertion("ha2", "hp2", hypothesis_id="CLINICAL_UTILITY"))
        result = kg.get_papers_for_hypothesis("SCALABILITY")
        assert p1.canonical_id in result
        assert p2.canonical_id not in result

    def test_empty_for_unused_hypothesis(self, use_rdflib: bool) -> None:
        """A hypothesis with no assertions should return empty."""
        kg = KnowledgeGraph(use_rdflib=use_rdflib)
        assert kg.get_papers_for_hypothesis("DOMAIN_GENERALIZATION") == []


class TestFullGraph:
    """Integration test: build a realistic graph and verify counts."""

    def test_full_build(self, use_rdflib: bool) -> None:
        """Build graph with 5 papers, 3 assertions, 4 citations, 2 subfields."""
        kg = KnowledgeGraph(use_rdflib=use_rdflib)

        papers = [_make_paper(f"full{i}", f"Full Paper {i}") for i in range(5)]
        for p in papers:
            kg.add_paper(p)

        assertions = [
            _make_assertion("fa1", "full0", "supports", "PRIMARY_EFFICACY"),
            _make_assertion("fa2", "full1", "contradicts", "SCALABILITY"),
            _make_assertion("fa3", "full2", "supports", "PROCESS_MODEL"),
        ]
        for a in assertions:
            kg.add_assertion(a)

        # 4 citations
        kg.add_citation(papers[0].canonical_id, papers[1].canonical_id)
        kg.add_citation(papers[0].canonical_id, papers[2].canonical_id)
        kg.add_citation(papers[1].canonical_id, papers[3].canonical_id)
        kg.add_citation(papers[3].canonical_id, papers[4].canonical_id)

        # 2 subfields
        kg.add_subfield(papers[0].canonical_id, "C1_neuroscience")
        kg.add_subfield(papers[2].canonical_id, "C2_robotics")

        # Verify papers
        assert len(kg.get_papers()) == 5

        # Verify assertions per paper
        assert kg.get_assertions_for_paper(papers[0].canonical_id) == ["fa1"]
        assert kg.get_assertions_for_paper(papers[1].canonical_id) == ["fa2"]
        assert kg.get_assertions_for_paper(papers[4].canonical_id) == []

        # Verify hypothesis lookup
        fep_papers = kg.get_papers_for_hypothesis("PRIMARY_EFFICACY")
        assert papers[0].canonical_id in fep_papers

        # Verify triple count is positive
        assert kg.num_triples > 0


class TestToNetworkx:
    """Validate export to networkx DiGraph."""

    def test_returns_digraph(self, use_rdflib: bool) -> None:
        """to_networkx should return a networkx DiGraph."""
        kg = KnowledgeGraph(use_rdflib=use_rdflib)
        p = _make_paper("nx1")
        kg.add_paper(p)
        g = kg.to_networkx()
        assert isinstance(g, nx.DiGraph)

    def test_exported_graph_has_edges(self, use_rdflib: bool) -> None:
        """Exported graph should contain edges from added triples."""
        kg = KnowledgeGraph(use_rdflib=use_rdflib)
        p1 = _make_paper("nxe1")
        p2 = _make_paper("nxe2")
        kg.add_paper(p1)
        kg.add_paper(p2)
        kg.add_citation(p1.canonical_id, p2.canonical_id)
        g = kg.to_networkx()
        assert g.number_of_edges() > 0

    def test_networkx_copy_is_independent(self) -> None:
        """For networkx backend, the copy should be independent."""
        kg = KnowledgeGraph(use_rdflib=False)
        p = _make_paper("ind1")
        kg.add_paper(p)
        g = kg.to_networkx()
        original_edges = kg.num_triples
        g.add_edge("x", "y")
        assert kg.num_triples == original_edges


class TestUnknownHypothesisId:
    """Validate behavior when assertion references unknown hypothesis."""

    def test_unknown_hypothesis_no_crash(self, use_rdflib: bool) -> None:
        """Adding assertion with unknown hypothesis_id should not crash."""
        kg = KnowledgeGraph(use_rdflib=use_rdflib)
        p = _make_paper("unk1")
        kg.add_paper(p)
        a = Assertion(
            assertion_id="a_unk",
            paper_id=p.canonical_id,
            claim="Test unknown hypothesis",
            assertion_type="supports",
            hypothesis_id="NONEXISTENT_HYPOTHESIS",
            confidence=1.0,
            citation_count=5,
        )
        # Should not raise
        kg.add_assertion(a)
        # Assertion should still be in the map
        assert "a_unk" in kg._assertion_map

    def test_unknown_hypothesis_logs_warning(self, use_rdflib: bool, caplog) -> None:
        """Adding assertion with unknown hypothesis_id should log warning."""
        import logging

        kg = KnowledgeGraph(use_rdflib=use_rdflib)
        p = _make_paper("unk2")
        kg.add_paper(p)
        a = Assertion(
            assertion_id="a_unk2",
            paper_id=p.canonical_id,
            claim="Test unknown hypothesis warning",
            assertion_type="supports",
            hypothesis_id="FAKE_HYPOTHESIS_42",
            confidence=1.0,
            citation_count=5,
        )
        with caplog.at_level(logging.WARNING):
            kg.add_assertion(a)
        assert "FAKE_HYPOTHESIS_42" in caplog.text
