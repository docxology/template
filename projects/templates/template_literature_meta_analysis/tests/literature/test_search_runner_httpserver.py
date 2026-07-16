"""HTTPServer integration tests for literature.search_runner."""

from __future__ import annotations

import argparse
import json
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
        skip_crossref=False,
        skip_pubmed=False,
        skip_sovietrxiv=False,
        skip_chinarxiv=False,
        skip_europepmc=False,
        skip_biorxiv=False,
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
    report = json.loads((output_dir / "data" / "retrieval_report.json").read_text())
    arxiv = next(row for row in report["engines"] if row["source"].startswith("arXiv"))
    assert arxiv["status"] == "ok"
    assert arxiv["fetched"] == 1
    assert report["route"]["source_order"]


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


# ---------------------------------------------------------------------------
# SovietRxiv dispatch tests
# ---------------------------------------------------------------------------

_SOVIETRXIV_RESPONSE = {
    "total": 2,
    "limit": 100,
    "next_cursor": None,
    "data": [
        {
            "id": "202312.00010",
            "title": "Modafinil and wakefulness: a SovietRxiv record",
            "authors": ["Cyril Researcher"],
            "abstract": "Modafinil promotes wakefulness in sleep-deprived populations.",
            "date": "1988-05-20",
            "source": "russiarxiv",
            "source_url": "https://mathnet.ru/abc1",
            "has_pdf": True,
            "has_full_text": True,
        },
        {
            "id": "202312.00011",
            "title": "A SovietRxiv-only modafinil record",
            "authors": ["Another Author"],
            "date": "1992-01-10",
            "source": "russiarxiv",
        },
    ],
}


def test_run_literature_search_sovietrxiv_dispatch(
    httpserver: HTTPServer,
    tmp_path: Path,
) -> None:
    """SovietRxiv engine dispatches and its papers enter the corpus."""
    httpserver.expect_request("/api/v1/papers").respond_with_json(_SOVIETRXIV_RESPONSE)

    output_dir = tmp_path / "output"
    args = _base_args(output_dir)
    args.query = "modafinil"
    args.skip_arxiv = True
    args.skip_s2 = True
    args.skip_openalex = True

    path = run_literature_search(
        args,
        project_root=tmp_path,
        sovietrxiv_base_url=httpserver.url_for(""),
    )
    corpus = Corpus.load(path)
    titles = sorted(p.title for p in corpus.papers)
    assert "Modafinil and wakefulness: a SovietRxiv record" in titles
    assert "A SovietRxiv-only modafinil record" in titles


def test_run_literature_search_sovietrxiv_skip_flag(
    httpserver: HTTPServer,
    tmp_path: Path,
) -> None:
    """--skip-sovietrxiv prevents the SovietRxiv engine from dispatching."""
    # All other keyless engines (Crossref, PubMed, Europe PMC, bioRxiv/medRxiv) would
    # also dispatch to their real production URLs when no fixture base_url is
    # provided. Skip them all so the corpus stays empty, proving SovietRxiv did not
    # fire either.
    output_dir = tmp_path / "output"
    args = _base_args(output_dir)
    args.skip_arxiv = True
    args.skip_s2 = True
    args.skip_openalex = True
    args.skip_crossref = True
    args.skip_pubmed = True
    args.skip_sovietrxiv = True
    args.skip_chinarxiv = True
    args.skip_europepmc = True
    args.skip_biorxiv = True

    path = run_literature_search(
        args,
        project_root=tmp_path,
    )
    corpus = Corpus.load(path)
    assert len(corpus) == 0


# ---------------------------------------------------------------------------
# ChinaRxiv dispatch tests (same unified API as SovietRxiv)
# ---------------------------------------------------------------------------

_CHINARXIV_RESPONSE = {
    "total": 1,
    "limit": 100,
    "next_cursor": None,
    "data": [
        {
            "id": "202401.00001",
            "title": "Modafinil effects on cognition: a ChinaRxiv record",
            "authors": ["Wei Zhang"],
            "abstract": "Modafinil improves cognitive performance under sleep restriction.",
            "date": "2021-07-15",
            "source": "chinaxiv",
            "source_url": "https://chinaxiv.org/abc1",
            "has_pdf": True,
        },
    ],
}


