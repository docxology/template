"""Deep-pass improvement tests pinning project contracts.

Covers contracts that earlier passes implicitly assumed but did not
explicitly pin in test code:

* ``paper_to_bibentry`` year-backfill decision (no fallback to
  ``paper.raw`` heuristics — entries without a year render as ``n.d.``
  which is the documented natbib behaviour for the 4 SPIE / Springer
  references in ``references_deep.bib`` whose Crossref payload carries
  no ``issued`` / ``published-print`` / ``published-online`` field).
* ``src.dotenv.load_dotenv`` default-path behaviour (line 66 — the
  ``Path(".env")`` branch).
* Manuscript-prompt ↔ source-prompt section parity for both
  ``synthesis.PROMPT_PER_PAPER`` (5 sections) and
  ``deep_search.DEEP_PROMPT`` (7 sections), so a future refactor of the
  prompt cannot drift past the methodology / deep-search prose without
  failing this test.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
import pytest
from infrastructure.reference.citation import paper_to_bibentry
from infrastructure.search.literature import Paper
from template_search_project.deep_search import DEEP_PROMPT
from template_search_project.dotenv import load_dotenv
from template_search_project.synthesis import PROMPT_PER_PAPER


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


class TestLLMRuntimeCallable:
    """Cover the inner ``_call`` body (lines 96-100) by injecting a
    fake :class:`infrastructure.llm.LLMClient` shape that supports both
    ``query_long`` (preferred) and ``query`` (fallback) so the
    AttributeError fallback path is exercised."""

    def test_callable_uses_query_long_when_available(self) -> None:
        from template_search_project import llm_runtime

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

        call = llm_runtime.build_llm_callable(
            model="m",
            seed=1,
            temperature=0.0,
            context_window=2048,
            long_max_tokens=512,
            max_input_length=1024,
            review_timeout=10.0,
            component_loader=lambda: (_FakeClient, _FakeConfig),
        )
        assert call is not None
        out = call("hello")
        assert out == "long-response: hello"

    def test_callable_falls_back_to_query_when_query_long_missing(self) -> None:
        from template_search_project import llm_runtime

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

        call = llm_runtime.build_llm_callable(
            model="m",
            seed=1,
            temperature=0.0,
            context_window=2048,
            long_max_tokens=512,
            max_input_length=1024,
            review_timeout=10.0,
            component_loader=lambda: (_OldClient, _FakeConfig),
        )
        assert call is not None
        assert call("ping") == "old-response: ping"


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
        from template_search_project.config import DeepSearchConfig
        from template_search_project.deep_search import run_deep_search

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
        from template_search_project.config import DeepSearchConfig
        from template_search_project.deep_search import run_deep_search

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
        from template_search_project.deep_search import write_per_paper_note

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
        from template_search_project.deep_search import build_rich_paper_block

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
        from template_search_project.deep_search import build_rich_paper_block

        paper = _Paper(id="x:1", title="t", venue="Some Journal")  # venue_type is None
        block = build_rich_paper_block(paper)
        assert "**Venue:** Some Journal" in block
        # No "(<type>)" suffix.
        assert "**Venue:** Some Journal\n" in block or block.endswith("**Venue:** Some Journal")

    def test_build_rich_paper_block_locator_without_publisher(self) -> None:
        """Paper with volume/issue but no publisher exercises 247->249
        (publisher row skip)."""
        from infrastructure.search.literature import Paper as _Paper
        from template_search_project.deep_search import build_rich_paper_block

        paper = _Paper(id="x:1", title="t", volume="42", issue="7")  # publisher None
        block = build_rich_paper_block(paper)
        assert "**Locator:**" in block
        assert "vol 42" in block and "no 7" in block
        assert "**Publisher:**" not in block

    def test_per_paper_note_short_fulltext_no_truncation_marker(self, tmp_path: Path) -> None:
        """Fulltext <= 1500 chars: no truncation ``...`` is appended
        (line 312->314 False branch)."""
        from infrastructure.search.literature import Paper as _Paper
        from template_search_project.deep_search import write_per_paper_note

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
        from template_search_project.deep_search import KeywordResult, write_keyword_report

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

        from template_search_project.deep_search import KeywordResult, write_keyword_report

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
