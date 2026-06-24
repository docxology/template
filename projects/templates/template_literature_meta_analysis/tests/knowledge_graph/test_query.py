"""Tests for knowledge_graph.query module.

Builds a small knowledge graph with known structure and verifies all
query helper functions return expected results.
No mocks -- all tests use real graph operations on real data.
"""

from __future__ import annotations

import pytest

from literature.models import Paper
from knowledge_graph.nanopublication import Assertion
from knowledge_graph.graph_builder import KnowledgeGraph, RDFLIB_AVAILABLE
from knowledge_graph.query import (
    query_papers_by_hypothesis,
    query_assertions_for_paper,
    query_supporting_papers,
    query_contradicting_papers,
    count_triples_by_type,
)


def _make_paper(doi_suffix: str, title: str = "Test Paper") -> Paper:
    """Build a Paper with a given DOI suffix."""
    return Paper(title=title, doi=f"10.5555/{doi_suffix}", year=2023)


def _make_assertion(
    assertion_id: str,
    paper_doi_suffix: str,
    assertion_type: str = "supports",
    hypothesis_id: str = "PRIMARY_EFFICACY",
) -> Assertion:
    """Build an Assertion linked to a paper by DOI suffix."""
    return Assertion(
        assertion_id=assertion_id,
        paper_id=f"doi:10.5555/{paper_doi_suffix}",
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


@pytest.fixture
def populated_kg(use_rdflib: bool) -> KnowledgeGraph:
    """Build a small graph with known structure for query tests.

    Structure:
        Papers: p1, p2, p3, p4
        Assertions:
            qa1: p1 supports PRIMARY_EFFICACY
            qa2: p2 supports PRIMARY_EFFICACY
            qa3: p3 contradicts PRIMARY_EFFICACY
            qa4: p2 supports SCALABILITY
        Citations:
            p1 -> p3
            p2 -> p3
        Subfields:
            p1 -> neuroscience
    """
    kg = KnowledgeGraph(use_rdflib=use_rdflib)

    papers = [_make_paper(f"qp{i}", f"Query Paper {i}") for i in range(1, 5)]
    for p in papers:
        kg.add_paper(p)

    kg.add_assertion(_make_assertion("qa1", "qp1", "supports", "PRIMARY_EFFICACY"))
    kg.add_assertion(_make_assertion("qa2", "qp2", "supports", "PRIMARY_EFFICACY"))
    kg.add_assertion(_make_assertion("qa3", "qp3", "contradicts", "PRIMARY_EFFICACY"))
    kg.add_assertion(_make_assertion("qa4", "qp2", "supports", "SCALABILITY"))

    kg.add_citation(papers[0].canonical_id, papers[2].canonical_id)
    kg.add_citation(papers[1].canonical_id, papers[2].canonical_id)

    kg.add_subfield(papers[0].canonical_id, "C1_neuroscience")

    return kg


class TestQueryPapersByHypothesis:
    """Validate query_papers_by_hypothesis."""

    def test_fep_returns_three_papers(self, populated_kg: KnowledgeGraph) -> None:
        """PRIMARY_EFFICACY has assertions from p1, p2, p3."""
        result = query_papers_by_hypothesis(populated_kg, "PRIMARY_EFFICACY")
        assert len(result) == 3
        assert "doi:10.5555/qp1" in result
        assert "doi:10.5555/qp2" in result
        assert "doi:10.5555/qp3" in result

    def test_scalability_returns_one(self, populated_kg: KnowledgeGraph) -> None:
        """SCALABILITY has one assertion from p2."""
        result = query_papers_by_hypothesis(populated_kg, "SCALABILITY")
        assert result == ["doi:10.5555/qp2"]

    def test_unused_hypothesis_returns_empty(self, populated_kg: KnowledgeGraph) -> None:
        """A hypothesis with no assertions should return empty."""
        result = query_papers_by_hypothesis(populated_kg, "DOMAIN_GENERALIZATION")
        assert result == []


class TestQueryAssertionsForPaper:
    """Validate query_assertions_for_paper."""

    def test_paper_with_one_assertion(self, populated_kg: KnowledgeGraph) -> None:
        """p1 has one assertion: qa1."""
        result = query_assertions_for_paper(populated_kg, "doi:10.5555/qp1")
        assert result == ["qa1"]

    def test_paper_with_two_assertions(self, populated_kg: KnowledgeGraph) -> None:
        """p2 has two assertions: qa2 (FEP) and qa4 (SCALABILITY)."""
        result = query_assertions_for_paper(populated_kg, "doi:10.5555/qp2")
        assert sorted(result) == ["qa2", "qa4"]

    def test_paper_with_no_assertions(self, populated_kg: KnowledgeGraph) -> None:
        """p4 has no assertions."""
        result = query_assertions_for_paper(populated_kg, "doi:10.5555/qp4")
        assert result == []


class TestQuerySupportingPapers:
    """Validate query_supporting_papers."""

    def test_fep_supporting(self, populated_kg: KnowledgeGraph) -> None:
        """p1 and p2 support PRIMARY_EFFICACY."""
        result = query_supporting_papers(populated_kg, "PRIMARY_EFFICACY")
        assert len(result) == 2
        assert "doi:10.5555/qp1" in result
        assert "doi:10.5555/qp2" in result

    def test_scalability_supporting(self, populated_kg: KnowledgeGraph) -> None:
        """p2 supports SCALABILITY."""
        result = query_supporting_papers(populated_kg, "SCALABILITY")
        assert result == ["doi:10.5555/qp2"]

    def test_no_support_returns_empty(self, populated_kg: KnowledgeGraph) -> None:
        """CLINICAL_UTILITY has no assertions at all."""
        result = query_supporting_papers(populated_kg, "CLINICAL_UTILITY")
        assert result == []


class TestQueryContradictingPapers:
    """Validate query_contradicting_papers."""

    def test_fep_contradicting(self, populated_kg: KnowledgeGraph) -> None:
        """p3 contradicts PRIMARY_EFFICACY."""
        result = query_contradicting_papers(populated_kg, "PRIMARY_EFFICACY")
        assert result == ["doi:10.5555/qp3"]

    def test_scalability_no_contradiction(self, populated_kg: KnowledgeGraph) -> None:
        """SCALABILITY has only supporting assertions."""
        result = query_contradicting_papers(populated_kg, "SCALABILITY")
        assert result == []


class TestCountTriplesByType:
    """Validate count_triples_by_type."""

    def test_has_all_predicate_keys(self, populated_kg: KnowledgeGraph) -> None:
        """Result should contain all 5 predicate names."""
        counts = count_triples_by_type(populated_kg)
        expected_keys = {"asserts", "cites", "belongsTo", "supports", "contradicts"}
        assert set(counts.keys()) == expected_keys

    def test_asserts_count(self, populated_kg: KnowledgeGraph) -> None:
        """There are 4 paper-asserts-assertion edges."""
        counts = count_triples_by_type(populated_kg)
        assert counts["asserts"] == 4

    def test_cites_count(self, populated_kg: KnowledgeGraph) -> None:
        """There are 2 citation edges."""
        counts = count_triples_by_type(populated_kg)
        assert counts["cites"] == 2

    def test_belongs_to_count(self, populated_kg: KnowledgeGraph) -> None:
        """There is 1 subfield edge."""
        counts = count_triples_by_type(populated_kg)
        assert counts["belongsTo"] == 1

    def test_supports_count(self, populated_kg: KnowledgeGraph) -> None:
        """There are 3 supporting edges (qa1, qa2, qa4)."""
        counts = count_triples_by_type(populated_kg)
        assert counts["supports"] == 3

    def test_contradicts_count(self, populated_kg: KnowledgeGraph) -> None:
        """There is 1 contradicting edge (qa3)."""
        counts = count_triples_by_type(populated_kg)
        assert counts["contradicts"] == 1

    def test_total_matches_expected(self, populated_kg: KnowledgeGraph) -> None:
        """Sum of typed counts should match the expected total typed edges."""
        counts = count_triples_by_type(populated_kg)
        # 4 asserts + 2 cites + 1 belongsTo + 3 supports + 1 contradicts = 11
        assert sum(counts.values()) == 11