_EUROPEPMC_RESPONSE = {
    "resultList": {
        "result": [
            {
                "doi": "10.1/shared",
                "title": "Modafinil and wakefulness: a Europe PMC record",
                "authorList": {"author": [{"fullName": "A. Author"}]},
                "pubYear": "2018",
                "abstractText": "Modafinil promotes wakefulness (Europe PMC).",
            },
            {
                "doi": "10.1/europepmc-only",
                "title": "A Europe PMC-only modafinil record",
                "pubYear": "2020",
            },
        ]
    }
}


def test_run_literature_search_europepmc_dispatch_and_dedup_with_crossref(
    httpserver: HTTPServer,
    tmp_path: Path,
) -> None:
    """Europe PMC dispatches; a DOI shared with Crossref collapses to one record."""
    httpserver.expect_request("/works").respond_with_json(_CROSSREF_RESPONSE)
    httpserver.expect_request("/search").respond_with_json(_EUROPEPMC_RESPONSE)

    output_dir = tmp_path / "output"
    args = _base_args(output_dir)
    args.query = "modafinil"
    args.skip_arxiv = True
    args.skip_s2 = True
    args.skip_openalex = True
    args.skip_pubmed = True

    path = run_literature_search(
        args,
        project_root=tmp_path,
        crossref_base_url=httpserver.url_for(""),
        europepmc_base_url=httpserver.url_for(""),
    )
    corpus = Corpus.load(path)
    dois = sorted(p.doi for p in corpus.papers)
    # Crossref returns 2 (10.1/shared, 10.1/crossref-only); Europe PMC returns 2
    # (10.1/shared, 10.1/europepmc-only). DOI 10.1/shared appears from BOTH -> deduped.
    assert dois == ["10.1/crossref-only", "10.1/europepmc-only", "10.1/shared"]


def test_run_literature_search_chinarxiv_dispatch(
    httpserver: HTTPServer,
    tmp_path: Path,
) -> None:
    """ChinaRxiv engine dispatches via the unified API and its papers enter the corpus."""
    httpserver.expect_request("/api/v1/papers").respond_with_json(_CHINARXIV_RESPONSE)

    output_dir = tmp_path / "output"
    args = _base_args(output_dir)
    args.query = "modafinil"
    args.skip_arxiv = True
    args.skip_s2 = True
    args.skip_openalex = True

    path = run_literature_search(
        args,
        project_root=tmp_path,
        chinarxiv_base_url=httpserver.url_for(""),
    )
    corpus = Corpus.load(path)
    titles = [p.title for p in corpus.papers]
    assert "Modafinil effects on cognition: a ChinaRxiv record" in titles


def test_run_literature_search_dispatches_biorxiv_and_medrxiv_distinctly(
    httpserver: HTTPServer,
    tmp_path: Path,
) -> None:
    """Both preprint corpora are queried and retain distinct provenance."""
    interval = "2013-01-01/2099-12-31"
    httpserver.expect_request(f"/details/biorxiv/{interval}/0/json").respond_with_json(
        {
            "collection": [
                {
                    "doi": "10.1101/bio",
                    "title": "Modafinil bioRxiv study",
                    "abstract": "A modafinil preclinical study.",
                    "date": "2024-01-01",
                    "authors": "Bio Author",
                }
            ]
        }
    )
    httpserver.expect_request(f"/details/medrxiv/{interval}/0/json").respond_with_json(
        {
            "collection": [
                {
                    "doi": "10.1101/med",
                    "title": "Modafinil medRxiv trial",
                    "abstract": "A modafinil clinical trial.",
                    "date": "2024-02-01",
                    "authors": "Med Author",
                }
            ]
        }
    )

    output_dir = tmp_path / "output"
    args = _base_args(output_dir)
    args.query = "modafinil"
    args.skip_arxiv = True
    args.skip_s2 = True
    args.skip_openalex = True
    args.skip_crossref = True
    args.skip_pubmed = True
    args.skip_sovietrxiv = True
    args.skip_chinarxiv = True
    args.skip_europepmc = True
    args.skip_biorxiv = False
    args.skip_medrxiv = False

    path = run_literature_search(
        args,
        project_root=tmp_path,
        biorxiv_base_url=httpserver.url_for(""),
    )

    corpus = Corpus.load(path)
    assert {paper.full_text_source for paper in corpus.papers} == {"biorxiv", "medrxiv"}
    report = json.loads((output_dir / "data" / "retrieval_report.json").read_text())
    rows = {row["source"]: row for row in report["engines"]}
    assert rows["bioRxiv"]["status"] == "ok"
    assert rows["medRxiv"]["status"] == "ok"
    assert rows["bioRxiv"]["fetched"] == 1
    assert rows["medRxiv"]["fetched"] == 1
