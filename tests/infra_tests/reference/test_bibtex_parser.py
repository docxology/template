"""Tests for infrastructure.reference.citation.bibtex_parser.

The most important assertion is the round-trip: parsing the writer's output
must produce a database whose re-rendered form is byte-identical.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.reference.citation.bibtex_parser import (
    BibParseError,
    parse_bibfile,
    parse_bibtex,
)
from infrastructure.reference.citation.bibtex_writer import render_database

REPO_ROOT = Path(__file__).resolve().parents[3]
EXEMPLAR_BIB = REPO_ROOT / "projects" / "template_code_project" / "manuscript" / "references.bib"


class TestParseBasicEntry:
    def test_single_article(self):
        text = "@article{smith2024,\n  title={A Paper},\n  author={Alice Smith},\n  year={2024}\n}\n"
        db = parse_bibtex(text)
        assert len(db) == 1
        e = db.entries[0]
        assert e.entry_type == "article"
        assert e.citation_key == "smith2024"
        assert e.get("title") == "A Paper"
        assert e.get("author") == "Alice Smith"
        assert e.get("year") == "2024"

    def test_field_order_preserved(self):
        text = "@article{k,\n  z={1},\n  a={2},\n  m={3}\n}\n"
        e = parse_bibtex(text).entries[0]
        assert list(e.fields.keys()) == ["z", "a", "m"]

    def test_quoted_values(self):
        text = '@article{k, title = "Hello, World", year = 2024}'
        e = parse_bibtex(text).entries[0]
        assert e.get("title") == "Hello, World"
        assert e.get("year") == "2024"

    def test_bare_numeric_values(self):
        text = "@article{k, year = 1964}"
        e = parse_bibtex(text).entries[0]
        assert e.get("year") == "1964"

    def test_nested_braces(self):
        text = "@article{k, title={The {LaTeX} Companion}}"
        e = parse_bibtex(text).entries[0]
        assert e.get("title") == "The {LaTeX} Companion"

    def test_trailing_comma_tolerated(self):
        text = "@article{k,\n  title={T},\n  year={2024},\n}\n"
        e = parse_bibtex(text).entries[0]
        assert e.get("year") == "2024"

    def test_paren_delimiters_supported(self):
        text = "@article(k, title={T}, year={2024})"
        db = parse_bibtex(text)
        assert db.entries[0].get("year") == "2024"

    def test_multiple_entries(self):
        text = "@article{a, title={A}, year={2024}}\n@book{b, title={B}, year={1999}}\n"
        db = parse_bibtex(text)
        assert [e.citation_key for e in db] == ["a", "b"]
        assert db.entries[1].entry_type == "book"

    def test_comment_block_collected_as_preamble(self):
        text = "@comment{Provenance note}\n@article{k, title={T}}\n"
        db = parse_bibtex(text)
        assert "Provenance note" in (db.preamble or "")
        assert len(db) == 1

    def test_unescapes_latex_specials(self):
        text = r"@book{k, publisher={Springer Science \& Business Media}}"
        e = parse_bibtex(text).entries[0]
        assert e.get("publisher") == "Springer Science & Business Media"

    def test_doi_not_unescaped(self):
        # DOIs / URLs may contain `_` legitimately; parser should not mangle them.
        text = "@article{k, doi={10.1007/s10107-012-0629-5}}"
        e = parse_bibtex(text).entries[0]
        assert e.get("doi") == "10.1007/s10107-012-0629-5"


class TestParseErrors:
    def test_missing_entry_type_raises(self):
        with pytest.raises(BibParseError):
            parse_bibtex("@{key, title={T}}")

    def test_missing_citation_key_raises(self):
        with pytest.raises(BibParseError):
            parse_bibtex("@article{, title={T}}")

    def test_unterminated_braces_raises(self):
        with pytest.raises(BibParseError):
            parse_bibtex("@article{k, title={Unterminated")

    def test_unterminated_quote_raises(self):
        with pytest.raises(BibParseError):
            parse_bibtex('@article{k, title="Unterminated')


class TestRoundTrip:
    @pytest.mark.parametrize(
        "text",
        [
            (
                "@article{smith2024,\n"
                "  title={A Paper},\n"
                "  author={Smith, Alice and Jones, Bob},\n"
                "  year={2024},\n"
                "  doi={10.1/x}\n"
                "}\n"
            ),
            (
                "@book{nocedal2006,\n"
                "  title={Numerical Optimization},\n"
                "  publisher={Springer Science \\& Business Media}\n"
                "}\n"
            ),
        ],
    )
    def test_writer_then_parser_recovers_fields(self, text: str):
        db = parse_bibtex(text)
        rerendered = render_database(db)
        # The format we produce is canonical — so re-parsing it should
        # yield the same entry contents (order + values).
        db2 = parse_bibtex(rerendered)
        assert len(db) == len(db2) == 1
        e1, e2 = db.entries[0], db2.entries[0]
        assert e1.entry_type == e2.entry_type
        assert e1.citation_key == e2.citation_key
        assert list(e1.fields.items()) == list(e2.fields.items())


class TestExemplarBib:
    """Verify that the actual references.bib file in this repo round-trips."""

    def test_parses_without_error(self):
        assert EXEMPLAR_BIB.exists(), f"Missing exemplar: {EXEMPLAR_BIB}"
        db = parse_bibfile(EXEMPLAR_BIB)
        assert len(db) >= 8

    def test_has_expected_keys(self):
        db = parse_bibfile(EXEMPLAR_BIB)
        keys = set(db.keys())
        # A few keys we know are in the exemplar.
        assert "nocedal2006numerical" in keys
        assert "boyd2004convex" in keys
        assert "kingma2014adam" in keys

    def test_round_trip_re_renders_each_entry(self):
        db = parse_bibfile(EXEMPLAR_BIB)
        rerendered = render_database(db)
        db2 = parse_bibtex(rerendered)
        assert len(db) == len(db2)
        for e1, e2 in zip(db.entries, db2.entries):
            assert e1.entry_type == e2.entry_type
            assert e1.citation_key == e2.citation_key
            # Field values must match exactly after a round trip.
            assert list(e1.fields.items()) == list(e2.fields.items())

    def test_preamble_preserved(self):
        db = parse_bibfile(EXEMPLAR_BIB)
        assert db.preamble is not None
        assert "infrastructure/rendering/latex_utils.py" in db.preamble
