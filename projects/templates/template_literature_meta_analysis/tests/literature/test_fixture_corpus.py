"""Tests for the deterministic synthetic fixture-corpus builder (no mocks)."""

from __future__ import annotations

from literature.fixture_corpus import DEFAULT_TERM, TOPICS, build_synthetic_corpus


def _serialize(corpus) -> list[dict]:
    return [p.to_dict() for p in corpus.papers]


def test_record_count_matches_n() -> None:
    corpus = build_synthetic_corpus(n=30, seed=42)
    assert len(corpus) == 30


def test_is_deterministic_same_seed() -> None:
    a = build_synthetic_corpus(term="modafinil", n=40, seed=42)
    b = build_synthetic_corpus(term="modafinil", n=40, seed=42)
    assert _serialize(a) == _serialize(b)


def test_different_seed_changes_corpus() -> None:
    a = build_synthetic_corpus(n=40, seed=42)
    b = build_synthetic_corpus(n=40, seed=7)
    assert _serialize(a) != _serialize(b)


def test_term_flows_into_dois() -> None:
    corpus = build_synthetic_corpus(term="caffeine", n=12, seed=42)
    assert all(p.doi.startswith("10.5555/caffeine.") for p in corpus.papers)


def test_dois_use_reserved_test_prefix() -> None:
    corpus = build_synthetic_corpus(n=20, seed=42)
    assert all(p.doi.startswith("10.5555/") for p in corpus.papers)


def test_references_point_to_earlier_records() -> None:
    corpus = build_synthetic_corpus(n=50, seed=42)
    papers = corpus.papers
    ids = [p.canonical_id for p in papers]
    index = {cid: i for i, cid in enumerate(ids)}
    has_any_ref = False
    for i, paper in enumerate(papers):
        for ref in paper.references:
            has_any_ref = True
            # every cited id exists and belongs to an earlier record
            assert ref in index
            assert index[ref] < i
    assert has_any_ref  # the corpus forms a non-trivial citation network


def test_all_subfields_represented() -> None:
    # n >= number of subfields, round-robin assignment hits every topic
    corpus = build_synthetic_corpus(n=len(TOPICS) * 3, seed=42)
    # every record's abstract is drawn from one of the topic sentence pools
    all_sentences = {s for t in TOPICS.values() for s in t["sentences"]}
    for paper in corpus.papers:
        assert any(sentence in paper.abstract for sentence in all_sentences)


def test_default_term_is_modafinil() -> None:
    assert DEFAULT_TERM == "modafinil"
    corpus = build_synthetic_corpus(n=6, seed=42)
    assert corpus.papers[0].doi.startswith("10.5555/modafinil.")


def test_some_records_open_access_with_pdf() -> None:
    corpus = build_synthetic_corpus(n=60, seed=42)
    oa = [p for p in corpus.papers if p.is_open_access]
    assert oa  # the OA fraction is non-empty
    assert all(p.pdf_url and p.full_text_source == "repository" for p in oa)


def test_some_records_have_openalex_id() -> None:
    corpus = build_synthetic_corpus(n=30, seed=42)
    assert any(p.openalex_id for p in corpus.papers)
