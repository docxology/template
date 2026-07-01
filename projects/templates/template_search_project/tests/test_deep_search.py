"""Tests for src.deep_search — multi-keyword deep search workflow.

No mocks. Uses LocalBackend against committed corpus + a deterministic
in-process LLM callable that returns real, well-formed reading-note text
so tests run offline and are reproducible.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.reference.citation import parse_bibfile
from infrastructure.search.literature import Paper, SearchBackend, SearchQuery

from src.config import DeepSearchConfig
from src.deep_search import (
    DEEP_PROMPT,
    DeepSearchArtifacts,
    KeywordResult,
    build_rich_paper_block,
    run_deep_search,
    safe_id,
    slugify,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _deterministic_llm(prompt: str) -> str:
    """Deterministic LLM: echoes prompt length + first 60 chars."""
    return f"## Contribution\n\n_(deterministic summary, prompt {len(prompt)} chars)_\n\n## Tags\n\ndeterministic, test, fixture\n"


def _make_corpus(tmp_path: Path) -> Path:
    """Write a small but realistic corpus that responds to multiple keywords."""
    papers = [
        {
            "id": "doi:10.1126/science.1213847",
            "title": "Reproducible research in computational science",
            "authors": ["Roger D Peng"],
            "year": 2011,
            "doi": "10.1126/science.1213847",
            "venue": "Science",
            "venue_type": "journal",
            "abstract": "Reproducible research is a hallmark of computational science.",
        },
        {
            "id": "doi:10.1017/CBO9780511804441",
            "title": "Convex Optimization",
            "authors": ["Stephen Boyd", "Lieven Vandenberghe"],
            "year": 2004,
            "doi": "10.1017/CBO9780511804441",
            "venue": "Cambridge University Press",
            "venue_type": "book",
            "abstract": "A comprehensive treatment of convex optimization theory.",
        },
        {
            "id": "arxiv:1412.6980",
            "title": "Adam: A method for stochastic gradient descent optimization",
            "authors": ["Kingma, Diederik P", "Ba, Jimmy"],
            "year": 2014,
            "venue": "ICLR",
            "venue_type": "conference",
            "abstract": "We introduce Adam, an algorithm for stochastic gradient descent.",
        },
        {
            "id": "doi:10.1007/s10107-012-0629-5",
            "title": "Gradient methods for minimizing composite functions",
            "authors": ["Nesterov, Yurii"],
            "year": 2013,
            "doi": "10.1007/s10107-012-0629-5",
            "venue": "Mathematical Programming",
            "venue_type": "journal",
            "abstract": "Methods for convex composite optimization with stochastic noise.",
        },
    ]
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(papers), encoding="utf-8")
    return path


def _config(tmp_path: Path, **overrides) -> DeepSearchConfig:
    """Build a deep-search config rooted in *tmp_path*."""
    base = dict(
        enabled=True,
        keywords=["reproducible", "convex", "stochastic"],
        max_results_per_keyword=10,
        sources=["local"],
        fetch_abstracts=False,
        fetch_fulltext=False,
        llm_per_paper=True,
        output_dir=str(tmp_path / "deep_out"),
        abstract_cache_dir=str(tmp_path / "cache_abs"),
        fulltext_cache_dir=str(tmp_path / "cache_pdf"),
        search_cache_dir=str(tmp_path / "cache_search"),
        write_unified_bibtex=True,
        unified_bibtex_path=str(tmp_path / "references_deep.bib"),
    )
    base.update(overrides)
    return DeepSearchConfig(**base)


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


class TestDataclassToDict:
    """``KeywordResult.to_dict`` and ``DeepSearchArtifacts.to_dict`` are
    serialisable views the run summary / aggregate JSON consume. Verify
    both round-trip every field (the no-mocks rule means we construct
    real records and inspect the dict)."""

    def test_keyword_result_to_dict_round_trips(self):
        from infrastructure.search.literature import SearchResult, SearchQuery

        result = SearchResult(
            query=SearchQuery(text="kw", max_results=5),
            papers=[Paper(id="x:1", title="t1", year=2024)],
            per_source_counts={"local": 1},
            errors={"crossref": "503"},
        )
        kr = KeywordResult(
            keyword="kw",
            slug="kw",
            search_result=result,
            citation_keys={"x:1": "anon2024t"},
            per_paper_summaries={"x:1": "summary text"},
        )
        d = kr.to_dict()
        assert d["keyword"] == "kw"
        assert d["slug"] == "kw"
        assert d["per_source_counts"] == {"local": 1}
        assert d["errors"] == {"crossref": "503"}
        assert d["citation_keys"] == {"x:1": "anon2024t"}
        assert d["per_paper_summaries"] == {"x:1": "summary text"}
        assert d["output_dir"] is None
        # papers are serialised via Paper.to_dict()
        assert len(d["papers"]) == 1
        assert d["papers"][0]["id"] == "x:1"

    def test_artifacts_to_dict_round_trips(self):
        a = DeepSearchArtifacts()
        d = a.to_dict()
        # Empty aggregate: counts are all 0 and paths are None.
        assert d["total_keywords"] == 0
        assert d["total_papers"] == 0
        assert d["unique_papers"] == 0
        assert d["bibtex_path"] is None
        assert d["aggregate_json_path"] is None
        assert d["aggregate_report_path"] is None
        assert d["output_dir"] is None
        assert d["keyword_results"] == []


class TestPureHelpers:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Convex Optimization", "convex_optimization"),
            ("foo  BAR  ", "foo_bar"),
            ("hello-world!?", "hello_world"),
            ("", "keyword"),
            ("___", "keyword"),
        ],
    )
    def test_slugify(self, text: str, expected: str):
        assert slugify(text) == expected

    @pytest.mark.parametrize(
        "pid,expected",
        [
            ("arxiv:1234.5678", "arxiv_1234.5678"),
            ("doi:10.1/foo", "doi_10.1_foo"),
            ("simple", "simple"),
        ],
    )
    def test_safe_id(self, pid: str, expected: str):
        assert safe_id(pid) == expected


class TestBuildPaperBlock:
    def test_full_paper(self):
        paper = Paper(
            id="doi:10.1/x",
            title="Hello",
            authors=["A", "B"],
            year=2024,
            doi="10.1/x",
            url="https://example.org",
            venue="Nature",
            venue_type="journal",
            volume="42",
            issue="3",
            pages="100-110",
            publisher="Springer",
            keywords=["a", "b"],
            score=0.91,
            source="local",
            abstract="An abstract.",
        )
        block = build_rich_paper_block(paper)
        assert "Hello" in block
        assert "A, B" in block
        assert "2024" in block
        assert "Nature (journal)" in block
        assert "10.1/x" in block
        assert "vol 42" in block
        assert "Abstract" in block
        assert "An abstract." in block

    def test_truncates_fulltext(self):
        paper = Paper(id="x", title="t", fulltext="X" * 20000)
        block = build_rich_paper_block(paper, max_fulltext=500)
        assert "Excerpt" in block
        assert "(truncated)" in block

    def test_minimal_paper(self):
        paper = Paper(id="x", title="Untitled")
        block = build_rich_paper_block(paper)
        assert "Untitled" in block
        # No exception on missing fields.

    def test_no_excerpt_when_no_fulltext(self):
        paper = Paper(id="x", title="t", abstract="A")
        block = build_rich_paper_block(paper)
        assert "Excerpt" not in block


# ---------------------------------------------------------------------------
# run_deep_search
# ---------------------------------------------------------------------------


class TestRunDeepSearch:
    def test_disabled_raises(self, tmp_path: Path):
        config = _config(tmp_path, enabled=False)
        with pytest.raises(ValueError, match="enabled is False"):
            run_deep_search(config, project_root=tmp_path)

    def test_no_keywords_raises(self, tmp_path: Path):
        config = _config(tmp_path, keywords=[])
        with pytest.raises(ValueError, match="keywords is empty"):
            run_deep_search(config, project_root=tmp_path)

    def test_local_corpus_required(self, tmp_path: Path):
        config = _config(tmp_path)
        with pytest.raises(ValueError, match="no corpus_path"):
            run_deep_search(config, project_root=tmp_path)

    def test_unknown_source_rejected(self, tmp_path: Path):
        config = _config(tmp_path, sources=["fictional_db"])
        with pytest.raises(ValueError, match="Unknown deep-search source"):
            run_deep_search(config, project_root=tmp_path)

    def test_paperclip_requires_env(self, tmp_path: Path, monkeypatch):
        """Same contract as the standard pipeline: missing
        ``PAPERCLIP_API_KEY`` is a fail-fast environmental error."""
        from src.deep_search import _build_backends

        monkeypatch.delenv("PAPERCLIP_API_KEY", raising=False)
        config = _config(tmp_path, sources=["paperclip"])
        with pytest.raises(RuntimeError, match="PAPERCLIP_API_KEY"):
            _build_backends(config)

    def test_arxiv_and_crossref_backends_constructable(self, tmp_path: Path):
        """Both backends are real classes — construct them and confirm
        the deep-search ``_build_backends`` returns the expected names
        in source-list order. (We do not actually call ``.search()`` so
        no network round-trip happens here.)"""
        from src.deep_search import _build_backends

        config = _config(tmp_path, sources=["arxiv", "crossref"])
        backends = _build_backends(config)
        assert [b.name for b in backends] == ["arxiv", "crossref"]

    def test_paperclip_backend_constructed_when_env_set(self, tmp_path: Path, monkeypatch):
        from src.deep_search import _build_backends

        monkeypatch.setenv("PAPERCLIP_API_KEY", "gxl_test_dummy")
        config = _config(tmp_path, sources=["paperclip"])
        backends = _build_backends(config)
        assert len(backends) == 1
        assert backends[0].name == "paperclip"

    def test_basic_run(self, tmp_path: Path):
        corpus = _make_corpus(tmp_path)
        config = _config(tmp_path)
        artifacts = run_deep_search(
            config,
            project_root=tmp_path,
            corpus_path=corpus,
            llm=_deterministic_llm,
        )
        assert artifacts.total_keywords == 3
        assert artifacts.total_papers >= 3
        assert artifacts.unique_papers >= 3
        assert artifacts.bibtex_path is not None
        assert artifacts.bibtex_path.exists()
        assert artifacts.aggregate_json_path is not None
        assert artifacts.aggregate_report_path is not None

    def test_outputs_per_keyword(self, tmp_path: Path):
        corpus = _make_corpus(tmp_path)
        config = _config(tmp_path)
        artifacts = run_deep_search(
            config,
            project_root=tmp_path,
            corpus_path=corpus,
            llm=_deterministic_llm,
        )
        for kr in artifacts.keyword_results:
            assert kr.output_dir is not None
            assert (kr.output_dir / "papers.json").exists()
            assert (kr.output_dir / "reading_report.md").exists()

    def test_per_paper_notes_written(self, tmp_path: Path):
        corpus = _make_corpus(tmp_path)
        config = _config(tmp_path)
        artifacts = run_deep_search(
            config,
            project_root=tmp_path,
            corpus_path=corpus,
            llm=_deterministic_llm,
        )
        for kr in artifacts.keyword_results:
            assert kr.output_dir is not None
            per_paper_dir = kr.output_dir / "per_paper"
            for paper in kr.search_result.papers:
                note = per_paper_dir / (safe_id(paper.id) + ".md")
                assert note.exists()
                text = note.read_text(encoding="utf-8")
                assert paper.title in text

    def test_llm_disabled_skips_summaries(self, tmp_path: Path):
        corpus = _make_corpus(tmp_path)
        config = _config(tmp_path, llm_per_paper=False)
        artifacts = run_deep_search(
            config,
            project_root=tmp_path,
            corpus_path=corpus,
            llm=_deterministic_llm,
        )
        for kr in artifacts.keyword_results:
            assert kr.per_paper_summaries == {}

    def test_llm_none_skips_summaries(self, tmp_path: Path):
        corpus = _make_corpus(tmp_path)
        config = _config(tmp_path)
        artifacts = run_deep_search(
            config,
            project_root=tmp_path,
            corpus_path=corpus,
            llm=None,
        )
        for kr in artifacts.keyword_results:
            assert kr.per_paper_summaries == {}

    def test_unified_bibtex_round_trips(self, tmp_path: Path):
        corpus = _make_corpus(tmp_path)
        config = _config(tmp_path)
        artifacts = run_deep_search(
            config,
            project_root=tmp_path,
            corpus_path=corpus,
            llm=_deterministic_llm,
        )
        assert artifacts.bibtex_path is not None
        db = parse_bibfile(artifacts.bibtex_path)
        # Must contain at least one of the expected keys.
        keys = set(db.keys())
        assert any("peng2011reproducible" in k or "boyd2004convex" in k for k in keys)

    def test_collision_free_keys(self, tmp_path: Path):
        corpus = _make_corpus(tmp_path)
        config = _config(tmp_path)
        artifacts = run_deep_search(
            config,
            project_root=tmp_path,
            corpus_path=corpus,
            llm=_deterministic_llm,
        )
        keys = list(artifacts.aggregate_citation_keys.values())
        assert len(set(keys)) == len(keys)  # no duplicates

    def test_aggregate_report_mentions_keywords(self, tmp_path: Path):
        corpus = _make_corpus(tmp_path)
        config = _config(tmp_path)
        artifacts = run_deep_search(
            config,
            project_root=tmp_path,
            corpus_path=corpus,
            llm=_deterministic_llm,
        )
        text = artifacts.aggregate_report_path.read_text(encoding="utf-8")
        for kw in config.keywords:
            assert kw in text

    def test_no_write_outputs(self, tmp_path: Path):
        corpus = _make_corpus(tmp_path)
        config = _config(tmp_path)
        artifacts = run_deep_search(
            config,
            project_root=tmp_path,
            corpus_path=corpus,
            llm=_deterministic_llm,
            write_outputs=False,
        )
        assert artifacts.bibtex_path is None
        assert artifacts.aggregate_json_path is None
        for kr in artifacts.keyword_results:
            assert kr.output_dir is None

    def test_extra_backend_contributes(self, tmp_path: Path):
        corpus = _make_corpus(tmp_path)
        config = _config(tmp_path)

        class _Extra(SearchBackend):
            name = "extra"

            def search(self, query: SearchQuery) -> list[Paper]:
                return [Paper(id=f"extra:{query.text}", title=f"Extra for {query.text}", year=2024)]

        artifacts = run_deep_search(
            config,
            project_root=tmp_path,
            corpus_path=corpus,
            llm=_deterministic_llm,
            extra_backends=[_Extra()],
        )
        all_ids = {p.id for kr in artifacts.keyword_results for p in kr.search_result.papers}
        # One extra paper per keyword should appear.
        assert any(pid.startswith("extra:") for pid in all_ids)

    def test_max_results_cap_honoured(self, tmp_path: Path):
        corpus = _make_corpus(tmp_path)
        config = _config(tmp_path, max_results_per_keyword=2)
        artifacts = run_deep_search(
            config,
            project_root=tmp_path,
            corpus_path=corpus,
            llm=_deterministic_llm,
        )
        for kr in artifacts.keyword_results:
            assert len(kr.search_result.papers) <= 2

    def test_aggregate_json_keyword_order(self, tmp_path: Path):
        corpus = _make_corpus(tmp_path)
        config = _config(tmp_path)
        artifacts = run_deep_search(
            config,
            project_root=tmp_path,
            corpus_path=corpus,
            llm=_deterministic_llm,
        )
        payload = json.loads(artifacts.aggregate_json_path.read_text(encoding="utf-8"))
        assert payload["keywords"] == config.keywords


class TestPromptTemplate:
    def test_required_placeholders(self):
        for placeholder in ("{keyword}", "{citation_key}", "{paper_block}"):
            assert placeholder in DEEP_PROMPT

    def test_template_formats(self):
        out = DEEP_PROMPT.format(keyword="convex", citation_key="x2024y", paper_block="content")
        assert "convex" in out
        assert "x2024y" in out
        assert "content" in out


class TestWritePerPaperNote:
    def test_url_only_paper_with_fulltext(self, tmp_path: Path):
        """Cover the URL-only locator and the fulltext-excerpt branches."""
        from src.deep_search import write_per_paper_note

        paper = Paper(
            id="x:1",
            title="A Paper",
            year=2024,
            url="https://example.org/paper",
            fulltext="X" * 2000,  # > 1500 chars triggers the truncation marker
        )
        path = write_per_paper_note(tmp_path, paper, "x2024a", summary=None, keyword="kw")
        text = path.read_text(encoding="utf-8")
        assert "URL: <https://example.org/paper>" in text
        assert "Fulltext excerpt" in text
        assert "..." in text  # truncation marker

    def test_with_summary_writes_summary_block(self, tmp_path: Path):
        from src.deep_search import write_per_paper_note

        paper = Paper(id="x:1", title="A Paper", abstract="Some abstract.")
        path = write_per_paper_note(tmp_path, paper, "x", summary="MY SUMMARY TEXT", keyword="kw")
        text = path.read_text(encoding="utf-8")
        assert "MY SUMMARY TEXT" in text
        # The "no LLM" placeholder must NOT appear when summary is given.
        assert "_LLM deep summary disabled" not in text


class TestWriteKeywordReport:
    def test_errors_block_rendered(self, tmp_path: Path):
        """When SearchResult.errors is non-empty, the report includes a callout."""
        from infrastructure.search.literature import SearchResult, SearchQuery

        from src.deep_search import KeywordResult, write_keyword_report

        result = SearchResult(
            query=SearchQuery(text="kw", max_results=5),
            papers=[Paper(id="x:1", title="t1")],
            per_source_counts={"local": 1},
            errors={"crossref": "HTTP 503"},
        )
        kr = KeywordResult(
            keyword="kw",
            slug="kw",
            search_result=result,
            citation_keys={"x:1": "x2024t"},
            per_paper_summaries={"x:1": "deep summary text"},
        )
        path = write_keyword_report(tmp_path, kr)
        text = path.read_text(encoding="utf-8")
        assert "Partial coverage" in text
        assert "crossref" in text
        assert "HTTP 503" in text
        assert "Deep summaries" in text
        assert "deep summary text" in text


class TestEnrichmentBranches:
    def test_run_deep_search_with_abstracts_and_fulltext(self, tmp_path: Path):
        """Cover the AbstractFetcher and FulltextFetcher initialisation paths."""
        corpus = _make_corpus(tmp_path)
        config = _config(
            tmp_path,
            keywords=["reproducible"],
            fetch_abstracts=True,
            fetch_fulltext=True,
            max_fulltext_chars=200,
            llm_per_paper=False,
        )
        artifacts = run_deep_search(
            config,
            project_root=tmp_path,
            corpus_path=corpus,
            llm=None,
        )
        # Both fetchers ran for at least one paper.
        kr = artifacts.keyword_results[0]
        # Each paper produced at least one FetchResult per fetcher.
        statuses = [fr.status for fr in kr.enrichment_log]
        assert len(kr.enrichment_log) >= 2 * len(kr.search_result.papers)
        # No fetcher raised — every status is a known string.
        assert all(s in {"hit", "skipped", "cached", "error"} for s in statuses)


class TestDeepSearchDeterminism:
    """Two consecutive runs over the same corpus must produce a
    byte-identical ``references_deep.bib`` and a byte-identical
    ``aggregate.json``. These are the two artefacts a downstream
    manuscript build consumes.
    """

    def test_bibtex_byte_identical_across_reruns(self, tmp_path: Path):
        corpus = _make_corpus(tmp_path)
        config = _config(tmp_path, llm_per_paper=False)
        first = run_deep_search(
            config,
            project_root=tmp_path,
            corpus_path=corpus,
            llm=None,
        )
        first_bib = first.bibtex_path.read_bytes()
        first_agg = first.aggregate_json_path.read_bytes()

        second = run_deep_search(
            config,
            project_root=tmp_path,
            corpus_path=corpus,
            llm=None,
        )
        assert second.bibtex_path.read_bytes() == first_bib
        assert second.aggregate_json_path.read_bytes() == first_agg

    def test_papers_with_no_year_render_as_anonymous(self, tmp_path: Path):
        """Crossref sometimes returns papers without a year. The unified
        BibTeX writer must still produce a valid entry (no ``year=`` line
        but a parseable record) so natbib's authoryear style can fall
        back to ``[Anonymous, n.d.]`` without breaking the build."""
        corpus_path = tmp_path / "corpus.json"
        corpus_path.write_text(
            json.dumps(
                [
                    {
                        "id": "doi:10.1/no_year",
                        "title": "Untimed Paper",
                        "authors": ["Smith, A"],
                        "doi": "10.1/no_year",
                        # year omitted on purpose
                    }
                ]
            ),
            encoding="utf-8",
        )
        config = _config(
            tmp_path,
            keywords=["paper"],
            llm_per_paper=False,
            max_results_per_keyword=10,
        )
        artifacts = run_deep_search(
            config,
            project_root=tmp_path,
            corpus_path=corpus_path,
            llm=None,
        )
        # Bib parses cleanly even with the missing-year entry.
        db = parse_bibfile(artifacts.bibtex_path)
        assert len(db.entries) == 1
        # The aggregate.json carries a ``year`` field set to None for the
        # paper (so downstream composition can render ``n.d.``).
        payload = json.loads(artifacts.aggregate_json_path.read_text(encoding="utf-8"))
        assert payload["unique_papers"][0]["year"] is None


class TestStandardDeepParity:
    """The standard pipeline and the deep-search pipeline must share a
    single source of truth for citation-key disambiguation. This test
    pins that contract: collision handling for the *aggregate roster*
    (deep search) goes through the same ``_disambiguate_citation_key``
    used by ``pipeline._build_citation_keys`` (standard), so behaviour
    matches across both workflows.
    """

    def test_long_collision_run_matches_pipeline_disambiguator(self, tmp_path: Path):
        """26+ collisions force the alphabetic→double-letter cascade.
        The deep-search aggregator must produce the same keys the
        standard pipeline would for the same author/year/title-word."""
        from src.pipeline import _disambiguate_citation_key

        # 30 papers all collide on the same proto-key, forcing the
        # disambiguator past the single-letter alphabet.
        papers = [
            {
                "id": f"doi:10.1/{i}",
                "title": "Method One",
                "authors": ["Smith, A"],
                "year": 2024,
                "doi": f"10.1/{i}",
            }
            for i in range(30)
        ]
        corpus_path = tmp_path / "corpus.json"
        corpus_path.write_text(json.dumps(papers), encoding="utf-8")
        config = _config(
            tmp_path,
            keywords=["method"],
            llm_per_paper=False,
            max_results_per_keyword=50,
        )
        artifacts = run_deep_search(
            config,
            project_root=tmp_path,
            corpus_path=corpus_path,
            llm=None,
        )
        keys = sorted(artifacts.aggregate_citation_keys.values())
        # All 30 keys are unique.
        assert len(set(keys)) == 30
        # The expected key set computed by the standard disambiguator —
        # this is the parity contract.
        used: set[str] = set()
        expected: list[str] = []
        for _ in range(30):
            k = _disambiguate_citation_key("smith2024method", used)
            used.add(k)
            expected.append(k)
        assert sorted(expected) == keys


class TestAggregateCitationKeyCollision:
    def test_collision_suffix_applied_in_aggregate(self, tmp_path: Path):
        """Two papers with the same author/year/title-word collide; the
        aggregate key generator suffixes the second one with `a`."""
        corpus_path = tmp_path / "corpus.json"
        corpus_path.write_text(
            json.dumps(
                [
                    {
                        "id": "doi:10.1/one",
                        "title": "Method One",
                        "authors": ["Smith, A"],
                        "year": 2024,
                        "doi": "10.1/one",
                    },
                    {
                        "id": "doi:10.1/two",
                        "title": "Method Two",
                        "authors": ["Smith, A"],
                        "year": 2024,
                        "doi": "10.1/two",
                    },
                ]
            ),
            encoding="utf-8",
        )
        config = _config(
            tmp_path,
            keywords=["method"],
            llm_per_paper=False,
            max_results_per_keyword=10,
        )
        artifacts = run_deep_search(
            config,
            project_root=tmp_path,
            corpus_path=corpus_path,
            llm=None,
        )
        keys = sorted(artifacts.aggregate_citation_keys.values())
        # Both keys must be distinct, and the second must carry an alphabetic suffix.
        assert len(set(keys)) == 2
        assert {keys[0], keys[1]} == {"smith2024method", "smith2024methoda"}
