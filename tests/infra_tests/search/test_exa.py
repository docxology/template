"""Exa search-interface tests using pytest-httpserver (no mocks).

Every test drives the real :class:`UrllibExaHttpClient` against a local
``pytest-httpserver``; the only override is ``base_url``. This exercises the
actual transport, header, URL-join, and JSON parse paths end to end.
"""

from __future__ import annotations

import json

import pytest
from pytest_httpserver import HTTPServer

from infrastructure.search.exa import (
    AnswerResponse,
    ContentsResponse,
    ExaClient,
    ExaConfig,
    ExaError,
    ExaResult,
    SearchResponse,
)
from infrastructure.search.exa.cli import build_parser, run
from infrastructure.search.exa.models import build_contents_payload, prune, validate_search_request


def _client(httpserver: HTTPServer) -> ExaClient:
    base = httpserver.url_for("/").rstrip("/")
    return ExaClient(ExaConfig(api_key="test-key", base_url=base))


# --------------------------------------------------------------------------- #
# /search
# --------------------------------------------------------------------------- #


def test_search_parses_real_payload(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/search", method="POST").respond_with_json(
        {
            "requestId": "req-1",
            "searchType": "auto",
            "results": [
                {
                    "id": "doc-1",
                    "url": "https://example.com/a",
                    "title": "Auth example",
                    "publishedDate": "2024-03-01",
                    "author": "Jane",
                    "highlights": ["use a route handler"],
                    "highlightScores": [0.91],
                }
            ],
            "costDollars": {"total": 0.005},
        }
    )
    resp = _client(httpserver).search("auth example", num_results=10)
    assert isinstance(resp, SearchResponse)
    assert resp.request_id == "req-1" and resp.search_type == "auto"
    assert resp.cost_dollars == pytest.approx(0.005)
    assert len(resp.results) == 1
    assert resp.results[0].id == "doc-1"
    assert resp.results[0].highlights == ["use a route handler"]
    assert resp.results[0].highlight_scores == [pytest.approx(0.91)]


def test_search_sends_camelcase_with_nested_contents_and_auth(httpserver: HTTPServer) -> None:
    captured: dict = {}

    def handler(request):  # type: ignore[no-untyped-def]
        captured["headers"] = dict(request.headers)
        captured["json"] = json.loads(request.get_data())
        from werkzeug.wrappers import Response

        return Response(json.dumps({"requestId": "r", "results": []}), content_type="application/json")

    httpserver.expect_request("/search", method="POST").respond_with_handler(handler)
    _client(httpserver).search(
        "query",
        type="fast",
        num_results=7,
        include_domains=["arxiv.org"],
        exclude_domains=["pinterest.com"],
    )
    body = captured["json"]
    # camelCase wire field names, default highlights nested under `contents`.
    assert body["type"] == "fast" and body["numResults"] == 7
    assert body["includeDomains"] == ["arxiv.org"] and body["excludeDomains"] == ["pinterest.com"]
    assert body["contents"] == {"highlights": True}
    # content keys must NOT leak to the top level (documented mistake).
    assert "highlights" not in body and "text" not in body and "summary" not in body
    assert captured["headers"]["X-Api-Key"] == "test-key"


def test_search_structured_output_and_grounding(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/search", method="POST").respond_with_json(
        {
            "requestId": "r",
            "results": [],
            "output": {
                "content": {"companies": [{"name": "Nvidia"}]},
                "grounding": [
                    {"field": "companies[0].name", "citations": [{"url": "u", "title": "t"}], "confidence": "high"}
                ],
            },
        }
    )
    resp = _client(httpserver).search("gpus", output_schema={"type": "object"}, system_prompt="prefer official")
    assert resp.output is not None
    assert resp.output.content == {"companies": [{"name": "Nvidia"}]}
    assert resp.output.grounding[0].field == "companies[0].name"
    assert resp.output.grounding[0].confidence == "high"


def test_search_rejects_empty_query() -> None:
    client = ExaClient(ExaConfig(api_key="k"))
    with pytest.raises(ExaError, match="non-empty"):
        client.search("   ")


def test_search_rejects_invalid_type() -> None:
    client = ExaClient(ExaConfig(api_key="k"))
    with pytest.raises(ExaError, match="invalid type"):
        client.search("q", type="turbo")


# --------------------------------------------------------------------------- #
# /contents, /answer, /find-similar
# --------------------------------------------------------------------------- #


def test_contents_uses_top_level_content_keys(httpserver: HTTPServer) -> None:
    captured: dict = {}

    def handler(request):  # type: ignore[no-untyped-def]
        captured["json"] = json.loads(request.get_data())
        from werkzeug.wrappers import Response

        return Response(
            json.dumps({"requestId": "c", "results": [{"id": "d", "url": "u", "text": "body"}]}),
            content_type="application/json",
        )

    httpserver.expect_request("/contents", method="POST").respond_with_handler(handler)
    resp = _client(httpserver).contents(["https://u.com"], text=True)
    assert isinstance(resp, ContentsResponse) and resp.results[0].text == "body"
    # On /contents the content keys are top-level (NOT nested under `contents`).
    assert captured["json"] == {"urls": ["https://u.com"], "text": True}


def test_contents_rejects_empty_urls() -> None:
    with pytest.raises(ExaError, match="at least one"):
        ExaClient(ExaConfig(api_key="k")).contents([" "])


