"""Regression tests for advanced-project evidence and fixture extensions."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT_ROOT = PROJECT_ROOT / "manuscript"


def test_fixture_corpus_is_deterministic_and_reserved() -> None:
    from literature.fixture_corpus import build_synthetic_corpus

    first = build_synthetic_corpus(n=5, seed=11)
    second = build_synthetic_corpus(n=5, seed=11)
    assert [paper.to_dict() for paper in first.papers] == [paper.to_dict() for paper in second.papers]
    assert all(paper.doi.startswith("10.5555/") for paper in first.papers)
    assert all("exoplanet" in paper.title.lower() for paper in first.papers)


def test_public_metadata_uses_pipeline_exemplar_framing() -> None:
    config = (MANUSCRIPT_ROOT / "config.yaml").read_text(encoding="utf-8")
    citation = (PROJECT_ROOT / "CITATION.cff").read_text(encoding="utf-8")
    codemeta = (PROJECT_ROOT / "codemeta.json").read_text(encoding="utf-8")
    zenodo = (PROJECT_ROOT / ".zenodo.json").read_text(encoding="utf-8")
    software_title = "A Reproducible Multi-Phase Literature-Review Pipeline for Exoplanet Atmospheres"
    manuscript_title = "A Reproducible Multi-Phase Literature-Review Pipeline for Exoplanet Atmospheres"

    assert manuscript_title in config
    assert software_title in citation
    assert software_title in json.loads(codemeta)["name"]
    assert software_title in json.loads(zenodo)["title"]
    assert 'doi_status: "forthcoming"' in config or "doi_status: forthcoming" in config


def test_manuscript_has_no_cross_domain_or_fixture_status_regressions() -> None:
    manuscript = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(MANUSCRIPT_ROOT.glob("*.md"))
        if path.name not in {"AGENTS.md", "README.md", "SYNTAX.md"}
    ).lower()

    assert "biomedical literature growth" not in manuscript
    assert "primary efficacy" not in manuscript
    assert "optimal performance" not in manuscript
    assert "mechanistic basis" not in manuscript
    assert "process model" not in manuscript
    assert "as in this instance" not in manuscript
    assert "unprecedented" not in manuscript


def test_hypothesis_results_are_configuration_driven() -> None:
    results = (MANUSCRIPT_ROOT / "03f_results_multi_phase.md").read_text(encoding="utf-8")
    config = (MANUSCRIPT_ROOT / "config.yaml").read_text(encoding="utf-8")

    assert "{{HYPOTHESIS_TABLE}}" in results
    assert "PRIMARY_EFFICACY_SCORE" not in results
    assert "JWST Atmospheric Characterization" in config
    assert 'id: "JWST_CHARACTERIZATION"' in config
    assert "Molecular Diversity Detection" in config
    assert "hypothesis_definitions:" in config
    assert "H1:" in config
    assert "PRIMARY_EFFICACY" not in config


def test_unmeasured_hypothesis_scores_render_as_pending(tmp_path: Path) -> None:
    from manuscript.variables.context import ExtractContext
    from manuscript.variables.extractors.hypotheses import extract_hypotheses

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "assertion_summary.json").write_text(
        json.dumps({"total_assertions": 0, "per_hypothesis": {}}), encoding="utf-8"
    )
    (data_dir / "hypothesis_scores.json").write_text(json.dumps({"JWST_CHARACTERIZATION": 0.0}), encoding="utf-8")
    config = {
        "project_config": {
            "hypothesis_definitions": {
                "H1": {
                    "id": "JWST_CHARACTERIZATION",
                    "name": "JWST Atmospheric Characterization",
                    "scope": "observational",
                }
            }
        }
    }
    ctx = ExtractContext(tmp_path, data_dir, tmp_path, config, 0)

    variables = extract_hypotheses(ctx)

    assert variables["HYPOTHESIS_TABLE"].endswith("| pending |")
    assert "JWST_CHARACTERIZATION_SCORE" not in variables


def test_reproducibility_results_aliases_are_populated_from_summary(tmp_path: Path) -> None:
    from manuscript.variables.context import ExtractContext
    from manuscript.variables.extractors.reproducibility import extract_reproducibility

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "reproducibility_summary.json").write_text(
        json.dumps({"mean_composite_score": 0.625, "n_papers_scored": 2}), encoding="utf-8"
    )
    (data_dir / "reproducibility_scores.json").write_text("{}", encoding="utf-8")
    ctx = ExtractContext(tmp_path, data_dir, tmp_path, {}, 0)

    variables = extract_reproducibility(ctx)

    assert variables["REPRO_MEAN_SCORE"] == "0.625"
    assert variables["REPRO_PAPERS_SCORED"] == "2"


def test_manuscript_citations_resolve_to_bibliography() -> None:
    citation_keys = {
        key
        for path in MANUSCRIPT_ROOT.glob("*.md")
        if path.name not in {"AGENTS.md", "README.md", "SYNTAX.md"}
        for key in re.findall(r"\[@([A-Za-z0-9_:-]+)\]", path.read_text(encoding="utf-8"))
    }
    bibliography = (MANUSCRIPT_ROOT / "references.bib").read_text(encoding="utf-8")
    bibliography_keys = set(re.findall(r"^@[A-Za-z]+\{([^,]+),", bibliography, flags=re.MULTILINE))

    assert citation_keys <= bibliography_keys
    assert "friston2010free" not in bibliography_keys


def test_fixture_honesty_detects_empirical_language(tmp_path: Path) -> None:
    from literature.fixture_honesty import (
        validate_fixture_honesty,
        validate_negative_control,
    )

    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "claim.md").write_text(
        "We found a universal effect in the exoplanet atmospheres literature.\n", encoding="utf-8"
    )
    findings = validate_fixture_honesty(manuscript, search_term="exoplanet atmospheres")
    assert len(findings) >= 2
    assert validate_negative_control()


def test_fixture_honesty_handles_safe_lines_and_extra_paths(tmp_path: Path) -> None:
    from literature.fixture_honesty import validate_fixture_honesty

    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    safe = manuscript / "safe.md"
    safe.write_text("# We found a heading\n{{SEARCH_TERM}} is a configured topic.\n", encoding="utf-8")
    missing = manuscript / "missing.md"
    assert validate_fixture_honesty(manuscript, extra_paths=[missing, safe]) == []


def test_advanced_variables_use_recorded_artifacts(tmp_path: Path) -> None:
    from manuscript.variables.advanced import extract_multi_phase_variables

    (tmp_path / "phase_metadata.json").write_text(
        json.dumps(
            {
                "phases": {"one": {"name": "Foundation", "papers_final": 3, "queries_executed": ["q"]}},
                "total_unique_papers": 3,
                "phase_overlap": {"one": {"two": {"jaccard_similarity": 0.5}}},
                "citation_validation": {"one": {"citation_rate": 0.25}},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "corpus.jsonl").write_text(
        "\n".join(
            [
                json.dumps({"year": 2020, "abstract": "a", "doi": "10.5555/a", "pdf_url": "x", "is_open_access": True}),
                json.dumps({"year": 2022, "abstract": "", "doi": None, "is_open_access": False}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "reproducibility_summary.json").write_text(
        json.dumps({"n_papers_scored": 2, "mean_composite_score": 0.625}),
        encoding="utf-8",
    )
    variables = extract_multi_phase_variables(
        tmp_path,
        {
            "project_config": {"search": {"term": "exoplanet atmospheres", "engines": {"arxiv": True}}},
            "keywords": ["spectra", "retrieval"],
        },
    )
    assert variables["CORPUS_SIZE"] == "3"
    assert variables["ABSTRACT_COVERAGE_PCT"] == "50.0"
    assert variables["YEAR_SPAN"] == "2"
    assert variables["ENGINE_LIST"] == "arXiv"
    assert variables["REPRO_PAPERS_SCORED"] == "2"
    assert variables["REPRO_MEAN_SCORE"] == "0.625"
    assert variables["LLM_FILTER_PRECISION"] == "pending"


def test_deep_research_fixture_replay_is_provider_neutral(tmp_path: Path) -> None:
    from deep_research.dispatch import (
        PROVIDER_CATALOGUE,
        default_fixture_path,
        dispatch_offline_replay,
    )

    replay = dispatch_offline_replay("exoplanet atmospheres", tmp_path)
    assert replay.request.query == "exoplanet atmospheres"
    assert default_fixture_path().is_file()
    assert set(replay.provider_profile["catalogue"]) == set(PROVIDER_CATALOGUE)
    assert replay.result.status == "completed"
    assert len(replay.result.citations) > 0


def test_deep_research_fixture_missing_path_fails_closed(tmp_path: Path) -> None:
    from deep_research.dispatch import dispatch_offline_replay

    with pytest.raises(FileNotFoundError):
        dispatch_offline_replay(
            "exoplanet atmospheres",
            tmp_path,
            fixture_path=tmp_path / "missing.json",
        )


def test_advanced_variables_handle_empty_and_optional_artifacts(tmp_path: Path) -> None:
    from manuscript.variables.advanced import extract_multi_phase_variables

    variables = extract_multi_phase_variables(tmp_path)
    assert variables["YEAR_START"] == "pending"
    assert variables["ENGINE_LIST"] == "none configured"
    assert variables["SEARCH_TERM"] == "the configured topic"


def test_advanced_variables_skip_malformed_optional_records(tmp_path: Path) -> None:
    from manuscript.variables.advanced import extract_multi_phase_variables

    (tmp_path / "phase_metadata.json").write_text(
        json.dumps(
            {
                "phases": {"bad": "not a mapping"},
                "phase_overlap": {"bad": "not a mapping"},
                "citation_validation": {"bad": "not a mapping"},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "corpus.jsonl").write_text("\n[]\n", encoding="utf-8")
    (tmp_path / "citation_network.json").write_text(json.dumps({"num_edges": 2}), encoding="utf-8")
    variables = extract_multi_phase_variables(tmp_path)
    assert variables["TOTAL_PHASES"] == "1"
    assert variables["CITATION_EDGES"] == "2"
    assert "CITATION_NODES" not in variables


def test_search_configuration_validator_covers_scalar_and_list_boundaries() -> None:
    from config_validation import validate_search_config

    base = {"project_config": {"search": {"term": "topic", "engines": {"arxiv": True}}}}
    invalid = {
        "project_config": {
            "search": {
                "term": "topic",
                "max_results": 0,
                "resume": "yes",
                "arxiv_queries": [""],
                "relevance_keywords": "keyword",
                "start_year": 1700,
            }
        }
    }
    assert validate_search_config(base) == []
    assert len(validate_search_config(invalid)) == 5
    assert validate_search_config({"project_config": {"search": {}}}, query_override="override") == []


def test_full_configuration_validator_reports_all_optional_sections(tmp_path: Path) -> None:
    from config_validation import validate_full_config

    config = {
        "project_config": {
            "hypothesis_definitions": {"H": "not a mapping"},
            "sampling": "bad",
            "knowledge_graph": {"checkpoint_interval": 0, "max_papers": -1, "clear_assertions": "yes"},
            "reproducibility_assessment": {
                "checkpoint_interval": 0,
                "max_papers": -1,
                "clear_workflow_graphs": "yes",
                "content_weights": {},
                "structural_weights": "bad",
                "low_score_threshold": 2,
                "fuzzy_quote_threshold": -1,
                "llm_model": "",
                "llm_url": 1,
                "llm_temperature": 3,
                "llm_timeout": 0,
                "llm_max_tokens": 0,
                "llm_max_retries": 0,
            },
            "fulltext": {"enabled": "yes", "unpaywall_email": 2, "download_dir": ""},
        },
    }
    path = tmp_path / "config.yaml"
    import yaml

    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    result = validate_full_config(path)
    assert {
        "hypothesis_config",
        "sampling_config",
        "knowledge_graph_config",
        "reproducibility_config",
        "fulltext_config",
    } <= set(result)


def test_configuration_file_boundary_and_require_helpers(tmp_path: Path) -> None:
    from config_validation import (
        ConfigValidationError,
        check_config_health,
        require_valid_config,
        require_valid_search_config,
        validate_full_config,
    )

    missing = tmp_path / "missing.yaml"
    assert "file_errors" in validate_full_config(missing)
    with pytest.raises(ConfigValidationError):
        require_valid_search_config(missing)
    malformed = tmp_path / "malformed.yaml"
    malformed.write_text("project_config: [bad", encoding="utf-8")
    assert "file_errors" in validate_full_config(malformed)
    valid = tmp_path / "valid.yaml"
    valid.write_text(
        "project_config:\n"
        "  search:\n"
        "    term: topic\n"
        "  hypothesis_definitions:\n"
        "    H:\n"
        "      name: Hypothesis\n"
        "      description: Description\n"
        "      scope: Scope\n",
        encoding="utf-8",
    )
    require_valid_search_config(valid)
    require_valid_search_config(valid, query_override="override")
    require_valid_config(valid, categories=["search_config"])
    assert check_config_health(valid)
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("project_config:\n  search: 7\n", encoding="utf-8")
    assert not check_config_health(invalid)
    non_mapping = tmp_path / "scalar.yaml"
    non_mapping.write_text("7\n", encoding="utf-8")
    assert "file_errors" in validate_full_config(non_mapping)
    project_non_mapping = tmp_path / "project-scalar.yaml"
    project_non_mapping.write_text("project_config: 7\n", encoding="utf-8")
    assert "file_errors" in validate_full_config(project_non_mapping)
    with pytest.raises(ValueError, match="Unknown"):
        validate_full_config(valid, categories=["unknown"])


@pytest.mark.parametrize(
    ("category", "config"),
    [
        ("knowledge_graph_config", {"project_config": {"knowledge_graph": {"max_papers": -1}}}),
        ("reproducibility_config", {"project_config": {"reproducibility_assessment": {"low_score_threshold": 2}}}),
        ("fulltext_config", {"project_config": {"fulltext": {"enabled": "yes"}}}),
        ("llm_config", {"project_config": {"llm_extraction": {"temperature": 3}}}),
    ],
)
def test_optional_configuration_validators_report_invalid_values(category: str, config: dict) -> None:
    result = validate_full_config_from_mapping(category, config)
    assert result


def validate_full_config_from_mapping(category: str, config: dict) -> list[str]:
    """Write a real config file so the loader boundary is exercised too."""
    import tempfile

    import yaml

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as handle:
        yaml.safe_dump(config, handle)
        handle.flush()
        from config_validation import validate_full_config

        return validate_full_config(Path(handle.name), categories=[category]).get(category, [])
