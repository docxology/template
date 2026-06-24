"""Tests for knowledge_graph.nanopublication module.

Covers Assertion/Nanopublication construction, create_nanopub factory,
dict round-trip serialization, and JSONL file serialization.
No mocks -- all tests use real data and real file I/O.
"""

from __future__ import annotations

from pathlib import Path

from knowledge_graph.nanopublication import (
    Assertion,
    Nanopublication,
    create_nanopub,
    nanopub_to_dict,
    nanopub_from_dict,
    serialize_nanopubs,
    deserialize_nanopubs,
    merge_nanopubs,
    get_processed_paper_ids,
    append_nanopubs,
    nanopub_to_rdf,
    serialize_nanopubs_to_trig,
)


def _make_assertion(
    assertion_id: str = "a1",
    paper_id: str = "doi:10.1234/test",
    claim: str = "FEP applies universally",
    assertion_type: str = "supports",
    hypothesis_id: str = "PRIMARY_EFFICACY",
    confidence: float = 0.9,
    citation_count: int = 42,
) -> Assertion:
    """Helper to build an Assertion with sensible defaults."""
    return Assertion(
        assertion_id=assertion_id,
        paper_id=paper_id,
        claim=claim,
        assertion_type=assertion_type,
        hypothesis_id=hypothesis_id,
        confidence=confidence,
        citation_count=citation_count,
    )


class TestAssertionDataclass:
    """Validate Assertion construction and field access."""

    def test_all_fields_set(self) -> None:
        """All fields should be accessible after construction."""
        a = _make_assertion()
        assert a.assertion_id == "a1"
        assert a.paper_id == "doi:10.1234/test"
        assert a.claim == "FEP applies universally"
        assert a.assertion_type == "supports"
        assert a.hypothesis_id == "PRIMARY_EFFICACY"
        assert a.confidence == 0.9
        assert a.citation_count == 42

    def test_default_confidence_and_citations(self) -> None:
        """Defaults should be confidence=1.0 and citation_count=0."""
        a = Assertion(
            assertion_id="a2",
            paper_id="doi:10.0/x",
            claim="test",
            assertion_type="neutral",
            hypothesis_id="SCALABILITY",
        )
        assert a.confidence == 1.0
        assert a.citation_count == 0


class TestNanopublicationDataclass:
    """Validate Nanopublication construction."""

    def test_fields(self) -> None:
        """All fields should be set."""
        a = _make_assertion()
        np = Nanopublication(
            nanopub_id="np:001",
            assertion=a,
            attribution="pipeline-v1",
            created_date="2025-01-01T00:00:00+00:00",
        )
        assert np.nanopub_id == "np:001"
        assert np.assertion is a
        assert np.attribution == "pipeline-v1"
        assert np.created_date == "2025-01-01T00:00:00+00:00"

    def test_defaults(self) -> None:
        """Attribution and created_date should default to empty strings."""
        a = _make_assertion()
        np = Nanopublication(nanopub_id="np:002", assertion=a)
        assert np.attribution == ""
        assert np.created_date == ""


class TestCreateNanopub:
    """Validate the create_nanopub factory function."""

    def test_generates_nanopub_id(self) -> None:
        """create_nanopub should produce a non-empty nanopub_id."""
        a = _make_assertion()
        np = create_nanopub(a)
        assert np.nanopub_id.startswith("nanopub:")
        assert len(np.nanopub_id) > len("nanopub:")

    def test_sets_created_date(self) -> None:
        """create_nanopub should set a non-empty ISO date string."""
        a = _make_assertion()
        np = create_nanopub(a)
        assert np.created_date != ""
        assert "T" in np.created_date  # ISO format contains 'T'

    def test_attribution_forwarded(self) -> None:
        """Attribution argument should be stored on the nanopub."""
        a = _make_assertion()
        np = create_nanopub(a, attribution="my-pipeline")
        assert np.attribution == "my-pipeline"

    def test_assertion_preserved(self) -> None:
        """The original assertion should be attached unchanged."""
        a = _make_assertion()
        np = create_nanopub(a)
        assert np.assertion.assertion_id == a.assertion_id
        assert np.assertion.claim == a.claim

    def test_unique_ids(self) -> None:
        """Two calls should produce different nanopub_ids."""
        a = _make_assertion()
        np1 = create_nanopub(a)
        np2 = create_nanopub(a)
        assert np1.nanopub_id != np2.nanopub_id


