"""Monid client tests using pytest-httpserver (no mocks)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from pytest_httpserver import HTTPServer

from infrastructure.search.monid import (
    LAST_REVIEWED,
    MonidClient,
    MonidConfig,
    MonidError,
    format_pricing_table,
    sorted_by_cost,
)
from infrastructure.search.monid.cli import build_parser, main, run
from infrastructure.search.monid.models import EndpointPrice, Money


def _client(httpserver: HTTPServer, **config_kwargs: object) -> MonidClient:
    base = httpserver.url_for("/").rstrip("/")
    cfg = MonidConfig(
        api_key="monid_test_key",
        base_url=base,
        poll_interval_seconds=0.01,
        max_poll_attempts=5,
        **config_kwargs,  # type: ignore[arg-type]
    )
    return MonidClient(cfg)


def test_discover_parses_results(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/v1/discover", method="POST").respond_with_json(
        {
            "query": "web search",
            "count": 1,
            "results": [
                {
                    "provider": "exa",
                    "providerName": "Exa",
                    "endpoint": "/search",
                    "description": "Neural web search",
                    "score": 0.91,
                    "tags": ["search"],
                    "price": {"type": "PER_CALL", "amount": {"value": 0.007, "currency": "USD"}},
                }
            ],
        }
    )
    resp = _client(httpserver).discover("web search", limit=3)
    assert resp.count == 1
    assert resp.results[0].provider == "exa"
    assert resp.results[0].price is not None
    assert resp.results[0].price.estimated_per_1k_calls_usd() == pytest.approx(7.0)


def test_discover_sends_auth_and_payload(httpserver: HTTPServer) -> None:
    captured: dict = {}

    def handler(request):  # type: ignore[no-untyped-def]
        captured["headers"] = dict(request.headers)
        captured["json"] = json.loads(request.get_data())
        from werkzeug.wrappers import Response

        return Response(json.dumps({"query": "x", "count": 0, "results": []}), content_type="application/json")

    httpserver.expect_request("/v1/discover", method="POST").respond_with_handler(handler)
    _client(httpserver).discover("  twitter posts  ", limit=7, min_score=0.5)
    assert captured["json"]["query"] == "twitter posts"
    assert captured["json"]["limit"] == 7
    assert captured["json"]["minScore"] == 0.5
    assert captured["headers"]["Authorization"] == "Bearer monid_test_key"


def test_discover_rejects_empty_query() -> None:
    client = MonidClient(MonidConfig(api_key="k"))
    with pytest.raises(MonidError, match="non-empty"):
        client.discover("   ")


def test_inspect_returns_schema(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/v1/inspect", method="POST").respond_with_json(
        {
            "provider": "apify",
            "endpoint": "/apidojo/tweet-scraper",
            "description": "Scrape tweets",
            "input": {"body": {"type": "object"}},
            "price": {"type": "PER_CALL", "amount": {"value": 0.003, "currency": "USD"}},
        }
    )
    detail = _client(httpserver).inspect("apify", "/apidojo/tweet-scraper")
    assert detail.provider == "apify"
    assert detail.input_schema["body"]["type"] == "object"
    assert detail.price is not None
    assert detail.price.estimated_per_call_usd() == pytest.approx(0.003)


def test_run_sync_completed(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/v1/run", method="POST").respond_with_json(
        {
            "runId": "01SYNC",
            "provider": "pdl",
            "endpoint": "/person/enrich",
            "status": "COMPLETED",
            "output": {"full_name": "Jane Doe"},
            "providerResponse": {"httpStatus": 200},
            "price": {"type": "PER_CALL", "amount": {"value": 0.003, "currency": "USD"}},
            "cost": {"value": 0.003, "currency": "USD"},
        }
    )
    record = _client(httpserver).run("pdl", "/person/enrich", {"email": "j@example.com"})
    assert record.status == "COMPLETED"
    assert record.output == {"full_name": "Jane Doe"}
    assert record.provider_http_status == 200


def test_run_async_polls_until_completed(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/v1/run", method="POST").respond_with_json(
        {
            "runId": "01ASYNC",
            "provider": "apify",
            "endpoint": "/apidojo/tweet-scraper",
            "status": "READY",
        },
        status=202,
    )
    poll_count = {"n": 0}

    def poll_handler(request):  # type: ignore[no-untyped-def]
        poll_count["n"] += 1
        payload = (
            {
                "runId": "01ASYNC",
                "status": "COMPLETED",
                "provider": "apify",
                "endpoint": "/x",
                "output": [{"text": "hello"}],
                "providerResponse": {"httpStatus": 200},
            }
            if poll_count["n"] >= 2
            else {"runId": "01ASYNC", "status": "RUNNING", "provider": "apify", "endpoint": "/x"}
        )
        from werkzeug.wrappers import Response

        return Response(json.dumps(payload), content_type="application/json")

    httpserver.expect_request("/v1/runs/01ASYNC", method="GET").respond_with_handler(poll_handler)
    record = _client(httpserver).run("apify", "/apidojo/tweet-scraper", {"maxItems": 1}, wait=True)
    assert record.status == "COMPLETED"
    assert record.output == [{"text": "hello"}]


def test_balance(httpserver: HTTPServer) -> None:
    captured: dict = {}

    def handler(request):  # type: ignore[no-untyped-def]
        captured["method"] = request.method
        captured["body"] = request.get_data()
        from werkzeug.wrappers import Response

        return Response(
            json.dumps({"balance": {"value": 2.85, "currency": "USD"}}),
            content_type="application/json",
        )

    httpserver.expect_request("/v1/wallet/balance", method="GET").respond_with_handler(handler)
    bal = _client(httpserver).balance()
    assert bal.value == pytest.approx(2.85)
    assert bal.currency == "USD"
    assert captured["method"] == "GET"
    assert captured["body"] == b""


def test_from_env_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MONID_API_KEY", raising=False)
    with pytest.raises(MonidError, match="MONID_API_KEY"):
        MonidClient.from_env()


def test_pricing_table_orders_cheapest_first() -> None:
    rows = sorted_by_cost()
    assert rows[0].provider == "Serper"
    assert rows[0].usd_per_1k_searches == pytest.approx(0.30)
    table = format_pricing_table()
    assert "USD / 1k searches" in table
    assert "Monid" in table


def test_cli_pricing_table_subcommand(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["pricing-table"]) == 0
    out = capsys.readouterr().out
    assert "Serper" in out and "Exa" in out


def test_cli_discover_with_env(httpserver: HTTPServer, monkeypatch: pytest.MonkeyPatch) -> None:
    httpserver.expect_request("/v1/discover", method="POST").respond_with_json(
        {"query": "ai", "count": 0, "results": []}
    )
    monkeypatch.setenv("MONID_API_KEY", "monid_live_test")
    base = httpserver.url_for("/").rstrip("/")
    assert main(["--base-url", base, "discover", "ai"]) == 0


def test_run_cli_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONID_API_KEY", "monid_live_test")
    parser = build_parser()
    args = parser.parse_args(["run", "p", "/e", "--input", "{bad"])
    with pytest.raises(MonidError, match="invalid --input JSON"):
        run(args)


def test_endpoint_price_per_result_with_flat_fee() -> None:
    price = EndpointPrice(
        type="PER_RESULT",
        amount=Money(value=0.001),
        flat_fee=Money(value=0.002),
    )
    assert price.estimated_per_call_usd(result_count=10) == pytest.approx(0.012)
    assert price.estimated_per_1k_calls_usd(result_count=1) == pytest.approx(3.0)


def test_endpoint_price_per_result_rejects_negative_count() -> None:
    price = EndpointPrice(type="PER_RESULT", amount=Money(value=0.001))
    with pytest.raises(ValueError, match="non-negative"):
        price.estimated_per_call_usd(result_count=-1)


def test_search_api_prices_have_current_review_date() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    pricing_md = (repo_root / "infrastructure/search/monid/PRICING.md").read_text(encoding="utf-8")
    assert f"**Last reviewed:** {LAST_REVIEWED}" in pricing_md


def test_hub_docs_do_not_hardcode_search_api_prices() -> None:
    """USD/1k list prices belong in pricing.py and PRICING.md only."""
    repo_root = Path(__file__).resolve().parents[3]
    forbidden = ("$7.00/1k", "$0.30/1k", "Serper **$0.30")
    hubs = (
        "README.md",
        "AGENTS.md",
        "infrastructure/search/SKILL.md",
        "infrastructure/search/README.md",
    )
    offenders: list[str] = []
    for relative in hubs:
        path = repo_root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden:
            if phrase in text:
                offenders.append(f"{relative}: {phrase}")
    assert not offenders, "hardcoded search API prices in hub docs:\n" + "\n".join(offenders)


@pytest.mark.network
def test_live_discover_includes_price_when_key_present() -> None:
    if not os.environ.get("MONID_API_KEY", "").strip():
        pytest.skip("MONID_API_KEY not set")
    resp = MonidClient.from_env().discover("web search", limit=3)
    assert resp.count >= 0
    if resp.results:
        assert resp.results[0].price is not None
        assert resp.results[0].price.type
