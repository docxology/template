"""Tests for reproducibility.runner — the reproducibility-assessment orchestrator.

Mirrors tests/knowledge_graph/test_kg_runner.py's shape (real tmp_path
corpus + argparse.Namespace + run_*_pipeline call) plus
tests/reproducibility/test_reproducibility_extraction.py's pytest-httpserver pattern for the
LLM stand-in (no mock/patch framework anywhere).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pytest_httpserver import HTTPServer

from literature.corpus import Corpus
from literature.fulltext_download import safe_filename
from reproducibility.runner import run_reproducibility_pipeline
from tests.knowledge_graph.llm_extraction_fixtures import httpserver_base_url, make_paper


def _valid_workflow_response() -> list[dict]:
    """A valid two-node workflow-graph LLM response (source -> method)."""
    return [
        {
            "node_id": "n1",
            "node_name": "Raw Dataset",
            "node_type": "source",
            "source_quote": "We used the publicly released benchmark dataset from the archive.",
            "description": "Raw benchmark dataset.",
            "reproducibility_rating": 3,
            "rationale": "Dataset named, no version pinned.",
            "depends_on": [],
        },
        {
            "node_id": "n2",
            "node_name": "Preprocessing",
            "node_type": "method",
            "source_quote": "Records were normalized and de-duplicated before analysis.",
            "description": "Standard preprocessing.",
            "reproducibility_rating": 4,
            "rationale": "Steps fully specified.",
            "depends_on": ["n1"],
        },
    ]


def _make_args(
    *,
    corpus_path: Path,
    output_dir: Path,
    fulltext_dir: str | None,
    llm_url: str,
    config: str | None = None,
    clear_workflow_graphs: bool = False,
    max_papers: int | None = None,
) -> argparse.Namespace:
    return argparse.Namespace(
        corpus=str(corpus_path),
        output_dir=str(output_dir),
        fulltext_dir=fulltext_dir,
        config=config,
        llm_model="test-model",
        llm_url=llm_url,
        checkpoint_interval=50,
        clear_workflow_graphs=clear_workflow_graphs,
        max_papers=max_papers,
    )


def _write_corpus(tmp_path: Path, papers: list) -> Path:
    corpus = Corpus()
    for paper in papers:
        corpus.add(paper)
    corpus_path = tmp_path / "corpus.jsonl"
    corpus.save(corpus_path)
    return corpus_path


def test_run_reproducibility_pipeline_writes_expected_outputs(httpserver: HTTPServer, tmp_path: Path):
    """A corpus with fulltext available -> all 3 output files are written, in order."""
    paper = make_paper(doi="10.1/runner-a", title="Runner Paper A")
    corpus_path = _write_corpus(tmp_path, [paper])

    fulltext_dir = tmp_path / "fulltext"
    fulltext_dir.mkdir()
    (fulltext_dir / f"{safe_filename(paper.canonical_id)}.txt").write_text(
        "Full text describing the paper's dataset and preprocessing pipeline.",
        encoding="utf-8",
    )

    httpserver.expect_request("/api/generate", method="POST").respond_with_json(
        {"response": json.dumps(_valid_workflow_response()), "done": True}
    )

    output_dir = tmp_path / "output"
    args = _make_args(
        corpus_path=corpus_path,
        output_dir=output_dir,
        fulltext_dir=str(fulltext_dir),
        llm_url=httpserver_base_url(httpserver),
    )

    run_reproducibility_pipeline(args, project_root=tmp_path)

    data_dir = output_dir / "data"
    workflow_graphs_path = data_dir / "workflow_graphs.jsonl"
    scores_path = data_dir / "reproducibility_scores.json"
    summary_path = data_dir / "reproducibility_summary.json"

    assert workflow_graphs_path.exists()
    assert scores_path.exists()
    assert summary_path.exists()

    lines = [line for line in workflow_graphs_path.read_text(encoding="utf-8").splitlines() if line]
    assert len(lines) == 1
    graph_data = json.loads(lines[0])
    assert graph_data["paper_id"] == paper.canonical_id
    assert len(graph_data["nodes"]) == 2

    scores = json.loads(scores_path.read_text(encoding="utf-8"))
    assert paper.canonical_id in scores
    entry = scores[paper.canonical_id]
    assert entry["n_nodes"] == 2
    assert entry["n_edges"] == 1
    assert 0.0 <= entry["composite_score"] <= 1.0
    assert entry["quote_verification_rate"] is not None

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["n_papers_scored"] == 1
    assert summary["n_skipped_no_fulltext"] == 0
    assert summary["n_skipped_unparseable_pdf"] == 0
    assert summary["fulltext_available"] is True
    assert 0.0 <= summary["mean_composite_score"] <= 1.0


def test_run_reproducibility_pipeline_clear_workflow_graphs_flag(httpserver: HTTPServer, tmp_path: Path):
    """--clear-workflow-graphs deletes the existing JSONL and forces full re-extraction."""
    paper = make_paper(doi="10.1/runner-clear", title="Runner Clear Paper")
    corpus_path = _write_corpus(tmp_path, [paper])

    fulltext_dir = tmp_path / "fulltext"
    fulltext_dir.mkdir()
    (fulltext_dir / f"{safe_filename(paper.canonical_id)}.txt").write_text(
        "Full text describing the paper's dataset and preprocessing pipeline.",
        encoding="utf-8",
    )

    output_dir = tmp_path / "output"
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True)
    stale_path = data_dir / "workflow_graphs.jsonl"
    stale_path.write_text('{"not": "a real graph, proves it gets deleted"}\n', encoding="utf-8")

    httpserver.expect_request("/api/generate", method="POST").respond_with_json(
        {"response": json.dumps(_valid_workflow_response()), "done": True}
    )

    args = _make_args(
        corpus_path=corpus_path,
        output_dir=output_dir,
        fulltext_dir=str(fulltext_dir),
        llm_url=httpserver_base_url(httpserver),
        clear_workflow_graphs=True,
    )

    run_reproducibility_pipeline(args, project_root=tmp_path)

    # Exactly one real LLM call was made (proves it was not skipped as
    # "already covered" by the stale/bogus pre-existing file).
    assert len(httpserver.log) == 1

    lines = [line for line in stale_path.read_text(encoding="utf-8").splitlines() if line]
    assert len(lines) == 1
    graph_data = json.loads(lines[0])
    assert graph_data["paper_id"] == paper.canonical_id
    assert len(graph_data["nodes"]) == 2


def test_run_reproducibility_pipeline_fulltext_disabled_logs_warning_and_degrades(
    tmp_path: Path, caplog
):
    """fulltext.enabled=false + no --fulltext-dir -> loud warning, valid empty outputs, no crash."""
    paper = make_paper(doi="10.1/runner-nofulltext", title="Runner No Fulltext Paper")
    corpus_path = _write_corpus(tmp_path, [paper])

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
project_config:
  fulltext:
    enabled: false
    download_dir: "output/fulltext"
""".strip(),
        encoding="utf-8",
    )

    output_dir = tmp_path / "output"
    args = _make_args(
        corpus_path=corpus_path,
        output_dir=output_dir,
        fulltext_dir=None,
        llm_url="http://127.0.0.1:1",  # unreachable -- proves zero LLM calls occur
        config=str(config_path),
    )

    import logging

    with caplog.at_level(logging.WARNING, logger="reproducibility_assessment"):
        run_reproducibility_pipeline(args, project_root=tmp_path)

    # Not a silent no-op: a WARNING (not DEBUG/INFO) was actually logged.
    warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert any("fulltext" in r.message.lower() for r in warnings)

    data_dir = output_dir / "data"
    workflow_graphs_path = data_dir / "workflow_graphs.jsonl"
    scores_path = data_dir / "reproducibility_scores.json"
    summary_path = data_dir / "reproducibility_summary.json"

    assert workflow_graphs_path.exists()
    assert workflow_graphs_path.read_text(encoding="utf-8").strip() == ""

    scores = json.loads(scores_path.read_text(encoding="utf-8"))
    assert scores == {}

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["n_papers_scored"] == 0
    assert summary["mean_composite_score"] == 0.0
    assert summary["n_skipped_no_fulltext"] == 1
    assert summary["n_skipped_unparseable_pdf"] == 0
    assert summary["fulltext_available"] is False


