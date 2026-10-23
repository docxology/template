"""Controlled HTTP execution of all declared producers and domain failure controls."""

from __future__ import annotations

import copy
import json
from collections import Counter
import shutil
from pathlib import Path

import pytest
from werkzeug.wrappers import Response

from infrastructure.search.literature.live_contract import LiteratureFailed, LiveSession, LiveSettings
from template_literature_meta_analysis.literature.corpus import Corpus
from template_literature_meta_analysis.literature.live_acceptance import _validate_temporal_analysis, main, run_live
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


def configure(httpserver, *, bad_quote=False, bad_annotation_quote=False, single_year=False, status=200):
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
    if single_year:
        records = records[:1]
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
            choices = invocation["format"]["properties"]["nodes"]["items"]["properties"]["source_quote"]["enum"]
            extracted["source_quote"] = choices[0]
            if bad_quote:
                extracted["source_quote"] = "This invented protocol is absent from the consumed source."
            value = {"nodes": [extracted]}
        else:
            choices = invocation["format"]["properties"]["source_quote"]["enum"]
            quote = (
                "This invented annotation is absent from the consumed source." if bad_annotation_quote else choices[0]
            )
            value = {"label": "neutral", "source_quote": quote}
        return Response(
            json.dumps({"model": "controlled", "done": True, "eval_count": 20, "response": json.dumps(value)}),
            content_type="application/json",
        )

    httpserver.expect_request("/api/generate", method="POST").respond_with_handler(generation)


@pytest.mark.parametrize("single_year", [False, True])
def test_real_controlled_live_producers_and_independent_analysis(tmp_path, httpserver, single_year):
    configure(httpserver, single_year=single_year)
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
    temporal = json.loads((path.parent / "analysis/data/temporal_analysis.json").read_text())
    if single_year:
        assert temporal["year_counts"] == temporal["cumulative"] == {"2020": 1}
        assert temporal["growth_status"] == "insufficient_years"
        assert all(temporal[field] is None for field in ("cagr", "mean_growth_rate", "doubling_time"))
    else:
        assert "growth_status" not in temporal and temporal["cagr"] is not None
    # Feed genuinely forged copies of the real producer's file through the
    # same real session-consuming validator, with years from its actual corpus.
    original_temporal = (path.parent / "analysis/data/temporal_analysis.json").read_bytes()
    actual_papers = Corpus.load(path.parent / "corpus.jsonl").papers
    years = {str(year): count for year, count in Counter(paper.year for paper in actual_papers).items()}
    forgeries = []
    if single_year:
        year = next(iter(years))
        wrong_count = copy.deepcopy(temporal)
        wrong_count["year_counts"][year] += 1
        missing_null = copy.deepcopy(temporal)
        del missing_null["cagr"]
        invented_growth = copy.deepcopy(temporal)
        invented_growth["mean_growth_rate"] = 0.0
        forgeries = [wrong_count, missing_null, invented_growth]
    else:
        unsupported = copy.deepcopy(temporal)
        unsupported.update(growth_status="insufficient_years", cagr=None, mean_growth_rate=None, doubling_time=None)
        forgeries = [unsupported]
    for index, forged in enumerate(forgeries):
        probe = LiveSession(root, Path(f"output/.pipeline/literature_acceptance/forged-temporal-{index}"), settings, [])
        target = probe.directory / "analysis/data/temporal_analysis.json"
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps(forged))
        with pytest.raises(LiteratureFailed, match="temporal"):
            _validate_temporal_analysis(probe, years)
    assert (path.parent / "analysis/data/temporal_analysis.json").read_bytes() == original_temporal
    assert receipt["producer_results"]["kg"]["assertion_count"] == 1
    assert len(receipt["producer_results"]["local-model"]["calls"]) == 2
    score = json.loads((path.parent / "workflow_score.json").read_text())
    assert score["n_nodes"] == 1 and score["n_edges"] == 0
    assert score["structural_components"]["path_coverage"] == 0.0
    # The existing domain score includes source/sink/cohesion components; an
    # isolated partial node does not imply an overall zero score.
    assert score["composite_score"] == pytest.approx((score["content_score"] * score["structural_score"]) ** 0.5)
    assert not (root / "output/data").exists()
    # Inspect the actual request retained by the supervised HTTP producer.
    request = json.loads((path.parent / "model_1/request.json").read_text())
    properties = request["format"]["properties"]["nodes"]["items"]["properties"]
    assert properties["depends_on"]["maxItems"] == 3
    assert properties["depends_on"]["uniqueItems"] is True
    assert properties["source_quote"]["minLength"] == 20
    quote_options = properties["source_quote"]["enum"]
    consumed_excerpt = (path.parent / "fulltext.txt").read_text()[:6000]
    assert quote_options and len(quote_options) == len(set(quote_options))
    assert all(20 <= len(quote) <= 200 and quote in consumed_excerpt for quote in quote_options)
    actual_workflow = json.loads((path.parent / "workflow.json").read_text())
    assert actual_workflow["nodes"][0]["source_quote"] in quote_options
    for field in ("node_name", "description", "source_quote"):
        assert properties[field]["maxLength"] == 1000
    assert request["options"]["num_predict"] == 1024
    annotation_request = json.loads((path.parent / "model_2/request.json").read_text())
    annotation_source = json.loads(annotation_request["prompt"].split("SOURCE (bounded excerpt):\n", 1)[1])
    assert annotation_source == consumed_excerpt
    annotation_options = annotation_request["format"]["properties"]["source_quote"]["enum"]
    assert annotation_options and len(annotation_options) == len(set(annotation_options))
    assert all(20 <= len(quote) <= 200 and quote in consumed_excerpt for quote in annotation_options)
    actual_annotation = json.loads(json.loads((path.parent / "model_2/response.json").read_text())["response"])
    assert actual_annotation["source_quote"] in annotation_options
    assert annotation_request["options"]["num_predict"] == 1024


@pytest.mark.parametrize(
    "bad_quote,bad_annotation_quote,status,expected",
    [(True, False, 200, "failed"), (False, False, 503, "blocked"), (False, True, 200, "failed")],
)
def test_required_producer_failure_or_fabricated_workflow_cannot_pass(
    tmp_path, httpserver, bad_quote, bad_annotation_quote, status, expected
):
    configure(httpserver, bad_quote=bad_quote, bad_annotation_quote=bad_annotation_quote, status=status)
    root = copied_project(tmp_path)
    settings = LiveSettings("controlled", httpserver.url_for("").replace("localhost", "127.0.0.1"))
    path = run_live(
        root,
        Path("output/.pipeline/literature_acceptance/negative"),
        settings,
        crossref_endpoint=httpserver.url_for("/works"),
        europepmc_endpoint=httpserver.url_for(""),
    )
    actual = json.loads(path.read_text())
    assert actual["status"] == expected
    if bad_annotation_quote:
        assert "extraction" in actual["producer_results"]
        assert any("annotation quote is not verbatim" in issue for issue in actual["issues"])


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
    for dependencies in (["n1", "n1"], ["n0", "n1", "n2", "n2"]):
        malformed = node()
        malformed["depends_on"] = dependencies
        with pytest.raises(ValueError, match="unique list"):
            parse_workflow({"nodes": [malformed]}, SOURCE, "doi:" + DOI)


def test_core_default_and_explicit_live_arguments(tmp_path, capsys):
    root = copied_project(tmp_path)
    assert main(root, []) == 0
    assert json.loads(capsys.readouterr().out)["execution_mode"] == "core-reference"
    with pytest.raises(SystemExit):
        main(root, ["--mode", "live"])
