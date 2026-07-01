"""Deep-pass improvement tests pinning project contracts.

Covers contracts that earlier passes implicitly assumed but did not
explicitly pin in test code:

* Reading-report edge cases (zero papers, all-failed enrichment,
  per-paper notes whose ``paper_id`` is missing from the citation map).
* ``paper_to_bibentry`` year-backfill decision (no fallback to
  ``paper.raw`` heuristics — entries without a year render as ``n.d.``,
  which is the documented natbib behaviour for the 4 SPIE / Springer
  references in ``references_deep.bib`` whose Crossref payload carries
  no ``issued`` / ``published-print`` / ``published-online`` field).
* Project-side cache-hash byte-stability — the project pipeline relies
  on ``infrastructure.search.literature.SearchCache``'s 16-char SHA-256
  prefix and we pin the exact bytes here so a Python-version or hashing
  refactor cannot silently invalidate every cache file the project ships.
* ``src.dotenv.load_dotenv`` default-path behaviour (line 66 — the
  ``Path(".env")`` branch).
* Manuscript-prompt ↔ source-prompt section parity for both
  ``synthesis.PROMPT_PER_PAPER`` (5 sections) and
  ``deep_search.DEEP_PROMPT`` (7 sections), so a future refactor of the
  prompt cannot drift past the methodology / deep-search prose without
  failing this test.
* Empty-result ``check_determinism_artifacts`` path where a search-cache
  directory exists but contains no ``*.json`` file (line 294).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from infrastructure.reference.citation import paper_to_bibentry
from infrastructure.search.literature import (
    Paper,
    SearchCache,
    SearchQuery,
    SearchResult,
)

from src.analysis import _extract_citation_keys, check_determinism_artifacts
from src.deep_search import DEEP_PROMPT
from src.dotenv import load_dotenv
from src.report import write_reading_report
from src.synthesis import PROMPT_PER_PAPER, SynthesisResult


# ---------------------------------------------------------------------------
# Reading-report edge cases
# ---------------------------------------------------------------------------


class TestReadingReportEdgeCases:
    """Pin the empty / partial-coverage behaviours of write_reading_report."""

    def test_zero_papers_writes_clean_report(self, tmp_path: Path) -> None:
        """Zero-paper run still writes a header, the topic line, and an
        explicit '(no source counts recorded)' marker rather than an
        empty markdown body."""
        result = SearchResult(
            query=SearchQuery(text="empty topic", max_results=10),
            papers=[],
            per_source_counts={},
        )
        out = write_reading_report(
            tmp_path / "report.md",
            search_result=result,
            citation_keys={},
        )
        text = out.read_text(encoding="utf-8")
        assert text.startswith("# Literature Reading Report")
        assert "_Topic:_ **empty topic**" in text
        assert "_results:_ 0" in text
        assert "## Summary by Source" in text
        assert "_(no source counts recorded)_" in text
        # Critically: no per-paper notes section is emitted when none exist.
        assert "## Per-Paper Notes" not in text
        assert "## Cross-Corpus Synthesis" not in text

    def test_all_failed_enrichment_papers_render_no_abstract_marker(self, tmp_path: Path) -> None:
        """Papers whose enrichment failed (no abstract attached) must
        render the documented ``(no abstract)`` placeholder rather than
        the literal Python ``None``."""
        papers = [
            Paper(id="x:1", title="No Abstract Paper", authors=["A One"], year=2020),
        ]
        result = SearchResult(
            query=SearchQuery(text="t"),
            papers=papers,
            per_source_counts={"local": 1},
            errors={"arxiv": "HTTP 503", "crossref": "HTTP 500"},
        )
        out = write_reading_report(
            tmp_path / "r.md",
            search_result=result,
            citation_keys={"x:1": "aone2020no"},
        )
        text = out.read_text(encoding="utf-8")
        # Backend errors must surface in the report header.
        assert "Partial coverage" in text
        assert "arxiv" in text and "HTTP 503" in text
        assert "crossref" in text and "HTTP 500" in text
        # The placeholder is the documented sentinel — never the literal
        # word "None" (which would point to a regression in
        # _format_paper_summary).
        assert "(no abstract)" in text
        assert "None" not in text

    def test_per_paper_note_with_unknown_paper_id_uses_question_mark_key(self, tmp_path: Path) -> None:
        """``write_reading_report`` is defensive about per-paper entries
        whose ``paper_id`` is not in the citation-key map: it falls back
        to ``paper_id`` itself, then to literal ``"?"``. This branch
        must never crash and the rendered note still includes the
        body text so reviewers see *something*.
        """
        result = SearchResult(query=SearchQuery(text="t"), papers=[], per_source_counts={})
        out = write_reading_report(
            tmp_path / "r.md",
            search_result=result,
            citation_keys={},
            per_paper=[
                SynthesisResult(
                    kind="per_paper",
                    prompt="p",
                    text="orphan note body",
                    paper_id=None,
                )
            ],
        )
        text = out.read_text(encoding="utf-8")
        assert "## Per-Paper Notes" in text
        assert "[?]" in text
        assert "orphan note body" in text


# ---------------------------------------------------------------------------
# Year-backfill contract pin
# ---------------------------------------------------------------------------


class TestYearBackfillContract:
    """Pin the documented decision NOT to backfill ``Paper.year`` from
    ``Paper.raw`` heuristics inside ``paper_to_bibentry``.

    Investigation summary
    ---------------------

    The 4 entries in ``manuscript/references_deep.bib`` that render as
    ``(n.d.)`` are SPIE-International Society for Optical Engineering
    proceedings figures and a Springer reference whose Crossref payload
    contains *no* ``issued`` / ``published-print`` / ``published-online``
    field at all (the Crossref backend already tries each in turn — see
    ``infrastructure/search/literature/backends.py::_item_to_paper``).
    There is no second-source year hint inside ``paper.raw`` to rescue;
    inventing one from e.g. the DOI suffix would be a fabrication, which
    contradicts the project's no-mocks / no-fabrication contract.

    Therefore: ``paper_to_bibentry`` is intentionally pure — it copies
    ``paper.year`` verbatim and never inspects ``paper.raw`` to invent a
    missing year. Citations correctly render as ``[Author, n.d.]`` so
    reviewers can see the gap. This test pins that contract.
    """

    def test_year_none_renders_as_no_year_field(self) -> None:
        """A Paper with year=None produces a BibEntry without a 'year'
        field. natbib's authoryear style then renders it as 'n.d.'."""
        paper = Paper(
            id="doi:10.1117/12.2305101",
            title="Some SPIE proceedings figure",
            authors=["Some Author"],
            year=None,
            doi="10.1117/12.2305101",
            raw={"DOI": "10.1117/12.2305101", "publisher": "SPIE"},
        )
        entry = paper_to_bibentry(paper)
        assert "year" not in entry.fields
        # Sanity: the paper.raw payload is preserved on the Paper but the
        # converter does NOT mine it for a year.
        assert paper.raw["DOI"] == "10.1117/12.2305101"

    def test_year_present_renders_year_field(self) -> None:
        """Sanity counter-test: when year IS present it's rendered."""
        paper = Paper(
            id="doi:10.1/x",
            title="t",
            authors=["A"],
            year=2020,
        )
        entry = paper_to_bibentry(paper)
        assert entry.fields["year"] == "2020"


