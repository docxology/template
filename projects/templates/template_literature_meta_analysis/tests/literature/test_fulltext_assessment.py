"""Tests for literature.fulltext_assessment."""

from __future__ import annotations

from literature.corpus import Corpus
from literature.fulltext_assessment import assess_corpus
from literature.models import Paper


def test_assess_corpus_reports_coverage(sample_papers: list[Paper]) -> None:
    corpus = Corpus()
    for paper in sample_papers:
        corpus.add(paper)
    report = assess_corpus(corpus)
    assert report["total_papers"] == len(sample_papers)
    assert "abstract_coverage" in report
    assert "pdf_availability" in report


def test_assess_corpus_pdf_domains_and_malformed_urls() -> None:
    corpus = Corpus()
    corpus.add(
        Paper(
            title="With PDF",
            abstract="active inference",
            authors=[],
            year=2020,
            pdf_url="https://arxiv.org/pdf/1709.02341.pdf",
        )
    )
    corpus.add(
        Paper(
            title="Bad URL",
            abstract="free energy",
            authors=[],
            year=2021,
            pdf_url="not-a-valid-url",
        )
    )
    report = assess_corpus(corpus)
    domains = report["pdf_domain_breakdown"]
    assert "arxiv.org" in domains or len(domains) >= 1
    assert report["pdf_availability"]["has_pdf_url"] == 2


def test_provider_breakdown_excludes_metadata_only_sources() -> None:
    """Search provenance and DOI presence do not imply a fulltext provider."""
    corpus = Corpus()
    corpus.add(
        Paper(
            title="Europe PMC metadata only",
            doi="10.1/metadata",
            full_text_source="europepmc",
        )
    )
    corpus.add(
        Paper(
            title="Direct bioRxiv PDF",
            doi="10.1/preprint",
            pdf_url="https://www.biorxiv.org/content/10.1/preprint.full.pdf",
            full_text_source="biorxiv",
        )
    )

    report = assess_corpus(corpus)

    assert report["provider_breakdown"] == {"biorxiv": 1}
    assert report["fulltext_source_breakdown"] == {"none": 1, "biorxiv": 1}
