"""Real controlled-provider phase/calibration execution, not actual-model evidence."""

from __future__ import annotations

import json
import shutil
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest
import yaml
from infrastructure.search.literature.live_contract import LiveSettings
from werkzeug.wrappers import Response

ROOT = Path(__file__).resolve().parents[1]
DOI = "10.1000/controlled-phases"
CONTACT = "controlled-protocol@example.invalid"
SOURCE = "We measured the exoplanet atmosphere with JWST and reported every calibrated spectral uncertainty. " * 4

# Required producers retain their <=600s run and <=60s worker deadlines.
# Real multi-worker cases also need finite final custody/cleanup allowance.
pytestmark = pytest.mark.timeout(720)


def copied_project(tmp_path):
    root = tmp_path / ROOT.name
    shutil.copytree(ROOT / "src", root / "src", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "data", root / "data")
    shutil.copytree(ROOT / "manuscript", root / "manuscript")
    shutil.copy2(ROOT / "pyproject.toml", root / "pyproject.toml")
    config_path = root / "manuscript/config.yaml"
    config = yaml.safe_load(config_path.read_text())
    corresponding = [row for row in config["authors"] if row.get("corresponding") is True]
    assert len(corresponding) == 1
    corresponding[0]["email"] = CONTACT
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))
    return root