def test_run_reproducibility_pipeline_distinguishes_unparseable_pdf_from_no_fulltext(
    tmp_path: Path,
):
    """A .pdf-with-no-.txt paper counts as unparseable_pdf, not no_fulltext."""
    paper_no_fulltext = make_paper(doi="10.1/runner-nof", title="No Fulltext At All")
    paper_bad_pdf = make_paper(doi="10.1/runner-badpdf", title="PDF But No Text")
    corpus_path = _write_corpus(tmp_path, [paper_no_fulltext, paper_bad_pdf])

    fulltext_dir = tmp_path / "fulltext"
    fulltext_dir.mkdir()
    # paper_bad_pdf has a PDF on disk but no extracted .txt (extraction failed).
    (fulltext_dir / f"{safe_filename(paper_bad_pdf.canonical_id)}.pdf").write_bytes(b"%PDF-1.4 not a real pdf")

    output_dir = tmp_path / "output"
    args = _make_args(
        corpus_path=corpus_path,
        output_dir=output_dir,
        fulltext_dir=str(fulltext_dir),
        llm_url="http://127.0.0.1:1",  # unreachable; both papers are skipped before any call
    )

    run_reproducibility_pipeline(args, project_root=tmp_path)

    summary_path = output_dir / "data" / "reproducibility_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["n_skipped_no_fulltext"] == 1
    assert summary["n_skipped_unparseable_pdf"] == 1


