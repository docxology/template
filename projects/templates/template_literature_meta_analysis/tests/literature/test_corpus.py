"""Tests for the Corpus class.

Tests add, merge, dedup, save/load round-trip with tmp_path, filter_by_year,
and contains/get operations. Uses real Paper objects with Active Inference
content.
"""

import json
from datetime import date
from pathlib import Path

import pytest

from literature.corpus import Corpus
from literature.models import Author, Paper


# ---------------------------------------------------------------------------
# Fixtures: reusable Paper objects
# ---------------------------------------------------------------------------


def make_friston_2010() -> Paper:
    """Create the Friston 2010 FEP paper."""
    return Paper(
        title="The free-energy principle: a unified brain theory?",
        abstract="A free-energy principle for the brain is proposed.",
        authors=[
            Author(name="Karl Friston", affiliation="UCL"),
        ],
        year=2010,
        doi="10.1038/nrn2787",
        venue="Nature Reviews Neuroscience",
        citation_count=3500,
        publication_date=date(2010, 2, 13),
    )


def make_friston_2017() -> Paper:
    """Create the Friston 2017 Active Inference process theory paper."""
    return Paper(
        title="Active Inference: A Process Theory",
        abstract="This paper introduces active inference.",
        authors=[
            Author(name="Karl Friston"),
            Author(name="Thomas Parr"),
        ],
        year=2017,
        doi="10.1162/NECO_a_00912",
        arxiv_id="1709.02341",
        venue="Neural Computation",
        citation_count=450,
    )


def make_parr_2022() -> Paper:
    """Create a Parr 2022 Active Inference textbook-related paper."""
    return Paper(
        title="Active Inference: The Free Energy Principle in Mind, Brain, and Behavior",
        abstract="A comprehensive introduction to active inference.",
        authors=[
            Author(name="Thomas Parr"),
            Author(name="Giovanni Pezzulo"),
            Author(name="Karl Friston"),
        ],
        year=2022,
        doi="10.7551/mitpress/12441.001.0001",
    )


def make_paper_no_doi() -> Paper:
    """Create a paper with only arXiv ID."""
    return Paper(
        title="Bayesian Mechanics for Active Inference",
        abstract="We describe a Bayesian mechanics.",
        authors=[Author(name="Dalton Sakthivadivel")],
        year=2023,
        arxiv_id="2301.12345",
    )


def make_paper_title_only() -> Paper:
    """Create a paper with minimal metadata (title only)."""
    return Paper(title="Unpublished Active Inference Draft")


# ---------------------------------------------------------------------------
# Corpus construction and add
# ---------------------------------------------------------------------------


class TestCorpusAdd:
    """Tests for Corpus add and basic operations."""

    def test_empty_corpus(self):
        """Empty corpus has length 0."""
        c = Corpus()
        assert len(c) == 0
        assert c.papers == []

    def test_init_with_papers(self):
        """Corpus initialized with papers has correct length."""
        papers = [make_friston_2010(), make_friston_2017()]
        c = Corpus(papers)
        assert len(c) == 2

    def test_add_single(self):
        """Adding a single paper increases length."""
        c = Corpus()
        c.add(make_friston_2010())
        assert len(c) == 1
        assert c.papers[0].title == "The free-energy principle: a unified brain theory?"

    def test_add_multiple(self):
        """Adding distinct papers gives correct count."""
        c = Corpus()
        c.add(make_friston_2010())
        c.add(make_friston_2017())
        c.add(make_parr_2022())
        assert len(c) == 3

    def test_dedup_same_canonical_id(self):
        """Adding a paper with same canonical_id deduplicates."""
        c = Corpus()
        p1 = Paper(title="Test", doi="10.1234/test", abstract="Short")
        p2 = Paper(title="Test Paper Full", doi="10.1234/test", abstract="Full abstract", year=2020)
        c.add(p1)
        c.add(p2)
        assert len(c) == 1

    def test_dedup_keeps_more_complete(self):
        """Dedup keeps the paper with more metadata."""
        c = Corpus()
        sparse = Paper(title="Test", doi="10.1234/test")
        rich = Paper(
            title="Test Full",
            doi="10.1234/test",
            abstract="Full abstract text",
            year=2020,
            venue="Nature",
            citation_count=50,
        )
        c.add(sparse)
        c.add(rich)
        assert len(c) == 1
        # Rich version should be kept (more metadata)
        assert c.papers[0].abstract == "Full abstract text"
        assert c.papers[0].venue == "Nature"

    def test_dedup_keeps_existing_if_equal_completeness(self):
        """If new paper has same or less completeness, existing is kept."""
        c = Corpus()
        first = Paper(title="Test", doi="10.1234/test", year=2020)
        second = Paper(title="Test Other", doi="10.1234/test", year=2021)
        c.add(first)
        c.add(second)
        assert len(c) == 1
        # Both have completeness 2 (year + doi), first should be kept
        assert c.papers[0].year == 2020

    def test_contains(self):
        """__contains__ checks canonical_id membership."""
        c = Corpus()
        p = make_friston_2010()
        c.add(p)
        assert p.canonical_id in c
        assert "doi:10.9999/nonexistent" not in c

    def test_get_existing(self):
        """get() returns paper by canonical_id."""
        c = Corpus()
        p = make_friston_2010()
        c.add(p)
        retrieved = c.get(p.canonical_id)
        assert retrieved is not None
        assert retrieved.title == p.title

    def test_get_nonexistent(self):
        """get() returns None for missing canonical_id."""
        c = Corpus()
        assert c.get("doi:10.9999/nonexistent") is None


