"""Real artifact and domain parity across the declared engine boundary."""

from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import json
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from manuscript.variables.context import ExtractContext

ARTIFACTS = {
    "temporal_analysis.json": {
        "year_counts": {"2020": 2, "2021": 1},
        "first_year": 2020,
        "last_year": 2021,
        "peak_year": 2020,
        "mean_growth_rate": 0.5,
        "cagr": 0.5,
        "doubling_time": 1.7,
    },
    "citation_network.json": {
        "num_nodes": 3,
        "num_edges": 2,
        "density": 1 / 3,
        "avg_in_degree": 2 / 3,
        "connected_components": 1,
        "num_communities": 1,
        "top_cited": [["doi:10.1000/source", 2]],
        "betweenness": {"doi:10.1000/source": 0.5},
        "assortativity": 0.25,
        "average_clustering": 0.5,
    },
    "subfield_classification.json": {"atmospheres": 2, "detection": 1},
    "topics.json": [{"topic_id": 0, "top_words": ["atmosphere", "spectrum"]}],
    "tfidf_data.json": {"feature_names": ["atmosphere", "spectrum"]},
    "fulltext_assessment.json": {
        "abstract_coverage": {"percent_with_abstract": 100, "has_abstract": 3},
        "open_access": {"is_oa": 2, "percent_oa": 200 / 3},
        "identifier_coverage": {"doi": 3},
    },
    "descriptive_stats.json": {
        "descriptive_stats": {
            "total": 3,
            "unique_authors": 2,
            "citation_count_mean": 2,
            "citation_count_median": 2,
            "citation_count_max": 3,
            "citation_count_total": 6,
            "counts_by_venue": {"Astrophysical Journal": 3},
        },
        "citation_distribution": {"gini": 0.25, "n": 3, "histogram": {"1-3": 3}},
        "author_productivity": [["Ada Researcher", 2]],
    },
    "entities.json": {"JWST": 2, "atmosphere": 1},
    "keyphrases.json": {"top_keyphrases": [{"phrase": "transmission spectrum", "score": 0.75}]},
    "embedding_analysis.json": {
        "num_clusters": 2,
        "top_similar_pairs": [{"paper_a": "A", "paper_b": "B", "similarity": 0.8}],
    },
}


@pytest.mark.parametrize("name", ["analysis", "citation", "subfields", "temporal"])
@pytest.mark.parametrize("layout", ["missing", "data", "root"])
def test_duplicate_extractors_preserve_actual_artifact_values(tmp_path, name, layout):
    output = tmp_path / "output"
    data = output / "data"
    data.mkdir(parents=True)
    if layout != "missing":
        base = data if layout == "data" else output
        for filename, value in ARTIFACTS.items():
            (base / filename).write_text(json.dumps(value))
        (output / "figures").mkdir()
        (output / "figures" / "source.png").write_bytes(b"bounded figure existence fixture")
    context = ExtractContext(output, data, tmp_path, {}, 3)
    local = importlib.import_module(f"manuscript.variables.extractors.{name}")
    provider = importlib.import_module(f"template_literature_meta_analysis.manuscript.variables.extractors.{name}")
    function = f"extract_{name}"
    actual = getattr(local, function)(context)
    assert actual == getattr(provider, function)(context)
    assert all(isinstance(value, str) for value in actual.values())
    if name == "analysis" and layout != "missing":
        assert actual["NUM_FIGURES"] == "1"
        assert actual["CITATION_TOTAL"] == "6"
        assert "| JWST | 2 |" in actual["TOP_ENTITIES_TABLE"]


@pytest.mark.parametrize("name", ["analysis", "citation", "subfields", "temporal"])
def test_duplicate_extractors_preserve_corrupt_artifact_failure(tmp_path, name):
    filename = {
        "analysis": "topics.json",
        "citation": "citation_network.json",
        "subfields": "subfield_classification.json",
        "temporal": "temporal_analysis.json",
    }[name]
    output = tmp_path / "output"
    output.mkdir()
    (output / filename).write_text("{invalid")
    context = ExtractContext(output, output / "data", tmp_path, {}, 0)
    for prefix in ("manuscript", "template_literature_meta_analysis.manuscript"):
        module = importlib.import_module(f"{prefix}.variables.extractors.{name}")
        with pytest.raises(json.JSONDecodeError):
            getattr(module, f"extract_{name}")(context)


