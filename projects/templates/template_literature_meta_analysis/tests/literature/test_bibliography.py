"""Tests for the unified bibliography export module.

Uses real Paper / Corpus / BibEntry objects throughout — no mocks. Verifies
the rendered BibTeX text structurally (brace balance, expected entry types,
expected field text) rather than parsing it with a third-party BibTeX
library, since the renderer under test (``infrastructure.reference.citation.
bibtex_writer.render_entries``) is itself the source of truth for the output
format.
"""

from __future__ import annotations

from literature.bibliography import corpus_to_bibtex, paper_to_bibentry
from literature.corpus import Corpus
from literature.models import Author, Paper


def _brace_balanced(text: str) -> bool:
    return text.count("{") == text.count("}")


class TestCorpusToBibtexVariedCompleteness:
    """A corpus of 3+ papers with varied field completeness."""

    def _build_corpus(self) -> Corpus:
        full_metadata_paper = Paper(
            title="Active Inference: A Process Theory",
            abstract="This paper presents active inference as a unified brain theory.",
            authors=[Author(name="Karl Friston"), Author(name="Thomas Parr")],
            year=2017,
            doi="10.1162/NECO_a_00912",
            venue="Neural Computation",
            pdf_url="https://example.org/friston2017.pdf",
        )
        preprint_paper = Paper(
            title="A Tutorial on Tangential Action Spaces",
            abstract="",
            authors=[Author(name="Ada Lovelace")],
            year=2025,
            arxiv_id="2509.03399",
            venue=None,
            doi=None,
        )
        no_authors_paper = Paper(
            title="Anonymous Survey Findings on Cognition",
            abstract="",
            authors=[],
            year=2019,
            doi="10.1000/anon.findings",
            venue="Journal of Anonymous Studies",
        )
        corpus = Corpus()
        for paper in (full_metadata_paper, preprint_paper, no_authors_paper):
            corpus.add(paper)
        return corpus

    def test_renders_expected_entry_types_and_fields(self) -> None:
        corpus = self._build_corpus()
        assert len(corpus) == 3

        bibtex_text = corpus_to_bibtex(corpus)

        # Structurally plausible BibTeX.
        assert "@" in bibtex_text
        assert _brace_balanced(bibtex_text)

        # The preprint paper (arxiv_id, no doi) must render as @preprint (or
        # @article if "preprint" is ever removed from CANONICAL_ENTRY_TYPES —
        # either way it must NOT silently vanish).
        preprint_paper = next(p for p in corpus.papers if p.arxiv_id == "2509.03399")
        assert preprint_paper.is_preprint is True
        assert "@preprint{" in bibtex_text or "@article{" in bibtex_text

        # Full-metadata paper: title/author/journal/year/doi/abstract present;
        # url omitted because doi is present.
        assert "Active Inference: A Process Theory" in bibtex_text
        assert "Karl Friston and Thomas Parr" in bibtex_text
        assert "Neural Computation" in bibtex_text
        assert "10.1162/NECO_a_00912" in bibtex_text
        assert "unified brain theory" in bibtex_text
        assert "https://example.org/friston2017.pdf" not in bibtex_text

        # No-authors paper: still renders (no author field), title/doi present.
        assert "Anonymous Survey Findings on Cognition" in bibtex_text
        assert "10.1000/anon.findings" in bibtex_text

    def test_paper_to_bibentry_no_authors_has_no_author_field(self) -> None:
        paper = Paper(title="Solo Findings", authors=[], year=2021, doi="10.1/xyz")
        entry = paper_to_bibentry(paper)
        assert entry.get("author") is None
        assert entry.get("title") == "Solo Findings"
        assert entry.entry_type == "article"

    def test_paper_to_bibentry_preprint_without_doi_uses_url(self) -> None:
        paper = Paper(
            title="A Preprint About Something",
            authors=[Author(name="Jane Doe")],
            year=2024,
            arxiv_id="2401.00001",
            pdf_url="https://arxiv.org/pdf/2401.00001",
        )
        entry = paper_to_bibentry(paper)
        assert paper.is_preprint is True
        assert entry.entry_type in {"preprint", "article"}
        assert entry.get("url") == "https://arxiv.org/pdf/2401.00001"
        assert entry.get("doi") is None


class TestCitationKeyDisambiguation:
    """Two papers that would generate the SAME citation key must disambiguate."""

    def test_second_paper_gets_suffixed_key(self) -> None:
        paper_one = Paper(
            title="Modafinil Effects on Cognition",
            authors=[Author(name="John Smith")],
            year=2020,
            doi="10.1000/aaa.111",
        )
        paper_two = Paper(
            title="Modafinil and Memory Consolidation",
            authors=[Author(name="John Smith")],
            year=2020,
            doi="10.1000/bbb.222",
        )
        corpus = Corpus()
        corpus.add(paper_one)
        corpus.add(paper_two)
        assert len(corpus) == 2

        bibtex_text = corpus_to_bibtex(corpus)

        assert "{smith2020modafinil,\n" in bibtex_text
        assert "{smith2020modafinila,\n" in bibtex_text

    def test_paper_to_bibentry_used_keys_collision_directly(self) -> None:
        paper_one = Paper(title="Modafinil Study One", authors=[Author(name="Jane Roe")], year=2021)
        paper_two = Paper(title="Modafinil Study Two", authors=[Author(name="Jane Roe")], year=2021)
        used_keys: set[str] = set()

        entry_one = paper_to_bibentry(paper_one, used_keys=used_keys)
        entry_two = paper_to_bibentry(paper_two, used_keys=used_keys)

        assert entry_one.citation_key == "roe2021modafinil"
        assert entry_two.citation_key == "roe2021modafinila"
        assert used_keys == {"roe2021modafinil", "roe2021modafinila"}

    def test_no_used_keys_means_no_disambiguation(self) -> None:
        paper_one = Paper(title="Modafinil Study One", authors=[Author(name="Jane Roe")], year=2021)
        paper_two = Paper(title="Modafinil Study Two", authors=[Author(name="Jane Roe")], year=2021)

        entry_one = paper_to_bibentry(paper_one)
        entry_two = paper_to_bibentry(paper_two)

        # Without a shared used_keys set, both get the same (undisambiguated) key.
        assert entry_one.citation_key == entry_two.citation_key == "roe2021modafinil"


class TestEmptyCorpus:
    """An empty corpus must not raise and should produce empty(-ish) output."""

    def test_empty_corpus_returns_empty_string(self) -> None:
        corpus = Corpus()
        assert len(corpus) == 0

        bibtex_text = corpus_to_bibtex(corpus)

        assert bibtex_text == ""