# ---------------------------------------------------------------------------
# Corpus merge
# ---------------------------------------------------------------------------


class TestCorpusMerge:
    """Tests for merging two corpora."""

    def test_merge_disjoint(self):
        """Merging disjoint corpora combines all papers."""
        c1 = Corpus([make_friston_2010()])
        c2 = Corpus([make_friston_2017(), make_parr_2022()])
        c1.merge(c2)
        assert len(c1) == 3

    def test_merge_overlapping(self):
        """Merging overlapping corpora deduplicates."""
        c1 = Corpus([make_friston_2010(), make_friston_2017()])
        c2 = Corpus([make_friston_2017(), make_parr_2022()])
        c1.merge(c2)
        assert len(c1) == 3  # Friston 2017 appears once

    def test_merge_keeps_better_metadata(self):
        """Merge keeps the more complete version of duplicate papers."""
        sparse = Paper(title="Test", doi="10.1234/test")
        rich = Paper(
            title="Test Full",
            doi="10.1234/test",
            abstract="Detailed abstract",
            year=2020,
            venue="Science",
        )
        c1 = Corpus([sparse])
        c2 = Corpus([rich])
        c1.merge(c2)
        assert len(c1) == 1
        assert c1.papers[0].abstract == "Detailed abstract"

    def test_merge_empty_into_populated(self):
        """Merging empty corpus into populated one has no effect."""
        c1 = Corpus([make_friston_2010()])
        c2 = Corpus()
        c1.merge(c2)
        assert len(c1) == 1

    def test_merge_populated_into_empty(self):
        """Merging populated corpus into empty one adds all papers."""
        c1 = Corpus()
        c2 = Corpus([make_friston_2010(), make_friston_2017()])
        c1.merge(c2)
        assert len(c1) == 2


# ---------------------------------------------------------------------------
# Corpus filter_by_year
# ---------------------------------------------------------------------------


class TestCorpusFilterByYear:
    """Tests for year-based filtering."""

    def test_filter_start_only(self):
        """Filter with start year only keeps papers >= start."""
        c = Corpus([make_friston_2010(), make_friston_2017(), make_parr_2022()])
        filtered = c.filter_by_year(start=2015)
        assert len(filtered) == 2
        years = {p.year for p in filtered.papers}
        assert years == {2017, 2022}

    def test_filter_end_only(self):
        """Filter with end year only keeps papers <= end."""
        c = Corpus([make_friston_2010(), make_friston_2017(), make_parr_2022()])
        filtered = c.filter_by_year(end=2017)
        assert len(filtered) == 2
        years = {p.year for p in filtered.papers}
        assert years == {2010, 2017}

    def test_filter_start_and_end(self):
        """Filter with both start and end keeps papers in range."""
        c = Corpus([make_friston_2010(), make_friston_2017(), make_parr_2022()])
        filtered = c.filter_by_year(start=2015, end=2020)
        assert len(filtered) == 1
        assert filtered.papers[0].year == 2017

    def test_filter_excludes_none_year(self):
        """Papers with year=None are excluded from filtered results."""
        c = Corpus([make_friston_2010(), make_paper_title_only()])
        filtered = c.filter_by_year(start=2000)
        assert len(filtered) == 1
        assert filtered.papers[0].year == 2010

    def test_filter_no_bounds(self):
        """Filter with no bounds keeps all papers with years."""
        c = Corpus([make_friston_2010(), make_friston_2017(), make_paper_title_only()])
        filtered = c.filter_by_year()
        # Papers with year=None are excluded
        assert len(filtered) == 2

    def test_filter_empty_result(self):
        """Filter that matches nothing returns empty corpus."""
        c = Corpus([make_friston_2010()])
        filtered = c.filter_by_year(start=2025)
        assert len(filtered) == 0

    def test_filter_returns_new_corpus(self):
        """filter_by_year returns a new Corpus, not mutating original."""
        c = Corpus([make_friston_2010(), make_friston_2017()])
        filtered = c.filter_by_year(start=2015)
        assert len(c) == 2
        assert len(filtered) == 1