def test_real_engine_model_corpus_bibtex_and_sampling_domain_contract(tmp_path):
    from template_literature_meta_analysis.literature.models import Paper as EnginePaper

    from literature.bibliography import corpus_to_bibtex
    from literature.corpus import Corpus
    from literature.models import Author, Paper
    from literature.sampling import load_sampling_config, sample_papers

    assert Paper is EnginePaper
    poor = Paper(title="Transmission spectra", doi="https://doi.org/10.1000/source", year=2024)
    richer = Paper(
        title="Transmission spectra",
        doi="10.1000/SOURCE",
        year=2024,
        authors=[Author(name="Ada Researcher")],
        abstract="Measured atmospheric spectra",
    )
    corpus = Corpus([poor, richer])
    assert len(corpus) == 1 and corpus.papers[0].abstract == richer.abstract
    corpus.save(tmp_path / "corpus.jsonl")
    loaded = Corpus.load(tmp_path / "corpus.jsonl")
    bibliography = corpus_to_bibtex(loaded)
    assert "researcher2024transmission" in bibliography and "doi={10.1000/SOURCE}" in bibliography
    assert sample_papers(loaded.papers, fraction=1, seed=7) == loaded.papers
    with pytest.raises(ValueError, match="fraction"):
        load_sampling_config({"sampling": {"fraction": True}})
    with pytest.raises(ValueError, match="start"):
        loaded.filter_by_year(start=2025, end=2024)


@pytest.mark.parametrize("layout", ["missing", "data", "root", "both"])
def test_duplicate_io_preserves_actual_data_precedence_and_reference_counts(tmp_path, layout):
    from template_literature_meta_analysis.manuscript.variables import io as engine

    from manuscript.variables import io as local

    data = tmp_path / "data"
    data.mkdir()
    if layout in {"root", "both"}:
        (tmp_path / "topics.json").write_text('[{"topic_id":9}]')
    if layout in {"data", "both"}:
        (data / "topics.json").write_text('[{"topic_id":1}]')
    corpus = data / "corpus.jsonl"
    corpus.write_text('{"references":["a","b"]}\n\nnot-json\n{"references":["c"]}\n')
    assert local.load_pipeline_json_raw(data, tmp_path, "topics.json") == engine.load_pipeline_json_raw(
        data, tmp_path, "topics.json"
    )
    assert local.count_jsonl_lines(corpus) == engine.count_jsonl_lines(corpus) == 3
    assert local.count_total_references(corpus) == engine.count_total_references(corpus) == 3
    assert local.load_json(tmp_path / "absent.json") == engine.load_json(tmp_path / "absent.json")
    if layout in {"data", "both"}:
        assert local.load_json(data / "topics.json") == {"_value": [{"topic_id": 1}]}


@pytest.mark.parametrize(
    "content,variables,lenient",
    [
        ("Corpus {{N}}; literal.", {"N": "3"}, False),
        ("{{MISSING}} {{N}}", {"N": "3"}, True),
        ("plain", {}, False),
        ("{{MISSING}}", {}, False),
    ],
)
def test_duplicate_injection_preserves_actual_output_or_failure(content, variables, lenient):
    from template_literature_meta_analysis.manuscript.variables.inject import inject_variables as engine

    from manuscript.variables.inject import inject_variables

    if not lenient and "{{MISSING}}" in content:
        for function in (inject_variables, engine):
            with pytest.raises(RuntimeError, match="MISSING"):
                function(content, variables, "source.md", lenient)
    else:
        assert inject_variables(content, variables, "source.md", lenient) == engine(
            content, variables, "source.md", lenient
        )


