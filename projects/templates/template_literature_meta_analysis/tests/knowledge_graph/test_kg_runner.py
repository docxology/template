"""Tests for knowledge_graph.kg_runner."""

from __future__ import annotations

import argparse
from pathlib import Path

from knowledge_graph.kg_runner import run_knowledge_graph_pipeline
from knowledge_graph.nanopublication import Assertion, create_nanopub, serialize_nanopubs
from literature.corpus import Corpus


def _seed_nanopubs(corpus: Corpus, nanopub_path: Path) -> None:
    nanopubs = []
    for paper in corpus.papers:
        if not paper.abstract:
            continue
        assertion = Assertion(
            assertion_id=f"test_{paper.canonical_id}",
            paper_id=paper.canonical_id,
            claim="Cached assertion for runner test.",
            assertion_type="supports",
            hypothesis_id="PRIMARY_EFFICACY",
            confidence=0.9,
            citation_count=paper.citation_count or 0,
        )
        nanopubs.append(create_nanopub(assertion, attribution="test"))
    serialize_nanopubs(nanopubs, nanopub_path)


def test_kg_runner_skips_llm_when_corpus_covered(
    sample_papers: list,
    tmp_path: Path,
) -> None:
    corpus = Corpus()
    for paper in sample_papers:
        corpus.add(paper)

    corpus_path = tmp_path / "corpus.jsonl"
    corpus.save(corpus_path)

    output_dir = tmp_path / "output"
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True)
    _seed_nanopubs(corpus, data_dir / "nanopublications.jsonl")

    args = argparse.Namespace(
        corpus=str(corpus_path),
        output_dir=str(output_dir),
        config=None,
        llm_model="gemma3:4b",
        llm_url="http://127.0.0.1:11434",
        checkpoint_interval=50,
        clear_assertions=False,
        max_papers=None,
    )
    project_root = Path(__file__).resolve().parents[2]
    run_knowledge_graph_pipeline(args, project_root=project_root)

    assert (data_dir / "hypothesis_scores.json").exists()
    assert (data_dir / "hypothesis_trends.json").exists()
    assert (data_dir / "assertion_summary.json").exists()


def test_kg_runner_loads_yaml_config(
    sample_papers: list,
    tmp_path: Path,
) -> None:
    corpus = Corpus()
    for paper in sample_papers:
        corpus.add(paper)
    corpus_path = tmp_path / "corpus.jsonl"
    corpus.save(corpus_path)

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
project_config:
  knowledge_graph:
    checkpoint_interval: 25
    clear_assertions: false
  llm_extraction:
    model: test-model
    base_url: http://127.0.0.1:11434
""".strip(),
        encoding="utf-8",
    )

    output_dir = tmp_path / "output"
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True)
    _seed_nanopubs(corpus, data_dir / "nanopublications.jsonl")

    args = argparse.Namespace(
        corpus=str(corpus_path),
        output_dir=str(output_dir),
        config=str(config_path),
        llm_model="gemma3:4b",
        llm_url="http://127.0.0.1:11434",
        checkpoint_interval=50,
        clear_assertions=False,
        max_papers=None,
    )
    run_knowledge_graph_pipeline(args, project_root=tmp_path)
    assert args.checkpoint_interval == 25
    assert args.llm_model == "test-model"


def test_kg_runner_removes_legacy_checkpoint(
    sample_papers: list,
    tmp_path: Path,
) -> None:
    corpus = Corpus()
    for paper in sample_papers:
        corpus.add(paper)
    corpus_path = tmp_path / "corpus.jsonl"
    corpus.save(corpus_path)

    output_dir = tmp_path / "output"
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True)
    _seed_nanopubs(corpus, data_dir / "nanopublications.jsonl")
    legacy = output_dir / "llm_checkpoint.jsonl"
    legacy.write_text('{"legacy": true}\n', encoding="utf-8")

    args = argparse.Namespace(
        corpus=str(corpus_path),
        output_dir=str(output_dir),
        config=None,
        llm_model="gemma3:4b",
        llm_url="http://127.0.0.1:11434",
        checkpoint_interval=50,
        clear_assertions=False,
        max_papers=None,
    )
    project_root = Path(__file__).resolve().parents[2]
    run_knowledge_graph_pipeline(args, project_root=project_root)
    assert not legacy.exists()
