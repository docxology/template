"""Boundary tests for executable literature configuration validation."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from config_validation import (
    ConfigValidationError,
    check_config_health,
    require_valid_config,
    require_valid_search_config,
    validate_full_config,
    validate_fulltext_config,
    validate_hypothesis_config,
    validate_knowledge_graph_config,
    validate_llm_config,
    validate_reproducibility_config,
    validate_sampling_config,
    validate_search_config,
)
from literature.search_runner import run_literature_search


@pytest.mark.parametrize("payload", ["", "[]\n", "42\n", '"config"\n'])
def test_validate_full_config_reports_non_mapping_roots(tmp_path: Path, payload: str) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(payload, encoding="utf-8")

    issues = validate_full_config(config_path, categories=("search_config",))

    assert "file_errors" in issues
    assert "must be a mapping" in issues["file_errors"][0]


@pytest.mark.parametrize(
    "search",
    [
        {"term": "modafinil"},
        {"query": '"modafinil" OR "armodafinil"'},
    ],
)
def test_search_validation_accepts_term_or_query(search: dict[str, str]) -> None:
    assert validate_search_config({"project_config": {"search": search}}) == []


def test_search_validation_rejects_boolean_numeric_values() -> None:
    issues = validate_search_config(
        {
            "project_config": {
                "search": {
                    "query": "modafinil",
                    "start_year": True,
                    "max_results": False,
                }
            }
        }
    )
    assert any("start_year" in issue for issue in issues)
    assert any("max_results" in issue for issue in issues)


def test_search_validation_supports_top_level_compatibility_shape() -> None:
    assert validate_search_config({"search": {"query": "modafinil"}}) == []


def test_require_valid_config_raises_with_structured_category(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "project_config:\n  sampling:\n    fraction: 2\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigValidationError, match="sampling_config"):
        require_valid_config(config_path, categories=("sampling_config",))


def test_search_runner_validates_before_creating_outputs(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text(
        "project_config:\n  search:\n    max_results: 0\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "output"
    args = argparse.Namespace(
        query=None,
        max_results=10,
        output_dir=str(output_dir),
        skip_arxiv=True,
        skip_s2=True,
        skip_openalex=True,
        skip_crossref=True,
        skip_pubmed=True,
        skip_sovietrxiv=True,
        skip_chinarxiv=True,
        skip_europepmc=True,
        skip_biorxiv=True,
        resume=False,
        clear_corpus=False,
        start_year=None,
        config=str(config_path),
    )

    with pytest.raises(ConfigValidationError, match="search_config"):
        run_literature_search(args, project_root=tmp_path)

    assert not output_dir.exists()


def test_search_runner_accepts_cli_query_when_config_has_no_target(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "project_config:\n  search:\n    resume: false\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "output"
    args = argparse.Namespace(
        query="modafinil",
        max_results=10,
        output_dir=str(output_dir),
        skip_arxiv=True,
        skip_s2=True,
        skip_openalex=True,
        skip_crossref=True,
        skip_pubmed=True,
        skip_sovietrxiv=True,
        skip_chinarxiv=True,
        skip_europepmc=True,
        skip_biorxiv=True,
        resume=False,
        clear_corpus=False,
        start_year=None,
        config=str(config_path),
    )

    path = run_literature_search(args, project_root=tmp_path)

    assert path.exists()


def _search(**search: object) -> dict[str, object]:
    """Build a project_config.search mapping for validator tests."""
    return {"project_config": {"search": dict(search)}}


def test_search_must_be_mapping() -> None:
    issues = validate_search_config({"project_config": {"search": "modafinil"}})
    assert issues == ["project_config.search must be a mapping"]


def test_search_engines_non_mapping() -> None:
    issues = validate_search_config(_search(query="modafinil", engines=["arxiv"]))
    assert "must be a mapping of engine names" in issues[0]


def test_search_engines_non_boolean_toggle() -> None:
    issues = validate_search_config(_search(query="modafinil", engines={"arxiv": "yes"}))
    assert "Search engine toggles must be boolean: arxiv" in issues[0]


def test_search_all_engines_disabled() -> None:
    issues = validate_search_config(_search(query="modafinil", engines={"arxiv": False, "pubmed": False}))
    assert "All configured search engines are disabled" in issues[0]


@pytest.mark.parametrize("name", ["resume", "clear_corpus"])
def test_search_boolean_flags_reject_non_boolean(name: str) -> None:
    issues = validate_search_config(_search(query="modafinil", **{name: "yes"}))
    assert f"Invalid search.{name}" in issues[0]


@pytest.mark.parametrize("name", ["arxiv_queries", "relevance_keywords"])
def test_search_list_fields_reject_non_string_lists(name: str) -> None:
    issues = validate_search_config(_search(query="modafinil", **{name: [1, 2]}))
    assert f"Invalid search.{name}" in issues[0]


def test_hypothesis_config_requires_mapping() -> None:
    issues = validate_hypothesis_config({"project_config": {"hypothesis_definitions": []}})
    assert "No hypothesis definitions configured" in issues[0]


def test_hypothesis_entry_must_be_mapping() -> None:
    issues = validate_hypothesis_config({"project_config": {"hypothesis_definitions": {"H1": "a string"}}})
    assert "Hypothesis H1: must be a mapping" in issues[0]


def test_hypothesis_entry_missing_required_fields() -> None:
    issues = validate_hypothesis_config({"project_config": {"hypothesis_definitions": {"H1": {"name": "x"}}}})
    assert any("missing required field 'description'" in m for m in issues)


def test_sampling_must_be_mapping() -> None:
    issues = validate_sampling_config({"project_config": {"sampling": 3}})
    assert "project_config.sampling must be a mapping" in issues[0]


def test_sampling_invalid_seed() -> None:
    issues = validate_sampling_config({"project_config": {"sampling": {"fraction": 0.5, "seed": -1}}})
    assert "Invalid sampling.seed" in issues[0]


def test_llm_config_must_be_mapping() -> None:
    issues = validate_llm_config({"llm_extraction": "gemma"})
    assert "project_config.llm_extraction must be a mapping" in issues[0]


@pytest.mark.parametrize("name", ["model", "base_url"])
def test_llm_string_fields_reject_empty(name: str) -> None:
    issues = validate_llm_config({"llm_extraction": {name: "  "}})
    assert f"Invalid llm_extraction.{name}" in issues[0]


def test_llm_numeric_bounds() -> None:
    issues = validate_llm_config({"llm_extraction": {"temperature": -1, "timeout_seconds": 0, "min_confidence": 2}})
    assert any("Invalid llm_extraction.temperature" in m for m in issues)
    assert any("Invalid llm_extraction.timeout_seconds" in m for m in issues)
    assert any("Invalid llm_extraction.min_confidence" in m for m in issues)


def test_llm_numeric_non_number() -> None:
    issues = validate_llm_config({"llm_extraction": {"min_confidence": "high"}})
    assert "must be numeric" in issues[0]


def test_llm_count_fields_reject_non_positive_int() -> None:
    issues = validate_llm_config({"llm_extraction": {"max_tokens": 0, "max_retries": -2}})
    assert any("Invalid llm_extraction.max_tokens" in m for m in issues)
    assert any("Invalid llm_extraction.max_retries" in m for m in issues)


def test_knowledge_graph_must_be_mapping() -> None:
    issues = validate_knowledge_graph_config({"knowledge_graph": "off"})
    assert "project_config.knowledge_graph must be a mapping" in issues[0]


def test_reproducibility_must_be_mapping() -> None:
    issues = validate_reproducibility_config({"reproducibility_assessment": ["off"]})
    assert "project_config.reproducibility_assessment must be a mapping" in issues[0]


def test_reproducibility_score_threshold_bound() -> None:
    issues = validate_reproducibility_config({"reproducibility_assessment": {"low_score_threshold": 1.5}})
    assert "Invalid reproducibility_assessment.low_score_threshold" in issues[0]


def test_reproducibility_llm_string_fields() -> None:
    issues = validate_reproducibility_config({"reproducibility_assessment": {"llm_model": "", "llm_url": "  "}})
    assert any("must be a non-empty string" in m for m in issues)


def test_reproducibility_llm_temperature_timeout() -> None:
    issues = validate_reproducibility_config(
        {
            "reproducibility_assessment": {
                "llm_temperature": 3.0,
                "llm_timeout": -1,
            }
        }
    )
    assert any("llm_temperature" in m for m in issues)
    assert any("llm_timeout" in m for m in issues)


def test_reproducibility_llm_count_fields() -> None:
    issues = validate_reproducibility_config(
        {"reproducibility_assessment": {"llm_max_tokens": 0, "llm_max_retries": 0}}
    )
    assert any("llm_max_tokens" in m for m in issues)
    assert any("llm_max_retries" in m for m in issues)


def test_reproducibility_weights_non_mapping() -> None:
    issues = validate_reproducibility_config({"reproducibility_assessment": {"content_weights": [1, 2]}})
    assert "reproducibility_assessment.content_weights must be a mapping" in issues[0]


def test_reproducibility_weights_invalid_and_zero_total() -> None:
    issues = validate_reproducibility_config(
        {
            "reproducibility_assessment": {
                "content_weights": {"sources": -1, "methods": 2},
                "structural_weights": {"cohesion": 0, "path_coverage": 0},
            }
        }
    )
    assert any("content_weights has invalid weights" in m for m in issues)
    assert any("structural_weights must have a positive total weight" in m for m in issues)


@pytest.mark.parametrize(
    ("key", "value", "match"),
    [
        ("checkpoint_interval", 0, "checkpoint_interval"),
        ("max_papers", -3, "max_papers"),
        ("clear_assertions", "yes", "clear_assertions"),
    ],
)
def test_orchestration_config_errors(key: str, value: object, match: str) -> None:
    issues = validate_knowledge_graph_config({"knowledge_graph": {key: value}})
    assert any(match in m for m in issues)


def test_fulltext_boolean_and_string_fields() -> None:
    issues = validate_fulltext_config(
        {
            "fulltext": {
                "enabled": "yes",
                "unpaywall_email": 7,
                "download_dir": "  ",
            }
        }
    )
    assert any("fulltext.enabled" in m for m in issues)
    assert any("fulltext.unpaywall_email" in m for m in issues)
    assert any("fulltext.download_dir" in m for m in issues)


def test_load_config_oserror(tmp_path: Path) -> None:
    """A directory path raises an OSError-family exception at open time."""
    issues = validate_full_config(tmp_path, categories=("search_config",))
    assert "file_errors" in issues


def test_load_config_yaml_error(tmp_path: Path) -> None:
    config_path = tmp_path / "bad.yaml"
    config_path.write_text("project_config: [unclosed\n", encoding="utf-8")
    issues = validate_full_config(config_path, categories=("search_config",))
    assert "file_errors" in issues


def test_load_config_project_config_must_be_mapping(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("project_config: 'not-a-mapping'\n", encoding="utf-8")
    issues = validate_full_config(config_path, categories=("search_config",))
    assert "file_errors" in issues
    assert issues["file_errors"][0] == "project_config must be a mapping"


def test_validate_full_config_unknown_category(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("project_config:\n  search:\n    term: modafinil\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Unknown config validation categories"):
        validate_full_config(config_path, categories=("nope",))


def test_require_valid_search_config_raises_on_override_free_invalid(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "project_config:\n  search:\n    max_results: 0\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigValidationError, match="search_config"):
        require_valid_search_config(config_path)


def test_require_valid_search_config_override_bypasses_missing_term(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("project_config:\n  search:\n    resume: false\n", encoding="utf-8")
    # Override supplies the missing term so validation passes.
    assert require_valid_search_config(config_path, query_override="modafinil") is None


def test_check_config_health_valid_and_invalid(tmp_path: Path) -> None:
    # check_config_health validates ALL categories, so the "good" fixture must
    # carry hypothesis definitions as well as a search term.
    good = tmp_path / "good.yaml"
    good.write_text(
        "project_config:\n"
        "  search:\n"
        "    term: modafinil\n"
        "  hypothesis_definitions:\n"
        "    H1:\n"
        "      name: efficacy\n"
        "      description: tested\n"
        "      scope: clinical\n",
        encoding="utf-8",
    )
    assert check_config_health(good) is True

    bad = tmp_path / "bad.yaml"
    bad.write_text("project_config:\n  search:\n    max_results: 0\n", encoding="utf-8")
    assert check_config_health(bad) is False
