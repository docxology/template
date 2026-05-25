"""Tests for infrastructure.reference.citation.models.

Real-data tests, no mocks (project policy).
"""

from __future__ import annotations

from collections import OrderedDict

import pytest

from infrastructure.reference.citation.models import (
    CANONICAL_ENTRY_TYPES,
    BibDatabase,
    BibEntry,
)


class TestBibEntry:
    def test_minimal_entry_constructs(self):
        entry = BibEntry("article", "smith2024paper")
        assert entry.entry_type == "article"
        assert entry.citation_key == "smith2024paper"
        assert len(entry.fields) == 0

    def test_entry_type_is_lowercased(self):
        entry = BibEntry("ARTICLE", "smith2024")
        assert entry.entry_type == "article"

    def test_entry_type_is_stripped(self):
        entry = BibEntry("  book  ", "smith2024")
        assert entry.entry_type == "book"

    def test_empty_entry_type_raises(self):
        with pytest.raises(ValueError, match="entry_type"):
            BibEntry("", "smith2024")

    def test_whitespace_entry_type_raises(self):
        with pytest.raises(ValueError, match="entry_type"):
            BibEntry("   ", "smith2024")

    def test_empty_citation_key_raises(self):
        with pytest.raises(ValueError, match="citation_key"):
            BibEntry("article", "")

    def test_fields_preserve_insertion_order(self):
        entry = BibEntry(
            "article",
            "k",
            OrderedDict([("title", "T"), ("author", "A"), ("year", "2024")]),
        )
        assert list(entry.fields.keys()) == ["title", "author", "year"]

    def test_dict_fields_coerced_to_ordered_dict(self):
        entry = BibEntry("article", "k", {"title": "T", "year": "2024"})
        assert isinstance(entry.fields, OrderedDict)

    def test_get_is_case_insensitive(self):
        entry = BibEntry("article", "k", OrderedDict([("Title", "T")]))
        assert entry.get("title") == "T"
        assert entry.get("TITLE") == "T"

    def test_get_returns_default_when_missing(self):
        entry = BibEntry("article", "k")
        assert entry.get("missing") is None
        assert entry.get("missing", "x") == "x"

    def test_set_preserves_existing_key_casing(self):
        entry = BibEntry("article", "k", OrderedDict([("Title", "old")]))
        entry.set("title", "new")
        assert "Title" in entry.fields
        assert entry.fields["Title"] == "new"

    def test_set_appends_new_field(self):
        entry = BibEntry("article", "k")
        entry.set("doi", "10.1/x")
        assert entry.fields["doi"] == "10.1/x"

    def test_has_returns_true_for_present_field(self):
        entry = BibEntry("article", "k", {"title": "T"})
        assert entry.has("title") is True
        assert entry.has("Title") is True
        assert entry.has("missing") is False


class TestBibDatabase:
    def test_empty_database(self):
        db = BibDatabase()
        assert len(db) == 0
        assert db.entries == []
        assert db.preamble is None

    def test_add_entry(self):
        db = BibDatabase()
        e = BibEntry("article", "k1")
        db.add(e)
        assert len(db) == 1
        assert db.entries[0] is e

    def test_extend_adds_multiple(self):
        db = BibDatabase()
        db.extend([BibEntry("article", "a"), BibEntry("book", "b")])
        assert [e.citation_key for e in db] == ["a", "b"]

    def test_find_returns_entry(self):
        db = BibDatabase(entries=[BibEntry("article", "found")])
        assert db.find("found") is not None
        assert db.find("missing") is None

    def test_keys_returns_list(self):
        db = BibDatabase(entries=[BibEntry("article", "a"), BibEntry("book", "b")])
        assert db.keys() == ["a", "b"]

    def test_as_mapping_returns_key_indexed(self):
        e1 = BibEntry("article", "a")
        db = BibDatabase(entries=[e1])
        m = db.as_mapping()
        assert m["a"] is e1


class TestCanonicalEntryTypes:
    def test_includes_standard_types(self):
        for t in ("article", "book", "inproceedings", "phdthesis", "misc"):
            assert t in CANONICAL_ENTRY_TYPES

    def test_includes_extensions(self):
        for t in ("software", "online", "preprint", "dataset"):
            assert t in CANONICAL_ENTRY_TYPES
