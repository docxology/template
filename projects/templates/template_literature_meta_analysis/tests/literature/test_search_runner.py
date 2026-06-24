"""Tests for literature.search_runner."""

from __future__ import annotations

import argparse
from pathlib import Path

from pytest_httpserver import HTTPServer

from literature.corpus import Corpus
from literature.models import Paper
from literature.search_runner import apply_relevance_filter, run_literature_search, search_source


def _paper(title: str, abstract: str = "active inference study") -> Paper:
    return Paper(title=title, abstract=abstract, authors=[], year=2020)


def test_apply_relevance_filter_removes_off_topic() -> None:
    corpus = Corpus()
    corpus.add(_paper("On topic", "free energy principle analysis"))
    corpus.add(_paper("Off topic", "unrelated gardening methods"))
    apply_relevance_filter(corpus, ["free energy"], __import__("logging").getLogger("test"))
    assert len(corpus) == 1


def test_apply_relevance_filter_is_case_insensitive_on_keywords() -> None:
    """An uppercase config keyword must still match (not silently exclude everything)."""
    corpus = Corpus()
    corpus.add(_paper("Modafinil and ADHD", "a study of adhd and wakefulness"))
    corpus.add(_paper("Gardening", "unrelated horticulture methods"))
    # Mixed-case keywords as a re-targeting user might write them in config.yaml.
    apply_relevance_filter(corpus, ["ADHD", "Wakefulness"], __import__("logging").getLogger("test"))
    assert len(corpus) == 1
    assert corpus.papers[0].title == "Modafinil and ADHD"


def test_apply_relevance_filter_empty_keywords_does_not_wipe_corpus() -> None:
    """An empty/blank keyword list is treated as no-filter, not a total wipe."""
    corpus = Corpus()
    corpus.add(_paper("Paper A"))
    corpus.add(_paper("Paper B"))
    apply_relevance_filter(corpus, [], __import__("logging").getLogger("test"))
    assert len(corpus) == 2
    apply_relevance_filter(corpus, ["   ", ""], __import__("logging").getLogger("test"))
    assert len(corpus) == 2


def test_search_source_adds_papers(tmp_path: Path) -> None:
    corpus = Corpus()
    logger = __import__("logging").getLogger("test")

    def fake_search(_query: str, max_results: int = 100) -> list[Paper]:
        return [_paper("Fetched")]

    result = search_source("Test", fake_search, "query", 10, corpus, logger)
    assert result is not None
    assert len(corpus) == 1


def test_run_literature_search_skips_sources(tmp_output_dir: str) -> None:
    args = argparse.Namespace(
        query="active inference",
        max_results=10,
        output_dir=tmp_output_dir,
        skip_arxiv=True,
        skip_s2=True,
        skip_openalex=True,
        resume=False,
        clear_corpus=False,
        start_year=None,
        config=None,
    )
    project_root = Path(__file__).resolve().parents[2]
    path = run_literature_search(args, project_root=project_root)
    assert path.exists()


def test_search_source_returns_none_on_failure() -> None:
    corpus = Corpus()
    logger = __import__("logging").getLogger("test")

    def failing_search(_query: str, max_results: int = 100) -> list[Paper]:
        raise RuntimeError("network unavailable")

    assert search_source("Fail", failing_search, "query", 10, corpus, logger) is None
    assert len(corpus) == 0


def test_run_literature_search_resumes_populated_corpus(
    sample_papers: list[Paper],
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True)
    corpus_path = data_dir / "corpus.jsonl"
    corpus = Corpus()
    for paper in sample_papers:
        corpus.add(paper)
    corpus.save(corpus_path)

    args = argparse.Namespace(
        query="active inference",
        max_results=10,
        output_dir=str(output_dir),
        skip_arxiv=True,
        skip_s2=True,
        skip_openalex=True,
        resume=True,
        clear_corpus=False,
        start_year=None,
        config=None,
    )
    project_root = Path(__file__).resolve().parents[2]
    path = run_literature_search(args, project_root=project_root)
    assert path == corpus_path
    reloaded = Corpus.load(corpus_path)
    assert len(reloaded) == len(sample_papers)


def test_run_literature_search_loads_yaml_config(
    sample_papers: list[Paper],
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
project_config:
  search:
    query: "custom query"
    max_results: 42
    resume: false
    arxiv_queries:
      - 'all:"active inference"'
    relevance_keywords:
      - "active inference"
""".strip(),
        encoding="utf-8",
    )
    output_dir = tmp_path / "output"
    args = argparse.Namespace(
        query="default query",
        max_results=10,
        output_dir=str(output_dir),
        skip_arxiv=True,
        skip_s2=True,
        skip_openalex=True,
        resume=True,
        clear_corpus=False,
        start_year=None,
        config=str(config_path),
    )
    project_root = tmp_path
    run_literature_search(args, project_root=project_root)
    assert args.query == "custom query"
    assert args.max_results == 42
    assert args.resume is False


def test_search_source_counts_duplicates() -> None:
    corpus = Corpus()
    logger = __import__("logging").getLogger("test")
    paper = _paper("Duplicate title", "free energy principle study")

    def duplicate_search(_query: str, max_results: int = 100) -> list[Paper]:
        return [paper, paper]

    result = search_source("Dup", duplicate_search, "query", 10, corpus, logger)
    assert result is not None
    assert len(corpus) == 1


def test_run_literature_search_resume_empty_corpus_searches(
    httpserver: HTTPServer,
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "corpus.jsonl").write_text("", encoding="utf-8")

    httpserver.expect_request("/api/query").respond_with_data(
        """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry><title>Resume fetch</title><summary>free energy active inference</summary></entry>
</feed>""",
        content_type="application/atom+xml",
    )

    args = argparse.Namespace(
        query="active inference",
        max_results=5,
        output_dir=str(output_dir),
        skip_arxiv=False,
        skip_s2=True,
        skip_openalex=True,
        resume=True,
        clear_corpus=False,
        start_year=None,
        config=None,
    )
    path = run_literature_search(
        args,
        project_root=tmp_path,
        arxiv_base_url=httpserver.url_for("/api/query"),
    )
    assert len(Corpus.load(path)) >= 1


def test_run_literature_search_uses_defaults_without_manuscript_config(
    tmp_path: Path,
) -> None:
    args = argparse.Namespace(
        query="active inference",
        max_results=10,
        output_dir=str(tmp_path / "output"),
        skip_arxiv=True,
        skip_s2=True,
        skip_openalex=True,
        resume=False,
        clear_corpus=False,
        start_year=None,
        config=None,
    )
    run_literature_search(args, project_root=tmp_path)
