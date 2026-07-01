"""Citation-key collision handling in the pipeline."""

from __future__ import annotations

from pathlib import Path

from infrastructure.search.literature import Paper, SearchBackend

from src.config import (
    EnrichmentConfig,
    LLMConfig,
    ProjectConfig,
    ReportConfig,
    SearchConfig,
)
from src.pipeline import (
    _build_citation_keys,
    _disambiguate_citation_key,
    run_literature_pipeline,
)


def test_disambiguate_returns_base_when_unique():
    assert _disambiguate_citation_key("foo2024bar", set()) == "foo2024bar"


def test_disambiguate_appends_letter():
    taken = {"foo2024bar"}
    assert _disambiguate_citation_key("foo2024bar", taken) == "foo2024bara"


def test_disambiguate_walks_alphabet():
    base = "x2024y"
    taken = {base, base + "a", base + "b", base + "c"}
    assert _disambiguate_citation_key(base, taken) == "x2024yd"


def test_disambiguate_handles_alpha_overflow():
    base = "x2024y"
    taken = {base} | {base + ch for ch in "abcdefghijklmnopqrstuvwxyz"}
    # Next available is the first two-letter combo: aa.
    assert _disambiguate_citation_key(base, taken) == "x2024yaa"


def test_build_citation_keys_unique_papers():
    papers = [
        Paper(id="x:1", title="Alpha Method", authors=["Smith, A"], year=2024),
        Paper(id="x:2", title="Beta Method", authors=["Jones, B"], year=2024),
    ]
    mapping, entries = _build_citation_keys(papers)
    assert len(mapping) == 2
    assert mapping["x:1"] != mapping["x:2"]
    keys = [e.citation_key for e in entries]
    assert len(set(keys)) == 2


def test_build_citation_keys_collision_disambiguated():
    # Same author + same year + same title-first-word => collision.
    papers = [
        Paper(id="x:1", title="Method One", authors=["Smith, A"], year=2024),
        Paper(id="x:2", title="Method Two", authors=["Smith, A"], year=2024),
        Paper(id="x:3", title="Method Three", authors=["Smith, A"], year=2024),
    ]
    mapping, entries = _build_citation_keys(papers)
    keys = list(mapping.values())
    # All distinct.
    assert len(set(keys)) == 3
    # First gets the bare key, rest get suffixes.
    assert keys[0] == "smith2024method"
    assert keys[1] == "smith2024methoda"
    assert keys[2] == "smith2024methodb"


def test_pipeline_writes_collision_free_bib(tmp_path: Path):
    config = ProjectConfig(
        title="Demo",
        search=SearchConfig(query="x", max_results=10, sources=["arxiv"], cache_dir=""),
        enrichment=EnrichmentConfig(fetch_abstracts=False, fetch_fulltext=False),
        llm=LLMConfig(enabled=False),
        report=ReportConfig(),
    )

    class _Colliding(SearchBackend):
        name = "fake"

        def search(self, query):
            return [
                Paper(id="x:1", title="Method One", authors=["Smith, A"], year=2024),
                Paper(id="x:2", title="Method Two", authors=["Smith, A"], year=2024),
            ]

    # Override sources to avoid hitting the network.
    config.search.sources = []
    artifacts = run_literature_pipeline(
        config,
        project_root=tmp_path,
        extra_backends=[_Colliding()],
    )
    assert artifacts.bibtex_path is not None
    text = artifacts.bibtex_path.read_text(encoding="utf-8")
    # Both keys must appear.
    assert "@article{smith2024method," in text
    assert "@article{smith2024methoda," in text
    # And the citation_keys map matches the file.
    assert set(artifacts.citation_keys.values()) == {
        "smith2024method",
        "smith2024methoda",
    }


def test_enrichment_log_persisted(tmp_path: Path):
    """When enrichment runs, a JSON log lands in output/enrichment_log.json."""
    config = ProjectConfig(
        title="Demo",
        search=SearchConfig(
            query="x",
            sources=["local"],
            local_corpus="data/corpus.json",
            cache_dir="",
        ),
        enrichment=EnrichmentConfig(fetch_abstracts=True, fetch_fulltext=False),
        llm=LLMConfig(enabled=False),
        report=ReportConfig(),
    )
    # Build a tiny corpus next to the project root. The paper carries an
    # abstract so the AbstractFetcher resolves "skipped" without a network
    # call — the log-write path is what we're verifying here.
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "corpus.json").write_text(
        '[{"id": "arxiv:1", "title": "x research", "year": 2020, "abstract": "An abstract."}]',
        encoding="utf-8",
    )

    run_literature_pipeline(config, project_root=tmp_path)
    log_path = tmp_path / "output" / "enrichment_log.json"
    assert log_path.exists()
    import json

    payload = json.loads(log_path.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert payload[0]["paper_id"] == "arxiv:1"
    # Status is either "skipped" (no source) or "error" (no http) — both are
    # valid; the key is that the log was written and is structured.
    assert payload[0]["status"] in {"skipped", "error", "hit", "cached"}


def test_local_corpus_resolved_from_config(tmp_path: Path):
    """`config.search.local_corpus` is resolved against project_root."""
    config = ProjectConfig(
        title="Demo",
        search=SearchConfig(
            query="x",
            sources=["local"],
            local_corpus="data/corpus.json",
            cache_dir="",
        ),
        enrichment=EnrichmentConfig(fetch_abstracts=False, fetch_fulltext=False),
        llm=LLMConfig(enabled=False),
        report=ReportConfig(),
    )
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "corpus.json").write_text('[{"id": "x:1", "title": "Convex"}]', encoding="utf-8")

    artifacts = run_literature_pipeline(config, project_root=tmp_path)
    # Should have found the corpus without an explicit corpus_path argument.
    assert any(p.id == "x:1" for p in artifacts.papers)