# ---------------------------------------------------------------------------
# Corpus filter_by_subfield
# ---------------------------------------------------------------------------


class TestCorpusFilterBySubfield:
    """Tests for subfield-based filtering using classify_paper."""

    def test_filter_neuroscience(self):
        """Papers about neural/cortical topics match neuroscience subfield."""
        neuro_paper = Paper(
            title="Cortical Hierarchies and Active Inference",
            abstract="We model cortical hierarchical processing using active inference with neural circuits.",
            doi="10.1234/neuro",
            year=2020,
        )
        general_paper = Paper(
            title="The Free Energy Principle",
            abstract="A general overview of the free energy principle and active inference.",
            doi="10.1234/general",
            year=2019,
        )
        c = Corpus([neuro_paper, general_paper])
        filtered = c.filter_by_subfield("C1_neuroscience")
        assert len(filtered) == 1
        assert "Cortical" in filtered.papers[0].title

    def test_filter_robotics(self):
        """Papers about robot control match robotics subfield."""
        robot_paper = Paper(
            title="Robot Control with Active Inference",
            abstract="An embodied robot navigation system using sensorimotor active inference.",
            doi="10.1234/robot",
            year=2021,
        )
        c = Corpus([robot_paper, make_friston_2010()])
        filtered = c.filter_by_subfield("C2_robotics")
        assert len(filtered) == 1
        assert "Robot" in filtered.papers[0].title

    def test_filter_no_matches(self):
        """Filtering for a subfield with no matching papers returns empty corpus."""
        c = Corpus([make_friston_2010()])
        filtered = c.filter_by_subfield("C3_language")
        assert len(filtered) == 0

    def test_filter_returns_new_corpus(self):
        """filter_by_subfield returns new Corpus, original unchanged."""
        c = Corpus([make_friston_2010(), make_friston_2017()])
        filtered = c.filter_by_subfield("A2_philosophy")
        assert len(c) == 2
        assert isinstance(filtered, Corpus)


# ---------------------------------------------------------------------------
# Corpus save and load (JSONL)
# ---------------------------------------------------------------------------


