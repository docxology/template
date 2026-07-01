"""Tests for src.manuscript_variables."""

from __future__ import annotations

import json
from pathlib import Path

from src.config import DeepSearchConfig
from src.manuscript_variables import (
    compute_variables,
    load_aggregate_payload,
    load_search_result_payload,
    substitute_in_text,
    write_resolved_manuscript_tree,
    write_variables,
)


def _payload(papers: list[dict] | None = None, errors: dict | None = None):
    return {
        "query": {"text": "x", "year_min": 2010, "year_max": None},
        "papers": papers or [],
        "per_source_counts": {"local": len(papers or [])},
        "errors": errors or {},
    }


def _deep() -> DeepSearchConfig:
    return DeepSearchConfig(
        enabled=True,
        keywords=["a", "b"],
        max_results_per_keyword=7,
        sources=["arxiv", "local"],
    )


def test_compute_variables_basic_counts():
    payload = _payload(
        papers=[
            {"title": "A", "abstract": "abs", "doi": "10.1/x"},
            {"title": "B", "abstract": "abs"},
            {"title": "C"},
        ]
    )
    vars_ = compute_variables(
        config_query="topic",
        config_max_results=10,
        config_sources=["local"],
        search_result_payload=payload,
    )
    assert vars_.result_num_papers == 3
    assert vars_.result_with_abstract == 2
    assert vars_.result_with_doi == 1
    assert vars_.result_num_sources == 1
    assert "local=3" in vars_.result_per_source
    assert vars_.deep_max_results_per_keyword == 10
    assert vars_.deep_keyword_count == 0
    assert vars_.deep_unique_papers == "<deep-search not run>"


def test_compute_variables_deep_and_aggregate():
    agg = {"unique_papers": [{"id": "1"}, {"id": "2"}]}
    vars_ = compute_variables(
        config_query="q",
        config_max_results=12,
        config_sources=["local"],
        search_result_payload=_payload(),
        deep_search=_deep(),
        aggregate_payload=agg,
    )
    assert vars_.deep_max_results_per_keyword == 7
    assert vars_.deep_keyword_count == 2
    assert "a" in vars_.deep_keywords_joined
    assert vars_.deep_sources == "arxiv, local"
    assert vars_.deep_unique_papers == "2"


def test_compute_variables_year_filter_strings():
    payload = _payload()
    vars_ = compute_variables(
        config_query="x",
        config_max_results=5,
        config_sources=["arxiv"],
        search_result_payload=payload,
    )
    assert vars_.result_year_min == "2010"
    assert vars_.result_year_max == "—"


def test_compute_variables_errors_serialized():
    payload = _payload(errors={"crossref": "HTTP 503"})
    vars_ = compute_variables(
        config_query="x",
        config_max_results=5,
        config_sources=[],
        search_result_payload=payload,
    )
    assert "crossref" in vars_.result_errors
    assert "HTTP 503" in vars_.result_errors


def test_compute_variables_no_errors_says_none():
    vars_ = compute_variables(
        config_query="x",
        config_max_results=5,
        config_sources=[],
        search_result_payload=_payload(),
    )
    assert vars_.result_errors == "none"


def test_uppercase_keys_format():
    vars_ = compute_variables(
        config_query="x",
        config_max_results=5,
        config_sources=["local"],
        search_result_payload=_payload(),
    )
    upper = vars_.as_uppercase_keys()
    assert "{{CONFIG_QUERY}}" in upper
    assert "{{RESULT_NUM_PAPERS}}" in upper
    assert "{{DEEP_MAX_RESULTS_PER_KEYWORD}}" in upper
    assert upper["{{CONFIG_QUERY}}"] == "x"