def test_run_reproducibility_pipeline_auto_loads_config_and_applies_overrides(
    httpserver: HTTPServer, tmp_path: Path
):
    """manuscript/config.yaml's reproducibility_assessment + fulltext blocks drive behavior.

    Covers: auto-load-without-explicit---config, checkpoint_interval/max_papers/
    llm_model/llm_url overrides, content_weights/structural_weights/
    low_score_threshold/fuzzy_quote_threshold wiring, and fulltext.download_dir
    resolved relative to project_root.
    """
    paper_a = make_paper(doi="10.1/runner-cfg-a", title="Config Paper A")
    paper_b = make_paper(doi="10.1/runner-cfg-b", title="Config Paper B")
    corpus_path = _write_corpus(tmp_path, [paper_a, paper_b])

    fulltext_dir = tmp_path / "output" / "fulltext"
    fulltext_dir.mkdir(parents=True)
    for paper in (paper_a, paper_b):
        (fulltext_dir / f"{safe_filename(paper.canonical_id)}.txt").write_text(
            "Full text describing the paper's dataset and preprocessing pipeline.",
            encoding="utf-8",
        )

    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    (manuscript_dir / "config.yaml").write_text(
        f"""
project_config:
  fulltext:
    enabled: true
    download_dir: "output/fulltext"
  reproducibility_assessment:
    checkpoint_interval: 1
    clear_workflow_graphs: false
    max_papers: 1
    llm_model: config-model
    llm_url: "{httpserver_base_url(httpserver)}"
    content_weights:
      sources: 0.4
      methods: 0.2
      experiments: 0.2
      sinks: 0.2
    structural_weights:
      source_consumption: 0.3
      sink_production: 0.2
      reference_resolution: 0.2
      path_coverage: 0.15
      cohesion: 0.15
    low_score_threshold: 0.9
    fuzzy_quote_threshold: 0.5
""".strip(),
        encoding="utf-8",
    )

    httpserver.expect_request("/api/generate", method="POST").respond_with_json(
        {"response": json.dumps(_valid_workflow_response()), "done": True}
    )

    output_dir = tmp_path / "output"
    args = _make_args(
        corpus_path=corpus_path,
        output_dir=output_dir,
        fulltext_dir=None,
        llm_url="http://127.0.0.1:1",  # deliberately wrong -- config's llm_url must win
        config=None,  # not explicit -> auto-loaded from project_root/manuscript/config.yaml
    )

    run_reproducibility_pipeline(args, project_root=tmp_path)

    # max_papers: 1 from config -> only paper_a is a candidate, exactly one LLM call.
    assert len(httpserver.log) == 1

    summary_path = output_dir / "data" / "reproducibility_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["n_papers_scored"] == 1
    assert summary["low_score_threshold"] == 0.9
    # A composite score below 0.9 is virtually certain for a 2-node graph ->
    # proves low_score_threshold was actually read from config, not defaulted.
    assert summary["n_low_score"] == 1


