"""Tests for literature data models: Paper, Author, Citation.

Covers construction, canonical_id priority, to_dict/from_dict round-trip,
metadata_completeness scoring, and edge cases. Uses real Active Inference
paper examples throughout.
"""

from datetime import date

from literature.models import Author, Citation, Paper


# ---------------------------------------------------------------------------
# Author tests
# ---------------------------------------------------------------------------


class TestAuthor:
    """Tests for the Author dataclass."""

    def test_author_minimal(self):
        """Author can be created with just a name."""
        a = Author(name="Karl Friston")
        assert a.name == "Karl Friston"
        assert a.affiliation is None
        assert a.orcid is None

    def test_author_full(self):
        """Author with all fields populated."""
        a = Author(
            name="Karl Friston",
            affiliation="University College London",
            orcid="0000-0001-7984-8909",
        )
        assert a.name == "Karl Friston"
        assert a.affiliation == "University College London"
        assert a.orcid == "0000-0001-7984-8909"

    def test_author_equality(self):
        """Two Authors with same fields are equal (dataclass default)."""
        a1 = Author(name="Thomas Parr")
        a2 = Author(name="Thomas Parr")
        assert a1 == a2

    def test_author_inequality(self):
        """Authors with different names are not equal."""
        a1 = Author(name="Karl Friston")
        a2 = Author(name="Thomas Parr")
        assert a1 != a2


# ---------------------------------------------------------------------------
# Citation tests
# ---------------------------------------------------------------------------


class TestCitation:
    """Tests for the Citation dataclass."""

    def test_citation_minimal(self):
        """Citation with required fields only."""
        c = Citation(source_id="doi:10.1162/NECO_a_00912", target_id="doi:10.1038/nrn2787")
        assert c.source_id == "doi:10.1162/NECO_a_00912"
        assert c.target_id == "doi:10.1038/nrn2787"
        assert c.context is None

    def test_citation_with_context(self):
        """Citation with context text."""
        c = Citation(
            source_id="s2:abc123",
            target_id="s2:def456",
            context="As shown in the free energy principle (Friston, 2010)...",
        )
        assert "free energy principle" in c.context

    def test_citation_equality(self):
        """Citations with same fields are equal."""
        c1 = Citation(source_id="s2:a", target_id="s2:b")
        c2 = Citation(source_id="s2:a", target_id="s2:b")
        assert c1 == c2


# ---------------------------------------------------------------------------
# Paper canonical_id priority tests
# ---------------------------------------------------------------------------


class TestPaperCanonicalId:
    """Tests for canonical_id priority: doi > arxiv > s2 > openalex > title hash."""

    def test_doi_highest_priority(self):
        """DOI takes priority over all other IDs (normalized to lower-case)."""
        p = Paper(
            title="Active Inference",
            doi="10.1162/NECO_a_00912",
            arxiv_id="1709.02341",
            s2_id="abc123",
            openalex_id="W12345",
        )
        # canonical_id case-folds the DOI per ISO 26324; raw .doi is preserved.
        assert p.canonical_id == "doi:10.1162/neco_a_00912"
        assert p.doi == "10.1162/NECO_a_00912"

    def test_doi_normalized_for_cross_engine_merge(self):
        """Case/prefix-variant DOIs from different engines map to ONE canonical_id.

        Without normalization these escape de-duplication and inflate the corpus.
        """
        from_crossref = Paper(title="Same Paper", doi="10.1038/Nature12345")
        from_openalex = Paper(title="Same Paper", doi="https://doi.org/10.1038/nature12345")
        from_pubmed = Paper(title="Same Paper", doi="  10.1038/NATURE12345  ")
        assert (
            from_crossref.canonical_id
            == from_openalex.canonical_id
            == from_pubmed.canonical_id
            == "doi:10.1038/nature12345"
        )

    def test_arxiv_second_priority(self):
        """arXiv ID used when DOI is absent."""
        p = Paper(
            title="Active Inference",
            arxiv_id="1709.02341",
            s2_id="abc123",
            openalex_id="W12345",
        )
        assert p.canonical_id == "arxiv:1709.02341"

    def test_s2_third_priority(self):
        """S2 ID used when DOI and arXiv are absent."""
        p = Paper(title="Active Inference", s2_id="abc123", openalex_id="W12345")
        assert p.canonical_id == "s2:abc123"

    def test_openalex_fourth_priority(self):
        """OpenAlex ID used when DOI, arXiv, and S2 are absent."""
        p = Paper(title="Active Inference", openalex_id="W12345")
        assert p.canonical_id == "openalex:W12345"

    def test_title_hash_fallback(self):
        """Title hash used when no other identifiers are present."""
        p = Paper(title="Active Inference: A Process Theory")
        cid = p.canonical_id
        assert cid.startswith("title:")
        # Hash should be deterministic
        p2 = Paper(title="Active Inference: A Process Theory")
        assert p.canonical_id == p2.canonical_id

    def test_title_hash_is_stable_across_processes(self):
        """Title fallback id must NOT depend on PYTHONHASHSEED.

        The builtin ``hash()`` on ``str`` is salted per process, so an
        in-process equality check cannot catch a regression here. We spawn two
        subprocesses with different hash seeds and assert the title-only
        canonical_id is identical — this is what makes de-dup and byte-stable
        corpora hold for live records that lack DOI/arXiv/S2/OpenAlex ids.
        """
        import subprocess
        import sys
        from pathlib import Path

        src = str(Path(__file__).resolve().parents[2] / "src")
        snippet = (
            "import sys; sys.path.insert(0, %r);"
            "from literature.models import Paper;"
            "print(Paper(title='No Identifiers Here At All').canonical_id)" % src
        )

        def run(seed: str) -> str:
            env = {"PYTHONHASHSEED": seed, "PATH": ""}
            out = subprocess.run(
                [sys.executable, "-c", snippet],
                capture_output=True,
                text=True,
                check=True,
                env=env,
            )
            return out.stdout.strip()

        id0, id1 = run("0"), run("1")
        assert id0 == id1, f"canonical_id varied with PYTHONHASHSEED: {id0!r} != {id1!r}"
        assert id0.startswith("title:")

    def test_title_hash_case_insensitive(self):
        """Title hash is case-insensitive."""
        p1 = Paper(title="Active Inference")
        p2 = Paper(title="active inference")
        assert p1.canonical_id == p2.canonical_id

    def test_title_hash_strip_whitespace(self):
        """Title hash ignores leading/trailing whitespace."""
        p1 = Paper(title="Active Inference")
        p2 = Paper(title="  Active Inference  ")
        assert p1.canonical_id == p2.canonical_id


