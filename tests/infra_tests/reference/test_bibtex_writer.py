"""Tests for infrastructure.reference.citation.bibtex_writer.

These tests pin the output format down to the byte level so that the writer
remains compatible with ``projects/templates/template_code_project/manuscript/references.bib``.
"""

from __future__ import annotations

from collections import OrderedDict


from infrastructure.reference.citation.bibtex_writer import (
    render_database,
    render_entries,
    render_entry,
    write_bibfile,
)
from infrastructure.reference.citation.models import BibDatabase, BibEntry


def _entry_nocedal() -> BibEntry:
    return BibEntry(
        "book",
        "nocedal2006numerical",
        OrderedDict(
            [
                ("title", "Numerical optimization"),
                ("author", "Nocedal, Jorge and Wright, Stephen"),
                ("year", "2006"),
                ("publisher", "Springer Science & Business Media"),
                ("edition", "2nd"),
                ("isbn", "978-0-387-30303-1"),
                ("doi", "10.1007/978-0-387-40065-5"),
            ]
        ),
    )


class TestRenderEntry:
    def test_matches_exemplar_byte_for_byte(self):
        # The reference output mirrors the exact format used in the
        # exemplar references.bib file.
        expected = (
            "@book{nocedal2006numerical,\n"
            "  title={Numerical optimization},\n"
            "  author={Nocedal, Jorge and Wright, Stephen},\n"
            "  year={2006},\n"
            "  publisher={Springer Science \\& Business Media},\n"
            "  edition={2nd},\n"
            "  isbn={978-0-387-30303-1},\n"
            "  doi={10.1007/978-0-387-40065-5}\n"
            "}\n"
        )
        assert render_entry(_entry_nocedal()) == expected

    def test_two_space_indent(self):
        out = render_entry(_entry_nocedal())
        for line in out.splitlines()[1:-1]:  # field lines
            assert line.startswith("  "), f"Field line missing 2-space indent: {line!r}"
            assert not line.startswith("   "), f"Field line over-indented: {line!r}"

    def test_last_field_has_no_trailing_comma(self):
        out = render_entry(_entry_nocedal())
        lines = out.splitlines()
        last_field = lines[-2]
        assert not last_field.rstrip().endswith(","), last_field

    def test_non_last_fields_have_trailing_comma(self):
        out = render_entry(_entry_nocedal())
        lines = out.splitlines()
        # First field through second-to-last field.
        for line in lines[1:-2]:
            assert line.rstrip().endswith(","), line

    def test_closing_brace_flush_left(self):
        out = render_entry(_entry_nocedal())
        assert out.rstrip().endswith("\n}") or out.endswith("}\n")
        # Closing line is exactly "}" (followed by newline).
        assert out.splitlines()[-1] == "}"

    def test_pages_normalized_to_double_dash(self):
        e = BibEntry("article", "k", OrderedDict([("pages", "536-538")]))
        out = render_entry(e)
        assert "pages={536--538}" in out

    def test_pages_unicode_dashes_normalized(self):
        e = BibEntry("article", "k", OrderedDict([("pages", "536–538")]))
        assert "pages={536--538}" in render_entry(e)

    def test_pages_already_double_dash_unchanged(self):
        e = BibEntry("article", "k", OrderedDict([("pages", "536--538")]))
        assert "pages={536--538}" in render_entry(e)

    def test_doi_not_escaped(self):
        # DOIs commonly contain `_` and `&` — they must NOT be LaTeX-escaped.
        e = BibEntry(
            "article",
            "k",
            OrderedDict([("doi", "10.1234/foo_bar&baz")]),
        )
        out = render_entry(e)
        assert "doi={10.1234/foo_bar&baz}" in out

    def test_url_not_escaped(self):
        e = BibEntry("misc", "k", OrderedDict([("url", "https://x.org/p?id=1&v=2")]))
        out = render_entry(e)
        assert "url={https://x.org/p?id=1&v=2}" in out

    def test_year_not_escaped(self):
        e = BibEntry("article", "k", OrderedDict([("year", "2024")]))
        assert "year={2024}" in render_entry(e)

    def test_ampersand_escaped_in_publisher(self):
        e = BibEntry(
            "book",
            "k",
            OrderedDict([("publisher", "Smith & Co")]),
        )
        out = render_entry(e)
        assert r"publisher={Smith \& Co}" in out

    def test_unicode_preserved(self):
        e = BibEntry("article", "k", OrderedDict([("title", "Méthode générale")]))
        out = render_entry(e)
        assert "title={Méthode générale}" in out

    def test_author_normalised_around_and(self):
        e = BibEntry(
            "article",
            "k",
            OrderedDict([("author", "Alice Smith   and   Bob Jones")]),
        )
        out = render_entry(e)
        assert "author={Alice Smith and Bob Jones}" in out

    def test_empty_fields_emits_minimal_record(self):
        e = BibEntry("misc", "key")
        assert render_entry(e) == "@misc{key\n}\n"

    def test_comment_emitted_above_entry(self):
        e = BibEntry("article", "k", OrderedDict([("title", "T")]))
        e.comment = "Originally cited from notebook"
        out = render_entry(e)
        assert out.startswith("@comment{Originally cited from notebook}\n")


class TestRenderDatabase:
    def test_empty_database_returns_empty_string(self):
        assert render_database(BibDatabase()) == ""

    def test_entries_separated_by_blank_line(self):
        db = BibDatabase(
            entries=[
                BibEntry("article", "a", {"title": "A"}),
                BibEntry("article", "b", {"title": "B"}),
            ]
        )
        out = render_database(db)
        # Between the two entries there is exactly one blank line.
        assert "}\n\n@article{b" in out

    def test_preamble_emitted_first(self):
        db = BibDatabase(entries=[BibEntry("article", "a", {"title": "A"})])
        db.preamble = "Provenance note"
        out = render_database(db)
        assert out.startswith("@comment{\nProvenance note\n}\n\n@article{a")

    def test_render_entries_ignores_preamble(self):
        out = render_entries([BibEntry("article", "k", {"title": "T"})])
        assert "@comment" not in out
        assert "@article{k" in out


class TestWriteBibfile:
    def test_writes_to_disk(self, tmp_path):
        db = BibDatabase(entries=[BibEntry("article", "k", OrderedDict([("title", "T")]))])
        out = write_bibfile(tmp_path / "x.bib", db)
        assert out.exists()
        text = out.read_text(encoding="utf-8")
        assert "@article{k" in text

    def test_creates_parent_directories(self, tmp_path):
        target = tmp_path / "deep" / "nested" / "out.bib"
        db = BibDatabase(entries=[BibEntry("article", "k", {"title": "T"})])
        out = write_bibfile(target, db)
        assert out.exists()

    def test_overwrites_existing_file(self, tmp_path):
        path = tmp_path / "x.bib"
        path.write_text("OLD CONTENT", encoding="utf-8")
        db = BibDatabase(entries=[BibEntry("article", "k", {"title": "T"})])
        write_bibfile(path, db)
        assert "OLD CONTENT" not in path.read_text(encoding="utf-8")