def test_declared_engine_custody_records_actual_dependency_source_and_version():
    from infrastructure.search.literature.live_contract import declared_dependency_custody

    project_root = Path(__file__).resolve().parents[1]
    import template_literature_meta_analysis as engine

    custody = declared_dependency_custody(project_root)["template-literature-meta-analysis"]
    assert isinstance(engine.__file__, str)
    actual_source = Path(engine.__file__).absolute().parent
    assert (
        custody["files"]["literature/models.py"]
        == hashlib.sha256((actual_source / "literature/models.py").read_bytes()).hexdigest()
    )
    if actual_source.name == "src" and (actual_source.parent / "pyproject.toml").is_file():
        checkout = actual_source.parent
        assert custody["binding_kind"] == "source-checkout"
        metadata = tomllib.loads((checkout / "pyproject.toml").read_text())["project"]
        assert re.sub(r"[-_.]+", "-", metadata["name"]).lower() == "template-literature-meta-analysis"
        assert metadata["version"] == "0.2.0"
        for filename in ("pyproject.toml", "uv.lock"):
            assert (
                custody["files"]["checkout/" + filename]
                == hashlib.sha256((checkout / filename).read_bytes()).hexdigest()
            )
    else:
        assert custody["binding_kind"] == "installed-distribution"
        assert not any(path.startswith("checkout/") for path in custody["files"])
        selected = importlib.metadata.distribution("template-literature-meta-analysis")
        assert selected.version == "0.2.0" and selected.files is not None
        records = [path for path in selected.files if str(path).endswith(".dist-info/RECORD")]
        assert len(records) == 1
        metadata = records[0].parent / "METADATA"
        installed = custody["distribution"]
        assert installed["name"] == "template-literature-meta-analysis" and installed["version"] == "0.2.0"
        for field, path in (("record_sha256", records[0]), ("metadata_sha256", metadata)):
            assert installed[field] == hashlib.sha256(Path(selected.locate_file(path)).read_bytes()).hexdigest()
        assert installed["public_python"] == custody["files"]
    if custody["distribution"] is not None:
        assert custody["distribution"]["version"] == "0.2.0"