def test_substitute_in_text():
    vars_ = compute_variables(
        config_query="my topic",
        config_max_results=5,
        config_sources=["local"],
        search_result_payload=_payload(papers=[{"title": "P"}]),
        deep_search=_deep(),
        aggregate_payload={"unique_papers": [{}]},
    )
    template = (
        "Query: {{CONFIG_QUERY}}, Found {{RESULT_NUM_PAPERS}} papers. "
        "Deep cap {{DEEP_MAX_RESULTS_PER_KEYWORD}}, unique {{DEEP_UNIQUE_PAPERS}}."
    )
    out = substitute_in_text(template, vars_)
    assert "my topic" in out
    assert "1 papers" in out
    assert "7" in out
    assert "1" in out.split("unique")[-1]


def test_substitute_leaves_unmatched_markers(tmp_path: Path):
    vars_ = compute_variables(
        config_query="x",
        config_max_results=5,
        config_sources=[],
        search_result_payload=_payload(),
    )
    out = substitute_in_text("{{NOT_A_VAR}} stays", vars_)
    assert "{{NOT_A_VAR}}" in out


def test_write_variables_round_trip(tmp_path: Path):
    vars_ = compute_variables(
        config_query="x",
        config_max_results=5,
        config_sources=["local"],
        search_result_payload=_payload(),
    )
    path = write_variables(vars_, tmp_path / "vars.json")
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["config_query"] == "x"


def test_load_search_result_payload(tmp_path: Path):
    src = tmp_path / "r.json"
    src.write_text(json.dumps(_payload()), encoding="utf-8")
    payload = load_search_result_payload(src)
    assert payload["query"]["text"] == "x"


def test_load_aggregate_payload_missing_returns_none(tmp_path: Path):
    assert load_aggregate_payload(tmp_path / "nope.json") is None


def test_write_resolved_manuscript_tree(tmp_path: Path):
    root = tmp_path / "proj"
    mdir = root / "manuscript"
    mdir.mkdir(parents=True)
    (mdir / "config.yaml").write_text("paper:\n  title: T\nsearch:\n  query: x\n", encoding="utf-8")
    (mdir / "references.bib").write_text("@article{a,\n title={t}\n}\n", encoding="utf-8")
    (mdir / "00_test.md").write_text("# Hi {{CONFIG_QUERY}} {{DEEP_UNIQUE_PAPERS}}\n", encoding="utf-8")

    vars_ = compute_variables(
        config_query="CQ",
        config_max_results=3,
        config_sources=["arxiv"],
        search_result_payload=_payload(),
        deep_search=_deep(),
        aggregate_payload={"unique_papers": [{"id": "1"}]},
    )
    out_dir = write_resolved_manuscript_tree(root, vars_)
    assert out_dir == root / "output" / "manuscript"
    resolved = (out_dir / "00_test.md").read_text(encoding="utf-8")
    assert "{{" not in resolved
    assert "CQ" in resolved
    assert (out_dir / "references.bib").exists()
    assert (out_dir / "config.yaml").exists()


def test_load_aggregate_payload_non_dict_returns_none(tmp_path: Path):
    p = tmp_path / "a.json"
    p.write_text("[1,2]", encoding="utf-8")
    assert load_aggregate_payload(p) is None


def test_compute_variables_aggregate_unique_papers_not_list():
    vars_ = compute_variables(
        config_query="q",
        config_max_results=1,
        config_sources=[],
        search_result_payload=_payload(),
        aggregate_payload={"unique_papers": "broken"},
    )
    assert vars_.deep_unique_papers == "<deep-search not run>"


def test_write_resolved_manuscript_tree_without_config_yaml(tmp_path: Path):
    root = tmp_path / "proj"
    mdir = root / "manuscript"
    mdir.mkdir(parents=True)
    (mdir / "x.md").write_text("{{CONFIG_QUERY}}\n", encoding="utf-8")
    vars_ = compute_variables(
        config_query="ok",
        config_max_results=1,
        config_sources=[],
        search_result_payload=_payload(),
    )
    write_resolved_manuscript_tree(root, vars_)
    assert (root / "output" / "manuscript" / "x.md").read_text(encoding="utf-8") == "ok\n"