class TestDictRoundTrip:
    """Validate nanopub_to_dict / nanopub_from_dict round-trip."""

    def test_round_trip_preserves_all_fields(self) -> None:
        """Serializing then deserializing should recover all fields."""
        a = _make_assertion(
            assertion_id="rt1",
            paper_id="doi:10.9999/round",
            claim="Round trip claim",
            assertion_type="contradicts",
            hypothesis_id="MECHANISTIC_BASIS",
            confidence=0.75,
            citation_count=123,
        )
        np = create_nanopub(a, attribution="test-suite")
        d = nanopub_to_dict(np)
        restored = nanopub_from_dict(d)

        assert restored.nanopub_id == np.nanopub_id
        assert restored.attribution == np.attribution
        assert restored.created_date == np.created_date
        assert restored.assertion.assertion_id == a.assertion_id
        assert restored.assertion.paper_id == a.paper_id
        assert restored.assertion.claim == a.claim
        assert restored.assertion.assertion_type == a.assertion_type
        assert restored.assertion.hypothesis_id == a.hypothesis_id
        assert restored.assertion.confidence == a.confidence
        assert restored.assertion.citation_count == a.citation_count

    def test_to_dict_returns_dict(self) -> None:
        """nanopub_to_dict should return a plain dict."""
        a = _make_assertion()
        np = create_nanopub(a)
        d = nanopub_to_dict(np)
        assert isinstance(d, dict)
        assert "nanopub_id" in d
        assert "assertion" in d
        assert isinstance(d["assertion"], dict)

    def test_from_dict_with_missing_optional_defaults(self) -> None:
        """Omitted optional fields should fall back to defaults."""
        data = {
            "nanopub_id": "np:manual",
            "assertion": {
                "assertion_id": "a99",
                "paper_id": "doi:10.0/manual",
                "claim": "manual claim",
                "assertion_type": "neutral",
                "hypothesis_id": "SCALABILITY",
            },
        }
        restored = nanopub_from_dict(data)
        assert restored.assertion.confidence == 1.0
        assert restored.assertion.citation_count == 0
        assert restored.attribution == ""
        assert restored.created_date == ""


class TestJSONLSerialization:
    """Validate serialize_nanopubs / deserialize_nanopubs with real files."""

    def test_round_trip_multiple(self, tmp_path: Path) -> None:
        """Serialize and deserialize multiple nanopubs via JSONL."""
        assertions = [_make_assertion(assertion_id=f"ser{i}", citation_count=i * 10) for i in range(5)]
        nanopubs = [create_nanopub(a, attribution=f"batch-{i}") for i, a in enumerate(assertions)]

        filepath = tmp_path / "nanopubs.jsonl"
        serialize_nanopubs(nanopubs, filepath)
        loaded = deserialize_nanopubs(filepath)

        assert len(loaded) == 5
        for original, restored in zip(nanopubs, loaded):
            assert original.nanopub_id == restored.nanopub_id
            assert original.assertion.assertion_id == restored.assertion.assertion_id
            assert original.assertion.citation_count == restored.assertion.citation_count
            assert original.attribution == restored.attribution

    def test_empty_list(self, tmp_path: Path) -> None:
        """Serializing an empty list should produce a readable empty file."""
        filepath = tmp_path / "empty.jsonl"
        serialize_nanopubs([], filepath)
        loaded = deserialize_nanopubs(filepath)
        assert loaded == []

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """serialize_nanopubs should create missing parent directories."""
        filepath = tmp_path / "sub" / "dir" / "nanopubs.jsonl"
        a = _make_assertion()
        np = create_nanopub(a)
        serialize_nanopubs([np], filepath)
        assert filepath.exists()
        loaded = deserialize_nanopubs(filepath)
        assert len(loaded) == 1

    def test_file_is_line_delimited(self, tmp_path: Path) -> None:
        """Each nanopub should occupy exactly one line."""
        assertions = [_make_assertion(assertion_id=f"line{i}") for i in range(3)]
        nanopubs = [create_nanopub(a) for a in assertions]
        filepath = tmp_path / "lines.jsonl"
        serialize_nanopubs(nanopubs, filepath)
        text = filepath.read_text()
        non_empty = [ln for ln in text.strip().split("\n") if ln.strip()]
        assert len(non_empty) == 3