def test_answer_parses_citations(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/answer", method="POST").respond_with_json(
        {
            "requestId": "a",
            "answer": "RAG combines retrieval with generation.",
            "citations": [{"id": "c", "url": "u", "title": "src"}],
        }
    )
    resp = _client(httpserver).answer("what is RAG?")
    assert isinstance(resp, AnswerResponse)
    assert resp.answer.startswith("RAG") and resp.citations[0].title == "src"


def test_find_similar_returns_search_shape(httpserver: HTTPServer) -> None:
    captured: dict = {}

    def handler(request):  # type: ignore[no-untyped-def]
        captured["json"] = json.loads(request.get_data())
        from werkzeug.wrappers import Response

        return Response(
            json.dumps({"requestId": "s", "results": [{"id": "sim", "url": "v"}]}), content_type="application/json"
        )

    httpserver.expect_request("/findSimilar", method="POST").respond_with_handler(handler)
    resp = _client(httpserver).find_similar("https://seed.com", num_results=3, exclude_source_domain=True)
    assert resp.results[0].id == "sim"
    assert captured["json"]["url"] == "https://seed.com"
    assert captured["json"]["numResults"] == 3 and captured["json"]["excludeSourceDomain"] is True


# --------------------------------------------------------------------------- #
# Errors, config, models
# --------------------------------------------------------------------------- #


def test_non_2xx_raises_with_status_and_body(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/search", method="POST").respond_with_json({"error": "bad request"}, status=400)
    with pytest.raises(ExaError) as excinfo:
        _client(httpserver).search("q")
    assert excinfo.value.status == 400 and "bad request" in (excinfo.value.body or "")


def test_non_json_body_raises(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/search", method="POST").respond_with_data(
        "<html>not json</html>", content_type="text/html"
    )
    with pytest.raises(ExaError, match="non-JSON"):
        _client(httpserver).search("q")


def test_config_from_env(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("EXA_API_KEY", "env-key")
    cfg = ExaConfig.from_env()
    assert cfg.api_key == "env-key" and cfg.base_url == "https://api.exa.ai"
    assert cfg.auth_headers()["x-api-key"] == "env-key"


def test_config_from_env_missing(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    with pytest.raises(ExaError, match="not set"):
        ExaConfig.from_env()


def test_config_strips_trailing_slash_and_validates_type() -> None:
    cfg = ExaConfig(api_key="k", base_url="https://api.exa.ai/")
    assert cfg.base_url == "https://api.exa.ai"
    with pytest.raises(ExaError, match="invalid default_type"):
        ExaConfig(api_key="k", default_type="turbo")


def test_validate_search_request_category_conflict() -> None:
    with pytest.raises(ExaError, match="does not support"):
        validate_search_request(
            category="company", exclude_domains=["x.com"], start_published_date=None, end_published_date=None
        )
    # No conflict for an unrestricted category.
    validate_search_request(
        category="news", exclude_domains=["x.com"], start_published_date=None, end_published_date=None
    )


def test_build_contents_payload_and_prune() -> None:
    assert build_contents_payload() == {}
    assert build_contents_payload(highlights=True, max_age_hours=0) == {"highlights": True, "maxAgeHours": 0}
    assert prune({"a": None, "b": 1, "contents": {}}) == {"b": 1}


def test_exaresult_from_dict_tolerates_missing_fields() -> None:
    r = ExaResult.from_dict({"url": "https://u.com"})
    assert r.id == "https://u.com" and r.title is None and r.highlights == []


# --------------------------------------------------------------------------- #
# CLI (thin orchestrator)
# --------------------------------------------------------------------------- #


def test_cli_search_roundtrip(httpserver: HTTPServer, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    httpserver.expect_request("/search", method="POST").respond_with_json(
        {"requestId": "cli", "results": [{"id": "d", "url": "u", "title": "T"}]}
    )
    monkeypatch.setenv("EXA_API_KEY", "cli-key")
    args = build_parser().parse_args(
        ["--base-url", httpserver.url_for("/").rstrip("/"), "search", "hello", "--num-results", "2"]
    )
    out = run(args)
    assert out["requestId"] == "cli" and out["results"][0]["id"] == "d"


def test_cli_contents_answer_findsimilar(httpserver: HTTPServer, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("EXA_API_KEY", "k")
    base = httpserver.url_for("/").rstrip("/")
    httpserver.expect_request("/contents", method="POST").respond_with_json(
        {"requestId": "c", "results": [{"id": "d", "url": "u"}]}
    )
    httpserver.expect_request("/answer", method="POST").respond_with_json(
        {"requestId": "a", "answer": "yes", "citations": []}
    )
    httpserver.expect_request("/findSimilar", method="POST").respond_with_json(
        {"requestId": "s", "results": [{"id": "sim", "url": "v"}]}
    )
    p = build_parser()
    assert run(p.parse_args(["--base-url", base, "contents", "https://u.com", "--text"]))["requestId"] == "c"
    assert run(p.parse_args(["--base-url", base, "answer", "what?"]))["answer"] == "yes"
    assert run(p.parse_args(["--base-url", base, "find-similar", "https://seed.com"]))["results"][0]["id"] == "sim"


def test_cli_reports_error_on_missing_key(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    from infrastructure.search.exa.cli import main

    monkeypatch.delenv("EXA_API_KEY", raising=False)
    assert main(["search", "q"]) == 1
    assert "error:" in capsys.readouterr().err
