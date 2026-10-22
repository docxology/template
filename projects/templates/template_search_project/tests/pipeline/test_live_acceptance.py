"""Real controlled-provider tests; these are never actual-model acceptance receipts."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from werkzeug.wrappers import Response

from infrastructure.search.literature.live_contract import LiveSettings
from template_search_project.pipeline.live_acceptance import main, run_live

ROOT = Path(__file__).resolve().parents[2]
DOI = "10.1000/controlled-search"
SOURCE = "We calibrated the telescope observations and reported uncertainty in each measured spectrum. " * 4


def copied_project(tmp_path):
    root = tmp_path / ROOT.name
    shutil.copytree(ROOT / "src", root / "src", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "data", root / "data")
    shutil.copytree(ROOT / "manuscript", root / "manuscript")
    shutil.copy2(ROOT / "pyproject.toml", root / "pyproject.toml")
    return root


def configure(httpserver, *, response_quote=None, status=200, incomplete=False):
    # The actual HTTP request keeps the configured query and three-record ceiling,
    # and asks only for the explicit rights/version/media sample the consumer uses.
    httpserver.expect_request(
        "/works",
        query_string={
            "query": "reproducible research optimization",
            "rows": "3",
            "filter": (
                "has-license:true,has-full-text:true,license.url:https://creativecommons.org/licenses/by/4.0/"
                ",license.version:vor,full-text.version:vor,full-text.type:application/pdf"
            ),
        },
    ).respond_with_json(
        {
            "message": {
                "items": [
                    {
                        "DOI": DOI,
                        "title": ["Controlled source"],
                        "author": [{"given": "Ada", "family": "Researcher"}],
                        "issued": {"date-parts": [[2024, 1, 1]]},
                        "abstract": SOURCE,
                        "license": [],
                        "link": [],
                    },
                    *(
                        [
                            {
                                "DOI": "10.1000/incomplete",
                                "title": ["Correction without deposited authors"],
                                "issued": {"date-parts": [[2024]]},
                            }
                        ]
                        if incomplete
                        else []
                    ),
                ]
            }
        },
        status=status,
    )
    httpserver.expect_request("/search").respond_with_json(
        {"resultList": {"result": [{"doi": DOI, "isOpenAccess": "Y", "pmcid": "PMC123"}]}}
    )
    xml = f'<article><front><article-id pub-id-type="doi">{DOI}</article-id><license href="https://creativecommons.org/licenses/by/4.0/"/></front><body><p>{SOURCE}</p></body></article>'
    httpserver.expect_request("/PMC123/fullTextXML").respond_with_data(xml, content_type="application/xml")
    httpserver.expect_request("/api/tags").respond_with_json({"models": [{"name": "controlled", "digest": "a" * 64}]})

    def generation(request):
        choices = request.json["format"]["properties"]["source_quote"]["enum"]
        quote = choices[0] if response_quote is None else response_quote
        return Response(
            json.dumps(
                {
                    "model": "controlled",
                    "done": True,
                    "eval_count": 10,
                    "response": json.dumps(
                        {
                            "summary": "A bounded source annotation",
                            "source_quote": quote,
                        }
                    ),
                }
            ),
            content_type="application/json",
        )

    httpserver.expect_request("/api/generate", method="POST").respond_with_handler(generation)


@pytest.mark.parametrize("incomplete", [False, True])
def test_live_requires_all_real_producers_and_retains_byte_custody(tmp_path, httpserver, incomplete):
    configure(httpserver, incomplete=incomplete)
    root = copied_project(tmp_path)
    endpoint = httpserver.url_for("").replace("localhost", "127.0.0.1")
    path = run_live(
        root,
        Path("output/.pipeline/literature_acceptance/controlled"),
        LiveSettings("controlled", endpoint),
        crossref_endpoint=httpserver.url_for("/works"),
        europepmc_endpoint=httpserver.url_for(""),
    )
    receipt = json.loads(path.read_text())
    assert receipt["status"] == "passed", receipt["issues"]
    assert receipt["source_unchanged"] and receipt["consumed_unchanged"]
    assert set(receipt["producer_results"]) == {
        "retrieval",
        "fulltext",
        "local-synthesis",
    }
    assert receipt["producer_results"]["local-synthesis"]["model_sha256"] == "a" * 64
    assert json.loads((path.parent / "synthesis.json").read_text())["paper_id"] == "doi:" + DOI
    assert not (root / "output/data").exists()
    request = json.loads((path.parent / "model_1/request.json").read_text())
    source = json.loads(request["prompt"].split("SOURCE (bounded excerpt):\n", 1)[1])
    assert source == (path.parent / "fulltext.txt").read_text()[:6000]
    choices = request["format"]["properties"]["source_quote"]["enum"]
    assert choices and len(choices) == len(set(choices))
    assert all(20 <= len(quote) <= 200 and quote in source for quote in choices)
    assert json.loads((path.parent / "synthesis.json").read_text())["source_quote"] in choices
    assert request["options"]["num_predict"] == 1024
    assert request["format"]["properties"]["summary"] == {"type": "string", "minLength": 1, "maxLength": 512}
    retrieval = json.loads((path.parent / "retrieval_report.json").read_text())
    assert retrieval["raw_count"] == 1 + int(incomplete)
    assert retrieval["eligible_count"] == retrieval["unique_count"] == 1
    assert retrieval["deduplicated_count"] == 0 and retrieval["excluded_count"] == int(incomplete)
    if incomplete:
        assert retrieval["excluded_records"] == [
            {
                "raw_index": 1,
                "paper_id": "doi:10.1000/incomplete",
                "doi": "10.1000/incomplete",
                "reasons": ["missing_authors"],
            }
        ]


@pytest.mark.parametrize(
    "quote,expected", [("This fabricated quote is absent from the source text.", "failed"), (SOURCE[:80], "blocked")]
)
def test_fabricated_quote_or_failed_required_retrieval_cannot_pass(tmp_path, httpserver, quote, expected):
    configure(httpserver, response_quote=quote, status=503 if expected == "blocked" else 200)
    root = copied_project(tmp_path)
    endpoint = httpserver.url_for("").replace("localhost", "127.0.0.1")
    path = run_live(
        root,
        Path("output/.pipeline/literature_acceptance/negative"),
        LiveSettings("controlled", endpoint),
        crossref_endpoint=httpserver.url_for("/works"),
        europepmc_endpoint=httpserver.url_for(""),
    )
    assert json.loads(path.read_text())["status"] == expected


def test_core_default_is_offline_and_live_requires_explicit_model_output(tmp_path, capsys):
    root = copied_project(tmp_path)
    assert main(root, []) == 0
    assert json.loads(capsys.readouterr().out)["live_capabilities_tested"] == []
    with pytest.raises(SystemExit):
        main(root, ["--mode", "live"])