class TestCorpusPersistence:
    """Tests for JSONL save/load round-trip."""

    def test_save_and_load_round_trip(self, tmp_path: Path):
        """Corpus survives save/load cycle."""
        original = Corpus([make_friston_2010(), make_friston_2017(), make_parr_2022()])
        filepath = tmp_path / "corpus.jsonl"

        original.save(filepath)
        loaded = Corpus.load(filepath)

        assert len(loaded) == 3

    def test_save_load_preserves_fields(self, tmp_path: Path):
        """All paper fields survive save/load."""
        p = make_friston_2010()
        original = Corpus([p])
        filepath = tmp_path / "corpus.jsonl"

        original.save(filepath)
        loaded = Corpus.load(filepath)

        lp = loaded.papers[0]
        assert lp.title == p.title
        assert lp.abstract == p.abstract
        assert lp.year == p.year
        assert lp.doi == p.doi
        assert lp.venue == p.venue
        assert lp.citation_count == p.citation_count
        assert lp.publication_date == p.publication_date
        assert len(lp.authors) == 1
        assert lp.authors[0].name == "Karl Friston"
        assert lp.authors[0].affiliation == "UCL"

    def test_save_load_preserves_canonical_id(self, tmp_path: Path):
        """Canonical IDs are preserved through save/load."""
        papers = [make_friston_2010(), make_paper_no_doi(), make_paper_title_only()]
        original = Corpus(papers)
        filepath = tmp_path / "corpus.jsonl"

        original_ids = {p.canonical_id for p in original.papers}
        original.save(filepath)
        loaded = Corpus.load(filepath)
        loaded_ids = {p.canonical_id for p in loaded.papers}

        assert original_ids == loaded_ids

    def test_save_creates_parent_dirs(self, tmp_path: Path):
        """save() creates parent directories if they don't exist."""
        filepath = tmp_path / "nested" / "dir" / "corpus.jsonl"
        c = Corpus([make_friston_2010()])
        c.save(filepath)
        assert filepath.exists()

    def test_load_empty_file(self, tmp_path: Path):
        """Loading an empty file returns empty corpus."""
        filepath = tmp_path / "empty.jsonl"
        filepath.write_text("")
        loaded = Corpus.load(filepath)
        assert len(loaded) == 0

    def test_load_nonexistent_raises(self, tmp_path: Path):
        """Loading from nonexistent path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            Corpus.load(tmp_path / "nonexistent.jsonl")

    def test_jsonl_format(self, tmp_path: Path):
        """Saved file is valid JSONL (one JSON object per line)."""
        c = Corpus([make_friston_2010(), make_friston_2017()])
        filepath = tmp_path / "corpus.jsonl"
        c.save(filepath)

        lines = filepath.read_text().strip().split("\n")
        assert len(lines) == 2
        for line in lines:
            obj = json.loads(line)
            assert "title" in obj
            assert "doi" in obj

    def test_save_empty_corpus(self, tmp_path: Path):
        """Saving empty corpus creates empty file."""
        filepath = tmp_path / "empty.jsonl"
        c = Corpus()
        c.save(filepath)
        assert filepath.exists()
        assert filepath.read_text().strip() == ""

    def test_dedup_preserved_after_load(self, tmp_path: Path):
        """Papers with same canonical_id are deduped on load."""
        c = Corpus([make_friston_2010()])
        filepath = tmp_path / "corpus.jsonl"
        c.save(filepath)

        # Manually append a duplicate line
        with open(filepath, "a") as f:
            f.write(json.dumps(make_friston_2010().to_dict()) + "\n")

        loaded = Corpus.load(filepath)
        # Corpus constructor deduplicates on canonical_id
        assert len(loaded) == 1


# ---------------------------------------------------------------------------
# Corpus filter_by_subfield
# ---------------------------------------------------------------------------


class TestCorpusFilterBySubfieldKeywords:
    """Additional subfield-filtering tests (renamed so it no longer shadows the
    earlier TestCorpusFilterBySubfield — both classes' tests now collect and run)."""

    def test_filter_neuroscience(self):
        """Papers with neuroscience keywords classified correctly."""
        neuro = Paper(
            title="Neural correlates of active inference",
            abstract="Cortical neural dynamics fMRI study",
            doi="10.1234/neuro1",
            year=2021,
        )
        robot = Paper(
            title="Robot navigation via active inference",
            abstract="Embodied robot motor control",
            doi="10.1234/robot1",
            year=2021,
        )
        c = Corpus([neuro, robot])
        filtered = c.filter_by_subfield("C1_neuroscience")
        assert len(filtered) == 1
        assert filtered.papers[0].doi == "10.1234/neuro1"

    def test_filter_returns_empty_for_no_match(self):
        """Filtering for subfield with no matches returns empty corpus."""
        general = Paper(
            title="Active inference overview",
            abstract="The free energy principle",
            doi="10.1234/gen1",
            year=2020,
        )
        c = Corpus([general])
        filtered = c.filter_by_subfield("C3_language")
        assert len(filtered) == 0

    def test_filter_by_subfield_does_not_mutate_original(self):
        """Subfield filter returns new corpus, original unchanged."""
        papers = [
            Paper(title="Robot motor control", abstract="Robot embodied navigation", doi="10.1234/r1", year=2021),
            Paper(
                title="Active inference basics",
                abstract="Free energy principle variational",
                doi="10.1234/g1",
                year=2020,
            ),
        ]
        c = Corpus(papers)
        filtered = c.filter_by_subfield("C2_robotics")
        assert len(c) == 2
        assert len(filtered) == 1


# ---------------------------------------------------------------------------
# Corpus remove
# ---------------------------------------------------------------------------


class TestCorpusRemove:
    """Tests for Corpus.remove() method."""

    def test_remove_existing(self):
        """Removing an existing paper returns True and decreases length."""
        c = Corpus([make_friston_2010(), make_friston_2017()])
        cid = make_friston_2010().canonical_id
        assert c.remove(cid) is True
        assert len(c) == 1
        assert cid not in c

    def test_remove_nonexistent(self):
        """Removing a nonexistent paper returns False and length unchanged."""
        c = Corpus([make_friston_2010()])
        assert c.remove("doi:10.9999/nonexistent") is False
        assert len(c) == 1

    def test_remove_from_empty_corpus(self):
        """Removing from empty corpus returns False."""
        c = Corpus()
        assert c.remove("doi:10.1234/test") is False

    def test_remove_all(self):
        """Removing all papers leaves empty corpus."""
        p1 = make_friston_2010()
        p2 = make_friston_2017()
        c = Corpus([p1, p2])
        c.remove(p1.canonical_id)
        c.remove(p2.canonical_id)
        assert len(c) == 0
        assert c.papers == []

    def test_remove_then_add_back(self):
        """Can add a paper back after removing it."""
        p = make_friston_2010()
        c = Corpus([p])
        c.remove(p.canonical_id)
        assert len(c) == 0
        c.add(p)
        assert len(c) == 1
