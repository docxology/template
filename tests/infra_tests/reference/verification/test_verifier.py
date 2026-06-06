"""Verifier classification tests (no mocks; pytest-httpserver + real SQLite)."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from pytest_httpserver import HTTPServer

from infrastructure.reference.citation.models import BibEntry
from infrastructure.reference.verification.cache import ResolutionCache
from infrastructure.reference.verification.models import VerificationStatus
from infrastructure.reference.verification.resolver import ReferenceResolver
from infrastructure.reference.verification.verifier import (
    extract_arxiv_id,
    parse_bib_year,
    verify_bibfile,
    verify_database,
    verify_entry,
)
from infrastructure.reference.citation.bibtex_parser import parse_bibtex

CROSSREF_MESSAGE = {
    "message": {
        "DOI": "10.1234/abcd",
        "title": ["A Study of Deterministic Gates"],
        "author": [{"given": "Ada", "family": "Lovelace"}],
        "issued": {"date-parts": [[2020]]},
        "type": "journal-article",
    }
}


def _entry(key: str, **fields: str) -> BibEntry:
    return BibEntry(entry_type="article", citation_key=key, fields=OrderedDict(fields))


def _online_resolver(httpserver: HTTPServer, tmp_path: Path) -> ReferenceResolver:
    return ReferenceResolver(
        cache=ResolutionCache(tmp_path / "c.db"),
        allow_network=True,
        crossref_base_url=httpserver.url_for("/crossref/works"),
        openalex_base_url=httpserver.url_for("/openalex/works"),
        arxiv_base_url=httpserver.url_for("/arxiv/query"),
    )


class TestPureHelpers:
    def test_parse_bib_year(self):
        assert parse_bib_year("2020") == 2020
        assert parse_bib_year("2020-05") == 2020
        assert parse_bib_year(None) is None
        assert parse_bib_year("forthcoming") is None

    def test_extract_arxiv_id_from_eprint(self):
        e = _entry("k", eprint="2501.12948", archiveprefix="arXiv")
        assert extract_arxiv_id(e) == "2501.12948"

    def test_extract_arxiv_id_from_arxiv_doi(self):
        e = _entry("k", doi="10.48550/arXiv.2501.12948")
        assert extract_arxiv_id(e) == "2501.12948"

    def test_extract_arxiv_id_from_url(self):
        e = _entry("k", url="https://arxiv.org/abs/2501.12948")
        assert extract_arxiv_id(e) == "2501.12948"

    def test_extract_arxiv_id_none(self):
        assert extract_arxiv_id(_entry("k", doi="10.1/x")) is None


class TestVerifyEntryOffline:
    def test_anachronism_needs_no_network(self):
        resolver = ReferenceResolver(allow_network=False)
        e = _entry("future", title="Tomorrow's Paper", year="2099", doi="10.1/x")
        verdict = verify_entry(e, resolver, as_of_year=2026)
        assert verdict.status is VerificationStatus.ANACHRONISM

    def test_unchecked_when_offline(self, tmp_path: Path):
        resolver = ReferenceResolver(cache=ResolutionCache(tmp_path / "c.db"), allow_network=False)
        e = _entry("k", title="Some Paper", year="2020", doi="10.1/x")
        verdict = verify_entry(e, resolver)
        assert verdict.status is VerificationStatus.UNCHECKED


class TestVerifyEntryOnline:
    def test_ok(self, httpserver: HTTPServer, tmp_path: Path):
        httpserver.expect_request("/crossref/works/10.1234/abcd").respond_with_json(CROSSREF_MESSAGE)
        e = _entry(
            "ok",
            title="A Study of Deterministic Gates",
            year="2020",
            author="Lovelace, Ada",
            doi="10.1234/abcd",
        )
        verdict = verify_entry(e, _online_resolver(httpserver, tmp_path), as_of_year=2026)
        assert verdict.status is VerificationStatus.OK
        assert verdict.resolved_via == "crossref"

    def test_fabricated(self, httpserver: HTTPServer, tmp_path: Path):
        httpserver.expect_request("/crossref/works/10.9/zz").respond_with_data("", status=404)
        httpserver.expect_request("/openalex/works").respond_with_json({"results": []})
        e = _entry("fab", title="Nonexistent", year="2020", doi="10.9/zz")
        verdict = verify_entry(e, _online_resolver(httpserver, tmp_path))
        assert verdict.status is VerificationStatus.FABRICATED
        assert verdict.is_blocking

    def test_mismatch_title(self, httpserver: HTTPServer, tmp_path: Path):
        httpserver.expect_request("/crossref/works/10.1234/abcd").respond_with_json(CROSSREF_MESSAGE)
        e = _entry(
            "mm",
            title="A Completely Unrelated Title About Penguins",
            year="2020",
            doi="10.1234/abcd",
        )
        verdict = verify_entry(e, _online_resolver(httpserver, tmp_path))
        assert verdict.status is VerificationStatus.MISMATCH
        assert any("title mismatch" in i for i in verdict.issues)

    def test_mismatch_year(self, httpserver: HTTPServer, tmp_path: Path):
        httpserver.expect_request("/crossref/works/10.1234/abcd").respond_with_json(CROSSREF_MESSAGE)
        e = _entry("yr", title="A Study of Deterministic Gates", year="1999", doi="10.1234/abcd")
        verdict = verify_entry(e, _online_resolver(httpserver, tmp_path))
        assert verdict.status is VerificationStatus.MISMATCH
        assert any("year mismatch" in i for i in verdict.issues)

    def test_unverifiable_no_identifier(self, httpserver: HTTPServer, tmp_path: Path):
        httpserver.expect_request("/crossref/works").respond_with_json({"message": {"items": []}})
        e = _entry("uv", title="Obscure Unindexed Title")
        verdict = verify_entry(e, _online_resolver(httpserver, tmp_path))
        assert verdict.status is VerificationStatus.UNVERIFIABLE

    def test_title_only_weak_match_is_unverifiable(self, httpserver: HTTPServer, tmp_path: Path):
        # Near-miss title clears the 0.82 floor but is a different paper, with no
        # corroborating year/author → must NOT be certified ok.
        near = {
            "message": {
                "items": [
                    {
                        "title": ["Bayesian Methods for Climate Model Design and Analysis"],
                        "type": "journal-article",
                        "DOI": "10.x/climate",
                    }
                ]
            }
        }
        httpserver.expect_request("/crossref/works").respond_with_json(near)
        e = _entry("weak", title="Bayesian Methods for Clinical Trial Design and Analysis")
        verdict = verify_entry(e, _online_resolver(httpserver, tmp_path))
        assert verdict.status is VerificationStatus.UNVERIFIABLE

    def test_title_only_exact_match_is_ok(self, httpserver: HTTPServer, tmp_path: Path):
        httpserver.expect_request("/crossref/works").respond_with_json(
            {"message": {"items": [CROSSREF_MESSAGE["message"]]}}
        )
        e = _entry("exact", title="A Study of Deterministic Gates")
        verdict = verify_entry(e, _online_resolver(httpserver, tmp_path))
        assert verdict.status is VerificationStatus.OK

    def test_uppercase_and_separator_no_false_first_author_mismatch(self, httpserver: HTTPServer, tmp_path: Path):
        httpserver.expect_request("/crossref/works/10.1234/abcd").respond_with_json(CROSSREF_MESSAGE)
        e = _entry(
            "andsep",
            title="A Study of Deterministic Gates",
            year="2020",
            author="Ada Lovelace AND Charles Babbage",
            doi="10.1234/abcd",
        )
        verdict = verify_entry(e, _online_resolver(httpserver, tmp_path), as_of_year=2026)
        assert verdict.status is VerificationStatus.OK


class TestVerifyDatabaseAndFile:
    def test_verify_database_counts(self):
        resolver = ReferenceResolver(allow_network=False)
        db = parse_bibtex(
            "@article{a, title={X}, year={2099}, doi={10.1/x}}\n@article{b, title={Y}, year={2020}, doi={10.2/y}}\n"
        )
        report = verify_database(db, resolver, as_of_year=2026)
        counts = report.counts()
        assert counts["anachronism"] == 1
        assert counts["unchecked"] == 1
        assert report.has_blocking is True
        assert "2 refs" in report.summary_line()

    def test_verify_bibfile(self, tmp_path: Path):
        bib = tmp_path / "refs.bib"
        bib.write_text("@article{a, title={X}, year={2020}, doi={10.1/x}}\n", encoding="utf-8")
        resolver = ReferenceResolver(cache=ResolutionCache(tmp_path / "c.db"), allow_network=False)
        report = verify_bibfile(bib, resolver)
        assert len(report.verdicts) == 1
        assert report.verdicts[0].status is VerificationStatus.UNCHECKED
        assert report.network_used is False