def test_run_reproducibility_pipeline_skips_when_corpus_already_covered(tmp_path: Path):
    """Every candidate paper already has a workflow graph -> zero LLM calls, no crash."""
    paper = make_paper(doi="10.1/runner-covered", title="Already Covered Paper")
    corpus_path = _write_corpus(tmp_path, [paper])

    output_dir = tmp_path / "output"
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True)

    from reproducibility.models import NodeType, WorkflowNode, build_workflow_graph, serialize_workflow_graphs

    existing_node = WorkflowNode(
        node_id="n1",
        node_name="Existing Source",
        node_type=NodeType.SOURCE,
        source_quote="Pre-existing quote for the already-covered paper.",
        description="Pre-existing node.",
        reproducibility_rating=3,
        paper_id=paper.canonical_id,
    )
    existing_graph = build_workflow_graph(paper.canonical_id, [existing_node])
    workflow_graphs_path = data_dir / "workflow_graphs.jsonl"
    workflow_graphs_path.write_text(
        "\n".join(serialize_workflow_graphs([existing_graph])) + "\n", encoding="utf-8"
    )

    args = _make_args(
        corpus_path=corpus_path,
        output_dir=output_dir,
        fulltext_dir=str(tmp_path / "nonexistent-fulltext"),
        llm_url="http://127.0.0.1:1",  # unreachable -- proves zero LLM calls occur
    )

    run_reproducibility_pipeline(args, project_root=tmp_path)

    scores_path = data_dir / "reproducibility_scores.json"
    scores = json.loads(scores_path.read_text(encoding="utf-8"))
    assert paper.canonical_id in scores
    # No fulltext on disk for this paper -> quote verification has nothing to check.
    assert scores[paper.canonical_id]["quote_verification_rate"] is None

    summary = json.loads((data_dir / "reproducibility_summary.json").read_text(encoding="utf-8"))
    assert summary["n_papers_scored"] == 1
    assert summary["n_skipped_no_fulltext"] == 0
    assert summary["n_skipped_unparseable_pdf"] == 0


def test_run_reproducibility_pipeline_default_fulltext_dir_when_no_config_at_all(tmp_path: Path):
    """No config file anywhere, no --fulltext-dir -> falls back to config.FULLTEXT_DIR."""
    paper = make_paper(doi="10.1/runner-nodefault", title="No Config At All Paper")
    corpus_path = _write_corpus(tmp_path, [paper])

    output_dir = tmp_path / "output"
    args = _make_args(
        corpus_path=corpus_path,
        output_dir=output_dir,
        fulltext_dir=None,
        llm_url="http://127.0.0.1:1",
        config=None,
    )

    # project_root has no manuscript/config.yaml at all.
    run_reproducibility_pipeline(args, project_root=tmp_path)

    summary = json.loads((output_dir / "data" / "reproducibility_summary.json").read_text(encoding="utf-8"))
    assert summary["fulltext_available"] is False
    assert summary["n_skipped_no_fulltext"] == 1


def test_run_reproducibility_pipeline_extraction_failure_not_double_counted(
    httpserver: HTTPServer, tmp_path: Path
):
    """A paper WITH fulltext whose LLM extraction fails is not counted as either skip reason."""
    paper = make_paper(doi="10.1/runner-failed-extraction", title="Extraction Fails Paper")
    corpus_path = _write_corpus(tmp_path, [paper])

    fulltext_dir = tmp_path / "fulltext"
    fulltext_dir.mkdir()
    (fulltext_dir / f"{safe_filename(paper.canonical_id)}.txt").write_text(
        "Full text describing the paper's pipeline.", encoding="utf-8"
    )

    # Every LLM call returns a 500 -> extract_workflow_nodes exhausts retries -> RuntimeError,
    # which extract_workflow_graphs_llm catches internally (fail_count), never adding this
    # paper's canonical_id to processed_ids and never producing a graph for it.
    httpserver.expect_request("/api/generate", method="POST").respond_with_data(
        "Internal Server Error", status=500
    )

    # llm_max_retries: 1 keeps this test fast (no exponential-backoff sleep
    # between attempts) while still exercising the RuntimeError-is-caught path.
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "project_config:\n  reproducibility_assessment:\n    llm_max_retries: 1\n",
        encoding="utf-8",
    )

    output_dir = tmp_path / "output"
    args = _make_args(
        corpus_path=corpus_path,
        output_dir=output_dir,
        fulltext_dir=str(fulltext_dir),
        llm_url=httpserver_base_url(httpserver),
        config=str(config_path),
    )

    run_reproducibility_pipeline(args, project_root=tmp_path)

    summary = json.loads((output_dir / "data" / "reproducibility_summary.json").read_text(encoding="utf-8"))
    assert summary["n_papers_scored"] == 0
    # Not counted as no_fulltext (it HAD fulltext) nor unparseable_pdf (no .pdf involved):
    # the extraction attempt itself failed, a third distinct outcome.
    assert summary["n_skipped_no_fulltext"] == 0
    assert summary["n_skipped_unparseable_pdf"] == 0
