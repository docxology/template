"""Tests for analysis.pipeline_runner."""

from __future__ import annotations

import argparse
from pathlib import Path

import json

from template_literature_meta_analysis.analysis.pipeline_runner import run_meta_analysis_pipeline
from template_literature_meta_analysis.literature.models import Paper


def test_run_meta_analysis_pipeline_writes_artifacts(sample_corpus_path: str) -> None:
    output_dir = Path(sample_corpus_path).parent / "analysis_out"
    args = argparse.Namespace(
        corpus=sample_corpus_path,
        output_dir=str(output_dir),
        min_year=2000,
        max_features=50,
        n_topics=2,
        seed=42,
    )
    project_root = Path(__file__).resolve().parents[2]
    run_meta_analysis_pipeline(args, project_root=project_root)

    data_dir = output_dir / "data"
    expected = [
        "subfield_classification.json",
        "subfield_timeline.json",
        "temporal_analysis.json",
        "tfidf_data.json",
        "topics.json",
        "citation_network.json",
        "citation_graph.gml",
    ]
    for name in expected:
        assert (data_dir / name).exists(), f"missing {name}"


def test_run_meta_analysis_pipeline_temporal_error_on_missing_years(
    tmp_path: Path,
) -> None:
    from template_literature_meta_analysis.literature.corpus import Corpus

    corpus = Corpus()
    corpus.add(
        Paper(
            title="Undated paper",
            abstract="active inference and free energy principle",
            authors=[],
            year=None,
        )
    )
    corpus_path = tmp_path / "corpus.jsonl"
    corpus.save(corpus_path)

    output_dir = tmp_path / "analysis_out"
    args = argparse.Namespace(
        corpus=str(corpus_path),
        output_dir=str(output_dir),
        min_year=2000,
        max_features=50,
        n_topics=2,
        seed=42,
    )
    project_root = Path(__file__).resolve().parents[2]
    run_meta_analysis_pipeline(args, project_root=project_root)

    temporal_path = output_dir / "data" / "temporal_analysis.json"
    payload = json.loads(temporal_path.read_text(encoding="utf-8"))
    assert "error" in payload

    # A genuinely dated one-paper corpus has counts but cannot estimate growth.
    dated = Corpus(
        papers=[Paper(title="Dated paper", abstract="active inference and free energy principle", year=2025)]
    )
    dated_path = tmp_path / "dated-corpus.jsonl"
    dated.save(dated_path)
    args.corpus, args.output_dir, args.n_topics = str(dated_path), str(tmp_path / "dated-analysis"), 1
    run_meta_analysis_pipeline(args, project_root=project_root)
    payload = json.loads((Path(args.output_dir) / "data/temporal_analysis.json").read_text())
    assert "error" not in payload
    assert payload["year_counts"] == payload["cumulative"] == {"2025": 1}
    assert payload["first_year"] == payload["last_year"] == payload["peak_year"] == 2025
    assert payload["total_papers"] == 1 and payload["growth_status"] == "insufficient_years"
    assert all(payload[field] is None for field in ("cagr", "mean_growth_rate", "doubling_time"))