# ---------------------------------------------------------------------------
# Paper construction and metadata
# ---------------------------------------------------------------------------


class TestPaperConstruction:
    """Tests for Paper object construction and metadata_completeness."""

    def test_minimal_paper(self):
        """Paper can be created with just a title."""
        p = Paper(title="Test Paper")
        assert p.title == "Test Paper"
        assert p.abstract == ""
        assert p.authors == []
        assert p.year is None
        assert p.citation_count == 0
        assert p.references == []

    def test_full_paper(self):
        """Paper with all fields populated."""
        p = Paper(
            title="Active Inference: A Process Theory",
            abstract="This paper introduces active inference...",
            authors=[
                Author(name="Karl Friston"),
                Author(name="Thomas Parr"),
                Author(name="Giovanni Pezzulo"),
            ],
            year=2017,
            doi="10.1162/NECO_a_00912",
            arxiv_id="1709.02341",
            s2_id="abc123",
            openalex_id="W12345",
            venue="Neural Computation",
            citation_count=450,
            references=["doi:10.1038/nrn2787"],
            publication_date=date(2017, 1, 15),
        )
        assert p.title == "Active Inference: A Process Theory"
        assert len(p.authors) == 3
        assert p.year == 2017
        assert p.citation_count == 450

    def test_metadata_completeness_empty(self):
        """Paper with only title has completeness 0."""
        p = Paper(title="Test")
        assert p.metadata_completeness == 0

    def test_metadata_completeness_full(self):
        """Paper with all optional fields has maximum completeness."""
        p = Paper(
            title="Test",
            abstract="Some abstract",
            authors=[Author(name="Author")],
            year=2020,
            doi="10.1234/test",
            arxiv_id="2001.00000",
            s2_id="s2id",
            openalex_id="oaid",
            venue="Nature",
            citation_count=100,
            references=["doi:10.other/ref"],
            publication_date=date(2020, 1, 1),
            pdf_url="https://arxiv.org/pdf/2001.00000.pdf",
            is_open_access=True,
        )
        assert p.metadata_completeness == 13  # All 11 original + pdf_url + is_open_access

    def test_metadata_completeness_partial(self):
        """Paper with some fields populated has intermediate completeness."""
        p = Paper(title="Test", abstract="Has abstract", year=2020, doi="10.1234/t")
        assert p.metadata_completeness == 3  # abstract, year, doi


# ---------------------------------------------------------------------------
# Round-trip serialization
# ---------------------------------------------------------------------------


