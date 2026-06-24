"""HTTPServer integration tests for literature.search_runner."""

from __future__ import annotations

import argparse
from pathlib import Path

from pytest_httpserver import HTTPServer

from literature.corpus import Corpus
from literature.search_runner import run_literature_search

ARXIV_ENTRY = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Active Inference Overview</title>
    <summary>Active inference and the free energy principle unify perception and action.</summary>
    <published>2020-01-01T00:00:00Z</published>
  </entry>
</feed>
"""

S2_RESPONSE = {
    "total": 1,
    "data": [
        {
            "paperId": "s2_test_1",
            "title": "Deep Active Inference",
            "abstract": "We study active inference agents using free energy minimization.",
            "year": 2021,
            "authors": [{"name": "Test Author"}],
            "citationCount": 10,
        }
    ],
}

OPENALEX_RESPONSE = {
    "meta": {"count": 1},
    "results": [
        {
            "id": "https://openalex.org/W999",
            "display_name": "OpenAlex Active Inference Paper",
            "publication_year": 2019,
            "abstract_inverted_index": {
                "Active": [0],
                "inference": [1],
                "and": [2],
                "free": [3],
                "energy": [4],
            },
        }
    ],
}


def _base_args(output_dir: Path) -> argparse.Namespace:
    return argparse.Namespace(
        query="active inference",
        max_results=5,
        output_dir=str(output_dir),
        skip_arxiv=False,
        skip_s2=False,
        skip_openalex=False,
        resume=False,
        clear_corpus=False,
        start_year=None,
        config=None,
    )


def test_run_literature_search_arxiv_httpserver(
    httpserver: HTTPServer,
    tmp_path: Path,
) -> None:
    httpserver.expect_request("/api/query").respond_with_data(
        ARXIV_ENTRY,
        content_type="application/atom+xml",
    )
    output_dir = tmp_path / "output"
    args = _base_args(output_dir)
    args.skip_s2 = True
    args.skip_openalex = True

    path = run_literature_search(
        args,
        project_root=tmp_path,
        arxiv_base_url=httpserver.url_for("/api/query"),
    )
    corpus = Corpus.load(path)
    assert len(corpus) >= 1


def test_run_literature_search_all_sources_httpserver(
    httpserver: HTTPServer,
    tmp_path: Path,
) -> None:
    httpserver.expect_request("/api/query").respond_with_data(
        ARXIV_ENTRY,
        content_type="application/atom+xml",
    )
    httpserver.expect_request("/paper/search").respond_with_json(S2_RESPONSE)
    httpserver.expect_request("/works").respond_with_json(OPENALEX_RESPONSE)

    output_dir = tmp_path / "output"
    args = _base_args(output_dir)
    base = httpserver.url_for("")
    path = run_literature_search(
        args,
        project_root=tmp_path,
        arxiv_base_url=f"{base}/api/query",
        semantic_scholar_base_url=base,
        openalex_base_url=base,
    )
    corpus = Corpus.load(path)
    assert len(corpus) >= 1


_CROSSREF_RESPONSE = {
    "message": {
        "items": [
            {
                "DOI": "10.1/shared",
                "title": ["Modafinil and wakefulness: a Crossref record"],
                "author": [{"given": "A.", "family": "Author"}],
                "issued": {"date-parts": [[2018]]},
                "container-title": ["Sleep"],
                "is-referenced-by-count": 12,
            },
            {
                "DOI": "10.1/crossref-only",
                "title": ["A Crossref-only modafinil record"],
                "issued": {"date-parts": [[2019]]},
            },
        ]
    }
}

_PUBMED_ESEARCH = {"esearchresult": {"idlist": ["111"]}}
_PUBMED_EFETCH = """\
<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <Article>
        <ArticleTitle>Modafinil and wakefulness: a PubMed record</ArticleTitle>
        <Abstract><AbstractText>Modafinil promotes wakefulness.</AbstractText></Abstract>
        <Journal><Title>Sleep</Title></Journal>
      </Article>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList><ArticleId IdType="doi">10.1/shared</ArticleId></ArticleIdList>
    </PubmedData>
  </PubmedArticle>
</PubmedArticleSet>
"""


def test_run_literature_search_crossref_pubmed_dispatch_and_dedup(
    httpserver: HTTPServer,
    tmp_path: Path,
) -> None:
    """Crossref + PubMed dispatch and a DOI shared across engines collapses to one record."""
    httpserver.expect_request("/works").respond_with_json(_CROSSREF_RESPONSE)
    httpserver.expect_request("/esearch").respond_with_json(_PUBMED_ESEARCH)
    httpserver.expect_request("/efetch").respond_with_data(_PUBMED_EFETCH, content_type="application/xml")

    output_dir = tmp_path / "output"
    args = _base_args(output_dir)
    args.query = "modafinil"
    args.skip_arxiv = True
    args.skip_s2 = True
    args.skip_openalex = True

    path = run_literature_search(
        args,
        project_root=tmp_path,
        crossref_base_url=httpserver.url_for(""),
        pubmed_esearch_url=httpserver.url_for("/esearch"),
        pubmed_efetch_url=httpserver.url_for("/efetch"),
    )
    corpus = Corpus.load(path)
    dois = sorted(p.doi for p in corpus.papers)
    # 3 fetched records, but DOI 10.1/shared appears from BOTH engines -> deduped.
    assert dois == ["10.1/crossref-only", "10.1/shared"]


def test_run_literature_search_clear_corpus_and_start_year(
    httpserver: HTTPServer,
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True)
    stale_path = data_dir / "corpus.jsonl"
    stale_path.write_text('{"title":"Old"}\n', encoding="utf-8")

    httpserver.expect_request("/api/query").respond_with_data(
        ARXIV_ENTRY,
        content_type="application/atom+xml",
    )

    args = _base_args(output_dir)
    args.clear_corpus = True
    args.start_year = 2020
    args.skip_s2 = True
    args.skip_openalex = True

    path = run_literature_search(
        args,
        project_root=tmp_path,
        arxiv_base_url=httpserver.url_for("/api/query"),
    )
    corpus = Corpus.load(path)
    assert all(paper.year is None or paper.year >= 2020 for paper in corpus.papers)
    assert path == stale_path