def configure(httpserver, *, wrong_calibration=False, bad_quote=False, status=200):
    httpserver.expect_request("/works").respond_with_json(
        {
            "message": {
                "items": [
                    {
                        "DOI": DOI,
                        "title": ["Controlled atmosphere source"],
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
    record = {
        "DOI": DOI,
        "title": ["Controlled atmosphere source"],
        "author": [{"given": "Ada", "family": "Researcher"}],
        "issued": {"date-parts": [[2024, 1, 1]]},
        "abstract": SOURCE,
        "license": [],
        "link": [],
    }
    httpserver.expect_request("/works/" + DOI).respond_with_json({"message": record})
    expected_queries = []
    for query, minimum in (
        ('"exoplanet atmosphere" OR "exoplanet atmospheric"', 2010),
        ('"James Webb" AND "atmosphere" AND ("exoplanet" OR "planet")', 2020),
        ('"water vapor" AND "exoplanet" AND ("detection" OR "abundance")', 2015),
    ):
        parameters = {
            "search.title_and_abstract": query,
            "per_page": "3",
            "filter": (
                "open_access.is_oa:true,primary_location.license:cc-by,primary_location.version:publishedVersion,"
                f"from_publication_date:{minimum}-01-01,to_publication_date:2026-12-31"
            ),
            "mailto": CONTACT,
        }
        expected_queries.append(parameters)
        httpserver.expect_request(
            "/openalex",
            query_string=parameters,
        ).respond_with_json(
            {
                "results": [
                    {
                        "id": "https://openalex.org/W1",
                        "doi": "https://doi.org/" + DOI,
                        "title": "Controlled atmosphere source",
                        "primary_location": {
                            "is_oa": True,
                            "version": "publishedVersion",
                            "license": "cc-by",
                        },
                        "abstract_inverted_index": {
                            word: [i for i, current in enumerate(SOURCE.split()) if current == word]
                            for word in set(SOURCE.split())
                        },
                    }
                ]
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
        invocation = request.json
        source = json.loads(invocation["prompt"].split("SOURCE (bounded excerpt):\n", 1)[1])
        labels = invocation["format"]["properties"]["label"]["enum"]
        if labels == ["yes", "no"]:
            label = "no" if "perspective" in source or "no information" in source else "yes"
            if wrong_calibration:
                label = "no" if label == "yes" else "yes"
        else:
            label = "observational"
        choices = invocation["format"]["properties"]["source_quote"]["enum"]
        quote = "This invented annotation is absent from the consumed source." if bad_quote else choices[0]
        value = {"label": label, "source_quote": quote}
        return Response(
            json.dumps(
                {
                    "model": "controlled",
                    "done": True,
                    "eval_count": 10,
                    "response": json.dumps(value),
                }
            ),
            content_type="application/json",
        )

    httpserver.expect_request("/api/generate", method="POST").respond_with_handler(generation)
    return expected_queries


@pytest.mark.parametrize("offered", [None, "foreign-protocol@example.invalid"])
def test_controlled_openalex_requires_the_declared_contact(httpserver, offered):
    """A real strict server admits the exact query, then refuses absent/foreign identity."""
    parameters = dict(configure(httpserver)[0])
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(
        httpserver.url_for("/openalex") + "?" + urllib.parse.urlencode(parameters), timeout=10
    ) as response:
        assert response.status == 200
        assert json.load(response)["results"][0]["doi"] == "https://doi.org/" + DOI
    if offered is None:
        parameters.pop("mailto")
    else:
        parameters["mailto"] = offered
    with pytest.raises(urllib.error.HTTPError) as refused:
        opener.open(httpserver.url_for("/openalex") + "?" + urllib.parse.urlencode(parameters), timeout=10)
    assert refused.value.code == 500


def test_copied_protocol_contact_preserves_original_source(tmp_path):
    original = (ROOT / "manuscript/config.yaml").read_bytes()
    root = copied_project(tmp_path)
    config = yaml.safe_load((root / "manuscript/config.yaml").read_text())
    assert [row["email"] for row in config["authors"] if row.get("corresponding") is True] == [CONTACT]
    assert (ROOT / "manuscript/config.yaml").read_bytes() == original


def test_all_selected_phases_calibration_classification_and_licensed_text_run(tmp_path, httpserver):
    from multi_phase.live_acceptance import run_live

    configure(httpserver)
    root = copied_project(tmp_path)
    settings = LiveSettings("controlled", httpserver.url_for("").replace("localhost", "127.0.0.1"))
    path = run_live(
        root,
        Path("output/.pipeline/literature_acceptance/controlled"),
        settings,
        crossref_endpoint=httpserver.url_for("/works"),
        europepmc_endpoint=httpserver.url_for(""),
        openalex_endpoint=httpserver.url_for("/openalex"),
    )
    receipt = json.loads(path.read_text())
    assert receipt["status"] == "passed", receipt["issues"]
    frozen = yaml.safe_load((path.parent / "inputs/manuscript/config.yaml").read_text())
    assert [row["email"] for row in frozen["authors"] if row.get("corresponding") is True] == [CONTACT]
    for index in range(3):
        http = json.loads((path.parent / f"phase_{index}_retrieval/http.json").read_text())
        assert urllib.parse.parse_qs(urllib.parse.urlsplit(http["requested_url"]).query)["mailto"] == [CONTACT]
    assert set(receipt["producer_results"]) == {
        "retrieval",
        "screening",
        "local-classification",
        "licensed-fulltext",
    }
    assert receipt["producer_results"]["screening"]["accuracy"] == 1.0
    assert len(receipt["local_generation_calls"]) == 7
    assert receipt["producer_results"]["retrieval"]["selected_provider"] == "openalex-crossref"
    selection = json.loads((path.parent / "fulltext_selection.json").read_text())
    assert selection["max_candidates"] == 3 and selection["candidate_ids"] == ["doi:" + DOI]
    assert len(selection["phase_eligible_ids"]) == 3
    assert all(ids == ["doi:" + DOI] for ids in selection["phase_eligible_ids"].values())
    analysis = json.loads((path.parent / "cross_phase_analysis.json").read_text())
    assert all(row["paper_count"] == 1 for row in analysis["phase_membership"].values())
    assert "do not establish scientific support" in analysis["claim_boundary"]
    assert "phase_1_foundation_corpus.jsonl" in receipt["consumed_artifacts"]
    assert not (root / "output/data").exists()
    calibration = json.loads((path.parent / "inputs/data/llm_filter_calibration.json").read_text())
    phase_abstracts = {
        json.loads(line)["abstract"][:6000]
        for corpus in path.parent.glob("phase_*_corpus.jsonl")
        for line in corpus.read_text().splitlines()
    }
    for index in range(1, 8):
        request = json.loads((path.parent / f"model_{index}/request.json").read_text())
        source = json.loads(request["prompt"].split("SOURCE (bounded excerpt):\n", 1)[1])
        if index <= 4:
            assert source == calibration["cases"][index - 1]["abstract"]
        else:
            assert source in phase_abstracts
        choices = request["format"]["properties"]["source_quote"]["enum"]
        assert choices and len(choices) == len(set(choices))
        assert all(20 <= len(quote) <= 200 and quote in source for quote in choices)
        actual_annotation = json.loads(
            json.loads((path.parent / f"model_{index}/response.json").read_text())["response"]
        )
        assert actual_annotation["source_quote"] in choices
        assert request["options"]["num_predict"] == 1024


@pytest.mark.parametrize(
    "wrong_calibration,bad_quote,status,expected",
    [
        (True, False, 200, "failed"),
        (False, False, 503, "blocked"),
        (False, True, 200, "failed"),
    ],
)
def test_failed_screening_or_phase_retrieval_cannot_pass(
    tmp_path, httpserver, wrong_calibration, bad_quote, status, expected
):
    from multi_phase.live_acceptance import run_live

    configure(
        httpserver,
        wrong_calibration=wrong_calibration,
        bad_quote=bad_quote,
        status=status,
    )
    root = copied_project(tmp_path)
    settings = LiveSettings("controlled", httpserver.url_for("").replace("localhost", "127.0.0.1"))
    path = run_live(
        root,
        Path("output/.pipeline/literature_acceptance/negative"),
        settings,
        crossref_endpoint=httpserver.url_for("/works"),
        europepmc_endpoint=httpserver.url_for(""),
        openalex_endpoint=httpserver.url_for("/openalex"),
    )
    assert json.loads(path.read_text())["status"] == expected
    if wrong_calibration:
        assert len(json.loads(path.read_text())["local_generation_calls"]) == 4
    if bad_quote:
        assert len(json.loads(path.read_text())["local_generation_calls"]) == 1
        assert any("annotation quote is not verbatim" in issue for issue in json.loads(path.read_text())["issues"])


def test_core_default_is_offline_and_live_arguments_are_explicit(tmp_path, capsys):
    from multi_phase.live_acceptance import main

    root = copied_project(tmp_path)
    corpus = root / "output/data/corpus.jsonl"
    corpus.parent.mkdir(parents=True)
    corpus.write_text('{"title":"Offline reference"}\n')
    assert main(root, []) == 0
    assert json.loads(capsys.readouterr().out)["live_capabilities_tested"] == []
    with pytest.raises(SystemExit):
        main(root, ["--mode", "live"])


def test_fulltext_round_robin_covers_phases_before_repeat() -> None:
    from infrastructure.search.literature.crossref_backend import crossref_item_to_paper

    from multi_phase.live_acceptance import _fulltext_candidates

    def record(name):
        return crossref_item_to_paper({"DOI": "10.1000/" + name, "title": [name]})

    foundation, jwst, molecules = [record(name) for name in ("foundation", "jwst", "molecules")]
    repeated = record("foundation")
    later = record("later")
    selected = _fulltext_candidates({"foundation": [foundation, later], "jwst": [jwst], "molecules": [molecules]})
    assert [paper.id for paper in selected] == [paper.id for paper in (foundation, jwst, molecules)]
    assert _fulltext_candidates({"foundation": [foundation], "jwst": [repeated, jwst]}) == [foundation, jwst]
    assert _fulltext_candidates({}) == []


@pytest.mark.parametrize(
    "citation_fields,eligible",
    [
        ({"is-referenced-by-count": 12}, True),
        ({"is-referenced-by-count": 6}, True),
        ({"is-referenced-by-count": 5}, False),
        ({"is-referenced-by-count": 0}, False),
        ({"is-referenced-by-count": None}, True),
        ({}, True),
    ],
    ids=["above-threshold", "at-threshold", "below-threshold", "measured-zero", "unavailable", "absent"],
)
def test_retrieved_citation_count_survives_phase_filter_and_corpus(
    tmp_path: Path, citation_fields: dict[str, int | None], eligible: bool
) -> None:
    from infrastructure.search.literature.crossref_backend import crossref_item_to_paper

    from literature.corpus import Corpus
    from multi_phase.live_acceptance import _domain_paper
    from multi_phase.search import MultiPhaseSearchRunner

    config_path = tmp_path / "config.yaml"
    config_path.write_text("project_config: {}\n", encoding="utf-8")
    runner = MultiPhaseSearchRunner(config_path, project_root=tmp_path)
    paper = _domain_paper(
        crossref_item_to_paper(
            {
                "DOI": DOI,
                "title": ["Citation eligibility boundary"],
                "issued": {"date-parts": [[2024]]},
                **citation_fields,
            }
        )
    )
    expected_count = citation_fields.get("is-referenced-by-count")
    assert paper.citation_count == expected_count
    retained = runner.apply_deterministic_filters([paper], {"min_citation_count": 6})
    expected = [(paper.canonical_id, expected_count)] if eligible else []
    assert [(row.canonical_id, row.citation_count) for row in retained] == expected
    corpus_path = tmp_path / "retained_corpus.jsonl"
    Corpus(papers=retained).save(corpus_path)
    restored = Corpus.load(corpus_path).papers
    assert [(row.canonical_id, row.citation_count) for row in restored] == expected
    assert runner.apply_deterministic_filters(restored, {"min_citation_count": 6}) == restored