def test_actual_engine_custody_rejects_corrupted_selected_binding(tmp_path):
    """Copy genuine selected records; prove admission before deliberately corrupting them."""
    import template_literature_meta_analysis as engine

    assert isinstance(engine.__file__, str)
    actual_source = Path(engine.__file__).absolute().parent
    checkout = actual_source.parent if actual_source.name == "src" else None
    fixture = tmp_path / "selected-engine"
    fixture.mkdir()
    if checkout is not None and (checkout / "pyproject.toml").is_file():
        copied_source = fixture / "src"
        shutil.copytree(actual_source, copied_source, ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"))
        for filename in ("pyproject.toml", "uv.lock"):
            shutil.copy2(checkout / filename, fixture / filename)
        bootstrap = (
            "import importlib.util\n"
            f"spec=importlib.util.spec_from_file_location('template_literature_meta_analysis', {str(copied_source / '__init__.py')!r},submodule_search_locations=[{str(copied_source)!r}])\n"
            "assert spec is not None and spec.loader is not None\n"
            "module=importlib.util.module_from_spec(spec)\n"
            "sys.modules[spec.name]=module\nspec.loader.exec_module(module)\n"
        )
        fault = fixture / "pyproject.toml"
        diagnostic = "dependency checkout package identity is inconsistent"
    else:
        selected = importlib.metadata.distribution("template-literature-meta-analysis")
        assert selected.version == "0.2.0" and selected.files is not None
        for relative in selected.files:
            # The real Meta wheel has only its package and metadata; no entrypoint or invented checkout.
            assert not relative.is_absolute() and ".." not in relative.parts
            source = Path(selected.locate_file(relative))
            if "__pycache__" in relative.parts and source.suffix == ".pyc":
                continue
            target = fixture / str(relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        copied_source = fixture / actual_source.name
        assert (copied_source / "__init__.py").is_file()
        bootstrap = f"sys.path.insert(0,{str(fixture)!r})\n"
        fault = copied_source / "literature/models.py"
        diagnostic = "differs from its declared RECORD"
    project = Path(__file__).resolve().parents[1]
    program = (
        "import sys,json\nimport infrastructure\n"
        + bootstrap
        + "from infrastructure.search.literature.live_contract import declared_dependency_custody\n"
        + f"from pathlib import Path\nprint(json.dumps(declared_dependency_custody(Path({str(project)!r}))))\n"
    )

    def invoke():
        return subprocess.run(
            [sys.executable, "-I", "-c", program], cwd=tmp_path, capture_output=True, text=True, timeout=60, check=False
        )

    admitted = invoke()
    assert admitted.returncode == 0, admitted.stdout + admitted.stderr
    assert json.loads(admitted.stdout)["template-literature-meta-analysis"]["binding_kind"] in {
        "source-checkout",
        "installed-distribution",
    }
    if fault.name == "pyproject.toml":
        original = fault.read_text()
        actual_name = tomllib.loads(original)["project"]["name"]
        assert re.sub(r"[-_.]+", "-", actual_name).lower() == "template-literature-meta-analysis"
        name_field = f'name = "{actual_name}"'
        assert original.count(name_field) == 1
        fault.write_text(original.replace(name_field, 'name = "wrong-provider"'))
    else:
        fault.write_bytes(fault.read_bytes() + b"\n# actual provider RECORD tamper control\n")
    rejected = invoke()
    assert rejected.returncode != 0 and diagnostic in rejected.stderr, rejected.stdout + rejected.stderr


@pytest.mark.parametrize("measured", [False, True])
def test_complete_manuscript_consumer_preserves_pending_and_measured_domain_scores(tmp_path, measured):
    import yaml

    from manuscript.variables import compute_variables

    config = {
        "project_config": {
            "search": {"term": "exoplanet atmosphere", "engines": {"crossref": True}},
            "subfield_keywords": {"atmospheres": ["spectrum"]},
            "hypothesis_definitions": {"H1": {"name": "Atmospheric spectra", "scope": "calibrated", "id": "H1"}},
        },
        "keywords": ["exoplanet", "spectra"],
    }
    (tmp_path / "manuscript").mkdir()
    (tmp_path / "manuscript/config.yaml").write_text(yaml.safe_dump(config))
    output = tmp_path / "output"
    data = output / "data"
    data.mkdir(parents=True)
    (data / "corpus.jsonl").write_text('{"title":"A"}\n{"title":"B"}\n')
    for name, value in ARTIFACTS.items():
        (data / name).write_text(json.dumps(value))
    (data / "hypothesis_scores.json").write_text('{"H1":{"score":0.5},"H2":-0.25}')
    if measured:
        (data / "assertion_summary.json").write_text(
            json.dumps(
                {
                    "total_assertions": 4,
                    "per_hypothesis": {"H1": {"supports": 2, "contradicts": 1, "neutral": 1}},
                    "type_counts": {"supports": 2, "contradicts": 1},
                }
            )
        )
        (data / "reproducibility_summary.json").write_text(
            json.dumps(
                {"mean_composite_score": 0.5, "n_papers_scored": 2, "n_low_score": 1, "low_score_threshold": 0.4}
            )
        )
        (data / "reproducibility_scores.json").write_text(
            json.dumps(
                {
                    "A": {"composite_score": 0.2, "content_score": 0.3, "structural_score": 0.1},
                    "B": {"composite_score": 0.8},
                }
            )
        )
    variables = compute_variables(output)
    assert variables["SEARCH_TERM"] == "exoplanet atmosphere"
    assert variables["RETRIEVED_CORPUS_SIZE"] == "2" and variables["ENGINE_LIST"] == "Crossref"
    assert variables["N_HYPOTHESES"] == "1"
    if measured:
        assert variables["H1_SCORE"] == "+0.50" and variables["H1_TOTAL"] == "4"
        assert "+0.50" in variables["HYPOTHESIS_TABLE"]
        assert variables["ASSERTION_SUPPORT_PCT"] == "66.7"
        assert variables["REPRO_MEAN_SCORE"] == "0.500"
        assert "| A | 0.200 |" in variables["REPRODUCIBILITY_TABLE"]
    else:
        assert "H1_SCORE" not in variables and "pending" in variables["HYPOTHESIS_TABLE"]
        assert variables["REPRO_MEAN_SCORE"] == "pending"

    (data / "corpus.jsonl").write_text('{"title":"A"}\n{"title":"B"}\n{"title":"C"}\n{"title":"D"}\n')
    (data / "phase_metadata.json").write_text(
        json.dumps({"total_papers": 1, "total_unique_papers": 1, "phases": {"one": {"papers_final": 1}}})
    )
    temporal = {**ARTIFACTS["temporal_analysis.json"], "year_counts": {"2020": 1, "2021": 1}, "total_papers": 2}
    (data / "temporal_analysis.json").write_text(json.dumps(temporal))
    scoped = compute_variables(output)
    assert scoped["RETRIEVED_CORPUS_SIZE"] == "4"
    assert scoped["ANALYZED_CORPUS_SIZE"] == "3"
    assert scoped["TEMPORAL_TOTAL_PAPERS"] == "2"
    assert scoped["PHASE_CORPUS_SIZE"] == "1"


def test_actual_crossref_and_repository_field_mapping_preserves_license_and_publication_kind():
    from defusedxml import ElementTree

    from literature.biorxiv_client import _parse_biorxiv_paper
    from literature.corpus import Corpus
    from literature.crossref_client import _parse_crossref_work
    from literature.europepmc_client import _parse_europepmc_result
    from literature.fulltext_assessment import assess_corpus
    from literature.pubmed_client import _parse_pubmed_article
    from literature.sovietrxiv_client import _parse_sovietrxiv_paper

    license_url = "https://creativecommons.org/licenses/by/4.0/"
    crossref = _parse_crossref_work(
        {
            "DOI": "10.1000/source",
            "title": ["Licensed source"],
            "issued": {"date-parts": [[2024]]},
            "author": [{"given": "Ada", "family": "Researcher"}],
            "license": [{"URL": license_url}],
        }
    )
    assert crossref.license_url == license_url and crossref.authors[0].name == "Ada Researcher"
    repository = _parse_europepmc_result({"doi": "10.1000/repository", "title": "Published source", "pubYear": "2024"})
    assert repository.is_preprint is False and repository.canonical_id == "doi:10.1000/repository"
    preprint = _parse_biorxiv_paper({"doi": "10.1000/preprint", "title": "Preprint", "date": "2024-01-01"}, "biorxiv")
    assert preprint.is_preprint and preprint.year == 2024
    translated = _parse_sovietrxiv_paper(
        {
            "title": "Translated source",
            "date": "2024-01-01",
            "source_url": "https://example.org/source",
            "english_pdf_url": "https://example.org/translation",
        }
    )
    assert translated.pdf_url == "https://example.org/translation"
    article = ElementTree.fromstring(
        "<PubmedArticle><MedlineCitation><PMID>123</PMID><Article>"
        "<ArticleTitle>Measured source</ArticleTitle></Article></MedlineCitation></PubmedArticle>"
    )
    assert _parse_pubmed_article(article).pmid == "123"
    report = assess_corpus(Corpus([crossref, repository, preprint]))
    assert report["total_papers"] == 3


def test_real_http_facade_and_disabled_fulltext_cli_are_bounded(tmp_path, httpserver, capsys):
    import requests

    from literature.fulltext_download import download_and_extract_fulltext
    from literature.fulltext_download_cli import main, parse_args
    from literature.http import request_with_retry

    httpserver.expect_request("/public").respond_with_json({"source": "bounded"})
    with requests.Session() as client:
        response = request_with_retry(client, "GET", httpserver.url_for("/public"), max_retries=0)
    assert response.json() == {"source": "bounded"}
    assert callable(download_and_extract_fulltext)
    (tmp_path / "manuscript").mkdir()
    config = tmp_path / "manuscript/config.yaml"
    config.write_text("project_config:\n  fulltext:\n    enabled: false\n")
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text("")
    assert parse_args(["--corpus", str(corpus)]).corpus == str(corpus)
    main(["--corpus", str(corpus), "--config", str(config)], project_root=tmp_path)
    assert capsys.readouterr().out.strip() == str(tmp_path / "output/fulltext")
    assert list((tmp_path / "output/fulltext").iterdir()) == []
    import argparse

    from literature.engine_dispatch import ENGINE_SPECS, engine_enabled

    assert len(ENGINE_SPECS) == 10
    assert (
        engine_enabled(ENGINE_SPECS[0], argparse.Namespace(), {"arxiv": False}, fast_api=False, url_injected=False)
        is False
    )


def _reference_corpus():
    from literature.corpus import Corpus
    from literature.models import Author, Paper

    return Corpus(
        [
            Paper(
                title="Transmission spectra",
                doi="10.1000/a",
                year=2024,
                authors=[Author("Ada Researcher")],
                abstract="Measured exoplanet atmosphere",
                full_text_source="publisher",
                citation_count=5,
            ),
            Paper(
                title="An independent calibration",
                arxiv_id="2401.00001",
                year=2023,
                authors=[Author("Bea Calibrator")],
                abstract="Calibration of telescope spectrum",
                references=["doi:10.1000/a"],
                full_text_source="arxiv",
            ),
            Paper(title="Missing metadata"),
        ]
    )


@pytest.mark.parametrize(
    "fraction,seed,identities",
    [
        (0.25, 0, ["doi:10.1000/a"]),
        (0.25, 42, ["title:5a151efc8d993fa2"]),
        (0.5, 0, ["doi:10.1000/a", "title:5a151efc8d993fa2"]),
        (0.5, 42, ["title:5a151efc8d993fa2", "arxiv:2401.00001"]),
        (1.0, 42, ["doi:10.1000/a", "arxiv:2401.00001", "title:5a151efc8d993fa2"]),
    ],
)
def test_retained_sampling_policy_matches_independent_reference(fraction, seed, identities):
    from literature.sampling import sample_papers

    # Gold selections were measured from the saved pre-consolidation domain
    # source, independently of this project's migrated engine facade.
    papers = _reference_corpus().papers
    selected = sample_papers(papers, fraction=fraction, seed=seed)
    assert [paper.canonical_id for paper in selected] == identities
    if fraction < 1:
        assert [
            paper.canonical_id for paper in sample_papers(list(reversed(papers)), fraction=fraction, seed=seed)
        ] == identities
    assert sample_papers([], fraction=fraction, seed=seed) == []


@pytest.mark.parametrize(
    "sampling",
    [
        {"fraction": False},
        {"fraction": "0.5"},
        {"fraction": 0},
        {"fraction": -0.1},
        {"fraction": 1.1},
        {"fraction": float("nan")},
        {"fraction": float("inf")},
        {"seed": True},
        {"seed": -1},
        {"seed": 1.5},
    ],
)
def test_sampling_rejects_invalid_runtime_controls(sampling):
    from literature.sampling import load_sampling_config

    with pytest.raises(ValueError, match="sampling"):
        load_sampling_config({"sampling": sampling})


def test_retained_evaluation_reports_real_missing_metadata_and_claims():
    from dataclasses import dataclass

    from literature.corpus import Corpus
    from literature.evaluation import evaluate_corpus
    from literature.sampling import load_sampling_config

    assert load_sampling_config({}) == (1.0, 42)
    assert load_sampling_config({"sampling": {"fraction": 0.5, "seed": 0}}) == (0.5, 0)
    empty = evaluate_corpus(Corpus())
    assert empty["total_papers"] == 0 and empty["metadata_completeness_mean"] == 0
    assert empty["claim_verification"] is None and empty["query_route"] is None

    @dataclass
    class Verdict:
        verdict: str
        confidence: float | None

    result = evaluate_corpus(
        _reference_corpus(),
        query="exoplanet systematic review",
        claim_verdicts=[
            {"verdict": "supported", "confidence": 0.8},
            Verdict("contradicted", 0.2),
            Verdict("unrecognized", None),
            {"verdict": None, "confidence": None},
        ],
    )
    assert result["total_papers"] == 3 and result["doi_count"] == 1 and result["preprint_count"] == 1
    assert result["metadata_completeness_mean"] == 3.33
    assert result["source_breakdown"] == {"publisher": 1, "arxiv": 1, "unknown": 1}
    assert result["query_route"]["source_order"] == [
        "crossref",
        "semantic_scholar",
        "openalex",
        "pubmed",
        "europepmc",
        "arxiv",
        "biorxiv",
        "sovietrxiv",
        "chinarxiv",
    ]
    assert result["claim_verification"] == {
        "count": 2,
        "supported": 1,
        "contradicted": 1,
        "insufficient": 0,
        "mean_confidence": 0.5,
    }
    assert evaluate_corpus(Corpus(), claim_verdicts=[Verdict("insufficient", None)])["claim_verification"] == {
        "count": 1,
        "supported": 0,
        "contradicted": 0,
        "insufficient": 1,
        "mean_confidence": 0.0,
    }


def test_manuscript_formatting_preserves_research_values():
    from manuscript.variables.formatters import humanize_key, humanize_list, latex_number, percentage

    assert [latex_number(number) for number in (0, 123, 1000, 1234567)] == ["0", "123", "1,000", "1,234,567"]
    assert [humanize_list(items) for items in ([], ["A"], ["A", "B"], ["A", "B", "C"])] == [
        "",
        "A",
        "A and B",
        "A, B, and C",
    ]
    assert humanize_key("quality_score") == "Quality Score"
    assert percentage(2 / 3) == "66.7"