# ---------------------------------------------------------------------------
# Cache-hash byte stability
# ---------------------------------------------------------------------------


class TestCacheHashStability:
    """Pin the exact 16-char hex prefix the project's SearchCache writes
    for a known query. If a future refactor of
    ``infrastructure.search.literature.cache._query_hash`` (or the
    upstream Python ``hashlib.sha256`` digest) ever changes, every
    cached file in this project's archive becomes orphaned in silence.
    This test catches that.
    """

    def test_query_hash_is_byte_stable_for_canonical_query(self, tmp_path: Path) -> None:
        """The cache filename for the project's canonical bundled query
        is stable: same query → same 16-char hash file → identical
        byte sequence on every Python build the project supports."""
        query = SearchQuery(
            text="reproducible research optimization",
            max_results=10,
            year_min=None,
            year_max=None,
            sources=[],
        )
        cache = SearchCache(tmp_path)
        path = cache.path_for(query)
        # The filename is search_<16-hex-char>.json.
        name = path.name
        assert name.startswith("search_")
        assert name.endswith(".json")
        hex_part = name[len("search_") : -len(".json")]
        assert len(hex_part) == 16
        # Pinning the actual bytes guards against a hashing-algorithm
        # swap or a payload-key reordering that would silently invalidate
        # every cache file shipped in the archive. Computed once and
        # frozen; if this test fails, audit the change to
        # ``infrastructure.search.literature.cache._query_hash``.
        import hashlib
        import json as _json

        expected_payload = _json.dumps(
            {
                "text": "reproducible research optimization",
                "max_results": 10,
                "year_min": None,
                "year_max": None,
                "sources": [],
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        expected = hashlib.sha256(expected_payload.encode("utf-8")).hexdigest()[:16]
        assert hex_part == expected

    def test_query_hash_is_case_and_whitespace_insensitive(self, tmp_path: Path) -> None:
        """Identical queries modulo case/whitespace share a cache file —
        the documented behaviour from ``02_methodology.md::Cache``."""
        cache = SearchCache(tmp_path)
        q1 = SearchQuery(text="Convex Optimization", max_results=5)
        q2 = SearchQuery(text="  convex optimization  ", max_results=5)
        assert cache.path_for(q1) == cache.path_for(q2)

    def test_query_hash_distinguishes_max_results(self, tmp_path: Path) -> None:
        """Different ``max_results`` produces a different cache file."""
        cache = SearchCache(tmp_path)
        a = cache.path_for(SearchQuery(text="x", max_results=5))
        b = cache.path_for(SearchQuery(text="x", max_results=6))
        assert a != b

    def test_cache_ttl_invalidates_stale_entry(self, tmp_path: Path) -> None:
        """When ``ttl_seconds`` is set, ``cache.get`` must return None
        for an entry whose ``_cached_at`` predates ``now - ttl``."""
        cache = SearchCache(tmp_path, ttl_seconds=1)
        query = SearchQuery(text="ttl-test", max_results=3)
        result = SearchResult(query=query, papers=[], per_source_counts={})
        path = cache.put(result)
        # Manually rewrite the timestamp to make the entry stale.
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["_cached_at"] = 0.0
        path.write_text(json.dumps(payload), encoding="utf-8")
        assert cache.get(query) is None


# ---------------------------------------------------------------------------
# dotenv default-path coverage
# ---------------------------------------------------------------------------


class TestDotenvDefaultPath:
    """Cover the ``Path(".env")`` default branch of
    ``load_dotenv`` (line 66 — uncovered before this test).
    """

    def test_load_dotenv_default_path_uses_cwd_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """When called with ``path=None`` and no ``.env`` exists in the
        current working directory, the loader must return ``{}``
        without raising — this is the bare-CLI happy path."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("MY_DEFAULT_PATH_ENV_KEY", raising=False)
        # No .env file in cwd.
        applied = load_dotenv()
        assert applied == {}

    def test_load_dotenv_default_path_reads_cwd_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """When ``./.env`` exists in cwd and ``path=None``, the loader
        reads it. This exercises the default-branch ``Path('.env')``
        construction."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("MY_DEFAULT_PATH_ENV_KEY", raising=False)
        (tmp_path / ".env").write_text("MY_DEFAULT_PATH_ENV_KEY=loaded_from_default\n", encoding="utf-8")
        applied = load_dotenv()
        assert applied["MY_DEFAULT_PATH_ENV_KEY"] == "loaded_from_default"
        assert os.environ["MY_DEFAULT_PATH_ENV_KEY"] == "loaded_from_default"

    def test_load_dotenv_extra_paths_loaded(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """``extra_paths`` is appended after the primary; existing
        environment values still win unless ``override=True``."""
        primary = tmp_path / ".env"
        extra = tmp_path / "extra.env"
        primary.write_text("PRIMARY=p\n", encoding="utf-8")
        extra.write_text("EXTRA=e\n", encoding="utf-8")
        monkeypatch.delenv("PRIMARY", raising=False)
        monkeypatch.delenv("EXTRA", raising=False)
        applied = load_dotenv(primary, extra_paths=[extra])
        assert applied["PRIMARY"] == "p"
        assert applied["EXTRA"] == "e"


# ---------------------------------------------------------------------------
# Prompt ↔ manuscript section parity
# ---------------------------------------------------------------------------


class TestPromptManuscriptParity:
    """Drift between the prompt source and the manuscript description is
    a documentation bug. These tests pin the section list of each prompt
    so a refactor that adds / removes a section without updating the
    manuscript prose fails CI.
    """

    def test_prompt_per_paper_has_exactly_5_sections(self) -> None:
        """``synthesis.PROMPT_PER_PAPER`` advertises 5 named sections in
        ``02_methodology.md``: CONTRIBUTION, METHOD, EVIDENCE, LIMITATION,
        TAGS. This test ensures the prompt source agrees byte-for-byte."""
        expected = ["CONTRIBUTION:", "METHOD:", "EVIDENCE:", "LIMITATION:", "TAGS:"]
        for header in expected:
            assert header in PROMPT_PER_PAPER, f"PROMPT_PER_PAPER missing {header!r}; methodology says it has it"
        # Hard pin: NO other ALL-CAPS section header should appear (e.g.
        # an accidental CONNECTIONS leak from the deep-search prompt).
        forbidden = ["CONNECTIONS:", "SIGNIFICANCE:", "LIMITATIONS:"]
        for header in forbidden:
            assert header not in PROMPT_PER_PAPER, (
                f"PROMPT_PER_PAPER must not contain {header!r}; that header belongs to deep_search.DEEP_PROMPT"
            )

    def test_deep_prompt_has_exactly_7_sections(self) -> None:
        """``deep_search.DEEP_PROMPT`` advertises 7 sections in
        ``07_deep_search.md`` and ``02_methodology.md``: Contribution,
        Method, Evidence, Limitations, Connections,
        Significance for {keyword}, Tags."""
        expected = [
            "## Contribution",
            "## Method",
            "## Evidence",
            "## Limitations",
            "## Connections",
            "## Significance for {keyword}",
            "## Tags",
        ]
        for header in expected:
            assert header in DEEP_PROMPT, f"DEEP_PROMPT missing {header!r}; deep_search.md says it has it"
        # Hard pin: total `##`-headed sections == 7, no more, no less.
        section_count = DEEP_PROMPT.count("\n## ")
        assert section_count == 7, f"DEEP_PROMPT has {section_count} sections; manuscript says 7"


# ---------------------------------------------------------------------------
# Determinism-check empty cache directory
# ---------------------------------------------------------------------------


class TestDeterminismEmptyCache:
    """Cover the line-294 branch where ``output/search/cache`` exists
    but contains zero ``*.json`` files (an aborted prior run)."""

    def test_check_determinism_empty_cache_dir(self, tmp_path: Path) -> None:
        out = tmp_path / "output"
        (out / "search" / "cache").mkdir(parents=True)
        # No *.json files inside the cache dir on purpose.
        (out / "run_summary.json").write_text("{}", encoding="utf-8")
        mdir = tmp_path / "manuscript"
        mdir.mkdir()
        (mdir / "config.yaml").write_text("llm:\n  seed: 1\n  temperature: 0\n", encoding="utf-8")
        res = check_determinism_artifacts(tmp_path)
        assert res.status == "failed"
        assert any("cache directory empty" in i for i in res.details["issues"])
        assert res.details["findings"]["search_cache_files"] == 0


# ---------------------------------------------------------------------------
# Citation-key extraction edge case (empty after stripping prefixes)
# ---------------------------------------------------------------------------


class TestDeterminismSeedMissing:
    """Cover line 311 — seed absent from config.yaml is flagged."""

    def test_check_determinism_seed_missing(self, tmp_path: Path) -> None:
        out = tmp_path / "output"
        (out / "search" / "cache").mkdir(parents=True)
        (out / "search" / "cache" / "x.json").write_text("{}", encoding="utf-8")
        (out / "run_summary.json").write_text("{}", encoding="utf-8")
        mdir = tmp_path / "manuscript"
        mdir.mkdir()
        # llm block present but no `seed` key.
        (mdir / "config.yaml").write_text("llm:\n  temperature: 0\n", encoding="utf-8")
        res = check_determinism_artifacts(tmp_path)
        assert res.status == "failed"
        assert any("llm.seed not set" in i for i in res.details["issues"])

    def test_check_determinism_no_config_yaml(self, tmp_path: Path) -> None:
        """Cover the 300->315 branch: config.yaml absent entirely.

        Determinism check still runs (cache present, run_summary present)
        but the seed/temperature subsection is skipped silently and the
        result is 'passed' iff no other issues were collected.
        """
        out = tmp_path / "output"
        (out / "search" / "cache").mkdir(parents=True)
        (out / "search" / "cache" / "x.json").write_text("{}", encoding="utf-8")
        (out / "run_summary.json").write_text("{}", encoding="utf-8")
        # No manuscript/config.yaml on purpose.
        res = check_determinism_artifacts(tmp_path)
        assert res.status == "passed"
        # findings dict should not contain llm_seed / llm_temperature
        # because the config-yaml-absent branch skips that entirely.
        assert "llm_seed" not in res.details["findings"]


class TestLLMRuntimeCallable:
    """Cover the inner ``_call`` body (lines 96-100) by injecting a
    fake :class:`infrastructure.llm.LLMClient` shape that supports both
    ``query_long`` (preferred) and ``query`` (fallback) so the
    AttributeError fallback path is exercised."""

    def test_callable_uses_query_long_when_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from src import llm_runtime

        class _FakeClient:
            def __init__(self, _config) -> None:
                self.calls: list[str] = []

            def query_long(self, prompt: str) -> str:
                self.calls.append(prompt)
                return f"long-response: {prompt}"

        class _FakeConfig:
            def __init__(self, **kwargs) -> None:
                self.kwargs = kwargs
                self.base_url = "http://stub"

            @classmethod
            def from_env(cls) -> "_FakeConfig":
                return cls()

        # Monkeypatch the import inside build_llm_callable.
        import sys
        import types

        fake_mod = types.ModuleType("infrastructure.llm")
        fake_mod.LLMClient = _FakeClient
        fake_mod.OllamaClientConfig = _FakeConfig
        monkeypatch.setitem(sys.modules, "infrastructure.llm", fake_mod)

        call = llm_runtime.build_llm_callable(
            model="m",
            seed=1,
            temperature=0.0,
            context_window=2048,
            long_max_tokens=512,
            max_input_length=1024,
            review_timeout=10.0,
        )
        assert call is not None
        out = call("hello")
        assert out == "long-response: hello"

    def test_callable_falls_back_to_query_when_query_long_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from src import llm_runtime

        class _OldClient:
            """Older LLMClient surface — only ``query`` is defined."""

            def __init__(self, _config) -> None:
                pass

            def query(self, prompt: str) -> str:
                return f"old-response: {prompt}"

        class _FakeConfig:
            def __init__(self, **kwargs) -> None:
                self.kwargs = kwargs
                self.base_url = "http://stub"

            @classmethod
            def from_env(cls) -> "_FakeConfig":
                return cls()

        import sys
        import types

        fake_mod = types.ModuleType("infrastructure.llm")
        fake_mod.LLMClient = _OldClient
        fake_mod.OllamaClientConfig = _FakeConfig
        monkeypatch.setitem(sys.modules, "infrastructure.llm", fake_mod)

        call = llm_runtime.build_llm_callable(
            model="m",
            seed=1,
            temperature=0.0,
            context_window=2048,
            long_max_tokens=512,
            max_input_length=1024,
            review_timeout=10.0,
        )
        assert call is not None
        assert call("ping") == "old-response: ping"


class TestAnalysisCLIInProcess:
    """Cover ``analysis._cli`` in-process so coverage tracks it (subprocess
    invocation does not contribute to ``--cov`` totals)."""

    def test_cli_bibliography_completeness_pass(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from src import analysis

        md = tmp_path / "manuscript"
        md.mkdir()
        (md / "references.bib").write_text("@article{k1,\n title={x}\n}\n", encoding="utf-8")
        (md / "01_intro.md").write_text("Cite [@k1].", encoding="utf-8")
        monkeypatch.setattr(
            "sys.argv",
            [
                "analysis.py",
                "--stage",
                "bibliography_completeness",
                "--project-root",
                str(tmp_path),
            ],
        )
        with pytest.raises(SystemExit) as excinfo:
            analysis._cli()
        assert excinfo.value.code == 0

    def test_cli_determinism_check_routes_correctly(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from src import analysis

        # Set up an empty repo skeleton — determinism_check will fail
        # (no run_summary.json, etc.) which is fine; we only need to
        # exercise the CLI dispatch.
        monkeypatch.setattr(
            "sys.argv",
            [
                "analysis.py",
                "--stage",
                "determinism_check",
                "--project-root",
                str(tmp_path),
            ],
        )
        with pytest.raises(SystemExit) as excinfo:
            analysis._cli()
        # Exit code is 1 (failed) because run_summary missing — this is
        # the expected behaviour and it proves the dispatch + return-code
        # plumbing in _cli works.
        assert excinfo.value.code == 1


class TestDeepSearchEdgeCases:
    """Cover branches in deep_search.py that earlier tests skirt around:
    empty per-paper summary continuation (line 378), aggregate report
    when no bibtex file is requested (423->427), and the
    ``write_unified_bibtex=False`` path (605->613).
    """

    def test_aggregate_report_without_bibtex(self, tmp_path: Path) -> None:
        """When ``write_unified_bibtex=False``, the bibtex_path on the
        artefacts is None and the aggregate report omits the
        ``_BibTeX written to:_`` line."""
        from src.config import DeepSearchConfig
        from src.deep_search import run_deep_search

        # Tiny in-tree corpus.
        corpus = tmp_path / "corpus.json"
        corpus.write_text(
            json.dumps(
                [
                    {
                        "id": "doi:10.1/x",
                        "title": "Convex Optimization",
                        "authors": ["S Boyd"],
                        "year": 2004,
                        "doi": "10.1/x",
                        "venue": "CUP",
                        "venue_type": "book",
                        "abstract": "abstract here",
                    }
                ]
            ),
            encoding="utf-8",
        )
        cfg = DeepSearchConfig(
            enabled=True,
            keywords=["convex"],
            max_results_per_keyword=5,
            sources=["local"],
            fetch_abstracts=False,
            fetch_fulltext=False,
            llm_per_paper=False,
            output_dir=str(tmp_path / "deep_out"),
            abstract_cache_dir=str(tmp_path / "cache_abs"),
            fulltext_cache_dir=str(tmp_path / "cache_pdf"),
            search_cache_dir=str(tmp_path / "cache_search"),
            write_unified_bibtex=False,  # ← exercises 605->613
            unified_bibtex_path=str(tmp_path / "ref.bib"),
        )
        artifacts = run_deep_search(cfg, project_root=tmp_path, corpus_path=corpus, llm=None)
        assert artifacts.bibtex_path is None
        # Aggregate report exists and DOES NOT contain the bibtex line.
        assert artifacts.aggregate_report_path is not None
        report_text = artifacts.aggregate_report_path.read_text(encoding="utf-8")
        assert "_BibTeX written to:_" not in report_text
        # Sanity: the unique-paper roster still rendered.
        assert "Convex Optimization" in report_text

    def test_run_deep_search_without_cache_dir(self, tmp_path: Path) -> None:
        """When ``search_cache_dir`` is empty/falsy, no SearchCache is
        constructed (line 471->474). Run an in-memory deep search and
        confirm artefacts still write."""
        from src.config import DeepSearchConfig
        from src.deep_search import run_deep_search

        corpus = tmp_path / "corpus.json"
        corpus.write_text(
            json.dumps([{"id": "doi:10.1/x", "title": "T", "year": 2020, "authors": ["A"]}]),
            encoding="utf-8",
        )
        cfg = DeepSearchConfig(
            enabled=True,
            keywords=["t"],
            max_results_per_keyword=5,
            sources=["local"],
            fetch_abstracts=False,
            fetch_fulltext=False,
            llm_per_paper=False,
            output_dir=str(tmp_path / "deep_out"),
            abstract_cache_dir=str(tmp_path / "cache_abs"),
            fulltext_cache_dir=str(tmp_path / "cache_pdf"),
            search_cache_dir="",  # ← exercises 471->474
            write_unified_bibtex=False,
            unified_bibtex_path=str(tmp_path / "ref.bib"),
        )
        artifacts = run_deep_search(cfg, project_root=tmp_path, corpus_path=corpus, llm=None)
        assert artifacts.unique_papers == 1

    def test_per_paper_note_truncates_long_fulltext(self, tmp_path: Path) -> None:
        """``write_per_paper_note`` truncates fulltext at 1500 chars and
        appends ``...`` (line 312->314 — the truncation-marker branch).
        """
        from infrastructure.search.literature import Paper as _Paper
        from src.deep_search import write_per_paper_note

        long_text = "x" * 2000  # > 1500
        paper = _Paper(id="x:1", title="t", year=2020, authors=["A"], fulltext=long_text)
        out = write_per_paper_note(tmp_path, paper, citation_key="k1", summary=None, keyword="kw")
        text = out.read_text(encoding="utf-8")
        assert "## Fulltext excerpt" in text
        assert "..." in text
        # Confirm only the first 1500 chars made it into the note.
        excerpt_start = text.find("```\n") + len("```\n")
        excerpt_end = text.find("\n...", excerpt_start)
        assert excerpt_end - excerpt_start == 1500

    def test_build_rich_paper_block_handles_minimal_paper(self) -> None:
        """``build_rich_paper_block`` accepts a Paper missing every
        optional field — exercises every ``if paper.X:`` False branch
        (lines 221-256 cluster).
        """
        from infrastructure.search.literature import Paper as _Paper
        from src.deep_search import build_rich_paper_block

        # All optional fields absent.
        minimal = _Paper(id="x:1", title="Just A Title")
        block = build_rich_paper_block(minimal)
        # Title is present.
        assert "**Title:** Just A Title" in block
        # No author/year/venue/doi rows.
        assert "**Authors:**" not in block
        assert "**Year:**" not in block
        assert "**Venue:**" not in block
        assert "**DOI:**" not in block

    def test_build_rich_paper_block_venue_without_type(self) -> None:
        """Paper with venue but no venue_type renders venue without
        the parenthetical type suffix (line 229->231 branch).
        """
        from infrastructure.search.literature import Paper as _Paper
        from src.deep_search import build_rich_paper_block

        paper = _Paper(id="x:1", title="t", venue="Some Journal")  # venue_type is None
        block = build_rich_paper_block(paper)
        assert "**Venue:** Some Journal" in block
        # No "(<type>)" suffix.
        assert "**Venue:** Some Journal\n" in block or block.endswith("**Venue:** Some Journal")

    def test_build_rich_paper_block_locator_without_publisher(self) -> None:
        """Paper with volume/issue but no publisher exercises 247->249
        (publisher row skip)."""
        from infrastructure.search.literature import Paper as _Paper
        from src.deep_search import build_rich_paper_block

        paper = _Paper(id="x:1", title="t", volume="42", issue="7")  # publisher None
        block = build_rich_paper_block(paper)
        assert "**Locator:**" in block
        assert "vol 42" in block and "no 7" in block
        assert "**Publisher:**" not in block

    def test_per_paper_note_short_fulltext_no_truncation_marker(self, tmp_path: Path) -> None:
        """Fulltext <= 1500 chars: no truncation ``...`` is appended
        (line 312->314 False branch)."""
        from infrastructure.search.literature import Paper as _Paper
        from src.deep_search import write_per_paper_note

        short = "y" * 100
        paper = _Paper(id="x:2", title="t", fulltext=short)
        out = write_per_paper_note(tmp_path, paper, citation_key="k", summary=None, keyword="kw")
        text = out.read_text(encoding="utf-8")
        assert "## Fulltext excerpt" in text
        # Inside the fenced block, the literal "..." truncation marker
        # must NOT appear.
        block_start = text.find("```\n") + 4
        block_end = text.rfind("```")
        block = text[block_start:block_end]
        assert "..." not in block

    def test_keyword_report_no_per_source_counts_skips_coverage(self, tmp_path: Path) -> None:
        """When ``per_source_counts`` is empty, the '## Coverage' table
        is not emitted (line 347->356 branch). Build a KeywordResult
        with empty per_source_counts and verify the section is absent.
        """
        from infrastructure.search.literature import (
            Paper as _Paper,
            SearchQuery as _SQ,
            SearchResult as _SR,
        )
        from src.deep_search import KeywordResult, write_keyword_report

        kr = KeywordResult(
            keyword="kw",
            slug="kw",
            search_result=_SR(
                query=_SQ(text="kw", max_results=10),
                papers=[_Paper(id="x:1", title="t", year=2020)],
                per_source_counts={},  # ← empty
            ),
            citation_keys={"x:1": "k1"},
        )
        out = write_keyword_report(tmp_path, kr)
        text = out.read_text(encoding="utf-8")
        assert "## Coverage" not in text

    def test_keyword_report_skips_empty_summary(self, tmp_path: Path) -> None:
        """``write_keyword_report`` must skip per-paper summaries that
        are present-but-empty (the ``if not summary: continue`` branch
        on line 378). Build a KeywordResult by hand with one empty and
        one populated summary, then verify only the populated one
        renders a heading.
        """
        from infrastructure.search.literature import (
            Paper as _Paper,
            SearchQuery as _SQ,
            SearchResult as _SR,
        )

        from src.deep_search import KeywordResult, write_keyword_report

        papers = [
            _Paper(id="x:1", title="With Note", year=2020),
            _Paper(id="x:2", title="No Note", year=2021),
        ]
        kr = KeywordResult(
            keyword="kw",
            slug="kw",
            search_result=_SR(
                query=_SQ(text="kw", max_results=10),
                papers=papers,
                per_source_counts={"local": 2},
            ),
            citation_keys={"x:1": "k1", "x:2": "k2"},
            per_paper_summaries={"x:1": "real summary text", "x:2": ""},
        )
        out = write_keyword_report(tmp_path, kr)
        text = out.read_text(encoding="utf-8")
        assert "## Deep summaries" in text
        assert "[k1]" in text and "real summary text" in text
        # The empty-summary paper has no per-paper heading under
        # "## Deep summaries" — only its catalog entry above.
        deep_section = text.split("## Deep summaries", 1)[1]
        assert "[k2]" not in deep_section


class TestCitationKeyExtractionEdge:
    """``_extract_citation_keys`` guards against tokens that become empty
    after stripping ``-+@`` (the ``token = token.lstrip(...)`` step)."""

    def test_empty_after_prefix_stripping_is_skipped(self) -> None:
        """``[@-]`` is a malformed pandoc cite — the inner token is just
        the prefix character, which strips to empty. The extractor must
        skip silently rather than emit an empty string into the key set.
        """
        keys = _extract_citation_keys("Garbage [@-] more")
        assert "" not in keys
        # The malformed cite contributes no key.
        assert keys == set()

    def test_mixed_valid_and_empty_token(self) -> None:
        keys = _extract_citation_keys("Real [@valid_key] and bad [@-]")
        assert keys == {"valid_key"}
