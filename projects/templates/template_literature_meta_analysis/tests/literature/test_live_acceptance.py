"""Controlled HTTP execution of all declared producers and domain failure controls."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from werkzeug.wrappers import Response

from infrastructure.search.literature.live_contract import LiveSettings
from template_literature_meta_analysis.literature.live_acceptance import main, run_live
from template_literature_meta_analysis.literature.live_workflow import parse_workflow

ROOT = Path(__file__).resolve().parents[2]
DOI = "10.1000/controlled-meta"
SOURCE = "We measured the clinical outcomes with a reproducible blinded protocol and reported every uncertainty. " * 4


def copied_project(tmp_path):
    root = tmp_path / ROOT.name
    shutil.copytree(ROOT / "src", root / "src", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "data", root / "data")
    shutil.copytree(ROOT / "manuscript", root / "manuscript")
    shutil.copy2(ROOT / "pyproject.toml", root / "pyproject.toml")
    return root


def node():
    return {
        "node_id": "n0",
        "node_name": "Measurements",
        "node_type": "experiment",
        "source_quote": SOURCE[:90],
        "description": "Reported measurements",
        "reproducibility_rating": 2,
        "depends_on": [],
    }


def configure(httpserver, *, bad_quote=False, status=200):
    records = [
        {
            "DOI": DOI + str(index),
            "title": [f"Controlled trial {index}"],
            "author": [{"given": "Ada", "family": "Researcher"}],
            "issued": {"date-parts": [[2020 + index, 1, 1]]},
            "abstract": SOURCE + (" Study protocol accuracy." if index else " Study safety evaluation."),
            "license": [],
            "link": [],
        }
        for index in range(3)
    ]
    records[0]["DOI"] = DOI
    httpserver.expect_request("/works").respond_with_json({"message": {"items": records}}, status=status)
    httpserver.expect_request("/search").respond_with_json(
        {"resultList": {"result": [{"doi": DOI, "isOpenAccess": "Y", "pmcid": "PMC123"}]}}
    )
    xml = f'<article><front><article-id pub-id-type="doi">{DOI}</article-id><license href="https://creativecommons.org/licenses/by/4.0/"/></front><body><p>{SOURCE}</p></body></article>'
    httpserver.expect_request("/PMC123/fullTextXML").respond_with_data(xml, content_type="application/xml")
    httpserver.expect_request("/api/tags").respond_with_json({"models": [{"name": "controlled", "digest": "a" * 64}]})

    def generation(request):
        invocation = request.json
        if "nodes" in invocation["format"]["properties"]:
            extracted = node()
            if bad_quote:
                extracted["source_quote"] = "This invented protocol is absent from the consumed source."
            value = {"nodes": [extracted]}
        else:
            value = {"label": "neutral", "source_quote": SOURCE[:90]}
        return Response(
            json.dumps({"model": "controlled", "done": True, "eval_count": 20, "response": json.dumps(value)}),
            content_type="application/json",
        )

    httpserver.expect_request("/api/generate", method="POST").respond_with_handler(generation)


def test_real_controlled_live_producers_and_independent_analysis(tmp_path, httpserver):
    configure(httpserver)
    root = copied_project(tmp_path)
    settings = LiveSettings("controlled", httpserver.url_for("").replace("localhost", "127.0.0.1"))
    path = run_live(
        root,
        Path("output/.pipeline/literature_acceptance/controlled"),
        settings,
        crossref_endpoint=httpserver.url_for("/works"),
        europepmc_endpoint=httpserver.url_for(""),
    )
    receipt = json.loads(path.read_text())
    assert receipt["status"] == "passed", receipt["issues"]
    assert set(receipt["producer_results"]) == {"retrieval", "fulltext", "extraction", "local-model", "kg"}
    assert receipt["producer_results"]["retrieval"]["analysis"]["independent_counts_match"]
    assert receipt["producer_results"]["kg"]["assertion_count"] == 1
    assert len(receipt["producer_results"]["local-model"]["calls"]) == 2
    score = json.loads((path.parent / "workflow_score.json").read_text())
    assert score["n_nodes"] == 1 and score["n_edges"] == 0
    assert score["structural_components"]["path_coverage"] == 0.0
    # The existing domain score includes source/sink/cohesion components; an
    # isolated partial node does not imply an overall zero score.
    assert score["composite_score"] == pytest.approx((score["content_score"] * score["structural_score"]) ** 0.5)
    assert not (root / "output/data").exists()


@pytest.mark.parametrize("bad_quote,status,expected", [(True, 200, "failed"), (False, 503, "blocked")])
def test_required_producer_failure_or_fabricated_workflow_cannot_pass(
    tmp_path, httpserver, bad_quote, status, expected
):
    configure(httpserver, bad_quote=bad_quote, status=status)
    root = copied_project(tmp_path)
    settings = LiveSettings("controlled", httpserver.url_for("").replace("localhost", "127.0.0.1"))
    path = run_live(
        root,
        Path("output/.pipeline/literature_acceptance/negative"),
        settings,
        crossref_endpoint=httpserver.url_for("/works"),
        europepmc_endpoint=httpserver.url_for(""),
    )
    assert json.loads(path.read_text())["status"] == expected


@pytest.mark.parametrize(
    "field,value",
    [
        ("node_type", "invented"),
        ("source_quote", "This invented quote is absent."),
        ("reproducibility_rating", True),
        ("reproducibility_rating", 2.5),
        ("depends_on", [None]),
        ("node_id", None),
        ("description", ""),
    ],
)
def test_workflow_domain_negative_controls(field, value):
    row = node()
    row[field] = value
    with pytest.raises(ValueError):
        parse_workflow({"nodes": [row]}, SOURCE, "doi:" + DOI)


def test_partial_workflow_retains_dangling_reference_signal_and_rejects_duplicates():
    row = node()
    row["depends_on"] = ["n1"]
    graph = parse_workflow({"nodes": [row]}, SOURCE, "doi:" + DOI)
    assert graph.dangling_reference_count == 1 and graph.edges == []
    with pytest.raises(ValueError, match="duplicated"):
        parse_workflow({"nodes": [row, row]}, SOURCE, "doi:" + DOI)
    with pytest.raises(ValueError):
        parse_workflow({"nodes": []}, SOURCE, "doi:" + DOI)


def test_core_default_and_explicit_live_arguments(tmp_path, capsys):
    root = copied_project(tmp_path)
    assert main(root, []) == 0
    assert json.loads(capsys.readouterr().out)["execution_mode"] == "core-reference"
    with pytest.raises(SystemExit):
        main(root, ["--mode", "live"])
