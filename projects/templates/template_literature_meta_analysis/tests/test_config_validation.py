"""Boundary tests for executable literature configuration validation."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from config_validation import (
    ConfigValidationError,
    require_valid_config,
    validate_full_config,
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