class TestMergeNanopubs:
    """Validate merge_nanopubs deduplication and accumulation."""

    def test_disjoint_lists_are_concatenated(self) -> None:
        """Merging disjoint lists should keep all entries."""
        a1 = _make_assertion(paper_id="doi:10.1/a", hypothesis_id="H1")
        a2 = _make_assertion(paper_id="doi:10.2/b", hypothesis_id="H2")
        np1 = create_nanopub(a1)
        np2 = create_nanopub(a2)
        merged = merge_nanopubs([np1], [np2])
        assert len(merged) == 2

    def test_duplicate_key_new_wins(self) -> None:
        """When both lists contain same (paper_id, hypothesis_id), new wins."""
        old = _make_assertion(paper_id="doi:10.1/a", hypothesis_id="H1", claim="old claim")
        new = _make_assertion(paper_id="doi:10.1/a", hypothesis_id="H1", claim="new claim")
        np_old = create_nanopub(old)
        np_new = create_nanopub(new)
        merged = merge_nanopubs([np_old], [np_new])
        assert len(merged) == 1
        assert merged[0].assertion.claim == "new claim"

    def test_empty_existing_returns_new(self) -> None:
        """Merging into empty existing should return all new entries."""
        a = _make_assertion(paper_id="doi:10.1/x")
        np1 = create_nanopub(a)
        merged = merge_nanopubs([], [np1])
        assert len(merged) == 1

    def test_empty_new_returns_existing(self) -> None:
        """Merging empty new into existing should return existing."""
        a = _make_assertion(paper_id="doi:10.1/x")
        np1 = create_nanopub(a)
        merged = merge_nanopubs([np1], [])
        assert len(merged) == 1

    def test_multiple_hypotheses_same_paper(self) -> None:
        """Different hypotheses for same paper should be kept."""
        a1 = _make_assertion(paper_id="doi:10.1/a", hypothesis_id="H1")
        a2 = _make_assertion(paper_id="doi:10.1/a", hypothesis_id="H2")
        np1 = create_nanopub(a1)
        np2 = create_nanopub(a2)
        merged = merge_nanopubs([np1], [np2])
        assert len(merged) == 2


class TestGetProcessedPaperIds:
    """Validate get_processed_paper_ids extracts unique paper IDs."""

    def test_extracts_unique_ids(self) -> None:
        """Should return set of unique paper IDs."""
        a1 = _make_assertion(paper_id="doi:10.1/a", hypothesis_id="H1")
        a2 = _make_assertion(paper_id="doi:10.1/a", hypothesis_id="H2")
        a3 = _make_assertion(paper_id="doi:10.2/b", hypothesis_id="H1")
        nps = [create_nanopub(a) for a in [a1, a2, a3]]
        ids = get_processed_paper_ids(nps)
        assert ids == {"doi:10.1/a", "doi:10.2/b"}

    def test_empty_returns_empty_set(self) -> None:
        """Empty list should return empty set."""
        assert get_processed_paper_ids([]) == set()