class TestPaperSerialization:
    """Tests for to_dict and from_dict round-trip."""

    def test_round_trip_minimal(self):
        """Minimal paper survives serialization round-trip."""
        original = Paper(title="Minimal Paper")
        data = original.to_dict()
        restored = Paper.from_dict(data)
        assert restored.title == original.title
        assert restored.abstract == ""
        assert restored.authors == []
        assert restored.year is None

    def test_round_trip_full(self):
        """Fully populated paper survives serialization round-trip."""
        original = Paper(
            title="The free-energy principle: a unified brain theory?",
            abstract="A unifying theory of the brain...",
            authors=[
                Author(
                    name="Karl Friston",
                    affiliation="UCL",
                    orcid="0000-0001-7984-8909",
                ),
            ],
            year=2010,
            doi="10.1038/nrn2787",
            arxiv_id=None,
            s2_id="friston2010",
            openalex_id="W2140",
            venue="Nature Reviews Neuroscience",
            citation_count=3500,
            references=["doi:10.1006/nimg.2002.1091"],
            publication_date=date(2010, 2, 13),
        )
        data = original.to_dict()
        restored = Paper.from_dict(data)

        assert restored.title == original.title
        assert restored.abstract == original.abstract
        assert len(restored.authors) == 1
        assert restored.authors[0].name == "Karl Friston"
        assert restored.authors[0].affiliation == "UCL"
        assert restored.authors[0].orcid == "0000-0001-7984-8909"
        assert restored.year == 2010
        assert restored.doi == "10.1038/nrn2787"
        assert restored.arxiv_id is None
        assert restored.s2_id == "friston2010"
        assert restored.openalex_id == "W2140"
        assert restored.venue == "Nature Reviews Neuroscience"
        assert restored.citation_count == 3500
        assert restored.references == ["doi:10.1006/nimg.2002.1091"]
        assert restored.publication_date == date(2010, 2, 13)
        assert restored.canonical_id == original.canonical_id

    def test_to_dict_structure(self):
        """to_dict returns expected keys."""
        p = Paper(title="Test")
        data = p.to_dict()
        expected_keys = {
            "title",
            "abstract",
            "authors",
            "year",
            "doi",
            "arxiv_id",
            "s2_id",
            "openalex_id",
            "venue",
            "citation_count",
            "references",
            "publication_date",
            "pdf_url",
            "is_open_access",
            "full_text_source",
        }
        assert set(data.keys()) == expected_keys

    def test_from_dict_missing_optional_fields(self):
        """from_dict handles missing optional fields gracefully."""
        data = {"title": "Only Title"}
        p = Paper.from_dict(data)
        assert p.title == "Only Title"
        assert p.abstract == ""
        assert p.year is None
        assert p.authors == []

    def test_publication_date_serialization(self):
        """Publication date serializes to ISO format and back."""
        original = Paper(title="T", publication_date=date(2023, 6, 15))
        data = original.to_dict()
        assert data["publication_date"] == "2023-06-15"
        restored = Paper.from_dict(data)
        assert restored.publication_date == date(2023, 6, 15)

    def test_publication_date_none(self):
        """None publication_date serializes as None."""
        p = Paper(title="T")
        data = p.to_dict()
        assert data["publication_date"] is None
        restored = Paper.from_dict(data)
        assert restored.publication_date is None

    def test_authors_serialization(self):
        """Multiple authors with varying fields serialize correctly."""
        original = Paper(
            title="Multi-author paper",
            authors=[
                Author(name="A. One", affiliation="MIT", orcid="0000-0001-0000-0001"),
                Author(name="B. Two"),
                Author(name="C. Three", affiliation="Stanford"),
            ],
        )
        data = original.to_dict()
        assert len(data["authors"]) == 3
        assert data["authors"][0]["orcid"] == "0000-0001-0000-0001"
        assert data["authors"][1]["affiliation"] is None
        assert data["authors"][2]["orcid"] is None

        restored = Paper.from_dict(data)
        assert len(restored.authors) == 3
        assert restored.authors[0].orcid == "0000-0001-0000-0001"
        assert restored.authors[1].affiliation is None

    def test_round_trip_fulltext_fields(self):
        """Full-text fields survive serialization round-trip."""
        original = Paper(
            title="OA Paper",
            pdf_url="https://arxiv.org/pdf/2301.12345.pdf",
            is_open_access=True,
            full_text_source="arxiv",
        )
        data = original.to_dict()
        assert data["pdf_url"] == "https://arxiv.org/pdf/2301.12345.pdf"
        assert data["is_open_access"] is True
        assert data["full_text_source"] == "arxiv"

        restored = Paper.from_dict(data)
        assert restored.pdf_url == original.pdf_url
        assert restored.is_open_access is True
        assert restored.full_text_source == "arxiv"

    def test_from_dict_backward_compatible(self):
        """from_dict handles legacy data without full-text fields."""
        data = {
            "title": "Old Paper",
            "abstract": "Legacy record",
            "authors": [],
            "year": 2019,
        }
        p = Paper.from_dict(data)
        assert p.title == "Old Paper"
        assert p.pdf_url is None
        assert p.is_open_access is None
        assert p.full_text_source is None

    def test_fulltext_fields_default_none(self):
        """New full-text fields default to None when not specified."""
        p = Paper(title="No FT")
        assert p.pdf_url is None
        assert p.is_open_access is None
        assert p.full_text_source is None

    def test_metadata_completeness_with_oa_fields(self):
        """pdf_url and is_open_access contribute to completeness."""
        p = Paper(title="Test", pdf_url="https://example.com/paper.pdf", is_open_access=False)
        assert p.metadata_completeness == 2  # pdf_url + is_open_access
