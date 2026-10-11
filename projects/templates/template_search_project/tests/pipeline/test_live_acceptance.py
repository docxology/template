"""Real controlled-provider tests; these are never actual-model acceptance receipts."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

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


def configure(httpserver, *, response_quote=SOURCE[:80], status=200):
    httpserver.expect_request("/works").respond_with_json(
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
                    }
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
    httpserver.expect_request("/api/generate", method="POST").respond_with_json(
        {
            "model": "controlled",
            "done": True,
            "eval_count": 10,
            "response": json.dumps({"summary": "A bounded source annotation", "source_quote": response_quote}),
        }
    )


def test_live_requires_all_real_producers_and_retains_byte_custody(tmp_path, httpserver):
    configure(httpserver)
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
    assert set(receipt["producer_results"]) == {"retrieval", "fulltext", "local-synthesis"}
    assert receipt["producer_results"]["local-synthesis"]["model_sha256"] == "a" * 64
    assert json.loads((path.parent / "synthesis.json").read_text())["paper_id"] == "doi:" + DOI
    assert not (root / "output/data").exists()


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