class TestAppendNanopubs:
    """Validate append_nanopubs atomic incremental persistence."""

    def test_creates_fresh_file(self, tmp_path: Path) -> None:
        """append_nanopubs on a non-existent file creates it."""
        p = tmp_path / "new.jsonl"
        a = _make_assertion(paper_id="doi:10.1/a", hypothesis_id="H1")
        np1 = create_nanopub(a)
        merged = append_nanopubs([np1], p)
        assert p.exists()
        assert len(merged) == 1
        assert merged[0].assertion.paper_id == "doi:10.1/a"

    def test_appends_to_existing(self, tmp_path: Path) -> None:
        """append_nanopubs merges with pre-existing entries."""
        p = tmp_path / "existing.jsonl"
        a1 = _make_assertion(paper_id="doi:10.1/a", hypothesis_id="H1")
        serialize_nanopubs([create_nanopub(a1)], p)

        a2 = _make_assertion(paper_id="doi:10.2/b", hypothesis_id="H2")
        merged = append_nanopubs([create_nanopub(a2)], p)
        assert len(merged) == 2

        # Verify file on disk has both
        reloaded = deserialize_nanopubs(p)
        assert len(reloaded) == 2
        ids = {np_obj.assertion.paper_id for np_obj in reloaded}
        assert ids == {"doi:10.1/a", "doi:10.2/b"}

    def test_deduplicates_new_wins(self, tmp_path: Path) -> None:
        """append_nanopubs deduplicates by (paper_id, hypothesis_id); new wins."""
        p = tmp_path / "dedup.jsonl"
        old = _make_assertion(paper_id="doi:10.1/a", hypothesis_id="H1", claim="old")
        serialize_nanopubs([create_nanopub(old)], p)

        new = _make_assertion(paper_id="doi:10.1/a", hypothesis_id="H1", claim="new")
        merged = append_nanopubs([create_nanopub(new)], p)
        assert len(merged) == 1
        assert merged[0].assertion.claim == "new"

    def test_atomicity_no_tmp_left(self, tmp_path: Path) -> None:
        """After append_nanopubs completes, no .tmp file should remain."""
        p = tmp_path / "atomic.jsonl"
        a = _make_assertion(paper_id="doi:10.1/a")
        append_nanopubs([create_nanopub(a)], p)
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == []

    def test_logs_file_path_and_count(self, tmp_path: Path, caplog) -> None:
        """append_nanopubs logs the nanopub count and file path."""
        import logging

        p = tmp_path / "logged.jsonl"
        a = _make_assertion(paper_id="doi:10.1/log")
        with caplog.at_level(logging.INFO, logger="knowledge_graph.nanopublication"):
            append_nanopubs([create_nanopub(a)], p)
        assert any("Wrote 1 nanopubs" in m for m in caplog.messages)
        assert any(str(p) in m for m in caplog.messages)


class TestNanopubRDF:
    """RDF/TriG serialization per https://nanopub.net/ (Assertion, Provenance, Publication Info)."""

    def test_nanopub_to_rdf_returns_dataset(self) -> None:
        """nanopub_to_rdf should return an rdflib Dataset with named graphs."""
        a = _make_assertion(
            assertion_id="r1",
            paper_id="doi:10.1234/rdf",
            claim="Test claim for RDF",
            assertion_type="supports",
            hypothesis_id="PRIMARY_EFFICACY",
        )
        np_obj = Nanopublication(
            nanopub_id="nanopub:abc123",
            assertion=a,
            attribution="pipeline_v1",
            created_date="2025-01-15T12:00:00+00:00",
        )
        ds = nanopub_to_rdf(np_obj)
        assert ds is not None
        graphs = list(ds.graphs())
        assert len(graphs) >= 4  # head, assertion, provenance, pubinfo

    def test_trig_contains_nanopub_structure(self, tmp_path: Path) -> None:
        """Serialized TriG should contain np:hasAssertion, hasProvenance, hasPublicationInfo."""
        a = _make_assertion(claim="RDF export test", assertion_type="contradicts")
        np_obj = create_nanopub(a, attribution="test")
        trig_path = tmp_path / "out.trig"
        serialize_nanopubs_to_trig([np_obj], trig_path)
        content = trig_path.read_text(encoding="utf-8")
        assert "hasAssertion" in content or "np:" in content
        assert "hasProvenance" in content
        assert "hasPublicationInfo" in content
        assert "Nanopublication" in content
        assert "RDF export test" in content

    def test_trig_roundtrip_two_nanopubs(self, tmp_path: Path) -> None:
        """Two nanopubs should both appear in the TriG file."""
        a1 = _make_assertion(paper_id="p1", hypothesis_id="PRIMARY_EFFICACY")
        a2 = _make_assertion(paper_id="p2", hypothesis_id="SCALABILITY")
        nanopubs = [create_nanopub(a1), create_nanopub(a2)]
        trig_path = tmp_path / "two.trig"
        serialize_nanopubs_to_trig(nanopubs, trig_path)
        content = trig_path.read_text(encoding="utf-8")
        assert "PRIMARY_EFFICACY" in content or "primary_efficacy" in content
        assert "SCALABILITY" in content or "scalability" in content