def test_disambiguate_numeric_pathological_fallback():
    """When all 26 + 26*26 + 26*26*26 alphabetic suffixes are taken, the
    function falls back to numeric ``_1``, ``_2``, … suffixes."""
    base = "z"
    taken: set[str] = {base}
    # Saturate single, double, and triple-letter alphabet space.
    from itertools import product

    for length in range(1, 4):
        for combo in product("abcdefghijklmnopqrstuvwxyz", repeat=length):
            taken.add(base + "".join(combo))
    # First fallback must be _1.
    assert _disambiguate_citation_key(base, taken) == base + "_1"
    # Skip _1 to verify the counter loop advances.
    assert _disambiguate_citation_key(base, taken | {base + "_1"}) == base + "_2"


def test_paperclip_backend_requires_api_key(monkeypatch, tmp_path: Path):
    """`paperclip` source without `PAPERCLIP_API_KEY` raises RuntimeError."""
    import pytest as _pytest

    monkeypatch.delenv("PAPERCLIP_API_KEY", raising=False)
    config = ProjectConfig(
        title="Demo",
        search=SearchConfig(query="x", sources=["paperclip"], cache_dir=""),
        enrichment=EnrichmentConfig(fetch_abstracts=False, fetch_fulltext=False),
        llm=LLMConfig(enabled=False),
        report=ReportConfig(),
    )
    with _pytest.raises(RuntimeError, match="PAPERCLIP_API_KEY"):
        run_literature_pipeline(config, project_root=tmp_path)


def test_unknown_source_raises_value_error(tmp_path: Path):
    """Unknown source names surface as a ValueError, not a silent skip."""
    import pytest as _pytest

    config = ProjectConfig(
        title="Demo",
        search=SearchConfig(query="x", sources=["bogus"], cache_dir=""),
        enrichment=EnrichmentConfig(fetch_abstracts=False, fetch_fulltext=False),
        llm=LLMConfig(enabled=False),
        report=ReportConfig(),
    )
    with _pytest.raises(ValueError, match="Unknown search source"):
        run_literature_pipeline(config, project_root=tmp_path)


def test_local_source_without_corpus_path_raises(tmp_path: Path):
    """Setting sources=[local] without a configured local_corpus path raises."""
    import pytest as _pytest

    config = ProjectConfig(
        title="Demo",
        search=SearchConfig(query="x", sources=["local"], local_corpus="", cache_dir=""),
        enrichment=EnrichmentConfig(fetch_abstracts=False, fetch_fulltext=False),
        llm=LLMConfig(enabled=False),
        report=ReportConfig(),
    )
    with _pytest.raises(ValueError, match="no corpus_path"):
        run_literature_pipeline(config, project_root=tmp_path)


def test_pipeline_with_fulltext_enrichment_log(tmp_path: Path):
    """Exercise the FulltextFetcher branch in run_literature_pipeline."""
    config = ProjectConfig(
        title="Demo",
        search=SearchConfig(
            query="x",
            sources=["local"],
            local_corpus="data/corpus.json",
            cache_dir="",
        ),
        enrichment=EnrichmentConfig(
            fetch_abstracts=False,
            fetch_fulltext=True,
            fulltext_cache_dir="output/cache/pdf",
            max_fulltext_chars=100,
        ),
        llm=LLMConfig(enabled=False),
        report=ReportConfig(),
    )
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "corpus.json").write_text(
        '[{"id": "x:1", "title": "x research paper", "fulltext": "abc"}]',
        encoding="utf-8",
    )
    artifacts = run_literature_pipeline(config, project_root=tmp_path)
    # Fulltext was already present so the fetcher returns "skipped";
    # what we're verifying is that the fulltext branch executed without error
    # and the FulltextFetcher contributed a FetchResult to the log.
    assert artifacts.enrichment_log, "fulltext branch should append a FetchResult"
    assert artifacts.enrichment_log[0].paper.id == "x:1"
