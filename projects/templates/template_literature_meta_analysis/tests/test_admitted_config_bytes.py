"""Actual config/validation/hypothesis/classification custody without pathname rereads."""

import argparse
import json
from pathlib import Path

import pytest
import yaml

from template_literature_meta_analysis.analysis.pipeline_runner import run_meta_analysis_pipeline
from template_literature_meta_analysis.analysis.subfield_classifier import classify_corpus
from template_literature_meta_analysis.config_loader import _load_yaml, load_project_config
from template_literature_meta_analysis.config_validation import validate_full_config
from template_literature_meta_analysis.knowledge_graph.hypothesis import load_hypotheses_from_config
from template_literature_meta_analysis.literature.models import Paper


@pytest.mark.parametrize("raw", [b"", b"[]", b"project_config: {}\n", b"project_config: [\n"])
def test_actual_meta_parser_value_and_error_parity(tmp_path: Path, raw: bytes):
    path = tmp_path / "config.yaml"
    path.write_bytes(raw)
    assert validate_full_config(path) == validate_full_config(path, source_bytes=raw)
    if raw.endswith(b"[\n"):
        with pytest.raises(yaml.YAMLError) as expected:
            _load_yaml(path)
        with pytest.raises(yaml.YAMLError) as actual:
            _load_yaml(path, source_bytes=raw)
        assert str(actual.value) == str(expected.value)
    else:
        assert _load_yaml(path) == _load_yaml(path, source_bytes=raw)
        assert load_project_config(path) == load_project_config(path, source_bytes=raw)


@pytest.mark.parametrize("restore", [False, True], ids=["lasting", "aba"])
def test_all_configured_domain_consumers_use_the_same_admitted_bytes(tmp_path: Path, restore):
    path = tmp_path / "config.yaml"
    raw = yaml.safe_dump(
        {
            "project_config": {
                "search": {"query": "admitted", "max_results": 3},
                "hypothesis_definitions": {"H1": {"id": "ADMITTED", "name": "Admitted", "description": "Original"}},
                "subfield_keywords": {"B_admitted": ["spectrum"], "A2_other": ["catchall"]},
            }
        }
    ).encode()
    path.write_bytes(raw)
    papers = [Paper(title="Measured spectrum", year=2024), Paper(title="General review", year=2023)]
    expected_config = load_project_config(path)
    expected_hypotheses = load_hypotheses_from_config(path)
    expected_classes = classify_corpus(papers, config_path=path)
    expected_validation = validate_full_config(path, categories=("search_config", "hypothesis_config"))
    path.write_text("project_config: {search: {query: injected}, subfield_keywords: {C_injected: [spectrum]}}\n")
    assert load_project_config(path, source_bytes=raw) == expected_config
    assert load_hypotheses_from_config(path, source_bytes=raw) == expected_hypotheses
    assert classify_corpus(papers, config_path=path, config_source_bytes=raw) == expected_classes
    assert (
        validate_full_config(path, categories=("search_config", "hypothesis_config"), source_bytes=raw)
        == expected_validation
    )
    if restore:
        path.write_bytes(raw)


@pytest.mark.timeout(60)
def test_real_analysis_outputs_match_path_reference_during_config_replacement(tmp_path: Path, sample_corpus_path: str):
    root = tmp_path / "project"
    (root / "manuscript").mkdir(parents=True)
    path = root / "manuscript/config.yaml"
    raw = yaml.safe_dump(
        {"project_config": {"subfield_keywords": {"B_admitted": ["inference", "principle"], "A2_other": ["catchall"]}}}
    ).encode()
    path.write_bytes(raw)
    args = argparse.Namespace(
        corpus=sample_corpus_path,
        output_dir=str(tmp_path / "expected"),
        min_year=2000,
        max_features=50,
        n_topics=1,
        seed=42,
    )
    run_meta_analysis_pipeline(args, project_root=root)
    path.write_text("project_config: {subfield_keywords: {C_injected: [inference]}}\n")
    args.output_dir = str(tmp_path / "actual")
    run_meta_analysis_pipeline(args, project_root=root, config_source_bytes=raw)
    # These complete deterministic outputs depend directly on configured
    # classification. The stored publication/reference files are untouched.
    for name in ("subfield_classification.json", "subfield_timeline.json", "descriptive_stats.json"):
        expected = (tmp_path / "expected/data" / name).read_bytes()
        actual = (tmp_path / "actual/data" / name).read_bytes()
        assert actual == expected
        assert isinstance(json.loads(actual), dict)


def test_admitted_domain_bytes_require_their_source_path():
    from template_literature_meta_analysis.analysis.subfield_registry import configure_subfields
    from template_literature_meta_analysis.knowledge_graph.hypothesis import configure_hypotheses

    with pytest.raises(ValueError, match="source path"):
        configure_subfields(source_bytes=b"project_config: {}")
    with pytest.raises(ValueError, match="source path"):
        configure_hypotheses(source_bytes=b"project_config: {}")
    with pytest.raises(ValueError, match="source path"):
        classify_corpus([], config_source_bytes=b"project_config: {}")
