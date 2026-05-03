"""Tests for infrastructure.reference.citation.converter."""

from __future__ import annotations

from infrastructure.reference.citation.converter import (
    generate_citation_key,
    paper_to_bibentry,
)
from infrastructure.search.literature.models import Paper


class TestGenerateCitationKey:
    def test_basic_format(self):
        key = generate_citation_key(
            authors=["Nocedal, Jorge"], year=2006, title="Numerical optimization"
        )
        assert key == "nocedal2006numerical"

    def test_handles_first_last_format(self):
        key = generate_citation_key(
            authors=["Diederik P Kingma", "Jimmy Ba"],
            year=2014,
            title="Adam: A method for stochastic optimization",
        )
        assert key == "ba2014adam" or key == "kingma2014adam"

    def test_skips_stop_words_in_title(self):
        key = generate_citation_key(
            authors=["Smith, Alice"], year=2024, title="On the Convex Optimization"
        )
        assert key == "smith2024convex"

    def test_unicode_folded(self):
        key = generate_citation_key(
            authors=["Cauchy, Augustin-Louis"],
            year=1847,
            title="Méthode générale",
        )
        assert key.startswith("cauchy1847")

    def test_no_authors_uses_fallback(self):
        key = generate_citation_key(
            authors=[], year=2024, title="Some Paper", fallback="anon"
        )
        assert key.startswith("anon2024")

    def test_no_year(self):
        key = generate_citation_key(
            authors=["Smith, Alice"], year=None, title="Paper"
        )
        assert "smith" in key
        assert "paper" in key

    def test_strips_punctuation(self):
        key = generate_citation_key(
            authors=["O'Brien, Patrick"], year=2024, title="P.D.E.s in Action"
        )
        assert key == "obrien2024pdes"


class TestPaperToBibentry:
    def test_article_default_entry_type(self):
        paper = Paper(
            id="doi:10.1/x",
            title="A Test",
            authors=["Smith, Alice"],
            year=2024,
            doi="10.1/x",
            venue="Nature",
            venue_type="journal",
        )
        entry = paper_to_bibentry(paper)
        assert entry.entry_type == "article"
        assert entry.citation_key == "smith2024test"
        assert entry.get("journal") == "Nature"

    def test_book_omits_journal(self):
        paper = Paper(
            id="isbn:1",
            title="Numerical Optimization",
            authors=["Nocedal, Jorge"],
            year=2006,
            venue="Springer",
            venue_type="book",
            publisher="Springer",
            edition="2nd",
            isbn="978-0",
        )
        entry = paper_to_bibentry(paper)
        assert entry.entry_type == "book"
        assert entry.get("journal") is None
        assert entry.get("publisher") == "Springer"
        assert entry.get("edition") == "2nd"

    def test_inproceedings_uses_booktitle(self):
        paper = Paper(
            id="x",
            title="Adam",
            authors=["Kingma, Diederik P"],
            year=2014,
            venue="ICLR",
            venue_type="conference",
        )
        entry = paper_to_bibentry(paper)
        assert entry.entry_type == "inproceedings"
        assert entry.get("booktitle") == "ICLR"
        assert entry.get("journal") is None

    def test_preprint_default_to_article(self):
        paper = Paper(
            id="arxiv:1",
            title="A Preprint",
            authors=["Smith, A"],
            year=2024,
            source="arxiv",
        )
        entry = paper_to_bibentry(paper)
        assert entry.entry_type == "article"

    def test_url_omitted_when_doi_present(self):
        paper = Paper(
            id="doi:10.1/x",
            title="A",
            authors=["Smith, A"],
            year=2024,
            doi="10.1/x",
            url="https://example.org",
        )
        entry = paper_to_bibentry(paper)
        assert entry.get("doi") == "10.1/x"
        assert entry.get("url") is None

    def test_url_kept_when_no_doi(self):
        paper = Paper(
            id="x",
            title="A",
            authors=["Smith, A"],
            year=2024,
            url="https://arxiv.org/abs/1412.6980",
        )
        entry = paper_to_bibentry(paper)
        assert entry.get("url") == "https://arxiv.org/abs/1412.6980"

    def test_caller_can_override_citation_key(self):
        paper = Paper(id="x", title="T", authors=["Smith, A"], year=2024)
        entry = paper_to_bibentry(paper, citation_key="custom_key")
        assert entry.citation_key == "custom_key"

    def test_caller_can_override_entry_type(self):
        paper = Paper(id="x", title="T", authors=["Smith, A"], year=2024)
        entry = paper_to_bibentry(paper, entry_type="techreport")
        assert entry.entry_type == "techreport"

    def test_keywords_joined_with_comma_space(self):
        paper = Paper(
            id="x",
            title="T",
            authors=["Smith, A"],
            year=2024,
            keywords=["optimization", "convex", "gradient"],
        )
        entry = paper_to_bibentry(paper)
        assert entry.get("keywords") == "optimization, convex, gradient"
